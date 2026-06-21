"""Tests for the catalog-partition and change-classification logic."""

from refresh import (
    partition,
    normalize_for_compare,
    classify_change,
    latest_amendment_date,
)


# --- partition --------------------------------------------------------------


def test_partition_added_existing_missing():
    lex_ids = {10, 20, 30, 40}
    corpus_ids = {20, 30, 50}
    added, existing, missing = partition(lex_ids, corpus_ids)
    assert added == {10, 40}
    assert existing == {20, 30}
    assert missing == {50}


def test_partition_disjoint_sets():
    added, existing, missing = partition({1, 2}, {3, 4})
    assert added == {1, 2}
    assert existing == set()
    assert missing == {3, 4}


def test_partition_identical_sets():
    added, existing, missing = partition({1, 2}, {1, 2})
    assert added == set()
    assert existing == {1, 2}
    assert missing == set()


# --- normalize_for_compare --------------------------------------------------


def test_normalize_collapses_whitespace():
    assert normalize_for_compare("a   b\n\n\nc") == normalize_for_compare("a b\nc")


def test_normalize_unifies_quotes():
    # Typographic and straight quotes must compare equal.
    assert normalize_for_compare("„Закон“") == normalize_for_compare('"Закон"')


def test_normalize_is_idempotent():
    once = normalize_for_compare("  foo   bar  ")
    assert normalize_for_compare(once) == once


# --- latest_amendment_date --------------------------------------------------


def test_latest_amendment_date_picks_max():
    hist = [
        {"dv": "56/1991", "date": "1991-07-13"},
        {"dv": "85/2003", "date": "2003-09-26"},
        {"dv": "18/2005", "date": "2005-02-25"},
    ]
    assert latest_amendment_date(hist) == "2005-02-25"


def test_latest_amendment_date_ignores_null_dates():
    hist = [
        {"dv": "56/1991", "date": "1991-07-13"},
        {"dv": "99", "date": None},
    ]
    assert latest_amendment_date(hist) == "1991-07-13"


def test_latest_amendment_date_empty_history():
    assert latest_amendment_date([]) is None


# --- classify_change --------------------------------------------------------


def _file(history_len: int, body: str = "БODY") -> str:
    """Minimal assembled-file string with a given amendment_history length."""
    hist = "\n".join(
        f"- dv: {i}/2020\n  date: '2020-01-0{i}'" for i in range(1, history_len + 1)
    )
    fm = "amendment_history:\n" + hist if history_len else "amendment_history: []"
    return f"---\n{fm}\n---\n\n{body}"


def test_classify_unchanged_when_identical():
    committed = _file(2, "Член 1. Текст.")
    candidate = _file(2, "Член 1. Текст.")
    assert classify_change(committed, candidate, hist_grew=False) == "unchanged"


def test_classify_reforma_when_history_grew():
    committed = _file(2, "Член 1. Стар текст.")
    candidate = _file(3, "Член 1. Нов текст.")
    assert classify_change(committed, candidate, hist_grew=True) == "reforma"


def test_classify_popravka_when_body_changed_but_history_did_not():
    committed = _file(2, "Член 1. Текст с печатна грешка.")
    candidate = _file(2, "Член 1. Текст без грешка.")
    assert classify_change(committed, candidate, hist_grew=False) == "popravka"


def test_classify_unchanged_ignores_cosmetic_whitespace():
    committed = _file(2, "Член 1.   Текст.")
    candidate = _file(2, "Член 1. Текст.")
    assert classify_change(committed, candidate, hist_grew=False) == "unchanged"
