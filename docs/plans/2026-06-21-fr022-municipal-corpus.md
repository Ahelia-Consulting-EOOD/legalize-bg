# FR-022 — Municipal Legislation Corpus — Plan (investigation + global-workflow design)

> **Status: PLAN ONLY.** Execution is gated on (1) PR #3 (batch 2.x-a) merged, and (2) the remaining MCP-track work finished — per owner directive 2026-06-21 ("finish MCP work before the municipal one"). This document records the live investigation (2026-06-21) and the global-workflow shape to execute later. FR-022 / D-035 / D-006 (timing superseded).

**Goal:** Build a Bulgarian *municipal* legislation corpus (наредби / правилници / инструкции на общинските съвети) as a separate track alongside the national corpus, with authoritative metadata and incremental coverage over time.

---

## 0. Owner decision — sourcing strategy (2026-06-21, D-037) — THE WAY

> Settles the Phase-0 source question (§2/§8) by owner directive.

**Treat APIS `obshtini.bg` exactly like lex.bg for the national corpus: a ONE-TIME bootstrap snapshot — and, in parallel, build per-municipality official-site adapters as the durable ongoing source.** This mirrors the national doctrine precisely (D-002/D-003): *lex.bg = bootstrap/oracle, DV = ongoing* → here *APIS = bootstrap/oracle, municipal sites = ongoing*.

- **Bootstrap (one-time):** scrape APIS once to seed the municipal corpus with structured, version-aware data (the `DocInfo`/`DocContent` JSON, which also carries the publication dates lex.bg lacked). Like the lex.bg bootstrap, this is a single photograph, not a recurring dependency.
- **Ongoing (durable):** identify + develop **catalog/discovery + fetch adapters for each municipality's own website** (the legally-mandated publication channel, ЗМСМА чл. 22(2)) — these become the authoritative source for updates, making the APIS touch transient.
- **Legal posture (see §8):** the act *texts* are public-domain (ЗАПСП чл. 4); a one-time APIS bootstrap still extracts a *substantial part* of APIS's чл. 93б database (ToS II.5/II.6) → keep it minimal and/or clear it with APIS, and rely on the parallel municipal-site adapters so the APIS extraction is one-off, not systematic. (Owner has chosen the lex.bg-style one-time treatment knowing this; recorded for an informed decision.)
- **Status:** plan + record only; **execution left for a future session**, gated on PR #3 merge + MCP-track completion ("finish MCP before municipal").

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

**Decision (owner, D-037 — see §0): RESOLVED.** APIS = one-time **bootstrap** (like lex.bg); per-municipality official sites (source 1) = the durable **ongoing** source, built in parallel. Start with Sofia + Veliko Tarnovo. Keep the APIS bootstrap minimal and/or clear it with APIS (§8); the ongoing municipal-site adapters make the APIS touch one-off.

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

## 8. APIS legal gate — detailed analysis (Phase-0 input)

**Bottom line: the act *texts* are free, but APIS's *database* is not — and that distinction is the whole gate. Do NOT bulk-extract `web-api.apis.bg`.**

### 8.1 The act texts themselves are public domain
- **ЗАПСП чл. 4, т. 1** (`laws/zakon-za-avtorskoto-pravo-i-srodnite-mu-prava.md`): *"Не са обект на авторското право: 1. нормативни и индивидуални актове на държавни органи за управление, актовете на съдилищата, както и официалните им преводи"* — and т. 4: *"новини, факти, сведения и данни"*. Municipal наредби/правилници are нормативни актове → **not copyrightable**. Copying the *content* of any municipal act is always lawful, from any source.

### 8.2 …but APIS holds a *sui generis* database right over its compilation
- **APIS ToS I.1.1** explicitly: *"«АПИС» е производител на база данни по смисъла на чл. 93б от ЗАПСП и носител на всички права на интелектуална собственост."*
- **ЗАПСП чл. 93б**: the database *producer* — the party that made a *"съществено в количествено или качествено отношение"* investment in collecting/verifying/presenting the content — holds the right. APIS's curated, consolidated, **version-tracked** municipal compilation is exactly such an investment.
- **ЗАПСП чл. 93в(1)** — the operative prohibition: the producer may forbid *"1. извличането ... на съдържанието на базата данни или на негова **съществена** ... част ... под каквато и да е форма; 2. повторното използване ... на негова **съществена** ... част ..."* — i.e. **extraction or re-utilization of a *substantial part*** of the database, by any means.
- **→ Systematic harvesting of `web-api.apis.bg/api/obshtina-*/Doc*` is precisely "извличане на съществена част" of APIS's database** — prohibitable under чл. 93в *even though every individual наредба text is copyright-free (чл. 4)*. The free-ness of the texts does **not** grant a right to lift a substantial part of APIS's *compilation*.

### 8.3 The APIS Terms of Use (apis.bg "Общи условия") confirm it
- **II.5:** *"Всяко използване, възпроизвеждане ... с търговска цел или за да се извлече друга облага без разрешение на «АПИС» е забранено."*
- **II.6:** *"Никой няма право без изричното разрешение на «АПИС» да разпространява с търговска цел цялата или част от базата данни."*
- **I.4:** no third-party access without prior written APIS consent. **III.10:** no decompiling/reverse-engineering.
- **II.3–4:** download/print/copy is permitted only for the *client's internal* use, with copyright notices intact.
- Scraping/bots/API are **not explicitly named**, and the public `obshtini.bg` portals are **not mentioned** in the general ToS — but the чл. 93б/93в database right applies regardless of an explicit anti-scraping clause.

