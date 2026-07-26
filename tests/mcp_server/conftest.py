import os
import sqlite3
import subprocess
from pathlib import Path

import pytest

from index.build import build
from index.fts import insert_segment_rows, insert_title_row
from index.migrations import migrate

# Fake "current_commit" stamped onto every populated_conn row. Tests
# that simulate the working-tree fast path in mcp_server.server.
# _read_law_markdown rely on this exact value matching what their
# fixture file system claims is HEAD — see test_get_law.py's `app`
# fixture. Pulled into a constant so a future fixture change stays in
# lockstep with the consumers.
FAKE_COMMIT_HASH = "a" * 40


@pytest.fixture
def conn():
    """Fresh in-memory SQLite with migrations applied.

    `check_same_thread=False` mirrors what the production CLI uses —
    FastMCP runs tool calls on a worker thread, so the e2e tests that
    invoke tools through the real Client need cross-thread access to
    the same in-memory DB. The catalog is read-only at runtime (writes
    happen via `index.build` against an on-disk file), so the
    same-thread guard is unnecessary defense.
    """
    c = sqlite3.connect(":memory:", check_same_thread=False)
    c.row_factory = sqlite3.Row
    migrate(c)
    yield c
    c.close()


@pytest.fixture
def populated_conn(conn):
    """Mini catalog: 5 acts including a slug collision (§7.1) and an
    empty-titulo phantom (§7.3)."""
    rows = [
        ("zakon-a",     100,         "Закон за А",            "laws"),
        ("zakon-b",     101,         "Закон за Б",            "laws"),
        ("naredba-7",   200,         "Наредба № 7 за нещо",   "ordinances"),
        ("naredba-7-2", 201,         "Наредба № 7 за нещо",   "ordinances"),  # §7.1
        ("phantom",     -549676032,  "",                      "ordinances"),  # §7.3
        # FR-015 part 2 (rang-aware re-rank, D-2026-05-09-04):
        # adversarial fixture where bm25 alone would put the
        # implementing reg + ordinance ABOVE the parent law (both have
        # shorter titles with denser query-token concentration). The
        # rang-tier sort in search_fts must invert that and put the
        # parent law (laws/) at the top.
        ("zakon-zop",     500,
         "Закон за обществените поръчки в Република България",
         "laws"),
        ("ppr-zop",       501,
         "Правилник обществени поръчки",
         "implementing"),
        ("reg-zop",       502,
         "Регистър обществени поръчки",
         "regulations"),
    ]
    fake_commit = FAKE_COMMIT_HASH
    for law_id, doc_id, title, cat in rows:
        conn.execute(
            "INSERT INTO laws (law_id, doc_id, title, category, status, current_commit) "
            "VALUES (?, ?, ?, ?, 'vigente', ?)",
            (law_id, doc_id, title, cat, fake_commit),
        )
        conn.execute(
            "INSERT INTO law_versions (law_id, valid_from, commit_hash) "
            "VALUES (?, ?, ?)",
            (law_id, "2020-01-01", fake_commit),
        )
        # FTS rows use the normalized title; phantom acts get the
        # <doc_id=N> placeholder. The title text doubles as the act's
        # one-segment body so body-tier (articles_fts) matches work in
        # tests, mirroring the pre-FR-032 fixture shape.
        fts_title = title or f"<doc_id={doc_id}>"
        insert_title_row(conn, law_id=law_id, title=fts_title, category=cat)
        insert_segment_rows(conn, law_id=law_id, body=fts_title,
                            category=cat)
    conn.commit()
    # Defensive lock: tests downstream couple their tmp-corpus fixture
    # to FAKE_COMMIT_HASH for the working-tree fast path (see
    # mcp_server.server._read_law_markdown). If the seed value drifts,
    # they silently flip to the slower `git show` path and pass for
    # the wrong reason.
    seeded = {row["current_commit"] for row in conn.execute(
        "SELECT DISTINCT current_commit FROM laws"
    )}
    assert seeded == {FAKE_COMMIT_HASH}, (
        f"populated_conn seed drift: expected current_commit="
        f"{FAKE_COMMIT_HASH!r}, got {seeded}"
    )
    return conn


def _commit(corpus: Path, msg: str, date: str) -> None:
    """Commit the corpus at a fixed author-date (mirrors the corpus
    commit-date discipline) so FR-020 version derivation is deterministic."""
    env = dict(os.environ, GIT_AUTHOR_DATE=f"{date}T00:00:00+00:00",
               GIT_COMMITTER_DATE=f"{date}T00:00:00+00:00")
    subprocess.run(["git", "add", "-A"], cwd=corpus, check=True)
    subprocess.run(
        ["git", "-c", "user.email=t@t", "-c", "user.name=t",
         "commit", "-q", "-m", msg], cwd=corpus, check=True, env=env)


@pytest.fixture(scope="module")
def file_catalog(tmp_path_factory) -> tuple[Path, str]:
    """A real on-disk catalog.db built from a one-act corpus.

    Per-call `mode=ro` connections (FR-029, via build_app(db_path=)) require a
    file DB, not the in-memory `conn`/`populated_conn` fixtures — so this
    builds an actual git-backed corpus + `index.build` catalog. Shared by
    test_connection_model.py and test_transport.py.
    """
    corpus = tmp_path_factory.mktemp("file-catalog-corpus")
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
