# Phase 2 — Temporal Index Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the Phase 2 temporal MCP tools — `history`, `diff`, `amendments_in_period` — backed by the (currently empty) `amendments` table, populated from each act's `amendment_history` frontmatter, with honest "single-version-held" semantics until a write-side lands more text versions.

**Architecture:** No schema migration is needed — the `amendments` table and the `law_versions` temporal columns already exist (`index/catalog.py`). `index/build.py` is extended to populate `amendments` from `amendment_history`. Three new pure query functions in `mcp_server/queries.py` are exposed as three new FastMCP tools in `mcp_server/server.py`, mirroring the existing thin-wrapper pattern. `history()` and `amendments_in_period()` are pure SQLite reads and deliver full value immediately; `diff()` shells out to `git diff` and returns a clear "single version held" result until the parallel re-scrape (see `docs/sync/HANDOFFS/2026-06-21-corpus-rescrape-refresh.md`) or Phase 4 accumulates more commits.

**Tech Stack:** Python 3.12, SQLite/FTS5, FastMCP 3.x, dataclasses, pytest. Interpreter is `.venv/bin/python` (there is no system `python`).

## Global Constraints

- **Interpreter:** all commands use `.venv/bin/python` (e.g. `.venv/bin/python -m pytest -q`). There is no system `python` on PATH.
- **Protected Surface 3 (MCP tool signatures)** — the three new tools MUST match the contracted signatures verbatim from `.ahelia/protected-surfaces.yaml`:
  - `history(law: str) -> list[VersionEntry]`
  - `diff(law: str, date1: str, date2: str) -> str`
  - `amendments_in_period(from_date: str, to_date: str) -> list[AmendmentEntry]`
- **No schema migration.** The `amendments` and `law_versions` tables already carry every column needed (`source_act`, `target_law`, `operation`, `affected_articles`, `dv_issue`, `dv_date`). Do NOT add migrations.
- **`tools.json` is a generated artifact.** Never hand-edit it. Regenerate with `.venv/bin/python -m mcp_server.export_tools --output tools.json`. The CI parity test (`tests/mcp_server/test_export_tools.py`) fails on drift.
- **Error taxonomy parity:** any new code in `mcp_server/errors.py:ERROR_CODES` must also appear in `docs/api/error-codes.md` (as a `### \`CODE\`` heading) and `docs/api/error-codes.json` (a `codes[].code` entry). Enforced by `tests/mcp_server/test_error_codes_doc.py`. The md and json `version` must match each other.
- **Honest version semantics (the load-bearing design choice):** we hold exactly ONE text version per act (the bootstrap commit). Never fabricate `law_versions` rows that point a historical `valid_from` at the bootstrap commit — `version_at_date` would then return 2026 text and falsely claim it was in force on a past date. Historical entries carry `commit_hash=null`; only the held consolidated version carries a real commit.
- **`bg-legal` output language note does NOT apply** — this is pipeline code, not legal-document generation. No em-dash restriction here.
- Commit pipeline-code changes with conventional commits (`feat:`, `test:`, `docs:`), NOT the Legalize `[bootstrap]/[reforma]` corpus format. Work on a feature branch is acceptable but the project's proven pattern is direct-to-`main` after review; follow the user's direction at execution time.

---

## File Structure

| File | Change | Responsibility |
|---|---|---|
| `index/build.py` | Modify | Populate `amendments` from `amendment_history` during build |
| `mcp_server/schemas.py` | Modify | Add `VersionEntry`, `AmendmentEntry` dataclasses |
| `mcp_server/errors.py` | Modify | Add `INVALID_DATE_RANGE` code |
| `docs/api/error-codes.md` / `.json` | Modify | Document the new code; bump version 1.0.0 → 1.1.0 |
| `mcp_server/queries.py` | Modify | Add `law_history`, `amendments_in_period`, `diff_law_versions` |
| `mcp_server/server.py` | Modify | Register `history`, `amendments_in_period`, `diff` tools |
| `mcp_server/export_tools.py` | Modify | Bump `TOOLS_JSON_VERSION` to 1.1.0; phase → "2" |
| `tools.json` | Regenerate | 3 → 6 tools + new error code |
| `tests/index/test_build.py` | Modify | Assert `amendments` populated |
| `tests/mcp_server/test_schemas.py` | Modify | Assert new dataclass shapes |
| `tests/mcp_server/test_queries.py` | Modify | Unit-test the 3 query functions |
| `tests/mcp_server/test_temporal_tools.py` | Create | Tool-level tests for the 3 new tools |
| `tests/mcp_server/test_tools_e2e.py` | Modify | e2e FastMCP transport coverage for new tools |
| `docs/sync/ACTIVE.md`, `DECISIONS.md`, `docs/frs/INDEX.md`, `.ahelia/protected-surfaces.yaml` | Modify | Phase-2 close-out (D-031; FR-001 → Done) |

---

## Task 1: Populate the `amendments` table during index build

**Files:**
- Modify: `index/build.py` (the per-act insert loop in `build()`)
- Test: `tests/index/test_build.py`

**Interfaces:**
- Consumes: `meta["amendment_history"]` — a `list[dict]` of `{"dv": str, "date": str|None}` (written by `fetcher/bg/assembler.assemble_file`).
- Produces: rows in `amendments(source_act, target_law, operation, affected_articles, dv_issue, dv_date)`. `history()` and `amendments_in_period()` read these.

