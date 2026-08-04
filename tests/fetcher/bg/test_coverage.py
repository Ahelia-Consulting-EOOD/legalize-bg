"""Tests for fetcher.bg.coverage — class-agnostic legal-text coverage validator."""
import pathlib

import pytest
from bs4 import BeautifulSoup, Tag

from fetcher.bg.text_parser import HtmlToMarkdown, CHROME_DENYLIST, CLASS_MAP, content_region
from fetcher.bg.coverage import (
    make_gate_record,
    structure_mismatches,
    uncovered_legal_text,
)

FIXTURES = pathlib.Path(__file__).parent.parent.parent / "fixtures"


def _load_soup(name: str) -> BeautifulSoup:
    html = (FIXTURES / "html" / name).read_bytes().decode("cp1251")
    return BeautifulSoup(html, "lxml")


def test_content_region_is_importable_and_callable():
    """content_region(soup) is a module-level function in text_parser.

    This test locks the public contract: coverage.py must import content_region
    from text_parser (not call the private HtmlToMarkdown()._content_region).
    """
    html = '<div class="TitleDocument">ЗАКОН</div><div class="Article">Чл. 1. Текст.</div>'
    soup = BeautifulSoup(html, "lxml")
    region, has_spine = content_region(soup)
    assert has_spine is True
    # Region must contain the two spine elements
    assert region.find(class_="Article") is not None


def test_content_region_matches_private_method():
    """content_region(soup) and HtmlToMarkdown()._content_region(soup) must return
    the same result so the refactor is behavior-preserving."""
    html = '<div class="TitleDocument">ЗАКОН</div><div class="Article">Чл. 1. Текст.</div>'
    soup = BeautifulSoup(html, "lxml")
    pub_region, pub_spine = content_region(soup)
    priv_region, priv_spine = HtmlToMarkdown()._content_region(soup)
    assert id(pub_region) == id(priv_region)
    assert pub_spine == priv_spine


def test_full_capture_has_zero_uncovered():
    """A well-converted fixture should have negligible uncovered Cyrillic text."""
    soup = _load_soup("naredba-04-14.html")
    md = HtmlToMarkdown().convert(soup)
    res = uncovered_legal_text(soup, md)
    assert res["uncovered_chars"] <= 30  # only fixed chrome residual (e.g. 'ДОБАВИ...')


def test_detects_a_forced_drop():
    """A simulated parser regression (missing text block) must be detected."""
    soup = _load_soup("zeu.html")
    md = HtmlToMarkdown().convert(soup)
    # Simulate a regression: corrupt a definition clause in the output
    broken = md.replace("По смисъла", "XXXXX")
    res = uncovered_legal_text(soup, broken)
    assert res["uncovered_chars"] > 200


# ---------------------------------------------------------------------------
# New tests for Task 6 — full-text signature + all-fixtures sweep
# ---------------------------------------------------------------------------


def test_shared_40char_prefix_false_negative_detected():
    """Full-text matching catches dropped element whose first 40 chars match a different present element.

    Two FinalEdictsArticle elements share an identical 41-char Bulgarian opener but
    differ in the tail.  Only element 1 reaches the markdown; element 2 is "dropped".

    With the old t[:40] signature: element 2's prefix matches element 1 in M → false
    negative (uncovered_chars == 0).  After the fix (full text / 100-char anchors):
    element 2's distinct tail is absent from M → gate fires.
    """
    # Shared opener: "§ 1. По смисъла на настоящия закон думата" — 41 chars after normalization
    shared = "§ 1. По смисъла на настоящия закон думата"
    body1 = f"{shared} означава специфично нещо по смисъла."
    body2 = f"{shared} означава нещо напълно различно и несвързано."

    html = (
        '<div class="TitleDocument">ЗАКОН ЗА ТЕСТ</div>'
        f'<div class="FinalEdictsArticle">{body1}</div>'
        f'<div class="FinalEdictsArticle">{body2}</div>'
    )
    soup = BeautifulSoup(html, "lxml")

    # Markdown contains only element 1 — element 2 is silently dropped
    md = f"# ЗАКОН ЗА ТЕСТ\n\n{body1}"

    res = uncovered_legal_text(soup, md)
    assert res["uncovered_chars"] > 0, (
        "Gate must detect the dropped element whose 40-char prefix "
        "matches another present element (false-negative regression)."
    )


