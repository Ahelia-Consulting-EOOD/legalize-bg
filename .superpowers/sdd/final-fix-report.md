# Final Fix Report — branch `fix/parser-data-loss`

Date: 2026-06-30

## Commits

| Hash | Description |
|------|-------------|
| `e5249276` | fix(refresh): inject coverage_gate into _fetch_assemble; regenerate zop/gpk goldens |
| `b70a0e09` | feat(coverage/refresh): items I1-I3, T5-#1, T5-#2, T4-#5 quality pass |

---

## Item 1 — [BLOCKER C1] Green the 4 failing orchestrator tests

**Root cause confirmed:** `FakeClient.fetch_soup(doc_id)` returns the int `doc_id` as an opaque token. `_fetch_assemble` called `uncovered_legal_text(soup=int, body)` → `content_region(int)` → `int.find_all(...)` → `AttributeError`, caught by `except Exception` → all 4 test acts misclassified as errors.

**Fix applied (`refresh.py`):**
- Added `coverage_gate=uncovered_legal_text` parameter to `_fetch_assemble(...)`.
- Added `coverage_gate=uncovered_legal_text` parameter to `refresh(...)`.
- Threaded `coverage_gate` from `refresh(...)` into both `_fetch_assemble(...)` call sites (ADDED and EXISTING loops).
- Updated the 4 failing orchestrator tests (`test_refresh_added_existing_missing_end_to_end`, `test_refresh_added_nonlaws_act_lands_in_corpus_dir_not_tree_slug`, `test_refresh_unchanged_act_is_skipped_no_commit`, `test_refresh_popravka_when_body_changed_history_did_not`) to pass `coverage_gate=lambda soup, body: {"uncovered_chars": 0, "buckets": {}}`.

**Result:** All 8 `tests/refresh/test_orchestrator.py` tests pass. The real default gate (`uncovered_legal_text`) is unchanged in production.

---

## Item 2 — [BLOCKER] Regenerate stale parser goldens

**Command:** `REGENERATE_GOLDENS=1 .venv/bin/python -m pytest tests/index/test_provisions.py::test_golden_provisions_per_fixture -q`

**Before/after counts (counts went UP — more complete):**

| Fixture | total_rows before→after | article_rows before→after | alinea_rows before→after |
|---------|------------------------|--------------------------|--------------------------|
| zop     | 1439 → 1443 (+4)       | 285 → 287 (+2)           | 1154 → 1156 (+2)         |
| gpk     | 2184 → 2231 (+47)      | 719 → 745 (+26)          | 1465 → 1486 (+21)        |

**Result:** All 6 parametrized golden tests pass without `REGENERATE_GOLDENS`.

---

## Item 3 — [I1] Add refresh gate tests

**New file:** `tests/refresh/test_gate.py` (11 tests for items 3+4+6, created TDD-first)

Tests cover:
- ADDED act gate-fail: not written, not committed, state=`gate-fail`, appears in `report.gate_failures`, appears in `gate-report.json`.
- EXISTING act gate-fail: file not overwritten, state=`gate-fail`, appears in `report.gate_failures`.
- Passing-gate counterpart for ADDED and EXISTING acts.

All 11 gate tests passed after item 1 fix was in place.

---

## Item 4 — [I3] Fix resumed-refresh gate-report

