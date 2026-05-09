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


@pytest.mark.parametrize(
    "user_input,error_family",
    [
        ("*", "unknown special query"),
        ('"foo', "unterminated string"),
        ('foo"bar', "unterminated string"),
        ('"unbalanced', "unterminated string"),
        ('"empty""', "unterminated string"),
        ("x:badcolumn", "no such column"),
    ],
    ids=[
        "lone-asterisk",
        "leading-quote",
        "embedded-quote",
        "unbalanced-quote",
        "doubled-trailing-quote",
        "invalid-column-qualifier",
    ],
)
def test_run_match_swallows_fts5_user_input_errors(user_input, error_family):
    """FTS5 raises OperationalError for malformed query terms — three
    error-message families verified empirically (see plan
    `2026-05-09-phase1b1-review-fixes.md`):

      - "unknown special query: "  (lone '*')
      - "unterminated string"      (any unbalanced quote)
      - "no such column: ..."      (invalid column qualifier)

    All must be swallowed (return []) so user typos in `search` don't
    surface as 500-equivalent errors. The resolver and search both depend
    on this fallback. The error_family arg is a sanity check that the
    test inputs are actually reaching the path under test (audit D-8 +
    review Issue #1)."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute(_LAWS_DDL)
    create_laws_fts_table(conn)
    # Sanity: confirm the input genuinely produces the expected family
    # at the SQLite layer (so a future SQLite version that changes the
    # message family causes a single, focused test failure rather than
    # silent allowlist drift).
    try:
        conn.execute(
            "SELECT 1 FROM laws_fts WHERE laws_fts MATCH ?", [user_input]
        ).fetchone()
    except sqlite3.OperationalError as e:
        assert error_family in str(e).lower(), (
            f"input {user_input!r}: expected error family containing "
            f"{error_family!r}, got {str(e)!r}. SQLite/FTS5 may have "
            f"changed its error wording — update the allowlist in "
            f"index/fts.py:_run_match accordingly."
        )
    # The actual contract: _run_match must return [] for all three families.
    assert _run_match(conn, user_input, category=None, limit=20) == []


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
