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


def test_undersection_rendered_as_level5_heading():
    """Подраздел (UnderSection) is a structural level below Раздел/Section and
    must render as a level-5 heading, not be flattened to plain text (D-047:
    preserve article/chapter/section structure)."""
    from bs4 import BeautifulSoup
    html = ('<div class="TitleDocument">Z</div>'
            '<div class="Section">Раздел I. Общи разпоредби</div>'
            '<div class="UnderSection">Подраздел I. Общи положения</div>')
    md = HtmlToMarkdown().convert(BeautifulSoup(html, "lxml"))
    assert "#### Раздел I. Общи разпоредби" in md
    assert "##### Подраздел I. Общи положения" in md


def test_child_div_alineas_become_paragraphs():
    """Pre-Указ-883 acts (ЗЗД, ЗС, ЗН, ЗЛС) have unnumbered алинеи, each
    in its own child <div> of the Article element (verified against live
    lex.bg HTML for doc_id 2121934337, чл. 36 ЗЗД, 2026-07-31). They must
    become separate Markdown paragraphs, not be glued with spaces."""
    html = '''
    <div class="Article">
        <div><b>Чл. 36.</b> Едно лице може да представлява друго по разпоредба на закона или по волята на представлявания.</div>
        <div>Последиците от правните действия, които представителят извършва, възникват направо за представлявания.</div>
        <br/>
    </div>
    '''
    soup = BeautifulSoup(html, "lxml")
    md = HtmlToMarkdown().convert(soup)
    blocks = [b.strip() for b in md.split("\n\n") if b.strip()]
    assert blocks[0].startswith("**Чл. 36.**")
    assert blocks[0].endswith("представлявания.")
    assert "Последиците" not in blocks[0], "алинеи glued into one paragraph"
    assert blocks[1].startswith("Последиците")


def test_mixed_layout_br_inside_child_div():
    """A child div that itself contains <br>-separated runs must split on
    those too (belt-and-braces for mixed layouts)."""
    html = '''
    <div class="Article">
        <div><b>Чл. 5.</b> Първа алинея.<br/>Втора алинея.</div>
        <div>Трета алинея.</div>
    </div>
    '''
    soup = BeautifulSoup(html, "lxml")
    md = HtmlToMarkdown().convert(soup)
    blocks = [b.strip() for b in md.split("\n\n") if b.strip()]
    assert len(blocks) == 3
    assert blocks[1] == "Втора алинея."
    assert blocks[2] == "Трета алинея."


def test_title_preamble_glued_to_article_anchor():
    """FR-034 rule 1a: lex.bg renders the article заглавие as its own child
    element preceding the anchor. Post-fix it would become a standalone
    paragraph that index.provisions routes to the PREVIOUS article's tail;
    glue it back into the documented „Title preamble Чл. N. …" form."""
    html = '''
    <div class="Article">
        <p>Стойностни прагове</p>
        <div><b>Чл. 20.</b> (1) Процедурите се прилагат, когато:</div>
        <div>1. публични възложители възлагат обществени поръчки.</div>
    </div>
    '''
    soup = BeautifulSoup(html, "lxml")
    md = HtmlToMarkdown().convert(soup)
    blocks = [b.strip() for b in md.split("\n\n") if b.strip()]
    assert blocks[0].startswith("Стойностни прагове Чл. 20."), blocks[:2]
    # the точка stays its own paragraph — only the title is glued
    assert blocks[1].startswith("1. публични")


def test_article_without_title_preamble_is_untouched():
    """The glue must not fire when the first line already carries the anchor."""
    html = '''
    <div class="Article">
        <div><b>Чл. 21.</b> Първа алинея.</div>
        <div>Втора алинея.</div>
    </div>
    '''
    soup = BeautifulSoup(html, "lxml")
    md = HtmlToMarkdown().convert(soup)
    blocks = [b.strip() for b in md.split("\n\n") if b.strip()]
    assert blocks[0] == "**Чл. 21.** Първа алинея."
    assert blocks[1] == "Втора алинея."
