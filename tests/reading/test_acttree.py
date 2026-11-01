"""The act tree (reading/acttree.py): a body read into addressable lines and written back unchanged."""
import pytest

from reading import acttree as T
from reading.checks import run_all

BODY = """# ЗАКОН за пробата

### Глава първа ОБЩИ ПОЛОЖЕНИЯ

**Чл. 1.** Този закон урежда пробата.

**Чл. 2.** (1) Пробата е:

1. първа;

2. втора.

(2) Втора алинея:

1. трета;

а) буква.

Предмет **Чл. 3.** (Изм. - ДВ, бр. 5 от 2020 г.) (1) Текст с заглавие.

(2) (Отм. - ДВ, бр. 6 от 2021 г.)

## Преходни и заключителни разпоредби

**§ 1.** По смисъла на този закон „проба“ е проба.

## Приложение № 1 към чл. 1

Чл. 1. Правило на приложението.

Ред на таблица.
"""


def test_roundtrip_kinds_and_parents():
    t = T.parse(BODY)
    assert t.to_markdown() == BODY
    kinds = [l.kind for l in t.lines]
    assert kinds == ["title", "chapter_heading", "article", "article", "item", "item", "alinea", "item", "letter", "article", "alinea",
                     "provisions_heading", "sign", "annex_heading", "annex_row", "annex_row"]
    assert t.lines[3].inline_alinea == "1" and t.lines[9].title == "Предмет" and t.lines[9].inline_alinea == "1"
    assert t.lines[4].parent == 3 and t.lines[7].parent == 6 and t.lines[8].parent == 7 and t.lines[14].parent == 13


def test_addresses_resolve_to_one_line_or_refuse():
    t = T.parse(BODY)
    assert t.lines[T.resolve(t, "чл. 2, ал. 1, т. 2")].body() == "втора."
    assert t.lines[T.resolve(t, "чл. 2, ал. 2, т. 1, б. „а“")].body() == "буква."
    assert T.resolve(t, "чл. 2, ал. 1") == 3 and t.lines[3].body() == "Пробата е:"
    assert t.lines[T.resolve(t, "чл. 3, ал. 1")].body() == "Текст с заглавие."
    assert t.lines[T.resolve(t, "чл. 3, ал. 2")].body() == ""
    assert T.resolve(t, "§ 1") == 12 and T.resolve(t, "глава първа") == 1 and T.resolve(t, "Приложение № 1") == 13
    assert T.resolve(t, "наименованието") == 0
    with pytest.raises(T.AddressError):
        T.resolve(t, "чл. 9")
    with pytest.raises(T.AddressError):
        T.resolve(t, "чл. 2, т. 1")   # items under two alineas: not one place
    assert T.parse_address("чл. 36, ал. 1, т. 5, б. „а“") == [("article", "36"), ("alinea", "1"), ("item", "5"), ("letter", "а")]


def test_the_checks_run_over_the_tree_and_the_annex_keeps_its_own_numbering():
    t = T.parse(BODY)
    blocks, smap = T.to_blocks_and_map(t)
    assert [b.text for b in blocks][9:11] == ["Предмет", "Чл. 3. (Изм. - ДВ, бр. 5 от 2020 г.) (1) Текст с заглавие."]
    md, ex = run_all(blocks, smap, source="dv")
    assert ex == []


def test_line_from_text_reads_the_gazettes_words_into_lines():
    assert T.line_from_text("Чл. 39а. (1) Текст.").text == "**Чл. 39а.** (1) Текст." and T.line_from_text("Чл. 39а. (1) Текст.").n == "39а"
    assert T.line_from_text("(4) Текст.").kind == "alinea" and T.line_from_text("§ 4а. Текст.").text == "**§ 4а.** Текст."
    h = T.line_from_text("Раздел X")
    assert (h.kind, h.text, h.n) == ("section_heading", "#### Раздел X", "X")
    assert T.line_from_text("2. нямат публични задължения;").kind == "item"
