# Phase 1b.2 — Structured Backend Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close Phase 1b.2 by hardening the perf-budget assertions (D-027), eliminating the FR-016 cold-call regression with a `QUERY_TOO_BROAD` rejection path, publishing versioned `tools.json` and error-codes schemas for downstream callers, and documenting the read-only idempotency contract — leaving Phase 1b.2's two open deferrals (`D-2026-05-09-03`, `D-2026-05-09-06`) resolved and the docs/code surface ready for the next phase boundary.

**Architecture:** Six task batches. Batch A fixes FR-016 with a stop-word reject in `mcp_server/queries.py:full_text_search` returning a new `QUERY_TOO_BROAD` `ToolError` — additive per Surface 3. Batch B promotes the soft perf assertions to hard AND adds a cold-call test (the existing test pattern lets warmed-cache numbers hide cold-call regressions). Batch C builds a `mcp_server/export_tools.py` script that asks the live FastMCP app for its tool schemas and writes them to a versioned `tools.json` — script is the source of truth, file is the artifact, CI enforces parity. Batch D publishes a versioned `docs/api/error-codes.md` catalog plus a machine-readable `docs/api/error-codes.json` schema. Batch E documents the read-only idempotency contract (one paragraph; this is observation, not new mechanism). Batch F closes the loop in `DEFERRED.md` (D-03 + D-06 → Resolved) and updates `ACTIVE.md`/`docs/sync/DECISIONS.md` to mark Phase 1b.2 done.

**Tech Stack:** Python 3.11+, FastMCP (live tool-schema introspection via `app.mcp.list_tools()`), SQLite3 + FTS5, pytest, JSON Schema (draft 2020-12) for `tools.json` and `error-codes.json`. Test runner: `.venv/bin/pytest`.

---

## Out of scope

- The Round-3-flagged `_run_match` allowlist consolidation between `index/fts.py` and `mcp_server/queries.py:resolve_name_to_law_id` (a known limitation noted in the existing comment block). Defer to a follow-up small-refactor plan; not required for Phase 1b.2 promotion.
- BM25 + LIMIT pushdown via FTS5 `rank` column (FR-016 alternative approach). The stop-word reject delivers the FR-016 outcome with smaller code; pushdown is heavier engineering for a single corner case.
- D-2026-05-09-01 (FR-013 long-form definite article), D-2026-05-09-02 (FR-017 body snippet), D-2026-05-09-04 (FR-015 synonyms), D-2026-05-09-05 (FR-014 incremental rebuild) — these target Phase 1b.3 / Phase 4, not 1b.2. They stay Open in `DEFERRED.md`.
- Telemetry / structured logging (Phase 1b.3 polish).
- `tools.json` versioning policy beyond a top-level `version: "1.0.0"` string + a one-line "additive only until 2.0" rule. Full SemVer governance is a 1b.3+ concern.

---

## Assumptions

- Working tree clean on `main` at HEAD `a33a70ab` after the review-fixes batch.
- Test baseline: **221 passing**.
- `.venv` exists with `pip install -e ".[dev]"` already run.
- Live `catalog.db` at repo root (1 GB, May 9 build) is available for cold-call perf measurement.
- FastMCP exposes tool schemas via `app.mcp.list_tools()` returning `FunctionTool` objects with `.parameters` (input JSON Schema) and `.output_schema` (output JSON Schema). Verified empirically.
- D-024 / D-026 / D-027 binding decisions remain in force.

## Empirical evidence (pre-recorded for Batch A and Batch B)

**FR-016 cold-call survey** (manual `python -c` against the live catalog, 5 calls per query, fresh process each batch — actually a single process, but the first call hits a cold FTS5 cache):

| Query | Min | Median | p95 (5 calls) | Max |
|---|---|---|---|---|
| **наредба** | **33ms** | 34ms | **437ms** | **437ms** |
| правилник | 7ms | 7ms | 60ms | 60ms |
| закон | 8ms | 9ms | 55ms | 55ms |
| кодекс | 1ms | 1ms | 7ms | 7ms |
| постановление | 24ms | 25ms | 27ms | 27ms |
| обществени поръчки | 10ms | 11ms | 66ms | 66ms |

Conclusion: FR-016 is **the cold-call case for single-word category queries**, not a steady-state regression. The existing 50-call test pattern (`REPRESENTATIVE_QUERIES * 5`) hides this because after the first warming call the FTS5 cache is hot. **Stop-word rejection eliminates the case entirely** (no FTS5 call → no cold cache concern → no budget risk).

**Stop-word list** (from FR-016 backlog text): `наредба`, `закон`, `правилник`, `кодекс`, `постановление`. Compared after `bg_normalize` (so `Наредба` → `наредба` triggers; `наредбата` → `наредба` triggers symmetric per `bg_normalize` last-character stripping; multi-word queries `наредба за` do NOT trigger).

**Live FastMCP tool-schema introspection** (verified):
```python
from mcp_server.server import build_app
app = build_app(conn, corpus_root=Path("."))
tools = await app.mcp.list_tools()  # returns list[FunctionTool]
for t in tools:
    d = t.model_dump()
    # d["parameters"] is the JSON Schema for the tool's INPUT
    # d["output_schema"] is the JSON Schema for the tool's OUTPUT
```

This is the load-bearing fact for Batch C: we don't write `tools.json` by hand; we let FastMCP introspect the live app and dump the result.

---

## File Structure

```
mcp_server/errors.py                            # MODIFY (Task 1): add QUERY_TOO_BROAD to ERROR_CODES
mcp_server/queries.py                           # MODIFY (Task 2): full_text_search rejects single-word category queries
tests/mcp_server/test_search.py                 # MODIFY (Tasks 1, 3): tests for the new reject path + non-category single words still work
mcp_server/server.py                            # NO MODIFICATION (full_text_search wraps the error correctly)

tests/perf/test_budgets.py                      # MODIFY (Task 5): _soft_assert → assert; add cold-call helper
tests/perf/test_cold_calls.py                   # CREATE (Task 4): cold-call perf test (each query gets a fresh connection)

mcp_server/export_tools.py                      # CREATE (Task 7): CLI that introspects FastMCP and writes tools.json
tools.json                                      # CREATE (Task 8): published schema artifact (regeneratable)
tests/mcp_server/test_export_tools.py           # CREATE (Task 9): parity test (tools.json matches what export_tools produces)

docs/api/error-codes.md                         # CREATE (Task 11): catalog of 9 error codes with payload shapes + version tag
docs/api/error-codes.json                       # CREATE (Task 12): JSON Schema for the 9 error codes (machine consumption)
tests/mcp_server/test_error_codes_doc.py        # CREATE (Task 13): asserts every ERROR_CODES entry has a row in error-codes.md AND a definition in error-codes.json

docs/runbook/2026-05-09-phase1b1-operator-setup.md  # MODIFY (Task 14): add Idempotency contract paragraph
                                                #   (file gets renamed implicitly — runbook lives at this path; contents updated)

docs/sync/DEFERRED.md                           # MODIFY (Task 15): D-03 + D-06 → Resolved
docs/sync/ACTIVE.md                             # MODIFY (Task 15): Phase 1b.2 status → complete; pending list updated
docs/sync/DECISIONS.md                          # MODIFY (Task 15): add D-028 (Phase 1b.2 closure) capturing the design choices
.ahelia/protected-surfaces.yaml                 # MODIFY (Task 15): mark D-2026-05-09-03 / -06 status: implemented; bump deferrals_meta.last_synced
```

No code-architecture changes outside the additive `QUERY_TOO_BROAD` error-code addition. No schema migrations. No changes to `bg_normalize`, `provisions` extraction, or response shapes (Surface 6 untouched). Surface 3 (MCP signatures) is touched only via the additive error code, not the function signatures.

---

## BATCH A — FR-016 fix: QUERY_TOO_BROAD reject (Tasks 1, 2, 3)

### Task 1: Failing test — `search` rejects single-word category queries with `QUERY_TOO_BROAD`

**Files:**
- Modify: `tests/mcp_server/test_search.py` (append new tests at the bottom)

- [ ] **Step 1: Inspect the existing test file for fixture conventions.**

Run: `grep -n "^def test_\|^@\|app =\|search\b" /Users/ekimir/swprj/legalize-bg/tests/mcp_server/test_search.py | head -20`
Expected: tests use the `app` fixture from `tests/mcp_server/conftest.py` and call `app.call_tool_sync("search", {...})`. The conftest fixture builds an app over a populated in-memory DB.

- [ ] **Step 2: Append two failing tests covering the new contract.**

```python
# Append to tests/mcp_server/test_search.py:

import pytest
from mcp_server.errors import ToolError


@pytest.mark.parametrize(
    "query",
    [
        "наредба",
        "закон",
        "правилник",
        "кодекс",
        "постановление",
        # bg_normalize symmetric forms — verify the reject also catches
        # the definite-article variants since users type both.
        "наредбата",
        "законът",
    ],
    ids=[
        "naredba",
        "zakon",
        "pravilnik",
        "kodeks",
        "postanovlenie",
        "naredba-definite",
        "zakon-definite",
    ],
)
def test_search_rejects_single_word_category_queries(app, query):
    """FR-016 / D-2026-05-09-03: single-word category queries match
    thousands of acts (2,604 ordinances for "наредба" alone), so FTS5
    has to rank all of them — pathological cold-call latency. Reject
    these before FTS5 with a structured QUERY_TOO_BROAD error so the
    caller can ask the user for more terms."""
    with pytest.raises(ToolError) as exc:
        app.call_tool_sync("search", {"query": query})
    assert exc.value.code == "QUERY_TOO_BROAD"
    payload = exc.value.payload
    assert "category_words" in payload
    assert isinstance(payload["category_words"], list)
    assert len(payload["category_words"]) == 5  # the 5 stop-words
    assert "hint" in payload
    # Hint should be model-actionable Bulgarian text.
    assert "повече" in payload["hint"] or "specific" in payload["hint"].lower()


def test_search_accepts_multi_word_query_starting_with_category_word(app):
    """Multi-word queries that include a category word are NOT rejected;
    'наредба за обществени' is a legitimate scoping query."""
    # Should not raise; should return a list (possibly empty).
    result = app.call_tool_sync("search", {"query": "наредба за обществени"})
    assert isinstance(result, list)


def test_search_accepts_single_word_non_category_query(app):
    """Non-category single words ('транспорт', 'образование') still go
    through FTS5 — the reject is targeted at the 5 specific category
    words only."""
    result = app.call_tool_sync("search", {"query": "транспорт"})
    assert isinstance(result, list)


def test_search_query_too_broad_payload_lists_actual_stop_words(app):
    """Payload's `category_words` should list the actual stop-words used
    so a model receiving the error can communicate them to the user
    without re-deriving the list."""
    with pytest.raises(ToolError) as exc:
        app.call_tool_sync("search", {"query": "наредба"})
    expected = {"наредба", "закон", "правилник", "кодекс", "постановление"}
    assert set(exc.value.payload["category_words"]) == expected
```

