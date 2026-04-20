# Phase 1a: Bootstrap Scrape — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Scrape all ~3,574 Bulgarian legislative acts from lex.bg, convert to Markdown+YAML, commit each as a `[bootstrap]` commit, and build a SQLite catalog index.

**Architecture:** Four Legalize-compatible modules in `fetcher/bg/` (client, discovery, text_parser, metadata) produce Markdown+YAML files. A bootstrap runner orchestrates the pipeline: crawl catalog → fetch each act → parse HTML → generate Markdown+YAML → commit to git → index in SQLite. Test-first with cached HTML fixtures.

**Tech Stack:** Python 3.12+, requests, BeautifulSoup4, PyYAML, sqlite3 (stdlib), pytest

**Key constraints:**
- Rate limit: 1 req/sec to lex.bg
- Encoding: cp1251 → UTF-8
- One `[bootstrap]` commit per act with Source-Id, Source-Date, Norm-Id trailers
- 8 mandatory Legalize YAML fields + 5 Bulgarian extensions
- Legalize interface compatibility (LegislativeClient, NormDiscovery, TextParser, MetadataParser)

**Authority docs to read before implementing:**
- `docs/process/delivery-contract.md` — commit format, quality gates, rate limiting protocol
- `docs/process/OWNER-DIRECTIVES.md` — non-negotiable constraints
- `docs/data/schema-reference.md` — YAML frontmatter + SQLite schema
- `docs/architecture/container-view.md` — module responsibilities
- `docs/architecture/runtime-flows.md` — bootstrap flow sequence
- `docs/testing/test-strategy.md` — fixture strategy, golden files

---

### Task 1: Project Setup

**Files:**
- Create: `pyproject.toml`
- Create: `fetcher/__init__.py`
- Create: `fetcher/bg/__init__.py`
- Create: `tests/__init__.py`
- Create: `tests/fetcher/__init__.py`
- Create: `tests/fetcher/bg/__init__.py`
- Create: `tests/fixtures/html/.gitkeep`
- Create: `tests/fixtures/golden/.gitkeep`

**Step 1: Create pyproject.toml**

```toml
[project]
name = "legalize-bg"
version = "0.1.0"
description = "Bulgarian legislation as code"
requires-python = ">=3.12"
dependencies = [
    "requests>=2.31",
    "beautifulsoup4>=4.12",
    "pyyaml>=6.0",
    "lxml>=5.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-cov>=4.0",
]

[tool.pytest.ini_options]
testpaths = ["tests"]
```

**Step 2: Create directory structure**

```bash
mkdir -p fetcher/bg tests/fetcher/bg tests/fixtures/html tests/fixtures/golden
touch fetcher/__init__.py fetcher/bg/__init__.py tests/__init__.py tests/fetcher/__init__.py tests/fetcher/bg/__init__.py
touch tests/fixtures/html/.gitkeep tests/fixtures/golden/.gitkeep
```

**Step 3: Install dependencies**

```bash
pip install -e ".[dev]"
```

**Step 4: Verify pytest runs**

Run: `pytest --co -q`
Expected: "no tests ran" (no error)

**Step 5: Commit**

```bash
git init
git add pyproject.toml fetcher/ tests/
git commit -m "chore: project setup with fetcher/bg/ structure and test fixtures"
```

---

### Task 2: Content Fetcher (client.py)

**Files:**
- Create: `fetcher/bg/client.py`
- Create: `tests/fetcher/bg/test_client.py`
- Create: `tests/fixtures/html/zop.html` (captured manually — see Step 1)

**Step 1: Capture a test fixture**

Save one real lex.bg page as a fixture. This is the only live HTTP request in the test suite.

```bash
python -c "
import requests
resp = requests.get('https://lex.bg/laws/ldoc/2136735703')
with open('tests/fixtures/html/zop.html', 'wb') as f:
    f.write(resp.content)
print(f'Saved {len(resp.content)} bytes')
"
```

Verify the fixture is cp1251 encoded (should contain bytes like `\xc7\xe0\xea\xee\xed` = "Закон").

**Step 2: Write the failing test**

```python
# tests/fetcher/bg/test_client.py
import pathlib
import pytest
from fetcher.bg.client import LexBgClient

FIXTURES = pathlib.Path(__file__).parent.parent.parent / "fixtures" / "html"


class FakeTransport:
    """Serves fixtures from disk instead of HTTP."""

    def __init__(self, fixtures_dir: pathlib.Path):
        self._fixtures = fixtures_dir

    def get(self, doc_id: int) -> bytes:
        # Map known doc_ids to fixture files
        mapping = {2136735703: "zop.html"}
        filename = mapping.get(doc_id)
        if filename is None:
            raise FileNotFoundError(f"No fixture for doc_id {doc_id}")
        return (self._fixtures / filename).read_bytes()


def test_fetch_returns_decoded_text():
    client = LexBgClient(transport=FakeTransport(FIXTURES))
    text = client.fetch(2136735703)
    assert isinstance(text, str)
    assert "Закон" in text  # Bulgarian text, properly decoded from cp1251


def test_fetch_returns_parseable_html():
    client = LexBgClient(transport=FakeTransport(FIXTURES))
    soup = client.fetch_soup(2136735703)
    title = soup.select_one(".TitleDocument")
    assert title is not None
    assert "ОБЩЕСТВЕНИТЕ ПОРЪЧКИ" in title.get_text()
```

**Step 3: Run test to verify it fails**

Run: `pytest tests/fetcher/bg/test_client.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'fetcher.bg.client'"

**Step 4: Write minimal implementation**

```python
# fetcher/bg/client.py
"""Content Fetcher — Legalize LegislativeClient interface for lex.bg."""

import time
from dataclasses import dataclass

import requests
from bs4 import BeautifulSoup


LEX_BG_BASE = "https://lex.bg/laws/ldoc"
ENCODING = "cp1251"
RATE_LIMIT_SECONDS = 1.0
USER_AGENT = "legalize-bg/0.1 (https://github.com/Ahelia-Consulting-EOOD/legalize-bg)"


