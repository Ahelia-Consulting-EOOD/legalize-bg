"""SQLite Catalog Index — per docs/data/schema-reference.md."""

import sqlite3
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS laws (
    law_id TEXT PRIMARY KEY,
    doc_id INTEGER,
    title TEXT NOT NULL,
    category TEXT NOT NULL,
    status TEXT DEFAULT 'vigente',
    current_commit TEXT
);

CREATE TABLE IF NOT EXISTS law_versions (
    id INTEGER PRIMARY KEY,
    law_id TEXT REFERENCES laws(law_id),
    valid_from DATE NOT NULL,
    valid_to DATE,
    commit_hash TEXT NOT NULL,
    dv_issue TEXT,
    dv_date DATE,
    amending_act TEXT
);

CREATE TABLE IF NOT EXISTS amendments (
    id INTEGER PRIMARY KEY,
    source_act TEXT NOT NULL,
    target_law TEXT REFERENCES laws(law_id),
    operation TEXT NOT NULL,
    affected_articles TEXT,
    dv_issue TEXT,
    dv_date DATE
);

CREATE TABLE IF NOT EXISTS provisions (
    id INTEGER PRIMARY KEY,
    law_id TEXT REFERENCES laws(law_id),
    article TEXT NOT NULL,
    paragraph TEXT,
    valid_from DATE NOT NULL,
    valid_to DATE,
    text_hash TEXT
);

CREATE INDEX IF NOT EXISTS idx_versions_date ON law_versions(law_id, valid_from);
CREATE INDEX IF NOT EXISTS idx_amendments_target ON amendments(target_law, dv_date);
CREATE INDEX IF NOT EXISTS idx_provisions_article ON provisions(law_id, article, valid_from);
"""


class CatalogIndex:
    def __init__(self, db_path: str = "catalog.db"):
        self._conn = sqlite3.connect(db_path)
        self._conn.row_factory = sqlite3.Row

    def initialize(self):
        self._conn.executescript(SCHEMA)

    def insert_law(self, law_id: str, doc_id: int, title: str,
                   category: str, commit_hash: str, effective_date: str):
        self._conn.execute(
            "INSERT INTO laws (law_id, doc_id, title, category, current_commit) VALUES (?, ?, ?, ?, ?)",
            (law_id, doc_id, title, category, commit_hash),
        )
        self._conn.execute(
            "INSERT INTO law_versions (law_id, valid_from, commit_hash) VALUES (?, ?, ?)",
            (law_id, effective_date, commit_hash),
        )
        self._conn.commit()

    def get_law(self, law_id: str) -> dict | None:
        row = self._conn.execute("SELECT * FROM laws WHERE law_id = ?", (law_id,)).fetchone()
        return dict(row) if row else None

    def get_versions(self, law_id: str) -> list[dict]:
        rows = self._conn.execute(
            "SELECT * FROM law_versions WHERE law_id = ? ORDER BY valid_from",
            (law_id,),
        ).fetchall()
        return [dict(r) for r in rows]

    def count_by_category(self) -> dict[str, int]:
        rows = self._conn.execute(
            "SELECT category, COUNT(*) as cnt FROM laws GROUP BY category"
        ).fetchall()
        return {r["category"]: r["cnt"] for r in rows}

    def list_tables(self) -> list[str]:
        rows = self._conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
        return [r["name"] for r in rows]

    def close(self):
        self._conn.close()
