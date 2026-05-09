# Phase 1b.1 — Operator Setup

**Status:** Phase 1b.1 ships 2026-05-09. Stable for daily use; Phase
1b.2 will harden JSON schemas and promote perf budgets to hard
assertions.

This runbook is for operators wiring the legalize-bg MCP server into
Claude Code, Claude Desktop, or OpenAI Codex. It covers index build,
host config, and the smoke test.

## Prerequisites

- Python 3.12+
- Cloned `legalize-bg` repo with `main` checked out
- Virtualenv at `.venv` with `pip install -e ".[dev]"` (installs
  `fastmcp>=2.0,<4.0` along with the rest)
- ~50 MB free disk for the catalog

## One-time index build

From the repo root:

```bash
python -m index.build --corpus . --db catalog.db
```

Or equivalently:

```bash
python scripts/build_index.py --corpus . --db catalog.db
```

This walks the corpus (3,573 acts on `main` as of 2026-05-09), parses
each `.md` frontmatter + body, and populates the SQLite catalog:

| Table | Rows | Purpose |
|---|---|---|
| `laws` | 3,573 | Act metadata + current_commit |
| `law_versions` | 3,573 | Temporal index (one entry per act in 1b.1; Phase 2 backfills history) |
| `provisions` | ~448,000 | Article + alinea text rows (D-023) |
| `laws_fts` | 3,573 | FTS5 virtual table for `bg_normalize`-ed title + body |

Build takes **~45 seconds** (measured: M-class Apple silicon, NVMe
SSD; ARM laptops with slower SSDs typically run ~60s, network
filesystems can be 2–5×). Output `catalog.db` is ~50–100 MB. The
catalog is **gitignored** — derived state, rebuildable from git+YAML.

If you see `INDEX_MISSING` from `python -m mcp_server`: the catalog
file isn't where the server expects. The error message includes the
exact path; run `index.build` to that path.

## MCP host configuration

### Claude Code

Edit `~/.claude/claude_code_config.json` (or your project's
`.claude/config.json`):

```json
{
  "mcpServers": {
    "legalize-bg": {
      "command": "/abs/path/to/legalize-bg/.venv/bin/python",
      "args": [
        "-m", "mcp_server",
        "--db", "/abs/path/to/legalize-bg/catalog.db",
        "--corpus", "/abs/path/to/legalize-bg"
      ]
    }
  }
}
```

### Claude Desktop / OpenAI Codex

Same JSON shape. The exact config-file location varies by host; the
`command` and `args` are identical. Use absolute paths — relative
paths are interpreted from the host's launch directory, not your
shell.

## Smoke test

In a new Claude Code session:

> Search the Bulgarian legislation corpus for "обществени поръчки"
> using the legalize-bg MCP.

Expected: top-5 includes ЗОП (Закон за обществените поръчки) along
with related implementing regulations.

> Show me чл. 1 of ЗОП using identificador 2136735703.

Expected: returns the article text with `(1) Този закон определя…`.

> What's the publication date of doc_id -549676032?

Expected: succeeds with `titulo: ""` (truthful empty for the §7.3
phantom act) **and** a `DATE_UNCERTAIN` warning in the response
(`source_date_marker: "unknown"`); `fecha_publicacion` is null. This
specific doc_id is in the intersection of the §7.3 empty-titulo set
**and** the 121 §7.2 null-pub-date set, so the warning is deterministic
— if you don't see `DATE_UNCERTAIN`, the index is stale or the §7.2
surfacing path is broken.

> **Aside — `titulo: ""` vs `<doc_id=...>`.** The frontmatter `titulo`
> for §7.3 phantom acts is genuinely empty (`titulo: ''` in the `.md`
> file), so `get_law` returns the truthful empty. The SQLite
> `laws.title` column for the same act, however, carries a substituted
> `<doc_id=N>` form — that substitution lives in `index/build.py` and
> only affects `search` results' display. So an operator running raw
> SQL like `SELECT title FROM laws WHERE doc_id = -549676032` will see
> `<doc_id=-549676032>`, not the empty string. Both views are
> consistent with their respective contracts; the substitution exists
> only so search results are recognizable in the LLM-facing output.

