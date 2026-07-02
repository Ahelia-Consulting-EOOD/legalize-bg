# Phase 1b.1 — Operator Setup

**Status:** written 2026-05-09 for the Phase 1b.1 ship (3-tool server);
kept truthful 2026-07-02 against the review that found the server had
grown well past what this doc described (2.x-a/b/c batches, Phase 2
temporal index, a 2026-07-02 hardening pass). The filename/date is kept
for doc-history continuity — treat the **content** as current. The
"Tools surfaced" table below is locked to the live tool set by
`tests/mcp_server/test_runbook_parity.py`; if this doc and the server
ever drift again, that test turns red.

This runbook is for operators wiring the legalize-bg MCP server into
Claude Code, Claude Desktop, or OpenAI Codex. It covers index build,
host config (native or Docker), and the smoke test.

## Prerequisites

- Python 3.12+
- Cloned `legalize-bg` repo with `main` checked out
- Virtualenv at `.venv` with `pip install -e ".[dev]"` (installs
  `fastmcp>=2.0,<4.0` along with the rest)
- ~2.5 GB free disk (catalog.db is ~1.1 GB — see sizing note below; the
  zero-downtime rebuild approach further down needs roughly double
  that temporarily, old + new side by side)
- Alternatively, Docker — see "Docker quick-start" below; no local
  Python/venv needed for the container path.

## One-time index build

From the repo root:

```bash
python -m index.build --corpus . --db catalog.db
```

Or equivalently:

```bash
python scripts/build_index.py --corpus . --db catalog.db
```

This walks the corpus (3,601 acts as of 2026-07-02), parses each `.md`
frontmatter + body, and populates the SQLite catalog:

| Table | Rows | Purpose |
|---|---|---|
| laws | 3,601 | Act metadata + current_commit |
| law_versions | 3,833 | Temporal index — one row per historical version (FR-020, `git log`-derived); 225 acts carry 2+ versions, the rest exactly one |
| provisions | 451,587 | Article + alinea text rows (D-023) |
| laws_fts | 3,601 | FTS5 virtual table for `bg_normalize`-ed title + body |

Full-rebuild time is now **~2–2.5 minutes** on the live corpus (Apple
M4 measured, `docs/research/2026-07-02-fr027-search-perf.md`) — up from
the original ~45 s baseline. The jump is the D-047 re-bootstrap, which
restored Допълнителни разпоредби text across 1,826 acts and grew the
FTS body corpus to ~223 M characters; `catalog.db` is correspondingly
~1.1 GB now, not ~50–100 MB. The catalog is **gitignored** — derived
state, rebuildable from git+YAML. For routine re-indexing after a small
number of changed acts, prefer `--incremental` (see "Re-indexing after
corpus changes" below) — it's the faster path when a full rebuild isn't
needed.

If you see `INDEX_MISSING` from `python -m mcp_server`: the catalog
file isn't where the server expects. The error message includes the
exact path; run `index.build` to that path.

**Category-drift guard.** `index.build` refuses to run (raises
`ValueError`, no partial write) if a top-level corpus directory outside
`fetcher/bg/discovery.py:CATEGORY_DIRS` holds `.md` files with YAML
frontmatter carrying an `identificador` key — i.e., a new act category
was added on disk but never wired into the indexer (`index/build.py:
_check_category_drift`, review 2026-07-02). If you add a new top-level
corpus directory, either relocate its acts into an existing category
dir or register the new category in `CATEGORY_DIRS` — that file is a
protected surface (IMPLEMENTATION-PREFLIGHT required).

## Docker quick-start

Packaging batch 2.x-c added a `Dockerfile` that carries only the
application; the corpus (Markdown + `.git`) and the derived
`catalog.db` are mounted at runtime, not baked into the image. Three
commands (from the `Dockerfile` header):

```bash
# Build the image:
docker build -t legalize-bg-mcp .

# Build the index once (host or a one-off container):
docker run --rm -v "$PWD:/corpus" --entrypoint python legalize-bg-mcp \
    -m index.build --corpus /corpus --db /corpus/catalog.db

# Run the stdio MCP server (the MCP host attaches over stdin/stdout; -i):
docker run --rm -i -v "$PWD:/corpus" legalize-bg-mcp \
    --db /corpus/catalog.db --corpus /corpus
```

The image installs `git` (historical `get_law`/`diff` shell out to it,
and `index.build` reads git HEAD) but no C build toolchain — `lxml`,
`pyyaml`, and `fastmcp` all install from wheels. To point an MCP host at
the container instead of a venv, set the host config's `command` to
`docker` and `args` to the third command's flags above (host configs
are covered next).

