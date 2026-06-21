"""tools.json parity tests — ensures the committed artifact never
drifts from the live FastMCP tool schemas."""

import json
import pathlib
import subprocess
import sys

import pytest

from mcp_server.errors import ERROR_CODES
from mcp_server.export_tools import export_tool_schemas, TOOLS_JSON_VERSION

REPO = pathlib.Path(__file__).resolve().parent.parent.parent
TOOLS_JSON = REPO / "tools.json"


def test_export_tools_returns_six_tools():
    d = export_tool_schemas()
    names = sorted(t["name"] for t in d["tools"])
    assert names == [
        "amendments_in_period", "diff", "get_article", "get_law", "history", "search",
    ]


def test_export_tools_includes_all_error_codes():
    d = export_tool_schemas()
    assert set(d["error_codes"]) == ERROR_CODES


def test_export_tools_sets_version():
    d = export_tool_schemas()
    assert d["version"] == TOOLS_JSON_VERSION
    # Sanity: a SemVer string with at least one dot.
    assert d["version"].count(".") == 2


def test_committed_tools_json_matches_live_schemas():
    """If this fails, run `python -m mcp_server.export_tools --output
    tools.json` to regenerate and commit. The CI mode of the script is
    exposed as the --check flag for shell-based pre-commit hooks."""
    if not TOOLS_JSON.exists():
        pytest.skip("tools.json not yet committed; run export script.")

    # Run the script in --check mode against the committed file.
    result = subprocess.run(
        [sys.executable, "-m", "mcp_server.export_tools",
         "--check", "--output", str(TOOLS_JSON)],
        capture_output=True,
        text=True,
        cwd=str(REPO),
    )
    assert result.returncode == 0, (
        "tools.json drift detected. stdout: "
        f"{result.stdout!r}\nstderr: {result.stderr!r}"
    )


def test_each_tool_has_input_and_output_schema():
    d = export_tool_schemas()
    for t in d["tools"]:
        assert isinstance(t["input_schema"], dict), t["name"]
        assert "properties" in t["input_schema"], t["name"]
        assert isinstance(t["output_schema"], dict), t["name"]


def test_search_input_schema_documents_query_too_broad_constraint():
    """Don't lock the exact wording, but ensure the description for
    `query` mentions the QUERY_TOO_BROAD constraint so MCP clients can
    surface it without reading the source. (Test passes if the error
    is mentioned anywhere in the search tool's description block.)"""
    d = export_tool_schemas()
    search = next(t for t in d["tools"] if t["name"] == "search")
    blob = json.dumps(search, ensure_ascii=False)
    assert "QUERY_TOO_BROAD" in blob, (
        "search docstring should mention the QUERY_TOO_BROAD reject "
        "for single-word category queries — currently missing."
    )
