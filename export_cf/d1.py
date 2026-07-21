"""D1 dump writer (spec v1.3.2): d1-schema.sql + two chunk series.

  d1-meta-NNNN.sql — laws, law_versions, amendments, schema_version as
      plain multi-row INSERTs. NOT idempotent: this series must only be
      imported into EMPTY tables (drop/recreate via d1-schema.sql
      first). Kept separate so a partially loaded database can reload
      one series without touching the other.
  d1-fts-NNNN.sql — laws_fts as FULLY IDEMPOTENT per-row statements:
      `INSERT ... SELECT ... WHERE NOT EXISTS (law_id)` plus, for rows
      whose body exceeds the statement budget, append UPDATEs guarded by
      `AND length(CAST(body AS BLOB)) = <expected-byte-offset>`. D1
      import success is not reliably observable client-side (a "fetch
      failed" attempt may have committed server-side), so blind retries
      of this series are safe at ANY point.

Streams row-by-row from the source catalog (never materializes a
table), in rowid order — FastAPI parity requires D1 to preserve catalog
insertion order (AMBIGUOUS_NAME candidate lists and no-ORDER-BY scans
follow it); for law_versions/amendments/schema_version the INTEGER
PRIMARY KEY is the rowid alias, so this equals id/version order.

`laws_fts` rows are re-emitted from the source catalog's logical
laws_fts view — byte-identically "the same source text the index
builder uses", while letting D1 build its own clean shadow tables.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

from export_cf.ddl import COPIED_TABLES, d1_schema_sql
from export_cf.sqlgen import (
    STATEMENT_MAX_BYTES,
    insert_statements,
    sql_literal,
)

# v1.3.1: 12 MB per chunk file. 50 MB chunks kept D1's import long-poll
# open long enough for transient "fetch failed" aborts; 12 MB imports
# reliably in under a minute per chunk.
CHUNK_MAX_BYTES = 12_000_000

# Spec v1.2: the indexed FTS body is DEFINED as "bg_normalize(body)
# truncated to 1,900,000 UTF-8 bytes at a character boundary" — the
# same cap lands upstream in index/fts.py via a separate owner-merged
# PR; the exporter caps unconditionally. (v1.3.2 correction: D1 values
# up to 2,000,000 bytes are empirically fine — the earlier TOOBIG was
# retry double-application — but the ratified body definition stays.)
# Affected law_ids surface in manifest.json `fts_truncated`.
FTS_BODY_MAX_BYTES = 1_900_000


class _ChunkWriter:
    """Sequential {prefix}NNNN.sql files, rolled before a statement
    would push the current file past `max_bytes`.

    INVARIANT (v1.3.1): chunk files break ONLY at statement boundaries
    — write() takes one complete statement and the roll happens between
    writes, never inside one. This matters because string literals
    contain RAW NEWLINES (legal text): any line-based post-splitting of
    these files is unsafe; the only safe split points are the ';\\n'
    statement ends, and each emitted file already respects them (every
    chunk is independently executable in sequence)."""

    def __init__(self, out_dir: Path, prefix: str,
                 max_bytes: int = CHUNK_MAX_BYTES):
        self.out_dir = out_dir
        self.prefix = prefix
        self.max_bytes = max_bytes
        self._n = 0
        self._fh = None
        self._written = 0
        self.max_stmt_bytes = 0
        self.files: list[Path] = []

    def _roll(self) -> None:
        if self._fh:
            self._fh.close()
        self._n += 1
        path = self.out_dir / f"{self.prefix}{self._n:04d}.sql"
        self._fh = open(path, "w", encoding="utf-8", newline="\n")
        self.files.append(path)
        self._written = 0

    def write(self, stmt: str) -> None:
        """Write ONE complete SQL statement (invariant: one call == one
        statement, so max_stmt_bytes is exact)."""
        size = len(stmt.encode("utf-8"))
        self.max_stmt_bytes = max(self.max_stmt_bytes, size)
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


def _cap_fts_body(body: str, max_bytes: int) -> tuple[str, bool]:
    """Return (body, truncated): body cut to ≤ max_bytes UTF-8 bytes at
    a character boundary (spec v1.2 definition, byte-identical to the
    upstream index/fts.py cap)."""
    encoded = (body or "").encode("utf-8")
    if len(encoded) <= max_bytes:
        return body, False
    return encoded[:max_bytes].decode("utf-8", errors="ignore"), True


def _take_escaped_slice(s: str, budget_bytes: int) -> tuple[str, str, str]:
    """Split `s` at the largest char boundary whose SQL-escaped UTF-8
    form fits `budget_bytes`; returns (escaped_slice, raw_slice,
    raw_remainder). Escaped length is monotonic in the char count, so
    binary search."""
    def esc_len(k: int) -> int:
        return len(s[:k].replace("'", "''").encode("utf-8"))

    lo, hi = 0, min(len(s), budget_bytes)
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if esc_len(mid) <= budget_bytes:
            lo = mid
        else:
            hi = mid - 1
    return s[:lo].replace("'", "''"), s[:lo], s[lo:]


def _fts_row_statements(law_id: str, title: str, body: str, category: str,
                        stmt_max_bytes: int) -> list[str]:
    """One laws_fts row → idempotent statement list (spec v1.3.2).

    The INSERT is per-row `INSERT ... SELECT ... WHERE NOT EXISTS
    (SELECT 1 FROM laws_fts WHERE law_id = ...)` so a retried import
    can never duplicate a row. When the body cannot fit one statement
    (v1.3 budget), the INSERT carries the first char-boundary slice and
    each remaining slice is appended with
    `UPDATE laws_fts SET body = body || '<slice>' WHERE law_id = ...
    AND length(CAST(body AS BLOB)) = <bytes-before-this-slice>` — the
    byte-offset guard makes every append apply EXACTLY once regardless
    of retries (the double-application incident: D1 "fetch failed"
    imports may have committed server-side). Statements are keyed on
    law_id because D1 import has no last_insert_rowid persistence.
    Slices are raw substrings, so their concatenation reproduces the
    body byte-exactly."""
    guard = (" WHERE NOT EXISTS (SELECT 1 FROM laws_fts WHERE law_id = "
             f"{sql_literal(law_id)});\n")
    head = "INSERT INTO laws_fts (law_id, title, body, category) SELECT "
    single = (head + f"{sql_literal(law_id)}, {sql_literal(title)}, "
              f"{sql_literal(body)}, {sql_literal(category)}" + guard)
    if len(single.encode("utf-8")) <= stmt_max_bytes:
        return [single]
    prefix = (head + f"{sql_literal(law_id)}, {sql_literal(title)}, '")
    mid_suffix = f"', {sql_literal(category)}" + guard
    budget = (stmt_max_bytes - len(prefix.encode("utf-8"))
              - len(mid_suffix.encode("utf-8")))
    if budget <= 0:
        raise ValueError(
            f"stmt_max_bytes={stmt_max_bytes} too small to slice "
            f"laws_fts row {law_id!r}")
    first_esc, first_raw, rest = _take_escaped_slice(body, budget)
    stmts = [prefix + first_esc + mid_suffix]
    offset = len(first_raw.encode("utf-8"))
    upd_prefix = "UPDATE laws_fts SET body = body || '"
    while rest:
        upd_suffix = (f"' WHERE law_id = {sql_literal(law_id)} "
                      f"AND length(CAST(body AS BLOB)) = {offset};\n")
        upd_budget = (stmt_max_bytes - len(upd_prefix.encode("utf-8"))
                      - len(upd_suffix.encode("utf-8")))
        if upd_budget <= 0:
            raise ValueError(
                f"stmt_max_bytes={stmt_max_bytes} too small to slice "
                f"laws_fts row {law_id!r}")
        piece_esc, piece_raw, rest = _take_escaped_slice(rest, upd_budget)
        stmts.append(upd_prefix + piece_esc + upd_suffix)
        offset += len(piece_raw.encode("utf-8"))
    return stmts


def export_d1(conn: sqlite3.Connection, out_dir: Path,
              chunk_max_bytes: int = CHUNK_MAX_BYTES,
              fts_body_max_bytes: int = FTS_BODY_MAX_BYTES,
              stmt_max_bytes: int = STATEMENT_MAX_BYTES) -> dict:
    """Write d1-schema.sql + d1-meta-NNNN.sql + d1-fts-NNNN.sql under
    `out_dir`. Returns
    {"counts": per-table row counts (incl. rebuilt laws_fts),
     "fts_truncated": law_ids whose FTS body hit the v1.2 byte cap,
     "max_statement_bytes": largest emitted statement (must be ≤90,000),
     "fts_guards": {"inserts": N, "updates": N} guarded-statement counts}.
    """
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "d1-schema.sql").write_text(
        d1_schema_sql(conn), encoding="utf-8", newline="\n")

    counts: dict[str, int] = {}
    truncated: list[str] = []
    guards = {"inserts": 0, "updates": 0}
    meta_writer = _ChunkWriter(out_dir, "d1-meta-", max_bytes=chunk_max_bytes)
    fts_writer = _ChunkWriter(out_dir, "d1-fts-", max_bytes=chunk_max_bytes)
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

            for stmt in insert_statements(table, cols, counted(),
                                          max_bytes=stmt_max_bytes):
                meta_writer.write(stmt)
            counts[table] = n

        cur = conn.execute(
            "SELECT law_id, title, body, category FROM laws_fts "
            "ORDER BY rowid")
        n = 0
        for law_id, title, body, category in cur:
            n += 1
            body, was_cut = _cap_fts_body(body, fts_body_max_bytes)
            if was_cut:
                truncated.append(law_id)
            stmts = _fts_row_statements(law_id, title, body, category,
                                        stmt_max_bytes)
            guards["inserts"] += 1
            guards["updates"] += len(stmts) - 1
            for stmt in stmts:
                fts_writer.write(stmt)
        counts["laws_fts"] = n
    finally:
        meta_writer.close()
        fts_writer.close()
    return {
        "counts": counts,
        "fts_truncated": truncated,
        "max_statement_bytes": max(meta_writer.max_stmt_bytes,
                                   fts_writer.max_stmt_bytes),
        "fts_guards": guards,
    }
