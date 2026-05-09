"""Tests for the Bulgarian legal-term synonym dictionary."""

import pytest

from index.synonyms import LEGAL_ABBREVIATIONS, expand_if_abbreviation


def test_expand_returns_canonical_for_known_abbreviation():
    assert expand_if_abbreviation("зоп") == (
        "закон за обществените поръчки"
    )


def test_expand_returns_none_for_unknown_token():
    assert expand_if_abbreviation("неизвестно") is None
    assert expand_if_abbreviation("xyz") is None


def test_expand_returns_none_for_multi_word_query():
    """Multi-word queries pass through unchanged — the user is providing
    enough context that FTS5 can match the act directly."""
    assert expand_if_abbreviation("закон за обществените") is None
    assert expand_if_abbreviation("зоп обществени поръчки") is None


def test_expand_returns_none_for_empty_or_whitespace():
    assert expand_if_abbreviation("") is None
    assert expand_if_abbreviation(" ") is None


@pytest.mark.parametrize(
    "abbrev,canonical_keyword",
    [
        ("зоп", "обществени"),
        ("ппзоп", "правилник"),
        ("нк", "наказателен"),
        ("гпк", "граждански"),
        ("кт", "кодекс на труда"),
        ("апк", "административнопроцесуален"),
    ],
    ids=["zop", "ppzop", "nk", "gpk", "kt", "apk"],
)
def test_expand_canonical_contains_expected_keyword(abbrev, canonical_keyword):
    """Sanity check that each canonical form contains a substring that
    would let FTS5 find the act. If a future canonical-form edit drops
    a load-bearing word, this catches it."""
    canonical = expand_if_abbreviation(abbrev)
    assert canonical is not None
    assert canonical_keyword in canonical


def test_dictionary_is_canonical_bg_normalize_form():
    """Every key must be bg_normalize-d (lowercase, no internal
    whitespace)."""
    from index.fts import bg_normalize
    for key in LEGAL_ABBREVIATIONS:
        assert key == bg_normalize(key), (
            f"key {key!r} is not bg_normalize-d "
            f"(would be {bg_normalize(key)!r})"
        )
        assert " " not in key, (
            f"key {key!r} has whitespace — abbreviations must be "
            "single tokens"
        )


def test_dictionary_no_circular_references():
    """No canonical form should be itself a registered abbreviation
    (would cause infinite expansion in any future bidirectional logic).
    Sanity check; not currently load-bearing since expansion is
    one-way."""
    canonical_set = set(LEGAL_ABBREVIATIONS.values())
    abbrev_set = set(LEGAL_ABBREVIATIONS.keys())
    assert not (canonical_set & abbrev_set), (
        "no abbreviation can also be a canonical form: "
        f"{canonical_set & abbrev_set}"
    )


def test_dictionary_is_at_least_15_entries():
    """Sanity guard against accidental wholesale truncation."""
    assert len(LEGAL_ABBREVIATIONS) >= 15
