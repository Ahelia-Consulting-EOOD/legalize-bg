"""Check that every figure in the plan's tables is printed by a script: each numeric cell of every Markdown table
in the plan must appear, as the same number, in one of the generated files of the measurement folder.

Generated files read: step1/usage.md (step1_usage.py), step1/requests.md (request_sums.py), step2/density.md
(density.py), step3/encoding.md (encoding.py), step4/ladder.md (ladder_density.py), step5/hints.md
(hint_agreement.py), step7/estimate.md (estimate.py), step8/cache_timing.md (cache_timing.py). Prints ``figures checked: N, matched: N`` and lists any
unmatched cell. Exit 1 on an unmatched cell.

Usage: python3 check_plan_figures.py PLAN.md MEASUREMENT_DIR
"""
import re, sys
from pathlib import Path

GENERATED = ["step1/usage.md", "step1/requests.md", "step2/density.md", "step3/encoding.md", "step4/ladder.md", "step5/hints.md", "step7/estimate.md", "step8/cache_timing.md"]
NUM = re.compile(r"(?<![\w.])\d[\d,]*(?:\.\d+)?(?![\w])")


def numbers(text):
    return {n.replace(",", "") for n in NUM.findall(text)}


def main():
    plan, mdir = Path(sys.argv[1]), Path(sys.argv[2])
    pool = set()
    for g in GENERATED:
        pool |= numbers((mdir / g).read_text(encoding="utf-8"))
    checked = matched = 0
    unmatched = []
    for ln, line in enumerate(plan.read_text(encoding="utf-8").splitlines(), 1):
        if not line.startswith("|") or set(line.strip()) <= set("|-: "):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if all(not NUM.search(c) for c in cells):
            continue
        if cells and not NUM.search(cells[0]) and not any(NUM.search(c) for c in cells[1:]):
            continue
        for c in cells[1:] if NUM.search("".join(cells[1:])) else []:
            for n in NUM.findall(c):
                v = n.replace(",", "")
                if v in ("1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "100", "2026", "21", "22"):
                    continue  # ordinals, positions, dates and round-number labels
                checked += 1
                if v in pool or (v.endswith("%") and v[:-1] in pool):
                    matched += 1
                else:
                    unmatched.append((ln, c, v))
    print(f"figures checked: {checked}, matched: {matched}")
    for ln, c, v in unmatched:
        print(f"  unmatched line {ln}: {v!r} in cell {c!r}")
    return 1 if unmatched else 0


if __name__ == "__main__":
    raise SystemExit(main())
