import pytest
from mcp_server.schemas import GetLawResponse, SearchHit, GetArticleResponse


def test_get_law_response_required_fields():
    r = GetLawResponse(
        law_id="zop", identificador="2136735703",
        titulo="ЗОП", category="laws",
        fecha_publicacion="2016-02-16",
        ultima_actualizacion="2024-03-15",
        dv_issue="13", dv_year=2016,
        effective_date="2016-04-15",
        eli="/eli/bg/закон/2016/2/16/zop/con",
        amendment_history=[],
        commit_hash="a" * 40,
        body_markdown="# ЗОП\n\n...",
        warnings=[],
    )
    d = r.to_dict()
    for k in ("law_id", "identificador", "titulo", "fecha_publicacion",
              "body_markdown", "warnings"):
        assert k in d


def test_get_law_response_warnings_optional():
    r = GetLawResponse(
        law_id="x", identificador="1", titulo="X", category="laws",
        fecha_publicacion=None, ultima_actualizacion=None,
        dv_issue=None, dv_year=None, effective_date=None,
        eli=None, amendment_history=[],
        commit_hash="b" * 40, body_markdown="...",
        warnings=[{"code": "DATE_UNCERTAIN", "law_id": "x"}],
    )
    assert len(r.warnings) == 1
    assert r.warnings[0]["code"] == "DATE_UNCERTAIN"


def test_search_hit_shape():
    h = SearchHit(law_id="zop", identificador="100", title="ЗОП",
                   category="laws", title_snippet="<b>ЗОП</b>",
                   body_snippet="...чл. 1. <b>урежда</b>...",
                   relevance=1.5)
    d = h.to_dict()
    assert d == {
        "law_id": "zop", "identificador": "100", "title": "ЗОП",
        "category": "laws", "title_snippet": "<b>ЗОП</b>",
        "body_snippet": "...чл. 1. <b>урежда</b>...",
        "relevance": 1.5,
    }


def test_search_hit_includes_body_snippet():
    """FR-017 / D-2026-05-09-02: SearchHit gains body_snippet.
    Non-optional; populated for top-5 results, empty string for the
    rest."""
    hit = SearchHit(
        law_id="zop",
        identificador="2136735703",
        title="Закон за обществените поръчки",
        category="laws",
        title_snippet="Закон за <b>обществените</b> поръчки",
        body_snippet="...чл. 1. Този закон <b>урежда</b> отношенията...",
        relevance=12.34,
    )
    d = hit.to_dict()
    assert d["body_snippet"].startswith("...")
    assert "<b>урежда</b>" in d["body_snippet"]


def test_search_hit_body_snippet_can_be_empty():
    """Results 6-N have body_snippet="" — explicit empty string, not
    null. Non-optional type intentional: callers always get a string."""
    hit = SearchHit(
        law_id="x",
        identificador="0",
        title="Х",
        category="laws",
        title_snippet="Х",
        body_snippet="",
        relevance=0.1,
    )
    assert hit.to_dict()["body_snippet"] == ""


def test_get_article_response_shape():
    r = GetArticleResponse(
        law_id="zop", article="14", paragraph="2",
        text="(2) ...", text_hash="abc", commit_hash="a" * 40,
        warnings=[],
    )
    d = r.to_dict()
    assert d["law_id"] == "zop" and d["article"] == "14" and d["paragraph"] == "2"
