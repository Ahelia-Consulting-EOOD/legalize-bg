"""SQL literal escaping + multi-row INSERT batching."""

import sqlite3

from export_cf.sqlgen import insert_statements, sql_literal


def test_literals():
    assert sql_literal(None) == "NULL"
    assert sql_literal(7) == "7"
    assert sql_literal(-549676032) == "-549676032"
    assert sql_literal("а'б") == "'а''б'"
    assert sql_literal("multi\nline") == "'multi\nline'"


def test_batching_row_cap():
    rows = [(i, f"t{i}") for i in range(1201)]
    stmts = list(insert_statements("laws", ("id", "t"), iter(rows),
                                   max_rows=500))
    assert len(stmts) == 3  # 500 + 500 + 201
    assert stmts[0].startswith("INSERT INTO laws (id, t) VALUES")
    assert stmts[0].rstrip().endswith(";")


def test_batching_byte_cap_flushes_early():
    big = "х" * 4000
    rows = [(i, big) for i in range(10)]
    stmts = list(insert_statements("laws_fts", ("id", "body"), iter(rows),
                                   max_rows=500, max_bytes=20_000))
    assert len(stmts) > 1  # byte cap forced a flush before 500 rows


def test_round_trip_through_sqlite():
    """The emitted SQL must reproduce the rows byte-exactly, Cyrillic
    and quotes included."""
    rows = [("а-1", "текст с 'кавички'", None, 5),
            ("б-2", "втори\nред", "x", -3)]
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE t (a TEXT, b TEXT, c TEXT, d INTEGER)")
    for stmt in insert_statements("t", ("a", "b", "c", "d"), iter(rows)):
        conn.executescript(stmt)
    got = conn.execute("SELECT a, b, c, d FROM t ORDER BY a").fetchall()
    assert got == rows
