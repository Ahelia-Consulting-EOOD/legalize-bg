# Source Log: I1 Legalize ecosystem

## Web Searches Performed

| # | Query | Date | Outcome |
|---|-------|------|---------|
| 1 | legalize-dev legalize github legislation as code Markdown git countries | 2026-06-22 | extract#1 |
| 2 | legalize-pipeline github fetcher base.py country interfaces ADDING_A_COUNTRY | 2026-06-22 | extract#2 |
| 3 | legalize-es legalize-fr legalize-eu github BOE Legifrance EUR-Lex consolidated laws | 2026-06-22 | extract#3 |
| 4 | legalize-dev legalize-kr South Korea legislation github pipeline law.go.kr | 2026-06-22 | extract#7 |
| 5 | 국가법령정보센터 OpenAPI 법령 연혁 consolidated version history law.go.kr | 2026-06-22 | extract#9 |
| 6 | BOE API datos abiertos "texto consolidado" legislación consolidada XML endpoint | 2026-06-22 | extract#4 |
| 7 | legalize-dev Germany legalize-de gesetze-im-internet Sweden legalize-se riksdagen consolidated | 2026-06-22 | extract#10 |

## Documents Read

| # | File Path | Sections Read | Outcome |
|---|-----------|---------------|---------|
| D1 | docs/sync/HANDOFFS/2026-06-22-freshness-consolidation-resource-roadmap.md | §1, §2, §3, §3a, §4, §5 | context |
| D2 | docs/frs/INDEX.md | FR-002/003/004/005/008/009/024 | context |
| D3 | docs/plans/2026-04-19-legalize-bg-design.md | R4, Architecture Decision, Consolidation Engine, Contribution Strategy | context |

## Web Sources Referenced

| # | URL | Title | Date Accessed | Outcome |
|---|-----|-------|---------------|---------|
| W1 | https://github.com/legalize-dev/legalize | legalize-dev/legalize (umbrella) | 2026-06-22 | extract#1 |
| W2 | https://raw.githubusercontent.com/legalize-dev/legalize-pipeline/main/src/legalize/fetcher/base.py | fetcher/base.py | 2026-06-22 | extract#5 |
| W3 | https://raw.githubusercontent.com/legalize-dev/legalize-pipeline/main/ADDING_A_COUNTRY.md | ADDING_A_COUNTRY.md | 2026-06-22 | extract#6 |
| W4 | https://raw.githubusercontent.com/legalize-dev/legalize-fr/main/README.md | legalize-fr README | 2026-06-22 | extract#8 |
| W5 | https://raw.githubusercontent.com/legalize-dev/legalize-pipeline/main/README.md | legalize-pipeline README | 2026-06-22 | extract#2 |
| W6 | https://github.com/legalize-kr/legalize-kr | legalize-kr README | 2026-06-22 | extract#7 |
| W7 | https://github.com/legalize-kr/compiler | legalize-kr/compiler (Rust) | 2026-06-22 | extract#7 |
| W8 | https://www.boe.es/datosabiertos/api/api.php + APIconsolidada.pdf | BOE Datos Abiertos — Legislación Consolidada API | 2026-06-22 | extract#4 |
| W9 | https://open.law.go.kr/LSO/openApi/guideList.do + data.go.kr/15059149 | KR National Law Information Center OpenAPI (현행법령 / 법령 연혁) | 2026-06-22 | extract#9 |
| W10 | https://www.gesetze-im-internet.de / legalize.dev | DE gesetze-im-internet; legalize.dev country list | 2026-06-22 | extract#10 |

## Extracted Content

