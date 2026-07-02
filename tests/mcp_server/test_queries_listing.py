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


def test_corpus_stats_shape(populated_conn):
    s = queries.corpus_stats(populated_conn)
    assert set(s.keys()) == {
        "total_acts", "by_category", "by_status",
        "multi_version_acts", "latest_version_date",
    }
    assert s["total_acts"] == sum(s["by_category"].values())
