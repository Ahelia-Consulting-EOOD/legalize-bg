# R4 — Text Consolidation, Time Machine & Storage

## Executive Summary

**Text consolidation** of Bulgarian legislation is feasible but challenging. Bulgarian amendments (ЗИД) follow a formulaic structure ("в чл. X, ал. Y думите '...' се заменят с '...'") that is highly parseable — estimated 70-80% of amendment operations can be automated with pattern matching, with the remainder requiring human review (complex restructuring, transitional provisions, retroactive effects).

**Recommended approach**: A **hybrid git-based + snapshot** storage model, inspired by the **Legalize** project (20 countries, 43K+ commits for Spain alone). Store consolidated legislation as Markdown files in git, with each amendment as a commit. Supplement with a **bitemporal SQLite/PostgreSQL index** for efficient point-in-time queries. For hosting, start with **GDrive + MCP** for simplicity, with a clear upgrade path to a **VPS with MCP server**.

**Key finding**: The **Legalize** project (legalize-dev) has already built a working pipeline for 20 countries using exactly this model — every law as a Markdown file, every reform as a Git commit. Bulgaria is NOT yet covered, but their pipeline engine could be adapted. This is the strongest prior art for our use case.

**Best open-source tool for our needs**: **Indigo** (Laws.Africa) is the most mature legislation management platform, but is likely overengineered for our scope. The Legalize pipeline pattern is more appropriate — simpler, git-native, and proven at scale.

---

## 1. Text Consolidation

### 1.1 Amendment Operations Taxonomy

Based on the academic literature (particularly Music et al. 2024 — the first automated consolidation paper) and analysis of Bulgarian legislative practice, amendment operations fall into these categories:

| Operation | Description | Frequency | Automation Difficulty |
|-----------|-------------|-----------|----------------------|
| **Substitution** | Replace word/phrase/sentence | ~40% | Low — pattern match |
| **Addition** | Insert new text (алинея, точка, буква) | ~25% | Low-Medium — position detection |
| **Deletion** | Remove word/phrase/paragraph | ~15% | Low — pattern match |
| **Renumbering** | Renumber articles/paragraphs after insert/delete | ~8% | Medium — cascading logic |
| **Restructuring** | Move, split, or merge articles/chapters | ~5% | High — structural understanding |
| **Full repeal** | Отменя се чл. X / закон Y | ~3% | Low — mark as repealed |
| **New chapter/section** | Add entirely new structural divisions | ~3% | Medium — structural insertion |
| **Table/annex modification** | Changes to appendices, tariffs, tables | ~1% | High — format-dependent |

### 1.2 Bulgarian Amendment Format (ЗИД)

Bulgarian amendments follow the **Закон за нормативните актове (ЗНА)** and have a highly formulaic structure. A ЗИД (Закон за изменение и допълнение) published in the Държавен вестник uses these canonical phrases:

**Substitution patterns:**
- `В чл. X, ал. Y думите „..." се заменят с „..."`
- `В чл. X, ал. Y, т. Z думата „..." се заменя с „..."`
- `Член X се изменя така: "..."`
- `Алинея Y на чл. X се изменя така: "..."`

**Addition patterns:**
- `В чл. X се създава ал. Y: "..."`
- `В чл. X, ал. Y се създава т. Z: "..."`
- `Създава се чл. Xа: "..."`
- `След чл. X се създава чл. Xа с текст: "..."`

**Deletion patterns:**
- `В чл. X, ал. Y думите „..." се заличават`
- `Член X се отменя`
- `Алинея Y на чл. X се отменя`

**Structural patterns:**
- `Създава се нов раздел Xa „..." с чл. X–Y`
- `Глава X се отменя`

These patterns are remarkably consistent because they are prescribed by ЗНА. This makes regex-based extraction highly feasible for the majority of amendments.

### 1.3 Automation Feasibility

**Estimated automation rates by approach:**

| Approach | Coverage | Accuracy | Notes |
|----------|----------|----------|-------|
| **Regex pattern matching** | 70-75% | 95%+ | Handles substitution, simple add/delete |
| **+ NLP entity recognition** | 80-85% | 90%+ | Handles article references, cross-refs |
| **+ LLM consolidation** | 90-95% | 60-85% | Handles complex restructuring (per Music et al.) |
| **Human review** | 100% | 99%+ | Required for edge cases |

