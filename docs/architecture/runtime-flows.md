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
| 1 | Crawl tree pages | HTTP GET to ~104 URLs; parse `<a href="/laws/ldoc/{id}">` links | Catalog Crawler |
| 1b | Dedup doc IDs | First-wins across categories (laws → code → ords → regs → reg_laws); drops the 104 `Конституция` sidebar duplicates and any cross-category overlaps; result: 3,573 unique acts | Catalog Crawler |
| 2 | Dispatch per act | `(doc_id, name, category)` tuples; shared `RateLimitedSession` enforces global 1 req/sec + 3× retry with 2/4/8s exp backoff on 429/5xx; Cloudflare challenge raises `CloudflareChallenge` and halts | Catalog Crawler |
| 3 | Fetch act HTML | HTTP GET, `resp.encoding = 'cp1251'`, BeautifulSoup parse | Content Fetcher |
| 4 | Parse structure | DOM elements selected by CSS class (.Article, .Part, .Heading, .Section, .TransitionalFinalEdicts); article alineas separated by `<br>` are joined with `\n\n` so they render as distinct Markdown paragraphs | HTML-to-Markdown Converter |
| 4b | Extract metadata | `.TitleDocument` → titulo; `.PreHistory` → effective_date (numeric form, e.g. `15.04.2016 г.`); `.HistoryOfDocument` → amendment_history (supports Bulgarian month-name form, e.g. `16 Февруари 2016г.`, and numeric form) | Metadata Parser |
| 5 | Generate Markdown | Structured Markdown body with H1 title, H2 parts, H3 chapters, H4 sections, bold article numbers | HTML-to-Markdown Converter |
| 6 | Generate YAML | 8 mandatory fields + 5 extensions + amendment_history list; `eli` built as `/eli/bg/{rango}/{Y}/{M}/{D}/{ascii-slug}/con` | Metadata Parser |
| 7 | Assemble file | YAML frontmatter + Markdown body; `generate_slug` (transliterated ASCII, shared between filename and ELI slug segment); `_unique_slug` appends `-2/-3/…` on same-run slug collision | Legalize transformer |
| 7b | Log null mandatory fields | If `fecha_publicacion` or `ultima_actualizacion` is null (degenerate acts with no `.PreHistory`/`.HistoryOfDocument`), emit WARN for G2 triage; continue processing | Bootstrap Runner |
| 8 | Commit to git | `git add {cat}/{slug}.md && git commit -m "[bootstrap] {title}" --date="{fecha_publicacion}"` | Legalize committer |
| 8b | Push to remote (optional) | When `--branch BOOTSTRAP_BRANCH --push-every N` is set, `git push --set-upstream origin BOOTSTRAP_BRANCH` after every N successful commits plus a final push; 3× retry with 2/4/8s backoff on transient failures | Bootstrap Runner |
| 9 | Index in SQLite | INSERT into `laws` and `law_versions` (single version with `valid_to = NULL`) | SQLite Index |

### Performance

- 3,573 unique acts at 1 req/sec = ~60 minutes for content fetching
- Tree crawl: ~104 requests = ~2 minutes (dry run verified: 104 requests in ~2:04, no retries, no CF challenges)
- Periodic `git push` (if enabled, e.g. `--push-every 250`): ~14 intermediate pushes over the run, ~1-2 s each
- Total estimated time: ~2 hours including parsing, commits, and remote delivery

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

Point-in-time retrieval of legislation by Claude Code, Claude Desktop, and OpenAI Codex sessions over MCP/stdio. Tool surface defined in `container-view.md` §7; full design in `docs/plans/2026-05-09-phase1b-mcp-design.md`.

### 6.3.1 Build-time flow (`python -m index.build`)

Idempotent. Single transaction per build. Rebuildable from git at any ref. Phase 3 (DV monitor) and Phase 4 (consolidation) invoke this as a final step in their pipelines; in Phase 1b.1 it's a manual command operators run after corpus changes. Soft-warn at MCP server startup if `git rev-parse HEAD` differs from `laws.current_commit`; `--strict` refuses to start.

```
git ref → for each .md in {laws, codes, ordinances, regulations, implementing}/:
    read frontmatter + body
    INSERT laws (current_commit)
    INSERT law_versions (valid_from = effective_date / fecha_publicacion / bootstrap-run-date for §7.2)
    provisions.parse(body) → INSERT provisions (article rows AND alinea rows; text + text_hash)
    INSERT laws_fts (bg_normalize(title), bg_normalize(body))
COMMIT
```

`bg_normalize` is symmetric — same function called at insert AND query time so morphological forms match without a custom SQLite tokenizer.

### 6.3.2 `get_law(name, date=None)`

