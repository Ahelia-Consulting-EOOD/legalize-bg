# Documentation Development Plan: legalize-bg

**Date:** 2026-04-20
**Status:** Draft — pending approval
**Purpose:** Bootstrap Ahelia documentation standard for legalize-bg before Phase 1a implementation begins
**Repo type:** data_pipeline_repo (standalone, not paired)
**Matrix column:** data/analytics repo (per software-documentation-standard.md §7)

---

## Classification Rationale

legalize-bg is a data pipeline that:
- Scrapes Bulgarian legislation from lex.bg (bootstrap) and dv.parliament.bg (ongoing)
- Transforms HTML to Markdown with YAML frontmatter per Legalize SPEC
- Stores legislation in git (one commit per amendment event) with SQLite index
- Exposes legislation via MCP server tools for Claude Code consumption
- Contributes upstream to the Legalize open-source ecosystem

Closest matrix column: **data/analytics repo** — data-heavy, tool interfaces, structured corpus production, agentic consumers.

---

## Documentation Surfaces

### Group A: Identity and Authority (no inter-file dependencies)

These files can be written in parallel. Content sources are identified.

| # | File | Standard ref | Content source |
|---|------|-------------|----------------|
| A1 | `README.md` | §5.1 | Design doc §Problem + §Architecture Decision |
| A2 | `.ahelia/repo-profile.yaml` | §5.11 | Classification from this plan + registry format from repos.yaml |
| A3 | `.ahelia/constraint-profile.yaml` | §5.11 | Rate limiting, encoding, Legalize SPEC, commit conventions |
| A4 | `.ahelia/protected-surfaces.yaml` | §5.11 | YAML schema, Legalize interfaces, MCP tool signatures |
| A5 | `docs/process/delivery-contract.md` | §5.3 | Legalize commit types, ADDING_A_COUNTRY.md 4 hard gates, review model |
| A6 | `docs/process/OWNER-DIRECTIVES.md` | §5.3 | HANDOVER.md "Decisions Already Made" section |
| A7 | `docs/process/COVERAGE-FLOOR.md` | §5.3 | Design doc §Phase Summary — all 6 phases, all 5 categories |
| A8 | `docs/process/IMPLEMENTATION-PREFLIGHT.md` | §5.3 | Protected surfaces: upstream PR, YAML schema, MCP interface |

### Group B: Product and Planning (depends on authority docs for scope)

| # | File | Standard ref | Content source |
|---|------|-------------|----------------|
| B1 | `docs/prd/legalize-bg-prd.md` | §5.2 | Design doc §Problem, §Research Summary, §Architecture Decision, §MCP Tools, §Phase Summary |
| B2 | `docs/frs/INDEX.md` | §5.2 | Design doc — features not in Phase 1a (consolidation engine, municipal, temporal queries) |
| B3 | `docs/plans/2026-04-19-legalize-bg-design.md` | §5.2 | Existing — remains as-is but scoped to phasing/sequencing |

### Group C: Architecture (depends on PRD for scope, can parallel with Group B)

| # | File | Standard ref | Content source |
|---|------|-------------|----------------|
| C1 | `docs/architecture/vision.md` | §5.4 | Design doc §Problem + §Architecture Decision |
| C2 | `docs/architecture/context.md` | §5.4 | Design doc §System Architecture — C4 context: lex.bg, DV, Legalize, MCP consumers, SQLite |
| C3 | `docs/architecture/container-view.md` | §5.4 | Design doc §System Architecture — catalog crawler, content fetcher, HTML→MD converter, MCP server, SQLite |
| C4 | `docs/architecture/data-model.md` | §5.4 | Design doc §Markdown File Format, §SQLite Index Schema, §Commit Message Format |
| C5 | `docs/architecture/runtime-flows.md` | §5.4 | Design doc — bootstrap flow (Phase 1a), amendment tracking flow (Phase 3-4), MCP query flow (Phase 1b) |

### Group D: Data and Schema (depends on architecture for structural context)

| # | File | Standard ref | Content source |
|---|------|-------------|----------------|
| D1 | `docs/data/canonical-data-model.md` | §5.7 | Design doc §Markdown File Format, §SQLite Index Schema — entities: Law, LawVersion, Amendment, Provision |
| D2 | `docs/data/schema-reference.md` | §5.7 | Design doc §YAML frontmatter (8 mandatory + 5 BG extension fields), §SQLite tables |

### Group E: Testing and Quality

| # | File | Standard ref | Content source |
|---|------|-------------|----------------|
| E1 | `docs/testing/test-strategy.md` | §5.8 | Design doc §Validation Against lex.bg, Legalize CI/CD gates, scraper reliability |

### Group F: Execution and Feedback (scaffolds — minimal content)

| # | File | Standard ref | Content source |
|---|------|-------------|----------------|
| F1 | `docs/sync/ACTIVE.md` | §5.10 | Current state: Phase 1a about to begin |
| F2 | `docs/sync/DECISIONS.md` | §5.10 | Seed from HANDOVER.md "Decisions Already Made" |
| F3 | `docs/sync/HANDOFFS/2026-04-19.md` | §5.10 | Move HANDOVER.md content here |

