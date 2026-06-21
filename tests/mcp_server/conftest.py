import sqlite3

import pytest

from index.fts import insert_fts_row
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
        # FTS row uses normalized title; phantom acts get <doc_id=N> placeholder
        fts_title = title or f"<doc_id={doc_id}>"
        insert_fts_row(conn, law_id=law_id, title=fts_title,
                       body=fts_title, category=cat)
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
