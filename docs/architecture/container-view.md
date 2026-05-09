# Architecture: Container View

**Arc42 Section 5 / C4 Level 2** | legalize-bg | Ahelia Consulting

---

## 5.1 Container Diagram

```
+===========================================================================+
|                        legalize-bg system boundary                         |
|                                                                           |
|  +------------------+    +------------------+    +---------------------+  |
|  | Catalog Crawler   |    | Content Fetcher  |    | HTML-to-Markdown    |  |
|  | (discovery.py)    +--->| (client.py)      +--->| Converter           |  |
|  |                   |    |                  |    | (text_parser.py)    |  |
|  | Crawls tree pages |    | HTTP GET + cp1251|    |                     |  |
|  | extracts doc IDs  |    | + BeautifulSoup  |    | CSS classes -->     |  |
|  +------------------+    +------------------+    | structured Markdown |  |
|                                                   +----------+----------+  |
|                                                              |             |
|  +------------------+                            +-----------v----------+  |
|  | Metadata Parser  |                            |                      |  |
|  | (metadata.py)    |<---------------------------+ Combined output:     |  |
|  |                  |                            | Markdown body +      |  |
|  | Extracts YAML    |                            | YAML frontmatter    |  |
|  | frontmatter      +--+                         +----------------------+  |
|  +------------------+  |                                                   |
|                         |  +-------------------------------------------+   |
|                         +->|            Git Corpus                      |  |
|                            |                                           |   |
|  +------------------+      |  laws/         ~394 laws as Markdown      |   |
|  | DV Monitor       |      |  codes/        ~24 codes                  |   |
|  | (monitor/)       +----->|  ordinances/   ~2,604 ordinances          |   |
|  |                  |      |  regulations/  ~490 regulations           |   |
|  | Polls Tue/Fri    |      |  implementing/ ~61 implementing regs     |   |
|  | Detects new ZID  |      |  municipal/    Phase 6+                   |   |
|  +------------------+      |                                           |   |
|                            |  One file per act, one commit per event   |   |
|  +------------------+      +---+---------------------------------------+   |
|  | Consolidation    |          |                                           |
|  | Engine           +----------+ writes [reforma] commits                  |
|  | (consolidation/) |          |                                           |
|  |                  |      +---v-----------------------------------+       |
|  | ZID parser +     |      |          SQLite Index                 |       |
|  | patcher +        |      |                                       |       |
|  | validator        |      |  laws | law_versions | amendments |   |       |
|  +------------------+      |  provisions                           |       |
|                            |                                       |       |
|                            |  Derived from git; temporal queries   |       |
|                            +---+-----------------------------------+       |
|                                |                                           |
|                            +---v-----------------------------------+       |
|                            |          MCP Server                   |       |
|                            |                                       |       |
|                            |  get_law | search | get_article |     |       |
|                            |  history | diff | amendments_in_period|       |
|                            |                                       |       |
|                            |  JSON-RPC over stdio to Claude Code   |       |
|                            +---------------------------------------+       |
+===========================================================================+
```

## 5.2 Container Details

### 1. Catalog Crawler

| Attribute | Value |
|-----------|-------|
| **Module** | `fetcher/bg/discovery.py` |
| **Implements** | Legalize `NormDiscovery` interface |
| **Responsibility** | Traverse lex.bg tree pages for all 5 categories, extract document IDs, names, and category metadata. Build a complete catalog of ~3,574 acts. |
| **Technology** | Python, `requests`, `BeautifulSoup` |
| **Inputs** | Category list (`laws`, `code`, `ords`, `regs`, `reg_laws`) |
| **Outputs** | List of `(doc_id: int, name: str, category: str)` tuples |
| **HTTP requests** | ~104 total (12 + 1 + 75 + 14 + 2 pages) |
| **Key detail** | Pagination is 0-based via `/laws/tree/{category}/{pageIndex}`. Each page has ~35 items. Doc IDs are signed 32-bit integers extracted from `href="/laws/ldoc/{id}"` links. `crawl_all` deduplicates doc IDs across categories (first-wins in iteration order laws → code → ords → regs → reg_laws) — `Конституция` appears on every tree page as a sidebar link, and a small number of acts appear in two related categories. Post-dedup yields 3,573 unique acts. |

