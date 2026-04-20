import pathlib
import pytest
from bs4 import BeautifulSoup
from fetcher.bg.text_parser import HtmlToMarkdown

FIXTURES = pathlib.Path(__file__).parent.parent.parent / "fixtures"


def _load_soup(name: str) -> BeautifulSoup:
    html = (FIXTURES / "html" / name).read_bytes().decode("cp1251")
    return BeautifulSoup(html, "lxml")


def test_extracts_title():
    soup = _load_soup("zop.html")
    md = HtmlToMarkdown().convert(soup)
    assert md.startswith("# ")
    assert "ОБЩЕСТВЕНИТЕ ПОРЪЧКИ" in md.split("\n")[0]


def test_title_document_becomes_h1():
    html = '<div class="TitleDocument">ЗАКОН ЗА НЕЩО</div>'
    soup = BeautifulSoup(html, "lxml")
    md = HtmlToMarkdown().convert(soup)
    assert "# ЗАКОН ЗА НЕЩО" in md


def test_part_becomes_h2():
    html = '<div class="Part">Част първа. ОСНОВНИ ПОЛОЖЕНИЯ</div>'
    soup = BeautifulSoup(html, "lxml")
    md = HtmlToMarkdown().convert(soup)
    assert "## Част първа. ОСНОВНИ ПОЛОЖЕНИЯ" in md


def test_heading_becomes_h3():
    html = '<div class="Heading">Глава първа. ПРЕДМЕТ</div>'
    soup = BeautifulSoup(html, "lxml")
    md = HtmlToMarkdown().convert(soup)
    assert "### Глава първа. ПРЕДМЕТ" in md


def test_section_becomes_h4():
    html = '<div class="Section">Раздел I. ОБЩИ ПРАВИЛА</div>'
    soup = BeautifulSoup(html, "lxml")
    md = HtmlToMarkdown().convert(soup)
    assert "#### Раздел I. ОБЩИ ПРАВИЛА" in md


def test_article_bold_formatting():
    html = '<div class="Article"><b>Чл. 1.</b> (1) Този закон определя...</div>'
    soup = BeautifulSoup(html, "lxml")
    md = HtmlToMarkdown().convert(soup)
    assert "**Чл. 1.**" in md
    assert "Този закон определя" in md


def test_transitional_provisions():
    html = '<div class="TransitionalFinalEdicts">ПРЕХОДНИ И ЗАКЛЮЧИТЕЛНИ РАЗПОРЕДБИ</div>'
    soup = BeautifulSoup(html, "lxml")
    md = HtmlToMarkdown().convert(soup)
    assert "## ПРЕХОДНИ И ЗАКЛЮЧИТЕЛНИ РАЗПОРЕДБИ" in md


def test_history_excluded_from_body():
    html = '''
    <div class="TitleDocument">ЗАКОН</div>
    <div class="HistoryOfDocument">ДВ, бр. 13 от 2016 г.</div>
    <div class="Article"><b>Чл. 1.</b> Текст.</div>
    '''
    soup = BeautifulSoup(html, "lxml")
    md = HtmlToMarkdown().convert(soup)
    assert "ДВ, бр. 13" not in md
    assert "Чл. 1." in md


def test_preserves_paragraph_structure():
    html = '''
    <div class="Article">
        <b>Чл. 14.</b> (1) Първа алинея.
        <br/>(2) Втора алинея.
        <br/>(3) Трета алинея.
    </div>
    '''
    soup = BeautifulSoup(html, "lxml")
    md = HtmlToMarkdown().convert(soup)
    assert "(1)" in md
    assert "(2)" in md
    assert "(3)" in md


def test_full_zop_produces_valid_markdown():
    """Integration test: full ZOP fixture produces reasonable Markdown."""
    soup = _load_soup("zop.html")
    md = HtmlToMarkdown().convert(soup)
    lines = md.strip().split("\n")
    assert len(lines) > 100  # ZOP is a large law
    assert lines[0].startswith("# ")
    # Should have articles
    assert any("**Чл." in line for line in lines)