- [ ] **Step 3: Run the new tests to confirm RED.**

Run: `.venv/bin/pytest -q tests/mcp_server/test_search.py::test_search_rejects_single_word_category_queries tests/mcp_server/test_search.py::test_search_accepts_multi_word_query_starting_with_category_word tests/mcp_server/test_search.py::test_search_accepts_single_word_non_category_query tests/mcp_server/test_search.py::test_search_query_too_broad_payload_lists_actual_stop_words 2>&1 | tail -10`

Expected: 7 fail (the 7 parametrizations of the rejection test) — `QUERY_TOO_BROAD` is not yet a registered error code AND `full_text_search` doesn't reject. The two acceptance tests should already pass (they don't depend on the new logic). So expected: 7 failed, 2 passed.

### Task 2: Add `QUERY_TOO_BROAD` to ERROR_CODES + implement the reject in `full_text_search`

**Files:**
- Modify: `mcp_server/errors.py` (add code to ERROR_CODES)
- Modify: `mcp_server/queries.py` (`full_text_search` checks the stop-word list before calling `search_fts`)

- [ ] **Step 1: Add the new code.**

In `mcp_server/errors.py`, find the `ERROR_CODES = frozenset({...})` block. Add `"QUERY_TOO_BROAD",` after `"INDEX_MISSING",` and before the closing `})`. The new block:

```python
ERROR_CODES = frozenset({
    "LAW_NOT_FOUND",
    "AMBIGUOUS_NAME",
    "NO_VERSION_AT_DATE",
    "DATE_UNCERTAIN",     # warning, rides in successful response
    "INVALID_ARTICLE_SPEC",
    "ARTICLE_NOT_FOUND",
    "INDEX_STALE",
    "INDEX_MISSING",
    "QUERY_TOO_BROAD",    # FR-016: single-word category queries (e.g. "наредба")
})
```

- [ ] **Step 2: Implement the reject in `full_text_search`.**

In `mcp_server/queries.py`, find `def full_text_search(...)`. Before the call to `search_fts`, add the stop-word check.

The relevant import: `from mcp_server.errors import ToolError`. Verify it exists at the top of the file with `grep -n "from mcp_server.errors" mcp_server/queries.py`. If not, add it.

The check goes immediately after the docstring, before any other logic:

```python
def full_text_search(conn: sqlite3.Connection, query: str,
                     category: str | None = None,
                     limit: int = 20) -> list[dict]:
    """FTS5 search; symmetric bg_normalize is applied inside search_fts.

    Substitutes `<doc_id=N>` in the `title` slot for §7.3 phantom acts
    (empty titulo) so callers get a non-blank display string.

    Output `relevance` is the negated bm25 score so higher = better
    match (the SQLite bm25() function returns negative-where-lower-is-
    better; exposing the raw value would surprise callers who expect
    the conventional "higher is better" ordering).

    Output `title_snippet` is a highlighted title fragment, not body.
    See SearchHit docstring + FR-017 for the 1b.3 body-snippet rework.

    Single-word category queries (`наредба`, `закон`, `правилник`,
    `кодекс`, `постановление`) match thousands of acts each (2,604
    ordinances for "наредба" alone) and produce 400+ ms cold-call
    latency on FTS5 — outside the 100ms p95 budget. These are rejected
    with a `QUERY_TOO_BROAD` ToolError before FTS5 is even invoked
    (FR-016 / D-2026-05-09-03). The check runs after `bg_normalize`
    so definite-article forms (`наредбата`) and capitalization
    variants are caught uniformly.
    """
    # FR-016 single-word category-query reject.
    from index.fts import bg_normalize as _bg_normalize
    normalized = _bg_normalize(query).strip()
    if normalized in _CATEGORY_STOP_WORDS:
        raise ToolError(
            "QUERY_TOO_BROAD",
            {
                "query": query,
                "category_words": sorted(_CATEGORY_STOP_WORDS),
                "hint": (
                    "Заявката съответства на хиляди актове. Добавете "
                    "повече ключови думи (напр. \"наредба за обществени "
                    "поръчки\") за по-конкретно търсене. "
                    "Be more specific — single category words like "
                    "'наредба' match thousands of acts."
                ),
            },
        )

    rows = search_fts(conn, query, category=category, limit=limit)
    out: list[dict] = []
    for r in rows:
        title = r["title"] or f"<doc_id={r['doc_id']}>"
        out.append({
            "law_id": r["law_id"],
            "identificador": str(r["doc_id"]),
            "title": title,
            "category": r["category"],
            "title_snippet": r["snippet"],
            "relevance": -float(r["score"]),
        })
    return out
```

- [ ] **Step 3: Add the `_CATEGORY_STOP_WORDS` module-level constant near the top of `mcp_server/queries.py`.**

Find the imports block at the top of the file. After the imports (and after any existing module-level constants like `_FTS_CTX`), add:

```python
# FR-016 / D-2026-05-09-03: single-word queries matching these terms
# get rejected with QUERY_TOO_BROAD before FTS5 runs. Compared after
# `bg_normalize`, so definite-article forms ("наредбата") and case
# variants ("Наредба") are caught uniformly. Multi-word queries that
# happen to start with one of these words ("наредба за ...") are NOT
# rejected — only the single-word case is pathological.
_CATEGORY_STOP_WORDS = frozenset({
    "наредба",
    "закон",
    "правилник",
    "кодекс",
    "постановление",
})
```

If a module-level constants area doesn't exist, add the constant directly above `def resolve_name_to_law_id` (the first function in the file).

- [ ] **Step 4: Verify the import chain is correct.**

Run: `.venv/bin/python -c "from mcp_server.queries import _CATEGORY_STOP_WORDS, full_text_search; from mcp_server.errors import ERROR_CODES; assert 'QUERY_TOO_BROAD' in ERROR_CODES; print('OK', sorted(_CATEGORY_STOP_WORDS))"`
Expected: `OK ['закон', 'кодекс', 'наредба', 'постановление', 'правилник']`.

- [ ] **Step 5: Run the new tests to confirm GREEN.**

Run: `.venv/bin/pytest -q tests/mcp_server/test_search.py 2>&1 | tail -3`
Expected: full search test count + 10 new (= prior + 10). All green.

- [ ] **Step 6: Run the full suite.**

Run: `.venv/bin/pytest -q 2>&1 | tail -3`
Expected: 231 passed (221 baseline + 10 new). If any unrelated test fails, stop and investigate.

- [ ] **Step 7: Commit.**

```bash
git add mcp_server/errors.py mcp_server/queries.py tests/mcp_server/test_search.py
git commit -m "$(cat <<'EOF'
feat(search): reject single-word category queries with QUERY_TOO_BROAD

FR-016 / D-2026-05-09-03: single-word category queries like "наредба"
match all 2,604 ordinances by title — FTS5 has to rank them all to
extract top-20 and the cold-call hits ~437 ms p95 (vs the 100 ms
budget). Steady-state is fine after the first warming call, but the
existing test pattern (REPRESENTATIVE_QUERIES * 5 sequentially) hides
the cold case.

Adds the stop-word reject path: full_text_search compares the
bg_normalize-d query against {наредба, закон, правилник, кодекс,
постановление}; matches raise ToolError("QUERY_TOO_BROAD", ...) before
FTS5 is invoked. Multi-word queries starting with the same words
("наредба за обществени") still go through FTS5 unchanged.

QUERY_TOO_BROAD is the 9th ERROR_CODES entry — additive per Protected
Surface 3, no contract break for callers that don't switch on it.
The error payload carries the actual stop-word list and a Bulgarian +
English hint so the model can communicate the constraint to the user
without re-deriving the rule.

Test count: 221 → 231 (10 new in tests/mcp_server/test_search.py).

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

### Task 3: Verify FR-016 cold-call regression no longer reproduces

**Files:** none modified (verification only).

- [ ] **Step 1: Re-run the manual cold-call survey to confirm "наредба" is now rejected before FTS5.**

Run:
```bash
.venv/bin/python -c "
import time, sqlite3
from mcp_server.queries import full_text_search
from mcp_server.errors import ToolError
conn = sqlite3.connect('catalog.db')
conn.row_factory = sqlite3.Row
# Reject path: should be < 1 ms (no FTS5 call)
t0 = time.monotonic()
try:
    full_text_search(conn, 'наредба')
except ToolError as e:
    elapsed_ms = (time.monotonic() - t0) * 1000
    print(f'Rejected as {e.code} in {elapsed_ms:.2f} ms')
