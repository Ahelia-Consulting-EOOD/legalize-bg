"""FR-028 Task 3: app factory, healthz, per-request connections,
D-052 error mapping."""

from fastapi.testclient import TestClient

from mcp_server.errors import ToolError


def test_healthz(client):
    r = client.get("/healthz")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_missing_catalog_db_returns_index_missing_503(tmp_path):
    # PR review fix #1: api/errors.py registers an exception_handler for
    # sqlite3.OperationalError that maps a catalog-level error (missing
    # file, missing table, ...) to the documented D-052 503, using the
    # SAME predicate mcp_server/server.py's `_register` wrapper uses
    # (relocated to mcp_server.queries.is_catalog_error). A nonexistent
    # db file makes sqlite3.connect(..., mode=ro) raise "unable to open
    # database file" — a marker in _SQLITE_CATALOG_ERRORS — deliberately
    # NOT using the real api_corpus fixture (that catalog exists).
    from api.app import create_app
    app = create_app(db_path=str(tmp_path / "does-not-exist.db"),
                     corpus_root=tmp_path)
    with TestClient(app) as c:
        r = c.get("/api/v1/stats")
    assert r.status_code == 503
    assert r.json()["code"] == "INDEX_MISSING"


def test_head_request_on_get_route_returns_200_empty_body(client):
    # PR review fix #4: FastAPI 0.139's APIRoute doesn't auto-add HEAD
    # for a registered GET route (unlike vanilla Starlette), so a bare
    # HEAD 405'd before api/head_support.py's ASGI middleware fix.
    get_r = client.get("/healthz")
    head_r = client.request("HEAD", "/healthz")
    assert head_r.status_code == 200
    assert head_r.content == b""
    assert head_r.headers.get("content-length") == get_r.headers.get(
        "content-length")


def test_head_request_on_cacheable_route_matches_get_headers(client):
    # zakon-vremeto is seeded by tests/api/conftest.py's api_corpus
    # fixture. Confirms HEAD carries the SAME headers as GET (including
    # Cache-Control) on a route beyond the trivial /healthz case, per
    # the finding's explicit ask.
    get_r = client.get("/api/v1/laws/zakon-vremeto")
    head_r = client.request("HEAD", "/api/v1/laws/zakon-vremeto")
    assert head_r.status_code == 200
    assert head_r.content == b""
    assert get_r.headers.get("cache-control") == "public, max-age=300"
    assert head_r.headers.get("cache-control") == get_r.headers.get(
        "cache-control")
    assert head_r.headers.get("content-length") == get_r.headers.get(
        "content-length")


def test_tool_error_maps_to_http_status_and_json_body(client):
    # No route raises INDEX_MISSING cheaply, so assert on the mapping
    # table + handler via a nonexistent law (LAW_NOT_FOUND → 404),
    # which exercises the full exception→JSON path end to end in Task 5.
    # Here: the mapping table itself is the contract.
    from api.errors import HTTP_STATUS_BY_CODE
    from mcp_server.errors import ERROR_CODES
    mapped = set(HTTP_STATUS_BY_CODE)
    assert mapped == ERROR_CODES - {"DATE_UNCERTAIN"}, (
        "every error code except the DATE_UNCERTAIN warning must map")


def test_unknown_route_is_plain_404(client):
    assert client.get("/api/v1/nope").status_code == 404


def test_cors_headers_present(api_corpus):
    from pathlib import Path
    from fastapi.testclient import TestClient
    from api.app import create_app
    corpus, db = api_corpus
    app = create_app(db_path=db, corpus_root=Path(corpus),
                     cors_origins=["http://localhost:3000"])
    with TestClient(app) as c:
        r = c.get("/healthz", headers={"Origin": "http://localhost:3000"})
        assert r.headers.get("access-control-allow-origin") == "http://localhost:3000"
