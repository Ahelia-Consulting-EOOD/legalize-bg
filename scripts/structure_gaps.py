#!/usr/bin/env python3
"""Structure-gap scan over the corpus: acts whose additional provisions the source dropped.

Two rules, both derived from a confirmed defect (Закон за обществения транспорт, lex.bg ldoc
2137259781, 2026-09-05: lex.bg renders the heading "Допълнителна разпоредба" with no text and
the final provisions start at § 2, while the State Gazette text, ДВ бр. 32/2026, carries § 1
with twelve definitions):

  additional-empty          a standalone additional-provisions heading is directly followed
                            (blank lines and amendment-block qualifier lines apart) by a
                            transitional or final provisions heading; reported once per file
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
# Not end-anchored: a consolidated act names the amending act on the heading itself
# ("Заключителни разпоредби КЪМ ЗАКОНА ЗА ИЗМЕНЕНИЕ ..."), and both section names occur in the
# singular ("Преходна разпоредба", "Заключителна разпоредба", "Преходни и заключителна разпоредба").
FINAL = re.compile(r"^(?:преходн[аи](?: и заключителн[аи])?|заключителн[аи]) разпоредб[аи]\b", re.I)
# Lines that belong to the heading below them rather than to the section above: the amending act's
# name and its promulgation note. "КЪМ" is matched case-sensitively because the corpus writes the
# qualifier in capitals, and a lowercase "Към" would be ordinary running text.
QUALIFIER = re.compile(r"^(?:КЪМ\s|(?i:\(\s*обн))")
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
        while j < len(lines) and (not lines[j].strip() or QUALIFIER.match(_heading(lines[j]))):
            j += 1
        if j < len(lines) and FINAL.match(_heading(lines[j])):
            out.append(Finding(path, "additional-empty", f"line {i + 1}: '{line.strip()}' is followed by '{lines[j].strip()}' at line {j + 1}"))
            # One finding per file: the rule reports acts to adjudicate, not every empty section
            # in an act. A second empty section in the same act is not listed separately.
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
        for p in sorted((root / cat).rglob("*.md")):
            for f in scan_file(p):
                f.path = str(p.relative_to(root))
                found.append(f)
    return found


RULES = ("additional-empty", "paragraph-start-above-1")


def self_test() -> bool:
    clean = "**Чл. 1.** Текст.\n\n## Допълнителни разпоредби\n\n**§ 1.** По смисъла на този закон.\n\n## Заключителни разпоредби\n\n**§ 2.** Влиза в сила.\n"
    qualified = clean.replace(
        "## Заключителни разпоредби\n",
        "## Заключителни разпоредби КЪМ ЗАКОНА ЗА ИЗМЕНЕНИЕ И ДОПЪЛНЕНИЕ НА ЕДИН ЗАКОН\n",
    )
    mutated = clean.replace("**§ 1.** По смисъла на този закон.\n\n", "")
    qualifier_form = "Допълнителна разпоредба\n\nКЪМ ЗАКОНА ЗА ИЗМЕНЕНИЕ И ДОПЪЛНЕНИЕ НА ЕДИН ЗАКОН\n\n## Заключителни разпоредби КЪМ ЗАКОНА ЗА ИЗМЕНЕНИЕ И ДОПЪЛНЕНИЕ НА ЕДИН ЗАКОН\n\n**§ 2.** Влиза в сила.\n"
    singular_form = "Допълнителна разпоредба\n\nЗаключителна разпоредба\n\n**§ 2.** Влиза в сила.\n"
    both = set(RULES)
    cases = [
        ("clean act", clean, set()),
        ("clean act, qualified final heading", qualified, set()),
        ("empty additional section", mutated, both),
        ("qualifier line between the headings", qualifier_form, both),
        ("singular section names", singular_form, both),
    ]
    ok = True
    fired: set[str] = set()
    for label, text, expected in cases:
        rules = {f.rule for f in scan_text(text)}
        fired |= rules
        ok = ok and rules == expected
        print(f"{label}: {sorted(rules) if rules else 'no findings'}{'' if rules == expected else ' UNEXPECTED'}")
    for rule in RULES:
        print(f"{rule}: {'fires on mutated input' if rule in fired else 'DID NOT FIRE'}")
    return ok and fired == both


def render(findings: list[Finding]) -> str:
    by_rule: dict[str, list[Finding]] = {}
    for f in findings:
        by_rule.setdefault(f.rule, []).append(f)
    out = ["| file | rule | detail |", "| --- | --- | --- |"]
    for f in findings:
        out.append(f"| `{f.path}` | {f.rule} | {f.detail} |")
    out.append("")
    counts = ", ".join(f"{r} {len(v)}" for r, v in sorted(by_rule.items())) or "no findings"
    out.append(f"Totals: {counts}; files {len({f.path for f in findings})}.")
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
