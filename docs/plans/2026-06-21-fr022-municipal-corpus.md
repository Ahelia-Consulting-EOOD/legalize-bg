# FR-022 — Municipal Legislation Corpus — Plan (investigation + global-workflow design)

> **Status: PLAN ONLY.** Execution is gated on (1) PR #3 (batch 2.x-a) merged, and (2) the remaining MCP-track work finished — per owner directive 2026-06-21 ("finish MCP work before the municipal one"). This document records the live investigation (2026-06-21) and the global-workflow shape to execute later. FR-022 / D-035 / D-006 (timing superseded).

**Goal:** Build a Bulgarian *municipal* legislation corpus (наредби / правилници / инструкции на общинските съвети) as a separate track alongside the national corpus, with authoritative metadata and incremental coverage over time.

---

## 1. Live investigation findings (2026-06-21)

### 1.1 Legal framework — how municipal acts are made & published (authoritative, from our own corpus)

- **Power to legislate — ЗМСМА чл. 21(2)** (`laws/zakon-za-mestnoto-samoupravlenie-i-mestnata-administratsiya.md`): *"В изпълнение на правомощията си … общинският съвет приема **правилници, наредби, инструкции, решения, декларации и обръщения**."* The normative instruments are **правилници + наредби + инструкции** — exactly matching the 104 municipal acts found in the FR-011 triage.
- **General publication rule — ЗНА чл. 37(3)** (`laws/zakon-za-normativnite-aktove.md`): *"Нормативните актове на общинските съвети се обнародват **в печата или се разгласяват по друг начин на територията на общината**."* — local press / local dissemination, **NOT** Държавен вестник. (чл. 37(1) reserves ДВ for laws, CoM acts, ministerial/agency acts; чл. 8 confirms councils issue наредби for local-significance matters.)
- **Dissemination + the ДВ exception — ЗМСМА чл. 22(2):** acts are disseminated to the population *"чрез средствата за масово осведомяване, чрез интернет страницата на общинския съвет или на общината…"* **AND** *"Актовете на общинския съвет се обнародват в «Държавен вестник», **когато това е предвидено със закон**."*
  - **→ This reconciles the owner's "we see municipal work in ДВ":** TRUE, but only for the **subset** of municipal acts a specific law mandates into ДВ. The *default* channel is local (council/municipality website + mass media). чл. 22(3) also obliges municipalities to keep paper copies of the last 10 years accessible.
- **Procedure / drafting — ЗНА чл. 26(3)** (draft published on the municipality/council website for consultation) + **АПК чл. 75–79** (подзаконови нормативни актове procedure).

**Sourcing implication:** ДВ is **not** the primary source for the municipal corpus — only the law-mandated minority appears there. The authoritative channels are the **municipal councils' own publications** (their websites) and the aggregator portals that mirror them.

### 1.2 The APIS `obshtini.bg` portal — structured, API-accessible, but commercial

- **What it is:** `sofia.obshtini.bg` (and `{municipality}.obshtini.bg`) is **APIS's commercial "Общински нормативни актове" SaaS** (apis.bg/bg/municipal-norm-acts). Municipalities contract APIS to host their normative acts publicly; APIS maintains **current + historical versions incl. repealed norms**. Sold in two tiers (capital/regional vs. others). Governed by APIS "Общи условия за ползване".
- **It is a JS SPA backed by a public JSON API** (`web-api.apis.bg`). Verified live for the example `https://sofia.obshtini.bg/doc/5353100/0` (НАРЕДБА за реда и условията за пътуване с обществения градски транспорт … Столична община, редакция 23.02.2023):
  - `GET web-api.apis.bg/api/obshtina-{slug}/DocInfo?uniqueId={id}&dbIndex={n}` → metadata (200).
  - `GET …/DocContent?uniqueId=&dbIndex=` → rendered content (200).
  - `GET …/DocTextJson/?uniqueId=&dbIndex=&searchText=` → text as JSON (200).
  - `…/DocList` → **405** (endpoint exists; needs POST/params) — the likely **enumeration** hook.
  - The portal URL `/doc/{uniqueId}/{dbIndex}` maps 1:1 to the API params; each municipality = its own subdomain → `obshtina-{slug}` API path.
