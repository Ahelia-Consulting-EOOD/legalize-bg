"""Persistent-connection warm-path budget (FR-027 / D-051).

`mcp_server/__main__.py:main()` opens exactly ONE sqlite3 connection for
the server process's entire lifetime, applies two read-only pragmas
(`mmap_size` / `cache_size`), and reuses that connection for every tool
call. Task 13's Experiment B (`docs/research/2026-07-02-fr027-search-perf.md`)
found this persistent-connection-with-pragmas model turns the two
pathological queries that never warmed down on a plain connection
("лични данни", "административни нарушения") into ~17-24ms warm calls
— a ~300-400x improvement — but that finding was never encoded as a
test: `test_budgets.py` shares one connection WITHOUT the pragmas, and
`test_cold_calls.py` opens a fresh connection per call (by design, to
measure first-touch latency) so neither exercises the pragma'd
persistent-connection path `__main__.py` actually runs in production.

This file closes that gap: one connection, opened exactly like
`main()` does, reused across repeated calls to the same queries Task 13
measured. "административни нарушения" still falls through to tier 2
(title-tier hits < the D-051 gating threshold even after the Task 14
gating change — see `index/fts.py:search_fts`) so it is the query that
actually exercises the pragma win here; "лични данни" and "обществени
поръчки" are included because Task 13 measured them in the same
experiment and now happen to be title-served post-gating (fast for a
different reason) — keeping all three means a regression in EITHER
mechanism (the pragmas or the tier-2 gate) trips this test.
"""

import pathlib
import sqlite3
import time

import pytest

pytestmark = pytest.mark.perf

REPO = pathlib.Path(__file__).resolve().parent.parent.parent
DB = REPO / "catalog.db"

# Task 13 Experiment B, first-in-process pragma group (order-controlled,
# 2 runs): "лични данни" warm 24/24ms, "административни нарушения" warm
# 20/18ms — ceiling 24ms. D-051 ratified rule: measured p95 × 1.5.
# 24ms × 1.5 = 36ms.
WARM_PERSISTENT_BUDGET = 0.036  # 36 ms
# FR-032 / D-057 re-ratification (2026-07-24): re-measured with this
# file's exact methodology on the v5 per-segment pipeline (two-phase
# tier 2, post-truncation snippet enrichment): p95 = 8.4 ms, max
# 8.8 ms, p50 0.1 ms on the reference machine. The 36 ms D-051 budget
# holds with >4x headroom and stays unchanged. (During implementation
# this budget caught a real 272 ms regression — snippet() computed
# over the full 500-row overscan window — which forced the two-phase
# design. Working budget, not a relic.)

QUERIES = (
    "лични данни",
    "административни нарушения",
    "обществени поръчки",
)


def _p95(samples: list[float]) -> float:
    samples = sorted(samples)
    idx = min(int(len(samples) * 0.95), len(samples) - 1)
    return samples[idx]


@pytest.fixture
def persistent_conn():
    if not DB.exists():
        pytest.skip(
            f"catalog.db missing at {DB}; run `python -m index.build` "
            "to enable perf tests."
        )
    # Mirrors mcp_server/__main__.py:main() exactly: one connection for
    # the fixture's lifetime, same two pragmas, same open() call shape.
    conn = sqlite3.connect(str(DB), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA mmap_size = 1073741824")
    conn.execute("PRAGMA cache_size = -65536")
    yield conn
    conn.close()


def test_search_warm_persistent_p95(persistent_conn):
    """One persistent connection (server's real model), each query
    primed with an unmeasured first call (the documented one-time
    per-process cost), then 20 interleaved warm calls per query. p95
    across all warm calls must stay under the D-051 budget."""
    from mcp_server.queries import full_text_search

    for q in QUERIES:
        full_text_search(persistent_conn, q, limit=20)  # unmeasured priming call

    durations: list[float] = []
    for _ in range(20):
        for q in QUERIES:
            t0 = time.monotonic()
            full_text_search(persistent_conn, q, limit=20)
            durations.append(time.monotonic() - t0)

    p95 = _p95(durations)
    if p95 > WARM_PERSISTENT_BUDGET:
        pytest.fail(
            f"PERF: search_warm_persistent_p95 p95={p95:.4f}s exceeds "
            f"budget {WARM_PERSISTENT_BUDGET:.4f}s (D-051 HARD). "
            "Investigate before merge — this is the actual production "
            "server's connection model (persistent, pragma'd)."
        )
