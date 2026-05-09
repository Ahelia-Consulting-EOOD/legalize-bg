import sqlite3

import pytest
from index.fts import bg_normalize, _run_match, create_laws_fts_table


def test_lowercase():
    assert bg_normalize("ЗАКОН") == "закон"


def test_strip_whitespace_and_collapse():
    # Multiple spaces and a newline collapse to single spaces. Inputs are
    # short, suffixless tokens so this test isolates whitespace handling
    # from definite-article stripping.
    assert bg_normalize("  едно   две\nтри  четири  ") == "едно две три четири"


def test_strips_short_definite_article_TA_TO_TE():
    # "поръчки[те]" → "поръчки", "държава[та]" → "държава", "място[то]" → "място"
    assert "поръчки" in bg_normalize("обществените поръчки").split()
    assert "държава" in bg_normalize("държавата").split()
    assert "място" in bg_normalize("мястото").split()


def test_strips_long_definite_article_ETO_ITE():
    # "управление[то]" → "управление", "решения[та]" → "решения"
    assert "управление" in bg_normalize("управлението").split()
    assert "решения" in bg_normalize("решенията").split()


def test_does_not_strip_short_words():
    out = bg_normalize("това дума")
    assert "това" in out.split()


def test_symmetric_query_matches_indexed_form():
    indexed = bg_normalize("обществените поръчки")
    query = bg_normalize("обществена поръчка")
    assert "поръчк" in indexed or "поръчки" in indexed
    assert "обществен" in indexed or "обществени" in indexed
    for tok in indexed.split():
        if len(tok) > 4:
            assert any(q.startswith(tok[:4]) or tok.startswith(q[:4]) for q in query.split()), \
                f"no prefix match for indexed token {tok!r}"


def test_idempotent():
    s = "обществените поръчки и държавата"
    assert bg_normalize(bg_normalize(s)) == bg_normalize(s)


def test_plural_definite_indefinite_symmetry():
    """D-022 symmetry MUST hold across number variants — users type the
    plural indefinite ("обществени поръчки") far more often than the
    plural definite ("обществените поръчки"), but both must reduce to
    the same indexed form or FTS silently drops indefinite-query hits.

    With the suffix list reduced to last-character articles only, the
    plural definite "те"/"та"/"то" peel off cleanly, leaving the bare
    plural marker that the indefinite already carries.
    """
    assert bg_normalize("обществените") == bg_normalize("обществени")
    assert bg_normalize("гражданите") == bg_normalize("граждани")
    assert bg_normalize("законите") == bg_normalize("закони")
    assert bg_normalize("решенията") == bg_normalize("решения")


def test_handles_empty_and_none():
    assert bg_normalize("") == ""
    assert bg_normalize(None) == ""


def test_preserves_numbers_and_latin():
    out = bg_normalize("Чл. 14 ЗОП от 2016 г.")
    assert "14" in out
    assert "2016" in out
    assert "зоп" in out


# ─── _run_match exception narrowing (audit D-8) ───────────────────────────────

_LAWS_DDL = """
    CREATE TABLE laws (
        law_id TEXT PRIMARY KEY,
        doc_id INTEGER,
        title TEXT NOT NULL,
        category TEXT NOT NULL,
        status TEXT DEFAULT 'vigente',
        current_commit TEXT
    )
"""


def test_run_match_swallows_fts5_syntax_errors():
    """A query with FTS5-special syntax (lone '*', unbalanced quote) must
    return [] rather than raise — both the resolver and search depend on
    this fallback so callers don't see FTS5 syntax errors from raw user
    input."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute(_LAWS_DDL)
    create_laws_fts_table(conn)
    # FTS5 emits "unknown special query: " for lone '*'. Must be
    # swallowed; result is empty list.
    assert _run_match(conn, "*", category=None, limit=20) == []


def test_run_match_does_not_swallow_corrupt_index_errors():
    """A non-FTS5 OperationalError (mirroring a corrupted/dropped FTS5
    index — base `laws` table intact but `laws_fts` virtual table
    missing) MUST propagate so the operator sees INDEX_STALE /
    INDEX_MISSING instead of silent empty results. The narrowed catch
    only suppresses fts5/syntax/unknown-special-query errors."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute(_LAWS_DDL)
    # Deliberately do NOT create laws_fts; expect OperationalError
    # ("no such table: laws_fts") to propagate.
    with pytest.raises(sqlite3.OperationalError):
        _run_match(conn, "поръчки", category=None, limit=20)
