/** Port of index/fts.py query-time pipeline (FR-032 / D-056): two-tier
 * search over the split index — title-only `laws_fts` (tier 1, unchanged
 * ranking) plus per-segment `articles_fts` (tier 2, two-phase: score-only
 * overscan + host-side breadth-corrected aggregation, then snippet
 * extraction for the surviving hits only) — finished by the FR-015
 * rang-aware re-rank. SQL text is copied verbatim from `_FTS_SELECT`,
 * `_SEGMENT_SCORE_SELECT`, and `_SEGMENT_SNIPPET_SELECT`. */

import { bgNormalize } from "./normalize";

/** Shape of index/fts.py search_fts hit dicts. Tier-2 (body) hits carry
 * matched_kind/matched_label/seg_snippet; title-tier hits carry null. */
export interface FtsHit {
  law_id: string;
  doc_id: number | null;
  title: string | null;
  category: string;
  snippet: string;
  score: number;
  matched_kind: string | null;
  matched_label: string | null;
  seg_snippet: string | null;
}

/** Internal pool hit: pre-enrichment body-tier hits carry the winning
 * segment's seg_no (Python's `_seg_no` key, deleted on enrichment). */
type PoolHit = FtsHit & { _seg_no?: string };

interface TitleRow {
  law_id: string;
  doc_id: number;
  title: string | null;
  category: string;
  snippet: string;
  score: number;
}

interface SegmentScoreRow {
  law_id: string;
  seg_no: string;
  kind: string;
  label: string;
  category: string;
  score: number;
}

// Tier-1 SELECT — verbatim from index/fts.py `_FTS_SELECT`.
const FTS_SELECT = `
    SELECT laws_fts.law_id          AS law_id,
           laws.doc_id              AS doc_id,
           laws.title               AS title,
           laws.category            AS category,
           snippet(laws_fts, 1, '<b>', '</b>', '...', 12) AS snippet,
           bm25(laws_fts)           AS score
      FROM laws_fts
      JOIN laws USING(law_id)
     WHERE laws_fts MATCH ?
`;

// Tier-2 phase 1 — verbatim from index/fts.py `_SEGMENT_SCORE_SELECT`
// (score-only: phase 1 fetches NO text; snippets come in phase 2 for
// the surviving hits only).
const SEGMENT_SCORE_SELECT = `
    SELECT articles_fts.law_id     AS law_id,
           articles_fts.seg_no     AS seg_no,
           articles_fts.kind       AS kind,
           articles_fts.label      AS label,
           articles_fts.category   AS category,
           bm25(articles_fts)      AS score
      FROM articles_fts
     WHERE articles_fts MATCH ?
`;

// Tier-2 phase 2 — verbatim from index/fts.py `_SEGMENT_SNIPPET_SELECT`
// ({keys} is replaced by the ?-placeholder list, like Python's .format).
const SEGMENT_SNIPPET_SELECT = `
    SELECT articles_fts.law_id     AS law_id,
           articles_fts.seg_no     AS seg_no,
           snippet(articles_fts, 4, '<b>', '</b>', '...', 12) AS seg_snippet
      FROM articles_fts
     WHERE articles_fts MATCH ?
       AND (articles_fts.law_id || ':' || articles_fts.seg_no) IN ({keys})
`;

/** Fixed overscan window for tier 2 — index/fts.py `TIER2_OVERSCAN`.
 * FIXED (not K×limit) so breadth counts, and therefore every act score,
 * are deterministic and independent of the caller's limit. */
export const TIER2_OVERSCAN = 500;

/** Breadth-corrected best-segment score constants (D-056 Q1 as amended
 * 2026-07-23): act_score = best_bm25 − ALPHA·n/(n+SATURATION). The
 * saturating RATIONAL form (no transcendentals) keeps the correction
 * float-identical across CPython/libm and V8/fdlibm. */