**Key insight from Music et al. (2024)**: Their French PLF consolidation achieved 63% correctness with fine-tuned OpenLLaMa-13b, and 61% with GPT-4 (on a harder subset). However, **Bulgarian amendments are MORE structured than French** ones — the formulaic ЗИД format means regex can handle a much larger proportion without needing LLMs.

**Recommended approach**: Regex-first pipeline with LLM fallback for complex cases, plus mandatory human review for structural changes.

### 1.4 Edge Cases

| Edge Case | Description | Frequency | Handling |
|-----------|-------------|-----------|----------|
| **Retroactive amendments** | ЗИД with `влиза в сила от ...` date in the past | Rare | Bitemporal model handles this naturally |
| **Transitional provisions** | Преходни и заключителни разпоредби — temporary rules | Common | Store separately, track validity period |
| **Partial repeal** | Only certain алинеи/точки repealed | Moderate | Mark individual elements, not whole article |
| **Conditional commencement** | `Влиза в сила от датата на присъединяване...` | Rare | Flag for manual date resolution |
| **Cross-law amendments** | ЗИД of law X amends law Y in ПЗР | Very common | Parse ПЗР section, apply to target law |
| **Corrigenda** | Поправки in subsequent ДВ issues | Occasional | Treat as another amendment event |
| **Court annulment** | КС обявява чл. X за противоконституционен | Rare | Track as special amendment event |
| **Deferred effect** | Provisions that enter into force on a future date | Common | Track commencement date per provision |

The **cross-law amendment** pattern (where ПЗР of a ЗИД to law A also amends laws B, C, D) is particularly important — a single ДВ issue can contain amendments to dozens of laws.

---

## 2. Temporal Versioning

### 2.1 Data Models

| Model | Description | Pros | Cons | Best For |
|-------|-------------|------|------|----------|
| **Valid-time only** | Track when law provisions are legally in force | Simple, covers main use case | Can't answer "what did we know at time X?" | Basic time machine |
| **Transaction-time only** | Track when data entered the system | Full audit trail | Can't query "law as of date X" | Audit/compliance |
| **Bitemporal** | Both valid-time AND transaction-time | Complete temporal picture | More complex queries and storage | Regulated/legal domains |

**Valid-time** is the period when a legal provision is in force (от ДВ бр. X/дата Y до изменение в ДВ бр. Z/дата W).

**Transaction-time** is when we recorded the information in our database.

**For legislation, valid-time is essential; transaction-time is useful but not critical.** The main use case is "what did ЗОП say on 2024-01-15?" (valid-time query), not "when did we first learn about the 2024 amendment?" (transaction-time query).

**Recommendation**: Implement valid-time as the primary dimension. Add transaction-time only if auditing requirements emerge.

### 2.2 Implementation Approaches

#### legislation.gov.uk (Gold Standard)
- **Data model**: FRBR-based (Work → Expression → Manifestation → Item)
  - **Work** = the law itself (e.g., "Public Contracts Regulations 2015")
  - **Expression** = a specific version at a point in time
  - **Manifestation** = a specific format (HTML, XML, PDF)
- **Storage**: MarkLogic (native XML database) + GraphDB/Virtuoso RDF stores, each version stored as a separate XML document
- **Format**: Crown Legislation Markup Language (CLML), migrating to Akoma Ntoso
- **URIs**: RESTful — `/ukpga/1985/67/2001-04-01` gives the version as of 2001-04-01
- **Base date**: February 1991 — no point-in-time data before this
- **Scale**: ~100,000 items of legislation, ~15M XML elements
- **Team**: ~43 people at The National Archives maintain the editorial process. Amendments are applied **manually** by editors. Has an editorial backlog of unapplied effects.
- **Lesson**: Incredibly powerful but took years and millions of pounds to build. Even with 43 staff, they have a backlog.

#### Italy — Normattiva (Notable EU Example)
- **"Multivigenza" system**: maintains original version, current consolidated version, and any past point-in-time version
- **Scale**: ~75,000 acts from 1861
- **Verification**: Algorithmic verification against Gazzetta Ufficiale
- **Lesson**: Demonstrates that point-in-time access at scale is achievable even for a large, old corpus

