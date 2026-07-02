"""D-052: shared ToolError taxonomy → HTTP statuses. One taxonomy, two
transports — the JSON body is ToolError.to_dict(), byte-compatible with
what an MCP client parses out of str(ToolError)."""

import sqlite3

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from api.schemas import ErrorResponseDict
from mcp_server import queries
from mcp_server.errors import ToolError
from mcp_server.queries import is_catalog_error

HTTP_STATUS_BY_CODE = {
    "INVALID_DATE": 400,
    "INVALID_ARTICLE_SPEC": 400,
    "INVALID_DATE_RANGE": 400,
    "QUERY_TOO_BROAD": 400,
    "LAW_NOT_FOUND": 404,
    "ARTICLE_NOT_FOUND": 404,
    "NO_VERSION_AT_DATE": 404,
    "AMBIGUOUS_NAME": 409,
    "DIFF_FAILED": 500,
    "INDEX_MISSING": 503,
    "INDEX_STALE": 503,
}

# Human-readable per-code descriptions for the OpenAPI contract (PR review
# fix #3) — one line per D-026/D-052 error code, reused by `error_responses`
# below to build each route's `responses={...}` kwarg from the SAME
# HTTP_STATUS_BY_CODE mapping that drives the actual exception handlers, so
# the documented error shapes can't drift from the real ones.
ERROR_RESPONSE_DESCRIPTIONS = {
    "INVALID_DATE": "a `date`-like parameter is missing or not a valid "
                    "YYYY-MM-DD string",
    "INVALID_ARTICLE_SPEC": "the article spec could not be parsed, or a "
                            "range (`чл. 5-7`) was given where only a "
                            "single article is accepted",
    "INVALID_DATE_RANGE": "the `from` date is later than the `to` date",
    "QUERY_TOO_BROAD": "the search query reduces to a bare category "
                       "stop-word (e.g. `наредба`) and would match "
                       "thousands of acts",
    "LAW_NOT_FOUND": "no act matches the given slug, identificador, or "
                     "title",
    "ARTICLE_NOT_FOUND": "the article/alinea spec parsed but no "
                         "provisions row matches it",
    "NO_VERSION_AT_DATE": "the requested date precedes the act's "
                          "earliest recorded version, or it has none",
    "AMBIGUOUS_NAME": "multiple acts share the given title",
    "DIFF_FAILED": "the underlying `git diff` invocation failed",
    "INDEX_MISSING": "catalog.db is missing tables/columns or unreadable "
                     "at query time",
    "INDEX_STALE": "the catalog and corpus have diverged for this act",
}

_SPEC_EXAMPLES = ["чл. 5", "чл. 5, ал. 2", "5.2", "чл. 5-7"]


def error_responses(*codes: str) -> dict[int, dict]:
    """Build a FastAPI `responses=` dict for the given D-026 error codes,
    grouping codes that map to the same HTTP status into one combined
    entry. Used as `@router.get(..., responses=error_responses(...))` so
    the locked OpenAPI contract documents the realistic error shapes per
    endpoint (PR review fix #3) — sourced from HTTP_STATUS_BY_CODE, the
    same table the exception handlers below use, so docs and behavior
    can't drift apart."""
    by_status: dict[int, list[str]] = {}
    for code in codes:
        by_status.setdefault(HTTP_STATUS_BY_CODE[code], []).append(code)
    return {
        status: {
            "model": ErrorResponseDict,
            "description": "; ".join(
                f"`{c}` — {ERROR_RESPONSE_DESCRIPTIONS[c]}" for c in cs),
        }
        for status, cs in by_status.items()
    }


def _json(code: str, payload: dict) -> JSONResponse:
    return JSONResponse(status_code=HTTP_STATUS_BY_CODE.get(code, 500),
                        content=jsonable_encoder({"code": code, **payload}))


def install_error_handlers(app: FastAPI) -> None:
    """Map the query layer's exceptions + ToolError to D-052 responses.
    Endpoints stay thin: they call queries and let exceptions fly."""

    @app.exception_handler(ToolError)
    async def _tool_error(request: Request, exc: ToolError):
        return JSONResponse(
            status_code=HTTP_STATUS_BY_CODE.get(exc.code, 500),
            content=jsonable_encoder(exc.to_dict()))

    @app.exception_handler(sqlite3.OperationalError)
    async def _catalog_error(request: Request, exc: sqlite3.OperationalError):
        # Mirrors mcp_server/server.py's `_register` wrapper (PR review
        # fix #1): a catalog-level OperationalError (missing/corrupt
        # schema) maps to the D-052 INDEX_MISSING 503; anything else is
        # a genuinely unexpected OperationalError and must NOT be
        # silently misclassified — re-raise so it surfaces as a real
        # (500) error via FastAPI's default handling.
        if not is_catalog_error(exc):
            raise exc
        return _json("INDEX_MISSING", {
            "detail": str(exc)[:300],
            "hint": ("catalog.db is missing tables or corrupt — re-run "
                     "`python -m index.build`"),
        })

    @app.exception_handler(queries.LawNotFound)
    async def _law_not_found(request: Request, exc: queries.LawNotFound):
        return _json("LAW_NOT_FOUND",
                     {"name": exc.name, "suggestions": exc.suggestions})

    @app.exception_handler(queries.AmbiguousName)
    async def _ambiguous(request: Request, exc: queries.AmbiguousName):
        return _json("AMBIGUOUS_NAME",
                     {"name": exc.name, "candidates": exc.candidates})

    @app.exception_handler(queries.NoVersionAtDate)
    async def _no_version(request: Request, exc: queries.NoVersionAtDate):
        return _json("NO_VERSION_AT_DATE", {
            "law_id": exc.law_id, "date": exc.date,
            "earliest_available": exc.earliest_available,
            "latest_available": exc.latest_available})

    @app.exception_handler(queries.ArticleNotFound)
    async def _article_not_found(request: Request,
                                 exc: queries.ArticleNotFound):
        return _json("ARTICLE_NOT_FOUND", {
            "law_id": exc.law_id, "article": exc.article,
            "paragraph": exc.paragraph,
            "available_articles": exc.available_articles})

    @app.exception_handler(queries.InvalidArticleSpec)
    async def _invalid_spec(request: Request,
                            exc: queries.InvalidArticleSpec):
        return _json("INVALID_ARTICLE_SPEC",
                     {"detail": str(exc), "examples": _SPEC_EXAMPLES})