class HttpTransport:
    """Live HTTP transport with rate limiting."""

    def __init__(self):
        self._session = requests.Session()
        self._session.headers["User-Agent"] = USER_AGENT
        self._last_request_time = 0.0

    def get(self, doc_id: int) -> bytes:
        elapsed = time.monotonic() - self._last_request_time
        if elapsed < RATE_LIMIT_SECONDS:
            time.sleep(RATE_LIMIT_SECONDS - elapsed)
        url = f"{LEX_BG_BASE}/{doc_id}"
        resp = self._session.get(url, timeout=30)
        self._last_request_time = time.monotonic()
        resp.raise_for_status()
        return resp.content

    def close(self):
        self._session.close()


@dataclass
class LexBgClient:
    """Fetches legislative act HTML from lex.bg with cp1251 decoding."""

    transport: object  # HttpTransport or FakeTransport for tests

    def fetch(self, doc_id: int) -> str:
        """Fetch raw HTML as decoded UTF-8 string."""
        raw = self.transport.get(doc_id)
        return raw.decode(ENCODING)

    def fetch_soup(self, doc_id: int) -> BeautifulSoup:
        """Fetch and parse HTML into BeautifulSoup DOM."""
        text = self.fetch(doc_id)
        return BeautifulSoup(text, "lxml")

    def close(self):
        if hasattr(self.transport, "close"):
            self.transport.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
```

**Step 5: Run test to verify it passes**

Run: `pytest tests/fetcher/bg/test_client.py -v`
Expected: 2 passed

**Step 6: Commit**

```bash
git add fetcher/bg/client.py tests/fetcher/bg/test_client.py tests/fixtures/html/zop.html
git commit -m "feat: content fetcher with cp1251 decoding and fixture-based tests"
```

---

### Task 3: Catalog Crawler (discovery.py)

**Files:**
- Create: `fetcher/bg/discovery.py`
- Create: `tests/fetcher/bg/test_discovery.py`
- Create: `tests/fixtures/html/tree_laws_0.html` (captured manually)

**Step 1: Capture a tree page fixture**

```bash
python -c "
import requests
resp = requests.get('https://lex.bg/laws/tree/laws/0')
with open('tests/fixtures/html/tree_laws_0.html', 'wb') as f:
    f.write(resp.content)
print(f'Saved {len(resp.content)} bytes')
"
```

**Step 2: Write the failing test**

```python
# tests/fetcher/bg/test_discovery.py
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
```

**Step 3: Run test to verify it fails**

Run: `pytest tests/fetcher/bg/test_discovery.py -v`
Expected: FAIL

**Step 4: Write minimal implementation**

```python
# fetcher/bg/discovery.py
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
```

**Step 5: Run test to verify it passes**

Run: `pytest tests/fetcher/bg/test_discovery.py -v`
Expected: 3 passed

**Step 6: Commit**

```bash
git add fetcher/bg/discovery.py tests/fetcher/bg/test_discovery.py tests/fixtures/html/tree_laws_0.html
git commit -m "feat: catalog crawler parses lex.bg tree pages for doc IDs"
```

---

### Task 4: HTML-to-Markdown Converter (text_parser.py)

**Files:**
- Create: `fetcher/bg/text_parser.py`
- Create: `tests/fetcher/bg/test_text_parser.py`
- Create: `tests/fixtures/golden/zop.md` (manually reviewed golden file)

**Step 1: Write the failing tests**

```python
# tests/fetcher/bg/test_text_parser.py
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
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/fetcher/bg/test_text_parser.py -v`
Expected: FAIL

**Step 3: Write minimal implementation**

```python
# fetcher/bg/text_parser.py
"""HTML-to-Markdown Converter — Legalize TextParser interface for lex.bg."""

from bs4 import BeautifulSoup, Tag


# CSS class -> (markdown prefix, include in output)
CLASS_MAP = {
    "TitleDocument": ("# ", True),
    "PreHistory": ("*", True),       # italic
    "Part": ("## ", True),
    "Heading": ("### ", True),
    "Section": ("#### ", True),
    "Article": ("", True),           # special handling for bold article number
    "TransitionalFinalEdicts": ("## ", True),
    "HistoryOfDocument": ("", False),  # excluded from body
}


class HtmlToMarkdown:
    """Converts lex.bg HTML DOM to structured Markdown."""

    def convert(self, soup: BeautifulSoup) -> str:
        """Convert parsed HTML to Markdown body (no frontmatter)."""
        lines: list[str] = []

        for element in soup.find_all(class_=list(CLASS_MAP.keys())):
            if not isinstance(element, Tag):
                continue

            css_class = self._get_mapped_class(element)
            if css_class is None:
                continue

            prefix, include = CLASS_MAP[css_class]
            if not include:
                continue

            if css_class == "Article":
                lines.append(self._format_article(element))
            elif css_class == "PreHistory":
                text = element.get_text(strip=True)
                if text:
                    lines.append(f"*{text}*")
            else:
                text = element.get_text(strip=True)
                if text:
                    lines.append(f"{prefix}{text}")

            lines.append("")  # blank line after each block

        return "\n".join(lines).strip() + "\n"

    def _get_mapped_class(self, element: Tag) -> str | None:
        """Find the first CSS class that maps to a known role."""
        for cls in element.get("class", []):
            if cls in CLASS_MAP:
                return cls
        return None

    def _format_article(self, element: Tag) -> str:
        """Format an article element, bolding the article number."""
        # Extract text, preserving paragraph breaks
        text = self._extract_article_text(element)

        # Bold the article number prefix (e.g., "Чл. 1.")
        if text.startswith("Чл."):
            dot_pos = text.find(".", 4)  # find the dot after article number
            if dot_pos > 0:
                article_num = text[: dot_pos + 1]
                rest = text[dot_pos + 1:]
                return f"**{article_num}**{rest}"

        return text

    def _extract_article_text(self, element: Tag) -> str:
        """Extract article text, converting <br> to newlines."""
        parts = []
        for child in element.children:
            if isinstance(child, Tag):
                if child.name == "br":
                    parts.append("\n")
                else:
                    parts.append(child.get_text())
            else:
                text = str(child)
                if text.strip():
                    parts.append(text.strip())
        return " ".join(parts).replace("  ", " ").strip()
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/fetcher/bg/test_text_parser.py -v`
Expected: 10 passed

Note: The real lex.bg HTML may have structural variations. If any test fails on the live fixture (`zop.html`), inspect the actual HTML structure and adjust the parser. This is expected — the unit tests with inline HTML verify the mapping logic, while the integration test reveals real-world edge cases.

**Step 5: Commit**

```bash
git add fetcher/bg/text_parser.py tests/fetcher/bg/test_text_parser.py
git commit -m "feat: HTML-to-Markdown converter with CSS class mapping"
```

---

### Task 5: Metadata Parser (metadata.py)

**Files:**
- Create: `fetcher/bg/metadata.py`
- Create: `tests/fetcher/bg/test_metadata.py`

**Step 1: Write the failing tests**

```python
# tests/fetcher/bg/test_metadata.py
import pathlib
import pytest
from bs4 import BeautifulSoup
from fetcher.bg.metadata import MetadataParser

