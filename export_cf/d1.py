"""D1 dump writer (spec v2.0): d1-schema.sql + three chunk series.

  d1-meta-NNNN.sql — laws, law_versions, amendments, schema_version as
      plain multi-row INSERTs. NOT idempotent: this series must only be
      imported into EMPTY tables (drop/recreate via d1-schema.sql
      first). Kept separate so a partially loaded database can reload
      one series without touching the others.
  d1-fts-laws-NNNN.sql — title-only laws_fts rows (law_id, title,
      category), one FULLY IDEMPOTENT statement per row:
      `INSERT ... SELECT ... WHERE NOT EXISTS (law_id)`. Titles are
      orders of magnitude below the statement budget, so this series
      never slices.
  d1-fts-articles-NNNN.sql — one articles_fts row per body segment
      (law_id, seg_no, kind, label, body, category), FULLY IDEMPOTENT:
      `INSERT ... SELECT ... WHERE NOT EXISTS (law_id AND seg_no)`
      plus, for rows whose body exceeds the statement budget, append
      UPDATEs guarded by `AND length(CAST(body AS BLOB)) =
      <expected-byte-offset>`. D1 import success is not reliably
      observable client-side (a "fetch failed" attempt may have
      committed server-side), so blind retries of both fts series are
      safe at ANY point.

Streams row-by-row from the source catalog (never materializes a
table), in rowid order — FastAPI parity requires D1 to preserve catalog
insertion order (AMBIGUOUS_NAME candidate lists and no-ORDER-BY scans
follow it); for law_versions/amendments/schema_version the INTEGER
PRIMARY KEY is the rowid alias, so this equals id/version order. For
articles_fts, rowid order equals per-act seg_no emission order.

FTS rows are re-emitted from the source catalog's logical laws_fts /
articles_fts views — byte-identically "the same source text the index
builder wrote", while letting D1 build its own clean shadow tables.
The v1.2 body-cap truncation is RETIRED: index/segments.py chunks
every segment to ≤ SEG_MAX_BYTES (400,000) normalized UTF-8 bytes, so
no emitted value can approach D1's 2MB cap; the exporter only ASSERTS
that invariant (a violation means a mis-built catalog).
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

from index.segments import SEG_MAX_BYTES

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

# D1's per-value hard cap. Structurally unreachable (SEG_MAX_BYTES is
# 5x smaller) — asserted anyway so the invariant is enforced where it
# matters, not just documented.
D1_VALUE_MAX_BYTES = 2_000_000


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


def _title_row_statement(law_id: str, title: str, category: str,
                         stmt_max_bytes: int) -> str:
    """One laws_fts (title-only) row → one idempotent statement keyed
    on law_id. No slicing path: laws_fts has no body column to append
    to, and titles (max ~1.6KB on the live corpus) sit far below the
    budget — a title overflowing it means corrupt input, so fail."""
    stmt = ("INSERT INTO laws_fts (law_id, title, category) SELECT "
            f"{sql_literal(law_id)}, {sql_literal(title)}, "
            f"{sql_literal(category)}"
            " WHERE NOT EXISTS (SELECT 1 FROM laws_fts WHERE law_id = "
            f"{sql_literal(law_id)});\n")
    if len(stmt.encode("utf-8")) > stmt_max_bytes:
        raise ValueError(
            f"laws_fts title row {law_id!r} exceeds "
            f"stmt_max_bytes={stmt_max_bytes} and cannot be sliced")
    return stmt


def _segment_row_statements(law_id: str, seg_no: str, kind: str,
                            label: str, body: str, category: str,
                            stmt_max_bytes: int) -> list[str]:
    """One articles_fts row → idempotent statement list.

    The INSERT is per-row `INSERT ... SELECT ... WHERE NOT EXISTS
    (SELECT 1 FROM articles_fts WHERE law_id = ... AND seg_no = ...)`
    so a retried import can never duplicate a row. When the body cannot
    fit one statement (v1.3 budget — segments run up to 400KB), the
    INSERT carries the first char-boundary slice and each remaining
    slice is appended with `UPDATE articles_fts SET body = body ||
    '<slice>' WHERE law_id = ... AND seg_no = ... AND
    length(CAST(body AS BLOB)) = <bytes-before-this-slice>` — the
    byte-offset guard makes every append apply EXACTLY once regardless
    of retries (the double-application incident: D1 "fetch failed"
    imports may have committed server-side). Statements are keyed on
    (law_id, seg_no) because D1 import has no last_insert_rowid
    persistence. Slices are raw substrings, so their concatenation
    reproduces the body byte-exactly."""
    key = f"law_id = {sql_literal(law_id)} AND seg_no = {sql_literal(seg_no)}"
    guard = (f" WHERE NOT EXISTS (SELECT 1 FROM articles_fts WHERE {key});\n")
    head = ("INSERT INTO articles_fts (law_id, seg_no, kind, label, body, "
            "category) SELECT "
            f"{sql_literal(law_id)}, {sql_literal(seg_no)}, "
            f"{sql_literal(kind)}, {sql_literal(label)}, ")
    single = (head + f"{sql_literal(body)}, {sql_literal(category)}" + guard)
    if len(single.encode("utf-8")) <= stmt_max_bytes:
        return [single]
    prefix = head + "'"
    mid_suffix = f"', {sql_literal(category)}" + guard
    budget = (stmt_max_bytes - len(prefix.encode("utf-8"))
              - len(mid_suffix.encode("utf-8")))
    if budget <= 0:
        raise ValueError(
            f"stmt_max_bytes={stmt_max_bytes} too small to slice "
            f"articles_fts row ({law_id!r}, seg {seg_no})")
    first_esc, first_raw, rest = _take_escaped_slice(body, budget)
    stmts = [prefix + first_esc + mid_suffix]
    offset = len(first_raw.encode("utf-8"))
    upd_prefix = "UPDATE articles_fts SET body = body || '"
    while rest:
        upd_suffix = (f"' WHERE {key} "
                      f"AND length(CAST(body AS BLOB)) = {offset};\n")
        upd_budget = (stmt_max_bytes - len(upd_prefix.encode("utf-8"))
                      - len(upd_suffix.encode("utf-8")))
        if upd_budget <= 0:
            raise ValueError(
                f"stmt_max_bytes={stmt_max_bytes} too small to slice "
                f"articles_fts row ({law_id!r}, seg {seg_no})")
        piece_esc, piece_raw, rest = _take_escaped_slice(rest, upd_budget)
        stmts.append(upd_prefix + piece_esc + upd_suffix)
        offset += len(piece_raw.encode("utf-8"))
    return stmts


def export_d1(conn: sqlite3.Connection, out_dir: Path,
              chunk_max_bytes: int = CHUNK_MAX_BYTES,
              stmt_max_bytes: int = STATEMENT_MAX_BYTES,
              seg_max_bytes: int = SEG_MAX_BYTES) -> dict:
    """Write d1-schema.sql + d1-meta-NNNN.sql + d1-fts-laws-NNNN.sql +
    d1-fts-articles-NNNN.sql under `out_dir`. Returns
    {"counts": per-table row counts (incl. both rebuilt FTS tables),
     "max_fts_body_bytes": largest emitted articles_fts body (must be
         ≤ seg_max_bytes — the SEG_MAX_BYTES chunking contract),
     "max_statement_bytes": largest emitted statement (must be ≤90,000),
     "fts_guards": {"inserts": N, "updates": N} guarded-statement
         counts across BOTH fts series}.
    Raises ValueError if any articles_fts body violates seg_max_bytes
    (which would mean a mis-built catalog, not an exporter condition).
    """
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "d1-schema.sql").write_text(
        d1_schema_sql(conn), encoding="utf-8", newline="\n")

    counts: dict[str, int] = {}
    max_body = 0
    guards = {"inserts": 0, "updates": 0}
    meta_writer = _ChunkWriter(out_dir, "d1-meta-", max_bytes=chunk_max_bytes)
    laws_writer = _ChunkWriter(out_dir, "d1-fts-laws-",
                               max_bytes=chunk_max_bytes)
    arts_writer = _ChunkWriter(out_dir, "d1-fts-articles-",
                               max_bytes=chunk_max_bytes)
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
            "SELECT law_id, title, category FROM laws_fts ORDER BY rowid")
        n = 0
        for law_id, title, category in cur:
            n += 1
            laws_writer.write(_title_row_statement(
                law_id, title, category, stmt_max_bytes))
            guards["inserts"] += 1
        counts["laws_fts"] = n

        cur = conn.execute(
            "SELECT law_id, seg_no, kind, label, body, category "
            "FROM articles_fts ORDER BY rowid")
        n = 0
        for law_id, seg_no, kind, label, body, category in cur:
            n += 1
            body_bytes = len((body or "").encode("utf-8"))
            if body_bytes > seg_max_bytes:
                raise ValueError(
                    f"articles_fts row ({law_id!r}, seg {seg_no}) body is "
                    f"{body_bytes} bytes > seg_max_bytes={seg_max_bytes} "
                    "(SEG_MAX_BYTES contract violated — rebuild the "
                    "catalog with python -m index.build)")
            max_body = max(max_body, body_bytes)
            stmts = _segment_row_statements(law_id, seg_no, kind, label,
                                            body, category, stmt_max_bytes)
            guards["inserts"] += 1
            guards["updates"] += len(stmts) - 1
            for stmt in stmts:
                arts_writer.write(stmt)
        counts["articles_fts"] = n
    finally:
        meta_writer.close()
        laws_writer.close()
        arts_writer.close()
    assert max_body < D1_VALUE_MAX_BYTES  # structural (seg cap is 5x lower)
    return {
        "counts": counts,
        "max_fts_body_bytes": max_body,
        "max_statement_bytes": max(meta_writer.max_stmt_bytes,
                                   laws_writer.max_stmt_bytes,
                                   arts_writer.max_stmt_bytes),
        "fts_guards": guards,
    }
