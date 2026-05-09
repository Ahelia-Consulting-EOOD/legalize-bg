import pytest
from index.fts import bg_normalize


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
