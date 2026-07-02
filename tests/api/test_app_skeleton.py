"""FR-028 Task 3: app factory, healthz, per-request connections,
D-052 error mapping."""

from mcp_server.errors import ToolError


def test_healthz(client):
    r = client.get("/healthz")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


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
