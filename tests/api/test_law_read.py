def test_get_law_current(client):
    r = client.get("/api/v1/laws/zakon-vremeto")
    assert r.status_code == 200
    body = r.json()
    assert body["law_id"] == "zakon-vremeto"
    assert body["titulo"] == "Закон за времето"
    assert "НОВА редакция" in body["body_markdown"]
    assert body["warnings"] == []


def test_get_law_historical_date(client):
    r = client.get("/api/v1/laws/zakon-vremeto", params={"date": "2020-06-01"})
    assert r.status_code == 200
    assert "СТАРА редакция" in r.json()["body_markdown"]


def test_get_law_not_found_is_404_with_taxonomy_body(client):
    r = client.get("/api/v1/laws/nesashtestvuvasht-akt")
    assert r.status_code == 404
    assert r.json()["code"] == "LAW_NOT_FOUND"
    assert "suggestions" in r.json()


def test_get_law_bad_date_is_400(client):
    r = client.get("/api/v1/laws/zakon-vremeto", params={"date": "утре"})
    assert r.status_code == 400
    assert r.json()["code"] == "INVALID_DATE"


def test_get_law_before_first_version_is_404(client):
    r = client.get("/api/v1/laws/zakon-vremeto", params={"date": "1990-01-01"})
    assert r.status_code == 404
    assert r.json()["code"] == "NO_VERSION_AT_DATE"


def test_get_law_ambiguous_name_is_409_with_candidates(client):
    # api_corpus (tests/api/conftest.py) seeds a title-twin of
    # zakon-vremeto (zakon-vremeto-dva) sharing the exact titulo
    # "Закон за времето". Neither slug matches that string, so
    # resolve_name_to_law_id (mcp_server/queries.py step 3) falls
    # through to its exact-title match, finds both rows, and genuinely
    # raises AmbiguousName through the real resolution code path.
    r = client.get("/api/v1/laws/Закон за времето")
    assert r.status_code == 409
    body = r.json()
    assert body["code"] == "AMBIGUOUS_NAME"
    candidate_ids = {c["law_id"] for c in body["candidates"]}
    assert candidate_ids == {"zakon-vremeto", "zakon-vremeto-dva"}


def test_get_article_not_found_is_404_via_non_get_law_route(client):
    # LAW_NOT_FOUND is otherwise only exercised via get_law; assert the
    # same taxonomy surfaces through get_article's independent
    # resolve_name_to_law_id call.
    r = client.get("/api/v1/laws/nesashtestvuvasht-akt/articles/чл. 1")
    assert r.status_code == 404
    assert r.json()["code"] == "LAW_NOT_FOUND"


def test_get_article_before_first_version_is_404(client):
    # NO_VERSION_AT_DATE is otherwise only exercised via get_law; assert
    # the same taxonomy surfaces through get_article's independent
    # version_with_warnings call.
    r = client.get("/api/v1/laws/zakon-vremeto/articles/чл. 1",
                   params={"date": "1990-01-01"})
    assert r.status_code == 404
    assert r.json()["code"] == "NO_VERSION_AT_DATE"


def test_get_article(client):
    r = client.get("/api/v1/laws/zakon-vremeto/articles/чл. 1, ал. 2")
    assert r.status_code == 200
    body = r.json()
    assert body["article"] == "1" and body["paragraph"] == "2"
    assert "Втора алинея" in body["text"]


def test_get_article_range_rejected(client):
    r = client.get("/api/v1/laws/zakon-vremeto/articles/чл. 1-3")
    assert r.status_code == 400
    assert r.json()["code"] == "INVALID_ARTICLE_SPEC"


def test_get_article_range_rejected_before_date_validation(client):
    # Regression (review 2026-07-02): get_article must validate the
    # article spec (and reject ranges) BEFORE resolving the version at
    # `date` — matching mcp_server/server.py::get_article's real call
    # order. A range spec combined with a date that precedes the law's
    # earliest version must still surface INVALID_ARTICLE_SPEC (400),
    # not NO_VERSION_AT_DATE (404) from a version lookup that should
    # never run.
    r = client.get("/api/v1/laws/zakon-vremeto/articles/чл. 1-3",
                   params={"date": "1990-01-01"})
    assert r.status_code == 400
    assert r.json()["code"] == "INVALID_ARTICLE_SPEC"


def test_get_article_missing_is_404(client):
    r = client.get("/api/v1/laws/zakon-vremeto/articles/чл. 99")
    assert r.status_code == 404
    body = r.json()
    assert body["code"] == "ARTICLE_NOT_FOUND"
    assert body["available_articles"]
