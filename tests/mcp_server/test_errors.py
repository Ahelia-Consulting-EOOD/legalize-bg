import pytest
from mcp_server.errors import ToolError, ERROR_CODES


def test_all_codes_are_defined():
    """The error taxonomy is the union of:
      - 8 codes from Phase 1b.1 (D-026)
      - QUERY_TOO_BROAD added in Phase 1b.2 (FR-016)
      - INVALID_DATE_RANGE added in Phase 2
      - DIFF_FAILED added in Phase 2
    See docs/api/error-codes.md for the catalog."""
    expected = {
        "LAW_NOT_FOUND", "AMBIGUOUS_NAME", "NO_VERSION_AT_DATE",
        "DATE_UNCERTAIN", "INVALID_ARTICLE_SPEC", "ARTICLE_NOT_FOUND",
        "INDEX_STALE", "INDEX_MISSING",
        "QUERY_TOO_BROAD",  # Phase 1b.2
        "INVALID_DATE_RANGE",  # Phase 2
        "DIFF_FAILED",  # Phase 2
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


def test_invalid_date_range_is_a_known_code():
    from mcp_server.errors import ERROR_CODES, ToolError
    assert "INVALID_DATE_RANGE" in ERROR_CODES
    err = ToolError("INVALID_DATE_RANGE", {"from_date": "2020-01-01",
                                           "to_date": "2019-01-01"})
    assert err.to_dict()["code"] == "INVALID_DATE_RANGE"
