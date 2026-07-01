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


def _typed_corpus(tmp_path, commits):
    """Commit zakon-a.md once per (body, date, message) tuple, honoring the
    Legalize commit-message convention in `message` (e.g. '[bootstrap] ...',
    '[popravka] ...', '[reforma] ...'). Returns [(sha, message), ...]."""
    (tmp_path / "laws").mkdir()
    f = tmp_path / "laws" / "zakon-a.md"
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.email", "t@t")
    _git(tmp_path, "config", "user.name", "T")
    _git(tmp_path, "config", "commit.gpgsign", "false")
    shas = []
    for body, d, msg in commits:
        f.write_text(_act(body), encoding="utf-8")
        _git(tmp_path, "add", ".")
        env = {**os.environ, "GIT_AUTHOR_DATE": f"{d}T00:00:00+00:00"}
        _git(tmp_path, "commit", "-q", "-m", msg, env=env)
        sha = subprocess.run(["git", "rev-parse", "HEAD"], cwd=tmp_path,
                             check=True, capture_output=True,
                             text=True).stdout.strip()
        shas.append((sha, msg))
    return shas


def test_popravka_commit_does_not_create_version_boundary(tmp_path):
    """D-047 / Task 13: a [popravka] is a corrigendum (e.g. the parser
    data-loss re-bootstrap that finally captured Допълнителни разпоредби),
    NOT a legal amendment — so it must NOT create a new law_versions row.
    Otherwise get_law(historical_date) returns the pre-fix DEFECTIVE text and
    the timeline fabricates a spurious 'incomplete->complete' step for ~every
    corrected act."""
    shas = _typed_corpus(tmp_path, [
        ("Чл. 1. Оригинал (без ДР).", "2018-01-01", "[bootstrap] Закон А"),
        ("Чл. 1. Оригинал.\n\n## Допълнителни разпоредби\n\n**§ 1.** Определения.",
         "2020-06-15", "[popravka] Закон А"),
    ])
    (_boot_sha, _), (pop_sha, _) = shas
    db = str(tmp_path / "c.db")
    build(str(tmp_path), db)
    c = _conn(db)
    rows = c.execute(
        "SELECT valid_from, valid_to, commit_hash FROM law_versions "
        "WHERE law_id='zakon-a' ORDER BY valid_from"
    ).fetchall()
    assert len(rows) == 1, \
        f"popravka must not add a version; got {[tuple(r) for r in rows]}"
    assert rows[0]["valid_from"] == "2018-01-01"   # keeps the bootstrap boundary
    assert rows[0]["valid_to"] is None
    assert rows[0]["commit_hash"] == pop_sha        # latest=HEAD => corrected text


def test_reforma_commit_still_creates_version_boundary(tmp_path):
    """Guard: excluding [popravka] must NOT swallow real amendments — a
    [reforma] (ЗИД) remains a legal version boundary."""
    shas = _typed_corpus(tmp_path, [
        ("Чл. 1. Оригинал.", "2018-01-01", "[bootstrap] Закон А"),
        ("Чл. 1. Изменен с ЗИД.", "2020-06-15", "[reforma] Закон А"),
    ])
    (boot_sha, _), (ref_sha, _) = shas
    db = str(tmp_path / "c.db")
    build(str(tmp_path), db)
    c = _conn(db)
    rows = c.execute(
        "SELECT valid_from, valid_to, commit_hash FROM law_versions "
        "WHERE law_id='zakon-a' ORDER BY valid_from"
    ).fetchall()
    assert len(rows) == 2, \
        f"reforma must add a version; got {[tuple(r) for r in rows]}"
    assert rows[0]["valid_from"] == "2018-01-01"
    assert rows[0]["commit_hash"] == boot_sha
    assert rows[1]["valid_from"] == "2020-06-15"
    assert rows[1]["valid_to"] is None