export const BREADTH_ALPHA = 4.0;
export const BREADTH_SATURATION = 5.0;

/** Act pool handed to the FR-015 rang-tier sort — index/fts.py
 * `TIER2_ACT_POOL`. FIXED at 20 (not `limit`): the sort must see enough
 * body-tier acts to rescue parent laws whose breadth-corrected rank
 * lands below the caller's limit. Truncation to `limit` happens AFTER
 * the sort; snippets are fetched after truncation. */
export const TIER2_ACT_POOL = 20;

function errorMessage(e: unknown): string {
  if (e instanceof Error) {
    const causeMsg = e.cause instanceof Error ? `: ${e.cause.message}` : "";
    return `${e.message}${causeMsg}`;
  }
  return String(e);
}

/** Port of index/fts.py `_is_user_input_error` — the user-input
 * OperationalError allowlist (malformed FTS5 queries → empty results;
 * everything else propagates so the route layer maps INDEX_MISSING).
 * D1 prefixes messages ("D1_ERROR: ..."), so "no such column" is
 * matched by inclusion rather than str.startswith — behaviorally
 * identical for real SQLite messages. Shared by both tiers and by
 * queries.ts's scoped title-tier snippet upgrade. */
export function isUserInputFtsError(e: unknown): boolean {
  const msg = errorMessage(e).toLowerCase();
  return (
    msg.includes("fts5") ||
    msg.includes("syntax error") ||
    msg.includes("unknown special query") ||
    msg.includes("unterminated string") ||
    msg.includes("no such column")
  );
}

/** Port of index/fts.py `_run_match` — tier-1 MATCH over title-only
 * laws_fts. */
async function runMatch(
  db: D1Database,
  matchQuery: string,
  category: string | null,
  limit: number,
): Promise<TitleRow[]> {
  let sql = FTS_SELECT;
  const params: (string | number)[] = [matchQuery];
  if (category) {
    sql += " AND laws.category = ?";
    params.push(category);
  }
  sql += " ORDER BY bm25(laws_fts) LIMIT ?";
  params.push(limit);
  try {
    const res = await db.prepare(sql).bind(...params).all<TitleRow>();
    return res.results;
  } catch (e) {
    if (!isUserInputFtsError(e)) throw e;
    return [];
  }
}

/** Port of index/fts.py `_run_segment_match` — tier-2 phase-1 MATCH over
 * articles_fts (score-only), fixed TIER2_OVERSCAN window, bm25-ordered.
 * Same user-input error contract as runMatch. */
async function runSegmentMatch(
  db: D1Database,
  matchQuery: string,
  category: string | null,
): Promise<SegmentScoreRow[]> {
  let sql = SEGMENT_SCORE_SELECT;
  const params: (string | number)[] = [matchQuery];
  if (category) {
    sql += " AND articles_fts.category = ?";
    params.push(category);
  }
  sql += " ORDER BY bm25(articles_fts) LIMIT ?";
  params.push(TIER2_OVERSCAN);
  try {
    const res = await db.prepare(sql).bind(...params).all<SegmentScoreRow>();
    return res.results;
  } catch (e) {
    if (!isUserInputFtsError(e)) throw e;
    return [];
  }
}

/** Port of index/fts.py `_fetch_segment_snippets` — phase 2:
 * {'law_id:seg_no': snippet} for the winning segments. */
async function fetchSegmentSnippets(
  db: D1Database,
  matchQuery: string,
  keys: string[],
): Promise<Map<string, string>> {
  if (keys.length === 0) return new Map();
  const sql = SEGMENT_SNIPPET_SELECT.replace("{keys}", keys.map(() => "?").join(", "));
  let rows: { law_id: string; seg_no: string; seg_snippet: string }[];
  try {
    const res = await db
      .prepare(sql)
      .bind(matchQuery, ...keys)
      .all<{ law_id: string; seg_no: string; seg_snippet: string }>();
    rows = res.results;
  } catch (e) {
    if (!isUserInputFtsError(e)) throw e;
    return new Map();
  }
  return new Map(rows.map((r) => [`${r.law_id}:${r.seg_no}`, r.seg_snippet]));
}

