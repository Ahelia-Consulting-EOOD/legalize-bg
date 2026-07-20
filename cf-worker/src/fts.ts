/** Port of index/fts.py query-time pipeline: two-tier FTS5 search with
 * rang-aware re-rank. SQL text is copied verbatim from `_FTS_SELECT`. */

import { bgNormalize } from "./normalize";

export interface FtsRow {
  law_id: string;
  doc_id: number;
  title: string | null;
  category: string;
  snippet: string;
  score: number;
}

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

function errorMessage(e: unknown): string {
  if (e instanceof Error) {
    const causeMsg = e.cause instanceof Error ? `: ${e.cause.message}` : "";
    return `${e.message}${causeMsg}`;
  }
  return String(e);
}

/** Port of index/fts.py `_run_match`, including its user-input
 * OperationalError allowlist (malformed FTS5 queries → empty results;
 * everything else propagates so the route layer maps INDEX_MISSING).
 * D1 prefixes messages ("D1_ERROR: ..."), so "no such column" is
 * matched by inclusion rather than str.startswith — behaviorally
 * identical for real SQLite messages. */
async function runMatch(
  db: D1Database,
  matchQuery: string,
  category: string | null,
  limit: number,
): Promise<FtsRow[]> {
  let sql = FTS_SELECT;
  const params: (string | number)[] = [matchQuery];
  if (category) {
    sql += " AND laws.category = ?";
    params.push(category);
  }
  sql += " ORDER BY bm25(laws_fts) LIMIT ?";
  params.push(limit);
  try {
    const res = await db.prepare(sql).bind(...params).all<FtsRow>();
    return res.results;
  } catch (e) {
    const msg = errorMessage(e).toLowerCase();
    const isUserInputError =
      msg.includes("fts5") ||
      msg.includes("syntax error") ||
      msg.includes("unknown special query") ||
      msg.includes("unterminated string") ||
      msg.includes("no such column");
    if (!isUserInputError) throw e;
    return [];
  }
}

/** FR-015 part 2 rang tiers — verbatim from index/fts.py `_RANG_TIER`. */
const RANG_TIER: Readonly<Record<string, number>> = {
  laws: 0,
  codes: 0,
  regulations: 1,
  implementing: 1,
  ordinances: 1,
};

function rangTier(row: FtsRow): number {
  return RANG_TIER[row.category] ?? 2;
}

function rangTierSort(rows: FtsRow[]): FtsRow[] {
  return rows
    .map((row, i) => [row, i] as const)
    .sort((a, b) => rangTier(a[0]) - rangTier(b[0]) || a[1] - b[1])
    .map(([row]) => row);
}

/** Port of index/fts.py `search_fts` — two-tier (title-restricted, then
 * full-corpus BM25) with dedup and rang-aware stable tier sort. */
export async function searchFts(
  db: D1Database,
  query: string,
  category: string | null = null,
  limit = 20,
): Promise<FtsRow[]> {
  const normalized = bgNormalize(query);
  if (!normalized) return [];

  const tokens = normalized.split(" ").filter((t) => t);
  let titleRows: FtsRow[] = [];
  if (tokens.length > 0) {
    const titleQ = tokens.map((t) => `title:${t}`).join(" ");
    titleRows = await runMatch(db, titleQ, category, limit);
  }

  const TIER2_MIN_TITLE_HITS = 3;
  if (titleRows.length >= Math.min(limit, TIER2_MIN_TITLE_HITS)) {
    return rangTierSort([...titleRows]).slice(0, limit);
  }

  const bodyRows = await runMatch(db, normalized, category, limit);

  const seenIds = new Set(titleRows.map((r) => r.law_id));
  const merged = [...titleRows];
  for (const r of bodyRows) {
    if (seenIds.has(r.law_id)) continue;
    merged.push(r);
    seenIds.add(r.law_id);
    if (merged.length >= limit) break;
  }
  return rangTierSort(merged.slice(0, limit));
}
