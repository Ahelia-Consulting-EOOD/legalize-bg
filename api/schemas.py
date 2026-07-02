"""API-only wire shapes (TypedDicts, same convention as
mcp_server/schemas.py — used as FastAPI response_model only)."""

from typing import TypedDict


class LawSummaryDict(TypedDict):
    law_id: str
    identificador: str
    title: str
    category: str
    status: str
    first_version: str | None
    latest_version: str | None
    version_count: int


class LawListResponseDict(TypedDict):
    total: int
    items: list[LawSummaryDict]


class StatsResponseDict(TypedDict):
    total_acts: int
    by_category: dict[str, int]
    by_status: dict[str, int]
    multi_version_acts: int
    latest_version_date: str | None


class DiffResponseDict(TypedDict):
    law_id: str
    from_date: str
    to_date: str
    diff: str