/** Port of index/fts.py `_fetch_laws_meta` — doc_id/title for the
 * winning acts (PK lookups; phase 1 carries no laws JOIN so the 500-row
 * window stays text-free). */
async function fetchLawsMeta(
  db: D1Database,
  lawIds: string[],
): Promise<Map<string, { law_id: string; doc_id: number; title: string | null }>> {
  if (lawIds.length === 0) return new Map();
  const sql =
    "SELECT law_id, doc_id, title FROM laws WHERE law_id IN (" +
    lawIds.map(() => "?").join(", ") +
    ")";
  const res = await db
    .prepare(sql)
    .bind(...lawIds)
    .all<{ law_id: string; doc_id: number; title: string | null }>();
  return new Map(res.results.map((r) => [r.law_id, r]));
}

/** FR-015 part 2 rang tiers — verbatim from index/fts.py `_RANG_TIER`. */
const RANG_TIER: Readonly<Record<string, number>> = {
  laws: 0,
  codes: 0,
  regulations: 1,
  implementing: 1,
  ordinances: 1,
};

function rangTier(hit: FtsHit): number {
  return RANG_TIER[hit.category] ?? 2;
}

function rangTierSort<T extends FtsHit>(hits: T[]): T[] {
  return hits
    .map((hit, i) => [hit, i] as const)
    .sort((a, b) => rangTier(a[0]) - rangTier(b[0]) || a[1] - b[1])
    .map(([hit]) => hit);
}

/** Port of index/fts.py `_trim_title` — deterministic title fragment for
 * tier-2 hits (whose MATCH ran on articles_fts, so no FTS title-snippet
 * is available): the leading 12 whitespace tokens, '...'-terminated when
 * truncated. */
export function trimTitle(title: string | null, maxTokens = 12): string {
  if (!title) return "";
  const tokens = title.split(/\s+/).filter((t) => t);
  if (tokens.length <= maxTokens) return title;
  return tokens.slice(0, maxTokens).join(" ") + "...";
}

function titleHit(row: TitleRow): PoolHit {
  return {
    law_id: row.law_id,
    doc_id: row.doc_id,
    title: row.title,
    category: row.category,
    snippet: row.snippet,
    score: row.score,
    matched_kind: null,
    matched_label: null,
    seg_snippet: null,
  };
}

/** Port of index/fts.py `_segment_hits` — aggregate phase-1 window rows
 * (bm25-ordered) to LIGHT act-level hits: first occurrence per act = its
 * best segment; n = occurrences in the window; score per the
 * breadth-corrected formula. Returns the top TIER2_ACT_POOL acts,
 * un-enriched (no titles, no snippets — see enrichSegmentHits, called
 * post-truncation). */
function segmentHits(rows: SegmentScoreRow[]): PoolHit[] {
  const order: string[] = [];
  const best = new Map<string, SegmentScoreRow>();
  const count = new Map<string, number>();
  for (const row of rows) {
    const lid = row.law_id;
    if (!best.has(lid)) {
      best.set(lid, row);
      order.push(lid);
    }
    count.set(lid, (count.get(lid) ?? 0) + 1);
  }

  const scored: { score: number; lid: string; row: SegmentScoreRow }[] = [];
  for (const lid of order) {
    const row = best.get(lid)!;
    const n = count.get(lid)!;
    // Plain arithmetic, no transcendentals — float-identical to Python's
    // `row["score"] - BREADTH_ALPHA * n / (n + BREADTH_SATURATION)`.
    scored.push({ score: row.score - (BREADTH_ALPHA * n) / (n + BREADTH_SATURATION), lid, row });
  }
  scored.sort((a, b) => a.score - b.score);

  const hits: PoolHit[] = [];
  for (const { score, lid, row } of scored.slice(0, TIER2_ACT_POOL)) {
    hits.push({
      law_id: lid,
      doc_id: null,
      title: null,
      category: row.category,
      snippet: "",
      score,
      matched_kind: row.kind,
      matched_label: row.label,
      seg_snippet: "",
      _seg_no: row.seg_no,
    });
  }
  return hits;
}

