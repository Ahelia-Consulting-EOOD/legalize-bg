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
from datetime import datetime
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


def _run_root(out: str) -> Path:
    root = (ROOT / out).resolve() if not Path(out).is_absolute() else Path(out).resolve()
    for cat in CATEGORIES:
        if root == (ROOT / cat).resolve() or (ROOT / cat).resolve() in root.parents:
            raise SystemExit(f"refusing to write under the corpus folder {cat}/")
    return root


def _slug(slug: str) -> str:
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", slug):
        raise SystemExit(f"not a corpus slug: {slug!r}")
    return slug


def cmd_prepare(args) -> int:
    run_dir = _run_root(args.out) / _slug(args.slug)
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
        if int(old_report.stem.rsplit("round", 1)[1]) > rnd:
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
            targets = [task["target"]] if task.get("target") is not None else [b["i"] for b in task["blocks"]]
            answers.append((task, [{"i": i, "label": "unknown", "note": f"unparsable answer: {exc}"} for i in targets]))
            continue
        answers.append((task, entries))
    return answers, missing


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