## Deploy guards

Two environment variables gate server startup, checked before any DB
access (so a refusal here wins over `INDEX_MISSING`/`INDEX_STALE`):

- `LEGALIZE_CORPUS_DEFECTIVE=1` — refuses to start (exit code 2) when
  the corpus is flagged as known-incomplete (D-047: a parser data-loss
  incident that dropped definitions and transitional/final provisions
  from affected acts). Off by default — this is a dormant safety net,
  not a normal operating mode.
- `LEGALIZE_ALLOW_DEFECTIVE=1` — explicit override to start anyway
  (debugging only); has no effect unless `LEGALIZE_CORPUS_DEFECTIVE=1`
  is also set.

See `mcp_server/__main__.py:_check_corpus_defective`.

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

`pip install -e .` also installs a `legalize-bg-mcp` console script
(`mcp_server.__main__:main`) — `command` can point directly at
`/abs/path/to/legalize-bg/.venv/bin/legalize-bg-mcp` with `args` being
just `["--db", ..., "--corpus", ...]`, if you'd rather not spell out
`-m mcp_server`.

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

> Show me the amendment history of ДОПК (identificador 2135514513).

Expected: `history` returns a multi-entry timeline; this act is one of
the 225 with real git-derived version history (FR-020), so `diff`
between two of its dates returns an actual unified diff rather than
the "single consolidated version held" note (see "Tools surfaced"
below).

## Re-indexing after corpus changes

Whenever `git pull` or local commits land new acts or amendments, the
default full rebuild is:

```bash
python -m index.build --corpus . --db catalog.db
```

For routine re-indexing where only a handful of acts changed, use the
incremental path instead (FR-014, done — D-041):

```bash
python -m index.build --corpus . --db catalog.db --incremental
```

