"""Sections per call against reliability, from the calls table and the run data (read-only).

Joins ``calls.csv`` (one row per subagent call) to the run folder: each task of a round-0 call is one
section; its blocks come from ``tasks/round0/NNNN.json`` and its exceptions from ``report-round0.json``
(label exceptions on its blocks, source findings excluded). A task is attributed to the last call that
listed it. Prints Markdown tables: tokens per call, per section and per block by agent and density;
exception rate (exceptions per 100 blocks) by position within the call; and writes ``tasks.csv``.

Usage: python3 density.py CALLS.csv RUN_ROOT OUT_DIR
"""
import csv, json, sys, collections, statistics as st
from pathlib import Path

SOURCE_FINDINGS = {"empty_section", "fragment", "article_gap", "sign_gap", "malformed_head"}


def main():
    calls_csv, run_root, out_dir = sys.argv[1], Path(sys.argv[2]), Path(sys.argv[3])
    calls = list(csv.DictReader(open(calls_csv, encoding="utf-8")))
    calls.sort(key=lambda r: r["ts"] or "9")
    # last call per (slug, round, task)
    owner = {}
    for ci, c in enumerate(calls):
        for pos, t in enumerate(c["tasks"].split()):
            owner[(c["slug"], int(c["round"]), t)] = (ci, pos)
    # exceptions per block from the round-0 reports
    exc_blocks = {}
    reports = {}
    for slug in {c["slug"] for c in calls}:
        rp = run_root / slug / "report-round0.json"
        if not rp.exists():
            continue
        rep = json.loads(rp.read_text(encoding="utf-8"))
        reports[slug] = rep
        cnt = collections.Counter()
        kinds = collections.defaultdict(collections.Counter)
        for e in rep["exceptions"]:
            if e["kind"] in SOURCE_FINDINGS or not isinstance(e["block"], int) or e["block"] < 0:
                continue
            cnt[e["block"]] += 1
            kinds[e["block"]][e["kind"]] += 1
        exc_blocks[slug] = (cnt, kinds)
    rows = []
    for (slug, rnd, t), (ci, pos) in owner.items():
        if rnd != 0 or slug not in reports:
            continue
        tf = run_root / slug / "tasks" / "round0" / f"{t}.json"
        if not tf.exists():
            continue
        task = json.loads(tf.read_text(encoding="utf-8"))
        blocks = [b["i"] for b in task["blocks"]]
        chars = sum(len(b["text"]) for b in task["blocks"])
        cnt, kinds = exc_blocks[slug]
        ex = sum(cnt[i] for i in blocks)
        kind = collections.Counter()
        for i in blocks:
            kind.update(kinds[i])
        c = calls[ci]
        rows.append({"session": c["session"], "agent": c["agent"], "model": c["model"], "slug": slug, "task": t,
                     "n_tasks": int(c["n_tasks"]), "position": pos + 1, "blocks": len(blocks), "chars": chars,
                     "exceptions": ex, "low_confidence": kind.get("low_confidence", 0),
                     "answer_defects": sum(v for k, v in kind.items() if k in ("missing_entry", "bad_number", "bad_label", "bad_index", "duplicate_entry", "bad_answer", "unknown")),
                     "check_failures": sum(v for k, v in kind.items() if k not in ("low_confidence", "missing_entry", "bad_number", "bad_label", "bad_index", "duplicate_entry", "bad_answer", "unknown")),
                     "call_tokens": int(c["tokens"]) if c["tokens"] else None})
    out_dir.mkdir(parents=True, exist_ok=True)
    with open(out_dir / "tasks.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    lines = []
    lines.append("## Round 0: tokens per call, per section and per block, by agent and sections per call\n")
    lines.append("| Agent | Sections per call | Calls | Sections | Blocks | Median tokens per call | Tokens per section | Tokens per block | Exceptions per 100 blocks | Low confidence per 100 | Answer defects per 100 | Check failures per 100 |")
    lines.append("|---|---|---|---|---|---|---|---|---|---|---|---|")
    groups = collections.defaultdict(list)
    for r in rows:
        groups[(r["session"], r["agent"], r["n_tasks"])].append(r)
    for k in sorted(groups, key=lambda k: (k[0], k[2])):
        g = groups[k]
        calls_tok = {}
        for r in g:
            if r["call_tokens"]:
                calls_tok[(r["slug"], r["task"])] = r["call_tokens"]
        percall = collections.defaultdict(set)
        # one token figure per call: group tasks by (slug, call tokens) is ambiguous, so use calls table directly
        ncalls = len({(r["slug"], r["call_tokens"], r["n_tasks"]) for r in g})
        toks = [r["call_tokens"] for r in g if r["call_tokens"]]
        med = int(st.median(toks)) if toks else 0
        blocks = sum(r["blocks"] for r in g); ex = sum(r["exceptions"] for r in g)
        lines.append(f"| {k[1]} ({k[0]}) | {k[2]} | {ncalls} | {len(g)} | {blocks} | {med:,} | {int(med / k[2]):,} | {int(med / (blocks / len(g)) / k[2]) if blocks else 0:,} | {100 * ex / blocks:.1f} | {100 * sum(r['low_confidence'] for r in g) / blocks:.1f} | {100 * sum(r['answer_defects'] for r in g) / blocks:.2f} | {100 * sum(r['check_failures'] for r in g) / blocks:.2f} |")
    lines.append("\nTokens per call is the harness's figure for the whole subagent call (fixed context, instructions, tasks and answers, counted once). Tokens per block divides the median call by the mean blocks per section and the sections per call.\n")
    lines.append("## Round 0: exceptions per 100 blocks by position within the call (calls of 8 sections)\n")
    lines.append("| Agent | Position | Sections | Blocks | Exceptions per 100 blocks | Low confidence per 100 | Answer defects per 100 |")
    lines.append("|---|---|---|---|---|---|---|")
    for agent in sorted({(r["session"], r["agent"]) for r in rows}):
        for pos in range(1, 9):
            g = [r for r in rows if (r["session"], r["agent"]) == agent and r["n_tasks"] == 8 and r["position"] == pos]
            if not g:
                continue
            blocks = sum(r["blocks"] for r in g)
            lines.append(f"| {agent[1]} ({agent[0]}) | {pos} | {len(g)} | {blocks} | {100 * sum(r['exceptions'] for r in g) / blocks:.1f} | {100 * sum(r['low_confidence'] for r in g) / blocks:.1f} | {100 * sum(r['answer_defects'] for r in g) / blocks:.2f} |")
    lines.append("\n## Round 0: exceptions per 100 blocks by position within the call (calls of 3 sections)\n")
    lines.append("| Agent | Position | Sections | Blocks | Exceptions per 100 blocks | Low confidence per 100 | Answer defects per 100 |")
    lines.append("|---|---|---|---|---|---|---|")
    for agent in sorted({(r["session"], r["agent"]) for r in rows}):
        for pos in range(1, 4):
            g = [r for r in rows if (r["session"], r["agent"]) == agent and r["n_tasks"] == 3 and r["position"] == pos]
            if not g:
                continue
            blocks = sum(r["blocks"] for r in g)
            lines.append(f"| {agent[1]} ({agent[0]}) | {pos} | {len(g)} | {blocks} | {100 * sum(r['exceptions'] for r in g) / blocks:.1f} | {100 * sum(r['low_confidence'] for r in g) / blocks:.1f} | {100 * sum(r['answer_defects'] for r in g) / blocks:.2f} |")
    lines.append("\n## Per act: exceptions per 100 blocks by density (round 0)\n")
    lines.append("| Act | Sections per call | Sections | Blocks | Exceptions per 100 blocks |")
    lines.append("|---|---|---|---|---|")
    pa = collections.defaultdict(list)
    for r in rows:
        pa[(r["slug"], r["n_tasks"])].append(r)
    for k in sorted(pa):
        g = pa[k]; blocks = sum(r["blocks"] for r in g)
        lines.append(f"| {k[0][:48]} | {k[1]} | {len(g)} | {blocks} | {100 * sum(r['exceptions'] for r in g) / blocks:.1f} |")
    (out_dir / "density.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    print(f"\n{len(rows)} sections attributed; written to {out_dir}")


if __name__ == "__main__":
    main()