### Group G: Automation

| # | File | Standard ref | Content source |
|---|------|-------------|----------------|
| G1 | `.claude/CLAUDE.md` | §5.11 | Repo startup protocol, key file paths, quality gates, session rules |

### Deferred (not created now)

| File | Standard ref | Trigger |
|------|-------------|---------|
| `docs/architecture/security.md` | §5.9 | When deployed or when scraping becomes sensitive |
| `docs/ops/deployment-runbook.md` | §5.9 | When MCP server is deployed |
| `api/mcp-tools.yaml` | §5.5 | Phase 1b — MCP server implementation |
| `docs/data/entity-lifecycle.md` | §5.7 | Phase 4 — consolidation engine |
| `docs/data/retention-and-deletion.md` | §5.7 | Not applicable until production |

---

## Execution Strategy

**Mode:** Subagents (Mode B) — independent document creation, no inter-agent coordination needed.

### Wave 1: Authority + Identity (parallel)

All Group A files. These have no dependencies on each other.

| Agent | Files | Primary sources to read |
|-------|-------|------------------------|
| agent-identity | A1 (README.md), A2 (repo-profile.yaml) | Design doc, HANDOVER.md, repos.yaml template |
| agent-governance | A3 (constraint-profile), A4 (protected-surfaces), A5 (delivery-contract) | Design doc, HANDOVER.md, hardening templates |
| agent-authority | A6 (OWNER-DIRECTIVES), A7 (COVERAGE-FLOOR), A8 (IMPL-PREFLIGHT) | HANDOVER.md "Decisions Already Made", design doc §Phase Summary, hardening templates |

### Wave 2: Product + Architecture + Data (parallel, after Wave 1 review)

Groups B, C, D. These can run in parallel because:
- PRD extracts from design doc directly
- Architecture extracts from design doc directly
- Data model extracts from design doc directly
- Cross-references can be added in a final consistency pass

| Agent | Files | Primary sources to read |
|-------|-------|------------------------|
| agent-prd | B1 (PRD), B2 (FRS INDEX) | Design doc full, HANDOVER.md, Wave 1 authority docs |
| agent-arch | C1-C5 (all architecture) | Design doc §System Architecture + §Consolidation Engine + §Legalize Integration |
| agent-data | D1-D2 (data model + schema) | Design doc §Markdown File Format + §SQLite Index Schema + §ЗИД Pattern Taxonomy |

### Wave 3: Testing + Execution + Automation (parallel, after Wave 2 review)

Groups E, F, G.

| Agent | Files | Primary sources to read |
|-------|-------|------------------------|
| agent-testing | E1 (test-strategy) | Design doc §Validation, Legalize CI/CD, research R1 |
| agent-execution | F1-F3 (sync surfaces) | HANDOVER.md, design doc §Decision Points |
| agent-claude | G1 (CLAUDE.md) | All Wave 1+2 docs, design doc |

### Wave 4: Consistency review

Single-session review pass:
- Cross-check all documents for internal consistency
- Verify all cross-references resolve
- Verify authority docs don't contradict each other
- Verify CLAUDE.md points to correct file paths

---

## Quality Gates

1. Every document has a clear primary role (§3.1) — no document does double duty
2. Authority docs (A5-A8) use explicit, machine-checkable language where possible
3. PRD (B1) defines acceptance criteria, not just capabilities
4. Architecture (C1-C5) uses arc42/C4 structure, not free-form prose
5. Data model (D1-D2) separates conceptual model from physical schema
6. All content is sourced from design doc or research — no fabrication
7. HANDOVER.md content is fully migrated to proper surfaces — no orphaned information

---

## What the Design Doc Becomes After This

The design doc (`2026-04-19-legalize-bg-design.md`) remains in `docs/plans/` but its role narrows to **phase sequencing and effort estimation**. The content it currently holds will be decomposed:

| Design doc section | Migrates to |
|-------------------|-------------|
| §Problem Statement | PRD (B1) |
| §Research Summary | Stays — it's plan context |
| §Architecture Decision | Architecture vision (C1) + PRD rationale |
| §System Architecture | Container view (C3) |
| §Markdown File Format | Data model (D1), schema reference (D2) |
| §Commit Message Format | Delivery contract (A5) |
| §SQLite Index Schema | Schema reference (D2) |
| §MCP Server Tools | PRD (B1) — capability definition |
| §Consolidation Engine Design | Architecture runtime-flows (C5) + FRS (B2) |
| §Legalize Contribution Strategy | PRD (B1) + delivery contract (A5) |
| §Municipal Legislation Roadmap | FRS (B2) |
| §Phase Summary | Stays — this IS the plan |
| §Risk Register | PRD (B1) risk section |
| §References | Stays |

The design doc will NOT be modified during this doc dev session. It remains as the historical artifact that prompted the decomposition. Future sessions update the proper surfaces, not the design doc.
