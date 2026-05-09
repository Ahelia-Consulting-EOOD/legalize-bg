"""Typed response shapes per D-024.

These are dataclasses (not Pydantic) — FastMCP renders dataclass returns
into MCP response envelopes via dict serialization. Field names match
the YAML frontmatter for any field that mirrors the Markdown source.
"""

from dataclasses import dataclass, field, asdict
from typing import Any


@dataclass(frozen=True)
class GetLawResponse:
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
    law_id: str
    identificador: str
    title: str
    category: str
    snippet: str
    score: float

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