- **`DocInfo` payload is rich and solves the FR-011 date gap:**
  ```json
  {"document":{"uniqueId":5353100,"caption":"НАРЕДБА за реда и условията…",
    "publDate":"2023-02-23","startDate":"2018-04-05","endDate":"2023-05-25",
    "isActual":1,"code":"54730","dv":null,"version":null},"hasVersions":true}
  ```
  - `caption`→`titulo`; `publDate`/`startDate`/`endDate`→ real `fecha_publicacion`/`effective_date`/validity; `isActual`→`estado`; `hasVersions:true`→ multiple редакции (temporal corpus, like FR-020 but for municipal). **`dv:null`** for this act = data-level confirmation of ЗНА чл. 37(3) (not in ДВ).
- **Scrapability verdict:** *technically* highly scrapable (clean public JSON, stable IDs, per-municipality subdomains, version-aware). **BUT** it is a **third-party commercial product** → **ToS / legal risk for bulk extraction.** Must not be treated as a free bulk source without due diligence.

### 1.3 The 104 municipal acts already in our corpus

The FR-011 triage's 104 municipal acts (Sofia + Veliko Tarnovo, in `ordinances/`) were scraped from **lex.bg**, which carried them **without dates** (null `fecha_publicacion`). The APIS `DocInfo` shows those dates **do exist** at the municipal source — so FR-022 can backfill them authoritatively and relocate these acts into a proper `municipal/` structure.

---

## 2. Source strategy (decision needed before execution)

Ranked by authority + legal safety:

1. **Official municipal council / municipality websites** (legally the dissemination channel per ЗМСМА чл. 22(2)) — authoritative, public, but **heterogeneous** (265 municipalities, each a different site; D-006's core difficulty). Best for legality; worst for uniformity.
2. **APIS `obshtini.bg` portals** — uniform, structured, version-aware, metadata-rich; covers the municipalities that contract APIS (incl. Sofia, Veliko Tarnovo). **Commercial → requires ToS review and likely an explicit arrangement with APIS** before any systematic extraction.
3. **ДВ (dv.parliament.bg)** — only the law-mandated subset of municipal acts; NOT a general municipal source. Useful as a cross-check for the acts that DO appear there.

**Open decision (owner):** which source(s) to build on. Recommended: **start with the municipalities already partly in our corpus (Sofia, Veliko Tarnovo)** and **resolve the APIS ToS question first** (review "Общи условия", and/or approach APIS — they already sell municipal data; a data arrangement may be cleanest). If APIS is off-limits, fall back to per-municipality official sites with bespoke adapters.

---

## 3. Storage & schema

- **Directory:** the top-level `municipal/` directory is **already reserved** as a protected surface (`.ahelia/protected-surfaces.yaml`) — use it. Same Markdown + YAML frontmatter contract as the national corpus.
- **Frontmatter mapping** (from APIS `DocInfo`, or municipal-site equivalents): `titulo`←caption, `fecha_publicacion`←publDate, `effective_date`←startDate, `estado`←isActual, plus a municipality field (e.g. `obshtina: stolichna`) and source provenance. **No `dv_issue` for the local-published majority** (it's legitimately absent — consistent with the FR-011 WAIVERS finding).
- **Frontmatter schema is Protected Surface 2 (additive only)** → adding a `municipal`/`obshtina` extension field needs an IMPLEMENTATION-PREFLIGHT.
- **Versions:** `hasVersions:true` → model редакции like the national temporal index (one `law_versions` row per редакция; pairs with FR-020/FR-014).

---

## 4. Integration (MCP — the product)

- Extend the SQLite index + `search` category filter to include a `municipal` category. **Decision needed:** is `municipal` in the **default** search scope or **opt-in** (a `scope=municipal|national|all` param)? Recommend opt-in initially so national-law agents aren't flooded by local acts.
- `get_law` / `get_articles` resolve municipal acts by the same handle rules; ambiguity across municipalities (two councils with same-titled наредби) → the existing `AMBIGUOUS_NAME` candidate mechanism, disambiguated by municipality.
- Tool signatures are Protected Surface 3 → any new param/category is additive + preflight.

---

## 5. Global-workflow execution shape (run AFTER the gate)

A deterministic Workflow (Mode D) over a discovered work-list, scaled per municipality:

- **Phase 0 — Legal/ToS clearance (manual gate):** resolve the APIS ToS / source decision in §2. **Blocks everything else.**
- **Phase 1 — Discover:** for each target municipality, enumerate its acts (APIS `DocList` POST probe, or the official site's index). Produce a work-list of `{obshtina, uniqueId/url, caption}`.
- **Phase 2 — Fetch + assemble (pipeline, rate-limited):** per act → fetch metadata + text (+ each version) → assemble Markdown + frontmatter. Reuse the national `fetcher`/`refresh.py` rate-limit + commit machinery (1 req/s, descriptive UA, backoff, stop-on-challenge). Worktree isolation per parallel worker if fetching concurrently.
- **Phase 3 — Validate:** frontmatter G2 against schema; spot-check N acts against the source (embedded-vision render+read, never external OCR per global rule); dedupe vs the 104 acts already in the corpus and **backfill their dates**.
- **Phase 4 — Index + integrate:** rebuild SQLite with the municipal category; smoke-test MCP `search`/`get_law` on municipal acts.
- **Phase 5 — Coverage policy:** incremental ("with time") — start Sofia + Veliko Tarnovo, expand municipality-by-municipality; log coverage, never claim completeness.

**Commit convention:** municipal corpus commits follow the Legalize commit format; `[bootstrap]`/`[nova]`/`[reforma]` as appropriate, with municipality in the body. (Commit format = Protected Surface 5 — reuse, don't change.)

---

## 6. Risks & open questions

| Item | Risk / question | Mitigation |
|---|---|---|
| APIS ToS | Bulk extraction from a commercial product may breach "Общи условия" | **Phase-0 gate:** review terms / approach APIS / fall back to official municipal sites |
| 265-municipality heterogeneity (D-006) | Each official site differs → many bespoke adapters | Start with APIS-covered + highest-value councils; expand incrementally |
| Source authority | APIS is an aggregator, not the legal publisher | Treat the municipal council/website as authoritative; record provenance per act |
| Frontmatter/schema change | Surface 2 (additive) | Preflight for the `obshtina` field |
| Search scope flooding | 1000s of local acts diluting national search | `municipal` opt-in / separate scope |
| Versions | редакции modeling | Reuse national temporal design (FR-020/FR-014) |

## 7. Immediate (pre-execution) checklist when the gate opens

1. Owner decision on §2 source + the APIS ToS question (Phase-0).
2. `superpowers:brainstorming` on scope/coverage + the schema (`obshtina` field) → IMPLEMENTATION-PREFLIGHT (Surfaces 2 + 3).
3. `superpowers:writing-plans` → a concrete per-phase implementation plan with the discovery/fetch adapters.
4. Then author the Workflow per §5.

---

### Evidence log (investigation 2026-06-21)
- ЗМСМА чл. 21(2), 22(2), 22(3) — `laws/zakon-za-mestnoto-samoupravlenie-i-mestnata-administratsiya.md`.
- ЗНА чл. 8, 37(1)/(3), 26(3) — `laws/zakon-za-normativnite-aktove.md`.
- APIS product: apis.bg/bg/municipal-norm-acts ("Общински нормативни актове"); ToS: apis.bg/bg/obshti-usloviya-za-polzvane-na-informatsionni-sistemi-apis.
- Live API (verified 200, in-browser): `web-api.apis.bg/api/obshtina-sofia/{DocInfo,DocContent,DocTextJson}?uniqueId=5353100&dbIndex=0`; `DocList` → 405 (exists). DocInfo payload schema captured above.
- ДВ structure (unofficial section carries some municipal administrative acts): dv.parliament.bg; pravatami.bg/s/15211.