/** Port of index/fts.py `_enrich_segment_hits` — phase 2, applied to the
 * ≤limit SURVIVING body-tier hits only: fetch act metadata
 * (title/doc_id) and the best-segment snippet, fill the display fields
 * in place. */
async function enrichSegmentHits(
  db: D1Database,
  matchQuery: string,
  hits: PoolHit[],
): Promise<void> {
  if (hits.length === 0) return;
  const keys = hits.map((h) => `${h.law_id}:${h._seg_no}`);
  const snippets = await fetchSegmentSnippets(db, matchQuery, keys);
  const meta = await fetchLawsMeta(
    db,
    hits.map((h) => h.law_id),
  );
  for (const h of hits) {
    const m = meta.get(h.law_id);
    const title = m ? m.title : null;
    h.doc_id = m ? m.doc_id : null;
    h.title = title;
    h.snippet = trimTitle(title);
    h.seg_snippet = snippets.get(`${h.law_id}:${h._seg_no}`) ?? "";
    delete h._seg_no;
  }
}

/** Port of index/fts.py `search_fts` — two-tier search over the FR-032
 * split index.
 *
 * Tier 1 (unchanged, D-051 gating): title-restricted MATCH over the
 * title-only laws_fts. Tier 2 (FR-032): overscan MATCH over
 * articles_fts, aggregated host-side to acts via the breadth-corrected
 * best-segment score; tier-2 hits carry matched_kind/matched_label/
 * seg_snippet, title-tier hits carry null there.
 *
 * Results are deduplicated by law_id (title tier wins), rang-sorted over
 * the FULL merged pool (title hits + TIER2_ACT_POOL body acts),
 * truncated to `limit`, and only then enriched (phase-2 snippet +
 * metadata for the surviving body-tier hits). */
export async function searchFts(
  db: D1Database,
  query: string,
  category: string | null = null,
  limit = 20,
): Promise<FtsHit[]> {
  const normalized = bgNormalize(query);
  if (!normalized) return [];

  const tokens = normalized.split(" ").filter((t) => t);
  let titleHits: PoolHit[] = [];
  if (tokens.length > 0) {
    const titleQ = tokens.map((t) => `title:${t}`).join(" ");
    titleHits = (await runMatch(db, titleQ, category, limit)).map(titleHit);
  }

  // Skip tier 2 when the title tier can serve the query (FR-027 /
  // D-051 — title-shaped queries are the dominant real traffic).
  const TIER2_MIN_TITLE_HITS = 3;
  if (titleHits.length >= Math.min(limit, TIER2_MIN_TITLE_HITS)) {
    return rangTierSort([...titleHits]).slice(0, limit);
  }

  const bodyHits = segmentHits(await runSegmentMatch(db, normalized, category));

  const seenIds = new Set(titleHits.map((h) => h.law_id));
  const merged: PoolHit[] = [...titleHits];
  for (const h of bodyHits) {
    if (seenIds.has(h.law_id)) continue;
    merged.push(h);
    seenIds.add(h.law_id);
  }

  // Rang-sort over the full pool (title hits + TIER2_ACT_POOL body
  // acts), truncate to the caller's limit, then enrich the surviving
  // body-tier hits (phase-2 snippet + metadata; ≤limit extractions).
  const final = rangTierSort(merged).slice(0, limit);
  await enrichSegmentHits(
    db,
    normalized,
    final.filter((h) => h._seg_no !== undefined),
  );
  return final;
}
