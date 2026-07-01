# I1 — Legalize ecosystem deep-dive

**Investigation:** I1 (freshness/consolidation/re-source roadmap). **Date:** 2026-06-22.
**Sources log:** [2026-06-22-I1-legalize-ecosystem-sources.md](./2026-06-22-I1-legalize-ecosystem-sources.md)

Every load-bearing claim below traces to an `extract#N` row in the sources log.

---

## RQ1 — The Legalize SPEC and pipeline (data model + the 4 fetcher interfaces)

**Ecosystem shape.** `github.com/legalize-dev/legalize` is the umbrella project: "Legislation as code. Every law as a Markdown file. Every reform as a Git commit," covering "structured legal data from 31 countries." The data model is uniform: "Each law is a Markdown file with YAML frontmatter. When a reform is published, the file is updated and committed with the official publication date" — so git history *is* the version history (extract#1). The umbrella's stated raison d'être is telling: "Official sources publish consolidated versions with no way to compare. Commercial providers charge hundreds per month for version history" (extract#1). The project's premise is that **an official source already publishes consolidated versions** — Legalize's value-add is putting them under version control, not producing the consolidation.

**Pipeline.** `legalize-dev/legalize-pipeline` (Python) is a three-stage architecture: **fetch** ("Fetch laws to data/ (does not touch git)") → **commit** ("Generate git commits from local data/ (does not download)") → **bootstrap** ("Full pipeline: fetch + commit"). Reforms are tracked via a "Daily incremental update" command (`legalize daily -c es --date 2026-03-28`); "Every reform is a commit" dated with the official publication date (extract#2).

**The 4 fetcher interfaces** (verbatim from `src/legalize/fetcher/base.py`, extract#5; corroborated by ADDING_A_COUNTRY.md, extract#6):

1. **`LegislativeClient`** — "Base class for country-specific legislative API clients."
   - `get_text(norm_id: str) -> bytes` — **"Fetch the consolidated text of a norm (XML or HTML)."**
   - `get_metadata(norm_id: str) -> bytes`
   - `close() -> None` (plus a `create()` classmethod per ADDING_A_COUNTRY.md)
2. **`NormDiscovery`** — "Base class for discovering norms in a country's catalog."
   - `discover_all(client, **kwargs) -> Iterator[str]`
   - `discover_daily(client, target_date: date, **kwargs) -> Iterator[str]` — "Discover norms published/updated on a specific date."
3. **`TextParser`** — "Base class for parsing **consolidated text** into structured blocks."
   - `parse_text(data: bytes) -> list[Any]` — "Parse consolidated text into a list of Block objects."
4. **`MetadataParser`** — "Base class for parsing norm metadata."
   - `parse(data: bytes, norm_id: str) -> NormMetadata`

**Decisive observation:** the interface contract bakes consolidation into the *source*. `get_text` is literally typed to return "the **consolidated** text of a norm"; `TextParser` parses "**consolidated** text." There is **no interface for an amendment/diff operation** — no `apply_amendment`, no patcher, no ЗИД operation type. The pipeline has no place to *do* consolidation; it only fetches text that is already consolidated. This matches our design doc, which lists the consolidation engine as "**No** — doesn't exist [in Legalize]; We build this at Ahelia" (D3, design doc, Legalize Integration Points table).

## RQ2 — How API-backed countries do it (ES / FR / EU + DE / SE)

Confirmed: **every API-backed country fetches already-consolidated text from an official state source and does NOT self-consolidate.**

- **Spain (`legalize-es`, 8,600+ laws):** "Data is obtained from the BOE's (Boletín Oficial del Estado) open data API" (extract#3). The BOE itself runs the official **Legislación Consolidada** REST API: "The State Agency BOE has made available to reusers a series of REST APIs that allow downloading, using and reusing **consolidated** legal norms," with endpoints for "**consolidated text of a norm by identifier**" and "blocks of a norm by identifier" (extract#4). The pipeline's Spain parser is "BOE XML -> Block/NormMetadata" (extract#2) — pure transformation of pre-consolidated XML. **AEBOE's documentary services produce the consolidation; the pipeline only transforms it.**
- **France (`legalize-fr`):** "Données issues de la base LEGI (open data, licence ouverte Etalab 2.0), publiée par la DILA." Explicitly: "The repository **does not self-consolidate amendments**. Instead, it retrieves **pre-consolidated versions** directly from the official LEGI database maintained by DILA." Each file is "texte consolidé"; "the actual legal text comes pre-consolidated from LEGI/Légifrance rather than being amended incrementally by this project" (extract#8). This is the single most explicit statement in the whole ecosystem.
- **EU (`legalize-eu`, 15,700+ regs, 1958–present):** sourced from EUR-Lex; "The repositories store **consolidated** legislation, meaning they include the current state of laws with all reforms applied" (extract#3). EUR-Lex/Cellar publishes the consolidated families; the pipeline transforms them.
- **Germany (`legalize-de`-equivalent, 5,729 laws):** sourced from `gesetze-im-internet.de`, the Federal Ministry/Office of Justice site that provides "the entire body of current federal law ... in their **current consolidated version as amendments are incorporated**" — i.e., the **German state incorporates the amendments** (extract#10).
- **Sweden (8,947 laws):** the pipeline "includes a Sweden (SFSR / Riksdag) fetcher with a Riksdag API client and SFS catalog discovery" — the official SFS register, again a state-consolidated source (extract#10).

## RQ3 — THE KEY QUESTION: does any country self-consolidate?

**No Legalize country self-consolidates from a raw amendment stream. None.**

The handoff's claim that "South Korea ran an independent pipeline" is **true but misleading** — "independent" means an *independent codebase/organization*, NOT independent (self-)consolidation:

- Korea has its own GitHub org `legalize-kr` (5,575 laws, a community contribution), its own pipeline, and even its own **Rust `compiler` repo** (extract#7). The umbrella confirms a country may "use the shared legalize-pipeline or build their own pipeline, **as long as output follows the specification**" — so "independent" = independent implementation of the same spec (extract#7).
- But Korea's **source is still an official state API that supplies consolidated text + official version history**: "모든 법령 데이터는 국가법령정보센터 OpenAPI(open.law.go.kr)에서 가져옵니다" (all data from the National Law Information Center OpenAPI) (extract#7). That API exposes "**현행법령**" (current in-force law) full text and "**법령 연혁**" (law-history / version list) endpoints, providing "the original text and metadata ... article numbers, enforcement dates, **revision history** ... Users can **compare current laws with past articles**" (extract#9). So the **Korean state** supplies both the consolidated current text and the per-version history; legalize-kr's own `compiler` is a transform/commit tool ("receives .cache/ ... to directly write bare Git repositories"), with **no documented amendment-application logic** (extract#7).
- Germany and Sweden likewise read state-consolidated sources (extract#10). No examined country (ES, FR, EU, DE, SE, KR) applies ЗИD-style amendment operations to reconstruct text.

**How a country WOULD cope without an official consolidation** (per the spec — RQ4): not by building a deterministic amendment-replay engine, but by **periodic re-download to accumulate history post-hoc** — and only as an explicitly *temporary* "single-snapshot" ship that must be documented and followed up (extract#6). The ecosystem has **no first-class support for self-consolidation at all.**

## RQ4 — ADDING_A_COUNTRY.md: the hard gates + the no-official-consolidation case

`ADDING_A_COUNTRY.md` exists in `legalize-pipeline` and restates the 4 interfaces (extract#6). Its mandatory gates (named by section number, not literally "G1–G4"):

- **Gate 0.5 — Version History Spike:** "If you cannot extract at least **2 distinct versions with dates** for a single law, stop and investigate." (The gate that Bulgaria structurally *cannot* pass from any official source — see Implications.)
- **Gate 0.7 — Format Coverage:** "Every format that contributes > 1% of unique laws or unique versions MUST be covered by the fetcher."
- **Gate 7.2 — AI Review:** "The parser is not ready until the agent reports all five [checks] as PASS for all 5 laws."
- **Gate 9.3 — Health Check:** "Every issue reported must be zero before pushing. `legalize health -c xx` reports zero issues."

(These are the ecosystem's current gate names. Our internal docs paraphrase "4 hard gates G1–G4"; the live doc uses these numbered milestone-gates. The intent maps: source has multi-version history → coverage → parser correctness → health.)

**Guidance for no official consolidation** (verbatim, extract#6): "Do not ship a single-snapshot country (one commit per law = the current text) unless you have tried and **documented in RESEARCH-{CC}.md** why historical versions are unreachable (robots.txt disallow, no archive API, paywalled, etc.). Single-snapshot ships are **temporary** and must have a follow-up task to add history." The sanctioned fallback is **periodic re-download over time** — NOT deterministic self-consolidation.

**Do our 4 fetcher interfaces still fit a self-consolidation design?** **Partially, and the gap is exactly the project's hard problem.** The 4 interfaces fit the *fetch/parse/commit* plumbing fine — `LegislativeClient` → ДВ/lex.bg HTTP, `NormDiscovery` → tree/issue crawl, `TextParser` → HTML/PDF→Blocks, `MetadataParser` → frontmatter. But `get_text` is contractually "the **consolidated** text of a norm," and there is **no interface for applying amendments**. A Bulgarian self-consolidation engine (the LawVM-style ЗИD replay in the roadmap) lives **entirely outside the Legalize fetcher contract** — it must run *before* `get_text` so that, by the time the fetcher is called, a consolidated text already exists to return. That is precisely how our design already positions it: consolidation engine = our own component, not part of `fetcher/bg/` (D3, design doc).

## Implications for Bulgaria

1. **Bulgaria cannot follow the ecosystem's normal path** because the ecosystem's normal path is "fetch the state's official consolidation." Bulgaria has no Légifrance/BOE/gesetze-im-internet — ДВ is a raw gazette of amendments, no consolidated API (handoff §1, D1). The two universal preconditions the ecosystem relies on — (a) a source that returns *consolidated* text via `get_text`, and (b) a source that exposes *≥2 dated versions* (Gate 0.5) — **are both absent at the official level in Bulgaria.**
2. **Bulgaria is genuinely the hard case the spec only half-anticipates.** The spec's *only* answer to "no official consolidation" is the temporary single-snapshot + periodic-re-download bridge (extract#6) — which is essentially what our bootstrap already is (D-039, one-time lex.bg photograph). The spec offers **no pattern for a sovereign deterministic consolidation engine** because no contributor has needed one. Our LawVM-style engine (roadmap Concern 2 / I2) is therefore **net-new relative to the entire ecosystem**, not a port of an existing country's approach.
3. **The 4 interfaces are reusable; the consolidation engine is ours alone.** This validates the existing architecture split (design doc Integration table: transformer/committer/CLI/state reused; consolidation engine, SQLite index, MCP server are ours). Self-consolidation slots in *upstream of* `get_text`.
4. **lex.bg-as-oracle is the right analogue to "the state's consolidation."** Every other country trusts the state's consolidated surface as ground truth; Bulgaria's only available consolidated surface is the private lex.bg. Keeping lex.bg as a *validation oracle* (roadmap D-b / D-003) is the faithful substitute for the official consolidation that ES/FR/EU/DE/SE/KR get for free — we just can't *source* from it for provenance reasons (FR-024/D-038), only validate against it.

## Answer to the key question (yes/no + evidence)

**NO — not a single Legalize country self-consolidates from a raw amendment stream.** All examined countries (Spain/BOE, France/LEGI-DILA, EU/EUR-Lex, Germany/gesetze-im-internet, Sweden/Riksdagen-SFS, South Korea/National Law Information Center) **fetch already-consolidated text and official version history from a state-run source** (extract#3, #4, #8, #10, #9). France's README says it outright: "does not self-consolidate amendments ... retrieves pre-consolidated versions directly from the official LEGI database" (extract#8). The fetcher interface itself encodes this: `get_text` returns "the **consolidated** text," `TextParser` parses "**consolidated** text," and there is **no amendment-application interface** (extract#5). South Korea's "independent pipeline" is an independent *codebase/org with its own Rust compiler*, still sourcing consolidated text + 연혁 (version history) from the Korean state API (extract#7, #9) — not self-consolidation.

**Therefore Bulgaria's need to self-consolidate is validated as both real and exceptional.** The ecosystem's only fallback for a missing official consolidation is a *temporary single-snapshot + periodic re-download* bridge (extract#6), not a deterministic amendment-replay engine. Bulgaria's planned LawVM-style deterministic consolidation engine has **no precedent in the Legalize ecosystem** — it is the sovereign, harder path precisely because Bulgaria, uniquely among examined members, has no official consolidated-law source to fetch from.
