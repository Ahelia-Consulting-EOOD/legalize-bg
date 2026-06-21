"""FR-014 incremental index rebuild — only changed acts are re-indexed,
and the result is identical to a full rebuild of the same HEAD."""

import sqlite3
import subprocess

import pytest

from index.build import build

TODAY = "2026-06-21"


def _git(cwd, *args):
    subprocess.run(["git", *args], cwd=cwd, check=True,
                   capture_output=True, text=True)


def _act(titulo, ident, rango="закон", cat="laws", estado="vigente"):
    return (
        "---\n"
        f"titulo: '{titulo}'\n"
        f"identificador: '{ident}'\n"
        "pais: bg\n"
        f"rango: {rango}\n"
        "fecha_publicacion: '2020-01-01'\n"
        "ultima_actualizacion: '2020-01-01'\n"
        f"estado: {estado}\n"
        "fuente: lex.bg\n"
        f"category: {cat}\n"
        "---\n\n"
        f"# {titulo}\n\nЧл. 1. Текст на акта.\n"
    )


@pytest.fixture
def corpus(tmp_path):
    (tmp_path / "laws").mkdir()
    (tmp_path / "ordinances").mkdir()
    (tmp_path / "laws" / "zakon-a.md").write_text(_act("Закон А", 1001),
                                                  encoding="utf-8")
    (tmp_path / "laws" / "zakon-b.md").write_text(_act("Закон Б", 1002),
                                                  encoding="utf-8")
    (tmp_path / "ordinances" / "naredba-1.md").write_text(
        _act("Наредба 1", 2001, "наредба", "ordinances"), encoding="utf-8")
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.email", "t@t")
    _git(tmp_path, "config", "user.name", "T")
    _git(tmp_path, "config", "commit.gpgsign", "false")
    _git(tmp_path, "add", ".")
    _git(tmp_path, "commit", "-q", "-m", "v1")
    return tmp_path


def _conn(db):
    c = sqlite3.connect(db)
    c.row_factory = sqlite3.Row
    return c


def test_incremental_reindexes_modified_act(corpus, tmp_path):
    db = str(tmp_path / "c.db")
    build(corpus, db, today_iso=TODAY)
    (corpus / "laws" / "zakon-a.md").write_text(
        _act("Закон А (изменен)", 1001), encoding="utf-8")
    _git(corpus, "commit", "-q", "-am", "v2")
    n = build(corpus, db, today_iso=TODAY, incremental=True)
    assert n == 3
    c = _conn(db)
    assert c.execute("SELECT title FROM laws WHERE law_id='zakon-a'"
                     ).fetchone()["title"] == "Закон А (изменен)"
    # unchanged act untouched
    assert c.execute("SELECT title FROM laws WHERE law_id='zakon-b'"
                     ).fetchone()["title"] == "Закон Б"


def test_incremental_adds_new_act(corpus, tmp_path):
    db = str(tmp_path / "c.db")
    build(corpus, db, today_iso=TODAY)
    (corpus / "laws" / "zakon-c.md").write_text(_act("Закон В", 1003),
                                                encoding="utf-8")
    _git(corpus, "add", ".")
    _git(corpus, "commit", "-q", "-m", "add c")
    n = build(corpus, db, today_iso=TODAY, incremental=True)
    assert n == 4
    c = _conn(db)
    assert c.execute("SELECT COUNT(*) FROM laws WHERE law_id='zakon-c'"
                     ).fetchone()[0] == 1


def test_incremental_deletes_removed_act(corpus, tmp_path):
    db = str(tmp_path / "c.db")
    build(corpus, db, today_iso=TODAY)
    _git(corpus, "rm", "-q", "laws/zakon-b.md")
    _git(corpus, "commit", "-q", "-m", "rm b")
    n = build(corpus, db, today_iso=TODAY, incremental=True)
    assert n == 2
    c = _conn(db)
    for t in ("laws", "law_versions", "provisions", "laws_fts"):
        assert c.execute(
            f"SELECT COUNT(*) FROM {t} WHERE law_id='zakon-b'"
        ).fetchone()[0] == 0, f"zakon-b rows linger in {t}"
    # amendments keys the act via target_law, not law_id
    assert c.execute(
        "SELECT COUNT(*) FROM amendments WHERE target_law='zakon-b'"
    ).fetchone()[0] == 0


def test_incremental_noop_when_at_head(corpus, tmp_path):
    db = str(tmp_path / "c.db")
    build(corpus, db, today_iso=TODAY)
    n = build(corpus, db, today_iso=TODAY, incremental=True)  # no commits since
    assert n == 3


def test_incremental_falls_back_to_full_on_empty_db(corpus, tmp_path):
    db = str(tmp_path / "c.db")
    # No prior build → empty catalog → incremental falls back to full.
    n = build(corpus, db, today_iso=TODAY, incremental=True)
    assert n == 3


def _dump(db):
    c = _conn(db)
    q = {
        "laws": "SELECT law_id,doc_id,title,category,status,current_commit FROM laws",
        "law_versions": "SELECT law_id,valid_from,valid_to,commit_hash,date_uncertain FROM law_versions",
        "amendments": "SELECT source_act,target_law,operation,dv_issue,dv_date FROM amendments",
        "provisions": "SELECT law_id,article,paragraph,valid_from,text,text_hash FROM provisions",
        "laws_fts": "SELECT law_id,title,body,category FROM laws_fts",
    }
    return {k: sorted(tuple(r) for r in c.execute(v)) for k, v in q.items()}


def test_incremental_matches_full_rebuild_oracle(corpus, tmp_path):
    """The strongest guarantee: an incremental rebuild (modify + add +
    delete) produces byte-identical content tables to a full rebuild of the
    same HEAD."""
    inc_db = str(tmp_path / "inc.db")
    build(corpus, inc_db, today_iso=TODAY)  # full at v1

    # v2: modify a, add c, delete b. naredba-1 stays unchanged.
    (corpus / "laws" / "zakon-a.md").write_text(_act("Закон А v2", 1001),
                                                encoding="utf-8")
    (corpus / "laws" / "zakon-c.md").write_text(_act("Закон В", 1003),
                                                encoding="utf-8")
    _git(corpus, "rm", "-q", "laws/zakon-b.md")
    _git(corpus, "add", ".")
    _git(corpus, "commit", "-q", "-m", "v2")

    build(corpus, inc_db, today_iso=TODAY, incremental=True)  # incremental v1→v2

    full_db = str(tmp_path / "full.db")
    build(corpus, full_db, today_iso=TODAY)  # full at v2

    assert _dump(inc_db) == _dump(full_db)
