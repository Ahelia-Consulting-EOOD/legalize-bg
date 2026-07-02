import sqlite3

from fastapi import APIRouter, Depends

from api.deps import get_conn
from api.errors import error_responses
from api.schemas import LawListResponseDict
from mcp_server import queries

router = APIRouter(prefix="/api/v1")


@router.get("/laws", response_model=LawListResponseDict,
            responses=error_responses("INDEX_MISSING"))
def list_laws(category: str | None = None, estado: str | None = None,
              limit: int = 50, offset: int = 0,
              conn: sqlite3.Connection = Depends(get_conn)):
    return queries.list_laws(conn, category=category, estado=estado,
                             limit=limit, offset=offset)
