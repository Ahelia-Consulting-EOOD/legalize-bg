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

    `title_snippet` is a highlighted fragment of the act's TITLE (not
    body). Body-context snippets cost ~700ms p95 in 1b.1 because FTS5
    must read the full body column for the largest matches; the
    deferred body-snippet rework is FR-017 (Phase 1b.3). Until then,
    callers should treat this as a "which act is this?" affordance,
    not as substantive content; call get_law for body context.
    """

    law_id: str
    identificador: str
    title: str
    category: str
    title_snippet: str
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