This diffs the catalog's indexed commit against git HEAD (`git diff
--name-status`), re-indexes only added/modified acts, drops removed
acts, and bumps unchanged acts' commit pointers — atomic (single
commit), and falls back automatically to a full rebuild if the catalog
is empty/inconsistent or its base commit isn't in git history any
more.

The MCP server soft-warns at startup when `git HEAD ≠
laws.current_commit`. Pass `--strict` to make staleness a hard
refusal (exit code 3).

**Zero-downtime rebuild.** A crashed in-place rebuild (full or
incremental) no longer empties the catalog — it's one SQLite
transaction, so a crash mid-rebuild rolls back cleanly and the server
keeps serving the pre-rebuild data (Task 1, P0-3). But a
*successful* in-place rebuild still races a live server: the rebuild's
commit can land between two calls in the same operator/LLM session,
so a `search` and a subsequent `get_law` could observe the catalog
before and after the rebuild respectively — usually harmless, but not
guaranteed-consistent within one logical interaction. For a genuinely
zero-downtime rebuild, build to a separate path and swap it in:

```bash
python -m index.build --corpus . --db catalog.db.new
mv catalog.db.new catalog.db
# then restart the MCP server process so it opens the new file
```

`mv` on the same filesystem is atomic, so any reader that opens
`catalog.db` sees either the fully-old or fully-new file, never a
partial one — but the *running* server process still holds its
original file descriptor open against the old (now unlinked, if on
POSIX) inode until it's restarted, so the restart step is required to
actually pick up the new data.

## Server runtime

**SQLite connection threading.** `mcp_server/__main__.py` opens the
catalog connection with `check_same_thread=False`. FastMCP serves tool
calls on a worker thread; SQLite would otherwise raise "SQLite objects
created in a thread can only be used in that same thread." All writes
happen at index-build time on a separate connection, so the runtime
connection is read-mostly — no concurrent-write hazard. The test
fixtures use the same setting via the `populated_conn` conftest fixture,
so component-level tests behave identically to the production server.

Every tool call additionally acquires a process-wide `threading.Lock`
(`build_app`'s `_db_lock`, FR-023/D-040) before touching the
connection. SQLite's own locking already serializes writers, but this
closes a residual `InterfaceError` race that showed up under concurrent
cross-thread reads on the one shared connection. The lock is
uncontended in the common case (stdio serves one request at a time), so
it costs nothing per call; the lock wraps entire tool bodies (including
git subprocess calls and 1 MB body reads), so one slow historical
`get_law`/`diff` call blocks every other tool call server-wide.
Retiring it for true per-thread/per-call connections is tracked as
FR-029 (backlog, "on demand" — pick up only when a concurrent MCP
fronting materializes, e.g. multi-session host or MCP-over-HTTP). The
separate REST API planned for the web UI (FR-028) does NOT inherit this
lock — it uses its own per-request connections.

**Read-performance pragmas (FR-027, Task 13).** Right after opening,
the runtime connection sets `PRAGMA mmap_size = 1073741824` (1 GB
memory-map) and `PRAGMA cache_size = -65536` (64 MB page cache).
Measured effect: same-connection repeat calls to queries that
previously stayed multi-second even after 5 warm-up calls (e.g. "лични
данни", "административни нарушения" — see
`docs/research/2026-07-02-fr027-search-perf.md`) drop to ~20 ms with
the pragmas set, a ~300–400x reduction. This does **not** fix the
first (cold) call on a fresh connection — see "Known limitations"
below.

**Metrics via SIGUSR1 (Task 16).** The stdio transport has no side
channel for runtime introspection, so send `SIGUSR1` to the running
server process (`kill -USR1 <pid>`) to have it log one JSON line:
`metrics_snapshot: {...}` with, per tool, `calls`, `errors`,
`error_codes` (counts by code), `total_ms`, `last_ms`, `avg_ms`.
Recording and the SIGUSR1 dump both go through their own
`threading.Lock` (`_AppHandle._metrics_lock`), separate from the DB
lock above, so pulling metrics never contends with in-flight tool
calls. Not available on Windows (no POSIX signals) — handler
installation is best-effort and silently no-ops there.

## Idempotency contract

All seven tools (`get_law`, `search`, `get_article`, `get_articles`,
`history`, `amendments_in_period`, `diff`) are **read-only with respect
to durable state**. A request never:

- Writes to the corpus (working-tree `.md` files).
- Writes to the SQLite catalog (`catalog.db`).
- Mutates remote services (no network I/O at request time).

A request DOES write to:

- The Python logger (INFO/WARN per the rules in §"Server runtime").
- The OS file cache (incidental — opening `.md` files for the working-tree fast path warms the page cache; this is invisible to callers).

**Idempotency consequences:**
- A retry of any tool call against the same `(name, date, article)` returns the same response (modulo OS-cache state, which only affects latency, not the response body).
- Concurrent calls do not race because the safety story is built on layers: (a) the stdio transport processes one JSON-RPC request per server connection at a time; (b) every tool call holds the process-wide `_db_lock` for the duration of its DB access (see "Server runtime"); (c) the tool implementations don't share mutable Python state across calls outside the lock-protected metrics dict. This holds regardless of FastMCP internals — even a future transport that runs requests in parallel would still inherit (b) and (c).
- A caller may safely retry on transport-level failures without risk of duplicated side-effects.

**Non-idempotency to be aware of:**
- The default full-rebuild path (`python -m index.build`) is NOT idempotent in the sense that it re-issues `DELETE FROM laws_fts` etc. and re-inserts every row inside one transaction (crash-safe per Task 1; still races live readers when it *succeeds* — see "Zero-downtime rebuild" above). `--incremental` (FR-014, done) re-indexes only changed acts instead, but the same in-place-vs-live-reader caveat applies to it too.
- Working-tree edits between requests will surface in subsequent `get_law` responses via the fast path (commit_hash matches HEAD). The runbook's `INDEX_STALE` advice covers this.

## Tools surfaced

| Tool | Inputs | Returns |
|---|---|---|
| `get_law` | name, date=None | title / slug / identificador lookup → full text + metadata + warnings. Date fields (`fecha_publicacion`, `ultima_actualizacion`, `effective_date`) are ISO 8601 strings — PyYAML's `datetime.date` is coerced via `mcp_server.server._iso` before serialization, so JSON-RPC consumers never see Python objects. With `date` set, resolves the historical version in force at that date (FR-020). |
| `search` | query, category=None, limit=20, include_body=False | Ranked list of hits. Each hit carries `title_snippet` (always populated, cheap) and `body_snippet` (empty unless `include_body=True`, then non-empty for top-2 only). Result list is rang-tier-sorted (laws/codes outrank implementing/regulations/ordinances per FR-015). Single-token Bulgarian abbreviation queries (`ЗОП`, `НК`, `ГПК` — see `index/synonyms.py`) are auto-expanded to canonical long forms before FTS5 runs. |
| `get_article` | law, article, date=None | Act + article spec (`чл. 14`, `14.2`, `чл. 14а`) → article or alinea text. Rejects a range spec (`чл. 14-16`) with `INVALID_ARTICLE_SPEC` and a hint pointing at `get_articles`. |
| `get_articles` | law, articles, date=None | Superset of `get_article` — accepts a single article or a RANGE (`чл. 14-16`), expanding to every article number in `[start, end]` including Cyrillic-suffixed ones present in the act (FR-018). |
| `history` | law | Amendment timeline, oldest→newest: `{date, dv_issue, operation, commit_hash}` per entry. `operation` is `"enacted"` for the original promulgation, `"amendment"` for each DV amendment event. |
| `amendments_in_period` | from_date, to_date | Every dated amendment across the whole corpus in `[from_date, to_date]` inclusive, oldest first: `{law_id, title, date, dv_issue}`. Answers "what changed in Bulgarian law between X and Y?". |
| `diff` | law, date1, date2 | Unified `git diff` of the act's text between the versions in force at `date1` and `date2` (FR-020). For the majority of acts, which still hold exactly one recorded version, returns a bilingual "single consolidated version held" note instead of an empty diff; for the 225 acts with 2+ `law_versions` rows, returns a real diff. |

Tool descriptions visible to the LLM are the full Python docstrings
(D-021). The model decides which tool to call based on those — keep
them in sync with behavior.

## Error codes (D-026)

> **Authoritative catalog:** `docs/api/error-codes.md` (Markdown for humans) and `docs/api/error-codes.json` (machine-readable). Both are version-tagged **1.3.0** and tested for parity with `mcp_server.errors.ERROR_CODES`.

When a tool call fails, the structured payload includes one of these
codes plus model-actionable context. (Backticks omitted below on
purpose — this table isn't parity-tested against the live tool set the
way "Tools surfaced" above is; see `docs/api/error-codes.md` for the
full per-code payload contracts.)

| Code | Returned when | Payload includes |
|---|---|---|
| LAW_NOT_FOUND | resolver exhausted identificador → slug → title | name, suggestions[] |
| AMBIGUOUS_NAME | multiple acts share the title (§7.1) | name, candidates[] with distinct identificadors |
| NO_VERSION_AT_DATE | requested date is before earliest valid_from, or the act has no versions | law_id, date, earliest_available, latest_available |
| DATE_UNCERTAIN | (warning, not blocker) §7.2 act with no parseable pub date | source_date_marker: "unknown" |
| INVALID_ARTICLE_SPEC | parser couldn't read the article spec, or `get_article` was given a range | spec, examples[], hint (range case only) |
| ARTICLE_NOT_FOUND | spec parsed, no provisions row matches (or none in a range) | law_id, article, paragraph, available_articles[] (legal-number sort) |
| INDEX_STALE | (read-path failure) catalog and corpus have diverged | law_id, commit_hash (historical path only), detail, hint |
| INDEX_MISSING | catalog.db missing tables/columns or unreadable at query time | detail, hint |
| QUERY_TOO_BROAD | `search` query reduces to one of the 5 Bulgarian category stop-words (наредба/закон/правилник/кодекс/постановление) | query, category_words[], hint |
| INVALID_DATE_RANGE | `diff`/`amendments_in_period` called with the start date later than the end date | from_date/date1, to_date/date2 |
| DIFF_FAILED | `diff`'s underlying `git diff` invocation failed | law_id, detail |
| INVALID_DATE | a date parameter isn't a valid `YYYY-MM-DD` string (empty/whitespace included) | param, value, expected: "YYYY-MM-DD" |

`INDEX_STALE`/`INDEX_MISSING` above are the read-path (`ToolError`)
forms. There's a separate startup-preflight mechanism with the same
names but different mechanics — see "Troubleshooting" below.

## REST API (FR-028)

The `api/` package exposes a peer HTTP surface over the SAME shared
query layer the MCP server uses (`mcp_server/queries.py`, `index/fts.py`)
— built for the `legalize-bg-web` Next.js frontend (sister repo, Phase
7.2) but usable by any HTTP client. It does **not** share the MCP
server's process-wide `_db_lock` described in "Server runtime" above:
every request opens its own short-lived `mode=ro` SQLite connection
with the D-051 read pragmas (`api/deps.py`) and closes it when the
response is sent. FR-029 tracks retiring the MCP lock the same way, on
its own trigger — the two are independent.

### Start command

```bash
legalize-bg-api --db catalog.db --corpus . --port 8228 \
    --cors-origin https://<frontend-domain>
