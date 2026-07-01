# FR-025 (redirected) — Comprehensive act-type coverage via delegation-chain discovery (design)

**Status:** Design draft 2026-07-02 (brainstorm, owner-steered). **Planning artifact — no implementation yet.** Supersedes the sourcing approach in `docs/plans/2026-07-02-fr025-category-coverage-design.md` (tree-crawl), which the discovery finding invalidated.
**Requirement:** FR-025 (redirected). **Defect:** D-049 (addendum 2026-07-02). **Converges with:** FR-024 (re-source) + roadmap-Phase-3 (ДВ monitor). **Carved out:** FR-026 (annex-as-separate-doc). **Legal posture:** D-039.
**Finding that triggered this:** `docs/research/2026-07-02-fr025-category-gap.md`.

## 1. Why the approach changed

The tree-crawl plan assumed lex.bg exposes N browsable act-type trees and we crawl 5. The 2026-07-02 discovery spike proved lex.bg exposes **only** those 5 browsable trees; ПМС/тарифи/инструкции/решения/укази are not tree-enumerable there (only per-`ldoc` or keyword search). So coverage of those act-types cannot come from "add tree slugs"; it needs a source that enumerates by act-type, plus a way to *know what should exist*. This design does both.

## 2. Completeness model — HYBRID (owner, 2026-07-02)

Two independent completeness signals; discrepancies are flagged for review (mirrors the LawVM two-level model from the 2026-06-22 investigations):

- **Primary = delegation graph (derived truth).** Every lesser act is issued under an explicit delegation in a higher act. Parse those references from acts we already hold to DERIVE the set of lesser acts that *should* exist. Each derived act we do not hold = a provable gap. Completeness = every delegation resolved (held, fetched, or explicitly waived).
- **Second = external enumeration (independent check).** Enumerate target act-types from an external authoritative source; diff against the corpus. Discrepancies between the two signals (delegation says X should exist but no source has it; a source lists Y that no delegation predicted) are flagged, not silently resolved.

**Feasibility evidence:** 2,377 / 2,628 наредби (90%) already contain "на основание чл. X …[Закон]"; the delegation language is regular and machine-parseable.

## 3. Delegation-chain mechanism

- **Directions.** (a) *Bottom-up* (child→parent): the "на основание" citation in acts we hold — builds the graph and validates parent existence. (b) *Top-down* (parent→child): "…се определя/приема с наредба/тарифа/инструкция на …" clauses in закони/ПМС — reveals EXPECTED children, some of which we LACK. Direction (b) is the gap-discovery engine.
- **ПМС are special:** often the *vehicle* that adopts a наредба/тарифа (the НСС case), not a leaf act. The parser must treat "ПОСТАНОВЛЕНИЕ … за приемане на …" as both an act to hold AND a delegation edge to the adopted instrument.
- **Resolver:** map a delegated reference (act-type + issuing body + subject + citation) to a concrete act (held, or a search target). Declension-aware, fail-loud (unique-confident hit or flag) — reuse the FR-019 casefold + the resolver posture settled in the paused Phase-3 brainstorm (handover 2026-07-01 §3 decision #4).
- **Version-aware:** a delegated act may have many versions; discovery records the identity, fetch/versioning follows the FR-020 model (author-dated commits; `[popravka]` corrigenda excluded from version boundaries per D-047/Task 13).

## 4. Source landscape (with legal posture, D-039)

| Source | Role | Posture / caveat |
|---|---|---|
| **ДВ — dv.parliament.bg** (`materiali.faces?idObj`→`showMaterialDV.jsp?idMat`) | Canonical enumeration + text; publishes EVERY act-type | Public-domain (D-039-clean). **Only last ~7 years online, as PDF.** IS the FR-024/Phase-3 acquisition layer. Older issues need another route. |
| **N-Lex** `n-lex.europa.eu/n-lex/legis_bg` | Structured search gateway over ДВ | EU official; **backend is APIS** — treat results as pointers, not a DB to reuse. |
| **justice.government.bg** (MoJ/Ciela) | Independent cross-check oracle + fetch fallback | Free, official-domain, HTML. Curated/PARTIAL — not complete alone. |
| **APIS** `web-api.apis.bg` | Read-only enumeration/count oracle | **Commercial, ToS-gated. D-039 forbids DB reuse** — cross-check counts only, never a text/structure source. |
| **lex.bg keyword search** (`/search`, CF-hardened) | Fetch channel: locate a specific delegation-derived act by title | Incomplete/ranked — not an enumeration. We hold the access. |
| **data.egov.bg** (open-data portal) | "Enlisting" hint source: ministries may publish act lists | Not canonical text; discovery hints only. |
| **Lex Alert** `lexalert.bg` | Freshness/monitoring reference | Commercial; reference only. |

## 5. Phased approach (research-first; detailed TDD plan deferred until Phase A informs it)

- **Phase A — ДВ landscape survey (empirical, next-session first step).** Fetch 20–30 full recent ДВ issues; catalogue the act-types actually published + their structure; confirm the `idObj`→`idMat` access path; assess the 7-year/PDF limit. This materializes what we're enumerating BEFORE committing the enumeration design. (Owner's suggestion.)
- **Phase B — delegation-parse prototype.** On the corpus we hold, extract both delegation directions; produce a first derived expected-set + the provable-gap list; measure resolver precision/recall on a sample (eval-harness discipline).
- **Phase C — source-access spikes.** Confirm access + legal posture for ДВ, justice.gov, N-Lex; establish APIS/Ciela as oracle-only. One tiny spike each.
- **Phase D — design freeze + detailed TDD plan.** With A–C evidence, write the implementation plan (discovery module, resolver + eval harness, hybrid coverage gate over the derived expected-set, per-act-type `rango`, CF-hardened/ДВ fetch, version-aware ingest, catalog + close-out).
- **Phase E — implementation** (per the Phase-D plan).
- **Interim throughout:** on-demand per-act `ldoc` capture (D-049 decision 2) remains the stopgap for specific consumer needs (e.g. DRS).

## 6. Reused mechanisms from the superseded plan

- Probe-to-end discovery (no hard-coded page counts) — still worth applying to the existing 5-category crawl (robustness).
- Corpus-level coverage gate — repurposed to run over the DERIVED expected-set (delegation graph), not a lex.bg tree manifest.

## 7. Risks / open questions (for Phase A–C to resolve)

- **R1 — ДВ historical depth.** dv.parliament.bg only serves ~7 years online as PDF; pre-~2019 act-types need another source (older ДВ archives, justice.gov, or accept a historical floor). OPEN.
- **R2 — PDF text extraction.** ДВ issues are PDF; per house rules, PDF text is read via agent vision at orchestration time, not an OCR lib — bulk cost implication. OPEN (Phase A informs).
- **R3 — resolver ambiguity.** Declension + generic titles → false matches; must fail-loud + ship an eval harness (Phase B).
- **R4 — legal posture on APIS/N-Lex.** N-Lex is APIS-backed; keep to pointers/counts, never DB reuse (D-039). Confirm in Phase C.
- **R5 — scope/depth of the chain.** How deep (закон→наредба→указания…) and whether to include individual/ephemeral acts (укази-appointments). Owner scope-gate after Phase B's gap list.
- **R6 — versioning.** Multiple versions per delegated act; align with FR-020 (D-042 + D-047/Task 13).

## 8. Out of scope
- Annex/приложение-as-separate-document capture → FR-026.
- Existing coarse `rango` fix for laws/codes/ords/regs → separate data-quality item.
- Municipal (FR-022), freshness/consolidation engine (roadmap Phase 3/4) beyond the ДВ-acquisition convergence.
