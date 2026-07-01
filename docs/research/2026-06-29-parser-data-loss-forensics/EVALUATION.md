# Evaluation: severity, recoverability, strategy, and decisions

**Date:** 2026-06-29 · **Input:** `FINDINGS.md`, `forensics.json` · **Status:** for owner review before the Phase-3 plan.

---

## 1. Severity classification — P0 / Sev-1 (data integrity)

The corpus exists to serve Bulgarian legislation *as law*. The defect removes, corpus-wide:
- **all legal definitions** (Допълнителни разпоредби, §1 "По смисъла на този закон" точки), and
- **all transitional/final provision bodies** (Преходни/Заключителни разпоредби §§).

Definitions are legally operative: sanction provisions must be exhaustive and cannot rely on analogy (чл. 46, ал. 3 ЗНА), and their elements are defined in the ДР. A corpus that answers "what does this term mean" or "when did this rule take effect" with silence is not fit for legal use. Article bodies survive (26,150 Чл.), so the corpus *looks* populated — which makes the defect more dangerous, not less: it passes a smell test while missing load-bearing content.

## 2. Recoverability — FULL (the one piece of good news)

This is a **parser bug, not data corruption**. The source (lex.bg, free public-domain text) still contains every dropped subdivision. Re-fetching and re-parsing with a corrected `CLASS_MAP` restores everything — proven by the Layer-2 oracle diff (definitions and §-ranges come back, recovered chars ≈ dropped chars). Nothing is permanently lost.

- No raw-HTML cache from the original bootstrap exists in-repo (only 7 fixtures + 1 ЗУО capture), so recovery requires **re-fetching all 3,599 acts** (the full corpus already shipped — laws 396, codes 24, ordinances 2627, regulations 492, implementing 60).
- At the mandated 1 req/s, 3,599 acts ≈ **~1 hour** of fetching. Cost is negligible; the work is in parser correctness + the validation gate, not the fetch. **BUT (2026-06-29): live lex.bg now returns a Cloudflare 403 challenge** (the client detects + stops per D-011), so re-sourcing is blocked until CF is solved or the corpus is pulled from authoritative primary sources (ДВ + official consolidations, already the D-038/FR-024 plan). The saved ЗУО capture sufficed for the single interim act; it does not cover 3,599.

## 3. What the evidence changes about project state

- **Invalidates** the current "corpus rebuilt / catalog.db trustworthy" status (memory `project_legalize_bg`, `ACTIVE.md`, DECISIONS through D-042) **for content completeness**. The article layer is fine; the §-provision layer is not.
- **FR-020 time-machine is built on sand twice over:** `law_versions` are reconstructed from the git log of files that never contained the ДР/ПЗР. Every historical version it returns is also incomplete. Re-bootstrap fixes go-forward, but historical reconstruction quality is bounded by what we can re-fetch (lex.bg serves the current consolidated text + edition markers, not arbitrary past full texts).
- **Git-history interaction (must be designed, not stumbled into):** re-writing 3,599 `.md` files produces new commits. FR-020 derives versions from commit history, so a naive re-bootstrap would inject a spurious "incomplete → complete" version transition into every act's timeline. The re-bootstrap must be modelled as a **corrective baseline** (not a `[reforma]`/amendment), and FR-020's version derivation may need to ignore or squash that baseline boundary.

## 4. Completeness of the fix — do not fix only what ЗУО showed

The evidence already proves a 2-class fix (the obvious ЗУО reading) is **insufficient**: the cross-act census surfaced `FinalEdicts` as a third dropped class, plus a separate heading-concatenation defect in 78% of acts, plus a minor `OfInsidetitle` to inspect. The lesson: the parser was built against an *incomplete enumeration* of lex.bg's class vocabulary, and so were its tests. The fix must therefore include a **vocabulary-completeness pass** (R3) — enumerate every subdivision-like class across a wide sample and fail loudly on unmapped ones — or we risk a second silent-loss class surfacing after re-bootstrap.

## 5. Strategy — recommended path

