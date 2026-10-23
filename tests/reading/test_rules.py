"""Tests of the rulings of D-072 (reading/rules.py) and the check changes that came with them."""
import pytest

from reading import rules
from reading.assembler import NUMBER_LINE, strip_line
from reading.checks import run_all
from reading.labels import validate_entries
from reading.ladder import evaluate
from reading.splitter import Block, SplitAct


def _act(texts):
    return SplitAct(blocks=[Block(i, t, "Article") for i, t in enumerate(texts)], sections=[], dropped_by_splitter={}, has_spine=True)


def _kinds(ex):
    return {(e["kind"], e["block"]) for e in ex}


def test_ruling_1_the_first_titled_copy_is_current_and_the_later_one_is_dropped():
    act = _act(["Глава първа.", "ОБЩИ ПОЛОЖЕНИЯ", "Глава първа.", "СТАРО ЗАГЛАВИЕ", "Чл. 1. Текст."])
    smap = {0: {"label": "chapter_heading"}, 1: {"label": "chapter_heading"}, 2: {"label": "chapter_heading"},
            3: {"label": "chapter_heading"}, 4: {"label": "article_head", "n": "1"}}
    assert rules.superseded_headings(act.blocks, smap) == [[2, 3]]
    out, _, om = rules.apply(act.blocks, smap)
    assert [out[i]["label"] for i in (2, 3)] == ["drop", "drop"] and out[2]["rule"] == "D-072/1"
    assert om == [{"kind": "superseded_heading", "blocks": [2, 3]}]
    out, blocks, _ = rules.apply(act.blocks, smap)
    md, ex = run_all(blocks, out)
    assert not ex and "СТАРО" not in md


def test_ruling_1_a_title_marked_changed_wins_and_an_untitled_copy_is_superseded():
    act = _act(["Раздел IV.", "Старо", "Раздел IV.", "Ново (Загл. изм. - ДВ, бр. 1 от 2000 г.)", "Чл. 1. Текст."])
    smap = {i: {"label": "section_heading"} for i in range(4)} | {4: {"label": "article_head", "n": "1"}}
    assert rules.superseded_headings(act.blocks, smap) == [[0, 1]]
    act = _act(["Раздел IV.", "Раздел IV.", "Заглавие", "Чл. 1. Текст."])
    smap = {i: {"label": "section_heading"} for i in range(3)} | {3: {"label": "article_head", "n": "1"}}
    assert rules.superseded_headings(act.blocks, smap) == [[0]]


def test_ruling_1_a_gazette_line_closes_the_stretch_and_a_body_line_separates_copies():
    act = _act(["ПРЕХОДНИ РАЗПОРЕДБИ", "(ОБН. - ДВ, БР. 1 ОТ 2000 Г.)", "ПРЕХОДНИ РАЗПОРЕДБИ", "§ 1. Текст."])
    smap = {0: {"label": "provisions_heading"}, 1: {"label": "editorial_note"}, 2: {"label": "provisions_heading"},
            3: {"label": "paragraph_sign", "n": "1"}}
    assert rules.superseded_headings(act.blocks, smap) == []
    act = _act(["Глава първа.", "А", "Чл. 1. Текст.", "Глава първа.", "Б", "Чл. 2. Текст."])
    smap = {0: {"label": "chapter_heading"}, 1: {"label": "chapter_heading"}, 2: {"label": "article_head", "n": "1"},
            3: {"label": "chapter_heading"}, 4: {"label": "chapter_heading"}, 5: {"label": "article_head", "n": "2"}}
    assert rules.superseded_headings(act.blocks, smap) == []


def test_the_repeated_heading_check_catches_a_copy_no_ruling_dropped():
    act = _act(["Глава първа.", "ОБЩИ", "Глава първа.", "СТАРО", "Чл. 1. Текст."])
    smap = {i: {"label": "chapter_heading"} for i in range(4)} | {4: {"label": "article_head", "n": "1"}}
    assert ("repeated_heading", 2) in _kinds(run_all(act.blocks, smap)[1])


def test_number_line_takes_multi_word_ordinals():
    for t in ("Глава двадесет и първа.", "Глава петдесет и шеста \"а\".", "Раздел IV.", "Част първа."):
        assert NUMBER_LINE.match(t), t
    assert not NUMBER_LINE.match("Глава първа. ОБЩИ ПОЛОЖЕНИЯ")