- [ ] **Step 1: Write the failing test**

Add to `tests/index/test_build.py`:

```python
def test_build_populates_amendments_from_history(fake_corpus, tmp_path):
    """Phase 2: each amendment_history entry becomes an `amendments` row,
    keyed to the act via target_law, with the DV issue + date carried."""
    db_path = str(tmp_path / "test.db")
    build(corpus_root=fake_corpus, db_path=db_path)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    # ZOP (the fixture) has a non-trivial amendment history.
    rows = conn.execute(
        "SELECT target_law, operation, dv_issue, dv_date FROM amendments"
    ).fetchall()
    assert len(rows) > 0, "expected amendments rows from amendment_history"
    # Every row is keyed to a real law and carries the generic operation.
    law_ids = {r["law_id"] for r in conn.execute("SELECT law_id FROM laws")}
    for r in rows:
        assert r["target_law"] in law_ids
        assert r["operation"] == "amendment"
    # dv_date values are ISO strings (not datetime.date objects).
    dated = [r for r in rows if r["dv_date"] is not None]
    assert dated, "expected at least one dated amendment"
    for r in dated:
        assert isinstance(r["dv_date"], str) and len(r["dv_date"]) == 10
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/index/test_build.py::test_build_populates_amendments_from_history -v`
Expected: FAIL — `amendments` is empty (currently never populated).

- [ ] **Step 3: Write the implementation**

In `index/build.py`, inside the `for cat, path in _iter_corpus_files(...)` loop, AFTER the `law_versions` insert and BEFORE the `for prov in parse_provisions(...)` loop, insert amendment rows:

```python
            # Phase 2 (FR-001): populate the `amendments` table from the
            # act's amendment_history frontmatter. This is the backing
            # store for the history() and amendments_in_period() tools.
            # We do NOT know the specific ЗИД operation (substitution /
            # addition / deletion) without Phase-4 ЗИД parsing, so we
            # record the generic operation 'amendment'. affected_articles
            # stays NULL for the same reason.
            for entry in (meta.get("amendment_history") or []):
                dv_issue = entry.get("dv")
                dv_date = entry.get("date")
                if hasattr(dv_date, "isoformat"):   # PyYAML may yield date
                    dv_date = dv_date.isoformat()
                conn.execute(
                    """INSERT INTO amendments
                           (source_act, target_law, operation,
                            affected_articles, dv_issue, dv_date)
                       VALUES (?, ?, 'amendment', NULL, ?, ?)""",
                    (f"ДВ {dv_issue}" if dv_issue else "unknown",
                     law_id, dv_issue, dv_date),
                )
```

(No new DELETE needed: `_drop_content_rows` already clears `amendments` before each rebuild, so this stays idempotent.)

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/index/test_build.py -v`
Expected: PASS (all build tests, including the new one and the existing idempotency test).

- [ ] **Step 5: Commit**

```bash
git add index/build.py tests/index/test_build.py
git commit -m "feat(index): populate amendments table from amendment_history (Phase 2 FR-001)"
```

---

## Task 2: Add `VersionEntry` and `AmendmentEntry` response shapes

**Files:**
- Modify: `mcp_server/schemas.py`
- Test: `tests/mcp_server/test_schemas.py`

**Interfaces:**
- Produces: `VersionEntry(date: str|None, dv_issue: str|None, operation: str, commit_hash: str|None)` and `AmendmentEntry(law_id: str, title: str, date: str|None, dv_issue: str|None)`, each with `to_dict()`. Consumed by `queries.law_history` / `queries.amendments_in_period` and the server tools.

- [ ] **Step 1: Write the failing test**

Add to `tests/mcp_server/test_schemas.py`:

```python
def test_version_entry_to_dict():
    from mcp_server.schemas import VersionEntry
    v = VersionEntry(date="2017-08-04", dv_issue="63/2017",
                     operation="amendment", commit_hash=None)
    d = v.to_dict()
    assert d == {"date": "2017-08-04", "dv_issue": "63/2017",
                 "operation": "amendment", "commit_hash": None}


def test_amendment_entry_to_dict():
    from mcp_server.schemas import AmendmentEntry
    a = AmendmentEntry(law_id="zakon-zop", title="Закон за ОП",
                       date="2017-08-04", dv_issue="63/2017")
    d = a.to_dict()
    assert d == {"law_id": "zakon-zop", "title": "Закон за ОП",
                 "date": "2017-08-04", "dv_issue": "63/2017"}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/mcp_server/test_schemas.py::test_version_entry_to_dict -v`
Expected: FAIL — `ImportError: cannot import name 'VersionEntry'`.

- [ ] **Step 3: Write the implementation**

Append to `mcp_server/schemas.py`:

```python
@dataclass(frozen=True)
class VersionEntry:
    """One entry in an act's version timeline (Phase 2 / FR-001).

    `commit_hash` is populated ONLY for the version whose text the
    corpus actually holds (operation='consolidated'); historical
    amendment events carry commit_hash=None because their separate
    text is not held yet (no per-amendment commits until the re-scrape
    or Phase 4 lands them). `operation` is 'amendment' for a DV
    amendment event and 'consolidated' for the held current version.
    """
    date: str | None
    dv_issue: str | None
    operation: str
    commit_hash: str | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class AmendmentEntry:
    """One amendment event across the corpus in a period (Phase 2)."""
    law_id: str
    title: str
    date: str | None
    dv_issue: str | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/mcp_server/test_schemas.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add mcp_server/schemas.py tests/mcp_server/test_schemas.py
