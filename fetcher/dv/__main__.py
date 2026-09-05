"""Command line for the ДВ acquisition layer.

    python -m fetcher.dv issues    --out data/dv/issues.jsonl [--max-pages N]
                                   [--start-page N] [--resume]
    python -m fetcher.dv materials --issues data/dv/issues.jsonl
                                   --out data/dv/materials.jsonl [--limit N]
                                   [--resume]
    python -m fetcher.dv material  --id-mat M [--cache-dir data/dv/cache]

Everything is written as UTF-8 JSONL, one object per line, in the order
the site serves it, with the keys in a fixed order, so two runs over the
same pages produce byte-identical files.

`--resume` appends to an existing output and skips what is already in
it, which is how a run interrupted anywhere (a network failure, a
пагинация error, Ctrl-C) is continued without re-fetching. Without it,
the output file is rewritten from scratch.

Logging goes to stderr at INFO, one line per HTTP request, so `material`
can be piped: its JSON is the only thing on stdout.
"""

import argparse
import json
import logging
import sys
from dataclasses import asdict
from pathlib import Path

from fetcher.dv.client import DvSession
from fetcher.dv.issues import enumerate_issues
from fetcher.dv.materials import (
    fetch_material,
    is_error_page,
    parse_material_header,
    parse_materials,
)
from fetcher.dv.materials import MATERIALS_URL

log = logging.getLogger("fetcher.dv")


def _write_line(handle, obj: dict) -> None:
    handle.write(json.dumps(obj, ensure_ascii=False) + "\n")
    handle.flush()


def _read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def _done_ids(path: Path, key: str, resume: bool) -> set[int]:
    """Identifiers already written to `path`, when resuming."""
    if not resume:
        return set()
    return {row[key] for row in _read_jsonl(path) if key in row}


def cmd_issues(args, session) -> int:
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    already = _done_ids(out, "id_obj", args.resume)
    if already:
        log.info("resuming: %d issues already in %s", len(already), out)

    written = 0
    with out.open("a" if args.resume else "w", encoding="utf-8") as handle:
        for row in enumerate_issues(
            session, max_pages=args.max_pages, start_page=args.start_page
        ):
            if row.id_obj in already:
                continue
            _write_line(handle, asdict(row))
            already.add(row.id_obj)
            written += 1
    log.info("wrote %d issue rows to %s", written, out)
    return 0


def cmd_materials(args, session) -> int:
    issues_path = Path(args.issues)
    if not issues_path.exists():
        raise SystemExit(f"no issues file at {issues_path}")
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    already = _done_ids(out, "id_obj", args.resume)
    if already:
        log.info("resuming: %d issues already in %s", len(already), out)

    issues = [row for row in _read_jsonl(issues_path) if row["id_obj"] not in already]
    if args.limit is not None:
        issues = issues[: args.limit]

    counts = {"ok": 0, "empty": 0, "error_page": 0}
    with out.open("a" if args.resume else "w", encoding="utf-8") as handle:
        for issue in issues:
            identity = {
                "id_obj": issue["id_obj"],
                "issue_year": issue.get("year"),
                "issue_number": issue.get("number"),
                "issue_date": issue.get("date"),
            }
            html = session.get(MATERIALS_URL, params={"idObj": issue["id_obj"]})
            if is_error_page(html):
                counts["error_page"] += 1
                _write_line(handle, {**identity, "status": "error_page"})
                continue
            rows = parse_materials(html)
            if not rows:
                counts["empty"] += 1
                _write_line(handle, {**identity, "status": "empty"})
                continue
            counts["ok"] += len(rows)
            for row in rows:
                _write_line(
                    handle,
                    {
                        **identity,
                        "status": "ok",
                        "position": row.position,
                        "id_mat": row.id_mat,
                        "section": row.section,
                        "title": row.title,
                        "start_page": row.start_page,
                    },
                )
    log.info(
        "wrote %d materials, %d empty issues, %d error pages to %s",
        counts["ok"], counts["empty"], counts["error_page"], out,
    )
    return 0


def cmd_material(args, session) -> int:
    cache_dir = Path(args.cache_dir) if args.cache_dir else None
    html = fetch_material(session, args.id_mat, cache_dir=cache_dir)
    if is_error_page(html):
        raise SystemExit(f"material {args.id_mat} is not available")
    header = parse_material_header(html)
    print(
        json.dumps({"id_mat": args.id_mat, **asdict(header)}, ensure_ascii=False)
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m fetcher.dv",
        description="Acquire issue, material and act metadata from Държавен вестник.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    issues = sub.add_parser("issues", help="enumerate the issue list to JSONL")
    issues.add_argument("--out", required=True, help="output JSONL path")
    issues.add_argument("--max-pages", type=int, default=None, help="stop after N pages")
    issues.add_argument(
        "--start-page", type=int, default=1, help="first list page to record"
    )
    issues.add_argument(
        "--resume", action="store_true", help="append, skipping issues already written"
    )
    issues.set_defaults(func=cmd_issues)

    materials = sub.add_parser("materials", help="enumerate the materials of each issue")
    materials.add_argument("--issues", required=True, help="issues JSONL from `issues`")
    materials.add_argument("--out", required=True, help="output JSONL path")
    materials.add_argument("--limit", type=int, default=None, help="stop after N issues")
    materials.add_argument(
        "--resume", action="store_true", help="append, skipping issues already written"
    )
    materials.set_defaults(func=cmd_materials)

    material = sub.add_parser("material", help="fetch one material and print its header")
    material.add_argument("--id-mat", type=int, required=True, help="idMat of the material")
    material.add_argument("--cache-dir", default=None, help="raw HTML cache directory")
    material.set_defaults(func=cmd_material)

    return parser


def main(argv=None, *, session=None) -> int:
    """Run one subcommand. `session` is the seam the tests use."""
    args = build_parser().parse_args(argv)
    logging.basicConfig(
        level=logging.INFO,
        stream=sys.stderr,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    owned = session is None
    session = session or DvSession()
    try:
        return args.func(args, session)
    finally:
        if owned:
            session.close()


if __name__ == "__main__":  # pragma: no cover - exercised by the CLI itself
    raise SystemExit(main())
