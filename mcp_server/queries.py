"""Pure query functions over the SQLite catalog.

Each function takes a sqlite3.Connection plus typed parameters; none has
an MCP dependency. Tools in mcp_server/server.py are thin wrappers that
catch domain exceptions and translate them into ToolError.

Caller responsibility: the connection passed in MUST have
`row_factory = sqlite3.Row` set so column-name access (`row["foo"]`) works,
AND must have had `register_query_functions(conn)` called to register the
`pylower` UDF used by Cyrillic-aware title resolution (FR-019). The
conftest fixture and the FastMCP server's connection-init (`build_app`)
both do this; new entry points must follow suit.
"""

from __future__ import annotations

import re
import sqlite3
import subprocess
from dataclasses import dataclass
from datetime import date as _date
from pathlib import Path

from index.fts import bg_normalize, search_fts
from index.synonyms import expand_if_abbreviation
from mcp_server.errors import ToolError
from mcp_server.schemas import VersionEntry, AmendmentEntry


# ────────────────────────────── connection UDFs (FR-019) ────────────────────


def _pylower(s):
    """Full-Unicode lowercase for the SQLite UDF. SQLite's built-in
    LOWER() is ASCII-only and does NOT fold Cyrillic; Python's
    str.lower() does, so `pylower(title) = pylower(?)` resolves
    mixed-case Cyrillic titles (FR-019). Non-str inputs pass through."""
    return s.lower() if isinstance(s, str) else s


def register_query_functions(conn: sqlite3.Connection) -> None:
    """Register the catalog query UDFs on `conn`. Idempotent — SQLite
    allows re-registering a function name. This is caller responsibility,
    exactly like `row_factory = sqlite3.Row` (see module docstring):
    every connection that reaches `resolve_name_to_law_id` MUST have this
    called first. `build_app` does it for all production/tool paths; the
    test `conn` fixture does it for direct-resolver tests. The numeric
    identificador and exact-slug resolution steps don't need it (they run
    before the title step), so connections used only for those — e.g. the
    perf cold-call harness — are unaffected. FR-019."""
    conn.create_function("pylower", 1, _pylower, deterministic=True)


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

    # 3. Exact title (case-insensitive). Multiple matches → AmbiguousName.
    # `pylower` (FR-019) folds Cyrillic case; SQLite's built-in LOWER()
    # is ASCII-only. Requires register_query_functions(conn) — see the
    # module docstring's caller-responsibility note.
    rows = conn.execute(
        "SELECT * FROM laws WHERE pylower(title) = pylower(?)", (name,)
    ).fetchall()
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
    or the law_id has no versions at all.
    """
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
    """
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
    `docs/data/schema-reference.md` §2.
    """
    target = date or _date.today().isoformat()
    lo = _legal_article_sort_key(start)
    hi = _legal_article_sort_key(end)
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
    QUERY_TOO_BROAD) when from_date > to_date.
    """
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

    Raises INVALID_DATE_RANGE on a reversed range. Propagates
    NoVersionAtDate (from version_at_date) for the server tool to map
    to NO_VERSION_AT_DATE.
    """
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
