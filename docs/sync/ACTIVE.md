# Active Work

**Current phase:** Phase 1b.1 — **complete on `main` 2026-05-09**.
**Current owner:** ekimir
**Started:** 2026-05-09 (design phase) → shipped same day after multi-batch executing-plans run.
**Next action:** Phase 1b.2 (structured backend hardening) — versioned JSON schemas published as `tools.json` + `mcp_server/schemas.py` dataclass freeze, error taxonomy formalized for downstream callers, soft perf assertions promoted to hard.

## Status

**Phase 1a** (national legislation corpus, 3,573 acts) — complete on `main`.

**Phase 1b.1** (MCP server) — complete on `main`:
- 3 tools (`get_law` / `search` / `get_article`) over FastMCP/stdio, accessible to Claude Code, Claude Desktop, OpenAI Codex.
- **221 tests passing** across unit, component, integration (FastMCP in-memory), real-corpus acceptance (§7.1/7.2/7.3), FTS regression, and soft perf-budget tiers (216 after the audit-gaps batch on 2026-05-09; 221 after the review-fixes commit added 5 parametrizations of the FTS5 user-input regression).
- Two formal code-review rounds; 18/18 findings addressed in-batch with zero deferrals (forward-looking items recorded as FR-012 through FR-017 in `docs/frs/INDEX.md` per Ahelia conventions).
- **Three** formal code-review rounds; the third (post-audit-gaps) surfaced 5 Important + 4 Minor findings, all closed in `docs/plans/2026-05-09-phase1b1-review-fixes.md` (FTS5 user-input allowlist regression, two `schema-reference.md` constraint mismatches the audit-fix itself introduced, a stale `runtime-flows.md` §6.3.4 predicate, and the duplicate Session Model gap). Phase 1b.1 docs and code are now publication-ready.
- SQLite catalog migrated to schema v4 with `provisions.text`, `laws_fts` virtual table, `idx_provisions_lookup`, and `law_versions.date_uncertain` columns.
- §7 data-quality semantics encoded as server-enforced contracts (D-026 error taxonomy with 8 codes; ambiguous-name candidates carry distinct identificadors; date_uncertain warning rides in successful responses).
- Operator runbook at `docs/runbook/2026-05-09-phase1b1-operator-setup.md`.
- Smoke-verified end-to-end: search/get_law/get_article all work against the live 3,573-act catalog. Build time 45 s. p95 latencies: get_law 3.4 ms, get_article 0.3 ms, search ~290 ms (soft warning on the "наредба" pathological query — FR-016 tracks the 1b.2 hardening).

**Phase 1b design** is recorded in `docs/plans/2026-05-09-phase1b-mcp-design.md`; D-020 through D-027 in `DECISIONS.md`.

## Blockers

None.

## Pending

- **Phase 1b.2** — structured backend hardening: publish `tools.json` schemas, formalize the error taxonomy for external callers, promote soft perf assertions to hard. The synonym/abbreviation dictionary described in FR-015 may land here or be split to 1b.3 depending on usage signal.
- **Phase 1b.3** — operator/end-user polish: structured logging + per-tool-call metrics, packaging, Bulgarian stemmer + legal-term synonym dictionary (FR-015), body-snippet rework (FR-017), pathological-query stop-words (FR-016).
- **Phase 2 temporal index** (FR-001) — strictly after Phase 1b completes. The 1b.1 `provisions` schema is built to support it without migration.
- **FR-011 G2 triage** of the ~128 degenerate acts (7 empty-titulo + 121 null-pub-date) — needed before Phase 5 upstream contribution; Phase 1b.1 surfaces these correctly so triage can proceed in parallel.

## Forward-looking items added in 1b.1 (FRS index)

- FR-012 — Phase 4 amendment-detection needs `body_text_minus_preamble` projection.
- FR-013 — Phase 1b.3 stemmer: adjective long-form definite article asymmetry.
- FR-014 — Phase 4 incremental rebuild path (vs current full DELETE-then-INSERT).
- FR-015 — Phase 1b.3 synonym dictionary + rang-aware re-ranking.
- FR-016 — Phase 1b.2 single-word category query stop-words.
- FR-017 — Phase 1b.3 body-snippet generation (currently title-snippet only for perf).
