# Phase 1b — MCP Server: Design

**Date:** 2026-05-09
**Authors:** ekimir + Claude Code
**Status:** Approved (brainstorming complete; implementation plan to follow via `superpowers:writing-plans`)
**Authoritative for:** Phase 1b architecture, scope, and acceptance criteria

---

## 1. Goal

Expose the 3,573-act Bulgarian legislation corpus to Claude Code, Claude Desktop, and OpenAI Codex via a single Model Context Protocol (MCP) server. The server is the polished, primary access surface — direct file access remains a fallback but is no longer the expected pattern.

The server is built **for completeness, not "good enough"**. Phase 1b is split into three mandatory milestones (§4) so the polish bar is reached without retrofits.

## 2. Authority docs consulted

- `docs/process/delivery-contract.md` — Phase 1b Definition of Done, rate limiting, branch model
- `docs/process/OWNER-DIRECTIVES.md` — D-002 (lex.bg = bootstrap only)
- `docs/process/COVERAGE-FLOOR.md` — required MCP tools (`get_law`, `search`, `get_article` minimum)
- `docs/architecture/container-view.md` §7 — MCP Server tool signatures (will be updated by this design)
- `docs/architecture/runtime-flows.md` §6.3 — MCP query flow placeholder (will be replaced)
- `docs/data/canonical-data-model.md` §7 — corpus data quality observations (binding on tool behavior)
- `docs/data/schema-reference.md` — YAML frontmatter + SQLite schema
- `docs/testing/test-strategy.md` Phase 1b section
- `docs/frs/INDEX.md` — FR-001 (Phase 2 temporal index, depends on 1b.1 provisions table)

## 3. Tech stack

- Python 3.12+
- `fastmcp` — high-level MCP server framework (transitive: official `mcp` SDK)
- `sqlite3` (stdlib) with FTS5 (compiled in by default on modern Python builds)
- `pyyaml`, `subprocess` (for `git show`) — already in pyproject.toml
- Pure-Python; no C extensions, no external services, no network at runtime

Transports: **stdio only** for Phase 1b.1 (the three target clients all support it). SSE/HTTP transports deferred to Phase 1b.3 only if a non-MCP-aware caller emerges.

## 4. Roadmap — three mandatory milestones

| Milestone | Workflow target | Scope | Acceptance |
|---|---|---|---|
| **Phase 1b.1** | B (drafting/review) + A (legal research, article precision) | FastMCP server (stdio); `get_law`, `search`, `get_article`; SQLite index build; `provisions` populated to article AND alinea level; FTS5 + Bulgarian-aware pre-normalization (`bg_normalize`); structured (typed-dict) responses; `index/migrations.py`; §7.1-7.3 data-quality semantics enforced; error taxonomy with all 8 codes returning structured payloads | All three tools work end-to-end through Claude Code, Claude Desktop, Codex; <2s single-law, <100ms search, <50ms article (current); test suite covers each error code and each §7.x case |
| **Phase 1b.2** | C (structured backend) | Versioned JSON response schemas published as `tools.json` + `mcp_server/schemas.py` dataclass freeze; error taxonomy formalized with stable codes for downstream callers; idempotency contract documented; performance regression tests promoted from soft to hard assertions | External callers can consume responses programmatically with breaking-change discipline; perf budgets fail CI on regression |
| **Phase 1b.3** | Operator/end-user polish | Structured logging + per-tool-call metrics; packaging (`pip install legalize-bg-mcp`); deployment docs; Claude Code/Desktop/Codex setup guides; Bulgarian stemmer + legal-term synonym dictionary (deferred from Q3(C) per usage data) | Daily-use ready for end-users; ready for third-party deployment |

Phase 2+ work (`history`, `diff`, `amendments_in_period`, temporal index population) is strictly out of Phase 1b scope but the 1b.1 schema (alinea-level `provisions` rows, populated `text_hash` on every row) is built to enable Phase 2/4 without schema migration.

## 5. Architecture

