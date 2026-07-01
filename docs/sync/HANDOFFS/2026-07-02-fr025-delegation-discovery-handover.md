# Handover: 2026-07-02 — FR-025 redirected to delegation-chain discovery (planning done, execution next session)

**Author:** ekimir session (Claude Opus 4.8, 1M). **For:** the next session.
**One-liner:** D-047 is fully remediated and live on origin. FR-025 (act-type category coverage) was found to be un-crawlable from lex.bg; it has been **redirected** to a hybrid delegation-chain discovery design. Planning is done; execution starts with an empirical ДВ survey.

## 0. Where we are

- **D-047 (parser data-loss): DONE, on `origin/main` (`fb3c3c11`), tag `corpus-d047-remediated`.** Corpus trustworthy; DRS trigger live. Nothing outstanding.
- **FR-025 (category coverage): REDIRECTED (planning complete, not implemented).** The discovery spike proved lex.bg exposes only 5 browsable act-type trees; ПМС/тарифи/инструкции/решения/укази are not tree-enumerable there. The tree-crawl plan is superseded. New approach = hybrid delegation-chain discovery. See the design doc.

## 1. Read path (next session)

1. `.claude/CLAUDE.md` → `docs/sync/ACTIVE.md` → `docs/sync/DEFERRED.md` → `docs/process/delivery-contract.md`.
2. `docs/sync/DECISIONS.md` → **D-049** (addendum 2026-07-02: the finding + the redirect decisions).
3. **`docs/research/2026-07-02-fr025-category-gap.md`** — the discovery finding (why lex.bg can't source this).
4. **`docs/plans/2026-07-02-fr025-delegation-discovery-design.md`** — the approved-direction design (START HERE for the approach).
5. Superseded (context only): `docs/plans/2026-07-02-fr025-category-coverage-{design,plan}.md` (tree-crawl).
6. Convergent prior work: `docs/research/2026-06-22-investigations-synthesis-brief.md` + the paused Phase-3 (ДВ monitor) decisions in `docs/sync/HANDOFFS/2026-07-01-parser-p0-status-and-phase3-brainstorm-handover.md` §3 (resolver posture, ДВ access path).

## 2. Settled decisions (do not re-litigate)

- Completeness = **HYBRID**: delegation graph (derived truth) + external enumeration (independent check); flag discrepancies.
- Discovery = **top-down delegation-chain**: derive expected lesser-acts from "на основание …" / "приема с наредба/тарифа…" clauses in acts we hold (90% of наредби carry the citation).
- Sources: **ДВ** (canonical, 7yr-PDF-limited), **N-Lex** (APIS-backed gateway), **justice.government.bg** (free partial oracle), **APIS/Ciela** (oracle-only, D-039 — never DB reuse), **lex.bg keyword** (fetch channel), **data.egov.bg** (enlisting hints), **Lex Alert** (freshness ref).
- Interim posture = **on-demand per-act `ldoc` capture** (as done for the НСС decree).
- Legal: **D-039** (own structure from public-domain texts; zero DB reuse — binds APIS/Ciela/N-Lex to pointers/counts only).
- Annex-as-separate-doc → **FR-026** (separate).

## 3. First execution steps (next session)

**Phase A — ДВ landscape survey (owner's suggested starting point):** fetch 20–30 full recent ДВ issues (`dv.parliament.bg`, `materiali.faces?idObj`→`showMaterialDV.jsp?idMat`); catalogue the act-types actually published + their page structure; confirm the access path + the 7-year/PDF limit. This materializes the enumeration target before designing it.
Then **Phase B** (delegation-parse prototype on the held corpus → first provable-gap list + resolver eval), **Phase C** (source-access spikes), **Phase D** (freeze design + write the detailed TDD plan), **Phase E** (implement). Detailed TDD plan is deliberately deferred until Phase A–C evidence exists.

## 4. Open questions carried forward (design §7)

R1 ДВ historical depth (7yr online limit) · R2 PDF text extraction cost (vision, no OCR lib) · R3 resolver ambiguity (eval harness) · R4 APIS/N-Lex legal posture · R5 chain depth + individual/ephemeral acts (owner scope-gate after Phase B) · R6 versioning (align FR-020).

## 5. State / housekeeping

- Working tree clean; local `main` == `origin/main` after the push accompanying this handover.
- SDD execution ledger halted: `.superpowers/sdd/progress.md` (gitignored scratch).
- No background tasks running; Playwright closed. A fresh `cf_clearance` cookie will be needed next session (mint via Playwright, runbook `docs/runbook/2026-07-01-cf-cookie-mint.md`).
- Governance synced: D-049 addendum, COVERAGE-FLOOR known-gap note, FR-025 REDIRECTED in INDEX, FR-026 to be formally registered when FR-026 is picked up.

## 6. Ready-to-paste kickoff prompt

```
Continue legalize-bg. Session startup protocol (.claude/CLAUDE.md → docs/sync/ACTIVE.md
→ DEFERRED.md → delivery-contract), then read:
  - docs/sync/DECISIONS.md → D-049 (addendum 2026-07-02)
  - docs/research/2026-07-02-fr025-category-gap.md          (the finding)
  - docs/plans/2026-07-02-fr025-delegation-discovery-design.md  (the approach)
  - docs/sync/HANDOFFS/2026-07-02-fr025-delegation-discovery-handover.md  (this file)

TASK: FR-025 comprehensive act-type coverage via delegation-chain discovery. Start with
Phase A — the ДВ landscape survey: mint a cf_clearance cookie (Playwright), fetch 20–30
recent ДВ issues from dv.parliament.bg, and catalogue the act-types published + structure
+ access path + the 7-year/PDF limit. Then Phase B (delegation-parse prototype on the held
corpus → provable-gap list + resolver eval). Do NOT re-litigate the settled decisions
(handover §2). Legal posture D-039: APIS/Ciela/N-Lex are oracle-only, never DB reuse.
Follow global-workflow; present the execution strategy before dispatching agents or code.
```
