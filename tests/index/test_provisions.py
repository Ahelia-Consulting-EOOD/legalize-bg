import json
import pathlib
import pytest
from index.provisions import parse, Provision

GOLDEN_DIR = pathlib.Path(__file__).parent.parent / "fixtures" / "golden" / "provisions"


def test_extracts_simple_article():
    md = "**Чл. 1.** Този закон определя нещо."
    rows = parse(md, law_id="test")
    article_rows = [r for r in rows if r.paragraph is None]
    assert len(article_rows) == 1
    assert article_rows[0].article == "1"
    assert "този закон" in article_rows[0].text.lower()


def test_extracts_multiple_articles():
    md = """**Чл. 1.** Първи член.

**Чл. 2.** Втори член.

**Чл. 3.** Трети член.
"""
    rows = parse(md, law_id="test")
    article_rows = [r for r in rows if r.paragraph is None]
    assert [r.article for r in article_rows] == ["1", "2", "3"]


def test_extracts_cyrillic_suffix_articles():
    md = """**Чл. 14.** Базов член.

**Чл. 14а.** Допълнителен член.

**Чл. 14б.** Още един.
"""
    rows = parse(md, law_id="test")
    article_rows = [r for r in rows if r.paragraph is None]
    assert [r.article for r in article_rows] == ["14", "14а", "14б"]


def test_stops_at_structural_header():
    md = """**Чл. 5.** Член преди ПЗР.

## ПРЕХОДНИ И ЗАКЛЮЧИТЕЛНИ РАЗПОРЕДБИ

**§ 1.** Параграф от ПЗР — не е член.
"""
    rows = parse(md, law_id="test")
    article_rows = [r for r in rows if r.paragraph is None]
    assert len(article_rows) == 1
    assert "ПРЕХОДНИ" not in article_rows[0].text
    assert "§ 1" not in article_rows[0].text


def test_text_hash_is_stable():
    md = "**Чл. 1.** Текст."
    rows1 = parse(md, law_id="test")
    rows2 = parse(md, law_id="test")
    assert rows1[0].text_hash == rows2[0].text_hash


def test_text_hash_changes_with_content():
    rows1 = parse("**Чл. 1.** Текст А.", law_id="test")
    rows2 = parse("**Чл. 1.** Текст Б.", law_id="test")
    assert rows1[0].text_hash != rows2[0].text_hash


def test_returns_law_id_on_each_row():
    md = "**Чл. 1.** Текст."
    rows = parse(md, law_id="zop")
    for r in rows:
        assert r.law_id == "zop"


def test_zop_golden_subset():
    """ZOP fixture should produce a known set of articles. Golden anchors
    the parser; alinea-level coverage added in Task 5."""
    from bs4 import BeautifulSoup
    from fetcher.bg.text_parser import HtmlToMarkdown

    fixture = pathlib.Path(__file__).parent.parent / "fixtures" / "html" / "zop.html"
    soup = BeautifulSoup(fixture.read_bytes().decode("cp1251"), "lxml")
    md = HtmlToMarkdown().convert(soup)

    rows = parse(md, law_id="zop")
    articles = sorted({r.article for r in rows if r.paragraph is None}, key=_article_sort_key)
    assert "1" in articles
    assert "100" in articles or any(a.startswith("100") for a in articles)
    assert any(a[-1] in "абвгд" for a in articles), f"expected Cyrillic-suffix articles, got {articles[:20]}..."


def _article_sort_key(article: str):
    import re
    m = re.match(r"^(\d+)([а-я]*)$", article)
    if not m:
        return (0, article)
    return (int(m.group(1)), m.group(2))
