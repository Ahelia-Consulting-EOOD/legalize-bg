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
    before = calls.task_set_id(list((run_dir / "tasks" / "round0").glob("*.json"))) if (run_dir / "tasks" / "round0").exists() else None
    if before is not None:
        for f in (run_dir / "tasks" / "round0").glob("*.json"):
            f.unlink()
    _write_tasks(run_dir, tasks)
    after = calls.task_set_id(list((run_dir / "tasks" / "round0").glob("*.json")))
    if before is not None and before != after:
        _set_aside_round(run_dir, 0, "prepare changed the round-0 task set")
        _set_aside_from(run_dir, 1, "prepare changed the round-0 task set", drop_tasks=True)
        for f in list(run_dir.glob("report-round*.json")) + [run_dir / "map.json", run_dir / "staged.md", run_dir / "diff.txt"]:
            if f.exists():
                f.unlink()
        print("round-0 task set changed: every round's answers set aside, later rounds' tasks and the reports removed", file=sys.stderr)
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
    earlier = [_answers(run_dir, r)[0] for r in range(rnd)]
    for a in earlier:
        smap, _ = ladder.merge(smap, a)
    answers, missing = _answers(run_dir, rnd)
    call_defects = _call_defects(run_dir, rnd)
    smap, problems = ladder.merge(smap, answers)
    md, exceptions = ladder.evaluate(act, smap, problems)
    mp.write_text(json.dumps({str(k): v for k, v in sorted(smap.items())}, ensure_ascii=False, indent=1), encoding="utf-8")
    (run_dir / "staged.md").write_text(md, encoding="utf-8")
    source_findings = [e for e in exceptions if e["kind"] in ladder.SOURCE_FINDINGS]
    label_exceptions = [e for e in exceptions if e["kind"] not in ladder.SOURCE_FINDINGS]
    report = {"slug": args.slug, "round": rnd, "blocks": len(act.blocks), "sections": len(act.sections),
              "answers_missing": missing, "call_defects": call_defects, "exceptions": label_exceptions, "source_findings": source_findings,
              "exception_kinds": _count(label_exceptions), "source_finding_kinds": _count(source_findings),
              "labels": _count_labels(smap),
              "dropped": [{"block": i, "text": act.blocks[i].text[:80], "note": smap.get(i, {}).get("note", "")}
                          for i in range(len(act.blocks)) if smap.get(i, {}).get("label") == "drop"]}
    tasks = ladder.next_round_tasks(act, smap, label_exceptions, rnd + 1) if rnd < ladder.MAX_ROUNDS else []
    # resumable: the next round's tasks are rewritten from scratch, and answers to an earlier task set are set aside
    report_note = _set_aside_from(run_dir, rnd + 1, "an earlier task set was replaced", drop_tasks=True)
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
        # each round's answers alone, so the residue is sorted by whether the labeller held its reading
        per_round = [ladder.merge({}, a) for a in earlier + [answers]]
        report["residue_detail"] = ladder.classify_residue(report["residue"], per_round, label_exceptions)
        report["residue_classes"] = _count([{"kind": d["class"]} for d in report["residue_detail"]])
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
            # a per-task file the model wrote directly (the pre-D-070 path) that does not parse: an exception on its blocks
            targets = [task["target"]] if task.get("target") is not None else [b["i"] for b in task["blocks"]]
            answers.append((task, [{"i": i, "label": "unknown", "note": str(got)} for i in targets]))
            continue
        answers.append((task, got))
    return answers, missing


