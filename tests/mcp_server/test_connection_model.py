"""FR-029: per-call `mode=ro` connections retire the D-040 global lock.

Production and remote transports build the server with `db_path=` so each
tool call opens its OWN read-only connection (mirroring `api/deps.py:get_conn`,
the pattern FR-028/D-052 already proved in production), instead of the single
shared `conn=` + `_db_lock` model that the existing in-memory test suite uses.
Both construction modes must work; the `db_path=` mode must open a fresh
connection per call and must not serialize concurrent calls behind one lock.

Per-call `mode=ro` connections require a file DB, not `:memory:` (see the note
in tests/api/conftest.py) — hence the on-disk catalog fixture here.
"""

from __future__ import annotations

import os
import sqlite3
import subprocess
import threading
from pathlib import Path

import pytest

from index.build import build
from mcp_server.server import build_app


def _commit(corpus: Path, msg: str, date: str) -> None:
    env = dict(os.environ, GIT_AUTHOR_DATE=f"{date}T00:00:00+00:00",
               GIT_COMMITTER_DATE=f"{date}T00:00:00+00:00")
    subprocess.run(["git", "add", "-A"], cwd=corpus, check=True)
    subprocess.run(
        ["git", "-c", "user.email=t@t", "-c", "user.name=t",
         "commit", "-q", "-m", msg], cwd=corpus, check=True, env=env)


@pytest.fixture(scope="module")
def file_catalog(tmp_path_factory) -> tuple[Path, str]:
    """A real on-disk catalog.db built from a one-act corpus."""
    corpus = tmp_path_factory.mktemp("conn-corpus")
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


def test_db_path_mode_serves_correct_results(file_catalog):
    """build_app(db_path=...) yields a working server: tools return the
    right data reading through per-call connections."""
    corpus, db = file_catalog
    handle = build_app(db_path=db, corpus_root=corpus)

    resp = handle.call_tool_sync("get_law", {"name": "999"})
    assert resp["titulo"] == "Закон за тест"
    assert "Съдържание на теста" in resp["body_markdown"]


def test_db_path_opens_a_fresh_connection_per_call(file_catalog, monkeypatch):
    """Each tool call opens exactly one new connection (per-call model),
    and no single shared connection is retained on the handle."""
    corpus, db = file_catalog
    handle = build_app(db_path=db, corpus_root=corpus)

    # No persistent shared connection is held in per-call mode.
    assert handle._conn is None

    # Spy on connection opens without replacing real behavior.
    real_connect = sqlite3.connect
    opened = {"n": 0}

    def counting_connect(*a, **k):
        opened["n"] += 1
        return real_connect(*a, **k)

    monkeypatch.setattr(sqlite3, "connect", counting_connect)

    handle.call_tool_sync("get_law", {"name": "999"})
    handle.call_tool_sync("get_law", {"name": "999"})

    # Two calls → two connections; none opened at build time.
    assert opened["n"] == 2


def test_db_path_concurrent_calls_neither_error_nor_hang(file_catalog):
    """The per-call model lets concurrent calls run without the
    InterfaceError race the D-040 lock guarded against — each call has its
    own connection, so no shared-connection serialization is needed."""
    corpus, db = file_catalog
    handle = build_app(db_path=db, corpus_root=corpus)
    results, errors = [], []

    def worker():
        try:
            for _ in range(20):
                r = handle.call_tool_sync("get_law", {"name": "999"})
                results.append(r)
        except Exception as e:  # noqa: BLE001
            errors.append(repr(e))

    threads = [threading.Thread(target=worker) for _ in range(16)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert not errors, f"concurrent per-call tool calls failed: {errors[:3]}"
    assert len(results) == 16 * 20
    assert all(r["titulo"] == "Закон за тест" for r in results)


def test_db_path_closes_connection_and_flows_taxonomy_when_tool_raises(
        file_catalog, monkeypatch):
    """On the per-call path, a tool that raises must still (a) surface the
    structured error taxonomy (ToolError, not a leaked exception) and (b)
    close its connection — the `_acquire` `finally` runs regardless of the
    tool raising, and the taxonomy `except` blocks sit outside `_acquire`."""
    from mcp_server.errors import ToolError

    corpus, db = file_catalog
    handle = build_app(db_path=db, corpus_root=corpus)

    real_connect = sqlite3.connect
    opened: list[sqlite3.Connection] = []

    def tracking_connect(*a, **k):
        c = real_connect(*a, **k)
        opened.append(c)
        return c

    monkeypatch.setattr(sqlite3, "connect", tracking_connect)

    with pytest.raises(ToolError) as ei:
        handle.call_tool_sync("get_law", {"name": "no-such-act-9999"})
    assert ei.value.code == "LAW_NOT_FOUND"  # taxonomy flows through per-call acquire

    assert opened, "expected the tool call to open a connection"
    for c in opened:
        with pytest.raises(sqlite3.ProgrammingError):
            c.execute("SELECT 1")  # connection was closed despite the raise


def test_build_app_requires_exactly_one_of_conn_or_db_path(file_catalog):
    """Exactly one connection source must be given — neither (ambiguous
    nothing to serve) nor both (which source wins?) is valid."""
    corpus, db = file_catalog
    with pytest.raises(ValueError):
        build_app(corpus_root=corpus)  # neither
    with pytest.raises(ValueError):
        conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
        build_app(conn=conn, db_path=db, corpus_root=corpus)  # both
