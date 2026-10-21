"""Run driver for the structure map, step 3 of the plan of 2026-10-21.

``prepare``: read the act's raw page from the raw store, split it, and write
``blocks.json`` and the round-0 task files under
``data/runs/structure-map-<date>/<slug>/tasks/round0/``.

``dispatch --round R``: group the tasks of the round that have no answer yet into
calls (eight sections per call in round 0, twenty-five re-labels per call above it:
decision D-070), write one call file per group under ``calls/round<R>/`` and print one
line per call with the call file, the answer file and the prompt for the labeller. A
run stops when no further call is launched and resumes when ``dispatch`` is run again.

``collect --round R``: read the answers the model wrote under ``maps/round<R>/``
(one JSON object per call, keyed by task number, which is split into one
``<task>.json`` per task; a bare array per task is still accepted), merge them into
``map.json``, assemble ``staged.md``, run the checks, write ``report.json`` and, while
rounds remain, the next round's tasks. The final report lists the residue for the
whole-act read and the diff against the corpus file.

The model calls themselves are made by the session (the ``labeller`` agent under the
owner's plans), one per call file; this script never calls a model.
"""
from __future__ import annotations

import argparse
import difflib
from datetime import datetime
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from reading import calls, ladder  # noqa: E402
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
        (d / f"{t['task']:04d}.json").write_text(json.dumps(t, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
        (run_dir / "maps" / f"round{t['round']}").mkdir(parents=True, exist_ok=True)


def _run_root(out: str) -> Path:
    root = (ROOT / out).resolve() if not Path(out).is_absolute() else Path(out).resolve()
    for cat in CATEGORIES:
        if root == (ROOT / cat).resolve() or (ROOT / cat).resolve() in root.parents:
            raise SystemExit(f"refusing to write under the corpus folder {cat}/")
    return root


def _slug(slug: str) -> str:
    if not re.fullmatch(r"-?[a-z0-9][a-z0-9-]*", slug):
        raise SystemExit(f"not a corpus slug: {slug!r}")
    return slug


def cmd_prepare(args) -> int:
    run_dir = _run_root(args.out) / _slug(args.slug)
    run_dir.mkdir(parents=True, exist_ok=True)
    doc_id = _doc_id(args.slug)
    raw = (RAW / f"{doc_id}.html").read_bytes()
    act = split_lexbg(raw)
    if not act.has_spine:
        raise SystemExit(f"{args.slug}: the page {doc_id} has no act (no spine of Title/Article blocks); it is site chrome only, a source finding for the owner")
    (run_dir / "blocks.json").write_text(json.dumps(act.to_dict(), ensure_ascii=False, indent=1), encoding="utf-8")
    (run_dir / "source.txt").write_text(act.source_text + "\n", encoding="utf-8")
    tasks = ladder.round0_tasks(act)
    _write_tasks(run_dir, tasks)
    print(f"{args.slug}: doc {doc_id}, {len(act.blocks)} blocks, {len(act.sections)} sections, "
          f"dropped by splitter {act.dropped_by_splitter}, spine={act.has_spine}")
    return 0


def cmd_collect(args) -> int:
    run_dir = _run_root(args.out) / _slug(args.slug)
    act = _load_act(run_dir)
    rnd = args.round
    # the map is rebuilt from the answers of rounds 0 to R in order, so re-collecting a round never keeps a later round's labels
    smap: dict[int, dict] = {}
    mp = run_dir / "map.json"
    for r in range(rnd):
        smap, _ = ladder.merge(smap, _answers(run_dir, r)[0])
    answers, missing = _answers(run_dir, rnd)
    smap, problems = ladder.merge(smap, answers)
    md, exceptions = ladder.evaluate(act, smap, problems)
    mp.write_text(json.dumps({str(k): v for k, v in sorted(smap.items())}, ensure_ascii=False, indent=1), encoding="utf-8")
    (run_dir / "staged.md").write_text(md, encoding="utf-8")
    source_findings = [e for e in exceptions if e["kind"] in ladder.SOURCE_FINDINGS]
    label_exceptions = [e for e in exceptions if e["kind"] not in ladder.SOURCE_FINDINGS]
    report = {"slug": args.slug, "round": rnd, "blocks": len(act.blocks), "sections": len(act.sections),
              "answers_missing": missing, "exceptions": label_exceptions, "source_findings": source_findings,
              "exception_kinds": _count(label_exceptions), "source_finding_kinds": _count(source_findings),
              "labels": _count_labels(smap),
              "dropped": [{"block": i, "text": act.blocks[i].text[:80], "note": smap.get(i, {}).get("note", "")}
                          for i in range(len(act.blocks)) if smap.get(i, {}).get("label") == "drop"]}
    tasks = ladder.next_round_tasks(act, smap, label_exceptions, rnd + 1) if rnd < ladder.MAX_ROUNDS else []
    # resumable: the next round's tasks are rewritten from scratch, and answers to an earlier task set are set aside
    nxt_tasks = run_dir / "tasks" / f"round{rnd + 1}"
    nxt_maps = run_dir / "maps" / f"round{rnd + 1}"
    report_note = ""
    if nxt_tasks.exists():
        for f in nxt_tasks.glob("*.json"):
            f.unlink()
    if nxt_maps.exists() and any(nxt_maps.glob("*.json")):
        stale = run_dir / "maps" / f"round{rnd + 1}-stale-{datetime.now().strftime('%H%M%S')}"
        nxt_maps.rename(stale)
        report_note = f"answers of an earlier round {rnd + 1} task set moved to {stale.name}"
    for old_report in run_dir.glob("report-round*.json"):
        m = re.fullmatch(r"report-round(\d+)", old_report.stem)
        if m and int(m.group(1)) > rnd:
            old_report.unlink()
    report["note"] = report_note
    if tasks:
        _write_tasks(run_dir, tasks)
        report["next_round_tasks"] = len(tasks)
    else:
        report["residue"] = sorted({e["block"] for e in label_exceptions if isinstance(e["block"], int) and e["block"] >= 0})
    cf = _corpus_file(args.slug)
    if cf:
        current = cf.read_text(encoding="utf-8").split("---", 2)[-1].lstrip("\n")
        diff = list(difflib.unified_diff(current.splitlines(), md.splitlines(), "corpus", "staged", lineterm="", n=1))
        (run_dir / "diff.txt").write_text("\n".join(diff) + "\n", encoding="utf-8")
        report["diff_lines"] = sum(1 for l in diff if l[:1] in "+-" and not l.startswith(("+++", "---")))
    (run_dir / f"report-round{rnd}.json").write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "exceptions"}, ensure_ascii=False))
    return 0


