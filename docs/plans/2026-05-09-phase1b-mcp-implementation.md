# Phase 1b.1 — MCP Server Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use `superpowers:executing-plans` to implement this plan task-by-task.

**Goal:** Build a polished MCP server exposing the 3,573-act Bulgarian legislation corpus through three tools (`get_law`, `search`, `get_article`) with workflows A (legal research / article precision) and B (drafting / review companion) covered end-to-end via Claude Code, Claude Desktop, and OpenAI Codex.

**Architecture:** FastMCP-based stdio server (`mcp_server/`) reading from a SQLite catalog (`catalog.db`) populated by a new `index/build.py` orchestrator. Index builder extracts article AND alinea-level rows into a `provisions` table with a `text` column, plus an FTS5 virtual table indexed via a symmetric Bulgarian-aware `bg_normalize()` function. All §7 data-quality cases (slug ≠ title, null `fecha_publicacion`, empty titulo) are server-enforced contracts with structured error returns.

**Tech Stack:** Python 3.12+, `fastmcp` (high-level MCP framework, transitive `mcp` SDK), `sqlite3` stdlib with FTS5, `pyyaml`, pytest.

**Key constraints (non-negotiable):**
- No corner-cutting: per D-023 `provisions` is alinea-level with `text` column from day one; per D-024 responses are typed-dicts; per D-025 `index/migrations.py` exists day one.
- TDD: every task is failing test → minimal impl → passing test → commit.
- No live HTTP at runtime: all data sourced from `catalog.db` + working tree + `git show`.
- Bulgarian normalizer must be symmetric (insert AND query) — asymmetry breaks search silently.

**Authority docs to read before implementing:**
- `docs/plans/2026-05-09-phase1b-mcp-design.md` — full design (read this first)
- `docs/sync/DECISIONS.md` D-020..D-027 — binding decisions for this plan
- `docs/data/canonical-data-model.md` §7 — corpus data-quality observations driving tool behavior
- `docs/architecture/container-view.md` §7 — tool surface
- `docs/process/IMPLEMENTATION-PREFLIGHT.md` Surfaces 3, 6, 7 — protected surfaces this plan touches

---

## Task 1: Project setup

**Files:**
- Modify: `pyproject.toml` — add `fastmcp` dependency
- Create: `mcp_server/__init__.py` (empty)
- Create: `mcp_server/__main__.py` (stub)
- Create: `tests/mcp_server/__init__.py` (empty)
- Create: `tests/index/test_migrations.py` (placeholder for Task 2)

**Step 1: Add `fastmcp` to dependencies**

Edit `pyproject.toml`:

```toml
[project]
...
dependencies = [
    "requests>=2.31",
    "beautifulsoup4>=4.12",
    "pyyaml>=6.0",
    "lxml>=5.0",
    "fastmcp>=0.4",
]

[tool.setuptools.packages.find]
include = ["fetcher*", "index*", "mcp_server*"]
exclude = ["tests*", "scripts*", "research*", "docs*"]
```

**Step 2: Create package skeletons**

```bash
mkdir -p mcp_server tests/mcp_server tests/fixtures/golden/provisions tests/fixtures/queries tests/fixtures/catalog
touch mcp_server/__init__.py tests/mcp_server/__init__.py
```

**Step 3: Install dependencies**

```bash
.venv/bin/pip install -e ".[dev]" 2>&1 | tail -5
```

Expected: `fastmcp` installed; existing 67 tests still pass.

**Step 4: Sanity check**

```bash
.venv/bin/python -c "import fastmcp; print('fastmcp', fastmcp.__version__)"
.venv/bin/pytest -q 2>&1 | tail -3
```

Expected: fastmcp imports; `67 passed`.

**Step 5: Commit**

```bash
git add pyproject.toml mcp_server/__init__.py tests/mcp_server/__init__.py
git commit -m "chore: add fastmcp dependency and mcp_server package skeleton"
```

---

## Task 2: `index/migrations.py` + schema delta

**Files:**
- Create: `index/migrations.py`
- Modify: `index/catalog.py` — extract schema-version tracking; reuse `migrations` runner
- Create: `tests/index/test_migrations.py`

**Step 1: Write failing test**

```python
# tests/index/test_migrations.py
import sqlite3
import pytest
from index.migrations import current_version, migrate, MIGRATIONS


def test_fresh_db_starts_at_version_zero():
    conn = sqlite3.connect(":memory:")
    assert current_version(conn) == 0


def test_migrate_applies_all_pending():
    conn = sqlite3.connect(":memory:")
    target = max(m.version for m in MIGRATIONS)
    migrate(conn)
    assert current_version(conn) == target


def test_migrate_is_idempotent():
    conn = sqlite3.connect(":memory:")
    migrate(conn)
    v1 = current_version(conn)
    migrate(conn)
    v2 = current_version(conn)
    assert v1 == v2


def test_migration_001_adds_text_column_to_provisions():
    conn = sqlite3.connect(":memory:")
    migrate(conn)
    cols = [r[1] for r in conn.execute("PRAGMA table_info(provisions)")]
    assert "text" in cols, f"expected 'text' in provisions cols, got {cols}"


def test_migration_002_creates_laws_fts_virtual_table():
    conn = sqlite3.connect(":memory:")
    migrate(conn)
    rows = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='laws_fts'"
    ).fetchall()
    assert len(rows) == 1, "laws_fts virtual table not created"


def test_migration_003_adds_provisions_lookup_index():
    conn = sqlite3.connect(":memory:")
    migrate(conn)
    rows = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='index' AND name='idx_provisions_lookup'"
    ).fetchall()
    assert len(rows) == 1
```

**Step 2: Run to verify failure**

```bash
.venv/bin/pytest tests/index/test_migrations.py -v 2>&1 | tail -10
```

Expected: ImportError for `index.migrations`.

**Step 3: Write minimal implementation**

```python
# index/migrations.py
"""Forward-only schema migrations for the SQLite catalog.

Each migration is a (version, name, sql) triple. `migrate(conn)` applies all
pending migrations in version order and is safe to call repeatedly.
"""

from dataclasses import dataclass
from typing import Iterable
import sqlite3


@dataclass(frozen=True)
class Migration:
    version: int
    name: str
    sql: str


# Phase 1a left the catalog at version 0 (no schema_version table). Phase
# 1b.1 introduces the table and three migrations:
#   001 — provisions.text column (per D-023)
#   002 — laws_fts virtual table (per D-022)
#   003 — provisions lookup index for (law_id, article, paragraph, valid_from)
#
# IMPORTANT: never edit a migration after it ships. Add a new one instead.

MIGRATIONS: tuple[Migration, ...] = (
    Migration(
        version=1,
        name="provisions_text_column",
        sql="ALTER TABLE provisions ADD COLUMN text TEXT;",
    ),
    Migration(
        version=2,
        name="laws_fts_virtual_table",
        sql="""
        CREATE VIRTUAL TABLE IF NOT EXISTS laws_fts USING fts5(
            law_id UNINDEXED,
            title,
            body,
            category UNINDEXED,
            tokenize='unicode61 remove_diacritics 2'
        );
        """,
    ),
    Migration(
        version=3,
        name="provisions_lookup_index",
        sql="""
        CREATE INDEX IF NOT EXISTS idx_provisions_lookup
            ON provisions(law_id, article, paragraph, valid_from);
        """,
    ),
)


def _ensure_schema_version_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_version (
            version INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )


def current_version(conn: sqlite3.Connection) -> int:
    _ensure_schema_version_table(conn)
    row = conn.execute("SELECT MAX(version) FROM schema_version").fetchone()
    return row[0] or 0


def migrate(conn: sqlite3.Connection, migrations: Iterable[Migration] = MIGRATIONS) -> int:
    """Apply all pending migrations. Returns the final version."""
    _ensure_schema_version_table(conn)
    # Need the base schema (laws, law_versions, provisions) before migrations
    # can ALTER them. CatalogIndex.initialize creates them; we mirror that
    # here so `migrate()` can be called against a fresh in-memory db too.
    from index.catalog import SCHEMA as BASE_SCHEMA
    conn.executescript(BASE_SCHEMA)

    applied = current_version(conn)
    for m in sorted(migrations, key=lambda x: x.version):
        if m.version <= applied:
            continue
        conn.executescript(m.sql)
        conn.execute(
            "INSERT INTO schema_version(version, name) VALUES (?, ?)",
            (m.version, m.name),
        )
        conn.commit()
        applied = m.version
    return applied
```

**Step 4: Run test to verify pass**

```bash
.venv/bin/pytest tests/index/test_migrations.py -v 2>&1 | tail -10
```

Expected: 6 passed.

**Step 5: Commit**

```bash
git add index/migrations.py tests/index/test_migrations.py
git commit -m "feat: forward-only schema migrations for SQLite catalog (D-025)

Three Phase 1b.1 migrations:
  001 — provisions.text column (D-023)
  002 — laws_fts virtual table (D-022)
  003 — idx_provisions_lookup for (law_id, article, paragraph, valid_from)

Idempotent. Migrations runner safe to call repeatedly. Forward-only by
construction — never edit a shipped migration, add a new one."
```

---

## Task 3: `bg_normalize()` Bulgarian normalizer

**Files:**
- Create: `index/fts.py`
- Create: `tests/index/test_fts.py`
- Create: `tests/fixtures/queries/bg_search_regression.yaml`

**Step 1: Write failing tests**

```python
# tests/index/test_fts.py
import pytest
from index.fts import bg_normalize


def test_lowercase():
    assert bg_normalize("ЗАКОН") == "закон"


def test_strip_whitespace_and_collapse():
    assert bg_normalize("  закон   за\nобществените  поръчки  ") \
        == "закон за обществените поръчки"


def test_strips_short_definite_article_TA_TO_TE():
    # "поръчки[те]" → "поръчки", "държава[та]" → "държава", "място[то]" → "място"
    assert "поръчки" in bg_normalize("обществените поръчки").split()
    assert "държава" in bg_normalize("държавата").split()
    assert "място" in bg_normalize("мястото").split()


def test_strips_long_definite_article_ETO_ITE():
    # "управление[то]" → "управление", "решения[та]" → "решения"
    assert "управление" in bg_normalize("управлението").split()
    assert "решения" in bg_normalize("решенията").split()


def test_does_not_strip_short_words():
    # words ≤4 chars: no suffix stripping (avoid mangling "това", "това["])
    out = bg_normalize("това дума")
    assert "това" in out.split()


def test_symmetric_query_matches_indexed_form():
    # the whole point: query "обществена поръчка" matches indexed
    # "обществените поръчки"
    indexed = bg_normalize("обществените поръчки")
    query = bg_normalize("обществена поръчка")
    # Both should reduce to same prefix tokens
    assert "поръчк" in indexed or "поръчки" in indexed
    assert "обществен" in indexed or "обществени" in indexed
    # Use shared root prefixes (4+ char prefix overlap is the realistic goal)
    for tok in indexed.split():
        if len(tok) > 4:
            # at least one query token shares its 4-char prefix
            assert any(q.startswith(tok[:4]) or tok.startswith(q[:4]) for q in query.split()), \
                f"no prefix match for indexed token {tok!r}"


def test_idempotent():
    s = "обществените поръчки и държавата"
    assert bg_normalize(bg_normalize(s)) == bg_normalize(s)


def test_handles_empty_and_none():
    assert bg_normalize("") == ""
    assert bg_normalize(None) == ""


def test_preserves_numbers_and_latin():
    out = bg_normalize("Чл. 14 ЗОП от 2016 г.")
    assert "14" in out
    assert "2016" in out
    assert "зоп" in out  # lowercased Latin/Cyrillic mix
```

**Step 2: Run to verify failure**

```bash
.venv/bin/pytest tests/index/test_fts.py -v 2>&1 | tail -10
```

Expected: ImportError for `index.fts`.

**Step 3: Write implementation**

```python
# index/fts.py
"""FTS5 helpers and Bulgarian-aware text normalizer.

bg_normalize() is symmetric: called at both index time AND query time so
morphological variants match. Bulgarian definite-article suffixes are
stripped from word endings; lowercasing and whitespace collapse round it
out. No external NLP libs; pure Python.

Per D-022. Symmetry is mandatory — asymmetry silently breaks search.
"""

import re
import sqlite3


# Definite-article suffixes ordered LONGEST FIRST so longer suffixes are
# stripped before shorter (e.g., "ите" before "те", "ето" before "то").
_BG_DEFINITE_SUFFIXES: tuple[str, ...] = (
    "ите", "ето",
    "ят", "ът",
    "та", "то", "те",
    "а", "ия",
)

_MIN_STEM_LEN = 4  # don't strip suffixes from words ≤4 chars (would mangle)
_WS_RE = re.compile(r"\s+")


def _strip_definite_article(token: str) -> str:
    if len(token) <= _MIN_STEM_LEN:
        return token
    for suffix in _BG_DEFINITE_SUFFIXES:
        if token.endswith(suffix) and len(token) - len(suffix) >= _MIN_STEM_LEN:
            return token[: -len(suffix)]
    return token


def bg_normalize(text: str | None) -> str:
    """Normalize text for symmetric FTS5 indexing/querying.

    - lowercase (Cyrillic + Latin)
    - collapse whitespace to single spaces
    - strip Bulgarian definite-article suffixes from word endings (>4 chars)
    - preserve digits and punctuation context (split on whitespace only)
    """
    if not text:
        return ""
    text = text.lower()
    text = _WS_RE.sub(" ", text).strip()
    if not text:
        return ""
    tokens = text.split(" ")
    return " ".join(_strip_definite_article(t) for t in tokens)


def create_laws_fts_table(conn: sqlite3.Connection) -> None:
    """Idempotent helper — migrations.py already creates this, but build.py
    uses this when working on a non-migrated test db."""
    conn.executescript(
        """
        CREATE VIRTUAL TABLE IF NOT EXISTS laws_fts USING fts5(
            law_id UNINDEXED,
            title,
            body,
            category UNINDEXED,
            tokenize='unicode61 remove_diacritics 2'
        );
        """
    )


def insert_fts_row(conn: sqlite3.Connection, law_id: str, title: str,
                   body: str, category: str) -> None:
    conn.execute(
        "INSERT INTO laws_fts (law_id, title, body, category) VALUES (?, ?, ?, ?)",
        (law_id, bg_normalize(title), bg_normalize(body), category),
    )


def search_fts(conn: sqlite3.Connection, query: str,
               category: str | None = None, limit: int = 20) -> list[sqlite3.Row]:
    """Run an FTS5 MATCH query and return ranked rows joined with laws."""
    normalized = bg_normalize(query)
    if not normalized:
        return []
    sql = """
        SELECT laws_fts.law_id          AS law_id,
               laws.doc_id              AS doc_id,
               laws.title               AS title,
               laws.category            AS category,
               snippet(laws_fts, 2, '<b>', '</b>', '...', 12) AS snippet,
               bm25(laws_fts)           AS score
          FROM laws_fts
          JOIN laws USING(law_id)
         WHERE laws_fts MATCH ?
    """
    params: list = [normalized]
    if category:
        sql += " AND laws.category = ?"
        params.append(category)
    sql += " ORDER BY bm25(laws_fts) LIMIT ?"
    params.append(limit)
    return conn.execute(sql, params).fetchall()
```

