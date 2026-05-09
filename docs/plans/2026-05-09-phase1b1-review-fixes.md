# Phase 1b.1 — Review-Findings Repair Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Apply the 5 Important findings + 4 Minor findings from the code review of commits `0433ed95..76dc9c4c` (Phase 1b.1 audit-gaps implementation), producing a publication-ready Phase 1b.1 docs/code surface with no known doc/code drift and no FTS5 user-input regressions.

**Architecture:** Six tasks across one code change (Task 1 — `_run_match` allowlist + parameterized regression), four documentation corrections (Tasks 2–5 — schema-reference Migration 2 columns, schema-reference `date_uncertain` NOT NULL, runtime-flows §6.3.4 inclusive-`valid_to`, delivery-contract Session Model adds DEFERRED.md), and one publication-readiness sweep (Task 6 — Minor findings + final test/parse/lint sweep + ACTIVE.md milestone). All changes are additive or correctional; no architectural shifts. D-024 / D-026 / D-027 remain binding; Surfaces 3 and 6 stay untouched.

**Tech Stack:** Python 3.11+, SQLite3 (FTS5), FastMCP, pytest, PyYAML, Markdown docs. Test runner: `.venv/bin/pytest`. YAML parse check: `.venv/bin/python -c "import yaml; yaml.safe_load(open('<path>'))"`.

---

## Out of scope

- Restructuring the duplicate session-startup-protocol lists (`.claude/CLAUDE.md` step list vs `delivery-contract.md` step list) into a single source of truth — flagged as Recommendation #4 by the reviewer; deeper-than-mechanical-fix; defer to a separate plan if approved.
- Consolidating the `_run_match`/`resolve_name_to_law_id` allowlists into a shared module-level tuple — Recommendation #3; touches both `index/fts.py` and `mcp_server/queries.py` and is best done as a separate small refactor with its own tests.
- Implementing any D-2..D-7 deferral (FR-013/14/15/16/17 + 1b.2 perf-budget hardening) — already Out-of-scope for the audit-gaps plan and stays out-of-scope here.

---

## Assumptions

- Working tree starts clean on `main` at HEAD = `76dc9c4c`. (Confirm with `git status --short` returning empty.)
- Test baseline is **216 passing** (212 original + 4 new from Batch 5).
- `.venv` exists and is editable-installed (`pip install -e ".[dev]"` already run).
- The 5 Important issues from the review are accepted as-stated (verified empirically — see "Empirical evidence" below). If any look wrong during execution, stop and consult.

## Empirical evidence (for Task 1 — pre-recorded)

Survey of FTS5 user-input error families against the same `_run_match` invocation (in-memory db, both `laws` and `laws_fts` created):

| Input | Result | Error message (lower-cased) |
|---|---|---|
| `'*'` | RAISED before narrowing | `unknown special query: ` |
| `'"foo'` | RAISED before narrowing | `unterminated string` |
| `'foo"bar'` | RAISED before narrowing | `unterminated string` |
| `'"unbalanced'` | RAISED before narrowing | `unterminated string` |
| `'"empty""'` | RAISED before narrowing | `unterminated string` |
| `'x:badcolumn'` | RAISED before narrowing | `no such column: x` |
| `'a OR'` | returned `[]` (no raise) | (no error) |
| `'(unbalanced'` | returned `[]` (no raise) | (no error) |
| `'*foo*'` | returned `[]` (no raise) | (no error) |
| `'NEAR('` | returned `[]` (no raise) | (no error) |
| `'AND'` | returned `[]` (no raise) | (no error) |
| `''` (empty) | returned `[]` (no raise) | (no error) |

Conclusion: three error-message families need to be in the allowlist:
1. `"unknown special query"` — already added in Batch 5
2. `"unterminated string"` — **missing** (covers all unbalanced-quote inputs)
3. `"no such column"` — **missing** (covers invalid column qualifier `x:bad`)

The `"fts5"` and `"syntax error"` substrings from the queries.py sibling pattern remain in the allowlist as belt-and-suspenders — some FTS5 builds may produce messages prefixed with `"fts5: ..."` even for the cases above.

The `"no such table"` error (the corrupt-index propagation contract from D-8) remains OUT of the allowlist — it must propagate.

---

## File Structure

```
index/fts.py                              # MODIFY (Task 1): broaden _run_match allowlist
tests/index/test_fts.py                   # MODIFY (Task 1): replace single-input test with parameterized + add propagation cases
docs/data/schema-reference.md             # MODIFY (Tasks 2, 3): fix Migration 2 columns + date_uncertain NOT NULL
docs/architecture/runtime-flows.md        # MODIFY (Task 4): §6.3.4 valid_to > → valid_to >=
docs/process/delivery-contract.md         # MODIFY (Task 5): Session Model adds DEFERRED.md
docs/sync/DEFERRED.md                     # MODIFY (Task 6): add Resolved-deferrals row template
docs/data/canonical-data-model.md         # MODIFY (Task 6, optional): tighten §7.5 wording if function-name spot-check fails
docs/runbook/2026-05-09-phase1b1-operator-setup.md  # MODIFY (Task 6): one-line note on laws.title vs frontmatter titulo for the smoke-test pin
docs/sync/ACTIVE.md                       # MODIFY (Task 6): add milestone line for the review-fixes commit
```

No new files. No code-architecture changes. Single code edit (Task 1).

---

## BATCH A — Code regression fix (Task 1)

### Task 1: Broaden `_run_match` FTS5 user-input allowlist + parameterize regression

**Audit of regression:** review Issue #1 — the Batch 5 narrowing locked the allowlist at `"fts5" / "syntax error" / "unknown special query"`, missing the `"unterminated string"` and `"no such column"` families. Quote-typo searches like `обществени "поръчки` now reach `_run_match` and propagate as unhandled `OperationalError` to the MCP `search` tool. Pre-narrowing, all such inputs returned `[]`.

**Files:**
- Modify: `index/fts.py` (function `_run_match`, the `except sqlite3.OperationalError as e:` block — currently lines ~132–145 after Batch 5)
- Modify: `tests/index/test_fts.py` (replace `test_run_match_swallows_fts5_syntax_errors` with a parameterized variant; keep `test_run_match_does_not_swallow_corrupt_index_errors` intact)

