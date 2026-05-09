"""Pure query functions over the SQLite catalog.

Each function takes a sqlite3.Connection plus typed parameters; none has
an MCP dependency. Tools in mcp_server/server.py are thin wrappers that
catch domain exceptions and translate them into ToolError.
"""

from __future__ import annotations

import re
import sqlite3
from dataclasses import dataclass

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
            {"law_id": r["law_id"], "title": r["title"], "score": r["score"]}
            for r in fts_rows
        ]
    except sqlite3.OperationalError:
        # Degenerate query (FTS5 syntax error) — return without suggestions.
        pass
    raise LawNotFound(name=name, suggestions=suggestions)


# ────────────────────────────── version_at_date (§7.2) ──────────────────────

from datetime import date as _date


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

    Raises NoVersionAtDate if the date is before the earliest valid_from
    or the law_id has no versions at all.
    """
    target = date or _date.today().isoformat()
    row = conn.execute(
        """SELECT commit_hash FROM law_versions
           WHERE law_id = ?
             AND valid_from <= ?
             AND (valid_to IS NULL OR valid_to > ?)
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

    §7.2 detection: when valid_from equals today (the bootstrap-run-date
    fallback used by `index.build` when fecha_publicacion was null), the
    response includes a DATE_UNCERTAIN warning. Per D-026 this is a
    warning (rides in the successful response), not a blocker.
    """
    commit = version_at_date(conn, law_id, date)
    warnings: list[dict] = []
    today = _date.today().isoformat()
    row = conn.execute(
        "SELECT valid_from FROM law_versions "
        "WHERE law_id = ? AND commit_hash = ?",
        (law_id, commit),
    ).fetchone()
    if row and row["valid_from"] == today:
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
