"""Pure query functions over the SQLite catalog.

Each function takes a sqlite3.Connection plus typed parameters; none has
an MCP dependency. Tools in mcp_server/server.py are thin wrappers that
catch domain exceptions and translate them into ToolError.

Caller responsibility: the connection passed in MUST have
`row_factory = sqlite3.Row` set so column-name access (`row["foo"]`) works.
The conftest fixture and the FastMCP server's connection-init code both
do this; new entry points must follow suit. (Cyrillic case-insensitive
title resolution is done in Python, NOT via a SQLite UDF — a Python-callback
UDF deadlocks under the FastMCP threadpool on the shared connection; see
`resolve_name_to_law_id` step 3.)
"""

from __future__ import annotations

import logging
import re
import sqlite3
import subprocess
from dataclasses import dataclass
from datetime import date as _date
from pathlib import Path
from typing import Any

import yaml

from index.fts import bg_normalize, search_fts
from index.synonyms import expand_if_abbreviation
from mcp_server.errors import ToolError
from mcp_server.schemas import VersionEntry, AmendmentEntry

log = logging.getLogger(__name__)


_MAX_QUERY_LEN = 512   # defensive cap: a pasted multi-MB string must not
_MAX_NAME_LEN = 512    # run through normalization/FTS5 under the DB lock

_ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _validate_date(value: str | None, param: str) -> str | None:
    """Strict ISO-8601 date validation for tool date parameters.
    None → None (meaning 'today'); anything else must be YYYY-MM-DD.
    Empty strings are INVALID (previously truthiness silently mapped
    them to 'today' — review 2026-07-02)."""
    if value is None:
        return None
    v = value.strip() if isinstance(value, str) else ""
    if not _ISO_DATE_RE.match(v):
        raise ToolError("INVALID_DATE", {
            "param": param, "value": str(value)[:50],
            "expected": "YYYY-MM-DD",
        })
    try:
        _date.fromisoformat(v)
    except ValueError:
        raise ToolError("INVALID_DATE", {
            "param": param, "value": v, "expected": "YYYY-MM-DD",
        })
    return v


# FR-016 / D-2026-05-09-03: single-word queries matching these terms
# get rejected with QUERY_TOO_BROAD before FTS5 runs. Compared after
# `bg_normalize`, so definite-article forms ("наредбата") and case
# variants ("Наредба") are caught uniformly. Multi-word queries that
# happen to start with one of these words ("наредба за ...") are NOT
# rejected — only the single-word case is pathological.
_CATEGORY_STOP_WORDS = frozenset({
    "наредба",
    "закон",
    "правилник",
    "кодекс",
    "постановление",
})


# FR-017 / D-2026-05-09-02 — body snippets are generated only for the
# top N hits to bound per-query cost. The biggest indexed bodies in
# the live catalog are 1+ MB (e.g. naredba-za-kachestvoto-na-...
# at 1.26 MB; kodeks-za-zastrahovaneto at 1.05 MB). Fetching one of
# those rows from SQLite takes ~50 ms because the entire row is
# materialized into Python regardless of substr() because of FTS5's
# storage layout. With N=2 the worst-case per-search overhead is
# ~100 ms — comfortably within the 250 ms cold-call search budget
# while still giving the model body context for the most likely
# answers. Phase 1b.3 chose N=2 over N=5 after a 5x cost overrun
# during integration testing (508 ms warm p95 vs 100 ms budget).
_BODY_SNIPPET_TOP_N = 2

# Half-window in characters around the matched token. ±60 chars gives
# the model a sentence-sized fragment without ballooning the response
# payload (max ~120 chars per snippet × _BODY_SNIPPET_TOP_N = ~240
# chars total per search call when include_body=True).
_BODY_SNIPPET_HALF_WINDOW = 60


def _make_body_snippet(conn: sqlite3.Connection, law_id: str,
                      terms: list[str]) -> str:
    """Return a Python-extracted body fragment around the first
    occurrence of any term in `terms` within the act's indexed body.

    Falls back to the empty string if:
      - The body row is missing or empty.
      - None of the terms appear in the body.

    Highlights the matched term with `<b>...</b>` to match the
    title-snippet convention. The body in laws_fts is bg_normalize-d
    (lowercased), so the lookup is on the lowercased input; the
    returned fragment shows the body verbatim (lowercased) with the
    match wrapped.
    """
    row = conn.execute(
        "SELECT body FROM laws_fts WHERE law_id = ?", (law_id,)
    ).fetchone()
    if not row:
        return ""
    body = row["body"] or ""
    if not body:
        return ""

    # Find the earliest occurrence of any term. The body in laws_fts
    # is already lowercased by insert_fts_row; terms are also
    # lowercased by bg_normalize, so direct .find() is sufficient.
    earliest = -1
    matched_term = ""
    for term in terms:
        idx = body.find(term)
        if idx != -1 and (earliest == -1 or idx < earliest):
            earliest = idx
            matched_term = term

    if earliest == -1:
        return ""

    start = max(0, earliest - _BODY_SNIPPET_HALF_WINDOW)
    end = min(len(body), earliest + len(matched_term)
              + _BODY_SNIPPET_HALF_WINDOW)

    prefix = "..." if start > 0 else ""
    suffix = "..." if end < len(body) else ""

    fragment = body[start:end]
    rel = earliest - start
    highlighted = (
        fragment[:rel]
        + "<b>"
        + fragment[rel:rel + len(matched_term)]
        + "</b>"
        + fragment[rel + len(matched_term):]
    )
    return f"{prefix}{highlighted}{suffix}"