- [ ] **Step 1: Read the current state to confirm baseline.**

Run: `grep -n "is_user_input_error\|fts5.*in msg\|unknown special query" /Users/ekimir/swprj/legalize-bg/index/fts.py`
Expected: hits at lines 142, 148–151 (the current allowlist).

Run: `grep -n "test_run_match_swallows\|test_run_match_does_not_swallow" /Users/ekimir/swprj/legalize-bg/tests/index/test_fts.py`
Expected: two test names, the swallowing one currently exercises only `*`.

- [ ] **Step 2: Replace the swallowing test with a parameterized version.**

In `tests/index/test_fts.py`, find the test:

```python
def test_run_match_swallows_fts5_syntax_errors():
    """A query with FTS5-special syntax (lone '*', unbalanced quote) must
    return [] rather than raise — both the resolver and search depend on
    this fallback so callers don't see FTS5 syntax errors from raw user
    input."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute(_LAWS_DDL)
    create_laws_fts_table(conn)
    # FTS5 emits "unknown special query: " for lone '*'. Must be
    # swallowed; result is empty list.
    assert _run_match(conn, "*", category=None, limit=20) == []
```

Replace it with:

```python
@pytest.mark.parametrize(
    "user_input,error_family",
    [
        ("*", "unknown special query"),
        ('"foo', "unterminated string"),
        ('foo"bar', "unterminated string"),
        ('"unbalanced', "unterminated string"),
        ('"empty""', "unterminated string"),
        ("x:badcolumn", "no such column"),
    ],
    ids=[
        "lone-asterisk",
        "leading-quote",
        "embedded-quote",
        "unbalanced-quote",
        "doubled-trailing-quote",
        "invalid-column-qualifier",
    ],
)
def test_run_match_swallows_fts5_user_input_errors(user_input, error_family):
    """FTS5 raises OperationalError for malformed query terms — three
    error-message families verified empirically (see plan
    `2026-05-09-phase1b1-review-fixes.md`):

      - "unknown special query: "  (lone '*')
      - "unterminated string"      (any unbalanced quote)
      - "no such column: ..."      (invalid column qualifier)

    All must be swallowed (return []) so user typos in `search` don't
    surface as 500-equivalent errors. The resolver and search both depend
    on this fallback. The error_family arg is a sanity check that the
    test inputs are actually reaching the path under test (audit D-8 +
    review Issue #1)."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute(_LAWS_DDL)
    create_laws_fts_table(conn)
    # Sanity: confirm the input genuinely produces the expected family
    # at the SQLite layer (so a future SQLite version that changes the
    # message family causes a single, focused test failure rather than
    # silent allowlist drift).
    try:
        conn.execute(
            "SELECT 1 FROM laws_fts WHERE laws_fts MATCH ?", [user_input]
        ).fetchone()
    except sqlite3.OperationalError as e:
        assert error_family in str(e).lower(), (
            f"input {user_input!r}: expected error family containing "
            f"{error_family!r}, got {str(e)!r}. SQLite/FTS5 may have "
            f"changed its error wording — update the allowlist in "
            f"index/fts.py:_run_match accordingly."
        )
    # The actual contract: _run_match must return [] for all three families.
    assert _run_match(conn, user_input, category=None, limit=20) == []
```

- [ ] **Step 3: Run the parameterized test to confirm it FAILS at the unterminated-string and no-such-column branches (RED step).**

Run: `.venv/bin/pytest -q tests/index/test_fts.py::test_run_match_swallows_fts5_user_input_errors 2>&1 | tail -15`

Expected: 1 passes (lone-asterisk — already in allowlist), 5 fail with `OperationalError: unterminated string` / `no such column: x`. The lone-asterisk parametrization stays green; the other five are the regression we're fixing.

- [ ] **Step 4: Broaden the allowlist in `index/fts.py:_run_match`.**

Find the existing block:

```python
    try:
        return conn.execute(sql, params).fetchall()
    except sqlite3.OperationalError as e:
        # FTS5 raises OperationalError for malformed query terms — the
        # user-input error families we suppress are:
        #   - "fts5: syntax error near ..."         (unbalanced quotes etc.)
        #   - "unknown special query: ..."          (lone '*' / bareword)
        #   - "syntax error"                        (generic FTS5 syntax)
        # Suppress those — the user gave us a string FTS5 can't tokenize,
        # so treat as no results. Other OperationalErrors (table missing,
        # DB locked, disk full, corruption) must propagate so callers
        # see INDEX_STALE / INDEX_MISSING instead of silent empty results
        # (audit D-8). Mirrors mcp_server.queries.resolve_name_to_law_id
        # in spirit; broadened to include the "unknown special query"
        # family that the resolver's path doesn't hit.
        msg = str(e).lower()
        is_user_input_error = (
            "fts5" in msg
            or "syntax error" in msg
            or "unknown special query" in msg
        )
        if not is_user_input_error:
            raise
        return []
```

Replace with:

```python
    try:
        return conn.execute(sql, params).fetchall()
    except sqlite3.OperationalError as e:
        # FTS5 raises OperationalError for malformed query terms — three
        # user-input error families verified empirically (see plan
        # docs/plans/2026-05-09-phase1b1-review-fixes.md, Task 1) plus
        # the historic "fts5"/"syntax error" prefixes some SQLite builds
        # emit:
        #   - "unknown special query: "              (lone '*' / bareword)
        #   - "unterminated string"                  (any unbalanced quote)
        #   - "no such column: ..."                  (invalid x:foo column qualifier)
        #   - "fts5: ..." / "syntax error"           (build-specific prefixes)
        # Suppress those — the user gave us a string FTS5 can't tokenize,
        # so treat as no results. Other OperationalErrors (table missing,
        # DB locked, disk full, corruption) must propagate so callers
        # see INDEX_STALE / INDEX_MISSING instead of silent empty
        # results (audit D-8 + review Issue #1). Mirrors
        # mcp_server.queries.resolve_name_to_law_id in spirit;
        # consolidating the two allowlists into a shared tuple is
        # tracked separately.
        msg = str(e).lower()
        is_user_input_error = (
            "fts5" in msg
            or "syntax error" in msg
            or "unknown special query" in msg
            or "unterminated string" in msg
            or msg.startswith("no such column")
        )
        if not is_user_input_error:
            raise
        return []
```

