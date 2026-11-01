"""The operation form and the apply step (reading/operations.py)."""
import pytest

from reading import acttree as T, material as M, operations as O
from reading.splitter import Block, SplitAct

BODY = """# ЗАКОН за пробата

### Глава първа ОБЩИ ПОЛОЖЕНИЯ

**Чл. 1.** Този закон урежда пробата.

**Чл. 2.** (1) Пробата е:

1. първа;

2. втора, до 30 000 лв.

(2) Втора алинея.

(3) Трета алинея.

**Чл. 3.** Член за отмяна.

## Преходни и заключителни разпоредби

**§ 1.** По смисъла на този закон „проба“ е проба.
"""

MATERIAL = ["ЗАКОН", "за изменение и допълнение на Закона за пробата", "(обн., ДВ, бр. 1 от 2020 г.)",
            "§ 1. В чл. 2 се правят следните изменения и допълнения:",
            "1. В ал. 1, т. 2 думите „до 30 000 лв.“ се заменят с „до 1 000 000 евро“.",
            "2. Създава се ал. 4:", "„(4) Четвърта алинея.“",
            "3. В ал. 2 накрая се добавя „и още думи“.",
            "§ 2. Член 3 се отменя.",
            "§ 3. Създава се чл. 3а:", "„Чл. 3а. (1) Нов член.", "(2) С втора алинея.“",
            "§ 4. В чл. 1 думите „урежда“ се заличават.",
            "§ 5. Алинея 3 на чл. 2 става ал. 5.",
            "§ 6. Законът влиза в сила от 1 януари 2027 г.",
            "Законът е приет от 52-рото Народно събрание.", "Председател на Народното събрание: Х", "4984"]
HINTS = {0: "DvCenter", 1: "DvCenter", 2: "DvCenter", 16: "DvRight"}
ANSWER = {"material": 1, "operations": [
    {"id": "§1.1", "kind": "replace_words", "address": "чл. 2, ал. 1, т. 2", "old": "q1", "new": "q2"},
    {"id": "§1.2", "kind": "insert_provision", "address": "чл. 2, ал. 4", "after": "чл. 2, ал. 3", "blocks": [6, 6]},
    {"id": "§1.3", "kind": "insert_words", "address": "чл. 2, ал. 2", "where": "end", "new": "q1"},
    {"id": "§2", "kind": "repeal", "address": "чл. 3"},
    {"id": "§3", "kind": "insert_provision", "address": "чл. 3а", "after": "чл. 3", "blocks": [10, 11]},
    {"id": "§4", "kind": "delete_words", "address": "чл. 1", "old": "q1"},
    {"id": "§5", "kind": "renumber", "address": "чл. 2, ал. 3", "to": "ал. 5"},
    {"id": "§6", "kind": "no_text_change", "note": "entry into force"}]}


def _mat():
    act = SplitAct(blocks=[Block(i, t, HINTS.get(i, "DvJustify")) for i, t in enumerate(MATERIAL)], sections=[], source="dv")
    return M.parse(act), act.blocks


def test_apply_every_kind_and_the_markers_in_the_corpus_convention():
    mat, blocks = _mat()
    assert mat.findings == []
    out = O.apply(ANSWER, mat, blocks, BODY, "96/2026")
    t = T.parse(out.markdown)
    assert t.lines[T.resolve(t, "чл. 2, ал. 1, т. 2")].text == "2. (изм. - ДВ, бр. 96 от 2026 г.) втора, до 1 000 000 евро."
    assert t.lines[T.resolve(t, "чл. 2, ал. 4")].text == "(4) (Нова - ДВ, бр. 96 от 2026 г.) Четвърта алинея."
    assert t.lines[T.resolve(t, "чл. 2, ал. 2")].text == "(2) (Доп. - ДВ, бр. 96 от 2026 г.) Втора алинея и още думи."
    assert t.lines[T.resolve(t, "чл. 3")].text == "**Чл. 3.** (Отм. - ДВ, бр. 96 от 2026 г.)"
    assert "**Чл. 3а.** (Нов - ДВ, бр. 96 от 2026 г.) (1) Нов член.\n\n(2) С втора алинея." in out.markdown
    assert t.lines[T.resolve(t, "чл. 1")].text == "**Чл. 1.** (Изм. - ДВ, бр. 96 от 2026 г.) Този закон пробата."
    assert t.lines[T.resolve(t, "чл. 2, ал. 5")].text == "(5) (Предишна ал. 3 - ДВ, бр. 96 от 2026 г.) Трета алинея."
    # the order of the lines holds: ал. 4 was inserted after ал. 3, which then became ал. 5
    assert [l.n for l in t.lines if l.kind == "alinea"] == ["1", "2", "5", "4", "1", "2"]
    assert len(out.log) == 8 and out.markdown.endswith("\n")
    # a second amendment extends the marker in lex.bg's form
    second = O.apply({"material": 2, "operations": [{"id": "§4", "kind": "delete_words", "address": "чл. 1", "old": "q1"}]},
                     *_mat_with("§ 4. В чл. 1 думите „пробата“ се заличават."), out.markdown, "10/2027")
    t2 = T.parse(second.markdown)
    assert t2.lines[T.resolve(t2, "чл. 1")].text == "**Чл. 1.** (Изм. - ДВ, бр. 96 от 2026 г., изм. - ДВ, бр. 10 от 2027 г.) Този закон."


def _mat_with(instruction: str):
    lines = ["ЗАКОН", "за изменение на Закона за пробата", "(обн., ДВ, бр. 1 от 2020 г.)", instruction, "Законът е приет.", "Председател на Народното събрание: Х", "1"]
    act = SplitAct(blocks=[Block(i, t, {0: "DvCenter", 1: "DvCenter", 2: "DvCenter", 5: "DvRight"}.get(i, "DvJustify")) for i, t in enumerate(lines)], sections=[], source="dv")
    return M.parse(act), act.blocks


def _with(op):
    """The full answer with one operation replaced (the form needs every instruction answered)."""
    ops = [o for o in ANSWER["operations"] if o["id"] != op["id"]] + [op]
    return {"material": 1, "operations": ops}


@pytest.mark.parametrize("answer, message", [
    (_with({"id": "§1.1", "kind": "rewrite", "address": "чл. 2"}), "not one of"),
    ({"operations": ANSWER["operations"] + [{"id": "§9", "kind": "repeal", "address": "чл. 2"}]}, "not an instruction"),
    (_with({"id": "§2", "kind": "repeal", "address": "чл. 9"}), "names 0 place"),
    (_with({"id": "§1.1", "kind": "replace_words", "address": "чл. 2, ал. 1, т. 2", "old": "q3", "new": "q2"}), "not a quoted segment"),
    (_with({"id": "§1.1", "kind": "replace_words", "address": "чл. 2", "old": "q1", "new": "q2", "extra": 1}), "outside the form"),
    (_with({"id": "§1.2", "kind": "insert_provision", "address": "чл. 2, ал. 4", "after": "чл. 2, ал. 3", "blocks": [4, 4]}), "outside the instruction's quoted text"),
    (_with({"id": "§3", "kind": "insert_provision", "address": "чл. 3а", "after": "чл. 3", "blocks": [10, 12]}), "outside the instruction's quoted text"),
    (_with({"id": "§3", "kind": "insert_provision", "address": "чл. 3б", "after": "чл. 3", "blocks": [10, 11]}), "the address names article '3б'"),
    (_with({"id": "§4", "kind": "delete_words", "address": "чл. 2", "old": "q1"}), "do not occur"),
    (_with({"id": "§4", "kind": "delete_words", "address": "чл. 1, предложение второ", "old": "q1"}), "a part the grammar does not read"),
    ({"operations": [o for o in ANSWER["operations"] if o["id"] != "§6"]}, "no operation for the instruction"),
])
def test_the_form_check_refuses_and_applies_nothing(answer, message):
    mat, blocks = _mat()
    with pytest.raises(O.FormError, match=message):
        O.apply(answer, mat, blocks, BODY, "96/2026")


def test_a_word_that_occurs_twice_needs_everywhere():
    mat, blocks = _mat_with("§ 1. В чл. 2 думите „алинея“ се заменят с „ал.“.")
    with pytest.raises(O.FormError, match="occur 2 times"):
        O.apply({"operations": [{"id": "§1", "kind": "replace_words", "address": "чл. 2", "old": "q1", "new": "q2"}]}, mat, blocks, BODY, "96/2026")
    out = O.apply({"operations": [{"id": "§1", "kind": "replace_words", "address": "чл. 2", "old": "q1", "new": "q2", "everywhere": True}]}, mat, blocks, BODY, "96/2026")
    assert "Втора ал." in out.markdown and "Трета ал." in out.markdown and "алинея" not in out.markdown


def test_replace_provision_and_heading_and_annex():
    mat, blocks = _mat_with("§ 1. Член 1 се изменя така:")
    blocks.insert(4, Block(4, "„Чл. 1. Новият текст.“", "DvJustify"))
    for k, b in enumerate(blocks):
        b.i = k
    mat = M.parse(SplitAct(blocks=blocks, sections=[], source="dv"))
    out = O.apply({"operations": [{"id": "§1", "kind": "replace_provision", "address": "чл. 1", "blocks": [4, 4]}]}, mat, blocks, BODY, "96/2026")
    t = T.parse(out.markdown)
    assert t.lines[T.resolve(t, "чл. 1")].text == "**Чл. 1.** (Изм. - ДВ, бр. 96 от 2026 г.) Новият текст."
    mat2, blocks2 = _mat_with("§ 1. В наименованието думите „пробата“ се заменят с „новата проба“.")
    out2 = O.apply({"operations": [{"id": "§1", "kind": "replace_heading", "address": "наименованието", "new": "q2"}]}, mat2, blocks2, BODY, "96/2026")
    assert out2.markdown.startswith("# новата проба\n")
    task = O.task_text(mat, blocks, T.parse(BODY), "zakon-za-probata", "96/2026", "a.json", [])
    assert "current text at „чл. 1“" in task and "no_text_change" in task


INLINE_BODY = """# ЗАКОН за пробата

**Чл. 6.** (1) Министърът провежда политиката.

(2) Министърът утвърждава плана.

(3) Трета алинея.

**Чл. 7.** Член седем.
"""


def test_an_inline_first_alinea_is_its_own_address():
    # the review of 1 November 2026, B1: operations on „чл. 6, ал. 1“ touch the alinea written in the head line, nothing else
    mat, blocks = _mat_with("§ 1. В чл. 6, ал. 1 думите „утвърждава“ се заменят с „приема“.")
    with pytest.raises(O.FormError, match="do not occur"):
        O.apply({"operations": [{"id": "§1", "kind": "replace_words", "address": "чл. 6, ал. 1", "old": "q1", "new": "q2"}]}, mat, blocks, INLINE_BODY, "5/2026")
    mat, blocks = _mat_with("§ 1. В чл. 6, ал. 1 думите „провежда“ се заменят с „води“.")
    out = O.apply({"operations": [{"id": "§1", "kind": "replace_words", "address": "чл. 6, ал. 1", "old": "q1", "new": "q2"}]}, mat, blocks, INLINE_BODY, "5/2026")
    assert "**Чл. 6.** (1) (Изм. - ДВ, бр. 5 от 2026 г.) Министърът води политиката.\n\n(2) Министърът утвърждава плана." in out.markdown
    mat, blocks = _mat_with("§ 1. В чл. 6 ал. 1 се отменя.")
    out = O.apply({"operations": [{"id": "§1", "kind": "repeal", "address": "чл. 6, ал. 1"}]}, mat, blocks, INLINE_BODY, "5/2026")
    assert "**Чл. 6.** (1) (Отм. - ДВ, бр. 5 от 2026 г.)\n\n(2) Министърът утвърждава плана.\n\n(3) Трета алинея." in out.markdown
    mat, blocks = _mat_with("§ 1. В чл. 6 се създава ал. 1а:")
    blocks.insert(4, Block(4, "„(1а) Нова алинея.“", "DvJustify"))
    for k, b in enumerate(blocks):
        b.i = k
    mat = M.parse(SplitAct(blocks=blocks, sections=[], source="dv"))
    out = O.apply({"operations": [{"id": "§1", "kind": "insert_provision", "address": "чл. 6, ал. 1а", "after": "чл. 6, ал. 1", "blocks": [4, 4]}]}, mat, blocks, INLINE_BODY, "5/2026")
    assert "(1) Министърът провежда политиката.\n\n(1а) (Нова - ДВ, бр. 5 от 2026 г.) Нова алинея.\n\n(2) Министърът" in out.markdown
    # the whole article: the marker goes after the head, before the inline alinea
    mat, blocks = _mat_with("§ 1. В чл. 6 думите „Министърът“ се заменят с „Министерството“.")
    out = O.apply({"operations": [{"id": "§1", "kind": "replace_words", "address": "чл. 6", "old": "q1", "new": "q2", "everywhere": True}]}, mat, blocks, INLINE_BODY, "5/2026")
    assert "**Чл. 6.** (Изм. - ДВ, бр. 5 от 2026 г.) (1) Министерството провежда политиката.\n\n(2) Министерството утвърждава плана." in out.markdown


