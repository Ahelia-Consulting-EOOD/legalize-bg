# Active Work

**Current phase:** Phase 1b.2 — **complete on `main` 2026-05-09**.
**Current owner:** ekimir
**Started:** 2026-05-09 (design phase) → shipped same day after multi-batch executing-plans run.
**Next action:** Phase 1b.3 (operator/end-user polish) OR Phase 2 (temporal index) — both are now unblocked. See "Pending" below.

## Status

**Phase 1a** (national legislation corpus, 3,573 acts) — complete on `main`.

**Phase 1b.1** (MCP server) — complete on `main`:
- 3 tools (`get_law` / `search` / `get_article`) over FastMCP/stdio, accessible to Claude Code, Claude Desktop, OpenAI Codex.
- **221 tests passing** across unit, component, integration (FastMCP in-memory), real-corpus acceptance (§7.1/7.2/7.3), FTS regression, and soft perf-budget tiers (216 after the audit-gaps batch on 2026-05-09; 221 after the review-fixes commit added 5 parametrizations of the FTS5 user-input regression).
- **Three formal code-review rounds; 27/27 findings closed**: 18 from Rounds 1–2 in-batch (forward-looking items recorded as FR-012 through FR-017 in `docs/frs/INDEX.md` per Ahelia conventions), and 9 from the third post-audit-gaps round closed in `docs/plans/2026-05-09-phase1b1-review-fixes.md` (FTS5 user-input allowlist regression; two `schema-reference.md` constraint mismatches the audit-fix itself introduced; a stale `runtime-flows.md` §6.3.4 predicate; the duplicate Session Model gap; four Minor doc/test polish items). Phase 1b.1 docs and code are publication-ready.
- SQLite catalog migrated to schema v4 with `provisions.text`, `laws_fts` virtual table, `idx_provisions_lookup`, and `law_versions.date_uncertain` columns.
- §7 data-quality semantics encoded as server-enforced contracts (D-026 error taxonomy with 8 codes; ambiguous-name candidates carry distinct identificadors; date_uncertain warning rides in successful responses).
- Operator runbook at `docs/runbook/2026-05-09-phase1b1-operator-setup.md`.
- Smoke-verified end-to-end: search/get_law/get_article all work against the live 3,573-act catalog. Build time 45 s. p95 latencies: get_law 3.4 ms, get_article 0.3 ms, search ~290 ms (soft warning on the "наредба" pathological query — FR-016 tracks the 1b.2 hardening).

**Phase 1b.2** (structured backend hardening) — complete on `main` 2026-05-09:
- **FR-016 closed** via the `QUERY_TOO_BROAD` reject path: single-word category queries (`наредба`, `закон`, `правилник`, `кодекс`, `постановление`) now short-circuit before FTS5 — the rejection runs in <1 ms instead of the 437 ms cold-call FTS5 ranking over 2,604 ordinances. 9th error code, additive per Surface 3.
- **D-027 closed**: `tests/perf/test_budgets.py` soft assertions promoted to hard via `_hard_assert(pytest.fail)`. New `tests/perf/test_cold_calls.py` adds first-user-hit coverage with fresh-connection-per-query. Shared `tests/perf/conftest.py` warmer keeps OS file cache hot across both files so the budgets measure SQLite/FTS5, not disk I/O.
- **`tools.json` published** (version 1.0.0) — full input/output JSON schemas for all 3 tools plus the 9-code error taxonomy. Source of truth: `mcp_server/export_tools.py`. CI parity test in `tests/mcp_server/test_export_tools.py` enforces no drift via `--check` mode.
- **Error taxonomy formalized**: `docs/api/error-codes.md` (humans) + `docs/api/error-codes.json` (machines), both at version 1.0.0, parity-tested against runtime `ERROR_CODES`.
- **Idempotency contract documented** in the runbook (read-only at request time; build path explicitly non-idempotent — FR-014 tracks the incremental rebuild).
- Test count: 221 → 244.

**Phase 1b design** is recorded in `docs/plans/2026-05-09-phase1b-mcp-design.md`; D-020 through D-028 in `DECISIONS.md`. Phase 1b.2 plan: `docs/plans/2026-05-09-phase1b2-hardening.md`.

## Blockers

None.

## Pending

- **Phase 1b.3** — operator/end-user polish: structured logging + per-tool-call metrics, packaging, Bulgarian stemmer + legal-term synonym dictionary (FR-015), body-snippet rework (FR-017), long-form definite-article stemming (FR-013).
  Note: FR-016 (pathological-query stop-words) was originally slated here but landed in 1b.2 via the `QUERY_TOO_BROAD` reject path.
- **Phase 2 temporal index** (FR-001) — strictly after Phase 1b completes. The 1b.1 `provisions` schema is built to support it without migration.
- **FR-011 G2 triage** of the ~128 degenerate acts (7 empty-titulo + 121 null-pub-date) — needed before Phase 5 upstream contribution; Phase 1b.1 surfaces these correctly so triage can proceed in parallel.

## Forward-looking items added in 1b.1 (FRS index)

- FR-012 — Phase 4 amendment-detection needs `body_text_minus_preamble` projection.
- FR-013 — Phase 1b.3 stemmer: adjective long-form definite article asymmetry.
- FR-014 — Phase 4 incremental rebuild path (vs current full DELETE-then-INSERT).
- FR-015 — Phase 1b.3 synonym dictionary + rang-aware re-ranking.
- FR-016 — Phase 1b.2 single-word category query stop-words.
- FR-017 — Phase 1b.3 body-snippet generation (currently title-snippet only for perf).