The `startswith("no such column")` (instead of `in msg`) is deliberate: it locks the suppression to *exactly* the FTS5 column-qualifier case and won't accidentally swallow a future error that happens to mention "no such column" in a different position (e.g., `"corrupt: no such column in shadow row"` — hypothetical but illustrates why bounded matching is safer for non-prefix messages).

- [ ] **Step 5: Re-run the parameterized test to confirm it now PASSES (GREEN step).**

Run: `.venv/bin/pytest -q tests/index/test_fts.py::test_run_match_swallows_fts5_user_input_errors 2>&1 | tail -5`

Expected: 6 passed (one per parametrization).

- [ ] **Step 6: Run the propagation contract test to confirm it still PASSES (regression guard).**

Run: `.venv/bin/pytest -q tests/index/test_fts.py::test_run_match_does_not_swallow_corrupt_index_errors 2>&1 | tail -3`

Expected: 1 passed. (No `laws_fts` table → "no such table: laws_fts" → not in allowlist → propagates.)

- [ ] **Step 7: Run the full FTS test surface to confirm no other regression.**

Run: `.venv/bin/pytest -q tests/index/test_fts.py tests/index/test_fts_regression.py 2>&1 | tail -3`

Expected: ~22 passed (15 original FTS unit tests + 1 propagation test + 6 parametrizations of the new user-input test + the existing FTS regression suite).

- [ ] **Step 8: Run the full test suite.**

Run: `.venv/bin/pytest -q 2>&1 | tail -3`

Expected: 221 passed (216 baseline − 1 replaced single-input test + 6 new parametrizations = 221). If the count is off by more than ±1, stop and investigate before committing.

- [ ] **Step 9: Commit.**

```bash
git add index/fts.py tests/index/test_fts.py
git commit -m "$(cat <<'EOF'
fix(fts): broaden _run_match allowlist to cover all FTS5 user-input families

Review Issue #1 (Important): the Batch 5 narrowing of _run_match's
OperationalError catch missed two user-input error families that the
audit explicitly named as suppression cases:

  - "unterminated string"    (unbalanced quotes, e.g. 'обществени "поръчки')
  - "no such column: x"      (invalid column qualifier, e.g. 'x:foo')

Pre-narrowing these returned []; post-narrowing they propagated as
unhandled OperationalError into the MCP `search` tool. A user typo
became a 500-equivalent.

Empirically surveyed FTS5 user-input cases (lone '*', leading quote,
embedded quote, unbalanced quote, doubled trailing quote, invalid
column qualifier) and locked all three error families into a
parameterized regression test. The corrupt-index propagation contract
(no-such-table → must raise) is preserved — its dedicated test stays
green.

Test count: 216 → 221 (replaced 1 single-input test with 6
parametrizations of test_run_match_swallows_fts5_user_input_errors).

The narrower `startswith("no such column")` instead of `in msg` locks
suppression to FTS5's column-qualifier prefix specifically; future
errors that contain "no such column" in a non-prefix position will
propagate, preserving the propagation contract.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## BATCH B — Documentation drift introduced in Batch 2 (Tasks 2, 3)

### Task 2: Fix `schema-reference.md` Migration 2 row — `laws_fts` has 4 columns, not 5

**Audit of regression:** review Issue #2 — Batch 2 added a Section 3 Migration 2 row claiming `laws_fts` has 5 columns including `identificador UNINDEXED`. Actual `index/fts.py:create_laws_fts_table` and `index/migrations.py` Migration 2 SQL define **4** columns: `law_id UNINDEXED, title, body, category UNINDEXED`. The trailing prose ("`law_id` / `identificador` / `category` ride along as filters") amplifies the error.

**Files:**
- Modify: `docs/data/schema-reference.md` (the Migration 2 row in Section 3 + the trailing prose)

- [ ] **Step 1: Verify the discrepancy.**

Run: `grep -n "laws_fts USING fts5\|identificador UNINDEXED" /Users/ekimir/swprj/legalize-bg/docs/data/schema-reference.md /Users/ekimir/swprj/legalize-bg/index/fts.py /Users/ekimir/swprj/legalize-bg/index/migrations.py`

Expected:
- `docs/data/schema-reference.md`: line ~229 has `law_id UNINDEXED, identificador UNINDEXED, title, body, category UNINDEXED` (the wrong 5-column shape).
- `index/fts.py`: lines 81–87 have `law_id UNINDEXED, title, body, category UNINDEXED` (the actual 4-column shape).
- `index/migrations.py`: Migration 2 SQL block matches `index/fts.py`.

- [ ] **Step 2: Make the change.**

In `docs/data/schema-reference.md`, find the Migration 2 row (under `### Shipped migrations (Phase 1b.1)`):

```
| 2 | `laws_fts_virtual_table` | `CREATE VIRTUAL TABLE laws_fts USING fts5(law_id UNINDEXED, identificador UNINDEXED, title, body, category UNINDEXED, tokenize='unicode61 remove_diacritics 2')` | D-022 — FTS5 with the `unicode61 remove_diacritics 2` tokenizer is the chosen Bulgarian-search backend. `title` and `body` are indexed; `law_id` / `identificador` / `category` ride along as filters. |
```

Replace with:

```
| 2 | `laws_fts_virtual_table` | `CREATE VIRTUAL TABLE laws_fts USING fts5(law_id UNINDEXED, title, body, category UNINDEXED, tokenize='unicode61 remove_diacritics 2')` | D-022 — FTS5 with the `unicode61 remove_diacritics 2` tokenizer is the chosen Bulgarian-search backend. `title` and `body` are indexed; `law_id` and `category` ride along as filters/UNINDEXED metadata. The `identificador` is NOT in `laws_fts` — it lives only on `laws.doc_id` and reaches search results via the JOIN in `_FTS_SELECT`. |
```

Three changes: (a) drop `identificador UNINDEXED` from the DDL; (b) drop `identificador` from the prose's "ride along" list; (c) add a clarifying sentence so readers understand where `identificador` actually lives — this is the kind of clarification that prevents the same drift from sneaking back next time.

- [ ] **Step 3: Verify the change landed and matches code.**

