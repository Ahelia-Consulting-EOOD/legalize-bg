"""FR-020 historical reads via `git show` and real two-version diff()
had zero coverage (review 2026-07-02); failures leaked raw
CalledProcessError. These tests use a REAL 2-commit corpus."""

import os
import sqlite3
import subprocess
from pathlib import Path

import pytest

from index.build import build
from mcp_server.errors import ToolError
from mcp_server.server import build_app


def _commit(corpus, msg, date):
    env = dict(os.environ, GIT_AUTHOR_DATE=f"{date}T00:00:00+00:00",
               GIT_COMMITTER_DATE=f"{date}T00:00:00+00:00")
    subprocess.run(["git", "add", "-A"], cwd=corpus, check=True)
    subprocess.run(
        ["git", "-c", "user.email=t@t", "-c", "user.name=t",
         "commit", "-q", "-m", msg], cwd=corpus, check=True, env=env)


@pytest.fixture
def two_version_app(tmp_path):
    corpus = tmp_path / "corpus"
    law = corpus / "laws" / "zakon-vremeto.md"
    law.parent.mkdir(parents=True)
    fm = ("---\ntitulo: Закон за времето\nidentificador: 777\n"
          "fecha_publicacion: 2020-01-01\n---\n\n")
    law.write_text(fm + "Чл. 1. СТАРА редакция.\n", encoding="utf-8")
    subprocess.run(["git", "init", "-q"], cwd=corpus, check=True)
    _commit(corpus, "[bootstrap] Закон за времето", "2020-01-01")
    law.write_text(fm + "Чл. 1. НОВА редакция.\n", encoding="utf-8")
    _commit(corpus, "[reforma] Закон за времето", "2021-06-15")

    db = str(tmp_path / "c.db")
    build(corpus, db)
    conn = sqlite3.connect(db, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    handle = build_app(conn, corpus_root=Path(corpus))
    yield handle, conn
    conn.close()


def test_get_law_historical_returns_v1_text(two_version_app):
    handle, _ = two_version_app
    out = handle.call_tool_sync(
        "get_law", {"name": "zakon-vremeto", "date": "2020-06-01"})
    assert "СТАРА редакция" in out["body_markdown"]
    current = handle.call_tool_sync("get_law", {"name": "zakon-vremeto"})
    assert "НОВА редакция" in current["body_markdown"]
    assert out["commit_hash"] != current["commit_hash"]


def test_diff_returns_real_two_version_diff(two_version_app):
    handle, _ = two_version_app
    out = handle.call_tool_sync(
        "diff", {"law": "zakon-vremeto",
                 "date1": "2020-06-01", "date2": "2021-12-31"})
    assert "-Чл. 1. СТАРА редакция." in out
    assert "+Чл. 1. НОВА редакция." in out


def test_unreachable_commit_surfaces_index_stale(two_version_app):
    handle, conn = two_version_app
    conn.execute("UPDATE law_versions SET commit_hash = ? "
                 "WHERE valid_to IS NOT NULL", ("0" * 40,))
    conn.commit()
    with pytest.raises(ToolError) as exc:
        handle.call_tool_sync(
            "get_law", {"name": "zakon-vremeto", "date": "2020-06-01"})
    assert exc.value.code == "INDEX_STALE"
    assert "hint" in exc.value.payload


def test_missing_working_tree_file_surfaces_index_stale(two_version_app, tmp_path):
    handle, _ = two_version_app
    (tmp_path / "corpus" / "laws" / "zakon-vremeto.md").unlink()
    with pytest.raises(ToolError) as exc:
        handle.call_tool_sync("get_law", {"name": "zakon-vremeto"})
    assert exc.value.code == "INDEX_STALE"


def test_dropped_table_surfaces_index_missing(two_version_app):
    handle, conn = two_version_app
    conn.execute("ALTER TABLE laws RENAME TO laws_gone")
    conn.commit()
    with pytest.raises(ToolError) as exc:
        handle.call_tool_sync("get_law", {"name": "zakon-vremeto"})
    assert exc.value.code == "INDEX_MISSING"
