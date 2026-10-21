"""Tests of the reading architecture: splitter partition, assembler round-trip, checks, ladder."""
from pathlib import Path

import pytest

from reading.assembler import assemble, strip_markers
from reading.checks import run_all
from reading.labels import validate_entries
from reading.ladder import merge, next_round_tasks, round0_tasks
from reading.splitter import Block, SplitAct, split_lexbg

FIX = Path(__file__).resolve().parents[1] / "fixtures" / "html"


@pytest.fixture(scope="module")
def zzd():
    return split_lexbg((FIX / "zzd.html").read_bytes())


def test_splitter_partitions_the_region_text(zzd):
    assert zzd.has_spine
    assert len(zzd.blocks) > 100
    assert all(b.text == b.text.strip() and b.text for b in zzd.blocks)
    assert [b.i for b in zzd.blocks] == list(range(len(zzd.blocks)))
    covered = sorted(i for s in zzd.sections for i in s.blocks)
    assert covered == list(range(len(zzd.blocks))), "every block is in exactly one section"
    assert max(len(s.blocks) for s in zzd.sections) <= 60 + 20


def test_splitter_drops_chrome_and_keeps_articles(zzd):
    assert any(b.text.startswith("Чл. 1.") for b in zzd.blocks)
    assert not any("picRefsFromActs" in b.text for b in zzd.blocks)
    assert zzd.dropped_by_splitter


def _act(texts, hints=None):
    hints = hints or ["Article"] * len(texts)
    blocks = [Block(i, t, h) for i, (t, h) in enumerate(zip(texts, hints))]
    return SplitAct(blocks=blocks, sections=[], dropped_by_splitter={}, has_spine=True)


def test_assembler_copies_text_and_round_trips():
    act = _act(["ЗАКОН ЗА НЕЩО", "Глава първа.", "ОБЩИ", "Чл. 1. Текст на член първи.", "(2) Втора алинея.", "продължение.", "1. точка едно;", "Форум"],
               ["TitleDocument", "Title", "Title", "Article", "Article", "Article", "Article", "unknown"])
    smap = {0: {"label": "title"}, 1: {"label": "chapter_heading"}, 2: {"label": "chapter_heading"}, 3: {"label": "article_head", "n": "1"},
            4: {"label": "alinea", "n": "2"}, 5: {"label": "continuation"}, 6: {"label": "item", "n": "1"}, 7: {"label": "drop", "note": "chrome"}}
    md, placed, dropped = assemble(act.blocks, smap)
    assert "# ЗАКОН ЗА НЕЩО" in md and "### Глава първа. ОБЩИ" in md and "**Чл. 1.** Текст" in md and "(2) Втора алинея. продължение." in md
    assert dropped == [7] and placed == [0, 1, 2, 3, 4, 5, 6]
    md2, ex = run_all(act.blocks, smap)
    assert not [e for e in ex if e["kind"] == "reassembly"]


def test_checks_find_order_nesting_duplicates_and_fragments():
    act = _act(["Чл. 1. Едно.", "(1) а", "(3) б", "Чл. 1. Дубъл.", "1. точка", "Чл. 3. SUP>текст", "Чл. 2. назад"])
    smap = {0: {"label": "article_head", "n": "1"}, 1: {"label": "alinea", "n": "1"}, 2: {"label": "alinea", "n": "3"},
            3: {"label": "article_head", "n": "1"}, 4: {"label": "item", "n": "1"}, 5: {"label": "article_head", "n": "3"},
            6: {"label": "article_head", "n": "2"}}
    md, ex = run_all(act.blocks, smap)
    kinds = {e["kind"] for e in ex}
    assert {"alinea_order", "duplicate_address", "fragment", "article_order"} <= kinds
    assert not any(e["kind"] == "reassembly" for e in ex)


def test_checks_flag_uncovered_and_unknown():
    act = _act(["Чл. 1. Едно.", "нещо"])
    md, ex = run_all(act.blocks, {0: {"label": "article_head", "n": "1"}})
    assert any(e["kind"] == "unknown" and e["block"] == 1 for e in ex)


def test_validate_entries_refuses_bad_shapes():
    got, probs = validate_entries([{"i": 0, "label": "article_head", "n": "x"}, {"i": 1, "label": "nonsense"}, {"i": 1, "label": "alinea", "n": "1"}], [0, 1, 2])
    assert 1 in got and 0 not in got
    kinds = sorted(p["kind"] for p in probs)
    assert kinds == ["bad_label", "bad_number", "missing_entry", "missing_entry"], "block 0 has no accepted entry either"


