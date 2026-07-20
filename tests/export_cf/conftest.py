"""Shared export_cf fixture: a REAL 2-commit corpus + built catalog
FILE, mirroring tests/api/conftest.py (the exporter reads catalog.db +
corpus checkout exactly like the REST API does). Module-scoped so each
test file pays the git/build cost once."""

import os
import subprocess

import pytest

from index.build import build


def _commit(corpus, msg, date):
    env = dict(os.environ, GIT_AUTHOR_DATE=f"{date}T00:00:00+00:00",
               GIT_COMMITTER_DATE=f"{date}T00:00:00+00:00")
    subprocess.run(["git", "add", "-A"], cwd=corpus, check=True)
    subprocess.run(
        ["git", "-c", "user.email=t@t", "-c", "user.name=t",
         "commit", "-q", "-m", msg], cwd=corpus, check=True, env=env)


@pytest.fixture(scope="module")
def export_corpus(tmp_path_factory):
    """(corpus_root, db_path): two laws + one ordinance, one act with
    two committed versions (СТАРА → НОВА) so versions/ export exercises
    the `git show` path, plus a no-frontmatter-date act so the
    DATE_UNCERTAIN warning path is covered."""
    corpus = tmp_path_factory.mktemp("cf-export-corpus")
    (corpus / "laws").mkdir(parents=True)
    (corpus / "ordinances").mkdir(parents=True)

    law = corpus / "laws" / "zakon-vremeto.md"
    fm = ("---\ntitulo: Закон за времето\nidentificador: 777\n"
          "fecha_publicacion: 2020-01-01\nultima_actualizacion: 2021-06-15\n"
          "dv_issue: 55\ndv_year: 2020\neli: /eli/bg/2020/777\n"
          "estado: vigente\nrango: Закон\n"
          "amendment_history:\n- dv: '55'\n  date: 2020-01-01\n"
          "- dv: '70'\n  date: 2021-06-15\n---\n\n")
    law.write_text(
        fm + "**Чл. 1.** (1) СТАРА редакция. (2) Втора алинея.\n\n"
             "**Чл. 2.** Без алинеи.\n",
        encoding="utf-8")

    ord_ = corpus / "ordinances" / "naredba-bez-data.md"
    ord_.write_text(
        "---\ntitulo: Наредба без дата\nidentificador: 888\n---\n\n"
        "**Чл. 1.** Единствен член.\n",
        encoding="utf-8")

    subprocess.run(["git", "init", "-q"], cwd=corpus, check=True)
    _commit(corpus, "[bootstrap] fixture", "2020-01-01")

    law.write_text(
        fm + "**Чл. 1.** (1) НОВА редакция. (2) Втора алинея.\n\n"
             "**Чл. 2.** Без алинеи.\n",
        encoding="utf-8")
    _commit(corpus, "[reforma] Закон за времето", "2021-06-15")

    db = str(corpus / "catalog.db")
    build(corpus, db)
    return corpus, db


@pytest.fixture(scope="module")
def export_run(export_corpus, tmp_path_factory):
    """Run the full exporter ONCE per module against the fixture corpus;
    yields (corpus_root, db_path, out_dir)."""
    from export_cf.run import run_export

    corpus, db = export_corpus
    out = tmp_path_factory.mktemp("cf-export-out")
    run_export(corpus_root=corpus, db_path=db, out_dir=out)
    return corpus, db, out
