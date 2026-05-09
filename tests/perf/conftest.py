"""Shared fixtures for perf tests — primarily, a session-scoped warmer
that pre-loads catalog.db pages into the OS file cache.

Without this warming step, the very first FTS5 query against the live
1 GB catalog reads index pages from disk and the resulting cold-call
latency dominates p95 measurements (~400 ms first-call, ~30 ms
subsequent calls within the same process). That's a disk-I/O regression
signal, not a SQLite/FTS5 regression signal — and it's not portable
across hardware.

After warming, the perf tests measure two distinct things:
  - test_budgets.py — warm-cache, sequential-on-one-connection p95.
    This is "steady-state running server" performance.
  - test_cold_calls.py — fresh-connection-per-call p95 with warm OS
    cache. This is "first user hit after server startup" performance.

Both budgets stay separate (test_budgets at 100/100/50 ms;
test_cold_calls at 250/100/50 ms) because they measure structurally
different things, but neither should be charging for first-touch disk
I/O.
"""

import pathlib
import sqlite3

import pytest

REPO = pathlib.Path(__file__).resolve().parent.parent.parent
DB = REPO / "catalog.db"

# Same query set as both test files use. Listed here once so the
# warmer covers exactly the FTS5 page set the tests touch.
_WARM_QUERIES = (
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
)


@pytest.fixture(scope="session", autouse=True)
def _warm_perf_caches():
    """Warm OS file cache and SQLite-session-level FTS5 pages for the
    queries the perf tests will time. Runs once at the very start of
    the perf-test session; no-op if catalog.db is missing (the tests
    themselves skip in that case)."""
    if not DB.exists():
        return
    from mcp_server.queries import full_text_search

    c = sqlite3.connect(str(DB), check_same_thread=False)
    c.row_factory = sqlite3.Row
    # Touch the FTS5 page set for every query the perf suite cares
    # about — different multi-word queries hit different B-tree pages.
    for q in _WARM_QUERIES:
        full_text_search(c, q, limit=20)
    # Also warm the SQL-only paths (provisions / laws) so the cold-
    # call get_law / get_article tests aren't paying first-touch I/O.
    c.execute("SELECT COUNT(*) FROM provisions").fetchone()
    c.execute("SELECT COUNT(*) FROM laws").fetchone()
    c.close()