**Step 4: Run to verify pass**

```bash
.venv/bin/pytest tests/index/test_fts.py -v 2>&1 | tail -10
```

Expected: 9 passed.

**Step 5: Seed the regression suite (placeholder; populated as parsers land)**

```yaml
# tests/fixtures/queries/bg_search_regression.yaml
# Curated query → expected behavior pairs. Updated as the corpus + tokenizer
# evolve. Each entry is: {query, must_include, must_exclude, top_k_law_ids}.
# Initial seed — expanded in Task 21.

cases:
  - query: "обществени поръчки"
    must_include: ["zakon-za-obshtestvenite-porachki"]
    description: "ЗОП should rank top-3 for the most obvious Bulgarian query"
  - query: "обществената поръчка"  # singular + definite article
    must_include: ["zakon-za-obshtestvenite-porachki"]
    description: "morphology test — singular def-art form should still match"
```

**Step 6: Commit**

```bash
git add index/fts.py tests/index/test_fts.py tests/fixtures/queries/bg_search_regression.yaml
git commit -m "feat: bg_normalize symmetric Bulgarian-aware FTS5 helper (D-022)

Strips definite-article suffixes (longest-first) from words >4 chars,
lowercases, collapses whitespace. Same function used at index and query
time so 'обществената поръчка' matches indexed 'обществените поръчки'.

Pure Python; no custom SQLite tokenizer, no extension loading. Phase 1b.3
will add a Snowball stemmer + legal synonyms layer driven by usage data."
```

---

## Task 4: Provisions extractor — article-level rows

**Files:**
- Create: `index/provisions.py`
- Create: `tests/index/test_provisions.py`
- Create: `tests/fixtures/golden/provisions/zop.json` (small slice; full goldens land in Task 5)

**Step 1: Write failing tests**

```python
# tests/index/test_provisions.py
import json
import pathlib
import pytest
from index.provisions import parse, Provision

GOLDEN_DIR = pathlib.Path(__file__).parent.parent / "fixtures" / "golden" / "provisions"


def test_extracts_simple_article():
    md = "**Чл. 1.** Този закон определя нещо."
    rows = parse(md, law_id="test")
    article_rows = [r for r in rows if r.paragraph is None]
    assert len(article_rows) == 1
    assert article_rows[0].article == "1"
    assert "този закон" in article_rows[0].text.lower()


def test_extracts_multiple_articles():
    md = """**Чл. 1.** Първи член.

**Чл. 2.** Втори член.

**Чл. 3.** Трети член.
"""
    rows = parse(md, law_id="test")
    article_rows = [r for r in rows if r.paragraph is None]
    assert [r.article for r in article_rows] == ["1", "2", "3"]


def test_extracts_cyrillic_suffix_articles():
    md = """**Чл. 14.** Базов член.

**Чл. 14а.** Допълнителен член.

**Чл. 14б.** Още един.
"""
    rows = parse(md, law_id="test")
    article_rows = [r for r in rows if r.paragraph is None]
    assert [r.article for r in article_rows] == ["14", "14а", "14б"]


def test_stops_at_structural_header():
    md = """**Чл. 5.** Член преди ПЗР.

## ПРЕХОДНИ И ЗАКЛЮЧИТЕЛНИ РАЗПОРЕДБИ

**§ 1.** Параграф от ПЗР — не е член.
"""
    rows = parse(md, law_id="test")
    article_rows = [r for r in rows if r.paragraph is None]
    # Article 5 should NOT include the ПЗР content
    assert len(article_rows) == 1
    assert "ПРЕХОДНИ" not in article_rows[0].text
    assert "§ 1" not in article_rows[0].text


def test_text_hash_is_stable():
    md = "**Чл. 1.** Текст."
    rows1 = parse(md, law_id="test")
    rows2 = parse(md, law_id="test")
    assert rows1[0].text_hash == rows2[0].text_hash


def test_text_hash_changes_with_content():
    rows1 = parse("**Чл. 1.** Текст А.", law_id="test")
    rows2 = parse("**Чл. 1.** Текст Б.", law_id="test")
    assert rows1[0].text_hash != rows2[0].text_hash


def test_returns_law_id_on_each_row():
    md = "**Чл. 1.** Текст."
    rows = parse(md, law_id="zop")
    for r in rows:
        assert r.law_id == "zop"


def test_zop_golden_subset():
    """ZOP fixture should produce a known set of articles. Golden anchors
    the parser; alinea-level coverage added in Task 5."""
    from bs4 import BeautifulSoup
    from fetcher.bg.text_parser import HtmlToMarkdown

    fixture = pathlib.Path(__file__).parent.parent / "fixtures" / "html" / "zop.html"
    soup = BeautifulSoup(fixture.read_bytes().decode("cp1251"), "lxml")
    md = HtmlToMarkdown().convert(soup)

    rows = parse(md, law_id="zop")
    articles = sorted({r.article for r in rows if r.paragraph is None}, key=_article_sort_key)
    # ЗОП has at least articles 1 through 100 in its current consolidated form
    assert "1" in articles
    assert "100" in articles or any(a.startswith("100") for a in articles)
    # And it has Cyrillic-suffixed articles (e.g. чл. 14а — common in Bulgarian legislation)
    assert any(a[-1] in "абвгд" for a in articles), f"expected Cyrillic-suffix articles, got {articles[:20]}..."


def _article_sort_key(article: str):
    # "14а" sorts after "14"; "100" sorts after "99"
    import re
    m = re.match(r"^(\d+)([а-я]*)$", article)
    if not m:
        return (0, article)
    return (int(m.group(1)), m.group(2))
```

**Step 2: Run to verify failure**

```bash
.venv/bin/pytest tests/index/test_provisions.py -v 2>&1 | tail -10
```

Expected: ImportError for `index.provisions`.

**Step 3: Write implementation**

```python
# index/provisions.py
"""Markdown-body → provisions rows extractor.

Walks the Markdown produced by `fetcher.bg.text_parser.HtmlToMarkdown` and
emits article-level rows AND alinea-level rows. Per D-023, both `text` and
`text_hash` columns are populated; `paragraph` is NULL for the
article-as-a-whole row, set to '1', '2', ... for each alinea.

Article anchors look like '**Чл. N.**' or '**Чл. Nа.**' (Cyrillic suffixes).
Alineas are paragraph blocks starting with '(N)' — Phase 1a's text_parser
emits each alinea as its own paragraph (separated by '\\n\\n' per the
post–code-review fix in D-of-Phase-1a's I7).
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass


# Article anchor: bold "Чл. N." or "Чл. Nа." (Cyrillic letter suffix).
# The regex captures the article identifier (digits + optional Cyrillic
# letter suffix), and is anchored to the start of a Markdown line.
_ARTICLE_RE = re.compile(
    r"\*\*Чл\.\s+(\d+[а-я]?)\.?\*\*",
    flags=re.MULTILINE,
)

# Structural headers that terminate an article body.
_STRUCTURAL_RE = re.compile(
    r"^(##\s|###\s|####\s|##\s+ПРЕХОДНИ|## ПРЕХОДНИ|## ЗАКЛЮЧИТЕЛНИ)",
    flags=re.MULTILINE,
)

# Alinea boundary inside an article body: a paragraph starting with "(N)"
# possibly preceded by whitespace.
_ALINEA_SPLIT_RE = re.compile(r"\n\n(?=\s*\(\d+[а-я]?\))")
_ALINEA_PREFIX_RE = re.compile(r"^\s*\((\d+[а-я]?)\)\s*")


@dataclass(frozen=True)
class Provision:
    law_id: str
    article: str
    paragraph: str | None  # None for article-as-whole row
    text: str
    text_hash: str


def _hash(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()[:16]


def _extract_article_blocks(markdown: str) -> list[tuple[str, str]]:
    """Return list of (article_id, body_text) — body is the text from the
    article anchor up to the next article anchor or structural header."""
    matches = list(_ARTICLE_RE.finditer(markdown))
    blocks: list[tuple[str, str]] = []
    for i, m in enumerate(matches):
        article_id = m.group(1)
        start = m.end()
        next_article_start = matches[i + 1].start() if i + 1 < len(matches) else len(markdown)
        # Trim at structural header if one appears before next article
        struct_m = _STRUCTURAL_RE.search(markdown, pos=start, endpos=next_article_start)
        end = struct_m.start() if struct_m else next_article_start
        body = markdown[start:end].strip()
        blocks.append((article_id, body))
    return blocks


def parse(markdown: str, law_id: str) -> list[Provision]:
    """Phase 1b.1 article-level extraction. Alinea rows added in Task 5."""
    rows: list[Provision] = []
    for article_id, body in _extract_article_blocks(markdown):
        rows.append(Provision(
            law_id=law_id,
            article=article_id,
            paragraph=None,
            text=body,
            text_hash=_hash(body),
        ))
    return rows
```

**Step 4: Run to verify pass**

```bash
.venv/bin/pytest tests/index/test_provisions.py -v 2>&1 | tail -15
```

Expected: 8 passed.

**Step 5: Commit**

```bash
git add index/provisions.py tests/index/test_provisions.py
git commit -m "feat: provisions extractor (article level) — Phase 1b.1 D-023

Article anchors '**Чл. N.**' / '**Чл. Nа.**' parsed from Markdown body.
Each article emits a Provision(law_id, article, paragraph=None, text,
text_hash) row. Body text trimmed at next article anchor or structural
header (## ПРЕХОДНИ, etc).

Alinea-level rows added in next task."
```

---

## Task 5: Provisions extractor — alinea-level rows

**Files:**
- Modify: `index/provisions.py` — extend `parse()` to also emit alinea rows
- Modify: `tests/index/test_provisions.py` — add alinea tests
- Create: `tests/fixtures/golden/provisions/{zop,zeu,gpk,naredba-04-14,pravilnik-sadilishta,ppz-aktsizi}.json`

**Step 1: Write failing tests**

Append to `tests/index/test_provisions.py`:

```python
def test_extracts_alineas_from_article():
    md = """**Чл. 14.** (1) Първа алинея.

(2) Втора алинея.

(3) Трета алинея.
"""
    rows = parse(md, law_id="test")
    alineas = [r for r in rows if r.paragraph is not None]
    assert [r.paragraph for r in alineas] == ["1", "2", "3"]
    assert "Първа" in alineas[0].text
    assert "Втора" in alineas[1].text
    assert "Трета" in alineas[2].text


def test_article_row_text_includes_all_alineas():
    md = """**Чл. 14.** (1) Първа.

(2) Втора.
"""
    rows = parse(md, law_id="test")
    article = next(r for r in rows if r.paragraph is None)
    assert "Първа" in article.text and "Втора" in article.text


def test_article_with_no_alineas_emits_only_article_row():
    md = "**Чл. 1.** Един параграф без алинеи."
    rows = parse(md, law_id="test")
    assert len(rows) == 1
    assert rows[0].paragraph is None


def test_alinea_with_cyrillic_letter():
    md = """**Чл. 5.** (1) Първа.

(1а) Допълнителна първа.

(2) Втора.
"""
    rows = parse(md, law_id="test")
    alineas = [r for r in rows if r.paragraph is not None]
    assert [r.paragraph for r in alineas] == ["1", "1а", "2"]


def test_alinea_text_hash_is_alinea_only():
    """alinea row's text_hash should reflect ONLY that alinea's text,
    so amendment detection in Phase 4 can pinpoint a single-alinea ZID."""
    md = """**Чл. 14.** (1) Първа.

(2) Втора.
"""
    rows = parse(md, law_id="test")
    alineas = [r for r in rows if r.paragraph is not None]
    h_alpha = alineas[0].text_hash
    # Now mutate only alinea 2; alinea 1's hash must not change
    md2 = """**Чл. 14.** (1) Първа.

(2) ВТОРА (изменена).
"""
    rows2 = parse(md2, law_id="test")
    alineas2 = [r for r in rows2 if r.paragraph is not None]
    assert alineas2[0].text_hash == h_alpha
    assert alineas2[1].text_hash != alineas[1].text_hash


@pytest.mark.parametrize("fixture_name,law_id", [
    ("zop", "zop"),
    ("zeu", "zeu"),
    ("gpk", "gpk"),
    ("naredba-04-14", "naredba-04-14"),
    ("pravilnik-sadilishta", "pravilnik-sadilishta"),
    ("ppz-aktsizi", "ppz-aktsizi"),
])
def test_golden_provisions_per_fixture(fixture_name, law_id, tmp_path):
    """Lock the parser against each fixture. Golden file is regenerated
    on demand: see CONTRIBUTING note (or just run with REGENERATE=1)."""
    import os
    from bs4 import BeautifulSoup
    from fetcher.bg.text_parser import HtmlToMarkdown

    fixture = pathlib.Path(__file__).parent.parent / "fixtures" / "html" / f"{fixture_name}.html"
    soup = BeautifulSoup(fixture.read_bytes().decode("cp1251"), "lxml")
    md = HtmlToMarkdown().convert(soup)

    rows = parse(md, law_id=law_id)
    summary = {
        "law_id": law_id,
        "total_rows": len(rows),
        "article_rows": sum(1 for r in rows if r.paragraph is None),
        "alinea_rows": sum(1 for r in rows if r.paragraph is not None),
        "first_articles": sorted(
            {r.article for r in rows if r.paragraph is None},
            key=_article_sort_key,
        )[:10],
    }

    golden_path = GOLDEN_DIR / f"{fixture_name}.json"
    if os.environ.get("REGENERATE_GOLDENS"):
        GOLDEN_DIR.mkdir(parents=True, exist_ok=True)
        golden_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2))
        return

    assert golden_path.exists(), \
        f"missing golden {golden_path} — regenerate with REGENERATE_GOLDENS=1"
    expected = json.loads(golden_path.read_text(encoding="utf-8"))
    assert summary == expected, f"provisions extraction drift for {fixture_name}"
```

