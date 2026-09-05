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
  These definitions are canonical; Directive 2, the FR rows and the ledgers cite them. The decision
  procedure that derives the grade from the recorded states is section 4.2 of
  `docs/plans/2026-09-05-dv-graded-source-design.md`; `checks/provenance.py` implements it and
  property-tests every combination of its inputs, so the derivation is total by construction.
  Vocabulary: an event's `source` is `dv_html`, `dv_pdf`, `dv_offline` or `unlocated` (claimed by
  lex.bg, not found on the Gazette side; always `pending`); an event's `applied` state is
  `replayed`, `verified`, `not_incorporated` (a Gazette instruction that cannot be applied, recorded
  without changing the text, terminal, never blocking a grade, always warned) or `pending`; a base is
  `rebuilt`, `read` or `snapshot`, and a snapshot is `frozen` once the Directive 14 repair sweep and
  the FR-041 capture have run on it; a base whose promulgation is cited but not found on the Gazette
  side, or not cited at all, is `unlocated`; the base record persists `chain_scanned_through` (the
  last HTML-era issue the ДВ-side body scan covered for the act) and `chain_inherited_before` (the
  date before which the chain is inherited from lex.bg because the Gazette side has no materials
  list), so the derivation is checkable from the tree alone.
  1. **Grade A, ДВ-complete.** The base text is a Gazette HTML material rebuilt through the corpus
     write gate; the ДВ-side body scan has covered every HTML-era issue in the act's lifetime; every
     amendment event is a Gazette HTML material replayed by the engine or recorded `not_incorporated`
     (until the engine exists, only acts with no amendment events can hold A). Gate: the write gate
     accepts the text, the Phase 4 replay invariants pass, and the offline diff against the committed
     lex.bg snapshot has zero unadjudicated divergences; an act with open divergences is held in
     staging and is not a committed file.
  2. **Grade B, ДВ-audited.** The base text is a frozen lex.bg snapshot or a Gazette text read from
     an issue PDF; where the promulgated material is online (`dv_html`, or `dv_pdf` read by vision
     for the audit without replacing the base), the base structural audit (its address inventory
     appears in the text or is explained by a located event) has passed; the ДВ-side body
     scan has covered every HTML-era issue in the act's lifetime; every online Gazette event has been
     replayed, verified against the frozen snapshot's text hash, or recorded `not_incorporated`.
     Gate: the freeze, the audit, the scan and every event's recorded state.
  3. **Grade B-pending.** As B, but with at least one open item: an event `pending` (including every
     `unlocated` one), the body scan not yet complete, the promulgation `unlocated` or not cited, the
     base audit not yet passed, or the snapshot not yet frozen. The record enumerates the open items, the count of pending events and the
     estimated Gazette pages still to read. This is a grade in its own right, not the absence of one;
     most older acts hold it during the transition, and every act audited before the repair sweep
     runs holds it.
  4. **Grade C, pre-1989 base.** The promulgation or at least one event exists only offline. Every
     online event is still sourced and verified as for B, and the pending counter applies. Handled as
     a separate track.
  An act may carry a declared base date (`base.declared_at`, the UK 1991 model): Gazette events before
  it are listed as not carried, the act grades B at best on the rest, and the declaration is surfaced
  with the grade. **ДВ-anchored** means grade A or B. B-pending and C acts are not anchored, and
  lex.bg re-scrape remains permitted for them (Directive 2), except that a frozen snapshot is never
  re-scraped: a frozen act that receives a new Gazette event becomes B-pending on that event, stays
  frozen, and is served with a truthful `checked_through` until the engine replays it.
- acceptance rule: a grade is earned by gates, never assigned by source. An act's grade is the weakest
  link in its current text. A grade may rise only when the corresponding events have been sourced and
  replayed or verified clean and the base audited; it never rises by declaration.
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

- expected verification artifact: `docs/process/BOOTSTRAP-MANIFEST.md` (never produced for the 2026-04 bootstrap; `docs/sync/CORPUS-STATUS.json` and the FR-040 records check stand in) listing all acts processed, with per-category counts matching the floor (3,624 on 2026-09-05; live count in `docs/sync/CORPUS-STATUS.json`)
- expected review artifact: per-phase gate review confirming category counts, MCP tool functionality, and adjudicated divergence counts (D-060; percentages are diagnostics)
- waiver path: dated entry in `docs/process/WAIVERS.md` with owner sign-off, specifying which floor element is deferred and the remediation plan
- correctness floor verification artifact: a corpus-wide integrity check that runs over every
  act in CI and hard-fails on any violation of the five properties, plus, per defect class, the
  detection output enumerating every affected act. Percentages are not an accepted artifact.
