from pathlib import Path

import pytest


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


def test_get_article_carries_implicit_flag(client):
    """FR-034: the article payload exposes the position-derived-alinea
    marker. The fixture act is modern (numbered alineas), so the flag is
    present and False — the additive key must exist regardless."""
    r = client.get("/api/v1/laws/zakon-vremeto/articles/чл. 1, ал. 2")
    assert r.status_code == 200
    assert r.json()["implicit"] is False


@pytest.fixture(scope="module")
def pre1974_client(tmp_path_factory):
    """A separate one-act corpus + catalog whose act is pre-Указ-883/1974
    style (чл. 36 has two UNNUMBERED paragraphs), served through the real
    app. Kept out of `api_corpus` on purpose — that fixture's act count is
    asserted verbatim by tests/api/test_laws_list.py."""
    import subprocess
    from fastapi.testclient import TestClient
    from api.app import create_app
    from index.build import build

    corpus = tmp_path_factory.mktemp("api-pre1974-corpus")
    law = corpus / "laws" / "zzd.md"
    law.parent.mkdir(parents=True)
    law.write_text(
        "---\ntitulo: Закон за задълженията и договорите\n"
        "identificador: 900\nfecha_publicacion: 1950-12-01\n---\n\n"
        "**Чл. 36.** Едно лице може да представлява друго.\n\n"
        "Последиците възникват направо за представлявания.\n",
        encoding="utf-8")
    subprocess.run(["git", "init", "-q"], cwd=corpus, check=True)
    subprocess.run(["git", "add", "-A"], cwd=corpus, check=True)
    subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t",
                    "commit", "-q", "-m", "[bootstrap] ЗЗД"],
                   cwd=corpus, check=True)
    db = str(corpus / "catalog.db")
    build(corpus, db)
    app = create_app(db_path=db, corpus_root=Path(corpus))
    with TestClient(app) as c:
        yield c


def test_rest_implicit_alinea_flags_and_warns(pre1974_client):
    """FR-034 review round 1 (minor 1): REST parity — an implicit alinea
    carries BOTH the machine flag and the bilingual human warning, the
    same pair the MCP get_article tool emits."""
    r = pre1974_client.get("/api/v1/laws/zzd/articles/чл. 36, ал. 2")
    assert r.status_code == 200
    body = r.json()
    assert body["paragraph"] == "2"
    assert body["implicit"] is True
    assert any(w["code"] == "IMPLICIT_ALINEA" for w in body["warnings"]), \
        body["warnings"]


def test_rest_whole_article_has_no_implicit_warning(pre1974_client):
    r = pre1974_client.get("/api/v1/laws/zzd/articles/чл. 36")
    assert r.status_code == 200
    body = r.json()
    assert body["implicit"] is False
    assert not any(w["code"] == "IMPLICIT_ALINEA" for w in body["warnings"])


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
