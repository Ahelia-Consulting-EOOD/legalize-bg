# tests/mcp_server/test_queries_listing.py
"""FR-028: list_laws + corpus_stats power GET /api/v1/laws and /stats.
They are plain read-only SELECTs over `laws` + `law_versions`."""

import pytest

from mcp_server import queries


def test_list_laws_returns_total_and_items(populated_conn):
    out = queries.list_laws(populated_conn)
    assert set(out.keys()) == {"total", "items"}
    assert out["total"] >= 1
    first = out["items"][0]
    assert set(first.keys()) == {
        "law_id", "identificador", "title", "category", "status",
        "first_version", "latest_version", "version_count",
    }


def test_list_laws_category_filter_and_pagination(populated_conn):
    all_laws = queries.list_laws(populated_conn)
    cat = all_laws["items"][0]["category"]
    filtered = queries.list_laws(populated_conn, category=cat)
    assert filtered["total"] <= all_laws["total"]
    assert all(i["category"] == cat for i in filtered["items"])
    page = queries.list_laws(populated_conn, limit=1, offset=0)
    assert len(page["items"]) == 1
    assert page["total"] == all_laws["total"]  # total ignores pagination


def test_list_laws_caps_limit(populated_conn):
    out = queries.list_laws(populated_conn, limit=100000)
    assert len(out["items"]) <= 200


def test_list_laws_tie_break_is_stable_across_pagination(populated_conn):
    # PR review fix #5: naredba-7 / naredba-7-2 (populated_conn, §7.1)
    # share the exact title "Наредба № 7 за нещо". ORDER BY l.title
    # alone leaves row order among ties unspecified, so a client walking
    # pages with limit=1 could in principle skip or repeat a row at that
    # boundary; the fix adds `l.law_id` (unique, stable) as a secondary
    # sort key. Walk every row one at a time and confirm each law_id —
    # including both title-twins — is seen exactly once.
    total = queries.list_laws(populated_conn)["total"]
    seen = []
    for offset in range(total):
        page = queries.list_laws(populated_conn, limit=1, offset=offset)
        assert len(page["items"]) == 1
        seen.append(page["items"][0]["law_id"])
    assert len(seen) == len(set(seen)) == total
    assert {"naredba-7", "naredba-7-2"} <= set(seen)


def test_corpus_stats_shape(populated_conn):
    s = queries.corpus_stats(populated_conn)
    assert set(s.keys()) == {
        "total_acts", "by_category", "by_status",
        "multi_version_acts", "latest_version_date",
    }
    assert s["total_acts"] == sum(s["by_category"].values())