def _split_call_answers(run_dir: Path, rnd: int) -> list[dict]:
    """Split every call answer file ``maps/round<R>/<set>-NNNN-MMMM.json`` into one ``<task>.json`` per task it answers.

    The call's name carries the id of the task set it was dispatched from; an answer whose set is not the round's
    current set (the round was re-collected since) is set aside unread as ``.stale-*``. Only a task whose answer is
    a list gets its own file; a task the call answered badly (an unparsable file, a missing key, a bare array for
    several tasks) gets none, stays unanswered and is listed by ``dispatch`` again. A sidecar
    ``<call>.split.json`` records the answer file's size and modification time, the tasks it produced and the
    defects it had, so a rewritten answer file (a retry) is split again, replaces the per-task files its earlier
    version produced where the retry has a valid entry, keeps them where it has none, and never touches a per-task
    file another call produced. ``collect`` reports the defects of every sidecar of the round.
    """
    mdir = run_dir / "maps" / f"round{rnd}"
    tdir = run_dir / "tasks" / f"round{rnd}"
    current_set = calls.task_set_id(list(tdir.glob("*.json"))) if tdir.exists() else None
    defects: list[dict] = []
    for af in sorted(mdir.glob("*-*-*.json")):
        m = calls.CALL_NAME.fullmatch(af.stem)
        if not m:
            continue
        if current_set and m.group(1) != current_set:
            stale = af.with_name(f"{af.stem}.stale-{datetime.now().strftime('%H%M%S%f')}.json")
            af.rename(stale)
            d = {"call": af.stem, "kind": "stale_task_set", "detail": f"the answer belongs to an earlier task set; set aside as {stale.name}"}
            defects.append(d)
            log = mdir / "set-aside.json"
            entries = json.loads(log.read_text(encoding="utf-8")) if log.exists() else []
            entries.append(d)
            log.write_text(json.dumps(entries, ensure_ascii=False, indent=1), encoding="utf-8")
            continue
        side = mdir / f"{af.stem}.split.json"
        st = af.stat()
        prev = json.loads(side.read_text(encoding="utf-8")) if side.exists() else {}
        if prev.get("size") == st.st_size and prev.get("mtime") == st.st_mtime_ns:
            continue
        cf = run_dir / "calls" / f"round{rnd}" / f"{af.stem}.tsv"
        names = calls.task_names(cf.read_text(encoding="utf-8")) if cf.exists() else [f"{k:04d}" for k in range(int(m.group(2)), int(m.group(3)) + 1)]
        got = calls.decode_answer_file(af.read_text(encoding="utf-8"), names)
        produced: list[str] = list(prev.get("tasks", []))
        mine: list[dict] = []
        for name, entries in got.items():
            tf = mdir / f"{name}.json"
            if not isinstance(entries, list):
                mine.append({"call": af.stem, "task": name, "kind": "bad_call_answer", "detail": str(entries)})
                continue                 # an earlier good answer of this call, if any, is kept
            if tf.exists() and name not in produced:
                continue                 # another call (a re-dispatch of one task) answered it: keep that answer
            tf.write_text(json.dumps(entries, ensure_ascii=False), encoding="utf-8")
            if name not in produced:
                produced.append(name)
        side.write_text(json.dumps({"size": st.st_size, "mtime": st.st_mtime_ns, "tasks": produced, "defects": mine}), encoding="utf-8")
        defects.extend(mine)
    return defects


def _call_defects(run_dir: Path, rnd: int) -> list[dict]:
    """The open defects of the round's calls (for the collect report): a sidecar's defect on a task that has an answer
    file by now (a retry or another call answered it) is resolved and left out; set-asides of stale answers are listed."""
    mdir = run_dir / "maps" / f"round{rnd}"
    out: list[dict] = []
    for side in sorted(mdir.glob("*.split.json")):
        for d in json.loads(side.read_text(encoding="utf-8")).get("defects", []):
            if d.get("task") and (mdir / f"{d['task']}.json").exists():
                continue
            out.append(d)
    log = mdir / "set-aside.json"
    if log.exists():
        out.extend(json.loads(log.read_text(encoding="utf-8")))
    return out


def _in_flight_tasks(run_dir: Path, rnd: int, task_set: str) -> set[str]:
    """Tasks named by a call file of the current set written less than RELIST_AFTER_MIN ago whose answer file is absent."""
    cdir = run_dir / "calls" / f"round{rnd}"
    mdir = run_dir / "maps" / f"round{rnd}"
    out: set[str] = set()
    if not cdir.exists():
        return out
    now = datetime.now().timestamp()
    for cf in cdir.glob(f"{task_set}-*-*.tsv"):
        if (mdir / f"{cf.stem}.json").exists() or now - cf.stat().st_mtime >= 60 * RELIST_AFTER_MIN:
            continue
        out.update(calls.task_names(cf.read_text(encoding="utf-8")))
    return out


def _set_aside_round(run_dir: Path, rnd: int, why: str) -> str:
    """Move a round's maps and calls aside (a task set that was replaced); returns a note for the report."""
    stamp = datetime.now().strftime("%H%M%S%f")
    note = ""
    maps = run_dir / "maps" / f"round{rnd}"
    if maps.exists() and any(maps.iterdir()):
        stale = run_dir / "maps" / f"round{rnd}-stale-{stamp}"
        maps.rename(stale)
        note = f"{why}: answers of round {rnd} moved to {stale.name}"
    cdir = run_dir / "calls" / f"round{rnd}"
    if cdir.exists() and any(cdir.iterdir()):
        cdir.rename(run_dir / "calls" / f"round{rnd}-stale-{stamp}")
    return note


