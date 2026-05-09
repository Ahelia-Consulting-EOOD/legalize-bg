"""End-to-end FastMCP integration tests.

Exercises the real JSON-RPC tool-call path via `fastmcp.Client` connected
to the in-memory FastMCP transport (passing the FastMCP instance
directly as the transport). Validates that:
  - tool registration produces a discoverable `tools/list` response
  - tool docstrings render as MCP descriptions (D-021 contract)
  - tool calls flow through serialization correctly
  - ToolError exceptions become structured MCP error envelopes
"""

import asyncio
import pytest

from fastmcp import Client

from mcp_server.server import build_app


def _run(coro):
    """Synchronous wrapper for async FastMCP Client interactions.

    Each call creates+tears-down a fresh event loop. That's fine at
    the current 5-test scale, where loop setup is dwarfed by FastMCP
    init. If 1b.2/1b.3 add many more e2e cases, switch to pytest-anyio
    or pytest-asyncio so loops are reused across tests.
    """
    return asyncio.run(coro)


def test_tools_list_contains_three_phase_1b1_tools(populated_conn, tmp_path):
    """Phase 1b.1 ships exactly three tools — locked here so future
    additions trip a test rather than slipping in silently."""
    app = build_app(conn=populated_conn, corpus_root=tmp_path)

    async def _list():
        async with Client(app.mcp) as c:
            return await c.list_tools()

    tools = _run(_list())
    names = {t.name for t in tools}
    assert names == {"get_law", "search", "get_article"}, \
        f"expected exactly 3 Phase 1b.1 tools; got {names}"


def test_tool_descriptions_are_substantive_docstrings(populated_conn, tmp_path):
    """D-021: FastMCP renders Python docstrings as MCP `tools/list`
    descriptions. The model uses these descriptions to decide which
    tool to call — substantive content matters."""
    app = build_app(conn=populated_conn, corpus_root=tmp_path)

    async def _list():
        async with Client(app.mcp) as c:
            return await c.list_tools()

    tools = _run(_list())
    for t in tools:
        desc = t.description or ""
        assert len(desc) > 100, \
            f"{t.name} description too short ({len(desc)} chars) for MCP"
        # Each tool should document its args and returns
        assert "Args:" in desc, f"{t.name} missing Args: section"
        assert "Returns:" in desc, f"{t.name} missing Returns: section"


def test_search_tool_call_round_trip(populated_conn, tmp_path):
    """End-to-end: client.call_tool serializes args, FastMCP invokes the
    Python function, the dict-list result serializes back. Validates
    that types survive the JSON-RPC round trip."""
    app = build_app(conn=populated_conn, corpus_root=tmp_path)

    async def _call():
        async with Client(app.mcp) as c:
            return await c.call_tool("search", {"query": "Закон"})

    result = _run(_call())
    # FastMCP returns a CallToolResult; the structured payload is in
    # `.data` (serialized) or `.structured_content`.
    payload = result.data if hasattr(result, "data") else result
    assert isinstance(payload, list)
    assert all("law_id" in h and "relevance" in h for h in payload)


def test_get_law_tool_call_round_trip(populated_conn, tmp_path):
    """Verify that `get_law` returns a typed-dict response via real
    JSON-RPC. Smoke test for D-024 (typed-dict responses)."""
    (tmp_path / "laws").mkdir()
    (tmp_path / "laws" / "zakon-a.md").write_text(
        "---\n"
        "titulo: 'Закон за А'\n"
        "identificador: '100'\n"
        "pais: bg\n"
        "rango: закон\n"
        "fecha_publicacion: '2020-01-01'\n"
        "ultima_actualizacion: '2020-01-01'\n"
        "estado: vigente\n"
        "fuente: lex.bg\n"
        "category: laws\n"
        "amendment_history: []\n"
        "---\n\nТекст.\n",
        encoding="utf-8",
    )
    app = build_app(conn=populated_conn, corpus_root=tmp_path)

    async def _call():
        async with Client(app.mcp) as c:
            return await c.call_tool("get_law", {"name": "100"})

    result = _run(_call())
    payload = result.data if hasattr(result, "data") else result
    assert payload["law_id"] == "zakon-a"
    assert payload["body_markdown"]


def test_invalid_article_spec_surfaces_through_mcp(populated_conn, tmp_path):
    """ToolError → MCP error envelope. The structured payload (with
    `examples` for INVALID_ARTICLE_SPEC) must reach the caller, not
    just an opaque transport failure."""
    app = build_app(conn=populated_conn, corpus_root=tmp_path)

    async def _call():
        async with Client(app.mcp) as c:
            return await c.call_tool(
                "get_article", {"law": "100", "article": "garbage"})

    # FastMCP can raise on tool error or return result with isError=True;
    # either signals failure correctly.
    with pytest.raises(Exception) as exc:
        _run(_call())
    # Must include the error code so the model can act on it
    assert "INVALID_ARTICLE_SPEC" in str(exc.value)
