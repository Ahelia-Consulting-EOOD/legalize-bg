# Architecture: Data Model

**Arc42 Section 8 (Crosscutting)** | legalize-bg | Ahelia Consulting

---

## 8.1 Conceptual Model

```
+-------------------+       1..*       +-------------------+
|  LegislativeAct   |<--------------->|     Version        |
|                   |                  |                    |
|  law_id (slug)    |                  |  valid_from        |
|  doc_id (lex.bg)  |                  |  valid_to          |
|  title            |                  |  commit_hash       |
|  category         |                  |  dv_issue          |
|  status           |                  |  amending_act      |
+--------+----------+                  +-------------------+
         |
         | 1..*
         v
+-------------------+       *..1       +-------------------+
|    Provision      |                  |    Amendment       |
|                   |                  |                    |
|  article          |<----- affects ---|  source_act (ZID)  |
|  paragraph        |                  |  operation         |
|  valid_from       |                  |  affected_articles |
|  valid_to         |                  |  dv_issue          |
|  text_hash        |                  |  dv_date           |
+-------------------+                  +--------+----------+
                                                |
                                                | references
                                                v
                                       +-------------------+
                                       |   DVReference     |
                                       |                   |
                                       |  issue_number     |
                                       |  year             |
                                       |  publication_date |
                                       +-------------------+
```

### Entity Definitions

**LegislativeAct** -- A single normative act (law, code, ordinance, regulation, or implementing regulation). Identified by a human-readable slug (`zop`, `zeu`) and a lex.bg numeric document ID. Has exactly one category and a lifecycle status (vigente = in force, derogado = repealed).

**Version** -- A temporal snapshot of an act. Created each time the act is amended. The `valid_from`/`valid_to` pair defines the time interval during which this version was in force. `valid_to = NULL` means the version is current. Each version corresponds to exactly one git commit.

**Amendment** -- A change event applied to one or more acts. Originates from a ZID (Zakon za Izmenenie i Dopalnenie) or from PZR (Prekhodni i Zaklyuchitelni Razporedbi) of another law. Classified by operation type: substitution, addition, deletion, repeal, restructure, renumbering. One amendment may affect multiple provisions of one or more acts.

**Provision** -- An article + paragraph within an act. Tracked individually to enable article-level temporal queries and change detection via `text_hash` (SHA256 of the provision text).

**DVReference** -- A State Gazette (Darzhaven Vestnik) issue that published a change. Format: `"{issue_number}/{year}"` (e.g., `"63/2017"`). Published on Tuesdays and Fridays.

### Category Taxonomy

| Category | Bulgarian | Count | Example |
|----------|-----------|-------|---------|
| `laws` | Закони | ~394 | Закон за обществените поръчки (ЗОП) |
| `codes` | Кодекси | ~24 | Кодекс на труда |
| `ordinances` | Наредби | ~2,604 | Наредба за обществените поръчки в областта на отбраната |
| `regulations` | Правилници | ~490 | Правилник за прилагане на ЗОП |
| `implementing` | Правилници по прилагане | ~61 | Правилник по прилагане на Закона за горите |

### Amendment Operation Types

| Operation | Bulgarian Pattern | Frequency |
|-----------|------------------|-----------|
| `substitution` | `думите "..." се заменят с "..."` | ~40% |
| `addition` | `се създава ал. Y: "..."` | ~25% |
| `deletion` | `се отменя` / `думите "..." се заличават` | ~15% |
| `renumbering` | Cascading after insert/delete | ~8% |
| `restructure` | Move, split, merge articles/chapters | ~5% |
| `repeal` | `Отменя се чл. X` / `Отменя се закон Y` | ~3% |
| `new_chapter` | `Създава се нов раздел Xa "..."` | ~3% |

## 8.2 Logical Model -- Storage Mapping

### Layer 1: Git (Primary Store)

Each LegislativeAct maps to one Markdown file in the appropriate category directory:

```
{category}/{slug}.md
```

Examples:
```
laws/zop.md
codes/kodeks-na-truda.md
ordinances/naredba-za-obshtestvenite-porachki-v-oblastta-na-otbranata.md
```

Each Version maps to one git commit:
- `GIT_AUTHOR_DATE` is set to the DV publication date of the amendment
- Commit message follows Legalize format: `[type] Act Title\n\nSource-Id: dv-{issue}-{year}\nSource-Date: {date}\nNorm-Id: {doc_id}`
- Commit types: `[bootstrap]`, `[reforma]`, `[nova]`, `[otmyana]`, `[popravka]`

Point-in-time retrieval: `git log --before={date} -1 -- {path}` yields the commit hash, then `git show {hash}:{path}` yields the file content at that date.

### Layer 2: SQLite (Derived Index)

Four tables provide fast temporal queries without walking git history. Fully rebuildable from git. See Section 8.3 for schema.

### Layer 3: YAML Frontmatter (Per-File Metadata)

Each Markdown file begins with a YAML frontmatter block containing structured metadata. This is the bridge between git storage and the SQLite index -- the index is populated by parsing frontmatter from git history.

## 8.3 Physical Schema

### YAML Frontmatter Fields

**Mandatory Legalize fields (8):**

