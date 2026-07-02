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


def test_get_article_missing_is_404(client):
    r = client.get("/api/v1/laws/zakon-vremeto/articles/чл. 99")
    assert r.status_code == 404
    body = r.json()
    assert body["code"] == "ARTICLE_NOT_FOUND"
    assert body["available_articles"]
