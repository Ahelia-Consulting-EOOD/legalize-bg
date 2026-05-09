"""Forward-only schema migrations for the SQLite catalog.

Each migration is a (version, name, sql) triple. `migrate(conn)` applies all
pending migrations in version order and is safe to call repeatedly.

Per D-025: forward-only by construction. Never edit a shipped migration —
add a new one. The base schema (laws/law_versions/amendments/provisions)
comes from index.catalog.SCHEMA so a fresh in-memory db reaches the same
state as a Phase-1a-built catalog after migrate() runs.
"""

from dataclasses import dataclass
from typing import Iterable
import sqlite3

from index.catalog import SCHEMA as BASE_SCHEMA


@dataclass(frozen=True)
class Migration:
    version: int
    name: str
    sql: str


# Phase 1a left the catalog at version 0 (no schema_version table). Phase
# 1b.1 introduces the table and three migrations:
#   001 — provisions.text column (per D-023)
#   002 — laws_fts virtual table (per D-022)
#   003 — provisions lookup index for (law_id, article, paragraph, valid_from)
MIGRATIONS: tuple[Migration, ...] = (
    Migration(
        version=1,
        name="provisions_text_column",
        sql="ALTER TABLE provisions ADD COLUMN text TEXT;",
    ),
    Migration(
        version=2,
        name="laws_fts_virtual_table",
        sql="""
        CREATE VIRTUAL TABLE IF NOT EXISTS laws_fts USING fts5(
            law_id UNINDEXED,
            title,
            body,
            category UNINDEXED,
            tokenize='unicode61 remove_diacritics 2'
        );
        """,
    ),
    Migration(
        version=3,
        name="provisions_lookup_index",
        sql="""
        CREATE INDEX IF NOT EXISTS idx_provisions_lookup
            ON provisions(law_id, article, paragraph, valid_from);
        """,
    ),
)


def _ensure_schema_version_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_version (
            version INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )


def current_version(conn: sqlite3.Connection) -> int:
    _ensure_schema_version_table(conn)
    row = conn.execute("SELECT MAX(version) FROM schema_version").fetchone()
    return row[0] or 0


def migrate(conn: sqlite3.Connection,
            migrations: Iterable[Migration] = MIGRATIONS) -> int:
    """Apply all pending migrations. Returns the final version."""
    _ensure_schema_version_table(conn)
    # Ensure base tables exist before migrations can ALTER them.
    # CatalogIndex.initialize creates them; this mirrors that so
    # `migrate()` works against a fresh in-memory db too. (CREATE TABLE
    # IF NOT EXISTS in the base SCHEMA makes this safe to re-run on a
    # Phase-1a-built db.)
    conn.executescript(BASE_SCHEMA)

    applied = current_version(conn)
    for m in sorted(migrations, key=lambda x: x.version):
        if m.version <= applied:
            continue
        conn.executescript(m.sql)
        conn.execute(
            "INSERT INTO schema_version(version, name) VALUES (?, ?)",
            (m.version, m.name),
        )
        conn.commit()
        applied = m.version
    return applied
