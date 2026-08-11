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
  - **All 5 lex.bg BROWSABLE categories:** laws (~394), codes (~24), ordinances (~2,604), regulations (~490), implementing regs (~61) = ~3,574 total acts
    - **KNOWN COVERAGE GAP (D-049 / FR-025, finding 2026-07-02):** other act-types — ПМС, тарифи, инструкции, решения на МС, разпореждания, укази — are NOT covered. This is not silent: lex.bg exposes only the 5 browsable trees above; those act-types are not tree-enumerable there (`docs/research/2026-07-02-fr025-category-gap.md`). Sourcing is redirected to the ДВ acquisition layer (FR-024) with on-demand per-act capture as the interim posture; a comprehensive delegation-chain discovery is to be brainstormed. Until then this floor covers ONLY the 5 browsable categories, by documented limitation, not omission.
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

## Correctness floor

Added 2026-08-11 by Owner Directive 9. The completeness rule above governs **which acts are
in the corpus**; this section governs **whether what the corpus says about them is right**.
Both floors must hold. Meeting one does not offset the other.

- required floor: for every act in the corpus, all five properties hold.

  1. **No fabricated address.** Every emitted anchor is a provision *of this act* as printed in
     the source. Text quoted from another act, site chrome and markup remnants never yield an
     address. Reference defect: ЗЗД чл. 1001а, quoted Закон за гражданското съдопроизводство
     text served as a ЗЗД provision.
  2. **No lost address.** Every provision the act carries is addressable. Nothing is swallowed
     by paragraph flattening or collapsed by a dropped superscript index. Reference defects:
     the pre-Указ-883 unnumbered-alinea flattening (FR-034 Defect A, closed); ТЗ чл. 260и¹ and
     the ЗКПО Pillar-Two articles collapsing onto a base key (FR-035, open).
  3. **No ambiguous address.** One address resolves to exactly one text. Duplicate keys are a
     defect, and returning the first matching row is never a valid resolution.
  4. **No contaminated or truncated text.** The text at an address is complete and free of
     injected markup and site chrome. Reference defect: a parenthesised value read as an alinea
     marker, truncating the real provision mid-sentence.
  5. **No silent uncertainty.** Where the pipeline cannot decide deterministically, the address
     is either not emitted or emitted with a machine-readable uncertainty flag surfaced at
     *every* consumer surface. An unlabelled uncertain answer is an error; a labelled one is
     not. This is what makes the zero-error standard reachable rather than aspirational: the
     semantic classes (citation versus alinea, quoted versus own article) are provably beyond
     deterministic rules, so the standard is **no unlabelled wrong answer**.

- acceptance rule: a defect class is closed only when all four hold.
  1. Detection is corpus-wide and exhaustive, executed over every act, with no sampling.
  2. The check runs in CI on every change and hard-fails.
  3. The violation count is **zero**, or every remaining instance appears on a dated
     owner-signed waiver that enumerates the exact acts.
  4. The repair has been applied to the corpus and re-verified after the sweep.

- what counts as omission:
  - Sampling in place of full enumeration.
  - Generalising an adjudicated subset to the corpus.
  - Closing a class on a percentage or artifact rate rather than a count.
  - Any gate left in report-only mode.
  - Any defect known but unregistered.
  - Any uncertainty served without a flag.

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
- correctness floor verification artifact: a corpus-wide integrity check that runs over every
  act in CI and hard-fails on any violation of the five properties, plus, per defect class, the
  detection output enumerating every affected act. Percentages are not an accepted artifact.
