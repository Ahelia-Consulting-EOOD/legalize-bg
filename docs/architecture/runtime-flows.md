# Architecture: Runtime Flows

**Arc42 Section 6** | legalize-bg | Ahelia Consulting

---

## 6.1 Bootstrap Flow (Phase 1a)

One-time initial population of the git corpus from lex.bg.

### Sequence

```
 Catalog       Content       HTML-to-MD     Metadata     Legalize       Git        SQLite
 Crawler       Fetcher       Converter      Parser       Committer      Corpus     Index
    |              |              |              |            |            |           |
    |--[1] GET /laws/tree/{cat}/{page} -------->|             |            |           |
    |     for each of 5 categories              |             |            |           |
    |     (~105 HTTP requests)                  |             |            |           |
    |              |              |              |            |            |           |
    |<--- list of (doc_id, name, category) -----|             |            |           |
    |              |              |              |            |            |           |
    |--[2] for each doc_id:      |              |            |            |           |
    |    dispatch to fetcher --->|              |             |            |           |
    |              |              |              |            |            |           |
    |              |--[3] GET /laws/ldoc/{id} -->|            |            |           |
    |              |     cp1251 decode           |            |            |           |
    |              |     BeautifulSoup parse     |            |            |           |
    |              |              |              |            |            |           |
    |              |--[4] DOM ---|->             |            |            |           |
    |              |             | CSS selectors |            |            |           |
    |              |             | .Article      |            |            |           |
    |              |             | .Part         |            |            |           |
    |              |             | .Heading etc  |            |            |           |
    |              |             |               |            |            |           |
    |              |             |--[5] Markdown body ------->|            |           |
    |              |              |              |            |            |           |
    |              |--[4b] DOM --|-------------->|            |            |           |
    |              |             |    .TitleDocument          |            |           |
    |              |             |    .HistoryOfDocument      |            |           |
    |              |             |    .PreHistory             |            |           |
    |              |              |              |            |            |           |
    |              |              |         [6] YAML dict --->|            |           |
    |              |              |              |            |            |           |
    |              |              |              |    [7] frontmatter.py   |           |
    |              |              |              |        + slug.py        |           |
    |              |              |              |        + markdown.py    |           |
    |              |              |              |            |            |           |
    |              |              |              |    [8] git commit ----->|           |
    |              |              |              |        msg: [bootstrap] Title       |
    |              |              |              |        file: {cat}/{slug}.md        |
    |              |              |              |            |            |           |
    |              |              |              |            |    [9] --->|           |
    |              |              |              |            |  INSERT    |           |
    |              |              |              |            |  laws,     |           |
    |              |              |              |            |  law_versions          |
    |              |              |              |            |            |           |
```

### Step Details

| Step | Action | Data | Container |
|------|--------|------|-----------|
| 1 | Crawl tree pages | HTTP GET to ~105 URLs; parse `<a href="/laws/ldoc/{id}">` links | Catalog Crawler |
| 2 | Dispatch per act | `(doc_id, name, category)` tuples; 1 req/sec rate limit | Catalog Crawler |
| 3 | Fetch act HTML | HTTP GET, `resp.encoding = 'cp1251'`, BeautifulSoup parse | Content Fetcher |
| 4 | Parse structure | DOM elements selected by CSS class (.Article, .Part, .Heading, .Section, .TransitionalFinalEdicts) | HTML-to-Markdown Converter |
| 4b | Extract metadata | `.TitleDocument` -> titulo; `.PreHistory` -> effective_date; `.HistoryOfDocument` -> amendment_history | Metadata Parser |
| 5 | Generate Markdown | Structured Markdown body with H1 title, H2 parts, H3 chapters, H4 sections, bold article numbers | HTML-to-Markdown Converter |
| 6 | Generate YAML | 8 mandatory fields + 5 extensions + amendment_history list | Metadata Parser |
| 7 | Assemble file | YAML frontmatter + Markdown body; compute slug from title for filename | Legalize transformer |
| 8 | Commit to git | `git add {cat}/{slug}.md && git commit -m "[bootstrap] {title}" --date="{fecha_publicacion}"` | Legalize committer |
| 9 | Index in SQLite | INSERT into `laws` and `law_versions` (single version with `valid_to = NULL`) | SQLite Index |