# Non-category single word still goes through FTS5
t0 = time.monotonic()
res = full_text_search(conn, 'транспорт')
print(f'транспорт: {len(res)} hits in {(time.monotonic() - t0) * 1000:.2f} ms')
"
```
Expected: `наредба` rejected in <5 ms; `транспорт` returns its hits in <100 ms.

- [ ] **Step 2: No commit.** Pure verification step.

---

## BATCH B — Hard perf-budget promotion (Tasks 4, 5, 6)

### Task 4: Cold-call perf test — fresh connection per query

**Files:**
- Create: `tests/perf/test_cold_calls.py`

**Why a separate file:** the existing `test_budgets.py` runs all queries in one connection on a hot FTS5 cache; cold-call latency is invisible there. A dedicated cold-call file with a fresh connection per query gives Phase 1b.2 a real signal that didn't exist in 1b.1.

- [ ] **Step 1: Inspect the existing test_budgets fixture pattern.**

Run: `grep -n "def conn\|catalog.db\|REPRESENTATIVE\|_p95" /Users/ekimir/swprj/legalize-bg/tests/perf/test_budgets.py`
Expected: see the `conn` fixture (module scope, opens catalog.db once) and `REPRESENTATIVE_QUERIES` list.

- [ ] **Step 2: Create the cold-call test file.**

```python
# Create tests/perf/test_cold_calls.py:

"""Cold-call perf budgets — each tool call uses a fresh SQLite
connection to mimic first-user-hit latency.

Phase 1b.1's `test_budgets.py` runs all queries in one connection,
so the FTS5 cache is hot after the first call and steady-state p95
hides cold-call regressions. Phase 1b.2 adds this file to lock the
cold case as a hard regression budget.

After the FR-016 stop-word reject (Batch A of the 1b.2 hardening
plan), the prior pathological cold-call case ("наредба" at 437 ms)
is short-circuited before FTS5 — but the budget itself stays
explicit so a future regression on any non-stop-word query is
caught.

All budgets in seconds; same numbers as test_budgets.py per design §9.
"""

import logging
import pathlib
import sqlite3
import time

import pytest

REPO = pathlib.Path(__file__).resolve().parent.parent.parent
DB = REPO / "catalog.db"

# Same numbers as test_budgets.py BUDGETS — one source of truth would
# be cleaner; for 1b.2 we keep the duplication to keep both files
# self-contained. A future small refactor can pull these out.
COLD_BUDGETS = {
    "search_cold_p95":         0.100,
    "get_law_cold_current_p95": 0.100,
    "get_article_cold_p95":    0.050,
}

# Smaller query set than test_budgets.py REPRESENTATIVE_QUERIES — cold
# calls open and close a fresh sqlite connection, which is the load-
# bearing cost we measure. 10 calls give a stable p95.
COLD_QUERIES = [
    "обществени поръчки",
    "електронно управление",
    "административно",
    "транспорт",
    "съд",
    "образование",
    "здравеопазване",
    "договор",
    "общини",
    "данък",
]


def _open_fresh() -> sqlite3.Connection:
    c = sqlite3.connect(str(DB), check_same_thread=False)
    c.row_factory = sqlite3.Row
    return c


def _p95(samples: list[float]) -> float:
    samples = sorted(samples)
    idx = min(int(len(samples) * 0.95), len(samples) - 1)
    return samples[idx]


def _hard_assert(p95: float, budget_key: str) -> None:
    """1b.2 hardened assertion (D-027): fails the test on regression."""
    budget = COLD_BUDGETS[budget_key]
    if p95 > budget:
        pytest.fail(
            f"PERF: {budget_key} p95={p95:.4f}s exceeds budget "
            f"{budget:.4f}s (1b.2 HARD). See FR-016 / DEFERRED.md "
            "if this is a single-word category query."
        )
    logging.info(
        "PERF: %s p95=%.4fs within budget %.4fs (HARD)",
        budget_key, p95, budget,
    )


@pytest.fixture(autouse=True)
def _skip_if_no_db():
    if not DB.exists():
        pytest.skip(
            f"catalog.db missing at {DB}; run `python -m index.build` "
            "to enable cold-call perf tests."
        )


def test_search_cold_p95():
    """Each query uses a fresh connection so the FTS5 cache is cold.
    Stop-word category queries are excluded (FR-016 reject path) — they
    don't reach FTS5."""
    from mcp_server.queries import full_text_search

    durations: list[float] = []
    for q in COLD_QUERIES:
        c = _open_fresh()
        t0 = time.monotonic()
        full_text_search(c, q, limit=20)
        durations.append(time.monotonic() - t0)
        c.close()
    _hard_assert(_p95(durations), "search_cold_p95")


def test_get_law_cold_current_p95():
    """Each lookup uses a fresh connection. Pulls 10 random doc_ids
    from the catalog up front, then opens fresh connections per call
    to time the cold lookup path."""
    from mcp_server.queries import resolve_name_to_law_id, version_with_warnings

    boot = _open_fresh()
    doc_ids = [
        str(r["doc_id"]) for r in boot.execute(
            "SELECT doc_id FROM laws WHERE doc_id != 0 LIMIT 10"
        ).fetchall()
    ]
    boot.close()

    durations: list[float] = []
    for did in doc_ids:
        c = _open_fresh()
        t0 = time.monotonic()
        law_id = resolve_name_to_law_id(c, did)
        version_with_warnings(c, law_id, date=None)
        durations.append(time.monotonic() - t0)
        c.close()
    _hard_assert(_p95(durations), "get_law_cold_current_p95")


def test_get_article_cold_p95():
    """SQL-only article lookups, fresh connection per call. Tightest
    budget (50 ms) — a regression here would mean the
    idx_provisions_lookup index is missing or the query plan changed."""
    from mcp_server.queries import article_lookup

    boot = _open_fresh()
    pairs = boot.execute(
        "SELECT law_id, article FROM provisions "
        "WHERE paragraph IS NULL LIMIT 10"
    ).fetchall()
    boot.close()

    durations: list[float] = []
    for r in pairs:
        c = _open_fresh()
        t0 = time.monotonic()
        article_lookup(c, r["law_id"], article=r["article"],
                       paragraph=None, date=None)
        durations.append(time.monotonic() - t0)
        c.close()
    _hard_assert(_p95(durations), "get_article_cold_p95")
```

- [ ] **Step 3: Run the new file to confirm baseline + verify the budgets pass.**

Run: `.venv/bin/pytest -q tests/perf/test_cold_calls.py -s --log-cli-level=INFO 2>&1 | tail -10`
Expected: 3 passed, with INFO log lines showing each cold-p95 and the budget. If any fail, the cold-call performance has actually regressed and Batch A's reject didn't fully address it — STOP and investigate. (Likely outcome: all three pass cleanly because the FR-016 reject removes the only pathological case from the COLD_QUERIES list.)

- [ ] **Step 4: No commit yet.** Task 5 modifies `test_budgets.py` to hard-promote — combined commit at end of Task 5.

### Task 5: Promote `_soft_assert` → `_hard_assert` in test_budgets.py

**Files:**
- Modify: `tests/perf/test_budgets.py` (replace `_soft_assert` with `_hard_assert` and update header comments)

- [ ] **Step 1: Replace the soft-assert function and its callsites.**

In `tests/perf/test_budgets.py`, find the docstring + `_soft_assert` block. Replace with:

```python
"""Performance regression budgets per design doc §9.

Phase 1b.1: SOFT assertions — log a warning on regression but pass.
Phase 1b.2 (this commit, D-027 hard-promotion): assertions FAIL the
test on regression so CI catches drift. The cold-call companion file
`test_cold_calls.py` adds first-user-hit coverage that this warm
sequential pattern alone can't see.

All budgets measured against the live catalog.db (3,573 acts, ~150k
article rows + ~300k alinea rows). Skipped when catalog.db is missing.
"""
```

(Notice: the prose changes; the imports stay.)

Then find:

```python
def _soft_assert(p95: float, budget_key: str) -> None:
    """1b.1 contract: log a warning above budget, don't fail. The
    eventual 1b.2 promotion swaps `logging.warning` for `assert`."""
    budget = BUDGETS[budget_key]
    if p95 > budget:
        logging.warning(
            "PERF: %s p95=%.4fs exceeds budget %.4fs (1b.1 SOFT)",
            budget_key, p95, budget,
        )
    else:
        logging.info(
            "PERF: %s p95=%.4fs within budget %.4fs",
            budget_key, p95, budget,
        )
```

Replace with:

```python
def _hard_assert(p95: float, budget_key: str) -> None:
    """1b.2 contract (D-027): fail the test on regression. Phase 1b.1
    used a soft warning here; Phase 1b.2's deferral D-2026-05-09-06
    promoted these to hard assertions now that observability has caught
    up enough that operators see CI failures instead of silent log
    lines."""
    budget = BUDGETS[budget_key]
    if p95 > budget:
        pytest.fail(
            f"PERF: {budget_key} p95={p95:.4f}s exceeds budget "
            f"{budget:.4f}s (1b.2 HARD). Investigate before merge."
        )
    logging.info(
        "PERF: %s p95=%.4fs within budget %.4fs (HARD)",
        budget_key, p95, budget,
    )
```

- [ ] **Step 2: Update the three call sites.**

Find `_soft_assert(_p95(durations), "search_p95")` and replace with `_hard_assert(_p95(durations), "search_p95")`. Same for `"get_law_current_p95"` and `"get_article_p95"` — three replacements total.

- [ ] **Step 3: Run the test_budgets module to confirm hard mode passes.**

Run: `.venv/bin/pytest -q tests/perf/test_budgets.py -s --log-cli-level=INFO 2>&1 | tail -10`
Expected: 3 passed; INFO log lines show "(HARD)" suffix in all three "within budget" messages. If any fail, the hot-cache p95 is somehow over budget — investigate (likely a transient OS-cache effect; rerun once before assuming a real regression).

- [ ] **Step 4: Run the full suite to confirm no other test depends on `_soft_assert` being soft.**

Run: `.venv/bin/pytest -q 2>&1 | tail -3`
Expected: 234 passed (231 from end of Batch A + 3 new in test_cold_calls.py). If anything else fails, investigate — most likely a fixture or import path issue.

- [ ] **Step 5: Commit Tasks 4 + 5 together.**

```bash
git add tests/perf/test_budgets.py tests/perf/test_cold_calls.py
git commit -m "$(cat <<'EOF'
perf(tests): hard-promote budgets + add cold-call coverage