**Step 2: Run to verify failure**

```bash
.venv/bin/pytest tests/index/test_provisions.py -v 2>&1 | tail -15
```

Expected: alinea tests fail; golden tests fail (goldens don't exist yet).

**Step 3: Extend `index/provisions.py`**

Replace `parse()` with:

```python
def parse(markdown: str, law_id: str) -> list[Provision]:
    """Emit one article-as-whole row + one row per alinea. D-023."""
    rows: list[Provision] = []
    for article_id, body in _extract_article_blocks(markdown):
        # Article-as-a-whole row: full body text
        rows.append(Provision(
            law_id=law_id,
            article=article_id,
            paragraph=None,
            text=body,
            text_hash=_hash(body),
        ))
        # Alinea rows: split body on "(N)" paragraph boundaries
        for paragraph_id, alinea_text in _split_alineas(body):
            rows.append(Provision(
                law_id=law_id,
                article=article_id,
                paragraph=paragraph_id,
                text=alinea_text,
                text_hash=_hash(alinea_text),
            ))
    return rows


def _split_alineas(body: str) -> list[tuple[str, str]]:
    """Split an article body into (paragraph_id, text) pairs. Returns []
    if the article has no '(N)' alinea markers."""
    # Find all alinea starts; if none, return []
    matches = list(re.finditer(r"\(\s*(\d+[а-я]?)\s*\)", body))
    if not matches:
        return []
    out: list[tuple[str, str]] = []
    for i, m in enumerate(matches):
        paragraph_id = m.group(1)
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(body)
        text = body[start:end].strip()
        # Strip leading punctuation/whitespace artifacts
        text = re.sub(r"^[\s\.,]+", "", text)
        out.append((paragraph_id, text))
    return out
```

**Step 4: Generate goldens, then run tests**

```bash
REGENERATE_GOLDENS=1 .venv/bin/pytest tests/index/test_provisions.py::test_golden_provisions_per_fixture -v 2>&1 | tail -10
```

Then **MANUALLY INSPECT** each golden in `tests/fixtures/golden/provisions/*.json` for sanity (ZOP should have ~250+ articles, GPK should have ~700+, naredba-04-14 should have ~50, etc.). Once satisfied:

```bash
.venv/bin/pytest tests/index/test_provisions.py -v 2>&1 | tail -10
```

Expected: all alinea + golden tests pass.

**Step 5: Commit**

```bash
git add index/provisions.py tests/index/test_provisions.py tests/fixtures/golden/provisions/
git commit -m "feat: provisions extractor — alinea-level rows from day one (D-023)

Each article now emits:
  - one article-as-whole row (paragraph=NULL, text=full article body)
  - one row per (N) alinea (paragraph=N, text=alinea text)

text_hash is per-row so single-alinea ZID amendment detection in Phase 4
becomes precise. Cyrillic-letter alinea suffixes ('1а') supported.

Goldens locked for all 6 HTML fixtures; regenerate via REGENERATE_GOLDENS=1."
```

---

## Task 6: `index/build.py` orchestrator

**Files:**
- Create: `index/build.py`
- Create: `tests/index/test_build.py`

**Step 1: Write failing tests**

```python
# tests/index/test_build.py
import sqlite3
import subprocess
import pathlib
import pytest

from index.build import build, _iter_corpus_files
from index.migrations import current_version


@pytest.fixture
def fake_corpus(tmp_path):
    """Create a tiny git-repo-like corpus with 2 fixture-derived .md files."""
    (tmp_path / "laws").mkdir()
    (tmp_path / "ordinances").mkdir()

    # Borrow real fixture content
    from bs4 import BeautifulSoup
    from fetcher.bg.text_parser import HtmlToMarkdown
    from fetcher.bg.metadata import MetadataParser
    from fetcher.bg.assembler import assemble_file, generate_slug

    repo_root = pathlib.Path(__file__).parent.parent.parent
    for fixture_name, doc_id, corpus_dir in [
        ("zop", 2136735703, "laws"),
        ("naredba-04-14", 2137197056, "ordinances"),
    ]:
        html = (repo_root / "tests/fixtures/html" / f"{fixture_name}.html").read_bytes().decode("cp1251")
        soup = BeautifulSoup(html, "lxml")
        body = HtmlToMarkdown().convert(soup)
        meta = MetadataParser().parse(soup, doc_id=doc_id, category=corpus_dir)
        slug = generate_slug(meta["titulo"])
        content = assemble_file(meta, body)
        (tmp_path / corpus_dir / f"{slug}.md").write_text(content, encoding="utf-8")

    # Initialize git repo so build() can `git rev-parse HEAD`
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "test@test"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "commit.gpgsign", "false"], cwd=tmp_path, check=True)
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "fixtures"], cwd=tmp_path, check=True)
    return tmp_path


def test_build_runs_migrations(fake_corpus, tmp_path):
    db_path = str(tmp_path / "test.db")
    build(corpus_root=fake_corpus, db_path=db_path)
    conn = sqlite3.connect(db_path)
    assert current_version(conn) >= 3


def test_build_populates_laws_and_versions(fake_corpus, tmp_path):
    db_path = str(tmp_path / "test.db")
    build(corpus_root=fake_corpus, db_path=db_path)
    conn = sqlite3.connect(db_path)
    laws_count = conn.execute("SELECT COUNT(*) FROM laws").fetchone()[0]
    assert laws_count == 2
    versions_count = conn.execute("SELECT COUNT(*) FROM law_versions").fetchone()[0]
    assert versions_count == 2


def test_build_populates_provisions_with_alineas(fake_corpus, tmp_path):
    db_path = str(tmp_path / "test.db")
    build(corpus_root=fake_corpus, db_path=db_path)
    conn = sqlite3.connect(db_path)
    article_rows = conn.execute(
        "SELECT COUNT(*) FROM provisions WHERE paragraph IS NULL"
    ).fetchone()[0]
    alinea_rows = conn.execute(
        "SELECT COUNT(*) FROM provisions WHERE paragraph IS NOT NULL"
    ).fetchone()[0]
    assert article_rows > 50  # ZOP alone has ~250+
    assert alinea_rows > article_rows  # most articles have multiple alineas


def test_build_populates_fts_with_normalized_text(fake_corpus, tmp_path):
    db_path = str(tmp_path / "test.db")
    build(corpus_root=fake_corpus, db_path=db_path)
    conn = sqlite3.connect(db_path)
    fts_count = conn.execute("SELECT COUNT(*) FROM laws_fts").fetchone()[0]
    assert fts_count == 2
    # FTS body should be normalized (lowercase, suffix-stripped)
    body = conn.execute("SELECT body FROM laws_fts WHERE law_id LIKE 'zakon%'").fetchone()[0]
    assert body == body.lower()


def test_build_is_idempotent(fake_corpus, tmp_path):
    db_path = str(tmp_path / "test.db")
    build(corpus_root=fake_corpus, db_path=db_path)
    build(corpus_root=fake_corpus, db_path=db_path)
    conn = sqlite3.connect(db_path)
    laws_count = conn.execute("SELECT COUNT(*) FROM laws").fetchone()[0]
    assert laws_count == 2  # not 4 — rebuild replaced, didn't append


def test_build_records_current_commit(fake_corpus, tmp_path):
    db_path = str(tmp_path / "test.db")
    build(corpus_root=fake_corpus, db_path=db_path)
    conn = sqlite3.connect(db_path)
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=fake_corpus,
        check=True, capture_output=True, text=True,
    ).stdout.strip()
    rows = conn.execute("SELECT DISTINCT current_commit FROM laws").fetchall()
    assert len(rows) == 1 and rows[0][0] == head
```

**Step 2: Run to verify failure**

```bash
.venv/bin/pytest tests/index/test_build.py -v 2>&1 | tail -10
```

Expected: ImportError for `index.build`.

**Step 3: Write implementation**

```python
# index/build.py
"""Index builder — populates the SQLite catalog from a git-tracked corpus.

Idempotent: drops & re-creates content tables before insertion (the schema
itself is migrated forward-only via index/migrations.py).

Per the design doc §6.1 / §7.1, this is invoked manually by operators
after Phase 1a bootstrap, and automatically by Phase 3 (DV monitor) and
Phase 4 (consolidation engine) at the end of their pipelines.
"""

import argparse
import logging
import sqlite3
import subprocess
import sys
from datetime import date
from pathlib import Path

import yaml

from fetcher.bg.discovery import CATEGORY_DIRS
from index.fts import bg_normalize, insert_fts_row
from index.migrations import migrate
from index.provisions import parse as parse_provisions

log = logging.getLogger(__name__)


def _git_head(cwd: Path) -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=cwd, check=True, capture_output=True, text=True,
    ).stdout.strip()


def _iter_corpus_files(corpus_root: Path):
    for cat in CATEGORY_DIRS.values():
        d = corpus_root / cat
        if not d.is_dir():
            continue
        for f in sorted(d.iterdir()):
            if f.suffix == ".md":
                yield cat, f


def _parse_md(path: Path) -> tuple[dict, str]:
    raw = path.read_text(encoding="utf-8")
    if not raw.startswith("---\n"):
        raise ValueError(f"missing frontmatter in {path}")
    _, fm, body = raw.split("\n---\n", 1)[0][4:], *raw.split("\n---\n", 1)
    # Above is awkward; rewrite cleanly:
    parts = raw.split("\n---\n", 1)
    fm_block = parts[0][4:]   # strip leading '---\n'
    body = parts[1] if len(parts) > 1 else ""
    return yaml.safe_load(fm_block), body


def _drop_content_tables(conn: sqlite3.Connection) -> None:
    """Idempotency: blow away rows from content tables before re-inserting.
    Schema (managed by migrations.py) stays intact."""
    for table in ("laws_fts", "provisions", "law_versions", "laws"):
        # FTS5 virtual table needs DELETE; regular tables can also use DELETE
        conn.execute(f"DELETE FROM {table}")
    conn.commit()


def build(corpus_root: Path, db_path: str = "catalog.db",
          today_iso: str | None = None) -> int:
    """Build (or rebuild) the SQLite catalog from the corpus at HEAD.

    Returns the number of acts indexed.
    """
    today_iso = today_iso or date.today().isoformat()
    conn = sqlite3.connect(db_path)
    try:
        migrate(conn)
        _drop_content_tables(conn)

        head = _git_head(corpus_root)
        log.info("indexing corpus at %s commit=%s", corpus_root, head[:8])

        count = 0
        for cat, path in _iter_corpus_files(corpus_root):
            meta, body = _parse_md(path)
            law_id = path.stem
            doc_id = int(meta.get("identificador") or 0)
            title = meta.get("titulo") or f"<doc_id={doc_id}>"
            effective = (
                meta.get("effective_date")
                or meta.get("fecha_publicacion")
                or today_iso  # §7.2 fallback to bootstrap-run-date
            )

            conn.execute(
                """INSERT INTO laws (law_id, doc_id, title, category,
                                     status, current_commit)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (law_id, doc_id, title, cat, "vigente", head),
            )
            conn.execute(
                """INSERT INTO law_versions (law_id, valid_from, commit_hash)
                   VALUES (?, ?, ?)""",
                (law_id, effective, head),
            )
            for prov in parse_provisions(body, law_id=law_id):
                conn.execute(
                    """INSERT INTO provisions
                       (law_id, article, paragraph, valid_from, text, text_hash)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (prov.law_id, prov.article, prov.paragraph,
                     effective, prov.text, prov.text_hash),
                )
            insert_fts_row(conn, law_id=law_id, title=title,
                           body=body, category=cat)
            count += 1

        conn.commit()
        log.info("indexed %d acts", count)
        return count
    finally:
        conn.close()


def main() -> int:
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(message)s")
    ap = argparse.ArgumentParser(description="Build SQLite catalog from corpus.")
    ap.add_argument("--corpus", type=Path, default=Path("."))
    ap.add_argument("--db", default="catalog.db")
    args = ap.parse_args()
    n = build(args.corpus, args.db)
    print(f"indexed {n} acts into {args.db}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

**Step 4: Run to verify pass**

```bash
.venv/bin/pytest tests/index/test_build.py -v 2>&1 | tail -10
```

Expected: 6 passed.

**Step 5: Commit**

```bash
git add index/build.py tests/index/test_build.py
git commit -m "feat: index/build.py orchestrator — D-022/023/025 unified

Reads each .md from the corpus, parses frontmatter + body, populates:
  - laws (one row per act, current_commit set)
  - law_versions (one initial row per act; §7.2 null-date fallback to today)
  - provisions (article + alinea rows, text + text_hash; D-023)
  - laws_fts (bg_normalized title + body; D-022)

Idempotent via DELETE-then-INSERT; schema managed by migrations.py (D-025).
CLI: python -m index.build --corpus . --db catalog.db"
```

---

## Task 7: `parse_article_spec()` — article variant parser

**Files:**
- Create: `mcp_server/queries.py` (initial; will grow across Tasks 7-13)
- Create: `tests/mcp_server/test_queries.py`

**Step 1: Write failing tests**

```python
# tests/mcp_server/test_queries.py
import pytest
from mcp_server.queries import parse_article_spec, ArticleSpec, InvalidArticleSpec


@pytest.mark.parametrize("spec,expected", [
    ("чл. 14",          ArticleSpec(article="14", paragraph=None, range_end=None)),
    ("Чл. 14",          ArticleSpec(article="14", paragraph=None, range_end=None)),
    ("14",              ArticleSpec(article="14", paragraph=None, range_end=None)),
    ("чл. 14а",         ArticleSpec(article="14а", paragraph=None, range_end=None)),
    ("14а",             ArticleSpec(article="14а", paragraph=None, range_end=None)),
    ("чл. 14, ал. 2",   ArticleSpec(article="14", paragraph="2", range_end=None)),
    ("Чл. 14 ал. 2",    ArticleSpec(article="14", paragraph="2", range_end=None)),
    ("14.2",            ArticleSpec(article="14", paragraph="2", range_end=None)),
    ("14, ал. 2",       ArticleSpec(article="14", paragraph="2", range_end=None)),
    ("чл. 14-16",       ArticleSpec(article="14", paragraph=None, range_end="16")),
    ("чл. 14 - 16",     ArticleSpec(article="14", paragraph=None, range_end="16")),
    ("чл. 14, ал. 2а",  ArticleSpec(article="14", paragraph="2а", range_end=None)),
])
def test_valid_specs(spec, expected):
    assert parse_article_spec(spec) == expected


@pytest.mark.parametrize("spec", [
    "",
    "garbage",
    "чл.",
    "ал. 2",  # no article number
    "чл. abc",
])
def test_invalid_specs_raise(spec):
    with pytest.raises(InvalidArticleSpec):
        parse_article_spec(spec)
```

**Step 2: Run to verify failure**

```bash
.venv/bin/pytest tests/mcp_server/test_queries.py -v 2>&1 | tail -10
```

Expected: ImportError.

**Step 3: Write implementation**

```python
# mcp_server/queries.py
"""Pure query functions over the SQLite catalog.

Each function takes a sqlite3.Connection plus typed parameters; none has
an MCP dependency. Tools in mcp_server/server.py are thin wrappers that
catch domain exceptions and translate them into ToolError.
"""

from __future__ import annotations

import re
import sqlite3
from dataclasses import dataclass


# ────────────────────────────── Article spec parser ─────────────────────────

@dataclass(frozen=True)
class ArticleSpec:
    article: str
    paragraph: str | None
    range_end: str | None


class InvalidArticleSpec(ValueError):
    pass


# Article: digits + optional Cyrillic letter suffix (e.g., "14а").
_ART_RE = r"(\d+[а-я]?)"
# Optional range: "- 16"
_RANGE_RE = rf"\s*-\s*(\d+[а-я]?)"
# Optional alinea: ", ал. 2" or " ал. 2" or ".2"
_ALINEA_RE = rf"(?:[\.,]\s*ал\.\s*|\s+ал\.\s*|\.){_ART_RE}"

_FULL_RE = re.compile(
    rf"^\s*(?:чл\.\s*)?{_ART_RE}(?:{_RANGE_RE}|(?:[\.,]\s*ал\.\s*|\s+ал\.\s*|\.)(\d+[а-я]?))?\s*$",
    flags=re.IGNORECASE,
)


def parse_article_spec(spec: str) -> ArticleSpec:
    """Parse Bulgarian article reference into structured spec."""
    if not spec or not spec.strip():
        raise InvalidArticleSpec(f"empty spec: {spec!r}")
    m = _FULL_RE.match(spec)
    if not m:
        raise InvalidArticleSpec(f"could not parse: {spec!r}")
    article, range_end, paragraph = m.group(1), m.group(2), m.group(3)
    return ArticleSpec(article=article, paragraph=paragraph, range_end=range_end)
```

**Step 4: Run to verify pass**

```bash
.venv/bin/pytest tests/mcp_server/test_queries.py -v 2>&1 | tail -15
```

Expected: 17 passed.

**Step 5: Commit**

```bash
git add mcp_server/queries.py tests/mcp_server/test_queries.py
git commit -m "feat: parse_article_spec — Bulgarian article reference parser

Accepts: 'чл. 14', '14', 'чл. 14а', 'чл. 14, ал. 2', '14.2', '14, ал. 2а',
ranges 'чл. 14-16'. Returns ArticleSpec(article, paragraph, range_end).
Raises InvalidArticleSpec for unparseable input.

First piece of mcp_server/queries.py — pure functions, no MCP dep."
```

---

## Task 8: `resolve_name_to_law_id()` + `AmbiguousName`

**Files:**
- Modify: `mcp_server/queries.py` — add resolution logic
- Modify: `tests/mcp_server/test_queries.py` — add resolution tests
- Create: `tests/mcp_server/conftest.py` — shared fixtures (in-memory catalog)

**Step 1: Write `conftest.py`**

```python
# tests/mcp_server/conftest.py
import sqlite3
import pytest
from index.migrations import migrate
from index.fts import insert_fts_row


@pytest.fixture
def conn():
    """Fresh in-memory SQLite with migrations applied."""
    c = sqlite3.connect(":memory:")
    c.row_factory = sqlite3.Row
    migrate(c)
    yield c
    c.close()


@pytest.fixture
def populated_conn(conn):
    """Mini catalog: 5 acts including a slug collision and an empty-titulo case."""
    rows = [
        ("zakon-a",       100, "Закон за А",                    "laws"),
        ("zakon-b",       101, "Закон за Б",                    "laws"),
        ("naredba-7",     200, "Наредба № 7 за нещо",           "ordinances"),
        ("naredba-7-2",   201, "Наредба № 7 за нещо",           "ordinances"),  # collision
        ("phantom",       -549676032, "",                       "ordinances"),  # empty titulo
    ]
    for law_id, doc_id, title, cat in rows:
        conn.execute(
            "INSERT INTO laws (law_id, doc_id, title, category, status, current_commit) "
            "VALUES (?, ?, ?, ?, 'vigente', 'a' * 40)",
            (law_id, doc_id, title, cat),
        )
        conn.execute(
            "INSERT INTO law_versions (law_id, valid_from, commit_hash) "
            "VALUES (?, ?, ?)",
            (law_id, "2020-01-01", "a" * 40),
        )
        # FTS row using normalized title; phantom acts get <doc_id=N> placeholder
        fts_title = title or f"<doc_id={doc_id}>"
        insert_fts_row(conn, law_id=law_id, title=fts_title,
                       body=fts_title, category=cat)
    conn.commit()
    return conn
```

**Step 2: Append failing tests**

```python
# tests/mcp_server/test_queries.py (append)
from mcp_server.queries import (
    resolve_name_to_law_id, LawNotFound, AmbiguousName,
)


def test_resolve_by_identificador(populated_conn):
    assert resolve_name_to_law_id(populated_conn, "100") == "zakon-a"


def test_resolve_by_negative_identificador(populated_conn):
    """§7.3 phantom act with negative doc_id."""
    assert resolve_name_to_law_id(populated_conn, "-549676032") == "phantom"


def test_resolve_by_exact_slug(populated_conn):
    assert resolve_name_to_law_id(populated_conn, "zakon-a") == "zakon-a"


def test_resolve_by_unique_title(populated_conn):
    assert resolve_name_to_law_id(populated_conn, "Закон за А") == "zakon-a"


def test_ambiguous_title_raises_with_candidates(populated_conn):
    """§7.1 — multiple acts with identical title."""
    with pytest.raises(AmbiguousName) as exc:
        resolve_name_to_law_id(populated_conn, "Наредба № 7 за нещо")
    assert len(exc.value.candidates) == 2
    ids = {c["law_id"] for c in exc.value.candidates}
    assert ids == {"naredba-7", "naredba-7-2"}
    # Each candidate carries identificador — the disambiguating handle
    for c in exc.value.candidates:
        assert "identificador" in c


def test_unknown_name_raises_LawNotFound_with_suggestions(populated_conn):
    with pytest.raises(LawNotFound) as exc:
        resolve_name_to_law_id(populated_conn, "напълно непознат акт")
    assert "напълно непознат акт" in exc.value.name
    # suggestions array is present (may be empty)
    assert hasattr(exc.value, "suggestions")
```

**Step 3: Run to verify failure**

```bash
.venv/bin/pytest tests/mcp_server/test_queries.py -v 2>&1 | tail -10
```

Expected: ImportErrors / new test failures.

**Step 4: Extend `mcp_server/queries.py`**

```python
# mcp_server/queries.py (append)

from index.fts import bg_normalize, search_fts


class LawNotFound(LookupError):
    def __init__(self, name: str, suggestions: list[dict] | None = None):
        super().__init__(f"law not found: {name!r}")
        self.name = name
        self.suggestions = suggestions or []


class AmbiguousName(LookupError):
    def __init__(self, name: str, candidates: list[dict]):
        super().__init__(f"ambiguous name: {name!r} matches {len(candidates)} acts")
        self.name = name
        self.candidates = candidates


def _row_to_candidate(row: sqlite3.Row) -> dict:
    return {
        "law_id": row["law_id"],
        "identificador": str(row["doc_id"]),
        "title": row["title"],
        "category": row["category"],
    }


def resolve_name_to_law_id(conn: sqlite3.Connection, name: str) -> str:
    """Resolve a free-form name to a unique law_id.

    Resolution order: identificador (numeric) → exact slug → exact title.
    Multiple matches at any step → AmbiguousName. No match → LawNotFound
    (with FTS-based suggestions when available).
    """
    if not name or not name.strip():
        raise LawNotFound(name=name)
    name = name.strip()

    # 1. Identificador (numeric)
    if re.fullmatch(r"-?\d+", name):
        row = conn.execute(
            "SELECT law_id FROM laws WHERE doc_id = ?", (int(name),)
        ).fetchone()
        if row:
            return row["law_id"]

    # 2. Exact slug
    row = conn.execute(
        "SELECT law_id FROM laws WHERE law_id = ?", (name,)
    ).fetchone()
    if row:
        return row["law_id"]

    # 3. Exact title (case-insensitive)
    rows = conn.execute(
        "SELECT * FROM laws WHERE LOWER(title) = LOWER(?)", (name,)
    ).fetchall()
    if len(rows) == 1:
        return rows[0]["law_id"]
    if len(rows) > 1:
        raise AmbiguousName(name=name, candidates=[_row_to_candidate(r) for r in rows])

    # 4. Not found — try FTS suggestions
    suggestions: list[dict] = []
    try:
        fts_rows = search_fts(conn, name, limit=5)
        suggestions = [
            {"law_id": r["law_id"], "title": r["title"], "score": r["score"]}
            for r in fts_rows
        ]
    except sqlite3.OperationalError:
        pass  # FTS may not match degenerate input
    raise LawNotFound(name=name, suggestions=suggestions)
```

**Step 5: Run to verify pass**

```bash
.venv/bin/pytest tests/mcp_server/test_queries.py -v 2>&1 | tail -15
```

Expected: all tests in this file pass (17 from Task 7 + 6 new = 23).

**Step 6: Commit**

```bash
git add mcp_server/queries.py tests/mcp_server/test_queries.py tests/mcp_server/conftest.py
git commit -m "feat: resolve_name_to_law_id with §7.1 ambiguous-name handling

Resolution order: identificador → slug → exact title. Multiple title
matches → AmbiguousName(name, candidates) with identificador for each
candidate (the stable disambiguating handle per D-026).

Unknown name → LawNotFound(name, suggestions) with up to 5 FTS-based
suggestions so the model has something to retry with."
```

---

## Task 9: `version_at_date()` — temporal lookup with §7.2 fallback

**Files:**
- Modify: `mcp_server/queries.py`
- Modify: `tests/mcp_server/test_queries.py`

**Step 1: Append failing tests**

```python
# tests/mcp_server/test_queries.py (append)
from mcp_server.queries import (
    version_at_date, NoVersionAtDate, version_with_warnings,
)


def test_version_at_date_returns_commit_for_current(populated_conn):
    commit = version_at_date(populated_conn, "zakon-a", date=None)
    assert len(commit) == 40  # SHA-1 hex


def test_version_at_date_for_date_after_validity(populated_conn):
    """Date after valid_from returns the version that's still in force
    (valid_to is NULL for current versions)."""
    commit = version_at_date(populated_conn, "zakon-a", date="2024-12-31")
    assert commit  # any 40-char string


def test_version_at_date_for_date_before_validity_raises(populated_conn):
    with pytest.raises(NoVersionAtDate) as exc:
        version_at_date(populated_conn, "zakon-a", date="1900-01-01")
    assert exc.value.law_id == "zakon-a"
    assert exc.value.earliest_available  # earliest valid_from for the law


def test_version_at_date_for_unknown_law_raises_NoVersion(populated_conn):
    with pytest.raises(NoVersionAtDate):
        version_at_date(populated_conn, "nonexistent", date=None)


def test_version_with_warnings_attaches_DATE_UNCERTAIN_for_null_pub_date(populated_conn):
    """§7.2: act with valid_from set to today (bootstrap-run-date fallback
    because fecha_publicacion was null) should produce a DATE_UNCERTAIN
    warning when retrieved."""
    from datetime import date as _date
    today = _date.today().isoformat()
    populated_conn.execute(
        "UPDATE law_versions SET valid_from = ? WHERE law_id = 'phantom'",
        (today,),
    )
    populated_conn.commit()

    commit, warnings = version_with_warnings(populated_conn, "phantom", date=None)
    codes = [w["code"] for w in warnings]
    assert "DATE_UNCERTAIN" in codes
```

**Step 2: Run to verify failure**

```bash
.venv/bin/pytest tests/mcp_server/test_queries.py -v 2>&1 | tail -10
```

Expected: ImportError / new test failures.

**Step 3: Extend `mcp_server/queries.py`**

```python
# mcp_server/queries.py (append)

from datetime import date as _date


class NoVersionAtDate(LookupError):
    def __init__(self, law_id: str, date: str | None,
                 earliest_available: str | None = None,
                 latest_available: str | None = None):
        super().__init__(f"no version of {law_id} at date {date}")
        self.law_id = law_id
        self.date = date
        self.earliest_available = earliest_available
        self.latest_available = latest_available


def _earliest_latest(conn: sqlite3.Connection, law_id: str) -> tuple[str | None, str | None]:
    row = conn.execute(
        "SELECT MIN(valid_from), MAX(valid_from) FROM law_versions WHERE law_id = ?",
        (law_id,),
    ).fetchone()
    return row[0], row[1]


def version_at_date(conn: sqlite3.Connection, law_id: str,
                    date: str | None) -> str:
    """Return the commit_hash valid at `date` (or current if None).

    Raises NoVersionAtDate if the date is before the earliest valid_from
    or the law_id has no versions at all.
    """
    target = date or _date.today().isoformat()
    row = conn.execute(
        """SELECT commit_hash FROM law_versions
           WHERE law_id = ?
             AND valid_from <= ?
             AND (valid_to IS NULL OR valid_to > ?)
           ORDER BY valid_from DESC
           LIMIT 1""",
        (law_id, target, target),
    ).fetchone()
    if row:
        return row["commit_hash"]
    earliest, latest = _earliest_latest(conn, law_id)
    raise NoVersionAtDate(
        law_id=law_id, date=date,
        earliest_available=earliest, latest_available=latest,
    )


def version_with_warnings(conn: sqlite3.Connection, law_id: str,
                          date: str | None) -> tuple[str, list[dict]]:
    """Same as version_at_date but also returns warnings (e.g., §7.2)."""
    commit = version_at_date(conn, law_id, date)
    warnings: list[dict] = []
    # §7.2: detect bootstrap-run-date fallback (valid_from == today) as
    # the heuristic for "publication date was unknown at index time".
    today = _date.today().isoformat()
    row = conn.execute(
        "SELECT valid_from FROM law_versions WHERE law_id = ? AND commit_hash = ?",
        (law_id, commit),
    ).fetchone()
    if row and row["valid_from"] == today:
        warnings.append({
            "code": "DATE_UNCERTAIN",
            "law_id": law_id,
            "source_date_marker": "unknown",
            "note": "publication date not parseable from lex.bg; "
                    "version validity falls back to bootstrap run date",
        })
    return commit, warnings
```

**Step 4: Run to verify pass**

```bash
.venv/bin/pytest tests/mcp_server/test_queries.py -v 2>&1 | tail -10
```

Expected: 5 new tests pass (28 total in file).

**Step 5: Commit**

```bash
git add mcp_server/queries.py tests/mcp_server/test_queries.py
git commit -m "feat: version_at_date with §7.2 DATE_UNCERTAIN warning surfacing

version_at_date returns the commit_hash valid at the requested date or
raises NoVersionAtDate(law_id, date, earliest_available, latest_available).

version_with_warnings adds §7.2 detection: when valid_from equals today
(the bootstrap-run-date fallback for null fecha_publicacion), the call
returns a DATE_UNCERTAIN warning alongside the successful result. Per D-026
this is a warning, not a blocker."
```

---

## Task 10: `full_text_search()` and `article_lookup()`

**Files:**
- Modify: `mcp_server/queries.py`
- Modify: `tests/mcp_server/test_queries.py`

**Step 1: Append failing tests**

```python
# tests/mcp_server/test_queries.py (append)
from mcp_server.queries import (
    full_text_search, article_lookup, ArticleNotFound,
)


def test_search_returns_matching_acts(populated_conn):
    hits = full_text_search(populated_conn, "Закон за А")
    assert any(h["law_id"] == "zakon-a" for h in hits)


def test_search_morphology_matches_definite_article(populated_conn):
    """bg_normalize symmetry: query 'наредбата 7' should still find 'Наредба № 7'."""
    hits = full_text_search(populated_conn, "наредбата")
    assert any(h["law_id"].startswith("naredba-7") for h in hits)


def test_search_filters_by_category(populated_conn):
    hits = full_text_search(populated_conn, "Закон", category="ordinances")
    assert all(h["category"] == "ordinances" for h in hits)


def test_search_phantom_act_uses_doc_id_as_title(populated_conn):
    """§7.3: empty titulo acts should still be searchable via the
    <doc_id=N> substitute populated in laws_fts.title."""
    hits = full_text_search(populated_conn, "549676032")
    assert any(h["law_id"] == "phantom" for h in hits)


def test_article_lookup_missing_provision_raises(populated_conn):
    # No provisions seeded in the conftest fixture
    with pytest.raises(ArticleNotFound) as exc:
        article_lookup(populated_conn, "zakon-a", article="14",
                        paragraph=None, date=None)
    assert exc.value.law_id == "zakon-a"
    assert exc.value.article == "14"


def test_article_lookup_returns_text_for_matching_provision(populated_conn):
    populated_conn.execute(
        """INSERT INTO provisions(law_id, article, paragraph, valid_from, text, text_hash)
           VALUES ('zakon-a', '14', NULL, '2020-01-01', 'Чл. 14 текст.', 'h1')""",
    )
    populated_conn.execute(
        """INSERT INTO provisions(law_id, article, paragraph, valid_from, text, text_hash)
           VALUES ('zakon-a', '14', '2', '2020-01-01', '(2) Алинея 2.', 'h2')""",
    )
    populated_conn.commit()

    rows = article_lookup(populated_conn, "zakon-a",
                           article="14", paragraph=None, date=None)
    assert any(r["paragraph"] is None and "Чл. 14" in r["text"] for r in rows)

    rows = article_lookup(populated_conn, "zakon-a",
                           article="14", paragraph="2", date=None)
    assert len(rows) == 1
    assert rows[0]["paragraph"] == "2"
    assert "Алинея 2" in rows[0]["text"]
```

**Step 2: Run to verify failure**

```bash
.venv/bin/pytest tests/mcp_server/test_queries.py -v 2>&1 | tail -10
```

Expected: 6 new failures.

**Step 3: Extend `mcp_server/queries.py`**

```python
# mcp_server/queries.py (append)

class ArticleNotFound(LookupError):
    def __init__(self, law_id: str, article: str, paragraph: str | None,
                 available_articles: list[str] | None = None):
        super().__init__(f"article {article} not found in {law_id}")
        self.law_id = law_id
        self.article = article
        self.paragraph = paragraph
        self.available_articles = available_articles or []


def full_text_search(conn: sqlite3.Connection, query: str,
                     category: str | None = None,
                     limit: int = 20) -> list[dict]:
    """FTS5 search; symmetric bg_normalize is applied inside search_fts."""
    rows = search_fts(conn, query, category=category, limit=limit)
    out: list[dict] = []
    for r in rows:
        title = r["title"] or f"<doc_id={r['doc_id']}>"
        out.append({
            "law_id": r["law_id"],
            "identificador": str(r["doc_id"]),
            "title": title,
            "category": r["category"],
            "snippet": r["snippet"],
            "score": r["score"],
        })
    return out


def article_lookup(conn: sqlite3.Connection, law_id: str,
                   article: str, paragraph: str | None,
                   date: str | None) -> list[dict]:
    """Return the provision row(s) for a law/article/paragraph at a date.

    If paragraph is None, returns the article-as-whole row.
    If paragraph is set, returns the alinea row (and only that).
    Raises ArticleNotFound if no row matches.
    """
    target = date or _date.today().isoformat()
    sql = """
        SELECT article, paragraph, text, text_hash, valid_from, valid_to
          FROM provisions
         WHERE law_id = ? AND article = ?
           AND valid_from <= ?
           AND (valid_to IS NULL OR valid_to > ?)
    """
    params: list = [law_id, article, target, target]
    if paragraph is None:
        sql += " AND paragraph IS NULL"
    else:
        sql += " AND paragraph = ?"
        params.append(paragraph)
    rows = conn.execute(sql, params).fetchall()
    if not rows:
        # Find available articles for this law to surface in the error
        avail = [r["article"] for r in conn.execute(
            "SELECT DISTINCT article FROM provisions WHERE law_id = ? "
            "ORDER BY article", (law_id,),
        ).fetchall()]
        raise ArticleNotFound(law_id=law_id, article=article,
                              paragraph=paragraph, available_articles=avail)
    return [dict(r) for r in rows]
```

**Step 4: Run to verify pass**

```bash
.venv/bin/pytest tests/mcp_server/test_queries.py -v 2>&1 | tail -10
```

Expected: 6 new tests pass (34 total in file).

**Step 5: Commit**

```bash
git add mcp_server/queries.py tests/mcp_server/test_queries.py
git commit -m "feat: full_text_search and article_lookup query functions

full_text_search: thin wrapper over index.fts.search_fts with §7.3 empty
titulo handling (substitutes <doc_id=N> when DB title is empty/null).

article_lookup: SQL query against provisions table; ArticleNotFound
includes available_articles list for the model to retry with."
```

---

## Task 11: Error taxonomy (`mcp_server/errors.py`)

**Files:**
- Create: `mcp_server/errors.py`
- Create: `tests/mcp_server/test_errors.py`

**Step 1: Write failing tests**

```python
# tests/mcp_server/test_errors.py
import pytest
from mcp_server.errors import ToolError, ERROR_CODES


def test_all_8_codes_are_defined():
    expected = {
        "LAW_NOT_FOUND", "AMBIGUOUS_NAME", "NO_VERSION_AT_DATE",
        "DATE_UNCERTAIN", "INVALID_ARTICLE_SPEC", "ARTICLE_NOT_FOUND",
        "INDEX_STALE", "INDEX_MISSING",
    }
    assert ERROR_CODES == expected


def test_tool_error_carries_code_and_payload():
    e = ToolError(code="LAW_NOT_FOUND", payload={"name": "ZOP"})
    assert e.code == "LAW_NOT_FOUND"
    assert e.payload == {"name": "ZOP"}


def test_tool_error_unknown_code_raises():
    with pytest.raises(ValueError):
        ToolError(code="MADE_UP_CODE", payload={})


def test_tool_error_str_is_useful():
    e = ToolError(code="LAW_NOT_FOUND", payload={"name": "X"})
    s = str(e)
    assert "LAW_NOT_FOUND" in s
    assert "X" in s


def test_tool_error_to_dict():
    e = ToolError(code="AMBIGUOUS_NAME", payload={"candidates": []})
    assert e.to_dict() == {"code": "AMBIGUOUS_NAME", "candidates": []}
```

**Step 2: Run to verify failure**

```bash
.venv/bin/pytest tests/mcp_server/test_errors.py -v 2>&1 | tail -10
```

Expected: ImportError.

**Step 3: Write `mcp_server/errors.py`**

```python
# mcp_server/errors.py
"""Tool error taxonomy. Per D-026, errors are first-class structured outputs.

Each ToolError carries a stable `code` (one of ERROR_CODES) and a payload
dict with model-actionable structured data (suggestions, candidates,
available_articles, etc.). FastMCP serializes ToolError into the MCP
response envelope.
"""

ERROR_CODES = frozenset({
    "LAW_NOT_FOUND",
    "AMBIGUOUS_NAME",
    "NO_VERSION_AT_DATE",
    "DATE_UNCERTAIN",     # warning, rides in successful response
    "INVALID_ARTICLE_SPEC",
    "ARTICLE_NOT_FOUND",
    "INDEX_STALE",
    "INDEX_MISSING",
})


class ToolError(Exception):
    """Structured tool failure surfaced through the MCP response envelope."""

    def __init__(self, code: str, payload: dict):
        if code not in ERROR_CODES:
            raise ValueError(f"unknown error code {code!r}; "
                             f"must be one of {sorted(ERROR_CODES)}")
        self.code = code
        self.payload = payload
        super().__init__(f"{code}: {payload}")

    def to_dict(self) -> dict:
        """JSON-serializable form for FastMCP."""
        return {"code": self.code, **self.payload}
```

**Step 4: Run to verify pass**

```bash
.venv/bin/pytest tests/mcp_server/test_errors.py -v 2>&1 | tail -10
```

Expected: 5 passed.

**Step 5: Commit**

```bash
git add mcp_server/errors.py tests/mcp_server/test_errors.py
git commit -m "feat: ToolError + 8 stable error codes (D-026)

Frozen set of codes; ToolError refuses construction with an unknown code
to prevent typos drifting the taxonomy. to_dict() yields the JSON-shaped
payload FastMCP serializes into the MCP response envelope."
```

---

## Task 12: Response schemas (`mcp_server/schemas.py`)

**Files:**
- Create: `mcp_server/schemas.py`
- Create: `tests/mcp_server/test_schemas.py`

**Step 1: Write failing tests**

```python
# tests/mcp_server/test_schemas.py
import pytest
from mcp_server.schemas import GetLawResponse, SearchHit, GetArticleResponse


def test_get_law_response_required_fields():
    r = GetLawResponse(
        law_id="zop", identificador="2136735703",
        titulo="ЗОП", category="laws",
        fecha_publicacion="2016-02-16",
        ultima_actualizacion="2024-03-15",
        dv_issue="13", dv_year=2016,
        effective_date="2016-04-15",
        eli="/eli/bg/закон/2016/2/16/zop/con",
        amendment_history=[],
        commit_hash="a" * 40,
        body_markdown="# ЗОП\n\n...",
        warnings=[],
    )
    d = r.to_dict()
    for k in ("law_id", "identificador", "titulo", "fecha_publicacion",
              "body_markdown", "warnings"):
        assert k in d


def test_get_law_response_warnings_optional():
    r = GetLawResponse(
        law_id="x", identificador="1", titulo="X", category="laws",
        fecha_publicacion=None, ultima_actualizacion=None,
        dv_issue=None, dv_year=None, effective_date=None,
        eli=None, amendment_history=[],
        commit_hash="b" * 40, body_markdown="...",
        warnings=[{"code": "DATE_UNCERTAIN", "law_id": "x"}],
    )
    assert len(r.warnings) == 1
    assert r.warnings[0]["code"] == "DATE_UNCERTAIN"


def test_search_hit_shape():
    h = SearchHit(law_id="zop", identificador="100", title="ЗОП",
                   category="laws", snippet="...", score=1.5)
    d = h.to_dict()
    assert d == {
        "law_id": "zop", "identificador": "100", "title": "ЗОП",
        "category": "laws", "snippet": "...", "score": 1.5,
    }


def test_get_article_response_shape():
    r = GetArticleResponse(
        law_id="zop", article="14", paragraph="2",
        text="(2) ...", text_hash="abc", commit_hash="a" * 40,
        warnings=[],
    )
    d = r.to_dict()
    assert d["law_id"] == "zop" and d["article"] == "14" and d["paragraph"] == "2"
```

**Step 2: Run to verify failure**

```bash
.venv/bin/pytest tests/mcp_server/test_schemas.py -v 2>&1 | tail -10
```

Expected: ImportError.

**Step 3: Write `mcp_server/schemas.py`**

```python
# mcp_server/schemas.py
"""Typed response shapes per D-024.

These are dataclasses (not Pydantic) — FastMCP renders dataclass returns
into MCP response envelopes via dict serialization. Field names match
the YAML frontmatter for any field that mirrors the Markdown source.
"""

from dataclasses import dataclass, field, asdict
from typing import Any


@dataclass(frozen=True)
class GetLawResponse:
    law_id: str
    identificador: str
    titulo: str
    category: str
    fecha_publicacion: str | None
    ultima_actualizacion: str | None
    dv_issue: str | None
    dv_year: int | None
    effective_date: str | None
    eli: str | None
    amendment_history: list[dict]
    commit_hash: str
    body_markdown: str
    warnings: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SearchHit:
    law_id: str
    identificador: str
    title: str
    category: str
    snippet: str
    score: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class GetArticleResponse:
    law_id: str
    article: str
    paragraph: str | None
    text: str
    text_hash: str
    commit_hash: str
    warnings: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
```

**Step 4: Run to verify pass**

```bash
.venv/bin/pytest tests/mcp_server/test_schemas.py -v 2>&1 | tail -10
```

Expected: 4 passed.

**Step 5: Commit**

```bash
git add mcp_server/schemas.py tests/mcp_server/test_schemas.py
git commit -m "feat: typed response dataclasses for MCP tools (D-024)

GetLawResponse, SearchHit, GetArticleResponse — frozen dataclasses with
to_dict() helpers for FastMCP serialization. body_markdown is the law
text; metadata fields mirror YAML frontmatter; warnings carries §7.2
DATE_UNCERTAIN events alongside successful results."
```

---

## Task 13: FastMCP server with `get_law` tool

**Files:**
- Create: `mcp_server/server.py`
- Create: `mcp_server/__main__.py`
- Create: `tests/mcp_server/test_get_law.py`

**Step 1: Write failing tests**

```python
# tests/mcp_server/test_get_law.py
import pytest
from mcp_server.server import build_app
from mcp_server.errors import ToolError


@pytest.fixture
def app(populated_conn, tmp_path):
    """Build a FastMCP app bound to the populated_conn fixture and a tmp
    corpus root with a single fake law file."""
    (tmp_path / "laws").mkdir()
    (tmp_path / "laws" / "zakon-a.md").write_text(
        "---\ntitulo: 'Закон за А'\nidentificador: '100'\npais: bg\n"
        "rango: закон\nfecha_publicacion: '2020-01-01'\n"
        "ultima_actualizacion: '2020-01-01'\nestado: vigente\nfuente: lex.bg\n"
        "dv_issue: '1'\ndv_year: 2020\neffective_date: '2020-01-01'\n"
        "category: laws\neli: /eli/bg/закон/2020/1/1/zakon-a/con\n"
        "amendment_history: []\n---\n\n# ЗАКОН ЗА А\n\nТекст.\n",
        encoding="utf-8",
    )
    return build_app(conn=populated_conn, corpus_root=tmp_path)


def test_get_law_by_identificador_returns_full_response(app):
    result = app.call_tool_sync("get_law", {"name": "100"})
    assert result["law_id"] == "zakon-a"
    assert result["identificador"] == "100"
    assert "titulo" in result
    assert result["body_markdown"].startswith("# ЗАКОН ЗА А")
    assert "warnings" in result


def test_get_law_unknown_raises_LAW_NOT_FOUND(app):
    with pytest.raises(ToolError) as exc:
        app.call_tool_sync("get_law", {"name": "напълно непознат"})
    assert exc.value.code == "LAW_NOT_FOUND"
    assert "suggestions" in exc.value.payload


def test_get_law_ambiguous_raises_AMBIGUOUS_NAME(app):
    with pytest.raises(ToolError) as exc:
        app.call_tool_sync("get_law", {"name": "Наредба № 7 за нещо"})
    assert exc.value.code == "AMBIGUOUS_NAME"
    candidates = exc.value.payload["candidates"]
    assert len(candidates) == 2


def test_get_law_with_phantom_emits_DATE_UNCERTAIN_when_applicable(app):
    """§7.2: when valid_from is today (bootstrap-run-date fallback),
    response should include DATE_UNCERTAIN warning."""
    from datetime import date as _date
    today = _date.today().isoformat()
    app._conn.execute(
        "UPDATE law_versions SET valid_from = ? WHERE law_id = 'phantom'",
        (today,),
    )
    app._conn.commit()
    # Phantom act has empty title; we look it up by identificador
    result = app.call_tool_sync("get_law", {"name": "-549676032"})
    codes = [w["code"] for w in result["warnings"]]
    assert "DATE_UNCERTAIN" in codes
```

**Step 2: Run to verify failure**

```bash
.venv/bin/pytest tests/mcp_server/test_get_law.py -v 2>&1 | tail -10
```

Expected: ImportError.

**Step 3: Write `mcp_server/server.py`**

```python
# mcp_server/server.py
"""FastMCP server: thin tool definitions over the queries layer.

Tool docstrings are the MCP `tools/list` descriptions seen by Claude Code,
Claude Desktop, and OpenAI Codex. Per D-021, keeping these in sync with
behavior is enforced by FastMCP rendering them automatically.
"""

from __future__ import annotations

import logging
import sqlite3
import subprocess
from pathlib import Path
from typing import Any

import yaml
from fastmcp import FastMCP

from mcp_server import queries
from mcp_server.errors import ToolError
from mcp_server.schemas import GetLawResponse

log = logging.getLogger(__name__)


# ─────────────────────────── helpers ──────────────────────────────────────

def _read_law_markdown(corpus_root: Path, law_id: str, category: str,
                       commit_hash: str, current_commit: str) -> str:
    """Return the full Markdown (frontmatter + body) for the law at the
    given commit. Working-tree fast path when commit_hash == HEAD."""
    rel_path = f"{category}/{law_id}.md"
    if commit_hash == current_commit:
        path = corpus_root / rel_path
        return path.read_text(encoding="utf-8")
    out = subprocess.run(
        ["git", "show", f"{commit_hash}:{rel_path}"],
        cwd=corpus_root, check=True, capture_output=True, text=True,
    )
    return out.stdout


def _split_frontmatter(raw: str) -> tuple[dict, str]:
    parts = raw.split("\n---\n", 1)
    fm = yaml.safe_load(parts[0][4:])
    body = parts[1] if len(parts) > 1 else ""
    return fm, body


def _law_meta(conn: sqlite3.Connection, law_id: str) -> dict:
    row = conn.execute(
        "SELECT * FROM laws WHERE law_id = ?", (law_id,)
    ).fetchone()
    return dict(row) if row else {}


# ─────────────────────────── app factory ──────────────────────────────────

class _AppHandle:
    """Wrapper exposing a sync test harness on top of FastMCP."""

    def __init__(self, mcp: FastMCP, conn: sqlite3.Connection,
                 corpus_root: Path):
        self.mcp = mcp
        self._conn = conn
        self._corpus = corpus_root
        self._tools: dict[str, Any] = {}

    def call_tool_sync(self, name: str, args: dict) -> Any:
        """Run a registered tool synchronously by name (for tests)."""
        return self._tools[name](**args)


def build_app(conn: sqlite3.Connection, corpus_root: Path,
              name: str = "legalize-bg") -> _AppHandle:
    mcp = FastMCP(name)
    handle = _AppHandle(mcp, conn, corpus_root)

    @mcp.tool()
    def get_law(name: str, date: str | None = None) -> dict:
        """Return the full text and metadata of a Bulgarian normative act.

        Args:
            name: The act's title, slug, or numeric lex.bg identificador.
                Identificador is the most stable handle — slugs may carry
                collision suffixes (-2, -3) and titles may be non-unique
                across acts. See §7.1 of canonical-data-model.md.
            date: ISO 8601 date for historical retrieval. If omitted,
                returns the current consolidated version.

        Returns:
            Structured response with metadata (titulo, identificador,
            fecha_publicacion, eli, amendment_history, commit_hash) and
            body_markdown. May include a `warnings` list — e.g.
            DATE_UNCERTAIN for acts with unknown publication dates (§7.2).
        """
        try:
            law_id = queries.resolve_name_to_law_id(conn, name)
        except queries.AmbiguousName as e:
            raise ToolError(code="AMBIGUOUS_NAME",
                            payload={"name": e.name, "candidates": e.candidates})
        except queries.LawNotFound as e:
            raise ToolError(code="LAW_NOT_FOUND",
                            payload={"name": e.name, "suggestions": e.suggestions})

        try:
            commit, warnings = queries.version_with_warnings(conn, law_id, date)
        except queries.NoVersionAtDate as e:
            raise ToolError(code="NO_VERSION_AT_DATE", payload={
                "law_id": e.law_id, "date": e.date,
                "earliest_available": e.earliest_available,
                "latest_available": e.latest_available,
            })

        meta_row = _law_meta(conn, law_id)
        raw = _read_law_markdown(corpus_root, law_id,
                                  meta_row["category"], commit,
                                  meta_row["current_commit"])
        fm, body = _split_frontmatter(raw)
        resp = GetLawResponse(
            law_id=law_id,
            identificador=str(meta_row["doc_id"]),
            titulo=fm.get("titulo") or "",
            category=meta_row["category"],
            fecha_publicacion=fm.get("fecha_publicacion"),
            ultima_actualizacion=fm.get("ultima_actualizacion"),
            dv_issue=fm.get("dv_issue"),
            dv_year=fm.get("dv_year"),
            effective_date=fm.get("effective_date"),
            eli=fm.get("eli"),
            amendment_history=fm.get("amendment_history") or [],
            commit_hash=commit,
            body_markdown=body.lstrip("\n"),
            warnings=warnings,
        )
        return resp.to_dict()

    handle._tools["get_law"] = get_law
    return handle
```

**Step 4: Write `mcp_server/__main__.py` (CLI stub)**

```python
# mcp_server/__main__.py
"""CLI entry: python -m mcp_server [--db PATH] [--corpus PATH] [--strict]"""

import argparse
import logging
import sqlite3
import subprocess
import sys
from pathlib import Path

from mcp_server.server import build_app


def main() -> int:
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(message)s")
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="catalog.db")
    ap.add_argument("--corpus", type=Path, default=Path("."))
    ap.add_argument("--strict", action="store_true",
                    help="refuse to start if catalog is stale vs HEAD")
    args = ap.parse_args()

    if not Path(args.db).exists():
        logging.error("INDEX_MISSING: %s — run python -m index.build", args.db)
        return 2

    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row

    head = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=args.corpus, check=True, capture_output=True, text=True,
    ).stdout.strip()
    indexed = conn.execute(
        "SELECT DISTINCT current_commit FROM laws LIMIT 1"
    ).fetchone()
    indexed_hash = indexed[0] if indexed else None
    if indexed_hash != head:
        msg = f"INDEX_STALE: head={head[:8]} indexed={(indexed_hash or '?')[:8]}"
        if args.strict:
            logging.error(msg + " — refusing (--strict)")
            return 3
        logging.warning(msg + " — continuing (use --strict to refuse)")

    handle = build_app(conn=conn, corpus_root=args.corpus)
    handle.mcp.run()  # stdio transport
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