```
          Claude Code / Claude Desktop / OpenAI Codex
                   |
                   | JSON-RPC over stdio (MCP)
                   v
      ┌────────────────────────────┐
      │     FastMCP Server         │   mcp_server/server.py
      │  @tool get_law             │   — tool definitions, docstrings = MCP descriptions
      │  @tool search              │   — no business logic inline
      │  @tool get_article         │
      └────────────┬───────────────┘
                   v
      ┌────────────────────────────┐
      │    Query layer (pure)      │   mcp_server/queries.py
      │  resolve_name_to_law_id    │   — handles §7.1 (slug ≠ title)
      │  version_at_date           │   — handles §7.2 (date-uncertain)
      │  parse_article_spec        │   — Bulgarian article variant parser
      │  full_text_search          │   — FTS5 + bg_normalize
      │  article_lookup            │   — provisions table SQL
      └─────┬──────────────────┬───┘
            v                  v
      ┌──────────┐      ┌──────────────┐
      │  SQLite  │      │  Git corpus  │
      │ catalog  │      │  (main)      │
      └──────────┘      └──────────────┘
           ^
           │
      ┌──────────────────────────────────┐
      │ Index builder                    │   index/build.py
      │  git ref → corpus iteration      │   index/provisions.py
      │   → laws + law_versions rows     │   index/fts.py
      │   → provisions rows (article + alinea)
      │   → laws_fts INSERT              │
      │  Idempotent; rebuildable from git│
      └──────────────────────────────────┘
```

### Invariants

- **Index is a derived cache.** Always rebuildable from git HEAD + YAML frontmatter. Never a source of truth.
- **FastMCP is the tool surface, never business logic.** Tool handlers are 5-10 lines each, calling pure functions in `mcp_server/queries.py`. The query layer is testable without an MCP harness.
- **Working tree for current versions; `git show` for historical.** Date-qualified queries resolve to a `commit_hash` via SQLite, then `subprocess.run(["git", "show", f"{commit_hash}:{path}"])`.
- **§7 data-quality cases are server-enforced contracts**, not per-conversation reinventions. The justification for the MCP investment over direct file access.

## 6. Components

```
legalize-bg/
├── fetcher/bg/                 (existing; unchanged in 1b.1)
│
├── index/                      (existing package; extended)
│   ├── catalog.py              — schema + insert_law (extended; provisions schema migrated)
│   ├── build.py                NEW — index builder; idempotent; CLI: `python -m index.build`
│   ├── provisions.py           NEW — Markdown body → article + alinea rows; goldens-tested
│   ├── fts.py                  NEW — FTS5 virtual table + bg_normalize symmetric pre-normalizer
│   └── migrations.py           NEW — forward-only schema versioning; from day one
│
├── mcp_server/                 NEW package
│   ├── __init__.py
│   ├── __main__.py             — `python -m mcp_server` entry point
│   ├── server.py               — FastMCP instance + tool definitions
│   ├── queries.py              — pure query functions; no MCP dependency
│   ├── schemas.py              — typed-dict / dataclass response shapes
│   └── errors.py               — `ToolError` envelope + 8 error codes
│
├── scripts/
│   └── build_index.py          — one-line wrapper around `index.build.main`
│
└── tests/
    ├── index/
    │   ├── test_build.py
    │   ├── test_provisions.py  — golden-file extraction (article + alinea)
    │   ├── test_fts.py         — bg_normalize roundtrip + search regression suite
    │   └── test_migrations.py  — forward-only application
    ├── mcp_server/
    │   ├── test_queries.py     — pure-function in-memory SQLite
    │   ├── test_resolve_name.py
    │   ├── test_get_law.py     — current + historical (tmp git repo)
    │   ├── test_get_article.py — every spec form
    │   ├── test_search.py
    │   ├── test_errors.py      — one test per code
    │   └── test_tools_e2e.py   — FastMCP test client round-trip
    └── fixtures/
        ├── golden/provisions/  NEW — JSON dumps per HTML fixture
        ├── queries/            NEW — bg_search_regression.yaml
        └── catalog/            NEW — mini.db.sql (10-act test catalog)
```

### 6.1 Index builder (`index/build.py`)

Idempotent. Single transaction per build. CLI:

```
python -m index.build [--db catalog.db] [--git-ref HEAD] [--corpus PATH]
```

Steps per .md file:
1. Read frontmatter + body
2. INSERT laws (identificador, title, category, current_commit, status)
3. INSERT law_versions (one per act; valid_from = effective_date or fecha_publicacion or bootstrap-run-date for §7.2 cases)
4. INSERT provisions rows from `index.provisions.parse(body)` — article-as-whole row + one row per alinea
5. INSERT laws_fts row with `bg_normalize(title)`, `bg_normalize(body)`

