# Handover: next session — Phase 3 (DV monitor / FR-002) brainstorm

**Author:** ekimir session (Claude Opus 4.8, 1M), 2026-06-22. **For:** the next session.
**Status:** Investigations I1–I4 COMPLETE + synthesized + owner-reviewed. Two decisions taken. Session PAUSED here by owner choice. This handover hands the baton to the Phase 3 brainstorm.

---

## 0. Where we are (one paragraph)

The national-functionality track's **investigation phase is done.** Four scoped investigations (I1 ecosystem, I2 LawVM, I3 ДВ access, I4 official sources) were run as parallel research agents, each with a sources log tracing every load-bearing claim to a verbatim `extract#N`, then synthesized into a **decision-ready brief**. The roadmap's central premise — *Bulgaria must self-consolidate because there is no official consolidated source to fetch* — is now **confirmed and triangulated** (I1+I3+I4 independently). The engine model is fixed (LawVM). Two open decisions were resolved with the owner. Nothing is running in the background; no Authority Surface was edited. The next session starts the **Phase 3 brainstorm.**

## 1. Read path (next session)

1. `.claude/CLAUDE.md` → `docs/sync/ACTIVE.md` → `docs/sync/DEFERRED.md` (empty) → `docs/process/delivery-contract.md` (Phase 3 + Phase 4 DoD — note the Phase-4 rewrite is **pending**, see §4).
2. **`docs/research/2026-06-22-investigations-synthesis-brief.md` ← START HERE** (the decisions + the plan; §5 is the shared design spine).
3. The four findings (with sources logs): `docs/research/2026-06-22-I{1,2,3,4}-*.md`.
4. The roadmap that scoped all this: `docs/sync/HANDOFFS/2026-06-22-freshness-consolidation-resource-roadmap.md`.
5. `docs/frs/INDEX.md` (FR-002 DV monitor, FR-003 ZID parser, FR-004 oracle, FR-005 upstream, FR-009 historical) · `docs/plans/2026-04-19-legalize-bg-design.md` (consolidation engine §). Memory: `project_legalize_bg.md`.

## 2. What is SETTLED — do NOT re-litigate

