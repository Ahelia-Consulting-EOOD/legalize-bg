"""FR-031 Phase B: the `--transport` flag selects the MCP transport and,
for network transports, the per-call connection model landed in Phase A.

- stdio stays the DEFAULT and keeps the persistent shared connection +
  `_db_lock` (zero behavior change for local/global users; perf budgets and
  DEFERRED row D-2026-07-02-01 depend on the warm persistent connection).
- network transports (http / sse / streamable-http) run over HTTP and build
  the app with `db_path=` → per-call `mode=ro` connections (FR-029), so
  concurrent remote clients don't serialize behind one lock.

The over-the-wire smoke test drives the real streamable-http protocol through
an in-process ASGI transport (`FastMCP.http_app()` + httpx ASGITransport) — a
genuine HTTP round-trip with no sockets or background threads to flake on.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

from index.build import build
import mcp_server.__main__ as m


def _commit(corpus: Path, msg: str, date: str) -> None:
    env = dict(os.environ, GIT_AUTHOR_DATE=f"{date}T00:00:00+00:00",
               GIT_COMMITTER_DATE=f"{date}T00:00:00+00:00")
    subprocess.run(["git", "add", "-A"], cwd=corpus, check=True)
    subprocess.run(
        ["git", "-c", "user.email=t@t", "-c", "user.name=t",
         "commit", "-q", "-m", msg], cwd=corpus, check=True, env=env)


@pytest.fixture(scope="module")
def cli_catalog(tmp_path_factory) -> tuple[Path, str]:
    corpus = tmp_path_factory.mktemp("cli-corpus")
    law = corpus / "laws" / "zakon-test.md"
    law.parent.mkdir(parents=True)
    fm = ("---\ntitulo: Закон за тест\nidentificador: 999\n"
          "fecha_publicacion: 2020-01-01\n---\n\n")
    law.write_text(fm + "**Чл. 1.** Съдържание на теста.\n", encoding="utf-8")
    subprocess.run(["git", "init", "-q"], cwd=corpus, check=True)
    _commit(corpus, "[bootstrap] Закон за тест", "2020-01-01")
    db = str(corpus / "catalog.db")
    build(corpus, db)
    return corpus, db


def _patch_run_recorder(monkeypatch):
    """Record how the server transport is launched without blocking."""
    from fastmcp import FastMCP
    calls: list[dict] = []

    def fake_run(self, transport=None, show_banner=None, **kw):
        calls.append({"transport": transport, **kw})

    monkeypatch.setattr(FastMCP, "run", fake_run)
    return calls


def _spy_build_app(monkeypatch):
    """Record how build_app was constructed (conn= vs db_path=)."""
    from mcp_server import server as srv
    real = srv.build_app
    seen: list[dict] = []

    def spy(*a, **k):
        seen.append(dict(k))
        return real(*a, **k)

    monkeypatch.setattr(m, "build_app", spy)
    return seen


def test_stdio_is_default_and_keeps_shared_connection(cli_catalog, monkeypatch):
    """No --transport → stdio (run() with no transport) + shared conn."""
    corpus, db = cli_catalog
    calls = _patch_run_recorder(monkeypatch)
    seen = _spy_build_app(monkeypatch)

    rc = m.main(["--db", db, "--corpus", str(corpus)])

    assert rc == 0
    assert calls == [{"transport": None}]
    assert seen and "conn" in seen[-1] and "db_path" not in seen[-1]


@pytest.mark.parametrize("transport", ["http", "sse", "streamable-http"])
def test_network_transport_selects_transport_and_per_call_conn(
        cli_catalog, monkeypatch, transport):
    """Every network transport → run(transport=..., host, port) and the
    per-call (db_path) connection model, not a shared connection."""
    corpus, db = cli_catalog
    calls = _patch_run_recorder(monkeypatch)
    seen = _spy_build_app(monkeypatch)

    rc = m.main(["--db", db, "--corpus", str(corpus),
                 "--transport", transport,
                 "--host", "127.0.0.1", "--port", "9123"])

    assert rc == 0
    assert calls == [{"transport": transport,
                      "host": "127.0.0.1", "port": 9123}]
    assert seen and "db_path" in seen[-1] and "conn" not in seen[-1]


def test_stdio_ignores_host_port_and_warns(cli_catalog, monkeypatch, caplog):
    """Passing --host/--port with stdio is accepted but ignored (stdio has no
    listener) — the server drops them, keeps the shared conn, and warns so an
    operator isn't misled into thinking they took effect."""
    import logging

    corpus, db = cli_catalog
    calls = _patch_run_recorder(monkeypatch)
    seen = _spy_build_app(monkeypatch)

    with caplog.at_level(logging.WARNING, logger="mcp_server"):
        rc = m.main(["--db", db, "--corpus", str(corpus),
                     "--transport", "stdio",
                     "--host", "0.0.0.0", "--port", "9000"])

    assert rc == 0
    assert calls == [{"transport": None}]  # stdio: host/port dropped
    assert seen and "conn" in seen[-1] and "db_path" not in seen[-1]
    assert any("ignored for the stdio transport" in r.message
               for r in caplog.records)


def test_streamable_http_serves_tools_over_http(cli_catalog):
    """End-to-end: a real MCP client talks to the server over the
    streamable-http protocol (in-process ASGI transport) and gets correct
    tool results — the Phase B smoke sequence the design requires."""
    import asyncio

    import httpx
    from fastmcp import Client
    from fastmcp.client.transports import StreamableHttpTransport

    from mcp_server.server import build_app

    corpus, db = cli_catalog
    handle = build_app(db_path=db, corpus_root=corpus)
    app = handle.mcp.http_app()

    def client_factory(**kwargs):
        # fastmcp passes headers/timeout/auth/follow_redirects; keep them,
        # but route the client at the in-process ASGI app instead of a socket.
        kwargs.pop("transport", None)
        kwargs.pop("base_url", None)
        return httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://mcp.test", **kwargs)

    transport = StreamableHttpTransport(
        url="http://mcp.test/mcp/", httpx_client_factory=client_factory)

    async def _smoke():
        # http_app() carries the session-manager lifespan; it must be entered
        # before the transport will accept requests.
        async with app.router.lifespan_context(app):
            async with Client(transport) as client:
                tools = {t.name for t in await client.list_tools()}
                res = await client.call_tool("get_law", {"name": "999"})
                return tools, res.structured_content

    tools, payload = asyncio.run(_smoke())
    assert {"get_law", "search", "get_article"} <= tools
    assert payload["titulo"] == "Закон за тест"
