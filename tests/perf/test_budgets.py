"""Performance regression budgets per design doc §9.

Phase 1b.1: SOFT assertions — log a warning on regression but pass.
Phase 1b.2 (D-027 hard-promotion): assertions FAIL the test on
regression so CI catches drift. The cold-call companion file
`test_cold_calls.py` adds first-user-hit coverage that this warm
sequential pattern alone can't see.

All budgets measured against the live catalog.db (3,573 acts, ~150k
article rows + ~300k alinea rows). Skipped when catalog.db is missing.
"""

import logging
import pathlib
import sqlite3
import time

import pytest

REPO = pathlib.Path(__file__).resolve().parent.parent.parent
DB = REPO / "catalog.db"

# Budgets in seconds. Per design §9:
#   search p95            < 100 ms  full-corpus FTS5 + two-tier ranker
#   get_law (current) p95 < 100 ms  fast path: working-tree read
#   get_article p95       < 50 ms   SQL-only lookup, no file I/O
BUDGETS = {
    "search_p95":          0.100,
    "get_law_current_p95": 0.100,
    "get_article_p95":     0.050,
}

REPRESENTATIVE_QUERIES = [
    "обществени поръчки",
    "електронно управление",
    # Single-word category queries ("наредба", "закон", "правилник",
    # "кодекс", "постановление") were removed as of Phase 1b.2 because
    # FR-016 rejects them before FTS5 — they no longer measure search
    # latency, only the reject path. The remaining queries are all
    # multi-word OR non-category single words representative of real
    # FTS5 work.
    "административно",
    "транспорт",
    "съд",
    "образование",
    "здравеопазване",
    "договор",          # multi-domain term, hits across categories
    "общини",           # municipal cross-cut
    "данък",            # finance
]


@pytest.fixture(scope="module")
def conn():
    if not DB.exists():
        pytest.skip(
            f"catalog.db missing at {DB}; run `python -m index.build` "
            "to enable perf tests."
        )
    c = sqlite3.connect(str(DB), check_same_thread=False)
    c.row_factory = sqlite3.Row
    return c


def _p95(samples: list[float]) -> float:
    samples = sorted(samples)
    idx = min(int(len(samples) * 0.95), len(samples) - 1)
    return samples[idx]


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


def test_search_p95(conn):
    """50 representative searches; p95 budget 100 ms."""
    from mcp_server.queries import full_text_search

    queries = REPRESENTATIVE_QUERIES * 5  # 50 calls
    durations: list[float] = []
    for q in queries:
        t0 = time.monotonic()
        full_text_search(conn, q, limit=20)
        durations.append(time.monotonic() - t0)
    _hard_assert(_p95(durations), "search_p95")


def test_get_law_current_p95(conn):
    """20 lookups by identificador against the live catalog. Each
    triggers resolve_name → version_at_date but NOT the working-tree
    file read (which the test of `get_law` tool would, this is the
    queries-layer-only timing)."""
    from mcp_server.queries import (
        resolve_name_to_law_id,
        version_with_warnings,
    )

    # Pull 20 random doc_ids from the catalog
    doc_ids = [
        str(r["doc_id"]) for r in conn.execute(
            "SELECT doc_id FROM laws WHERE doc_id != 0 LIMIT 20"
        ).fetchall()
    ]
    durations: list[float] = []
    for did in doc_ids:
        t0 = time.monotonic()
        law_id = resolve_name_to_law_id(conn, did)
        version_with_warnings(conn, law_id, date=None)
        durations.append(time.monotonic() - t0)
    _hard_assert(_p95(durations), "get_law_current_p95")


def test_get_article_p95(conn):
    """20 article_lookup calls — pure SQL, fastest budget (50ms)."""
    from mcp_server.queries import article_lookup

    pairs = conn.execute(
        "SELECT law_id, article FROM provisions "
        "WHERE paragraph IS NULL LIMIT 20"
    ).fetchall()
    durations: list[float] = []
    for r in pairs:
        t0 = time.monotonic()
        article_lookup(conn, r["law_id"], article=r["article"],
                       paragraph=None, date=None)
        durations.append(time.monotonic() - t0)
    _hard_assert(_p95(durations), "get_article_p95")
