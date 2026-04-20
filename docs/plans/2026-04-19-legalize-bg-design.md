# Design: legalize-bg — Bulgarian Legislation as Code

**Date:** 2026-04-19
**Status:** Approved
**Author:** Lead session (synthesized from 4-agent research team)
**Repository:** ahelia-consulting/legalize-bg (private, later upstream to legalize-dev)

---

## Problem Statement

Bulgarian legislation is locked behind commercial portals (lex.bg/Ciela, APIS) with no public API, no international standards compliance (no ELI, no Akoma Ntoso), and no machine-readable access. The user needs:

1. **Fast access** to current legislation for Claude Code legal skills (ZOP, contracts, rfp-response, legislative-draft)
2. **Time machine** for corruption research in public procurement — ability to see exactly how ЗОП changed on specific dates, who loosened thresholds, when
3. **Guarantees of freshness** — knowing the legislation is up-to-date
4. **Municipal legislation** coverage (Sofia Municipality first, then national)

---

## Research Summary

Four parallel research agents investigated the problem space (full reports in `/Users/ekimir/swprj/ccskills/lex/research/R1-R4`):

### R1: lex.bg Structure (Site Analyst)
- **Major finding:** Playwright is NOT needed. All content is server-rendered HTML accessible via simple HTTP GET. No SOAP auth, no cookies, no JS rendering required.
- ~3,574 acts across 5 categories (394 laws, 24 codes, 2,604 ordinances, 490 regulations, 61 implementing regs)
- Semantic CSS classes (`.Article`, `.Part`, `.Heading`, `.Section`) ideal for parsing
- windows-1251 encoding throughout
- No rate limiting detected. ~1.2s per page.
- No API, no sitemap, no legislation RSS

### R2: International Systems (Intl Researcher)
- Akoma Ntoso (OASIS LegalDocML) is the dominant standard — used by EU, UK, Italy, Africa
- ELI (European Legislation Identifier) is the EU standard for legislation URIs
- FRBR data model (Work/Expression/Manifestation) is the gold standard
- legislation.gov.uk uses 43-person editorial team for consolidation — not scalable for us
- Italy's Normattiva uses algorithmic consolidation — better model for our scale
- Bulgaria implements NONE of these standards
- 40 sources cited

### R3: BG Legislation Volume (Volume Analyst)
- Total plain text: ~150-200 MB; with metadata: ~500 MB-1 GB
- Storage cost is negligible (EUR 0-7/month)
- Initial crawl: ~2 hours at 1 req/sec
- APIS Pravo: EUR 269/year (has time machine, daily updates)
- dv.parliament.bg: 4,101 issues since 2003, free, but raw gazette only (no consolidation)
- LEX.BG and APIS are separate companies
- All national normative acts are published in DV — lex.bg adds consolidation, not new content

### R4: Text Consolidation (Consolidation Architect)
- Bulgarian ЗИД format is highly formulaic (prescribed by ЗНА) — 70-80% automatable with regex
- **Legalize project** (legalize-dev): 20 countries, 400K+ norms as Markdown in git, each reform as a commit. Bulgaria NOT covered.
- Legalize pipeline (Python): fetch → transform → commit architecture with 4 country-specific interfaces
- Recommended storage: hybrid git + SQLite index
- Recommended format: Markdown with YAML frontmatter
- DV reconstruction from scratch impractical — better to bootstrap from lex.bg, track forward
- 28 sources cited

---

## Architecture Decision

### Chosen Approach: Option A — Contribute to Legalize Ecosystem

**Rationale:**
- Legalize provides ~70% of needed infrastructure (transformer, committer, git ops, CI/CD, CLI)
- We write ~30% (fetcher/bg/ implementing 4 interfaces, MCP server, SQLite index, ЗИД parser)
- Bulgaria joins a 25-country ecosystem with 1,380+ stars and daily CI
- Ahelia repo hosts the private layer (MCP server, corruption research tooling, municipal pipeline)

