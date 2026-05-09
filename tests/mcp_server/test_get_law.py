"""Tests for the `get_law` MCP tool, exercised via the build_app
test-shortcut. End-to-end FastMCP transport tests live in test_tools_e2e."""

import pytest

from mcp_server.errors import ToolError
from mcp_server.server import build_app


@pytest.fixture
def app(populated_conn, tmp_path):
    """Build a FastMCP app bound to populated_conn + a tmp corpus root
    holding a single fake law file matching `zakon-a` in the catalog.

    The frontmatter mirrors what `index.build` would write: 8 mandatory
    SPEC fields + 5 Bulgarian extensions + amendment_history.
    """
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
        "dv_issue: '1'\n"
        "dv_year: 2020\n"
        "effective_date: '2020-01-01'\n"
        "category: laws\n"
        "eli: /eli/bg/закон/2020/1/1/zakon-a/con\n"
        "amendment_history: []\n"
        "---\n\n# ЗАКОН ЗА А\n\nТекст.\n",
        encoding="utf-8",
    )
    # The build records current_commit; the test fixture uses a fake commit
    # that matches what populated_conn seeded ('a'*40). build_app reads
    # this for the working-tree fast path.
    return build_app(conn=populated_conn, corpus_root=tmp_path)


def test_get_law_by_identificador_returns_full_response(app):
    result = app.call_tool_sync("get_law", {"name": "100"})
    assert result["law_id"] == "zakon-a"
    assert result["identificador"] == "100"
    assert result["titulo"] == "Закон за А"
    assert "body_markdown" in result
    assert result["body_markdown"].startswith("# ЗАКОН ЗА А")
    assert result["category"] == "laws"
    assert "warnings" in result and isinstance(result["warnings"], list)


def test_get_law_response_includes_metadata_fields(app):
    """D-024: the response is a typed-dict with all metadata fields,
    not a bare Markdown string."""
    result = app.call_tool_sync("get_law", {"name": "100"})
    for k in ("law_id", "identificador", "titulo", "category",
              "fecha_publicacion", "ultima_actualizacion",
              "dv_issue", "dv_year", "effective_date", "eli",
              "amendment_history", "commit_hash", "body_markdown",
              "warnings"):
        assert k in result, f"missing field {k!r}"


def test_get_law_unknown_raises_LAW_NOT_FOUND(app):
    with pytest.raises(ToolError) as exc:
        app.call_tool_sync("get_law", {"name": "напълно непознат"})
    assert exc.value.code == "LAW_NOT_FOUND"
    assert "name" in exc.value.payload
    assert "suggestions" in exc.value.payload


def test_get_law_ambiguous_raises_AMBIGUOUS_NAME(app):
    with pytest.raises(ToolError) as exc:
        app.call_tool_sync("get_law", {"name": "Наредба № 7 за нещо"})
    assert exc.value.code == "AMBIGUOUS_NAME"
    candidates = exc.value.payload["candidates"]
    assert len(candidates) == 2
    # All candidates carry identificador (D-026 disambiguation contract)
    for c in candidates:
        assert "identificador" in c and c["identificador"]


def test_get_law_emits_DATE_UNCERTAIN_when_flag_set(app):
    """§7.2: DATE_UNCERTAIN warning surfaces from the persisted
    date_uncertain column, not a time-dependent comparison."""
    app._conn.execute(
        "UPDATE law_versions SET date_uncertain = 1 WHERE law_id = 'zakon-a'",
    )
    app._conn.commit()
    result = app.call_tool_sync("get_law", {"name": "100"})
    codes = [w["code"] for w in result["warnings"]]
    assert "DATE_UNCERTAIN" in codes


def test_get_law_no_DATE_UNCERTAIN_by_default(app):
    """Acts with date_uncertain=0 must not emit the warning."""
    result = app.call_tool_sync("get_law", {"name": "100"})
    codes = [w["code"] for w in result["warnings"]]
    assert "DATE_UNCERTAIN" not in codes
