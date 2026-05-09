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


@pytest.mark.parametrize(
    "query",
    [
        # Trailing punctuation — Round-4 review Issue #1 found that
        # "наредба—" (em-dash suffix) was bypassing the reject and
        # reproducing the original 1.14 sec cold-call regression
        # FR-016 was supposed to eliminate.
        "наредба—",       # em-dash
        "наредба–",       # en-dash
        "наредба.",       # period
        "наредба*",       # asterisk
        "наредба…",       # ellipsis
        'наредба"',       # trailing quote (FTS5-special)
        "НАРЕДБА—",       # case + em-dash
        "законът—",       # definite article + em-dash
        # Leading whitespace + trailing punctuation
        "  наредба—  ",
        # Multiple punctuation
        "наредба...",
    ],
    ids=[
        "em-dash-suffix",
        "en-dash-suffix",
        "period-suffix",
        "asterisk-suffix",
        "ellipsis-suffix",
        "trailing-quote",
        "uppercase-em-dash",
        "definite-article-em-dash",
        "leading-whitespace-em-dash",
        "triple-period",
    ],
)
def test_search_rejects_category_words_with_trailing_punctuation(app, query):
    """Round-4 review Issue #1: the v1 reject (membership against
    bg_normalize(query).strip()) was bypassed by trailing punctuation —
    notably em-dash, which is common in Bulgarian legal writing. The v2
    reject tokenizes the normalized query (re.findall(r'\\w+', ...))
    and rejects when exactly one token comes out and matches the
    stop-word set. This test locks the contract for every punctuation
    bypass discovered in Round-4."""
    with pytest.raises(ToolError) as exc:
        app.call_tool_sync("search", {"query": query})
    assert exc.value.code == "QUERY_TOO_BROAD"


def test_search_does_not_reject_multi_category_word_queries(app):
    """A query with two stop-words connected by punctuation (e.g.
    'наредба—правилник') is NOT rejected — it tokenizes to 2 distinct
    words, the two-tier FTS5 ranker handles the conjunction efficiently,
    and the user clearly intends a multi-term search."""
    result = app.call_tool_sync("search", {"query": "наредба—правилник"})
    assert isinstance(result, list)


def test_search_rejection_is_constant_time(app):
    """Reject path must short-circuit before FTS5 — running the reject
    1000 times in a tight loop should still be fast (<1 second total).
    A regression where the reject accidentally invokes search_fts (or a
    tokenizer that's not O(input)) would break this budget. The actual
    timing is hardware-dependent, so the assertion is generous."""
    import time
    t0 = time.monotonic()
    for _ in range(1000):
        with pytest.raises(ToolError):
            app.call_tool_sync("search", {"query": "наредба—"})
    elapsed = time.monotonic() - t0
    assert elapsed < 5.0, (
        f"1000 rejects took {elapsed:.2f}s — reject path is invoking "
        "FTS5 or doing O(n²) work somewhere."
    )


# ─── FR-015 synonym expansion (D-2026-05-09-04 part 1) ────────────────────────


def test_search_expands_single_token_abbreviation(populated_conn, tmp_path):
    """FR-015: a single-token abbreviation query should be rewritten
    to its canonical form before FTS5 sees it. The conftest fixture
    seeds 'Закон за А' with law_id='zakon-a'; we use a custom
    abbreviation registered just for the test to avoid coupling the
    test to whatever happens to be in the production dictionary."""
    from mcp_server.server import build_app
    import index.synonyms as syn

    # Patch the dictionary for this test only.
    orig = syn.LEGAL_ABBREVIATIONS.copy()
    try:
        # 'тестабс' (test-abbrev) → 'закон за а' which matches zakon-a
        # by title in the populated_conn fixture.
        syn.LEGAL_ABBREVIATIONS["тестабс"] = "закон за а"
        app = build_app(conn=populated_conn, corpus_root=tmp_path)
        hits = app.call_tool_sync("search", {"query": "тестабс"})
        assert any(h["law_id"] == "zakon-a" for h in hits), (
            "synonym expansion should let 'тестабс' find zakon-a "
            f"via its canonical form. Got: {[h['law_id'] for h in hits]}"
        )
    finally:
        syn.LEGAL_ABBREVIATIONS.clear()
        syn.LEGAL_ABBREVIATIONS.update(orig)


