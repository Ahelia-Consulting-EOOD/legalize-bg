/** Port of mcp_server/queries.py over D1 — semantics must match the
 * Python original EXACTLY (payload key order included, since FastAPI
 * serializes dicts in insertion order and the parity gate compares
 * bodies). */

import { ToolError, type JsonValue } from "./errors";
import { searchFts } from "./fts";
import { bgNormalize } from "./normalize";
import { expandIfAbbreviation } from "./synonyms";
import { legalArticleSortKey, compareSortKeys } from "./sortkey";
import { todayISO, validateDate } from "./validation";

const MAX_QUERY_LEN = 512;
const MAX_NAME_LEN = 512;

// FR-016 / D-2026-05-09-03 category stop words.
const CATEGORY_STOP_WORDS = new Set([
  "наредба",
  "закон",
  "правилник",
  "кодекс",
  "постановление",
]);

const BODY_SNIPPET_TOP_N = 2;
const BODY_SNIPPET_HALF_WINDOW = 60;

// Python re.findall(r"\w+", ...) with full Unicode semantics.
const WORD_RE = /[\p{L}\p{N}_]+/gu;

export interface LawRow {
  law_id: string;
  doc_id: number;
  title: string;
  category: string;
  status: string;
  current_commit: string | null;
}

// ── Name resolution (§7.1) ──────────────────────────────────────────────

export async function resolveNameToLawId(db: D1Database, name: string): Promise<string> {
  if (!name || !name.trim()) {
    throw new ToolError("LAW_NOT_FOUND", { name, suggestions: [] });
  }
  name = name.trim();
  if (name.length > MAX_NAME_LEN) {
    throw new ToolError("LAW_NOT_FOUND", { name: name.slice(0, 100) + "…", suggestions: [] });
  }

  // 1. Identificador (numeric, may be negative for §7.3 phantom acts)
  if (/^-?\d+$/.test(name)) {
    const row = await db
      .prepare("SELECT law_id FROM laws WHERE doc_id = ?")
      .bind(parseInt(name, 10))
      .first<{ law_id: string }>();
    if (row) return row.law_id;
  }

  // 2. Exact slug
  const slugRow = await db
    .prepare("SELECT law_id FROM laws WHERE law_id = ?")
    .bind(name)
    .first<{ law_id: string }>();
  if (slugRow) return slugRow.law_id;

  // 3. Exact title, Cyrillic case-insensitive — folded in JS (SQLite
  // LOWER() is ASCII-only), mirroring the Python-side casefold.
  const needle = name.toLowerCase();
  const all = await db
    .prepare(
      "SELECT law_id, doc_id, title, category FROM laws WHERE title IS NOT NULL AND title <> ''",
    )
    .all<{ law_id: string; doc_id: number; title: string; category: string }>();
  const matches = all.results.filter((r) => (r.title || "").toLowerCase() === needle);
  if (matches.length === 1) return (matches[0] as { law_id: string }).law_id;
  if (matches.length > 1) {
    throw new ToolError("AMBIGUOUS_NAME", {
      name,
      candidates: matches.map((r) => ({
        law_id: r.law_id,
        identificador: String(r.doc_id),
        title: r.title,
        category: r.category,
      })),
    });
  }

  // 4. Not found — best-effort FTS suggestions for retry. searchFts
  // already suppresses FTS5 user-input syntax errors internally.
  let suggestions: JsonValue[] = [];
  const ftsRows = await searchFts(db, name, null, 5);
  suggestions = ftsRows.map((r) => ({
    law_id: r.law_id,
    title: r.title,
    relevance: -r.score,
  }));
  throw new ToolError("LAW_NOT_FOUND", { name, suggestions });
}

// ── version_at_date (§7.2) ──────────────────────────────────────────────

export interface VersionRow {
  commit_hash: string;
  valid_from: string;
}

export async function versionAtDate(
  db: D1Database,
  lawId: string,
  date: string | null,
): Promise<VersionRow> {
  const validated = validateDate(date, "date");
  const target = validated ?? todayISO();
  const row = await db
    .prepare(
      `SELECT commit_hash, valid_from FROM law_versions
           WHERE law_id = ?
             AND valid_from <= ?
             AND (valid_to IS NULL OR valid_to >= ?)
           ORDER BY valid_from DESC
           LIMIT 1`,
    )
    .bind(lawId, target, target)
    .first<VersionRow>();
  if (row) return row;
  const mm = await db
    .prepare(
      "SELECT MIN(valid_from) AS earliest, MAX(valid_from) AS latest FROM law_versions WHERE law_id = ?",
    )
    .bind(lawId)
    .first<{ earliest: string | null; latest: string | null }>();
  throw new ToolError("NO_VERSION_AT_DATE", {
    law_id: lawId,
    date: validated,
    earliest_available: mm?.earliest ?? null,
    latest_available: mm?.latest ?? null,
  });
}

