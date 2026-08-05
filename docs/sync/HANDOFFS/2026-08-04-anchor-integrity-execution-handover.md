# Anchor-integrity execution handover — 2026-08-04

**For the next session. Read in order:** this file → `docs/plans/2026-08-04-anchor-integrity-remediation.md` (the plan — Tasks 1–9) → `docs/research/2026-08-02-fr034-sweep-report.md` §10 and §12 (the census this plan acts on) → `docs/sync/DECISIONS.md` D-058 (the blind-spot class and its binding countermeasure).

## What just landed

FR-034 is **merged** (PR #20, merge commit `00e93494` on `main`). It restored intra-article paragraph structure for pre-Указ-883 acts and made unnumbered алинеи addressable. Suite **699 passed / 8 deselected**. Catalog: 3,624 acts / 147,771 article rows / 309,999 explicit alinea rows / 21,043 implicit rows across 218 acts.

## What is still wrong — and why it is urgent

**The corpus contains articles that the acts do not have.** `laws/zakon-za-zadalzheniyata-i-dogovorite.md` carries `Чл. 1001а.` as if it were a ЗЗД provision; it is quoted ГПК/ЗПИ text sitting in ЗЗД's ПЗР. `get_article("zakon-za-zadalzheniyata-i-dogovorite", "чл. 1001а")` answers with it. Anyone citing „ЗЗД чл. 1001а“ cites a provision that does not exist.

This corpus is in **daily legal use**. Treat a wrong answer as the defect, not a wrong row count.

Measured extent (FR-034 census, all individually read and adjudicated): **90 artifact rows across 8 of the 13 doctrinal acts** — ЗОРВКС 50, ЗЛС 16, ЗЗД 10, ЗБППМН 7, ЗС 2, ЗОС 2, ЗВТ 2, ЗА-1947 1 — plus **20,282 implicit rows in the annex/table stratum at a 95% artifact rate**. The census covered 13 acts plus a sample, so **coverage is partial**: the pipeline generalises, the census does not.

## The owner's binding requirement

Stated directly, and it governs every design choice: *„I want to make sure we fix the false insertions once and for all, and in the next ingest we do not reintroduce it.“*

Two designs were proposed and **rejected by the owner** — do not resurrect either:

1. **Query-time filtering** of bad rows. Rejected: the corpus is the product. A read filter leaves `laws/*.md` wrong, leaves every non-MCP consumer wrong, and gives no guarantee about the next ingest.
2. **A stopgap suppression list** of the 90 verified rows. Rejected as symptom-hiding on a corpus in daily legal use.

The fix lands **at the parser**, the guarantee is **a gate that blocks the write**, and repair comes from a re-ingest. Anything that hides rather than prevents will be rejected again.

## The five-mechanism assurance chain (plan §The assurance chain)

1. **Parser never emits a false anchor** — quoted ЗИД text is blockquoted, never promoted to `**Чл. N.**`. Every character survives; only anchor status changes (Task 3).
2. **Monotonic-numbering invariant** — the backstop. Catches phantoms by arithmetic, not by recognising Bulgarian phrasing, so a layout nobody has catalogued still trips it (Tasks 1, 4).
3. **Hard ingest gate** — `refresh.py` / `bootstrap.py` refuse to write an act with an anchor-integrity violation. Not a warning; the write does not happen (Task 4). **This is the answer to „the next ingest must not reintroduce it.“**
4. **Corpus-wide CI invariant** — every commit checks no corpus file promotes a quoted anchor (Task 5).
5. **Per-article baseline** — D-058 (iv); per-law aggregates let losses cancel against gains (Task 6).

## Execution state

- Plan and this handover are on branch **`docs/anchor-integrity-plan`** (off `main` at `00e93494`). **Merge that branch first**, or branch execution work from it — the plan must be reachable from wherever you work.
- No execution work has started. Task 1 is the first thing to write.
- Phases: P0 detect (Tasks 1–2, no behaviour change) → P1 prevent (Tasks 3–6, the „never again“ phase) → P2 repair (Task 7, the ~2h sweep) → P3 implicit eligibility (Task 8) → P4 governance (Task 9). One PR per phase (D-h).

## Model policy (owner-ratified, carry it forward)

ALL execution agents (implementers, task reviewers, re-reviewers, sweep runner) = **Opus 5** (`model: opus`). Final whole-branch review = **Fable 5** (`model: fable`). Orchestrator writes no code; per-task review loop per `superpowers:subagent-driven-development`.

## Owner decisions still open (plan §Owner decision register)

- **D-1** — when the ~2h repair sweep may run. **Blocks Task 7 only.** Everything before it needs no lex.bg traffic.
- **D-2** — is `1974-01-01` the right era cutoff for position-derived алинеи (blocks Task 8).
- **D-3** — cf-plane `implicit_paragraphs` mirror-or-skip (gated on the D1 cutover, not on this plan).
- **D-4** — confirm each entry of the non-monotonic allowlist. Task 2 produces the candidate list; **do not allowlist anything without the owner's confirmation and a source citation.**

Tasks 1–6 can proceed with none of these answered.

## Traps and invariants — violations are unrecoverable

- Work in the **primary checkout** `/Users/ekimir/swprj/legalize-bg`, never a `.claude/worktrees/*` path. That is where `.venv`, `catalog.db`, the baselines and the logs live.
- **NEVER run `scripts/fr034_verify.py baseline`.** `.fr034-baseline.json` (repo root, untracked, **417,566 bytes**) is the irreplaceable pre-sweep floor. It now has a `FR034_FORCE=1` guard — do not set that variable. Task 6's `article-baseline` gets the same guard and the same discipline.
- **NEVER `git add -A` / `git add .`.** Untracked and never to be committed: `catalog.db` (1.4 GB) and the six `*fr034*.log` census files (gitignored as of `main`).
- **Owner-gated — never touch, stage, or revert:** `.claude/CLAUDE.md` (carries a pre-existing uncommitted modification) and `docs/sync/SYNC-NOTICE-2026-07-07.md` (untracked).
- **Corpus `.md` files are written ONLY by `refresh.py`.** Never hand-edit. Never hand-write a corpus commit.
- Before any sweep: back up `.refresh-state.json` into `.superpowers/fr034-preserved/`, then delete it. A surviving checkpoint makes the sweep a **silent no-op** — this bit two prior sessions.
- On a Cloudflare halt: **STOP and report.** Cookie minting is interactive and happens in the main session (D-047 path: `--cookie-file` + Playwright-minted `cf_clearance`). Do not improvise fetch workarounds.
- On an `anchor_integrity` gate failure during the sweep: **that is the gate working.** Record the act and its violating anchors. Do not disable the gate.
- Test runner is `.venv/bin/python -m pytest` — system python3 is 3.9 and cannot import the code.
- Bulgarian text uses **„…“** (U+201E opener, U+201C closer). Never ASCII `"`, never U+201D. Verify `count(„) == count(“)` with a **whole-file** check — spans wrap across lines and a per-line checker cannot see them (this bit the FR-034 session twice). **Never** run `bg-doc-tools/skills/bg-docx-formatter/scripts/fix_bg_quotes.py`; it is wrong on this point.
- Bulgarian legislative text comes ONLY from this corpus or the project's own lex.bg pipeline. Never aggregators (ciela, apis, lakorda, econ.bg) or web snippets. „lex.bg is blocked“ is never a stopping point.
- **Any branch carrying corpus commits merges with a MERGE COMMIT, never squash** — FR-020's time machine derives version boundaries from per-act `Source-Id`/`Source-Date`/`Norm-Id` trailers and `GIT_AUTHOR_DATE`. The GitHub UI default may be squash. Phase 2 is the branch this applies to.
- `fetcher/bg/` ships upstream **without** the Ahelia-private `index/` package. Task 3 imports the anchor modules from `fetcher/` — resolve the layering deliberately (vendor, defensive import, or move the modules) and state which you chose. `coverage.py` duplicated a regex for exactly this reason; follow its precedent or better it.

## Preserved state

`.superpowers/fr034-preserved/` (gitignored) holds the complete FR-034 SDD ledger (`progress.md`, 42 KB — every fix round, ruling and parked finding) and both refresh-state backups (`refresh-state.pre-fr034.json`, `refresh-state.run1-fr034.json`). Regenerating those checkpoints would cost a 2h sweep.

## Known-good verification state to preserve

`scripts/fr034_verify.py check` returns **exactly four residuals**, all adjudicated as non-defects — do not "fix" them:

- `R2 naredba-5-ot-10-may-1999-…kadastralni` articles 44→43 — phantom article; the **pre-sweep baseline** was the contaminated side (lex.bg forum chrome).
- `R1 naredba-69-ot-15-yuni-2021-…` alineas 9→6 — lawful ДВ бр. 61/2026 repeal of чл. 2.
- `R1 zakon-za-fiskalen-savet-…` 36→34 — lawful ДВ бр. 69/2026 recast of чл. 16.
- `R1 zakon-za-zhelezopatniya-transport` 425→424 — genuine lex.bg source change (one changed span in a 40,335-word diff).

R3/R4/R5 must stay clean.

## Kickoff prompt for the next session

„Execute `docs/plans/2026-08-04-anchor-integrity-remediation.md` per `docs/sync/HANDOFFS/2026-08-04-anchor-integrity-execution-handover.md` (read the handover FIRST, in full — it has state, the owner's binding requirement, rejected designs, and the traps). Work in the primary checkout `/Users/ekimir/swprj/legalize-bg`, never a worktree. Subagent-driven per `superpowers:subagent-driven-development`, Opus 5 execution agents, Fable 5 final review, one PR per phase. Start at Task 1; Tasks 1–6 need no owner decisions. Never run `scripts/fr034_verify.py baseline`, never `git add -A`, never hand-edit corpus `.md`.“