git commit -m "feat(schemas): add VersionEntry + AmendmentEntry for Phase 2 temporal tools"
```

---

## Task 3: Add the `INVALID_DATE_RANGE` error code + docs + regenerate tools.json

**Files:**
- Modify: `mcp_server/errors.py`, `docs/api/error-codes.md`, `docs/api/error-codes.json`, `mcp_server/export_tools.py`
- Regenerate: `tools.json`
- Test: `tests/mcp_server/test_errors.py`

**Interfaces:**
- Produces: `"INVALID_DATE_RANGE"` in `ERROR_CODES`. Raised by `amendments_in_period` and `diff` when `from/date1 > to/date2`.

- [ ] **Step 1: Write the failing test**

Add to `tests/mcp_server/test_errors.py`:

```python
def test_invalid_date_range_is_a_known_code():
    from mcp_server.errors import ERROR_CODES, ToolError
    assert "INVALID_DATE_RANGE" in ERROR_CODES
    err = ToolError("INVALID_DATE_RANGE", {"from_date": "2020-01-01",
                                           "to_date": "2019-01-01"})
    assert err.to_dict()["code"] == "INVALID_DATE_RANGE"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/mcp_server/test_errors.py::test_invalid_date_range_is_a_known_code -v`
Expected: FAIL — code not in `ERROR_CODES`.

- [ ] **Step 3: Add the code to the runtime registry**

In `mcp_server/errors.py`, add to the `ERROR_CODES` frozenset:

```python
    "INVALID_DATE_RANGE",  # Phase 2: diff/amendments_in_period with from > to
```

- [ ] **Step 4: Document in `error-codes.md`**

Add a section under `## Codes` in `docs/api/error-codes.md`:

```markdown
### `INVALID_DATE_RANGE`

Raised by: `diff`, `amendments_in_period`.
When: the start date is later than the end date (`date1 > date2` or `from_date > to_date`).
Payload:
- `from_date` (string): the start date supplied.
- `to_date` (string): the end date supplied.
```

And bump the version marker near the top of `error-codes.md`:

```markdown
**Version:** 1.1.0  (matches `tools.json` `version`)
**Spec since:** Phase 1b.1 — D-026; extended in Phase 1b.2 with `QUERY_TOO_BROAD`; Phase 2 adds `INVALID_DATE_RANGE`.
```

- [ ] **Step 5: Document in `error-codes.json`**

Set `"version": "1.1.0"` and add to the `codes` array:

```json
    {
      "code": "INVALID_DATE_RANGE",
      "raised_by": ["diff", "amendments_in_period"],
      "category": "error",
      "since_phase": "2",
      "payload": {
        "from_date": {"type": "string", "optional": false, "description": "start date supplied"},
        "to_date": {"type": "string", "optional": false, "description": "end date supplied"}
      }
    }
```

- [ ] **Step 6: Bump the tools.json version and regenerate**

In `mcp_server/export_tools.py` set `TOOLS_JSON_VERSION = "1.1.0"` and change the server block `"phase": "1b.2"` to `"phase": "2"`. Then regenerate:

```bash
.venv/bin/python -m mcp_server.export_tools --output tools.json
```

(`tools.json` still lists 3 tools at this point — Task 7 adds the other 3 — but its `error_codes` array and `version` are now in parity.)

- [ ] **Step 7: Run the parity tests**

Run: `.venv/bin/python -m pytest tests/mcp_server/test_errors.py tests/mcp_server/test_error_codes_doc.py tests/mcp_server/test_export_tools.py -v`
Expected: PASS (runtime code documented in md + json; md/json versions match; tools.json matches live schemas).

- [ ] **Step 8: Commit**

```bash
git add mcp_server/errors.py mcp_server/export_tools.py docs/api/error-codes.md docs/api/error-codes.json tools.json tests/mcp_server/test_errors.py
git commit -m "feat(errors): add INVALID_DATE_RANGE; bump taxonomy + tools.json to 1.1.0"
```

---

## Task 4: `law_history` query function

**Files:**
- Modify: `mcp_server/queries.py`
- Test: `tests/mcp_server/test_queries.py`

**Interfaces:**
- Consumes: `amendments` rows (Task 1), `law_versions` rows, `mcp_server.schemas.VersionEntry`.
- Produces: `law_history(conn, law_id: str) -> list[VersionEntry]` — amendment events oldest→newest, then one `operation='consolidated'` entry carrying the held `commit_hash`.

- [ ] **Step 1: Write the failing test**

Add to `tests/mcp_server/test_queries.py` (the file already imports from `mcp_server.queries` and uses the `populated_conn` fixture):

