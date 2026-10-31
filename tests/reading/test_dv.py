"""The Gazette as a source (step S1 of the plan of 31 October 2026): split_dv, the source-aware checks, the title join."""
import json
import re
from pathlib import Path

import pytest
from bs4 import BeautifulSoup

from reading import ladder
from reading.checks import dv_decree, run_all
from reading.splitter import SplitAct, dv_content_region, split_dv

REPO = Path(__file__).resolve().parents[2]
MATERIAL = REPO / "data" / "dv" / "cache" / "242220.html"

SMALL = """<html><body><div class="titleHead">Народно събрание</div><span class="mark">Брой 32 от 1.4.2026 г.</span>
<div style=" width: 100%;"><span style="font-size:8.5pt">
<p style="text-align:center">УКАЗ № 139</p>
<p style="text-align:justify">На основание чл. 98, т. 4 от Конституцията на Република България</p>
<p style="text-align:center">ПОСТАНОВЯВАМ:</p>
<p style="text-align:justify">Да се обнародва в „Държавен вестник“ Законът за пробата.</p>
<p style="text-align:right">Президент на Републиката: <b>Име Фамилия</b></p>
<p style="text-align:right">Министър на правосъдието: <b>Друго Име</b></p>
<p style="text-align:center"><b>ЗАКОН</b></p>
<p style="text-align:center"><b>за пробата</b></p>
<p style="text-align:center">Глава първа</p>
<p style="text-align:center">ОБЩИ ПОЛОЖЕНИЯ</p>
<p style="text-align:justify;text-indent:14pt"><b>Чл. 1. </b>Този закон урежда пробата.</p>
<p style="text-align:justify"><b>Чл. 2. </b>(1) Пробата е публична.<br/>(2) Втора алинея.</p>
<p style="text-align:center">ЗАКЛЮЧИТЕЛНА РАЗПОРЕДБА</p>
<p style="text-align:justify"><b>Параграф единствен.</b> Законът влиза в сила от деня на обнародването му.</p>
<p style="text-align:justify">Законът е приет от 51-вото Народно събрание на 19 март 2026 г. и е подпечатан с официалния печат на Народното събрание.</p>
<p style="text-align:right">Председател на Народното събрание: <b>Рая Назарян</b></p>
<p style="text-align:justify">1563</p>
</span></div></body></html>"""

MAP = {0: {"label": "drop", "note": "decree"}, 1: {"label": "drop", "note": "decree"}, 2: {"label": "drop", "note": "decree"},
       3: {"label": "drop", "note": "decree"}, 4: {"label": "drop", "note": "decree"}, 5: {"label": "drop", "note": "decree"},
       6: {"label": "title"}, 7: {"label": "title"}, 8: {"label": "chapter_heading"}, 9: {"label": "chapter_heading"},
       10: {"label": "article_head", "n": "1"}, 11: {"label": "article_head", "n": "2"}, 12: {"label": "alinea", "n": "2"},
       13: {"label": "provisions_heading"}, 14: {"label": "paragraph_sign", "n": "единствен"}, 15: {"label": "adoption_formula"},
       16: {"label": "drop", "note": "signature"}, 17: {"label": "drop", "note": "material number"}}


def _chars(s: str) -> str:
    return re.sub(r"\s+", "", s)


def test_split_dv_keeps_every_character_of_a_small_material_in_exactly_one_block():
    act = split_dv(SMALL)
    region = dv_content_region(BeautifulSoup(SMALL, "lxml"))
    assert _chars("".join(b.text for b in act.blocks)) == _chars(region.get_text())
    assert act.source == "dv" and act.has_spine and act.dropped_by_splitter == {}
    assert [b.text for b in act.blocks][6:10] == ["ЗАКОН", "за пробата", "Глава първа", "ОБЩИ ПОЛОЖЕНИЯ"]
    assert act.blocks[10].text == "Чл. 1. Този закон урежда пробата." and act.blocks[12].text == "(2) Втора алинея."  # a <br> cuts a block
    assert [b.hint for b in act.blocks][:8] == ["DvCenter", "DvJustify", "DvCenter", "DvJustify", "DvRight", "DvRight", "DvCenter", "DvCenter"]
    assert list(dv_decree(act.blocks)) == [0, 1, 2, 3, 4, 5]
    assert SplitAct.from_dict(json.loads(json.dumps(act.to_dict()))).to_dict() == act.to_dict() and act.to_dict()["source"] == "dv"
    assert [b.i for s in act.sections for b in [act.blocks[i] for i in s.blocks]] == list(range(len(act.blocks)))