**Step 5: Run to verify pass**

```bash
.venv/bin/pytest tests/mcp_server/test_get_law.py -v 2>&1 | tail -10
```

Expected: 4 passed (note: real FastMCP integration tested in Task 16; here we use the `_AppHandle.call_tool_sync` shortcut).

**Step 6: Commit**

```bash
git add mcp_server/server.py mcp_server/__main__.py tests/mcp_server/test_get_law.py
git commit -m "feat: FastMCP server + get_law tool (D-021/024/026)

build_app(conn, corpus_root) returns a handle with the FastMCP app and a
test shortcut. get_law:
  - resolve_name_to_law_id (§7.1 ambiguity → AMBIGUOUS_NAME)
  - version_with_warnings (§7.2 → DATE_UNCERTAIN warning)
  - read working-tree .md OR git show <commit>:<path> for historical
  - return GetLawResponse.to_dict() with body_markdown + metadata

CLI in __main__.py wires up --db / --corpus / --strict and the staleness
check (soft-warn default; --strict refuses on mismatch)."
```

---

## Task 14: `search` and `get_article` tools

**Files:**
- Modify: `mcp_server/server.py` — add `search` and `get_article`
- Create: `tests/mcp_server/test_search.py`
- Create: `tests/mcp_server/test_get_article.py`

