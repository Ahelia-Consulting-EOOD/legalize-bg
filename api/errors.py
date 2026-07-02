"""D-052: shared ToolError taxonomy → HTTP statuses. One taxonomy, two
transports — the JSON body is ToolError.to_dict(), byte-compatible with
what an MCP client parses out of str(ToolError)."""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from mcp_server import queries
from mcp_server.errors import ToolError

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

_SPEC_EXAMPLES = ["чл. 5", "чл. 5, ал. 2", "5.2", "чл. 5-7"]


def _json(code: str, payload: dict) -> JSONResponse:
    return JSONResponse(status_code=HTTP_STATUS_BY_CODE.get(code, 500),
                        content={"code": code, **payload})


def install_error_handlers(app: FastAPI) -> None:
    """Map the query layer's exceptions + ToolError to D-052 responses.
    Endpoints stay thin: they call queries and let exceptions fly."""

    @app.exception_handler(ToolError)
    async def _tool_error(request: Request, exc: ToolError):
        return JSONResponse(
            status_code=HTTP_STATUS_BY_CODE.get(exc.code, 500),
            content=exc.to_dict())

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
