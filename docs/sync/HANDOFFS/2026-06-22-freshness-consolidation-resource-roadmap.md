# Handoff / Plan: Freshness → deterministic consolidation → re-source (national functionality)

**Author:** ekimir session (Claude Opus 4.8, 1M), 2026-06-22. **For:** the next session.
**Status:** DISCUSSION outcome + scoped plan. **Nothing implemented here** — this is the starting point for the next session (owner: "discuss here, plan all for the next session").

---

## 0. Where we are

The **MCP track + time-machine are fully shipped on `main`** (`95b3b067`): PRs #3 (2.x-a FR-019/FR-018), #4 (FR-023), #5 (2.x-c logging/packaging/FR-014), #6 (FR-020 time-machine) all merged. 7 MCP tools, tools.json 1.2.0, DECISIONS→D-042, FRS→FR-024, **DEFERRED.md empty**. `catalog.db` rebuilt with FR-020 (real historical `diff()`/`get_law(date)`; 252 multi-version acts).

**Owner direction (2026-06-22):** finish the **national functionality** next, in this order — **freshness → consolidation → (re-source folds in)** — then **FR-022 municipal LAST**. Two hard constraints raised by the owner, both reframing the old plan:

1. **Re-source must be understood** — is it reading thousands of ДВ issues, deterministically rebuilding, or other? And **how does the Legalize ecosystem do it for other countries?**
2. **Phase-4 consolidation must be FULLY DETERMINISTIC** — the delivery-contract's "≥70% regex / ≥90% LLM" target is **REJECTED**. Each ДВ amendment must apply deterministically and exactly.

---

## 1. The decisive finding: how Legalize does it elsewhere, and why Bulgaria is harder

**github.com/legalize-dev** (public): Spain `legalize-es` (8,600+ laws), `legalize-fr`, `legalize-eu` (15,700+ regs), Germany, Sweden, South Korea, … Documented pipeline: *"extract **consolidated** laws from **APIs**, transform to Markdown, monitor reforms through dated git commits."*

→ **The ecosystem fetches already-consolidated text from an OFFICIAL government API** (Spain BOE, France Légifrance, EU EUR-Lex/Cellar). **It does NOT self-consolidate amendments — it relies on the state's official consolidation.** (South Korea ran an independent pipeline but still to the same spec.)

**Bulgaria has NO official consolidated-law API.** ДВ (`dv.parliament.bg`, confirmed 2026-06-22): a gazette — issues by number/date ("Брой 56, 19.6.2026"), per-document `showMaterialDV.jsp?idMat=N` URLs, "Изтегли броя" download (PDF), **no API / no feed / no consolidated text — amendments (ЗИД) only**. That is exactly *why* the pipeline chose lex.bg (a private consolidator) as the oracle (D-003) — there is no Bulgarian Légifrance.

**Consequence:** Bulgaria cannot follow the ecosystem's "fetch official consolidated text" path. It must EITHER keep a private consolidator (lex.bg/APIS) as source (the provenance FR-024/D-038 wants to retire, + the чл. 93б concern), OR **self-consolidate deterministically from ДВ** — which is the harder, sovereign path, and the reason concerns 1 & 2 exist.

---

## 2. Concern 2 — deterministic consolidation (reframed)

**Model to adopt: LawVM** (lawvm.org) — a *deterministic replay compiler* that reconstructs point-in-time statutory text from the amendment stream, reproducible/auditable, and **exposes where it diverges from the official consolidated surface** (proven on Finland, a hard amendment stream). This is the owner's "fully deterministic" bar done right.