### Performance

- ~3,574 acts at 1 req/sec = ~60 minutes for content fetching
- Tree crawl: ~105 requests = ~2 minutes
- Total estimated time: ~2 hours including parsing and commits

---

## 6.2 Amendment Tracking Flow (Phase 3-4)

Ongoing detection and application of legislative amendments from the State Gazette.

### Sequence

```
 DV Monitor     Consolidation Engine              Git        SQLite     lex.bg
 (poller +      (zid_parser + patcher             Corpus     Index      (validator)
  detector)      + validator)                        |          |           |
     |                |                              |          |           |
     |--[1] GET dv.parliament.bg -------->           |          |           |
     |     (every Tue & Fri)                         |          |           |
     |     Check for new gazette issues              |          |           |
     |                |                              |          |           |
     |--[2] Parse gazette HTML/PDF                   |          |           |
     |     Detect ЗИД titles matching                |          |           |
     |     acts in our corpus                        |          |           |
     |                |                              |          |           |
     |--[3] Extract amendment text -->|              |          |           |
     |     (source_act, target_law,   |              |          |           |
     |      raw instruction text)     |              |          |           |
     |                |               |              |          |           |
     |                |--[4] Parse ZID instructions   |          |           |
     |                |     Regex match canonical     |          |           |
     |                |     ЗНА phrases:              |          |           |
     |                |     "думите ... се заменят"   |          |           |
     |                |     "създава се ал."          |          |           |
     |                |     "се отменя"               |          |           |
     |                |               |              |          |           |
     |                |--[5] git show HEAD:{path} -->|          |           |
     |                |     Fetch current Markdown    |          |           |
     |                |               |              |          |           |
     |                |<-- current text --------------|          |           |
     |                |               |              |          |           |
     |                |--[6] Apply patches            |          |           |
     |                |     (patcher.py)              |          |           |
     |                |     Text substitution,        |          |           |
     |                |     insertion, deletion       |          |           |
     |                |               |              |          |           |
     |                |--[7] Update YAML frontmatter  |          |           |
     |                |     ultima_actualizacion,     |          |           |
     |                |     amendment_history[]       |          |           |
     |                |               |              |          |           |
     |                |--[8] git commit ------------->|          |           |
     |                |     msg: [reforma] Title      |          |           |
     |                |     date: DV publication date |          |           |
     |                |     Source-Id: dv-{n}-{year}  |          |           |
     |                |               |              |          |           |
     |                |--[9] UPDATE law_versions -----|--------->|           |
     |                |     SET valid_to on old row   |          |           |
     |                |     INSERT new version row    |          |           |
     |                |     INSERT amendment row      |          |           |
     |                |               |              |          |           |
     |                |--[10] Validate (Phase 4v) ----|----------|---------->|
     |                |     GET /laws/ldoc/{id}       |          |     fetch |
     |                |     Normalize + diff          |          |   current |
     |                |     Report discrepancies      |          |     text  |
     |                |               |              |          |           |
```

### Step Details