```

`pip install -e ".[api]"` installs `fastapi`/`uvicorn`; the console
script (`legalize-bg-api` → `api.__main__:main`) comes from the base
install's `[project.scripts]`. Equivalent: `python -m api --db catalog.db
--corpus . --port 8228`. `--host` defaults to `127.0.0.1`;
`--cors-origin` is repeatable — add `--cors-origin
http://localhost:3000` alongside the production origin for the Next.js
dev server. No auth / rate-limiting / reverse-proxy is wired up (design
§Deployment marks that as future work); this start command is
sufficient for Phase 7.2 frontend development.

**Operational note before exposing this publicly.** Some full-text
search queries are slow at the SQL layer — the REST API's per-request
connections don't benefit from the MCP server's warm, pragma'd,
long-lived connection, so a pathological body-only query can take
several seconds server-side (tracked as the open D-2026-07-02-01 row in
`docs/sync/DEFERRED.md`; not addressed by this runbook note). Before
routing real public traffic at this API, put it behind a reverse proxy
(e.g. Caddy or nginx) and configure request-rate limiting there — this
process does not implement any rate-limiting itself.

### Endpoints

| Endpoint | Purpose |
|---|---|
| GET /healthz | Liveness probe — `{"status": "ok"}`, no DB access |
| GET /api/v1/laws | Paginated law list; `category`, `estado`, `limit`, `offset` query params |
| GET /api/v1/laws/{slug} | Full law metadata + body markdown; optional `date=` resolves the historical version in force at that date (FR-020) |
| GET /api/v1/laws/{slug}/articles/{art} | Single article/alinea text; optional `date=`; rejects a range spec (`чл. 14-16`) with INVALID_ARTICLE_SPEC — ranges stay MCP-only (`get_articles`) |
| GET /api/v1/laws/{slug}/history | Amendment timeline, oldest to newest |
| GET /api/v1/laws/{slug}/diff | Unified diff between two dates; `from`/`to` query params (`YYYY-MM-DD`) |
| GET /api/v1/search | Full-text search; `q`, `category`, `limit` (capped at 50, mirrors the MCP `search` tool's cap), `include_body` query params |
| GET /api/v1/stats | Corpus-wide counts — `total_acts`, `by_category`, `by_status`, `multi_version_acts`, `latest_version_date` |
| GET /api/v1/metrics | Per-route call/error/latency snapshot (excluded from its own recording) |

That's 7 REST endpoints plus `/healthz` and `/api/v1/metrics` (9 routes
total). Response bodies reuse the MCP server's TypedDicts
(`mcp_server/schemas.py`) where the shape matches 1:1 (`get_law`,
`get_article`, `history`, `search`), plus REST-only TypedDicts in
`api/schemas.py` (`LawListResponseDict`/`LawSummaryDict`,
`StatsResponseDict`, `DiffResponseDict`) for endpoints with no MCP
analogue or a REST-shaped list wrapper. `GET /laws/{slug}`,
`/articles/{art}`, and `/history` set `Cache-Control: public,
max-age=300`; `/search` sets `max-age=60`.