- **Premise confirmed (3 ways):** no official consolidated BG source/API; self-consolidate from ДВ. **Zero precedent** in the Legalize ecosystem — every country (ES/FR/EU/DE/SE/KR) fetches state-consolidated text; KR "independent" = own codebase, still state-sourced.
- **Engine model = LawVM** (`eliask/lawvm`): forward replay, anchor on ДВ promulgation; tiny **4-op canonical kernel** (`replace` / `insert` / `repeal` (tombstone) / `text_replace` (narrow)) + a separate **elaboration layer** (renumber / move / restructure / tables / conditional commencement live here — "replay is boring; elaboration is the effort"); `LegalAddress` `kind:label` path, **exact-then-unique-suffix, fail-loud** (`ambiguous_address`, never guess); `content_state` (live/tombstone/absent) + `lineage`/`address_chain` for identity across renumbering. Order by **in-force date (влизане в сила)** first, then ДВ publication date.
- **Architecture boundary:** the self-consolidation engine lives **UPSTREAM of Legalize `get_text()`**, outside `fetcher/bg/`. The 4 fetcher interfaces (`LegislativeClient` / `NormDiscovery` / `TextParser` / `MetadataParser`) all bake "consolidated text" into the source — there is **no amendment/apply interface** in the contract.
- **Phase-3 detection = PARSE-NOT-FETCH:** ДВ exposes NO structured ЗИД→amended-act link (`.HistoryOfDocument` is an APIS construct). Parse the ЗНА-templated genitive title (`Закон за изменение и допълнение на Закона за …`) + the inline `(ДВ, бр. N от YYYY г.)` promulgation citation; resolve the *declined* name with a **declension-aware Cyrillic matcher** (reuse FR-019 casefold); disambiguate via the citation against `amendment_history`/`Source-Id`; **flag ambiguous matches** rather than guessing.
- **ДВ access = server-side HTML** (no PDF/OCR for main text): documents at `showMaterialDV.jsp?idMat=M`, enumerated from `materiali.faces?idObj=N` (`idObj`=issue, `idMat`=document — two independent ID spaces). Reuse `fetcher/bg/client.py:RateLimitedSession` (≤1 req/s, 2/4/8s backoff, halt-on-Cloudflare); **verify charset per-response** (don't assume cp1251 *or* UTF-8); poll by latest-issue `(year, number)` high-water mark (Tue/Fri baseline + извънреден any day); avoid crawling the 413-page JSF list.
- **Validation oracles:** lex.bg **+** MoJ/Ciela `justice.government.bg/home/normdoc/{id}` (free, official-domain, curated subset, HTML-only). Both are **witnesses, not truth** — the oracle can itself be wrong.

## 3. Owner decisions taken 2026-06-22 (after reviewing the brief)

- **D-a RATIFIED → LawVM TWO-LEVEL model** is the Phase-4 acceptance bar: (a) replay **invariants** as strict hard-failures (failed op = no-op; no touch outside target; no opaque tree surgery; no silent guessing/date-estimation), + (b) oracle **adjudication** of residual divergence into lanes (source-pathology / replay-demotion / risk-signal / editorial) with an editorial-witness cross-check. Divergence is **always an explicit classified fact, never silently accepted** — but **not** naïve byte-identity. (Finland evidence: even a mature compiler leaves 0.65% text / 104-of-690 <90% residual, and the official oracle was wrong in 22 cases.)
- **Governance edits HELD** until the Phase 3 brainstorm confirms nothing shifts (avoids editing Authority Surfaces twice).
- **Second oracle (MoJ/Ciela):** recorded now, wire when the validator is built.

## 4. The TASK for the next session

1. **Phase 3 (DV monitor / FR-002) brainstorm** — `superpowers:brainstorming` — conducted with the **shared Phase-3/Phase-4 design spine** (brief §5) in view: the declension-aware resolver, the typed-op model, `LegalAddress` fail-loud resolution, the flag-don't-guess discipline, and the ДВ acquisition layer all serve both phases — design them once.
2. **Surface-6 preflight** (fetcher interfaces — `IMPLEMENTATION-PREFLIGHT.md`) for the ДВ transport/`NormDiscovery` additions; Surface-1 (frontmatter) only if touched, additive-only.
3. **`writing-plans`** → plan file `docs/plans/YYYY-MM-DD-phase3-dv-monitor.md`.
4. **TDD** on a branch, owner-merged (proven session pattern; do not introduce feature branches without confirming, but Phase-3 is pipeline code → branch + PR per the branch model).
5. **THEN — only after the brainstorm confirms** — apply the **held governance edits in ONE pass:**
   - Rewrite `delivery-contract.md` §"Phase 4 — Consolidation Engine" DoD → the LawVM two-level bar (drop "≥70%/≥90%"; keep G1–G4).
   - Add `DECISIONS.md` **D-043…D-046** (the D-a…D-d resolutions; reuse the brief §3 wording).
   - Reword `frs/INDEX.md`: **FR-009** "reverse-apply" → **forward replay** (anchor ДВ promulgation, lex.bg+MoJ endpoints, order by in-force date, depends on the engine); **FR-002** parse-not-fetch + ДВ HTML access; **FR-003** 4-op kernel + elaboration grammar (drop "~70-80%"); **FR-004** add MoJ second oracle + witness-not-truth; **FR-005** Gate 0.5 satisfied via self-consolidated history + git-dated corpus, documented per `ADDING_A_COUNTRY.md` RESEARCH-{CC}.md.
   - Advance `ACTIVE.md`.

**Process discipline:** follow `global-workflow` — present the execution strategy for approval before dispatching agents or writing code. Phase 3 and the engine each get brainstorm → preflight → plan → TDD (decision D-d).

## 5. Open risks to carry into the Phase 3 brainstorm (from I3 §"Open risks")

- **R1 (highest-effort):** title→act resolution accuracy — declined prose + `(ДВ,бр.N)` citation is the only signal; coverage unmeasured until built (parallels roadmap T2). Flag-on-ambiguity is the deterministic-or-flagged escape hatch.
- **R2:** ДВ JSF/`ViewState`/`jsessionid` fragility — lean on stable GET surfaces + monotonic issue cursor.
- **R3:** ДВ charset unconfirmed — detect per-response.
- **R4:** извънреден issues land off the Tue/Fri cadence — poll by issue number, not calendar day.
- **R5:** whole-issue PDF / appendices — embedded vision if scanned (global rule, no external OCR); main text is HTML so this is an edge case.
- **R6:** no `robots.txt` — proceed on official-publication + public-domain-text basis with strict ≤1 req/s.

## 6. Ready-to-paste kickoff prompt

```
Continue the legalize-bg national-functionality track. Run the session startup protocol
first (.claude/CLAUDE.md → docs/sync/ACTIVE.md → docs/sync/DEFERRED.md →
docs/process/delivery-contract.md), then read this handover and the synthesis brief:

  - docs/sync/HANDOFFS/2026-06-22-phase3-next-session-handover.md   ← this file
  - docs/research/2026-06-22-investigations-synthesis-brief.md      ← decisions + plan
  - docs/research/2026-06-22-I{1,2,3,4}-*.md                        ← investigation findings

Everything in §2 of the handover is SETTLED — do not re-litigate. TASK: brainstorm Phase 3
(DV monitor / FR-002) via superpowers:brainstorming with the shared Phase-3/Phase-4 design
spine in view → Surface-6 preflight → writing-plans → TDD on a branch. THEN (only after the
brainstorm confirms) apply the held governance edits in one pass per handover §4.5.

Follow global-workflow: present the execution strategy for approval before dispatching
agents or writing code.
```
