import sqlite3

from fastapi import APIRouter, Depends

from api.deps import get_conn
from api.errors import error_responses
from api.schemas import StatsResponseDict
from mcp_server import queries

router = APIRouter(prefix="/api/v1")


@router.get("/stats", response_model=StatsResponseDict,
            responses=error_responses("INDEX_MISSING"))
def stats(conn: sqlite3.Connection = Depends(get_conn)):
    return queries.corpus_stats(conn)
