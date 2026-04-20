# Product Requirements Document: legalize-bg

**Product:** legalize-bg -- Bulgarian Legislation as Code
**Owner:** Ahelia Consulting
**Date:** 2026-04-20
**Status:** Draft
**Source:** [Design Document](../plans/2026-04-19-legalize-bg-design.md)

---

## 1. Problem Statement

Bulgarian legislation is locked behind commercial portals (lex.bg, Ciela, APIS) with no public API, no compliance with international standards (no ELI, no Akoma Ntoso), and no machine-readable access. This creates four concrete unmet needs:

1. **Fast access** -- Claude Code legal skills (ZOP, contracts, rfp-response, legislative-draft) need programmatic access to current legislation. Today they operate without authoritative source text.
2. **Time machine** -- Corruption research in public procurement requires the ability to see exactly how a law (e.g. ZOP) read on a specific historical date, who loosened thresholds, and when.
3. **Freshness guarantees** -- Users need confidence that the legislation they are reading is up-to-date, with a known maximum staleness window.
4. **Municipal coverage** -- Municipal ordinances (наредби на общински съвети) are published only on individual municipal websites with no central registry. Sofia Municipality alone has ~30-50 active ordinances relevant to procurement, planning, and local taxation.

---

## 2. Users and Stakeholders

| User / Stakeholder | Role | Primary Need |
|---------------------|------|-------------|
| **Claude Code sessions** | Primary consumer | MCP tool access to legislation for legal skills |
| **Ahelia developers** | Builders and maintainers | Pipeline reliability, clear interfaces, testable components |
| **Legalize community** | Upstream ecosystem (legalize-dev) | Bulgaria country module (fetcher/bg/) conforming to SPEC.md |
| **Legal researchers** | End users via Claude Code | Temporal queries, amendment tracking, cross-law analysis |

---

## 3. Product Capabilities

### Capability 1: Full Corpus Access

All ~3,574 national legislative acts available as Markdown files with YAML frontmatter, stored in git.

**Acceptance Criteria:**
- All 5 categories covered: laws (~394), codes (~24), ordinances (~2,604), regulations (~490), implementing regulations (~61)
- Each file contains valid YAML frontmatter with the 8 mandatory Legalize SPEC fields (`titulo`, `identificador`, `pais`, `rango`, `fecha_publicacion`, `ultima_actualizacion`, `estado`, `fuente`)
- Markdown structure preserves semantic hierarchy: Part > Chapter > Section > Article > Paragraph
- All text correctly decoded from windows-1251 to UTF-8 with no corruption
- Git history contains one `[bootstrap]` commit per act

### Capability 2: MCP Tool Access

Claude Code can query legislation through MCP server tools: `get_law()`, `search()`, `get_article()`.

**Acceptance Criteria:**
- `get_law(name)` returns full Markdown text of named law
- `get_law(name, date)` returns the version valid at the specified date
- `search(query)` returns a ranked list of `{law_id, title, snippet}` across all acts
- `search(query, category)` filters results to one category
- `get_article(law, article)` returns the text of a single article (supports "14" and "14a")
- All tools respond within 2 seconds for single-law queries

### Capability 3: Temporal Queries

Users can view legislation at any historical date, compare versions, and list amendments in a period.

**Acceptance Criteria:**
- `history(law)` returns complete amendment history: `[{date, dv_issue, operation, commit}]`
- `diff(law, date1, date2)` returns a git diff between the law's state at two dates
- `amendments_in_period(from_date, to_date)` returns all amendments across all laws within the period
- Temporal index stored in SQLite, derived from git metadata and YAML frontmatter
- Date-based queries resolve to the correct git commit via the `law_versions` table

### Capability 4: Ongoing Freshness

Automated monitoring of Darzhaven Vestnik (DV) detects new amendments. The consolidation engine applies amendments to the Markdown corpus and commits changes.

**Acceptance Criteria:**
- DV poller checks dv.parliament.bg on Tuesday and Friday publication days
- New ZID (amendment acts) detected and logged within 48 hours of DV publication
- Consolidation engine parses ZID amendment instructions and applies them to target laws
- Each amendment committed as a `[reforma]` commit with correct `GIT_AUTHOR_DATE` and DV metadata
- Amendment detection latency: < 48 hours from DV publication

### Capability 5: Consolidation Validation

Engine output validated against lex.bg as an oracle to measure and maintain consolidation accuracy.

**Acceptance Criteria:**
- After consolidation, fetch the same law from lex.bg and compare
- Both texts normalized (whitespace, quotes, formatting) before comparison
- Non-trivial diffs flagged for human review
- Consolidation accuracy tracked over time with a target of > 95% agreement with lex.bg
- Validation results logged per law per amendment event

### Capability 6: Legalize Ecosystem Integration

The fetcher/bg/ module contributed upstream to legalize-pipeline, making Bulgaria part of the 25+ country Legalize ecosystem.

**Acceptance Criteria:**
- `fetcher/bg/` implements the 4 required interfaces: `LegislativeClient`, `NormDiscovery`, `TextParser`, `MetadataParser`
- Module passes all 4 Legalize hard gates (per ADDING_A_COUNTRY.md)
- PR submitted and merged to legalize-pipeline
- Bulgaria appears in Legalize CI daily-update matrix
- Commit messages follow Legalize conventions: `[bootstrap]`, `[reforma]`, `[nova]`, `[otmyana]`, `[popravka]`

### Capability 7: Municipal Coverage

Municipal ordinances starting with Sofia, then scaling to all 265 municipalities.

**Acceptance Criteria:**
- Sofia: all active ordinances (~30-50) scraped from council.sofia.bg, sofia.bg, sofia.obshtini.bg
- Stored under `municipal/sofia/` with same Markdown+YAML format
- Top 10 cities covered in second wave (~200-300 acts)
- Per-municipality parsers handle differing website structures
- Municipal acts include cross-references to national legislation where applicable

