"""List the next groups of unanswered tasks for the run driver, so a labelling run can stop and resume at any time.

Usage: .venv/bin/python reading/groups.py SLUG [SLUG ...] [--per 3] [--max 20] [--round 0] [--out data/runs/structure-map-2026-10-22]

Prints one line per group: ``SLUG round<R> 0000 0001 0002``. A task is unanswered while its answer file
``maps/round<R>/<task>.json`` does not exist, so the listing is the whole state: stopping a run is not
dispatching the next batch, and resuming is running this listing again. Nothing is lost but a section that
was being written when the run stopped, which is listed again.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def groups(run_root: Path, slugs: list[str], per: int, mx: int, rnd: int) -> list[tuple[str, list[str]]]:
    out: list[tuple[str, list[str]]] = []
    for s in slugs:
        tdir = run_root / s / "tasks" / f"round{rnd}"
        mdir = run_root / s / "maps" / f"round{rnd}"
        todo = [t.stem for t in sorted(tdir.glob("*.json")) if not (mdir / t.name).exists()]
        for k in range(0, len(todo), per):
            out.append((s, todo[k:k + per]))
            if len(out) >= mx:
                return out
    return out


def main() -> int:
    args = sys.argv[1:]

    def opt(name: str, default):
        return type(default)(args[args.index(name) + 1]) if name in args else default

    per, mx, rnd, out = opt("--per", 3), opt("--max", 20), opt("--round", 0), opt("--out", "data/runs/structure-map-2026-10-22")
    slugs = [a for i, a in enumerate(args) if not a.startswith("--") and (i == 0 or not args[i - 1].startswith("--"))]
    gs = groups(ROOT / out, slugs, per, mx, rnd)
    for s, ts in gs:
        print(f"{s} round{rnd} {' '.join(ts)}")
    remaining = sum(len(ts) for ts in [g[1] for g in groups(ROOT / out, slugs, per, 10**9, rnd)])
    print(f"# {len(gs)} groups listed, {remaining} tasks unanswered in round {rnd}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
