"""Tests for the `search` MCP tool."""

import pytest

from mcp_server.server import build_app


@pytest.fixture
def app(populated_conn, tmp_path):
    return build_app(conn=populated_conn, corpus_root=tmp_path)


def test_search_returns_list_of_hits(app):
    hits = app.call_tool_sync("search", {"query": "Закон за"})
    assert isinstance(hits, list)
    assert all("law_id" in h and "relevance" in h for h in hits)


def test_search_hit_has_title_snippet_not_snippet(app):
    """Field is title_snippet (not snippet) — we want callers to know
    the snippet is title-derived, not body-context. FR-017 tracks the
    1b.3 body-snippet rework."""
    hits = app.call_tool_sync("search", {"query": "Закон за"})
    assert hits
    for h in hits:
        assert "title_snippet" in h, f"missing title_snippet in {h}"
        assert "snippet" not in h, f"unexpected legacy `snippet` in {h}"


def test_search_returns_positive_relevance(app):
    """SearchHit.relevance is positive-where-higher-is-better. Raw bm25
    is negative-where-lower-is-better; the queries layer negates so
    callers using the conventional sort-descending get the right answer."""
    hits = app.call_tool_sync("search", {"query": "Закон за"})
    assert hits  # at least one zakon-* matches
    for h in hits:
        assert h["relevance"] > 0, \
            f"relevance must be positive after negation, got {h['relevance']}"


def test_search_with_category_filter(app):
    hits = app.call_tool_sync("search", {
        "query": "Закон за", "category": "ordinances",
    })
    assert all(h["category"] == "ordinances" for h in hits)


def test_search_phantom_act_uses_doc_id_placeholder(app):
    """§7.3: phantom acts surface with `<doc_id=N>` in the title slot."""
    hits = app.call_tool_sync("search", {"query": "549676032"})
    phantom_hits = [h for h in hits if h["law_id"] == "phantom"]
    assert phantom_hits, "phantom act must remain findable via identificador"
    assert phantom_hits[0]["title"].startswith("<doc_id=")


def test_search_caps_extreme_limit(app):
    """The tool caps `limit` at 50 to protect against runaway requests.
    Note: the test fixture has only 5 seeded acts so this assertion is
    trivially true on the in-memory DB; the load-bearing validation of
    the cap is in mcp_server/server.py:228 (min(max(1, int(limit)), 50))
    — we just confirm the call doesn't error and returns within-limit."""
    hits = app.call_tool_sync("search", {"query": "Закон за", "limit": 1000})
    assert len(hits) <= 50


def test_search_empty_query_returns_empty_list(app):
    hits = app.call_tool_sync("search", {"query": ""})
    assert hits == []


# ─── FR-016 / D-2026-05-09-03: QUERY_TOO_BROAD reject ─────────────────────────


from mcp_server.errors import ToolError  # noqa: E402


@pytest.mark.parametrize(
    "query",
    [
        "наредба",
        "закон",
        "правилник",
        "кодекс",
        "постановление",
        # bg_normalize symmetric forms — verify the reject also catches
        # the definite-article variants since users type both.
        "наредбата",
        "законът",
    ],
    ids=[
        "naredba",
        "zakon",
        "pravilnik",
        "kodeks",
        "postanovlenie",
        "naredba-definite",
        "zakon-definite",
    ],
)
def test_search_rejects_single_word_category_queries(app, query):
    """FR-016 / D-2026-05-09-03: single-word category queries match
    thousands of acts (2,604 ordinances for "наредба" alone), so FTS5
    has to rank all of them — pathological cold-call latency. Reject
    these before FTS5 with a structured QUERY_TOO_BROAD error so the
    caller can ask the user for more terms."""
    with pytest.raises(ToolError) as exc:
        app.call_tool_sync("search", {"query": query})
    assert exc.value.code == "QUERY_TOO_BROAD"
    payload = exc.value.payload
    assert "category_words" in payload
    assert isinstance(payload["category_words"], list)
    assert len(payload["category_words"]) == 5  # the 5 stop-words
    assert "hint" in payload
    # Hint should be model-actionable Bulgarian text.
    assert "повече" in payload["hint"] or "specific" in payload["hint"].lower()


def test_search_accepts_multi_word_query_starting_with_category_word(app):
    """Multi-word queries that include a category word are NOT rejected;
    'наредба за обществени' is a legitimate scoping query."""
    # Should not raise; should return a list (possibly empty against
    # the in-memory test fixture).
    result = app.call_tool_sync("search", {"query": "наредба за обществени"})
    assert isinstance(result, list)


def test_search_accepts_single_word_non_category_query(app):
    """Non-category single words ('за', 'нещо' from the test fixture)
    still go through FTS5 — the reject is targeted at the 5 specific
    category words only."""
    result = app.call_tool_sync("search", {"query": "нещо"})
    assert isinstance(result, list)


def test_search_query_too_broad_payload_lists_actual_stop_words(app):
    """Payload's `category_words` should list the actual stop-words used
    so a model receiving the error can communicate them to the user
    without re-deriving the list."""
    with pytest.raises(ToolError) as exc:
        app.call_tool_sync("search", {"query": "наредба"})
    expected = {"наредба", "закон", "правилник", "кодекс", "постановление"}
    assert set(exc.value.payload["category_words"]) == expected