```python
def test_law_history_lists_amendments_then_consolidated(populated_conn):
    from mcp_server.queries import law_history
    from tests.mcp_server.conftest import FAKE_COMMIT_HASH
    # Seed two amendment events for zakon-a.
    populated_conn.execute(
        "INSERT INTO amendments (source_act, target_law, operation, dv_issue, dv_date) "
        "VALUES ('ДВ 13/2016', 'zakon-a', 'amendment', '13/2016', '2016-02-16')")
    populated_conn.execute(
        "INSERT INTO amendments (source_act, target_law, operation, dv_issue, dv_date) "
        "VALUES ('ДВ 63/2017', 'zakon-a', 'amendment', '63/2017', '2017-08-04')")
    populated_conn.commit()

    hist = law_history(populated_conn, "zakon-a")
    # Two amendment events + one consolidated entry.
    assert [v.operation for v in hist] == ["amendment", "amendment", "consolidated"]
    # Historical entries hold no separate text version.
    assert hist[0].commit_hash is None and hist[1].commit_hash is None
    assert hist[0].dv_issue == "13/2016"
    # The held consolidated version carries the real commit.
    assert hist[-1].commit_hash == FAKE_COMMIT_HASH


def test_law_history_no_amendments_returns_consolidated_only(populated_conn):
    from mcp_server.queries import law_history
    hist = law_history(populated_conn, "zakon-b")  # no amendments seeded
    assert len(hist) == 1
    assert hist[0].operation == "consolidated"
    assert hist[0].commit_hash is not None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/mcp_server/test_queries.py::test_law_history_lists_amendments_then_consolidated -v`
Expected: FAIL — `ImportError: cannot import name 'law_history'`.

- [ ] **Step 3: Write the implementation**

Add to `mcp_server/queries.py` (import the schema at the top: `from mcp_server.schemas import VersionEntry, AmendmentEntry`):

```python
def law_history(conn: sqlite3.Connection, law_id: str) -> list[VersionEntry]:
    """Return the act's version timeline, oldest→newest.

    Amendment events come from the `amendments` table (populated from
    amendment_history at build time). Each historical event carries
    commit_hash=None — we know the act was amended on that DV date but
    don't hold a separate text snapshot for it. A final
    operation='consolidated' entry carries the real commit of the held
    current text. Honest semantics per the Phase 2 design: never imply
    we hold historical text we don't have.
    """
    amend_rows = conn.execute(
        "SELECT dv_issue, dv_date, operation FROM amendments "
        "WHERE target_law = ? ORDER BY dv_date IS NULL, dv_date",
        (law_id,),
    ).fetchall()
    entries: list[VersionEntry] = [
        VersionEntry(date=r["dv_date"], dv_issue=r["dv_issue"],
                     operation=r["operation"], commit_hash=None)
        for r in amend_rows
    ]
    lv = conn.execute(
        "SELECT valid_from, commit_hash FROM law_versions "
        "WHERE law_id = ? ORDER BY valid_from DESC LIMIT 1",
        (law_id,),
    ).fetchone()
    if lv:
        last_dated = [r["dv_date"] for r in amend_rows if r["dv_date"]]
        held_date = last_dated[-1] if last_dated else lv["valid_from"]
        entries.append(VersionEntry(
            date=held_date, dv_issue=None,
            operation="consolidated", commit_hash=lv["commit_hash"]))
    return entries
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/mcp_server/test_queries.py -k law_history -v`
Expected: PASS (both new tests).

- [ ] **Step 5: Commit**

```bash
git add mcp_server/queries.py tests/mcp_server/test_queries.py
git commit -m "feat(queries): add law_history (Phase 2 timeline with honest commit mapping)"
```

---

## Task 5: `amendments_in_period` query function

**Files:**
- Modify: `mcp_server/queries.py`
- Test: `tests/mcp_server/test_queries.py`

**Interfaces:**
- Consumes: `amendments` joined to `laws`, `schemas.AmendmentEntry`, `errors.ToolError`.
- Produces: `amendments_in_period(conn, from_date: str, to_date: str) -> list[AmendmentEntry]`. Raises `ToolError("INVALID_DATE_RANGE", ...)` when `from_date > to_date`.

- [ ] **Step 1: Write the failing test**

Add to `tests/mcp_server/test_queries.py`:

```python
def test_amendments_in_period_filters_and_joins_title(populated_conn):
    from mcp_server.queries import amendments_in_period
    populated_conn.execute(
        "INSERT INTO amendments (source_act, target_law, operation, dv_issue, dv_date) "
        "VALUES ('x', 'zakon-a', 'amendment', '13/2016', '2016-02-16')")
    populated_conn.execute(
        "INSERT INTO amendments (source_act, target_law, operation, dv_issue, dv_date) "
        "VALUES ('y', 'zakon-b', 'amendment', '63/2017', '2017-08-04')")
    populated_conn.commit()

    out = amendments_in_period(populated_conn, "2016-01-01", "2016-12-31")
    assert len(out) == 1
    assert out[0].law_id == "zakon-a"
    assert out[0].title == "Закон за А"
    assert out[0].dv_issue == "13/2016"


def test_amendments_in_period_rejects_reversed_range(populated_conn):
    from mcp_server.queries import amendments_in_period
    from mcp_server.errors import ToolError
    with pytest.raises(ToolError) as exc:
        amendments_in_period(populated_conn, "2020-01-01", "2019-01-01")
    assert exc.value.code == "INVALID_DATE_RANGE"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/mcp_server/test_queries.py::test_amendments_in_period_filters_and_joins_title -v`
Expected: FAIL — `ImportError`.