Run: `grep -n "identificador UNINDEXED" /Users/ekimir/swprj/legalize-bg/docs/data/schema-reference.md`

Expected: 0 hits.

Run: `grep -n "law_id UNINDEXED, title, body, category UNINDEXED" /Users/ekimir/swprj/legalize-bg/docs/data/schema-reference.md`

Expected: 1 hit (the corrected Migration 2 row).

Run: `.venv/bin/python -c "
from index.fts import create_laws_fts_table
import sqlite3
conn = sqlite3.connect(':memory:')
create_laws_fts_table(conn)
# Confirm shape: laws_fts has exactly 4 columns
cols = [r[1] for r in conn.execute('PRAGMA table_info(laws_fts)').fetchall()]
assert cols == ['law_id', 'title', 'body', 'category'], f'unexpected columns: {cols}'
print('OK — 4 columns:', cols)
"`

Expected: `OK — 4 columns: ['law_id', 'title', 'body', 'category']`. Confirms the doc now matches code.

- [ ] **Step 4: Stage but do not commit yet.** Task 3 modifies the same file; one combined commit at the end of Task 3.

```bash
git add docs/data/schema-reference.md
```

### Task 3: Fix `schema-reference.md` `date_uncertain` — `NOT NULL DEFAULT 0`, not `Nullable, default 0`

**Audit of regression:** review Issue #3 — Batch 2 documented `law_versions.date_uncertain` as `Nullable, default 0` in three places (DDL comment, column row description, Migration 4 effect). Actual SQL in `index/migrations.py:65-68` is `NOT NULL DEFAULT 0`.

**Files:**
- Modify: `docs/data/schema-reference.md` (three locations — DDL block, column-row table, Migration 4 row)

- [ ] **Step 1: Verify the discrepancy.**

Run: `grep -n "date_uncertain INTEGER\|date_uncertain.*Nullable\|date_uncertain.*NOT NULL" /Users/ekimir/swprj/legalize-bg/docs/data/schema-reference.md /Users/ekimir/swprj/legalize-bg/index/migrations.py`

Expected:
- `docs/data/schema-reference.md`: 3 mentions, all variants of `Nullable` / `DEFAULT 0` (no `NOT NULL`).
- `index/migrations.py:66-67`: `INTEGER NOT NULL DEFAULT 0`.

- [ ] **Step 2: Fix the DDL comment in the law_versions Section 2 block.**

Find:

```sql
    date_uncertain INTEGER DEFAULT 0  -- added by Migration 004
```

Replace with:

```sql
    date_uncertain INTEGER NOT NULL DEFAULT 0  -- added by Migration 004
```

- [ ] **Step 3: Fix the column-row description in the law_versions table.**

Find:

```
| `date_uncertain` | INTEGER | Nullable, default 0 (0/1 boolean) | §7.2 marker: 1 when `fecha_publicacion` was null at index time and `valid_from` fell back to the bootstrap-run date. Read by `mcp_server/queries.py:version_with_warnings` to attach a `DATE_UNCERTAIN` warning to every response. Added by Migration 004. |
```

Replace with:

```
| `date_uncertain` | INTEGER | NOT NULL, default 0 (0/1 boolean) | §7.2 marker: 1 when `fecha_publicacion` was null at index time and `valid_from` fell back to the bootstrap-run date. Read by `mcp_server/queries.py:version_with_warnings` to attach a `DATE_UNCERTAIN` warning to every response. Added by Migration 004. |
```

- [ ] **Step 4: Fix the Migration 4 row in Section 3.**

Find:

```
| 4 | `law_versions_date_uncertain_column` | `ALTER TABLE law_versions ADD COLUMN date_uncertain INTEGER DEFAULT 0;` | §7.2 surfacing — when `fecha_publicacion` is null, the indexer falls back to bootstrap-run date and sets `date_uncertain=1` so `version_with_warnings` can attach a `DATE_UNCERTAIN` warning rather than silently emit a fabricated date. |
```

Replace with:

```
| 4 | `law_versions_date_uncertain_column` | `ALTER TABLE law_versions ADD COLUMN date_uncertain INTEGER NOT NULL DEFAULT 0;` | §7.2 surfacing — when `fecha_publicacion` is null, the indexer falls back to bootstrap-run date and sets `date_uncertain=1` so `version_with_warnings` can attach a `DATE_UNCERTAIN` warning rather than silently emit a fabricated date. The NOT NULL constraint pairs with DEFAULT 0 so existing rows get the safe-default value at migration time and new rows are forced to declare a value. |
```

- [ ] **Step 5: Verify all three locations now say `NOT NULL`.**

Run: `grep -n "date_uncertain" /Users/ekimir/swprj/legalize-bg/docs/data/schema-reference.md`

Expected: 3+ hits, every `date_uncertain` mention now followed (within the same line or adjacent context) by `NOT NULL`.

Run: `grep -c "date_uncertain.*Nullable" /Users/ekimir/swprj/legalize-bg/docs/data/schema-reference.md`

Expected: 0 (no `Nullable` mentions of `date_uncertain` remain).

- [ ] **Step 6: Verify against actual SQL.**

Run: `.venv/bin/python -c "
import sqlite3
from index import migrations
conn = sqlite3.connect(':memory:')
# Apply just the law_versions table + Migration 4
conn.execute('CREATE TABLE law_versions (id INTEGER PRIMARY KEY, law_id TEXT, valid_from DATE NOT NULL, valid_to DATE, commit_hash TEXT NOT NULL, dv_issue TEXT, dv_date DATE, amending_act TEXT)')
migrations.migrate(conn)
info = conn.execute('PRAGMA table_info(law_versions)').fetchall()
date_unc = [r for r in info if r[1] == 'date_uncertain']
assert date_unc, 'date_uncertain column missing'
# (cid, name, type, notnull, dflt_value, pk)
assert date_unc[0][3] == 1, f'date_uncertain should be NOT NULL (notnull=1), got {date_unc[0][3]}'
assert date_unc[0][4] == '0', f'date_uncertain default should be 0, got {date_unc[0][4]!r}'
print('OK — date_uncertain is NOT NULL DEFAULT 0:', date_unc[0])
"`

Expected: `OK — date_uncertain is NOT NULL DEFAULT 0: ...`. Confirms the doc now matches the live constraint.

