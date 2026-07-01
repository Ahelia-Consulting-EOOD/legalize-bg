# Handover: 2026-07-01 — P0 parser remediation status + Phase 3 (DV monitor) brainstorm PAUSED

**Author:** ekimir session (Claude Opus 4.8, 1M), 2026-07-01. **For:** the next session.
**Status:** A P0 corpus-integrity defect (**D-047**, parser data-loss) was found and partially remediated between 2026-06-22 and 2026-06-30. The parser is fixed and a coverage gate is in place (committed to `main`), **but the corpus is still defective for ~3,579 of 3,599 acts** — the full corrective re-bootstrap has NOT run. Separately, this session ran the **Phase 3 (DV monitor / FR-002) brainstorm**; it produced five settled design decisions but is now **PAUSED behind the P0 remediation** — no design doc was written. This handover reconciles the two.

---

## 0. Where we are (one paragraph)

The **P0 corpus-integrity defect (D-047) is the top priority, ahead of the freshness track** (per the committed `ACTIVE.md` banner). The lex.bg body parser silently dropped three subdivision classes → ~100% of acts lost their Допълнителни разпоредби (definitions) and all §-numbered Преходни/Заключителни bodies. **The parser is now fixed** (keep-unknown-by-default + chrome denylist) and a **class-agnostic coverage gate** hard-fails any act with uncovered legal text — both committed to `main` with tests (428 passed / 3 pre-existing-or-flaky failures). **But only ~20 of 3,599 acts have been restored** (7 that survived + 13 re-scraped: ЗУО + 12 consumer-priority acts). The full corrective re-bootstrap is **blocked on re-sourcing at scale**: live lex.bg now returns a Cloudflare 403. A workaround ("path A": a real-browser `cf_clearance` cookie reused in the rate-limited `requests` session) is **proven on 13 acts** but has not been run over the full corpus, and there is an open owner decision to instead **pivot re-sourcing to ДВ / official consolidations** (ties to FR-024/D-038). Meanwhile this session's **Phase 3 DV-monitor brainstorm** settled five design decisions (below) but did not proceed to a design doc — it is paused until the P0 corpus is trustworthy again, and its ДВ-acquisition and coverage-gate primitives now **converge with the P0 re-source work**.

## 1. Read path (next session)

1. `.claude/CLAUDE.md` → `docs/sync/ACTIVE.md` (**P0 banner at top**) → `docs/sync/DEFERRED.md` (empty) → `docs/process/delivery-contract.md`.
2. **`docs/sync/DECISIONS.md` → D-047** ← the P0 finding + the four resolved decisions (D1–D4) + the CF obstacle. START HERE for the defect.
3. **`docs/plans/2026-06-29-parser-remediation-plan.md`** ← the 5-phase remediation plan (Task-by-Task). *Uncommitted — see §5.*
4. `.superpowers/sdd/final-fix-report.md` ← what the branch-review wave actually fixed (now gitignored/local per `658d9340`; the durable record is the committed forensics in item 5).
5. `docs/research/2026-06-29-parser-data-loss-forensics/` (`FINDINGS.md`, `EVALUATION.md`, `COMPLETENESS.md`, `forensics.py`, `coverage_ledger.py`) ← the evidence base. *Uncommitted — see §5.*
6. **This handover §3** ← the paused Phase 3 brainstorm decisions (to preserve).
7. When Phase 3 resumes: `docs/sync/HANDOFFS/2026-06-22-phase3-next-session-handover.md` (the prior handover; its §2 SETTLED facts still hold) + `docs/research/2026-06-22-investigations-synthesis-brief.md` + the four `docs/research/2026-06-22-I{1,2,3,4}-*.md` findings.

## 2. The P0 defect (D-047) — what broke, how handled, current state

### 2.1 What broke
`fetcher/bg/text_parser.py` `CLASS_MAP` was a CSS-class **allowlist** (`find_all(class_=keys)` → any unmapped class silently dropped). It omitted `AdditionalEdicts` (ДР heading), `FinalEdictsArticle` (§ definition/transitional bodies), and `FinalEdicts` (Заключителни разпоредби КЪМ… heading). Measured over the full corpus: **7/3599 acts retained a ДР heading (0.19%), 5/3599 retained any real § provision (0.14%)** — near-total loss of legal definitions and §-numbered transitional/final provisions across every category. A separate heading-concatenation defect affected ~30% of acts. `catalog.db` and the FR-020 versions were built on the corrupted text → contaminated. The unit tests encoded the same blind spot (`test_text_parser.py:58`). **Recoverable** — a parser bug, not source corruption; the texts are re-fetchable.