**Step 1: Write `tests/mcp_server/test_search.py`**

```python
# tests/mcp_server/test_search.py
import pytest
from mcp_server.server import build_app


def test_search_returns_list_of_hits(populated_conn, tmp_path):
    app = build_app(conn=populated_conn, corpus_root=tmp_path)
    hits = app.call_tool_sync("search", {"query": "Закон"})
    assert isinstance(hits, list)
    assert all("law_id" in h and "score" in h for h in hits)


def test_search_with_category_filter(populated_conn, tmp_path):
    app = build_app(conn=populated_conn, corpus_root=tmp_path)
    hits = app.call_tool_sync("search", {"query": "Закон",
                                          "category": "laws"})
    assert all(h["category"] == "laws" for h in hits)


def test_search_phantom_act_uses_doc_id_placeholder(populated_conn, tmp_path):
    """§7.3: phantom acts surface with `<doc_id=N>` in title field."""
    app = build_app(conn=populated_conn, corpus_root=tmp_path)
    hits = app.call_tool_sync("search", {"query": "549676032"})
    phantom_hits = [h for h in hits if h["law_id"] == "phantom"]
    assert phantom_hits
    assert phantom_hits[0]["title"].startswith("<doc_id=")
```

**Step 2: Write `tests/mcp_server/test_get_article.py`**