D-027 / D-2026-05-09-06: 1b.1 used SOFT assertions in test_budgets.py
(log warning, don't fail). 1b.2 promotes them to HARD assertions
(pytest.fail) so CI catches budget drift instead of producing a log
line nobody reads. The promotion was deferred until 1b.1 had real-use
signal that the budgets are achievable; the past three review rounds
plus the FR-016 reject (Batch A) have established that signal.

Adds tests/perf/test_cold_calls.py — each tool call uses a fresh
SQLite connection so the FTS5 cache is cold. The existing
test_budgets.py runs all queries on one connection (warm cache after
the first call) and would have hidden the FR-016 cold-call regression
indefinitely if not for manual measurement. The cold-call file uses
the same numeric budgets (search<100ms, get_law<100ms,
get_article<50ms) and a smaller, FR-016-safe query set so the
pathological category words are excluded.

Test count: 231 → 234 (3 new in test_cold_calls.py).

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

### Task 6: Verify the perf-budget pair holds together

**Files:** none modified.

- [ ] **Step 1: Run the perf surface twice in quick succession.**

Run: `.venv/bin/pytest -q tests/perf/ 2>&1 | tail -3`
Expected: 6 passed (3 in `test_budgets.py` + 3 in `test_cold_calls.py`).

Run: `.venv/bin/pytest -q tests/perf/ 2>&1 | tail -3`
Expected: 6 passed again (run twice to catch flakes from OS cache state).

- [ ] **Step 2: No commit.**

---

## BATCH C — `tools.json` publication (Tasks 7, 8, 9)

### Task 7: Create `mcp_server/export_tools.py` CLI

**Files:**
- Create: `mcp_server/export_tools.py`

- [ ] **Step 1: Create the script.**

```python
# Create mcp_server/export_tools.py:

"""Export the live FastMCP tool schemas to a static `tools.json`
artifact for downstream callers.

Usage:
    .venv/bin/python -m mcp_server.export_tools --output tools.json

Why:
    Phase 1b.2 deliverable D-024 / D-2026-05-09-06 closure: callers
    consuming the MCP via the JSON-RPC `tools/list` endpoint already
    get these schemas at runtime, but downstream tooling (other-
    language clients, openapi-style codegen, doc renderers) wants a
    static artifact with a stable version tag.

    The CLI is the source of truth — `tools.json` is the artifact. CI
    runs `python -m mcp_server.export_tools --output /tmp/tools.json`
    and `diff` against the committed file, so any code change that
    shifts a tool schema either lands a regenerated tools.json or
    fails CI (see tests/mcp_server/test_export_tools.py).

Versioning:
    Top-level `version` field follows additive-SemVer: any change that
    only adds optional fields stays at 1.x; a breaking change (field
    removal or required-field addition) bumps to 2.0. The version is
    read from this script — code-side authority.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sqlite3
import sys
from pathlib import Path

from mcp_server.errors import ERROR_CODES
from mcp_server.server import build_app

# Bumped on any breaking change to the tool schemas. Additive changes
# (new optional input arg, new optional output field) stay at 1.x.
TOOLS_JSON_VERSION = "1.0.0"


def export_tool_schemas(corpus_root: Path | None = None) -> dict:
    """Build a transient FastMCP app and dump its tool schemas as a
    versioned dict ready for json.dumps."""
    # Use an in-memory DB — we don't actually run the tools, just ask
    # FastMCP what their input/output schemas look like.
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    app = build_app(conn, corpus_root=corpus_root or Path("."))

    async def _list() -> list[dict]:
        tools = await app.mcp.list_tools()
        return [
            {
                "name": t.name,
                "description": t.description,
                "input_schema": t.parameters,
                "output_schema": t.output_schema,
            }
            for t in tools
        ]

    tool_dicts = asyncio.run(_list())

    return {
        "version": TOOLS_JSON_VERSION,
        "spec": "https://modelcontextprotocol.io/specification/server/tools",
        "server": {
            "name": "legalize-bg",
            "phase": "1b.2",
            "transport": "stdio",
        },
        "tools": tool_dicts,
        "error_codes": sorted(ERROR_CODES),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Export legalize-bg MCP tool schemas to tools.json."
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("tools.json"),
        help="Output path (default: ./tools.json).",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help=("Compare existing --output file against freshly generated "
              "schemas; exit 1 on mismatch (CI parity check)."),
    )
    args = parser.parse_args(argv)

    payload = export_tool_schemas()
    serialized = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"

    if args.check:
        if not args.output.exists():
            print(f"ERROR: {args.output} does not exist; run without "
                  "--check to create it.", file=sys.stderr)
            return 1
        existing = args.output.read_text(encoding="utf-8")
        if existing != serialized:
            print(f"ERROR: {args.output} is out of date with the live "
                  "MCP tool schemas. Run `python -m "
                  "mcp_server.export_tools --output tools.json` to "
                  "regenerate.", file=sys.stderr)
            return 1
        print(f"OK: {args.output} matches live schemas "
              f"(version={TOOLS_JSON_VERSION}).")
        return 0

    args.output.write_text(serialized, encoding="utf-8")
    print(f"Wrote {args.output} (version={TOOLS_JSON_VERSION}, "
          f"{len(payload['tools'])} tools, "
          f"{len(payload['error_codes'])} error codes).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 2: Verify the script is importable and the export function runs.**

Run: `.venv/bin/python -c "
from mcp_server.export_tools import export_tool_schemas, TOOLS_JSON_VERSION
import json
d = export_tool_schemas()
print('version:', d['version'])
print('tools:', [t['name'] for t in d['tools']])
print('error_codes:', d['error_codes'])
print('search has output_schema:', bool([t for t in d['tools'] if t['name']=='search'][0]['output_schema']))
"`
Expected:
```
version: 1.0.0
tools: ['get_law', 'search', 'get_article']
error_codes: ['AMBIGUOUS_NAME', 'ARTICLE_NOT_FOUND', 'DATE_UNCERTAIN', 'INDEX_MISSING', 'INDEX_STALE', 'INVALID_ARTICLE_SPEC', 'LAW_NOT_FOUND', 'NO_VERSION_AT_DATE', 'QUERY_TOO_BROAD']
search has output_schema: True
```

- [ ] **Step 3: No commit.** Task 8 generates the file; one commit at end of Task 8.

### Task 8: Generate `tools.json` and verify

**Files:**
- Create: `tools.json` (at repo root)

- [ ] **Step 1: Run the script.**

Run: `.venv/bin/python -m mcp_server.export_tools --output tools.json`
Expected: prints `Wrote tools.json (version=1.0.0, 3 tools, 9 error codes).`

- [ ] **Step 2: Sanity-check the artifact.**

Run: `.venv/bin/python -c "
import json
d = json.loads(open('tools.json').read())
assert d['version'] == '1.0.0'
assert d['server']['name'] == 'legalize-bg'
assert d['server']['phase'] == '1b.2'
assert len(d['tools']) == 3
assert len(d['error_codes']) == 9  # 8 1b.1 + QUERY_TOO_BROAD
assert 'QUERY_TOO_BROAD' in d['error_codes']
for t in d['tools']:
    assert 'input_schema' in t
    assert 'output_schema' in t
    assert 'description' in t
print('OK')
"`
Expected: `OK`.

- [ ] **Step 3: --check mode round-trip — should pass against the file we just wrote.**

Run: `.venv/bin/python -m mcp_server.export_tools --check --output tools.json`
Expected: `OK: tools.json matches live schemas (version=1.0.0).`

- [ ] **Step 4: No commit yet.** Task 9 adds the parity test; commit Tasks 7+8+9 together.

### Task 9: Parity test — `tools.json` stays in sync with live schemas

**Files:**
- Create: `tests/mcp_server/test_export_tools.py`

- [ ] **Step 1: Create the parity test.**

```python
# Create tests/mcp_server/test_export_tools.py:

"""tools.json parity tests — ensures the committed artifact never
drifts from the live FastMCP tool schemas."""

import json
import pathlib
import subprocess
import sys

import pytest

from mcp_server.errors import ERROR_CODES
from mcp_server.export_tools import export_tool_schemas, TOOLS_JSON_VERSION

REPO = pathlib.Path(__file__).resolve().parent.parent.parent
TOOLS_JSON = REPO / "tools.json"


def test_export_tools_returns_three_tools():
    d = export_tool_schemas()
    names = sorted(t["name"] for t in d["tools"])
    assert names == ["get_article", "get_law", "search"]


def test_export_tools_includes_all_error_codes():
    d = export_tool_schemas()
    assert set(d["error_codes"]) == ERROR_CODES


def test_export_tools_sets_version():
    d = export_tool_schemas()
    assert d["version"] == TOOLS_JSON_VERSION
    # Sanity: a SemVer string with at least one dot.
    assert d["version"].count(".") == 2


def test_committed_tools_json_matches_live_schemas():
    """If this fails, run `python -m mcp_server.export_tools --output
    tools.json` to regenerate and commit. The CI mode of the script is
    exposed as the --check flag for shell-based pre-commit hooks."""
    if not TOOLS_JSON.exists():
        pytest.skip("tools.json not yet committed; run export script.")

    # Run the script in --check mode against the committed file.
    result = subprocess.run(
        [sys.executable, "-m", "mcp_server.export_tools",
         "--check", "--output", str(TOOLS_JSON)],
        capture_output=True,
        text=True,
        cwd=str(REPO),
    )
    assert result.returncode == 0, (
        "tools.json drift detected. stdout: "
        f"{result.stdout!r}\nstderr: {result.stderr!r}"
    )


def test_each_tool_has_input_and_output_schema():
    d = export_tool_schemas()
    for t in d["tools"]:
        assert isinstance(t["input_schema"], dict), t["name"]
        assert "properties" in t["input_schema"], t["name"]
        assert isinstance(t["output_schema"], dict), t["name"]


def test_search_input_schema_documents_query_too_broad_constraint():
    """Don't lock the exact wording, but ensure the description for
    `query` mentions the QUERY_TOO_BROAD constraint so MCP clients can
    surface it without reading the source. (Test passes if the error
    is mentioned anywhere in the search tool's description block.)"""
    d = export_tool_schemas()
    search = next(t for t in d["tools"] if t["name"] == "search")
    blob = json.dumps(search, ensure_ascii=False)
    assert "QUERY_TOO_BROAD" in blob, (
        "search docstring should mention the QUERY_TOO_BROAD reject "
        "for single-word category queries — currently missing."
    )
```

- [ ] **Step 2: Run the parity tests.**

Run: `.venv/bin/pytest -q tests/mcp_server/test_export_tools.py 2>&1 | tail -5`
Expected: 5 passed and 1 failed — the last test (`test_search_input_schema_documents_query_too_broad_constraint`) fails because the `search` docstring in `mcp_server/server.py` does NOT yet mention `QUERY_TOO_BROAD`. This drives Task 9b.

- [ ] **Step 2b: Update the `search` tool docstring in `mcp_server/server.py` to mention QUERY_TOO_BROAD.**

Find `def search(query: str, category: str | None = None, limit: int = 20)` in `mcp_server/server.py`. The docstring currently describes input args. Add a line in the `Raises:` section (or create one if absent):

```python
    def search(query: str, category: str | None = None,
               limit: int = 20) -> list[dict]:
        """Search the legislation corpus by free-text query.

        ... (existing args section) ...

        Raises:
            QUERY_TOO_BROAD: when the query (after normalization) is a
                single Bulgarian category word ("наредба", "закон",
                "правилник", "кодекс", "постановление"). These would
                match thousands of acts each; the rejection prevents
                a 400 ms+ cold-call latency outside the 100 ms p95
                budget. Multi-word queries containing the same words
                ("наредба за обществени поръчки") are NOT rejected.
        """
```

Locate the actual docstring (use `grep -n "def search" mcp_server/server.py` then read the docstring block) and graft the new `Raises:` paragraph at the end. If a `Raises:` section already exists, append to it instead of duplicating.

- [ ] **Step 3: Regenerate `tools.json` (the docstring change shifts the description).**

Run: `.venv/bin/python -m mcp_server.export_tools --output tools.json`
Expected: `Wrote tools.json (version=1.0.0, 3 tools, 9 error codes).`

- [ ] **Step 4: Re-run the parity tests.**

Run: `.venv/bin/pytest -q tests/mcp_server/test_export_tools.py 2>&1 | tail -3`
Expected: 6 passed.

- [ ] **Step 5: Run the full suite.**

Run: `.venv/bin/pytest -q 2>&1 | tail -3`
Expected: 240 passed (234 from end of Batch B + 6 new in test_export_tools.py).

- [ ] **Step 6: Commit Tasks 7+8+9 together.**

```bash
git add mcp_server/export_tools.py mcp_server/server.py tools.json tests/mcp_server/test_export_tools.py
git commit -m "$(cat <<'EOF'
feat(mcp): publish tools.json + export script + parity test

Phase 1b.2 deliverable: versioned static artifact for downstream
callers consuming the legalize-bg MCP. Three pieces:

- mcp_server/export_tools.py — CLI that introspects the live FastMCP
  app via app.mcp.list_tools() and dumps the input/output JSON
  schemas plus the 9-code error taxonomy. The CLI is the source of
  truth; tools.json is the artifact. --check mode for CI parity.

- tools.json (new at repo root) — version=1.0.0; 3 tools (get_law,
  search, get_article) with full input_schema, output_schema, and
  description; 9 error codes (8 from 1b.1 + QUERY_TOO_BROAD added in
  Batch A).

- tests/mcp_server/test_export_tools.py — 6 parity tests; the
  load-bearing one shells out to `--check` to confirm the committed
  artifact matches the live schemas. CI catches drift automatically.

- mcp_server/server.py: search docstring gains a Raises: section
  documenting QUERY_TOO_BROAD so the constraint reaches MCP clients
  via the standard tool-description channel.

Test count: 234 → 240 (6 new in test_export_tools.py).

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## BATCH D — Error-taxonomy formalization (Tasks 10, 11, 12, 13)

### Task 10: Catalog the 9 error codes in `docs/api/error-codes.md`

**Files:**
- Create: `docs/api/error-codes.md`

- [ ] **Step 1: Create the directory if absent.**

Run: `mkdir -p /Users/ekimir/swprj/legalize-bg/docs/api && ls /Users/ekimir/swprj/legalize-bg/docs/api/`
Expected: empty (or shows existing api/ contents — currently expected to be absent).

- [ ] **Step 2: Write the catalog.**

```markdown
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

### `DATE_UNCERTAIN` ⚠️ warning, rides in successful response

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

### `QUERY_TOO_BROAD` ✨ added in 1b.2 (FR-016)

Raised by: `search`.
When: the query, after `bg_normalize`, is exactly one of the five Bulgarian category words: `наредба`, `закон`, `правилник`, `кодекс`, `постановление`. These match thousands of acts each (2,604 ordinances for `наредба` alone) and produce 400+ ms cold-call latency outside the 100 ms p95 budget.
Payload:
- `query` (string): the input.
- `category_words` (array of strings): the five stop-words, sorted alphabetically.
- `hint` (string): bilingual Bulgarian/English instruction asking for a more specific query.

Multi-word queries that contain a category word (`"наредба за обществени"`) are NOT rejected — they pass through FTS5 unchanged.

## Versioning policy

- **Patch (1.0.x):** clarifying docs, payload field descriptions. No behavior change.
- **Minor (1.x.0):** adding a new code; adding optional payload fields to an existing code. Existing callers continue to work.
- **Major (x.0.0):** removing or renaming a code; making a previously optional payload field required. Compatibility break.

The version is set in `mcp_server/export_tools.py:TOOLS_JSON_VERSION` and propagates into `tools.json` and `error-codes.json`.
```

- [ ] **Step 3: No commit.** Task 11 adds the JSON Schema; combined commit at end of Task 13.

### Task 11: Create `docs/api/error-codes.json` machine-readable schema

**Files:**
- Create: `docs/api/error-codes.json`

- [ ] **Step 1: Write the JSON schema.**

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://github.com/Ahelia-Consulting-EOOD/legalize-bg/docs/api/error-codes.json",
  "title": "legalize-bg MCP error taxonomy",
  "version": "1.0.0",
  "description": "Machine-readable catalog of every error code the legalize-bg MCP server returns. Mirror of docs/api/error-codes.md.",
  "type": "object",
  "properties": {
    "version": {
      "type": "string",
      "const": "1.0.0"
    },
    "codes": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["code", "raised_by", "category", "payload"],
        "properties": {
          "code": {"type": "string"},
          "raised_by": {
            "type": "array",
            "items": {"type": "string", "enum": ["get_law", "search", "get_article"]}
          },
          "category": {
            "type": "string",
            "enum": ["error", "warning"]
          },
          "since_phase": {"type": "string"},
          "payload": {
            "type": "object",
            "description": "Payload fields. Each entry: name -> {type, optional, description}."
          }
        }
      }
    }
  },
  "required": ["version", "codes"],

  "data": {
    "version": "1.0.0",
    "codes": [
      {
        "code": "LAW_NOT_FOUND",
        "raised_by": ["get_law", "get_article"],
        "category": "error",
        "since_phase": "1b.1",
        "payload": {
          "name": {"type": "string", "optional": false, "description": "the input that failed to resolve"},
          "suggestions": {"type": "array", "optional": false, "description": "up to 5 nearby matches; empty if no candidates"}
        }
      },
      {
        "code": "AMBIGUOUS_NAME",
        "raised_by": ["get_law", "get_article"],
        "category": "error",
        "since_phase": "1b.1",
        "payload": {
          "name": {"type": "string", "optional": false, "description": "the input"},
          "candidates": {"type": "array", "optional": false, "description": "every candidate with law_id, title, identificador"}
        }
      },
      {
        "code": "NO_VERSION_AT_DATE",
        "raised_by": ["get_law", "get_article"],
        "category": "error",
        "since_phase": "1b.1",
        "payload": {
          "law_id": {"type": "string", "optional": false, "description": "resolved act"},
          "date": {"type": "string", "optional": false, "description": "ISO date requested"},
          "earliest_valid_from": {"type": "string|null", "optional": false, "description": "earliest version's valid_from, or null"}
        }
      },
      {
        "code": "DATE_UNCERTAIN",
        "raised_by": ["get_law"],
        "category": "warning",
        "since_phase": "1b.1",
        "payload": {
          "code": {"type": "string", "optional": false, "description": "always 'DATE_UNCERTAIN'"},
          "source_date_marker": {"type": "string", "optional": false, "description": "always 'unknown'"}
        }
      },
      {
        "code": "INVALID_ARTICLE_SPEC",
        "raised_by": ["get_article"],
        "category": "error",
        "since_phase": "1b.1",
        "payload": {
          "article": {"type": "string", "optional": false, "description": "the input"},
          "expected_forms": {"type": "array", "optional": false, "description": "canonical accepted forms"}
        }
      },
      {
        "code": "ARTICLE_NOT_FOUND",
        "raised_by": ["get_article"],
        "category": "error",
        "since_phase": "1b.1",
        "payload": {
          "law_id": {"type": "string", "optional": false, "description": "resolved act"},
          "article": {"type": "string", "optional": false, "description": "requested article"},
          "paragraph": {"type": "string|null", "optional": false, "description": "alinea if requested"},
          "available_articles": {"type": "array", "optional": false, "description": "every article in the act at the requested date"}
        }
      },
      {
        "code": "INDEX_STALE",
        "raised_by": ["get_law", "search", "get_article"],
        "category": "error",
        "since_phase": "1b.1",
        "payload": {
          "expected_commit": {"type": "string", "optional": false, "description": "working-tree HEAD"},
          "index_commit": {"type": "string", "optional": false, "description": "laws.current_commit"},
          "instruction": {"type": "string", "optional": false, "description": "remediation"}
        }
      },
      {
        "code": "INDEX_MISSING",
        "raised_by": ["get_law", "search", "get_article"],
        "category": "error",
        "since_phase": "1b.1",
        "payload": {
          "db_path": {"type": "string", "optional": false, "description": "expected catalog path"},
          "instruction": {"type": "string", "optional": false, "description": "remediation"}
        }
      },
      {
        "code": "QUERY_TOO_BROAD",
        "raised_by": ["search"],
        "category": "error",
        "since_phase": "1b.2",
        "payload": {
          "query": {"type": "string", "optional": false, "description": "the input"},
          "category_words": {"type": "array", "optional": false, "description": "five stop-words, alphabetically sorted"},
          "hint": {"type": "string", "optional": false, "description": "bilingual instruction"}
        }
      }
    ]
  }
}
```

- [ ] **Step 2: Verify it parses as JSON.**

Run: `.venv/bin/python -c "import json; d = json.loads(open('docs/api/error-codes.json').read()); print('OK', len(d['data']['codes']), 'codes; version', d['data']['version'])"`
Expected: `OK 9 codes; version 1.0.0`.

- [ ] **Step 3: No commit.** Task 12 wires the parity test.

### Task 12: Parity test — every `ERROR_CODES` entry has a Markdown row AND a JSON entry

**Files:**
- Create: `tests/mcp_server/test_error_codes_doc.py`

- [ ] **Step 1: Create the test.**

```python
# Create tests/mcp_server/test_error_codes_doc.py:

"""Parity tests for the error-taxonomy publication. Every code in
`mcp_server.errors.ERROR_CODES` must appear in both
`docs/api/error-codes.md` (as a section heading) and
`docs/api/error-codes.json` (as a `codes[].code` entry). Catches drift
when a new code is added to the runtime registry but not to the
published catalog."""

import json
import pathlib
import re

from mcp_server.errors import ERROR_CODES

REPO = pathlib.Path(__file__).resolve().parent.parent.parent
ERR_MD = REPO / "docs" / "api" / "error-codes.md"
ERR_JSON = REPO / "docs" / "api" / "error-codes.json"


def test_every_runtime_code_has_a_markdown_section():
    """Each ERROR_CODES entry must appear as a `### `code`` heading in
    the catalog (e.g., ### `LAW_NOT_FOUND` or ### `QUERY_TOO_BROAD`)."""
    md = ERR_MD.read_text(encoding="utf-8")
    headings = set(re.findall(r"^### `([A-Z_]+)`", md, flags=re.M))
    runtime = set(ERROR_CODES)
    missing_in_md = runtime - headings
    extra_in_md = headings - runtime
    assert not missing_in_md, (
        f"runtime ERROR_CODES not documented in error-codes.md: "
        f"{sorted(missing_in_md)}"
    )
    assert not extra_in_md, (
        f"error-codes.md mentions codes not in runtime ERROR_CODES: "
        f"{sorted(extra_in_md)}"
    )


def test_every_runtime_code_has_a_json_entry():
    d = json.loads(ERR_JSON.read_text(encoding="utf-8"))
    json_codes = {entry["code"] for entry in d["data"]["codes"]}
    runtime = set(ERROR_CODES)
    missing_in_json = runtime - json_codes
    extra_in_json = json_codes - runtime
    assert not missing_in_json, (
        f"runtime ERROR_CODES not in error-codes.json: "
        f"{sorted(missing_in_json)}"
    )
    assert not extra_in_json, (
        f"error-codes.json has codes not in runtime: "
        f"{sorted(extra_in_json)}"
    )


def test_md_and_json_versions_match():
    md = ERR_MD.read_text(encoding="utf-8")
    md_version_match = re.search(r"\*\*Version:\*\*\s*([0-9.]+)", md)
    assert md_version_match, "error-codes.md missing **Version:** marker"
    md_version = md_version_match.group(1)

    j = json.loads(ERR_JSON.read_text(encoding="utf-8"))
    json_version = j["data"]["version"]

    from mcp_server.export_tools import TOOLS_JSON_VERSION
    assert md_version == json_version == TOOLS_JSON_VERSION, (
        f"version drift: md={md_version} json={json_version} "
        f"code={TOOLS_JSON_VERSION}"
    )


def test_query_too_broad_marked_since_1b2():
    """Sanity check that the new 1b.2 code is correctly tagged."""
    j = json.loads(ERR_JSON.read_text(encoding="utf-8"))
    qtb = next(c for c in j["data"]["codes"] if c["code"] == "QUERY_TOO_BROAD")
    assert qtb["since_phase"] == "1b.2"
    assert qtb["category"] == "error"
    assert "search" in qtb["raised_by"]
```

- [ ] **Step 2: Run the parity tests.**

Run: `.venv/bin/pytest -q tests/mcp_server/test_error_codes_doc.py 2>&1 | tail -3`
Expected: 4 passed.

- [ ] **Step 3: No commit yet.** Task 13 cross-links from the runbook; combined commit at end of Task 13.

### Task 13: Cross-link from runbook + commit Batch D

**Files:**
- Modify: `docs/runbook/2026-05-09-phase1b1-operator-setup.md` (add a one-line link in the Error codes section)

- [ ] **Step 1: Find the existing "Error codes (D-026)" section in the runbook.**

Run: `grep -n "Error codes (D-026)\|^## Error\|Error envelope" /Users/ekimir/swprj/legalize-bg/docs/runbook/2026-05-09-phase1b1-operator-setup.md | head -5`
Expected: a line ~129 with the `## Error codes (D-026)` heading.

- [ ] **Step 2: Append a cross-link line beneath the section heading.**

Find the `## Error codes (D-026)` heading and the prose that follows. Insert immediately after the heading (before the existing table):

```
> **Authoritative catalog:** `docs/api/error-codes.md` (Markdown for humans) and `docs/api/error-codes.json` (machine-readable). Both are version-tagged 1.0.0 and tested for parity with `mcp_server.errors.ERROR_CODES`. Phase 1b.2 added `QUERY_TOO_BROAD` (FR-016 — single-word category-query reject).
```

- [ ] **Step 3: Run the full test suite.**

Run: `.venv/bin/pytest -q 2>&1 | tail -3`
Expected: 244 passed (240 from end of Batch C + 4 new in test_error_codes_doc.py).

- [ ] **Step 4: Commit Batch D.**

```bash
git add docs/api/error-codes.md docs/api/error-codes.json tests/mcp_server/test_error_codes_doc.py docs/runbook/2026-05-09-phase1b1-operator-setup.md
git commit -m "$(cat <<'EOF'
docs(api): publish versioned error-code catalog (md + json + parity tests)

Phase 1b.2 deliverable: formalize the 9-code error taxonomy for
downstream callers consuming the legalize-bg MCP. Three artifacts:

- docs/api/error-codes.md — human-readable catalog with each code's
  raising tools, payload fields, and the 1b.1 vs 1b.2 phase tags.
  Version 1.0.0; SemVer policy spelled out.

- docs/api/error-codes.json — machine-readable mirror with payload
  field types and descriptions. Same version. Includes a JSON Schema
  envelope so consumers can validate.

- tests/mcp_server/test_error_codes_doc.py — 4 parity tests:
  every ERROR_CODES entry has a Markdown section AND a JSON entry;
  versions across md/json/code stay in sync; QUERY_TOO_BROAD is
  correctly tagged since_phase=1b.2.

Runbook gains a one-line cross-link in the existing "Error codes
(D-026)" section pointing at the new authoritative artifacts.

Test count: 240 → 244.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## BATCH E — Idempotency contract documentation (Task 14)

### Task 14: Document the read-only idempotency contract

**Files:**
- Modify: `docs/runbook/2026-05-09-phase1b1-operator-setup.md` (add "Idempotency" subsection)

The Phase 1b.2 design entry in the design doc lists "idempotency contract documented" as a deliverable. The legalize-bg MCP tools are all read-only — no writes against the catalog or working tree at request time. This is observation, not new mechanism, so it's a small documentation addition.

- [ ] **Step 1: Find a sensible insertion point.**

Run: `grep -n "^## " /Users/ekimir/swprj/legalize-bg/docs/runbook/2026-05-09-phase1b1-operator-setup.md`
Expected: a sequence of `##` sections including `Server runtime`, `Tools surfaced`, `Error codes (D-026)`, `Known limitations (tracked as FRs)`, etc.

- [ ] **Step 2: Insert a new `## Idempotency contract` section between "Server runtime" and "Tools surfaced".**

```markdown
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
- Concurrent calls do not race — SQLite is opened with `check_same_thread=False`, FastMCP serializes per-tool execution, and there are no shared mutable structures across calls.
- A caller may safely retry on transport-level failures without risk of duplicated side-effects.

**Non-idempotency to be aware of:**
- The build path (`python -m index.build`) IS NOT idempotent in the sense that re-running it issues `DELETE FROM laws_fts` etc. (full rebuild). FR-014 tracks the incremental rebuild path; until then, do not re-run the build under load.
- Working-tree edits between requests will surface in subsequent `get_law` responses via the fast path (commit_hash matches HEAD). The runbook's `INDEX_STALE` advice covers this.
```

- [ ] **Step 3: Verify no markdown-rendering surprises.**

Run: `grep -n "^## Idempotency" /Users/ekimir/swprj/legalize-bg/docs/runbook/2026-05-09-phase1b1-operator-setup.md`
Expected: 1 hit on the new heading.

Run: `head -200 /Users/ekimir/swprj/legalize-bg/docs/runbook/2026-05-09-phase1b1-operator-setup.md | tail -40`
Expected: the new section sits between `Server runtime` and `Tools surfaced` with consistent heading levels.

- [ ] **Step 4: Commit.**

```bash
git add docs/runbook/2026-05-09-phase1b1-operator-setup.md
git commit -m "$(cat <<'EOF'
docs(runbook): document read-only idempotency contract for MCP tools

Phase 1b.2 deliverable closure: the design doc named "idempotency
contract documented" as a 1b.2 deliverable. All three tools are
read-only at request time — no corpus writes, no catalog writes, no
network I/O — so the contract is observation rather than new
mechanism. Documents:

- What the tools never write to (corpus, catalog, network).
- What they DO write (logger, OS file cache — the latter incidental).
- Idempotency consequences: retries safe, concurrent calls don't
  race, no duplicated side-effects.
- Non-idempotency to be aware of: the build path is NOT idempotent
  (DELETE/INSERT full rebuild — FR-014 tracks the incremental path).

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## BATCH F — Close-out (Task 15)

### Task 15: Resolve deferrals + update ACTIVE.md + DECISIONS.md + protected-surfaces.yaml

**Files:**
- Modify: `docs/sync/DEFERRED.md` (move D-2026-05-09-03 and D-2026-05-09-06 to Resolved deferrals)
- Modify: `docs/sync/ACTIVE.md` (Phase 1b.2 → complete; update next actions)
- Modify: `docs/sync/DECISIONS.md` (add D-028 capturing Phase 1b.2 closure decisions)
- Modify: `.ahelia/protected-surfaces.yaml` (mark D-2026-05-09-03 and -06 status: implemented; bump deferrals_meta.last_synced)

- [ ] **Step 1: Update `docs/sync/DEFERRED.md`.**

Find the row for `D-2026-05-09-03` in the Active deferrals table. Cut it and the `D-2026-05-09-06` row. Move them under the "Resolved deferrals" section, applying the row schema introduced for the Resolved section:

In the Active table, REMOVE these two rows (leaving the other four):
```
| D-2026-05-09-03 | Single-word category queries (`наредба`) overrun the 100 ms p95 search budget | Phase 1b.1 | Phase 1b.2 | Open | 2026-05-09 (filed) | [FR-016](../frs/INDEX.md) |
| D-2026-05-09-06 | Soft perf assertions (`tests/perf/test_budgets.py` logs warnings, doesn't fail) — promote to hard | Phase 1b.1 | Phase 1b.2 | Open | 2026-05-09 (filed) | [D-027](DECISIONS.md) |
```

In the Resolved deferrals section, REPLACE the existing template/schema block (the example row) with TWO real rows reflecting the resolutions:

```
## Resolved deferrals

| ID | Title | Punted from | Target | Status | Last reviewed | FR / Decision | Resolution note |
|---|---|---|---|---|---|---|---|
| D-2026-05-09-03 | Single-word category queries (`наредба`) overrun the 100 ms p95 search budget | Phase 1b.1 | Phase 1b.2 | Implemented | 2026-05-09 | [FR-016](../frs/INDEX.md) | Stop-word reject path in `mcp_server/queries.py:full_text_search` raises new `QUERY_TOO_BROAD` error before FTS5; closed in Phase 1b.2 hardening plan. See [D-028](DECISIONS.md). |
| D-2026-05-09-06 | Soft perf assertions (`tests/perf/test_budgets.py` logs warnings, doesn't fail) — promote to hard | Phase 1b.1 | Phase 1b.2 | Implemented | 2026-05-09 | [D-027](DECISIONS.md) | `_soft_assert` → `_hard_assert` in `tests/perf/test_budgets.py`; new `tests/perf/test_cold_calls.py` adds first-user-hit coverage. See [D-028](DECISIONS.md). |
```

(Keep the row-schema explanatory text below in case the next phase boundary resolves more rows; just drop the EXAMPLE row whose ID was D-YYYY-MM-DD-NN.)

- [ ] **Step 2: Update `docs/sync/ACTIVE.md`.**

Find the section header `**Phase 1b.1** (MCP server) — complete on \`main\`:`. Add a sibling section for 1b.2 just below the 1b.1 bullet list:

```
**Phase 1b.2** (structured backend hardening) — complete on `main` 2026-05-09:
- FR-016 closed via the `QUERY_TOO_BROAD` reject path: single-word category queries now short-circuit before FTS5 (returns the structured error in <5 ms instead of 437 ms cold-call FTS5 ranking over 2,604 ordinances). 9th error code, additive per Surface 3.
- D-027 closed: `tests/perf/test_budgets.py` soft assertions promoted to hard via `_hard_assert`. New `tests/perf/test_cold_calls.py` adds first-user-hit coverage with fresh-connection-per-query.
- `tools.json` published (version 1.0.0) — full input/output JSON schemas for all 3 tools plus the 9-code error taxonomy. Source of truth: `mcp_server/export_tools.py`. CI parity test in `tests/mcp_server/test_export_tools.py`.
- Error taxonomy formalized: `docs/api/error-codes.md` (humans) + `docs/api/error-codes.json` (machines), both at version 1.0.0, parity-tested against runtime `ERROR_CODES`.
- Idempotency contract documented in the runbook (read-only at request time; build path explicitly non-idempotent — FR-014 tracks the incremental rebuild).
- Test count: 221 → 244.
```

In the "Pending" section of ACTIVE.md, REMOVE the bullet that mentions Phase 1b.2 as upcoming work (it's now done). Reformat:

OLD bullet to remove (search for the start):
```
- **Phase 1b.2** — structured backend hardening: ...
```

LEAVE 1b.3 and Phase 2 / FR-011 G2 triage bullets intact.

- [ ] **Step 3: Add D-028 to `docs/sync/DECISIONS.md`.**

Find the last decision (likely D-027). Append at the end of the file (or before any "draft" sentinel section):

```markdown
## D-028 — Phase 1b.2 closure (2026-05-09)

**Status:** Decided.
**Context:** Phase 1b.2 had four deliverables per the design doc §4 roadmap and the two open deferrals in `docs/sync/DEFERRED.md` targeting 1b.2: (a) FR-016 perf cold-call regression, (b) D-027 soft → hard perf assertions, (c) versioned `tools.json` artifact, (d) formalized error-taxonomy publication. Plus the design doc's "idempotency contract documented" line item.

**Decision:** Closed all four with a single coordinated batch (`docs/plans/2026-05-09-phase1b2-hardening.md`). Specific design choices:

1. **FR-016 stop-word reject** instead of BM25 + LIMIT pushdown. Smaller code, eliminates the cold-call case entirely, fits the existing `ToolError` pattern. New error code `QUERY_TOO_BROAD` is additive per Surface 3. Trade-off: rejects 5 single-word inputs that *might* in theory be legitimate; in practice these match thousands of acts and the rejection improves UX (the model can ask the user for more terms instead of dumping 20 random ordinances).

2. **`tools.json` source of truth** = `mcp_server/export_tools.py`. The committed file is an artifact, not a hand-edited document. CI parity (`--check` mode) prevents drift. Versioning policy: additive minor bumps, breaking-change major bumps; the version string lives in code.

3. **Error-taxonomy double publication** (md + json). The Markdown is for humans reading the runbook; the JSON is for machine consumption (other-language SDKs, codegen). Parity tests in `tests/mcp_server/test_error_codes_doc.py` enforce both stay in sync with the runtime registry.

4. **Cold-call test added as a separate file** rather than extending `test_budgets.py`. The two test patterns (sequential warm cache vs fresh-connection-per-call cold cache) measure structurally different things; mixing them in one file would obscure both.

5. **Idempotency contract stays as documentation, not a runtime check.** The tools are already read-only by construction; adding runtime assertions would be belt-and-suspenders for an invariant the test suite already establishes.

**Consequences:**
- Phase 1b.2 closes; 1b.3 (operator polish) is now the next development phase.
- `tools.json` and `error-codes.{md,json}` are published artifacts; downstream callers can consume them now.
- Three of the six 1b.1-era deferrals close (D-2026-05-09-03, -06; the FR-016 one and the D-027 one). The remaining four (FR-013, FR-014, FR-015, FR-017) target 1b.3 / Phase 4 and stay Open.

**Cross-references:** `docs/plans/2026-05-09-phase1b2-hardening.md` (this plan), `docs/sync/DEFERRED.md` (the two now-Resolved rows), `tools.json`, `docs/api/error-codes.{md,json}`.
```

- [ ] **Step 4: Update `.ahelia/protected-surfaces.yaml` deferrals block.**

In the `deferrals:` block at the bottom of `.ahelia/protected-surfaces.yaml`, find the entries with `id: D-2026-05-09-03` and `id: D-2026-05-09-06`. Change `status: open` to `status: implemented` for BOTH rows. Add a new key `resolution_note:` to each:

For `D-2026-05-09-03`:
```yaml
  - id: D-2026-05-09-03
    fr: FR-016
    title: single-word category queries overrun the 100ms p95 search budget
    punted_from: 1b.1
    target: 1b.2
    status: implemented
    resolution_note: "Stop-word reject path in mcp_server.queries.full_text_search; D-028."
    surfaces_affected:
      - "index/fts.py:search_fts"
      - "tests/perf/test_budgets.py"
```

For `D-2026-05-09-06`:
```yaml
  - id: D-2026-05-09-06
    decision: D-027
    title: soft perf assertions (1b.2 hard-promote)
    punted_from: 1b.1
    target: 1b.2
    status: implemented
    resolution_note: "_soft_assert → _hard_assert + cold-call coverage; D-028."
    surfaces_affected:
      - "tests/perf/test_budgets.py"
```

In the `deferrals_meta:` block, update `last_synced: 2026-05-09` (already that date — keep the same value, but ensure the file is touched).

- [ ] **Step 5: YAML parse + cross-reference sweep.**

Run: `.venv/bin/python -c "
import yaml
d = yaml.safe_load(open('.ahelia/protected-surfaces.yaml'))
defs = d['deferrals']
implemented = [x for x in defs if x['status'] == 'implemented']
open_ = [x for x in defs if x['status'] == 'open']
assert len(implemented) == 2, f'expected 2 implemented, got {len(implemented)}'
assert len(open_) == 4, f'expected 4 open, got {len(open_)}'
ids_imp = sorted(x['id'] for x in implemented)
assert ids_imp == ['D-2026-05-09-03', 'D-2026-05-09-06'], ids_imp
print('OK', f'{len(implemented)} implemented, {len(open_)} open')
"`
Expected: `OK 2 implemented, 4 open`.

Run: `grep -c "D-028" /Users/ekimir/swprj/legalize-bg/docs/sync/DECISIONS.md /Users/ekimir/swprj/legalize-bg/docs/sync/DEFERRED.md /Users/ekimir/swprj/legalize-bg/docs/sync/ACTIVE.md`
Expected: D-028 appears in DECISIONS.md (multiple times — heading + cross-references) and DEFERRED.md (in the Resolution note column).

- [ ] **Step 6: Final full test run.**

Run: `.venv/bin/pytest -q 2>&1 | tail -3`
Expected: 244 passed (no behavioral change in this batch).

- [ ] **Step 7: Commit Batch F.**

```bash
git add docs/sync/DEFERRED.md docs/sync/ACTIVE.md docs/sync/DECISIONS.md .ahelia/protected-surfaces.yaml
git commit -m "$(cat <<'EOF'
docs(sync): close Phase 1b.2 — D-2026-05-09-03 + -06 → implemented; D-028 logged

Phase 1b.2 closeout commit:

- DEFERRED.md: D-2026-05-09-03 (FR-016 perf) and D-2026-05-09-06
  (D-027 hard-promote) move from Active to Resolved with Resolution
  notes pointing at D-028. Other four deferrals (FR-013/14/15/17)
  stay Open per their 1b.3 / Phase-4 targets.

- ACTIVE.md: new "Phase 1b.2 — complete on main" section listing the
  four deliverables (QUERY_TOO_BROAD reject, hard perf budgets,
  tools.json publication, error-taxonomy formalization) plus
  idempotency-contract documentation. Pending list updated.

- DECISIONS.md: D-028 captures the design choices made for Phase 1b.2
  closure — stop-word reject over BM25 pushdown, code-as-source-of-
  truth for tools.json, double-publish error catalog (md + json),
  cold-call as a separate test file, idempotency as documentation
  not runtime assertion.

- .ahelia/protected-surfaces.yaml: deferrals block flips two entries
  from status: open → status: implemented with resolution_note tags
  pointing at D-028. last_synced bumped.

Test count holds at 244 (this batch is doc-only).

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

- [ ] **Step 8: Final commit chain check.**

Run: `git log --oneline a33a70ab..HEAD`
Expected: 5 commits (1 per Batch A through F, except A and B each had 2-3 tasks combined into one commit each: A=Task 2's commit, B=Task 5's commit, C=Task 9's commit, D=Task 13's commit, E=Task 14's commit, F=Task 15's commit).

Also commit the plan file itself:

```bash
git add docs/plans/2026-05-09-phase1b2-hardening.md
git commit -m "$(cat <<'EOF'
docs(plan): Phase 1b.2 hardening implementation plan

Plan covering the four Phase 1b.2 deliverables (FR-016 reject, D-027
hard perf, tools.json publication, error-taxonomy formalization) plus
the design doc's idempotency-contract documentation line item. Six
batches; 15 tasks; ~25 minutes total execution time.

Pre-recorded empirical evidence: FR-016 cold-call survey showing
"наредба" hits 437 ms p95 on cold cache (vs 33 ms steady-state), and
the FastMCP tool-schema introspection pattern that drives the
tools.json export script. Risk register documents the SQLite-version
drift mitigation already built into the regression tests.

Plan was written and self-reviewed before execution.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Definition of Done

- [ ] **Batch A:** `mcp_server/errors.py` adds `QUERY_TOO_BROAD`; `mcp_server/queries.py` rejects single-word category queries before FTS5; 10 new tests in `tests/mcp_server/test_search.py` cover the reject + the non-rejected paths.
- [ ] **Batch B:** `tests/perf/test_budgets.py` uses `pytest.fail` on regression; new `tests/perf/test_cold_calls.py` exercises the cold-cache case with fresh-connection-per-query; both modules pass twice in succession.
- [ ] **Batch C:** `mcp_server/export_tools.py` introspects FastMCP and emits `tools.json` (version 1.0.0); committed `tools.json` matches the live schemas (CI parity test in `tests/mcp_server/test_export_tools.py`); `search` docstring documents `QUERY_TOO_BROAD`.
- [ ] **Batch D:** `docs/api/error-codes.md` lists all 9 codes with payload shapes; `docs/api/error-codes.json` is the machine-readable mirror; 4 parity tests in `tests/mcp_server/test_error_codes_doc.py`; runbook cross-links the new artifacts.
- [ ] **Batch E:** Runbook has an "Idempotency contract" section between "Server runtime" and "Tools surfaced".
- [ ] **Batch F:** `DEFERRED.md` Resolved table contains 2 rows; `ACTIVE.md` shows Phase 1b.2 complete; `DECISIONS.md` D-028 logged; `.ahelia/protected-surfaces.yaml` deferrals block has 2 implemented + 4 open.
- [ ] **Test suite:** **244 passing** (221 baseline + 10 from Batch A + 3 from Batch B + 6 from Batch C + 4 from Batch D = 244).
- [ ] **No new schema migrations.**
- [ ] **No changes to `bg_normalize`, `provisions` extraction, or `get_law` / `get_article` response shapes** (Surfaces 3 and 6 untouched in their structural sense; Surface 3 sees only the additive new error code).
- [ ] **Each task batch commits as its own commit** (6 commits) plus a 7th for the plan file.

---

## Risk register

| Risk | Mitigation |
|---|---|
| The 5-stop-word list might over-reject in practice (e.g., a future legitimate single-word search). | The list is small and well-bounded (the 5 Bulgarian rang words). If a 6th legitimate single-word category appears (hypothetical: a future municipal-tier word), an FR can extend the list; the test pattern will lock the new word. |
| Cold-call test (`test_cold_calls.py`) might be flaky on slow CI hosts (FTS5 cache not the only OS-cache state). | The 100ms / 50ms budgets have ~2× headroom against the measured numbers (33ms/0.5ms steady-state); a 5× slower CI host still passes. If CI flakes appear, add a `pytest-rerunfailures` marker rather than relaxing the budget. |
| `mcp_server/export_tools.py` builds a transient `:memory:` DB that doesn't have any tables — `app.mcp.list_tools()` may surprisingly need them. | Verified empirically in plan-write: `app.mcp.list_tools()` only inspects the registered tool decorators, never queries the DB. The `:memory:` connection is a placeholder for the factory pattern. |
| `tools.json` formatting (key order, indentation, line endings) might differ between local and CI Python versions, breaking the `--check` parity. | `json.dumps(..., indent=2, ensure_ascii=False) + "\n"` is deterministic across Python 3.11/3.12. The newline-at-EOF avoids the only remaining cross-platform divergence (Windows CRLF, but git's `core.autocrlf=false` is the project default). |
| The error-codes.json structure puts data inside a `data` key alongside the JSON Schema — confusing nesting. | Acknowledged tradeoff: the file serves as both the schema and the data, which is non-standard but documented in the comment block at the top. Cleaner alternative (separate `error-codes.schema.json` and `error-codes.data.json`) is over-engineering for 9 codes; the current format is good enough for 1b.2 and can be split when the catalog grows. |
| ACTIVE.md gets longer with every phase milestone. | Future `1b.3` and beyond can fold the milestone bullets into a per-phase summary table at the top of the file. Not a blocker for 1b.2; tracked separately if needed. |

---

## Out-of-scope (re-stated)

- `_run_match` / `resolve_name_to_law_id` allowlist consolidation (Round-3 limitation note).
- BM25 + LIMIT pushdown (alternative FR-016 approach).
- Phase 1b.3 deliverables (FR-013, FR-014, FR-015, FR-017).
- Telemetry, structured logging, packaging.
- Schema migration v5+ (no schema changes in this plan).

## Self-review notes

Walked back through the plan once after writing. Spec coverage check:
- FR-016 fix (Batch A) ✓
- D-027 hard promotion (Batch B) ✓
- `tools.json` (Batch C) ✓
- Error taxonomy formalized (Batch D) ✓
- Idempotency documented (Batch E) ✓
- Deferral resolution + DECISIONS log (Batch F) ✓

Placeholder scan: no "TBD", no "implement later", no unresolved FR references. The script-as-source-of-truth pattern (Batch C) and the parity tests (Batches C + D) are explicit.

Type / identifier consistency:
- `QUERY_TOO_BROAD` used uniformly across `mcp_server/errors.py`, `mcp_server/queries.py`, tests, docs, json.
- `_CATEGORY_STOP_WORDS` is a `frozenset`; tests check it as a set.
- `TOOLS_JSON_VERSION = "1.0.0"` is the single source; both md and json carry the same string.
- `_hard_assert` replaces `_soft_assert` in `test_budgets.py` AND is independently defined in `test_cold_calls.py` (deliberate duplication noted in the cold-call file's docstring).

No gaps found. Plan ready for execution.
