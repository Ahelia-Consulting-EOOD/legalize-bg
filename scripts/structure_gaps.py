#!/usr/bin/env python3
"""Structure-gap scan over the corpus: acts whose additional provisions the source dropped.

Two rules, both derived from a confirmed defect (Закон за обществения транспорт, lex.bg ldoc
2137259781, 2026-09-05: lex.bg renders the heading "Допълнителна разпоредба" with no text and
the final provisions start at § 2, while the State Gazette text, ДВ бр. 32/2026, carries § 1
with twelve definitions):

  additional-empty          a standalone additional-provisions heading is directly followed
                            (blank lines apart) by a transitional or final provisions heading
  paragraph-start-above-1   the lowest bold "**§ N.**" number in the file is above 1

Usage:
  structure_gaps.py [ROOT] [--report PATH] [--json PATH] [--warn] [--self-test]
Exit 1 when a rule fires (0 with --warn). ROOT defaults to the repository root; the scan
covers laws/, codes/, ordinances/, implementing/, regulations/ and postanovleniya/.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

CATEGORIES = ["laws", "codes", "ordinances", "implementing", "regulations", "postanovleniya"]
HEADING_MARK = re.compile(r"^\s*(?:#+\s*|\*\*)?\s*(.*?)\s*(?:\*\*)?\s*$")
ADDITIONAL = re.compile(r"^допълнителн[аи] разпоредб[аи]\.?$", re.I)
FINAL = re.compile(r"^(?:преходни(?: и заключителни)?|заключителни) разпоредб[аи]\.?$", re.I)
PARAGRAPH = re.compile(r"^\*\*§ (\d+)\.\*\*", re.M)


@dataclass
class Finding:
    path: str
    rule: str
    detail: str


def _heading(line: str) -> str:
    m = HEADING_MARK.match(line)
    return m.group(1) if m else line.strip()


def scan_text(text: str, path: str = "") -> list[Finding]:
    out: list[Finding] = []
    lines = text.split("\n")
    for i, line in enumerate(lines):
        if not ADDITIONAL.match(_heading(line)):
            continue
        j = i + 1
        while j < len(lines) and not lines[j].strip():
            j += 1
        if j < len(lines) and FINAL.match(_heading(lines[j])):
            out.append(Finding(path, "additional-empty", f"line {i + 1}: '{line.strip()}' is followed by '{lines[j].strip()}' at line {j + 1}"))
            break
    numbers = [int(n) for n in PARAGRAPH.findall(text)]
    if numbers and min(numbers) > 1:
        out.append(Finding(path, "paragraph-start-above-1", f"lowest § is {min(numbers)}"))
    return out


def scan_file(path: Path) -> list[Finding]:
    return scan_text(path.read_text(encoding="utf-8"), str(path))


def scan_root(root: Path) -> list[Finding]:
    found: list[Finding] = []
    for cat in CATEGORIES:
        for p in sorted((root / cat).glob("*.md")):
            for f in scan_file(p):
                f.path = str(p.relative_to(root))
                found.append(f)
    return found


def self_test() -> bool:
    clean = "**Чл. 1.** Текст.\n\n## Допълнителни разпоредби\n\n**§ 1.** По смисъла на този закон.\n\n## Заключителни разпоредби\n\n**§ 2.** Влиза в сила.\n"
    if scan_text(clean):
        return False
    mutated = clean.replace("**§ 1.** По смисъла на този закон.\n\n", "")
    rules = {f.rule for f in scan_text(mutated)}
    ok = rules == {"additional-empty", "paragraph-start-above-1"}
    for rule in ("additional-empty", "paragraph-start-above-1"):
        print(f"{rule}: {'fires on mutated input' if rule in rules else 'DID NOT FIRE'}")
    return ok


def render(findings: list[Finding]) -> str:
    by_rule: dict[str, list[Finding]] = {}
    for f in findings:
        by_rule.setdefault(f.rule, []).append(f)
    out = ["| file | rule | detail |", "| --- | --- | --- |"]
    for f in findings:
        out.append(f"| `{f.path}` | {f.rule} | {f.detail} |")
    out.append("")
    out.append("Totals: " + ", ".join(f"{r} {len(v)}" for r, v in sorted(by_rule.items())) + f"; files {len({f.path for f in findings})}.")
    return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("root", nargs="?", default=str(Path(__file__).resolve().parents[1]))
    ap.add_argument("--report")
    ap.add_argument("--json")
    ap.add_argument("--warn", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        ok = self_test()
        print("structure-gaps self-test", "passed" if ok else "FAILED")
        return 0 if ok else 1
    findings = scan_root(Path(a.root))
    text = render(findings)
    if a.report:
        Path(a.report).write_text(text + "\n", encoding="utf-8")
    if a.json:
        Path(a.json).write_text(json.dumps([f.__dict__ for f in findings], ensure_ascii=False, indent=1), encoding="utf-8")
    print(text.splitlines()[-1])
    return 0 if (a.warn or not findings) else 1


if __name__ == "__main__":
    sys.exit(main())
