"""tools.json parity tests — ensures the committed artifact never
drifts from the live FastMCP tool schemas."""

import dataclasses
import json
import pathlib
import subprocess
import sys

import pytest

from mcp_server import schemas
from mcp_server.errors import ERROR_CODES
from mcp_server.export_tools import export_tool_schemas, TOOLS_JSON_VERSION

REPO = pathlib.Path(__file__).resolve().parent.parent.parent
TOOLS_JSON = REPO / "tools.json"


def test_export_tools_returns_seven_tools():
    d = export_tool_schemas()
    names = sorted(t["name"] for t in d["tools"])
    assert names == [
        "amendments_in_period", "diff", "get_article", "get_articles",
        "get_law", "history", "search",
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


def test_core_read_tools_export_field_level_output_schemas():
    """get_law/get_article/get_articles carried
    {"additionalProperties": true} — nothing for UI codegen
    (review 2026-07-02 P1)."""
    from mcp_server.export_tools import export_tool_schemas
    tools = {t["name"]: t for t in export_tool_schemas()["tools"]}
    assert "body_markdown" in tools["get_law"]["output_schema"]["properties"]
    assert "text_hash" in tools["get_article"]["output_schema"]["properties"]
    assert "articles" in tools["get_articles"]["output_schema"]["properties"]


# ── dataclass ↔ TypedDict field parity (final review 2026-07-02) ───────────
#
# schemas.py's TypedDicts (used only as tool return annotations so
# FastMCP can derive field-level output_schema) are meant to mirror
# their dataclass counterparts field-for-field. CI has no catalog.db to
# validate this at runtime (see test_core_read_tools_export_field_level_
# output_schemas' live-catalog dependents), so a drift between a
# dataclass and its TypedDict would only surface as a silently-wrong
# output_schema, not a test failure. This test is the only guard.

_DATACLASS_TYPEDDICT_PAIRS = [
    (schemas.SearchHit, schemas.SearchHitDict),
    (schemas.GetLawResponse, schemas.GetLawResponseDict),
    (schemas.GetArticleResponse, schemas.GetArticleResponseDict),
    (schemas.ArticleEntry, schemas.ArticleEntryDict),
    (schemas.GetArticlesResponse, schemas.GetArticlesResponseDict),
    (schemas.VersionEntry, schemas.VersionEntryDict),
    (schemas.AmendmentEntry, schemas.AmendmentEntryDict),
]


@pytest.mark.parametrize(
    "dataclass_cls,typeddict_cls",
    _DATACLASS_TYPEDDICT_PAIRS,
    ids=[dc.__name__ for dc, _ in _DATACLASS_TYPEDDICT_PAIRS],
)
def test_dataclass_typeddict_field_parity(dataclass_cls, typeddict_cls):
    dataclass_fields = {f.name for f in dataclasses.fields(dataclass_cls)}
    typeddict_fields = set(typeddict_cls.__annotations__)
    assert typeddict_fields == dataclass_fields
