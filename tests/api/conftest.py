"""Shared API fixture: a REAL 2-commit corpus + built catalog FILE
(per-request `mode=ro` connections require a file DB, not :memory:),
served through the actual FastAPI app via TestClient."""

import os
import subprocess
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from api.app import create_app
from index.build import build


def _commit(corpus, msg, date):
    env = dict(os.environ, GIT_AUTHOR_DATE=f"{date}T00:00:00+00:00",
               GIT_COMMITTER_DATE=f"{date}T00:00:00+00:00")
    subprocess.run(["git", "add", "-A"], cwd=corpus, check=True)
    subprocess.run(
        ["git", "-c", "user.email=t@t", "-c", "user.name=t",
         "commit", "-q", "-m", msg], cwd=corpus, check=True, env=env)


@pytest.fixture(scope="module")
def api_corpus(tmp_path_factory):
    corpus = tmp_path_factory.mktemp("api-corpus")
    law = corpus / "laws" / "zakon-vremeto.md"
    law.parent.mkdir(parents=True)
    fm = ("---\ntitulo: Закон за времето\nidentificador: 777\n"
          "fecha_publicacion: 2020-01-01\n---\n\n")
    law.write_text(fm + "**Чл. 1.** (1) СТАРА редакция. (2) Втора алинея.\n",
                   encoding="utf-8")
    subprocess.run(["git", "init", "-q"], cwd=corpus, check=True)
    _commit(corpus, "[bootstrap] Закон за времето", "2020-01-01")
    law.write_text(fm + "**Чл. 1.** (1) НОВА редакция. (2) Втора алинея.\n",
                   encoding="utf-8")
    _commit(corpus, "[reforma] Закон за времето", "2021-06-15")
    db = str(corpus / "catalog.db")
    build(corpus, db)
    return corpus, db


@pytest.fixture()
def client(api_corpus):
    corpus, db = api_corpus
    app = create_app(db_path=db, corpus_root=Path(corpus))
    with TestClient(app) as c:
        yield c
