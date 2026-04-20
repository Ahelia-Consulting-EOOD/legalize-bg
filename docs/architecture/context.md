# Architecture: System Context

**Arc42 Section 3 / C4 Level 1** | legalize-bg | Ahelia Consulting

---

## 3.1 System Context Diagram

```
                                 +-----------------------+
                                 |   Claude Code         |
                                 |   Sessions            |
                                 |   (primary consumer)  |
                                 +----------+------------+
                                            |
                                            | MCP protocol
                                            | get_law, search,
                                            | get_article, history, diff
                                            |
+-------------------+           +-----------v-----------+           +-------------------+
|                   |  HTTP GET |                       |  git ops  |                   |
|    lex.bg         +----------->                       +----------->    Git Corpus      |
|                   |  cp1251   |                       |  commit   |    (laws/, codes/  |
|  Bootstrap source |  ~1.2s/pg |     legalize-bg       |  per act  |     ordinances/,  |
|  + Validation     |           |                       |           |     regulations/,  |
|    oracle         <-----------+     Pipeline          <-----------+     implementing/) |
|                   |  Phase 4v |                       |  git show |                   |
+-------------------+  validate |                       |           +-------------------+
                                |                       |
+-------------------+           |                       |           +-------------------+
|                   |  HTTP GET |                       |  SQL R/W  |                   |
| dv.parliament.bg  +----------->                       +----------->   SQLite Index    |
|                   |  Tue/Fri  |                       |           |   (derived)       |
| Ongoing amendment |  gazette  |                       <-----------+                   |
| source            |  HTML/PDF |                       |  temporal |   law_versions    |
|                   |           +-----------+-----------+  queries  |   provisions      |
+-------------------+                       |                       |   amendments      |
                                            |                       +-------------------+
                                            | fetcher/bg/ interfaces
                                            | transformer, committer
                                            |
                                +-----------v-----------+
                                |                       |
                                |  Legalize Pipeline    |
                                |  (upstream ecosystem) |
                                |                       |
                                |  transformer/         |
                                |  committer/           |
                                |  CLI, CI/CD, state/   |
                                +-----------------------+
```

## 3.2 External Actors and Systems

### lex.bg (Ciela Norma AD)

- **Role:** Bootstrap data source (Phase 1a) and validation oracle (Phase 4v)
- **Interface:** HTTP GET to `https://lex.bg/laws/ldoc/{doc_id}` and `https://lex.bg/laws/tree/{category}/{page}`
- **Encoding:** windows-1251 (cp1251)
- **Response time:** ~1.2 seconds per page
- **Authentication:** None required (no cookies, no sessions, no special headers)
- **Rate limit:** None detected; self-imposed 1 req/sec
- **Catalog:** ~3,574 acts across 5 categories, discoverable via ~105 tree page requests
- **Limitation:** Serves only current consolidated text, no historical versions
- **Data provided:** Full HTML with semantic CSS classes (.Article, .Part, .Heading, .Section, .TitleDocument, .HistoryOfDocument)

### dv.parliament.bg (State Gazette)

- **Role:** Ongoing amendment source (Phase 3+)
- **Interface:** HTTP GET; gazette issues in HTML and PDF
- **Publication cadence:** Tuesday and Friday
- **Archive depth:** 4,101+ issues since 2003 (digital archive)
- **Data provided:** Raw gazette text containing ZID (amendment laws) with canonical ЗНА amendment phrases
- **Limitation:** No consolidation; raw amendment instructions only. Pre-2003 issues may be scanned PDFs requiring OCR.

### Legalize Pipeline (legalize-dev/legalize-pipeline)

- **Role:** Upstream ecosystem providing ~70% of needed infrastructure
- **Interface:** Python module interfaces -- `fetcher/bg/` must implement `LegislativeClient`, `NormDiscovery`, `TextParser`, `MetadataParser`
- **We reuse:** `transformer/markdown.py`, `transformer/frontmatter.py`, `transformer/slug.py`, `committer/`, CLI commands (`fetch`, `commit`, `bootstrap`, `daily`), CI/CD (`daily-update.yml`), `state/` resume, `config.yaml`
- **We build (not in Legalize):** MCP server, SQLite index, consolidation engine

### Claude Code Sessions

- **Role:** Primary consumers of the legislation corpus
- **Interface:** MCP protocol (JSON-RPC over stdio)
- **Tools consumed:** `get_law(name, date?)`, `search(query, category?)`, `get_article(law, article, date?)`, `history(law)`, `diff(law, date1, date2)`, `amendments_in_period(from, to)`
- **Quality needs:** Sub-second response, current law text, optional point-in-time queries

### Git Repository

- **Role:** Primary storage and temporal versioning system
- **Interface:** Standard git operations (commit, show, log, diff)
- **Structure:** One Markdown file per act; one commit per legislative event; `GIT_AUTHOR_DATE` set to DV publication date
- **Commit types:** `[bootstrap]`, `[reforma]`, `[nova]`, `[otmyana]`, `[popravka]`
- **Hosting:** `ahelia-consulting/legalize-bg` (GitHub, private; later upstream to legalize-dev)

### SQLite Index

- **Role:** Derived temporal query layer over the git corpus
- **Interface:** SQL queries from MCP server and pipeline tools
- **Tables:** `laws`, `law_versions`, `amendments`, `provisions`
- **Rebuild policy:** Fully rebuildable from git history; treated as a cache, not a source of truth

## 3.3 Data Flow Summary

| Flow | Source | Target | Data | Trigger |
|------|--------|--------|------|---------|
| Bootstrap scrape | lex.bg | Git corpus | Full HTML -> Markdown + YAML | One-time (Phase 1a) |
| Catalog discovery | lex.bg tree pages | Pipeline | Doc IDs + names + categories | One-time + periodic refresh |
| Validation check | lex.bg | Pipeline | Current consolidated HTML for diff | After each consolidation (Phase 4v) |
| Amendment detection | dv.parliament.bg | Pipeline | New gazette issues with ZID text | Tue/Fri poll (Phase 3) |
| Amendment application | Pipeline | Git corpus | Patched Markdown + `[reforma]` commit | Per detected amendment (Phase 4) |
| Index update | Git corpus | SQLite | Metadata + version records | After each commit |
| Law query | Claude Code | MCP server -> SQLite -> Git | Markdown text at point in time | On demand |
| Upstream contribution | Git corpus + fetcher/bg/ | Legalize pipeline | PR with country module | Phase 5 |