### Strategic Roles of Data Sources

| Source | Role | When Used |
|--------|------|-----------|
| **lex.bg** | Bootstrap source + validation oracle | Phase 1 (initial scrape), Phase 4v (consolidation validation) |
| **dv.parliament.bg** | Ongoing amendment source | Phase 3+ (monitor Tue/Fri for new ЗИД) |
| **Consolidation engine** | Self-sufficient update pipeline | Phase 4+ (apply amendments to Markdown, commit to git) |
| **Municipal websites** | Municipal legislation source | Phase 6+ (Sofia first, then scale) |

### System Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                    ahelia-consulting/legalize-bg                  │
│                                                                  │
│  laws/                          # ~394 laws as Markdown          │
│  ├── zop.md                     # ЗОП — consolidated            │
│  ├── zeu.md                     # ЗЕУ                           │
│  └── ...                                                         │
│  codes/                         # ~24 codes                      │
│  ordinances/                    # ~2,604 наредби                 │
│  regulations/                   # ~490+ правилници               │
│  implementing/                  # ~61 правилници по прилагане    │
│  municipal/                     # Phase 6+                       │
│  ├── sofia/                                                      │
│  └── ...                                                         │
│                                                                  │
│  Each file: Markdown + YAML frontmatter                          │
│  Each commit: one amendment event with GIT_AUTHOR_DATE           │
│  Commit types: [bootstrap] [reforma] [nova] [otmyana] [popravka]│
└──────────────────────────────────────────────────────────────────┘
        │                              │
        ▼                              ▼
┌──────────────────┐      ┌──────────────────────────┐
│  SQLite Index    │      │  MCP Server (Claude Code) │
│  (derived)       │      │                          │
│  law_versions    │      │  get_law(name, date?)    │
│  provisions      │      │  search(query)           │
│  amendments      │      │  get_article(law, art)   │
│  dv_references   │      │  history(law)            │
│                  │      │  diff(law, date1, date2) │
└──────────────────┘      └──────────────────────────┘
        │
        ▼
┌──────────────────────────────────────────┐
│         Pipeline (Python)                │
│                                          │
│  fetcher/bg/                             │
│  ├── client.py        # HTTP to lex.bg   │
│  ├── discovery.py     # tree crawler     │
│  ├── text_parser.py   # HTML → Blocks    │
│  └── metadata.py      # → NormMetadata   │
│                                          │
│  consolidation/                          │
│  ├── zid_parser.py    # regex ЗИД parser │
│  ├── patcher.py       # apply amendments │
│  └── validator.py     # compare vs lex.bg│
│                                          │
│  monitor/                                │
│  ├── dv_poller.py     # poll Tue/Fri     │
│  └── amendment_detector.py               │
└──────────────────────────────────────────┘
```

### Markdown File Format

Following Legalize SPEC.md with Bulgarian adaptations:

```markdown
---
titulo: "Закон за обществените поръчки"
identificador: "2136735703"
pais: bg
rango: закон
fecha_publicacion: "2016-02-16"
ultima_actualizacion: "2024-03-15"
estado: vigente
fuente: "lex.bg"
# Bulgarian extensions
dv_issue: "13"
dv_year: 2016
effective_date: "2016-04-15"
category: laws
eli: "/eli/bg/закон/2016/2/16/zop/con"
amendment_history:
  - dv: "34/2016"
    date: "2016-05-03"
  - dv: "63/2017"
    date: "2017-08-04"
---

# ЗАКОН ЗА ОБЩЕСТВЕНИТЕ ПОРЪЧКИ

В сила от 15.04.2016 г.

## Част първа. ОСНОВНИ ПОЛОЖЕНИЯ

### Глава първа. ПРЕДМЕТ, ЦЕЛ И ПРИНЦИПИ