def _answers(run_dir: Path, rnd: int) -> tuple[list[tuple[dict, list[dict]]], list[str]]:
    """The (task, entries) pairs of a round and the names of the tasks without an answer."""
    answers: list[tuple[dict, list[dict]]] = []
    missing: list[str] = []
    tdir = run_dir / "tasks" / f"round{rnd}"
    mdir = run_dir / "maps" / f"round{rnd}"
    _split_call_answers(run_dir, rnd)
    for tf in sorted(tdir.glob("*.json")):
        task = json.loads(tf.read_text(encoding="utf-8"))
        af = mdir / tf.name
        if not af.exists():
            missing.append(tf.name)
            continue
        got = calls.decode_answer_file(af.read_text(encoding="utf-8"), [tf.stem])[tf.stem]
        if not isinstance(got, list):
            targets = [task["target"]] if task.get("target") is not None else [b["i"] for b in task["blocks"]]
            answers.append((task, [{"i": i, "label": "unknown", "note": str(got)} for i in targets]))
            continue
        answers.append((task, got))
    return answers, missing


def _split_call_answers(run_dir: Path, rnd: int) -> int:
    """Split every call answer file ``maps/round<R>/NNNN-MMMM.json`` into one ``<task>.json`` per task it covers.

    A task's own file is written only when it does not exist yet, so a later per-task answer (a re-dispatch of one
    task) is never overwritten by an older call file. The call file is kept as the record of the call.
    """
    mdir = run_dir / "maps" / f"round{rnd}"
    n = 0
    for af in sorted(mdir.glob("*-*.json")):
        m = re.fullmatch(r"(\d{4})-(\d{4})", af.stem)
        if not m:
            continue
        cf = run_dir / "calls" / f"round{rnd}" / f"{af.stem}.tsv"
        names = calls.task_names(cf.read_text(encoding="utf-8")) if cf.exists() else [f"{k:04d}" for k in range(int(m.group(1)), int(m.group(2)) + 1)]
        got = calls.decode_answer_file(af.read_text(encoding="utf-8"), names)
        for name, entries in got.items():
            tf = mdir / f"{name}.json"
            if tf.exists():
                continue
            tf.write_text(json.dumps(entries if isinstance(entries, list) else {"error": entries}, ensure_ascii=False), encoding="utf-8")
            n += 1
    return n


PER_CALL = {0: 8}
PER_CALL_LADDER = 25


def cmd_dispatch(args) -> int:
    root = _run_root(args.out)
    rnd = args.round
    per = args.per or PER_CALL.get(rnd, PER_CALL_LADDER)
    printed = 0
    remaining = 0
    for slug in args.slugs:
        run_dir = root / _slug(slug)
        tdir = run_dir / "tasks" / f"round{rnd}"
        mdir = run_dir / "maps" / f"round{rnd}"
        if not tdir.exists():
            continue
        _split_call_answers(run_dir, rnd)
        todo = [t for t in sorted(tdir.glob("*.json")) if not (mdir / t.name).exists()]
        remaining += len(todo)
        for k in range(0, len(todo), per):
            group = todo[k:k + per]
            if printed >= args.max:
                continue
            tasks = [json.loads(t.read_text(encoding="utf-8")) for t in group]
            name = f"{group[0].stem}-{group[-1].stem}"
            cdir = run_dir / "calls" / f"round{rnd}"
            cdir.mkdir(parents=True, exist_ok=True)
            mdir.mkdir(parents=True, exist_ok=True)
            call_file = cdir / f"{name}.tsv"
            call_file.write_text(calls.encode_tasks(tasks), encoding="utf-8")
            answer_file = mdir / f"{name}.json"
            print(f"{slug} round{rnd} {name} {len(tasks)} tasks\t{call_file}\t{answer_file}")
            if args.prompts:
                print("  " + calls.DISPATCH_PROMPT.format(call_file=call_file, answer_file=answer_file))
            printed += 1
    print(f"# {printed} calls listed, {remaining} tasks unanswered in round {rnd}", file=sys.stderr)
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
    d = sub.add_parser("dispatch"); d.add_argument("slugs", nargs="+"); d.add_argument("--round", type=int, default=0); d.add_argument("--per", type=int, default=0, help="tasks per call (default 8 in round 0, 25 above)")
    d.add_argument("--max", type=int, default=20, help="calls to list"); d.add_argument("--prompts", action="store_true", help="print the labeller prompt under each call"); d.add_argument("--out", default="data/runs/structure-map-2026-10-22"); d.set_defaults(fn=cmd_dispatch)
    args = ap.parse_args()
    return args.fn(args)


if __name__ == "__main__":
    raise SystemExit(main())
