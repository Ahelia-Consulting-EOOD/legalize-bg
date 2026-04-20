# Architecture: Introduction and Goals

**Arc42 Section 1** | legalize-bg | Ahelia Consulting

---

## 1.1 System Purpose

legalize-bg is a data pipeline that converts Bulgarian legislation into machine-readable, temporally versioned Markdown files stored in git. It produces a corpus of ~3,574 normative acts (laws, codes, ordinances, regulations, implementing regulations) with full amendment history, enabling point-in-time reconstruction of any legislative text.

Bulgaria currently has no public API, no ELI identifiers, no Akoma Ntoso markup, and no machine-readable access to its legislation. Commercial portals (lex.bg/Ciela, APIS) hold a de facto monopoly on consolidated legal text. legalize-bg breaks this lock-in by bootstrapping from lex.bg, then tracking amendments independently via the State Gazette (Darzhaven Vestnik).

The system is designed as a Bulgarian country module for the Legalize ecosystem (legalize-dev), contributing `fetcher/bg/` upstream while hosting private extensions (MCP server, SQLite index, consolidation engine) under the Ahelia Consulting organization.

## 1.2 Key Stakeholders

| Stakeholder | Concern | How legalize-bg Addresses It |
|-------------|---------|------------------------------|
| **Claude Code sessions** | Fast, structured access to current Bulgarian law for legal skills (ZOP, contracts, rfp-response, legislative-draft) | MCP server with `get_law`, `search`, `get_article` tools; sub-second response from local git + SQLite |
| **Legal researchers** | Point-in-time "time machine" — see exactly how a law read on a specific date; track who changed what, when | Git history with `GIT_AUTHOR_DATE` per amendment; `history()` and `diff()` MCP tools; SQLite temporal index |
| **Legalize community** | Standard-compliant Bulgarian contribution; interoperable with 25-country ecosystem | SPEC.md compliance (8 mandatory YAML fields, commit message format); `fetcher/bg/` implementing 4 required interfaces |
| **Ahelia Consulting** | Reliable legal data foundation for procurement analysis and corruption research tooling | Automated freshness via DV monitor (Tue/Fri polling); validation against lex.bg as oracle |
| **Public interest** | Open access to Bulgarian legislation without commercial paywalls | Git corpus is the authoritative store; can be published openly after Legalize upstream merge |

## 1.3 Top Quality Goals

| Priority | Quality Goal | Scenario |
|----------|-------------|----------|
| **Q1** | **Data completeness** | The corpus contains all ~3,574 nationally applicable normative acts currently on lex.bg, with no missing acts and no truncated content. Every CSS-classified structural element (article, chapter, section, transitional provisions) is captured. |
| **Q2** | **Temporal accuracy** | For any law and any date after bootstrap, `get_law(name, date)` returns the exact text that was in force on that date. Each amendment commit carries the correct `GIT_AUTHOR_DATE` matching the DV publication date. The SQLite `law_versions` table has no gaps in `valid_from`/`valid_to` intervals. |
| **Q3** | **Legalize compatibility** | Every Markdown file passes Legalize quality gates: 8 mandatory YAML frontmatter fields (`titulo`, `identificador`, `pais`, `rango`, `fecha_publicacion`, `ultima_actualizacion`, `estado`, `fuente`), correct commit message format (`[bootstrap]`, `[reforma]`, etc.), and proper directory layout. The `fetcher/bg/` module implements all 4 required interfaces. |

## 1.4 Key Constraints

| Constraint | Type | Rationale |
|------------|------|-----------|
| **Markdown + YAML frontmatter** | Format | Legalize SPEC mandates this format across all 25 countries. No Akoma Ntoso, no custom XML. |
| **Git as primary storage** | Storage | Each legislative event is one commit with `GIT_AUTHOR_DATE`. Git history IS the temporal versioning system. The corpus is the single source of truth. |
| **Legalize SPEC compliance** | Standards | 8 mandatory YAML fields, 5 commit types (`[bootstrap]`, `[reforma]`, `[nova]`, `[otmyana]`, `[popravka]`), directory-per-category layout, and 4 fetcher interfaces. |
| **lex.bg rate limiting** | Operational | Self-imposed 1 req/sec ceiling. No rate limiting was detected, but robots.txt formally disallows non-search-engine bots. Cloudflare CDN is present and could begin blocking. Playwright kept as emergency fallback. |
| **windows-1251 encoding** | Technical | All lex.bg pages use cp1251. Must decode at fetch time and produce UTF-8 Markdown output. Encoding errors cause silent data corruption. |
| **DV publication cadence** | Temporal | State Gazette publishes Tuesday and Friday. Amendment detection cannot be faster than this. |
| **No lex.bg time machine** | Data availability | lex.bg serves only the current consolidated version. Historical reconstruction requires tracking DV amendments forward from the bootstrap snapshot, or reverse-engineering from `.HistoryOfDocument` metadata. |