**Чл. 1.** (1) Този закон определя условията и реда за възлагане на обществени поръчки...
```

### Commit Message Format

Following Legalize SPEC.md:

```
[reforma] Закон за обществените поръчки

Source-Id: dv-63-2017
Source-Date: 2017-08-04
Norm-Id: 2136735703
```

Commit types mapped to Bulgarian legislative practice:
- `[bootstrap]` — initial scrape from lex.bg
- `[reforma]` — ЗИД (Закон за изменение и допълнение)
- `[nova]` — new law published for first time
- `[otmyana]` — full repeal (отмяна)
- `[popravka]` — corrigendum (поправка) in subsequent DV issue

### SQLite Index Schema

```sql
CREATE TABLE laws (
    law_id TEXT PRIMARY KEY,      -- "zop", "zeu", etc.
    doc_id INTEGER,               -- lex.bg doc ID (2136735703)
    title TEXT NOT NULL,
    category TEXT NOT NULL,       -- laws, codes, ordinances, regulations, implementing
    status TEXT DEFAULT 'vigente', -- vigente, derogado
    current_commit TEXT           -- HEAD commit hash for this file
);

CREATE TABLE law_versions (
    id INTEGER PRIMARY KEY,
    law_id TEXT REFERENCES laws(law_id),
    valid_from DATE NOT NULL,     -- effective date of this version
    valid_to DATE,                -- NULL = current version
    commit_hash TEXT NOT NULL,    -- git commit that created this version
    dv_issue TEXT,                -- "63/2017"
    dv_date DATE,
    amending_act TEXT             -- "ЗИД на ЗОП"
);

CREATE TABLE amendments (
    id INTEGER PRIMARY KEY,
    source_act TEXT NOT NULL,     -- the ЗИД or ПЗР that made the change
    target_law TEXT REFERENCES laws(law_id),
    operation TEXT NOT NULL,      -- substitution, addition, deletion, repeal, restructure
    affected_articles TEXT,       -- "чл. 14, ал. 1; чл. 20, ал. 1"
    dv_issue TEXT,
    dv_date DATE
);

CREATE TABLE provisions (
    id INTEGER PRIMARY KEY,
    law_id TEXT REFERENCES laws(law_id),
    article TEXT NOT NULL,        -- "1", "14а"
    paragraph TEXT,               -- "1", "2"
    valid_from DATE NOT NULL,
    valid_to DATE,
    text_hash TEXT                -- SHA256 of provision text for change detection
);

CREATE INDEX idx_versions_date ON law_versions(law_id, valid_from);
CREATE INDEX idx_amendments_target ON amendments(target_law, dv_date);
CREATE INDEX idx_provisions_article ON provisions(law_id, article, valid_from);
```

### MCP Server Tools

```python
# Phase 1b — basic access
get_law(name: str, date: str | None = None) -> str
    # Returns full law text as Markdown. If date provided, returns version at that date.

search(query: str, category: str | None = None) -> list[dict]
    # Full-text search across all laws. Returns [{law_id, title, snippet}]

get_article(law: str, article: str, date: str | None = None) -> str
    # Returns specific article text. Supports "чл. 14" or just "14".

# Phase 2 — temporal queries
history(law: str) -> list[dict]
    # Returns amendment history [{date, dv_issue, operation, commit}]

diff(law: str, date1: str, date2: str) -> str
    # Returns git diff of law between two dates

amendments_in_period(from_date: str, to_date: str) -> list[dict]
    # All amendments across all laws in a period

