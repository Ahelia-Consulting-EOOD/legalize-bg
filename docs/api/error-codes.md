# legalize-bg MCP Error Taxonomy

**Version:** 1.0.0  (matches `tools.json` `version`)
**Spec since:** Phase 1b.1 — D-026; extended in Phase 1b.2 with `QUERY_TOO_BROAD`.

This document catalogs every error code the legalize-bg MCP server returns through the FastMCP error envelope. Codes are stable: additive changes (new code) bump the minor version; removing or renaming a code bumps the major version (compatibility break).

The runtime authority is `mcp_server/errors.py:ERROR_CODES` (a `frozenset`). The machine-readable mirror is `docs/api/error-codes.json`. The published `tools.json` artifact carries the codes as a top-level `error_codes` array.

## Format

Every `ToolError` is serialized as:

```json
{
  "code": "<one of the codes below>",
  "<payload field 1>": "...",
  "<payload field 2>": "...",
  ...
}
```

The `code` is always a top-level key (not nested under "error"). Payload fields differ per code; this catalog enumerates them.

## Codes

### `LAW_NOT_FOUND`

Raised by: `get_law`, `get_article`.
When: the supplied name (title, slug, or identificador) does not resolve to any act in the catalog.
Payload:
- `name` (string): the input that failed to resolve.
- `suggestions` (array of objects): up to 5 nearby matches, each with `law_id`, `title`, and `identificador`. Empty array if no near matches.

### `AMBIGUOUS_NAME`

Raised by: `get_law`, `get_article`.
When: the supplied name matches multiple distinct acts (§7.1 slug-collision territory).
Payload:
- `name` (string): the input.
- `candidates` (array of objects): every candidate, each with `law_id`, `title`, and `identificador`. The model is expected to either disambiguate by `identificador` or ask the user.

### `NO_VERSION_AT_DATE`

Raised by: `get_law`, `get_article`.
When: the requested ISO date is before any `valid_from` for the resolved act, OR the act has no `law_versions` rows at all.
Payload:
- `law_id` (string).
- `date` (string, ISO 8601): the requested date.
- `earliest_valid_from` (string|null): the earliest `valid_from` recorded for this act, or null if no versions exist.

### `DATE_UNCERTAIN` (warning, rides in successful response)

Raised by: `get_law` (as a warning in the `warnings` array, not as a thrown error).
When: §7.2 — the act's `fecha_publicacion` was null at index time, so `valid_from` fell back to the bootstrap-run date.
Payload (as warning entry):
- `code: "DATE_UNCERTAIN"`.
- `source_date_marker: "unknown"` — signals to the model that the publication date in the response is approximate.

### `INVALID_ARTICLE_SPEC`

Raised by: `get_article`.
When: the article string can't be parsed by `parse_article_spec` (e.g., empty, or contains characters outside the allowed `Чч.0-9 а-яA-Z, -` set).
Payload:
- `article` (string): the input.
- `expected_forms` (array of strings): the canonical accepted forms (`"чл. 14"`, `"14"`, `"чл. 14а"`, `"чл. 14, ал. 2"`, `"14.2"`, `"чл. 14-16"`).

### `ARTICLE_NOT_FOUND`

Raised by: `get_article`.
When: the article spec parses but no `provisions` row matches `(law_id, article, paragraph?)` at the requested date.
Payload:
- `law_id` (string).
- `article` (string).
- `paragraph` (string|null): if a specific alinea was requested.
- `available_articles` (array of strings): every distinct article number in the act at the requested date, sorted by `_legal_article_sort_key`. Helps the model retry with a valid article number.

### `INDEX_STALE`

Raised by: any tool, at server startup.
When: `git HEAD ≠ laws.current_commit` for the relevant act AND `--strict` is in effect (or via runtime check; see runbook "Server runtime").
Payload:
- `expected_commit` (string): the working-tree HEAD.
- `index_commit` (string): what `laws.current_commit` says.
- `instruction` (string): "Re-run `python -m index.build --corpus . --db catalog.db`."

### `INDEX_MISSING`

Raised by: any tool, at server startup.
When: `catalog.db` does not exist or lacks the expected tables (typically a fresh checkout that hasn't been built).
Payload:
- `db_path` (string): the absolute path the server tried.
- `instruction` (string): "Run `python -m index.build --corpus . --db catalog.db` to create the index."

### `QUERY_TOO_BROAD` (added in 1b.2 — FR-016)

Raised by: `search`.
When: the query reduces to exactly one of the five Bulgarian category words: `наредба`, `закон`, `правилник`, `кодекс`, `постановление`. The reduction is: tokenize the input via `re.findall(r"\w+", query)` (alphanumeric runs only — punctuation is stripped), `bg_normalize` each token (case-fold + symmetric definite-article suffix stripping), then check that exactly one token comes out and matches the stop-word set. This catches all surface-form variants:

- Canonical: `"наредба"`, `"закон"`, `"правилник"`, `"кодекс"`, `"постановление"`.
- Definite article: `"наредбата"`, `"законът"`.
- Trailing punctuation: `"наредба."`, `"наредба—"`, `"наредба*"`, `"наредба…"`, `'"наредба"'`.
- Case + punctuation: `"НАРЕДБА—"`, `"  Наредба  "`.
- Definite + punctuation: `"законът—"`.

These all match thousands of acts each (2,604 ordinances for `наредба` alone) and produce 400+ ms cold-call latency outside the 100 ms p95 budget.

Payload:
- `query` (string): the input, truncated to 200 characters (defensive bound against accidentally-large client inputs).
- `category_words` (array of strings): the five stop-words, sorted alphabetically.
- `hint` (string): bilingual Bulgarian/English instruction asking for a more specific query.

Multi-word queries that contain a category word are NOT rejected:
- `"наредба за обществени"` → 3 tokens → passes through FTS5.
- `"наредба—правилник"` → 2 tokens (em-dash splits) → passes through FTS5; the two-tier ranker handles the conjunction efficiently.

## Versioning policy

- **Patch (1.0.x):** clarifying docs, payload field descriptions. No behavior change.
- **Minor (1.x.0):** adding a new code; adding optional payload fields to an existing code. Existing callers continue to work.
- **Major (x.0.0):** removing or renaming a code; making a previously optional payload field required. Compatibility break.

The version is set in `mcp_server/export_tools.py:TOOLS_JSON_VERSION` and propagates into `tools.json` and `error-codes.json`.