FIXTURES = pathlib.Path(__file__).parent.parent.parent / "fixtures"


def _load_soup(name: str) -> BeautifulSoup:
    html = (FIXTURES / "html" / name).read_bytes().decode("cp1251")
    return BeautifulSoup(html, "lxml")


def test_extracts_titulo():
    soup = _load_soup("zop.html")
    meta = MetadataParser().parse(soup, doc_id=2136735703, category="laws")
    assert "ОБЩЕСТВЕНИТЕ ПОРЪЧКИ" in meta["titulo"]


def test_extracts_identificador():
    soup = _load_soup("zop.html")
    meta = MetadataParser().parse(soup, doc_id=2136735703, category="laws")
    assert meta["identificador"] == "2136735703"


def test_pais_is_bg():
    soup = _load_soup("zop.html")
    meta = MetadataParser().parse(soup, doc_id=2136735703, category="laws")
    assert meta["pais"] == "bg"


def test_rango_for_law():
    soup = _load_soup("zop.html")
    meta = MetadataParser().parse(soup, doc_id=2136735703, category="laws")
    assert meta["rango"] == "закон"


def test_fuente_is_lexbg():
    soup = _load_soup("zop.html")
    meta = MetadataParser().parse(soup, doc_id=2136735703, category="laws")
    assert meta["fuente"] == "lex.bg"


def test_extracts_effective_date():
    soup = _load_soup("zop.html")
    meta = MetadataParser().parse(soup, doc_id=2136735703, category="laws")
    assert "effective_date" in meta
    # ZOP effective date is 2016-04-15
    assert meta["effective_date"] is not None


def test_extracts_amendment_history():
    soup = _load_soup("zop.html")
    meta = MetadataParser().parse(soup, doc_id=2136735703, category="laws")
    assert "amendment_history" in meta
    assert isinstance(meta["amendment_history"], list)
    # ZOP has been amended many times
    assert len(meta["amendment_history"]) > 5
    # Each entry has dv and date
    for entry in meta["amendment_history"]:
        assert "dv" in entry
        assert "date" in entry


def test_category_to_rango_mapping():
    assert MetadataParser.CATEGORY_TO_RANGO["laws"] == "закон"
    assert MetadataParser.CATEGORY_TO_RANGO["codes"] == "кодекс"
    assert MetadataParser.CATEGORY_TO_RANGO["ordinances"] == "наредба"
    assert MetadataParser.CATEGORY_TO_RANGO["regulations"] == "правилник"
    assert MetadataParser.CATEGORY_TO_RANGO["implementing"] == "правилник по прилагане"


def test_all_13_fields_present():
    soup = _load_soup("zop.html")
    meta = MetadataParser().parse(soup, doc_id=2136735703, category="laws")
    required = [
        "titulo", "identificador", "pais", "rango",
        "fecha_publicacion", "ultima_actualizacion", "estado", "fuente",
        "dv_issue", "dv_year", "effective_date", "category", "eli",
    ]
    for field in required:
        assert field in meta, f"Missing field: {field}"
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/fetcher/bg/test_metadata.py -v`
Expected: FAIL

**Step 3: Write minimal implementation**

```python
# fetcher/bg/metadata.py
"""Metadata Parser — Legalize MetadataParser interface for lex.bg."""

import re
from datetime import date

from bs4 import BeautifulSoup, Tag


CATEGORY_TO_RANGO = {
    "laws": "закон",
    "codes": "кодекс",
    "ordinances": "наредба",
    "regulations": "правилник",
    "implementing": "правилник по прилагане",
}

# Maps lex.bg tree category slugs to corpus directory names
CATEGORY_SLUG_TO_DIR = {
    "laws": "laws",
    "code": "codes",
    "ords": "ordinances",
    "regs": "regulations",
    "reg_laws": "implementing",
}

# Regex patterns for parsing Bulgarian dates and DV references
DATE_PATTERN = re.compile(
    r"(\d{1,2})\.(\d{1,2})\.(\d{4})\s*г\."
)

DV_REF_PATTERN = re.compile(
    r"(?:ДВ|DV),?\s*бр\.?\s*(\d+)\s*(?:от\s*(\d{1,2})\.(\d{1,2})\.(\d{4})\s*г\.?)?"
)

EFFECTIVE_DATE_PATTERN = re.compile(
    r"[Вв]\s*сила\s*от\s*(\d{1,2})\.(\d{1,2})\.(\d{4})\s*г\."
)


