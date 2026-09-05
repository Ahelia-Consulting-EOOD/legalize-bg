"""Command line for the ДВ acquisition layer.

    python -m fetcher.dv issues    --out data/dv/issues.jsonl [--max-pages N]
                                   [--start-page N] [--resume]
    python -m fetcher.dv materials --issues data/dv/issues.jsonl
                                   --out data/dv/materials.jsonl [--limit N]
                                   [--resume] [--max-consecutive-errors N]
    python -m fetcher.dv material  --id-mat M [--cache-dir data/dv/cache]

Everything is written as UTF-8 JSONL, one object per line, in the order
the site serves it, with the keys in a fixed order, so two runs over the
same pages produce byte-identical files.

`--resume` appends to an existing output and skips the issues already
finished in it, which is how a run interrupted anywhere (a network
failure, a pagination error, Ctrl-C) is continued without re-fetching.
The LAST issue in the output is not trusted, because the interruption may
have landed between two of its lines: its rows are dropped and it is
fetched again, which costs one request. Without `--resume` the output
file is rewritten from scratch.

The materials sweep also refuses to turn a bad afternoon into a
permanent claim about the Gazette. Five „недостъпен“ stubs in a row are
an outage rather than five neighbouring gaps in the sparse id space, so
the run halts, discards that run of stub rows and exits non-zero; and
pages this code cannot read are recorded as `unrecognized` and halt the
run once there are too many of them, so a redesign of the site cannot
write „this issue holds nothing“ 4,146 times.

Logging goes to stderr at INFO, one line per HTTP request, so `material`
can be piped: its JSON is the only thing on stdout.
"""

import argparse
import json
import logging
import sys
from dataclasses import asdict
from pathlib import Path

from fetcher.dv.client import DvSession, is_dv_error_body
from fetcher.dv.issues import enumerate_issues
from fetcher.dv.materials import (
    classify_page,
    fetch_material,
    parse_material_header,
    parse_materials,
)
from fetcher.dv.materials import MATERIALS_URL, fetch_materials_page

#: Consecutive „недостъпен“ stubs that mean the site is down rather than
#: the id space being sparse. Five neighbouring real gaps would be needed
#: to trip it by accident.
DEFAULT_MAX_CONSECUTIVE_ERRORS = 5

#: How many unreadable pages are tolerated. Both clauses guard the same
#: thing from opposite ends: a redesign shows up immediately as a burst,
#: and a slower drift shows up as a share of the whole run.
UNRECOGNIZED_EARLY_WINDOW = 50
UNRECOGNIZED_EARLY_LIMIT = 10
UNRECOGNIZED_RATIO = 0.05

log = logging.getLogger("fetcher.dv")


def _write_line(handle, obj: dict) -> None:
    handle.write(json.dumps(obj, ensure_ascii=False) + "\n")
    handle.flush()


def _read_jsonl(path: Path) -> list[dict]:
    """Read a JSONL file, tolerating a final line cut in half.

    A run killed between the write and the flush leaves a partial object
    on the last line. That is the signature of the interruption this file
    exists to survive, so it is dropped with a warning; a malformed line
    anywhere else is corruption and raises.
    """
    if not path.exists():
        return []
    lines = [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    rows = []
    for number, line in enumerate(lines, start=1):
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            if number == len(lines):
                log.warning(
                    "%s line %d is a half-written object; dropping it", path, number
                )
                break
            raise SystemExit(f"{path} line {number} is not JSON")
    return rows


def _finished_ids(path: Path, resume: bool) -> set[int]:
    """The `id_obj` values already read from the site, when resuming.

    Two kinds of row are not finished and are dropped from the file so
    that the sweep asks for them again:

    The LAST issue in the file. The materials sweep writes one line per
    material, so an interruption between two lines of the same issue
    leaves it looking complete while most of its rows are missing;
    trusting it loses those materials silently and for good. One issue
    re-fetched per resume is one request.

    Every issue recorded as `unrecognized`, which means „this parser
    could not read the page“. Resuming after the parser is fixed must
    come back to exactly those issues, not skip them as done.

    Rows are removed wherever in the file they sit, so the rewrite also
    de-duplicates the issue that is about to be fetched again.
    """
    if not resume:
        return set()
    rows = _read_jsonl(path)
    if not rows:
        return set()
    retry = {row.get("id_obj") for row in rows if row.get("status") == "unrecognized"}
    retry.add(rows[-1].get("id_obj"))
    kept = [row for row in rows if row.get("id_obj") not in retry]
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in kept),
        encoding="utf-8",
    )
    log.info(
        "resuming: re-fetching %d issue(s) that were unread or half written: %s",
        len(retry),
        ", ".join(str(i) for i in sorted(retry, key=lambda v: (v is None, v))),
    )
    return {row["id_obj"] for row in kept if "id_obj" in row}


def _too_many_unrecognized(unrecognized: int, processed: int) -> bool:
    """Whether unreadable pages have stopped being an anomaly."""
    if processed <= UNRECOGNIZED_EARLY_WINDOW:
        return unrecognized > UNRECOGNIZED_EARLY_LIMIT
    return unrecognized / processed > UNRECOGNIZED_RATIO


