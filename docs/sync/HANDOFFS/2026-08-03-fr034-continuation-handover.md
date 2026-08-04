# FR-034 continuation handover — 2026-08-03

**For the next session. Read in order:** this file → `docs/plans/2026-08-02-fr034-unnumbered-alinea-remediation.md` (Tasks 6b/6c/7 are what remain) → SDD ledger `.superpowers/sdd/2026-08-02-fr034-unnumbered-alinea-remediation/progress.md` (fix-round history, rulings, parked items) → `docs/research/2026-07-31-unnumbered-alinea-structure-loss.md` (original findings).

## Model policy (owner-ratified this session)

ALL execution agents (implementers, task reviewers, re-reviewers, sweep runner) = **Opus 5** (`model: opus`). Final whole-branch review = **Fable 5** subagent (`model: fable`). Orchestrator does not write code; per-task review loop per superpowers:subagent-driven-development.

## State

- Branch `fix/fr034-unnumbered-alineas`, HEAD `d6065ccb` (617 sweep commits on top of 6 code commits `a4f0491d..f5296f54` + base `f934698f` = main).
- Suite: 663 non-perf green. tools.json 1.5.0, openapi checked. Preflight: all additive (plan §Preflight).
- Sweep run 1 COMPLETE (3,598 acts, 0 errors, no CF challenge, no cookie needed): 496 `[popravka]` + 99 `[reforma]` + 22 `[nova]`; catalog rebuilt = 3,624 acts; 207 laws / 18,488 implicit rows; 8 gate-fail skips (7 titulo stubs + 1 coverage, D-047 precedent).
- `fr034_verify.py check` = **RED** (this is the blocker): R3 ЗЗД чл. 36 still flat; R1×3 + R2×1 (two `[reforma]` = likely lawful amendments vs stale baseline; two `[popravka]` = ЗЖТ −1 alinea, Наредба № 5/1999 −1 article — unadjudicated).

## Root cause of R3 (VERIFIED — do not re-derive)

`refresh.py:238 normalize_for_compare` collapses ALL whitespace → structure-only rewrites classify `unchanged` → never written. ЗЗД/ЗН/ЗС skipped (live lex.bg HTML re-verified 2026-08-03: ЗЗД still serves 453 Article divs / 184 multi-child-div — the parser fix is correct, the classifier hid it). Third instance of the text-presence-not-topology blind-spot class (D-047 coverage gate → reviews → change classifier). Fix + re-sweep = plan Task 6b; adjudications + implicit sampling = Task 6c; then Task 7 (governance mentions ALL THREE blind-spot instances in D-058).

## Traps / invariants

- `.fr034-baseline.json` (repo root, untracked, 417,566 bytes) is the R1/R2 floor — NEVER re-run `baseline`; run `check` only, from repo root.
- State backups in SDD workspace: `refresh-state.pre-fr034.json` (pre-run-1, June-21 D-047-era). Before run 2: back up run-1's `.refresh-state.json` there too, then clear.
- Untracked, never commit: `catalog.db`, `.fr034-baseline.json`, `refresh-fr034.log`, `rebuild-fr034.log` (neither log is gitignored — no `git add -A` ever). Owner-gated, never touch: `.claude/CLAUDE.md` (modified), `docs/sync/SYNC-NOTICE-2026-07-07.md`.
- Commit plan doc + research docs in Task 7, not before. Corpus commits only via refresh.py.
- Census from the refresh log (grep "structure mismatch (report-only)" and "structure check skipped"), NOT gate-report.json (failures-only). Run-1 census: 51 mismatches, 0 skips.
- R5's duplicate-anchor exclusion covers 457 (law_id,article) pairs — FR-030 remit, documented in the script.
- Parked/deferred (ledger has rulings): export_cf implicit labeling (D1 regen decision), ППЗ чл. 102б English annex remnant (FR-026), get_articles handled (fixed in `88028d6c`), fr034_verify repo-root docstring cosmetic, `_ANCHOR_PREFIX_RE.search` citation-in-title nit.
- Task 7 numbers: next FR = FR-034 (row exists? NO — register), next decision = D-058, FR-030 gets the Defect-C annex note.
- **MERGE MODE (owner-confirmed): merge commit of the whole branch, NEVER squash** — per-act commit provenance (`Source-Id`/`GIT_AUTHOR_DATE`) feeds FR-020 time-machine version derivation; D-047 precedent. Put this in the PR body explicitly.

## Kickoff prompt for next session

„Continue FR-034 execution per docs/sync/HANDOFFS/2026-08-03-fr034-continuation-handover.md: run Tasks 6b, 6c, then 7 from docs/plans/2026-08-02-fr034-unnumbered-alinea-remediation.md, subagent-driven (Opus 5 execution agents, Fable 5 final review), continuing the ledger at .superpowers/sdd/2026-08-02-fr034-unnumbered-alinea-remediation/progress.md."