# ────────────────────────────── Article spec parser ─────────────────────────

@dataclass(frozen=True)
class ArticleSpec:
    article: str
    paragraph: str | None
    range_end: str | None


class InvalidArticleSpec(ValueError):
    pass


_ART_RE = r"(\d+[а-я]?)"
_RANGE_RE = rf"\s*-\s*(\d+[а-я]?)"

_FULL_RE = re.compile(
    rf"^\s*(?:чл\.\s*)?{_ART_RE}(?:{_RANGE_RE}|(?:[\.,]\s*ал\.\s*|\s+ал\.\s*|\.)(\d+[а-я]?))?\s*$",
    flags=re.IGNORECASE,
)


def parse_article_spec(spec: str) -> ArticleSpec:
    """Parse Bulgarian article reference into structured spec."""
    if not spec or not spec.strip():
        raise InvalidArticleSpec(f"empty spec: {spec!r}")
    m = _FULL_RE.match(spec)
    if not m:
        raise InvalidArticleSpec(f"could not parse: {spec!r}")
    article, range_end, paragraph = m.group(1), m.group(2), m.group(3)
    return ArticleSpec(article=article, paragraph=paragraph, range_end=range_end)


# ────────────────────────────── Name resolver (§7.1) ────────────────────────


class LawNotFound(LookupError):
    def __init__(self, name: str, suggestions: list[dict] | None = None):
        super().__init__(f"law not found: {name!r}")
        self.name = name
        self.suggestions = suggestions or []


class AmbiguousName(LookupError):
    def __init__(self, name: str, candidates: list[dict]):
        super().__init__(
            f"ambiguous name: {name!r} matches {len(candidates)} acts"
        )
        self.name = name
        self.candidates = candidates


def _row_to_candidate(row: sqlite3.Row) -> dict:
    return {
        "law_id": row["law_id"],
        "identificador": str(row["doc_id"]),
        "title": row["title"],
        "category": row["category"],
    }


def resolve_name_to_law_id(conn: sqlite3.Connection, name: str) -> str:
    """Resolve a free-form name to a unique law_id.

    Resolution order: identificador (numeric) → exact slug → exact
    title (case-insensitive). Multiple matches at the title step raise
    AmbiguousName with all candidates including identificador (the
    stable disambiguating handle per §7.1). No match → LawNotFound with
    up to 5 FTS-based suggestions so the model has something to retry.
    """
    if not name or not name.strip():
        raise LawNotFound(name=name)
    name = name.strip()
    if len(name) > _MAX_NAME_LEN:
        raise LawNotFound(name=name[:100] + "…")

    # 1. Identificador (numeric, may be negative for §7.3 phantom acts)
    if re.fullmatch(r"-?\d+", name):
        row = conn.execute(
            "SELECT law_id FROM laws WHERE doc_id = ?", (int(name),)
        ).fetchone()
        if row:
            return row["law_id"]

    # 2. Exact slug
    row = conn.execute(
        "SELECT law_id FROM laws WHERE law_id = ?", (name,)
    ).fetchone()
    if row:
        return row["law_id"]

    # 3. Exact title, Cyrillic case-insensitive (FR-019). SQLite's
    # built-in LOWER()/NOCASE are ASCII-only and do NOT fold Cyrillic.
    # We fold case in PYTHON over the candidate rows rather than via a
    # SQLite UDF: a Python-callback UDF invoked during statement
    # execution deadlocks under FastMCP's worker-thread pool on the
    # single shared (check_same_thread=False) connection — a GIL ↔
    # connection-mutex lock-order inversion (the UDF re-acquires the GIL
    # while holding the connection mutex, while another worker holds the
    # GIL and waits for that mutex). Folding in Python keeps no callback
    # inside SQLite, so concurrent title lookups can't wedge. This step
    # is the fallback (after identificador + exact slug) and the catalog
    # is a few thousand short titles, so the full read is sub-10 ms.
    needle = name.casefold()
    rows = [
        r for r in conn.execute(
            "SELECT law_id, doc_id, title, category FROM laws "
            "WHERE title IS NOT NULL AND title <> ''"
        ).fetchall()
        if (r["title"] or "").casefold() == needle
    ]
    if len(rows) == 1:
        return rows[0]["law_id"]
    if len(rows) > 1:
        raise AmbiguousName(
            name=name,
            candidates=[_row_to_candidate(r) for r in rows],
        )

    # 4. Not found — best-effort FTS suggestions for retry
    suggestions: list[dict] = []
    try:
        fts_rows = search_fts(conn, name, limit=5)
        suggestions = [
            {"law_id": r["law_id"], "title": r["title"],
             # Negated bm25: higher = better, matching full_text_search's
             # `relevance` field convention.
             "relevance": -float(r["score"])}
            for r in fts_rows
        ]
    except sqlite3.OperationalError as e:
        # FTS5 raises OperationalError for malformed queries (special
        # chars like '*', ':', unbalanced quotes). Suppress those —
        # the user gave us a search string we can't tokenize, suggestions
        # are best-effort. Other OperationalErrors (DB locked, disk
        # full, corruption) must propagate so they're not silently
        # swallowed.
        if "fts5" not in str(e).lower() and "syntax error" not in str(e).lower():
            raise
    raise LawNotFound(name=name, suggestions=suggestions)


