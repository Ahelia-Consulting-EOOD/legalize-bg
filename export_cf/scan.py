"""SQL-statement-aware chunk scanner (spec v1.3 self-check).

D1 caps each SQL statement at ~100,000 bytes; the exporter budgets
90,000. `max_statement_bytes` measures the longest statement in an
emitted .sql file WITHOUT parsing SQL: it splits the byte stream on
single quotes — quote-parity alternates outside/inside string literals
(an '' escape yields an empty outside segment with no ';', so parity
stays correct) — and honors ';' terminators only in outside segments.
O(n) with C-level splits.
"""

from __future__ import annotations


def max_statement_bytes(path: str) -> int:
    """Byte length (terminator ';' included, inter-statement whitespace
    excluded) of the longest SQL statement in `path`."""
    with open(path, "rb") as fh:
        data = fh.read()
    segments = data.split(b"'")
    last = len(segments) - 1
    longest = 0
    current = 0      # bytes of the statement in progress
    outside = True   # are we outside a string literal?
    for i, seg in enumerate(segments):
        boundary = 1 if i < last else 0  # the "'" consumed by this split
        if outside and b";" in seg:
            parts = seg.split(b";")
            current += len(parts[0]) + 1          # completes current stmt
            longest = max(longest, current)
            for mid in parts[1:-1]:               # whole stmts in-segment
                longest = max(longest, len(mid.lstrip()) + 1)
            current = len(parts[-1].lstrip()) + boundary
        else:
            current += len(seg) + boundary
        if boundary:
            outside = not outside
    return max(longest, current)
