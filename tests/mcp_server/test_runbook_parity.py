"""The runbook's tool table drifted to 3 tools while the server grew to
7 (review 2026-07-02 P1) — lock it to the live tool set the same way
tools.json is locked."""

import re
from pathlib import Path

from mcp_server.export_tools import export_tool_schemas

RUNBOOK = Path("docs/runbook/2026-05-09-phase1b1-operator-setup.md")


def test_runbook_tool_table_matches_live_tools():
    live = {t["name"] for t in export_tool_schemas()["tools"]}
    text = RUNBOOK.read_text(encoding="utf-8")
    documented = set(re.findall(r"^\|\s*`(\w+)`", text, flags=re.M))
    assert documented == live, (
        f"runbook tool table out of date: documented={sorted(documented)} "
        f"live={sorted(live)}")
