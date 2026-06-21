"""Tests for the `get_article` MCP tool."""

import pytest

from mcp_server.errors import ToolError
from mcp_server.server import build_app


@pytest.fixture
def app_with_provisions(populated_conn, tmp_path):
    """Seed two provisions rows on zakon-a: the article-as-whole row
    and one alinea row, so both retrieval paths can be exercised."""
    populated_conn.execute(
        """INSERT INTO provisions(law_id, article, paragraph, valid_from,
                                  text, text_hash)
           VALUES ('zakon-a', '14', NULL, '2020-01-01',
                   '**Чл. 14.** (1) Първа. (2) Втора.', 'h0')"""
    )
    populated_conn.execute(
        """INSERT INTO provisions(law_id, article, paragraph, valid_from,
                                  text, text_hash)
           VALUES ('zakon-a', '14', '1', '2020-01-01', 'Първа.', 'h1')"""
    )
    populated_conn.execute(
        """INSERT INTO provisions(law_id, article, paragraph, valid_from,
                                  text, text_hash)
           VALUES ('zakon-a', '14', '2', '2020-01-01', 'Втора.', 'h2')"""
    )
    populated_conn.commit()
    return build_app(conn=populated_conn, corpus_root=tmp_path)


def test_get_article_full_article(app_with_provisions):
    r = app_with_provisions.call_tool_sync(
        "get_article", {"law": "100", "article": "чл. 14"})
    assert r["article"] == "14"
    assert r["paragraph"] is None
    assert "Първа" in r["text"] and "Втора" in r["text"]
    assert r["text_hash"] == "h0"
    assert r["commit_hash"]
    assert r["warnings"] == []


def test_get_article_with_alinea(app_with_provisions):
    r = app_with_provisions.call_tool_sync(
        "get_article", {"law": "100", "article": "чл. 14, ал. 2"})
    assert r["article"] == "14"
    assert r["paragraph"] == "2"
    assert r["text"] == "Втора."
    assert r["text_hash"] == "h2"


def test_get_article_alinea_via_dot_notation(app_with_provisions):
    """parse_article_spec supports '14.2' as shorthand for 'чл. 14, ал. 2'."""
    r = app_with_provisions.call_tool_sync(
        "get_article", {"law": "100", "article": "14.1"})
    assert r["paragraph"] == "1"
    assert r["text"] == "Първа."


def test_get_article_invalid_spec_raises(app_with_provisions):
    with pytest.raises(ToolError) as exc:
        app_with_provisions.call_tool_sync(
            "get_article", {"law": "100", "article": "garbage"})
    assert exc.value.code == "INVALID_ARTICLE_SPEC"
    assert "examples" in exc.value.payload
    assert "spec" in exc.value.payload


def test_get_article_range_rejected_with_get_articles_hint(app_with_provisions):
    """FR-018: get_article serves single articles only. A range spec must
    raise INVALID_ARTICLE_SPEC pointing at get_articles, not silently
    return just the first article (the pre-FR-018 bug)."""
    with pytest.raises(ToolError) as exc:
        app_with_provisions.call_tool_sync(
            "get_article", {"law": "100", "article": "чл. 14-16"})
    assert exc.value.code == "INVALID_ARTICLE_SPEC"
    assert "get_articles" in exc.value.payload.get("hint", "")


def test_get_article_not_found_raises_with_available(app_with_provisions):
    with pytest.raises(ToolError) as exc:
        app_with_provisions.call_tool_sync(
            "get_article", {"law": "100", "article": "999"})
    assert exc.value.code == "ARTICLE_NOT_FOUND"
    avail = exc.value.payload["available_articles"]
    assert "14" in avail
    # Legal-number ordering preserved (must-fix #4 from batch-3 review)
    assert avail == sorted(avail, key=_sk)


def test_get_article_law_not_found_raises(app_with_provisions):
    with pytest.raises(ToolError) as exc:
        app_with_provisions.call_tool_sync(
            "get_article",
            {"law": "напълно непознат", "article": "чл. 1"})
    assert exc.value.code == "LAW_NOT_FOUND"


def _sk(article: str):
    """Local copy of the legal-number sort key — used to assert that
    available_articles comes back ordered."""
    import re
    m = re.match(r"^(\d+)([а-я]*)$", article)
    if not m:
        return (10**9, article)
    return (int(m.group(1)), m.group(2))
