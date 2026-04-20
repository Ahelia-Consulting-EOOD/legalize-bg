# Decision Log

| ID | Date | Decision | Rationale | Status |
|----|------|----------|-----------|--------|
| D-001 | 2026-04-19 | Contribute to Legalize upstream (not fork) | Get ~70% infrastructure free (transformer, committer, git ops, CI/CD, CLI); Bulgaria joins 25-country ecosystem | Active |
| D-002 | 2026-04-19 | lex.bg = bootstrap only, DV = ongoing | Avoid ongoing scraping dependency; DV is the authoritative gazette source for forward tracking | Active |
| D-003 | 2026-04-19 | lex.bg = validation oracle | Compare consolidation engine output against lex.bg consolidated texts to measure accuracy | Active |
| D-004 | 2026-04-19 | Markdown + YAML format (not Akoma Ntoso) | Legalize ecosystem compatibility; entire ecosystem uses Markdown with YAML frontmatter | Active |
| D-005 | 2026-04-19 | Git + SQLite hybrid storage | Git for versioned text (each amendment = commit with GIT_AUTHOR_DATE); SQLite for temporal queries and indexing | Active |
| D-006 | 2026-04-19 | Municipal = Phase 6 | After national pipeline is stable; 265 municipalities each with different website structure | Active |
| D-007 | 2026-04-19 | Host at Ahelia-Consulting-EOOD | Private repo for MCP server, corruption research tooling, municipal pipeline; later upstream fetcher/bg/ to Legalize | Active |
| D-008 | 2026-04-20 | Repo type = data_pipeline_repo | Per Ahelia documentation standard classification | Active |
| D-009 | 2026-04-20 | Full governance pack adopted | OWNER-DIRECTIVES, COVERAGE-FLOOR, IMPLEMENTATION-PREFLIGHT governance documents | Active |