```
 Client (Claude Code/Desktop/Codex)    FastMCP/queries        SQLite              Git
     |                                    |                    |                   |
     |--[1] tools/call get_law ---------->|                    |                   |
     |   name="ЗОП", date="2020-06-15"    |                    |                   |
     |                                    |                    |                   |
     |    [2] resolve_name_to_law_id ──→  |                    |                   |
     |    identificador → slug → title    |                    |                   |
     |                                    |--SELECT laws ─────>|                   |
     |                                    |<-- law_id="zop" ---|                   |
     |                                    |                    |                   |
     |    [3] version_at_date ────────→   |                    |                   |
     |                                    |--SELECT versions ─>|                   |
     |                                    |<-- commit_hash ----|                   |
     |                                    |                    |                   |
     |    [4a] current version: read working-tree .md          |                   |
     |    [4b] historical:                |                    |                   |
     |                                    |--git show ────────────────────────────>|
     |                                    |<-- Markdown text ──────────────────────|
     |                                    |                    |                   |
     |    [5] split frontmatter+body, build GetLawResponse    |                   |
     |    [6] attach warnings if §7.2 (DATE_UNCERTAIN)         |                   |
     |                                    |                    |                   |
     |<--[7] tools/result ────────────────|                    |                   |
     |   {titulo, identificador, eli, ...,|                    |                   |
     |    body_markdown, warnings: [...]} |                    |                   |
```

Per D-024, response is a structured typed-dict, not bare Markdown — model gets metadata for citations alongside body.

### 6.3.3 `search(query, category=None, limit=20)`

```
 Client          FastMCP/queries           SQLite (laws_fts)
     |                |                       |
     |--search ───────|                       |
     |   "обществените поръчки"               |
     |                |                       |
     |   bg_normalize(query) →                |
     |   "обществен поръчк"                   |
     |                |--FTS5 MATCH ─────────>|
     |                |   SELECT law_id, ...  |
     |                |   FROM laws_fts JOIN laws
     |                |   WHERE laws_fts MATCH ?
     |                |   ORDER BY bm25(laws_fts)
     |                |   LIMIT ?             |
     |                |<-- ranked rows -------|
     |                |                       |
     |   §7.3: substitute "<doc_id=N>"        |
     |   for empty titles                     |
     |                |                       |
     |<-- list[SearchHit] ──|                 |
     |   [{law_id, identificador,             |
     |     title, category,                   |
     |     title_snippet, relevance}]         |
```

Per D-022, Bulgarian morphology coverage is ~70-80% via symmetric `bg_normalize`; Snowball stemmer + legal-term synonyms slated for Phase 1b.3 if usage data justifies.

**Two-tier ranking.** `index/fts.py:search_fts` issues two FTS5 MATCH queries in sequence rather than a single combined match. **Tier 1** is a column-restricted match against `title:` (e.g. `title:обществен title:поръчк`) — high precision; documents whose title contains every query token are almost always the right answer. **Tier 2** is general FTS5 over title+body — recall, catching body-only matches and abbreviations. Tier 2 is **skipped when tier 1 already filled the limit** (saves ~100 ms per query). Results are deduplicated by `law_id` (title-tier wins on ties). Rationale: BM25 alone over title+body would invert canonical-title rankings — a law's implementing regulation, with a denser body match, would outrank the law itself. FR-015 tracks the Phase 1b.3 stemmer + synonym dictionary that will further refine ranking.

### 6.3.4 `get_article(law, article, date=None)`

```
 Client                FastMCP/queries                SQLite (provisions)
     |                     |                              |
     |--get_article ──────>|                              |
     |   law="ЗОП"         |                              |
     |   article="чл. 14, ал. 2"                          |
     |                     |                              |
     |   resolve_name_to_law_id("ЗОП") → "zop"            |
     |   parse_article_spec("чл. 14, ал. 2")              |
     |     → (article="14", paragraph="2")                |
     |   version_at_date("zop", date) → commit_hash       |
     |                     |                              |
     |                     |--SELECT text ───────────────>|
     |                     |   FROM provisions            |
     |                     |   WHERE law_id="zop"         |
     |                     |     AND article="14"         |
     |                     |     AND (paragraph IS NULL   |
     |                     |          OR paragraph="2")   |
     |                     |     AND valid_from <= date   |
     |                     |     AND (valid_to IS NULL    |
     |                     |          OR valid_to >= date)|
     |                     |<-- text ────────────────────|
     |                     |                              |
     |<-- GetArticleResponse|                             |
     |   {law_id, article, paragraph, text, commit_hash} |
```

Per D-023, `provisions` is populated to alinea level from day one with `text` + `text_hash` columns — `get_article` is a single SQL lookup, no runtime Markdown parsing for current versions.

**Inclusive `valid_to`.** The `>=` in the WHERE clause is intentional — see `docs/data/schema-reference.md` §2 ("Predicate semantics") for the in-force predicate definition. A version with `valid_to = '2020-12-31'` is in force ON 2020-12-31; using `>` would silently exclude the boundary day. The same `>=` predicate appears in the `version_at_date` SQL in §6.3.2 above — both are uniform across the codebase per `mcp_server/queries.py`.

### 6.3.5 Error envelope (8 codes)

Per D-026, errors are first-class structured outputs. `LAW_NOT_FOUND`, `AMBIGUOUS_NAME` (§7.1 collisions), `NO_VERSION_AT_DATE`, `DATE_UNCERTAIN` (§7.2 warning, rides in successful response), `INVALID_ARTICLE_SPEC`, `ARTICLE_NOT_FOUND`, `INDEX_STALE`, `INDEX_MISSING`. FastMCP serializes `ToolError(code, payload)` into the MCP response envelope.

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
