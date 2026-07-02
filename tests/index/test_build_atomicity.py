"""Full rebuild must never destroy the previous catalog on failure
(P0-3, review 2026-07-02): the DELETE of all content tables and the
re-INSERT loop must share ONE transaction so a crash mid-rebuild rolls
back to the prior good state when the connection closes."""

import sqlite3
import subprocess

import pytest

import index.build as build_mod
from index.build import build


def _write_act(corpus, cat, slug, title, doc_id):
    d = corpus / cat
    d.mkdir(parents=True, exist_ok=True)
    (d / f"{slug}.md").write_text(
        "---\n"
        f"titulo: {title}\n"
        f"identificador: {doc_id}\n"
        "fecha_publicacion: 2020-01-01\n"
        "---\n\n"
        f"**Чл. 1.** (1) Текст на {title}.\n",
        encoding="utf-8",
    )


@pytest.fixture
def git_corpus(tmp_path):
    corpus = tmp_path / "corpus"
    _write_act(corpus, "laws", "zakon-a", "Закон А", 111)
    _write_act(corpus, "laws", "zakon-b", "Закон Б", 222)
    subprocess.run(["git", "init", "-q"], cwd=corpus, check=True)
    subprocess.run(["git", "add", "-A"], cwd=corpus, check=True)
    subprocess.run(
        ["git", "-c", "user.email=t@t", "-c", "user.name=t",
         "commit", "-q", "-m", "[bootstrap] fixture"],
        cwd=corpus, check=True)
    return corpus


def test_failed_full_rebuild_preserves_previous_catalog(
        git_corpus, tmp_path, monkeypatch):
    db = str(tmp_path / "catalog.db")
    assert build(git_corpus, db) == 2  # good build first

    real = build_mod._reindex_act
    calls = {"n": 0}

    def boom(*args, **kwargs):
        calls["n"] += 1
        if calls["n"] >= 2:
            raise RuntimeError("simulated crash mid-rebuild")
        return real(*args, **kwargs)

    monkeypatch.setattr(build_mod, "_reindex_act", boom)
    with pytest.raises(RuntimeError):
        build(git_corpus, db)

    conn = sqlite3.connect(db)
    try:
        n_laws = conn.execute("SELECT COUNT(*) FROM laws").fetchone()[0]
        n_fts = conn.execute("SELECT COUNT(*) FROM laws_fts").fetchone()[0]
    finally:
        conn.close()
    assert n_laws == 2, "previous catalog must survive a failed rebuild"
    assert n_fts == 2
