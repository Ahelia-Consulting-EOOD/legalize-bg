"""Parity tests for the error-taxonomy publication. Every code in
`mcp_server.errors.ERROR_CODES` must appear in both
`docs/api/error-codes.md` (as a section heading) and
`docs/api/error-codes.json` (as a `codes[].code` entry). Catches drift
when a new code is added to the runtime registry but not to the
published catalog."""

import json
import pathlib
import re

from mcp_server.errors import ERROR_CODES

REPO = pathlib.Path(__file__).resolve().parent.parent.parent
ERR_MD = REPO / "docs" / "api" / "error-codes.md"
ERR_JSON = REPO / "docs" / "api" / "error-codes.json"


def test_every_runtime_code_has_a_markdown_section():
    """Each ERROR_CODES entry must appear as a `### `code`` heading in
    the catalog (e.g., ### `LAW_NOT_FOUND` or ### `QUERY_TOO_BROAD`)."""
    md = ERR_MD.read_text(encoding="utf-8")
    headings = set(re.findall(r"^### `([A-Z_]+)`", md, flags=re.M))
    runtime = set(ERROR_CODES)
    missing_in_md = runtime - headings
    extra_in_md = headings - runtime
    assert not missing_in_md, (
        f"runtime ERROR_CODES not documented in error-codes.md: "
        f"{sorted(missing_in_md)}"
    )
    assert not extra_in_md, (
        f"error-codes.md mentions codes not in runtime ERROR_CODES: "
        f"{sorted(extra_in_md)}"
    )


def test_every_runtime_code_has_a_json_entry():
    d = json.loads(ERR_JSON.read_text(encoding="utf-8"))
    json_codes = {entry["code"] for entry in d["codes"]}
    runtime = set(ERROR_CODES)
    missing_in_json = runtime - json_codes
    extra_in_json = json_codes - runtime
    assert not missing_in_json, (
        f"runtime ERROR_CODES not in error-codes.json: "
        f"{sorted(missing_in_json)}"
    )
    assert not extra_in_json, (
        f"error-codes.json has codes not in runtime: "
        f"{sorted(extra_in_json)}"
    )


def test_md_and_json_versions_match():
    md = ERR_MD.read_text(encoding="utf-8")
    md_version_match = re.search(r"\*\*Version:\*\*\s*([0-9.]+)", md)
    assert md_version_match, "error-codes.md missing **Version:** marker"
    md_version = md_version_match.group(1)

    j = json.loads(ERR_JSON.read_text(encoding="utf-8"))
    json_version = j["version"]

    from mcp_server.export_tools import TOOLS_JSON_VERSION
    assert md_version == json_version == TOOLS_JSON_VERSION, (
        f"version drift: md={md_version} json={json_version} "
        f"code={TOOLS_JSON_VERSION}"
    )


def test_query_too_broad_marked_since_1b2():
    """Sanity check that the new 1b.2 code is correctly tagged."""
    j = json.loads(ERR_JSON.read_text(encoding="utf-8"))
    qtb = next(c for c in j["codes"] if c["code"] == "QUERY_TOO_BROAD")
    assert qtb["since_phase"] == "1b.2"
    assert qtb["category"] == "error"
    assert "search" in qtb["raised_by"]