- [ ] **Step 3: Write the implementation**

Add to `mcp_server/queries.py`:

```python
def amendments_in_period(conn: sqlite3.Connection, from_date: str,
                         to_date: str) -> list[AmendmentEntry]:
    """Return every dated amendment event across the corpus whose DV
    date falls within [from_date, to_date] inclusive, oldest first.

    Raises INVALID_DATE_RANGE (directly, like full_text_search's
    QUERY_TOO_BROAD) when from_date > to_date.
    """
    if from_date and to_date and from_date > to_date:
        raise ToolError("INVALID_DATE_RANGE",
                        {"from_date": from_date, "to_date": to_date})
    rows = conn.execute(
        """SELECT a.target_law AS law_id, l.title AS title,
                  a.dv_date AS date, a.dv_issue AS dv_issue
             FROM amendments a
             JOIN laws l ON l.law_id = a.target_law
            WHERE a.dv_date IS NOT NULL
              AND a.dv_date >= ? AND a.dv_date <= ?
            ORDER BY a.dv_date, a.target_law""",
        (from_date, to_date),
    ).fetchall()
    return [
        AmendmentEntry(
            law_id=r["law_id"],
            title=r["title"] or f"<doc_id-unknown:{r['law_id']}>",
            date=r["date"], dv_issue=r["dv_issue"])
        for r in rows
    ]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/mcp_server/test_queries.py -k amendments_in_period -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add mcp_server/queries.py tests/mcp_server/test_queries.py
git commit -m "feat(queries): add amendments_in_period with INVALID_DATE_RANGE guard"
```

---

## Task 6: `diff_law_versions` query function

**Files:**
- Modify: `mcp_server/queries.py`
- Test: `tests/mcp_server/test_queries.py`

**Interfaces:**
- Consumes: `version_at_date` (existing, may raise `NoVersionAtDate`), `laws.category`, `errors.ToolError`, `subprocess`.
- Produces: `diff_law_versions(conn, corpus_root: Path, law_id: str, date1: str, date2: str) -> str`. Raises `INVALID_DATE_RANGE` on reversed range; propagates `NoVersionAtDate` for the server to map.

- [ ] **Step 1: Write the failing test**

Add to `tests/mcp_server/test_queries.py`:

```python
def test_diff_single_version_returns_no_change_message(populated_conn, tmp_path):
    from mcp_server.queries import diff_law_versions
    # Both dates resolve to the same (only) commit → human-readable note,
    # no git invocation.
    out = diff_law_versions(populated_conn, tmp_path, "zakon-a",
                            "2020-06-01", "2021-06-01")
    assert "one consolidated version" in out.lower() \
        or "single consolidated version" in out.lower()


def test_diff_rejects_reversed_range(populated_conn, tmp_path):
    from mcp_server.queries import diff_law_versions
    from mcp_server.errors import ToolError
    with pytest.raises(ToolError) as exc:
        diff_law_versions(populated_conn, tmp_path, "zakon-a",
                          "2021-01-01", "2020-01-01")
    assert exc.value.code == "INVALID_DATE_RANGE"
```

(Note: `populated_conn` seeds every `law_versions.valid_from = '2020-01-01'`, so both query dates resolve to the single FAKE_COMMIT_HASH commit — exercising the single-version branch without needing a real git repo.)

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/mcp_server/test_queries.py::test_diff_single_version_returns_no_change_message -v`
Expected: FAIL — `ImportError`.

- [ ] **Step 3: Write the implementation**

Add to `mcp_server/queries.py` (ensure `import subprocess` and `from pathlib import Path` are present at the top — add if missing):

```python
def diff_law_versions(conn: sqlite3.Connection, corpus_root: Path,
                      law_id: str, date1: str, date2: str) -> str:
    """Return a `git diff` of the act's text between the versions in
    force at date1 and date2.

    When both dates resolve to the same commit (the common case until a
    write-side accumulates more versions), returns a clear bilingual
    "single consolidated version held" note instead of an empty diff —
    so the model doesn't mistake "no diff" for "no data".

    Raises INVALID_DATE_RANGE on a reversed range. Propagates
    NoVersionAtDate (from version_at_date) for the server tool to map
    to NO_VERSION_AT_DATE.
    """
    if date1 and date2 and date1 > date2:
        raise ToolError("INVALID_DATE_RANGE",
                        {"from_date": date1, "to_date": date2})
    commit1 = version_at_date(conn, law_id, date1)
    commit2 = version_at_date(conn, law_id, date2)
    if commit1 == commit2:
        return (
            f"Хранилището съдържа една консолидирана версия на „{law_id}“; "
            f"няма записана текстова промяна между {date1} и {date2}. / "
            f"The corpus holds one consolidated version of '{law_id}'; "
            f"no textual change is recorded between {date1} and {date2}."
        )
    cat_row = conn.execute(
        "SELECT category FROM laws WHERE law_id = ?", (law_id,)
    ).fetchone()
    rel_path = f"{cat_row['category']}/{law_id}.md"
    out = subprocess.run(
        ["git", "diff", commit1, commit2, "--", rel_path],
        cwd=str(corpus_root), check=True, capture_output=True, text=True,
    )
    return out.stdout
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/mcp_server/test_queries.py -k diff -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add mcp_server/queries.py tests/mcp_server/test_queries.py
git commit -m "feat(queries): add diff_law_versions with single-version note + reversed-range guard"
```

---

## Task 7: Register `history`, `amendments_in_period`, `diff` MCP tools

**Files:**
- Modify: `mcp_server/server.py` (inside `build_app`, after the `get_article` registration)
- Test: `tests/mcp_server/test_temporal_tools.py` (create)

**Interfaces:**
- Consumes: `queries.law_history`, `queries.amendments_in_period`, `queries.diff_law_versions`, `queries.resolve_name_to_law_id`, `queries.NoVersionAtDate`, `ToolError`.
- Produces: three registered tools matching the protected signatures. Each returns JSON-serializable output (`list[dict]` or `str`).

- [ ] **Step 1: Write the failing test**

Create `tests/mcp_server/test_temporal_tools.py`:

```python
"""Tool-level tests for the Phase 2 temporal tools via build_app's
sync shortcut. e2e transport coverage lives in test_tools_e2e."""