class MetadataParser:
    """Extracts YAML frontmatter fields from lex.bg HTML DOM."""

    CATEGORY_TO_RANGO = CATEGORY_TO_RANGO

    def parse(self, soup: BeautifulSoup, doc_id: int, category: str) -> dict:
        """Extract all frontmatter fields from parsed HTML.

        Args:
            soup: Parsed HTML DOM
            doc_id: lex.bg document ID
            category: Corpus category directory name (laws, codes, ordinances, ...)

        Returns:
            dict with 13 named fields + amendment_history array
        """
        title = self._extract_title(soup)
        pre_history = self._extract_pre_history(soup)
        amendment_history = self._extract_amendment_history(soup)

        effective_date = self._parse_effective_date(pre_history)
        pub_date = self._extract_publication_date(amendment_history, pre_history)
        last_update = self._extract_last_update(amendment_history, pub_date)
        dv_issue, dv_year = self._extract_first_dv(amendment_history, pre_history)

        rango = CATEGORY_TO_RANGO.get(category, "закон")
        slug = self._title_to_slug(title)

        return {
            # 8 mandatory Legalize fields
            "titulo": title,
            "identificador": str(doc_id),
            "pais": "bg",
            "rango": rango,
            "fecha_publicacion": pub_date,
            "ultima_actualizacion": last_update,
            "estado": "vigente",
            "fuente": "lex.bg",
            # 5 Bulgarian extensions
            "dv_issue": dv_issue,
            "dv_year": dv_year,
            "effective_date": effective_date,
            "category": category,
            "eli": f"/eli/bg/{rango}/{pub_date[:4] if pub_date else 'unknown'}/{slug}/con",
            # Amendment history array
            "amendment_history": amendment_history,
        }

    def _extract_title(self, soup: BeautifulSoup) -> str:
        el = soup.select_one(".TitleDocument")
        return el.get_text(strip=True) if el else ""

    def _extract_pre_history(self, soup: BeautifulSoup) -> str:
        el = soup.select_one(".PreHistory")
        return el.get_text(strip=True) if el else ""

    def _extract_amendment_history(self, soup: BeautifulSoup) -> list[dict]:
        el = soup.select_one(".HistoryOfDocument")
        if el is None:
            return []

        text = el.get_text()
        entries = []
        for match in DV_REF_PATTERN.finditer(text):
            issue = match.group(1)
            if match.group(2) and match.group(3) and match.group(4):
                day = int(match.group(2))
                month = int(match.group(3))
                year = int(match.group(4))
                try:
                    d = date(year, month, day)
                    entries.append({"dv": f"{issue}/{year}", "date": d.isoformat()})
                except ValueError:
                    entries.append({"dv": f"{issue}/{year}", "date": None})
            else:
                entries.append({"dv": issue, "date": None})

        return entries

    def _parse_effective_date(self, pre_history: str) -> str | None:
        match = EFFECTIVE_DATE_PATTERN.search(pre_history)
        if match:
            day, month, year = int(match.group(1)), int(match.group(2)), int(match.group(3))
            try:
                return date(year, month, day).isoformat()
            except ValueError:
                return None
        return None

    def _extract_publication_date(self, amendments: list[dict], pre_history: str) -> str | None:
        # First DV reference is usually the publication
        if amendments and amendments[0].get("date"):
            return amendments[0]["date"]
        # Fallback: parse from pre_history
        match = DATE_PATTERN.search(pre_history)
        if match:
            day, month, year = int(match.group(1)), int(match.group(2)), int(match.group(3))
            try:
                return date(year, month, day).isoformat()
            except ValueError:
                return None
        return None

    def _extract_last_update(self, amendments: list[dict], pub_date: str | None) -> str | None:
        if amendments:
            # Last amendment with a date
            for entry in reversed(amendments):
                if entry.get("date"):
                    return entry["date"]
        return pub_date

    def _extract_first_dv(self, amendments: list[dict], pre_history: str) -> tuple[str | None, int | None]:
        if amendments:
            dv = amendments[0].get("dv", "")
            if "/" in dv:
                issue, year = dv.split("/", 1)
                return issue, int(year) if year.isdigit() else None
            return dv, None
        # Fallback
        match = DV_REF_PATTERN.search(pre_history)
        if match:
            issue = match.group(1)
            year = int(match.group(4)) if match.group(4) else None
            return issue, year
        return None, None

    @staticmethod
    def _title_to_slug(title: str) -> str:
        """Generate a filesystem-safe slug from a Bulgarian title."""
        # Transliterate common patterns
        slug = title.lower().strip()
        # Remove non-alphanumeric (keeping Cyrillic)
        slug = re.sub(r"[^\w\s-]", "", slug)
        slug = re.sub(r"[\s_]+", "-", slug)
        slug = slug.strip("-")
        return slug[:80]  # cap length
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/fetcher/bg/test_metadata.py -v`
Expected: 10 passed

Note: The regex patterns for date and DV extraction may need tuning against real fixtures. If `test_extracts_effective_date` or `test_extracts_amendment_history` fail on the live fixture, inspect the actual HTML structure of `.PreHistory` and `.HistoryOfDocument` and adjust patterns.

**Step 5: Commit**

```bash
git add fetcher/bg/metadata.py tests/fetcher/bg/test_metadata.py
git commit -m "feat: metadata parser extracts 13 YAML fields from lex.bg HTML"
```

---

### Task 6: File Assembler

**Files:**
- Create: `fetcher/bg/assembler.py`
- Create: `tests/fetcher/bg/test_assembler.py`

**Step 1: Write the failing tests**

```python
# tests/fetcher/bg/test_assembler.py
import yaml
import pytest
from fetcher.bg.assembler import assemble_file, generate_slug


def test_assemble_produces_yaml_frontmatter():
    metadata = {
        "titulo": "Закон за нещо",
        "identificador": "123456",
        "pais": "bg",
        "rango": "закон",
        "fecha_publicacion": "2020-01-01",
        "ultima_actualizacion": "2020-01-01",
        "estado": "vigente",
        "fuente": "lex.bg",
        "dv_issue": "1",
        "dv_year": 2020,
        "effective_date": "2020-03-01",
        "category": "laws",
        "eli": "/eli/bg/закон/2020/zakon-za-neshto/con",
        "amendment_history": [],
    }
    body = "# ЗАКОН ЗА НЕЩО\n\n**Чл. 1.** Текст.\n"
    result = assemble_file(metadata, body)

    assert result.startswith("---\n")
    assert "\n---\n" in result
    # YAML should be parseable
    yaml_end = result.index("\n---\n", 4) + 5
    yaml_block = result[4:yaml_end - 5]
    parsed = yaml.safe_load(yaml_block)
    assert parsed["titulo"] == "Закон за нещо"
    assert parsed["pais"] == "bg"
    # Body follows
    assert "# ЗАКОН ЗА НЕЩО" in result[yaml_end:]


