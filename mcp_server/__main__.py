"""CLI entry: `python -m mcp_server [--db PATH] [--corpus PATH] [--strict]`

Starts the FastMCP server over stdio. Designed to be invoked by Claude
Code, Claude Desktop, or OpenAI Codex via their MCP host config (see
docs/runbook/2026-05-09-phase1b1-operator-setup.md).

Pre-flight checks (operator-actionable, not part of any tool response):
  - INDEX_MISSING: catalog.db unreadable → exit code 2 with hint
  - INDEX_STALE: laws.current_commit ≠ git HEAD → soft warn (default)
    or refuse (--strict). The mismatch usually means the operator forgot
    to re-run `python -m index.build` after a git pull.

Per the queries.py docstring, the connection is opened with
`row_factory = sqlite3.Row` so column-name access works in queries/.
"""

from __future__ import annotations

import argparse
import logging
import sqlite3
import subprocess
import sys
from pathlib import Path

from mcp_server.server import build_app


log = logging.getLogger("mcp_server")


def _git_head(corpus_root: Path) -> str | None:
    """Return git HEAD's commit_hash for the corpus, or None if the
    directory is not a git repository (e.g., test environments). Real
    operator deployments always have a git-tracked corpus."""
    try:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=corpus_root, check=True, capture_output=True, text=True,
        ).stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def _check_index_state(db_path: Path, corpus_root: Path,
                       strict: bool) -> int | None:
    """Return non-None exit code if the index is in an unstartable state.

    Returns None (continue) on either:
      - clean state (HEAD == indexed commit)
      - stale state under default (soft warn, continue)

    Returns int exit code on:
      - INDEX_MISSING: catalog.db doesn't exist
      - INDEX_STALE under --strict
    """
    if not db_path.exists():
        log.error(
            "INDEX_MISSING: %s does not exist. "
            "Run `python -m index.build --db %s --corpus %s`.",
            db_path, db_path, corpus_root,
        )
        return 2

    head = _git_head(corpus_root)
    if head is None:
        # Not a git repo (or git not available). Skip stale check —
        # operator is likely running in a non-standard environment;
        # don't block startup.
        return None

    conn = sqlite3.connect(str(db_path))
    try:
        row = conn.execute(
            "SELECT DISTINCT current_commit FROM laws LIMIT 1"
        ).fetchone()
    finally:
        conn.close()

    indexed = row[0] if row else None
    if indexed != head:
        msg = (
            f"INDEX_STALE: git HEAD={head[:8]} but indexed "
            f"current_commit={(indexed or '?')[:8]}. "
            f"Re-run `python -m index.build --db {db_path} "
            f"--corpus {corpus_root}` to refresh."
        )
        if strict:
            log.error("%s — refusing to start (--strict)", msg)
            return 3
        log.warning("%s — continuing (use --strict to refuse)", msg)
    return None


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    ap = argparse.ArgumentParser(
        prog="mcp_server",
        description="legalize-bg MCP server — stdio transport.",
    )
    ap.add_argument("--db", type=Path, default=Path("catalog.db"),
                    help="Path to catalog.db (default: ./catalog.db)")
    ap.add_argument("--corpus", type=Path, default=Path("."),
                    help="Path to legalize-bg repo root (default: cwd)")
    ap.add_argument("--strict", action="store_true",
                    help="Refuse to start when catalog is stale vs git HEAD")
    args = ap.parse_args(argv)

    db_path = args.db.resolve()
    corpus_root = args.corpus.resolve()

    rc = _check_index_state(db_path, corpus_root, args.strict)
    if rc is not None:
        return rc

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row

    handle = build_app(conn=conn, corpus_root=corpus_root)
    log.info("starting MCP server: db=%s corpus=%s tools=%s",
             db_path, corpus_root, sorted(handle._tools.keys()))
    handle.mcp.run()  # stdio transport (FastMCP default)
    return 0


if __name__ == "__main__":
    sys.exit(main())