### Error → HTTP mapping (D-052)

Errors reuse the SAME `ToolError` / query-layer exception taxonomy the
MCP server raises (D-026) — the JSON body is `ToolError.to_dict()`,
byte-compatible with what an MCP client parses out of `str(ToolError)`.
`api/errors.py` maps each code to an HTTP status:

| Code | HTTP status |
|---|---|
| INVALID_DATE | 400 |
| INVALID_ARTICLE_SPEC | 400 |
| INVALID_DATE_RANGE | 400 |
| QUERY_TOO_BROAD | 400 |
| LAW_NOT_FOUND | 404 |
| ARTICLE_NOT_FOUND | 404 |
| NO_VERSION_AT_DATE | 404 |
| AMBIGUOUS_NAME | 409 |
| DIFF_FAILED | 500 |
| INDEX_MISSING | 503 |
| INDEX_STALE | 503 |

Any code not in this table falls back to 500. A malformed HTTP request
line (e.g. a query string with a raw, un-percent-encoded non-ASCII byte
— some curl invocations do this for path segments but not query
strings) is rejected by uvicorn's `h11` parser before it ever reaches
FastAPI routing: a `400 Bad Request` / `text/plain` "Invalid HTTP
request received." response, not a D-052 JSON error body. Well-behaved
HTTP clients (browsers, `fetch`, `requests`, `axios`) percent-encode the
whole URL and never hit this path.

### OpenAPI contract