def test_ruling_5_a_numbered_continuation_run_after_an_item_with_a_colon_is_items():
    act = _act(["Чл. 1. Текст:", "1. следните:", "1. едно;", "2. две.", "Чл. 2. Текст."])
    smap = {0: {"label": "article_head", "n": "1"}, 1: {"label": "item", "n": "1"}, 2: {"label": "continuation"},
            3: {"label": "continuation"}, 4: {"label": "article_head", "n": "2"}}
    assert rules.numbered_lists(act.blocks, smap) == [(2, "1"), (3, "2")]
    out, _, _ = rules.apply(act.blocks, smap)
    assert [(out[i]["label"], out[i]["n"], out[i]["rule"]) for i in (2, 3)] == [("item", "1", "D-072/5"), ("item", "2", "D-072/5")]


def test_ruling_6_a_number_printed_twice_gets_the_suffix_and_passes_the_order_check():
    act = _act(["Чл. 1. (1) Текст.", "(2) Едно.", "(2) Друго.", "(3) Три."])
    smap = {0: {"label": "article_head", "n": "1"}, 1: {"label": "alinea", "n": "2"}, 2: {"label": "alinea", "n": "2"},
            3: {"label": "alinea", "n": "3"}}
    assert rules.duplicate_numbers(act.blocks, smap) == [[1, 2]]
    out, blocks, om = rules.apply(act.blocks, smap)
    assert out[2]["n"] == "2-2" and out[2]["rule"] == "D-072/6"
    assert om == [{"kind": "duplicate_number", "blocks": [1, 2]}]
    assert not [e for e in run_all(blocks, out)[1] if e["kind"].endswith("order") or e["kind"] == "duplicate"]
    # "1. … :" then "1. …" is a sub-list, not a repeat
    act = _act(["Чл. 1. Текст:", "1. следните:", "1. едно."])
    smap = {0: {"label": "article_head", "n": "1"}, 1: {"label": "item", "n": "1"}, 2: {"label": "item", "n": "1"}}
    assert rules.duplicate_numbers(act.blocks, smap) == []


def test_item_grammar_takes_doubled_letters():
    got, probs = validate_entries([{"i": 0, "label": "item", "n": "27аа"}, {"i": 1, "label": "item", "n": "27аб"}], [0, 1])
    assert 0 in got and 1 not in got and [p["kind"] for p in probs] == ["bad_number", "missing_entry"]


@pytest.mark.parametrize("texts,smap,block", [
    (["Чл. 1. Текст:", "2.В чл. 20:"], {1: {"label": "item", "n": "2"}}, 1),
    (["Чл. 1. Текст:", "1) когато"], {1: {"label": "item", "n": "1"}}, 1),
    (["Чл. 1. (1) Текст.", "(2 (Нова - ДВ, бр. 11 от 2020 г.) Текст."], {1: {"label": "alinea", "n": "2"}}, 1),
    (["ЗАКЛЮЧИТЕЛНИ РАЗПОРЕДБИ", "§ 1. Текст.", "§ 2.Този закон влиза в сила."],
     {0: {"label": "provisions_heading"}, 1: {"label": "paragraph_sign", "n": "1"}}, 2),
])
def test_ruling_7_an_irregular_head_with_an_agreeing_number_is_a_source_finding(texts, smap, block):
    smap = {0: {"label": "article_head", "n": "1"}} | smap
    if block == 2:
        smap[2] = {"label": "paragraph_sign", "n": "2"}
    kinds = _kinds(run_all(_act(texts).blocks, smap)[1])
    assert ("malformed_head", block) in kinds and ("label_text_mismatch", block) not in kinds


def test_ruling_7_alinea_and_item_gaps_the_page_prints_are_source_findings():
    act = _act(["Чл. 1. Текст.", "(2) Две."])
    smap = {0: {"label": "article_head", "n": "1"}, 1: {"label": "alinea", "n": "2"}}
    assert ("alinea_gap", 1) in _kinds(run_all(act.blocks, smap)[1])
    act = _act(["Чл. 1. Текст:", "84. едно;", "86. две."])
    smap = {0: {"label": "article_head", "n": "1"}, 1: {"label": "item", "n": "84"}, 2: {"label": "item", "n": "86"}}
    assert ("item_gap", 2) in _kinds(run_all(act.blocks, smap)[1])