# ────────────────────────────── version_at_date (§7.2) ──────────────────────


class NoVersionAtDate(LookupError):
    def __init__(self, law_id: str, date: str | None,
                 earliest_available: str | None = None,
                 latest_available: str | None = None):
        super().__init__(f"no version of {law_id} at date {date}")
        self.law_id = law_id
        self.date = date
        self.earliest_available = earliest_available
        self.latest_available = latest_available


def _earliest_latest(conn: sqlite3.Connection, law_id: str) -> tuple[str | None, str | None]:
    row = conn.execute(
        "SELECT MIN(valid_from), MAX(valid_from) FROM law_versions WHERE law_id = ?",
        (law_id,),
    ).fetchone()
    return row[0], row[1]


def version_at_date(conn: sqlite3.Connection, law_id: str,
                    date: str | None) -> str:
    """Return the commit_hash valid at `date` (or current if None).

    `valid_to` is INCLUSIVE per `docs/data/schema-reference.md` §2
    ("Predicate semantics") — a version with valid_to='2020-12-31' is in
    force ON 2020-12-31. So the in-force predicate is `valid_from <= date
    AND (valid_to IS NULL OR valid_to >= date)` (NOT `>`, which would
    exclude the boundary day).

    Raises NoVersionAtDate if the date is before the earliest valid_from
    or the law_id has no versions at all. Raises INVALID_DATE (via
    `_validate_date`) if `date` is malformed or an empty string.
    """
    date = _validate_date(date, "date")
    target = date or _date.today().isoformat()
    row = conn.execute(
        """SELECT commit_hash FROM law_versions
           WHERE law_id = ?
             AND valid_from <= ?
             AND (valid_to IS NULL OR valid_to >= ?)
           ORDER BY valid_from DESC
           LIMIT 1""",
        (law_id, target, target),
    ).fetchone()
    if row:
        return row["commit_hash"]
    earliest, latest = _earliest_latest(conn, law_id)
    raise NoVersionAtDate(
        law_id=law_id, date=date,
        earliest_available=earliest, latest_available=latest,
    )


def version_with_warnings(conn: sqlite3.Connection, law_id: str,
                          date: str | None) -> tuple[str, list[dict]]:
    """Same as `version_at_date` but also returns warnings.

    §7.2 detection: reads the persisted `date_uncertain` flag set by
    `index.build` when fecha_publicacion was null at index time. Reading
    a column (instead of comparing valid_from to today() at query time)
    keeps the warning stable across days and rebuilds.
    """
    commit = version_at_date(conn, law_id, date)
    warnings: list[dict] = []
    row = conn.execute(
        "SELECT date_uncertain FROM law_versions "
        "WHERE law_id = ? AND commit_hash = ?",
        (law_id, commit),
    ).fetchone()
    if row and row["date_uncertain"]:
        warnings.append({
            "code": "DATE_UNCERTAIN",
            "law_id": law_id,
            "source_date_marker": "unknown",
            "note": (
                "publication date not parseable from lex.bg; "
                "version validity falls back to bootstrap run date"
            ),
        })
    return commit, warnings


# ────────────────────────────── full_text_search + article_lookup ──────────


class ArticleNotFound(LookupError):
    def __init__(self, law_id: str, article: str, paragraph: str | None,
                 available_articles: list[str] | None = None):
        super().__init__(f"article {article} not found in {law_id}")
        self.law_id = law_id
        self.article = article
        self.paragraph = paragraph
        self.available_articles = available_articles or []


