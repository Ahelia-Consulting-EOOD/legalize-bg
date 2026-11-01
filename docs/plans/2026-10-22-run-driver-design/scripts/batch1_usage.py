"""Batch 1 of the audit: what every labeller call cost and how long it took, read from the workflow subagent transcripts.

For each call of the run driver (one call file, one answer file) matched by the call file path in the subagent's first
user message: the number of API requests, the four token classes summed over the requests (uncached input, cache
write split by lifetime, cache read, output), the context counted once (the largest request's context plus every
output), the cost-weighted total relative to one input token (write 1.25, read 0.1, output 5), dollars at Claude
Opus 5.5 list prices, the call's duration and time to first response, the share of the first request read from a warm
cache, and whether a sibling call had finished its first request within the cache lifetime before this call started.
Then the exception rate after round 0 by position in the call, for the sixteen-section calls against the eight-section
ones (the drift measurement of batch-1.md).

Usage: python3 batch1_usage.py WORKFLOWS_DIR RUN_DIR OUT_DIR
  WORKFLOWS_DIR  the session's subagents/workflows folder (wf_*/agent-*.jsonl)
  RUN_DIR        data/runs/structure-map-2026-10-22
  OUT_DIR        where calls.csv, usage.md and drift.md are written
"""
import csv, json, re, sys, statistics as st, collections
from datetime import datetime
from pathlib import Path

PRICE = {"input": 4.0, "write_5m": 5.0, "write_1h": 10.0, "read": 0.40, "output": 20.0}   # dollars per million, Opus 5.5 list, 6 October 2026
W_WRITE, W_READ, W_OUT = 1.25, 0.1, 5.0
TTL_S = 300
CALL = re.compile(r"structure-map-2026-10-22/([^/\s]+)/calls/round(\d)/([0-9a-f]{12}-(\d{4})-(\d{4}))\.tsv")