import pytest

from mcp_server.errors import ToolError
from mcp_server.server import build_app
from tests.mcp_server.conftest import FAKE_COMMIT_HASH


@pytest.fixture
def app(populated_conn, tmp_path):
    assert FAKE_COMMIT_HASH == "a" * 40
    (tmp_path / "laws").mkdir()
    # zakon-a needs a file only if a real git diff is exercised; the
    # single-version path here does not touch the filesystem.
    populated_conn.execute(
        "INSERT INTO amendments (source_act, target_law, operation, dv_issue, dv_date) "
        "VALUES ('ДВ 13/2016', 'zakon-a', 'amendment', '13/2016', '2016-02-16')")
    populated_conn.commit()
    return build_app(conn=populated_conn, corpus_root=tmp_path)


def test_history_returns_timeline(app):
    out = app.call_tool_sync("history", {"law": "100"})  # zakon-a doc_id
    assert isinstance(out, list)
    assert out[-1]["operation"] == "consolidated"
    assert out[-1]["commit_hash"] == FAKE_COMMIT_HASH
    assert out[0]["operation"] == "amendment"
    assert out[0]["dv_issue"] == "13/2016"


def test_history_unknown_law_raises(app):
    with pytest.raises(ToolError) as exc:
        app.call_tool_sync("history", {"law": "не съществува"})
    assert exc.value.code == "LAW_NOT_FOUND"


def test_amendments_in_period_returns_entries(app):
    out = app.call_tool_sync("amendments_in_period",
                             {"from_date": "2016-01-01", "to_date": "2016-12-31"})
    assert len(out) == 1
    assert out[0]["law_id"] == "zakon-a"


def test_amendments_in_period_reversed_raises(app):
    with pytest.raises(ToolError) as exc:
        app.call_tool_sync("amendments_in_period",
                           {"from_date": "2020-01-01", "to_date": "2019-01-01"})
    assert exc.value.code == "INVALID_DATE_RANGE"


