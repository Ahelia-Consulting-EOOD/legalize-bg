"""SQL text generation for the D1 dump.

Emits multi-row `INSERT INTO t (cols) VALUES (...), (...);` statements.
NO explicit BEGIN/COMMIT: Cloudflare D1's import path rejects SQL
transaction-control statements (each statement is atomic on D1, and
`wrangler d1 execute --file` ingests the file server-side). Batching to
`max_rows` rows per statement gives the same import-throughput benefit;
`max_bytes` flushes early so a statement never balloons on 1 MB+ FTS
bodies (keeps every statement well under the 50 MB chunk size and
memory flat — rows are streamed, never materialized as a whole table).
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from typing import Any

DEFAULT_MAX_ROWS = 500
DEFAULT_MAX_BYTES = 1_000_000  # per-statement soft cap (bytes of SQL text)


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


def insert_statements(table: str, columns: tuple[str, ...],
                      rows: Iterable[tuple],
                      max_rows: int = DEFAULT_MAX_ROWS,
                      max_bytes: int = DEFAULT_MAX_BYTES) -> Iterator[str]:
    """Stream rows into multi-row INSERT statements (≤ max_rows rows and
    ~≤ max_bytes of SQL text each; a single oversized row still emits)."""
    head = f"INSERT INTO {table} ({', '.join(columns)}) VALUES\n"
    batch: list[str] = []
    batch_bytes = 0

    def flush() -> str:
        nonlocal batch, batch_bytes
        stmt = head + ",\n".join(batch) + ";\n"
        batch = []
        batch_bytes = 0
        return stmt

    for row in rows:
        tup = "(" + ", ".join(sql_literal(v) for v in row) + ")"
        size = len(tup.encode("utf-8"))
        if batch and (len(batch) >= max_rows
                      or batch_bytes + size > max_bytes):
            yield flush()
        batch.append(tup)
        batch_bytes += size
    if batch:
        yield flush()