def test_ladder_round0_and_next_round():
    act = _act(["Чл. 1. Едно.", "(1) а", "(3) б", "Чл. 2. Две."])
    act.sections = [type("S", (), {"k": 0, "blocks": [0, 1, 2, 3]})()]
    tasks = round0_tasks(act)
    assert tasks[0]["target"] is None and [b["i"] for b in tasks[0]["blocks"]] == [0, 1, 2, 3]
    smap, probs = merge({}, [(tasks[0], [{"i": 0, "label": "article_head", "n": "1"}, {"i": 1, "label": "alinea", "n": "1"},
                                          {"i": 2, "label": "alinea", "n": "3"}, {"i": 3, "label": "article_head", "n": "2"}])])
    md, ex = run_all(act.blocks, smap)
    nxt = next_round_tasks(act, smap, ex, 1)
    assert nxt and nxt[0]["target"] == 2 and [b["i"] for b in nxt[0]["blocks"]] == [1, 2, 3]
    assert nxt[0]["blocks"][0]["current_label"] == "alinea"
    smap2, _ = merge(smap, [(nxt[0], [{"i": 2, "label": "continuation", "n": None}])])
    assert smap2[2]["label"] == "continuation"


def test_splitter_keeps_every_character_of_every_fixture():
    """The joined blocks equal the region text, whitespace removed: no word is lost or duplicated (review finding 1)."""
    import re
    from bs4 import BeautifulSoup
    from fetcher.bg.text_parser import content_region
    from reading.splitter import decode, SKIP_CLASSES, INLINE_TAGS
    for name in ("zzd.html", "zop.html", "gpk.html", "ppz-aktsizi.html", "naredba-04-14.html"):
        raw = (FIX / name).read_bytes()
        act = split_lexbg(raw)
        soup = BeautifulSoup(decode(raw), "lxml")
        region, _ = content_region(soup)
        for el in list(region.find_all(True)):
            if getattr(el, "decomposed", False):
                continue
            if (set(el.get("class") or []) & SKIP_CLASSES) and el.name not in INLINE_TAGS:
                el.decompose()
        expected = re.sub(r"\s+", "", region.get_text())
        got = re.sub(r"\s+", "", "".join(b.text for b in act.blocks))
        assert got == expected, f"{name}: {len(got)} vs {len(expected)} characters"


def test_titled_article_round_trips():
    act = _act(["Предмет и цел", "Чл. 1. Текст.", "(2) Втора."], ["Title", "Article", "Article"])
    smap = {0: {"label": "article_title"}, 1: {"label": "article_head", "n": "1"}, 2: {"label": "alinea", "n": "2"}}
    md, ex = run_all(act.blocks, smap)
    assert "Предмет и цел **Чл. 1.** Текст." in md
    assert not [e for e in ex if e["kind"] == "reassembly"], ex


def test_targeted_merge_reads_only_the_target():
    act = _act(["Чл. 1. Едно.", "(1) а", "(3) б", "Чл. 2. Две."])
    smap = {0: {"label": "article_head", "n": "1"}, 1: {"label": "alinea", "n": "1"}, 2: {"label": "alinea", "n": "3"}, 3: {"label": "article_head", "n": "2"}}
    task = {"round": 1, "task": 0, "target": 2, "blocks": [{"i": 1}, {"i": 2}, {"i": 3}]}
    smap2, probs = merge(dict(smap), [(task, [{"i": 2, "label": "continuation", "n": None}])])
    assert smap2[2]["label"] == "continuation" and smap2[1]["label"] == "alinea" and probs == []
    smap3, probs = merge(dict(smap), [(task, [{"i": 1, "label": "nonsense"}, {"i": 2, "label": "continuation"}])])
    assert smap3[1]["label"] == "alinea" and smap3[2]["label"] == "continuation" and probs == []


def test_malformed_answers_are_refused_not_crashed():
    for bad in ({"i": 0, "label": "title"}, [[1]], ["x"], [None], [{"i": True, "label": "title"}], [{"i": "x", "label": "title"}], [{"i": 0, "label": ["title"]}]):
        got, probs = validate_entries(bad, [0, 1])
        assert not got or all(isinstance(k, int) and not isinstance(k, bool) for k in got)
        assert all(isinstance(p["block"], int) for p in probs)


def test_checks_catch_drops_text_mismatch_first_alinea_and_sign_order():
    letters = "абвгдежзик"
    act = _act(["Чл. 1. Едно.", "(2) втора", "Чл. 2. Две.", "(1) а", "Чл. 3. Три.", "§ 5. x", "§ 3. y"] + [f"{c}) буква" for c in letters])
    smap = {0: {"label": "article_head", "n": "1"}, 1: {"label": "alinea", "n": "2"}, 2: {"label": "drop", "note": "x"},
            3: {"label": "alinea", "n": "1"}, 4: {"label": "article_head", "n": "4"}, 5: {"label": "paragraph_sign", "n": "5"},
            6: {"label": "paragraph_sign", "n": "3"}}
    for k, c in enumerate(letters):
        smap[7 + k] = {"label": "letter", "n": c}
    md, ex = run_all(act.blocks, smap)
    kinds = [e["kind"] for e in ex]
    assert "alinea_order" in kinds, "(2) right after an article head without (1)"
    assert "drop_of_provision" in kinds
    assert "label_text_mismatch" in kinds, "Чл. 3 labelled n=4"
    assert "sign_order" in kinds
    assert "letter_order" not in kinds, "и) then к) is the Bulgarian lettering order"