def test_diff_single_version_message(app):
    out = app.call_tool_sync("diff", {"law": "100",
                                      "date1": "2020-06-01", "date2": "2021-06-01"})
    assert isinstance(out, str)
    assert "consolidated" in out.lower()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/mcp_server/test_temporal_tools.py -v`
Expected: FAIL — `KeyError: 'history'` (tool not registered).

- [ ] **Step 3: Write the implementation**

In `mcp_server/server.py`, inside `build_app`, AFTER the `get_article` registration block and BEFORE `return handle`, add (import `VersionEntry`/`AmendmentEntry` are not needed here — the query functions return them and we call `.to_dict()`):

```python
    # ─────────────────── history (Phase 2) ───────────────────────────

    def history(law: str) -> list[dict]:
        """Return the amendment timeline of a Bulgarian act, oldest→newest.

        Args:
            law: The act's title, slug, or identificador (see get_law).

        Returns:
            A list of version entries, each {date, dv_issue, operation,
            commit_hash}. `operation` is "amendment" for a DV amendment
            event and "consolidated" for the currently-held text. Only
            the consolidated entry carries a non-null `commit_hash`:
            the corpus holds one consolidated text per act, so the text
            of historical amendments is not separately retrievable yet
            (commit_hash is null for those). Use this to answer "when
            was this act amended?" — it lists every DV amendment date.
        """
        try:
            law_id = queries.resolve_name_to_law_id(conn, law)
        except queries.AmbiguousName as e:
            raise ToolError(code="AMBIGUOUS_NAME",
                            payload={"name": e.name, "candidates": e.candidates})
        except queries.LawNotFound as e:
            raise ToolError(code="LAW_NOT_FOUND",
                            payload={"name": e.name, "suggestions": e.suggestions})
        return [v.to_dict() for v in queries.law_history(conn, law_id)]

    mcp.tool(description=_full_docstring(history))(history)
    handle._tools["history"] = history

    # ─────────────────── amendments_in_period (Phase 2) ──────────────

    def amendments_in_period(from_date: str, to_date: str) -> list[dict]:
        """List every dated amendment across the whole corpus in a period.

        Args:
            from_date: ISO 8601 start date (inclusive).
            to_date: ISO 8601 end date (inclusive).

        Returns:
            A list of {law_id, title, date, dv_issue}, oldest first —
            every act amended on a DV date within the period. Useful for
            "what changed in Bulgarian law between X and Y?" research.

        Raises:
            INVALID_DATE_RANGE: when from_date is later than to_date.
        """
        return [a.to_dict()
                for a in queries.amendments_in_period(conn, from_date, to_date)]

    mcp.tool(description=_full_docstring(amendments_in_period))(amendments_in_period)
    handle._tools["amendments_in_period"] = amendments_in_period

    # ─────────────────── diff (Phase 2) ──────────────────────────────

    def diff(law: str, date1: str, date2: str) -> str:
        """Return a git diff of an act's text between two dates.

        Args:
            law: The act's title, slug, or identificador (see get_law).
            date1: ISO 8601 start date.
            date2: ISO 8601 end date.

        Returns:
            The unified `git diff` of the act between the versions in
            force at date1 and date2. When the corpus holds a single
            consolidated version (the current state for most acts), a
            clear bilingual "single consolidated version held" note is
            returned instead of an empty diff. Real diffs appear once
            additional versions are committed (corpus re-scrape / Phase 4).

        Raises:
            INVALID_DATE_RANGE: when date1 is later than date2.
            NO_VERSION_AT_DATE: when a date precedes the act's earliest
                recorded version.
        """
        try:
            law_id = queries.resolve_name_to_law_id(conn, law)
        except queries.AmbiguousName as e:
            raise ToolError(code="AMBIGUOUS_NAME",
                            payload={"name": e.name, "candidates": e.candidates})
        except queries.LawNotFound as e:
            raise ToolError(code="LAW_NOT_FOUND",
                            payload={"name": e.name, "suggestions": e.suggestions})
        try:
            return queries.diff_law_versions(
                conn, handle._corpus, law_id, date1, date2)
        except queries.NoVersionAtDate as e:
            raise ToolError(code="NO_VERSION_AT_DATE", payload={
                "law_id": e.law_id, "date": e.date,
                "earliest_available": e.earliest_available,
                "latest_available": e.latest_available,
            })

    mcp.tool(description=_full_docstring(diff))(diff)
    handle._tools["diff"] = diff
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/mcp_server/test_temporal_tools.py -v`
Expected: PASS (all 5).

- [ ] **Step 5: Commit**

```bash
git add mcp_server/server.py tests/mcp_server/test_temporal_tools.py
git commit -m "feat(server): register history / amendments_in_period / diff tools (Phase 2)"
```

---

## Task 8: Regenerate `tools.json` with all 6 tools

**Files:**
- Regenerate: `tools.json`
- Test: `tests/mcp_server/test_export_tools.py`

**Interfaces:**
- Consumes: the now-registered 6 tools. Produces the published artifact downstream clients read.

- [ ] **Step 1: Confirm the parity test currently fails**

Run: `.venv/bin/python -m pytest tests/mcp_server/test_export_tools.py -v`
Expected: FAIL — committed `tools.json` has 3 tools, live schema now has 6.

- [ ] **Step 2: Regenerate the artifact**

```bash
.venv/bin/python -m mcp_server.export_tools --output tools.json
```

Expected stdout: `Wrote tools.json (version=1.1.0, 6 tools, 10 error codes).`

- [ ] **Step 3: Run the parity test to verify it passes**

Run: `.venv/bin/python -m pytest tests/mcp_server/test_export_tools.py -v`
Expected: PASS.

- [ ] **Step 4: Commit**

```bash
git add tools.json
git commit -m "chore(tools): regenerate tools.json — 6 tools, version 1.1.0 (Phase 2)"
```

---

## Task 9: End-to-end FastMCP transport coverage

**Files:**
- Modify: `tests/mcp_server/test_tools_e2e.py`
- Test: same file

**Interfaces:**
- Consumes: the registered tools through `fastmcp.Client(handle.mcp)` (real JSON-RPC serialization), confirming the tools list and a representative call survive transport.

- [ ] **Step 1: Write the failing test**

Read the existing `tests/mcp_server/test_tools_e2e.py` to match its client-construction pattern, then add:

```python
@pytest.mark.asyncio
async def test_e2e_lists_six_tools(e2e_app):
    from fastmcp import Client
    async with Client(e2e_app.mcp) as client:
        tools = await client.list_tools()
        names = {t.name for t in tools}
    assert names == {"get_law", "search", "get_article",
                     "history", "amendments_in_period", "diff"}


@pytest.mark.asyncio
async def test_e2e_history_roundtrips(e2e_app):
    from fastmcp import Client
    async with Client(e2e_app.mcp) as client:
        result = await client.call_tool("history", {"law": "100"})
    # FastMCP wraps structured output; assert the timeline shape survives.
    assert result.data[-1]["operation"] == "consolidated"