def _legal_article_sort_key(article: str) -> tuple:
    """Sort key for Bulgarian article numbers: '1', '2', …, '14',
    '14а', '14б', …, '15', …, '100'. Pure text-sort gives the
    confusing order '1','10','100','11',…,'14','14а','14б',…,'9'."""
    m = re.match(r"^(\d+)([а-я]*)$", article)
    if not m:
        return (10**9, article)  # unparseable trails
    return (int(m.group(1)), m.group(2))


def full_text_search(conn: sqlite3.Connection, query: str,
                     category: str | None = None,
                     limit: int = 20,
                     include_body: bool = False) -> list[dict]:
    """FTS5 search; symmetric bg_normalize is applied inside search_fts.

    Substitutes `<doc_id=N>` in the `title` slot for §7.3 phantom acts
    (empty titulo) so callers get a non-blank display string.

    Output `relevance` is the negated bm25 score so higher = better
    match (the SQLite bm25() function returns negative-where-lower-is-
    better; exposing the raw value would surprise callers who expect
    the conventional "higher is better" ordering).

    Output `title_snippet` is a highlighted title fragment, not body.
    See SearchHit docstring + FR-017 for the 1b.3 body-snippet rework.

    Single-word category queries (`наредба`, `закон`, `правилник`,
    `кодекс`, `постановление`) match thousands of acts each (2,604
    ordinances for "наредба" alone) and produce 400+ ms cold-call
    latency on FTS5 — outside the 100 ms p95 budget. These are
    rejected with a `QUERY_TOO_BROAD` ToolError before FTS5 is even
    invoked (FR-016 / D-2026-05-09-03). The reject tokenizes the
    bg_normalize-d query via `re.findall(r"\\w+", ...)` (alphanumeric
    runs only, ignoring punctuation), then checks `len(tokens) == 1
    and tokens[0] in _CATEGORY_STOP_WORDS`. This catches:
      - "наредба" (canonical case)
      - "наредба—", "наредба.", "наредба*" (trailing punct)
      - "законът", "наредбата" (definite-article forms — bg_normalize
        symmetric stripping reduces them)
      - "  наредба  ", "НАРЕДБА" (whitespace + case variants)
    Multi-word queries "наредба за обществени" are NOT rejected
    (tokens=3); two-stop-word conjunctions like "наредба—правилник"
    are also NOT rejected (tokens=2 — the two-tier FTS5 ranker handles
    the AND efficiently).

    FR-015 / D-2026-05-09-04 closed in Phase 1b.3: single-token
    abbreviation queries (`ЗОП`, `НК`, `ГПК`, etc. — see
    `index/synonyms.LEGAL_ABBREVIATIONS` for the full list) are
    rewritten to their canonical long form before FTS5 runs. Multi-word
    queries pass through unchanged.
    """
    # Defensive length cap (review 2026-07-02 P2): a pasted multi-MB
    # string must not run through tokenization/FTS5 under the DB lock.
    # Checked before anything else in this function.
    if isinstance(query, str) and len(query) > _MAX_QUERY_LEN:
        raise ToolError("QUERY_TOO_BROAD", {
            "query": query[:200],
            "hint": f"query longer than {_MAX_QUERY_LEN} chars — send a focused query",
        })

    # FR-016 single-word category-query reject. Round-4 review (Issue
    # #1) caught a v1 bypass: `bg_normalize(q).strip() in STOP_WORDS`
    # missed punctuation suffixes like "наредба—" because bg_normalize
    # doesn't strip punctuation, and missed "законът—" because
    # bg_normalize's suffix-stripping looks at the trailing character
    # which is the em-dash, not the actual letter suffix.
    #
    # The fix: tokenize the raw query FIRST (extract alphanumeric runs
    # only), THEN bg_normalize each token. This naturally handles
    # punctuation, mixed case, AND definite-article-plus-punctuation
    # combinations. Multi-word queries (tokens > 1) skip the reject;
    # the two-tier FTS5 ranker handles them efficiently.
    raw_tokens = re.findall(r"\w+", query) if isinstance(query, str) else []
    if len(raw_tokens) == 1 and bg_normalize(raw_tokens[0]) in _CATEGORY_STOP_WORDS:
        raise ToolError(
            "QUERY_TOO_BROAD",
            {
                # Truncate the input echo to bound payload size against
                # accidentally-large client inputs (Round-4 Minor #11).
                "query": query[:200] if isinstance(query, str) else "",
                "category_words": sorted(_CATEGORY_STOP_WORDS),
                "hint": (
                    "Заявката съответства на хиляди актове. Добавете "
                    "повече ключови думи (напр. \"наредба за обществени "
                    "поръчки\") за по-конкретно търсене. "
                    "Be more specific — single category words like "
                    "'наредба' match thousands of acts."
                ),
            },
        )

    # FR-015 synonym expansion: single-token abbreviation queries get
    # rewritten to their canonical long form before FTS5 sees them.
    # Multi-word queries pass through unchanged (the user provided
    # context). The expanded form is what FTS5 indexes via the title
    # column, so the rewrite turns "ЗОП" into a hit on
    # "Закон за обществените поръчки". Reuses raw_tokens from the
    # FR-016 pass above — no double regex work.
    effective_query = query
    if isinstance(query, str) and len(raw_tokens) == 1:
        normalized_token = bg_normalize(raw_tokens[0])
        canonical = expand_if_abbreviation(normalized_token)
        if canonical is not None:
            effective_query = canonical

    rows = search_fts(conn, effective_query, category=category, limit=limit)

    # FR-017 / D-2026-05-09-02: Python-side body snippet for the top
    # _BODY_SNIPPET_TOP_N results. Tokens are extracted from the
    # bg_normalize-d effective query (which already includes any
    # synonym expansion). 3-char minimum to avoid noise from very
    # short terms.
    snippet_terms = [
        t for t in re.findall(r"\w+", bg_normalize(effective_query))
        if len(t) >= 3
    ]

    out: list[dict] = []
    for idx, r in enumerate(rows):
        title = r["title"] or f"<doc_id={r['doc_id']}>"
        body_snippet = ""
        # Body-snippet generation is opt-in: each fetch reads a full
        # 100KB-1MB body row from FTS5 and the catalog's largest acts
        # (kodeks-za-zastrahovaneto, naredba-za-kachestvoto, etc.) blow
        # the 100 ms warm-search budget at any TOP_N > 0. Callers that
        # need body context pass include_body=True and accept the
        # extra latency; the default preserves the 1b.2 hard budget.
        if include_body and idx < _BODY_SNIPPET_TOP_N and snippet_terms:
            body_snippet = _make_body_snippet(conn, r["law_id"],
                                              snippet_terms)
        out.append({
            "law_id": r["law_id"],
            "identificador": str(r["doc_id"]),
            "title": title,
            "category": r["category"],
            "title_snippet": r["snippet"],
            "body_snippet": body_snippet,
            "relevance": -float(r["score"]),
        })
    return out


