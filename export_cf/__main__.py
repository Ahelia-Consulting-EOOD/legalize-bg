"""CLI: `python -m export_cf --corpus . --db catalog.db --out ./cf-export/
[--verify]` (spec §Exporter)."""

from __future__ import annotations

import argparse
import logging
import sys
import time
from pathlib import Path

from export_cf.run import run_export
from export_cf.verify import VerifyError, verify_export


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(message)s")
    ap = argparse.ArgumentParser(
        prog="export_cf",
        description="Export catalog.db + corpus to Cloudflare D1/R2 "
                    "artifacts (read-only on all inputs).")
    ap.add_argument("--corpus", type=Path, default=Path("."))
    ap.add_argument("--db", default="catalog.db")
    ap.add_argument("--out", type=Path, default=Path("./cf-export/"))
    ap.add_argument("--verify", action="store_true",
                    help="after exporting, self-check the artifacts "
                         "against catalog.db (row counts, hashes, "
                         "25-act provisions sample)")
    args = ap.parse_args(argv)

    t0 = time.monotonic()
    manifest = run_export(corpus_root=args.corpus, db_path=args.db,
                          out_dir=args.out)
    dt = time.monotonic() - t0
    counts = manifest["counts"]
    print(f"exported {counts['acts_json']} acts, "
          f"{counts['versions_json']} versions, "
          f"{counts['laws_fts']} FTS rows → {args.out} "
          f"in {dt:.1f}s")

    if args.verify:
        t1 = time.monotonic()
        try:
            report = verify_export(db_path=args.db, out_dir=args.out)
        except VerifyError as e:
            print(f"verify: FAILED\n{e}", file=sys.stderr)
            return 1
        print(f"verify: OK ({report['sampled_acts']} acts sampled, "
              f"{report['laws_rows']} laws, "
              f"{report['fts_rows']} FTS rows) "
              f"in {time.monotonic() - t1:.1f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
