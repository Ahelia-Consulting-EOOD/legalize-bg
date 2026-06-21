"""Tests for the `get_articles` MCP tool (FR-018 article ranges)."""

import pytest

from mcp_server.errors import ToolError
from mcp_server.server import build_app


@pytest.fixture
def app_with_range(populated_conn, tmp_path):
    """Seed article-as-whole rows 14, 14а, 16, 17 on zakon-a (note the gap
    at 15 and the out-of-range 17)."""
    for art, h in [("14", "h14"), ("14а", "h14a"), ("16", "h16"), ("17", "h17")]:
        populated_conn.execute(
            "INSERT INTO provisions(law_id, article, paragraph, valid_from, text, text_hash) "
            "VALUES ('zakon-a', ?, NULL, '2020-01-01', ?, ?)",
            (art, f"Чл. {art} текст.", h),
        )
    populated_conn.commit()
    return build_app(conn=populated_conn, corpus_root=tmp_path)


def test_get_articles_single(app_with_range):
    """A non-range spec returns a one-entry articles list with the shared
    commit_hash + warnings channel."""
    r = app_with_range.call_tool_sync(
        "get_articles", {"law": "100", "articles": "чл. 14"})
    assert r["law_id"] == "zakon-a"
    assert [a["article"] for a in r["articles"]] == ["14"]
    assert r["articles"][0]["text_hash"] == "h14"
    assert r["articles"][0]["paragraph"] is None
    assert r["commit_hash"]
    assert r["warnings"] == []


def test_get_articles_range_expands(app_with_range):
    """A range returns every in-range article (incl. suffixed 14а),
    ordered, skipping the gap at 15 and excluding the next integer 17."""
    r = app_with_range.call_tool_sync(
        "get_articles", {"law": "100", "articles": "чл. 14-16"})
    assert [a["article"] for a in r["articles"]] == ["14", "14а", "16"]
    assert all(a["paragraph"] is None for a in r["articles"])
    assert all("text" in a and "text_hash" in a for a in r["articles"])


def test_get_articles_empty_range_raises(app_with_range):
    with pytest.raises(ToolError) as exc:
        app_with_range.call_tool_sync(
            "get_articles", {"law": "100", "articles": "чл. 50-60"})
    assert exc.value.code == "ARTICLE_NOT_FOUND"


def test_get_articles_invalid_spec_raises(app_with_range):
    with pytest.raises(ToolError) as exc:
        app_with_range.call_tool_sync(
            "get_articles", {"law": "100", "articles": "garbage"})
    assert exc.value.code == "INVALID_ARTICLE_SPEC"


def test_get_articles_law_not_found(app_with_range):
    with pytest.raises(ToolError) as exc:
        app_with_range.call_tool_sync(
            "get_articles", {"law": "напълно непознат", "articles": "чл. 14-16"})
    assert exc.value.code == "LAW_NOT_FOUND"