# Phase 6 — municipal
get_municipal_ordinance(municipality: str, name: str) -> str
```

---

## DV vs. lex.bg Coverage Analysis

| Content Type | In DV? | On lex.bg? | Our Source |
|-------------|--------|-----------|-----------|
| Laws (закони) | Yes | Yes (consolidated) | lex.bg bootstrap → DV ongoing |
| Codes (кодекси) | Yes | Yes (consolidated) | lex.bg bootstrap → DV ongoing |
| CoM ordinances (наредби на МС) | Yes | Yes (consolidated) | lex.bg bootstrap → DV ongoing |
| Regulations (правилници) | Yes | Yes (consolidated) | lex.bg bootstrap → DV ongoing |
| Implementing regs | Yes | Yes (consolidated) | lex.bg bootstrap → DV ongoing |
| Constitution | Yes | Yes | lex.bg bootstrap |
| EU regulations | No (OJ EU) | Partially | Out of scope |
| **Municipal ordinances** | **No** | **Partially** | **Municipal websites (Phase 6)** |
| Consolidated texts | **No** | **Yes** | lex.bg = validation oracle |

**Key finding:** At the national level, there is NO act on lex.bg that wasn't in DV. lex.bg adds consolidation and structured navigation, not new content.

---

## Consolidation Engine Design

### ЗИД Pattern Taxonomy

Bulgarian amendments follow ЗНА and use canonical phrases:

| Operation | Pattern | Frequency | Automation |
|-----------|---------|-----------|-----------|
| Substitution | `В чл. X, ал. Y думите „..." се заменят с „..."` | ~40% | Regex |
| Addition | `В чл. X се създава ал. Y: "..."` | ~25% | Regex |
| Deletion | `Член X се отменя` / `думите „..." се заличават` | ~15% | Regex |
| Renumbering | Cascading after insert/delete | ~8% | Logic |
| Restructuring | Move, split, merge articles/chapters | ~5% | LLM fallback |
| Full repeal | `Отменя се чл. X / закон Y` | ~3% | Regex |
| New chapter | `Създава се нов раздел Xa „..."` | ~3% | Regex |
| Table/annex | Changes to appendices, tariffs | ~1% | Manual |

**Estimated automation:** 70-80% with regex, 90%+ with LLM fallback, 100% requires human review for structural changes.

### Validation Against lex.bg

After consolidation engine produces a result:
1. Fetch current text from lex.bg for the same law
2. Normalize both (strip whitespace, normalize quotes)
3. Diff and report
4. If diff is non-trivial → flag for human review
5. Track validation accuracy over time

---

## Legalize Contribution Strategy

### Two-Path Approach

**Path A (Phase 5 — fast entry):**
- Bootstrap with current text as single `[bootstrap]` commit per law
- Track reforms going forward with proper `[reforma]` commits
- No historical versions initially (Korea model)
- Submit PR to legalize-pipeline with `fetcher/bg/`

**Path B (Phase 5+ — full compliance):**
- After consolidation engine works (Phase 4), reconstruct past versions
- Parse `.HistoryOfDocument` for all DV amendment references
- Apply amendments in reverse to reconstruct historical versions
- Re-commit with proper `GIT_AUTHOR_DATE` per reform
- Satisfies all Legalize quality gates

### Legalize Integration Points

| Legalize Component | We Reuse? | Notes |
|-------------------|-----------|-------|
| `transformer/markdown.py` | Yes | Generic Markdown rendering from Blocks |
| `transformer/frontmatter.py` | Yes | YAML generation |
| `transformer/slug.py` | Yes | Norm → filepath |
| `committer/` | Yes | Git ops with historical dates, idempotency |
| `CLI` (fetch/commit/bootstrap/daily) | Yes | Standard commands |
| `CI/CD` (daily-update.yml) | Yes | Cron Mon-Sat, parallel matrix |
| `state/` | Yes | Resume from last run |
| `config.yaml` | Yes | Per-country settings |
| MCP server | **No** — doesn't exist | We build this at Ahelia |
| SQLite index | **No** — doesn't exist | We build this at Ahelia |
| Consolidation engine | **No** — doesn't exist | We build this at Ahelia |

---

## Municipal Legislation Roadmap (Phase 6+)

### Landscape

- 265 municipalities, each with elected Municipal Council
- No central registry (per ЗНА чл. 37, published locally only)
- ~5,300 active municipal ordinances nationally (est. 20 per municipality)
- Each municipality has different website structure — no standard format

