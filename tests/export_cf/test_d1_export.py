"""D1 dump: d1-schema.sql + d1-data-NNNN.sql chunks that re-import into
a fresh SQLite byte-identically to the source catalog (minus provisions)."""

import sqlite3

import pytest

from export_cf.d1 import export_d1


@pytest.fixture(scope="module")
def d1_out(export_corpus, tmp_path_factory):
    _, db = export_corpus
    out = tmp_path_factory.mktemp("d1-out")
    conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    counts = export_d1(conn, out)
    conn.close()
    return db, out, counts


@pytest.fixture(scope="module")
def reimported(d1_out):
    db, out, _ = d1_out
    fresh = sqlite3.connect(":memory:")
    fresh.executescript((out / "d1-schema.sql").read_text(encoding="utf-8"))
    for chunk in sorted(out.glob("d1-data-*.sql")):
        fresh.executescript(chunk.read_text(encoding="utf-8"))
    yield db, fresh
    fresh.close()


def test_chunk_files_exist(d1_out):
    _, out, counts = d1_out
    assert (out / "d1-schema.sql").is_file()
    chunks = sorted(out.glob("d1-data-*.sql"))
    assert chunks and chunks[0].name == "d1-data-0001.sql"
    assert counts["laws"] > 0
    assert counts["laws_fts"] == counts["laws"]


def test_tables_copied_1_to_1(reimported):
    db, fresh = reimported
    src = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    for table, order in (("laws", "law_id"), ("law_versions", "id"),
                         ("amendments", "id"), ("schema_version", "version")):
        cols = [r[1] for r in src.execute(f"PRAGMA table_info({table})")]
        q = f"SELECT {', '.join(cols)} FROM {table} ORDER BY {order}"
        assert fresh.execute(q).fetchall() == src.execute(q).fetchall(), table
    src.close()


def test_no_provisions_in_d1(reimported):
    _, fresh = reimported
    names = {r[0] for r in fresh.execute(
        "SELECT name FROM sqlite_master WHERE type='table'")}
    assert "provisions" not in names


def test_fts_rebuilt_with_same_source_text(reimported):
    db, fresh = reimported
    src = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    q = ("SELECT law_id, title, body, category FROM laws_fts "
         "ORDER BY law_id")
    assert fresh.execute(q).fetchall() == src.execute(q).fetchall()
    src.close()


def test_fts_index_is_queryable(reimported):
    """The rebuilt FTS index must answer a normalized MATCH — proving
    the INSERT rebuild produced a working index, not just stored rows."""
    _, fresh = reimported
    hits = fresh.execute(
        "SELECT law_id FROM laws_fts WHERE laws_fts MATCH 'време'"
    ).fetchall()
    assert ("zakon-vremeto",) in hits
