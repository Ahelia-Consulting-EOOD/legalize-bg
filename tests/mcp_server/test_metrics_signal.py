"""metrics_snapshot() was unreachable in production (never a tool, no
signal handler) — an operator had NO runtime observability over stdio
(review 2026-07-02 P1)."""

import json
import logging
import signal
import sqlite3
from pathlib import Path

from mcp_server.__main__ import _install_metrics_signal_handler
from mcp_server.server import build_app


def test_sigusr1_handler_logs_metrics_json(caplog):
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    handle = build_app(conn, corpus_root=Path("."))
    handler = _install_metrics_signal_handler(handle)
    with caplog.at_level(logging.INFO, logger="mcp_server"):
        handler(signal.SIGUSR1, None)   # invoke directly — no real signal
    line = next(r for r in caplog.records if "metrics_snapshot" in r.message)
    payload = json.loads(line.message.split("metrics_snapshot: ", 1)[1])
    assert isinstance(payload, dict)
