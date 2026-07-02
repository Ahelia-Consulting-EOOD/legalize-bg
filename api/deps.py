"""Per-request read-only connections (D-050: the REST API does NOT
inherit the MCP global lock). Each request opens its own `mode=ro`
connection with the D-051 pragmas and closes it after the response.
`check_same_thread=False` is REQUIRED: FastAPI may run a sync
dependency and its endpoint on different threadpool threads."""

import sqlite3
from collections.abc import Iterator

from fastapi import Request

# Shared Cache-Control value for the routes that cache for 5 minutes
# (/laws/{slug}, /laws/{slug}/articles/{art}, /laws/{slug}/history).
# `/search` uses its own shorter-lived max-age=60 (not a duplicate of
# this constant — kept local to api/routes/search.py).
CACHE_HEADER_300 = "public, max-age=300"


def get_conn(request: Request) -> Iterator[sqlite3.Connection]:
    db_path = request.app.state.db_path
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True,
                           check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        # D-051 (FR-027): memory-map the 1.2 GB catalog + 64 MB page
        # cache. Inside `try` (PR review fix #6) so a PRAGMA failure
        # can't leak the just-opened connection.
        conn.execute("PRAGMA mmap_size = 1073741824")
        conn.execute("PRAGMA cache_size = -65536")
        yield conn
    finally:
        conn.close()