| Step | Action | Data | Container |
|------|--------|------|-----------|
| 1 | Poll DV | HTTP GET to dv.parliament.bg; check for new gazette issues since last poll | DV Monitor (dv_poller.py) |
| 2 | Detect amendments | Parse gazette HTML/PDF; match ZID titles against `laws` table in SQLite | DV Monitor (amendment_detector.py) |
| 3 | Extract instructions | Raw amendment text with article references and operation phrases | DV Monitor -> Consolidation Engine |
| 4 | Parse ZID | Regex matching against ЗНА canonical patterns; classify each instruction by operation type | zid_parser.py |
| 5 | Fetch current text | `git show HEAD:{category}/{slug}.md` to get the latest version | Git Corpus |
| 6 | Apply patches | Execute amendment instructions on Markdown text: substitute words, insert paragraphs, delete articles | patcher.py |
| 7 | Update frontmatter | Increment `ultima_actualizacion`, append to `amendment_history`, update `dv_issue`/`dv_year` | Metadata Parser |
| 8 | Commit | `[reforma]` commit with `GIT_AUTHOR_DATE` set to DV publication date | Legalize committer |
| 9 | Update SQLite | Close old `law_versions` row (`valid_to`), insert new version row, insert amendment row, update provision hashes | SQLite Index |
| 10 | Validate | Fetch same law from lex.bg, normalize both texts, diff; flag non-trivial discrepancies for human review | validator.py |

### LLM Fallback

When zid_parser.py cannot match an instruction to a known regex pattern (estimated ~20-30% of cases involving restructuring, complex renumbering, or table changes), the instruction is routed to an LLM for interpretation. The LLM produces a structured patch that patcher.py can apply. All LLM-assisted patches are flagged for human review.

---

## 6.3 MCP Query Flow (Phase 1b-2)

Point-in-time retrieval of legislation by Claude Code sessions.

### Sequence

```
 Claude Code        MCP Server          SQLite Index        Git Corpus
     |                   |                   |                   |
     |--[1] get_law ---->|                   |                   |
     |   name="zop"      |                   |                   |
     |   date="2020-06-15"|                  |                   |
     |                   |                   |                   |
     |                   |--[2] SELECT ----->|                   |
     |                   |   commit_hash     |                   |
     |                   |   FROM law_versions                   |
     |                   |   WHERE law_id='zop'                  |
     |                   |     AND valid_from <= '2020-06-15'    |
     |                   |     AND (valid_to IS NULL             |
     |                   |          OR valid_to > '2020-06-15')  |
     |                   |                   |                   |
     |                   |<-- commit_hash ---|                   |
     |                   |   "a3f7c2d..."    |                   |
     |                   |                   |                   |
     |                   |--[3] git show ----|------------------>|
     |                   |   a3f7c2d:laws/zop.md                 |
     |                   |                   |                   |
     |                   |<-- Markdown text --|-------------------|
     |                   |                   |                   |
     |<--[4] return -----|                   |                   |
     |   full Markdown   |                   |                   |
     |   with YAML       |                   |                   |
     |   frontmatter     |                   |                   |
     |                   |                   |                   |
```

### Variant: get_law without date (current version)

When `date` is omitted, step 2 simplifies to:
```sql
SELECT current_commit FROM laws WHERE law_id = 'zop';
```
Or simply reads the file from the working tree: `laws/zop.md`.

### Variant: search(query)

```
 Claude Code        MCP Server          SQLite Index
     |                   |                   |
     |--[1] search ----->|                   |
     |   query="поръчки" |                   |
     |   category="laws" |                   |
     |                   |--[2] FTS query -->|
     |                   |   SELECT law_id,  |
     |                   |   title, snippet  |
     |                   |   FROM laws_fts   |
     |                   |   WHERE text MATCH|
     |                   |   'поръчки'       |
     |                   |                   |
     |<--[3] results ----|                   |
     |   [{law_id: "zop",|                   |
     |     title: "...", |                   |
     |     snippet: "..."}]                  |
```

### Variant: diff(law, date1, date2)