`--git-ref` enables Phase 2 to build historical indexes. Phase 3 (DV monitor) and Phase 4 (consolidation) invoke `index.build` as a final step in their own pipelines.

### 6.2 Provisions extractor (`index/provisions.py`)

Walks Markdown body, finds `**Чл. N.**` and `**Чл. Nа.**` (Cyrillic suffixes а, б, в, … supported), captures text until the next article or structural header (`## `, `### `, `#### `, `## ПРЕХОДНИ…`).

Emits two row types per article:
- **Article-as-whole**: `(law_id, article=N, paragraph=NULL, text=full_article_text, text_hash=...)`
- **Alinea**: `(law_id, article=N, paragraph=K, text=alinea_text, text_hash=...)` — one per `(K)` block

Goldens for each of the 6 captured HTML fixtures, frozen as JSON under `tests/fixtures/golden/provisions/`.

### 6.3 FTS5 + Bulgarian-aware normalization (`index/fts.py`)

Schema:

```sql
CREATE VIRTUAL TABLE laws_fts USING fts5(
    law_id UNINDEXED,
    title,
    body,
    category UNINDEXED,
    tokenize='unicode61 remove_diacritics 2'
);
```

`bg_normalize(text: str) -> str`: lowercase, strip whitespace, token-wise stripping of Bulgarian definite-article suffixes (`-та`, `-то`, `-те`, `-ят`, `-ът`, `-ите`, `-ето`) for words >4 chars. Same function called at insert time AND query time — symmetric — so `обществена поръчка` (query) matches `обществените поръчки` (indexed) without any custom SQLite tokenizer or extension loading.

Phase 1b.3 evaluates a Snowball-style Bulgarian stemmer + legal-term synonym dictionary based on real query patterns observed via 1b.3 logging.

### 6.4 Query layer (`mcp_server/queries.py`)

Pure functions. SQLite `Connection` is the only injected dependency. Each function is unit-testable against an in-memory database built from fixtures.

```python
def resolve_name_to_law_id(conn, name: str) -> str: ...
def version_at_date(conn, law_id: str, date: str | None) -> str: ...  # commit_hash
def parse_article_spec(spec: str) -> ArticleSpec: ...
def full_text_search(conn, query: str, category: str | None, limit: int = 20) -> list[SearchHit]: ...
def article_lookup(conn, law_id: str, spec: ArticleSpec, commit_hash: str) -> list[ProvisionHit]: ...
```

Resolution order in `resolve_name_to_law_id`: identificador (numeric) → exact slug → title FTS exact-phrase → fuzzy title (top-K). Multiple matches at any level → raise `AmbiguousName` with all candidates including identificador.

### 6.5 FastMCP server (`mcp_server/server.py`)

Each tool is a thin wrapper. Docstrings serve as MCP `tools/list` descriptions — Claude Code, Claude Desktop, and Codex all read these to decide which tool to call.

```python
@mcp.tool()
def get_law(name: str, date: str | None = None) -> GetLawResponse:
    """Return the full text and metadata of a Bulgarian normative act.

    Args:
        name: The act's title (e.g. "Закон за обществените поръчки"),
            slug (e.g. "zakon-za-obshtestvenite-porachki"), or numeric
            lex.bg identificador (e.g. "2136735703"). Identificador is
            the most stable handle — slugs may carry collision suffixes
            (-2, -3) and titles may be non-unique. See §7.1 of
            canonical-data-model.md.
        date: ISO 8601 date for historical retrieval. If omitted,
            returns the current consolidated version.

    Returns:
        GetLawResponse with metadata fields (titulo, identificador,
        fecha_publicacion, ultima_actualizacion, dv_issue, dv_year,
        effective_date, eli, amendment_history, commit_hash) and
        body_markdown. May include a `warnings` list with
        DATE_UNCERTAIN for acts with unknown publication dates.
    """
    law_id = queries.resolve_name_to_law_id(conn, name)
    commit = queries.version_at_date(conn, law_id, date)
    return _read_law_as_response(law_id, commit)
```

Configuration (argparse, mirrors `bootstrap.py`):
- `--db PATH` (default `catalog.db`)
- `--corpus PATH` (default `.`)
- `--strict` (refuse start on stale index; default soft warn)

Operator install in MCP host config:

