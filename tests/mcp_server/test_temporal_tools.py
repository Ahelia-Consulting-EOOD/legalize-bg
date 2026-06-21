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
