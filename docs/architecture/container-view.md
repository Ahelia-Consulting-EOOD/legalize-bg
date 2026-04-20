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
| **HTTP requests** | ~105 total (12 + 1 + 75 + 14 + 2 pages) |
| **Key detail** | Pagination is 0-based via `/laws/tree/{category}/{pageIndex}`. Each page has ~35 items. Doc IDs are signed 32-bit integers extracted from `href="/laws/ldoc/{id}"` links. |

### 2. Content Fetcher

| Attribute | Value |
|-----------|-------|
| **Module** | `fetcher/bg/client.py` |
| **Implements** | Legalize `LegislativeClient` interface |
| **Responsibility** | Fetch full HTML for a single normative act from lex.bg. Handle encoding, rate limiting, error recovery. |
| **Technology** | Python, `requests`, `BeautifulSoup` |
| **Inputs** | `doc_id: int` |
| **Outputs** | Parsed `BeautifulSoup` DOM of the law page |
| **Key details** | URL pattern: `https://lex.bg/laws/ldoc/{doc_id}`. Encoding: `resp.encoding = 'cp1251'`. Self-imposed rate limit: 1 req/sec via `time.sleep()`. No cookies, no headers, no auth required. Playwright kept as emergency fallback if Cloudflare starts blocking. |

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
| **Phase** | Phase 1b (basic), Phase 2 (temporal) |
| **Responsibility** | Expose legislation corpus to Claude Code sessions via Model Context Protocol. |
| **Technology** | Python, MCP SDK, JSON-RPC over stdio |
| **Data sources** | SQLite index for lookups, `git show` for content retrieval |

| Tool | Signature | Phase | Description |
|------|-----------|-------|-------------|
| `get_law` | `(name: str, date: str?) -> str` | 1b | Full law text as Markdown. If `date` provided, returns version at that date via `git show {commit}:{path}`. |
| `search` | `(query: str, category: str?) -> list[dict]` | 1b | Full-text search. Returns `[{law_id, title, snippet}]`. |
| `get_article` | `(law: str, article: str, date: str?) -> str` | 1b | Single article text. Accepts `"чл. 14"` or `"14"`. |
| `history` | `(law: str) -> list[dict]` | 2 | Amendment history: `[{date, dv_issue, operation, commit}]`. |
| `diff` | `(law: str, date1: str, date2: str) -> str` | 2 | Git diff of a law between two dates. |
| `amendments_in_period` | `(from_date: str, to_date: str) -> list[dict]` | 2 | All amendments across all laws in a time range. |

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
