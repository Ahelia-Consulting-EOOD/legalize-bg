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
    (_with({"id": "§3", "kind": "insert_provision", "address": "чл. 3а", "after": "чл. 3", "blocks": [10, 10]}), "does not close the quotation"),
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
    assert "1. (изм. - ДВ, бр. 96 от 2026 г.) министъра на реда на реда;" in out.markdown
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
    out = O.apply({"operations": [{"id": "§5.1", "kind": "replace_words", "address": "чл. 1", "old": "q1", "new": "q2"}]}, scoped, act.blocks, BODY, "96/2026")
    assert "**Чл. 1.** (Изм. - ДВ, бр. 96 от 2026 г.) Този закон определя пробата." in out.markdown