- [ ] **Step 7: Commit Tasks 2 + 3 together.**

```bash
git add docs/data/schema-reference.md
git commit -m "$(cat <<'EOF'
docs(schema-reference): fix laws_fts column count + date_uncertain constraint

Review Issues #2 and #3 (Important): Batch 2 introduced documentation
drift on the very file it was supposed to align — the audit-fix
re-introduced doc/code mismatches.

Issue #2 — Migration 2 row claimed laws_fts has 5 columns including
`identificador UNINDEXED`. Actual: 4 columns (law_id, title, body,
category). The trailing prose amplified the error by listing
identificador in the "ride along" set. Corrected the DDL and added a
clarifying sentence: identificador lives on laws.doc_id, reaches search
results via the JOIN in _FTS_SELECT, not via the FTS table itself.

Issue #3 — date_uncertain documented as "Nullable, default 0" in three
places (DDL comment, column row, Migration 4). Actual SQL in
index/migrations.py:67 is `INTEGER NOT NULL DEFAULT 0`. Corrected all
three locations and added a one-line note on why the NOT NULL pairs
with DEFAULT 0 (safe migration of existing rows + forces new rows to
declare).

Both issues verified against runtime: PRAGMA table_info confirms
laws_fts has exactly 4 columns and law_versions.date_uncertain is
notnull=1, dflt_value='0'.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## BATCH C — runtime-flows §6.3.4 inclusive-`valid_to` (Task 4)

### Task 4: Fix `runtime-flows.md` §6.3.4 ASCII — `valid_to > date` → `valid_to >= date`

**Audit of regression:** review Issue #4 — `runtime-flows.md` §6.3.4 (the `get_article` flow diagram) shows `OR valid_to > date)` (strict `>`). Inconsistent with §6.3.3 (which Batch 3 fixed), `mcp_server/queries.py:article_lookup` (which uses `>=`), and the Predicate semantics paragraph in `schema-reference.md` §2 added by Batch 2. Pre-existing drift not on the audit list, but Batch 3 touched the immediate neighbor without noticing.

**Files:**
- Modify: `docs/architecture/runtime-flows.md` (single line, around line 274)

- [ ] **Step 1: Verify the discrepancy.**

Run: `grep -n "valid_to > date\|valid_to >= date" /Users/ekimir/swprj/legalize-bg/docs/architecture/runtime-flows.md /Users/ekimir/swprj/legalize-bg/mcp_server/queries.py`

Expected:
- `runtime-flows.md`: 1 hit at line ~274 with `valid_to > date` (strict).
- `mcp_server/queries.py`: 2 hits with `valid_to >= ?` (inclusive — what the code actually does).

- [ ] **Step 2: Make the change.**

Find:

```
     |                     |     AND (valid_to IS NULL    |
     |                     |          OR valid_to > date) |
```

Replace with:

```
     |                     |     AND (valid_to IS NULL    |
     |                     |          OR valid_to >= date) |
```

(Single character: `>` → `>=`. Preserve trailing spaces and column alignment of the ASCII diagram — the closing `|` should still land at the same column.)

- [ ] **Step 3: Add a one-line forward reference under the diagram.**

Locate the section heading `### 6.3.4 `get_article(law, article, date=None)`` and the prose paragraph that follows the ASCII diagram. After the existing prose (or in a new line directly after the diagram closes), add:

```
**Inclusive `valid_to`.** The `>=` in the WHERE clause is intentional — see `docs/data/schema-reference.md` §2 ("Predicate semantics") for the in-force predicate definition. A version with `valid_to = '2020-12-31'` is in force ON 2020-12-31; using `>` would silently exclude the boundary day.
```

This duplicates the predicate sentence from `schema-reference.md` §2 *deliberately* — diagrams are read in isolation, and a one-character drift like `>` vs `>=` is exactly the kind of doc/code mismatch the audit flagged.

- [ ] **Step 4: Verify both changes landed.**

Run: `grep -n "valid_to >\|Inclusive .valid_to" /Users/ekimir/swprj/legalize-bg/docs/architecture/runtime-flows.md`

Expected: the strict `>` line is now `>=`; the new "Inclusive `valid_to`." paragraph is present.

Run: `grep -c "valid_to > date" /Users/ekimir/swprj/legalize-bg/docs/architecture/runtime-flows.md`

Expected: 0.

- [ ] **Step 5: Commit.**

```bash
git add docs/architecture/runtime-flows.md
git commit -m "$(cat <<'EOF'
docs(runtime-flows): §6.3.4 valid_to > → valid_to >= (inclusive predicate)

Review Issue #4 (Important): the get_article flow diagram in §6.3.4
showed the strict `valid_to > date` predicate while the rest of the
codebase (queries.py, schema-reference §2 Predicate semantics, §6.3.3
search diagram, container-view §7) was uniformly aligned on the
inclusive `valid_to >= date` semantic.

Pre-existing drift on the same audit-A-4 theme; Batch 3 fixed the
immediate neighbor (§6.3.3) but missed §6.3.4. A reader cross-
referencing the new schema-reference §2 with this section would have
seen an explicit `>` vs `>=` contradiction.

Single-character fix in the ASCII; added a one-line "Inclusive
valid_to" paragraph below the diagram so the rationale rides with the
diagram (diagrams are often read in isolation; the paragraph guards
against a future copy-paste that would re-introduce the strict form).

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## BATCH D — delivery-contract Session Model adds DEFERRED.md (Task 5)

### Task 5: Add DEFERRED.md to `delivery-contract.md` Session Model

**Audit of regression:** review Issue #5 — `delivery-contract.md:11-19` has its own Session Model startup-protocol list (separate from `.claude/CLAUDE.md`'s, which Batch 7 did update). The two lists now contradict on the read path. Per `.claude/CLAUDE.md`'s own Authority Surfaces ordering, `delivery-contract.md` is a *higher-precedence* authority document, so the gap matters more than it would for an arbitrary doc.

**Files:**
- Modify: `docs/process/delivery-contract.md` (Session Model lines ~11–19)

- [ ] **Step 1: Verify the gap.**

Run: `grep -n "DEFERRED.md" /Users/ekimir/swprj/legalize-bg/.claude/CLAUDE.md /Users/ekimir/swprj/legalize-bg/docs/process/delivery-contract.md`

Expected:
- `.claude/CLAUDE.md`: 1 hit (Batch 7 wired step 3).
- `delivery-contract.md`: 0 hits in the Session Model (the phase-promotion gate Batch 7 added is further down in the Definition of Done section).

- [ ] **Step 2: Make the change.**

Find the Session Model block:

```
Claude Code sessions work against this repo with the following startup protocol:

1. Read `.claude/CLAUDE.md` for repo-specific instructions
2. Read `docs/sync/ACTIVE.md` for current work state and next actions
3. Check `.ahelia/constraint-profile.yaml` for machine-readable constraints
4. Check `.ahelia/protected-surfaces.yaml` before modifying any interface or schema
5. Identify current phase (1a through 6c) and work within its scope

Sessions must not skip phases or begin work on a later phase until its prerequisites are met.
```

Replace with:

```
Claude Code sessions work against this repo with the following startup protocol:

1. Read `.claude/CLAUDE.md` for repo-specific instructions
2. Read `docs/sync/ACTIVE.md` for current work state and next actions
3. Read `docs/sync/DEFERRED.md` for items punted from prior phases that may be relevant to the current phase or to changes about to be made
4. Check `.ahelia/constraint-profile.yaml` for machine-readable constraints
5. Check `.ahelia/protected-surfaces.yaml` before modifying any interface or schema (includes the machine-readable `deferrals:` block mirroring `DEFERRED.md`)
6. Identify current phase (1a through 6c) and work within its scope

Sessions must not skip phases or begin work on a later phase until its prerequisites are met. The Definition of Done for any phase X→Y promotion includes resolving every Open row in `DEFERRED.md` whose Target ≤ X — see "Universal phase-promotion gate" below.
```

Three changes: (a) insert step 3 reading `DEFERRED.md`, renumber subsequent steps; (b) enhance step 5's parenthetical noting the machine-readable mirror; (c) add a closing sentence cross-referencing the phase-promotion gate to make the integration visible from the Session Model.

- [ ] **Step 3: Verify the change landed.**

Run: `grep -n "DEFERRED.md" /Users/ekimir/swprj/legalize-bg/docs/process/delivery-contract.md`

Expected: at least 8 hits (1 new in Session Model + 1 in the closing sentence + 6 in the per-phase DoD bullets + 1 in the universal gate paragraph from Batch 7).

Run: `grep -A1 "Read .docs/sync/DEFERRED.md" /Users/ekimir/swprj/legalize-bg/docs/process/delivery-contract.md | head -2`

Expected: the Session Model line shows up first (not the per-phase bullet, which has a different prefix).

- [ ] **Step 4: Sanity-check the renumbering.**

Run: `grep -n "^[1-6]\. " /Users/ekimir/swprj/legalize-bg/docs/process/delivery-contract.md | head -10`

Expected: lines 1–6 of the Session Model are now numbered 1–6 (was 1–5 before).

- [ ] **Step 5: Commit.**

```bash
git add docs/process/delivery-contract.md
git commit -m "$(cat <<'EOF'
docs(delivery-contract): add DEFERRED.md to Session Model startup protocol

Review Issue #5 (Important): Batch 7 added DEFERRED.md to .claude/
CLAUDE.md's startup protocol but missed delivery-contract.md's
separate Session Model list. Per .claude/CLAUDE.md's Authority
Surfaces section, delivery-contract is the higher-precedence
authority — the two lists contradicted on the read path, with the
higher-precedence one missing the new file.

Inserts step 3 ("Read docs/sync/DEFERRED.md ...") into the Session
Model, renumbers subsequent steps, and enhances step 5's parenthetical
to note the machine-readable deferrals mirror in
.ahelia/protected-surfaces.yaml. Closing sentence cross-references the
universal phase-promotion gate so the connection between the Session
Model and the per-phase DoD bullets is visible from a single read.

