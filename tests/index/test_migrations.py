import sqlite3

from index.migrations import current_version, migrate, MIGRATIONS


def test_fresh_db_starts_at_version_zero():
    conn = sqlite3.connect(":memory:")
    assert current_version(conn) == 0


def test_migrate_applies_all_pending():
    conn = sqlite3.connect(":memory:")
    target = max(m.version for m in MIGRATIONS)
    migrate(conn)
    assert current_version(conn) == target


def test_migrate_is_idempotent():
    conn = sqlite3.connect(":memory:")
    migrate(conn)
    v1 = current_version(conn)
    migrate(conn)
    v2 = current_version(conn)
    assert v1 == v2


def test_migration_001_adds_text_column_to_provisions():
    conn = sqlite3.connect(":memory:")
    migrate(conn)
    cols = [r[1] for r in conn.execute("PRAGMA table_info(provisions)")]
    assert "text" in cols, f"expected 'text' in provisions cols, got {cols}"


def test_migration_002_creates_laws_fts_virtual_table():
    conn = sqlite3.connect(":memory:")
    migrate(conn)
    rows = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='laws_fts'"
    ).fetchall()
    assert len(rows) == 1, "laws_fts virtual table not created"


def test_migration_003_adds_provisions_lookup_index():
    conn = sqlite3.connect(":memory:")
    migrate(conn)
    rows = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='index' AND name='idx_provisions_lookup'"
    ).fetchall()
    assert len(rows) == 1


def test_migration_004_adds_date_uncertain_column():
    conn = sqlite3.connect(":memory:")
    migrate(conn)
    cols = [r[1] for r in conn.execute("PRAGMA table_info(law_versions)")]
    assert "date_uncertain" in cols, \
        f"expected 'date_uncertain' in law_versions cols, got {cols}"


# ── migration 005: FR-032 two-index split (D-056) ──────────────────────

def test_migration_005_laws_fts_is_title_only():
    conn = sqlite3.connect(":memory:")
    migrate(conn)
    cols = [r[1] for r in conn.execute("PRAGMA table_info(laws_fts)")]
    assert cols == ["law_id", "title", "category"], cols


def test_migration_005_creates_articles_fts():
    conn = sqlite3.connect(":memory:")
    migrate(conn)
    cols = [r[1] for r in conn.execute("PRAGMA table_info(articles_fts)")]
    assert cols == ["law_id", "seg_no", "kind", "label", "body",
                    "category"], cols


def test_migration_005_drops_v1_laws_fts_content():
    """A v4 db with a populated one-row-per-act laws_fts migrates to an
    EMPTY title-only laws_fts (catalog.db is derived; the migration
    mandates a full rebuild rather than in-place re-segmentation)."""
    conn = sqlite3.connect(":memory:")
    migrate(conn, [m for m in MIGRATIONS if m.version <= 4])
    conn.execute(
        "INSERT INTO laws_fts (law_id, title, body, category)"
        " VALUES ('a', 'заглавие', 'тяло', 'laws')")
    migrate(conn)
    assert conn.execute("SELECT COUNT(*) FROM laws_fts").fetchone()[0] == 0
    cols = [r[1] for r in conn.execute("PRAGMA table_info(laws_fts)")]
    assert "body" not in cols