```
 Claude Code        MCP Server          SQLite Index        Git Corpus
     |                   |                   |                   |
     |--[1] diff ------->|                   |                   |
     |   law="zop"       |                   |                   |
     |   date1="2020-01" |                   |                   |
     |   date2="2021-01" |                   |                   |
     |                   |--[2] 2x SELECT -->|                   |
     |                   |   commit for date1|                   |
     |                   |   commit for date2|                   |
     |                   |                   |                   |
     |                   |<-- hash1, hash2 --|                   |
     |                   |                   |                   |
     |                   |--[3] git diff ----|------------------>|
     |                   |   hash1..hash2 -- |                   |
     |                   |   laws/zop.md     |                   |
     |                   |                   |                   |
     |<--[4] unified diff|                   |                   |
```

---

## 6.4 Validation Flow (Phase 4v)

Verification of consolidation engine accuracy against lex.bg as oracle.

### Sequence

```
 Consolidation      Content         Validator           Report
 Engine             Fetcher         (validator.py)
     |                   |               |                  |
     |--[1] After each [reforma] commit, trigger validation |
     |                   |               |                  |
     |   patched text -->|-------------->|                  |
     |   (from git)      |               |                  |
     |                   |               |                  |
     |                   |--[2] GET ---->|                  |
     |                   |  /laws/ldoc/{id}                 |
     |                   |  from lex.bg  |                  |
     |                   |               |                  |
     |                   |<-- HTML ------|                  |
     |                   |               |                  |
     |                   |--[3] parse -->|                  |
     |                   |  to Markdown  |                  |
     |                   |  (same parser)|                  |
     |                   |               |                  |
     |                   |         [4] Normalize both:      |
     |                   |             - strip whitespace   |
     |                   |             - normalize quotes   |
     |                   |             - normalize dashes   |
     |                   |               |                  |
     |                   |         [5] Diff                 |
     |                   |               |                  |
     |                   |         [6] Classify result:     |
     |                   |               |                  |
     |                   |     +---------+---------+        |
     |                   |     |                   |        |
     |                   |   trivial            non-trivial |
     |                   |   (whitespace only)  (content    |
     |                   |                      differs)    |
     |                   |     |                   |        |
     |                   |   [7a] Log OK     [7b] Flag --->|
     |                   |   Track accuracy  for human     |
     |                   |   metric          review        |
     |                   |                                  |
```

### Step Details

| Step | Action | Detail |
|------|--------|--------|
| 1 | Trigger | Validation runs after each `[reforma]` commit. Can also run as a batch job across the entire corpus. |
| 2 | Fetch oracle | HTTP GET to `lex.bg/laws/ldoc/{doc_id}` for the same act. Uses Content Fetcher with cp1251 decoding. |
| 3 | Parse to Markdown | Same HTML-to-Markdown Converter used for bootstrap, ensuring identical normalization. |
| 4 | Normalize | Strip leading/trailing whitespace per line, normalize typographic quotes to standard quotes, normalize en-dash/em-dash, collapse multiple blank lines. |
| 5 | Diff | Line-by-line unified diff between our consolidated version and the lex.bg version. |
| 6 | Classify | Trivial = whitespace-only differences. Non-trivial = any content difference (missing text, wrong text, different structure). |
| 7a | Log success | Record in validation log: `(law_id, date, status=ok, our_hash, oracle_hash)`. Track overall accuracy rate. |
| 7b | Flag for review | Record discrepancy details. Create issue or alert. Include the diff, the affected articles, and the DV reference that triggered the amendment. |

### Accuracy Tracking

The validator maintains a running accuracy metric:

```
accuracy = (laws_matching_oracle) / (laws_validated) * 100
```

Target: 95%+ accuracy after Phase 4 stabilization. The remaining 5% accounts for:
- Timing differences (lex.bg may update before or after DV publication)
- Table/annex changes (1% of amendments, lowest automation rate)
- Structural changes requiring manual review

### Batch Validation

A full corpus validation can be triggered manually:
1. For each law in `laws` table
2. Fetch current text from lex.bg
3. Compare against HEAD version in git
4. Produce summary report: total validated, matches, discrepancies, accuracy percentage

This serves as a regression test for the consolidation engine and detects any amendments that the DV Monitor may have missed.
