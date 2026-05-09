import sqlite3

import pytest

from index.fts import insert_fts_row
from index.migrations import migrate


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
    ]
    fake_commit = "a" * 40
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
        # FTS row uses normalized title; phantom acts get <doc_id=N> placeholder
        fts_title = title or f"<doc_id={doc_id}>"
        insert_fts_row(conn, law_id=law_id, title=fts_title,
                       body=fts_title, category=cat)
    conn.commit()
    return conn
