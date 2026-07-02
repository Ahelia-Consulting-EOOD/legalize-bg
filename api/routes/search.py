"""Search endpoint. Composition mirrors the MCP `search` tool body
(mcp_server/server.py) over a per-request connection.

Adjustment vs. the plan's transcribed code (verified against live
source): `mcp_server/server.py`'s `search` tool caps `limit` to
`min(max(1, int(limit)), 50)` BEFORE calling `queries.full_text_search`
— `full_text_search` itself does no internal capping (unlike
`queries.list_laws`, which caps internally and is REST-only). Dropping
that cap here would let a REST client pass an uncapped `limit` straight
into FTS5, which the shared function's docstring flags as an OOM risk
on the million-row catalog. Mirrored here to keep both transports'
defensive behavior identical."""

import sqlite3

from fastapi import APIRouter, Depends, Query, Response

from api.deps import get_conn
from api.errors import error_responses
from mcp_server import queries
from mcp_server.schemas import SearchHitDict

router = APIRouter(prefix="/api/v1")


@router.get("/search", response_model=list[SearchHitDict],
            responses=error_responses("QUERY_TOO_BROAD", "INDEX_MISSING"))
def search(response: Response, q: str = Query(min_length=1),
           category: str | None = None, limit: int = 20,
           include_body: bool = False,
           conn: sqlite3.Connection = Depends(get_conn)):
    response.headers["Cache-Control"] = "public, max-age=60"
    capped = min(max(1, int(limit)), 50)
    return queries.full_text_search(conn, query=q, category=category,
                                    limit=capped, include_body=bool(include_body))
