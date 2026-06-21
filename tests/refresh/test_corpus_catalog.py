"""Tests for loading the corpus catalog from disk and slug minting."""

from pathlib import Path

import pytest

from fetcher.bg.assembler import generate_slug
from refresh import (
    history_grew,
    load_corpus_catalog,
    mint_slug,
    seed_used_slugs,
)


# --- history_grew -----------------------------------------------------------


def test_history_grew_true_when_new_dv_appears():
    committed = [{"dv": "56/1991", "date": "1991-07-13"}]
    candidate = [
        {"dv": "56/1991", "date": "1991-07-13"},
        {"dv": "85/2003", "date": "2003-09-26"},
    ]
    assert history_grew(committed, candidate) is True


def test_history_grew_false_when_identical():
    hist = [{"dv": "56/1991", "date": "1991-07-13"}]
    assert history_grew(hist, list(hist)) is False


def test_history_grew_false_when_candidate_subset():
    committed = [{"dv": "56/1991"}, {"dv": "85/2003"}]
    candidate = [{"dv": "56/1991"}]
    assert history_grew(committed, candidate) is False


# --- load_corpus_catalog ----------------------------------------------------


def _write_act(root: Path, category: str, slug: str, doc_id: int, hist_dvs: list[str]):
    d = root / category
    d.mkdir(parents=True, exist_ok=True)
    hist = "".join(f"- dv: {dv}\n  date: '2020-01-01'\n" for dv in hist_dvs)
    hist_block = f"amendment_history:\n{hist}" if hist_dvs else "amendment_history: []\n"
    content = (
        "---\n"
        f"titulo: Act {doc_id}\n"
        f"identificador: '{doc_id}'\n"
        "pais: bg\n"
        f"category: {category}\n"
        f"{hist_block}"
        "---\n\nБody text\n"
    )
    (d / f"{slug}.md").write_text(content, encoding="utf-8")


def test_load_corpus_catalog_keys_by_int_doc_id(tmp_path):
    _write_act(tmp_path, "laws", "act-one", 100, ["1/2020"])
    _write_act(tmp_path, "ordinances", "act-two", 200, ["2/2020", "3/2021"])
    catalog = load_corpus_catalog(tmp_path)
    assert set(catalog) == {100, 200}
    assert catalog[100].slug == "act-one"
    assert catalog[100].category == "laws"
    assert catalog[200].slug == "act-two"


def test_load_corpus_catalog_carries_amendment_history(tmp_path):
    _write_act(tmp_path, "laws", "act-one", 100, ["1/2020", "5/2022"])
    catalog = load_corpus_catalog(tmp_path)
    dvs = [e["dv"] for e in catalog[100].amendment_history]
    assert dvs == ["1/2020", "5/2022"]


def test_load_corpus_catalog_preserves_raw_text_for_compare(tmp_path):
    _write_act(tmp_path, "laws", "act-one", 100, ["1/2020"])
    catalog = load_corpus_catalog(tmp_path)
    assert catalog[100].raw_text == (tmp_path / "laws" / "act-one.md").read_text(encoding="utf-8")


def test_load_corpus_catalog_only_known_categories(tmp_path):
    _write_act(tmp_path, "laws", "act-one", 100, [])
    # A stray dir that is NOT a known corpus category must be ignored.
    _write_act(tmp_path, "drafts", "junk", 999, [])
    catalog = load_corpus_catalog(tmp_path)
    assert set(catalog) == {100}


# --- slug minting / reuse ---------------------------------------------------


def test_seed_used_slugs_collects_every_existing_slug(tmp_path):
    _write_act(tmp_path, "laws", "alpha", 1, [])
    _write_act(tmp_path, "ordinances", "beta", 2, [])
    catalog = load_corpus_catalog(tmp_path)
    assert seed_used_slugs(catalog) == {"alpha", "beta"}


def test_mint_slug_dedupes_against_existing():
    title = "Наредба № 7"
    base = generate_slug(title)
    used = {base}
    minted = mint_slug(title, doc_id=555, used_slugs=used)
    assert minted == f"{base}-2"
    assert minted in used  # used set is updated in place


def test_mint_slug_falls_back_to_doc_id_for_empty_title():
    used: set[str] = set()
    minted = mint_slug("", doc_id=777, used_slugs=used)
    assert minted == "777"
