# Decision-ready brief: national-functionality track (freshness → deterministic consolidation → re-source)

**Author:** ekimir session (Claude Opus 4.8, 1M), 2026-06-22.
**Status:** SYNTHESIS of investigations I1–I4. **Decision-ready, NOT yet enacted** — governance edits (delivery-contract §Phase 4, DECISIONS D-a…D-d, FR rewordings) are *recommended* here and held for owner ratification (Authority Surfaces). The owner asked to PAUSE here for review before the Phase 3 brainstorm.
**Inputs:** `docs/research/2026-06-22-I{1,2,3,4}-*.md` (+ their `*-sources.md` logs; every load-bearing claim in those docs traces to a verbatim `extract#N`).
**Supersedes for planning purposes:** the open questions in `docs/sync/HANDOFFS/2026-06-22-freshness-consolidation-resource-roadmap.md` §5–§6 (the investigations those sections requested are now done).

> **OWNER DECISIONS (2026-06-22, after reviewing this brief):**
> - **D-a direction RATIFIED → the LawVM two-level model** (replay invariants as strict hard-failures + oracle adjudication into divergence lanes; never a silent accept; *not* naïve byte-identity). This is the settled Phase-4 acceptance bar; the formal delivery-contract rewrite is deferred (below).
> - **Governance edits HELD** (delivery-contract §Phase-4 rewrite, DECISIONS D-a…D-d → D-043…D-046, FR-002/003/004/005/009 rewordings) — to be applied in one pass *after* the Phase 3 brainstorm confirms nothing shifts. Authority Surfaces stay unedited this session.
> - **Q2 (second oracle MoJ/Ciela):** record now (done, this brief), wire when the validator is built. **Q3:** session paused here as planned; Phase 3 brainstorm is the next session's first action.

---

## 0. TL;DR

The roadmap's central premise is **confirmed and triangulated**: Bulgaria has no official consolidated-law source to fetch from, so it must **self-consolidate deterministically from ДВ** — a path with **zero precedent in the entire Legalize ecosystem**. The engine design is no longer open: adopt the **LawVM model** (forward replay; a tiny 4-op canonical kernel; a separate elaboration layer; a two-level validation model). Two refinements emerged that the owner should ratify before planning: (1) the Phase-4 acceptance bar should be **LawVM's two-level model (invariants + classified adjudication), not a naïve "byte-identical-or-fail"** — because even a mature deterministic compiler leaves a classified residual gap and the oracle itself can be wrong; (2) adopt the **MoJ/Ciela `justice.government.bg` portal as a *second* government-domain validation oracle** alongside lex.bg.

---

## 1. The four findings, cross-checked

### The central premise is triangulated three ways (I1 + I3 + I4)
"Bulgaria must self-consolidate because there is nothing official to fetch" is confirmed from three independent angles:

- **I4 (sources):** No official, state-authored, full-corpus, API/machine-readable consolidated database exists. ДВ is constitutionally the official channel but publishes **only the changed parts** of an amended act (an amendment stream), per the EU's own N-Lex Bulgaria page (*"the State gazette consists mainly of editions and corrections … and not of the full texts of actual laws"*). N-Lex/EUR-Lex offer no shortcut — N-Lex links back to the ДВ gazette; EUR-Lex consolidates only EU acts.
- **I3 (ДВ shape):** No official ДВ API, XML/JSON, RSS, sitemap, or `robots.txt`; `data.egov.bg` carries no ДВ dataset; N-Lex's BG search form is itself APIS-backed. The structured/consolidated layer is the *commercial* providers, not the state.
- **I1 (ecosystem):** Not one Legalize country (ES/BOE, FR/LEGI-DILA, EU/EUR-Lex, DE/gesetze-im-internet, SE/Riksdag-SFS, KR/National Law Information Center) self-consolidates. **All** fetch already-consolidated text + official version history from a state source. France's README says it outright. South Korea's "independent pipeline" is an independent *codebase* (its own Rust compiler) still sourcing consolidated text + 연혁 history from the Korean state API — not self-consolidation.

**Conclusion:** Bulgaria is uniquely the hard case. The ecosystem's only sanctioned fallback for a missing official consolidation is a *temporary single-snapshot + periodic re-download* bridge (which is what our bootstrap already is, D-039) — **not** a deterministic replay engine. Our planned engine is net-new relative to the whole ecosystem.

