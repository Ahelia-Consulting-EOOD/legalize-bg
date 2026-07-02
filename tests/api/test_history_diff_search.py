def test_history_lists_versions(client):
    r = client.get("/api/v1/laws/zakon-vremeto/history")
    assert r.status_code == 200
    entries = r.json()
    assert isinstance(entries, list) and entries
    assert entries[-1]["operation"] == "consolidated"


def test_diff_between_the_two_versions(client):
    r = client.get("/api/v1/laws/zakon-vremeto/diff",
                   params={"from": "2020-06-01", "to": "2021-12-31"})
    assert r.status_code == 200
    body = r.json()
    assert body["law_id"] == "zakon-vremeto"
    assert "-**Чл. 1.** (1) СТАРА редакция." in body["diff"]
    assert "+**Чл. 1.** (1) НОВА редакция." in body["diff"]


def test_diff_reversed_range_is_400(client):
    r = client.get("/api/v1/laws/zakon-vremeto/diff",
                   params={"from": "2021-12-31", "to": "2020-06-01"})
    assert r.status_code == 400
    assert r.json()["code"] == "INVALID_DATE_RANGE"


def test_diff_missing_params_is_422(client):
    assert client.get("/api/v1/laws/zakon-vremeto/diff").status_code == 422


def test_history_not_found_is_404_via_non_get_law_route(client):
    # LAW_NOT_FOUND is otherwise only exercised via get_law; assert the
    # same taxonomy surfaces through history's independent
    # resolve_name_to_law_id call.
    r = client.get("/api/v1/laws/nesashtestvuvasht-akt/history")
    assert r.status_code == 404
    assert r.json()["code"] == "LAW_NOT_FOUND"


def test_diff_before_first_version_is_404_via_non_get_law_route(client):
    # NO_VERSION_AT_DATE is otherwise only exercised via get_law; assert
    # the same taxonomy surfaces through diff's independent
    # version_at_date call.
    r = client.get("/api/v1/laws/zakon-vremeto/diff",
                   params={"from": "1990-01-01", "to": "2021-12-31"})
    assert r.status_code == 404
    assert r.json()["code"] == "NO_VERSION_AT_DATE"


def test_search_finds_the_act(client):
    # Both fixture acts share the titulo "Закон за времето" (the
    # zakon-vremeto-dva twin exists for AMBIGUOUS_NAME coverage — see
    # tests/api/conftest.py), so both legitimately match this query;
    # relative bm25 ranking between them isn't a contract to assert on.
    r = client.get("/api/v1/search", params={"q": "времето"})
    assert r.status_code == 200
    hits = r.json()
    assert {h["law_id"] for h in hits} >= {"zakon-vremeto", "zakon-vremeto-dva"}


def test_search_missing_q_is_422(client):
    assert client.get("/api/v1/search").status_code == 422


def test_search_overlong_query_is_400(client):
    r = client.get("/api/v1/search", params={"q": "закон " * 200})
    assert r.status_code == 400
    assert r.json()["code"] == "QUERY_TOO_BROAD"
