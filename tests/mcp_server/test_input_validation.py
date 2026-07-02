"""Empty-string dates were silently treated as 'today' (truthiness) and
malformed dates fell through to string comparison; free-text params had
no length bound (review 2026-07-02 P2s)."""

import pytest

from mcp_server.errors import ToolError
from mcp_server import queries


@pytest.mark.parametrize("bad", ["", "  ", "2020-13-45", "vinagi", "2020/01/01"])
def test_malformed_date_raises_invalid_date(populated_conn, bad):
    with pytest.raises(ToolError) as exc:
        queries.version_at_date(populated_conn, "zakon-a", bad)
    assert exc.value.code == "INVALID_DATE"
    assert exc.value.payload["expected"] == "YYYY-MM-DD"


def test_none_date_still_means_today(populated_conn):
    assert queries.version_at_date(populated_conn, "zakon-a", None)


def test_overlong_query_rejected_as_too_broad(conn):
    with pytest.raises(ToolError) as exc:
        queries.full_text_search(conn, "закон " * 200)
    assert exc.value.code == "QUERY_TOO_BROAD"


def test_overlong_name_raises_law_not_found(conn):
    with pytest.raises(queries.LawNotFound):
        queries.resolve_name_to_law_id(conn, "х" * 1000)
