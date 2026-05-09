"""Pure query functions over the SQLite catalog.

Each function takes a sqlite3.Connection plus typed parameters; none has
an MCP dependency. Tools in mcp_server/server.py are thin wrappers that
catch domain exceptions and translate them into ToolError.

Caller responsibility: the connection passed in MUST have
`row_factory = sqlite3.Row` set so column-name access (`row["foo"]`) works.
The conftest fixture and the FastMCP server's connection-init code both
do this; new entry points must follow suit.
"""

from __future__ import annotations

import re
import sqlite3
from dataclasses import dataclass
from datetime import date as _date

from index.fts import search_fts


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
    rows = conn.execute(
        "SELECT * FROM laws WHERE LOWER(title) = LOWER(?)", (name,)
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

    `valid_to` is INCLUSIVE per `docs/data/schema-reference.md` §3 — a
    version with valid_to='2020-12-31' is in force ON 2020-12-31. So the
    in-force predicate is `valid_from <= date AND (valid_to IS NULL OR
    valid_to >= date)` (NOT `>`, which would exclude the boundary day).

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
                     limit: int = 20) -> list[dict]:
    """FTS5 search; symmetric bg_normalize is applied inside search_fts.

    Substitutes `<doc_id=N>` in the `title` slot for §7.3 phantom acts
    (empty titulo) so callers get a non-blank display string.

    Output `relevance` is the negated bm25 score so higher = better
    match (the SQLite bm25() function returns negative-where-lower-is-
    better; exposing the raw value would surprise callers who expect
    the conventional "higher is better" ordering).

    Output `title_snippet` is a highlighted title fragment, not body.
    See SearchHit docstring + FR-017 for the 1b.3 body-snippet rework.
    """
    rows = search_fts(conn, query, category=category, limit=limit)
    out: list[dict] = []
    for r in rows:
        title = r["title"] or f"<doc_id={r['doc_id']}>"
        out.append({
            "law_id": r["law_id"],
            "identificador": str(r["doc_id"]),
            "title": title,
            "category": r["category"],
            "title_snippet": r["snippet"],
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

    `valid_to` is INCLUSIVE per `docs/data/schema-reference.md` §3, so
    the in-force predicate is `valid_to >= date` (NOT `>`).
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
