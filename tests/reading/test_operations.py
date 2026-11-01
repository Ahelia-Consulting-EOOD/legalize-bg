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
    a = T.resolve(t, "чл. 3а")
    assert t.lines[a].text == "**Чл. 3а.** (Нов - ДВ, бр. 96 от 2026 г.) (1) Нов член." and t.lines[a + 1].text == "(2) С втора алинея."
    assert t.lines[T.resolve(t, "чл. 1")].text == "**Чл. 1.** (Изм. - ДВ, бр. 96 от 2026 г.) Този закон пробата."
    assert t.lines[T.resolve(t, "чл. 2, ал. 5")].text == "(5) (Предишна ал. 3 - ДВ, бр. 96 от 2026 г.) Трета алинея."
    # the order of the lines holds: ал. 4 was inserted after ал. 3, which then became ал. 5
    assert [l.n for l in t.lines if l.kind == "alinea"] == ["2", "5", "4", "2"]
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


@pytest.mark.parametrize("answer, message", [
    ({"operations": [{"id": "§1.1", "kind": "rewrite", "address": "чл. 2"}]}, "not one of"),
    ({"operations": [{"id": "§9", "kind": "repeal", "address": "чл. 2"}]}, "not an instruction"),
    ({"operations": [{"id": "§2", "kind": "repeal", "address": "чл. 9"}]}, "names 0 place"),
    ({"operations": [{"id": "§1.1", "kind": "replace_words", "address": "чл. 2, ал. 1, т. 2", "old": "q3", "new": "q2"}]}, "not a quoted segment"),
    ({"operations": [{"id": "§1.1", "kind": "replace_words", "address": "чл. 2", "old": "q1", "new": "q2", "extra": 1}]}, "outside the form"),
    ({"operations": [{"id": "§1.2", "kind": "insert_provision", "address": "чл. 2, ал. 4", "after": "чл. 2, ал. 3", "blocks": [4, 4]}]}, "does not open with a quotation mark"),
    ({"operations": [{"id": "§3", "kind": "replace_provision", "address": "чл. 3", "blocks": [10, 11]}]}, "carries the number"),
    ({"operations": [{"id": "§4", "kind": "delete_words", "address": "чл. 2", "old": "q1"}]}, "do not occur"),
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
