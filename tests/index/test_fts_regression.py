"""bg_search_regression.yaml runner.

Loads each curated case and verifies that the live catalog.db (built
from `main`) produces hits matching the case's must_include /
must_exclude / must_include_substring constraints. Skipped if
catalog.db is missing.
"""

import pathlib
import sqlite3

import pytest
import yaml

from mcp_server.queries import full_text_search

REPO = pathlib.Path(__file__).resolve().parent.parent.parent
DB = REPO / "catalog.db"
CASES_FILE = REPO / "tests/fixtures/queries/bg_search_regression.yaml"


def _load_cases() -> list[dict]:
    return yaml.safe_load(CASES_FILE.read_text(encoding="utf-8"))["cases"]


@pytest.fixture(scope="module")
def conn():
    if not DB.exists():
        pytest.skip(
            f"catalog.db missing at {DB}; run `python -m index.build` first."
        )
    c = sqlite3.connect(str(DB), check_same_thread=False)
    c.row_factory = sqlite3.Row
    return c


@pytest.mark.parametrize(
    "case", _load_cases(), ids=lambda c: c["query"][:30]
)
def test_search_regression(conn, case):
    """Run the curated case against the live catalog and verify
    must_include/exclude/substring rules."""
    hits = full_text_search(conn, case["query"], limit=20)
    hit_ids = [h["law_id"] for h in hits]

    for needed in case.get("must_include", []):
        assert needed in hit_ids, (
            f"{case['query']!r} should include {needed!r}; "
            f"top-5 was {hit_ids[:5]}"
        )

    for forbidden in case.get("must_exclude", []):
        assert forbidden not in hit_ids, (
            f"{case['query']!r} unexpectedly returned forbidden {forbidden!r}"
        )

    if "must_include_substring" in case:
        sub = case["must_include_substring"]
        assert any(sub in h_id for h_id in hit_ids), (
            f"{case['query']!r} should produce a hit whose law_id contains "
            f"{sub!r}; got {hit_ids[:5]}"
        )
