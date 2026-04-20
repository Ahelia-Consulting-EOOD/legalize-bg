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
