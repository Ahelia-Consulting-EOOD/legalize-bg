import logging
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
    # Alineas must be separated by a blank line (CommonMark paragraph break);
    # a single `\n` is a soft break that renders as a space in HTML, which
    # collapses the legal paragraph structure.
    blocks = [b.strip() for b in md.split("\n\n") if b.strip()]
    assert any(b.startswith("(2)") for b in blocks), (
        f"(2) should be its own block, got blocks: {blocks!r}"
    )
    assert any(b.startswith("(3)") for b in blocks), (
        f"(3) should be its own block, got blocks: {blocks!r}"
    )


def test_full_zop_produces_valid_markdown():
    """Integration test: full ZOP fixture produces reasonable Markdown."""
    soup = _load_soup("zop.html")
    md = HtmlToMarkdown().convert(soup)
    lines = md.strip().split("\n")
    assert len(lines) > 100  # ZOP is a large law
    assert lines[0].startswith("# ")
    # Should have articles
    assert any("**Чл." in line for line in lines)


# --- Task 2: ДР/ПЗР subdivision classes ---


def test_additional_provisions_heading_present():
    md = HtmlToMarkdown().convert(_load_soup("zeu.html"))
    assert "## Допълнителни разпоредби" in md


def test_paragraph_definitions_captured():
    md = HtmlToMarkdown().convert(_load_soup("zeu.html"))
    assert "§ 1." in md and "По смисъла" in md


def test_final_edicts_heading_variant_captured():
    # ГПК carries standalone "Заключителни разпоредби КЪМ ..." blocks (class=FinalEdicts)
    md = HtmlToMarkdown().convert(_load_soup("gpk.html"))
    assert "Заключителни разпоредби" in md


def test_transitional_heading_is_not_glued_to_kym():
    md = HtmlToMarkdown().convert(_load_soup("gpk.html"))
    assert "разпоредбиКЪМ" not in md  # de-glued


def test_section_paragraph_bodies_present_for_zuo_like():
    md = HtmlToMarkdown().convert(_load_soup("zop.html"))
    assert md.count("§") > 20  # §-provisions, not just headings


# --- Task 3: keep-unknown-by-default + chrome denylist ---


def test_unknown_content_class_is_kept_not_dropped():
    html = ('<div class="TitleDocument">Z</div>'
            '<div class="SomeBrandNewEdict">КЪМ ЗАКОНА ЗА НЕЩО СИ нова разпоредба</div>')
    md = HtmlToMarkdown().convert(BeautifulSoup(html, "lxml"))
    assert "нова разпоредба" in md  # kept by default, not silently dropped


def test_known_chrome_class_is_excluded():
    html = ('<div class="TitleDocument">Z</div>'
            '<p class="buttons">ДОБАВИ В МОИТЕ АКТОВЕ</p>')
    md = HtmlToMarkdown().convert(BeautifulSoup(html, "lxml"))
    assert "ДОБАВИ В МОИТЕ АКТОВЕ" not in md


# --- Task 4: Portion(Дял) heading, no-spine fail-safe, warning assertion ---


def test_division_portion_heading_captured():
    md = HtmlToMarkdown().convert(_load_soup("gpk.html"))
    assert "## Дял" in md          # Дял (Division) headings now formatted, not plain text
    assert md.count("## Дял") >= 4


def test_no_spine_does_not_inject_page_chrome():
    html = '<div class="wrapper"><div class="content">НОВИНИ СПРАВОЧНИК ФОРУМ</div></div>'
    md = HtmlToMarkdown().convert(BeautifulSoup(html, "lxml"))
    assert "НОВИНИ" not in md


def test_warning_emitted_for_kept_unmapped_class(caplog):
    html = '<div class="TitleDocument">Z</div><div class="SomeNovelEdict">нова разпоредба тук</div>'
    with caplog.at_level(logging.WARNING):
        md = HtmlToMarkdown().convert(BeautifulSoup(html, "lxml"))
    assert "нова разпоредба тук" in md
    assert any("SomeNovelEdict" in (r.getMessage()) for r in caplog.records)