def test_generate_slug_from_title():
    slug = generate_slug("ЗАКОН ЗА ОБЩЕСТВЕНИТЕ ПОРЪЧКИ")
    assert slug  # non-empty
    assert "/" not in slug
    assert " " not in slug


def test_slug_is_deterministic():
    s1 = generate_slug("ЗАКОН ЗА ЕЛЕКТРОННОТО УПРАВЛЕНИЕ")
    s2 = generate_slug("ЗАКОН ЗА ЕЛЕКТРОННОТО УПРАВЛЕНИЕ")
    assert s1 == s2


def test_file_path_generation():
    metadata = {"category": "laws"}
    slug = "zakon-za-obshtestvenite-porachki"
    path = f"{metadata['category']}/{slug}.md"
    assert path == "laws/zakon-za-obshtestvenite-porachki.md"
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/fetcher/bg/test_assembler.py -v`
Expected: FAIL

**Step 3: Write minimal implementation**

```python
# fetcher/bg/assembler.py
"""File Assembler — combines Markdown body with YAML frontmatter."""

import re
import yaml


# Bulgarian Cyrillic transliteration table (simplified)
_TRANSLIT = str.maketrans({
    "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e",
    "ж": "zh", "з": "z", "и": "i", "й": "y", "к": "k", "л": "l",
    "м": "m", "н": "n", "о": "o", "п": "p", "р": "r", "с": "s",
    "т": "t", "у": "u", "ф": "f", "х": "h", "ц": "ts", "ч": "ch",
    "ш": "sh", "щ": "sht", "ъ": "a", "ь": "y", "ю": "yu", "я": "ya",
})


def generate_slug(title: str) -> str:
    """Generate a filesystem-safe slug from a Bulgarian title."""
    slug = title.lower().strip()
    # Character-by-character transliteration
    result = []
    for ch in slug:
        if ch in _TRANSLIT:
            result.append(_TRANSLIT[ch])
        elif ch.isascii() and ch.isalnum():
            result.append(ch)
        elif ch in (" ", "-", "_"):
            result.append("-")
        # skip other characters
    slug = "".join(result)
    slug = re.sub(r"-+", "-", slug)
    slug = slug.strip("-")
    return slug[:80]


def assemble_file(metadata: dict, body: str) -> str:
    """Combine YAML frontmatter and Markdown body into a complete file."""
    # Order fields: mandatory first, then extensions, then amendment_history
    ordered = {}
    mandatory = [
        "titulo", "identificador", "pais", "rango",
        "fecha_publicacion", "ultima_actualizacion", "estado", "fuente",
    ]
    extensions = ["dv_issue", "dv_year", "effective_date", "category", "eli"]

    for key in mandatory:
        if key in metadata:
            ordered[key] = metadata[key]
    for key in extensions:
        if key in metadata:
            ordered[key] = metadata[key]
    if "amendment_history" in metadata:
        ordered["amendment_history"] = metadata["amendment_history"]

    yaml_str = yaml.dump(
        ordered,
        default_flow_style=False,
        allow_unicode=True,
        sort_keys=False,
    )

    return f"---\n{yaml_str}---\n\n{body}"
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/fetcher/bg/test_assembler.py -v`
Expected: 4 passed

**Step 5: Commit**

```bash
git add fetcher/bg/assembler.py tests/fetcher/bg/test_assembler.py
git commit -m "feat: file assembler with YAML frontmatter and Cyrillic slug generation"
```

---

### Task 7: SQLite Catalog Index

**Files:**
- Create: `index/__init__.py`
- Create: `index/catalog.py`
- Create: `tests/index/__init__.py`
- Create: `tests/index/test_catalog.py`

**Step 1: Write the failing tests**

```python
# tests/index/test_catalog.py
import sqlite3
import pytest
from index.catalog import CatalogIndex


@pytest.fixture
def db():
    """In-memory SQLite database for testing."""
    idx = CatalogIndex(":memory:")
    idx.initialize()
    yield idx
    idx.close()


def test_initialize_creates_tables(db):
    tables = db.list_tables()
    assert "laws" in tables
    assert "law_versions" in tables


def test_insert_law(db):
    db.insert_law(
        law_id="zop",
        doc_id=2136735703,
        title="Закон за обществените поръчки",
        category="laws",
        commit_hash="abc123",
        effective_date="2016-04-15",
    )
    law = db.get_law("zop")
    assert law is not None
    assert law["doc_id"] == 2136735703
    assert law["title"] == "Закон за обществените поръчки"
    assert law["category"] == "laws"


def test_insert_creates_initial_version(db):
    db.insert_law(
        law_id="zop",
        doc_id=2136735703,
        title="Закон за обществените поръчки",
        category="laws",
        commit_hash="abc123",
        effective_date="2016-04-15",
    )
    versions = db.get_versions("zop")
    assert len(versions) == 1
    assert versions[0]["valid_from"] == "2016-04-15"
    assert versions[0]["valid_to"] is None  # current version
    assert versions[0]["commit_hash"] == "abc123"


def test_count_by_category(db):
    db.insert_law("zop", 1, "ЗОП", "laws", "a1", "2016-01-01")
    db.insert_law("zeu", 2, "ЗЕУ", "laws", "a2", "2017-01-01")
    db.insert_law("ppzop", 3, "ППЗОП", "implementing", "a3", "2016-01-01")
    counts = db.count_by_category()
    assert counts["laws"] == 2
    assert counts["implementing"] == 1
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/index/test_catalog.py -v`
Expected: FAIL

**Step 3: Write minimal implementation**

```python
# index/catalog.py
"""SQLite Catalog Index — per docs/data/schema-reference.md."""

