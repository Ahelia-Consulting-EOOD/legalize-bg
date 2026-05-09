"""Tests for the `search` MCP tool."""

import pytest

from mcp_server.server import build_app


@pytest.fixture
def app(populated_conn, tmp_path):
    return build_app(conn=populated_conn, corpus_root=tmp_path)


def test_search_returns_list_of_hits(app):
    hits = app.call_tool_sync("search", {"query": "Закон"})
    assert isinstance(hits, list)
    assert all("law_id" in h and "relevance" in h for h in hits)


def test_search_returns_positive_relevance(app):
    """SearchHit.relevance is positive-where-higher-is-better. Raw bm25
    is negative-where-lower-is-better; the queries layer negates so
    callers using the conventional sort-descending get the right answer."""
    hits = app.call_tool_sync("search", {"query": "Закон"})
    assert hits  # at least one zakon-* matches
    for h in hits:
        assert h["relevance"] > 0, \
            f"relevance must be positive after negation, got {h['relevance']}"


def test_search_with_category_filter(app):
    hits = app.call_tool_sync("search", {
        "query": "Закон", "category": "ordinances",
    })
    assert all(h["category"] == "ordinances" for h in hits)


def test_search_phantom_act_uses_doc_id_placeholder(app):
    """§7.3: phantom acts surface with `<doc_id=N>` in the title slot."""
    hits = app.call_tool_sync("search", {"query": "549676032"})
    phantom_hits = [h for h in hits if h["law_id"] == "phantom"]
    assert phantom_hits, "phantom act must remain findable via identificador"
    assert phantom_hits[0]["title"].startswith("<doc_id=")


def test_search_caps_extreme_limit(app):
    """The tool caps `limit` at 50 to protect against runaway requests."""
    hits = app.call_tool_sync("search", {"query": "Закон", "limit": 1000})
    assert len(hits) <= 50


def test_search_empty_query_returns_empty_list(app):
    hits = app.call_tool_sync("search", {"query": ""})
    assert hits == []
