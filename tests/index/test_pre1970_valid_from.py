"""D-017 clamps pre-1970 GIT_AUTHOR_DATEs to 1970-01-01 (git rejects
negative epochs). The version map must repair the EARLIEST version's
valid_from from frontmatter so pre-1970 history isn't denied (review
2026-07-02: Inheritance Act 1949 reported earliest_available=1970-01-01)."""

import os
import sqlite3
import subprocess

from index.build import build


def test_earliest_valid_from_prefers_frontmatter_over_epoch_clamp(tmp_path):
    corpus = tmp_path / "corpus"
    d = corpus / "laws"
    d.mkdir(parents=True)
    (d / "zakon-star.md").write_text(
        "---\ntitulo: Закон за наследството\nidentificador: 999\n"
        "fecha_publicacion: 1949-01-29\n---\n\nЧл. 1. Текст.\n",
        encoding="utf-8")
    subprocess.run(["git", "init", "-q"], cwd=corpus, check=True)
    subprocess.run(["git", "add", "-A"], cwd=corpus, check=True)
    env = dict(os.environ,
               GIT_AUTHOR_DATE="1970-01-01T00:00:00+00:00",
               GIT_COMMITTER_DATE="1970-01-01T00:00:00+00:00")
    subprocess.run(
        ["git", "-c", "user.email=t@t", "-c", "user.name=t",
         "commit", "-q", "-m", "[bootstrap] Закон за наследството"],
        cwd=corpus, check=True, env=env)

    db = str(tmp_path / "c.db")
    build(corpus, db)
    conn = sqlite3.connect(db)
    try:
        vf = conn.execute(
            "SELECT MIN(valid_from) FROM law_versions "
            "WHERE law_id='zakon-star'").fetchone()[0]
    finally:
        conn.close()
    assert vf == "1949-01-29"


def test_earliest_valid_from_uses_fecha_publicacion_not_effective_date(tmp_path):
    """Mirrors the real Inheritance Act (review 2026-07-02 follow-up):
    frontmatter carries BOTH fecha_publicacion (ДВ publication date) and a
    later effective_date (entry-into-force). git author-dates are derived
    from fecha_publicacion at bootstrap time (bootstrap.py), never
    effective_date — so the clamp repair must restore fecha_publicacion,
    not `effective` (which prefers effective_date), or pre-1970 acts would
    carry different valid_from semantics than the rest of the corpus."""
    corpus = tmp_path / "corpus"
    d = corpus / "laws"
    d.mkdir(parents=True)
    (d / "zakon-za-nasledstvoto.md").write_text(
        "---\ntitulo: ЗАКОН ЗА НАСЛЕДСТВОТО\nidentificador: 998\n"
        "fecha_publicacion: 1949-01-29\neffective_date: 1949-04-30\n"
        "---\n\nЧл. 1. Текст.\n",
        encoding="utf-8")
    subprocess.run(["git", "init", "-q"], cwd=corpus, check=True)
    subprocess.run(["git", "add", "-A"], cwd=corpus, check=True)
    env = dict(os.environ,
               GIT_AUTHOR_DATE="1970-01-01T00:00:00+00:00",
               GIT_COMMITTER_DATE="1970-01-01T00:00:00+00:00")
    subprocess.run(
        ["git", "-c", "user.email=t@t", "-c", "user.name=t",
         "commit", "-q", "-m", "[bootstrap] ЗАКОН ЗА НАСЛЕДСТВОТО"],
        cwd=corpus, check=True, env=env)

    db = str(tmp_path / "c.db")
    build(corpus, db)
    conn = sqlite3.connect(db)
    try:
        vf = conn.execute(
            "SELECT MIN(valid_from) FROM law_versions "
            "WHERE law_id='zakon-za-nasledstvoto'").fetchone()[0]
    finally:
        conn.close()
    assert vf == "1949-01-29"
