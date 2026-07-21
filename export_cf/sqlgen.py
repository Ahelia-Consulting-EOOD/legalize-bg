"""SQL text generation for the D1 dump.

Emits multi-row `INSERT INTO t (cols) VALUES (...), (...);` statements.
NO explicit BEGIN/COMMIT: Cloudflare D1's import path rejects SQL
transaction-control statements (each statement is atomic on D1, and
`wrangler d1 execute --file` ingests the file server-side).

Spec v1.3: D1 additionally caps every SQL STATEMENT at ~100,000 bytes
(SQLITE_TOOBIG "statement too long" — separate from the 2 MB value
cap). The budget here is STATEMENT_MAX_BYTES = 90,000 and it is STRICT:
head + tuples + separators + terminator, measured in UTF-8 bytes. Rows
too large to fit a single statement are the caller's problem —
export_cf.d1 slices oversized laws_fts bodies into INSERT + UPDATE
append statements before they ever reach the batcher.
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from typing import Any

DEFAULT_MAX_ROWS = 500
STATEMENT_MAX_BYTES = 90_000  # spec v1.3 (D1 statement cap ~100 KB)


def sql_literal(value: Any) -> str:
    """Render one Python value as a SQLite/D1 SQL literal."""
    if value is None:
        return "NULL"
    if isinstance(value, bool):
        return "1" if value else "0"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return repr(value)
    if isinstance(value, bytes):
        return "X'" + value.hex() + "'"
    return "'" + str(value).replace("'", "''") + "'"


class Batcher:
    """Incremental multi-row INSERT builder with a strict per-statement
    byte budget. `add(row)` returns a finished statement when the row
    would overflow the current batch (the row starts the next batch);
    `flush()` returns the pending statement, if any."""

    def __init__(self, table: str, columns: tuple[str, ...],
                 max_rows: int = DEFAULT_MAX_ROWS,
                 max_bytes: int = STATEMENT_MAX_BYTES):
        self._head = f"INSERT INTO {table} ({', '.join(columns)}) VALUES\n"
        self._head_bytes = len(self._head.encode("utf-8"))
        self._max_rows = max_rows
        self._max_bytes = max_bytes
        self._tuples: list[str] = []
        self._tuple_bytes = 0  # sum of tuple bytes, no separators

    def _stmt_bytes_with(self, extra: int) -> int:
        n = len(self._tuples) + 1
        # head + tuples + ",\n" separators + ";\n" terminator
        return (self._head_bytes + self._tuple_bytes + extra
                + 2 * (n - 1) + 2)

    def add(self, row: tuple) -> str | None:
        tup = "(" + ", ".join(sql_literal(v) for v in row) + ")"
        size = len(tup.encode("utf-8"))
        stmt = None
        if self._tuples and (len(self._tuples) >= self._max_rows
                             or self._stmt_bytes_with(size) > self._max_bytes):
            stmt = self.flush()
        self._tuples.append(tup)
        self._tuple_bytes += size
        return stmt

    def flush(self) -> str | None:
        if not self._tuples:
            return None
        stmt = self._head + ",\n".join(self._tuples) + ";\n"
        self._tuples = []
        self._tuple_bytes = 0
        return stmt


def insert_statements(table: str, columns: tuple[str, ...],
                      rows: Iterable[tuple],
                      max_rows: int = DEFAULT_MAX_ROWS,
                      max_bytes: int = STATEMENT_MAX_BYTES) -> Iterator[str]:
    """Stream rows into multi-row INSERT statements, each ≤ max_bytes
    TOTAL (a single row whose lone statement exceeds the budget still
    emits — callers must pre-slice such rows)."""
    b = Batcher(table, columns, max_rows=max_rows, max_bytes=max_bytes)
    for row in rows:
        stmt = b.add(row)
        if stmt:
            yield stmt
    tail = b.flush()
    if tail:
        yield tail
