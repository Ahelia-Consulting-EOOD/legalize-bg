"""Export the live FastMCP tool schemas to a static `tools.json`
artifact for downstream callers.

Usage:
    .venv/bin/python -m mcp_server.export_tools --output tools.json

Why:
    Phase 1b.2 deliverable D-024 / D-2026-05-09-06 closure: callers
    consuming the MCP via the JSON-RPC `tools/list` endpoint already
    get these schemas at runtime, but downstream tooling (other-
    language clients, openapi-style codegen, doc renderers) wants a
    static artifact with a stable version tag.

    The CLI is the source of truth — `tools.json` is the artifact. CI
    runs `python -m mcp_server.export_tools --output /tmp/tools.json`
    and `diff` against the committed file, so any code change that
    shifts a tool schema either lands a regenerated tools.json or
    fails CI (see tests/mcp_server/test_export_tools.py).

Versioning:
    Top-level `version` field follows additive-SemVer: any change that
    only adds optional fields stays at 1.x; a breaking change (field
    removal or required-field addition) bumps to 2.0. The version is
    read from this script — code-side authority.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sqlite3
import sys
from pathlib import Path

from mcp_server.errors import ERROR_CODES
from mcp_server.server import build_app

# Bumped on any breaking change to the tool schemas. Additive changes
# (new optional input arg, new optional output field) stay at 1.x.
TOOLS_JSON_VERSION = "1.1.0"


def export_tool_schemas(corpus_root: Path | None = None) -> dict:
    """Build a transient FastMCP app and dump its tool schemas as a
    versioned dict ready for json.dumps."""
    # Use an in-memory DB — we don't actually run the tools, just ask
    # FastMCP what their input/output schemas look like.
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    app = build_app(conn, corpus_root=corpus_root or Path("."))

    async def _list() -> list[dict]:
        tools = await app.mcp.list_tools()
        return [
            {
                "name": t.name,
                "description": t.description,
                "input_schema": t.parameters,
                "output_schema": t.output_schema,
            }
            for t in tools
        ]

    tool_dicts = asyncio.run(_list())

    return {
        "version": TOOLS_JSON_VERSION,
        "spec": "https://modelcontextprotocol.io/specification/server/tools",
        "server": {
            "name": "legalize-bg",
            "phase": "2",
            "transport": "stdio",
        },
        "tools": tool_dicts,
        "error_codes": sorted(ERROR_CODES),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Export legalize-bg MCP tool schemas to tools.json."
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("tools.json"),
        help="Output path (default: ./tools.json).",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help=("Compare existing --output file against freshly generated "
              "schemas; exit 1 on mismatch (CI parity check)."),
    )
    args = parser.parse_args(argv)

    payload = export_tool_schemas()
    serialized = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"

    if args.check:
        if not args.output.exists():
            print(f"ERROR: {args.output} does not exist; run without "
                  "--check to create it.", file=sys.stderr)
            return 1
        existing = args.output.read_text(encoding="utf-8")
        if existing != serialized:
            print(f"ERROR: {args.output} is out of date with the live "
                  "MCP tool schemas. Run `python -m "
                  "mcp_server.export_tools --output tools.json` to "
                  "regenerate.", file=sys.stderr)
            return 1
        print(f"OK: {args.output} matches live schemas "
              f"(version={TOOLS_JSON_VERSION}).")
        return 0

    args.output.write_text(serialized, encoding="utf-8")
    print(f"Wrote {args.output} (version={TOOLS_JSON_VERSION}, "
          f"{len(payload['tools'])} tools, "
          f"{len(payload['error_codes'])} error codes).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
