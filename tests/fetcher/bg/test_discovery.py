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


class FakeTreeTransport:
    """Returns canned cp1251-encoded bytes per URL."""

    def __init__(self, url_to_html: dict[str, str]):
        self._map = {u: h.encode("cp1251") for u, h in url_to_html.items()}

    def get_tree_page(self, url: str) -> bytes:
        return self._map.get(url, b"")


def _tree_html(doc_ids: list[tuple[int, str]]) -> str:
    links = "".join(
        f'<a href="/laws/ldoc/{d}">{n}</a>' for d, n in doc_ids
    )
    return f"<html><body>{links}</body></html>"


def test_crawl_all_dedupes_doc_ids_across_categories(monkeypatch):
    """Конституция (doc_id 521957377) appears on every tree page as a sidebar
    link. crawl_all must keep exactly one entry per doc_id (first-wins)."""
    from fetcher.bg import discovery

    # Shrink to 1 page per category for the test
    monkeypatch.setattr(
        discovery, "CATEGORIES_CONFIG",
        {"laws": 1, "code": 1, "ords": 1, "regs": 1, "reg_laws": 1},
    )
    monkeypatch.setattr(
        CatalogCrawler, "CATEGORIES",
        {"laws": 1, "code": 1, "ords": 1, "regs": 1, "reg_laws": 1},
    )

    # Конституция (42) appears on every tree; each category also has a unique doc.
    urls = {
        "https://lex.bg/laws/tree/laws/0": _tree_html([(42, "Конституция"), (100, "Law A")]),
        "https://lex.bg/laws/tree/code/0": _tree_html([(42, "Конституция"), (200, "Code A")]),
        "https://lex.bg/laws/tree/ords/0": _tree_html([(42, "Конституция"), (300, "Ord A")]),
        "https://lex.bg/laws/tree/regs/0": _tree_html([(42, "Конституция"), (400, "Reg A"), (500, "Shared")]),
        "https://lex.bg/laws/tree/reg_laws/0": _tree_html([(42, "Конституция"), (500, "Shared"), (600, "PPZ A")]),
    }

    catalog = CatalogCrawler().crawl_all(FakeTreeTransport(urls))
    doc_ids = [e["doc_id"] for e in catalog]

    # Each doc_id appears exactly once
    assert len(doc_ids) == len(set(doc_ids)), f"duplicates found: {doc_ids}"
    # Конституция lands in the first category encountered (laws)
    konstitutsiya = [e for e in catalog if e["doc_id"] == 42]
    assert len(konstitutsiya) == 1
    assert konstitutsiya[0]["category"] == "laws"
    # Shared правилник lands in regs (first of regs/reg_laws iteration)
    shared = [e for e in catalog if e["doc_id"] == 500]
    assert len(shared) == 1
    assert shared[0]["category"] == "regs"
    # All expected unique docs are present
    assert set(doc_ids) == {42, 100, 200, 300, 400, 500, 600}
