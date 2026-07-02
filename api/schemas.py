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


class ErrorResponseDict(TypedDict):
    """D-052 error envelope shape, for OpenAPI documentation only (PR
    review fix #3). Every REST error body carries at least `code`; the
    remaining keys vary per code — see docs/api/error-codes.md for the
    full per-code payload contracts."""
    code: str
