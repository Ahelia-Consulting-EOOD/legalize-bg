def test_list_laws_returns_seeded_act(client):
    # api_corpus seeds two acts (zakon-vremeto + its title-twin
    # zakon-vremeto-dva, added for AMBIGUOUS_NAME coverage — see
    # tests/api/conftest.py). Order-agnostic: both share `titulo`, so
    # ORDER BY l.title ties aren't a contract to assert on.
    r = client.get("/api/v1/laws")
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 2
    law_ids = {item["law_id"] for item in body["items"]}
    assert law_ids == {"zakon-vremeto", "zakon-vremeto-dva"}
    assert all(item["title"] == "Закон за времето" for item in body["items"])


def test_list_laws_filters_and_paginates(client):
    assert client.get("/api/v1/laws",
                      params={"category": "laws"}).json()["total"] == 2
    assert client.get("/api/v1/laws",
                      params={"category": "codes"}).json()["total"] == 0
    page = client.get("/api/v1/laws", params={"limit": 1, "offset": 5}).json()
    assert page["total"] == 2 and page["items"] == []


def test_stats(client):
    r = client.get("/api/v1/stats")
    assert r.status_code == 200
    s = r.json()
    assert s["total_acts"] == 2
    assert s["by_category"] == {"laws": 2}
    assert s["multi_version_acts"] == 1   # only zakon-vremeto is the 2-commit act
