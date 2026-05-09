# Canonical Data Model

**Scope:** This document explains what the legalize-bg data entities mean in the Bulgarian legal system, how they relate to each other, and how they are stored. For the structural schema definitions (YAML fields, SQL DDL), see `schema-reference.md`.

---

## 1. Domain Entities

### LegislativeAct

A single normative act published in the State Gazette (Държавен вестник, DV). Examples: Закон за обществените поръчки (ЗОП), Наказателно-процесуален кодекс (НПК), Наредба за обществените поръчки в областта на отбраната.

Each act is stored as one Markdown file in the repository (e.g., `laws/zop.md`). The file always contains the **current consolidated text** of the act — the version that is in force today. Historical versions are reconstructed from git history.

An act has exactly one `law_id` (a short slug like `zop`) and one `doc_id` (the lex.bg numeric identifier like `2136735703`). The `law_id` is the primary key across the entire system.

### Version

A specific textual state of an act at a point in time. Every time a ЗИД (Закон за изменение и допълнение) amends an act, a new version is created. Versions are identified by:

- **valid_from / valid_to dates** — the calendar interval during which this text was the law in force
- **commit hash** — the git commit that introduced this version
- **DV reference** — the gazette issue that published the amendment (e.g., "ДВ, бр. 63 от 2017 г.")

The HEAD of the repository always contains the latest version. Past versions are accessed via `git show {commit_hash}:{path}`.

### Amendment

A discrete change operation performed on an act by an amending act. One ЗИД typically contains multiple amendments targeting the same law (e.g., "В чл. 14, ал. 1 думите '...' се заменят с '...'") and may also amend other laws through its transitional and final provisions (ПЗР).

Amendments are classified by operation type (see Section 4 below) and tracked in both the SQLite `amendments` table and the git commit metadata.

### Provision

A specific structural unit within an act: an article (член), paragraph (алинея), point (точка), or letter (буква). Provisions are the finest-grained addressable units in the system.

Each provision has its own temporal lifecycle — it can be created, amended, or repealed independently of the rest of the act. The `provisions` table tracks this per-provision history using `valid_from` / `valid_to` dates and a `text_hash` for change detection.

### DVReference

A reference to a specific issue of the State Gazette, formatted as `{issue_number}/{year}` (e.g., "63/2017"). DV references are the canonical citation mechanism in Bulgarian law. Every amendment, new act, and repeal is tied to a DV reference.

The `amendment_history` array in YAML frontmatter records the complete chain of DV references for an act, creating a verifiable audit trail back to the official gazette.

---

## 2. Entity Ownership

The system uses a hybrid storage model where git and SQLite serve complementary roles:

| Concern | Owner | Rationale |
|---------|-------|-----------|
| **Authoritative text** | Git (Markdown files) | Git provides content-addressable storage, diffing, and full history — exactly what legislation versioning needs |
| **Temporal index** | SQLite | Temporal queries ("what was the law on 2019-03-15?") require indexed date ranges — unnatural for git alone |
| **Metadata bridge** | YAML frontmatter | The frontmatter in each Markdown file bridges git and SQLite: it contains the structured fields that SQLite indexes, embedded in the file that git versions |

**Derivation rule:** SQLite is always derivable from git. If the SQLite database is lost, it can be fully reconstructed by walking git history and parsing YAML frontmatter from every commit. Git is the system of record; SQLite is a derived acceleration structure.

**Commit as version identifier:** Each git commit that modifies a law file represents exactly one version transition. The commit hash is stored in `law_versions.commit_hash` and in `laws.current_commit`, creating a bidirectional link between the temporal index and the versioned text.

---

## 3. Temporal Model

### Version Tracking

Versions form a gapless timeline for each act:

```
Version 1: valid_from=2016-04-15, valid_to=2016-12-31, commit=abc123
Version 2: valid_from=2017-01-01, valid_to=2017-08-03, commit=def456
Version 3: valid_from=2017-08-04, valid_to=NULL,       commit=ghi789  (current)
```

- `valid_from` is the effective date of the amendment (not the DV publication date — Bulgarian law typically provides a grace period)
- `valid_to = NULL` means the version is currently in force
- When a new amendment takes effect, the previous version's `valid_to` is set to `new_valid_from - 1 day`

### Git Log as Amendment History

The git log for any law file is a complete amendment history:

```
git log --format="%H %ai %s" -- laws/zop.md
ghi789 2017-08-04 [reforma] Закон за обществените поръчки
def456 2017-01-01 [reforma] Закон за обществените поръчки
abc123 2016-04-15 [bootstrap] Закон за обществените поръчки
```

Commit messages follow Legalize conventions with Bulgarian commit types:
- `[bootstrap]` — initial scrape from lex.bg (Phase 1a)
- `[reforma]` — ЗИД amendment
- `[nova]` — new act published for the first time
- `[otmyana]` — full repeal (the file is emptied or removed, `estado` set to `derogado`)
- `[popravka]` — corrigendum published in a subsequent DV issue