def test_search_does_not_expand_multi_word_query(populated_conn, tmp_path):
    """Multi-word queries with an abbreviation in them pass through
    unchanged — FTS5 sees the literal tokens. This is correct: if the
    user typed 'ЗОП обществени', they're scoping; rewriting would
    duplicate context."""
    from mcp_server.server import build_app
    import index.synonyms as syn

    orig = syn.LEGAL_ABBREVIATIONS.copy()
    try:
        # Even though 'тестабс' is registered, the multi-word query
        # 'тестабс за А' should NOT be rewritten — multi-word
        # passthrough is the contract.
        syn.LEGAL_ABBREVIATIONS["тестабс"] = "закон за б"  # would map to a different law
        app = build_app(conn=populated_conn, corpus_root=tmp_path)
        # The multi-word search shouldn't be turned into the synonym's
        # canonical form (which would point at zakon-b). The literal
        # tokens 'тестабс' and 'А' don't match any seeded act, so the
        # result is an empty list (or no zakon-b in the hits).
        hits = app.call_tool_sync("search", {"query": "тестабс за А"})
        zakon_b_hits = [h for h in hits if h["law_id"] == "zakon-b"]
        # Either no hits at all, or no zakon-b — the rewrite did NOT fire.
        assert not zakon_b_hits, (
            "multi-word query should pass through unchanged; "
            f"unexpected zakon-b match suggests rewrite fired. Got: {hits}"
        )
    finally:
        syn.LEGAL_ABBREVIATIONS.clear()
        syn.LEGAL_ABBREVIATIONS.update(orig)


def test_search_synonym_expansion_is_case_insensitive(populated_conn, tmp_path):
    """The lookup is via bg_normalize, which lowercases. So 'ЗОП' and
    'зоп' both resolve to the same canonical form."""
    from mcp_server.server import build_app
    import index.synonyms as syn

    orig = syn.LEGAL_ABBREVIATIONS.copy()
    try:
        syn.LEGAL_ABBREVIATIONS["тестабс"] = "закон за а"
        app = build_app(conn=populated_conn, corpus_root=tmp_path)
        for variant in ("ТЕСТАБС", "Тестабс", "тестабс", "ТестАбс"):
            hits = app.call_tool_sync("search", {"query": variant})
            assert any(h["law_id"] == "zakon-a" for h in hits), (
                f"variant {variant!r} should expand to canonical via "
                f"bg_normalize. Got: {[h['law_id'] for h in hits]}"
            )
    finally:
        syn.LEGAL_ABBREVIATIONS.clear()
        syn.LEGAL_ABBREVIATIONS.update(orig)


# ─── FR-015 part 2: rang-aware re-ranking (D-2026-05-09-04) ────────────────────


def test_search_parent_law_outranks_implementing_regulation(app):
    """FR-015 part 2: when a parent law and its implementing
    regulations / ordinances all match the same query, the parent law
    (category=`laws` or `codes`) must outrank the implementing acts
    (category=`implementing`/`regulations`/`ordinances`) in search
    results.

    Conftest seeds an adversarial fixture (zakon-zop with a long
    title vs ppr-zop / reg-zop with shorter denser titles). bm25 alone
    would put the shorter implementing acts FIRST because of higher
    query-token density. The rang-aware tier sort in search_fts must
    invert that: parent law on top, implementing acts after."""
    hits = app.call_tool_sync("search", {"query": "обществени поръчки"})
    law_pos = next(
        (i for i, h in enumerate(hits) if h["law_id"] == "zakon-zop"),
        None,
    )
    ppr_pos = next(
        (i for i, h in enumerate(hits) if h["law_id"] == "ppr-zop"),
        None,
    )
    reg_pos = next(
        (i for i, h in enumerate(hits) if h["law_id"] == "reg-zop"),
        None,
    )
    assert law_pos is not None, (
        f"parent law not found: {[h['law_id'] for h in hits]}"
    )
    assert ppr_pos is not None, (
        f"implementing reg not found: {[h['law_id'] for h in hits]}"
    )
    assert reg_pos is not None, (
        f"regulation not found: {[h['law_id'] for h in hits]}"
    )
    assert law_pos < ppr_pos and law_pos < reg_pos, (
        f"parent law (pos {law_pos}) should outrank implementing reg "
        f"(pos {ppr_pos}) and regulation (pos {reg_pos}). "
        f"Hits: {[h['law_id'] for h in hits]}"
    )


# ─── FR-017 body-snippet generation (D-2026-05-09-02) ─────────────────────────


