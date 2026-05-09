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

**Budgets are higher than `test_budgets.py` for `search`** because
cold-cache FTS5 has to read index pages from disk on every fresh
connection: empirically, the same multi-word queries that run in
~33 ms warm take ~100–160 ms cold on this hardware. The cold
budget for `search` is therefore set at 250 ms — wide enough to
absorb hardware variance without losing regression-protection on
genuine pathological cases (e.g., the FR-016 "наредба" case at
437 ms would still fail this budget). The `get_law` and
`get_article` budgets stay at the steady-state numbers because
they're SQL-only, not FTS5, and don't suffer the same cold-cache
penalty (measured at 5 ms / 0.3 ms cold).
"""

import logging
import pathlib
import sqlite3
import time

import pytest

REPO = pathlib.Path(__file__).resolve().parent.parent.parent
DB = REPO / "catalog.db"

# search_cold_p95 is structurally higher than the warm budget — see
# module docstring. The 250 ms ceiling catches the historical
# pathological case (FR-016 "наредба" at 437 ms) and any future
# regression that would push cold-call latency into the half-second
# range, without being so tight that ordinary cold-cache variance
# trips it.
COLD_BUDGETS = {
    "search_cold_p95":          0.250,  # 250 ms cold; warm budget is 100 ms
    "get_law_cold_current_p95": 0.100,
    "get_article_cold_p95":     0.050,
}

# Smaller query set than test_budgets.py REPRESENTATIVE_QUERIES — cold
# calls open and close a fresh sqlite connection, which is the load-
# bearing cost we measure. 10 calls give a stable p95.
# Excludes the 5 stop-words (FR-016 reject path doesn't reach FTS5,
# so they wouldn't measure search latency anyway).
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


# The OS-cache warmer is in `tests/perf/conftest.py` (session-scoped,
# autouse) so both this file and test_budgets.py share the same
# pre-warmed page set. See the conftest module docstring for why.


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