```json
{
  "mcpServers": {
    "legalize-bg": {
      "command": "python",
      "args": ["-m", "mcp_server",
               "--db", "/abs/path/to/catalog.db",
               "--corpus", "/abs/path/to/legalize-bg"]
    }
  }
}
```

## 7. Data flow

### 7.1 Build-time

```
[git HEAD] ──→ git rev-parse HEAD → current_commit
              ↓
for each .md in corpus:
    read → split frontmatter + body
    INSERT laws (current_commit)
    INSERT law_versions (valid_from = effective_date / fecha_publicacion / bootstrap-run-date)
    provisions.parse(body) → INSERT provisions (article rows + alinea rows)
    INSERT laws_fts (bg_normalize(title), bg_normalize(body))
COMMIT
```

Single transaction. ~3-5 minutes for full corpus.

### 7.2 Query-time

`get_law(name, date=None)`:

1. `resolve_name_to_law_id(name)` → `law_id` or `LawNotFound` / `AmbiguousName`
2. `version_at_date(law_id, date)` → `commit_hash` or `NoVersionAtDate`
3. Read .md from working tree if `commit_hash == HEAD`; else `git show <commit_hash>:<corpus_dir>/<law_id>.md`
4. Parse frontmatter + body, build `GetLawResponse`, attach `warnings` if §7.2 case
5. Return

`search(query, category=None, limit=20)`:

1. `bg_normalize(query)`
2. SQL: `SELECT law_id, title, identificador, snippet(...) FROM laws_fts JOIN laws USING(law_id) WHERE laws_fts MATCH ? ORDER BY bm25(laws_fts) LIMIT ?` (with optional category filter)
3. For each result, if `title` is empty (§7.3), substitute `f"<no title; doc_id={identificador}>"`
4. Return `list[SearchHit]`

`get_article(law, article, date=None)`:

1. `resolve_name_to_law_id(law)` → `law_id`
2. `parse_article_spec(article)` → `(article_n, paragraph_n, range_end)`
3. `version_at_date(law_id, date)` → `commit_hash`
4. SQL on `provisions` filtering by `(law_id, article, paragraph, valid_from <= date, valid_to IS NULL OR valid_to > date)`
5. Return text directly from `provisions.text` for current versions; `git show` + re-parse path for historical

## 8. Error handling and §7 semantics

### 8.1 Error taxonomy (8 codes)

| Code | Trigger | Payload |
|---|---|---|
| `LAW_NOT_FOUND` | resolve exhausts identificador → slug → title | `{name, suggestions: [{law_id, title, score}]}` |
| `AMBIGUOUS_NAME` | multiple law_ids match (§7.1) | `{name, candidates: [{law_id, title, identificador, category}]}` |
| `NO_VERSION_AT_DATE` | date before any valid_from | `{law_id, date, earliest_available, latest_available}` |
| `DATE_UNCERTAIN` | (warning, not blocker) §7.2 act | `{law_id, source_date_marker: "unknown"}` — appears in `warnings` of successful response |
| `INVALID_ARTICLE_SPEC` | parser can't read spec | `{spec, examples: ["чл. 14", "14", "чл. 14а", "чл. 14, ал. 2", "14-16"]}` |
| `ARTICLE_NOT_FOUND` | spec parsed, no provisions row | `{law_id, article, paragraph, available_articles}` |
| `INDEX_STALE` | (only `--strict`) git HEAD ≠ laws.current_commit | `{head, indexed, command: "python -m index.build"}` |
| `INDEX_MISSING` | catalog.db unreadable | `{db_path, command: "python -m index.build --db <path>"}` |

All errors are `ToolError(code, payload)` exceptions raised inside tool handlers; FastMCP serializes them into the MCP response envelope with structured content the model can act on.

### 8.2 §7 data-quality semantics encoded

- **§7.1 — Slug collisions:** `resolve_name_to_law_id` always tries identificador first; multiple matches → `AMBIGUOUS_NAME` with full candidate list including identificador as the disambiguating handle.
- **§7.2 — Null `fecha_publicacion`:** `law_versions.valid_from` set to bootstrap-run-date for these acts (preserves the existing fallback). `version_at_date` succeeds for any date ≥ that fallback; response includes `warnings: [{code: "DATE_UNCERTAIN", ...}]`. Date queries before fallback raise `NO_VERSION_AT_DATE` with `earliest_available` set.
- **§7.3 — Empty `titulo`:** index build populates `laws_fts.title` with `f"<doc_id={identificador}>"`; search results substitute the same display string in the `title` field; `get_law` response carries the truthful empty `titulo` field but never returns blank where a UI would render.