**Bug confirmed (RED test):** `test_resume_gate_report_includes_prior_gate_fail_entries` failed because the second-run `gate-report.json` was overwritten with an empty list (skipped doc_ids don't appear in `report.gate_failures`).

**Fix applied (`refresh.py`):**
1. At the start of the non-dry-run path, load the prior `gate-report.json` into `prior_gate_by_doc: dict[int, dict]`.
2. At the end, before writing `gate-report.json`, merge prior entries: for every doc_id in `state` with disposition `"gate-fail"` that was NOT processed this run (i.e., not in `current_fail_ids`), include its record from `prior_gate_by_doc`.
3. The merged list is written as the new `gate-report.json`.
4. Log line updated to report how many entries were carried from the prior run.

**Result:** `test_resume_gate_report_includes_prior_gate_fail_entries` passes (GREEN).

---

## Item 5 — [I2] Document + guard the shared-denylist seam

**Standing test added** (`tests/fetcher/bg/test_coverage.py::test_denylist_seam_no_spine_inside_chrome`):
- Parametrized over all 6 act fixtures.
- For each fixture: finds all denylisted-class elements STRICTLY INSIDE the content region; asserts none contain a descendant with a spine class.
- Returns 0 violations across all 6 fixtures today.

**Docstring added** to `fetcher/bg/coverage.py` module docstring: explains the shared-denylist boundary, names the standing test, and states that any future violation requires IMPLEMENTATION-PREFLIGHT.

---

## Item 6 — [Minor T5-#1] Validate threshold early

**Fix applied in `refresh.py` and `bootstrap.py`:**
```python
_threshold_raw = os.environ.get("LEGALIZE_COVERAGE_THRESHOLD", "64")
try:
    threshold = int(_threshold_raw)
except (ValueError, TypeError):
    log.warning("Invalid LEGALIZE_COVERAGE_THRESHOLD value %r — falling back to default 64", _threshold_raw)
    threshold = 64
```

**Test added** (`test_bad_threshold_env_var_falls_back_to_64` in `tests/refresh/test_gate.py`):
- Sets `LEGALIZE_COVERAGE_THRESHOLD=not-a-number` via `monkeypatch.setenv`.
- Verifies `refresh()` does not raise and the act is processed normally (fallback=64).
- Was RED before the fix (raised `ValueError`), GREEN after.

---

## Item 7 — [Minor T5-#2] Dedup the gate-record dict

**Extracted `make_gate_record(doc_id, slug, title, gate) -> dict`** into `fetcher/bg/coverage.py` with docstring noting it is a protected surface.

**Updated all 3 call sites:**
- `bootstrap.py` (1 site): imports `make_gate_record` from `fetcher.bg.coverage`; inline dict removed.
- `refresh.py` ADDED loop (1 site): inline dict removed.
- `refresh.py` EXISTING loop (1 site): inline dict removed.

---

## Item 8 — [Minor T4-#5] Decouple coverage from `_content_region`

**Promoted to module-level** in `fetcher/bg/text_parser.py`:
```python
def content_region(soup: BeautifulSoup) -> tuple[Tag, bool]:
    """..."""
    # (former body of _content_region)
```

**`HtmlToMarkdown._content_region` now delegates:**
```python
def _content_region(self, soup):
    """Delegate to module-level content_region() for backward compatibility."""
    return content_region(soup)
```

**`coverage.py` updated:**
```python
from fetcher.bg.text_parser import CHROME_DENYLIST, CLASS_MAP, content_region
# ...
region, _ = content_region(soup)  # was: HtmlToMarkdown()._content_region(soup)
```

**Two new tests** lock the contract:
- `test_content_region_is_importable_and_callable`: imports and calls `content_region` from `text_parser`, verifies `has_spine=True` and content in region.
- `test_content_region_matches_private_method`: asserts `content_region(soup)` and `HtmlToMarkdown()._content_region(soup)` return the same object (same region id, same has_spine).

Both tests were RED before (ImportError), GREEN after.

---

## Final Full-Suite Result

```
3 failed, 428 passed in 78.78s (0:01:18)
```

**Remaining failures (all 3 are pre-existing, NOT caused by this branch):**

| Test | Reason |
|------|--------|
| `tests/mcp_server/test_data_quality_acceptance.py::test_72_null_pub_date_count_matches_canonical_data_model` | Reads unrebuilt `catalog.db` |
| `tests/perf/test_budgets.py::test_search_p95` | Load-flaky perf budget |
| `tests/perf/test_cold_calls.py::test_search_cold_p95` | Load-flaky perf budget |

Zero branch-caused failures remain.