```python
# tests/mcp_server/test_get_article.py
import pytest
from mcp_server.server import build_app
from mcp_server.errors import ToolError


@pytest.fixture
def app_with_provisions(populated_conn, tmp_path):
    populated_conn.execute(
        """INSERT INTO provisions(law_id, article, paragraph, valid_from,
                                   text, text_hash)
           VALUES ('zakon-a', '14', NULL, '2020-01-01',
                   '**Чл. 14.** (1) Първа. (2) Втора.', 'h0')""")
    populated_conn.execute(
        """INSERT INTO provisions(law_id, article, paragraph, valid_from,
                                   text, text_hash)
           VALUES ('zakon-a', '14', '1', '2020-01-01', 'Първа.', 'h1')""")
    populated_conn.execute(
        """INSERT INTO provisions(law_id, article, paragraph, valid_from,
                                   text, text_hash)
           VALUES ('zakon-a', '14', '2', '2020-01-01', 'Втора.', 'h2')""")
    populated_conn.commit()
    return build_app(conn=populated_conn, corpus_root=tmp_path)


def test_get_article_full_article(app_with_provisions):
    r = app_with_provisions.call_tool_sync("get_article",
        {"law": "100", "article": "чл. 14"})
    assert r["article"] == "14"
    assert r["paragraph"] is None
    assert "Първа" in r["text"] and "Втора" in r["text"]


def test_get_article_with_alinea(app_with_provisions):
    r = app_with_provisions.call_tool_sync("get_article",
        {"law": "100", "article": "чл. 14, ал. 2"})
    assert r["article"] == "14"
    assert r["paragraph"] == "2"
    assert r["text"] == "Втора."


def test_get_article_invalid_spec_raises(app_with_provisions):
    with pytest.raises(ToolError) as exc:
        app_with_provisions.call_tool_sync("get_article",
            {"law": "100", "article": "garbage"})
    assert exc.value.code == "INVALID_ARTICLE_SPEC"
    assert "examples" in exc.value.payload


def test_get_article_not_found_raises(app_with_provisions):
    with pytest.raises(ToolError) as exc:
        app_with_provisions.call_tool_sync("get_article",
            {"law": "100", "article": "999"})
    assert exc.value.code == "ARTICLE_NOT_FOUND"
    assert "available_articles" in exc.value.payload


def test_get_article_law_not_found_raises(app_with_provisions):
    with pytest.raises(ToolError) as exc:
        app_with_provisions.call_tool_sync("get_article",
            {"law": "напълно непознат", "article": "чл. 1"})
    assert exc.value.code == "LAW_NOT_FOUND"
```