def article_lookup(conn: sqlite3.Connection, law_id: str,
                   article: str, paragraph: str | None,
                   date: str | None) -> list[dict]:
    """Return provision row(s) for a law/article/paragraph at a date.

    If `paragraph` is None, returns the article-as-whole row.
    If `paragraph` is set, returns just that alinea row.
    Raises ArticleNotFound (with `available_articles` for retry) if no
    matching row exists.

    `valid_to` is INCLUSIVE per `docs/data/schema-reference.md` §2
    ("Predicate semantics"), so the in-force predicate is
    `valid_to >= date` (NOT `>`).

    Raises INVALID_DATE (via `_validate_date`) if `date` is malformed
    or an empty string — added for direct-call safety even though
    callers normally pass an already-validated value through
    `version_at_date`.
    """
    date = _validate_date(date, "date")
    target = date or _date.today().isoformat()
    sql = """
        SELECT article, paragraph, text, text_hash, valid_from, valid_to
          FROM provisions
         WHERE law_id = ? AND article = ?
           AND valid_from <= ?
           AND (valid_to IS NULL OR valid_to >= ?)
    """
    params: list = [law_id, article, target, target]
    if paragraph is None:
        sql += " AND paragraph IS NULL"
    else:
        sql += " AND paragraph = ?"
        params.append(paragraph)
    rows = conn.execute(sql, params).fetchall()
    if not rows:
        # Sort available articles in legal-number order so '14а' follows
        # '14' rather than '15' (text sort is misleading for retry).
        raw_articles = [r["article"] for r in conn.execute(
            "SELECT DISTINCT article FROM provisions WHERE law_id = ?",
            (law_id,),
        ).fetchall()]
        avail = sorted(raw_articles, key=_legal_article_sort_key)
        raise ArticleNotFound(law_id=law_id, article=article,
                              paragraph=paragraph, available_articles=avail)
    return [dict(r) for r in rows]