def test_headings_and_annexes_keep_their_number_and_take_the_marker_at_the_end():
    # B2
    mat, blocks = _mat_with("§ 1. В наименованието на глава първа думите „ОБЩИ ПОЛОЖЕНИЯ“ се заменят с „Нови положения“.")
    out = O.apply({"operations": [{"id": "§1", "kind": "replace_heading", "address": "глава първа", "new": "q2"}]}, mat, blocks, BODY, "5/2026")
    assert "### Глава първа Нови положения (Загл. изм. - ДВ, бр. 5 от 2026 г.)" in out.markdown
    t = T.parse(out.markdown)
    assert T.resolve(t, "глава първа") == 1
    annex_body = BODY + "\n## Приложение № 1 към чл. 1\n\nред първи\n\nред втори\n"
    mat, blocks = _mat_with("§ 1. Приложение № 1 към чл. 1 се отменя.")
    out = O.apply({"operations": [{"id": "§1", "kind": "repeal_annex", "address": "Приложение № 1"}]}, mat, blocks, annex_body, "5/2026")
    assert out.markdown.endswith("## Приложение № 1 към чл. 1 (Отм. - ДВ, бр. 5 от 2026 г.)\n") and "ред първи" not in out.markdown
    mat, blocks = _mat_with("§ 1. Приложение № 1 към чл. 1 се изменя така:")
    blocks[4:4] = [Block(4, "„Приложение № 1 към чл. 1", "DvCenter"), Block(5, "нов ред“", "DvJustify")]
    for k, b in enumerate(blocks):
        b.i = k
    mat = M.parse(SplitAct(blocks=blocks, sections=[], source="dv"))
    out = O.apply({"operations": [{"id": "§1", "kind": "replace_annex", "address": "Приложение № 1", "blocks": [4, 5]}]}, mat, blocks, annex_body, "5/2026")
    assert out.markdown.endswith("## Приложение № 1 към чл. 1 (Изм. - ДВ, бр. 5 от 2026 г.)\n\nнов ред\n")
    t = T.parse(out.markdown)
    assert t.lines[-1].kind == "annex_row" and t.lines[-2].kind == "annex_heading"


def test_markers_merge_and_carry_and_sentences_and_the_whole_act():
    # M2: two operations of one issue on one line; the earlier marker survives a replaced provision; the gender of „Предишен“
    mat, blocks = _mat_with("§ 1. В чл. 1 думите „урежда“ се заменят с „определя“ и накрая се добавя „изцяло“.")
    out = O.apply({"operations": [{"id": "§1", "kind": "replace_words", "address": "чл. 1", "old": "q1", "new": "q2"},
                                  {"id": "§1", "kind": "insert_words", "address": "чл. 1", "where": "end", "new": "q3"}]}, mat, blocks, BODY, "5/2026")
    assert "**Чл. 1.** (Изм. и доп. - ДВ, бр. 5 от 2026 г.) Този закон определя пробата изцяло." in out.markdown
    mat, blocks = _mat_with("§ 1. Член 1 се изменя така:")
    blocks.insert(4, Block(4, "„Чл. 1. Съвсем нов текст.“", "DvJustify"))
    for k, b in enumerate(blocks):
        b.i = k
    mat = M.parse(SplitAct(blocks=blocks, sections=[], source="dv"))
    out2 = O.apply({"operations": [{"id": "§1", "kind": "replace_provision", "address": "чл. 1", "blocks": [4, 4]}]}, mat, blocks, out.markdown, "10/2027")
    assert "**Чл. 1.** (Изм. и доп. - ДВ, бр. 5 от 2026 г., изм. - ДВ, бр. 10 от 2027 г.) Съвсем нов текст." in out2.markdown
    mat, blocks = _mat_with("§ 1. Член 3 става чл. 4.")
    out3 = O.apply({"operations": [{"id": "§1", "kind": "renumber", "address": "чл. 3", "to": "чл. 4"}]}, mat, blocks, BODY, "5/2026")
    assert "**Чл. 4.** (Предишен чл. 3 - ДВ, бр. 5 от 2026 г.) Член за отмяна." in out3.markdown
    # B3 / sentences: the second sentence only
    two = BODY.replace("**Чл. 1.** Този закон урежда пробата.", "**Чл. 1.** Този закон урежда пробата. Той важи навсякъде.")
    mat, blocks = _mat_with("§ 1. В чл. 1, изречение второ накрая се добавя „в страната“.")
    out4 = O.apply({"operations": [{"id": "§1", "kind": "insert_words", "address": "чл. 1, изречение второ", "where": "end", "new": "q1"}]}, mat, blocks, two, "5/2026")
    assert "Този закон урежда пробата. Той важи навсякъде в страната." in out4.markdown
    # M4: the whole act
    mat, blocks = _mat_with("§ 1. Навсякъде в закона думите „пробата“ се заменят с „опита“.")
    out5 = O.apply({"operations": [{"id": "§1", "kind": "replace_words", "address": "навсякъде", "old": "q1", "new": "q2"}]}, mat, blocks, BODY, "5/2026")
    assert "пробата" not in out5.markdown.split("\n\n", 1)[1] and "# ЗАКОН за пробата" in out5.markdown and "Този закон урежда опита." in out5.markdown


def test_round_three_the_lead_in_the_annex_name_the_heading_repeal_and_the_marker_history():
    lead_body = """# ЗАКОН за пробата

### Глава първа ОБЩИ ПОЛОЖЕНИЯ (НОВА - ДВ, БР. 42 ОТ 2018 Г.)

**Чл. 2.** (1) Определя се от министъра:

1. министъра на реда;

2. друго.

**Чл. 3.** Трети член.

### Глава двадесет и първа ПОСЛЕДНА

**Чл. 4.** Четвърти.

## Приложение № 3 към чл. 2

ред
"""
    # blocking 1: „текста преди т. 1“ is the provision's own words, never т. 1
    mat, blocks = _mat_with("§ 1. В чл. 2, ал. 1, текста преди т. 1 думата „министъра“ се заменя с „министъра на транспорта“.")
    out = O.apply({"operations": [{"id": "§1", "kind": "replace_words", "address": "чл. 2, ал. 1, текста преди т. 1", "old": "q1", "new": "q2"}]}, mat, blocks, lead_body, "96/2026")
    assert "**Чл. 2.** (1) (Изм. - ДВ, бр. 96 от 2026 г.) Определя се от министъра на транспорта:\n\n1. министъра на реда;" in out.markdown
    with pytest.raises(O.FormError, match="do not occur"):
        O.apply({"operations": [{"id": "§1", "kind": "replace_words", "address": "чл. 2, ал. 1, текста преди т. 1", "old": "q1", "new": "q2"}]}, mat, blocks,
                lead_body.replace("Определя се от министъра:", "Определя се:"), "96/2026")
    # blocking 2: an annex heading keeps its reference
    mat, blocks = _mat_with("§ 1. В наименованието на приложение № 3 се добавя „към чл. 2 и чл. 3“.")
    out = O.apply({"operations": [{"id": "§1", "kind": "replace_heading", "address": "Приложение № 3", "new": "q1"}]}, mat, blocks, lead_body, "96/2026")
    assert "## Приложение № 3 към чл. 2 към чл. 2 и чл. 3 (Загл. изм. - ДВ, бр. 96 от 2026 г.)" in out.markdown
    # blocking 3: a repealed chapter keeps its articles as repealed heads
    mat, blocks = _mat_with("§ 1. Глава първа се отменя.")
    out = O.apply({"operations": [{"id": "§1", "kind": "repeal", "address": "глава първа"}]}, mat, blocks, lead_body, "96/2026")
    assert "### Глава първа ОБЩИ ПОЛОЖЕНИЯ (НОВА - ДВ, БР. 42 ОТ 2018 Г., отм. - ДВ, бр. 96 от 2026 г.)\n\n**Чл. 2.** (Отм. - ДВ, бр. 96 от 2026 г.)\n\n**Чл. 3.** (Отм. - ДВ, бр. 96 от 2026 г.)\n\n### Глава двадесет и първа" in out.markdown
    # major 4 and 5: the marker history of a heading survives a rename; a compound chapter number is one number
    mat, blocks = _mat_with("§ 1. В наименованието на глава първа думите „ОБЩИ ПОЛОЖЕНИЯ“ се заменят с „НАЧАЛО“.")
    out = O.apply({"operations": [{"id": "§1", "kind": "replace_heading", "address": "глава първа", "new": "q2"}]}, mat, blocks, lead_body, "96/2026")
    assert "### Глава първа НАЧАЛО (НОВА - ДВ, БР. 42 ОТ 2018 Г., загл. изм. - ДВ, бр. 96 от 2026 г.)" in out.markdown
    t = T.parse(lead_body)
    assert t.lines[T.resolve(t, "глава двадесет и първа")].n == "двадесет и първа"
    mat, blocks = _mat_with("§ 1. В наименованието на глава двадесет и първа думата „ПОСЛЕДНА“ се заменя с „КРАЙНА“.")
    out = O.apply({"operations": [{"id": "§1", "kind": "replace_heading", "address": "глава двадесет и първа", "new": "q2"}]}, mat, blocks, lead_body, "96/2026")
    assert "### Глава двадесет и първа КРАЙНА (Загл. изм. - ДВ, бр. 96 от 2026 г.)" in out.markdown
    # major 7: an act-wide replace marks every changed line
    mat, blocks = _mat_with("§ 1. Навсякъде в закона думата „министъра“ се заменя с „министъра на реда“.")
    out = O.apply({"operations": [{"id": "§1", "kind": "replace_words", "address": "навсякъде", "old": "q1", "new": "q2"}]}, mat, blocks, lead_body, "96/2026")
    assert "на реда на реда" not in out.markdown   # a place that already reads the new words is not extended again (ODZ, 1 November 2026)
    assert "(изм. - дв, бр. 96 от 2026 г.)" in out.markdown.lower() and "министъра на реда" in out.markdown
    # major 8: words cannot land between a head and its inline alinea
    mat, blocks = _mat_with("§ 1. В чл. 2 накрая се добавя „и още“.")
    with pytest.raises(O.FormError, match="are in its alineas"):
        O.apply({"operations": [{"id": "§1", "kind": "insert_words", "address": "чл. 2", "where": "end", "new": "q1"}]}, mat, blocks, lead_body, "96/2026")