@pytest.mark.skipif(not MATERIAL.exists(), reason="material 242220 not in the Gazette cache")
def test_split_dv_keeps_every_character_of_the_transport_laws_material():
    html = MATERIAL.read_text(encoding="utf-8")
    act = split_dv(html)
    region = dv_content_region(BeautifulSoup(html, "lxml"))
    assert _chars("".join(b.text for b in act.blocks)) == _chars(region.get_text())
    assert act.has_spine and act.blocks[0].text.startswith("УКАЗ №") and list(dv_decree(act.blocks)) == list(range(8))
    assert any(b.text.startswith("§ 1.") for b in act.blocks) and any(b.text == "ДОПЪЛНИТЕЛНА РАЗПОРЕДБА" for b in act.blocks)
    assert sum(1 for b in act.blocks if b.text.startswith("Чл. ")) == 106


def test_the_checks_know_the_gazettes_chrome_and_join_a_two_line_title():
    act = split_dv(SMALL)
    md, ex = run_all(act.blocks, MAP, source="dv")
    assert ex == [], ex
    assert md.startswith("# ЗАКОН за пробата\n\n### Глава първа ОБЩИ ПОЛОЖЕНИЯ\n\n**Чл. 1.** Този закон урежда пробата.")
    assert "УКАЗ" not in md and "Председател" not in md and "1563" not in md
    # the decree placed under a label is chrome placed; a dropped line after the act that is not the signature is a drop outside the act
    smap = {**MAP, 0: {"label": "title"}}
    _, ex = run_all(act.blocks, smap, source="dv")
    assert [e["kind"] for e in ex if e["block"] == 0] == ["chrome_placed"]
    smap = {**MAP, 15: {"label": "drop", "note": "x"}}
    _, ex = run_all(act.blocks, smap, source="dv")
    assert [e["kind"] for e in ex if e["block"] == 15] == ["drop_outside_act"]
    # under the lex.bg chrome rules the same map fails: the decree is not lex.bg's known chrome
    _, ex = run_all(act.blocks, MAP)
    assert "drop_outside_act" in {e["kind"] for e in ex}


def test_round0_tasks_of_a_gazette_act_carry_the_source_context():
    act = split_dv(SMALL)
    tasks = ladder.round0_tasks(act)
    assert tasks and tasks[0]["context"][0] == ladder.DV_CONTEXT
    md, ex, omissions, ruled = ladder.evaluate(act, MAP, [], "zakon-za-probata")
    assert ex == [] and "# ЗАКОН за пробата" in md


def test_lost_text_is_a_source_finding_that_the_write_refuses():
    act = split_dv(SMALL.replace("<b>Параграф единствен.</b> Законът", "<b>§ 2. </b>Законът"))
    smap = {**MAP, 14: {"label": "paragraph_sign", "n": "2"}}
    _, ex = run_all(act.blocks, smap, source="dv")
    assert [(e["kind"], e["block"]) for e in ex] == [("sign_start", 14)]
    assert ladder.LOST_TEXT == {"empty_section", "sign_start"} and ladder.LOST_TEXT <= ladder.SOURCE_FINDINGS