@pytest.mark.parametrize("fixture", [
    "zeu.html",
    "gpk.html",
    "zop.html",
    "ppz-aktsizi.html",
    "pravilnik-sadilishta.html",
    "naredba-04-14.html",
])
def test_denylist_seam_no_spine_inside_chrome(fixture: str):
    """Shared-denylist guarantee: no denylisted-class element STRICTLY INSIDE the
    content region wraps a spine element in any act fixture.

    The parser and the gate share CHROME_DENYLIST — both skip the same subtrees.
    If a denylisted element ever wrapped real legal text (a spine element), neither
    pass would see it: the gate would not flag the gap, and the parser would not emit
    it.  This test asserts that the current fixtures have no such invisible wrapper.

    A non-zero result would require IMPLEMENTATION-PREFLIGHT before proceeding,
    because it would mean the denylist needs a targeted exception rather than a
    blanket skip.
    """
    html = (FIXTURES / "html" / fixture).read_bytes().decode("cp1251")
    soup = BeautifulSoup(html, "lxml")

    # Locate the content region (same LCA the parser and gate use)
    region, _ = HtmlToMarkdown()._content_region(soup)

    # Spine classes: CLASS_MAP entries with include=True
    spine_classes: frozenset[str] = frozenset(c for c, (_, inc) in CLASS_MAP.items() if inc)

    violations: list[str] = []
    for el in region.descendants:
        if not isinstance(el, Tag):
            continue
        el_classes = set(el.get("class") or [])
        if not (el_classes & CHROME_DENYLIST):
            continue
        # This element has a denylisted class — check if it wraps any spine element
        for desc in el.descendants:
            if not isinstance(desc, Tag):
                continue
            desc_classes = set(desc.get("class") or [])
            if desc_classes & spine_classes:
                violations.append(
                    f"chrome element <{el.name} class='{' '.join(el.get('class', []))}' /> "
                    f"wraps spine <{desc.name} class='{' '.join(desc.get('class', []))}' />"
                )

    assert violations == [], (
        f"{fixture}: {len(violations)} denylisted element(s) inside content region "
        f"wrap spine elements — the denylist seam is broken:\n"
        + "\n".join(violations[:5])
    )


@pytest.mark.parametrize("fixture", [
    "zeu.html",
    "gpk.html",
    "zop.html",
    "ppz-aktsizi.html",
    "pravilnik-sadilishta.html",
    "naredba-04-14.html",
])
def test_all_fixtures_no_false_positives(fixture: str):
    """Full parse of every act fixture must stay within the chrome-residual budget.

    A clean conversion leaves at most ~21 chars of 'boxi' chrome residual.
    64 chars is the gate threshold: anything above indicates a real false positive.
    """
    soup = _load_soup(fixture)
    md = HtmlToMarkdown().convert(soup)
    res = uncovered_legal_text(soup, md)
    assert res["uncovered_chars"] <= 64, (
        f"{fixture}: uncovered_chars={res['uncovered_chars']} exceeds gate threshold 64; "
        f"buckets={res['buckets']}"
    )


# ---------------------------------------------------------------------------
# New tests for Task 9 — full-substring match at any length (P0-4)
# ---------------------------------------------------------------------------


def test_middle_truncation_of_long_node_is_uncovered():
    """>200-char nodes were only head/tail-anchored: a parser bug
    dropping text from the MIDDLE passed the gate with 0 uncovered
    chars (P0-4, review 2026-07-02) — the exact D-047 failure class."""
    sentence = ("Възложителят провежда процедурата при условията и по реда "
                "на този закон и приложимите подзаконови нормативни актове, "
                "като осигурява публичност и прозрачност на всички етапи. ")
    full_text = sentence * 4                      # ~640 normalized chars
    html = f'<div class="boxi"><p class="Article">{full_text}</p></div>'
    soup = BeautifulSoup(html, "lxml")
    truncated = full_text[:200] + full_text[-200:]   # middle dropped
    result = uncovered_legal_text(soup, truncated)
    assert result["uncovered_chars"] > 0


def test_trailing_punctuation_variance_still_passes():
    text = ("Министерският съвет приема наредба за прилагането на този "
            "закон в тримесечен срок от обнародването му в Държавен "
            "вестник, като определя реда и условията за нейното изпълнение "
            "и контролните органи по прилагането ѝ. ") * 2
    html = f'<div class="boxi"><p class="Article">{text}</p></div>'
    soup = BeautifulSoup(html, "lxml")
    markdown = text.strip().rstrip(".")           # trailing '.' lost only
    result = uncovered_legal_text(soup, markdown)
    assert result["uncovered_chars"] == 0


# ---------------------------------------------------------------------------
# FR-034 Task 4 — structural paragraph-topology check (REPORT mode)
# ---------------------------------------------------------------------------


