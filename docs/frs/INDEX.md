# Future Requirements Index

**Product:** legalize-bg
**Date:** 2026-04-20
**Source:** [Design Document](../plans/2026-04-19-legalize-bg-design.md)

These are capabilities identified but NOT being built in the current phase. Each will be elaborated into a full requirement document when its phase begins.

---

| ID | Title | Phase | Priority | Status | Description |
|----|-------|-------|----------|--------|-------------|
| FR-001 | Temporal SQLite index | 2 | High | Backlog | Derived index over git history and YAML metadata enabling date-based law version lookup, provision tracking, and amendment cross-references. |
| FR-002 | DV gazette monitor | 3 | High | Backlog | Automated poller for dv.parliament.bg on Tue/Fri publication days; detects new ZID acts and flags target laws for consolidation. |
| FR-003 | ZID consolidation parser | 4 | High | Backlog | Regex-based parser for Bulgarian amendment instructions (ZNA-prescribed patterns); covers substitution, addition, deletion, renumbering, and repeal operations (~70-80% automation). |
| FR-004 | lex.bg validation oracle | 4v | High | Backlog | Post-consolidation validation pipeline that compares engine output against lex.bg current text; normalizes both, diffs, and flags non-trivial discrepancies for human review. |
| FR-005 | Legalize upstream contribution | 5 | Medium | Backlog | Package fetcher/bg/ as a PR to legalize-pipeline; pass 4 hard gates from ADDING_A_COUNTRY.md; integrate Bulgaria into daily CI matrix. |
| FR-006 | Sofia municipal ordinances | 6a | Medium | Backlog | Scrape ~30-50 active ordinances from council.sofia.bg, sofia.bg, and sofia.obshtini.bg; store under municipal/sofia/ with standard Markdown+YAML format. |
| FR-007 | National municipal coverage | 6b-c | Low | Backlog | Scale municipal scraping to top 10 cities (~200-300 acts), then all 265 municipalities (~5,300 acts); requires per-municipality parser adapters. |
| FR-008 | LLM fallback for complex ZID patterns | 4 (enhancement) | Medium | Backlog | LLM-assisted parsing for restructuring, table/annex changes, and ambiguous amendment instructions that regex cannot handle (~10-20% of ZID patterns). |
| FR-009 | Historical version reconstruction | 5+ | Low | Backlog | Reverse-apply amendments using .HistoryOfDocument DV references to reconstruct past law versions; re-commit with correct GIT_AUTHOR_DATE for full temporal coverage. |
| FR-010 | Municipal cross-reference index | 6+ | Low | Backlog | Index linking municipal ordinances to the national laws they implement (e.g., municipal tax ordinance to ZMDT); enables impact analysis when national law changes. |
| FR-011 | G2 triage of degenerate bootstrap acts | 5 (pre-gate) | Medium | Backlog | Manually review the ~128 acts flagged by bootstrap WARN logs (7 with empty titulo, 121 with null fecha_publicacion). For each: (a) drop with WAIVERS entry, (b) backfill from DV or parliament.bg sources, or (c) mark as deprecated. Required before G2 (frontmatter schema validation) can pass 100%. See `../data/canonical-data-model.md` §7. |