def articles_lookup(conn: sqlite3.Connection, law_id: str,
                    start: str, end: str, date: str | None) -> list[dict]:
    """Return article-as-whole provision rows for every article in the law
    whose legal-number sort key falls within [start, end] inclusive,
    ordered legally (FR-018 range expansion).

    A range addresses WHOLE articles only (paragraph IS NULL); ranges never
    carry an alinea (the parser's `_FULL_RE` makes range and `ал.`
    mutually exclusive). Cyrillic-suffixed articles inside the numeric span
    are included — `чл. 14-16` returns `14, 14а, 14б, 15, 16` if present.
    Gaps are skipped (an agent asking 14-16 wants whatever exists).

    Raises ArticleNotFound (with `available_articles` for retry, and
    `article` set to the `"start-end"` span) when no article in the act
    falls in the range at `date`. `valid_to` is INCLUSIVE per
    `docs/data/schema-reference.md` §2. Raises INVALID_DATE (via
    `_validate_date`) if `date` is malformed or an empty string — added
    for direct-call safety even though callers normally pass an
    already-validated value through `version_at_date`.
    """
    date = _validate_date(date, "date")
    target = date or _date.today().isoformat()
    lo = _legal_article_sort_key(start)
    hi = _legal_article_sort_key(end)
    if lo > hi:
        # Reversed range (e.g. "16-14"): the parser accepts it, but it can
        # never match. Raise InvalidArticleSpec (→ INVALID_ARTICLE_SPEC with
        # a hint) rather than the misleading ARTICLE_NOT_FOUND an empty
        # match would give — mirrors the INVALID_DATE_RANGE guards on
        # diff()/amendments_in_period().
        raise InvalidArticleSpec(
            f"reversed range: start {start!r} is after end {end!r}")
    rows = conn.execute(
        """SELECT article, paragraph, text, text_hash, valid_from, valid_to
             FROM provisions
            WHERE law_id = ? AND paragraph IS NULL
              AND valid_from <= ?
              AND (valid_to IS NULL OR valid_to >= ?)""",
        (law_id, target, target),
    ).fetchall()
    in_range = [r for r in rows
                if lo <= _legal_article_sort_key(r["article"]) <= hi]
    in_range.sort(key=lambda r: _legal_article_sort_key(r["article"]))
    if not in_range:
        raw_articles = [r["article"] for r in conn.execute(
            "SELECT DISTINCT article FROM provisions WHERE law_id = ?",
            (law_id,),
        ).fetchall()]
        raise ArticleNotFound(
            law_id=law_id, article=f"{start}-{end}", paragraph=None,
            available_articles=sorted(raw_articles, key=_legal_article_sort_key),
        )
    return [dict(r) for r in in_range]


# ────────────────────────────── law_history (Phase 2 timeline) ──────────────


def law_history(conn: sqlite3.Connection, law_id: str) -> list[VersionEntry]:
    """Return the act's version timeline, oldest→newest.

    Amendment events come from the `amendments` table (populated from
    amendment_history at build time). Each historical event carries
    commit_hash=None — we know the act was amended on that DV date but
    don't hold a separate text snapshot for it. A final
    operation='consolidated' entry carries the real commit of the held
    current text. Honest semantics per the Phase 2 design: never imply
    we hold historical text we don't have.
    """
    amend_rows = conn.execute(
        "SELECT dv_issue, dv_date, operation FROM amendments "
        "WHERE target_law = ? ORDER BY dv_date IS NULL, dv_date",
        (law_id,),
    ).fetchall()
    entries: list[VersionEntry] = [
        VersionEntry(date=r["dv_date"], dv_issue=r["dv_issue"],
                     operation=r["operation"], commit_hash=None)
        for r in amend_rows
    ]
    lv = conn.execute(
        "SELECT valid_from, commit_hash FROM law_versions "
        "WHERE law_id = ? ORDER BY valid_from DESC LIMIT 1",
        (law_id,),
    ).fetchone()
    if lv:
        last_dated = [r["dv_date"] for r in amend_rows if r["dv_date"]]
        # The held consolidated text reflects all amendments through the most
        # recent, so it is dated to that last amendment date (or
        # law_versions.valid_from when the act was never amended).
        held_date = last_dated[-1] if last_dated else lv["valid_from"]
        entries.append(VersionEntry(
            date=held_date, dv_issue=None,
            operation="consolidated", commit_hash=lv["commit_hash"]))
    return entries


def amendments_in_period(conn: sqlite3.Connection, from_date: str,
                         to_date: str) -> list[AmendmentEntry]:
    """Return every dated amendment event across the corpus whose DV
    date falls within [from_date, to_date] inclusive, oldest first.

    Raises INVALID_DATE_RANGE (directly, like full_text_search's
    QUERY_TOO_BROAD) when from_date > to_date. Raises INVALID_DATE if
    either date is malformed, empty, or missing — both are required for
    this tool (unlike `date` elsewhere, which defaults to "today" on
    None).
    """
    from_date = _validate_date(from_date, "from_date")
    to_date = _validate_date(to_date, "to_date")
    if from_date is None or to_date is None:
        raise ToolError("INVALID_DATE", {
            "param": "from_date/to_date", "value": "null",
            "expected": "YYYY-MM-DD",
        })
    if from_date and to_date and from_date > to_date:
        raise ToolError("INVALID_DATE_RANGE",
                        {"from_date": from_date, "to_date": to_date})
    rows = conn.execute(
        """SELECT a.target_law AS law_id, l.title AS title,
                  a.dv_date AS date, a.dv_issue AS dv_issue
             FROM amendments a
             JOIN laws l ON l.law_id = a.target_law
            WHERE a.dv_date IS NOT NULL
              AND a.operation = 'amendment'
              AND a.dv_date >= ? AND a.dv_date <= ?
            ORDER BY a.dv_date, a.target_law""",
        (from_date, to_date),
    ).fetchall()
    return [
        AmendmentEntry(
            law_id=r["law_id"],
            title=r["title"] or f"<doc_id-unknown:{r['law_id']}>",
            date=r["date"], dv_issue=r["dv_issue"])
        for r in rows
    ]


