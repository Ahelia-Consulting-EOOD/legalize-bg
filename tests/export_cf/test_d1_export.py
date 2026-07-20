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
    counts_and_truncated = export_d1(conn, out)
    conn.close()
    return db, out, counts_and_truncated


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
    _, out, (counts, _) = d1_out
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


def test_laws_dumped_in_rowid_order(reimported):
    """Parity: FastAPI's AMBIGUOUS_NAME candidates and no-ORDER-BY scans
    follow insertion (rowid) order — the reimported D1 must preserve it
    (fixture: laws/ act inserted before ordinances/ act, while sorted
    law_id order is the reverse)."""
    db, fresh = reimported
    src = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    src_order = [r[0] for r in src.execute(
        "SELECT law_id FROM laws ORDER BY rowid")]
    src.close()
    assert src_order[0] == "zakon-vremeto"  # insertion order, not sorted
    fresh_order = [r[0] for r in fresh.execute(
        "SELECT law_id FROM laws ORDER BY rowid")]
    assert fresh_order == src_order
    fts_order = [r[0] for r in fresh.execute(
        "SELECT law_id FROM laws_fts ORDER BY rowid")]
    assert fts_order == src_order


def test_fts_row_cap_truncates_oversized_bodies(export_corpus, tmp_path):
    """D1 hard limit: any string/row over 2MB throws SQLITE_TOOBIG at
    query time. Oversized laws_fts bodies are truncated at a char
    boundary so the TOTAL row stays under the cap; truncated law_ids are
    reported for the manifest."""
    _, db = export_corpus
    src = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    counts, truncated = export_d1(src, tmp_path, fts_row_max_bytes=100)
    src.close()
    assert set(truncated)  # fixture bodies exceed 100 bytes total row
    fresh = sqlite3.connect(":memory:")
    fresh.executescript((tmp_path / "d1-schema.sql").read_text("utf-8"))
    for chunk in sorted(tmp_path.glob("d1-data-*.sql")):
        fresh.executescript(chunk.read_text("utf-8"))
    for law_id, title, body, cat in fresh.execute(
            "SELECT law_id, title, body, category FROM laws_fts"):
        total = sum(len(s.encode("utf-8")) for s in (law_id, title, body, cat))
        assert total <= 100, law_id
    fresh.close()


def test_fts_row_cap_default_no_truncation_on_fixture(d1_out):
    _, _, (counts, truncated) = d1_out
    assert truncated == []