### One correction to the premise (I4)
A *government-domain* consolidated surface DOES exist: the **Ministry of Justice e-justice portal** (`justice.government.bg/home/normdoc/{id}`), serving genuine amended-into-base, point-in-time-capable text current to ДВ бр.30/2026, free, with per-element "Редакции". **But** it is (a) a **curated subset**, not the full corpus (ЗОП — one of the most-amended laws — is absent); (b) **HTML-only, no API/bulk/enumeration**; and (c) consolidated by the **private vendor Ciela Norma** under an EU-funded MoJ contract, not by the state. So it is an *official-domain re-publication of private consolidation* — not a sovereign source to fetch from, **but an excellent free validation oracle for major acts.**

### The architecture boundary is settled (I1)
The Legalize fetcher contract **bakes consolidation into the source**: `LegislativeClient.get_text()` is typed "fetch the *consolidated* text"; `TextParser` parses "*consolidated* text"; there is **no amendment/diff/apply interface anywhere** in `fetcher/base.py`. The four interfaces are: `LegislativeClient`, `NormDiscovery`, `TextParser`, `MetadataParser`. ⇒ The Bulgarian self-consolidation engine lives **entirely upstream of `get_text()`**, outside `fetcher/bg/` — exactly the split the design doc already assumes. The four interfaces are reusable for fetch/parse/commit plumbing; the engine is ours alone.

### The engine blueprint is concrete (I2 — LawVM)
- **Forward replay**, confirmed. Anchor on the original promulgation, apply amendment deltas forward in date order. Order by **in-force date (влизане в сила) first**, then publication date — not merely the ДВ issue date — and model deferred/conditional commencement (effect-time = a resolved date *or* a trigger rule).
- **Tiny canonical kernel — 4 ops:** `replace`, `insert`, `repeal` (tombstone), `text_replace` (narrow substring correction, *not* a generic editor), each with explicit pre/postconditions. The Finnish verbs map 1:1 to Bulgarian (`отменя се`→repeal, `се изменя`/`думите…се заменят`→replace/text_replace, `се създава`→insert). **Renumber/move/restructure are kept OUT of the kernel**, handled in a separate **elaboration layer**. "Replay is comparatively boring; the effort is elaboration."
- **`LegalAddress`** = `kind:label` slash-path (чл./ал./т./раздел/глава + lettered suffixes like чл. 5а), resolved **exact-match-then-unique-suffix**; ≥2 matches → loud `ambiguous_address`, never a guess. `content_state` (live/tombstone/absent) drives op preconditions; a `lineage`/`address_chain` preserves node identity across renumbering.
- **Two-level validation** (see §2 — this is the key refinement).
- **Finland evidence:** 690 fully-replayable statutes; vs the frozen Finlex oracle, mean **0.65% Levenshtein text distance**, **4.25% mean structural error**, **104/690 below 90%** (the "investigation frontier"), and **22 cases where the *official* consolidation was wrong** (not LawVM). Even a mature deterministic compiler does not hit 100% byte-match.

### Phase-3 amendment detection is parse-not-fetch (I3)
ДВ does **not** expose ЗИД→amended-act linkage as structured data (confirmed on a real ЗИД, an Инструкция, and N-Lex). The `.HistoryOfDocument`/"Изменя"/"Изменен със" graph the project docs cite is an **APIS construct**, not a ДВ feature. The amended act is named only in **title prose** (`Закон за изменение и допълнение на Закона за …`, genitive) + an inline `(ДВ, бр. N от YYYY г.)` promulgation citation. ⇒ The detector parses the ЗНА-templated title, resolves the *declined* act name with a **declension-aware Cyrillic matcher** (reuse FR-019 casefold), disambiguates via the `(ДВ, бр. N)` citation against the corpus act's `amendment_history`/`Source-Id`, and **flags ambiguous matches** rather than guessing.

### ДВ access is HTML, low-friction (I3)
Documents render as **server-side HTML text** at `showMaterialDV.jsp?idMat=M`, enumerated from `materiali.faces?idObj=N` (two independent ID spaces: `idObj`=issue, `idMat`=document). **No PDF/OCR needed** for the main act text. Cadence is Tue/Fri baseline + извънреден issues any day → poll by latest-issue `(year, number)` high-water mark, not by calendar day. Reuse `RateLimitedSession` (≤1 req/s, 2/4/8s backoff, halt-on-Cloudflare); verify charset per-response (do not assume cp1251 *or* UTF-8). 7 polite recon GETs, all HTTP 200, no challenge.

---

## 2. What changed vs the handoff's assumptions (the refinements that need owner sign-off)