### Phased Approach

| Step | Scope | Source | Est. Acts | Effort |
|------|-------|--------|-----------|--------|
| 6a | Sofia | council.sofia.bg, sofia.bg, sofia.obshtini.bg | ~30-50 | 3-5 days |
| 6b | Top 10 cities | Plovdiv, Varna, Burgas, Ruse, Stara Zagora, Pleven, Sliven, Dobrich, Shumen, Pernik | ~200-300 | 5-10 days |
| 6c | All 265 municipalities | Individual municipal websites | ~5,300 | Ongoing |

### Directory Structure

```
municipal/
├── sofia/
│   ├── naredba-mestni-danatsi-i-taksi.md
│   ├── naredba-obshtestvenia-red.md
│   └── ...
├── plovdiv/
├── varna/
└── ...
```

---

## Phase Summary

| Phase | What | Source | Effort | Delivers |
|-------|------|--------|--------|----------|
| **1a** | Bootstrap: scrape 3,574 acts → Markdown + YAML → git | lex.bg | 2-3 days | Full corpus in git |
| **1b** | MCP server: get_law, search, get_article | Local git + SQLite | 1-2 days | Claude Code access |
| **2** | SQLite temporal index | Derived from git + metadata | 1 day | Date-based queries |
| **3** | DV monitor: poll Tue/Fri, detect ЗИД | dv.parliament.bg | 2-3 days | Automated updates |
| **4** | Consolidation engine: ЗИД parser + patcher | DV gazette text | 3-5 days | Self-sufficient pipeline |
| **4v** | Validation: compare vs lex.bg | lex.bg as oracle | 1 day | Consolidation accuracy |
| **5** | Legalize contribution: fetcher/bg/ + PR | Our pipeline | 4-7 days | In Legalize ecosystem |
| **6a** | Municipal: Sofia | council.sofia.bg + 2 portals | 3-5 days | Sofia ordinances |
| **6b-c** | Municipal: scale | 265 municipal websites | 10-20 days | National municipal coverage |

**Total estimated effort:** ~30-50 working days for full roadmap (Phases 1-6b).

---

## Risk Register

| Risk | Severity | Mitigation |
|------|----------|-----------|
| Cloudflare starts blocking lex.bg scraping | Medium | Keep Playwright as emergency fallback; rate-limit to 1 req/sec |
| ЗИД parser accuracy < 70% | Medium | LLM fallback for complex cases; human review for structural changes |
| Legalize project becomes inactive | Low | We own the data and pipeline; can operate independently |
| Municipal websites change structure | High | Per-municipality parsers; monitor for breakage |
| lex.bg changes HTML structure | Medium | CSS class selectors are semantic and stable; monitor for changes |
| windows-1251 encoding causes data corruption | Low | Explicit cp1251 decode at fetch time; validate UTF-8 output |
| DV gazette text is unparseable (PDF/scanned) | Medium | Limit to post-2003 digital archive; OCR fallback for critical laws |

---

## References

- R1: `/Users/ekimir/swprj/ccskills/lex/research/R1-lexbg-structure.md` (20 sources)
- R2: `/Users/ekimir/swprj/ccskills/lex/research/R2-international-systems.md` (40 sources)
- R3: `/Users/ekimir/swprj/ccskills/lex/research/R3-bg-volume-sources.md` (25 sources)
- R4: `/Users/ekimir/swprj/ccskills/lex/research/R4-consolidation-timemachine.md` (28 sources)
- Prior plan: `/Users/ekimir/swprj/ccskills/docs/plans/2026-03-26-legal-extraction-tool.md`
- Legalize SPEC: `github.com/legalize-dev/legalize/SPEC.md`
- Legalize pipeline: `github.com/legalize-dev/legalize-pipeline`
- Legalize contribution guide: `legalize-pipeline/ADDING_A_COUNTRY.md`