import sqlite3
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS laws (
    law_id TEXT PRIMARY KEY,
    doc_id INTEGER,
    title TEXT NOT NULL,
    category TEXT NOT NULL,
    status TEXT DEFAULT 'vigente',
    current_commit TEXT
);

CREATE TABLE IF NOT EXISTS law_versions (
    id INTEGER PRIMARY KEY,
    law_id TEXT REFERENCES laws(law_id),
    valid_from DATE NOT NULL,
    valid_to DATE,
    commit_hash TEXT NOT NULL,
    dv_issue TEXT,
    dv_date DATE,
    amending_act TEXT
);

CREATE TABLE IF NOT EXISTS amendments (
    id INTEGER PRIMARY KEY,
    source_act TEXT NOT NULL,
    target_law TEXT REFERENCES laws(law_id),
    operation TEXT NOT NULL,
    affected_articles TEXT,
    dv_issue TEXT,
    dv_date DATE
);

CREATE TABLE IF NOT EXISTS provisions (
    id INTEGER PRIMARY KEY,
    law_id TEXT REFERENCES laws(law_id),
    article TEXT NOT NULL,
    paragraph TEXT,
    valid_from DATE NOT NULL,
    valid_to DATE,
    text_hash TEXT
);

CREATE INDEX IF NOT EXISTS idx_versions_date ON law_versions(law_id, valid_from);
CREATE INDEX IF NOT EXISTS idx_amendments_target ON amendments(target_law, dv_date);
CREATE INDEX IF NOT EXISTS idx_provisions_article ON provisions(law_id, article, valid_from);
"""


class CatalogIndex:
    def __init__(self, db_path: str = "catalog.db"):
        self._conn = sqlite3.connect(db_path)
        self._conn.row_factory = sqlite3.Row

    def initialize(self):
        self._conn.executescript(SCHEMA)

    def insert_law(self, law_id: str, doc_id: int, title: str,
                   category: str, commit_hash: str, effective_date: str):
        self._conn.execute(
            "INSERT INTO laws (law_id, doc_id, title, category, current_commit) VALUES (?, ?, ?, ?, ?)",
            (law_id, doc_id, title, category, commit_hash),
        )
        self._conn.execute(
            "INSERT INTO law_versions (law_id, valid_from, commit_hash) VALUES (?, ?, ?)",
            (law_id, effective_date, commit_hash),
        )
        self._conn.commit()

    def get_law(self, law_id: str) -> dict | None:
        row = self._conn.execute("SELECT * FROM laws WHERE law_id = ?", (law_id,)).fetchone()
        return dict(row) if row else None

    def get_versions(self, law_id: str) -> list[dict]:
        rows = self._conn.execute(
            "SELECT * FROM law_versions WHERE law_id = ? ORDER BY valid_from",
            (law_id,),
        ).fetchall()
        return [dict(r) for r in rows]

    def count_by_category(self) -> dict[str, int]:
        rows = self._conn.execute(
            "SELECT category, COUNT(*) as cnt FROM laws GROUP BY category"
        ).fetchall()
        return {r["category"]: r["cnt"] for r in rows}

    def list_tables(self) -> list[str]:
        rows = self._conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
        return [r["name"] for r in rows]

    def close(self):
        self._conn.close()
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/index/test_catalog.py -v`
Expected: 4 passed

**Step 5: Commit**

```bash
mkdir -p index tests/index
touch index/__init__.py tests/index/__init__.py
git add index/ tests/index/
git commit -m "feat: SQLite catalog index with schema from docs/data/schema-reference.md"
```

---

### Task 8: Bootstrap Runner

**Files:**
- Create: `bootstrap.py`
- Create: `tests/test_bootstrap.py`

**Step 1: Write the failing test**

```python
# tests/test_bootstrap.py
import pathlib
import tempfile
import sqlite3
import subprocess
import pytest

from fetcher.bg.client import LexBgClient
from fetcher.bg.discovery import CatalogCrawler
from fetcher.bg.text_parser import HtmlToMarkdown
from fetcher.bg.metadata import MetadataParser
from fetcher.bg.assembler import assemble_file, generate_slug
from index.catalog import CatalogIndex


FIXTURES = pathlib.Path(__file__).parent / "fixtures" / "html"


class FakeTransport:
    def get(self, doc_id: int) -> bytes:
        # Serve ZOP fixture for any doc_id
        return (FIXTURES / "zop.html").read_bytes()


def test_single_act_pipeline():
    """End-to-end: fetch → parse → convert → assemble → verify."""
    client = LexBgClient(transport=FakeTransport())
    parser = HtmlToMarkdown()
    metadata_parser = MetadataParser()

    # Fetch
    soup = client.fetch_soup(2136735703)

    # Parse
    body = parser.convert(soup)
    meta = metadata_parser.parse(soup, doc_id=2136735703, category="laws")

    # Assemble
    content = assemble_file(meta, body)

    # Verify structure
    assert content.startswith("---\n")
    assert "\n---\n" in content
    assert "titulo:" in content
    assert "identificador:" in content
    assert "# " in content  # has H1 title
    assert "**Чл." in content  # has articles

    # Verify slug
    slug = generate_slug(meta["titulo"])
    assert slug
    filepath = f"{meta['category']}/{slug}.md"
    assert filepath.startswith("laws/")
    assert filepath.endswith(".md")
```

**Step 2: Run test to verify it fails (if modules don't exist) or passes**

Run: `pytest tests/test_bootstrap.py -v`
Expected: PASS (all modules already exist)

**Step 3: Write the bootstrap runner**

```python
# bootstrap.py
"""Bootstrap Runner — orchestrates Phase 1a full corpus scrape."""

import argparse
import logging
import os
import subprocess
import time
from pathlib import Path

from fetcher.bg.client import LexBgClient, HttpTransport
from fetcher.bg.discovery import CatalogCrawler, CATEGORY_SLUG_TO_DIR
from fetcher.bg.text_parser import HtmlToMarkdown
from fetcher.bg.metadata import MetadataParser
from fetcher.bg.assembler import assemble_file, generate_slug
from index.catalog import CatalogIndex

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
log = logging.getLogger(__name__)


class TreeTransport:
    """HTTP transport for tree page requests with rate limiting."""

    def __init__(self):
        import requests
        self._session = requests.Session()
        self._session.headers["User-Agent"] = (
            "legalize-bg/0.1 (https://github.com/Ahelia-Consulting-EOOD/legalize-bg)"
        )
        self._last = 0.0

    def get_tree_page(self, url: str) -> bytes:
        elapsed = time.monotonic() - self._last
        if elapsed < 1.0:
            time.sleep(1.0 - elapsed)
        resp = self._session.get(url, timeout=30)
        self._last = time.monotonic()
        resp.raise_for_status()
        return resp.content


def bootstrap(output_dir: Path, db_path: str = "catalog.db", dry_run: bool = False):
    """Run the full bootstrap pipeline."""
    # Initialize components
    client = LexBgClient(transport=HttpTransport())
    crawler = CatalogCrawler()
    parser = HtmlToMarkdown()
    metadata_parser = MetadataParser()
    db = CatalogIndex(db_path)
    db.initialize()

    # Create corpus directories
    for dir_name in CATEGORY_SLUG_TO_DIR.values():
        (output_dir / dir_name).mkdir(parents=True, exist_ok=True)

    # Phase 1: Crawl catalog
    log.info("Crawling lex.bg catalog...")
    tree_transport = TreeTransport()
    catalog = crawler.crawl_all(tree_transport)
    log.info(f"Found {len(catalog)} acts across {len(CatalogCrawler.CATEGORIES)} categories")

    if dry_run:
        log.info("Dry run — stopping after catalog crawl")
        for cat, count in _count_by_cat(catalog).items():
            log.info(f"  {cat}: {count}")
        return catalog

    # Phase 2: Fetch, parse, commit each act
    errors = []
    for i, entry in enumerate(catalog, 1):
        doc_id = entry["doc_id"]
        name = entry["name"]
        tree_category = entry["category"]
        corpus_dir = CATEGORY_SLUG_TO_DIR.get(tree_category, tree_category)

        try:
            log.info(f"[{i}/{len(catalog)}] {name} (doc_id={doc_id})")

            # Fetch
            soup = client.fetch_soup(doc_id)

            # Parse
            body = parser.convert(soup)
            meta = metadata_parser.parse(soup, doc_id=doc_id, category=corpus_dir)

            # Assemble
            slug = generate_slug(meta["titulo"])
            filepath = output_dir / corpus_dir / f"{slug}.md"
            content = assemble_file(meta, body)

            # Write file
            filepath.write_text(content, encoding="utf-8")

            # Git commit
            _git_commit(
                filepath=filepath,
                title=meta["titulo"],
                doc_id=doc_id,
                pub_date=meta.get("fecha_publicacion", ""),
                cwd=output_dir,
            )

            # Index in SQLite
            commit_hash = _git_head(output_dir)
            db.insert_law(
                law_id=slug,
                doc_id=doc_id,
                title=meta["titulo"],
                category=corpus_dir,
                commit_hash=commit_hash,
                effective_date=meta.get("effective_date") or meta.get("fecha_publicacion", ""),
            )

        except Exception as e:
            log.error(f"FAILED: {name} (doc_id={doc_id}): {e}")
            errors.append({"doc_id": doc_id, "name": name, "error": str(e)})

    # Summary
    log.info(f"Bootstrap complete: {len(catalog) - len(errors)} succeeded, {len(errors)} failed")
    if errors:
        log.warning("Failed acts:")
        for err in errors:
            log.warning(f"  {err['name']}: {err['error']}")

    client.close()
    db.close()
    return catalog


def _git_commit(filepath: Path, title: str, doc_id: int, pub_date: str, cwd: Path):
    """Create a [bootstrap] commit for a single act."""
    subprocess.run(
        ["git", "add", str(filepath.relative_to(cwd))],
        cwd=cwd, check=True, capture_output=True,
    )
    msg = (
        f"[bootstrap] {title}\n\n"
        f"Source-Id: lexbg-{doc_id}\n"
        f"Source-Date: {pub_date}\n"
        f"Norm-Id: {doc_id}\n"
    )
    env = os.environ.copy()
    if pub_date:
        env["GIT_AUTHOR_DATE"] = pub_date
    subprocess.run(
        ["git", "commit", "-m", msg],
        cwd=cwd, check=True, capture_output=True, env=env,
    )


def _git_head(cwd: Path) -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=cwd, check=True, capture_output=True, text=True,
    )
    return result.stdout.strip()


def _count_by_cat(catalog: list[dict]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for entry in catalog:
        cat = entry["category"]
        counts[cat] = counts.get(cat, 0) + 1
    return counts


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Bootstrap Bulgarian legislation corpus")
    ap.add_argument("--output", type=Path, default=Path("."), help="Output directory")
    ap.add_argument("--db", default="catalog.db", help="SQLite database path")
    ap.add_argument("--dry-run", action="store_true", help="Only crawl catalog, don't fetch acts")
    args = ap.parse_args()
    bootstrap(args.output, args.db, args.dry_run)
```

**Step 4: Run all tests**

Run: `pytest -v`
Expected: All tests pass

**Step 5: Commit**

```bash
git add bootstrap.py tests/test_bootstrap.py
git commit -m "feat: bootstrap runner orchestrates full Phase 1a pipeline"
```

---

### Task 9: Capture Additional Fixtures

**Files:**
- Create: `tests/fixtures/html/zeu.html`
- Create: `tests/fixtures/html/npk.html`
- Create: `tests/fixtures/html/naredba-7-2004.html`
- Create: `tests/fixtures/html/ppzop.html`
- Create: `scripts/capture_fixtures.py`

**Step 1: Write fixture capture script**

```python
# scripts/capture_fixtures.py
"""Capture HTML fixtures from lex.bg for the test suite.