def test_a_child_scope_keeps_its_parents_quotes():
    # major 6: „§ 5. В следните закони думите „X“ се заменят с „Y“: 1. в Закона за пробата – в чл. 1; 2. в Закона за друго – в чл. 9.“
    from reading.steps import _scoped
    lines = ["ЗАКОН", "за изменение на нормативни актове", "(обн., ДВ, бр. 1 от 2020 г.)",
             "§ 5. В следните закони думите „урежда“ се заменят с „определя“:", "1. в Закона за пробата (обн., ДВ, бр. 1 от 2020 г.) – в чл. 1;", "2. в Закона за друго (обн., ДВ, бр. 2 от 2020 г.) – в чл. 9.",
             "Законът е приет.", "Председател на Народното събрание: Х", "1"]
    act = SplitAct(blocks=[Block(i, t, {0: "DvCenter", 1: "DvCenter", 2: "DvCenter", 7: "DvRight"}.get(i, "DvJustify")) for i, t in enumerate(lines)], sections=[], source="dv")
    mat = M.parse(act)
    scoped = _scoped(mat, ["§5.1"])
    assert [n.id for n in scoped.instructions()] == ["§5", "§5.1"] and scoped.nodes[0].inline_quotes == ["урежда", "определя"]
    whole = _scoped(mat, ["§5"])
    assert [n.id for n in whole.instructions()] == ["§5", "§5.1", "§5.2"], "a § attributed as a whole keeps its items"
    out = O.apply({"operations": [{"id": "§5.1", "kind": "replace_words", "address": "чл. 1", "old": "q1", "new": "q2"}]}, scoped, act.blocks, BODY, "96/2026")
    assert "**Чл. 1.** (Изм. - ДВ, бр. 96 от 2026 г.) Този закон определя пробата." in out.markdown


def test_a_text_reference_where_nested_marks_cut_the_segment():
    mat, blocks = _mat_with("§ 1. В чл. 1 думите “закон урежда “пробата” се заменят с “закон определя опита”.")
    assert mat.nodes[0].inline_quotes[0] == "закон урежда "   # the Gazette's nested marks cut q1 short
    out = O.apply({"operations": [{"id": "§1", "kind": "replace_words", "address": "чл. 1", "old": {"text": "закон урежда “пробата”"}, "new": "q2"}]}, mat, blocks,
                  BODY.replace("Този закон урежда пробата.", "Този закон урежда “пробата”."), "96/2026")
    assert "**Чл. 1.** (Изм. - ДВ, бр. 96 от 2026 г.) Този закон определя опита." in out.markdown
    with pytest.raises(O.FormError, match="does not stand in the instruction"):
        O.apply({"operations": [{"id": "§1", "kind": "replace_words", "address": "чл. 1", "old": {"text": "думи от другаде"}, "new": "q2"}]}, mat, blocks, BODY, "96/2026")


def test_a_range_inside_the_instructions_quoted_run_need_not_open_or_close_the_quotation():
    lines = ["ЗАКОН", "за изменение на Закона за пробата", "(обн., ДВ, бр. 1 от 2020 г.)", "§ 1. В глава първа се създава раздел II с чл. 1а и 1б:",
             "„Раздел II", "Нови правила", "Чл. 1а. Първи нов.", "Чл. 1б. Втори нов.“",
             "Законът е приет.", "Председател на Народното събрание: Х", "1"]
    act = SplitAct(blocks=[Block(i, t, {0: "DvCenter", 1: "DvCenter", 2: "DvCenter", 4: "DvCenter", 5: "DvCenter", 9: "DvRight"}.get(i, "DvJustify")) for i, t in enumerate(lines)], sections=[], source="dv")
    mat = M.parse(act)
    assert mat.nodes[0].quoted == [4, 5, 6, 7]
    out = O.apply({"operations": [{"id": "§1", "kind": "insert_heading", "address": "глава първа, раздел II", "after": "чл. 3", "blocks": [4, 5]},
                                  {"id": "§1", "kind": "insert_provision", "address": "чл. 1а", "after": "глава първа, раздел II", "blocks": [6, 6]},
                                  {"id": "§1", "kind": "insert_provision", "address": "чл. 1б", "after": "чл. 1а", "blocks": [7, 7]}]}, mat, act.blocks, BODY, "96/2026")
    assert "#### Раздел II Нови правила (Нова - ДВ, бр. 96 от 2026 г.)\n\n**Чл. 1а.** (Нов - ДВ, бр. 96 от 2026 г.) Първи нов.\n\n**Чл. 1б.** (Нов - ДВ, бр. 96 от 2026 г.) Втори нов." in out.markdown


def test_a_sentence_replaced_whole_and_an_annex_printed_after_the_act():
    two = BODY.replace("**Чл. 1.** Този закон урежда пробата.", "**Чл. 1.** Този закон урежда пробата. Той важи навсякъде.")
    mat, blocks = _mat_with("§ 1. В чл. 1 изречение първо се изменя така: „Този закон определя опита.“")
    out = O.apply({"operations": [{"id": "§1", "kind": "replace_sentence", "address": "чл. 1, изречение първо", "new": "q1"}]}, mat, blocks, two, "96/2026")
    assert "**Чл. 1.** (Изм. - ДВ, бр. 96 от 2026 г.) Този закон определя опита. Той важи навсякъде." in out.markdown
    lines = ["ЗАКОН", "за изменение на Закона за пробата", "(обн., ДВ, бр. 1 от 2020 г.)", "§ 1. Създава се приложение № 1 към чл. 1.",
             "Приложение № 1 към чл. 1", "ред първи", "ред втори", "Законът е приет.", "Председател на Народното събрание: Х", "1"]
    act = SplitAct(blocks=[Block(i, t, {0: "DvCenter", 1: "DvCenter", 2: "DvCenter", 4: "DvCenter", 8: "DvRight"}.get(i, "DvJustify")) for i, t in enumerate(lines)], sections=[], source="dv")
    mat = M.parse(act)
    assert mat.nodes[0].continuation == [5, 6] or mat.roles[4] in ("heading", "continuation")
    cont = mat.nodes[0].continuation
    out = O.apply({"operations": [{"id": "§1", "kind": "insert_annex", "address": "Приложение № 1", "after": "", "blocks": [cont[0], cont[-1]]}]}, mat, act.blocks, BODY, "96/2026") if mat.roles[4] == "continuation" else None
    if out is not None:
        assert out.markdown.rstrip().endswith("ред втори")


def test_a_new_item_at_a_taken_number_moves_the_former_items_first_highest_first():
    body = BODY.replace("2. втора, до 30 000 лв.", "2. втора, до 30 000 лв.;\n\n3. трета;")
    lines = ["ЗАКОН", "за изменение на Закона за пробата", "(обн., ДВ, бр. 1 от 2020 г.)", "§ 1. В чл. 2, ал. 1 се правят следните допълнения:",
             "1. Създава се нова т. 2:", "„2. нова втора;“", "2. Досегашните т. 2 и 3 стават съответно т. 3 и 4.",
             "Законът е приет.", "Председател на Народното събрание: Х", "1"]
    act = SplitAct(blocks=[Block(i, t, {0: "DvCenter", 1: "DvCenter", 2: "DvCenter", 8: "DvRight"}.get(i, "DvJustify")) for i, t in enumerate(lines)], sections=[], source="dv")
    mat = M.parse(act)
    answer = {"operations": [{"id": "§1", "kind": "no_text_change"},
                             {"id": "§1.1", "kind": "insert_provision", "address": "чл. 2, ал. 1, т. 2", "after": "чл. 2, ал. 1, т. 1", "blocks": [5, 5]},
                             {"id": "§1.2", "kind": "renumber", "address": "чл. 2, ал. 1, т. 2", "to": "т. 3"},
                             {"id": "§1.2", "kind": "renumber", "address": "чл. 2, ал. 1, т. 3", "to": "т. 4"}]}
    out = O.apply(answer, mat, act.blocks, body, "96/2026")
    t = T.parse(out.markdown)
    assert [t.lines[k].text for k in t.subtree(T.resolve(t, "чл. 2, ал. 1")) if t.lines[k].kind == "item"] == [
        "1. първа;", "2. (нова - ДВ, бр. 96 от 2026 г.) нова втора;", "3. (предишна т. 2 - ДВ, бр. 96 от 2026 г.) втора, до 30 000 лв.;",
        "4. (предишна т. 3 - ДВ, бр. 96 от 2026 г.) трета;"]
    assert out.log[1].startswith("§1.2 renumber: 3 -> 4 (moved before §1.1)") and out.log[2].startswith("§1.2 renumber: 2 -> 3")
    # a taken number with no renumber to move it is refused
    with pytest.raises(O.FormError, match="already carried"):
        O.apply({"operations": answer["operations"][:2] + [{"id": "§1.2", "kind": "no_text_change"}]}, mat, act.blocks, body, "96/2026")


def test_a_number_matches_a_whole_number_only():
    body = BODY.replace("**Чл. 1.** Този закон урежда пробата.", "**Чл. 1.** По чл. 11, ал. 1, чл. 13, ал. 2 или по чл. 11, ал. 4 и 5.")
    mat, blocks = _mat_with("§ 1. В чл. 1 след цифрата „1“ се добавя „или ал. 4“, а цифрите „4“ и „5“ се заменят съответно с „5“ и „6“.")
    out = O.apply({"operations": [{"id": "§1", "kind": "replace_words", "address": "чл. 1", "old": "q4", "new": "q6"},
                                  {"id": "§1", "kind": "replace_words", "address": "чл. 1", "old": "q3", "new": "q5"},
                                  {"id": "§1", "kind": "insert_words", "address": "чл. 1", "anchor": "q1", "where": "after", "new": "q2"}]}, mat, blocks, body, "96/2026")
    assert "По чл. 11, ал. 1 или ал. 4, чл. 13, ал. 2 или по чл. 11, ал. 5 и 6." in out.markdown
    # words match whole words: the Gazette names the form it means, never a stem
    with pytest.raises(O.FormError, match="do not occur"):
        O.apply({"operations": [{"id": "§1", "kind": "replace_words", "address": "чл. 1", "old": "q1", "new": "q2"}]},
                *_mat_with("§ 1. В чл. 1 думата „проба“ се заменя с „опит“."), BODY, "96/2026")
    out2 = O.apply({"operations": [{"id": "§1", "kind": "replace_words", "address": "чл. 1", "old": "q1", "new": "q2"}]},
                   *_mat_with("§ 1. В чл. 1 думата „пробата“ се заменя с „опита“."), BODY, "96/2026")
    assert "Този закон урежда опита." in out2.markdown


def test_deleted_words_take_the_comma_the_instruction_names_with_them():
    body = BODY.replace("**Чл. 1.** Този закон урежда пробата.", "**Чл. 1.** Този закон урежда пробата, както и опита, за всички.")
    mat, blocks = _mat_with("§ 1. В чл. 1 думите „както и опита“ и запетаята пред тях се заличават.")
    out = O.apply({"operations": [{"id": "§1", "kind": "delete_words", "address": "чл. 1", "old": "q1", "punctuation": "before"}]}, mat, blocks, body, "96/2026")
    assert "**Чл. 1.** (Изм. - ДВ, бр. 96 от 2026 г.) Този закон урежда пробата, за всички." in out.markdown
    out = O.apply({"operations": [{"id": "§1", "kind": "delete_words", "address": "чл. 1", "old": "q1", "punctuation": "after"}]}, mat, blocks, body, "96/2026")
    assert "Този закон урежда пробата, за всички." in out.markdown
    mat2, blocks2 = _mat_with("§ 1. В чл. 1 след думите „закон“ се поставя запетая и се добавя „който е пробен“.")
    out = O.apply({"operations": [{"id": "§1", "kind": "insert_words", "address": "чл. 1", "anchor": "q1", "where": "after", "new": "q2", "punctuation": "before"}]}, mat2, blocks2, BODY, "96/2026")
    assert "Този закон, който е пробен урежда пробата." in out.markdown
    with pytest.raises(O.FormError, match="before or after, for delete_words"):
        O.check_form({"operations": [{"id": "§1", "kind": "replace_words", "address": "чл. 1", "old": "q1", "new": "q1", "punctuation": "before"}]}, mat, blocks)
    with pytest.raises(O.FormError, match="no comma or semicolon stands before"):
        O.apply({"operations": [{"id": "§1", "kind": "delete_words", "address": "чл. 1", "old": "q1", "punctuation": "before"}]},
                *_mat_with("§ 1. В чл. 1 думите „урежда“ и запетаята пред тях се заличават."), BODY, "96/2026")