1. **The Phase-4 acceptance bar — the handoff said "deterministic apply + byte-validate vs oracle + hard-fail on divergence." The Finland evidence shows a naïve binary "byte-identical-or-fail" is the WRONG bar.** Even a mature deterministic compiler leaves a classified residual (0.65% text / 104-of-690 below 90%), and the oracle is *itself sometimes wrong* (22 confirmed official-consolidation bugs). The correct formulation is LawVM's **two-level model**: (a) **replay invariants as hard failures** in strict mode (failed op = no-op; no op touches outside its target; no opaque tree surgery; no duplicate sibling labels; no silent target guessing/date estimation), AND (b) **oracle adjudication** that classifies every residual divergence into a lane (**source-pathology / replay-demotion / risk-signal / editorial**) with an **editorial-witness cross-check** to attribute *our-bug vs oracle-bug* — *never a silent accept, but not a binary byte-equal gate either.* The spirit of the owner's "fully deterministic, hard-fail, never a silent 70-90% accept" is **preserved and strengthened** — it just lands on the proven model rather than an unachievable byte-identity threshold.

2. **A second validation oracle.** Adopt MoJ/Ciela `justice.government.bg` as a *government-domain* oracle alongside lex.bg for the curated subset of major acts (free, official-domain). Strengthens D-003/D-b.

3. **`.HistoryOfDocument` is not real (for ДВ).** The Phase-3 design must not assume a structured amendment graph from ДВ; it's APIS's. Detection is parse-not-fetch.

4. **Ordering subtlety.** Replay/commit ordering keys on the Bulgarian **in-force date**, not just the ДВ publication date, with conditional/deferred commencement modeled.

5. **Gate 0.5 ("≥2 dated versions or stop") is the gate BG structurally cannot pass from any *official* source** — relevant later for FR-005 (Legalize upstream contribution): our multi-version history comes from self-consolidation + the existing git-dated corpus, documented per `ADDING_A_COUNTRY.md`'s RESEARCH-{CC}.md requirement.

---

## 3. Resolution of the open decisions (D-a … D-d) — recommended

| ID | Handoff framing | Recommended resolution (evidence) | Governance action (held for ratification) |
|---|---|---|---|
| **D-a** | Replace Phase-4 "≥70%/≥90%" with "deterministic apply + byte-validate + hard-fail" | **Adopt, but as LawVM's two-level model**, not binary byte-equality: replay invariants (strict hard-fail) + oracle adjudication into divergence lanes + editorial-witness cross-check; divergence is always an explicit classified fact, never silently accepted. LLM may *assist* elaboration of irregular ЗИД prose, but the deterministic validation gate is the authority — never an LLM confidence score. (I2 §Q3, Finland numbers) | Rewrite delivery-contract §"Phase 4 — Consolidation Engine" DoD; new DECISIONS **D-a** entry. |
| **D-b** | Keep lex.bg as validation oracle even after retiring it as source | **Confirm — and add MoJ/Ciela `justice.government.bg` as a second government-domain oracle** for major acts. Treat both as *witnesses, not automatic truth* (the oracle can be wrong). (I4 conclusion; I2 §Q3) | New DECISIONS **D-b**; cross-ref D-003/D-038/D-039. |
| **D-c** | Re-source: forward-only near-term, FR-009 historical re-derivation deferred | **Confirm.** Forward replay (Phase 3+4) makes ДВ the forward source and retires lex.bg from the *source* role (keeps it as oracle). The bootstrap stays a legitimate one-time photograph (D-039). FR-009 = full historical re-derivation, **forward replay** (not "reverse-apply"), deferred polish, depends on the engine. (I2 §Q4; I1 ecosystem fallback) | New DECISIONS **D-c**; reword FR-009 (see §4). |
| **D-d** | Process: Phase 3 and engine each get brainstorm → preflight → plan → TDD | **Confirm**, with one addition: Phase 3 and Phase 4 **share a design spine** (§5) so the Phase-3 brainstorm should be conducted with the engine's typed-op/locator/flag-don't-guess model in view, even though they ship as separate phases. Surface 6 (fetcher interfaces) preflight applies to the ДВ transport; Surface 1 (frontmatter) is additive-only if touched. | New DECISIONS **D-d**; no contract change beyond noting the shared spine. |

---

## 4. Recommended governance edits (held for ratification — NOT yet applied)

