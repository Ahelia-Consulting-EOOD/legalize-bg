"""The ladder's calls: tokens per re-labelled block at each density, and whether position within the call matters.

From ``calls.csv`` (rounds 1 and 2, lean agent) fit tokens per call = fixed + per task. From the run data
(read-only) measure the round-1 task files' sizes and whether each round-1 target was still excepted after
round 1 (``report-round1.json``), by position within its call.

Usage: python3 ladder_density.py CALLS.csv RUN_ROOT OUT_DIR
"""
import csv, json, sys, collections, statistics as st
from pathlib import Path

SOURCE_FINDINGS = {"empty_section", "fragment", "article_gap", "sign_gap", "malformed_head"}


def fit(pairs):
    n = len(pairs); sx = sum(x for x, _ in pairs); sy = sum(y for _, y in pairs)
    sxx = sum(x * x for x, _ in pairs); sxy = sum(x * y for x, y in pairs)
    b = (n * sxy - sx * sy) / (n * sxx - sx * sx); a = (sy - b * sx) / n
    return a, b


def main():
    calls_csv, run_root, out_dir = sys.argv[1], Path(sys.argv[2]), Path(sys.argv[3])
    calls = [r for r in csv.DictReader(open(calls_csv, encoding="utf-8")) if r["round"] in ("1", "2") and r["tokens"]]
    lines = ["## Rounds 1 and 2: tokens per call by tasks per call (one task = one target block with its two neighbours)\n",
             "| Agent | Round | Tasks per call | Calls | Median tokens per call | Tokens per task |", "|---|---|---|---|---|---|"]
    g = collections.defaultdict(list)
    for r in calls:
        g[(r["session"], r["agent"], r["round"], int(r["n_tasks"]))].append(int(r["tokens"]))
    for k in sorted(g):
        v = g[k]; med = st.median(v)
        lines.append(f"| {k[1]} ({k[0]}) | {k[2]} | {k[3]} | {len(v)} | {int(med):,} | {int(med / k[3]):,} |")
    for sess, agent in sorted({(r["session"], r["agent"]) for r in calls}):
        pairs = [(int(r["n_tasks"]), int(r["tokens"])) for r in calls if (r["session"], r["agent"]) == (sess, agent)]
        if len({x for x, _ in pairs}) > 1:
            a, b = fit(pairs)
            lines.append(f"\nFit for {agent} ({sess}), rounds 1 and 2, {len(pairs)} calls: tokens per call = {a:,.0f} + {b:,.0f} x tasks. "
                         f"Projected per task: at 10 tasks {int(a / 10 + b):,}; at 20 tasks {int(a / 20 + b):,}; at 30 tasks {int(a / 30 + b):,}; at 40 tasks {int(a / 40 + b):,}.")
    # task sizes and resolution by position
    pos_rows = []
    sizes = []
    owner = {}
    for r in sorted(calls, key=lambda r: r["ts"] or "9"):
        if r["round"] != "1":
            continue
        for pos, t in enumerate(r["tasks"].split()):
            owner[(r["slug"], t)] = (r["session"], r["agent"], int(r["n_tasks"]), pos + 1)
    for (slug, t), (sess, agent, n, pos) in owner.items():
        tf = run_root / slug / "tasks" / "round1" / f"{t}.json"
        rp = run_root / slug / "report-round1.json"
        if not tf.exists() or not rp.exists():
            continue
        task = json.loads(tf.read_text(encoding="utf-8"))
        sizes.append(tf.stat().st_size)
        rep = json.loads(rp.read_text(encoding="utf-8"))
        still = any(e["block"] == task["target"] and e["kind"] not in SOURCE_FINDINGS for e in rep["exceptions"])
        pos_rows.append({"session": sess, "agent": agent, "n_tasks": n, "position": pos, "slug": slug, "task": t, "target": task["target"], "unresolved": int(still)})
    lines.append(f"\nRound-1 task files: {len(sizes)} files, median {int(st.median(sizes)):,} bytes, mean {int(st.mean(sizes)):,} bytes (three blocks, the context headings, the exceptions and the neighbours' labels).\n")
    lines.append("## Round 1: targets still excepted after the round, by position within the call\n")
    lines.append("| Agent | Tasks per call | Position | Targets | Still excepted after round 1 | Share |")
    lines.append("|---|---|---|---|---|---|")
    for key in sorted({(r["session"], r["agent"], r["n_tasks"]) for r in pos_rows}):
        rows_k = [r for r in pos_rows if (r["session"], r["agent"], r["n_tasks"]) == key]
        if len(rows_k) < 20:
            continue
        for pos in range(1, key[2] + 1):
            gg = [r for r in rows_k if r["position"] == pos]
            if gg:
                lines.append(f"| {key[1]} ({key[0]}) | {key[2]} | {pos} | {len(gg)} | {sum(r['unresolved'] for r in gg)} | {100 * sum(r['unresolved'] for r in gg) / len(gg):.0f}% |")
    tot = len(pos_rows); unres = sum(r["unresolved"] for r in pos_rows)
    lines.append(f"\nAll round-1 targets attributed to a call: {tot}; still excepted after round 1: {unres} ({100 * unres / tot:.0f}%).")
    out_dir.mkdir(parents=True, exist_ok=True)
    with open(out_dir / "round1_targets.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(pos_rows[0].keys())); w.writeheader(); w.writerows(pos_rows)
    (out_dir / "ladder.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