def test_a_quoted_run_the_parser_closed_by_the_sequence_is_taken_as_closed():
    lines = ["ЗАКОН", "за изменение на Закона за пробата", "(обн., ДВ, бр. 1 от 2020 г.)", "§ 1. Член 3 се изменя така:",
             "„Чл. 3. Нов текст без затваряща кавичка.", "Заключителна разпоредба", "§ 2. Законът влиза в сила от 1 януари 2027 г.",
             "Законът е приет.", "Председател на Народното събрание: Х", "1"]
    act = SplitAct(blocks=[Block(i, t, {0: "DvCenter", 1: "DvCenter", 2: "DvCenter", 5: "DvCenter", 8: "DvRight"}.get(i, "DvJustify")) for i, t in enumerate(lines)], sections=[], source="dv")
    mat = M.parse(act)
    assert [f["kind"] for f in mat.findings] == ["quote_closed_by_sequence"] and mat.findings[0]["block"] == 5
    out = O.apply({"operations": [{"id": "§1", "kind": "replace_provision", "address": "чл. 3", "blocks": [4, 4]}, {"id": "§2", "kind": "no_text_change"}]}, mat, act.blocks, BODY, "96/2026")
    assert "**Чл. 3.** (Изм. - ДВ, бр. 96 от 2026 г.) Нов текст без затваряща кавичка." in out.markdown


def test_an_unnumbered_annex_is_named_by_its_provision():
    body = BODY + "\n## Приложениекъм чл. 1\n\nстар ред\n\n## Приложение към чл. 2, ал. 2 Численост\n\nред А\n\n5\n"
    assert T.parse_address("Приложението към чл. 2, ал. 2") == [("annex_heading", "към чл. 2, ал. 2")]
    assert T.parse_address("Приложение към чл.1") == [("annex_heading", "към чл. 1")]
    t = T.parse(body)
    assert t.lines[T.resolve(t, "Приложението към чл. 2, ал. 2")].text.startswith("## Приложение към чл. 2, ал. 2")
    assert t.lines[T.resolve(t, "приложение към чл. 1")].text == "## Приложениекъм чл. 1"
    lines = ["ЗАКОН", "за изменение на Закона за пробата", "(обн., ДВ, бр. 1 от 2020 г.)", "§ 1. Приложението към чл. 2, ал. 2 се изменя, както следва:",
             "„Приложение към чл. 2, ал. 2", "Численост", "ред Б", "7“", "Законът е приет.", "Председател на Народното събрание: Х", "1"]
    act = SplitAct(blocks=[Block(i, t, {0: "DvCenter", 1: "DvCenter", 2: "DvCenter", 4: "DvCenter", 9: "DvRight"}.get(i, "DvJustify")) for i, t in enumerate(lines)], sections=[], source="dv")
    mat = M.parse(act)
    out = O.apply({"operations": [{"id": "§1", "kind": "replace_annex", "address": "Приложението към чл. 2, ал. 2", "blocks": [4, 7]}]}, mat, act.blocks, body, "96/2026")
    assert out.markdown.rstrip().endswith("## Приложение към чл. 2, ал. 2 (Изм. - ДВ, бр. 96 от 2026 г.)\n\nЧисленост\n\nред Б\n\n7") and "ред А" not in out.markdown
    with pytest.raises(T.AddressError, match="not a provision the grammar reads"):
        T.parse_address("Приложение към наредбата")


def test_an_articles_text_becomes_its_first_alinea():
    lines = ["ЗАКОН", "за изменение на Закона за пробата", "(обн., ДВ, бр. 1 от 2020 г.)", "§ 1. В чл. 2 досегашният текст става ал. 1 и в нея т. 1 се изменя така:",
             "„1. нова първа;“", "Законът е приет.", "Председател на Народното събрание: Х", "1"]
    act = SplitAct(blocks=[Block(i, t, {0: "DvCenter", 1: "DvCenter", 2: "DvCenter", 6: "DvRight"}.get(i, "DvJustify")) for i, t in enumerate(lines)], sections=[], source="dv")
    mat, blocks = M.parse(act), act.blocks
    body = BODY.replace("**Чл. 2.** (1) Пробата е:", "**Чл. 2.** Пробата е:").replace("(2) Втора алинея.\n\n(3) Трета алинея.\n\n", "")
    out = O.apply({"operations": [{"id": "§1", "kind": "renumber", "address": "чл. 2", "to": "ал. 1"},
                                  {"id": "§1", "kind": "replace_provision", "address": "чл. 2, ал. 1, т. 1", "blocks": [4, 4]}]}, mat, blocks, body, "96/2026")
    assert "**Чл. 2.** (1) (Предишен текст на чл. 2 - ДВ, бр. 96 от 2026 г.) Пробата е:\n\n1. (изм. - ДВ, бр. 96 от 2026 г.) нова първа;\n\n2. втора, до 30 000 лв." in out.markdown
    with pytest.raises(O.FormError, match="already has alineas"):
        O.apply({"operations": [{"id": "§1", "kind": "renumber", "address": "чл. 2", "to": "ал. 1"}]}, mat, blocks, BODY, "96/2026")


def test_a_quoted_title_line_before_a_new_article_is_its_title():
    body = BODY.replace("**Чл. 1.** Този закон урежда пробата.", "Предмет **Чл. 1.** Този закон урежда пробата.")
    lines = ["ЗАКОН", "за изменение на Закона за пробата", "(обн., ДВ, бр. 1 от 2020 г.)", "§ 1. Създава се чл. 1а:",
             "„Обхват на пробата", "Чл. 1а. (1) Пробата има обхват.", "(2) Втора.“", "Законът е приет.", "Председател на Народното събрание: Х", "1"]
    act = SplitAct(blocks=[Block(i, t, {0: "DvCenter", 1: "DvCenter", 2: "DvCenter", 4: "DvCenter", 8: "DvRight"}.get(i, "DvJustify")) for i, t in enumerate(lines)], sections=[], source="dv")
    mat = M.parse(act)
    out = O.apply({"operations": [{"id": "§1", "kind": "insert_provision", "address": "чл. 1а", "after": "чл. 1", "blocks": [4, 6]}]}, mat, act.blocks, body, "96/2026")
    assert "Обхват на пробата **Чл. 1а.** (Нов - ДВ, бр. 96 от 2026 г.) (1) Пробата има обхват.\n\n(2) Втора." in out.markdown
    t = T.parse(out.markdown)
    assert t.lines[T.resolve(t, "чл. 1а")].title == "Обхват на пробата"


def test_the_space_before_an_ellipsis_is_free_and_a_sentence_can_be_repealed():
    body = BODY.replace("**Чл. 1.** Този закон урежда пробата.", "**Чл. 1.** Този закон урежда „лекар, специализант по …“, „фармацевт, специализант по …“. Второ изречение.")
    mat, blocks = _mat_with("§ 1. В чл. 1 думите „лекар, специализант по…“ се заличават.")
    out = O.apply({"operations": [{"id": "§1", "kind": "delete_words", "address": "чл. 1", "old": "q1"}]}, mat, blocks, body, "96/2026")
    assert "Този закон урежда „“, „фармацевт, специализант по …“. Второ изречение." in out.markdown
    out = O.apply({"operations": [{"id": "§1", "kind": "repeal", "address": "чл. 1, изречение второ"}]}, *_mat_with("§ 1. В чл. 1 изречение второ се заличава."), body, "96/2026")
    assert "**Чл. 1.** (Изм. - ДВ, бр. 96 от 2026 г.) Този закон урежда „лекар, специализант по …“, „фармацевт, специализант по …“." in out.markdown


def test_a_new_sentence_joins_the_provision_and_a_moved_alinea_is_followed_to_its_new_number():
    lines = ["ЗАКОН", "за изменение на Закона за пробата", "(обн., ДВ, бр. 1 от 2020 г.)", "§ 1. В чл. 1 се създава изречение второ:",
             "„Той важи навсякъде.“", "Законът е приет.", "Председател на Народното събрание: Х", "1"]
    act = SplitAct(blocks=[Block(i, t, {0: "DvCenter", 1: "DvCenter", 2: "DvCenter", 6: "DvRight"}.get(i, "DvJustify")) for i, t in enumerate(lines)], sections=[], source="dv")
    mat = M.parse(act)
    out = O.apply({"operations": [{"id": "§1", "kind": "insert_provision", "address": "чл. 1, изречение второ", "after": "", "blocks": [4, 4]}]}, mat, act.blocks, BODY, "96/2026")
    assert "**Чл. 1.** (Доп. - ДВ, бр. 96 от 2026 г.) Този закон урежда пробата. Той важи навсякъде." in out.markdown
    with pytest.raises(O.FormError, match="has 1 sentence"):
        O.apply({"operations": [{"id": "§1", "kind": "insert_provision", "address": "чл. 1, изречение трето", "after": "", "blocks": [4, 4]}]}, mat, act.blocks, BODY, "96/2026")
    lines = ["ЗАКОН", "за изменение на Закона за пробата", "(обн., ДВ, бр. 1 от 2020 г.)", "§ 1. В чл. 2 се правят следните изменения и допълнения:",
             "1. Създава се нова ал. 2:", "„(2) Нова втора.“", "2. Досегашната ал. 2 става ал. 3 и в нея думите „Втора“ се заменят с „Бивша втора“.",
             "3. Досегашната ал. 3 става ал. 4.", "Законът е приет.", "Председател на Народното събрание: Х", "1"]
    act = SplitAct(blocks=[Block(i, t, {0: "DvCenter", 1: "DvCenter", 2: "DvCenter", 9: "DvRight"}.get(i, "DvJustify")) for i, t in enumerate(lines)], sections=[], source="dv")
    mat = M.parse(act)
    out = O.apply({"operations": [{"id": "§1", "kind": "no_text_change"},
                                  {"id": "§1.1", "kind": "insert_provision", "address": "чл. 2, ал. 2", "after": "чл. 2, ал. 1", "blocks": [5, 5]},
                                  {"id": "§1.2", "kind": "renumber", "address": "чл. 2, ал. 2", "to": "ал. 3"},
                                  {"id": "§1.2", "kind": "replace_words", "address": "чл. 2, ал. 2", "old": "q1", "new": "q2"},
                                  {"id": "§1.3", "kind": "renumber", "address": "чл. 2, ал. 3", "to": "ал. 4"}]}, mat, act.blocks, BODY, "96/2026")
    t = T.parse(out.markdown)
    assert [t.lines[k].text for k in t.subtree(T.resolve(t, "чл. 2")) if t.lines[k].kind == "alinea"] == [
        "(1) Пробата е:", "(2) (Нова - ДВ, бр. 96 от 2026 г.) Нова втора.",
        "(3) (Предишна ал. 2 - ДВ, бр. 96 от 2026 г., изм. - ДВ, бр. 96 от 2026 г.) Бивша втора алинея.",
        "(4) (Предишна ал. 3 - ДВ, бр. 96 от 2026 г.) Трета алинея."]
    assert O._renumbered_address("чл. 25, ал. 3", "ал. 4") == "чл. 25, ал. 4" and O._renumbered_address("чл. 5, т. 2, б. „а“", "б. „б“") == "чл. 5, т. 2, б. „б“"


def test_the_text_after_the_anchor_is_deleted_and_a_material_id_with_a_prefix_is_read():
    mat, blocks = _mat_with("§ 1. В чл. 1 след думите „урежда“ се поставя точка и текстът докрая се заличава.")
    out = O.apply({"material": "05-214105", "operations": [{"id": "§1", "kind": "delete_words", "address": "чл. 1", "anchor": "q1", "where": "after"}]}, mat, blocks, BODY, "96/2026")
    assert "**Чл. 1.** (Изм. - ДВ, бр. 96 от 2026 г.) Този закон урежда." in out.markdown and out.material == 214105
    with pytest.raises(O.FormError, match="needs where"):
        O.check_form({"operations": [{"id": "§1", "kind": "delete_words", "address": "чл. 1", "anchor": "q1"}]}, mat, blocks)