```

(Match `e2e_app` to whatever fixture name the existing file uses; reuse its corpus + amendments seeding. If the existing e2e fixture doesn't seed `amendments`, add one `INSERT INTO amendments ... target_law='zakon-a' ...` line to it, mirroring Task 7's `app` fixture.)

- [ ] **Step 2: Run test to verify it fails (then passes after wiring)**

Run: `.venv/bin/python -m pytest tests/mcp_server/test_tools_e2e.py -v`
Expected: the list-tools test fails first if the fixture predates the new tools; once the fixture builds the current `build_app`, it passes. Adjust the fixture, not the production code.

- [ ] **Step 3: Commit**

```bash
git add tests/mcp_server/test_tools_e2e.py
git commit -m "test(e2e): cover the three Phase 2 temporal tools through FastMCP transport"
```

---

## Task 10: Phase 2 close-out — governance docs

**Files:**
- Modify: `docs/sync/ACTIVE.md`, `docs/sync/DECISIONS.md`, `docs/frs/INDEX.md`, `.ahelia/protected-surfaces.yaml`
- No test (documentation task)

- [ ] **Step 1: Rebuild the real index and smoke-test against the live corpus**

```bash
.venv/bin/python -m index.build --corpus . --db catalog.db
.venv/bin/python -m pytest -q
```

Expected: index rebuild logs `indexed 3573 acts`; full suite green (was 287, now +~16 new tests).

Then a manual smoke check of the new tools against a real, heavily-amended act (e.g. ЗОП):

```bash
.venv/bin/python - <<'PY'
import sqlite3
from pathlib import Path
from mcp_server.server import build_app
conn = sqlite3.connect("catalog.db"); conn.row_factory = sqlite3.Row
app = build_app(conn, Path("."))
zop = app.call_tool_sync("history", {"law": "Закон за обществените поръчки"})
print("ЗОП amendment events:", len([v for v in zop if v["operation"] == "amendment"]))
print("latest consolidated commit:", zop[-1]["commit_hash"][:8])
PY
```

Expected: a non-trivial count of amendment events (ЗОП has many) and a real commit hash — confirming `history()` delivers value on the live corpus today.

- [ ] **Step 2: Update `docs/frs/INDEX.md`**

Change the FR-001 row Status from `Backlog` to `**Done (2026-06-21)**` with a one-line resolution note: amendments table populated from amendment_history; history/diff/amendments_in_period tools shipped; honest single-version semantics for diff/get_law(date) pending a write-side (re-scrape / Phase 4). Add FR-018 note if range-expansion still deferred (unchanged).

- [ ] **Step 3: Append a decision to `docs/sync/DECISIONS.md`**

Add row: `| D-031 | 2026-06-21 | Phase 2 honest single-version temporal semantics | history()/amendments_in_period() backed by amendments table from amendment_history (full value now); diff()/get_law(date) return correct-but-limited results until a write-side accumulates more text versions — chose this over fabricating law_versions rows pointing historical valid_from at the bootstrap commit, which would make get_law(date) return current text and falsely claim it was in force on a past date | Active |`

- [ ] **Step 4: Update `docs/sync/ACTIVE.md`**

Set current phase to "Phase 2 — complete on `main` 2026-06-21"; note the 3 new tools, the test count, and that the time-travel tools (`diff`, historical `get_law`) are wired but await the parallel corpus re-scrape (`docs/sync/HANDOFFS/2026-06-21-corpus-rescrape-refresh.md`) to show multi-version output. Move Phase 2 out of "Pending".

- [ ] **Step 5: Update `.ahelia/protected-surfaces.yaml`**

In the Surface 3 block, move the three `phase_2:` signatures from the "Not yet implemented" note into the implemented set (or relabel the comment to "implemented 2026-06-21"), keeping the exact signatures.

- [ ] **Step 6: Commit**

```bash
git add docs/sync/ACTIVE.md docs/sync/DECISIONS.md docs/frs/INDEX.md .ahelia/protected-surfaces.yaml
git commit -m "docs: Phase 2 temporal index close-out (FR-001 Done; D-031)"
```

---

## Self-Review

**Spec coverage (against FR-001 / delivery-contract Phase 2 DoD / protected-surfaces phase_2):**
- `law_versions` populated from git history → already done in Phase 1b (one row/act); amendment events now in `amendments` (Task 1). ✅
- `history()` tool working → Tasks 4, 7, 9. ✅
- `diff()` tool working → Tasks 6, 7, 9. ✅
- `amendments_in_period()` tool → Tasks 5, 7, 9 (this tool is in the design/protected-surfaces though not the terse DoD checklist). ✅
- Date-based retrieval returns correct historical version → `get_law(date)` already wired in 1b.1; honest semantics documented (D-031). Limited to one version until a write-side lands more — explicitly out of Phase 2 scope per the design discussion. ✅
- DEFERRED.md gate: the only open deferral (FR-014) targets Phase 4, so Phase 2 promotion is clean — no DEFERRED rows to resolve. ✅
- Protected signatures matched verbatim (Global Constraints). ✅

**Placeholder scan:** every code step contains complete code; every command has expected output. No TBD/TODO. ✅

**Type consistency:** `VersionEntry`/`AmendmentEntry` field names are identical across Task 2 (definition), Tasks 4–5 (construction), and Tasks 7/9 (`.to_dict()` consumption). `law_history`/`amendments_in_period`/`diff_law_versions` names match between queries (Tasks 4–6) and server (Task 7). `INVALID_DATE_RANGE` spelled identically in errors, docs, and both raising sites. ✅

**Known non-blocking note:** Task 9's exact fixture name (`e2e_app`) and FastMCP result accessor (`result.data`) must be reconciled against the existing `test_tools_e2e.py` at execution time — the step says to read that file first and match its pattern. This is the one place the plan defers to the existing file's convention rather than inventing one.
