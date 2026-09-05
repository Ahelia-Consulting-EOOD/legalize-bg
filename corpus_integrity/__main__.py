"""Aggregate runner: run every registered check and hard-fail on any violation.

Design decision 3 of Part II: exit code 1 on any unwaived violation or any
stale waiver. There is no report mode, because a gate that records a violation
and permits the write is not a gate (Owner Directive 12).

Exit codes: 0 clean, 1 violations or stale waivers, 2 usage error.
"""

import argparse
import json
import sys
from pathlib import Path

from corpus_integrity.checks.chrome import ChromeCheck
from corpus_integrity.checks.remnants import RemnantCheck
from corpus_integrity.loader import iter_acts
from corpus_integrity.protocol import Check
from corpus_integrity.waivers import load_waivers, reconcile

CHECKS: list[Check] = [RemnantCheck(), ChromeCheck()]  # later classes append here

DEFAULT_WAIVERS = Path("docs/data/waivers.yaml")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="corpus_integrity")
    parser.add_argument("--root", default=Path("."), type=Path)
    parser.add_argument("--waivers", default=DEFAULT_WAIVERS, type=Path)
    parser.add_argument(
        "--check", default="all", choices=["all", *(c.name for c in CHECKS)]
    )
    parser.add_argument("--enumerate", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    if not args.waivers.is_file():
        parser.error(f"waiver file not found: {args.waivers}")

    waivers = load_waivers(args.waivers)
    unknown = sorted(set(waivers) - {c.name for c in CHECKS})
    acts = list(iter_acts(args.root))
    failed, summary = False, {}

    for check in CHECKS:
        if args.check not in ("all", check.name):
            continue
        unwaived, stale = reconcile(
            check.name, check.run(acts), waivers.get(check.name, set())
        )
        summary[check.name] = {
            "violations": len(unwaived),
            "stale_waivers": len(stale),
        }
        if unwaived or stale:
            failed = True
        if args.enumerate:
            for v in unwaived:
                print(f"{v.check}\t{v.slug}\t{v.locator}\t{v.detail}")
        for slug in stale:
            print(
                f"{check.name}\tSTALE WAIVER\t{slug}\t"
                "no longer violates; remove from waivers"
            )

    if args.json:
        print(
            json.dumps(
                {"acts": len(acts), "checks": summary, "inert_waivers": unknown},
                ensure_ascii=False,
                indent=2,
            )
        )
    else:
        for name, counts in sorted(summary.items()):
            print(
                f"{name}: {counts['violations']} violations, "
                f"{counts['stale_waivers']} stale waivers"
            )
        # Waiver entries seeded ahead of their detector are inert, not stale:
        # reconciliation cannot reach them, so they are reported separately.
        for name in unknown:
            print(f"{name}: waived without a detector; entry is inert")

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