def _rounds_on_disk(run_dir: Path) -> list[int]:
    out = set()
    for kind in ("tasks", "maps", "calls"):
        for d in (run_dir / kind).glob("round[0-9]*"):
            m = re.fullmatch(r"round(\d+)", d.name)
            if m:
                out.add(int(m.group(1)))
    return sorted(out)


def _set_aside_from(run_dir: Path, first: int, why: str, drop_tasks: bool) -> str:
    """Set aside every round from ``first`` upward: maps and calls moved aside, and (when asked) the task files of those
    rounds deleted, so that no later round keeps answers or tasks built on a replaced task set or block list."""
    notes = []
    for r in _rounds_on_disk(run_dir):
        if r < first:
            continue
        n = _set_aside_round(run_dir, r, why)
        if n:
            notes.append(n)
        if drop_tasks:
            for f in (run_dir / "tasks" / f"round{r}").glob("*.json"):
                f.unlink()
    return "; ".join(notes)


PER_CALL = {0: 8}
PER_CALL_LADDER = 25
RELIST_AFTER_MIN = 15      # a call file written less than this many minutes ago with no answer is taken as still running


def cmd_dispatch(args) -> int:
    root = _run_root(args.out)
    rnd = args.round
    per = args.per or PER_CALL.get(rnd, PER_CALL_LADDER)
    printed = 0
    remaining = 0
    listed: list[dict] = []
    for slug in args.slugs:
        run_dir = root / _slug(slug)
        tdir = run_dir / "tasks" / f"round{rnd}"
        mdir = run_dir / "maps" / f"round{rnd}"
        if not tdir.exists():
            continue
        _split_call_answers(run_dir, rnd)
        task_files = sorted(tdir.glob("*.json"))
        task_set = calls.task_set_id(task_files)
        unanswered = [t for t in task_files if not (mdir / t.name).exists()]
        remaining += len(unanswered)
        running = set() if args.relist else _in_flight_tasks(run_dir, rnd, task_set)
        todo = [t for t in unanswered if t.stem not in running]
        if running:
            print(f"# {slug} round{rnd}: {len(running)} tasks in calls written less than {RELIST_AFTER_MIN} minutes ago and not answered, taken as running; --relist lists them again", file=sys.stderr)
        cdir = run_dir / "calls" / f"round{rnd}"
        for k in range(0, len(todo), per):
            group = todo[k:k + per]
            if printed >= args.max:
                break
            tasks = [json.loads(t.read_text(encoding="utf-8")) for t in group]
            name = f"{task_set}-{group[0].stem}-{group[-1].stem}"
            cdir.mkdir(parents=True, exist_ok=True)
            mdir.mkdir(parents=True, exist_ok=True)
            call_file = cdir / f"{name}.tsv"
            call_file.write_text(calls.encode_tasks(tasks, task_set), encoding="utf-8")
            answer_file = mdir / f"{name}.json"
            if answer_file.exists():
                # a retry of a call whose earlier answer was bad or partial: the old answer is set aside so the labeller writes
                # a fresh file; the sidecar stays, so the per-task files that answer produced remain owned by this call
                answer_file.rename(answer_file.with_name(f"{name}.superseded-{datetime.now().strftime('%H%M%S%f')}.json"))
            prompt = calls.DISPATCH_PROMPT.format(call_file=call_file, answer_file=answer_file)
            listed.append({"slug": slug, "round": rnd, "name": name, "tasks": len(tasks), "call_file": str(call_file), "answer_file": str(answer_file), "prompt": prompt})
            if not args.json:
                print(f"{slug} round{rnd} {name} {len(tasks)} tasks\t{call_file}\t{answer_file}")
                if args.prompts:
                    print("  " + prompt)
            printed += 1
    if args.json:
        print(json.dumps(listed, ensure_ascii=False))
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
    d.add_argument("--max", type=int, default=20, help="calls to list"); d.add_argument("--prompts", action="store_true", help="print the labeller prompt under each call")
    d.add_argument("--relist", action="store_true", help="list again the calls listed less than 15 minutes ago and still unanswered"); d.add_argument("--json", action="store_true", help="print the calls as a JSON list (for a workflow script's args)")
    d.add_argument("--out", default="data/runs/structure-map-2026-10-22"); d.set_defaults(fn=cmd_dispatch)
    args = ap.parse_args()
    return args.fn(args)


if __name__ == "__main__":
    raise SystemExit(main())
