"""CLI entry: `python -m mcp_server [--db PATH] [--corpus PATH] [--strict]
              [--transport {stdio,http,sse,streamable-http}] [--host H] [--port P]`

Starts the FastMCP server. Default transport is stdio — invoked locally by
Claude Code, Claude Desktop, or OpenAI Codex via their MCP host config (see
docs/runbook/2026-05-09-phase1b1-operator-setup.md). Network transports
(http/sse/streamable-http) serve over HTTP with per-call mode=ro connections
(FR-029/FR-031); they bind loopback by default — front them with a TLS/auth
reverse proxy before public exposure.

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
import json
import logging
import os
import signal
import sqlite3
import subprocess
import sys
from pathlib import Path

from mcp_server.server import build_app


log = logging.getLogger("mcp_server")


def _install_metrics_signal_handler(handle):
    """SIGUSR1 → log the metrics snapshot as one JSON line. The stdio
    transport has no side channel, so a signal is the only way an
    operator can pull runtime metrics without killing the process
    (review 2026-07-02). Returns the handler for direct-call tests."""
    def _dump(signum, frame):
        log.info("metrics_snapshot: %s",
                 json.dumps(handle.metrics_snapshot(), ensure_ascii=False))
    try:
        signal.signal(signal.SIGUSR1, _dump)
    except (ValueError, OSError, AttributeError):
        pass  # non-main thread, or platform without SIGUSR1 (Windows)
    return _dump


def _check_corpus_defective() -> int | None:
    """Deploy-guard: refuse to serve a corpus flagged as defective (D-047).

    Returns a non-None exit code when ``LEGALIZE_CORPUS_DEFECTIVE=1`` and the
    explicit ``LEGALIZE_ALLOW_DEFECTIVE=1`` override is not set; otherwise
    None (continue). The flag is OFF by default, so this is a dormant safety
    net: it exists so a known-incomplete corpus (missing definitions and
    transitional/final provisions) can never be served unnoticed. Checked
    before any DB access so the refusal wins over INDEX_MISSING/INDEX_STALE.
    """
    if (os.environ.get("LEGALIZE_CORPUS_DEFECTIVE") == "1"
            and os.environ.get("LEGALIZE_ALLOW_DEFECTIVE") != "1"):
        log.error(
            "REFUSING TO START: corpus flagged defective "
            "(LEGALIZE_CORPUS_DEFECTIVE=1; D-047 parser data-loss). "
            "Definitions and transitional/final provisions may be missing. "
            "Set LEGALIZE_ALLOW_DEFECTIVE=1 to override for debugging only."
        )
        return 2
    return None


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

    # Single-threaded preflight check; the FastMCP runtime connection
    # is opened separately at the bottom of main() with
    # check_same_thread=False so worker threads can use it.
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
        description="legalize-bg MCP server — stdio (default) or network transport.",
    )
    ap.add_argument("--db", type=Path, default=Path("catalog.db"),
                    help="Path to catalog.db (default: ./catalog.db)")
    ap.add_argument("--corpus", type=Path, default=Path("."),
                    help="Path to legalize-bg repo root (default: cwd)")
    ap.add_argument("--strict", action="store_true",
                    help="Refuse to start when catalog is stale vs git HEAD")
    ap.add_argument("--transport", default="stdio",
                    choices=["stdio", "http", "sse", "streamable-http"],
                    help="MCP transport (default: stdio — the local/global "
                         "model). Network transports (http/sse/streamable-http) "
                         "serve over HTTP with per-call connections "
                         "(FR-029/FR-031).")
    ap.add_argument("--host", default="127.0.0.1",
                    help="Bind host for network transports (default: 127.0.0.1, "
                         "loopback only — put a TLS/auth reverse proxy in front "
                         "before exposing publicly, FR-031 Phase C).")
    ap.add_argument("--port", type=int, default=8000,
                    help="Bind port for network transports (default: 8000).")
    args = ap.parse_args(argv)

    db_path = args.db.resolve()
    corpus_root = args.corpus.resolve()

    # Deploy-guard first: a corpus flagged defective must not be served, even
    # if the index is otherwise present and fresh (D-047 Phase 0 / Task 0).
    rc = _check_corpus_defective()
    if rc is not None:
        return rc

    rc = _check_index_state(db_path, corpus_root, args.strict)
    if rc is not None:
        return rc

    # Transport selection (FR-031). stdio (the default) keeps the persistent
    # shared connection + D-040 lock — zero behavior change for local/global
    # users, and the warm connection the perf budgets assume (DEFERRED
    # D-2026-07-02-01). Network transports use the FR-029 per-call `mode=ro`
    # model (build_app(db_path=)) so concurrent remote clients don't serialize
    # behind one process-wide lock.
    if args.transport == "stdio":
        if args.host != "127.0.0.1" or args.port != 8000:
            log.warning(
                "--host/--port are ignored for the stdio transport "
                "(host=%s port=%s); they apply only to network transports "
                "(--transport http/sse/streamable-http).",
                args.host, args.port)
        # FastMCP runs tool calls on a worker thread; SQLite refuses
        # cross-thread connection usage by default. The catalog is read-only
        # at runtime (writes happen via `index.build`), so disabling the
        # same-thread guard is safe — concurrent writers would still be
        # serialized by SQLite's locking even if we had any.
        conn = sqlite3.connect(str(db_path), check_same_thread=False)
        conn.row_factory = sqlite3.Row
        # FR-027: the 1.2 GB catalog is read-only at serve time — memory-map
        # it (page-cache reads without syscalls) and give SQLite a 64 MB
        # page cache. Both are per-connection and harmless on small DBs.
        conn.execute("PRAGMA mmap_size = 1073741824")
        conn.execute("PRAGMA cache_size = -65536")
        handle = build_app(conn=conn, corpus_root=corpus_root)
        _install_metrics_signal_handler(handle)
        log.info("starting MCP server: transport=stdio db=%s corpus=%s tools=%s",
                 db_path, corpus_root, sorted(handle._tools.keys()))
        handle.mcp.run()  # stdio transport (FastMCP default)
    else:
        # Per-call mode=ro connections (FR-029); build_app opens/pragmas/closes
        # one per tool call, so no shared connection is held here.
        handle = build_app(db_path=str(db_path), corpus_root=corpus_root)
        _install_metrics_signal_handler(handle)
        log.info("starting MCP server: transport=%s host=%s port=%s db=%s "
                 "corpus=%s tools=%s (per-call mode=ro connections)",
                 args.transport, args.host, args.port, db_path, corpus_root,
                 sorted(handle._tools.keys()))
        handle.mcp.run(transport=args.transport, host=args.host,
                       port=args.port)
    return 0


if __name__ == "__main__":
    sys.exit(main())
