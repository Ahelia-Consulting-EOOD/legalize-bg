"""Catalog Crawler — Legalize NormDiscovery interface for lex.bg."""

import re
from dataclasses import dataclass

from bs4 import BeautifulSoup


LEX_BG_TREE = "https://lex.bg/laws/tree"
ENCODING = "cp1251"

# Category name -> number of tree pages (0-based index)
CATEGORIES_CONFIG = {
    "laws": 12,
    "code": 1,
    "ords": 75,
    "regs": 14,
    "reg_laws": 2,
}

# Category URL slug -> corpus directory name
CATEGORY_DIRS = {
    "laws": "laws",
    "code": "codes",
    "ords": "ordinances",
    "regs": "regulations",
    "reg_laws": "implementing",
}

DOC_ID_PATTERN = re.compile(r"/laws/ldoc/(-?\d+)")


@dataclass
class CatalogCrawler:
    """Crawls lex.bg tree pages to discover all legislative act doc IDs."""

    CATEGORIES = CATEGORIES_CONFIG

    @staticmethod
    def parse_tree_page(html: str, category: str) -> list[dict]:
        """Parse a single tree page and extract doc entries."""
        soup = BeautifulSoup(html, "lxml")
        entries = []
        for link in soup.find_all("a", href=DOC_ID_PATTERN):
            match = DOC_ID_PATTERN.search(link["href"])
            if match:
                doc_id = int(match.group(1))
                name = link.get_text(strip=True)
                entries.append({
                    "doc_id": doc_id,
                    "name": name,
                    "category": category,
                })
        return entries

    def crawl_all(self, transport) -> list[dict]:
        """Crawl all tree pages across all categories. Returns full catalog.

        Deduplicates doc_ids across categories with first-wins semantics.
        lex.bg puts the Конституция (doc_id 521957377) as a sidebar link on
        every tree page — without dedup the catalog would carry ~104 copies.
        A small number of acts (e.g. правилници) also legitimately appear in
        two related categories; first-wins keeps the one the crawler
        encounters first (iteration order: laws → code → ords → regs → reg_laws).
        """
        catalog: list[dict] = []
        seen: set[int] = set()
        for category, num_pages in CATEGORIES_CONFIG.items():
            for page_idx in range(num_pages):
                url = f"{LEX_BG_TREE}/{category}/{page_idx}"
                raw = transport.get_tree_page(url)
                html = raw.decode(ENCODING)
                for entry in self.parse_tree_page(html, category):
                    if entry["doc_id"] in seen:
                        continue
                    seen.add(entry["doc_id"])
                    catalog.append(entry)
        return catalog