def test_structure_mismatch_detects_flattened_alineas():
    html = '''
    <div class="Article">
        <div><b>Чл. 36.</b> Първа алинея текст.</div>
        <div>Втора алинея текст.</div>
    </div>
    '''
    soup = BeautifulSoup(html, "lxml")
    flattened_md = "**Чл. 36.** Първа алинея текст. Втора алинея текст.\n"
    mismatches = structure_mismatches(soup, flattened_md)
    assert mismatches == [
        {"article": "36", "expected_blocks": 2, "got_blocks": 1}]


def test_structure_mismatch_clean_when_paragraphs_preserved():
    html = '''
    <div class="Article">
        <div><b>Чл. 36.</b> Първа алинея текст.</div>
        <div>Втора алинея текст.</div>
    </div>
    '''
    soup = BeautifulSoup(html, "lxml")
    good_md = "**Чл. 36.** Първа алинея текст.\n\nВтора алинея текст.\n"
    assert structure_mismatches(soup, good_md) == []


def test_structure_mismatch_title_glue_is_not_a_lost_paragraph():
    """Rule-1a accounting: the заглавие block is merged INTO the anchor
    block by the parser, so a titled article with N source blocks maps to
    N-1 markdown paragraphs by design — never a mismatch."""
    html = '''
    <div class="boxi">
        <div class="Article">
            <div>Предмет на закона</div>
            <div><b>Чл. 1.</b> Първа алинея текст.</div>
            <div>Втора алинея текст.</div>
        </div>
    </div>
    '''
    soup = BeautifulSoup(html, "lxml")
    md = HtmlToMarkdown().convert(soup)
    # Lock the parser side: title glued onto the anchor line (rule 1a)
    assert "Предмет на закона Чл. 1. Първа алинея текст." in md
    assert structure_mismatches(soup, md) == []


def test_structure_mismatch_titled_article_flattening_still_detected():
    """Glue awareness must not blind the check: a titled article whose
    алинеи ARE flattened still reports expected 2 / got 1."""
    html = '''
    <div class="Article">
        <div>Предмет на закона</div>
        <div><b>Чл. 1.</b> Първа алинея текст.</div>
        <div>Втора алинея текст.</div>
    </div>
    '''
    soup = BeautifulSoup(html, "lxml")
    flattened_md = "Предмет на закона Чл. 1. Първа алинея текст. Втора алинея текст.\n"
    assert structure_mismatches(soup, flattened_md) == [
        {"article": "1", "expected_blocks": 2, "got_blocks": 1}]


def test_structure_mismatch_ignores_headers_and_cite_paragraphs():
    """A structural header closes the running article; a paragraph with
    2+ anchors (cite list / template) is never counted as continuation."""
    html = '''
    <div class="Article">
        <div><b>Чл. 5.</b> Първа алинея текст.</div>
        <div>Втора алинея текст.</div>
    </div>
    '''
    soup = BeautifulSoup(html, "lxml")
    md = (
        "**Чл. 5.** Първа алинея текст.\n\n"
        "Втора алинея текст.\n\n"
        "## Глава втора\n\n"
        "Декларация по Чл. 5. и Чл. 6. от закона.\n"
    )
    assert structure_mismatches(soup, md) == []


@pytest.mark.parametrize("fixture", [
    "zeu.html",
    "gpk.html",
    "zop.html",
    "ppz-aktsizi.html",
    "pravilnik-sadilishta.html",
    "naredba-04-14.html",
    "zzd.html",
])
def test_structure_mismatch_zero_on_real_fixtures(fixture: str):
    """Post-FR-034 parser: no act fixture loses a source block. This is the
    corpus-facing false-positive guard for the report-mode gate."""
    soup = _load_soup(fixture)
    md = HtmlToMarkdown().convert(soup)
    assert structure_mismatches(soup, md) == []


def test_make_gate_record_carries_structure_mismatches():
    """REPORT mode: the gate record gains a structure_mismatches key
    without changing any pass/fail semantics."""
    gate = {"uncovered_chars": 120, "buckets": {"Article": 120}}
    rec = make_gate_record(7, "slug", "Заглавие", gate)
    assert rec["structure_mismatches"] == []

    mm = [{"article": "36", "expected_blocks": 2, "got_blocks": 1}]
    rec2 = make_gate_record(7, "slug", "Заглавие", gate, structure_mismatches=mm)
    assert rec2["structure_mismatches"] == mm
    assert rec2["uncovered_chars"] == 120