def diff_law_versions(conn: sqlite3.Connection, corpus_root: Path,
                      law_id: str, date1: str, date2: str) -> str:
    """Return a `git diff` of the act's text between the versions in
    force at date1 and date2.

    When both dates resolve to the same commit (the common case until a
    write-side accumulates more versions), returns a clear bilingual
    "single consolidated version held" note instead of an empty diff —
    so the model doesn't mistake "no diff" for "no data".

    Raises INVALID_DATE_RANGE on a reversed range. Raises INVALID_DATE
    if either date is malformed or an empty string. Propagates
    NoVersionAtDate (from version_at_date) for the server tool to map
    to NO_VERSION_AT_DATE.
    """
    date1 = _validate_date(date1, "date1")
    date2 = _validate_date(date2, "date2")
    if date1 and date2 and date1 > date2:
        raise ToolError("INVALID_DATE_RANGE",
                        {"from_date": date1, "to_date": date2})
    commit1 = version_at_date(conn, law_id, date1)
    commit2 = version_at_date(conn, law_id, date2)
    if commit1 == commit2:
        return (
            f"Хранилището съдържа една консолидирана версия на '{law_id}'; "
            f"няма записана текстова промяна между {date1} и {date2}. / "
            f"The corpus holds one consolidated version of '{law_id}'; "
            f"no textual change is recorded between {date1} and {date2}."
        )
    cat_row = conn.execute(
        "SELECT category FROM laws WHERE law_id = ?", (law_id,)
    ).fetchone()
    if cat_row is None:
        raise ToolError("LAW_NOT_FOUND", {"name": law_id, "suggestions": []})
    rel_path = f"{cat_row['category']}/{law_id}.md"
    try:
        out = subprocess.run(
            ["git", "diff", commit1, commit2, "--", rel_path],
            cwd=corpus_root, check=True, capture_output=True, text=True,
        )
    except subprocess.CalledProcessError as e:
        raise ToolError("DIFF_FAILED", {
            "law_id": law_id,
            "detail": (e.stderr or "").strip()[:300] or f"git diff exited {e.returncode}",
        })
    return out.stdout


# ─────────────── catalog-error detection (PR review fix #1) ────────────────
# Relocated from mcp_server/server.py (was _SQLITE_CATALOG_ERRORS /
# _is_catalog_error) so both transports recognize a catalog-level
# sqlite3.OperationalError (missing/corrupt schema) with the identical
# predicate. server.py keeps its old private name as an aliased import;
# api/errors.py imports the public name directly for the REST
# INDEX_MISSING (503) exception handler.

_SQLITE_CATALOG_ERRORS = ("no such table", "no such column",
                          "unable to open database",
                          "database disk image is malformed",
                          "file is not a database")


def is_catalog_error(e: sqlite3.OperationalError) -> bool:
    """Catalog-level OperationalErrors (schema missing/corrupt) — as
    opposed to FTS5 user-input syntax errors, which queries/index.fts
    already suppress before reaching the tool wrapper."""
    msg = str(e).lower()
    return any(marker in msg for marker in _SQLITE_CATALOG_ERRORS)


# ────────────────────────────── Composition helpers (FR-028) ────────────────
# Relocated from mcp_server/server.py (was _read_law_markdown/_split_
# frontmatter/_law_meta/_iso) so the REST API layer (Tasks 3-8) can call
# them without importing the MCP server module. server.py keeps the old
# private names as aliased imports so its call sites stay untouched.


def read_law_markdown(corpus_root: Path, law_id: str, category: str,
                       commit_hash: str, current_commit: str) -> str:
    """Return the full Markdown (frontmatter + body) for the law at the
    given commit. Working-tree fast path when commit_hash ==
    current_commit; historical versions go through `git show`.

    Read failures surface as INDEX_STALE (structured, actionable): a
    missing working-tree file or an unreachable commit both mean the
    catalog no longer matches the corpus — re-run `python -m index.build`
    (review 2026-07-02; previously leaked OSError/CalledProcessError).
    """
    rel_path = f"{category}/{law_id}.md"
    rebuild_hint = ("catalog and corpus have diverged — re-run "
                    "`python -m index.build` against this corpus")
    if commit_hash == current_commit:
        path = corpus_root / rel_path
        try:
            return path.read_text(encoding="utf-8")
        except OSError as e:
            raise ToolError("INDEX_STALE", {
                "law_id": law_id,
                "detail": f"indexed file unreadable: {rel_path} ({e})",
                "hint": rebuild_hint,
            })
    try:
        out = subprocess.run(
            ["git", "show", f"{commit_hash}:{rel_path}"],
            cwd=corpus_root, check=True, capture_output=True, text=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError, OSError) as e:
        stderr = (getattr(e, "stderr", "") or "").strip()
        raise ToolError("INDEX_STALE", {
            "law_id": law_id,
            "commit_hash": commit_hash,
            "detail": stderr[:300] or str(e),
            "hint": rebuild_hint,
        })
    return out.stdout