**Fix-then-rebootstrap, gated by a structural oracle.** In order:
1. TDD the parser fix: add the 3 classes (FEA with proper alinea/`<br>` handling), fix concatenation, inspect `OfInsidetitle`.
2. Add a **structural oracle gate** to the pipeline: for each act, assert presence of ДР/ПЗР when the source has them, and §-count parity source-vs-output. This is the gate that would have caught the original bug; it must exist before re-bootstrap so the same class of loss can never ship silently again.
3. Re-fetch + re-parse all 3,599 acts (5 category dirs); validate every act against the coverage gate + oracle; commit as a corrective baseline; rebuild `catalog.db`.
4. (CF obstacle first) resolve the lex.bg Cloudflare block or switch to authoritative primary sources before the bulk re-fetch.

Rejected alternatives: *defer/document-as-known-issue* (corpus unusable); *hand-patch the .md files* (can't reconstruct dropped text without re-parsing source anyway).

**Completeness is guaranteed structurally, not by enumeration** (see `COMPLETENESS.md`): the class-agnostic coverage ledger run as a per-act hard gate over 100% of acts answers "did we lose any legal text" with yes/no, catching drops by classes we have never seen. On the 7-act multi-type sample, the 3-class fix already drives uncovered legal text to **0 real chars** (residual = button chrome + duplicate article headings already in output). R6 below makes the default itself safe.

**R6. Invert the parser default** from allowlist (drop-by-default → silent loss) to keep-by-default with a chrome denylist, so an unknown legal class can never silently vanish (worst case: visible noise, caught by the gate). Strongly recommended; it is the architectural fix to the *class* of defect, not just this instance.

## 6. Risk register

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| A *fourth* unmapped class surfaces post-rebootstrap | Medium | High (re-do) | **Class-agnostic coverage gate** (`COMPLETENESS.md`): assert ~0 uncovered legal text per act over 100% of acts — catches drops by classes never seen. Plus keep-by-default inversion (R6). |
| FEA crude get_text loses alinea/point structure | Medium | Medium | Treat FEA like `Article` (br→paragraph handling); test against ЗУО §1 точки 1..51 |
| Re-bootstrap pollutes FR-020 version timelines | High if unhandled | Medium | Model as corrective baseline; adjust FR-020 derivation; document in DECISIONS |
| lex.bg layout drift since April bootstrap | Low | Medium | Re-fetch is fresh anyway; oracle gate catches structural regressions |
| Protected-surface change merged without preflight | Low | High | IMPLEMENTATION-PREFLIGHT for `fetcher/bg/` (mandatory per CLAUDE.md) |
| Concatenation fix changes heading text and breaks downstream parsing/catalog | Medium | Medium | Snapshot tests on heading output; rebuild catalog.db after |

## 7. Owner decision points (these shape the Phase-3 plan)

D1. **Re-bootstrap scope:** the full 3,599-act corpus must be re-done (the entire bootstrap already shipped — no partial reprieve). Open sub-choice: stage it (validate the fixed parser on a slice first, then run all 5 dirs) vs. one corrected full pass. **[Resolved D-047: full re-bootstrap, staged-then-full, oracle-gated.]**
D2. **Concatenation defect (R2):** **[Resolved D-047: fix in the same parser pass.]**
D3. **Hardening (R3):** **[Resolved D-047: keep-by-default inversion + class-agnostic coverage gate, not a minimal 3-class fix.]**
D4. **FR-020 git-history handling:** **[Resolved D-047: model the re-bootstrap as a corrective baseline, not a `[reforma]`.]**

These four are now ratified in `DECISIONS.md` D-047 (owner, 2026-06-29). The remaining genuinely-open choices — which feed the Phase-3 plan — are the *sequencing/sourcing* ones below (how to clear the Cloudflare block, and stage-first vs full pass), surfaced to the owner separately.

## 8. Effort / sequencing estimate

| Step | Effort | Gating |
|---|---|---|
| 1. Parser fix (3 classes + concat + OfInsidetitle) TDD | S-M | IMPLEMENTATION-PREFLIGHT |
| 2. Vocabulary-completeness + fail-loud guard | S | — |
| 3. Structural oracle gate | M | design the assertions |
| 4. Re-fetch + re-parse 3,599 + validate + rebuild catalog.db | M (compute, ~1h fetch) / M (review) | gate must pass; **CF block resolved first** |
| 5. Docs: DECISIONS, ACTIVE, memory; FR-020 baseline note | S | — |

S = hours, M = day-ish, in planning terms. The intellectual work is steps 2-3 (getting the enumeration and the gate right); steps 1, 4, 5 are mechanical once those are sound.
```
