import pytest
from mcp_server.errors import ToolError, ERROR_CODES


def test_all_8_codes_are_defined():
    expected = {
        "LAW_NOT_FOUND", "AMBIGUOUS_NAME", "NO_VERSION_AT_DATE",
        "DATE_UNCERTAIN", "INVALID_ARTICLE_SPEC", "ARTICLE_NOT_FOUND",
        "INDEX_STALE", "INDEX_MISSING",
    }
    assert ERROR_CODES == expected


def test_tool_error_carries_code_and_payload():
    e = ToolError(code="LAW_NOT_FOUND", payload={"name": "ZOP"})
    assert e.code == "LAW_NOT_FOUND"
    assert e.payload == {"name": "ZOP"}


def test_tool_error_unknown_code_raises():
    with pytest.raises(ValueError):
        ToolError(code="MADE_UP_CODE", payload={})


def test_tool_error_str_is_useful():
    e = ToolError(code="LAW_NOT_FOUND", payload={"name": "X"})
    s = str(e)
    assert "LAW_NOT_FOUND" in s
    assert "X" in s


def test_tool_error_to_dict():
    e = ToolError(code="AMBIGUOUS_NAME", payload={"candidates": []})
    assert e.to_dict() == {"code": "AMBIGUOUS_NAME", "candidates": []}
