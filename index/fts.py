"""FTS5 helpers and Bulgarian-aware text normalizer.

bg_normalize() is symmetric: called at both index time AND query time so
morphological variants match. Bulgarian definite-article suffixes are
stripped from word endings; lowercasing and whitespace collapse round it
out. No external NLP libs; pure Python.

Per D-022. Symmetry is mandatory — asymmetry silently breaks search.
"""

import re
import sqlite3


# Bulgarian definite-article suffixes.
#
# Strip the trailing definite article. The list is ordered longest-first
# so longer matches win (e.g. "новият" matches both 3-char "ият" and
# 2-char "ят"; the 3-char strip gives "нов", the 2-char gives "нови" —
# we want the 3-char strip).
#
# Each entry is (suffix, min_stem_len): the suffix is stripped only if
# the resulting stem has at least `min_stem_len` characters. This
# per-suffix threshold lets the canonical FR-013 case `новият → нов`
# work (stem=3) without over-stripping short demonstratives via the
# 2-char suffixes (stem=4 floor protects "това", "този", etc.).
#
# Suffixes deliberately NOT added (would break existing symmetry or
# mangle plural-noun endings):
#   "ите" — would split "обществените" → "обществен" while leaving
#     "обществени" unchanged → query/index forms diverge.
#   "ето" — would mangle "управлението" → "управлени".
#   "ия" — would mangle "решения" (plural noun) → "реше".
#   "а" — would mangle "държава" → "държав".
#
# FR-013 / D-2026-05-09-01 closed in Phase 1b.3 by adding the 3-char
# "ият" entry; the broader 3-char/2-char additions remain off-table
# because they conflict with plural-indefinite forms.
#
# Known residual gap (FR-021 / D-032, deferred from batch 2.x-a):
# masculine adjectives with a consonant stem still diverge — "българският"
# strips via "ият" to "българск", but the INDEFINITE "български" ends in a
# bare "-и" and is left intact, so query/index forms don't meet. Closing
# this needs stripping bare "-и", which mangles plural nouns ("закони",
# "поръчки") and collides with the rejected "ия"/"ите" suffixes above — a
# POS-aware morphology problem that requires a real Bulgarian stemmer.
# That conflicts with D-022 (pure-Python, no NLP libs) and needs a
# full-corpus eval harness, so it is scoped as its own effort (FR-021),
# NOT a suffix-table tweak here.
_BG_DEFINITE_SUFFIXES: tuple[tuple[str, int], ...] = (
    # 3-char (long-form) — try first.
    ("ият", 3),  # masc adj long-form definite: новият → нов  (FR-013)
    # 2-char.
    ("ът", 4),   # masc nom: градът → град
    ("ят", 4),   # masc nom variant: дъждът → дъжд
    ("та", 4),   # feminine: жената → жена
    ("то", 4),   # neuter: детето → дете
    ("те", 4),   # plural: новите → нови, обществените → обществени
)

_WS_RE = re.compile(r"\s+")


