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
