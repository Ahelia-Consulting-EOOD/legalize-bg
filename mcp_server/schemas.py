"""Typed response shapes per D-024.

These are dataclasses (not Pydantic) — FastMCP renders dataclass returns
into MCP response envelopes via dict serialization. Field names match
the YAML frontmatter for any field that mirrors the Markdown source.
"""

from dataclasses import dataclass, field, asdict
from typing import Any


@dataclass(frozen=True)
class GetLawResponse:
    """Structured `get_law` response per D-024.

    All date fields (`fecha_publicacion`, `ultima_actualizacion`,
    `effective_date`, and any `amendment_history[].date`) are ISO 8601
    strings (YYYY-MM-DD), never `datetime.date`. PyYAML parses unquoted
    ISO date scalars to `datetime.date`; `mcp_server.server._iso` coerces
    them back to strings before they reach this dataclass so JSON-RPC
    consumers don't see Python objects (audit C-4). Quoted-string YAML
    date fields pass through unchanged.
    """
    law_id: str
    identificador: str
    titulo: str
    category: str
    fecha_publicacion: str | None
    ultima_actualizacion: str | None
    dv_issue: str | None
    dv_year: int | None
    effective_date: str | None
    eli: str | None
    amendment_history: list[dict]
    commit_hash: str
    body_markdown: str
    warnings: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SearchHit:
    """One ranked search result.

    `relevance` is positive-where-higher-is-better (the negated SQLite
    bm25 score). Convention chosen so model callers don't need to know
    SQLite-specific scoring details (raw bm25 returns negative-where-
    lower-is-better, which surprises naive sort-descending usage).

    NOTE on ordering (post-FR-015 part 2): the result list is NOT
    strictly relevance-sorted — `mcp_server/queries.py:full_text_search`
    runs a rang-aware tier sort (parent laws / codes above implementing
    regs / ordinances) AFTER the bm25 ranking, so within-tier the bm25
    order holds but cross-tier the tier wins. Use `relevance` as a
    within-tier signal, not a global one.

    `title_snippet` is a highlighted fragment of the act's TITLE (not
    body). Cheap (~75 ms p95) — FTS5's snippet() over the title column.
    Always populated.

    `body_snippet` is a Python-extracted ±60-char window around the
    first matching query token in the act's body, with `<b>...</b>`
    highlighting. Generated **only** when the caller passes
    `include_body=True` to `search` (default False). When enabled,
    cost-bounded to the top 2 hits — results 3+ always carry the
    empty string. When disabled (the default), every hit carries
    the empty string. The non-optional `str` type is intentional:
    callers always get a string, never None. Closed FR-017 /
    D-2026-05-09-02 in Phase 1b.3 — opt-in design preserves the
    100 ms warm / 250 ms cold p95 search budget for the default
    path; the live catalog has 1+ MB indexed bodies that make any
    body fetch expensive.
    """

    law_id: str
    identificador: str
    title: str
    category: str
    title_snippet: str
    body_snippet: str  # FR-017 — empty for results 6-N (cost bound)
    relevance: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class GetArticleResponse:
    law_id: str
    article: str
    paragraph: str | None
    text: str
    text_hash: str
    commit_hash: str
    warnings: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
