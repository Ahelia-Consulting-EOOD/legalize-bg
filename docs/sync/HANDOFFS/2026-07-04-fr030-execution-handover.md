# Handover: FR-030 alinea/citation discriminator — ready to execute (2026-07-04)

**From:** the session that shipped FR-031 (remote MCP, merged PR #10) and then
brainstormed + designed + planned FR-030.
**To:** a fresh execution session. This is a clean start — everything you need is
committed; nothing is in flight.

## State
- FR-031 (remote MCP transport, Phase A/B) is **merged to `main`** (PR #10).
- FR-030 is **planned, not started.** Design and plan are committed:
  - Design: `docs/plans/2026-07-04-fr030-alinea-citation-discriminator-design.md`
  - Plan: `docs/plans/2026-07-04-fr030-alinea-citation-discriminator-plan.md`
- `main` is clean; `catalog.db` is the current (pre-fix) build.

## What FR-030 is (one paragraph)
`index/provisions.py` parses parenthesised citation numbers (`чл. 8 (3)`,
`четири (4)`, treaty/standard/grade refs) as alinea markers, creating bogus
`provisions` rows. An empirical scan + vision inspection (captured in the design
doc §2) proved the fix is a **hybrid discriminator**: a `(N)` opens an alinea
only if it (1) continues the contiguous sequence AND (2) isn't in a
citation-context (preceding token is a digit/Roman/cross-ref/cardinal word). The
problem is general (~600+ markers corpus-wide), not the 8 originally-documented
rows.

## How to execute
1. Read the design doc, then the plan.
2. Execute the plan **task-by-task under `superpowers:subagent-driven-development`**
   (the plan header requires it). 4 tasks: (1) citation guard, (2) discriminator,
   (3) full-corpus rebuild validation, (4) governance.
3. **Standing rule (owner):** after each task goes green, run the per-task
   review loop — fresh-subagent code review → `receiving-code-review` → fix →
   re-review until clean — before advancing. (Memory:
   `per-task-fresh-subagent-review-loop`.)

## The one thing that needs judgment, not just code
**Task 3 is the real gate.** After rebuilding the catalog with the new parser,
diff the alinea rows before/after and **vision-verify (Claude at orchestration
time — no external OCR) that no removed marker was a real alinea.** The design
carries a known residual: a semantic citation that both continues the sequence
and lacks a structural preceding token (e.g. a grade `"(3)"` right after real
alinea (2)) can slip through the guard. If the vision pass finds a *dropped real
alinea* (false negative), STOP — add a failing test, tighten Signal 2, re-run.
Do not merge on green unit tests alone; the corpus diff is the acceptance
evidence.

## After FR-030
Per owner sequencing (2026-07-04): **FR-030 → then FR-026 (annex-as-separate-doc
facet) → then Phase 3/4 (ДВ freshness monitor → consolidation engine).** Phase
3/4 has substantial prior brainstorming to fold in (`docs/research/2026-06-22-*`,
`docs/sync/HANDOFFS/2026-06-22-freshness-consolidation-resource-roadmap.md`) and
should get its own brainstorm → design → plan pass — do not start it cold.

## Kickoff prompt for the new session
> Execute the FR-030 plan at `docs/plans/2026-07-04-fr030-alinea-citation-discriminator-plan.md`
> using subagent-driven-development, one task at a time, with a fresh-subagent
> code review after each task (fix → re-review until clean) before advancing.
> Task 3's rebuild-diff must be vision-verified — do not accept the fix on unit
> tests alone. Read the design doc first.
