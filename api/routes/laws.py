"""Law + article read endpoints. Composition mirrors the MCP get_law /
get_article tool bodies (mcp_server/server.py) over per-request
connections; the query layer raises, api/errors.py maps (D-052)."""

import sqlite3

from fastapi import APIRouter, Depends, Request, Response

from api.deps import CACHE_HEADER_300, get_conn
from api.errors import error_responses
from mcp_server import queries
from mcp_server.errors import ToolError
from mcp_server.schemas import GetArticleResponseDict, GetLawResponseDict

router = APIRouter(prefix="/api/v1")


@router.get("/laws/{slug}", response_model=GetLawResponseDict,
            responses=error_responses(
                "INVALID_DATE", "LAW_NOT_FOUND", "NO_VERSION_AT_DATE",
                "AMBIGUOUS_NAME", "INDEX_STALE", "INDEX_MISSING"))
def get_law(slug: str, request: Request, response: Response,
            date: str | None = None,
            conn: sqlite3.Connection = Depends(get_conn)):
    law_id = queries.resolve_name_to_law_id(conn, slug)
    commit, warnings = queries.version_with_warnings(conn, law_id, date)
    meta_row = queries.law_meta(conn, law_id)
    raw = queries.read_law_markdown(
        request.app.state.corpus_root, law_id, meta_row["category"],
        commit, meta_row["current_commit"])
    fm, body = queries.split_frontmatter(raw)
    response.headers["Cache-Control"] = CACHE_HEADER_300
    return {
        "law_id": law_id,
        "identificador": str(meta_row["doc_id"]),
        "titulo": fm.get("titulo") or "",
        "category": meta_row["category"],
        "fecha_publicacion": queries.iso_date(fm.get("fecha_publicacion")),
        "ultima_actualizacion": queries.iso_date(fm.get("ultima_actualizacion")),
        "dv_issue": fm.get("dv_issue"),
        "dv_year": fm.get("dv_year"),
        "effective_date": queries.iso_date(fm.get("effective_date")),
        "eli": fm.get("eli"),
        "amendment_history": fm.get("amendment_history") or [],
        "commit_hash": commit,
        "body_markdown": body,
        "warnings": warnings,
    }


@router.get("/laws/{slug}/articles/{art}",
            response_model=GetArticleResponseDict,
            responses=error_responses(
                "INVALID_DATE", "INVALID_ARTICLE_SPEC", "LAW_NOT_FOUND",
                "NO_VERSION_AT_DATE", "ARTICLE_NOT_FOUND", "AMBIGUOUS_NAME",
                "INDEX_MISSING"))
def get_article(slug: str, art: str, response: Response,
                date: str | None = None,
                conn: sqlite3.Connection = Depends(get_conn)):
    law_id = queries.resolve_name_to_law_id(conn, slug)
    spec = queries.parse_article_spec(art)
    if spec.range_end is not None:
        raise ToolError("INVALID_ARTICLE_SPEC", {
            "spec": art,
            "detail": "ranges are not served by this endpoint — request "
                      "single articles (the MCP get_articles tool serves "
                      "ranges)",
            "examples": ["чл. 5", "чл. 5, ал. 2"],
        })
    commit, warnings = queries.version_with_warnings(conn, law_id, date)
    rows = queries.article_lookup(conn, law_id, spec.article,
                                  spec.paragraph, date)
    row = rows[0]
    response.headers["Cache-Control"] = CACHE_HEADER_300
    return {
        "law_id": law_id,
        "article": row["article"],
        "paragraph": row["paragraph"],
        "text": row["text"],
        "text_hash": row["text_hash"],
        "commit_hash": commit,
        "warnings": warnings,
    }
