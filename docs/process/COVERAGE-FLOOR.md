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
  - **All 5 lex.bg BROWSABLE categories:** laws, codes, ordinances, regulations, implementing regs. Count on 2026-09-05: 3,624 acts on disk (laws 399, codes 25, ordinances 2,645, regulations 495, implementing 60). The live count is published in `docs/sync/CORPUS-STATUS.json` and its agreement with the tree and with every declaring file is enforced by the records check (FR-040); the 2026-04 bootstrap estimate of about 3,574 is historical.
    - **KNOWN COVERAGE GAP (D-049 / FR-025, finding 2026-07-02):** other act-types — ПМС, тарифи, инструкции, решения на МС, разпореждания, укази — are NOT covered. This is not silent: lex.bg exposes only the 5 browsable trees above; those act-types are not tree-enumerable there (`docs/research/2026-07-02-fr025-category-gap.md`). Sourcing is redirected to the ДВ acquisition layer (FR-024) with on-demand per-act capture as the interim posture; a comprehensive delegation-chain discovery is to be brainstormed. Until then this floor covers ONLY the 5 browsable categories, by documented limitation, not omission.
  - **All 6 phases must eventually ship:** 1a, 1b, 2, 3, 4/4v, 5, 6a-6c
  - **MCP server** with at minimum: `get_law`, `search`, `get_article` tools (Phase 1b); extended with `history`, `diff`, `amendments_in_period` (Phase 2+); extended with `get_municipal_ordinance` (Phase 6)
    - **Phase scoping (per D-027):** Phase 1b.1 ships exactly 3 tools (`get_law`, `search`, `get_article`); Phase 2 adds the other 3 (`history`, `diff`, `amendments_in_period`) once the temporal index (FR-001) is populated. The `get_municipal_ordinance` tool is Phase 6.
  - **SQLite temporal index** covering all acts with tables: `laws`, `law_versions`, `amendments`, `provisions`
  - **Consolidation engine** for ongoing ДВ amendments: ЗИД parser lowering the enumerated amendment grammar into the 4-operation kernel (replace, insert, repeal, text_replace), with renumbering, restructuring, full repeal and new-chapter forms handled as elaborations that lower to the kernel (D-060)
  - **Validation pipeline** comparing engine output against the witnesses (lex.bg, Ministry of Justice portal), adjudicating every divergence into a lane with the Gazette as arbiter (D-061)
  - **YAML frontmatter** on every act with all 8 mandatory Legalize SPEC fields plus Bulgarian extensions

- acceptance rule: coverage is met when every category has zero acts silently dropped, every phase has shipped or has a documented waiver, and every MCP tool listed above is functional.

- what counts as omission:
  - Skipping an entire lex.bg category (e.g., omitting implementing regs)
  - Dropping individual acts silently during bootstrap (every act must be accounted for -- converted or listed in a skip manifest with reason)
  - Shipping MCP server without `search` tool
  - Skipping witness validation (Phase 4v)
  - Omitting a phase from the roadmap without a dated waiver
  - Deploying the consolidation engine with any enumerated grammar form that neither lowers to the kernel nor flags (D-060; this supersedes the former list of 7 operation types, which conflicted with FR-003's 5 and the ratified 4-operation kernel)

## Correctness floor

Added 2026-08-11 by Owner Directive 9. The completeness rule above governs **which acts are
in the corpus**; this section governs **whether what the corpus says about them is right**.
Both floors must hold. Meeting one does not offset the other.

- required floor: for every act in the corpus, all five properties hold.

  1. **No fabricated address.** Every emitted anchor is *licensed*: it traces either to the act's
     own promulgated text, or to exactly one applied amendment operation whose target address
     resolved. Text quoted from another act, site chrome and markup remnants never yield an
     address. Reference defect: ЗЗД чл. 1001а, quoted Закон за гражданското съдопроизводство
     text served as a ЗЗД provision.

     *Why "licensed" and not "as printed in the source":* under lex.bg the corpus photographs an
     already-consolidated page, so faithfulness to the source is the whole test. Under ДВ the
     corpus **constructs** the consolidated text, and a newly inserted чл. 5а is correct precisely
     because no source prints it yet. A source-fidelity wording would make this property
     unsatisfiable the day the source changes, so it is stated on the licence for the address
     instead. Both readings coincide for lex.bg-sourced text.
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

## Provenance floor

Added 2026-09-05 by Owner Directive 2 as amended (D-059). The completeness floor says which acts are
in the corpus and the correctness floor says whether their addresses are right; this floor says
**where each text came from and how far that origin has been verified**.

- required floor: every act carries a machine-readable provenance grade and every amendment event a
  source class, both surfaced at every consumer surface (frontmatter, index, MCP, REST, cf-plane).
  1. **Grade A, ДВ-complete.** Base text and every amendment event come from Gazette HTML materials;
     the replay passes the Phase 4 invariants; unadjudicated witness divergences are zero.
  2. **Grade B, ДВ-audited snapshot.** Base text is a lex.bg snapshot; every Gazette event since the
     HTML era is replayed or verified; events from the 1989 to 2004 PDF era are read from the issue
     PDFs by vision and applied, and the grade records how many of them still are not.
  3. **Grade C, pre-1989 base.** The origin or some events exist only offline. The base is a lex.bg
     snapshot that cannot be verified against the Gazette online. Handled as a separate track.
- acceptance rule: a grade is earned by gates, never assigned by source. An act's grade is the weakest
  link in its current text. A grade may rise only when the corresponding events have been sourced and
  replayed clean; it never rises by declaration.
- what counts as omission:
  - An act without a grade, or a grade not derivable from its recorded events.
  - Serving a grade B or C text without the grade at the consumer surface.
  - Raising a grade without the sourcing that the grade definition requires.
- verification artifact: the coverage map (per act, per event: Gazette HTML available, PDF only, or
  not online) and the per-act grade derivation, both regenerated by the pipeline.

## Priority ordering

This section is only for sequencing. It does NOT weaken the coverage floor.

- implement first: Phase 1a (bootstrap scrape) and Phase 1b (MCP server) -- delivers immediate Claude Code access to legislation
- implement second: Phase 2 (temporal index), Phase 3 (DV monitor), Phase 4/4v (consolidation + validation) -- delivers self-sufficient pipeline
- implement third: Phase 5 (Legalize upstream contribution) -- delivers ecosystem integration
- implement last: Phase 6a-6c (municipal legislation, Sofia first) -- requires stable national pipeline per Owner Directive 6. Phase 6 Definition of Done criteria will be documented in the delivery contract when the phase begins.

## Evidence

- expected verification artifact: `docs/process/BOOTSTRAP-MANIFEST.md` listing all acts processed, with per-category counts matching the floor (3,624 on 2026-09-05; live count in `docs/sync/CORPUS-STATUS.json`)
- expected review artifact: per-phase gate review confirming category counts, MCP tool functionality, and validation accuracy metrics
- waiver path: dated entry in `docs/process/WAIVERS.md` with owner sign-off, specifying which floor element is deferred and the remediation plan
- correctness floor verification artifact: a corpus-wide integrity check that runs over every
  act in CI and hard-fails on any violation of the five properties, plus, per defect class, the
  detection output enumerating every affected act. Percentages are not an accepted artifact.