def test_a_range_renumber_moves_each_number_and_a_new_sentence_may_be_a_segment():
    body = BODY.replace("2. втора, до 30 000 лв.", "2. втора, до 30 000 лв.;\n\n3. трета;\n\n4. четвърта;")
    lines = ["ЗАКОН", "за изменение на Закона за пробата", "(обн., ДВ, бр. 1 от 2020 г.)", "§ 1. В чл. 2, ал. 1 се правят следните допълнения:",
             "1. Създава се нова т. 2:", "„2. нова втора;“", "2. Досегашните т. 2 – 4 стават съответно 3 – 5.",
             "Законът е приет.", "Председател на Народното събрание: Х", "1"]
    act = SplitAct(blocks=[Block(i, t, {0: "DvCenter", 1: "DvCenter", 2: "DvCenter", 8: "DvRight"}.get(i, "DvJustify")) for i, t in enumerate(lines)], sections=[], source="dv")
    mat = M.parse(act)
    out = O.apply({"operations": [{"id": "§1", "kind": "no_text_change"},
                                  {"id": "§1.1", "kind": "insert_provision", "address": "чл. 2, ал. 1, т. 2", "after": "чл. 2, ал. 1, т. 1", "blocks": [5, 5]},
                                  {"id": "§1.2", "kind": "renumber", "address": "чл. 2, ал. 1, т. 2 – 4", "to": "3 – 5"}]}, mat, act.blocks, body, "96/2026")
    t = T.parse(out.markdown)
    assert [l.n for l in t.lines if l.kind == "item"] == ["1", "2", "3", "4", "5"]
    assert t.lines[T.resolve(t, "чл. 2, ал. 1, т. 5")].text == "5. (предишна т. 4 - ДВ, бр. 96 от 2026 г.) четвърта;"
    with pytest.raises(O.FormError, match="differ in"):
        O.check_form({"operations": [{"id": "§1", "kind": "no_text_change"}, {"id": "§1.1", "kind": "no_text_change"},
                                     {"id": "§1.2", "kind": "renumber", "address": "чл. 2, ал. 1, т. 2 – 4", "to": "3 – 4"}]}, mat, act.blocks)
    mat2, blocks2 = _mat_with("§ 1. В чл. 1 се създава изречение второ: „Той важи навсякъде.“")
    out = O.apply({"operations": [{"id": "§1", "kind": "insert_provision", "address": "чл. 1, изречение второ", "new": "q1"}]}, mat2, blocks2, BODY, "96/2026")
    assert "**Чл. 1.** (Доп. - ДВ, бр. 96 от 2026 г.) Този закон урежда пробата. Той важи навсякъде." in out.markdown


def test_title_words_table_rows_and_annex_sections_are_addressed():
    body = BODY.replace("**Чл. 1.** Този закон урежда пробата.", "Канцелария **Чл. 1.** Този закон урежда пробата, както и опита, за всички.")
    body += "\n## Приложение към чл. 2, ал. 2 Обща численост – 1742 щатни бройки\n\nДирекция „Земеделие“ – Варна\n\n74\n\nДирекция „Земеделие“ – Видин\n\n63\n\n## Приложение № 1 към чл. 3\n\nI.\n\nПърви раздел\n\n1. ред\n\nII.\n\nВтори раздел\n\n2. ред\n\nIII.\n\nТрети\n"
    assert T.parse_address("наименованието на чл. 1") == [("article", "1"), ("article_title", "")]
    assert T.parse_address("Приложение към чл. 2, ал. 2, наименованието") == [("annex_heading", "към чл. 2, ал. 2"), ("article_title", "")]
    assert T.parse_address("Приложение към чл. 2, ал. 2, ред „Дирекция „Земеделие“ – Варна“") == [("annex_heading", "към чл. 2, ал. 2"), ("annex_row", "Дирекция „Земеделие“ – Варна")]
    assert T.parse_address("наименованието") == [("title", "")]
    # the article's title goes; the annex heading's number changes; a table row's number changes; a section of an annex is replaced
    mat, blocks = _mat_with("§ 1. Наименованието на чл. 1 „Канцелария“ се заличава.")
    out = O.apply({"operations": [{"id": "§1", "kind": "delete_words", "address": "наименованието на чл. 1", "old": "q1"}]}, mat, blocks, body, "96/2026")
    assert "\n**Чл. 1.** (Загл. отм. - ДВ, бр. 96 от 2026 г.) Този закон урежда пробата, както и опита, за всички." in out.markdown
    mat, blocks = _mat_with("§ 1. В приложението към чл. 2, ал. 2 в наименованието числото „1742“ се заменя с „1751“.")
    out = O.apply({"operations": [{"id": "§1", "kind": "replace_words", "address": "Приложение към чл. 2, ал. 2, наименованието", "old": "q1", "new": "q2"}]}, mat, blocks, body, "96/2026")
    assert "## Приложение към чл. 2, ал. 2 Обща численост – 1751 щатни бройки (Изм. - ДВ, бр. 96 от 2026 г.)" in out.markdown
    mat, blocks = _mat_with("§ 1. В приложението към чл. 2, ал. 2 на ред „Дирекция „Земеделие“ – Варна“ числото „74“ се заменя със „75“.")
    out = O.apply({"operations": [{"id": "§1", "kind": "replace_words", "address": "Приложение към чл. 2, ал. 2, ред „Дирекция „Земеделие“ – Варна“", "old": "q2", "new": "q3"}]}, mat, blocks, body, "96/2026")
    assert "Дирекция „Земеделие“ – Варна\n\n75\n\nДирекция „Земеделие“ – Видин\n\n63" in out.markdown and "1742 щатни бройки (Изм. - ДВ" in out.markdown
    lines = ["ЗАКОН", "за изменение на Закона за пробата", "(обн., ДВ, бр. 1 от 2020 г.)", "§ 1. В приложение № 1 към чл. 3 раздел II се изменя така:",
             "„II.", "Нов втори раздел", "2. нов ред", "3. още ред“", "Законът е приет.", "Председател на Народното събрание: Х", "1"]
    act = SplitAct(blocks=[Block(i, t, {0: "DvCenter", 1: "DvCenter", 2: "DvCenter", 9: "DvRight"}.get(i, "DvJustify")) for i, t in enumerate(lines)], sections=[], source="dv")
    mat = M.parse(act)
    out = O.apply({"operations": [{"id": "§1", "kind": "replace_provision", "address": "приложение № 1, раздел II", "blocks": [4, 7]}]}, mat, act.blocks, body, "96/2026")
    assert out.markdown.rstrip().endswith("## Приложение № 1 към чл. 3 (Изм. - ДВ, бр. 96 от 2026 г.)\n\nI.\n\nПърви раздел\n\n1. ред\n\nII.\n\nНов втори раздел\n\n2. нов ред\n\n3. още ред\n\nIII.\n\nТрети")
    # a deletion inside an enumeration takes one comma with it, and before a full stop
    mat, blocks = _mat_with("§ 1. В чл. 1 думите „както и опита“ се заличават.")
    out = O.apply({"operations": [{"id": "§1", "kind": "delete_words", "address": "чл. 1", "old": "q1"}]}, mat, blocks, body, "96/2026")
    assert "Този закон урежда пробата, за всички." in out.markdown
    mat, blocks = _mat_with("§ 1. В чл. 1 думите „за всички“ се заличават.")
    out = O.apply({"operations": [{"id": "§1", "kind": "delete_words", "address": "чл. 1", "old": "q1"}]}, mat, blocks, body, "96/2026")
    assert "Този закон урежда пробата, както и опита." in out.markdown
    body = BODY.replace("**Чл. 1.** Този закон урежда пробата.", "**Чл. 1.** Осиновяващият - български гражданин, който има местопребиваване.")
    mat, blocks = _mat_with("§ 1. В чл. 1 думите „български гражданин“ се заличават.")
    out = O.apply({"operations": [{"id": "§1", "kind": "delete_words", "address": "чл. 1", "old": "q1"}]}, mat, blocks, body, "96/2026")
    assert "Осиновяващият, който има местопребиваване." in out.markdown


def test_loose_marks_sub_items_lead_words_and_list_renumbers():
    body = BODY.replace("**Чл. 1.** Този закон урежда пробата.", "**Чл. 1.** Този закон урежда пробата по глава шеста - чл. 242 от дирекция “Социално подпомагане”.")
    mat, blocks = _mat_with("§ 1. В чл. 1 думите „по глава шеста – чл. 242“ се заличават, а след думите „Социално подпомагане“ се добавя „и други“.")
    out = O.apply({"operations": [{"id": "§1", "kind": "delete_words", "address": "чл. 1", "old": "q1"},
                                  {"id": "§1", "kind": "insert_words", "address": "чл. 1", "anchor": "q2", "where": "after", "new": "q3"}]}, mat, blocks, body, "96/2026")
    assert "Този закон урежда пробата от дирекция “Социално подпомагане и други”." in out.markdown
    # a sub-item inside an item's flattened text
    body = BODY.replace("1. първа;", "1. първа; 1.1. осъществява контрол по ЗОП, НВМОП и други актове; 1.2. друго;")
    mat, blocks = _mat_with("§ 1. В чл. 2, ал. 1, т. 1.1 думата „НВМОП“ се заличава.")
    assert T.parse_address("чл. 2, ал. 1, т. 1.1") == [("article", "2"), ("alinea", "1"), ("item", "1"), ("subitem", "1.1")]
    out = O.apply({"operations": [{"id": "§1", "kind": "delete_words", "address": "чл. 2, ал. 1, т. 1.1", "old": "q1", "punctuation": "before"}]}, mat, blocks, body, "96/2026")
    assert "1. (изм. - ДВ, бр. 96 от 2026 г.) първа; 1.1. осъществява контрол по ЗОП и други актове; 1.2. друго;" in out.markdown
    # the words before the items replaced by a segment
    mat, blocks = _mat_with("§ 1. В чл. 2, ал. 1 текстът преди т. 1 се изменя така: „Пробата бива:“")
    out = O.apply({"operations": [{"id": "§1", "kind": "replace_provision", "address": "чл. 2, ал. 1, текстът преди т. 1", "new": "q1"}]}, mat, blocks, BODY, "96/2026")
    assert "**Чл. 2.** (1) (Изм. - ДВ, бр. 96 от 2026 г.) Пробата бива:\n\n1. първа;" in out.markdown
    # … or by a quoted block that carries the alinea's number: the items stay
    lines = ["ЗАКОН", "за изменение на Закона за пробата", "(обн., ДВ, бр. 1 от 2020 г.)", "§ 1. В чл. 2, ал. 1 текстът преди т. 1 се изменя така:", "„(1) Пробата е следната:“",
             "Законът е приет.", "Председател на Народното събрание: Х", "1"]
    act = SplitAct(blocks=[Block(i, t, {0: "DvCenter", 1: "DvCenter", 2: "DvCenter", 6: "DvRight"}.get(i, "DvJustify")) for i, t in enumerate(lines)], sections=[], source="dv")
    mat = M.parse(act)
    out = O.apply({"operations": [{"id": "§1", "kind": "replace_provision", "address": "чл. 2, ал. 1, текстът преди т. 1", "blocks": [4, 4]}]}, mat, act.blocks, BODY, "96/2026")
    assert "**Чл. 2.** (1) (Изм. - ДВ, бр. 96 от 2026 г.) Пробата е следната:\n\n1. първа;\n\n2. втора, до 30 000 лв." in out.markdown
    # „ал. 2 и 3 стават ал. 3 и 4“
    lines = ["ЗАКОН", "за изменение на Закона за пробата", "(обн., ДВ, бр. 1 от 2020 г.)", "§ 1. В чл. 2 се правят следните допълнения:",
             "1. Създава се нова ал. 2:", "„(2) Нова втора.“", "2. Досегашните ал. 2 и 3 стават съответно ал. 3 и 4.",
             "Законът е приет.", "Председател на Народното събрание: Х", "1"]
    act = SplitAct(blocks=[Block(i, t, {0: "DvCenter", 1: "DvCenter", 2: "DvCenter", 8: "DvRight"}.get(i, "DvJustify")) for i, t in enumerate(lines)], sections=[], source="dv")
    mat = M.parse(act)
    out = O.apply({"operations": [{"id": "§1", "kind": "no_text_change"},
                                  {"id": "§1.1", "kind": "insert_provision", "address": "чл. 2, ал. 2", "after": "чл. 2, ал. 1", "blocks": [5, 5]},
                                  {"id": "§1.2", "kind": "renumber", "address": "чл. 2, ал. 2 и 3", "to": "ал. 3 и 4"}]}, mat, act.blocks, BODY, "96/2026")
    t = T.parse(out.markdown)
    assert [l.n for l in t.lines if l.kind == "alinea"] == ["1", "2", "3", "4"]
    # a replaced annex whose Gazette heading is bare takes its title row into the heading, as the promulgation reading has it
    body = BODY + "\n## Приложение към чл. 2, ал. 2 Численост – 10 бройки\n\nред А\n\n5\n"
    lines = ["ЗАКОН", "за изменение на Закона за пробата", "(обн., ДВ, бр. 1 от 2020 г.)", "§ 1. Приложението към чл. 2, ал. 2 се изменя, както следва:",
             "„Приложение към чл. 2, ал. 2", "Численост – 12 бройки", "ред Б", "7“", "Законът е приет.", "Председател на Народното събрание: Х", "1"]
    act = SplitAct(blocks=[Block(i, t, {0: "DvCenter", 1: "DvCenter", 2: "DvCenter", 4: "DvRight", 5: "DvCenter", 9: "DvRight"}.get(i, "DvJustify")) for i, t in enumerate(lines)], sections=[], source="dv")
    mat = M.parse(act)
    out = O.apply({"operations": [{"id": "§1", "kind": "replace_annex", "address": "Приложението към чл. 2, ал. 2", "blocks": [4, 7]}]}, mat, act.blocks, body, "96/2026")
    assert "## Приложение към чл. 2, ал. 2 Численост – 12 бройки (Изм. - ДВ, бр. 96 от 2026 г.)\n\nред Б\n\n7" in out.markdown