#### Czech Republic — e-Sbírka (2024, Newest EU System)
- Fully digital official gazette, replaced paper publication
- Supports point-in-time access
- Integrates with EUR-Lex and N-Lex
- **Lesson**: Most recent EU implementation — could be a model for Bulgaria

#### Estonia — Riigi Teataja
- Digital-only since 2010, consolidated texts maintained
- ELI-compatible URIs (e.g. `riigiteataja.ee/en/eli/...`)
- **Lesson**: Small EU country successfully maintaining digital legislation — closest analogue to Bulgaria's scale

#### Ontario e-Laws
- Point-in-time from 2003/2004
- New version created on every amendment
- **Official digital copies have legal force** (unlike EUR-Lex consolidated texts)
- **Lesson**: Legal force for digital consolidated texts is possible but requires explicit legislative authorization

#### EUR-Lex
- **Data model**: FRBR-based CDM ontology (Work/Expression/Manifestation/Item), ELI (European Legislation Identifier)
  - Each consolidated version is a separate document pointing to base act + all amending acts
  - Version V0 created immediately from base act (textually identical but distinct document)
  - URI pattern includes start-date (entry into force of latest included amendment)
- **Consolidation**: Semi-automated by the Publications Office; consolidated texts have no legal value
- **ELI-I**: Formal data model for representing impacts of amendments on base text
- **Format**: Formex (EU-specific XML), migrating to Akoma Ntoso via AKN4EU
- **Scale**: CELLAR stores 2.7M works; ~250,000 legal acts, ~88,000 consolidated texts
- **Lesson**: The "no legal value" disclaimer means they can accept lower accuracy

#### N-Lex (EU gateway to national legislation)
- Links to national databases including Bulgaria
- Bulgarian link points to lex.bg
- Does NOT provide its own consolidated versions of national legislation

### 2.3 Git-Based Versioning

The **Legalize** project (legalize-dev) demonstrates that git-based versioning works at scale:

**How it works:**
1. Each law is a Markdown file with YAML frontmatter (title, identifier, rank, publication date, status, ELI)
2. When a reform is published, the file is updated and committed
3. Commit date = official publication date
4. Commit trailers contain norm ID and reform ID
5. `git log -- path/to/law.md` gives complete amendment history
6. `git diff` between commits shows exact textual changes
7. `git show <commit>:path/to/law.md` gives any historical version

**Scale evidence (legalize-es — Spain):**
- 12,235 norms, 43,104 commits
- 17 autonomous communities
- Pipeline built in ~4 hours using Claude Code
- Data source: BOE open data API

**Pros:**
- Natural diff/history/blame built-in
- Standard tooling (GitHub, GitLab)
- No custom database required
- Human-readable format (Markdown)
- Easy to verify changes
- Existing ecosystem for CI/CD, search
- Branching for "what-if" scenarios