def _strip_definite_article(token: str) -> str:
    """Strip a Bulgarian definite-article suffix from `token` if one
    matches AND the stem after stripping is at least the suffix's
    minimum length. The `_BG_DEFINITE_SUFFIXES` table is ordered
    longest-first so 3-char suffixes (e.g. `ият` in `новият`) take
    priority over their 2-char prefixes (e.g. `ят`)."""
    for suffix, min_stem in _BG_DEFINITE_SUFFIXES:
        if token.endswith(suffix) and len(token) - len(suffix) >= min_stem:
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
# index 1), not the body (index 2). Body-snippet via FTS5 was the perf
# killer in 1b.1: extracting a fragment from large indexed bodies takes
# ~700ms even with limit 20. Title-snippet runs in ~75ms and produces
# useful "which act is this?" output for callers.
#
# FR-017 closed in Phase 1b.3 with an OPT-IN body-snippet path: see
# `mcp_server/queries.py:_make_body_snippet`, gated on the new
# `include_body=True` parameter on the `search` tool. Default `search`
# calls preserve the title-only behavior here. FR-015 (synonym
# expansion + rang-aware re-rank) and FR-016 (single-word category
# query reject) are also closed; remaining open deferral is FR-014
# (Phase 4 incremental rebuild).
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
    except sqlite3.OperationalError as e:
        # FTS5 raises OperationalError for malformed query terms — three
        # user-input error families verified empirically (see plan
        # docs/plans/2026-05-09-phase1b1-review-fixes.md, Task 1) plus
        # the historic "fts5"/"syntax error" prefixes some SQLite builds
        # emit:
        #   - "unknown special query: "              (lone '*' / bareword)
        #   - "unterminated string"                  (any unbalanced quote)
        #   - "no such column: ..."                  (invalid x:foo column qualifier)
        #   - "fts5: ..." / "syntax error"           (build-specific prefixes)
        # Suppress those — the user gave us a string FTS5 can't tokenize,
        # so treat as no results. Other OperationalErrors (table missing,
        # DB locked, disk full, corruption) must propagate so callers
        # see INDEX_STALE / INDEX_MISSING instead of silent empty
        # results (audit D-8 + review Issue #1). Mirrors
        # mcp_server.queries.resolve_name_to_law_id in spirit;
        # consolidating the two allowlists into a shared tuple is
        # tracked separately.
        #
        # Known limitation (reviewed Round-3): startswith("no such
        # column") would also swallow a hypothetical schema-corruption
        # case where laws.* columns are renamed/dropped. Realistic
        # exposure is near-zero (the schema is fixed code behind a
        # protected-surface preflight) but the tighter form
        # `startswith("no such column: ") and ":" in match_query`
        # would gate suppression on the user actually typing a
        # column-qualifier — fold into the consolidation work
        # mentioned above.
        msg = str(e).lower()
        is_user_input_error = (
            "fts5" in msg
            or "syntax error" in msg
            or "unknown special query" in msg
            or "unterminated string" in msg
            or msg.startswith("no such column")
        )
        if not is_user_input_error:
            raise
        return []


# FR-015 part 2 / D-2026-05-09-04: rang-aware re-rank tiers. Lower
# number = higher priority. Parent legislative instruments
# (`laws` directory = закони; `codes` = кодекси) outrank implementing
# regs / ordinances / regulations within the same query result set.
# Tier 2 is fallback for unknown categories.
_RANG_TIER: dict[str, int] = {
    "laws":         0,
    "codes":        0,
    "regulations":  1,
    "implementing": 1,
    "ordinances":   1,
}


def _rang_tier(row: sqlite3.Row) -> int:
    """Return the rang-tier for a search result row (0 = parent
    laws/codes, 1 = regulations/implementing/ordinances, 2 = unknown).
    Used as the primary sort key in search_fts's final tier sort."""
    try:
        category = row["category"]
    except (IndexError, KeyError):
        return 2
    return _RANG_TIER.get(category, 2)


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
        return _rang_tier_sort(list(title_rows))

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

    # FR-015 part 2 / D-2026-05-09-04: rang-aware tier sort. Parent
    # laws (закон / кодекс categories) outrank implementing regs /
    # ordinances within the result set. Sort is stable within each
    # tier (key = (tier, original_index)), preserving bm25 ordering
    # among same-rang results.
    return _rang_tier_sort(merged[:limit])


def _rang_tier_sort(rows: list[sqlite3.Row]) -> list[sqlite3.Row]:
    """Stable tier sort by `_rang_tier(row)` then original position —
    parent laws/codes float to the top, bm25 order is preserved within
    each tier."""
    indexed = list(enumerate(rows))
    indexed.sort(key=lambda pair: (_rang_tier(pair[1]), pair[0]))
    return [row for _, row in indexed]