def test_item_repeal_marker_sentence_insertion_title_replacement_and_wrapped_rows():
    mat, blocks = _mat_with("§ 1. В чл. 2, ал. 1 т. 2 се отменя.")
    out = O.apply({"operations": [{"id": "§1", "kind": "repeal", "address": "чл. 2, ал. 1, т. 2"}]}, mat, blocks, BODY, "96/2026")
    assert "1. първа;\n\n2. (отм. - ДВ, бр. 96 от 2026 г.)\n\n(2) Втора алинея." in out.markdown
    t = T.parse(out.markdown)
    assert t.lines[T.resolve(t, "чл. 2, ал. 1, т. 2")].kind == "item"
    # a new second sentence before the existing second; the old one is „renumbered“ by the Gazette, which changes no text
    body = BODY.replace("**Чл. 1.** Този закон урежда пробата.", "**Чл. 1.** Този закон урежда пробата. Той важи навсякъде.")
    mat, blocks = _mat_with("§ 1. В чл. 1 се създава ново изречение второ: „Той е кратък.“, а досегашното изречение второ става изречение трето.")
    out = O.apply({"operations": [{"id": "§1", "kind": "insert_provision", "address": "чл. 1, изречение второ", "new": "q1"},
                                  {"id": "§1", "kind": "renumber", "address": "чл. 1, изречение второ", "to": "изречение трето"}]}, mat, blocks, body, "96/2026")
    assert "**Чл. 1.** (Доп. - ДВ, бр. 96 от 2026 г.) Този закон урежда пробата. Той е кратък. Той важи навсякъде." in out.markdown
    # an article's title replaced whole
    body = BODY.replace("**Чл. 1.** Този закон урежда пробата.", "Направление „Правна дейност“ **Чл. 1.** Този закон урежда пробата.")
    mat, blocks = _mat_with("§ 1. Наименованието на чл. 1 „Направление „Правна дейност“ се заменя с „Дирекция „Правна дейност и собственост“.")
    out = O.apply({"operations": [{"id": "§1", "kind": "replace_heading", "address": "чл. 1", "new": {"text": "Дирекция „Правна дейност и собственост“"}}]}, mat, blocks, body, "96/2026")
    assert "Дирекция „Правна дейност и собственост“ **Чл. 1.** (Загл. изм. - ДВ, бр. 96 от 2026 г.) Този закон урежда пробата." in out.markdown
    # a table row whose name wraps onto two row lines
    body = BODY + "\n## Приложение към чл. 2, ал. 2 Численост\n\nОбластна дирекция „Земеделие“ –\n\nВарна\n\n74\n\nОбластна дирекция „Земеделие“ – Видин\n\n63\n"
    mat, blocks = _mat_with("§ 1. В приложението към чл. 2, ал. 2 на ред „Областна дирекция „Земеделие“ – Варна“ числото „74“ се заменя със „75“.")
    out = O.apply({"operations": [{"id": "§1", "kind": "replace_words", "address": "Приложение към чл. 2, ал. 2, ред „Областна дирекция „Земеделие“ – Варна“", "old": "q2", "new": "q3"}]}, mat, blocks, body, "96/2026")
    assert "Областна дирекция „Земеделие“ –\n\nВарна\n\n75\n\nОбластна дирекция „Земеделие“ – Видин\n\n63" in out.markdown


def test_sentence_appended_whole_word_conjunction_heading_title_renamed_annex_and_repealed_head_rewritten():
    # a whole sentence added at the end keeps the provision's full stop before it
    mat, blocks = _mat_with("§ 1. В чл. 1 накрая се добавя „Той важи навсякъде.“")
    out = O.apply({"operations": [{"id": "§1", "kind": "insert_words", "address": "чл. 1", "where": "end", "new": "q1"}]}, mat, blocks, BODY, "96/2026")
    assert "Този закон урежда пробата. Той важи навсякъде." in out.markdown
    # „съюзът „и“ се заличава“ counts the word, not the letter
    body = BODY.replace("**Чл. 1.** Този закон урежда пробата.", "**Чл. 1.** Съобщава на родителя, ако той е известен, и на детето, ако то е навършило години.")
    mat, blocks = _mat_with("§ 1. В чл. 1 съюзът „и“ се заличава.")
    out = O.apply({"operations": [{"id": "§1", "kind": "delete_words", "address": "чл. 1", "old": "q1"}]}, mat, blocks, body, "96/2026")
    assert "Съобщава на родителя, ако той е известен, на детето, ако то е навършило години." in out.markdown
    # an article's title read as a heading line above it
    body = BODY.replace("**Чл. 1.** Този закон урежда пробата.", "##### Дирекция „Стара“\n\n**Чл. 1.** Този закон урежда пробата.")
    mat, blocks = _mat_with("§ 1. Наименованието на чл. 1 „Дирекция „Стара“ се заменя с „Дирекция „Нова“.")
    out = O.apply({"operations": [{"id": "§1", "kind": "replace_heading", "address": "чл. 1", "new": {"text": "Дирекция „Нова“"}}]}, mat, blocks, body, "96/2026")
    assert "##### Дирекция „Нова“ (Загл. изм. - ДВ, бр. 96 от 2026 г.)\n\n**Чл. 1.** Този закон урежда пробата." in out.markdown
    # an annex moved to another provision and rewritten in one instruction
    body = BODY + "\n## Приложение към чл. 2, ал. 2\n\nстар ред\n"
    lines = ["ЗАКОН", "за изменение на Закона за пробата", "(обн., ДВ, бр. 1 от 2020 г.)", "§ 1. Досегашното приложение към чл. 2, ал. 2 става приложение към чл. 3 и се изменя така:",
             "„Приложение към чл. 3", "нов ред“", "Законът е приет.", "Председател на Народното събрание: Х", "1"]
    act = SplitAct(blocks=[Block(i, t, {0: "DvCenter", 1: "DvCenter", 2: "DvCenter", 4: "DvRight", 7: "DvRight"}.get(i, "DvJustify")) for i, t in enumerate(lines)], sections=[], source="dv")
    mat = M.parse(act)
    out = O.apply({"operations": [{"id": "§1", "kind": "replace_annex", "address": "Приложение към чл. 2, ал. 2", "blocks": [4, 5]}]}, mat, act.blocks, body, "96/2026")
    assert out.markdown.rstrip().endswith("## Приложение към чл. 3 (Предишно приложение към чл. 2, ал. 2 - ДВ, бр. 96 от 2026 г., изм. - ДВ, бр. 96 от 2026 г.)\n\nнов ред")
    body2 = BODY + "\n## Приложение към чл. 2, ал. 2 (Ново - ДВ, бр. 38 от 2008 г.)\n\nстар ред\n"
    out = O.apply({"operations": [{"id": "§1", "kind": "replace_annex", "address": "Приложение към чл. 2, ал. 2", "blocks": [4, 5]}]}, mat, act.blocks, body2, "96/2026")
    assert "## Приложение към чл. 3 (Ново - ДВ, бр. 38 от 2008 г., предишно приложение към чл. 2, ал. 2 - ДВ, бр. 96 от 2026 г., изм. - ДВ, бр. 96 от 2026 г.)" in out.markdown
    # a new alinea at a repealed head's number rewrites the head and keeps its history
    body = BODY.replace("(2) Втора алинея.", "(2) (Отм. - ДВ, бр. 5 от 2021 г.)")
    mat, blocks = _mat_with("§ 1. В чл. 2 се създава нова ал. 2: „(2) Пак втора.“")
    lines = ["ЗАКОН", "за изменение на Закона за пробата", "(обн., ДВ, бр. 1 от 2020 г.)", "§ 1. В чл. 2 се създава нова ал. 2:", "„(2) Пак втора.“", "Законът е приет.", "Председател на Народното събрание: Х", "1"]
    act = SplitAct(blocks=[Block(i, t, {0: "DvCenter", 1: "DvCenter", 2: "DvCenter", 6: "DvRight"}.get(i, "DvJustify")) for i, t in enumerate(lines)], sections=[], source="dv")
    mat = M.parse(act)
    out = O.apply({"operations": [{"id": "§1", "kind": "insert_provision", "address": "чл. 2, ал. 2", "after": "чл. 2, ал. 1", "blocks": [4, 4]}]}, mat, act.blocks, body, "96/2026")
    assert "(2) (Отм. - ДВ, бр. 5 от 2021 г., нова - ДВ, бр. 96 от 2026 г.) Пак втора.\n\n(3) Трета алинея." in out.markdown


def test_a_renumber_onto_a_taken_number_moves_the_holder_first_and_marks_in_the_act_are_free():
    body = BODY.replace("(3) Трета алинея.", "(3) Трета алинея.\n\n(4) Четвърта алинея.")
    lines = ["ЗАКОН", "за изменение на Закона за пробата", "(обн., ДВ, бр. 1 от 2020 г.)", "§ 1. В чл. 2 се правят следните изменения:",
             "1. Досегашната ал. 2 става ал. 3 и се изменя така:", "„(3) Нова трета.“", "2. Досегашната ал. 3 става ал. 4.", "3. Досегашната ал. 4 става ал. 5.",
             "Законът е приет.", "Председател на Народното събрание: Х", "1"]
    act = SplitAct(blocks=[Block(i, t, {0: "DvCenter", 1: "DvCenter", 2: "DvCenter", 9: "DvRight"}.get(i, "DvJustify")) for i, t in enumerate(lines)], sections=[], source="dv")
    mat = M.parse(act)
    out = O.apply({"operations": [{"id": "§1", "kind": "no_text_change"},
                                  {"id": "§1.1", "kind": "renumber", "address": "чл. 2, ал. 2", "to": "ал. 3"},
                                  {"id": "§1.1", "kind": "replace_provision", "address": "чл. 2, ал. 3", "blocks": [5, 5]},
                                  {"id": "§1.2", "kind": "renumber", "address": "чл. 2, ал. 3", "to": "ал. 4"},
                                  {"id": "§1.3", "kind": "renumber", "address": "чл. 2, ал. 4", "to": "ал. 5"}]}, mat, act.blocks, body, "96/2026")
    t = T.parse(out.markdown)
    assert [t.lines[k].text for k in t.subtree(T.resolve(t, "чл. 2")) if t.lines[k].kind == "alinea"] == [
        "(1) Пробата е:", "(3) (Предишна ал. 2 - ДВ, бр. 96 от 2026 г., изм. - ДВ, бр. 96 от 2026 г.) Нова трета.",
        "(4) (Предишна ал. 3 - ДВ, бр. 96 от 2026 г.) Трета алинея.", "(5) (Предишна ал. 4 - ДВ, бр. 96 от 2026 г.) Четвърта алинея."]
    # the act's quotation marks around a name the instruction writes bare
    body = BODY.replace("**Чл. 1.** Този закон урежда пробата.", "**Чл. 1.** Прилага се Регламент (ЕС) № 651/2014, наричан по-нататък „Регламент (ЕС) 2017/1084“, и други.")
    mat, blocks = _mat_with("§ 1. В чл. 1 след думите „наричан по-нататък Регламент (ЕС) 2017/1084“ се поставя запетая и се добавя „Регламент (ЕС) 2020/972“.")
    out = O.apply({"operations": [{"id": "§1", "kind": "insert_words", "address": "чл. 1", "anchor": "q1", "where": "after", "new": "q2", "punctuation": "before"}]}, mat, blocks, body, "96/2026")
    assert "наричан по-нататък „Регламент (ЕС) 2017/1084“, Регламент (ЕС) 2020/972, и други." in out.markdown