| Source ref | Extract (verbatim, <300 words) | Used in section |
|------------|--------------------------------|-----------------|
| extract#1 | (W1/search1) "Legislation as code. Every law as a Markdown file. Every reform as a Git commit." Coverage: "structured legal data from 31 countries." Format: "Each law is a Markdown file with YAML frontmatter. When a reform is published, the file is updated and committed with the official publication date." Problem: "Legal texts are amended constantly... Official sources publish consolidated versions with no way to compare. Commercial providers charge hundreds per month for version history." Origin: "Legalize-es was created in March 2026 by independent IT consultant Enrique Lopez." | RQ1, Implications |
| extract#2 | (W5/search2) Pipeline stages: "Fetch laws to data/ (does not touch git)" → "Generate git commits from local data/ (does not download)" → "Full pipeline: fetch + commit". Spain: "Spain (BOE API)", "HTTP client with rate limiting, caching", "BOE XML -> Block/NormMetadata". 4 interfaces: "LegislativeClient -- fetch raw data," "NormDiscovery -- discover all laws in catalog," "TextParser -- parse into Bloque objects," "MetadataParser -- parse into NormaMetadata." Reforms: "Daily incremental update" (`legalize daily -c es --date ...`), "Every reform is a commit". Adding: "fetcher/{code}/ with client.py, discovery.py, parser.py"; "See ADDING_A_COUNTRY.md". | RQ1, RQ2 |
| extract#3 | (search3) "legalize-es (Spain): ... Data is obtained from the BOE's (Boletín Oficial del Estado) open data API." "legalize-fr (France): France uses LEGI (Legifrance) as its data source." "legalize-eu (European Union): ... 15,700+ regulations from 1958 to present." "The repositories store consolidated legislation, meaning they include the current state of laws with all reforms applied." Sources: "Spain (BOE): ... open data API; France (Legifrance): LEGI XML dumps; EU (EUR-Lex): European Union's legal database." | RQ2 |
| extract#4 | (W8/search6) "The State Agency BOE has made available to reusers a series of REST APIs that allow downloading, using and reusing consolidated legal norms. The API /datosabiertos/api/legislacion-consolidada allows obtaining the list of consolidated norms..." Endpoints include: "metadata of a norm by identifier, ELI metadata ..., analysis of a norm by identifier, consolidated text of a norm by identifier, and blocks of a norm by identifier." Format XML, OpenAPI v3.1.0. | RQ2 |
| extract#5 | (W2) fetcher/base.py — 4 abstract classes. **1. LegislativeClient** ("Base class for country-specific legislative API clients"): `get_text(norm_id: str) -> bytes` "Fetch the consolidated text of a norm (XML or HTML)"; `get_metadata(norm_id) -> bytes`; `close()`. **2. NormDiscovery** ("discovering norms in a country's catalog"): `discover_all(client, **kwargs) -> Iterator[str]`; `discover_daily(client, target_date: date, **kwargs) -> Iterator[str]` "Discover norms published/updated on a specific date." **3. TextParser** ("parsing consolidated text into structured blocks"): `parse_text(data: bytes) -> list[Any]` "Parse consolidated text into a list of Block objects." **4. MetadataParser** ("parsing norm metadata"): `parse(data: bytes, norm_id: str) -> NormMetadata`. | RQ1, RQ4, Implications |
| extract#6 | (W3) ADDING_A_COUNTRY.md — 4 interfaces: "LegislativeClient — fetches raw data with get_text(), get_metadata(), ... create() classmethod; NormDiscovery — yields law IDs via discover_all() and discover_daily(target_date); TextParser — converts raw bytes to Block objects with versioned Paragraph content; MetadataParser — extracts metadata into NormMetadata dataclass plus country-specific fields in extra." Gates: **Gate 0.5 (Version History Spike):** "If you cannot extract at least 2 distinct versions with dates for a single law, stop and investigate." **Gate 0.7 (Format Coverage):** "Every format that contributes > 1% of unique laws or unique versions MUST be covered by the fetcher." **Gate 7.2 (AI Review):** "The parser is not ready until the agent reports all five [checks] as PASS for all 5 laws." **Gate 9.3 (Health Check):** "Every issue reported must be zero before pushing. legalize health -c xx reports zero issues." Missing consolidation: "Do not ship a single-snapshot country (one commit per law = the current text) unless you have tried and documented in RESEARCH-{CC}.md why historical versions are unreachable (robots.txt disallow, no archive API, paywalled, etc.). Single-snapshot ships are temporary and must have a follow-up task to add history." Fallback = "periodic re-download over time to build history post-hoc." | RQ4, RQ3, Implications |
| extract#7 | (W6/W7/search4) legalize-kr is its OWN org (`legalize-kr/legalize-kr`, 5,575 laws, community contribution). README: "모든 법령 데이터는 국가법령정보센터 OpenAPI(open.law.go.kr)에서 가져옵니다" (All legal data obtained from National Law Information Center OpenAPI). Commits use "실제 공포일자" (actual proclamation dates). Korea "was built with an independent pipeline ... Users can either use the shared legalize-pipeline or build their own pipeline, as long as output follows the specification, with South Korea being built with an independent pipeline." legalize-kr also has its OWN `compiler` repo (Rust): "receives .cache/ directory as input to directly write bare Git repositories" for laws/precedents/admin-rules/local-ordinances — a transform/commit compiler, README does NOT describe amendment-application/self-consolidation. | RQ3 |
| extract#9 | (W9/search5) KR National Law Information Center: "provides the original text and metadata of various laws ... including the content of articles, article numbers, enforcement dates, revision history, and responsible ministries in structured form. Users can compare current laws with past articles..." data.go.kr exposes "법제처_현행법령 목록 조회" (current in-force law list) and "법제처_법령 연혁 목록 조회" (law history/version list) OpenAPIs. → The STATE API supplies current consolidated text + the version/연혁 history. | RQ3, Answer |
| extract#8 | (W4) legalize-fr README: "Données issues de la base LEGI (open data, licence ouverte Etalab 2.0), publiée par la DILA." "The repository does not self-consolidate amendments. Instead, it retrieves pre-consolidated versions directly from the official LEGI database maintained by DILA." Each file = "texte consolidé"; git history reflects "date historique de publication officielle au Journal Officiel" but "the actual legal text comes pre-consolidated from LEGI/Légifrance rather than being amended incrementally by this project." | RQ2, Answer |
| extract#10 | (search7) legalize.dev country list incl. "Germany (gesetze-im-internet.de with 5,729 laws)" and "Sweden (Riksdagen with 8,947 laws)." Germany: gesetze-im-internet.de (Federal Ministry of Justice + Federal Office of Justice) provides "the entire body of current federal law ... in their current consolidated version as amendments are incorporated." Sweden: legalize-pipeline "includes a Sweden (SFSR / Riksdag) fetcher with a Riksdag API client and SFS catalog discovery." | RQ2, RQ3 |
