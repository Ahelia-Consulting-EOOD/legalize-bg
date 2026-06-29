"""Tests for fetcher.bg.coverage — class-agnostic legal-text coverage validator."""
import pathlib

import pytest
from bs4 import BeautifulSoup

from fetcher.bg.text_parser import HtmlToMarkdown
from fetcher.bg.coverage import uncovered_legal_text

FIXTURES = pathlib.Path(__file__).parent.parent.parent / "fixtures"


def _load_soup(name: str) -> BeautifulSoup:
    html = (FIXTURES / "html" / name).read_bytes().decode("cp1251")
    return BeautifulSoup(html, "lxml")


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