**Design direction (to be brainstormed → decided next session):**
- Each ЗИД becomes a **typed, deterministic operation** with a precise locator: replace-text(`чл. X, ал. Y`, old→new), insert-article(`чл. Xа` after `чл. X`), repeal(`чл. X`), renumber, etc.
- Apply operations deterministically to the prior consolidated text → candidate new version.
- **VALIDATE byte-for-byte against the oracle** (lex.bg's consolidated version — D-003 keeps lex.bg as a *validation oracle* even after it is retired as the *source*). **Any divergence is a HARD FAILURE / flag for review — never a silent 70-90% accept.** Correctness is *proven by validation*, not assumed from the parser.
- This **replaces the delivery-contract Phase-4 acceptance criteria** ("≥70% regex / ≥90% LLM") → needs a `delivery-contract.md` update + a DECISIONS entry. LLM may *assist* parsing of irregular ЗИД phrasings, but the gate is the deterministic validation, not an accuracy percentage.

---

## 3. Concern 1 — full re-source (reframed)

- **"Rebuild from the corpus" cannot change provenance** — the corpus *is* lex.bg-derived consolidated text; re-deriving from it is still lex.bg.
- A real re-source = **FR-009** (already in the backlog): reverse-apply ДВ amendments (via `.HistoryOfDocument` DV references) to reconstruct each past version from ДВ primary sources, re-committed with correct `GIT_AUTHOR_DATE`. **This DEPENDS on the deterministic engine (Concern 2).** So Concern 2 is the prerequisite for Concern 1.
- **Forward** (after Phase 3 + engine): new versions are ДВ-sourced + self-consolidated → lex.bg leaves the loop. The **original bootstrap snapshot stays a legitimate one-time photograph** (D-039) until/unless FR-009 re-derives it. Full historical re-derivation is the *last* polish, not a blocker.

---

## 4. Proposed sequence (national functionality)

1. **Phase 3 — DV monitor (freshness).** Poller for new ДВ issues (Tue/Fri), detect new issues, **amendment detector** (which act(s) each ДВ issue touches — via ЗИД cross-references / `.HistoryOfDocument`), alert/log acts needing processing. Independent (needs only ДВ read access). Per delivery-contract Phase 3 DoD.
2. **Phase 4 — deterministic consolidation engine (LawVM-style, oracle-validated).** The hard, sovereign core. Replaces the 70/90% target with deterministic-apply + byte-validate-against-oracle + hard-fail-on-divergence.
3. **FR-024 — forward ДВ-sourced steady state.** Achieved *by* Phases 3+4 (lex.bg leaves the loop forward); bootstrap stays a legitimate photograph (D-039).
4. **FR-009 — full historical re-source** (optional, needs the engine; reverse-apply all ДВ history). Last national polish.
5. **FR-022 — municipal corpus** (after all national functionality; already sized ~8k acts, sourcing-cost-bound, D-037).

---

## 5. Investigations to run NEXT SESSION (scoped; do before/with planning)

- **I1 — Legalize ecosystem deep-dive.** Read `legalize-dev/legalize` (SPEC), `legalize-pipeline` (`fetcher/base.py` interfaces + any consolidation/monitor code), `legalize-es`/`-fr`/`-eu` (how they fetch consolidated text + monitor reforms + commit dated), `ADDING_A_COUNTRY.md`. **Key question:** does ANY Legalize country self-consolidate (no official API), and how? (Study South Korea's independent pipeline.) Adopt their patterns; confirm our 4 interfaces still fit.
- **I2 — LawVM study.** The deterministic replay-compiler model (lawvm.org, Finland): operation taxonomy, validation-against-official-consolidation, divergence reporting. Basis for our ЗИД engine design.
- **I3 — ДВ access + ЗИД parsing.** `dv.parliament.bg`: issue list (number/date), `idMat` document URLs, "Изтегли броя" format (PDF? HTML?), scraping approach (no API — rate-limit politely like lex.bg). **ЗИД cross-reference structure** — does ДВ link an amendment to the act(s) it changes (the `.HistoryOfDocument` ref FR-009 cites)? **PDF parsing via EMBEDDED VISION (render + Read), NOT external OCR** (global rule). Check `data.egov.bg` for any structured ДВ dataset.
- **I4 — Official BG consolidation sources.** Confirm whether ANY official consolidated-law source exists beyond private lex.bg/APIS (likely none — verify so the "self-consolidate" conclusion is grounded).

---

## 6. Open design decisions for next session

- **D-a:** Replace Phase-4 acceptance criteria (drop "≥70%/≥90%" → "deterministic apply + byte-validate vs oracle + hard-fail on divergence"). Update `delivery-contract.md` §"Phase 4" + new DECISIONS entry.
- **D-b:** Keep lex.bg as the **validation oracle** (D-003) even after retiring it as the **source** (consistent with D-039 — we never re-use its DB, only validate our own ДВ-derived output against it).
- **D-c:** Re-source strategy — forward-only (Phase 3+4 + D-039 bootstrap legitimacy) as the near-term, FR-009 full historical re-derivation as deferred polish.
- **D-d:** Process — Phase 3 and the engine each get brainstorm → preflight (Surface 6 / fetcher interfaces) → plan → TDD, on branches, owner-merged.

---

## 7. Session-start read path (next session)
`.claude/CLAUDE.md` → `docs/sync/ACTIVE.md` → `docs/sync/DEFERRED.md` (empty) → `docs/process/delivery-contract.md` (Phase 3/4 DoD — note the Phase-4 criteria change pending, D-a) → THIS handoff → `docs/frs/INDEX.md` (FR-009, FR-024 near-term) → `docs/plans/2026-04-19-legalize-bg-design.md` (consolidation engine §). Memory: `project_legalize_bg.md`.