### 8.3 Logging vs returning

- **Returned to caller (model-actionable):** all 8 codes
- **Logged INFO (operator-actionable, not in response):** every tool call with timing, query shape, result count
- **Logged WARN:** `INDEX_STALE`, `DATE_UNCERTAIN` events, FTS queries returning zero rows (signal for the 1b.3 stemmer/synonym investment)

## 9. Testing strategy

Four layers, fast feedback, fixture-first.

| Layer | Scope | Speed |
|---|---|---|
| **L1 unit** | Pure functions (`bg_normalize`, `parse_article_spec`, `resolve_name_to_law_id` w/ in-memory SQLite, `version_at_date`) | <1 s |
| **L2 component** | `index.build` end-to-end against fixture-built catalog (10 acts); `provisions.parse` golden tests; FTS5 regression suite | <10 s |
| **L3 integration** | FastMCP test client → server → SQLite (+ tmp git repo for `git show`); every tool, every error code | <30 s |
| **L4 acceptance** | Real Claude Code / Desktop / Codex session smoke test (Phase 1b.3 milestone) | manual |

§7 data-quality cases are named explicit tests, anchored to real corpus rows:
- §7.1: pick a `-2` suffix slug from the corpus, expect `AMBIGUOUS_NAME`
- §7.2: pick one of the 121 null-pub_date acts, expect `DATE_UNCERTAIN` warning + successful return
- §7.3: doc_id `-549676032`, expect `<doc_id=-549676032>` display in search, successful `get_law` via identificador

Performance regression budgets are **soft assertions in 1b.1, hardened in 1b.2**:

| Operation | p95 budget |
|---|---|
| `search(query)` over full catalog | <100 ms |
| `get_law(name)` current | <100 ms |
| `get_law(name, date)` historical | <500 ms (subprocess overhead) |
| `get_article(law, article)` | <50 ms |
| `python -m index.build` full corpus | <5 min |

## 10. Out of scope for Phase 1b.1

- `history`, `diff`, `amendments_in_period` tools — Phase 2 (FR-001 temporal index)
- Backfilling historical versions of existing acts — Phase 4 (consolidation engine) + FR-009
- DV monitor / incremental updates from dv.parliament.bg — Phase 3 (FR-002)
- Bulgarian Snowball stemmer + legal-term synonym dictionary — Phase 1b.3 (deferred per Q3(C); decided after observability data exists)
- SSE / HTTP transports — Phase 1b.3 only if needed for non-MCP-aware callers
- CI runner configuration — Phase 1b.3 packaging milestone
- Property-based / mutation tests — overkill for greenfield; revisit later
- Municipal acts (Phase 6+)

## 11. Decisions log cross-reference

This design records eight new decisions. Full entries in `docs/sync/DECISIONS.md`:

- **D-020** — Phase 1b ships through MCP server, not direct file access. Pros/cons table in this design §1.
- **D-021** — FastMCP for the SDK. Tool descriptions are docstrings; tool selection by Claude Code / Desktop / Codex depends on this.
- **D-022** — Bulgarian search via FTS5 + symmetric `bg_normalize` pre-normalization (1b.1). Stemmer + synonyms deferred to 1b.3 pending real-usage data.
- **D-023** — `provisions` populated to alinea level from day one. `text` column stored, not just hash. Schema enables Phases 2 and 4 without migration.
- **D-024** — `get_law` response is a structured typed-dict (metadata + body), not a Markdown string.
- **D-025** — `index/migrations.py` exists from Phase 1b.1, not deferred. Forward-only versioning.
- **D-026** — Error taxonomy returns structured `{code, payload}` to model; not opaque MCP failures.
- **D-027** — Phase 1b is a three-mandatory-milestone plan (1b.1 / 1b.2 / 1b.3); Bulgarian stemmer + packaging are roadmapped, not optional.

## 12. Implementation plan handoff

This design is the **what and why**. The **how — task by task, file by file, TDD step by step** — comes from the `superpowers:writing-plans` skill, which produces a sibling document under `docs/plans/2026-05-09-phase1b-mcp-implementation.md`. That document is the executable artifact.