## Re-indexing after corpus changes

Whenever `git pull` or local commits land new acts or amendments:

```bash
python -m index.build --corpus . --db catalog.db
```

The MCP server soft-warns at startup when `git HEAD ≠
laws.current_commit`. Pass `--strict` to make staleness a hard
refusal (exit code 3).

## Server runtime

**SQLite connection threading.** `mcp_server/__main__.py` opens the
catalog connection with `check_same_thread=False`. FastMCP serves tool
calls on a worker thread; SQLite would otherwise raise "SQLite objects
created in a thread can only be used in that same thread." All writes
happen at index-build time on a separate connection, so the runtime
connection is read-mostly — no concurrent-write hazard. The test
fixtures use the same setting via the `populated_conn` conftest fixture,
so component-level tests behave identically to the production server.

## Idempotency contract

All three tools (`get_law`, `search`, `get_article`) are **read-only with respect to durable state**. A request never:

- Writes to the corpus (working-tree `.md` files).
- Writes to the SQLite catalog (`catalog.db`).
- Mutates remote services (no network I/O at request time).

A request DOES write to:

- The Python logger (INFO/WARN per the rules in §"Server runtime").
- The OS file cache (incidental — opening `.md` files for the working-tree fast path warms the page cache; this is invisible to callers).

**Idempotency consequences:**
- A retry of any tool call against the same `(name, date, article)` returns the same response (modulo OS-cache state, which only affects latency, not the response body).
- Concurrent calls do not race because the safety story is built on three independent layers: (a) the stdio transport processes one JSON-RPC request per server connection at a time; (b) SQLite is opened with `check_same_thread=False` and handles concurrent readers via its own internal locking (the runtime catalog is read-only); (c) the tool implementations don't share mutable Python state across calls (no module-level dicts mutated at request time, no per-tool caches). This holds regardless of FastMCP internals — even a future transport that runs requests in parallel would still inherit (b) and (c).
- A caller may safely retry on transport-level failures without risk of duplicated side-effects.

**Non-idempotency to be aware of:**
- The build path (`python -m index.build`) IS NOT idempotent in the sense that re-running it issues `DELETE FROM laws_fts` etc. (full rebuild). FR-014 tracks the incremental rebuild path; until then, do not re-run the build under load.
- Working-tree edits between requests will surface in subsequent `get_law` responses via the fast path (commit_hash matches HEAD). The runbook's `INDEX_STALE` advice covers this.

## Tools surfaced

| Tool | Inputs | Returns |
|---|---|---|
| `get_law(name, date=None)` | title / slug / identificador, optional ISO date | full text + metadata + warnings. Date fields (`fecha_publicacion`, `ultima_actualizacion`, `effective_date`) are ISO 8601 strings — PyYAML's `datetime.date` is coerced via `mcp_server.server._iso` before serialization, so JSON-RPC consumers never see Python objects. |
| `search(query, category=None, limit=20, include_body=False)` | Bulgarian/Cyrillic text + optional category filter | Ranked list of hits. Each hit carries `title_snippet` (always populated, cheap) and `body_snippet` (empty unless `include_body=True`, then non-empty for top-2 only). Result list is rang-tier-sorted (laws/codes outrank implementing/regulations/ordinances per FR-015). Single-token Bulgarian abbreviation queries (`ЗОП`, `НК`, `ГПК` — see `index/synonyms.py`) are auto-expanded to canonical long forms before FTS5 runs. |
| `get_article(law, article, date=None)` | act + article spec (`чл. 14`, `14.2`, `чл. 14а`) | article or alinea text |

