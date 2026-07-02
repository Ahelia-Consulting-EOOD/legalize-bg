"""A top-level directory holding corpus-shaped acts but absent from
CATEGORY_DIRS must fail the build loudly instead of being silently
invisible (review 2026-07-02: postanovleniya/ had 0 catalog rows)."""

import subprocess

import pytest

from index.build import _check_category_drift, build


def _init_git(corpus):
    subprocess.run(["git", "init", "-q"], cwd=corpus, check=True)
    subprocess.run(["git", "add", "-A"], cwd=corpus, check=True)
    subprocess.run(
        ["git", "-c", "user.email=t@t", "-c", "user.name=t",
         "commit", "-q", "-m", "[bootstrap] fixture"],
        cwd=corpus, check=True)


def _act(text_dir, slug, doc_id):
    text_dir.mkdir(parents=True, exist_ok=True)
    (text_dir / f"{slug}.md").write_text(
        "---\ntitulo: Тест\n"
        f"identificador: {doc_id}\n"
        "fecha_publicacion: 2020-01-01\n---\n\nЧл. 1. Текст.\n",
        encoding="utf-8")


def test_rogue_corpus_dir_fails_build(tmp_path):
    corpus = tmp_path / "corpus"
    _act(corpus / "laws", "zakon-a", 1)
    _act(corpus / "postanovleniya", "pms-1", 2)   # rogue, corpus-shaped
    _init_git(corpus)
    with pytest.raises(ValueError, match="postanovleniya"):
        build(corpus, str(tmp_path / "c.db"))


def test_non_corpus_dirs_are_ignored(tmp_path):
    corpus = tmp_path / "corpus"
    _act(corpus / "laws", "zakon-a", 1)
    docs = corpus / "docs"
    docs.mkdir()
    (docs / "notes.md").write_text("# just docs\n", encoding="utf-8")
    _init_git(corpus)
    _check_category_drift(corpus)  # must not raise
    assert build(corpus, str(tmp_path / "c.db")) == 1
