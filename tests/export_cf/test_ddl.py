"""D1 schema emission (spec v2.0: tables 1:1 from catalog.db; BOTH FTS
virtual tables recreated with declarations IDENTICAL to migration 005;
provisions and its indexes excluded)."""

import re
import sqlite3

import pytest

from index.migrations import migrate


@pytest.fixture()
def migrated_conn():
    c = sqlite3.connect(":memory:")
    migrate(c)
    yield c
    c.close()


def _schema(migrated_conn) -> str:
    from export_cf.ddl import d1_schema_sql
    return d1_schema_sql(migrated_conn)


def _decl_tokens(sql: str, table: str) -> list[str]:
    """Whitespace-normalized fts5(...) argument tokens of `table`'s
    virtual-table declaration inside `sql`."""
    m = re.search(
        rf"CREATE VIRTUAL TABLE (?:IF NOT EXISTS )?{table}"
        r"\s+USING fts5\s*\((.*?)\)\s*;",
        sql, re.DOTALL)
    assert m, f"no fts5 declaration for {table}"
    return [" ".join(part.split()) for part in m.group(1).split(",")]


def test_copied_tables_present(migrated_conn):
    sql = _schema(migrated_conn)
    for table in ("laws", "law_versions", "amendments", "schema_version"):
        assert f"CREATE TABLE IF NOT EXISTS {table}" in sql, table


def test_law_versions_carries_migrated_column(migrated_conn):
    # date_uncertain arrives via migration 004 (ALTER TABLE); the D1
    # schema must be the post-migration shape, not the base SCHEMA.
    sql = _schema(migrated_conn)
    ddl = sql[sql.index("CREATE TABLE IF NOT EXISTS law_versions"):]
    ddl = ddl[:ddl.index(";")]
    assert "date_uncertain" in ddl


def test_provisions_text_column_not_leaked(migrated_conn):
    sql = _schema(migrated_conn)
    assert "CREATE TABLE IF NOT EXISTS provisions" not in sql


def test_both_fts_declarations_identical_to_migration_005(migrated_conn):
    """Spec rule: the D1 FTS declarations are IDENTICAL to what
    migration 005 created (token-for-token, whitespace aside) — the
    cf-worker copies MATCH SQL verbatim from index/fts.py, so any
    column drift breaks it silently."""
    sql = _schema(migrated_conn)
    for table in ("laws_fts", "articles_fts"):
        migrated = migrated_conn.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name=?",
            (table,)).fetchone()[0] + ";"
        assert _decl_tokens(sql, table) == _decl_tokens(migrated, table), \
            table


def test_laws_fts_is_title_only(migrated_conn):
    # Migration 005 dropped the body column from laws_fts; a body
    # column reappearing here would resurrect the 2MB-value problem.
    tokens = _decl_tokens(_schema(migrated_conn), "laws_fts")
    assert "body" not in tokens
    assert "title" in tokens


def test_articles_fts_declaration(migrated_conn):
    sql = _schema(migrated_conn)
    tokens = _decl_tokens(sql, "articles_fts")
    assert tokens == ["law_id UNINDEXED", "seg_no UNINDEXED",
                      "kind UNINDEXED", "label UNINDEXED", "body",
                      "category UNINDEXED",
                      "tokenize='unicode61 remove_diacritics 2'"]
    # rebuild via INSERT — never carry the raw shadow tables
    for shadow in ("laws_fts_data", "laws_fts_idx", "laws_fts_content",
                   "articles_fts_data", "articles_fts_idx",
                   "articles_fts_content"):
        assert shadow not in sql, shadow


def test_indexes(migrated_conn):
    sql = _schema(migrated_conn)
    assert "idx_amendments_target" in sql
    assert "idx_versions_date" in sql
    assert "idx_provisions" not in sql
