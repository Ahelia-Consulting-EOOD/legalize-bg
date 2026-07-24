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



# ── FR-032 (D-056): two-index split ────────────────────────────────────
#
# `laws_fts` is TITLE-ONLY (tier-1 ranking unchanged by construction);
# `articles_fts` holds one row per body segment produced by
# index/segments.py, chunked to ≤ SEG_MAX_BYTES so no value approaches
# Cloudflare D1's 2 MB cap (which retired FTS_BODY_MAX_BYTES / spec
# v1.2). Design: docs/plans/2026-07-21-fr032-per-article-fts-design.md;
# measurements: docs/research/2026-07-23-fr032-spike.md.

from index.segments import segment_texts  # noqa: E402


def create_laws_fts_table(conn: sqlite3.Connection) -> None:
    """Idempotent helper — migrations.py already creates this, but tests
    working on a non-migrated db use it. Title-only since migration 005."""
    conn.executescript(
        """
        CREATE VIRTUAL TABLE IF NOT EXISTS laws_fts USING fts5(
            law_id UNINDEXED,
            title,
            category UNINDEXED,
            tokenize='unicode61 remove_diacritics 2'
        );
        """
    )


def create_articles_fts_table(conn: sqlite3.Connection) -> None:
    """Idempotent helper for the per-segment index (migration 005)."""
    conn.executescript(
        """
        CREATE VIRTUAL TABLE IF NOT EXISTS articles_fts USING fts5(
            law_id UNINDEXED,
            seg_no UNINDEXED,
            kind UNINDEXED,
            label UNINDEXED,
            body,
            category UNINDEXED,
            tokenize='unicode61 remove_diacritics 2'
        );
        """
    )


def create_fts_tables(conn: sqlite3.Connection) -> None:
    create_laws_fts_table(conn)
    create_articles_fts_table(conn)


def insert_title_row(conn: sqlite3.Connection, law_id: str, title: str,
                     category: str) -> None:
    conn.execute(
        "INSERT INTO laws_fts (law_id, title, category) VALUES (?, ?, ?)",
        (law_id, bg_normalize(title), category),
    )


def insert_segment_rows(conn: sqlite3.Connection, law_id: str, body: str,
                        category: str) -> None:
    """Segment `body` (index/segments.py, coverage-invariant) and write
    one articles_fts row per (possibly chunked) segment. seg_no is the
    0-based emission order; kind/label are advisory display metadata.

    Coverage gate (design §9, the D-047 lesson): the segment spans must
    tile the body exactly — contiguous, gap-free, first at 0, last at
    len(body). A violation aborts the act's indexing loudly rather than
    silently indexing partial text."""
    rows = segment_texts(body, bg_normalize)
    pos = 0
    for seg, _ in rows:
        if seg.start != pos:
            raise ValueError(
                f"{law_id}: segmentation coverage invariant violated — "
                f"gap/overlap at offset {pos} (segment starts {seg.start})")
        pos = seg.end
    if pos != len(body):
        raise ValueError(
            f"{law_id}: segmentation coverage invariant violated — spans "
            f"end at {pos}, body has {len(body)} chars")
    for seg_no, (seg, norm) in enumerate(rows):
        conn.execute(
            "INSERT INTO articles_fts (law_id, seg_no, kind, label, body,"
            " category) VALUES (?, ?, ?, ?, ?, ?)",
            (law_id, str(seg_no), seg.kind, seg.label, norm, category),
        )


# Tier-1 SELECT: snippet() on the TITLE column (index 1 — unchanged by
# the title-only recreation: law_id 0, title 1, category 2).
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

# Tier-2 phase 1 (FR-032): SCORE-ONLY overscan over articles_fts — the
# spike proved MIN(bm25) cannot run inside GROUP BY over an FTS5 aux
# function and the MATERIALIZED-CTE form pays 700–1050 ms materializing
# snippets for every matching segment on broad terms. Measured on the
# live catalog: snippet() over the 500-row window costs 425–560 ms warm
# vs 1–10 ms for bm25-only — so phase 1 fetches NO text; act-level
# aggregation happens host-side, and phase 2 below extracts snippets
# for the ≤limit winning segments only.
_SEGMENT_SCORE_SELECT = """
    SELECT articles_fts.law_id     AS law_id,
           articles_fts.seg_no     AS seg_no,
           articles_fts.kind       AS kind,
           articles_fts.label      AS label,
           articles_fts.category   AS category,
           bm25(articles_fts)      AS score
      FROM articles_fts
     WHERE articles_fts MATCH ?
"""

