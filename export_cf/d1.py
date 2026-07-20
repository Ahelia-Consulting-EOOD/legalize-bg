"""D1 dump writer: d1-schema.sql + d1-data-NNNN.sql chunks (≤50 MB each).

Streams row-by-row from the source catalog (never materializes a table),
in deterministic order. `laws_fts` rows are re-emitted as plain INSERTs
selected from the source catalog's logical laws_fts view — this is
byte-identically "the same source text the index builder uses" (the
builder inserted exactly these bg_normalize-d strings), while letting D1
build its own clean shadow tables.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

from export_cf.ddl import COPIED_TABLES, d1_schema_sql
from export_cf.sqlgen import insert_statements

CHUNK_MAX_BYTES = 50_000_000  # ≤50 MB per d1-data-NNNN.sql

# D1 hard limit: max string/BLOB/row size is 2 MB — a row at/over it
# throws SQLITE_TOOBIG at import or query time. Cap the TOTAL laws_fts
# row (law_id+title+body+category, UTF-8 bytes) with a safety margin;
# oversized bodies are truncated at a char boundary and the affected
# law_ids surface in manifest.json (documented FTS-recall divergence
# for those few giant acts — unavoidable under D1 limits).
FTS_ROW_MAX_BYTES = 1_950_000

# All tables are dumped in rowid order — FastAPI parity requires D1 to
# preserve catalog insertion order (AMBIGUOUS_NAME candidate lists and
# any no-ORDER-BY scan follow it). Sequential re-INSERT preserves it in
# D1. (For law_versions/amendments/schema_version the INTEGER PRIMARY
# KEY is the rowid alias, so this equals id/version order.)


class _ChunkWriter:
    """Sequential d1-data-NNNN.sql files, rolled before a statement
    would push the current file past `max_bytes`."""

    def __init__(self, out_dir: Path, max_bytes: int = CHUNK_MAX_BYTES):
        self.out_dir = out_dir
        self.max_bytes = max_bytes
        self._n = 0
        self._fh = None
        self._written = 0
        self.files: list[Path] = []

    def _roll(self) -> None:
        if self._fh:
            self._fh.close()
        self._n += 1
        path = self.out_dir / f"d1-data-{self._n:04d}.sql"
        self._fh = open(path, "w", encoding="utf-8", newline="\n")
        self.files.append(path)
        self._written = 0

    def write(self, stmt: str) -> None:
        size = len(stmt.encode("utf-8"))
        if self._fh is None or (self._written
                                and self._written + size > self.max_bytes):
            self._roll()
        self._fh.write(stmt)
        self._written += size

    def close(self) -> None:
        if self._fh:
            self._fh.close()
            self._fh = None


def _columns(conn: sqlite3.Connection, table: str) -> tuple[str, ...]:
    return tuple(r[1] for r in conn.execute(f"PRAGMA table_info({table})"))


def _cap_fts_row(law_id: str, title: str, body: str, category: str,
                 max_bytes: int) -> tuple[str, bool]:
    """Return (body, truncated) with body cut at a UTF-8 char boundary
    so the total row stays ≤ max_bytes."""
    fixed = sum(len((s or "").encode("utf-8"))
                for s in (law_id, title, category))
    budget = max(0, max_bytes - fixed)
    encoded = (body or "").encode("utf-8")
    if len(encoded) <= budget:
        return body, False
    return encoded[:budget].decode("utf-8", errors="ignore"), True


def export_d1(conn: sqlite3.Connection, out_dir: Path,
              chunk_max_bytes: int = CHUNK_MAX_BYTES,
              fts_row_max_bytes: int = FTS_ROW_MAX_BYTES,
              ) -> tuple[dict[str, int], list[str]]:
    """Write d1-schema.sql + d1-data-NNNN.sql under `out_dir`; returns
    (per-table row counts incl. the rebuilt laws_fts,
     law_ids whose FTS body was truncated for the D1 2 MB row limit)."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "d1-schema.sql").write_text(
        d1_schema_sql(conn), encoding="utf-8", newline="\n")

    counts: dict[str, int] = {}
    truncated: list[str] = []
    writer = _ChunkWriter(out_dir, max_bytes=chunk_max_bytes)
    try:
        for table in COPIED_TABLES:
            cols = _columns(conn, table)
            cur = conn.execute(
                f"SELECT {', '.join(cols)} FROM {table} ORDER BY rowid")
            n = 0

            def counted(cur=cur):
                nonlocal n
                for row in cur:
                    n += 1
                    yield row

            for stmt in insert_statements(table, cols, counted()):
                writer.write(stmt)
            counts[table] = n

        fts_cols = ("law_id", "title", "body", "category")
        cur = conn.execute(
            "SELECT law_id, title, body, category FROM laws_fts "
            "ORDER BY rowid")
        n = 0

        def counted_fts():
            nonlocal n
            for law_id, title, body, category in cur:
                n += 1
                body, was_cut = _cap_fts_row(law_id, title, body,
                                             category, fts_row_max_bytes)
                if was_cut:
                    truncated.append(law_id)
                yield law_id, title, body, category

        for stmt in insert_statements("laws_fts", fts_cols, counted_fts()):
            writer.write(stmt)
        counts["laws_fts"] = n
    finally:
        writer.close()
    return counts, truncated