---

## 4. Success Metrics

| Metric | Target | Measurement Method |
|--------|--------|-------------------|
| Corpus completeness | 3,574 / 3,574 national acts | Count files in git by category |
| Consolidation accuracy | > 95% vs lex.bg | Automated diff after each consolidation run |
| MCP response time | < 2 seconds (single-law queries) | Instrumented tool latency |
| Amendment detection latency | < 48 hours from DV publication | Timestamp comparison: DV publish date vs commit date |
| Legalize integration | PR merged, CI green | GitHub PR status and CI dashboard |
| Municipal coverage (Sofia) | 30-50 ordinances | Count files under `municipal/sofia/` |

---

## 5. Data Sources

| Source | URL | Role | Access Method | Encoding |
|--------|-----|------|--------------|----------|
| **lex.bg** | lex.bg/laws/ldoc/{doc_id} | Bootstrap scrape + validation oracle | HTTP GET (server-rendered HTML) | windows-1251 |
| **dv.parliament.bg** | dv.parliament.bg | Ongoing amendment detection | HTTP polling (Tue/Fri) | UTF-8 |
| **Municipal websites** | council.sofia.bg, others | Municipal ordinances (Phase 6) | HTTP GET, per-site parsers | Varies |

Key findings from research:
- lex.bg requires no authentication, no Playwright, no cookies. All content is server-rendered.
- ~1.2s response time per page, no rate limiting detected (1 req/sec recommended).
- CSS classes are semantic (`.Article`, `.Part`, `.Heading`, `.Section`) -- ideal for parsing.
- At the national level, every act on lex.bg was published in DV. lex.bg adds consolidation, not new content.
- DV digital archive covers 4,101 issues since 2003.

---

## 6. Integration Requirements

### Legalize Pipeline Interfaces

The `fetcher/bg/` module must implement 4 interfaces defined by legalize-pipeline:

| Interface | File | Responsibility |
|-----------|------|---------------|
| `LegislativeClient` | `client.py` | HTTP access to lex.bg, cp1251 decoding |
| `NormDiscovery` | `discovery.py` | Tree page crawler, doc ID + name extraction |
| `TextParser` | `text_parser.py` | HTML to Legalize Block structure using CSS selectors |
| `MetadataParser` | `metadata.py` | Extract YAML frontmatter fields from HTML |

### Legalize SPEC Compliance

Every Markdown file must include these 8 mandatory YAML frontmatter fields:

| Field | Example | Description |
|-------|---------|-------------|
| `titulo` | "Закон за обществените поръчки" | Official title |
| `identificador` | "2136735703" | lex.bg document ID |
| `pais` | bg | ISO country code |
| `rango` | закон | Norm type (закон, кодекс, наредба, правилник) |
| `fecha_publicacion` | "2016-02-16" | First publication date |
| `ultima_actualizacion` | "2024-03-15" | Last amendment date |
| `estado` | vigente | Status (vigente = in force, derogado = repealed) |
| `fuente` | "lex.bg" | Data source |

### Legalize Commit Conventions

| Commit Type | Bulgarian Equivalent | Usage |
|-------------|---------------------|-------|
| `[bootstrap]` | -- | Initial scrape from lex.bg |
| `[reforma]` | ЗИД | Amendment act applied |
| `[nova]` | -- | New law published |
| `[otmyana]` | Отмяна | Full repeal |
| `[popravka]` | Поправка | Corrigendum |

---

## 7. Risks

| ID | Risk | Severity | Mitigation | Acceptance Criteria for Mitigation |
|----|------|----------|------------|-----------------------------------|
| R1 | Cloudflare starts blocking lex.bg scraping | Medium | Keep Playwright as emergency fallback; rate-limit to 1 req/sec | Playwright fallback tested and documented; scraper completes within 4 hours |
| R2 | ZID parser accuracy < 70% | Medium | LLM fallback for complex cases; human review for structural changes | Parser accuracy measured per ZID pattern type; LLM fallback covers restructuring and table/annex changes |
| R3 | Legalize project becomes inactive | Low | We own the data and pipeline; can operate independently | All pipeline components runnable without upstream dependencies |
| R4 | Municipal websites change structure | High | Per-municipality parsers with breakage monitoring | Automated tests detect parser failures within 24 hours; parser isolation limits blast radius |
| R5 | lex.bg changes HTML structure | Medium | CSS class selectors are semantic and stable; monitor for changes | Scraper includes structural assertions; alerts on class name changes |
| R6 | windows-1251 encoding causes data corruption | Low | Explicit cp1251 decode at fetch time; validate UTF-8 output | Post-scrape validation checks all files for valid UTF-8; Bulgarian character spot-checks |
| R7 | DV gazette text is unparseable (PDF/scanned) | Medium | Limit to post-2003 digital archive; OCR fallback for critical laws | Coverage limited to digital DV; OCR pipeline available for priority laws |

---

## 8. Out of Scope

The following are explicitly excluded from this product:

- **EU regulations** -- Published in the Official Journal of the EU, not in DV. Different legal system and access patterns.
- **Court decisions** -- Jurisprudence (case law) is a separate corpus with different structure and sources.
- **Private sector contracts** -- Not normative acts; not published in official sources.
- **Real-time notification** -- The system operates on a polling model (Tue/Fri DV check). Push notifications or webhooks for law changes are not planned.
- **Akoma Ntoso / LegalDocML** -- While the international gold standard, adopting it adds complexity without proportional benefit for our use case. Markdown+YAML is the Legalize ecosystem standard.
- **APIS Pravo integration** -- Commercial service (EUR 269/year) with its own consolidation. We use free public sources only.