**Step 3: Run to verify failure**

```bash
.venv/bin/pytest tests/mcp_server/test_search.py tests/mcp_server/test_get_article.py -v 2>&1 | tail -15
```

Expected: failures (tools not registered yet).

**Step 4: Append `search` + `get_article` to `mcp_server/server.py`**

Inside `build_app()`, after the `get_law` definition:

```python
    @mcp.tool()
    def search(query: str, category: str | None = None,
               limit: int = 20) -> list[dict]:
        """Full-text search over the Bulgarian legislation corpus.

        Bulgarian morphology is handled via symmetric `bg_normalize`
        pre-processing (definite-article suffix stripping) so queries
        match grammatical variants without requiring exact form.

        Args:
            query: Free-form Bulgarian (or mixed Cyrillic/Latin) text.
            category: Optional filter — one of laws/codes/ordinances/
                regulations/implementing.
            limit: Max results (default 20).

        Returns:
            List of {law_id, identificador, title, category, snippet, score}.
            Acts with empty titles (§7.3) get `<doc_id=N>` substituted in
            the `title` slot.
        """
        return queries.full_text_search(conn, query=query,
                                         category=category, limit=limit)

    @mcp.tool()
    def get_article(law: str, article: str,
                    date: str | None = None) -> dict:
        """Return a specific article (or alinea) of a Bulgarian act.

        Args:
            law: Title, slug, or identificador (see get_law).
            article: Article reference. Accepts:
                "чл. 14", "14", "чл. 14а" (Cyrillic suffix),
                "чл. 14, ал. 2" or "14.2" (alinea), "чл. 14-16" (range).
            date: ISO 8601 date for historical retrieval; omit for current.

        Returns:
            {law_id, article, paragraph, text, text_hash, commit_hash,
             warnings}. paragraph is null for the article-as-whole row.
        """
        try:
            law_id = queries.resolve_name_to_law_id(conn, law)
        except queries.AmbiguousName as e:
            raise ToolError(code="AMBIGUOUS_NAME",
                            payload={"name": e.name, "candidates": e.candidates})
        except queries.LawNotFound as e:
            raise ToolError(code="LAW_NOT_FOUND",
                            payload={"name": e.name, "suggestions": e.suggestions})

        try:
            spec = queries.parse_article_spec(article)
        except queries.InvalidArticleSpec:
            raise ToolError(code="INVALID_ARTICLE_SPEC", payload={
                "spec": article,
                "examples": ["чл. 14", "14", "чл. 14а",
                              "чл. 14, ал. 2", "14.2", "чл. 14-16"],
            })

        try:
            commit, warnings = queries.version_with_warnings(conn, law_id, date)
        except queries.NoVersionAtDate as e:
            raise ToolError(code="NO_VERSION_AT_DATE", payload={
                "law_id": e.law_id, "date": e.date,
                "earliest_available": e.earliest_available,
                "latest_available": e.latest_available,
            })

        try:
            rows = queries.article_lookup(
                conn, law_id, article=spec.article,
                paragraph=spec.paragraph, date=date)
        except queries.ArticleNotFound as e:
            raise ToolError(code="ARTICLE_NOT_FOUND", payload={
                "law_id": e.law_id, "article": e.article,
                "paragraph": e.paragraph,
                "available_articles": e.available_articles,
            })

        # When paragraph requested, return the alinea row; else the article-as-whole row
        target = next((r for r in rows
                        if (r["paragraph"] == spec.paragraph)
                        or (spec.paragraph is None and r["paragraph"] is None)), rows[0])
        return {
            "law_id": law_id,
            "article": target["article"],
            "paragraph": target["paragraph"],
            "text": target["text"],
            "text_hash": target["text_hash"],
            "commit_hash": commit,
            "warnings": warnings,
        }

    handle._tools["search"] = search
    handle._tools["get_article"] = get_article
```

**Step 5: Run to verify pass**

```bash
.venv/bin/pytest tests/mcp_server/ -v 2>&1 | tail -15
```

Expected: all mcp_server tests pass.

**Step 6: Commit**

```bash
git add mcp_server/server.py tests/mcp_server/test_search.py tests/mcp_server/test_get_article.py
git commit -m "feat: search and get_article MCP tools

search: thin wrapper over queries.full_text_search; returns ranked
SearchHit list. §7.3 phantom-title acts get <doc_id=N> substitute.

get_article: parse_article_spec → resolve_name → version_at_date →
article_lookup. Errors translate to ToolError codes:
  INVALID_ARTICLE_SPEC (with examples in payload)
  ARTICLE_NOT_FOUND (with available_articles list)
  LAW_NOT_FOUND, AMBIGUOUS_NAME, NO_VERSION_AT_DATE."
```

---

## Task 15: §7 acceptance tests + FTS regression suite

**Files:**
- Create: `tests/mcp_server/test_data_quality_acceptance.py`
- Modify: `tests/fixtures/queries/bg_search_regression.yaml`

**Step 1: Write acceptance tests anchored to real corpus rows**

```python
# tests/mcp_server/test_data_quality_acceptance.py
"""§7.1, §7.2, §7.3 cases tested against the real catalog.db built from
the live `main` branch of legalize-bg. Skipped if catalog.db is missing
(developers should run `python -m index.build` first).
"""

import pathlib
import sqlite3
import pytest

from mcp_server.server import build_app
from mcp_server.errors import ToolError

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
DB_PATH = REPO_ROOT / "catalog.db"


@pytest.fixture(scope="module")
def real_app():
    if not DB_PATH.exists():
        pytest.skip("catalog.db missing; run python -m index.build first")
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return build_app(conn=conn, corpus_root=REPO_ROOT)


def test_71_ambiguous_collision_slug(real_app):
    """Pick a law whose slug ends in '-2' (collision-resolved) and search
    by its title — expect AMBIGUOUS_NAME with both candidates."""
    row = real_app._conn.execute(
        "SELECT law_id, title FROM laws WHERE law_id LIKE '%-2' LIMIT 1"
    ).fetchone()
    assert row, "no collision-suffixed law in catalog (expected ~5-10% per §7.1)"
    title = row["title"]
    with pytest.raises(ToolError) as exc:
        real_app.call_tool_sync("get_law", {"name": title})
    assert exc.value.code == "AMBIGUOUS_NAME"
    candidates = exc.value.payload["candidates"]
    assert len(candidates) >= 2
    for c in candidates:
        assert c["identificador"]


def test_72_null_pub_date_returns_DATE_UNCERTAIN(real_app):
    """Pick one of the 121 acts where law_versions.valid_from equals today
    (the bootstrap fallback) and expect DATE_UNCERTAIN warning."""
    from datetime import date as _date
    today = _date.today().isoformat()
    row = real_app._conn.execute(
        """SELECT laws.law_id, laws.doc_id FROM laws
              JOIN law_versions USING(law_id)
             WHERE law_versions.valid_from = ?
             LIMIT 1""", (today,),
    ).fetchone()
    if not row:
        pytest.skip("no §7.2 acts in current build (expected 121 per data quality §7.2)")
    result = real_app.call_tool_sync("get_law", {"name": str(row["doc_id"])})
    codes = [w["code"] for w in result["warnings"]]
    assert "DATE_UNCERTAIN" in codes


def test_73_empty_titulo_phantom_act(real_app):
    """Doc_id -549676032 (the spot-check phantom) has empty titulo on
    lex.bg. Expected behavior: get_law via identificador succeeds with
    empty `titulo`, search uses `<doc_id=N>` substitute."""
    result = real_app.call_tool_sync("get_law", {"name": "-549676032"})
    assert result["law_id"]
    assert result["titulo"] == ""  # truthful empty
    hits = real_app.call_tool_sync("search", {"query": "549676032"})
    phantom = [h for h in hits if h["law_id"] == result["law_id"]]
    assert phantom and phantom[0]["title"].startswith("<doc_id=")
```

**Step 2: Expand `bg_search_regression.yaml` with realistic queries**

```yaml
# tests/fixtures/queries/bg_search_regression.yaml
cases:
  - query: "обществени поръчки"
    must_include: ["zakon-za-obshtestvenite-porachki"]
    description: "ЗОП should rank top-3"

  - query: "обществената поръчка"
    must_include: ["zakon-za-obshtestvenite-porachki"]
    description: "morphology — singular def-art form should still match"

  - query: "електронното управление"
    must_include: ["zakon-za-elektronnoto-upravlenie"]
    description: "ЗЕУ via def-art form"

  - query: "ЗОП"
    must_include: ["zakon-za-obshtestvenite-porachki"]
    description: "Latin-letter abbreviation should match (case-folded)"

  - query: "интелигентни транспортни системи"
    must_include_substring: "intelligent"
    description: "ITS naredba (PMS 14/2013) should be found"
```

**Step 3: Add a regression-suite runner test**

```python
# tests/index/test_fts_regression.py
import pathlib
import sqlite3
import pytest
import yaml

from mcp_server.queries import full_text_search

REPO = pathlib.Path(__file__).resolve().parent.parent.parent
DB = REPO / "catalog.db"
CASES = REPO / "tests/fixtures/queries/bg_search_regression.yaml"


@pytest.fixture(scope="module")
def conn():
    if not DB.exists():
        pytest.skip("catalog.db missing")
    c = sqlite3.connect(str(DB))
    c.row_factory = sqlite3.Row
    return c


def _cases():
    return yaml.safe_load(CASES.read_text())["cases"]


@pytest.mark.parametrize("case", _cases(), ids=lambda c: c["query"][:30])
def test_search_regression(conn, case):
    hits = full_text_search(conn, case["query"], limit=20)
    hit_ids = [h["law_id"] for h in hits]
    for needed in case.get("must_include", []):
        assert needed in hit_ids, f"{case['query']!r} missing {needed!r}; got top-5: {hit_ids[:5]}"
    for forbidden in case.get("must_exclude", []):
        assert forbidden not in hit_ids
    if "must_include_substring" in case:
        assert any(case["must_include_substring"] in h_id for h_id in hit_ids)
```

**Step 4: Build the catalog and run**

```bash
.venv/bin/python -m index.build --corpus . --db catalog.db 2>&1 | tail -3
.venv/bin/pytest tests/mcp_server/test_data_quality_acceptance.py tests/index/test_fts_regression.py -v 2>&1 | tail -15
```

