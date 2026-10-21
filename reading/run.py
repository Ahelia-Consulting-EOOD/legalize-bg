"""Run driver for the structure map, step 3 of the plan of 2026-10-21.

``prepare``: read the act's raw page from the raw store, split it, and write
``blocks.json`` and the round-0 task files under
``data/runs/structure-map-<date>/<slug>/tasks/round0/``.

``collect --round R``: read the answers the model wrote under
``maps/round<R>/<task>.json`` (one JSON array each), merge them into
``map.json``, assemble ``staged.md``, run the checks, write ``report.json``
and, while rounds remain, the next round's tasks. The final report lists the
residue for the whole-act read and the diff against the corpus file.

The model calls themselves are made by the session (Claude Code subagents
under the owner's plans), one per task file; this script never calls a model.
"""
from __future__ import annotations

import argparse
import difflib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from reading import ladder  # noqa: E402
from reading.splitter import Block, SplitAct, Section, split_lexbg  # noqa: E402

RAW = ROOT / "data" / "raw" / "lexbg"
CATEGORIES = ("laws", "codes", "ordinances", "regulations", "implementing")


def _corpus_file(slug: str) -> Path | None:
    for cat in CATEGORIES:
        p = ROOT / cat / f"{slug}.md"
        if p.exists():
            return p
    return None


def _doc_id(slug: str) -> str:
    p = _corpus_file(slug)
    if p is None:
        raise SystemExit(f"no corpus file for slug {slug}")
    m = re.search(r"^identificador:\s*'?(-?\d+)'?", p.read_text(encoding="utf-8"), re.M)
    if not m:
        raise SystemExit(f"no identificador in {p}")
    return m.group(1)


def _load_act(run_dir: Path) -> SplitAct:
    d = json.loads((run_dir / "blocks.json").read_text(encoding="utf-8"))
    return SplitAct(blocks=[Block(**b) for b in d["blocks"]], sections=[Section(**s) for s in d["sections"]],
                    dropped_by_splitter=d["dropped_by_splitter"], has_spine=d["has_spine"])


def _write_tasks(run_dir: Path, tasks: list[dict]) -> None:
    for t in tasks:
        d = run_dir / "tasks" / f"round{t['round']}"
        d.mkdir(parents=True, exist_ok=True)
        (d / f"{t['task']:04d}.json").write_text(json.dumps(t, ensure_ascii=False, indent=1), encoding="utf-8")
        (run_dir / "maps" / f"round{t['round']}").mkdir(parents=True, exist_ok=True)


def cmd_prepare(args) -> int:
    run_dir = Path(args.out) / args.slug
    run_dir.mkdir(parents=True, exist_ok=True)
    doc_id = _doc_id(args.slug)
    raw = (RAW / f"{doc_id}.html").read_bytes()
    act = split_lexbg(raw)
    (run_dir / "blocks.json").write_text(json.dumps(act.to_dict(), ensure_ascii=False, indent=1), encoding="utf-8")
    (run_dir / "source.txt").write_text(act.source_text + "\n", encoding="utf-8")
    tasks = ladder.round0_tasks(act)
    _write_tasks(run_dir, tasks)
    print(f"{args.slug}: doc {doc_id}, {len(act.blocks)} blocks, {len(act.sections)} sections, "
          f"dropped by splitter {act.dropped_by_splitter}, spine={act.has_spine}")
    return 0


def cmd_collect(args) -> int:
    run_dir = Path(args.out) / args.slug
    act = _load_act(run_dir)
    rnd = args.round
    smap: dict[int, dict] = {}
    mp = run_dir / "map.json"
    if mp.exists() and rnd > 0:
        smap = {int(k): v for k, v in json.loads(mp.read_text(encoding="utf-8")).items()}
    answers = []
    tdir = run_dir / "tasks" / f"round{rnd}"
    mdir = run_dir / "maps" / f"round{rnd}"
    missing = []
    for tf in sorted(tdir.glob("*.json")):
        task = json.loads(tf.read_text(encoding="utf-8"))
        af = mdir / tf.name
        if not af.exists():
            missing.append(tf.name)
            continue
        text = af.read_text(encoding="utf-8").strip()
        text = re.sub(r"^```(?:json)?|```$", "", text, flags=re.M).strip()
        try:
            entries = json.loads(text)
        except json.JSONDecodeError as exc:
            answers.append((task, [{"i": None, "label": "unknown", "note": f"unparsable answer: {exc}"}]))
            continue
        answers.append((task, entries))
    smap, problems = ladder.merge(smap, answers)
    md, exceptions = ladder.evaluate(act, smap, problems)
    mp.write_text(json.dumps({str(k): v for k, v in sorted(smap.items())}, ensure_ascii=False, indent=1), encoding="utf-8")
    (run_dir / "staged.md").write_text(md, encoding="utf-8")
    report = {"slug": args.slug, "round": rnd, "blocks": len(act.blocks), "sections": len(act.sections),
              "answers_missing": missing, "exceptions": exceptions,
              "exception_kinds": _count(exceptions), "labels": _count_labels(smap)}
    if rnd < ladder.MAX_ROUNDS and exceptions:
        tasks = ladder.next_round_tasks(act, smap, exceptions, rnd + 1)
        _write_tasks(run_dir, tasks)
        report["next_round_tasks"] = len(tasks)
    else:
        report["residue"] = sorted({e["block"] for e in exceptions})
    cf = _corpus_file(args.slug)
    if cf:
        current = cf.read_text(encoding="utf-8").split("---", 2)[-1].lstrip("\n")
        diff = list(difflib.unified_diff(current.splitlines(), md.splitlines(), "corpus", "staged", lineterm="", n=1))
        (run_dir / "diff.txt").write_text("\n".join(diff) + "\n", encoding="utf-8")
        report["diff_lines"] = sum(1 for l in diff if l[:1] in "+-" and not l.startswith(("+++", "---")))
    (run_dir / f"report-round{rnd}.json").write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "exceptions"}, ensure_ascii=False))
    return 0


def _count(ex: list[dict]) -> dict[str, int]:
    c: dict[str, int] = {}
    for e in ex:
        c[e["kind"]] = c.get(e["kind"], 0) + 1
    return c


def _count_labels(smap: dict[int, dict]) -> dict[str, int]:
    c: dict[str, int] = {}
    for e in smap.values():
        c[e["label"]] = c.get(e["label"], 0) + 1
    return c


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("prepare"); p.add_argument("--slug", required=True); p.add_argument("--out", default="data/runs/structure-map-2026-10-22"); p.set_defaults(fn=cmd_prepare)
    c = sub.add_parser("collect"); c.add_argument("--slug", required=True); c.add_argument("--round", type=int, default=0); c.add_argument("--out", default="data/runs/structure-map-2026-10-22"); c.set_defaults(fn=cmd_collect)
    args = ap.parse_args()
    return args.fn(args)


if __name__ == "__main__":
    raise SystemExit(main())
