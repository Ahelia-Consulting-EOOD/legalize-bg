def test_metrics_counts_requests_and_errors(client):
    client.get("/api/v1/stats")
    client.get("/api/v1/laws/nesashtestvuvasht-akt")   # 404 → error count
    r = client.get("/api/v1/metrics")
    assert r.status_code == 200
    m = r.json()
    stats_m = m["/api/v1/stats"]
    assert stats_m["calls"] >= 1 and stats_m["errors"] == 0
    law_m = m["/api/v1/laws/{slug}"]
    assert law_m["errors"] >= 1
    assert "avg_ms" in stats_m


def test_metrics_records_truly_unhandled_exceptions():
    # PR review fix #2: api/metrics.py's middleware previously only
    # called metrics.record() AFTER call_next(request) returned — a
    # genuinely unhandled exception makes call_next raise instead, so
    # the record() call never ran and the route silently vanished from
    # /api/v1/metrics. ToolError and the D-052 query-layer exceptions
    # are already caught by registered exception handlers before they
    # ever reach this middleware (see test_metrics_counts_requests_and_
    # errors above, which already covers that path via a 404) — this
    # test needs an exception with NO registered handler at all, which
    # isn't reachable through the real public routes, so it targets the
    # middleware in isolation with a throwaway route on a test-local app
    # (per the finding's suggested fallback).
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from api.metrics import install_metrics

    app = FastAPI()
    install_metrics(app)

    @app.get("/boom")
    def boom():
        raise ValueError("kaboom")

    with TestClient(app, raise_server_exceptions=False) as c:
        r = c.get("/boom")
        assert r.status_code == 500
        m = c.get("/api/v1/metrics").json()
    assert m["/boom"]["calls"] == 1
    assert m["/boom"]["errors"] == 1