# Tier-2 phase 2: snippet extraction for the winning segments. SQLite
# evaluates SELECT expressions only for rows surviving the WHERE, so
# one MATCH scan with the (law_id:seg_no) allowlist computes ≤limit
# snippets. snippet() column index 4 = body (law_id 0, seg_no 1,
# kind 2, label 3, body 4, category 5).
_SEGMENT_SNIPPET_SELECT = """
    SELECT articles_fts.law_id     AS law_id,
           articles_fts.seg_no     AS seg_no,
           snippet(articles_fts, 4, '<b>', '</b>', '...', 12) AS seg_snippet
      FROM articles_fts
     WHERE articles_fts MATCH ?
       AND (articles_fts.law_id || ':' || articles_fts.seg_no) IN ({keys})
"""

# Fixed overscan window for tier 2. FIXED (not K×limit) so the breadth
# count below — and therefore every act score — is deterministic and
# independent of the caller's limit (parity + testability requirement,
# spike §2).
TIER2_OVERSCAN = 500

# Breadth-corrected best-segment score (D-056 Q1 as AMENDED 2026-07-23):
#   act_score = best_segment_bm25 − BREADTH_ALPHA · n / (n + BREADTH_SATURATION)
# where n = the act's matching segments within the overscan window.
# Plain MIN showed a measured short-segment bias (Кодекс на труда #31
# for "трудов договор", ЗАНН #6 for "административни нарушения" —
# spike §5); the saturating RATIONAL form (not ln) keeps the correction
# float-identical across CPython/libm and V8/fdlibm for cross-plane
# bm25 parity.
BREADTH_ALPHA = 4.0
BREADTH_SATURATION = 5.0


def _is_user_input_error(e: sqlite3.OperationalError) -> bool:
    """FTS5 raises OperationalError for malformed query terms — the
    error families verified empirically in plan
    docs/plans/2026-05-09-phase1b1-review-fixes.md Task 1, plus the
    historic "fts5"/"syntax error" prefixes some builds emit. Shared by
    both tiers (the consolidation the pre-FR-032 comments tracked).
    Other OperationalErrors (table missing, DB locked, corruption) must
    propagate so callers see INDEX_STALE / INDEX_MISSING instead of
    silent empty results (audit D-8 + review Issue #1)."""
    msg = str(e).lower()
    return (
        "fts5" in msg
        or "syntax error" in msg
        or "unknown special query" in msg
        or "unterminated string" in msg
        or msg.startswith("no such column")
    )


def _run_match(conn: sqlite3.Connection, match_query: str,
               category: str | None, limit: int) -> list[sqlite3.Row]:
    """Tier-1 MATCH over title-only laws_fts."""
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
        if not _is_user_input_error(e):
            raise
        return []


def _run_segment_match(conn: sqlite3.Connection, match_query: str,
                       category: str | None) -> list[sqlite3.Row]:
    """Tier-2 phase-1 MATCH over articles_fts (score-only), fixed
    TIER2_OVERSCAN window, bm25-ordered. Same user-input error contract
    as _run_match."""
    sql = _SEGMENT_SCORE_SELECT
    params: list = [match_query]
    if category:
        sql += " AND articles_fts.category = ?"
        params.append(category)
    sql += " ORDER BY bm25(articles_fts) LIMIT ?"
    params.append(TIER2_OVERSCAN)
    try:
        return conn.execute(sql, params).fetchall()
    except sqlite3.OperationalError as e:
        if not _is_user_input_error(e):
            raise
        return []


def _fetch_segment_snippets(conn: sqlite3.Connection, match_query: str,
                            keys: list[str]) -> dict[str, str]:
    """Phase 2: {'law_id:seg_no': snippet} for the winning segments."""
    if not keys:
        return {}
    sql = _SEGMENT_SNIPPET_SELECT.format(
        keys=", ".join("?" for _ in keys))
    try:
        rows = conn.execute(sql, [match_query, *keys]).fetchall()
    except sqlite3.OperationalError as e:
        if not _is_user_input_error(e):
            raise
        return {}
    return {f"{r['law_id']}:{r['seg_no']}": r["seg_snippet"] for r in rows}


def _fetch_laws_meta(conn: sqlite3.Connection,
                     law_ids: list[str]) -> dict[str, sqlite3.Row]:
    """doc_id/title for the winning acts (PK lookups; phase 1 carries
    no laws JOIN so the 500-row window stays text-free)."""
    if not law_ids:
        return {}
    sql = ("SELECT law_id, doc_id, title FROM laws WHERE law_id IN ({})"
           .format(", ".join("?" for _ in law_ids)))
    return {r["law_id"]: r
            for r in conn.execute(sql, law_ids).fetchall()}


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


def _rang_tier(hit: dict) -> int:
    return _RANG_TIER.get(hit.get("category"), 2)


