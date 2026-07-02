"""History + diff endpoints. Composition mirrors the MCP `history` /
`diff` tool bodies (mcp_server/server.py) over per-request connections;
the query layer raises, api/errors.py maps (D-052).

Unlike the MCP tools (which catch `queries.NoVersionAtDate` explicitly
and re-raise as `ToolError`), these routes let it fly straight to the
D-052 `queries.NoVersionAtDate` handler installed in api/errors.py — the
same thin-route convention already used by api/routes/laws.py."""

import sqlite3

from fastapi import APIRouter, Depends, Query, Request, Response

from api.deps import CACHE_HEADER_300, get_conn
from api.errors import error_responses
from api.schemas import DiffResponseDict
from mcp_server import queries
from mcp_server.schemas import VersionEntryDict

router = APIRouter(prefix="/api/v1")


@router.get("/laws/{slug}/history", response_model=list[VersionEntryDict],
            responses=error_responses(
                "LAW_NOT_FOUND", "AMBIGUOUS_NAME", "INDEX_MISSING"))
def history(slug: str, response: Response,
            conn: sqlite3.Connection = Depends(get_conn)):
    law_id = queries.resolve_name_to_law_id(conn, slug)
    response.headers["Cache-Control"] = CACHE_HEADER_300
    return [e.to_dict() for e in queries.law_history(conn, law_id)]


@router.get("/laws/{slug}/diff", response_model=DiffResponseDict,
            responses=error_responses(
                "INVALID_DATE", "INVALID_DATE_RANGE", "LAW_NOT_FOUND",
                "NO_VERSION_AT_DATE", "AMBIGUOUS_NAME", "DIFF_FAILED",
                "INDEX_MISSING"))
def diff(slug: str, request: Request, response: Response,
         from_date: str = Query(alias="from"),
         to_date: str = Query(alias="to"),
         conn: sqlite3.Connection = Depends(get_conn)):
    law_id = queries.resolve_name_to_law_id(conn, slug)
    text = queries.diff_law_versions(
        conn, request.app.state.corpus_root, law_id, from_date, to_date)
    # PR review fix #10: /diff is just as deterministic for a fixed
    # from/to pair as the other GET read endpoints, which all set this.
    response.headers["Cache-Control"] = CACHE_HEADER_300
    return {"law_id": law_id, "from_date": from_date,
            "to_date": to_date, "diff": text}