Per docs/testing/test-strategy.md, fixtures cover structural diversity.
Rate-limited to 1 req/sec.
"""

import time
import requests
from pathlib import Path

FIXTURES_DIR = Path(__file__).parent.parent / "tests" / "fixtures" / "html"

# Representative acts from test strategy
FIXTURES = {
    "zop.html": 2136735703,       # ЗОП — large law, frequent amendments
    "zeu.html": 2135555445,       # ЗЕУ — medium law, IT domain
    # npk and others — doc IDs will be discovered from catalog crawl
}

USER_AGENT = "legalize-bg/0.1 fixture-capture"


def capture():
    session = requests.Session()
    session.headers["User-Agent"] = USER_AGENT

    for filename, doc_id in FIXTURES.items():
        filepath = FIXTURES_DIR / filename
        if filepath.exists():
            print(f"  SKIP {filename} (already exists)")
            continue
        print(f"  FETCH {filename} (doc_id={doc_id})...")
        resp = session.get(f"https://lex.bg/laws/ldoc/{doc_id}", timeout=30)
        resp.raise_for_status()
        filepath.write_bytes(resp.content)
        print(f"  SAVED {len(resp.content)} bytes")
        time.sleep(1.0)

    print("Done.")


if __name__ == "__main__":
    capture()
```

**Step 2: Run the capture script**

```bash
python scripts/capture_fixtures.py
```

**Step 3: Run all tests against new fixtures**

Run: `pytest -v`
Expected: All tests pass (new fixtures are not yet referenced by tests — this validates existing tests still work)

**Step 4: Commit**

```bash
git add scripts/capture_fixtures.py tests/fixtures/html/
git commit -m "feat: fixture capture script and additional HTML fixtures"
```

---

### Task 10: Dry Run — Catalog Crawl

**Step 1: Run bootstrap in dry-run mode**

```bash
python bootstrap.py --dry-run
```

Expected output:
```
Crawling lex.bg catalog...
Found ~3574 acts across 5 categories
Dry run — stopping after catalog crawl
  laws: ~394
  code: ~24
  ords: ~2604
  regs: ~490
  reg_laws: ~61
```

**Step 2: Verify counts match expectations**

Cross-check against `docs/process/COVERAGE-FLOOR.md` expected counts.

**Step 3: Save catalog as reference**

```bash
python -c "
from bootstrap import bootstrap
from pathlib import Path
import json
catalog = bootstrap(Path('.'), dry_run=True)
with open('catalog.json', 'w') as f:
    json.dump(catalog, f, ensure_ascii=False, indent=2)
print(f'Saved {len(catalog)} entries to catalog.json')
"
```

**Step 4: Commit catalog snapshot**

```bash
git add catalog.json
git commit -m "chore: catalog snapshot from dry-run crawl"
```

---

### Task 11: Full Bootstrap Run

**Step 1: Ensure git repo is initialized and clean**

```bash
git status
```

**Step 2: Run full bootstrap**

```bash
python bootstrap.py --output . --db catalog.db
```

Expected: ~2 hours at 1 req/sec for ~3,574 acts. Monitor for errors.

**Step 3: Verify corpus integrity**

```bash
# Count files per category
find laws/ -name "*.md" | wc -l
find codes/ -name "*.md" | wc -l
find ordinances/ -name "*.md" | wc -l
find regulations/ -name "*.md" | wc -l
find implementing/ -name "*.md" | wc -l

# Verify git history
git log --oneline | head -20
git log --oneline | wc -l  # should be ~3,574

# Verify SQLite
sqlite3 catalog.db "SELECT category, COUNT(*) FROM laws GROUP BY category;"
```

**Step 4: Spot-check 10 random acts**

Per `docs/process/delivery-contract.md` Definition of Done for Phase 1a:

```bash
# Pick 10 random acts and compare against lex.bg
python -c "
import sqlite3, random
conn = sqlite3.connect('catalog.db')
laws = conn.execute('SELECT law_id, doc_id, title FROM laws').fetchall()
sample = random.sample(laws, min(10, len(laws)))
for law_id, doc_id, title in sample:
    print(f'{law_id}: {title} -> https://lex.bg/laws/ldoc/{doc_id}')
"
```

Manually verify each sampled act matches lex.bg content.

**Step 5: Update ACTIVE.md**

Update `docs/sync/ACTIVE.md` to reflect Phase 1a completion and Phase 1b as next.

---

## Post-Bootstrap Checklist

From `docs/process/delivery-contract.md` Definition of Done for Phase 1a:

- [ ] All ~3,574 acts scraped from lex.bg and converted to Markdown
- [ ] YAML frontmatter with all 13 fields populated for every act
- [ ] One `[bootstrap]` commit per act with correct Source-Id, Source-Date, Norm-Id
- [ ] SQLite catalog index built and queryable
- [ ] Spot-check: 10 randomly selected acts match lex.bg text exactly (after normalization)
- [ ] No cp1251 encoding artifacts in any file
- [ ] `docs/sync/ACTIVE.md` updated to reflect Phase 1a completion

---

## Dependencies and Ordering

```
Task 1 (setup)
  ├─> Task 2 (client) ─────────────────────┐
  ├─> Task 3 (discovery) ──────────────────│──┐
  ├─> Task 4 (text_parser) ────────────────│──│──┐
  ├─> Task 5 (metadata) ──────────────────│──│──│──┐
  │                                        │  │  │  │
  │   Task 6 (assembler) <────────────────│──│──┘──┘
  │      needs: text_parser, metadata      │  │
  │                                        │  │
  │   Task 7 (SQLite) ────────────────────│──│
  │      no deps on fetcher               │  │
  │                                        │  │
  └─> Task 8 (bootstrap runner) <─────────┘──┘
         needs: all of the above

Task 9 (fixtures) — can run any time after Task 2
Task 10 (dry run) — needs Task 8
Task 11 (full run) — needs Task 10
```

Tasks 2, 3, 4, 5, 7 can be implemented in parallel.
Task 6 depends on 4 and 5.
Task 8 depends on all of 2-7.
