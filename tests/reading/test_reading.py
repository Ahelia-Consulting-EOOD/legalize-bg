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
    act = _act(["ЗАКОН ЗА НЕЩО", "Глава първа. ОБЩИ", "Чл. 1. Текст на член първи.", "(2) Втора алинея.", "1. точка едно;", "Форум"],
               ["TitleDocument", "Heading", "Article", "Article", "Article", "unknown"])
    smap = {0: {"label": "title"}, 1: {"label": "chapter_heading"}, 2: {"label": "article_head", "n": "1"},
            3: {"label": "alinea", "n": "2"}, 4: {"label": "item", "n": "1"}, 5: {"label": "drop", "note": "chrome"}}
    md, placed, dropped = assemble(act.blocks, smap)
    assert "# ЗАКОН ЗА НЕЩО" in md and "### Глава първа. ОБЩИ" in md and "**Чл. 1.** Текст" in md
    assert dropped == [5] and placed == [0, 1, 2, 3, 4]
    assert strip_markers(md).rstrip("\n") == "\n".join(act.blocks[i].text for i in placed)


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
