# Coverage Floor

This file defines what must eventually be covered with no silent omissions.

## Scope

- capability: Bulgarian national legislation corpus + MCP access layer
- owner: ekimir
- effective date: 2026-04-19

## Authoritative source

- primary source: `docs/plans/2026-04-19-legalize-bg-design.md` -- Phase Summary table and DV vs lex.bg Coverage Analysis
- secondary sources: R1 (lex.bg structure, act counts), R3 (volume estimates), HANDOVER.md

## Completeness rule

- required floor:
  - **All 5 lex.bg categories:** laws (~394), codes (~24), ordinances (~2,604), regulations (~490), implementing regs (~61) = ~3,574 total acts
  - **All 6 phases must eventually ship:** 1a, 1b, 2, 3, 4/4v, 5, 6a-6c
  - **MCP server** with at minimum: `get_law`, `search`, `get_article` tools (Phase 1b); extended with `history`, `diff`, `amendments_in_period` (Phase 2+); extended with `get_municipal_ordinance` (Phase 6)
    - **Phase scoping (per D-027):** Phase 1b.1 ships exactly 3 tools (`get_law`, `search`, `get_article`); Phase 2 adds the other 3 (`history`, `diff`, `amendments_in_period`) once the temporal index (FR-001) is populated. The `get_municipal_ordinance` tool is Phase 6.
  - **SQLite temporal index** covering all acts with tables: `laws`, `law_versions`, `amendments`, `provisions`
  - **Consolidation engine** for ongoing DV amendments: ZID parser + patcher covering substitution, addition, deletion, repeal, renumbering, restructuring, new chapter operations
  - **Validation pipeline** comparing engine output against lex.bg consolidated text, with diff reporting and human-review flagging for non-trivial discrepancies
  - **YAML frontmatter** on every act with all 8 mandatory Legalize SPEC fields plus Bulgarian extensions

- acceptance rule: coverage is met when every category has zero acts silently dropped, every phase has shipped or has a documented waiver, and every MCP tool listed above is functional.

- what counts as omission:
  - Skipping an entire lex.bg category (e.g., omitting implementing regs)
  - Dropping individual acts silently during bootstrap (every act must be accounted for -- converted or listed in a skip manifest with reason)
  - Shipping MCP server without `search` tool
  - Skipping validation against lex.bg (Phase 4v)
  - Omitting a phase from the roadmap without a dated waiver
  - Deploying consolidation engine without covering all 7 ZID operation types (substitution, addition, deletion, renumbering, restructuring, full repeal, new chapter)

## Priority ordering

This section is only for sequencing. It does NOT weaken the coverage floor.

- implement first: Phase 1a (bootstrap scrape) and Phase 1b (MCP server) -- delivers immediate Claude Code access to legislation
- implement second: Phase 2 (temporal index), Phase 3 (DV monitor), Phase 4/4v (consolidation + validation) -- delivers self-sufficient pipeline
- implement third: Phase 5 (Legalize upstream contribution) -- delivers ecosystem integration
- implement last: Phase 6a-6c (municipal legislation, Sofia first) -- requires stable national pipeline per Owner Directive 6. Phase 6 Definition of Done criteria will be documented in the delivery contract when the phase begins.

## Evidence

- expected verification artifact: `docs/process/BOOTSTRAP-MANIFEST.md` listing all acts processed, with per-category counts matching the floor (~3,574 total)
- expected review artifact: per-phase gate review confirming category counts, MCP tool functionality, and validation accuracy metrics
- waiver path: dated entry in `docs/process/WAIVERS.md` with owner sign-off, specifying which floor element is deferred and the remediation plan
