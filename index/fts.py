"""FTS5 helpers and Bulgarian-aware text normalizer.

bg_normalize() is symmetric: called at both index time AND query time so
morphological variants match. Bulgarian definite-article suffixes are
stripped from word endings; lowercasing and whitespace collapse round it
out. No external NLP libs; pure Python.

Per D-022. Symmetry is mandatory — asymmetry silently breaks search.
"""

import re
import sqlite3


# Bulgarian definite-article suffixes — last-character stripping only.
#
# Strip just the trailing definite article: feminine "та", neuter "то",
# masculine "ът"/"ят" (after consonant / after specific vowels), plural
# "те". Critically, NOT stripping the longer "ите"/"ия"/"ето"/"а"
# variants — those would mangle valid base forms or break plural
# symmetry:
#   "ите" stripped: "обществените" → "обществен", but "обществени"
#     (plural indefinite — what users actually type) → "обществени".
#     The two forms diverge → search silently misses indefinite hits.
#     Stripping just "те": both reduce to "обществени". Symmetric.
#   "ето" stripped: "управлението" → "управлени" (mangled).
#   "а" stripped: "държава" → "държав" (feminine base form mangled).
#   "ия" stripped: "решения" → "реше" (plural base form mangled).
#
# All entries are 2 chars, so order doesn't change matching, but we list
# them grouped by gender/number for readability.
_BG_DEFINITE_SUFFIXES: tuple[str, ...] = (
    "ът", "ят",  # masculine
    "та",        # feminine
    "то",        # neuter
    "те",        # plural
)

# Minimum length of the stem AFTER stripping a suffix. 4 chars protects
# against catastrophic over-stripping of short words. Known asymmetry
# this introduces: adjective long-form definite (`новият` 6→`нови` 4)
# does not match indefinite (`нов` 3 chars, below threshold, returned
# unchanged). Acceptable for Phase 1b.1 (rare in legal subject position);
# tracked as FR-013 in `docs/frs/INDEX.md` for the 1b.3 stemmer milestone.
_MIN_STEM_LEN = 4
_WS_RE = re.compile(r"\s+")


def _strip_definite_article(token: str) -> str:
    if len(token) <= _MIN_STEM_LEN:
        return token
    for suffix in _BG_DEFINITE_SUFFIXES:
        if token.endswith(suffix) and len(token) - len(suffix) >= _MIN_STEM_LEN:
            return token[: -len(suffix)]
    return token


def bg_normalize(text: str | None) -> str:
    """Normalize text for symmetric FTS5 indexing/querying.

    - lowercase (Cyrillic + Latin)
    - collapse whitespace to single spaces
    - strip Bulgarian definite-article suffixes from word endings (>4 chars)
    - preserve digits and punctuation context (split on whitespace only)
    """
    if not text:
        return ""
    text = text.lower()
    text = _WS_RE.sub(" ", text).strip()
    if not text:
        return ""
    tokens = text.split(" ")
    return " ".join(_strip_definite_article(t) for t in tokens)


def create_laws_fts_table(conn: sqlite3.Connection) -> None:
    """Idempotent helper — migrations.py already creates this, but build.py
    uses this when working on a non-migrated test db."""
    conn.executescript(
        """
        CREATE VIRTUAL TABLE IF NOT EXISTS laws_fts USING fts5(
            law_id UNINDEXED,
            title,
            body,
            category UNINDEXED,
            tokenize='unicode61 remove_diacritics 2'
        );
        """
    )


def insert_fts_row(conn: sqlite3.Connection, law_id: str, title: str,
                   body: str, category: str) -> None:
    conn.execute(
        "INSERT INTO laws_fts (law_id, title, body, category) VALUES (?, ?, ?, ?)",
        (law_id, bg_normalize(title), bg_normalize(body), category),
    )


# Single-stage SELECT with snippet() on the TITLE column (FTS5 column
# index 1), not the body (index 2). Body-snippet was the perf killer:
# extracting a fragment from ЗОП's 559 KB indexed body takes ~700ms
# even with limit 20. Title-snippet runs in ~75ms and produces more
# useful "which act is this?" output for callers — body context is
# already available one tool-call away via get_law.
#
# FR-017 tracks body-snippet generation for 1b.3 (truncated-excerpt
# column or Python-side substring snippet). FR-015/FR-016 cover the
# related ranking-quality and perf-pathological-query work.
_FTS_SELECT = """
    SELECT laws_fts.law_id          AS law_id,
           laws.doc_id              AS doc_id,
           laws.title               AS title,
           laws.category            AS category,
           snippet(laws_fts, 1, '<b>', '</b>', '...', 12) AS snippet,
           bm25(laws_fts)           AS score
      FROM laws_fts
      JOIN laws USING(law_id)
     WHERE laws_fts MATCH ?
"""


def _run_match(conn: sqlite3.Connection, match_query: str,
               category: str | None, limit: int) -> list[sqlite3.Row]:
    sql = _FTS_SELECT
    params: list = [match_query]
    if category:
        sql += " AND laws.category = ?"
        params.append(category)
    sql += " ORDER BY bm25(laws_fts) LIMIT ?"
    params.append(limit)
    try:
        return conn.execute(sql, params).fetchall()
    except sqlite3.OperationalError:
        # FTS5 raises OperationalError on syntax issues (special chars,
        # empty terms after tokenization). Treat as no results.
        return []


def search_fts(conn: sqlite3.Connection, query: str,
               category: str | None = None,
               limit: int = 20) -> list[sqlite3.Row]:
    """FTS5 search with two-tier ranking: title-restricted matches
    first, body matches second.

    BM25 alone over title+body produces inverted rankings for canonical
    title queries — e.g., "обществени поръчки" puts the implementing
    regulation above ЗОП itself because the implementing reg has a
    shorter body where the terms repeat more densely. Two-tier search
    fixes the dominant case without a stemmer:
      tier 1: docs whose TITLE contains every query token (high
              precision; a doc with all query tokens in the title is
              almost always the right answer)
      tier 2: BM25 over the full corpus (recall — catches body matches
              and abbreviations like 'ЗОП' that don't appear in titles)

    Both tiers honor the optional category filter. Results are
    deduplicated by law_id (title-tier wins). FR-015 tracks the
    Phase 1b.3 stemmer + synonym dictionary that will further refine
    ranking once usage data exists.
    """
    normalized = bg_normalize(query)
    if not normalized:
        return []

    # Tier 1: column-restricted title query (e.g. "title:наказателен
    # title:кодекс"). FTS5's column qualifier requires lowercased
    # column name and the same normalized tokens.
    tokens = [t for t in normalized.split() if t]
    if tokens:
        title_q = " ".join(f"title:{t}" for t in tokens)
        title_rows = _run_match(conn, title_q, category, limit)
    else:
        title_rows = []

    # Skip tier 2 when tier 1 already filled the limit — the second
    # FTS5 query is the bigger of the two (full-corpus body match) and
    # adds ~100ms even when its results are discarded by the dedup loop.
    if len(title_rows) >= limit:
        return list(title_rows)

    # Tier 2: general FTS5 over title+body (covers abbreviations and
    # body-only matches when no title fully covers the query).
    body_rows = _run_match(conn, normalized, category, limit)

    seen_ids = {r["law_id"] for r in title_rows}
    merged = list(title_rows)
    for r in body_rows:
        if r["law_id"] in seen_ids:
            continue
        merged.append(r)
        seen_ids.add(r["law_id"])
        if len(merged) >= limit:
            break
    return merged[:limit]