### 2. Content Fetcher

| Attribute | Value |
|-----------|-------|
| **Module** | `fetcher/bg/client.py` |
| **Implements** | Legalize `LegislativeClient` interface |
| **Responsibility** | Fetch full HTML for a single normative act from lex.bg. Handle encoding, rate limiting, error recovery. |
| **Technology** | Python, `requests`, `BeautifulSoup` |
| **Inputs** | `doc_id: int` |
| **Outputs** | Parsed `BeautifulSoup` DOM of the law page |
| **Key details** | URL pattern: `https://lex.bg/laws/ldoc/{doc_id}`. Encoding: `resp.encoding = 'cp1251'`. Wrapped in `RateLimitedSession` which enforces: (a) global 1 req/sec ceiling shared between `HttpTransport` (doc pages) and `bootstrap.py:TreeTransport` (tree crawl) so the limit applies across the whole pipeline, not per-transport; (b) automatic retry on HTTP 429 / 5xx — up to 3 attempts with exponential backoff (2 / 4 / 8 s); (c) Cloudflare challenge detection (status 403/503 with markers like `"Just a moment"`, `challenge-platform`, `__cf_chl_`, `Attention Required! | Cloudflare`) raises `CloudflareChallenge` and halts the pipeline — do not attempt to bypass; (d) per-request INFO log line with URL, status, and elapsed ms; WARN on retries. No cookies, no headers, no auth required. Playwright kept as emergency fallback if Cloudflare starts blocking. |

### 3. HTML-to-Markdown Converter

| Attribute | Value |
|-----------|-------|
| **Module** | `fetcher/bg/text_parser.py` |
| **Implements** | Legalize `TextParser` interface |
| **Responsibility** | Convert parsed HTML DOM into structured Markdown using CSS class selectors. Map lex.bg's semantic classes to Markdown heading levels and formatting. |
| **Technology** | Python, `BeautifulSoup` |
| **Inputs** | `BeautifulSoup` DOM |
| **Outputs** | Markdown string (body only, no frontmatter) |
| **CSS-to-Markdown mapping** | |

| CSS Class | Markdown Output |
|-----------|----------------|
| `.TitleDocument` | `# TITLE` (H1) |
| `.PreHistory` | Italic line below title |
| `.Part` | `## Част ...` (H2) |
| `.Heading` | `### Глава ...` (H3) |
| `.Section` | `#### Раздел ...` (H4) |
| `.Article` | `**Чл. N.** (paragraph text)` |
| `.TransitionalFinalEdicts` | `## ПРЕХОДНИ И ЗАКЛЮЧИТЕЛНИ РАЗПОРЕДБИ` |
| `.HistoryOfDocument` | Excluded from body; consumed by Metadata Parser |

### 4. Metadata Parser

| Attribute | Value |
|-----------|-------|
| **Module** | `fetcher/bg/metadata.py` |
| **Implements** | Legalize `MetadataParser` interface |
| **Responsibility** | Extract YAML frontmatter fields from the HTML DOM. Produces both Legalize-mandatory fields and Bulgarian extension fields. |
| **Technology** | Python, regex for date/DV parsing |
| **Inputs** | `BeautifulSoup` DOM, category string |
| **Outputs** | `dict` of frontmatter fields (merged into YAML block by `transformer/frontmatter.py`) |
| **Mandatory Legalize fields (8)** | `titulo`, `identificador`, `pais` (always `bg`), `rango`, `fecha_publicacion`, `ultima_actualizacion`, `estado`, `fuente` (always `lex.bg`) |
| **Bulgarian extensions (5)** | `dv_issue`, `dv_year`, `effective_date`, `category`, `eli` |
| **Amendment history** | Parsed from `.HistoryOfDocument` → `amendment_history` list of `{dv, date}` entries |

### 5. Consolidation Engine

