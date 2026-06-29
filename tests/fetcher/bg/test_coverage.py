"""Tests for fetcher.bg.coverage — class-agnostic legal-text coverage validator."""
import pathlib

import pytest
from bs4 import BeautifulSoup, Tag

from fetcher.bg.text_parser import HtmlToMarkdown, CHROME_DENYLIST, CLASS_MAP, content_region
from fetcher.bg.coverage import uncovered_legal_text

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