`docs/api/openapi-rest.json` is the locked contract, generated by
`python -m api.export_openapi --output docs/api/openapi-rest.json` from
a throwaway `create_app()` instance (no DB access required) and
verified via `python -m api.export_openapi --check
docs/api/openapi-rest.json` (CI-wired, `tests/api/test_export_openapi.py`).
Interactive docs are served at `/api/v1/docs` when the app is running
(Swagger UI over the same generated spec).

### Metrics

`GET /api/v1/metrics` returns a per-route snapshot keyed by route
template (not the concrete URL, so cardinality stays bounded —
`api/metrics.py`): `calls`, `errors`, `total_ms`, `avg_ms` per route.
Unlike the MCP server's SIGUSR1 dump, this is a normal HTTP endpoint —
its own middleware, its own lock, and it excludes itself from its own
recording.

## Known limitations (tracked as FRs)

- **Search cold-call latency (FR-027, open — Task 14 owner checkpoint
  pending, D-051).** After the D-047 re-bootstrap grew the FTS body
  corpus to ~223 M characters, some multi-token Bulgarian queries take
  1–7 seconds on the *first* call against a fresh connection —
  "лични данни" and "административни нарушения" are the worst measured
  cases, both dominated (>97%) by the tier-2 full-corpus body `MATCH` +
  `bm25()` path, not I/O. Task 13's read-only pragmas (see "Server
  runtime") fix the *warm* case (~300–400x) but do nothing for cold
  calls. This blows the declared 250 ms cold budget by 1–2 orders of
  magnitude for affected queries; short/rare-token queries (`ЗОП`,
  "касови апарати") stay within budget. See
  `docs/research/2026-07-02-fr027-search-perf.md` for the full
  measurement; the fix (body-index restructuring or tier-2 gating) is
  Task 14's decision, not yet made.
- **`diff`/historical `get_law(date)` single-version acts.** Real
  historical diffs only exist for the 225 acts with 2+ `law_versions`
  rows (FR-020) — for the other ~3,376 acts, `diff` returns the
  bilingual "single consolidated version held" note rather than a real
  diff, because the corpus itself only holds one recorded text version
  for those acts.
- **Bulgarian stemming (FR-021, backlog).** `bg_normalize` strips
  definite-article suffixes but isn't a real stemmer — the masculine
  adjective indefinite/definite pair `български`/`българският` still
  diverges in some cases. Closing this needs a proper Bulgarian
  Snowball stemmer, which conflicts with D-022 (pure-Python, no
  external NLP libs) unless that decision is revisited.

## Troubleshooting

### Process exit codes

`python -m mcp_server` exits non-zero on preflight failures so wrappers
(launchd, systemd, supervisord) can react before any tool call lands:

| Code | Meaning | Recovery |
|---|---|---|
| 0 | Server exited cleanly (host disconnected) | normal |
| 2 | `INDEX_MISSING` (catalog.db not at the configured path) OR the `LEGALIZE_CORPUS_DEFECTIVE` deploy-guard refused to start | run `python -m index.build --db <path>` to create the catalog; or set `LEGALIZE_ALLOW_DEFECTIVE=1` only if you understand the D-047 caveat it overrides |
| 3 | `INDEX_STALE` under `--strict` — git HEAD ≠ indexed commit | re-run `python -m index.build` (or `--incremental`), OR drop `--strict` to allow soft-warn startup |

### Common errors

**`ModuleNotFoundError: fastmcp`** → reinstall deps: `pip install -e
".[dev]"` from the repo root.

**`INDEX_MISSING` (exit 2)** → run `python -m index.build` to create
`catalog.db`.

**`INDEX_STALE` warning** (default) or refusal (`--strict`, exit 3) →
re-run `python -m index.build` (or `--incremental`) to refresh. Pass
`--strict` if you want the server to refuse to start on stale catalogs.

**"corpus-shaped directories not indexed" `ValueError` from
`index.build`** → the category-drift guard fired (see "One-time index
build" above); relocate the new directory's acts into a known category
dir or register it in `CATEGORY_DIRS`.

**FastMCP transport timeouts** → confirm the MCP host's `command`
points at the venv's `python` (or the `legalize-bg-mcp` console
script), not the system one. The system Python won't have `fastmcp`
installed.

**Search returns nothing for an obvious query** → check the actual
indexed form via `bg_normalize`:
```python
from index.fts import bg_normalize
print(bg_normalize("your query"))
```
The two-tier ranker requires at least one query token to match a
title or body token after normalization.