| Attribute | Value |
|-----------|-------|
| **Module** | `consolidation/` (`zid_parser.py`, `patcher.py`, `validator.py`) |
| **Phase** | Phase 4 |
| **Responsibility** | Parse ZID (amendment law) instructions using ЗНА-canonical phrases, apply patches to existing Markdown files, validate results against lex.bg. |
| **Technology** | Python, regex, optional LLM fallback for complex structural changes |

| Submodule | Role |
|-----------|------|
| `zid_parser.py` | Regex-based parser for 7 amendment operations (substitution ~40%, addition ~25%, deletion ~15%, renumbering ~8%, restructuring ~5%, full repeal ~3%, new chapter ~3%). Estimated 70-80% automation with regex alone. |
| `patcher.py` | Applies parsed amendment instructions to Markdown text. Handles article/paragraph targeting, text replacement, insertion, deletion. |
| `validator.py` | Fetches current text from lex.bg, normalizes both versions (strip whitespace, normalize quotes), diffs, and reports discrepancies. Non-trivial diffs flagged for human review. |

### 6. DV Monitor

| Attribute | Value |
|-----------|-------|
| **Module** | `monitor/` (`dv_poller.py`, `amendment_detector.py`) |
| **Phase** | Phase 3 |
| **Responsibility** | Poll dv.parliament.bg on Tuesday and Friday for new State Gazette issues. Detect ZID (amendment laws) that affect acts in the corpus. Feed detected amendments to the Consolidation Engine. |
| **Technology** | Python, `requests`, HTML/PDF parsing |
| **Inputs** | dv.parliament.bg gazette pages |
| **Outputs** | List of `(source_act, target_law, amendment_text)` for each detected ZID |

### 7. MCP Server

| Attribute | Value |
|-----------|-------|
| **Module** | Top-level MCP server module |
| **Phase** | Phase 1b.1 (3 tools shipped), Phase 2 (3 more tools — temporal) |
| **Responsibility** | Expose legislation corpus to Claude Code sessions via Model Context Protocol. |
| **Technology** | Python, MCP SDK, JSON-RPC over stdio |
| **Data sources** | SQLite index for lookups, `git show` for content retrieval |

| Tool | Signature | Phase | Description |
|------|-----------|-------|-------------|
| `get_law` | `(name: str, date: str?) -> GetLawResponse` | 1b.1 | Structured response: metadata fields (titulo, identificador, fecha_publicacion, ultima_actualizacion, dv_issue, dv_year, effective_date, eli, amendment_history, commit_hash) + body_markdown + optional `warnings` array. Date-qualified historical retrieval via `git show {commit}:{path}`. See D-024. |
| `search` | `(query: str, category: str?, limit: int = 20) -> list[SearchHit]` | 1b.1 | Full-text search with FTS5 + BM25 ranking + Bulgarian-aware `bg_normalize` pre-normalization. Each hit: `{law_id, identificador, title, category, title_snippet, relevance}`. The snippet is over the act's TITLE only (not body) — title-snippet runs in ~75 ms vs ~700 ms for body-snippet on the 3,573-act corpus; body-snippet generation is tracked as FR-017 for Phase 1b.3. The `relevance` score is the negated SQLite `bm25` (higher = better). Empty-titulo acts (§7.3) get `<doc_id=N>` substituted in `title` slot. `limit` defaults to 20 and is capped at 50 (defensive — FTS5 with very large limits can OOM on a million-row catalog; 50 is plenty for an LLM caller). See D-022. |
| `get_article` | `(law: str, article: str, date: str?) -> GetArticleResponse` | 1b.1 | Single article or alinea text via SQL lookup on `provisions` table (populated to alinea level from day one per D-023). Accepts `"чл. 14"`, `"14"`, `"чл. 14а"` (Cyrillic suffixes), `"чл. 14, ал. 2"`, `"14.2"`. Ranges `"чл. 14-16"` parse but only the first article is returned in 1b.1 — full range expansion tracked as FR-018. |
| `history` | `(law: str) -> list[VersionEntry]` | 2 | Amendment history: `[{date, dv_issue, operation, commit_hash}]`. Deferred to Phase 2 — depends on FR-001 temporal index. |
| `diff` | `(law: str, date1: str, date2: str) -> str` | 2 | Git diff of a law between two dates. Deferred to Phase 2 — depends on FR-001 temporal index. |
| `amendments_in_period` | `(from_date: str, to_date: str) -> list[AmendmentEntry]` | 2 | All amendments across all laws in a time range. Deferred to Phase 2 — depends on FR-001 temporal index. |

