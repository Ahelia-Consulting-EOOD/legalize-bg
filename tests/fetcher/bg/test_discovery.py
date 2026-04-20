import pathlib
import pytest
from fetcher.bg.discovery import CatalogCrawler

FIXTURES = pathlib.Path(__file__).parent.parent.parent / "fixtures" / "html"


def test_parse_tree_page_extracts_doc_ids():
    html = (FIXTURES / "tree_laws_0.html").read_bytes().decode("cp1251")
    entries = CatalogCrawler.parse_tree_page(html, category="laws")
    assert len(entries) > 0
    for entry in entries:
        assert "doc_id" in entry
        assert "name" in entry
        assert "category" in entry
        assert entry["category"] == "laws"
        assert isinstance(entry["doc_id"], int)


def test_parse_tree_page_extracts_correct_count():
    """Tree pages have ~35 items."""
    html = (FIXTURES / "tree_laws_0.html").read_bytes().decode("cp1251")
    entries = CatalogCrawler.parse_tree_page(html, category="laws")
    assert 30 <= len(entries) <= 40  # ~35 per page


CATEGORIES = {
    "laws": 12,
    "code": 1,
    "ords": 75,
    "regs": 14,
    "reg_laws": 2,
}


def test_category_config():
    assert CatalogCrawler.CATEGORIES == CATEGORIES