def ts(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp() if s else None


def read_call(path):
    key = None; t0 = t1 = tend = None; reqs = {}; order = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            j = json.loads(line)
        except Exception:
            continue
        t = j.get("type"); m = j.get("message"); when = ts(j.get("timestamp"))
        if when and t in ("user", "assistant"):
            t0 = t0 or when; tend = when
        if key is None and t == "user" and isinstance(m, dict):
            c = m.get("content"); text = c if isinstance(c, str) else "".join(b.get("text", "") for b in c if isinstance(b, dict)) if isinstance(c, list) else ""
            pm = CALL.search(text)
            if pm:
                key = (pm.group(1), int(pm.group(2)), pm.group(3), int(pm.group(5)) - int(pm.group(4)) + 1)
        if t == "assistant" and isinstance(m, dict) and isinstance(m.get("usage"), dict) and m.get("id"):
            u = m["usage"]; cc = u.get("cache_creation") or {}
            if m["id"] not in reqs:
                order.append(m["id"]); t1 = t1 or when
            r = reqs.setdefault(m["id"], {"input": u.get("input_tokens", 0), "write_5m": cc.get("ephemeral_5m_input_tokens", u.get("cache_creation_input_tokens", 0)),
                                         "write_1h": cc.get("ephemeral_1h_input_tokens", 0), "read": u.get("cache_read_input_tokens", 0), "output": 0,
                                         "thinking": 0, "when": when})
            r["output"] = max(r["output"], u.get("output_tokens", 0))
            r["thinking"] = max(r["thinking"], (u.get("output_tokens_details") or {}).get("thinking_tokens", 0))
    if key is None or not reqs:
        return None
    rows = [reqs[i] for i in order]
    first = rows[0]
    ctx = [r["input"] + r["write_5m"] + r["write_1h"] + r["read"] for r in rows]
    tot = {k: sum(r[k] for r in rows) for k in ("input", "write_5m", "write_1h", "read", "output", "thinking")}
    return {"slug": key[0], "round": key[1], "name": key[2], "tasks": key[3], "requests": len(rows), **tot,
            "counted_once": max(ctx) + tot["output"],
            "weighted": tot["input"] + W_WRITE * (tot["write_5m"] + tot["write_1h"]) + W_READ * tot["read"] + W_OUT * tot["output"],
            "dollars": sum(tot[k] * PRICE[k] for k in PRICE) / 1e6,
            "first_ctx": ctx[0], "first_read": first["read"], "first_read_share": first["read"] / ctx[0] if ctx[0] else 0.0,
            "start": t0, "first_response": t1, "end": tend, "duration": (tend - t0) if t0 and tend else None, "ttfr": (t1 - t0) if t0 and t1 else None}


def median(xs):
    xs = [x for x in xs if x is not None]
    return st.median(xs) if xs else 0


def fmt(x, nd=0):
    return f"{x:,.{nd}f}"


def main(wf_dir, run_dir, out_dir):
    wf_dir, run_dir, out_dir = Path(wf_dir), Path(run_dir), Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    calls = [c for p in sorted(wf_dir.glob("wf_*/agent-*.jsonl")) for c in [read_call(p)] if c]
    calls.sort(key=lambda c: c["start"])
    # warm prefix available: a sibling's first response within TTL before this call's start
    firsts = sorted(c["first_response"] for c in calls if c["first_response"])
    import bisect
    for c in calls:
        i = bisect.bisect_left(firsts, c["start"])
        c["warm_available"] = i > 0 and c["start"] - firsts[i - 1] <= TTL_S
    with (out_dir / "calls.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(calls[0].keys())); w.writeheader(); w.writerows(calls)

    def group(c):
        return (c["round"], 16 if c["round"] == 0 and c["tasks"] > 8 else (8 if c["round"] == 0 else "ladder"))
    groups = collections.OrderedDict()
    for c in calls:
        groups.setdefault(group(c), []).append(c)
    lines = ["## Per call: the four token classes, duration and cache use (medians by round and sections per call)", "",
             "| Round | Sections or tasks per call | Calls | Requests | Duration, s | Time to first response, s | Uncached input | Cache write, 5-minute | Cache write, 1-hour | Cache read | Output (of which thinking) | Context counted once | Cost-weighted | First request read from a warm prefix | Warm prefix available at start | Dollars per call | Cents per section or task |",
             "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for (rnd, per), cs in groups.items():
        tasks = sum(c["tasks"] for c in cs)
        lines.append(f"| {rnd} | {per if per != 'ladder' else median(c['tasks'] for c in cs)} | {len(cs)} | {median(c['requests'] for c in cs):.0f} | {median(c['duration'] for c in cs):.0f} | {median(c['ttfr'] for c in cs):.1f} | "
                     f"{fmt(median(c['input'] for c in cs))} | {fmt(median(c['write_5m'] for c in cs))} | {fmt(median(c['write_1h'] for c in cs))} | {fmt(median(c['read'] for c in cs))} | "
                     f"{fmt(median(c['output'] for c in cs))} ({fmt(median(c['thinking'] for c in cs))}) | {fmt(median(c['counted_once'] for c in cs))} | {fmt(median(c['weighted'] for c in cs))} | "
                     f"{median(c['first_read_share'] for c in cs):.0%} | {sum(c['warm_available'] for c in cs) / len(cs):.0%} of calls | {median(c['dollars'] for c in cs):.3f} | {100 * sum(c['dollars'] for c in cs) / tasks:.2f} |")
    tot = {k: sum(c[k] for c in calls) for k in ("input", "write_5m", "write_1h", "read", "output", "thinking", "counted_once", "weighted", "dollars")}
    sections0 = sum(c["tasks"] for c in calls if c["round"] == 0)
    lines += ["", f"Over all {len(calls)} calls: uncached input {fmt(tot['input'])} tokens ({tot['input'] * PRICE['input'] / 1e6:.2f} dollars), five-minute cache writes {fmt(tot['write_5m'])} ({tot['write_5m'] * PRICE['write_5m'] / 1e6:.2f}), one-hour cache writes {fmt(tot['write_1h'])} ({tot['write_1h'] * PRICE['write_1h'] / 1e6:.2f}), cache reads {fmt(tot['read'])} ({tot['read'] * PRICE['read'] / 1e6:.2f}), output {fmt(tot['output'])} of which thinking {fmt(tot['thinking'])} ({tot['output'] * PRICE['output'] / 1e6:.2f}); {tot['dollars']:.2f} dollars at list price in all. Context counted once {fmt(tot['counted_once'])} tokens; cost-weighted {fmt(tot['weighted'])}.",
              f"Round 0: {sections0} sections in {sum(1 for c in calls if c['round'] == 0)} calls; counted once {fmt(sum(c['counted_once'] for c in calls if c['round'] == 0) / sections0)} tokens per section, cost-weighted {fmt(sum(c['weighted'] for c in calls if c['round'] == 0) / sections0)}, {100 * sum(c['dollars'] for c in calls if c['round'] == 0) / sections0:.2f} cents per section.",
              f"Rounds 1 and 2: {sum(c['tasks'] for c in calls if c['round'] > 0)} re-labels in {sum(1 for c in calls if c['round'] > 0)} calls; counted once {fmt(sum(c['counted_once'] for c in calls if c['round'] > 0) / max(1, sum(c['tasks'] for c in calls if c['round'] > 0)))} tokens per re-label, {100 * sum(c['dollars'] for c in calls if c['round'] > 0) / max(1, sum(c['tasks'] for c in calls if c['round'] > 0)):.2f} cents per re-label.",
              f"Wall time: first call started {datetime.fromtimestamp(calls[0]['start']).isoformat(timespec='seconds')}, last call ended {datetime.fromtimestamp(max(c['end'] for c in calls)).isoformat(timespec='seconds')} (local time).",
              "", "## The fixed context", "",
              f"First request of the first call: {fmt(calls[0]['first_ctx'])} tokens of context ({fmt(calls[0]['write_5m'] if calls[0]['requests'] else 0)} written over the call in all); the agent definition with the labelling instructions, the tool schemas and the workflow harness header. Median first-request context over all calls: {fmt(median(c['first_ctx'] for c in calls))}.",
              ]
    (out_dir / "usage.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))

    # drift by position in the call, round 0
    drift = ["## Exception rate after round 0 by position in the call (sixteen-section calls against eight-section ones)", ""]
    pos = collections.defaultdict(lambda: [0, 0])   # (per, position) -> [exceptions, blocks]
    halves = collections.defaultdict(lambda: [0, 0])
    for c in calls:
        if c["round"] != 0:
            continue
        per = 16 if c["tasks"] > 8 else 8
        cf = run_dir / c["slug"] / "calls" / "round0" / f"{c['name']}.tsv"
        rep = run_dir / c["slug"] / "report-round0.json"
        if not cf.exists() or not rep.exists():
            continue
        names = re.findall(r"^## task (\d{4})", cf.read_text(encoding="utf-8"), re.M)
        exc = collections.Counter(e["block"] for e in json.loads(rep.read_text(encoding="utf-8"))["exceptions"] if isinstance(e.get("block"), int))
        for p, name in enumerate(names, 1):
            tf = run_dir / c["slug"] / "tasks" / "round0" / f"{name}.json"
            if not tf.exists():
                continue
            blocks = [b["i"] for b in json.loads(tf.read_text(encoding="utf-8"))["blocks"]]
            e = sum(exc[i] for i in blocks)
            pos[(per, p)][0] += e; pos[(per, p)][1] += len(blocks)
            halves[(per, "first half" if p <= per // 2 else "second half")][0] += e; halves[(per, "first half" if p <= per // 2 else "second half")][1] += len(blocks)
    drift += ["| Sections per call | Position | Blocks | Exceptions | Rate |", "|---|---|---|---|---|"]
    for (per, p), (e, b) in sorted(pos.items(), key=lambda x: (x[0][0], x[0][1])):
        drift.append(f"| {per} | {p} | {b} | {e} | {e / b:.2%} |")
    drift += ["", "| Sections per call | Half | Blocks | Exceptions | Rate |", "|---|---|---|---|---|"]
    for (per, h), (e, b) in sorted(halves.items()):
        drift.append(f"| {per} | {h} | {b} | {e} | {e / b:.2%} |")
    for per in (8, 16):
        e = sum(v[0] for k, v in pos.items() if k[0] == per); b = sum(v[1] for k, v in pos.items() if k[0] == per)
        drift.append(f"\nAll positions, {per} sections per call: {e} exceptions over {b} blocks, {e / b:.2%}." if b else "")
    (out_dir / "drift.md").write_text("\n".join(drift) + "\n", encoding="utf-8")
    print("\n".join(drift))


if __name__ == "__main__":
    main(*sys.argv[1:4])