### GIT_AUTHOR_DATE for Historical Reconstruction

When reconstructing past versions (Phase 5+), commits are created with `GIT_AUTHOR_DATE` set to the actual effective date of each amendment. This means `git log` shows the true legislative timeline, not the date the data was ingested.

---

## 4. Amendment Model

Bulgarian amendments follow the Закон за нормативните актове (ЗНА) and use canonical phrases that are highly formulaic. The consolidation engine classifies each amendment into one of eight operation types:

| Operation | Canonical Pattern (Bulgarian) | Frequency | Automation Level |
|-----------|-------------------------------|-----------|------------------|
| **Substitution** | `В чл. X, ал. Y думите "..." се заменят с "..."` | ~40% | Regex — direct string replacement |
| **Addition** | `В чл. X се създава ал. Y: "..."` | ~25% | Regex — insert at specified position |
| **Deletion** | `Член X се отменя` / `думите "..." се заличават` | ~15% | Regex — remove matched text/provision |
| **Renumbering** | Cascading renumber after insert/delete | ~8% | Programmatic logic — adjust all subsequent numbers |
| **Restructuring** | Move, split, or merge articles/chapters | ~5% | LLM fallback — structural changes are too varied for regex |
| **Full repeal** | `Отменя се чл. X` / `Закон Y се отменя` | ~3% | Regex — mark provision or entire act as repealed |
| **New chapter** | `Създава се нов раздел Xa "..."` | ~3% | Regex — insert new structural block |
| **Table/annex** | Changes to appendices, tariffs, schedules | ~1% | Manual — tabular content requires human review |

**Overall automation estimate:** 70-80% with regex alone, 90%+ with LLM fallback for restructuring cases, 100% requires human review for tables and annexes.

**Cross-law amendments:** A ЗИД targeting law A often amends laws B, C, D through its ПЗР (Преходни и заключителни разпоредби / transitional and final provisions). The system must detect these and apply amendments to all affected laws, not just the primary target.

### 4a. Provisions Extraction Heuristics

**Exactly-one-anchor-per-paragraph article extraction.** `index/provisions.py:_extract_article_blocks` only emits an article row for paragraphs containing exactly one `**Чл. N.**` anchor. Paragraphs with two or more anchors (cite-lists like "В чл. 14, ал. 1, чл. 15, ал. 2 ...", template enumerations, or amendment preambles that recite the articles they touch) are skipped — they reference articles in passing but do not constitute the article body. Without this rule, a single ЗИД preamble would emit dozens of false article rows whose `text_hash` collides with the genuine articles, polluting both `provisions` and `laws_fts`.

Test: `tests/index/test_provisions.py::test_skip_paragraph_with_multiple_anchors_cite_list`.

---

## 5. Category Taxonomy

Bulgarian normative acts are organized into five categories, matching the lex.bg classification:

| Category (BG) | Category (EN) | Slug | Count | Description |
|----------------|---------------|------|-------|-------------|
| Закони | Laws | `laws` | ~394 | Acts of Parliament (Народно събрание). The primary legislative instrument. |
| Кодекси | Codes | `codes` | ~24 | Systematic codifications of an entire legal domain (НК, НПК, ГПК, etc.). Technically a subtype of закон but treated separately due to their size and structural complexity. |
| Наредби | Ordinances | `ordinances` | ~2,604 | Ordinances (наредби). Secondary legislation implementing laws. Includes Council of Ministers ordinances and others. |
| Правилници | Regulations | `regulations` | ~490 | Organizational and procedural regulations issued by state bodies. |
| Правилници по прилагане | Implementing regulations | `implementing` | ~61 | Regulations specifically implementing a named law (e.g., ППЗОП implements ЗОП). |

**Directory mapping:** Each category maps to a top-level directory in the repository: `laws/`, `codes/`, `ordinances/`, `regulations/`, `implementing/`.

**Municipal acts** (Phase 6+) will be stored under `municipal/{municipality}/` and are outside the national category taxonomy.

---

## 6. Relationship to Legalize SPEC

The legalize-bg data model is a Bulgarian specialization of the international Legalize data model (legalize-dev). The mapping between Legalize SPEC fields and Bulgarian legal concepts:

| Legalize Field | Type | Bulgarian Meaning | Example |
|----------------|------|-------------------|---------|
| `titulo` | string | Title of the act (full Bulgarian name) | "Закон за обществените поръчки" |
| `identificador` | string | lex.bg document ID (unique numeric identifier) | "2136735703" |
| `pais` | literal | Country code — always "bg" for this repo | "bg" |
| `rango` | enum | Rank/type of normative act in Bulgarian hierarchy | "закон", "кодекс", "наредба", "правилник" |
| `fecha_publicacion` | date | Date of first publication in DV | "2016-02-16" |
| `ultima_actualizacion` | date | Date of most recent amendment's DV publication | "2024-03-15" |
| `estado` | enum | Current status of the act | "vigente" (in force) or "derogado" (repealed) |
| `fuente` | literal | Data source — always "lex.bg" for bootstrapped data | "lex.bg" |

