"""R2 acts/{law_id}.json payloads: meta mirrors the REST API's get_law
composition, body_markdown is the current consolidated text, articles
map is baked via index.provisions.parse, preamble_raw + body_markdown
reconstruct the raw file byte-exactly (cf-worker interface agreement)."""

import json
import sqlite3

import pytest

from index.provisions import parse as parse_provisions
from mcp_server.queries import split_frontmatter


@pytest.fixture(scope="module")
def acts_dir(export_run):
    _, _, out = export_run
    return out / "r2" / "acts"


def _load(acts_dir, law_id):
    p = acts_dir / f"{law_id}.json"
    assert p.is_file()
    return json.loads(p.read_text(encoding="utf-8"))


def test_one_json_per_law(export_run, acts_dir):
    _, db, _ = export_run
    src = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    law_ids = [r[0] for r in src.execute("SELECT law_id FROM laws")]
    src.close()
    on_disk = {p.stem for p in acts_dir.glob("*.json")}
    assert on_disk == set(law_ids)


def test_meta_fields(export_run, acts_dir):
    corpus, db, _ = export_run
    doc = _load(acts_dir, "zakon-vremeto")
    meta = doc["meta"]
    assert meta["law_id"] == "zakon-vremeto"
    assert meta["identificador"] == "777"
    assert meta["titulo"] == "Закон за времето"
    assert meta["category"] == "laws"
    assert meta["rango"] == "Закон"
    assert meta["estado"] == "vigente"
    assert meta["fecha_publicacion"] == "2020-01-01"
    assert meta["ultima_actualizacion"] == "2021-06-15"
    assert meta["dv_issue"] == 55
    assert meta["dv_year"] == 2020
    assert meta["eli"] == "/eli/bg/2020/777"
    assert len(meta["amendment_history"]) == 2
    assert meta["warnings"] == []
    # commit_hash must be the act's CURRENT commit per catalog.db
    src = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    head = src.execute("SELECT current_commit FROM laws "
                       "WHERE law_id='zakon-vremeto'").fetchone()[0]
    src.close()
    assert meta["commit_hash"] == head


def test_body_is_current_consolidated_text(export_run, acts_dir):
    corpus, _, _ = export_run
    doc = _load(acts_dir, "zakon-vremeto")
    raw = (corpus / "laws" / "zakon-vremeto.md").read_text(encoding="utf-8")
    _, body = split_frontmatter(raw)
    assert doc["body_markdown"] == body
    assert "НОВА редакция" in doc["body_markdown"]
    # cf-worker /diff parity: raw file reconstructs byte-exactly
    assert doc["preamble_raw"] + doc["body_markdown"] == raw


def test_articles_map_from_provisions_parser(export_run, acts_dir):
    doc = _load(acts_dir, "zakon-vremeto")
    arts = doc["articles"]
    assert set(arts) == {"1", "2"}
    assert arts["1"]["paragraphs"]["1"] == "НОВА редакция."
    assert arts["1"]["paragraphs"]["2"] == "Втора алинея."
    assert arts["2"]["paragraphs"] == {}
    # text + text_hash agree with the SAME extraction logic (imported)
    rows = parse_provisions(doc["body_markdown"], law_id="zakon-vremeto")
    whole = {r.article: r for r in rows if r.paragraph is None}
    for art_id, art in arts.items():
        assert art["text"] == whole[art_id].text
        assert art["text_hash"] == whole[art_id].text_hash


def test_date_uncertain_warning_passthrough(export_run, acts_dir):
    doc = _load(acts_dir, "naredba-bez-data")
    codes = [w["code"] for w in doc["meta"]["warnings"]]
    assert codes == ["DATE_UNCERTAIN"]


def test_minified(acts_dir):
    text = (acts_dir / "zakon-vremeto.json").read_text(encoding="utf-8")
    assert '": ' not in text  # no pretty-print separators
    assert "Закон" in text    # ensure_ascii=False (readable UTF-8)


def test_articles_map_first_wins_on_duplicate_anchor():
    """Corpus reality (457 cases): quoted amendment text inside ПЗР
    re-anchors 'Чл. N.' and produces a SECOND provisions block for the
    same article id. FastAPI's article_lookup serves rows[0] — the FIRST
    inserted row — so the baked map must keep the FIRST occurrence
    (parity-gate failure on zakon-za-obshtestvenite-porachki чл. 5)."""
    from export_cf.acts import articles_map

    md = ("**Чл. 5.** (1) Първа алинея на истинския член. "
          "(2) Втора алинея.\n\n"
          "## ПРЕХОДНИ И ЗАКЛЮЧИТЕЛНИ РАЗПОРЕДБИ\n\n"
          "Чл. 5. В случаите на продажба на акции чрез публично "
          "предлагане (3) фалшива алинея.\n")
    arts = articles_map(md, law_id="x")
    assert arts["5"]["text"].startswith("**Чл. 5.**")
    assert arts["5"]["paragraphs"]["1"] == "Първа алинея на истинския член."
    # ал. 3 exists ONLY in the later duplicate block: article_lookup
    # would still serve it (rows[0] of the (5, 3) key), so it stays.
    assert arts["5"]["paragraphs"]["3"] == "фалшива алинея."


def test_articles_map_paragraph_first_wins_per_key():
    """Paragraph fidelity matches article_lookup exactly: rows[0] per
    (article, paragraph) key — so an alinea that exists ONLY in a later
    duplicate block is still served (FastAPI would return it)."""
    from export_cf.acts import articles_map

    md = ("**Чл. 7.** (1) Първи блок ал. 1.\n\n"
          "Чл. 7. (1) Втори блок ал. 1 — губи. (2) Само тук.\n")
    arts = articles_map(md, law_id="x")
    assert arts["7"]["paragraphs"]["1"] == "Първи блок ал. 1."
    assert arts["7"]["paragraphs"]["2"] == "Само тук."