def test_a_quoted_chapter_runs_through_odd_nested_marks_and_an_annex_letter_is_addressed():
    lines = ["ЗАКОН", "за изменение на Закона за пробата", "(обн., ДВ, бр. 1 от 2020 г.)", "§ 1. Глава първа се изменя така:",
             "„Глава първа", "НОВИ ПОЛОЖЕНИЯ", "Чл. 1. Печат с надпис „Предприятие „Пристанища“, а долу – „Управление“.", "Чл. 2. Втори нов.“",
             "§ 2. Законът влиза в сила от 1 януари 2027 г.", "Законът е приет.", "Председател на Народното събрание: Х", "1"]
    act = SplitAct(blocks=[Block(i, t, {0: "DvCenter", 1: "DvCenter", 2: "DvCenter", 4: "DvCenter", 5: "DvCenter", 10: "DvRight"}.get(i, "DvJustify")) for i, t in enumerate(lines)], sections=[], source="dv")
    mat = M.parse(act)
    assert mat.nodes[0].quoted == [4, 5, 6, 7] and [n.id for n in mat.instructions()] == ["§1", "§2"]
    out = O.apply({"operations": [{"id": "§1", "kind": "replace_provision", "address": "глава първа", "blocks": [4, 7]}, {"id": "§2", "kind": "no_text_change"},
                                  {"id": "§1.1", "kind": "no_text_change"}]}, mat, act.blocks, BODY, "96/2026")   # a stray id of a no_text_change is ignored
    assert "### Глава първа НОВИ ПОЛОЖЕНИЯ (Изм. - ДВ, бр. 96 от 2026 г.)\n\n**Чл. 1.** Печат с надпис „Предприятие „Пристанища“, а долу – „Управление“.\n\n**Чл. 2.** Втори нов." in out.markdown
    # a lettered entry of an annex form, and a „№“ the instruction omits
    body = BODY.replace("**Чл. 1.** Този закон урежда пробата.", "**Чл. 1.** Регламент (ЕС) № 2017/1084 важи.") + "\n## Приложение към чл. 2, ал. 2\n\n(c) Трето.\n\n(d) Четвърто:\n\n1. да\n\n(e) Пето.\n"
    assert T.parse_address("Приложение към чл. 2, ал. 2, буква (d)") == [("annex_heading", "към чл. 2, ал. 2"), ("annex_letter", "d")]
    lines = ["ЗАКОН", "за изменение на Закона за пробата", "(обн., ДВ, бр. 1 от 2020 г.)", "§ 1. В приложението към чл. 2, ал. 2 буква (d) се изменя така:",
             "„(d) Ново четвърто:", "1. не", "2. може“", "Законът е приет.", "Председател на Народното събрание: Х", "1"]
    act = SplitAct(blocks=[Block(i, t, {0: "DvCenter", 1: "DvCenter", 2: "DvCenter", 8: "DvRight"}.get(i, "DvJustify")) for i, t in enumerate(lines)], sections=[], source="dv")
    mat = M.parse(act)
    out = O.apply({"operations": [{"id": "§1", "kind": "replace_provision", "address": "Приложение към чл. 2, ал. 2, буква (d)", "blocks": [4, 6]}]}, mat, act.blocks, body, "96/2026")
    assert out.markdown.rstrip().endswith("## Приложение към чл. 2, ал. 2 (Изм. - ДВ, бр. 96 от 2026 г.)\n\n(c) Трето.\n\n(d) Ново четвърто:\n\n1. не\n\n2. може\n\n(e) Пето.")
    mat, blocks = _mat_with("§ 1. В чл. 1 след думите „Регламент (ЕС) 2017/1084“ се добавя „и други“.")
    out = O.apply({"operations": [{"id": "§1", "kind": "insert_words", "address": "чл. 1", "anchor": "q1", "where": "after", "new": "q2"}]}, mat, blocks, body, "96/2026")
    assert "Регламент (ЕС) № 2017/1084 и други важи." in out.markdown


def test_a_bare_after_is_read_under_the_address_and_a_single_alineas_designation_goes():
    body = BODY.replace("**Чл. 3.** Член за отмяна.", "**Чл. 3.** (1) Член за отмяна:\n\n1. първа тук;\n\n2. втора тук.")
    lines = ["ЗАКОН", "за изменение на Закона за пробата", "(обн., ДВ, бр. 1 от 2020 г.)", "§ 1. В чл. 3, ал. 1 се създава нова т. 2:", "„2. нова тук;“",
             "§ 2. В чл. 3 означението „(1)“ се заличава.", "Законът е приет.", "Председател на Народното събрание: Х", "1"]
    act = SplitAct(blocks=[Block(i, t, {0: "DvCenter", 1: "DvCenter", 2: "DvCenter", 7: "DvRight"}.get(i, "DvJustify")) for i, t in enumerate(lines)], sections=[], source="dv")
    mat = M.parse(act)
    out = O.apply({"operations": [{"id": "§1", "kind": "insert_provision", "address": "чл. 3, ал. 1, т. 2", "after": "т. 1", "blocks": [4, 4]},
                                  {"id": "§1", "kind": "renumber", "address": "чл. 3, ал. 1, т. 2", "to": "т. 3"},
                                  {"id": "§2", "kind": "delete_words", "address": "чл. 3, ал. 1", "old": "q1"}]}, mat, act.blocks, body, "96/2026")
    assert "**Чл. 3.** (Изм. - ДВ, бр. 96 от 2026 г.) Член за отмяна:\n\n1. първа тук;\n\n2. (нова - ДВ, бр. 96 от 2026 г.) нова тук;\n\n3. (предишна т. 2 - ДВ, бр. 96 от 2026 г.) втора тук." in out.markdown
    with pytest.raises(O.FormError, match="single alinea"):
        O.apply({"operations": [{"id": "§1", "kind": "no_text_change"}, {"id": "§2", "kind": "delete_words", "address": "чл. 2, ал. 1", "old": "q1"}]}, mat, act.blocks, BODY, "96/2026")


def test_moved_alineas_rewritten_by_their_new_numbers_and_latin_letter_markers():
    body = BODY.replace("(3) Трета алинея.", "(3) Трета алинея.")
    lines = ["ЗАКОН", "за изменение на Закона за пробата", "(обн., ДВ, бр. 1 от 2020 г.)", "§ 1. В чл. 2 се правят следните изменения:",
             "1. Създава се нова ал. 2:", "„(2) Нова втора.“", "2. Досегашните ал. 2 и 3 стават съответно ал. 3 и 4 и се изменят така:",
             "„(3) Трета вече.", "(4) Четвърта вече.“", "3. В чл. 3 се създават букви:", "„a) първа буква;", "б) втора буква.“",
             "Законът е приет.", "Председател на Народното събрание: Х", "1"]
    act = SplitAct(blocks=[Block(i, t, {0: "DvCenter", 1: "DvCenter", 2: "DvCenter", 13: "DvRight"}.get(i, "DvJustify")) for i, t in enumerate(lines)], sections=[], source="dv")
    mat = M.parse(act)
    out = O.apply({"operations": [{"id": "§1", "kind": "no_text_change"},
                                  {"id": "§1.1", "kind": "insert_provision", "address": "чл. 2, ал. 2", "after": "чл. 2, ал. 1", "blocks": [5, 5]},
                                  {"id": "§1.2", "kind": "renumber", "address": "чл. 2, ал. 2 и 3", "to": "ал. 3 и 4"},
                                  {"id": "§1.2", "kind": "replace_provision", "address": "чл. 2, ал. 3", "blocks": [7, 7]},
                                  {"id": "§1.2", "kind": "replace_provision", "address": "чл. 2, ал. 4", "blocks": [8, 8]},
                                  {"id": "§1.3", "kind": "insert_provision", "address": "чл. 3, б. „а“", "after": "чл. 3", "blocks": [10, 10]},
                                  {"id": "§1.3", "kind": "insert_provision", "address": "чл. 3, б. „б“", "after": "чл. 3, б. „а“", "blocks": [11, 11]}]}, mat, act.blocks, body, "96/2026")
    t = T.parse(out.markdown)
    assert [t.lines[k].text for k in t.subtree(T.resolve(t, "чл. 2")) if t.lines[k].kind == "alinea"] == [
        "(1) Пробата е:", "(2) (Нова - ДВ, бр. 96 от 2026 г.) Нова втора.",
        "(3) (Предишна ал. 2 - ДВ, бр. 96 от 2026 г., изм. - ДВ, бр. 96 от 2026 г.) Трета вече.",
        "(4) (Предишна ал. 3 - ДВ, бр. 96 от 2026 г., изм. - ДВ, бр. 96 от 2026 г.) Четвърта вече."]
    assert "а) (нова - ДВ, бр. 96 от 2026 г.) първа буква;\n\nб) (нова - ДВ, бр. 96 от 2026 г.) втора буква." in out.markdown


def test_the_whole_act_is_addressed_by_its_name():
    assert T.parse_address("наредбата и приложенията към нея") == [("act", "")]
    assert T.parse_address("в закона") == [("act", "")]
    mat, blocks = _mat_with("§ 1. Навсякъде в закона думата „пробата“ се заменя с „опита“.")
    out = O.apply({"operations": [{"id": "§1", "kind": "replace_words", "address": "закона", "old": "q1", "new": "q2", "everywhere": True}]}, mat, blocks, BODY, "96/2026")
    assert "Този закон урежда опита." in out.markdown


def test_a_deletion_may_cover_every_occurrence_when_the_applier_says_so():
    body = BODY.replace("**Чл. 1.** Този закон урежда пробата.", "**Чл. 1.** Участие в подготовката и участие в комисии.")
    mat, blocks = _mat_with("§ 1. В чл. 1 думите „участие в“ се заличават.")
    out = O.apply({"operations": [{"id": "§1", "kind": "delete_words", "address": "чл. 1", "old": "q1", "everywhere": True}]}, mat, blocks, body, "96/2026")
    assert "Участие в подготовката и комисии." in out.markdown   # the capitalised form is another word


def test_an_abbreviation_is_replaced_wherever_it_stands_at_the_address():
    body = BODY.replace("**Чл. 1.** Този закон урежда пробата.", "**Чл. 1.** МЗХ одобрява, а МЗХ контролира.")
    mat, blocks = _mat_with("§ 1. В чл. 1 абревиатурата „МЗХ“ се заменя с „МЗХГ“.")
    out = O.apply({"operations": [{"id": "§1", "kind": "replace_words", "address": "чл. 1", "old": "q1", "new": "q2"}]}, mat, blocks, body, "96/2026")
    assert "МЗХГ одобрява, а МЗХГ контролира." in out.markdown