export interface Warning {
  code: string;
  law_id: string;
  source_date_marker: string;
  note: string;
}

export async function versionWithWarnings(
  db: D1Database,
  lawId: string,
  date: string | null,
): Promise<{ version: VersionRow; warnings: Warning[] }> {
  const version = await versionAtDate(db, lawId, date);
  const warnings: Warning[] = [];
  const row = await db
    .prepare(
      "SELECT date_uncertain FROM law_versions WHERE law_id = ? AND commit_hash = ?",
    )
    .bind(lawId, version.commit_hash)
    .first<{ date_uncertain: number }>();
  if (row && row.date_uncertain) {
    warnings.push({
      code: "DATE_UNCERTAIN",
      law_id: lawId,
      source_date_marker: "unknown",
      note: "publication date not parseable from lex.bg; version validity falls back to bootstrap run date",
    });
  }
  return { version, warnings };
}

// ── full_text_search ────────────────────────────────────────────────────

async function makeBodySnippet(
  db: D1Database,
  lawId: string,
  terms: string[],
): Promise<string> {
  const row = await db
    .prepare("SELECT body FROM laws_fts WHERE law_id = ?")
    .bind(lawId)
    .first<{ body: string | null }>();
  if (!row) return "";
  const body = row.body || "";
  if (!body) return "";

  let earliest = -1;
  let matchedTerm = "";
  for (const term of terms) {
    const idx = body.indexOf(term);
    if (idx !== -1 && (earliest === -1 || idx < earliest)) {
      earliest = idx;
      matchedTerm = term;
    }
  }
  if (earliest === -1) return "";

  const start = Math.max(0, earliest - BODY_SNIPPET_HALF_WINDOW);
  const end = Math.min(body.length, earliest + matchedTerm.length + BODY_SNIPPET_HALF_WINDOW);
  const prefix = start > 0 ? "..." : "";
  const suffix = end < body.length ? "..." : "";
  const fragment = body.slice(start, end);
  const rel = earliest - start;
  const highlighted =
    fragment.slice(0, rel) +
    "<b>" +
    fragment.slice(rel, rel + matchedTerm.length) +
    "</b>" +
    fragment.slice(rel + matchedTerm.length);
  return `${prefix}${highlighted}${suffix}`;
}

export interface SearchHit {
  law_id: string;
  identificador: string;
  title: string;
  category: string;
  title_snippet: string;
  body_snippet: string;
  relevance: number;
}

export async function fullTextSearch(
  db: D1Database,
  query: string,
  category: string | null,
  limit: number,
  includeBody: boolean,
): Promise<SearchHit[]> {
  if (typeof query === "string" && query.length > MAX_QUERY_LEN) {
    throw new ToolError("QUERY_TOO_BROAD", {
      query: query.slice(0, 200),
      hint: `query longer than ${MAX_QUERY_LEN} chars — send a focused query`,
    });
  }

  const rawTokens = typeof query === "string" ? query.match(WORD_RE) ?? [] : [];
  if (rawTokens.length === 1 && CATEGORY_STOP_WORDS.has(bgNormalize(rawTokens[0]))) {
    throw new ToolError("QUERY_TOO_BROAD", {
      query: query.slice(0, 200),
      category_words: [...CATEGORY_STOP_WORDS].sort(),
      hint:
        "Заявката съответства на хиляди актове. Добавете " +
        'повече ключови думи (напр. "наредба за обществени ' +
        'поръчки") за по-конкретно търсене. ' +
        "Be more specific — single category words like " +
        "'наредба' match thousands of acts.",
    });
  }

  let effectiveQuery = query;
  if (rawTokens.length === 1) {
    const canonical = expandIfAbbreviation(bgNormalize(rawTokens[0]));
    if (canonical !== null) effectiveQuery = canonical;
  }

  const rows = await searchFts(db, effectiveQuery, category, limit);

  const snippetTerms = (bgNormalize(effectiveQuery).match(WORD_RE) ?? []).filter(
    (t) => t.length >= 3,
  );

  const out: SearchHit[] = [];
  for (let idx = 0; idx < rows.length; idx++) {
    const r = rows[idx]!;
    const title = r.title || `<doc_id=${r.doc_id}>`;
    let bodySnippet = "";
    if (includeBody && idx < BODY_SNIPPET_TOP_N && snippetTerms.length > 0) {
      bodySnippet = await makeBodySnippet(db, r.law_id, snippetTerms);
    }
    out.push({
      law_id: r.law_id,
      identificador: String(r.doc_id),
      title,
      category: r.category,
      title_snippet: r.snippet,
      body_snippet: bodySnippet,
      relevance: -r.score,
    });
  }
  return out;
}