def _rang_tier_sort(hits: list[dict]) -> list[dict]:
    """Stable tier sort — parent laws/codes float to the top, score
    order is preserved within each tier."""
    indexed = list(enumerate(hits))
    indexed.sort(key=lambda pair: (_rang_tier(pair[1]), pair[0]))
    return [hit for _, hit in indexed]


def _trim_title(title: str | None, max_tokens: int = 12) -> str:
    """Deterministic title fragment for tier-2 hits (whose MATCH ran on
    articles_fts, so no FTS title-snippet is available): the leading 12
    whitespace tokens, '...'-terminated when truncated — mirroring the
    v1 snippet() shape for non-matching titles."""
    if not title:
        return ""
    tokens = title.split()
    if len(tokens) <= max_tokens:
        return title
    return " ".join(tokens[:max_tokens]) + "..."


def _title_hit(row: sqlite3.Row) -> dict:
    return {
        "law_id": row["law_id"], "doc_id": row["doc_id"],
        "title": row["title"], "category": row["category"],
        "snippet": row["snippet"], "score": row["score"],
        "matched_kind": None, "matched_label": None, "seg_snippet": None,
    }


def _segment_hits(conn: sqlite3.Connection, match_query: str,
                  rows: list[sqlite3.Row], limit: int) -> list[dict]:
    """Aggregate phase-1 window rows (bm25-ordered) to act-level hits:
    first occurrence per act = its best segment; n = occurrences in the
    window; score per the breadth-corrected formula above. Then phase 2
    fetches snippets + act metadata for the top `limit` acts only."""
    order: list[str] = []
    best: dict[str, sqlite3.Row] = {}
    count: dict[str, int] = {}
    for row in rows:
        lid = row["law_id"]
        if lid not in best:
            best[lid] = row
            order.append(lid)
        count[lid] = count.get(lid, 0) + 1

    scored = []
    for lid in order:
        row = best[lid]
        n = count[lid]
        scored.append(
            (row["score"] - BREADTH_ALPHA * n / (n + BREADTH_SATURATION),
             lid, row))
    scored.sort(key=lambda t: t[0])
    winners = scored[:limit]

    keys = [f"{lid}:{row['seg_no']}" for _, lid, row in winners]
    snippets = _fetch_segment_snippets(conn, match_query, keys)
    meta = _fetch_laws_meta(conn, [lid for _, lid, _ in winners])

    hits = []
    for score, lid, row in winners:
        m = meta.get(lid)
        title = m["title"] if m else None
        hits.append({
            "law_id": lid, "doc_id": m["doc_id"] if m else None,
            "title": title, "category": row["category"],
            "snippet": _trim_title(title),
            "score": score,
            "matched_kind": row["kind"], "matched_label": row["label"],
            "seg_snippet": snippets.get(f"{lid}:{row['seg_no']}", ""),
        })
    return hits


def search_fts(conn: sqlite3.Connection, query: str,
               category: str | None = None,
               limit: int = 20) -> list[dict]:
    """Two-tier search over the FR-032 split index.

    Tier 1 (unchanged, D-051 gating): title-restricted MATCH over the
    title-only laws_fts — same documents and token statistics as v1, so
    title-tier ordering is preserved by construction.

    Tier 2 (FR-032): overscan MATCH over articles_fts, aggregated
    host-side to acts via the breadth-corrected best-segment score.
    Tier-2 hits carry matched_kind/matched_label/seg_snippet (the Q3
    additive attribution); title-tier hits carry None there.

    Results are deduplicated by law_id (title tier wins) and finish
    with the FR-015 rang-tier sort.
    """
    normalized = bg_normalize(query)
    if not normalized:
        return []

    tokens = [t for t in normalized.split() if t]
    if tokens:
        title_q = " ".join(f"title:{t}" for t in tokens)
        title_hits = [_title_hit(r)
                      for r in _run_match(conn, title_q, category, limit)]
    else:
        title_hits = []

    # Skip tier 2 when the title tier can serve the query (FR-027 /
    # D-051 — title-shaped queries are the dominant real traffic).
    _TIER2_MIN_TITLE_HITS = 3
    if len(title_hits) >= min(limit, _TIER2_MIN_TITLE_HITS):
        return _rang_tier_sort(title_hits)[:limit]

    body_hits = _segment_hits(
        conn, normalized, _run_segment_match(conn, normalized, category),
        limit)

    seen_ids = {h["law_id"] for h in title_hits}
    merged = list(title_hits)
    for h in body_hits:
        if h["law_id"] in seen_ids:
            continue
        merged.append(h)
        seen_ids.add(h["law_id"])
        if len(merged) >= limit:
            break

    return _rang_tier_sort(merged[:limit])