def split_frontmatter(raw: str) -> tuple[dict, str]:
    """Split a Markdown file with YAML frontmatter into (frontmatter, body).
    Mirrors `index.build._parse_md` so the read path matches the write
    path; if the corpus invariant changes, both fix together.

    Behavior on missing `---\\n` prefix: returns ({}, raw) and emits a
    WARN log. The build path raises on missing frontmatter; the query
    path doesn't, because the working-tree fast path may legitimately
    encounter a hand-edited file mid-edit. Without the WARN, an operator
    could silently get titulo="" / eli=None responses (audit D-9).
    """
    if not raw.startswith("---\n"):
        log.warning(
            "frontmatter delimiter '---' missing at start of markdown; "
            "returning empty frontmatter dict (working-tree may be dirty "
            "or the file is hand-edited — re-run index.build if so)"
        )
        return {}, raw
    after_open = raw[4:]
    parts = after_open.split("\n---\n", 1)
    fm = yaml.safe_load(parts[0]) or {}
    body = parts[1] if len(parts) > 1 else ""
    return fm, body.lstrip("\n")


def law_meta(conn: sqlite3.Connection, law_id: str) -> dict:
    row = conn.execute(
        "SELECT * FROM laws WHERE law_id = ?", (law_id,)
    ).fetchone()
    return dict(row) if row else {}


def iso_date(v: Any) -> str | None:
    """Coerce date-like YAML value to ISO string (PyYAML may yield
    datetime.date for ISO date fields)."""
    if v is None:
        return None
    if hasattr(v, "isoformat"):
        return v.isoformat()
    return str(v)


_MAX_LIST_LIMIT = 200


def list_laws(conn: sqlite3.Connection, category: str | None = None,
              estado: str | None = None, limit: int = 50,
              offset: int = 0) -> dict:
    """Paginated act listing for the REST API (FR-028).

    Returns {"total": N, "items": [...]}; `total` counts ALL rows
    matching the filters (pagination-independent, so a UI can render
    page controls). Dates come from `law_versions` (min/max valid_from),
    not from frontmatter reads — a list endpoint must not open 3,601
    files.
    """
    limit = max(1, min(int(limit), _MAX_LIST_LIMIT))
    offset = max(0, int(offset))
    where, params = [], []
    if category:
        where.append("l.category = ?")
        params.append(category)
    if estado:
        where.append("l.status = ?")
        params.append(estado)
    where_sql = ("WHERE " + " AND ".join(where)) if where else ""
    total = conn.execute(
        f"SELECT COUNT(*) FROM laws l {where_sql}", params).fetchone()[0]
    rows = conn.execute(
        f"""SELECT l.law_id, l.doc_id, l.title, l.category, l.status,
                   MIN(v.valid_from) AS first_version,
                   MAX(v.valid_from) AS latest_version,
                   COUNT(v.id) AS version_count
            FROM laws l LEFT JOIN law_versions v ON v.law_id = l.law_id
            {where_sql}
            GROUP BY l.law_id ORDER BY l.title, l.law_id
            LIMIT ? OFFSET ?""",
        params + [limit, offset]).fetchall()
    items = [{
        "law_id": r["law_id"], "identificador": str(r["doc_id"]),
        "title": r["title"], "category": r["category"],
        "status": r["status"], "first_version": r["first_version"],
        "latest_version": r["latest_version"],
        "version_count": r["version_count"],
    } for r in rows]
    return {"total": total, "items": items}


def corpus_stats(conn: sqlite3.Connection) -> dict:
    """Corpus stats for GET /api/v1/stats and the frontend sitemap."""
    total = conn.execute("SELECT COUNT(*) FROM laws").fetchone()[0]
    by_cat = dict(conn.execute(
        "SELECT category, COUNT(*) FROM laws GROUP BY category").fetchall())
    by_status = dict(conn.execute(
        "SELECT status, COUNT(*) FROM laws GROUP BY status").fetchall())
    multi = conn.execute(
        "SELECT COUNT(*) FROM (SELECT law_id FROM law_versions "
        "GROUP BY law_id HAVING COUNT(*) > 1)").fetchone()[0]
    latest = conn.execute(
        "SELECT MAX(valid_from) FROM law_versions").fetchone()[0]
    return {"total_acts": total, "by_category": by_cat,
            "by_status": by_status, "multi_version_acts": multi,
            "latest_version_date": latest}