// ── law_history ─────────────────────────────────────────────────────────

export interface VersionEntry {
  date: string | null;
  dv_issue: string | null;
  operation: string;
  commit_hash: string | null;
}

export async function lawHistory(db: D1Database, lawId: string): Promise<VersionEntry[]> {
  const amendRows = (
    await db
      .prepare(
        "SELECT dv_issue, dv_date, operation FROM amendments " +
          "WHERE target_law = ? ORDER BY dv_date IS NULL, dv_date",
      )
      .bind(lawId)
      .all<{ dv_issue: string | null; dv_date: string | null; operation: string }>()
  ).results;
  const entries: VersionEntry[] = amendRows.map((r) => ({
    date: r.dv_date,
    dv_issue: r.dv_issue,
    operation: r.operation,
    commit_hash: null,
  }));
  const lv = await db
    .prepare(
      "SELECT valid_from, commit_hash FROM law_versions " +
        "WHERE law_id = ? ORDER BY valid_from DESC LIMIT 1",
    )
    .bind(lawId)
    .first<{ valid_from: string; commit_hash: string }>();
  if (lv) {
    const lastDated = amendRows.map((r) => r.dv_date).filter((d): d is string => !!d);
    const heldDate = lastDated.length > 0 ? lastDated[lastDated.length - 1]! : lv.valid_from;
    entries.push({
      date: heldDate,
      dv_issue: null,
      operation: "consolidated",
      commit_hash: lv.commit_hash,
    });
  }
  return entries;
}

// ── laws / meta helpers ─────────────────────────────────────────────────

export async function lawMeta(db: D1Database, lawId: string): Promise<LawRow | null> {
  return db.prepare("SELECT * FROM laws WHERE law_id = ?").bind(lawId).first<LawRow>();
}

const MAX_LIST_LIMIT = 200;

export interface LawListResult {
  total: number;
  items: {
    law_id: string;
    identificador: string;
    title: string;
    category: string;
    status: string;
    first_version: string | null;
    latest_version: string | null;
    version_count: number;
  }[];
}

export async function listLaws(
  db: D1Database,
  category: string | null,
  estado: string | null,
  limit: number,
  offset: number,
): Promise<LawListResult> {
  limit = Math.max(1, Math.min(Math.trunc(limit), MAX_LIST_LIMIT));
  offset = Math.max(0, Math.trunc(offset));
  const where: string[] = [];
  const params: (string | number)[] = [];
  if (category) {
    where.push("l.category = ?");
    params.push(category);
  }
  if (estado) {
    where.push("l.status = ?");
    params.push(estado);
  }
  const whereSql = where.length > 0 ? "WHERE " + where.join(" AND ") : "";
  const totalRow = await db
    .prepare(`SELECT COUNT(*) AS n FROM laws l ${whereSql}`)
    .bind(...params)
    .first<{ n: number }>();
  const rows = (
    await db
      .prepare(
        `SELECT l.law_id, l.doc_id, l.title, l.category, l.status,
                   MIN(v.valid_from) AS first_version,
                   MAX(v.valid_from) AS latest_version,
                   COUNT(v.id) AS version_count
            FROM laws l LEFT JOIN law_versions v ON v.law_id = l.law_id
            ${whereSql}
            GROUP BY l.law_id ORDER BY l.title, l.law_id
            LIMIT ? OFFSET ?`,
      )
      .bind(...params, limit, offset)
      .all<{
        law_id: string;
        doc_id: number;
        title: string;
        category: string;
        status: string;
        first_version: string | null;
        latest_version: string | null;
        version_count: number;
      }>()
  ).results;
  return {
    total: totalRow?.n ?? 0,
    items: rows.map((r) => ({
      law_id: r.law_id,
      identificador: String(r.doc_id),
      title: r.title,
      category: r.category,
      status: r.status,
      first_version: r.first_version,
      latest_version: r.latest_version,
      version_count: r.version_count,
    })),
  };
}

export { legalArticleSortKey, compareSortKeys };