### 2.2 How it was handled (the four D-047 decisions)
- **D1** — re-bootstrap the FULL national corpus with the fixed parser, oracle-gated (the whole 3,599-act bootstrap already shipped → no "caught early" reprieve).
- **D2** — fix the heading-concatenation defect in the same pass.
- **D3** — **harden against the defect *class*, not the instance**: invert the parser to **keep-unknown-by-default** (chrome denylist) + a **class-AGNOSTIC coverage gate** that asserts ~0 uncovered legal text per act, for 100% of acts. Completeness is proven by *measuring uncovered source text*, NOT by enumerating classes. The strict source-vs-output check is the **sole acceptance gate on every act** — structure heuristics (base-ДР present / §1 present) are rejected as false-negative-prone (canonical counterexample: ЗАДС defines terms in `Чл. 4`, has no base ДР).
- **D4** — model the re-bootstrap as an FR-020 **corrective baseline**, not a `[reforma]`, so version timelines aren't polluted.

### 2.3 DONE vs REMAINS (against `docs/plans/2026-06-29-parser-remediation-plan.md`)

| Plan phase | Status | Evidence |
|---|---|---|
| **Phase 1 — parser fix** (ДР/ПЗР/Дял classes, de-glue, keep-by-default + chrome denylist) | ✅ **DONE, committed** | `fe22b787`, `32ac26d0`, `f61d5f39` |
| **Phase 2 — class-agnostic coverage gate + tests** (validator, hard gate wired into `bootstrap.py`/`refresh.py`, all-fixtures sweep) | ✅ **DONE, committed** | `7392987d`, `5ed322ee`, `d2ac3581`, `e5249276`, `b70a0e09`; `tests/refresh/test_gate.py` (+11) |
| Branch review wave (green the suite, regenerate goldens, seam guards) | ✅ **DONE, committed** | `.superpowers/sdd/final-fix-report.md`; suite 428 pass / 3 pre-existing-or-flaky |
| Partial corpus restore (ЗУО + 12 consumer-priority acts) | ✅ **DONE, committed** | `947444dd` `[popravka]` |
| **Phase 0 — MCP deploy-guard** (`LEGALIZE_CORPUS_DEFECTIVE` refuse-to-start + offline runbook) | ❌ **NOT DONE** | no guard in `mcp_server/`, no `docs/runbook/2026-06-29-corpus-offline-notice.md`. *Latent only — the MCP server is not deployed anywhere yet.* |
| **Phase 3 — Cloudflare / re-source spike** (Tasks 7–9; decision gate: lex.bg-CF vs ДВ pivot) | 🟡 **PARTIAL** | "path A" (`cf_clearance` cookie in `requests`) proven on 13 acts only; no productionized fetch path; **owner decision open (plan Task 8)** |
| **Phase 4 — full corrective re-bootstrap** (all 3,599 acts, gated) | ❌ **NOT STARTED** | no `refresh/2026-06-29-parser-fix` branch |
| **Phase 5 — lift offline + governance close-out** | ❌ **NOT STARTED** | D-047 still `Active`; `catalog.db` unrebuilt |

### 2.4 Corpus state
**Still defective.** Only ~20 of 3,599 acts have restored ДР/ПЗР bodies (spot check: `grep -rlF 'Допълнителни разпоредби' ... --include='*.md' | wc -l` → 20). The other ~3,579 acts still lack their definitions and §-numbered transitional/final provisions. `catalog.db` + FR-020 versions remain contaminated until the Phase-4 re-bootstrap + rebuild.

### 2.5 The blocker
Re-sourcing 3,599 acts requires either (a) clearing Cloudflare on lex.bg at scale (path A proven small-scale, honoring D-011 stop-on-CF + ≤1 req/s + D-039 texts-only), **or** (b) pivoting re-sourcing to ДВ + official consolidations (FR-024/D-038). **This is the pivotal open owner decision** (plan Task 8) and it directly overlaps the freshness track (§4).

## 3. Phase 3 (DV monitor / FR-002) brainstorm — SETTLED this session, now PAUSED

Ran `superpowers:brainstorming` with the shared Phase-3/Phase-4 design spine in view. Reached "design presented, awaiting approval." **No design doc written; the brainstorm is paused behind the P0.** Preserve these five decisions — they remain valid design work:

1. **Phase-3/Phase-4 seam = detect + fetch + ARCHIVE.** The monitor fetches the full ЗИД HTML at detection time and archives the raw artifact (LawVM pipeline phase 1 "acquire + archive source artifacts") — pinning the witnessed text for reproducible Phase-4 consolidation, not just recording metadata.
2. **Persistence = flat files in git, no DB.** `cursor.json` (issue high-water mark) + `detections.ndjson` (append-only) + a Markdown review queue for flagged items + raw archive under `monitor/dv/{year}/{br}/{idMat}.html` + per-issue manifest. Matches "corpus `.md` = truth, `catalog.db` = derived"; a derived `monitor.db` can be added later if querying demands it.
3. **Commit model = conventional commits on `main`, no new corpus type.** Monitor data is a Phase-4 *input*, not a legislative event, so it uses `chore(monitor): …` — leaving the protected commit-message-format surface untouched and not polluting per-act `git log --follow` / FR-020.
4. **Resolver (title→act, R1) = full declension-aware fuzzy matcher, but built pure-Python.** Owner chose the "build it fully now" option (design-once shared spine). Reconciliation with D-022 (no NLP libs) / FR-021 (deferred stemmer): **build Option 1** (rich pure-Python morphology rules + stdlib edit-distance + flag-on-ambiguity, D-022 preserved), **run it through the Option 3 lens** (an eval harness measures precision/recall on real ЗИД titles — a Phase-3 deliverable), and **record in DECISIONS the fork + the possible evidence-gated swing** to a lemmatizer (Option 2, which would supersede D-022 / close FR-021) with a stated coverage trigger. Non-negotiable: even fuzzy matching must **fail loud** (unique-confident hit or flag), never silently pick the top match.
5. **Non-negotiable design commitments** (follow from settled principles): flag-don't-guess survives fuzzification; a resolver eval harness ships with the matcher.

**Folded recommendations still awaiting owner confirm/redline** (presented, not yet ratified): module layout (`monitor/` package importing `RateLimitedSession`); conservative classifier (unmatched title → `unclassified`, flagged, never dropped); CLI-invoked-by-external-scheduler (not a daemon); the on-disk layout in decision #2. **The prior handover's §2 SETTLED facts still hold** (parse-not-fetch; ДВ HTML access via `materiali.faces?idObj`→`showMaterialDV.jsp?idMat`; charset-detect; poll by issue cursor; engine upstream of `get_text()`).

## 4. What MOVED (re-sequencing) + convergences