- **`docs/process/delivery-contract.md` §"Phase 4 — Consolidation Engine":** replace the `≥70% regex / ≥90% LLM` acceptance bullets with the D-a two-level model (invariants + adjudication lanes + editorial-witness cross-check; hard-fail/flag, never silent). Keep G1–G4 as-is.
- **`docs/sync/DECISIONS.md`:** add **D-a…D-d** (next IDs after D-042; note these reuse the handoff's `D-a…D-d` working labels — assign real `D-043…D-046` numbers on ratification).
- **`docs/frs/INDEX.md`:**
  - **FR-009** — reword "reverse-apply" → **forward replay** anchored on ДВ promulgation, lex.bg+MoJ as validation endpoints; order by in-force date; depends on the Phase-4 engine.
  - **FR-002 (DV monitor)** — note detection is **parse-not-fetch** (title-prose + `(ДВ,бр.N)` citation + declension-aware matcher + flag-on-ambiguity); ДВ access = HTML via `materiali.faces`/`showMaterialDV.jsp`, `RateLimitedSession`, poll by issue high-water mark.
  - **FR-003 (ZID parser)** — reframe from "~70-80% automation" to the **4-op canonical kernel + BG elaboration grammar**; the deterministic core is small, elaboration is the effort.
  - **FR-004 (lex.bg oracle)** — add MoJ/Ciela as a second oracle; oracle = witness, not truth.
  - **FR-005 (Legalize upstream)** — note Gate 0.5 is satisfied via self-consolidated multi-version history + git-dated corpus, documented per `ADDING_A_COUNTRY.md` RESEARCH-{CC}.md.
- **`docs/sync/ACTIVE.md`:** advance the current-phase note to "investigations complete; Phase 3 brainstorm next."

---

## 5. The shared design spine for Phase 3 + Phase 4

Both phases reuse the same primitives — design them once:

1. **Declension-aware Cyrillic act-name resolver** (extends FR-019 casefold): genitive title prose → corpus act, with `(ДВ,бр.N)` disambiguation; **flag-on-ambiguity** path. *(Phase 3 detector; Phase 4 elaboration target resolution.)*
2. **The typed-op model** (`{address, action, payload, provenance}`) with the 4-op kernel + elaboration layer. *(Phase 3 emits an op-type guess + confidence per material; Phase 4 lowers prose to canonical ops.)*
3. **`LegalAddress` + exact-then-unique-suffix resolution that fails loudly.** *(Both.)*
4. **Flag-don't-guess discipline** = the deterministic-or-flagged escape hatch, identical in both phases.
5. **ДВ acquisition layer** (`RateLimitedSession` over `materiali.faces`/`showMaterialDV.jsp`, charset-detecting). *(Phase 3 fetches; Phase 4 consumes the same HTML ЗИД text.)*

---

## 6. Recommended next step + open questions for the owner

**Recommended next step:** ratify §3/§4, then run the **Phase 3 (DV monitor / FR-002) brainstorm** (`superpowers:brainstorming`) → Surface-6 preflight → plan → TDD, conducted with the shared spine (§5) in view. Phase 4 follows.

**Open questions the owner should weigh in on:**
- **Q1 (the substantive one):** accept the **D-a refinement** (LawVM two-level invariants + adjudication) over the handoff's literal "byte-validate + hard-fail"? *(Recommendation: yes — it's the same intent on a proven model.)*
- **Q2:** adopt the **MoJ/Ciela portal as a second oracle** now, or keep lex.bg sole oracle for simplicity and add MoJ later? *(Recommendation: record it now, wire it when the validator is built.)*
- **Q3:** start the **Phase 3 brainstorm this session**, or pause fully here and resume next session? *(Owner already chose to pause after this brief; confirming.)*
- **Q4:** should I **apply the §4 governance edits now** (record D-a…D-d, reword the FR rows, rewrite the Phase-4 DoD), or hold all of it until after the Phase 3 brainstorm? *(These are Authority Surfaces — owner's call.)*

---

## 7. Provenance
Findings: `docs/research/2026-06-22-I1-legalize-ecosystem.md`, `…-I2-lawvm.md`, `…-I3-dv-access.md`, `…-I4-official-consolidation.md` (+ matching `*-sources.md`). All four were dispatched with the full research protocol (source log created first; every load-bearing claim traced to a verbatim `extract#N`). I1 noted a sourcing caveat (ES/EU raw READMEs 404'd → those two rest on search summaries + the authoritative BOE API docs; FR/KR/`base.py`/`ADDING_A_COUNTRY` read directly). I2 confirmed lawvm.org is substantive (repo `eliask/lawvm`, ~55 spec files). I4's negative conclusion rests on direct checks of each named official portal + the EU's own N-Lex Bulgaria page.
