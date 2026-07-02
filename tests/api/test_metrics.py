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