def cmd_issues(args, session) -> int:
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    already = _finished_ids(out, args.resume)
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


def _read_issues_file(path: Path) -> list[dict]:
    """The issue rows to sweep. `id_obj` is required; the rest describes.

    One strictness, stated once: without `id_obj` there is nothing to
    fetch, so a row that lacks it stops the run naming its line, while
    the descriptive fields are copied through as whatever they are,
    including absent.
    """
    rows = _read_jsonl(path)
    for number, row in enumerate(rows, start=1):
        if "id_obj" not in row:
            raise SystemExit(f"{path} line {number} has no id_obj")
    return rows


def cmd_materials(args, session) -> int:
    issues_path = Path(args.issues)
    if not issues_path.exists():
        raise SystemExit(f"no issues file at {issues_path}")
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    already = _finished_ids(out, args.resume)
    if already:
        log.info("resuming: %d issues already in %s", len(already), out)

    issues = [row for row in _read_issues_file(issues_path) if row["id_obj"] not in already]
    if args.limit is not None:
        issues = issues[: args.limit]

    counts = {"ok": 0, "empty": 0, "error_page": 0, "unrecognized": 0}
    processed = 0
    consecutive_errors = 0
    last_good: int | None = None
    halt: str | None = None
    # Stub rows wait here until a readable page proves the site was up.
    # A run of them that ends in a halt is discarded rather than written,
    # because „no such issue“ is exactly what those rows would claim.
    pending_errors: list[dict] = []
    # The last non-empty set of idMat values written. Two different issues
    # never share a material, so a repeat means the server ignored idObj
    # (session-bound issue selection, found 2026-09-05) and every further
    # row would be a copy of the wrong issue.
    prev_ids: frozenset[int] = frozenset()

    with out.open("a" if args.resume else "w", encoding="utf-8") as handle:
        for issue in issues:
            id_obj = issue["id_obj"]
            identity = {
                "id_obj": id_obj,
                "issue_year": issue.get("year"),
                "issue_number": issue.get("number"),
                "issue_date": issue.get("date"),
            }
            html = fetch_materials_page(session, id_obj)
            status = classify_page(html)
            processed += 1

            if status == "error_page":
                pending_errors.append({**identity, "status": "error_page"})
                consecutive_errors += 1
                if consecutive_errors >= args.max_consecutive_errors:
                    halt = (
                        f"{consecutive_errors} consecutive error views, ending at "
                        f"id_obj {id_obj}: the site is down, not the id space "
                        f"exhausted. Last issue that answered: "
                        f"{last_good if last_good is not None else 'none in this run'}. "
                        f"Those {consecutive_errors} rows were discarded rather than "
                        f"recorded as gaps; re-run with --resume when the site is back."
                    )
                    pending_errors.clear()
                    break
                continue

            if status == "unrecognized":
                # Not a claim about the Gazette: a claim about this code.
                counts["unrecognized"] += 1
                _write_line(handle, {**identity, "status": "unrecognized"})
                if _too_many_unrecognized(counts["unrecognized"], processed):
                    halt = (
                        f"{counts['unrecognized']} of {processed} pages could not be "
                        f"read, the last at id_obj {id_obj}: the site's markup has "
                        f"changed and this parser is measuring nothing. Fix the "
                        f"parser before re-running; --resume keeps what was read."
                    )
                    break
                continue

            # A readable answer: the site is up, so the gaps behind us are
            # real gaps and can be committed.
            for row in pending_errors:
                _write_line(handle, row)
            counts["error_page"] += len(pending_errors)
            pending_errors.clear()
            consecutive_errors = 0
            last_good = id_obj

            if status == "empty":
                counts["empty"] += 1
                _write_line(handle, {**identity, "status": "empty"})
                continue

            rows = parse_materials(html)
            ids = frozenset(row.id_mat for row in rows)
            if ids and ids == prev_ids:
                halt = (
                    f"id_obj {id_obj} returned the same materials as the previous "
                    f"non-empty issue ({len(ids)} idMat values). Two issues never share "
                    f"a material: the server is serving a session-bound issue and "
                    f"ignoring idObj. Nothing from this issue was written; fix the "
                    f"client (fresh session per request) and re-run with --resume."
                )
                break
            prev_ids = ids
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

        for row in pending_errors:
            _write_line(handle, row)
        counts["error_page"] += len(pending_errors)

    log.info(
        "wrote %d materials, %d empty issues, %d error pages, "
        "%d unreadable pages to %s",
        counts["ok"], counts["empty"], counts["error_page"],
        counts["unrecognized"], out,
    )
    if halt is not None:
        log.error("stopped: %s", halt)
        return 1
    return 0


def cmd_material(args, session) -> int:
    cache_dir = Path(args.cache_dir) if args.cache_dir else None
    html = fetch_material(session, args.id_mat, cache_dir=cache_dir)
    if is_dv_error_body(html):
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
    materials.add_argument(
        "--max-consecutive-errors",
        type=int,
        default=DEFAULT_MAX_CONSECUTIVE_ERRORS,
        help="halt after this many „недостъпен“ stubs in a row (an outage)",
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