### 8.4 The "it's a public portal" argument does NOT clear the gate
Municipalities pay APIS to *display* their acts to citizens at `{obshtina}.obshtini.bg`. That is a public **display/consultation** license — not a license to **extract and re-utilize a substantial part**. The unauthenticated `web-api` endpoints exist to serve APIS's own SPA front-end; using them for bulk harvest is the textbook database-right scenario (cf. EU Database Directive 96/9/EC; *Innoweb/Ryanair* line of cases).

### 8.5 The TDM exceptions — a narrow possible path, not a green light
Bulgaria transposed the EU DSM Directive (2019/790) TDM exceptions:
- **ЗАПСП чл. 26е** (general text-&-data-mining): permits automated extraction *"от лице, което разполага с **правомерен достъп**"* (lawful access) — including *"извличане ... по смисъла на чл. 93в на бази данни"* — **BUT** чл. 26е(4): the rightholder may **opt out** for electronically-accessed content via machine-readable means. For APIS, "lawful access" normally means a paid subscription, and a commercial ToS prohibiting reproduction functions as that reservation. **Not a reliable basis for bulk extraction.**
- **ЗАПСП чл. 26ж** (TDM for scientific research): broader (no opt-out), but **only for** universities, research institutes, public libraries/museums/archives, and non-profit/public-interest research organisations. legalize-bg is an Ahelia private project — it does **not** plainly qualify. *(If the corpus were produced under/with a qualifying research institution, чл. 26ж could change the analysis — a strategic option, not a default.)*

### 8.6 Clean paths (ranked) — the actual Phase-0 decision
- **(A) Source from the municipal councils' own websites** — the legally-mandated publication channel (ЗМСМА чл. 22(2)); the official act text there is public-domain (чл. 4) and **no APIS database right attaches to the council's own publication**. Cleanest, and mirrors our national pattern (scrape the *source*, not an aggregator — lex.bg was bootstrap-only, DV is the ongoing source). Cost: 265 heterogeneous sites → bespoke adapters, start with the highest-value councils.
- **(B) Data agreement / license with APIS** — APIS already *sells* municipal data; a licence removes the gate and yields uniform, structured, version-aware data (incl. the dates our lex.bg-sourced acts lack). Cost: commercial + negotiation.
- **(C) Municipal open data / ЗДОИ requests** — some municipalities publish open data or must provide acts on request (ЗМСМА чл. 22(3) keeps 10 years accessible; ЗДОИ access-to-public-information).
- **(D) Research-institution route** — partner with a qualifying body to rely on чл. 26ж.
- **Either way:** respect `robots.txt` / TDM opt-out, rate-limit, attribute. APIS may still be used the way lex.bg is for the national corpus — as a *validation oracle* for a handful of acts — without harvesting a substantial part.

**Recommendation → superseded by owner decision D-037 (§0):** APIS is used as a **one-time bootstrap** (like lex.bg — a single photograph, not a systematic ongoing feed), and **(A)** the per-municipality official sites are the durable ongoing source built in parallel. This keeps the legally-clean municipal sites authoritative while the (substantial-part) APIS extraction stays one-off; keep that bootstrap minimal and/or clear it with APIS. `web-api.apis.bg` is therefore the bootstrap **oracle**, not the corpus's ongoing source.

---

### Evidence log (investigation 2026-06-21)
- ЗМСМА чл. 21(2), 22(2), 22(3) — `laws/zakon-za-mestnoto-samoupravlenie-i-mestnata-administratsiya.md`.
- ЗНА чл. 8, 37(1)/(3), 26(3) — `laws/zakon-za-normativnite-aktove.md`.
- APIS product: apis.bg/bg/municipal-norm-acts ("Общински нормативни актове"); ToS: apis.bg/bg/obshti-usloviya-za-polzvane-na-informatsionni-sistemi-apis (clauses I.1.1 DB-producer per чл.93б; I.4 no third-party access; II.2 rights reserved; II.3–4 internal copies; II.5–6 no commercial reproduction/distribution of the DB; III.10 no reverse-engineering; scraping/API not explicitly named).
- ЗАПСП (`laws/zakon-za-avtorskoto-pravo-i-srodnite-mu-prava.md`): чл. 4 т.1/т.4 (official acts + facts/data not copyrightable); чл. 93б (database-producer sui generis right); чл. 93в(1) (prohibit extraction/re-utilization of a *substantial part*); чл. 26е (general TDM — lawful access + opt-out); чл. 26ж (research-institution TDM — no opt-out). EU basis: Database Directive 96/9/EC; DSM Directive 2019/790 arts. 3–4.
- Live API (verified 200, in-browser): `web-api.apis.bg/api/obshtina-sofia/{DocInfo,DocContent,DocTextJson}?uniqueId=5353100&dbIndex=0`; `DocList` → 405 (exists). DocInfo payload schema captured above.
- ДВ structure (unofficial section carries some municipal administrative acts): dv.parliament.bg; pravatami.bg/s/15211.
