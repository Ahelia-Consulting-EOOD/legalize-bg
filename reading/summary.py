"""Summary table over a structure-map run folder: one row per act, the latest round's figures.

Usage: .venv/bin/python reading/summary.py [data/runs/structure-map-2026-10-22] [--md]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path


def rows(run_root: Path) -> list[dict]:
    out = []
    for act_dir in sorted(p for p in run_root.iterdir() if p.is_dir()):
        reports = sorted(act_dir.glob("report-round*.json"))
        blocks = act_dir / "blocks.json"
        if not blocks.exists():
            continue
        nb = len(json.loads(blocks.read_text(encoding="utf-8"))["blocks"])
        tasks0 = len(list((act_dir / "tasks" / "round0").glob("*.json"))) if (act_dir / "tasks" / "round0").exists() else 0
        if not reports:
            out.append({"act": act_dir.name, "blocks": nb, "sections": tasks0, "round": "-", "state": "prepared, not labelled"})
            continue
        r = json.loads(reports[-1].read_text(encoding="utf-8"))
        kinds = r.get("exception_kinds", {})
        per_round = []
        for rp in reports:
            d = json.loads(rp.read_text(encoding="utf-8"))
            per_round.append(f"r{d['round']}:{len(d.get('exceptions', []))}")
        out.append({
            "act": act_dir.name, "blocks": nb, "sections": tasks0, "round": r["round"],
            "exceptions": " ".join(per_round), "kinds": ", ".join(f"{k} {v}" for k, v in sorted(kinds.items())) or "none",
            "residue": len(r.get("residue", [])) if "residue" in r else "-",
            "source_findings": ", ".join(f"{k} {v}" for k, v in sorted(r.get("source_finding_kinds", {}).items())) or "none",
            "missing_answers": len(r.get("answers_missing", [])), "diff_lines": r.get("diff_lines", "-"),
            "state": "done" if "residue" in r else f"round {r['round']} collected, {r.get('next_round_tasks', 0)} tasks pending",
        })
    return out


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    root = Path(args[0]) if args else Path("data/runs/structure-map-2026-10-22")
    rs = rows(root)
    if "--md" in sys.argv:
        print("| act | blocks | sections | exceptions per round | kinds (latest) | residue | source findings | diff lines | state |")
        print("|---|---|---|---|---|---|---|---|---|")
        for r in rs:
            print(f"| {r['act']} | {r['blocks']} | {r['sections']} | {r.get('exceptions', '-')} | {r.get('kinds', '-')} | {r.get('residue', '-')} | {r.get('source_findings', '-')} | {r.get('diff_lines', '-')} | {r['state']} |")
    else:
        for r in rs:
            print(json.dumps(r, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