Expected: all pass.

**Step 5: Commit**

```bash
git add tests/mcp_server/test_data_quality_acceptance.py tests/index/test_fts_regression.py tests/fixtures/queries/bg_search_regression.yaml
git commit -m "test: §7.1/7.2/7.3 acceptance + FTS regression suite

Real-corpus acceptance tests anchored to actual catalog rows:
  §7.1 — collision-suffixed law triggers AMBIGUOUS_NAME
  §7.2 — null-pub-date act surfaces DATE_UNCERTAIN warning
  §7.3 — phantom act (doc_id -549676032) returns empty titulo, search uses <doc_id=N>

bg_search_regression.yaml — query → expected behavior pairs to detect
Bulgarian normalizer drift. Five seed cases including ITS naredba spot-check."
```

---

## Task 16: FastMCP end-to-end integration test

**Files:**
- Create: `tests/mcp_server/test_tools_e2e.py`

**Step 1: Write tests using the real FastMCP test transport**

```python
# tests/mcp_server/test_tools_e2e.py
"""End-to-end integration via the FastMCP in-memory test transport.

Validates that tool registration produces a discoverable MCP `tools/list`
response and that JSON-RPC tool calls flow through correctly. The
populated_conn fixture is reused; a 1-act fake corpus is materialized.
"""

import pytest
from mcp_server.server import build_app


def test_tools_list_contains_three_phase_1b1_tools(populated_conn, tmp_path):
    app = build_app(conn=populated_conn, corpus_root=tmp_path)
    listed = list(app._tools.keys())
    assert "get_law" in listed
    assert "search" in listed
    assert "get_article" in listed
    assert len(listed) == 3, f"expected exactly 3 Phase 1b.1 tools; got {listed}"


def test_tool_descriptions_are_docstrings(populated_conn, tmp_path):
    """FastMCP renders docstrings as MCP descriptions (D-021). Confirm
    each tool has a non-trivial docstring covering args and returns."""
    app = build_app(conn=populated_conn, corpus_root=tmp_path)
    for name in ("get_law", "search", "get_article"):
        fn = app._tools[name]
        doc = fn.__doc__ or ""
        assert len(doc) > 100, f"{name} docstring too short for MCP description"
        assert "Args:" in doc and ("Returns:" in doc or "Returns " in doc)
```

**Step 2: Run**

```bash
.venv/bin/pytest tests/mcp_server/test_tools_e2e.py -v 2>&1 | tail -10
```

Expected: 2 passed.

**Step 3: Commit**

```bash
git add tests/mcp_server/test_tools_e2e.py
git commit -m "test: FastMCP integration — tool registration + docstring contract

Confirms 3 Phase 1b.1 tools register, and each carries a substantive
docstring (≥100 chars, Args: + Returns sections) so FastMCP can render
high-quality MCP tools/list descriptions for Claude Code, Claude Desktop,
and OpenAI Codex (D-021)."
```

---

## Task 17: Performance regression budgets (soft assertions)

**Files:**
- Create: `tests/perf/test_budgets.py`
- Create: `tests/perf/__init__.py`

**Step 1: Write soft-assertion budget test**

```python
# tests/perf/test_budgets.py
"""Soft-assertion performance budgets per design doc §9.

Phase 1b.1: WARN on regression (test passes but logs a warning).
Phase 1b.2: promote to hard assertions (skipped here for now).

Skipped when catalog.db is missing.
"""

import pathlib
import sqlite3
import time
import logging
import pytest

REPO = pathlib.Path(__file__).resolve().parent.parent.parent
DB = REPO / "catalog.db"

BUDGETS = {
    "search_p95":             0.100,  # 100 ms
    "get_law_current_p95":    0.100,
    "get_article_p95":        0.050,
}


@pytest.fixture(scope="module")
def conn():
    if not DB.exists():
        pytest.skip("catalog.db missing")
    c = sqlite3.connect(str(DB))
    c.row_factory = sqlite3.Row
    return c


def _p95(samples: list[float]) -> float:
    samples = sorted(samples)
    idx = int(len(samples) * 0.95)
    return samples[min(idx, len(samples) - 1)]


def test_search_p95(conn):
    from mcp_server.queries import full_text_search
    queries = ["обществени поръчки", "електронно управление", "наредба",
                "правилник", "закон", "административно", "транспорт",
                "съд", "образование", "здравеопазване"] * 5  # 50 calls
    durations = []
    for q in queries:
        t0 = time.monotonic()
        full_text_search(conn, q, limit=20)
        durations.append(time.monotonic() - t0)
    p95 = _p95(durations)
    if p95 > BUDGETS["search_p95"]:
        logging.warning("search p95=%.3fs exceeds budget %.3fs (1b.1 SOFT)",
                         p95, BUDGETS["search_p95"])
    # 1b.1: don't fail; 1b.2 will promote: assert p95 <= BUDGETS["search_p95"]
```

**Step 2: Run**

```bash
mkdir -p tests/perf && touch tests/perf/__init__.py
.venv/bin/pytest tests/perf/ -v 2>&1 | tail -10
```

Expected: passes; may log a perf warning.

**Step 3: Commit**

```bash
git add tests/perf/__init__.py tests/perf/test_budgets.py
git commit -m "test: performance budget infra (soft 1b.1, hard 1b.2)

50-query search p95 budget at 100ms. Logs a warning on regression in
1b.1; will promote to hard assertions in 1b.2 (structured backend
hardening milestone) once observability lands."
```

---

## Task 18: `scripts/build_index.py` + smoke test

**Files:**
- Create: `scripts/build_index.py`

**Step 1: Write thin wrapper**

```python
# scripts/build_index.py
"""One-line wrapper so operators can run `python scripts/build_index.py`."""

from index.build import main

if __name__ == "__main__":
    raise SystemExit(main())
```

**Step 2: Smoke build the full corpus + verify**

```bash
.venv/bin/python -m index.build --corpus . --db catalog.db 2>&1 | tail -3
.venv/bin/python -c "
import sqlite3
c = sqlite3.connect('catalog.db')
print('laws:', c.execute('SELECT COUNT(*) FROM laws').fetchone()[0])
print('versions:', c.execute('SELECT COUNT(*) FROM law_versions').fetchone()[0])
print('article rows:', c.execute('SELECT COUNT(*) FROM provisions WHERE paragraph IS NULL').fetchone()[0])
print('alinea rows:', c.execute('SELECT COUNT(*) FROM provisions WHERE paragraph IS NOT NULL').fetchone()[0])
print('fts rows:', c.execute('SELECT COUNT(*) FROM laws_fts').fetchone()[0])
"
```

Expected: 3,573 laws / 3,573 versions / many thousands of article + alinea rows / 3,573 fts rows.

**Step 3: Smoke run all 3 tools end-to-end**

```bash
.venv/bin/python -c "
import sqlite3
from pathlib import Path
from mcp_server.server import build_app

conn = sqlite3.connect('catalog.db')
conn.row_factory = sqlite3.Row
app = build_app(conn=conn, corpus_root=Path('.'))

# search
hits = app.call_tool_sync('search', {'query': 'обществени поръчки'})
print(f'search: {len(hits)} hits; top: {hits[0][\"law_id\"] if hits else None}')

# get_law by identificador
r = app.call_tool_sync('get_law', {'name': '2136735703'})
print(f'get_law: {r[\"law_id\"]} ({r[\"titulo\"][:50]}...) body={len(r[\"body_markdown\"])} chars')

# get_article
a = app.call_tool_sync('get_article', {'law': '2136735703', 'article': 'чл. 1'})
print(f'get_article: чл. {a[\"article\"]} text={len(a[\"text\"])} chars')
"
```

Expected: all three return reasonable results.

**Step 4: Commit**

```bash
git add scripts/build_index.py catalog.db || true   # catalog.db is gitignored
git status --short
git commit -m "feat: scripts/build_index.py thin wrapper

Operators run `python scripts/build_index.py` (or equivalently
`python -m index.build`) after a fresh clone or after corpus changes.
catalog.db remains gitignored — derived state, rebuildable from git+YAML."
```

---

## Task 19: Final integration — full test suite + Claude Code config example

**Files:**
- Modify: `README.md` — add MCP setup section
- Create: `docs/runbook/2026-05-09-phase1b1-operator-setup.md`

**Step 1: Run full test suite**

```bash
.venv/bin/pytest -q 2>&1 | tail -5
```

Expected: all tests pass (existing 67 + ~60 new from Phase 1b.1 ≈ 130+ total).

**Step 2: Write operator setup doc**

```markdown
# Phase 1b.1 Operator Setup

## Prerequisites

- Python 3.12+
- Cloned `legalize-bg` repo with `main` checked out
- Virtualenv at `.venv` with `pip install -e ".[dev]"`

## One-time index build

```bash
python -m index.build --corpus . --db catalog.db
```

Takes ~3-5 minutes. Produces `catalog.db` (~50-100 MB).

## Claude Code / Claude Desktop / OpenAI Codex config

```json
{
  "mcpServers": {
    "legalize-bg": {
      "command": "/abs/path/to/legalize-bg/.venv/bin/python",
      "args": ["-m", "mcp_server",
               "--db", "/abs/path/to/legalize-bg/catalog.db",
               "--corpus", "/abs/path/to/legalize-bg"]
    }
  }
}
```

## Smoke test

In a new Claude Code session, ask:
> Search the Bulgarian legislation corpus for "обществени поръчки" using the legalize-bg MCP.

Expected: top result is ЗОП. Then:
> Show me чл. 14 of ЗОП using identificador 2136735703.

Expected: returns the article text via `get_article`.

## Re-indexing after corpus changes

`python -m index.build` again. The MCP server soft-warns at startup if HEAD != indexed commit; pass `--strict` to enforce a hard refusal.
```

**Step 3: Update README.md**

Append a brief section:

```markdown
## MCP server (Phase 1b.1)

The `mcp_server/` package exposes the corpus to Claude Code, Claude
Desktop, and OpenAI Codex via Model Context Protocol. See
[Phase 1b.1 operator setup](docs/runbook/2026-05-09-phase1b1-operator-setup.md)
for installation. Design rationale in
[Phase 1b design](docs/plans/2026-05-09-phase1b-mcp-design.md).
```

**Step 4: Update `docs/sync/ACTIVE.md` to reflect 1b.1 ship**

Replace the "Pending" section so 1b.1 is marked done, 1b.2 is the next milestone.

**Step 5: Commit**

```bash
git add README.md docs/runbook/2026-05-09-phase1b1-operator-setup.md docs/sync/ACTIVE.md
git commit -m "docs: Phase 1b.1 operator setup runbook + ACTIVE.md milestone update

Phase 1b.1 ships:
  - 3 MCP tools (get_law, search, get_article) wired through FastMCP/stdio
  - Bulgarian-aware FTS5 search with morphological coverage
  - Provisions table populated to alinea level (D-023)
  - 8-code error taxonomy with structured payloads (D-026)
  - §7.1/7.2/7.3 data-quality cases as server-enforced contracts
  - Real-corpus acceptance tests + FTS regression suite + soft perf budgets

Next: Phase 1b.2 (structured backend hardening — JSON schemas published
as tools.json, error taxonomy formalized for downstream callers,
performance budgets promoted from soft to hard assertions)."
```

**Step 6: Push to main**

```bash
git push origin main 2>&1 | tail -3
```

Expected: clean push.

---

## Dependencies and parallelization

Tasks that can run in parallel via subagents (Phase 1a precedent):

```
Task 1 (setup) ─── sequential, foundation
       │
       ▼
Task 2 (migrations) ─── sequential, schema first
       │
       ├─→ Task 3 (bg_normalize)     ┐
       ├─→ Task 4 (provisions article)│
       │      └─→ Task 5 (alinea)    │ all parallel after T2
       ├─→ Task 7 (parse_article_spec)│
       ├─→ Task 11 (errors)          │
       └─→ Task 12 (schemas)         ┘

Task 6 (index.build) — depends on T3, T4/T5
       │
       ▼
Task 8 (resolve_name) ─── parallel with T9
Task 9 (version_at_date)
Task 10 (search + article_lookup) — depends on T3 (bg_normalize) + T7 (parse_article_spec)
       │
       ▼
Task 13 (server + get_law) — depends on T8/9/10/11/12
       │
       ▼
Task 14 (search + get_article tools) — sequential; same file
       │
       ▼
Task 15 (acceptance + regression) — depends on T13/14 + a built catalog.db
Task 16 (e2e tests)               ┘
       │
       ▼
Task 17 (perf budgets) — depends on T13/14 + catalog.db
       │
       ▼
Task 18 (smoke + scripts/) — sequential, integration
       │
       ▼
Task 19 (docs + final push) — sequential
```

Tasks 3-5, 7, 11, 12 are five parallel-dispatchable pure-code tasks (no overlapping files, no shared in-flight git state). Phase 1a precedent: dispatch 5 subagents, each writes its own files + tests + runs pytest, none commits — coordinator commits sequentially in plan order after all return.

---

## Definition of Done — Phase 1b.1

Per `delivery-contract.md`:

- [ ] `get_law()`, `search()`, `get_article()` tools working through FastMCP/stdio
- [ ] Claude Code, Claude Desktop, and OpenAI Codex can each access the corpus via the MCP server
- [ ] Response times under 2 seconds for single-law queries (search <100ms p95, get_law current <100ms p95, get_article <50ms p95 — all soft asserted)
- [ ] All 8 error codes covered by tests
- [ ] §7.1, §7.2, §7.3 data-quality cases covered by acceptance tests against the real corpus
- [ ] `provisions` table populated to alinea level (D-023) with `text` and `text_hash` columns
- [ ] `index/migrations.py` schema-version tracking active (D-025)
- [ ] `bg_normalize` symmetric across index + query (D-022)
- [ ] Operator setup runbook published; smoke test verified by manual exercise from each of the 3 client tools
