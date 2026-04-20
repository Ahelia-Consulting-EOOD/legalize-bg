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
        """Crawl all tree pages across all categories. Returns full catalog."""
        catalog = []
        for category, num_pages in CATEGORIES_CONFIG.items():
            for page_idx in range(num_pages):
                url = f"{LEX_BG_TREE}/{category}/{page_idx}"
                raw = transport.get_tree_page(url)
                html = raw.decode(ENCODING)
                entries = self.parse_tree_page(html, category)
                catalog.extend(entries)
        return catalog