Doesn't restructure the duplicate-startup-protocol-lists problem
(flagged as Recommendation #4) — that's a deeper consolidation tracked
separately. This commit just brings the two lists into agreement.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## BATCH E — Minor findings + publication-readiness sweep (Task 6)

### Task 6: Apply Minor findings + final test/parse/integrity sweep + ACTIVE.md milestone

**Audit:** review Minor findings #6, #7, #8, #9 — DEFERRED.md missing Resolved-row schema example; `_iter_corpus_files` function-name spot-check; runbook one-line note about `laws.title` vs frontmatter `titulo` for the smoke-test pin; observation that the unbalanced-quote regression test from Task 1 supersedes the narrower pre-Batch 5 test (already handled in Task 1).

**Files (in order of edit):**
- Modify: `docs/sync/DEFERRED.md` (add Resolved-row template/schema clarification — Minor #6)
- Verify (no edit if function name correct): `docs/data/canonical-data-model.md` §7.5 — Minor #7
- Modify: `docs/runbook/2026-05-09-phase1b1-operator-setup.md` (one-line `laws.title` clarification on the smoke-test pin — Minor #8)
- Modify: `docs/sync/ACTIVE.md` (append a milestone line for the review-fixes commit + bump test count to 221)

- [ ] **Step 1: Add Resolved-row schema example to DEFERRED.md (Minor #6).**

In `docs/sync/DEFERRED.md`, find the section header:

```
## Resolved deferrals

(empty — Phase 1b.1 is the first phase to register deferrals in this file.)
```

Replace with:

```
## Resolved deferrals

(empty — Phase 1b.1 is the first phase to register deferrals in this file.)

> **Row schema for resolved entries.** When an Open row is resolved at a phase boundary it migrates here with the same columns; only the values change. The `Status` column flips from `Open` to one of `Implemented` / `Re-affirmed` / `Withdrawn`; `Last reviewed` becomes the resolution date; an extra column "Resolution note" can be added inline with a one-sentence explanation and a link to the closing `DECISIONS.md` entry. Example row format (kept as a template, not an actual deferral):
>
> | ID | Title | Punted from | Target | Status | Last reviewed | FR / Decision | Resolution note |
> |---|---|---|---|---|---|---|---|
> | D-YYYY-MM-DD-NN | _example title_ | _from-phase_ | _target-phase_ | Implemented | YYYY-MM-DD | [FR-NNN](../frs/INDEX.md) | _One-sentence resolution; link to_ [_DECISIONS.md_](DECISIONS.md) _entry._ |
```

- [ ] **Step 2: Spot-check `_iter_corpus_files` function name (Minor #7).**

Run: `grep -n "def _iter_corpus_files\|def _load_frontmatter\|def _parse_md" /Users/ekimir/swprj/legalize-bg/index/build.py`

Expected: a `def _iter_corpus_files` line. If absent (i.e., the actual function has a different name), proceed to Step 2a; otherwise skip to Step 3.

- [ ] **Step 2a (conditional — only if Step 2 found a different name):** update `docs/data/canonical-data-model.md` §7.5 to use the actual function name. Find the line:

```
`index/build.py:_iter_corpus_files` raises `ValueError` when an `.md` file has `identificador` ∈ {None, "", 0, "0"}.
```

Replace `_iter_corpus_files` with the actual function name observed at Step 2.

If the function name was correct (the expected case based on plan baseline-checks at line 40 of `build.py`), skip this step.

- [ ] **Step 3: Add `laws.title` vs frontmatter `titulo` clarification to runbook (Minor #8).**

Find the Smoke test third prompt + expected outcome:

```
> What's the publication date of doc_id -549676032?

Expected: succeeds with `titulo: ""` (truthful empty for the §7.3
phantom act) **and** a `DATE_UNCERTAIN` warning in the response
(`source_date_marker: "unknown"`); `fecha_publicacion` is null. This
specific doc_id is in the intersection of the §7.3 empty-titulo set
**and** the 121 §7.2 null-pub-date set, so the warning is deterministic
— if you don't see `DATE_UNCERTAIN`, the index is stale or the §7.2
surfacing path is broken.
```

Append a paragraph immediately after (still inside the Smoke test section):

```
> **Aside — `titulo: ""` vs `<doc_id=...>`.** The frontmatter `titulo` for §7.3 phantom acts is genuinely empty (`titulo: ''` in the `.md` file), so `get_law` returns the truthful empty. The SQLite `laws.title` column for the same act, however, carries a substituted `<doc_id=N>` form — that substitution lives in `index/build.py` and only affects `search` results' display. So an operator running raw SQL like `SELECT title FROM laws WHERE doc_id = -549676032` will see `<doc_id=-549676032>`, not the empty string. Both views are consistent with their respective contracts; the substitution exists only so search results are recognizable in the LLM-facing output.
```

- [ ] **Step 4: Run the full test suite to confirm Tasks 1–5 + Step 1 of Task 6 still leave the suite green.**

Run: `.venv/bin/pytest -q 2>&1 | tail -3`

Expected: 221 passed.

- [ ] **Step 5: YAML parse check on the two YAML files we touched across the whole plan series (audit-gaps + this plan).**

Run: `.venv/bin/python -c "
import yaml
for p in ['.ahelia/protected-surfaces.yaml']:
    d = yaml.safe_load(open(p))
    assert isinstance(d, dict), f'{p}: not a dict'
    print(f'{p}: parses OK ({len(d)} top-level keys)')
"`

Expected: `protected-surfaces.yaml: parses OK (3 top-level keys)` (paths, rules, deferrals — plus `deferrals_meta` so should be 4).

- [ ] **Step 6: Cross-reference integrity sweep — every `schema-reference.md §X (...)` claim resolves.**

Run: `grep -n "schema-reference.md..§\|schema-reference\.md.*§" /Users/ekimir/swprj/legalize-bg/mcp_server/queries.py /Users/ekimir/swprj/legalize-bg/docs/architecture/runtime-flows.md`

Expected: cross-references point at `§2 ("Predicate semantics")` (queries.py docstrings) — no leftover `§3` pointers.

Run: `grep -n "Predicate semantics" /Users/ekimir/swprj/legalize-bg/docs/data/schema-reference.md`

Expected: 1 hit (the heading).

- [ ] **Step 7: Cross-reference integrity sweep — every FR-018 claim resolves.**

Run: `grep -rn "FR-018" /Users/ekimir/swprj/legalize-bg/mcp_server /Users/ekimir/swprj/legalize-bg/docs 2>&1 | head`

Expected: hits in `mcp_server/server.py` (Batch 5 retarget), `docs/frs/INDEX.md` (FR-018 row), `docs/architecture/container-view.md` (Batch 3 forward pointer), `docs/plans/...` (the prior plan + this plan). No `FR-001 Phase 2` leftovers.

Run: `grep -rn "FR-001 Phase 2" /Users/ekimir/swprj/legalize-bg/mcp_server /Users/ekimir/swprj/legalize-bg/docs/architecture /Users/ekimir/swprj/legalize-bg/docs/runbook 2>&1 | grep -v "docs/plans/" | head`

Expected: no hits outside plan files. (Plan files reference the old text in the context of describing the fix; that's appropriate.)

- [ ] **Step 8: Update `docs/sync/ACTIVE.md` with the milestone.**

Find the bullet list under `**Phase 1b.1** (MCP server) — complete on `main`:` and locate the line:

```
- 211 tests passing across unit, component, integration (FastMCP in-memory), real-corpus acceptance (§7.1/7.2/7.3), FTS regression, and soft perf-budget tiers.
```

Replace with:

```
- **221 tests passing** across unit, component, integration (FastMCP in-memory), real-corpus acceptance (§7.1/7.2/7.3), FTS regression, and soft perf-budget tiers (216 after the audit-gaps batch on 2026-05-09; 221 after the review-fixes commit added 5 parametrizations of the FTS5 user-input regression).
```

Find the bullet:

```
- Two formal code-review rounds; 18/18 findings addressed in-batch with zero deferrals (forward-looking items recorded as FR-012 through FR-017 in `docs/frs/INDEX.md` per Ahelia conventions).
```

Append a sibling bullet immediately after:

```
- **Three** formal code-review rounds; the third (post-audit-gaps) surfaced 5 Important + 4 Minor findings, all closed in `docs/plans/2026-05-09-phase1b1-review-fixes.md` (FTS5 user-input allowlist regression, two `schema-reference.md` constraint mismatches the audit-fix itself introduced, a stale `runtime-flows.md §6.3.4` predicate, and the duplicate Session Model gap). Phase 1b.1 docs and code are now publication-ready.
```

- [ ] **Step 9: Commit Task 6.**

```bash
git add docs/sync/DEFERRED.md docs/runbook/2026-05-09-phase1b1-operator-setup.md docs/sync/ACTIVE.md
# Conditionally include canonical-data-model.md only if Step 2a was needed
if git diff --cached --name-only | grep -q "canonical-data-model.md"; then :; fi
# (No-op; just pattern-checking. The actual edit, if performed, was already staged in Step 2a.)
git diff --cached --stat
git commit -m "$(cat <<'EOF'
docs: apply 4 Minor review findings + ACTIVE.md milestone for review-fixes

Review Minor findings #6, #7 (verified — no edit needed), #8, #9
(superseded by Task 1).

#6 — DEFERRED.md "Resolved deferrals" section had no row-schema
example, leaving the first session that resolves a deferral to invent
the row format. Adds a template row clarifying that resolved entries
keep the same columns, gain a "Resolution note" column linking to a
DECISIONS.md entry, and have Status flipped from Open to one of
Implemented / Re-affirmed / Withdrawn.

#7 — Spot-checked `_iter_corpus_files` in canonical-data-model.md §7.5
against the actual `index/build.py:40` function definition. Match
confirmed; no edit needed.

#8 — runbook smoke-test third prompt had a subtle gotcha: get_law
returns truthful empty `titulo: ""` for §7.3 phantom acts, but a
careful operator running raw SQL on `laws.title` would see the
`<doc_id=-549676032>` substitution and wonder. Added a one-paragraph
"Aside" explaining the search-display vs frontmatter-truth split.

#9 — superseded by the Task 1 parameterized regression already
committed; no separate edit.

ACTIVE.md updated: test count 211 → 221 (the previously stale "211"
predated the audit-gaps batch and the review-fixes commit's 5
parametrizations); milestone bullet added marking Phase 1b.1 as
publication-ready after three review rounds.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

- [ ] **Step 10: Final green test run + summary.**

Run: `.venv/bin/pytest -q 2>&1 | tail -3`

Expected: 221 passed in <12 seconds.

Run: `git log --oneline 76dc9c4c..HEAD`

Expected: 5 new commits (Task 1 + Tasks 2–3 + Task 4 + Task 5 + Task 6).

---

## Definition of Done

- [ ] **Task 1**: `index/fts.py:_run_match` allowlist includes `unterminated string` and `no such column` (prefix match); `tests/index/test_fts.py` has parameterized regression covering all three error families; full suite at 221 passing.
- [ ] **Task 2**: `docs/data/schema-reference.md` Migration 2 row shows the actual 4-column `laws_fts` DDL; `identificador UNINDEXED` no longer appears anywhere; PRAGMA table_info confirms doc-code parity.
- [ ] **Task 3**: `docs/data/schema-reference.md` `date_uncertain` documented as `NOT NULL DEFAULT 0` in all three locations (DDL block, column-row table, Migration 4 row); PRAGMA table_info confirms `notnull=1` after migrate.
- [ ] **Task 4**: `docs/architecture/runtime-flows.md` §6.3.4 ASCII shows `valid_to >= date`; new "Inclusive `valid_to`" paragraph references `schema-reference §2`.
- [ ] **Task 5**: `docs/process/delivery-contract.md` Session Model lists `DEFERRED.md` as step 3 (renumbered to 6 total steps); closing sentence cross-references the universal phase-promotion gate.
- [ ] **Task 6**: DEFERRED.md has Resolved-row schema example; runbook smoke-test has the `laws.title` aside; ACTIVE.md milestone updated; full sweep clean (no `§3` references in queries.py docstrings, no `FR-001 Phase 2` outside plan files, YAML parses, 221 passing).
- [ ] **Final commit count**: 5 commits on top of `76dc9c4c` (one per batch — Task 1 alone, Tasks 2+3 combined, Task 4 alone, Task 5 alone, Task 6 alone).
- [ ] **No new files**: only modifications to existing files (no new tests, no new docs, no schema migrations, no behavioral changes outside the documented `_run_match` allowlist broadening).
- [ ] **Surfaces 3 and 6 untouched**: confirmed by `git diff 76dc9c4c..HEAD -- mcp_server/schemas.py mcp_server/server.py | grep -E "(get_law|search|get_article).*\(|response shape"` returning no signature changes (Surface 3) and no edits to `bg_normalize` or `_extract_article_blocks` (Surface 6).

---

## Risk register

| Risk | Mitigation |
|---|---|
| FTS5 SQLite version drift — a future SQLite update could change the error-message wording (e.g., "unterminated string literal") and break the allowlist's substring match. | Task 1 Step 2's parameterized test has an inner `try/except` that asserts the expected error family is in the message at the SQLite layer; a wording change produces a focused, actionable test failure rather than silent allowlist drift. |
| `startswith("no such column")` is narrower than the other allowlist entries; some FTS5 build could emit "Error: no such column" with a leading prefix. | If observed, replace `startswith` with `in msg`; the trade-off is documented in the inline comment so the next maintainer can make the change without re-deriving the rationale. |
| Adding step 3 (DEFERRED.md) to delivery-contract.md Session Model could miss a downstream reader following the old 5-step numbering. | The `.claude/CLAUDE.md` step list went 1–4 → 1–5 in Batch 7 with the same kind of insertion; no observed breakage. The cross-reference sentence at the end of the Session Model points readers at the phase-promotion gate, anchoring the change in the broader DoD model. |
| The Resolved-row schema example added in Task 6 Step 1 might over-specify the format — a future phase boundary may discover it doesn't fit cleanly. | The template is marked "kept as a template, not an actual deferral" so a session resolving the first real deferral can adjust the schema before it hardens. |

---

## Out-of-scope (re-stated)

- Single-source-of-truth refactor for the duplicate startup-protocol lists (Recommendation #4). Defer to a separate plan.
- Shared module-level `_FTS5_USER_INPUT_PATTERNS` tuple consolidating the `_run_match` and `resolve_name_to_law_id` allowlists (Recommendation #3). Defer to a separate refactor.
- D-2..D-7 deferral implementations (FR-013/14/15/16/17 + 1b.2 perf-budget hardening). Already registered in `DEFERRED.md`; resolution is a phase-boundary decision per the contract.