**Cons:**
- Point-in-time queries require `git log --before` + checkout (not instant)
- No structured query language (can't ask "all laws amended in 2024")
- Large repos can get slow (but legalize-es with 43K commits works fine)
- Binary files (PDFs, images) don't diff well
- Cross-references between laws not natively supported

**Verdict**: Git is an excellent **storage backend** for consolidated legislation, but needs a **supplementary index** for temporal and structured queries.

---

## 3. Storage Strategies

| Strategy | Storage Efficiency | Query Speed | Implementation Complexity | Best For |
|----------|--------------------|-------------|--------------------------|----------|
| **Snapshot** (full text per version) | Low (redundant text) | Excellent (direct lookup) | Very Low | Small corpus, simple needs |
| **Diff-based** (base + patches) | High | Moderate (reconstruct) | Medium | Archive, bandwidth-limited |
| **Event-sourced** (amendment events) | Very High | Slow (replay all events) | High | Audit trail, analytics |
| **Git-based** (commits = amendments) | Medium-High (git packing) | Good (checkout any commit) | Low-Medium | Development workflow, diffs |
| **Hybrid: Git + Index** | Medium | Excellent | Medium | **Best overall for our use case** |

### Recommended: Hybrid Git + SQLite Index

```
┌─────────────────────────────────────┐
│         Git Repository              │
│  /bg/laws/zop.md                    │
│  /bg/laws/zeu.md                    │
│  /bg/laws/zna.md                    │
│  Each commit = one amendment event  │
│  Markdown + YAML frontmatter        │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│      SQLite Index (derived)         │
│  law_versions:                      │
│    law_id, valid_from, valid_to,    │
│    commit_hash, dv_issue, dv_date,  │
│    amending_act                     │
│  provisions:                        │
│    law_id, article, paragraph,      │
│    valid_from, valid_to,            │
│    text_hash                        │
│  amendments:                        │
│    source_act, target_law,          │
│    operation, dv_issue, date        │
└─────────────────────────────────────┘
```

The git repo is the **source of truth** (human-readable, diffable, version-controlled). The SQLite index is **derived** and can be rebuilt from git at any time. This gives us:
- `git show <hash>:bg/laws/zop.md` → any historical version (time machine)
- `SELECT * FROM law_versions WHERE law_id='zop' AND valid_from <= '2024-01-15' ORDER BY valid_from DESC LIMIT 1` → find the right commit for a date
- `SELECT * FROM amendments WHERE dv_date >= '2024-01-01'` → all amendments in a period

---

## 4. Open-Source Tools

### 4.1 Indigo (Laws.Africa) — Most Mature Platform

- **URL**: https://github.com/laws-africa/indigo
- **Stack**: Django/Python, PostgreSQL, Vue.js
- **Format**: Akoma Ntoso XML (via Cobalt library)
- **Stars**: 71 | **Commits**: 10,926 | **Latest**: v19.1.0 (Dec 2025)
- **License**: LGPL 3.0
- **Features**: Full legislation lifecycle (publication, commencement, amendment, repeal), multi-version tracking, REST API, editorial workflow
- **Strengths**: Production-proven (used across Africa), handles consolidation, Docker deployment
- **Weaknesses**: Designed for African jurisdictions, heavy infrastructure (PostgreSQL, Redis, Elasticsearch), Akoma Ntoso XML is verbose
- **Relevance for BG**: **Medium** — could be adapted but significant localization work needed. Overkill for a corpus of ~500 laws.

### 4.2 Legalize (legalize-dev) — Best Pattern Match

- **URL**: https://github.com/legalize-dev/legalize
- **Stack**: Node.js pipeline, Git, Markdown
- **Coverage**: 20 countries, 400K+ norms
- **Stars**: Growing | **Commits**: 43K+ (Spain alone)
- **License**: Open source
- **Features**: Automated pipeline per country, git-native versioning, YAML frontmatter, daily updates
- **Strengths**: Simple, proven at scale, human-readable output, easy to fork/adapt
- **Weaknesses**: No structured query layer, no Akoma Ntoso, no point-in-time API
- **Relevance for BG**: **High** — Bulgaria is NOT covered yet. We could either contribute a BG pipeline or fork the pattern for our own use. The pipeline was built for Spain in ~4 hours with Claude Code.

### 4.3 LEOS (European Commission) — EU Legislative Drafting

- **URL**: https://interoperable-europe.ec.europa.eu/.../leos-open-source-software-editing-legislation
- **Stack**: Java (likely Spring), Akoma Ntoso XML (AKN4EU subschema), CMIS storage
- **Version**: v5.3.1 (March 2026)
- **License**: EUPL 1.2
- **Features**: Web-based co-editing, comments/suggestions, version control, structural validation
- **Strengths**: EU-backed, AKN4EU interoperability, designed for the legislative drafting workflow
- **Weaknesses**: Drafting tool, NOT a consolidation/publishing tool. Heavy enterprise architecture.
- **Relevance for BG**: **Low** — wrong use case (drafting vs. consolidation)

### 4.4 XTDB — Bitemporal Database

- **URL**: https://github.com/xtdb/xtdb
- **Stack**: Clojure/JVM, Apache Arrow, Kafka (v1) or standalone (v2)
- **License**: MPL 2.0
- **Features**: Native bitemporality (valid-time + transaction-time), SQL interface, immutable storage
- **Strengths**: Purpose-built for temporal data, no schema required, time-travel queries built-in
- **Weaknesses**: Clojure ecosystem (niche), v2 is relatively new, requires JVM
- **Relevance for BG**: **Medium** — excellent temporal model but heavy infrastructure for our scale

### 4.5 Metanorma — Standards Authoring

- **URL**: https://www.metanorma.org/
- **Stack**: Ruby, AsciiDoc → HTML/PDF/Word
- **Features**: Document metamodels, multi-format output, ISO/IETF standard support
- **Relevance for BG**: **Low** — designed for standards documents, not legislation

### 4.6 Legal MCP Servers (Various)

Several MCP servers exist for legislation access:
- **canlii-mcp** (Canada): CanLII API integration
- **legifrance-mcp** (France): Legifrance API
- **German-law-mcp**: gesetze-im-internet.de
- **us-legal-mcp**: US Congress, Federal Register
- **Dutch Law MCP**: Dutch statutes

**No Bulgarian law MCP server exists.** Building one would be a direct output of this project.

### 4.7 open-source-legislation (spartypkp) — Cautionary Tale

- **URL**: https://github.com/spartypkp/open-source-legislation
- **Stack**: Python, PostgreSQL + pgvector, Pydantic
- **Status**: **Abandoned** (Aug 2024) — infrastructure shut down, all download links broken
- **Reason**: "Full-time job disguised as a side project" — maintenance burden of 50+ jurisdictions
- **Useful patterns**: Hierarchical node IDs (`us/ca/statutes/title=1/chapter=2/section=3`), structure vs. content nodes, JSONB metadata
- **Lesson**: Scope carefully. Don't try to cover all of Bulgarian legislation at once.

### 4.8 Consolidation-Specific Research

**Automatic Legislative Text Consolidation (Music et al., 2024)**
- **URL**: https://arxiv.org/abs/2501.16794
- **Approach**: Fine-tuned LLM (OpenLLaMa-13b with LoRA) for French tax code consolidation
- **Results**: 63% correctness on real PLF 2024, 49.8% coverage (token limits)
- **Lesson**: LLMs work for consolidation but with significant error rate. Regex-first is better for structured amendment formats like Bulgarian ЗИД.

---

## 5. DV as Consolidation Source

### 5.1 Feasibility Assessment

**dv.parliament.bg** publishes the official Държавен вестник. Key facts:

| Aspect | Details |
|--------|---------|
| **Archive depth** | 4,101 issues indexed; browsable from 2003, full-text search from 2009 |
| **Format** | PDF downloads for individual issues + HTML view online. **No XML, no API, no bulk download.** |
| **Publication frequency** | Every Tuesday and Friday + extraordinary issues (~100-110/year) |
| **Content per issue** | Laws, ЗИД, наредби, решения, обявления |
| **Free access** | Yes, fully open |
| **Alternative archives** | Ciela.net (180K scanned pages 1920-1989, full archive from 1885), Lex Alert (organized by year) |
| **Total corpus size** | ~150-200 MB plain text, ~1 GB with metadata — **storage is trivial** |
| **Commercial alternatives** | APIS Pravo (~EUR 269/yr) and Ciela Normi (~EUR 145/yr) both offer built-in time machine with daily DV updates |

### 5.2 Reconstruction Pipeline

To build consolidated texts from DV:

```
1. FETCH: Download all DV issues (PDF or HTML)
   ├── dv.parliament.bg (official, JS-heavy)
   ├── ciela.net/свободна-зона-държавен-вестник (free archive)
   └── N-Lex (last 7 years in PDF)

2. PARSE: Extract amendment instructions from ЗИД texts
   ├── OCR for older scanned PDFs
   ├── HTML extraction for newer issues
   └── Regex pattern matching for amendment operations

3. CATALOG: Build amendment event timeline per law
   ├── Law ID → [ЗИД₁(DV 45/2020), ЗИД₂(DV 78/2021), ...]
   └── Each event: DV issue, date, operation type, affected articles

4. CONSOLIDATE: Apply amendments sequentially to base text
   ├── Start with original law text (from first DV publication)
   ├── Apply each ЗИД in chronological order
   └── Generate consolidated version at each step

5. VERIFY: Cross-check against lex.bg consolidated versions
   ├── Compare our output with lex.bg current version
   └── Fix discrepancies, improve parser
```

### 5.3 Challenges

| Challenge | Severity | Mitigation |
|-----------|----------|------------|
| **OCR quality** for pre-2000 PDFs | High | Limit scope to post-2000 initially |
| **Cross-law amendments** in ПЗР | Medium | Parse ПЗР section of every ЗИД |
| **JavaScript rendering** of dv.parliament.bg | Medium | Use Playwright or alternative sources |
| **Volume** (~100+ DV issues/year × 20+ years) | Medium | Incremental processing, start with key laws |
| **Missing base texts** for very old laws | High | Use lex.bg or APIS for base text, DV for amendments |

### 5.4 lex.bg as Amendment Timeline Source (Confirmed by Site Analysis)

While lex.bg cannot provide past versions, it CAN provide:
1. **Current consolidated text** via `/laws/ldoc/{docID}` — already working
2. **Complete amendment history** via `div.HistoryOfDocument` — lists every ДВ amendment with issue number and date (e.g., "Обн. ДВ. бр.13 от 16 Февруари 2016г., доп. ДВ. бр.34 от 3 Май 2016г., ...")
3. **Cross-reference IDs** via `window.external.OpenRef(this, NNNN)` — numeric reference IDs to other acts
4. **Per-article metadata** via `/lawsdetails/{type}/{docID}/{articleID}` — cross-refs, case law, notes

**Pipeline implication**: We can scrape the amendment history from lex.bg to build the SQLite index of amendment events (law → DV issue → date), then fetch the actual ЗИД text from DV to apply/reverse amendments.

### 5.5 Pragmatic Alternative

Rather than reconstructing from DV from scratch:
1. **Get current consolidated text** from lex.bg (already working for most laws)
2. **Track amendments going forward** by monitoring new DV issues
3. **Build backward** only for laws where time machine is specifically needed
4. **Use APIS/legislation.apis.bg** for structured data where available

This is far more practical than a full DV reconstruction.

### 5.6 Build vs. Buy Consideration

Commercial time machines exist at modest cost (APIS Pravo ~EUR 269/yr, Ciela Normi ~EUR 145/yr). However, building our own offers:
- **MCP integration** — commercial tools have no Claude Code integration
- **Programmable access** — SQL queries, git diffs, automated monitoring
- **No vendor lock-in** — own our data pipeline
- **Customizable** — can add domain-specific features (e.g., ЗОП change tracking)
- **Free** — no recurring cost

**Verdict**: Build our own for the MCP/programmability value, but commercial tools serve as a **verification baseline** (compare our consolidated output against theirs).

---

## 6. Hosting Options

| Option | Cost | Maintenance | Query Speed | Freshness | MCP Integration | Best For |
|--------|------|-------------|-------------|-----------|-----------------|----------|
| **GDrive folder** | Free | Very Low | Slow (file search) | Manual update | Via Google Drive MCP | Quick start, small corpus |
| **Git repo (GitHub)** | Free | Low | Medium (git ops) | CI/CD pipeline | Via local clone | Version control, diffs |
| **SQLite + GDrive/local** | Free | Low | Fast (SQL queries) | Script-based | Direct file access | Structured queries |
| **VPS + PostgreSQL** | ~$5-20/mo | Medium | Very Fast | Automated | Custom MCP server | Production quality |
| **Static site (GitHub Pages)** | Free | Low | N/A (browse only) | GitHub Actions | No MCP, web only | Public access |
| **Custom MCP server** | Depends on hosting | Medium-High | Fast | Real-time | Native | Ideal for Claude Code |

### Recommended Phased Approach

**Phase 1 (Now)**: Git repo + SQLite index, local access via Claude Code
- Store consolidated laws as Markdown in a git repo
- Build SQLite index for temporal queries
- Access via local filesystem — no hosting needed

**Phase 2 (When needed)**: Add MCP server
- Build a lightweight MCP server (stdio transport) that queries the git repo + SQLite
- Tools: `get_law(name, date?)`, `search_law(query)`, `get_article(law, article, date?)`, `list_amendments(law, from?, to?)`
- Run locally alongside Claude Code

**Phase 3 (If sharing needed)**: Host on VPS or GDrive
- Push git repo to GitHub (private)
- Either: Share via Google Drive MCP (simple) or deploy MCP server on VPS (powerful)

---

## Implications for Architecture

### Recommended Stack

```
┌──────────────────────────────────┐
│       MCP Server (Phase 2)       │
│  get_law(), search(), history()  │
└──────────┬───────────────────────┘
           │
    ┌──────┴──────┐
    │             │
    ▼             ▼
┌────────┐  ┌──────────┐
│  Git   │  │  SQLite  │
│  Repo  │  │  Index   │
│ (truth)│  │(derived) │
└────────┘  └──────────┘
    │
    ▼
┌────────────────────────────────┐
│     Consolidation Pipeline     │
│  1. Fetch ЗИД from DV/lex.bg  │
│  2. Parse amendment operations │
│  3. Apply to base text         │
│  4. Commit to git              │
│  5. Update SQLite index        │
└────────────────────────────────┘
```

### Key Design Decisions

1. **Format**: Markdown with YAML frontmatter (like Legalize), NOT Akoma Ntoso XML. Rationale: simpler, human-readable, sufficient for our use case (~500 laws, not 100K).

2. **Storage**: Git repo as source of truth + SQLite index for queries. Rationale: proven pattern, no infrastructure, easy to verify.

3. **Consolidation**: Regex-first pipeline for Bulgarian ЗИД format, with optional LLM fallback. NOT full NLP pipeline initially.

4. **Scope**: Start with ~20 key laws (ЗОП, ЗЕУ, ЗНА, etc.), expand incrementally. Do NOT attempt full corpus.

5. **Time machine**: Valid-time only (via git history + SQLite valid_from/valid_to). Bitemporal only if audit requirements emerge.

6. **Sources**: lex.bg for current consolidated text (base), DV for amendment tracking (going forward).

---

## Open Questions

1. ~~**Does lex.bg expose version history?**~~ **RESOLVED**: No. lex.bg only serves the latest consolidated version. The `div.HistoryOfDocument` lists all DV amendment references (issue number + date), but past versions are NOT accessible via web — the `window.external.OpenEdition(N)` handler was a Ciela desktop app API. No ELI, no Akoma Ntoso — proprietary Ciela backend with windows-1251 encoding.
2. ~~**How far back does dv.parliament.bg archive go in structured format?**~~ **RESOLVED**: 4,101 issues indexed, browsable from 2003, full-text search from 2009. PDF only, no XML/API/bulk download. Ciela has scanned archive back to 1885. Total corpus is ~150-200 MB plain text — storage is trivial. Commercial time machines exist: APIS Pravo (~EUR 269/yr), Ciela Normi (~EUR 145/yr).
3. ~~**Is EUR-Lex consolidation automated or manual?**~~ **RESOLVED**: Semi-automated by Publications Office. Consolidated texts have no legal value. legislation.gov.uk uses 43 editorial staff applying amendments manually (with backlog).
4. **Should we contribute a Bulgarian pipeline to Legalize?** (Pro: community, prior art. Con: dependency on external project)
5. **What is the exact coverage of legislation.apis.bg?** (Their REST API may provide structured amendment data)
6. **Can КС (Constitutional Court) decisions be tracked as amendment events?** (When чл. X is declared unconstitutional)
7. **How to handle the ПЗР (transitional provisions) problem?** — ПЗР of law A can amend laws B, C, D, E...

---

## Sources Log

| # | Source | URL | Date Accessed | What Was Found |
|---|--------|-----|--------------|----------------|
| 1 | Automatic Legislative Text Consolidation (Arxiv) | https://arxiv.org/abs/2501.16794 | 2026-04-19 | LLM-based consolidation: 63% accuracy on French PLF, operation taxonomy |
| 2 | ACL Anthology (Proceedings) | https://aclanthology.org/2024.nllp-1.13/ | 2026-04-19 | Peer-reviewed version of the consolidation paper |
| 3 | Indigo Platform (Laws.Africa) | https://github.com/laws-africa/indigo | 2026-04-19 | Django/AKN platform, 71 stars, v19.1.0, LGPL 3.0 |
| 4 | Indigo Documentation | https://indigo.readthedocs.io/en/latest/ | 2026-04-19 | Full legislation lifecycle management |
| 5 | Legalize (legalize-dev) | https://github.com/legalize-dev/legalize | 2026-04-19 | 20 countries, git-based versioning, markdown format |
| 6 | Legalize-ES (Spain) | https://github.com/legalize-dev/legalize-es | 2026-04-19 | 12,235 norms, 43,104 commits, BOE API pipeline |
| 7 | legislation.gov.uk (Wikipedia) | https://en.wikipedia.org/wiki/Legislation.gov.uk | 2026-04-19 | FRBR model, MarkLogic, CLML/AKN |
| 8 | legislation.gov.uk (SlideShare) | https://www.slideshare.net/JeniT/legislationgovuk | 2026-04-19 | RESTful URI architecture, point-in-time design |
| 9 | legislation.gov.uk Developer Formats | https://www.legislation.gov.uk/developer/formats | 2026-04-19 | XML, RDF, HTML5, PDF output formats |
| 10 | EUR-Lex Consolidated Texts | https://eur-lex.europa.eu/collection/eu-law/consleg.html | 2026-04-19 | Consolidation methodology, no legal value disclaimer |
| 11 | EUR-Lex ELI Implementation | https://eur-lex.europa.eu/eli-register/implementing_eli.html | 2026-04-19 | ELI data model, ELI-I for impact tracking |
| 12 | Akoma Ntoso (Wikipedia) | https://en.wikipedia.org/wiki/Akoma_Ntoso | 2026-04-19 | OASIS standard, lifecycle element, AT4AM |
| 13 | Akoma Ntoso OASIS Spec | https://docs.oasis-open.org/legaldocml/akn-core/v1.0/akn-core-v1.0-part1-vocabulary.html | 2026-04-19 | Full XML vocabulary specification |
| 14 | XTDB Bitemporality | https://v1-docs.xtdb.com/concepts/bitemporality/ | 2026-04-19 | Bitemporal model, legal documentation use case |
| 15 | XTDB GitHub | https://github.com/xtdb/xtdb | 2026-04-19 | Open source bitemporal database, MPL 2.0 |
| 16 | Version Control for Law (Data Foundation) | https://datafoundation.org/news/blogs/335/335 | 2026-04-19 | USLM standard, machine-readable amendments |
| 17 | GitLaw (HN discussion) | https://news.ycombinator.com/item?id=3967921 | 2026-04-19 | Early discussion of git for law |
| 18 | LEOS (Interoperable Europe) | https://interoperable-europe.ec.europa.eu/.../leos-open-source-software-editing-legislation | 2026-04-19 | EU legislative drafting tool, AKN4EU, v5.3.1 |
| 19 | PostgreSQL Temporal Tables | https://github.com/arkhipov/temporal_tables | 2026-04-19 | SQL:2011 temporal extension for PostgreSQL |
| 20 | open-source-legislation (spartypkp) | https://github.com/spartypkp/open-source-legislation | 2026-04-19 | Abandoned Aug 2024, lessons on scope/maintenance |
| 21 | Martin Fowler - Bitemporal History | https://martinfowler.com/articles/bitemporal-history.html | 2026-04-19 | Canonical bitemporal modeling reference |
| 22 | Metanorma | https://www.metanorma.org/ | 2026-04-19 | Standards authoring, not legislation-focused |
| 23 | dv.parliament.bg | https://dv.parliament.bg/DVWeb/dv130.faces | 2026-04-19 | Official DV portal, free access |
| 24 | Ciela.net DV Archive | https://www.ciela.net/свободна-зона-държавен-вестник | 2026-04-19 | Free digitized DV archive |
| 25 | N-Lex Bulgaria | https://n-lex.europa.eu/n-lex/info/info-bg/index?lang=bg | 2026-04-19 | Last 7 years of DV in PDF |
| 26 | canlii-mcp (GitHub) | https://github.com/mohammadfarooqi/canlii-mcp | 2026-04-19 | Canadian law MCP server pattern |
| 27 | German-law-mcp (GitHub) | https://github.com/Ansvar-Systems/German-law-mcp | 2026-04-19 | German law MCP server pattern |
| 28 | APIS (apis.bg) | https://apis.bg/en/ | 2026-04-19 | Commercial BG legislation provider, has API |