**Bulgarian extensions** (fields not in the Legalize SPEC, prefixed or namespaced to avoid conflicts):

| Extension Field | Type | Purpose |
|-----------------|------|---------|
| `dv_issue` | string | DV issue number of first publication |
| `dv_year` | integer | DV year of first publication |
| `effective_date` | date | Date the act entered into force (may differ from publication date) |
| `category` | enum | Repository directory category (laws, codes, ordinances, regulations, implementing) |
| `eli` | string | European Legislation Identifier URI (constructed, not officially assigned by Bulgaria) |
| `amendment_history` | array | Ordered list of all DV amendments with issue and date |

**Legalize compliance path:** Phase 5 submits `fetcher/bg/` to the legalize-pipeline repository, implementing four interfaces: `LegislativeClient`, `NormDiscovery`, `TextParser`, `MetadataParser`. The 8 mandatory YAML fields satisfy all four Legalize hard gates. Bulgarian extensions are carried alongside but ignored by the Legalize CI.

---

## 7. Corpus Data Quality (post-bootstrap observations)

Observed characteristics of the 3,573-act corpus after Phase 1a. These are facts about lex.bg source data, not pipeline bugs — they surface via WARN logs during bootstrap and are candidates for the G2 schema-validation triage (pre-Phase-5).

### 7.1 Slug collisions are ~5-10% of the corpus, not an edge case

Many Bulgarian наредби and правилници share generic titles (e.g., "Наредба № 1", "Правилник на Столичен общински съвет…"). Transliterated, they collapse to the same slug. Observed in a random 10-act sample from the bootstrap, 2 acts carried a `-2` suffix — the `_unique_slug` dedup in `bootstrap.py` is load-bearing, not paranoia. Plan for roughly 200-300 collision-suffixed filenames across the corpus.

**Implication for consumers:** `law_id` (filename stem) is not derivable from the title alone — always go through SQLite or git to map identificador → law_id.

### 7.2 Null `fecha_publicacion` affects 3.4% of acts (121 / 3,573)

Acts whose lex.bg page has no parseable `.PreHistory` text AND no `.HistoryOfDocument` DV references produce YAML with `fecha_publicacion: null` and `ultima_actualizacion: null`. `bootstrap.py` logs a WARN for each and falls back to the bootstrap run date for `GIT_AUTHOR_DATE`, keeping `Source-Date: unknown` in the commit body.

**Implication for temporal queries (Phase 2+):**
- `git log --before=<past_date>` will NOT return these 121 acts — they appear dated at bootstrap time.
- The temporal index must treat `Source-Date: unknown` commits as "date uncertain," not "published 2026-04-20."
- Fix path: Phase 2 amendment detection from DV may recover real publication dates; otherwise FR-011 (G2 triage, below) covers manual repair.

### 7.3 Empty titles: 7 / 3,573 acts (0.2%)

Seven acts have no `.TitleDocument` element on lex.bg at all — the page exists but carries no substantive content (likely withdrawn or placeholder entries). Filename falls back to `{doc_id}.md`; frontmatter carries empty `titulo`. Cross-check during spot-check confirmed these are consistent with source (lex.bg itself shows empty), not parser failures.

**Implication:** Search by title cannot find these acts; search by `identificador` (doc_id) can. Listed for G2 triage — most should probably be dropped from the corpus with a WAIVER entry.

### 7.4 Surfacing mechanism

- Bootstrap emits `WARNING mandatory field(s) null for <title> (doc_id=N): ['fecha_publicacion', ...]` per affected act.
- The 7 empty-title + 121 null-date acts together (~128, with overlap) constitute the initial G2 triage backlog — see FR-011 in `frs/INDEX.md`.

### 7.5 Missing/zero `identificador` is a hard build error

`index/build.py:_iter_corpus_files` raises `ValueError` when an `.md` file has `identificador` ∈ {None, "", 0, "0"}. Collapsing such acts to `doc_id=0` would cause silent dedup against any future zero-id row and corrupt every join keyed on `laws.doc_id`. The fetcher always populates `identificador` from lex.bg's URL pattern (`https://lex.bg/laws/ldoc/{doc_id}`), so a missing or zero value at index time is a data bug — surfaced loudly at build time rather than swallowed and rediscovered as a query-time anomaly weeks later.

This contract is asymmetric with the §7.3 empty-titulo acts (which do enter the catalog with `titulo=""`): a missing title is recoverable (search by `identificador` still works); a missing `identificador` is not.