- **Priority flip.** The P0 corpus remediation is now top priority, **ahead of** the national-functionality freshness track. The Phase 3 DV-monitor (and everything after it: Phase 4 consolidation, FR-024 re-source, FR-022 municipal) is **deferred until the corpus is trustworthy again.**
- **Naming hazard — two "Phase 3"s.** (a) **Roadmap Phase 3** = DV monitor / FR-002 (§3, paused). (b) **Remediation-plan Phase 3** = the Cloudflare / re-source spike (§2.3). Keep them distinct in all future writing.
- **Convergence A — re-source ↔ ДВ acquisition.** The P0 blocker (re-source 3,599 acts; lex.bg CF-gated) may pivot to **ДВ / official consolidations** (FR-024/D-038, plan Task 8). That pivot builds the **same ДВ acquisition layer** the DV monitor needs (brainstorm decision #1). If the pivot happens, design the ДВ acquisition layer ONCE for both.
- **Convergence B — coverage gate ↔ DV-monitor + Phase-4 validation.** The D-047 class-agnostic coverage gate ("prove completeness by measuring uncovered source text") is now a **proven, reusable discipline**. It strengthens the DV-monitor's conservative-classifier / flag-don't-guess posture (decision #5) and is a natural fit for the Phase-4 consolidation validation model (the LawVM two-level bar).
- **Held governance edits — still held, now larger.** The 2026-06-22 handover §4.5 held a one-pass governance edit (delivery-contract §Phase-4 rewrite → LawVM two-level model; DECISIONS D-043…D-046; FR-002/003/004/005/009 rewordings). That is **still pending** and must **now also capture the resolver D-022 fork** from brainstorm decision #4. Apply in one pass when the freshness track resumes. (Note: D-047 already took the next decision ID after D-042, so the held D-043…D-046 labels should be re-numbered on ratification.)

## 5. Uncommitted state (RESOLVED 2026-07-01)

All primary evidence cited by committed decisions/handovers is now in git history — no cited evidence remains untracked:

- **2026-06-29 D-047 evidence** — the remediation plan, the parser preflight, and the full `docs/research/2026-06-29-parser-data-loss-forensics/` dir (FINDINGS/EVALUATION/COMPLETENESS + `forensics.py`/`coverage_ledger.py`) — **committed** in `3f046e44`.
- **2026-06-22 freshness track** — the nine investigation files (I1–I4 + sources logs + synthesis brief) and `2026-06-22-phase3-next-session-handover.md` — **committed** alongside this handover update (`docs(research)`, 2026-07-01).
- `docs/sync/ACTIVE.md` (P0 banner + D-047 row) — committed (`3f046e44` / `d368febf`); this handover — committed (`d368febf`). `docs/sync/DECISIONS.md`'s prior `git status` "modified" flag was mtime-only (no content diff).

Historical note: `.superpowers/` scratch was gitignored and a stray SDD report untracked in `658d9340` — the durable D-047 record is the committed forensics above, not that local report.

## 6. Risks to carry forward

- **R-P0a — corpus untrustworthy.** ~3,579 acts still missing definitions + transitional/final bodies. Anything that reads legal *content* corpus-wide (search-by-body, consolidation, upstream contribution) is unsafe until the re-bootstrap completes.
- **R-P0b — no deploy-guard.** The MCP server has no refuse-to-serve guard yet (plan Task 0 not done). Latent because nothing is deployed, but do Task 0 before any deployment.
- **R-P0c — re-source at scale / CF fragility + ToS.** Path A (cookie reuse) is proven only on 13 acts; scaling it must stay ≤1 req/s, honor D-011 (stop-on-CF, never bypass aggressively), and respect lex.bg ToS / D-039 (texts only). The cleaner long-term answer may be the ДВ pivot.
- **R-P0d — FR-020 baseline pollution.** The corrective re-bootstrap must be modeled as a corrective baseline (D4), not `[reforma]`, or it fabricates an "incomplete→complete" version step in every act's timeline (plan Task 13).
- **R-P3a — Phase 3 design may shift.** Given Convergence A/B, resuming the DV-monitor brainstorm should re-check decisions against whatever the re-source pivot builds — don't write the Phase-3 design doc until the ДВ-acquisition ownership is settled.
- Prior Phase-3 risks (R1 resolver accuracy, R2 JSF fragility, R3 charset, R4 извънреден cadence, R5 appendix PDFs, R6 no robots.txt) still apply when Phase 3 resumes — see the 2026-06-22 handover §5.

## 7. The task for the next session (recommended sequencing)

**Finish the P0 remediation first; resume the freshness track only after the corpus is trustworthy.**

1. **Clear owner decision (plan Task 8):** re-source via lex.bg path-A at scale **or** pivot to ДВ / official consolidations (FR-024/D-038). Record as a DECISIONS addendum to D-047. *(If ДВ pivot: design the ДВ acquisition layer once, shared with the DV monitor — Convergence A.)*
2. **Phase 0 deploy-guard (plan Task 0)** — cheap, do it now so the defective corpus can never be served.
3. **Phase 4 full corrective re-bootstrap** on a branch (`refresh/2026-06-29-parser-fix`), coverage gate active, HALT-and-triage on any gate failure; corrective-baseline commits (D4); then rebuild `catalog.db` + `scripts/verify_catalog.py`; spot-check FR-020.
4. **Phase 5 close-out** — lift offline, update D-047 → remediated, restore `ACTIVE.md` corpus-trustworthy status, update memory.
5. **THEN resume roadmap Phase 3** (DV monitor) — re-confirm the §3 decisions against the re-source outcome, write the design doc, Surface-6 preflight, `writing-plans`, TDD. Apply the held governance edits (§4) in one pass.

**Process discipline:** follow `global-workflow` — present the execution strategy for approval before dispatching agents or writing code. The remediation plan is already TDD-structured for `subagent-driven-development`/`executing-plans`.

## 8. Ready-to-paste kickoff prompt

```
Continue legalize-bg. Run the session startup protocol (.claude/CLAUDE.md →
docs/sync/ACTIVE.md [note the P0 banner] → docs/sync/DEFERRED.md →
docs/process/delivery-contract.md), then read this handover and D-047:

  - docs/sync/HANDOFFS/2026-07-01-parser-p0-status-and-phase3-brainstorm-handover.md  ← this file
  - docs/sync/DECISIONS.md → D-047                                                    ← the P0 defect
  - docs/plans/2026-06-29-parser-remediation-plan.md                                  ← the fix plan

TOP PRIORITY is finishing the P0 parser-data-loss remediation, NOT the freshness track.
Parser + coverage gate are DONE (committed); the corpus is STILL defective for ~3,579/3,599
acts (full re-bootstrap not run). Next: (1) clear the owner decision — re-source lex.bg at
scale via path A vs pivot to ДВ/official (plan Task 8); (2) Phase-0 deploy-guard;
(3) full corrective re-bootstrap on a branch + rebuild catalog; (4) close-out.

The roadmap Phase 3 (DV monitor / FR-002) brainstorm is PAUSED with 5 settled decisions
recorded in the handover §3 — do NOT re-litigate them; resume Phase 3 only after the corpus
is trustworthy. Watch the two convergences (§4): the ДВ pivot builds the same acquisition
layer the DV monitor needs; the coverage gate is reusable for Phase-4 validation.

First housekeeping: commit the uncommitted evidence/plans/research (handover §5) so
committed decisions stop pointing at untracked files.

Follow global-workflow: present the execution strategy for approval before dispatching
agents or writing code.
```
