"""Aggregate runner: run every registered check and hard-fail on any violation.

Design decision 3 of Part II: exit code 1 on any unwaived violation, any stale
waiver or any count drift. There is no report mode, because a gate that records
a violation and permits the write is not a gate (Owner Directive 12).

Exit codes: 0 clean, 1 violations or a rotted waiver, 2 usage error.

`--json` reports the same run as a payload: per check, the violation rows
themselves (`check`, `slug`, `locator`, `detail`), their count, the stale
waivers and the count drifts.

Row shape, one per line, four tab-separated columns, so a waiver list can be
regenerated straight from `--enumerate`:

    tag_remnants<TAB>slug<TAB>line 42<TAB>markup remnant '/span>'
    STALE_WAIVER<TAB>slug<TAB>tag_remnants<TAB>no longer violates; remove it
    COUNT_DRIFT<TAB>slug<TAB>tag_remnants<TAB>expected 41, found 12; ...

The label is always column 1 and the act slug always column 2, so filtering on
the check name cannot pick up a row label as if it were a slug.
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

    try:
        waivers = load_waivers(args.waivers)
    except ValueError as exc:
        parser.error(str(exc))
    unknown = sorted(set(waivers) - {c.name for c in CHECKS})

    acts = list(iter_acts(args.root))
    if not acts:
        # A clean report over nothing is indistinguishable from a clean corpus.
        parser.error(
            f"zero acts loaded under {args.root}: refusing to report a clean run"
        )

    failed, summary = False, {}

    for check in CHECKS:
        if args.check not in ("all", check.name):
            continue
        unwaived, stale, drift = reconcile(
            check.name, check.run(acts), waivers.get(check.name, {})
        )
        summary[check.name] = {
            # The rows, not only how many: a machine consumer that has to
            # re-run the checker to find out which lines failed is reading a
            # number, not a report.
            "violations": [
                {"check": v.check, "slug": v.slug, "locator": v.locator,
                 "detail": v.detail}
                for v in unwaived
            ],
            "violation_count": len(unwaived),
            "stale_waivers": stale,
            "count_drift": [
                {"slug": d.slug, "expected": d.expected, "actual": d.actual}
                for d in drift
            ],
        }
        if unwaived or stale or drift:
            failed = True
        if args.json:
            continue  # nothing but the payload goes to stdout in --json mode
        if args.enumerate:
            for v in unwaived:
                print(f"{v.check}\t{v.slug}\t{v.locator}\t{v.detail}")
        for slug in stale:
            print(
                f"STALE_WAIVER\t{slug}\t{check.name}\t"
                "no longer violates; remove from waivers"
            )
        for d in drift:
            print(
                f"COUNT_DRIFT\t{d.slug}\t{check.name}\t"
                f"expected {d.expected} violations, found {d.actual}; "
                "update the waiver count"
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
                f"{name}: {counts['violation_count']} violations, "
                f"{len(counts['stale_waivers'])} stale waivers, "
                f"{len(counts['count_drift'])} count drifts"
            )
        # Waiver entries seeded ahead of their detector are inert, not stale:
        # reconciliation cannot reach them, so they are reported separately.
        for name in unknown:
            print(f"{name}: waived without a detector; entry is inert")

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
