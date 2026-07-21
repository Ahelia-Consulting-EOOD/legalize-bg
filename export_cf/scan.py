"""SQL-statement-aware chunk scanner (spec v1.3/v1.3.2 self-checks).

Splits emitted .sql files into statements WITHOUT parsing SQL: the byte
stream is split on single quotes — quote parity alternates
outside/inside string literals (an '' escape yields an empty outside
segment with no ';', so parity stays correct) — and ';' terminates a
statement only in outside segments. This is the ONLY safe way to split
these files: string literals contain raw newlines (legal text), so any
line-based splitting is wrong.

Used by --verify for two checks: max statement size ≤ the D1 budget
(v1.3) and per-statement idempotency guards in the d1-fts series
(v1.3.2).
"""

from __future__ import annotations

from collections.abc import Iterator


def iter_statements(path: str) -> Iterator[bytes]:
    """Yield each SQL statement in `path` as bytes (terminator ';'
    included, inter-statement whitespace stripped)."""
    with open(path, "rb") as fh:
        data = fh.read()
    segments = data.split(b"'")
    last = len(segments) - 1
    buf = bytearray()
    outside = True
    for i, seg in enumerate(segments):
        boundary = i < last  # this split consumed one "'"
        if outside and b";" in seg:
            parts = seg.split(b";")
            buf += parts[0]
            buf += b";"
            yield bytes(buf)
            for mid in parts[1:-1]:  # whole statements inside one segment
                yield mid.lstrip() + b";"
            buf = bytearray(parts[-1].lstrip())
            if boundary:
                buf += b"'"
        else:
            buf += seg
            if boundary:
                buf += b"'"
        if boundary:
            outside = not outside
    tail = bytes(buf).strip()
    if tail:  # unterminated trailing content — surface it to callers
        yield tail


def max_statement_bytes(path: str) -> int:
    """Byte length of the longest SQL statement in `path`."""
    return max((len(s) for s in iter_statements(path)), default=0)