def test_search_default_omits_body_snippet(app):
    """FR-017: body_snippet is opt-in. The default `search` call (no
    include_body) returns body_snippet="" for every hit so the
    100 ms p95 search budget is preserved."""
    hits = app.call_tool_sync("search", {"query": "обществени поръчки"})
    assert hits, "expected at least one hit"
    for h in hits:
        assert h["body_snippet"] == "", (
            f"default search should not populate body_snippet; "
            f"hit={h!r}"
        )


def test_search_with_include_body_populates_top_results(app):
    """When include_body=True, the top results carry a non-empty
    body_snippet with <b>...</b> highlighting."""
    hits = app.call_tool_sync(
        "search",
        {"query": "обществени поръчки", "include_body": True},
    )
    assert hits, "expected at least one hit"

    top = hits[0]
    assert top["body_snippet"], (
        f"top result body_snippet should be non-empty when "
        f"include_body=True; got {top!r}"
    )
    assert "<b>" in top["body_snippet"] and "</b>" in top["body_snippet"]


def test_search_body_snippet_cap_excludes_results_past_top_n(app, monkeypatch):
    """Results past the top _BODY_SNIPPET_TOP_N have body_snippet=''
    even with include_body=True. We monkey-patch the cap to 1 so
    3rd+ results exercise the empty-string path."""
    import mcp_server.queries as q
    monkeypatch.setattr(q, "_BODY_SNIPPET_TOP_N", 1)
    hits = app.call_tool_sync(
        "search",
        {"query": "обществени", "limit": 50, "include_body": True},
    )
    assert len(hits) >= 2, (
        f"need >=2 hits with patched cap=1; got {len(hits)}."
    )
    # Hits 2+ must all have empty body_snippet under the patched cap.
    for i, h in enumerate(hits[1:], start=2):
        assert h["body_snippet"] == "", (
            f"hit #{i} (law_id={h['law_id']!r}) should have empty "
            f"body_snippet under cap=1; got {h['body_snippet']!r}"
        )
    # The first hit must have a non-empty body_snippet (proving the
    # cap doesn't accidentally zero out the whole list).
    assert hits[0]["body_snippet"], (
        f"top-1 hit should have non-empty body_snippet; "
        f"got: {hits[0]['body_snippet']!r}"
    )


def test_make_body_snippet_returns_empty_on_no_term_match(populated_conn):
    """Direct unit test: when no term appears in the body, return ''."""
    from mcp_server.queries import _make_body_snippet
    out = _make_body_snippet(populated_conn, "zakon-a",
                             terms=["неизвестен_термин"])
    assert out == ""


def test_make_body_snippet_returns_empty_for_unknown_law_id(populated_conn):
    """If the law_id isn't in laws_fts, return ''."""
    from mcp_server.queries import _make_body_snippet
    out = _make_body_snippet(populated_conn, "doesnotexist",
                             terms=["обществен"])
    assert out == ""


def test_insert_fts_row_lowercases_body(populated_conn):
    """LOAD-BEARING INVARIANT: _make_body_snippet does case-sensitive
    str.find() against laws_fts.body, expecting bg_normalize-d
    (lowercased) text. If insert_fts_row ever stops lowercasing, the
    snippet helper silently returns empty for queries that should
    match. Lock the invariant here so a future change to the
    normalization pipeline produces a focused failure."""
    row = populated_conn.execute(
        "SELECT body FROM laws_fts WHERE law_id = 'zakon-zop'"
    ).fetchone()
    assert row is not None
    body = row["body"]
    # bg_normalize lowercases — body should not contain any uppercase
    # Cyrillic. Spot-check the canonical case-marker chars.
    assert body == body.lower(), (
        f"laws_fts.body for zakon-zop should be lowercased after "
        f"bg_normalize; got mixed case: {body[:60]!r}"
    )
    # And the bg_normalize symmetric form is what _make_body_snippet
    # expects for case-insensitive matching.
    assert "закон" in body
    assert "Закон" not in body


def test_make_body_snippet_finds_earliest_match(populated_conn):
    """When multiple terms appear in the body, the snippet is built
    around the EARLIEST occurrence (so the user sees the first context
    they'd naturally read in)."""
    from mcp_server.queries import _make_body_snippet
    # zakon-zop has body "закон за обществените поръчки в република
    # българия" (lowercased by insert_fts_row). 'българия' appears AFTER
    # 'закон'; both are in the body. The snippet should be around 'закон'
    # (earliest), not 'българия'.
    out = _make_body_snippet(populated_conn, "zakon-zop",
                             terms=["българия", "закон"])
    assert "<b>закон</b>" in out, (
        f"snippet should highlight earliest term 'закон', got: {out!r}"
    )