| Field | Type | Source | Example |
|-------|------|--------|---------|
| `titulo` | string | `.TitleDocument` CSS class | `"Закон за обществените поръчки"` |
| `identificador` | string | Doc ID from lex.bg URL | `"2136735703"` |
| `pais` | string | Constant | `bg` |
| `rango` | string | Derived from category | `закон`, `кодекс`, `наредба`, `правилник` |
| `fecha_publicacion` | date | `.PreHistory` or `.HistoryOfDocument` | `"2016-02-16"` |
| `ultima_actualizacion` | date | Latest entry in `.HistoryOfDocument` | `"2024-03-15"` |
| `estado` | string | Inferred from content/status | `vigente` or `derogado` |
| `fuente` | string | Constant for bootstrap | `"lex.bg"` |

**Bulgarian extension fields (5):**

| Field | Type | Source | Example |
|-------|------|--------|---------|
| `dv_issue` | string | Parsed from `.HistoryOfDocument` | `"13"` |
| `dv_year` | integer | Parsed from `.HistoryOfDocument` | `2016` |
| `effective_date` | date | `.PreHistory` "В сила от" text | `"2016-04-15"` |
| `category` | string | Tree page category | `laws`, `codes`, `ordinances`, `regulations`, `implementing` |
| `eli` | string | Constructed per ELI spec | `"/eli/bg/закон/2016/2/16/zop/con"` |

**Amendment history (nested list):**

| Field | Type | Example |
|-------|------|---------|
| `amendment_history[].dv` | string | `"34/2016"` |
| `amendment_history[].date` | date | `"2016-05-03"` |

**Full frontmatter example:**

```yaml
---
titulo: "Закон за обществените поръчки"
identificador: "2136735703"
pais: bg
rango: закон
fecha_publicacion: "2016-02-16"
ultima_actualizacion: "2024-03-15"
estado: vigente
fuente: "lex.bg"
dv_issue: "13"
dv_year: 2016
effective_date: "2016-04-15"
category: laws
eli: "/eli/bg/закон/2016/2/16/zop/con"
amendment_history:
  - dv: "34/2016"
    date: "2016-05-03"
  - dv: "63/2017"
    date: "2017-08-04"
---
```

### SQLite Schema

```sql
CREATE TABLE laws (
    law_id TEXT PRIMARY KEY,      -- "zop", "zeu", etc.
    doc_id INTEGER,               -- lex.bg doc ID (2136735703)
    title TEXT NOT NULL,
    category TEXT NOT NULL,       -- laws, codes, ordinances, regulations, implementing
    status TEXT DEFAULT 'vigente', -- vigente, derogado
    current_commit TEXT           -- HEAD commit hash for this file
);

CREATE TABLE law_versions (
    id INTEGER PRIMARY KEY,
    law_id TEXT REFERENCES laws(law_id),
    valid_from DATE NOT NULL,     -- effective date of this version
    valid_to DATE,                -- NULL = current version
    commit_hash TEXT NOT NULL,    -- git commit that created this version
    dv_issue TEXT,                -- "63/2017"
    dv_date DATE,
    amending_act TEXT             -- "ЗИД на ЗОП"
);

CREATE TABLE amendments (
    id INTEGER PRIMARY KEY,
    source_act TEXT NOT NULL,     -- the ЗИД or ПЗР that made the change
    target_law TEXT REFERENCES laws(law_id),
    operation TEXT NOT NULL,      -- substitution, addition, deletion, repeal, restructure
    affected_articles TEXT,       -- "чл. 14, ал. 1; чл. 20, ал. 1"
    dv_issue TEXT,
    dv_date DATE
);

CREATE TABLE provisions (
    id INTEGER PRIMARY KEY,
    law_id TEXT REFERENCES laws(law_id),
    article TEXT NOT NULL,        -- "1", "14а"
    paragraph TEXT,               -- "1", "2"
    valid_from DATE NOT NULL,
    valid_to DATE,
    text_hash TEXT                -- SHA256 of provision text for change detection
);

CREATE INDEX idx_versions_date ON law_versions(law_id, valid_from);
CREATE INDEX idx_amendments_target ON amendments(target_law, dv_date);
CREATE INDEX idx_provisions_article ON provisions(law_id, article, valid_from);
```

### Key Temporal Query Patterns

**Get law version at a specific date:**
```sql
SELECT commit_hash FROM law_versions
WHERE law_id = ?
  AND valid_from <= ?
  AND (valid_to IS NULL OR valid_to > ?)
ORDER BY valid_from DESC LIMIT 1;
```

**Get all amendments to a law:**
```sql
SELECT * FROM amendments
WHERE target_law = ?
ORDER BY dv_date;
```

**Get article history:**
```sql
SELECT * FROM provisions
WHERE law_id = ? AND article = ?
ORDER BY valid_from;
```

**Find all laws amended in a period:**
```sql
SELECT DISTINCT l.law_id, l.title, a.dv_issue, a.dv_date, a.operation
FROM amendments a
JOIN laws l ON a.target_law = l.law_id
WHERE a.dv_date BETWEEN ? AND ?
ORDER BY a.dv_date;
```