def test_ruling_8_gazette_line_elision_and_separator_are_editorial_notes():
    act = _act(["(ОБН. - ДВ, БР. 1 ОТ 2000 Г.)", ". . . . . . . . .", "-------", "Законът е приет от 40-то Народно събрание."])
    smap = {0: {"label": "provisions_heading"}, 1: {"label": "continuation"}, 2: {"label": "continuation"},
            3: {"label": "adoption_formula"}}
    out, _, _ = rules.apply(act.blocks, smap)
    assert [(out[i]["label"], out[i]["rule"]) for i in range(3)] == [("editorial_note", "D-072/8")] * 3
    act = _act(["-------", "Чл. 1. Текст."])
    out, _, _ = rules.apply(act.blocks, {0: {"label": "continuation"}, 1: {"label": "article_head", "n": "1"}})
    assert out[0]["label"] == "continuation", "a separator not before the adoption formula stays as labelled"


def test_ruling_13_superscript_and_span_remnants_are_repaired():
    act = _act(["Чл. 278б.SUP>1. Текст.", "Чл. 166.SUP>1. Текст.", "Чл. 3./span>. Текст.", "3. Чл. 5./span> до 7 от Закона."])
    smap = {0: {"label": "article_head", "n": "278б1"}, 1: {"label": "article_head", "n": "167"},
            2: {"label": "article_head", "n": "3"}, 3: {"label": "item", "n": "3"}}
    out, blocks, om = rules.apply(act.blocks, smap)
    assert [b.text for b in blocks] == ["Чл. 278б¹. Текст.", "Чл. 166.SUP>1. Текст.", "Чл. 3. Текст.", "3. Чл. 5 до 7 от Закона."]
    assert [o["blocks"] for o in om] == [[0], [2], [3]], "a number that does not agree is not repaired"
    for n in ("1661", "166-1"):
        smap[1] = {"label": "article_head", "n": n}
        out, blocks, om = rules.apply(act.blocks, smap)
        assert blocks[1].text == "Чл. 166¹. Текст." and out[1]["n"] == "166-1" and out[1]["rule"] == "D-072/13"
    assert not [e for e in run_all(blocks, out)[1] if e["kind"] in ("fragment", "label_text_mismatch")]


def test_a_judgement_whose_block_changed_is_refused(monkeypatch):
    act = _act(["Чл. 1. Текст.", "Особена разпоредба"])
    smap = {0: {"label": "article_head", "n": "1"}, 1: {"label": "continuation"}}
    monkeypatch.setitem(rules.JUDGEMENTS, "test-act", {1: ("section_heading", "Особена разпоредба")})
    out, _, _ = rules.apply(act.blocks, smap, "test-act")
    assert out[1]["label"] == "section_heading" and out[1]["rule"] == "D-072/judgement"
    monkeypatch.setitem(rules.JUDGEMENTS, "test-act", {1: ("section_heading", "Друг текст")})
    with pytest.raises(ValueError, match="judgement block 1"):
        rules.apply(act.blocks, smap, "test-act")


def test_a_judgement_quoted_block_is_not_held_to_the_quotation_marks(monkeypatch):
    act = _act(["Чл. 1. Текст.", "§ 2. След чл. 1001 се прибавя следната", "Чл. 1001а. Текст.", "Чл. 2. Текст."])
    smap = {0: {"label": "article_head", "n": "1"}, 1: {"label": "paragraph_sign", "n": "2"}, 2: {"label": "quoted"},
            3: {"label": "article_head", "n": "2"}}
    assert ("label_text_mismatch", 2) in _kinds(evaluate(act, smap, [])[1]), "a run with no mark goes to the ladder"
    monkeypatch.setitem(rules.JUDGEMENTS, "test-act", {2: ("quoted", "Чл. 1001а.")})
    assert ("label_text_mismatch", 2) not in _kinds(evaluate(act, smap, [], "test-act")[1])


def test_evaluate_settles_a_validator_problem_on_a_ruled_block():
    act = _act(["(ОБН. - ДВ, БР. 1 ОТ 2000 Г.)", "Чл. 1. Текст."])
    smap = {1: {"label": "article_head", "n": "1"}}
    md, ex, om, ruled = evaluate(act, smap, [{"block": 0, "kind": "missing_entry"}, {"block": 1, "kind": "x"}])
    assert ruled[0]["rule"] == "D-072/8"
    assert ("missing_entry", 0) not in _kinds(ex) and ("x", 1) in _kinds(ex)


def test_strip_line_keeps_footnote_asterisks():
    assert strip_line("**Чл. 1.** Текст.") == "Чл. 1. Текст."
    assert strip_line("(**) Бележка към текста (*).") == "(**) Бележка към текста (*)."
    assert strip_line("**§ 2.** Текст (**).") == "§ 2. Текст (**)."
