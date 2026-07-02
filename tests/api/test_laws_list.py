def test_list_laws_returns_seeded_act(client):
    r = client.get("/api/v1/laws")
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 1
    assert body["items"][0]["law_id"] == "zakon-vremeto"
    assert body["items"][0]["title"] == "Закон за времето"


def test_list_laws_filters_and_paginates(client):
    assert client.get("/api/v1/laws",
                      params={"category": "laws"}).json()["total"] == 1
    assert client.get("/api/v1/laws",
                      params={"category": "codes"}).json()["total"] == 0
    page = client.get("/api/v1/laws", params={"limit": 1, "offset": 5}).json()
    assert page["total"] == 1 and page["items"] == []


def test_stats(client):
    r = client.get("/api/v1/stats")
    assert r.status_code == 200
    s = r.json()
    assert s["total_acts"] == 1
    assert s["by_category"] == {"laws": 1}
    assert s["multi_version_acts"] == 1   # the 2-commit fixture act
