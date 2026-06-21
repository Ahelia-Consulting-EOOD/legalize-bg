"""FR-020 time-machine: index/build.py populates one law_versions row per
git commit of an act, so version_at_date / get_law(date) / diff resolve
historical versions instead of a single consolidated one."""

import os
import sqlite3
import subprocess

import pytest

from index.build import build
from mcp_server.queries import version_at_date, diff_law_versions


def _git(cwd, *args, env=None):
    subprocess.run(["git", *args], cwd=cwd, check=True,
                   capture_output=True, text=True, env=env)


def _act(body, titulo="Закон А", ident=1001):
    return (
        "---\n"
        f"titulo: '{titulo}'\n"
        f"identificador: '{ident}'\n"
        "pais: bg\n"
        "rango: закон\n"
        "fecha_publicacion: '2018-01-01'\n"
        "ultima_actualizacion: '2020-06-15'\n"
        "estado: vigente\n"
        "fuente: lex.bg\n"
        "category: laws\n"
        "---\n\n"
        f"# Закон А\n\n{body}\n"
    )


@pytest.fixture
def time_corpus(tmp_path):
    """A git corpus where zakon-a.md is committed twice at distinct
    author-dates (the legislative dates), per the corpus commit discipline."""
    (tmp_path / "laws").mkdir()
    f = tmp_path / "laws" / "zakon-a.md"
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.email", "t@t")
    _git(tmp_path, "config", "user.name", "T")
    _git(tmp_path, "config", "commit.gpgsign", "false")

    def commit(body, d):
        f.write_text(_act(body), encoding="utf-8")
        _git(tmp_path, "add", ".")
        env = {**os.environ,
               "GIT_AUTHOR_DATE": f"{d}T00:00:00+00:00",
               "GIT_COMMITTER_DATE": f"{d}T00:00:00+00:00"}
        _git(tmp_path, "commit", "-q", "-m", d, env=env)
        return subprocess.run(["git", "rev-parse", "HEAD"], cwd=tmp_path,
                              check=True, capture_output=True,
                              text=True).stdout.strip()

    sha1 = commit("Чл. 1. Първоначален текст на акта.", "2018-01-01")
    sha2 = commit("Чл. 1. Изменен текст на акта.", "2020-06-15")
    return tmp_path, sha1, sha2


def _conn(db):
    c = sqlite3.connect(db)
    c.row_factory = sqlite3.Row
    return c


def test_law_versions_one_row_per_commit(time_corpus, tmp_path):
    corpus, sha1, sha2 = time_corpus
    db = str(tmp_path / "c.db")
    build(corpus, db)
    c = _conn(db)
    rows = c.execute(
        "SELECT valid_from, valid_to, commit_hash FROM law_versions "
        "WHERE law_id='zakon-a' ORDER BY valid_from"
    ).fetchall()
    assert len(rows) == 2, f"expected 2 versions, got {[tuple(r) for r in rows]}"
    # v1: in force from its commit date until the day before v2
    assert rows[0]["valid_from"] == "2018-01-01"
    assert rows[0]["valid_to"] == "2020-06-14"   # day before v2 (INCLUSIVE)
    assert rows[0]["commit_hash"] == sha1
    # v2: latest → valid_to NULL, commit_hash = HEAD
    assert rows[1]["valid_from"] == "2020-06-15"
    assert rows[1]["valid_to"] is None
    assert rows[1]["commit_hash"] == sha2


def test_version_at_date_resolves_historical(time_corpus, tmp_path):
    corpus, sha1, sha2 = time_corpus
    db = str(tmp_path / "c.db")
    build(corpus, db)
    c = _conn(db)
    assert version_at_date(c, "zakon-a", "2019-01-01") == sha1   # within v1
    assert version_at_date(c, "zakon-a", "2021-01-01") == sha2   # within v2
    assert version_at_date(c, "zakon-a", None) == sha2           # current


def test_version_at_date_inclusive_boundary(time_corpus, tmp_path):
    corpus, sha1, sha2 = time_corpus
    db = str(tmp_path / "c.db")
    build(corpus, db)
    c = _conn(db)
    assert version_at_date(c, "zakon-a", "2020-06-14") == sha1   # last day of v1
    assert version_at_date(c, "zakon-a", "2020-06-15") == sha2   # first day of v2


def test_diff_returns_real_diff_across_versions(time_corpus, tmp_path):
    corpus, sha1, sha2 = time_corpus
    db = str(tmp_path / "c.db")
    build(corpus, db)
    c = _conn(db)
    out = diff_law_versions(c, corpus, "zakon-a", "2019-01-01", "2021-01-01")
    # Real git diff between the two versions — NOT the single-version note.
    assert "single consolidated version" not in out.lower()
    assert ("Първоначален" in out or "Изменен" in out
            or out.startswith("diff") or "@@" in out), \
        f"expected a real diff, got: {out[:200]!r}"
