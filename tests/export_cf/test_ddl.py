"""D1 schema emission (spec: tables 1:1 from catalog.db; laws_fts
recreated with the IDENTICAL declaration; provisions and its indexes
excluded)."""

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


def test_fts_declaration_identical(migrated_conn):
    sql = _schema(migrated_conn)
    assert "CREATE VIRTUAL TABLE IF NOT EXISTS laws_fts USING fts5" in sql
    for frag in ("law_id UNINDEXED", "category UNINDEXED",
                 "tokenize='unicode61 remove_diacritics 2'"):
        assert frag in sql, frag
    # rebuild via INSERT — never carry the raw shadow tables
    assert "laws_fts_data" not in sql
    assert "laws_fts_idx" not in sql
    assert "laws_fts_content" not in sql


def test_indexes(migrated_conn):
    sql = _schema(migrated_conn)
    assert "idx_amendments_target" in sql
    assert "idx_versions_date" in sql
    assert "idx_provisions" not in sql