def test_a_lettered_chapter_number_is_addressed_with_or_without_the_marks():
    lines = ["ЗАКОН", "за изменение на Закона за пробата", "(обн., ДВ, бр. 1 от 2020 г.)", "§ 1. Създава се глава първа „а“ с чл. 3а:",
             "„Глава първа „а“", "НОВА ГЛАВА", "Чл. 3а. Нов член.“", "Законът е приет.", "Председател на Народното събрание: Х", "1"]
    act = SplitAct(blocks=[Block(i, t, {0: "DvCenter", 1: "DvCenter", 2: "DvCenter", 4: "DvCenter", 5: "DvCenter", 8: "DvRight"}.get(i, "DvJustify")) for i, t in enumerate(lines)], sections=[], source="dv")
    mat = M.parse(act)
    out = O.apply({"operations": [{"id": "§1", "kind": "insert_heading", "address": "глава първа „а“", "after": "чл. 3", "blocks": [4, 5]},
                                  {"id": "§1", "kind": "insert_provision", "address": "чл. 3а", "after": "глава първа „а“", "blocks": [6, 6]}]}, mat, act.blocks, BODY, "96/2026")
    assert "### Глава първа „а“ НОВА ГЛАВА (Нова - ДВ, бр. 96 от 2026 г.)\n\n**Чл. 3а.** (Нов - ДВ, бр. 96 от 2026 г.) Нов член." in out.markdown
    t = T.parse(out.markdown)
    assert t.lines[T.resolve(t, "глава първа „а“")].kind == "chapter_heading"
    # heading words in capitals, and a comma the instruction writes that the act lacks
    mat, blocks = _mat_with("§ 1. В наименованието на глава първа думите „общи положения“ се заличават.")
    out = O.apply({"operations": [{"id": "§1", "kind": "delete_words", "address": "наименованието на глава първа", "old": "q1"}]}, mat, blocks, BODY, "96/2026")
    assert "### Глава първа (Загл. изм. - ДВ, бр. 96 от 2026 г.)" in out.markdown
    body = BODY.replace("**Чл. 1.** Този закон урежда пробата.", "**Чл. 1.** Детето както и родителят идват.")
    mat, blocks = _mat_with("§ 1. В чл. 1 думите „Детето, както и родителят“ се заменят с „Всички“.")
    out = O.apply({"operations": [{"id": "§1", "kind": "replace_words", "address": "чл. 1", "old": "q1", "new": "q2"}]}, mat, blocks, body, "96/2026")
    assert "Всички идват." in out.markdown


def test_heading_words_change_and_a_mark_that_replaces_a_word_closes_up():
    mat, blocks = _mat_with("§ 1. В наименованието на глава първа думите „ОБЩИ“ се заличават.")
    out = O.apply({"operations": [{"id": "§1", "kind": "delete_words", "address": "наименованието на глава първа", "old": "q1"}]}, mat, blocks, BODY, "96/2026")
    assert "### Глава първа ПОЛОЖЕНИЯ (Загл. изм. - ДВ, бр. 96 от 2026 г.)" in out.markdown
    body = BODY.replace("**Чл. 1.** Този закон урежда пробата.", "**Чл. 1.** Настанява се в семейство или в институция.")
    mat, blocks = _mat_with("§ 1. В чл. 1 съюзът „или“ се заменя със запетая.")
    out = O.apply({"operations": [{"id": "§1", "kind": "replace_words", "address": "чл. 1", "old": "q1", "new": {"text": ","}}]}, mat, blocks, body, "96/2026")
    assert "Настанява се в семейство, в институция." in out.markdown
    mat2, blocks2 = _mat_with("§ 1. В чл. 1 думите „семейство, в институция“ се заменят с „дом“.")
    body2 = BODY.replace("**Чл. 1.** Този закон урежда пробата.", "**Чл. 1.** Настанява се в семейство , в институция.")
    out = O.apply({"operations": [{"id": "§1", "kind": "replace_words", "address": "чл. 1", "old": "q1", "new": "q2"}]}, mat2, blocks2, body2, "96/2026")
    assert "Настанява се в дом." in out.markdown


def test_the_parentheses_around_an_abbreviation_go():
    body = BODY.replace("**Чл. 1.** Този закон урежда пробата.", "**Чл. 1.** Строителни и монтажни работи (СМР) се извършват.")
    mat, blocks = _mat_with("§ 1. В чл. 1 скобите на абревиатурата „СМР“ се заличават.")
    out = O.apply({"operations": [{"id": "§1", "kind": "delete_words", "address": "чл. 1", "old": "q1", "punctuation": "brackets"}]}, mat, blocks, body, "96/2026")
    assert "Строителни и монтажни работи СМР се извършват." in out.markdown


def test_a_row_the_act_abbreviates_is_found_by_its_full_name():
    body = BODY + "\n## Приложение към чл. 2, ал. 2 Численост\n\nОбластна дирекция „Земеделие“ – В. Търново\n\n63\n"
    mat, blocks = _mat_with("§ 1. В приложението към чл. 2, ал. 2 на ред „Областна дирекция „Земеделие“ – Велико Търново“ числото „63“ се заменя с „62“.")
    out = O.apply({"operations": [{"id": "§1", "kind": "replace_words", "address": "Приложение към чл. 2, ал. 2, ред „Областна дирекция „Земеделие“ – Велико Търново“", "old": "q2", "new": "q3"}]}, mat, blocks, body, "96/2026")
    assert "Областна дирекция „Земеделие“ – В. Търново\n\n62" in out.markdown


def test_an_extension_replace_skips_places_already_extended_and_a_comma_is_not_doubled():
    body = BODY.replace("**Чл. 1.** Този закон урежда пробата.", "**Чл. 1.** Министъра на земеделието и храните и министъра на земеделието решават.")
    mat, blocks = _mat_with("§ 1. В чл. 1 думите „министъра на земеделието“ се заменят с „министъра на земеделието и храните“.")
    out = O.apply({"operations": [{"id": "§1", "kind": "replace_words", "address": "чл. 1", "old": "q1", "new": "q2", "everywhere": True}]}, mat, blocks, body, "96/2026")
    assert "Министъра на земеделието и храните и министъра на земеделието и храните решават." in out.markdown
    body = BODY.replace("**Чл. 1.** Този закон урежда пробата.", "**Чл. 1.** Законът (ЗЕЕ), наредбата и други важат.")
    mat, blocks = _mat_with("§ 1. В чл. 1 след думите „(ЗЕЕ)“ се поставя запетая и се добавя „правилникът“.")
    out = O.apply({"operations": [{"id": "§1", "kind": "insert_words", "address": "чл. 1", "anchor": {"text": "(ЗЕЕ)"}, "where": "after", "new": "q2", "punctuation": "before"}]}, mat, blocks, body, "96/2026")
    assert "Законът (ЗЕЕ), правилникът, наредбата и други важат." in out.markdown


def test_an_article_rewritten_whole_marks_its_alineas_and_a_comma_comes_with_words_added_at_the_end():
    lines = ["ЗАКОН", "за изменение на Закона за пробата", "(обн., ДВ, бр. 1 от 2020 г.)", "§ 1. Член 2 се изменя така:",
             "„Чл. 2. (1) Първа нова.", "(2) Втора нова.", "(3) Трета нова.", "(4) Четвърта нова.“", "§ 2. В чл. 1 накрая се поставя запетая и се добавя „ако деянието е тежко“.",
             "Законът е приет.", "Председател на Народното събрание: Х", "1"]
    act = SplitAct(blocks=[Block(i, t, {0: "DvCenter", 1: "DvCenter", 2: "DvCenter", 10: "DvRight"}.get(i, "DvJustify")) for i, t in enumerate(lines)], sections=[], source="dv")
    mat = M.parse(act)
    out = O.apply({"operations": [{"id": "§1", "kind": "replace_provision", "address": "чл. 2", "blocks": [4, 7]},
                                  {"id": "§2", "kind": "insert_words", "address": "чл. 1", "where": "end", "new": "q1", "punctuation": "before"}]}, mat, act.blocks, BODY, "96/2026")
    assert "**Чл. 2.** (1) (Изм. - ДВ, бр. 96 от 2026 г.) Първа нова.\n\n(2) (Изм. - ДВ, бр. 96 от 2026 г.) Втора нова.\n\n(3) (Изм. - ДВ, бр. 96 от 2026 г.) Трета нова.\n\n(4) (Нова - ДВ, бр. 96 от 2026 г.) Четвърта нова." in out.markdown
    assert "**Чл. 1.** (Доп. - ДВ, бр. 96 от 2026 г.) Този закон урежда пробата, ако деянието е тежко." in out.markdown


def test_a_rewritten_annex_keeps_its_marker_history_and_one_issue_marks_a_heading_once():
    body = BODY + "\n## Приложение към чл. 2, ал. 2 Численост (Изм. - ДВ, бр. 9 от 2010 г.)\n\nред А\n\n5\n\nред Б\n\n7\n"
    lines = ["ЗАКОН", "за изменение на Закона за пробата", "(обн., ДВ, бр. 1 от 2020 г.)", "§ 1. В приложението към чл. 2, ал. 2 се правят следните изменения:",
             "1. На ред „ред А“ числото „5“ се заменя с „6“.", "2. На ред „ред Б“ числото „7“ се заменя с „8“.", "§ 2. Приложението към чл. 2, ал. 2 се изменя така:",
             "„Приложение към чл. 2, ал. 2", "Численост", "ред В", "9“", "Законът е приет.", "Председател на Народното събрание: Х", "1"]
    act = SplitAct(blocks=[Block(i, t, {0: "DvCenter", 1: "DvCenter", 2: "DvCenter", 7: "DvRight", 8: "DvCenter", 12: "DvRight"}.get(i, "DvJustify")) for i, t in enumerate(lines)], sections=[], source="dv")
    mat = M.parse(act)
    out = O.apply({"operations": [{"id": "§1", "kind": "no_text_change"},
                                  {"id": "§1.1", "kind": "replace_words", "address": "Приложение към чл. 2, ал. 2, ред „ред А“", "old": "q2", "new": "q3"},
                                  {"id": "§1.2", "kind": "replace_words", "address": "Приложение към чл. 2, ал. 2, ред „ред Б“", "old": "q2", "new": "q3"},
                                  {"id": "§2", "kind": "no_text_change"}]}, mat, act.blocks, body, "96/2026")
    assert "## Приложение към чл. 2, ал. 2 Численост (Изм. - ДВ, бр. 9 от 2010 г., изм. - ДВ, бр. 96 от 2026 г.)\n\nред А\n\n6\n\nред Б\n\n8" in out.markdown
    out = O.apply({"operations": [{"id": "§1", "kind": "no_text_change"}, {"id": "§1.1", "kind": "no_text_change"}, {"id": "§1.2", "kind": "no_text_change"},
                                  {"id": "§2", "kind": "replace_annex", "address": "Приложение към чл. 2, ал. 2", "blocks": [7, 10]}]}, mat, act.blocks, body, "96/2026")
    assert "## Приложение към чл. 2, ал. 2 Численост (Изм. - ДВ, бр. 9 от 2010 г., изм. - ДВ, бр. 96 от 2026 г.)\n\nред В\n\n9" in out.markdown


def test_a_renumber_onto_a_repealed_heads_number_takes_its_place():
    body = BODY.replace("(3) Трета алинея.", "(3) Трета алинея.\n\n(4) (Отм. - ДВ, бр. 5 от 2021 г.)")
    mat, blocks = _mat_with("§ 1. В чл. 2 досегашната ал. 3 става ал. 4.")
    out = O.apply({"operations": [{"id": "§1", "kind": "renumber", "address": "чл. 2, ал. 3", "to": "ал. 4"}]}, mat, blocks, body, "96/2026")
    t = T.parse(out.markdown)
    assert [t.lines[k].text for k in t.subtree(T.resolve(t, "чл. 2")) if t.lines[k].kind == "alinea"] == [
        "(1) Пробата е:", "(2) Втора алинея.", "(4) (Предишна ал. 3 - ДВ, бр. 96 от 2026 г.) Трета алинея."]
