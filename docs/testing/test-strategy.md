# Test Strategy

Testing strategy for the legalize-bg pipeline. Covers unit through validation testing, acceptance criteria per phase, test data management, and regression policy.

---

## 1. Test Layers

### Unit Tests

**Scope:** Individual functions in isolation. No network access, no git operations.

- **HTML parser correctness** — For each CSS class (`.TitleDocument`, `.PreHistory`, `.HistoryOfDocument`, `.Part`, `.Heading`, `.Section`, `.Article`, `.TransitionalFinalEdicts`), verify that the parser produces the correct Markdown structure. One test per class, using minimal HTML snippets as input.
- **YAML field extraction** — Verify that metadata extraction produces all 13 frontmatter fields with correct types and values. Test edge cases: missing DV references, acts with no amendments, acts with status `derogado`.
- **ЗИД regex patterns** — For each of the 8 operation types (substitution, addition, deletion, renumbering, restructuring, full repeal, new chapter, table/annex), verify pattern matching against real-world amendment text extracted from DV. Test both positive matches and negative cases (text that looks similar but is not an amendment instruction).
- **Slug generation** — Verify that Bulgarian titles produce correct filesystem slugs (Cyrillic transliteration, abbreviation handling).
- **Encoding** — Verify correct cp1251 to UTF-8 conversion for all Bulgarian characters and edge cases (special quotes, em-dashes, section signs).

### Integration Tests

**Scope:** End-to-end pipeline stages using cached HTML fixtures. No live network access.

- **Fetch-parse-convert pipeline** — For each of the 5 categories, run the full pipeline on a cached lex.bg page and verify: (1) valid Markdown output, (2) correct YAML frontmatter, (3) article structure preserved, (4) amendment history correctly extracted from `.HistoryOfDocument`.
- **SQLite index build** — From a set of test Markdown files with frontmatter, build the SQLite index and verify all tables are correctly populated, all foreign keys resolve, and temporal ranges are gapless.
- **Git commit generation** — Verify that the committer produces correctly formatted commit messages with proper `[bootstrap]`/`[reforma]` prefixes, `Source-Id`, `Source-Date`, `Norm-Id` metadata, and `GIT_AUTHOR_DATE` set correctly.
- **MCP tool responses** — Verify that `get_law()`, `search()`, `get_article()` return correct data for known laws in the test corpus.

### Validation Tests

**Scope:** Consolidation engine output compared against lex.bg as oracle (Phase 4v).

- **Round-trip validation** — For each law in the test set: (1) apply a known ЗИД to the pre-amendment version using the consolidation engine, (2) fetch the post-amendment version from lex.bg, (3) normalize both (strip whitespace, normalize quotes and dashes), (4) diff and report.
- **Accuracy tracking** — Maintain a running accuracy metric (percentage of test laws where consolidation matches lex.bg within normalization tolerance). Target: >95%.
- **Failure classification** — When consolidation diverges from lex.bg, classify the cause: regex pattern gap, renumbering error, structural change, lex.bg editorial correction, etc.

### Contract Tests

**Scope:** Compliance with external interface contracts.

- **YAML frontmatter vs. Legalize SPEC** — Validate that every Markdown file in the repository has all 8 mandatory Legalize fields with correct types and allowed values. Run as a CI check on every commit.
- **MCP tool response format** — Validate that MCP tool responses match the expected JSON schema (correct keys, types, non-null required fields). Tests run against a local MCP server instance.
- **Legalize hard gates** — The 4 gates from the Legalize contribution guide must pass before Phase 5 submission: (1) valid YAML frontmatter on all files, (2) correct commit message format, (3) no duplicate `identificador` values, (4) CI pipeline green.

### Phase 1b.1 testing layers

The MCP server uses four practical testing layers, all running against an in-memory FastMCP app (no separate server process):

- **L1 — Unit:** Pure functions. `bg_normalize`, `parse_article_spec`, `_legal_article_sort_key`, schema dataclass round-trips. Files under `tests/index/test_fts.py`, `tests/mcp_server/test_queries.py`, `tests/mcp_server/test_schemas.py`.
- **L2 — Component:** Per-tool tests via the `_AppHandle.call_tool_sync(name, args)` shortcut. Skips JSON-RPC serialization; bound to a populated in-memory SQLite via the `populated_conn` fixture. Files: `tests/mcp_server/test_get_law.py`, `test_search.py`, `test_get_article.py`, `test_errors.py`.
- **L3 — In-memory FastMCP `Client`:** Exercises the JSON-RPC envelope itself, using `fastmcp.Client(handle.mcp)`. File: `tests/mcp_server/test_tools_e2e.py`.
- **L4 — Acceptance:** §7 data-quality cases (slug ≠ title, null `fecha_publicacion`, empty titulo) and the perf-budget tier in `tests/mcp_server/test_data_quality_acceptance.py` and the soft-perf-assertion suite. Soft in 1b.1, promoted to hard in 1b.2 per D-027.

The `populated_conn` conftest fixture stamps `current_commit = "a"*40` (FAKE_COMMIT_HASH) so the working-tree fast path in `_read_law_markdown` works against `tmp_path` without needing a real git repo.

---

## 2. Acceptance Criteria per Phase

