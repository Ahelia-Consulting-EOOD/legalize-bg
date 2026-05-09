# Active Work

**Current phase:** Phase 1b.1 (MCP server, polished — workflows A+B) — design approved, awaiting implementation plan
**Current owner:** ekimir
**Started:** 2026-05-09 (design phase)
**Next action:** Invoke `superpowers:writing-plans` to produce `docs/plans/2026-05-09-phase1b-mcp-implementation.md`. After approval, execute task-by-task per the Phase 1a precedent.

## Status

Phase 1a (national legislation corpus, 3,573 acts) is complete and on `main`.

Phase 1b design is complete:
- Brainstorming done across 5 sections (architecture / components / data flow / errors+§7 semantics / testing).
- Design recorded in `docs/plans/2026-05-09-phase1b-mcp-design.md`.
- Eight new decisions logged: D-020 through D-027 in `DECISIONS.md`.
- Container-view §7 and runtime-flows §6.3 updated to reflect the firmer details.
- Phase 1b is a **three-mandatory-milestone plan** per D-027:
  - **1b.1** — all three tools (`get_law`, `search`, `get_article`) polished end-to-end. Workflows A (legal research / article precision) and B (drafting / review companion) covered. FastMCP server (stdio); SQLite index with FTS5 + Bulgarian-aware `bg_normalize`; `provisions` populated to article AND alinea level from day one; structured (typed-dict) responses; `index/migrations.py`; §7.1-7.3 data-quality semantics enforced; error taxonomy with all 8 codes.
  - **1b.2** — workflow C (structured backend hardening): versioned JSON schemas, error taxonomy formalized, idempotency contract, performance regression tests promoted from soft to hard assertions.
  - **1b.3** — operator/end-user polish: structured logging + per-tool-call metrics, packaging (`pip install legalize-bg-mcp`), deployment docs, Claude Code/Desktop/Codex setup guides, Bulgarian stemmer + legal-term synonym dictionary (deferred from 1b.1 per usage data per D-022).

## Blockers

None.

## Pending

- **`superpowers:writing-plans`** — produce the implementation plan (the executable artifact, task-by-task, file-by-file, TDD step by step).
- **Phase 1b.1 implementation** — execute the plan once approved.
- **Phase 1b.2 + 1b.3** — sequential after 1b.1 ships.
- **Phase 2 temporal index** (FR-001) — strictly after Phase 1b completes. The 1b.1 `provisions` schema is built to support it without migration.
- **FR-011 G2 triage** of the ~128 degenerate acts (7 empty-titulo + 121 null-pub-date) — needed before Phase 5 upstream contribution; Phase 1b.1 surfaces these correctly so triage can proceed in parallel.
