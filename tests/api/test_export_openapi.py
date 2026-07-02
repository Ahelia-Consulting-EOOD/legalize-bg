"""Lock docs/api/openapi-rest.json to the live app schema, exactly like
tools.json is locked to the MCP tool schemas."""

import subprocess
import sys
from pathlib import Path

EXPECTED_PATHS = {
    "/healthz", "/api/v1/laws", "/api/v1/laws/{slug}",
    "/api/v1/laws/{slug}/articles/{art}", "/api/v1/laws/{slug}/history",
    "/api/v1/laws/{slug}/diff", "/api/v1/search", "/api/v1/stats",
    "/api/v1/metrics",
}


def test_openapi_export_covers_all_endpoints():
    from api.export_openapi import generate_spec
    spec = generate_spec()
    assert set(spec["paths"].keys()) == EXPECTED_PATHS
    assert spec["info"]["version"] == "1.0.0"


def test_committed_spec_matches_live():
    assert Path("docs/api/openapi-rest.json").exists(), (
        "run: .venv/bin/python -m api.export_openapi "
        "--output docs/api/openapi-rest.json")
    rc = subprocess.run(
        [sys.executable, "-m", "api.export_openapi",
         "--check", "docs/api/openapi-rest.json"]).returncode
    assert rc == 0