### Phase 1a: Bootstrap Scrape

- All 5 categories scraped: laws (~394), codes (~24), ordinances (~2,604), regulations (~490), implementing (~61).
- Every act has a valid YAML frontmatter block with all 13 fields populated.
- Markdown output preserves article structure: parts, chapters, sections, articles, paragraphs are correctly nested using Markdown heading levels.
- No cp1251 encoding artifacts in any file (all output is valid UTF-8).
- Each act is committed as a separate `[bootstrap]` commit.

### Phase 1b: MCP Server

- `get_law(name)` returns the full Markdown text for any law in the corpus.
- `get_law(name, date)` returns the version of the law that was in force on the given date (after Phase 2 populates the temporal index).
- `search(query)` returns relevant results ranked by relevance, with correct snippets.
- `get_article(law, article)` returns the correct article text, supporting both "чл. 14" and "14" input formats.
- MCP tool responses are valid JSON matching the documented schema.

### Phase 4: Consolidation Engine

- Consolidation accuracy >95% vs. lex.bg for a test set of 50 frequently-amended laws.
- All 7 non-LLM operation types (substitution, addition, deletion, renumbering, full repeal, new chapter, table/annex) correctly handled. Renumbering uses programmatic logic rather than regex but does not require LLM.
- LLM fallback correctly handles restructuring cases (move, split, merge).
- Cross-law amendments via ПЗР are detected and applied to all target laws.

### Phase 5: Legalize Contribution

- Passes all 4 Legalize hard gates.
- `fetcher/bg/` implements all 4 required interfaces: `LegislativeClient`, `NormDiscovery`, `TextParser`, `MetadataParser`.
- Legalize CI pipeline runs green with Bulgarian data.
- No regressions in existing Legalize country pipelines.

---

## 3. Test Data Strategy

### HTML Fixtures

Cached HTML responses from lex.bg, stored in `tests/fixtures/html/`. Each fixture is a complete HTTP response body saved as a file with cp1251 encoding preserved.

One fixture per corpus category so structural divergence in CSS classes and metadata shapes surfaces in unit tests, not at 3,574-act scale. Captured via `scripts/capture_fixtures.py` (rate-limited at 1 req/sec, idempotent — re-running skips files already on disk):

| Fixture | Category | Act | Why Selected |
|---------|----------|-----|--------------|
| `zop.html` | laws | Закон за обществените поръчки | Large law, many amendments, complex ПЗР; also used as the live-fixture integration anchor for every parser test |
| `zeu.html` | laws | Закон за електронното управление | Medium law, IT domain relevance |
| `gpk.html` | codes | Граждански процесуален кодекс | Code (кодекс), very large, deep nesting |
| `naredba-04-14.html` | ordinances | Наредба № 04-14 от 9 октомври 2019 г. | Modern наредба, exercises the Bulgarian month-name DV date form |
| `pravilnik-sadilishta.html` | regulations | Правилник за администрацията в съдилищата | Плaвилник (regulation) shape, distinct from "правилник по прилагане" |
| `ppz-aktsizi.html` | implementing | Правилник за прилагане на закона за акцизите и данъчните складове | Implementing regulation (правилник по прилагане), largest category-5 fixture |

A parametrized smoke test (`tests/fetcher/bg/test_cross_category.py`) runs the full pipeline — metadata parse → HTML-to-Markdown → file assembly — on all six fixtures and verifies rango, ELI prefix, slug generation, and frontmatter invariants per category.

Additional fixtures added as bugs are discovered (see Regression Policy below).

### Golden Files

Expected Markdown output for each HTML fixture, stored in `tests/fixtures/golden/`. Each golden file is the correct Markdown + YAML frontmatter that the parser should produce from the corresponding HTML fixture.

Golden files are manually reviewed and approved before being committed. They serve as the ground truth for parser correctness.

### No Mocking of lex.bg

Integration tests use real cached HTML responses, not mocked HTTP clients. This ensures tests exercise the actual HTML structure and encoding that the parser will encounter in production. The HTTP layer is replaced only at the transport level — a test harness serves fixtures from disk instead of making network requests.

### Live Tests

Rate-limited live tests that actually fetch from lex.bg are run only in CI nightly builds, not per-commit. These tests:

- Verify that lex.bg HTML structure has not changed (CSS classes still present).
- Compare a sample of fresh fetches against cached fixtures to detect site changes.
- Rate-limited to 1 request per second, with a maximum of 20 requests per nightly run.
- Failures in live tests trigger an alert but do not block the build — they indicate lex.bg changes that require parser updates.

---

## 4. Regression Policy

**Rule:** Every bug in parsing creates a new fixture + golden file pair.

When a parsing bug is discovered:

1. Save the HTML that triggered the bug as a new fixture in `tests/fixtures/html/`.
2. Manually produce the correct expected output and save it as a golden file in `tests/fixtures/golden/`.
3. Write a unit test that reproduces the bug using the new fixture.
4. Fix the parser.
5. Verify the fix produces output matching the golden file.
6. Commit the fixture, golden file, test, and fix together.

This ensures the test suite grows monotonically — every bug that was ever found is permanently guarded against regression. The fixture corpus becomes an increasingly comprehensive sample of lex.bg's structural diversity.
