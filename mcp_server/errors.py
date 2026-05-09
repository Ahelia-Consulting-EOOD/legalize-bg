"""Tool error taxonomy. Per D-026, errors are first-class structured outputs.

Each ToolError carries a stable `code` (one of ERROR_CODES) and a payload
dict with model-actionable structured data (suggestions, candidates,
available_articles, etc.). FastMCP serializes ToolError into the MCP
response envelope.
"""

ERROR_CODES = frozenset({
    "LAW_NOT_FOUND",
    "AMBIGUOUS_NAME",
    "NO_VERSION_AT_DATE",
    "DATE_UNCERTAIN",     # warning, rides in successful response
    "INVALID_ARTICLE_SPEC",
    "ARTICLE_NOT_FOUND",
    "INDEX_STALE",
    "INDEX_MISSING",
})


class ToolError(Exception):
    """Structured tool failure surfaced through the MCP response envelope."""

    def __init__(self, code: str, payload: dict):
        if code not in ERROR_CODES:
            raise ValueError(f"unknown error code {code!r}; "
                             f"must be one of {sorted(ERROR_CODES)}")
        self.code = code
        self.payload = payload
        super().__init__(f"{code}: {payload}")

    def to_dict(self) -> dict:
        """JSON-serializable form for FastMCP."""
        return {"code": self.code, **self.payload}
