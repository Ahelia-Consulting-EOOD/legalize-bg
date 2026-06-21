"""Tests for 2.x-c structured logging + per-tool-call metrics."""

import logging

import pytest

from mcp_server.errors import ToolError
from mcp_server.server import build_app


@pytest.fixture
def app(populated_conn, tmp_path):
    return build_app(conn=populated_conn, corpus_root=tmp_path)


def test_metrics_track_successful_calls(app):
    app.call_tool_sync("history", {"law": "100"})
    app.call_tool_sync("history", {"law": "100"})
    snap = app.metrics_snapshot()
    assert snap["history"]["calls"] == 2
    assert snap["history"]["errors"] == 0
    assert snap["history"]["avg_ms"] >= 0.0
    assert snap["history"]["last_ms"] >= 0.0


def test_metrics_track_errors_with_codes(app):
    with pytest.raises(ToolError):
        app.call_tool_sync("get_law", {"name": "напълно непознат акт"})
    snap = app.metrics_snapshot()
    assert snap["get_law"]["calls"] == 1
    assert snap["get_law"]["errors"] == 1
    assert snap["get_law"]["error_codes"].get("LAW_NOT_FOUND") == 1


def test_metrics_snapshot_is_readonly_copy(app):
    app.call_tool_sync("history", {"law": "100"})
    snap = app.metrics_snapshot()
    snap["history"]["calls"] = 999
    snap["history"]["error_codes"]["X"] = 1
    # Internal state must be unaffected by mutating the snapshot.
    assert app.metrics_snapshot()["history"]["calls"] == 1
    assert "X" not in app.metrics_snapshot()["history"]["error_codes"]


def test_successful_tool_call_emits_structured_info_log(app, caplog):
    with caplog.at_level(logging.INFO, logger="mcp_server.server"):
        app.call_tool_sync("history", {"law": "100"})
    msgs = [r.getMessage() for r in caplog.records]
    assert any("tool=history" in m and "ok=true" in m and "duration_ms=" in m
               for m in msgs), f"no structured success log: {msgs}"


def test_failed_tool_call_emits_warning_log_with_code(app, caplog):
    with caplog.at_level(logging.WARNING, logger="mcp_server.server"):
        with pytest.raises(ToolError):
            app.call_tool_sync("get_law", {"name": "напълно непознат акт"})
    msgs = [r.getMessage() for r in caplog.records]
    assert any("tool=get_law" in m and "ok=false" in m
               and "code=LAW_NOT_FOUND" in m for m in msgs), \
        f"no structured error log: {msgs}"