**Errors are first-class tool outputs**, not opaque transport failures. Eight stable codes returned as `ToolError(code, payload)` per D-026: `LAW_NOT_FOUND`, `AMBIGUOUS_NAME`, `NO_VERSION_AT_DATE`, `DATE_UNCERTAIN` (warning, rides in successful response), `INVALID_ARTICLE_SPEC`, `ARTICLE_NOT_FOUND`, `INDEX_STALE`, `INDEX_MISSING`. Each carries a structured payload the model can act on (suggestions, candidates, available_articles, etc.).

**Implementation reference:** see `docs/plans/2026-05-09-phase1b-mcp-design.md` for the full Phase 1b design — milestone split (1b.1/1b.2/1b.3 per D-027), components, data flow, error taxonomy, and testing strategy. The implementation plan (task-by-task) lives in `docs/plans/2026-05-09-phase1b-mcp-implementation.md`.

**Data-quality constraints (implementers, read this before Phase 1b):** post-bootstrap observations in [`../data/canonical-data-model.md` §7](../data/canonical-data-model.md) shape the tool behavior. In brief:

- §7.1 — `law_id` (filename slug) is NOT derivable from the title alone. Slug collisions ~5-10% of the corpus carry `-2/-3` suffixes; transliteration also drops information. `get_law(name)` must look up via SQLite (title → law_id) or accept `identificador` directly; it cannot hash-compute the path from `name`.
- §7.2 — ~3.4% of acts have null `fecha_publicacion`. Commits for these are dated at bootstrap run time (`Source-Date: unknown` in the body). `get_law(name, date=X)` and Phase-2 temporal tools must treat these as date-uncertain, not "published 2026". Returning "most recent" for a date query on such an act is preferable to silently excluding it.
- §7.3 — 7 acts have empty titulo. `search(query)` must surface them by `identificador` (doc_id) and show something recognizable in the result snippet instead of an empty title field.

### 8. SQLite Index

| Attribute | Value |
|-----------|-------|
| **Phase** | Phase 2 |
| **Responsibility** | Provide temporal query capabilities over the git corpus. Map dates to commit hashes, enable article-level search, track amendment metadata. |
| **Technology** | SQLite3 |
| **Tables** | `laws` (catalog), `law_versions` (temporal snapshots), `amendments` (change events), `provisions` (article-level tracking) |
| **Rebuild policy** | Fully derived from git history and YAML frontmatter. Can be dropped and rebuilt at any time. Not a source of truth. |
| **Key indexes** | `idx_versions_date(law_id, valid_from)`, `idx_amendments_target(target_law, dv_date)`, `idx_provisions_article(law_id, article, valid_from)` |

### 9. Git Corpus

| Attribute | Value |
|-----------|-------|
| **Location** | Repository root directories |
| **Responsibility** | Single source of truth for all legislation content and history. |
| **Technology** | Git |
| **Estimated size** | ~150-200 MB plain text; ~500 MB-1 GB with metadata |
| **Structure** | |

```
laws/           ~394 files    (закони)
codes/          ~24 files     (кодекси)
ordinances/     ~2,604 files  (наредби)
regulations/    ~490 files    (правилници)
implementing/   ~61 files     (правилници по прилагане)
municipal/      Phase 6+      (общински наредби)
```

| **File format** | Markdown with YAML frontmatter (per Legalize SPEC) |
| **Commit strategy** | One commit per legislative event. `GIT_AUTHOR_DATE` set to DV publication date. |
| **Commit types** | `[bootstrap]` (initial scrape), `[reforma]` (ZID amendment), `[nova]` (new law), `[otmyana]` (full repeal), `[popravka]` (corrigendum) |