def test_an_annex_after_the_signature_is_not_excused_and_the_signature_is_chrome_wherever_it_stands():
    html = SMALL.replace('<p style="text-align:justify">1563</p>',
                         '<p style="text-align:justify">1563</p><p style="text-align:center">Приложение № 1 към чл. 2</p>'
                         '<p style="text-align:justify">Чл. 1. Ред от приложението.</p><p style="text-align:justify">Данни.</p>')
    act = split_dv(html)
    dropped_all = {**MAP, 18: {"label": "drop", "note": "x"}, 19: {"label": "drop", "note": "x"}, 20: {"label": "drop", "note": "x"}}
    _, ex = run_all(act.blocks, dropped_all, source="dv")
    assert {e["kind"] for e in ex} >= {"drop_of_provision", "drop_outside_act"}   # the annex is not the signature's tail (S1 review, finding 1)
    placed = {**MAP, 18: {"label": "annex_heading"}, 19: {"label": "annex_row"}, 20: {"label": "annex_row"}}
    _, ex = run_all(act.blocks, placed, source="dv")
    assert ex == [], ex   # the signature and the number dropped between the act and its annex are chrome


def test_every_empty_section_is_found():
    from reading.splitter import Block, SplitAct
    def act(texts):
        return [Block(i, t, "DvCenter") for i, t in enumerate(texts)]
    # an empty transitional section before the final one; an empty chapter before the next chapter; an empty heading at the end
    blocks = act(["Чл. 1. Едно.", "ПРЕХОДНИ РАЗПОРЕДБИ", "ЗАКЛЮЧИТЕЛНИ РАЗПОРЕДБИ", "§ 1. Текст.", "Глава втора", "ПРАЗНА", "Глава трета", "ПЪЛНА", "Чл. 2. Две.", "Глава четвърта", "КРАЙ"])
    smap = {0: {"label": "article_head", "n": "1"}, 1: {"label": "provisions_heading"}, 2: {"label": "provisions_heading"}, 3: {"label": "paragraph_sign", "n": "1"},
            4: {"label": "chapter_heading"}, 5: {"label": "chapter_heading"}, 6: {"label": "chapter_heading"}, 7: {"label": "chapter_heading"},
            8: {"label": "article_head", "n": "2"}, 9: {"label": "chapter_heading"}, 10: {"label": "chapter_heading"}}
    _, ex = run_all(blocks, smap)
    assert [(e["kind"], e["block"]) for e in ex if e["kind"] == "empty_section"] == [("empty_section", 1), ("empty_section", 5), ("empty_section", 10)]
    # a provisions heading continued by its "КЪМ …" line, and a chapter with its two-line title, are not empty
    blocks = act(["Чл. 1. Едно.", "Преходни и Заключителни разпоредби", "КЪМ ЗАКОНА ЗА ИЗМЕНЕНИЕ", "Преходни и Заключителни разпоредби", "§ 3. Текст.", "Глава втора", "ЗАГЛАВИЕ", "Раздел I", "Чл. 2. Две."])
    smap = {0: {"label": "article_head", "n": "1"}, 1: {"label": "provisions_heading"}, 2: {"label": "provisions_heading"}, 3: {"label": "provisions_heading"},
            4: {"label": "paragraph_sign", "n": "3"}, 5: {"label": "chapter_heading"}, 6: {"label": "chapter_heading"}, 7: {"label": "section_heading"}, 8: {"label": "article_head", "n": "2"}}
    _, ex = run_all(blocks, smap)
    assert not [e for e in ex if e["kind"] == "empty_section"], ex


def test_a_three_line_heading_is_one_heading():
    from reading.assembler import assemble
    from reading.splitter import Block
    blocks = [Block(0, "Глава втора", "DvCenter"), Block(1, "ПЛАНИРАНЕ И УПРАВЛЕНИЕ", "DvCenter"), Block(2, "КЛИРИНГОВА СИСТЕМА", "DvCenter"), Block(3, "Чл. 1. Едно.", "DvJustify")]
    smap = {0: {"label": "chapter_heading"}, 1: {"label": "chapter_heading"}, 2: {"label": "chapter_heading"}, 3: {"label": "article_head", "n": "1"}}
    md, _, _ = assemble(blocks, smap)
    assert md.startswith("### Глава втора ПЛАНИРАНЕ И УПРАВЛЕНИЕ КЛИРИНГОВА СИСТЕМА\n")
    _, ex = run_all(blocks, smap, source="dv")
    assert ex == []