Tool descriptions visible to the LLM are the full Python docstrings
(D-021). The model decides which tool to call based on those — keep
them in sync with behavior.

## Error codes (D-026)

> **Authoritative catalog:** `docs/api/error-codes.md` (Markdown for humans) and `docs/api/error-codes.json` (machine-readable). Both are version-tagged 1.0.0 and tested for parity with `mcp_server.errors.ERROR_CODES`. Phase 1b.2 added `QUERY_TOO_BROAD` (FR-016 — single-word category-query reject).

When a tool call fails, the structured payload includes one of these
codes plus model-actionable context:

| Code | Returned when | Payload includes |
|---|---|---|
| `LAW_NOT_FOUND` | resolver exhausted identificador → slug → title | `name`, `suggestions[]` |
| `AMBIGUOUS_NAME` | multiple acts share the title (§7.1) | `candidates[]` with distinct identificadors |
| `NO_VERSION_AT_DATE` | requested date is before earliest valid_from | `earliest_available`, `latest_available` |
| `DATE_UNCERTAIN` | (warning, not blocker) §7.2 act with no parseable pub date | `source_date_marker: "unknown"` |
| `INVALID_ARTICLE_SPEC` | parser couldn't read the article spec | `examples[]` |
| `ARTICLE_NOT_FOUND` | spec parsed, no provisions row matches | `available_articles[]` (legal-number sort) |
| `INDEX_STALE` | (operator log only — soft warn unless `--strict`) | `head`, `indexed`, rebuild command |
| `INDEX_MISSING` | (operator log only — exits before serving) | `db_path`, build command |

## Known limitations (tracked as FRs)

- **Search ranking quality** — BM25 + title-tier ranking puts canonical
  laws in top-5 but not always #1. Synonym dictionary (ЗОП ↔ Закон за
  обществените поръчки) and rang-aware re-ranking land in Phase 1b.3.
  See `docs/frs/INDEX.md` FR-015.
- **Single-word category queries** — "наредба" alone matches all
  ~2,600 ordinances and overruns the 100ms perf budget. 1b.2 adds a
  stop-word-list / "be more specific" hint. See FR-016.
- **Body snippets** — current `search` returns highlighted-title
  snippets. Body-context snippets land in Phase 1b.3. See FR-017.

## Phase 2+ deferred

`history`, `diff`, `amendments_in_period`, full historical version
retrieval — all require the temporal index (FR-001) which Phase 1b.1
prepared the schema for but does not populate. See `docs/frs/INDEX.md`.

## Troubleshooting

### Process exit codes

`python -m mcp_server` exits non-zero on preflight failures so wrappers
(launchd, systemd, supervisord) can react before any tool call lands:

| Code | Meaning | Recovery |
|---|---|---|
| 0 | Server exited cleanly (host disconnected) | normal |
| 2 | `INDEX_MISSING` — catalog.db not at the configured path | run `python -m index.build --db <path>` to create it |
| 3 | `INDEX_STALE` under `--strict` — git HEAD ≠ indexed commit | re-run `python -m index.build`, OR drop `--strict` to allow soft-warn startup |

### Common errors

**`ModuleNotFoundError: fastmcp`** → reinstall deps: `pip install -e
".[dev]"` from the repo root.

**`INDEX_MISSING` (exit 2)** → run `python -m index.build` to create
`catalog.db`.

**`INDEX_STALE` warning** (default) or refusal (`--strict`, exit 3) →
re-run `python -m index.build` to refresh. Pass `--strict` if you want
the server to refuse to start on stale catalogs.

**FastMCP transport timeouts** → confirm the MCP host's `command`
points at the venv's `python`, not the system one. The system Python
won't have `fastmcp` installed.

**Search returns nothing for an obvious query** → check the actual
indexed form via `bg_normalize`:
```python
from index.fts import bg_normalize
print(bg_normalize("your query"))
```
The two-tier ranker requires at least one query token to match a
title or body token after normalization.
