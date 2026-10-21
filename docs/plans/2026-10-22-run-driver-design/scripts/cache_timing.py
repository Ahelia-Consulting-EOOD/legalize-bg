"""Read and write tokens, call durations and cache use, per measured call (the owner's requirement of 21 October 2026).

For every labelling call matched to its dispatch, reads the subagent transcript for: the time the call started, the
time its first API response arrived, the time it ended, and per request the four token classes (uncached input,
cache write, cache read, output). Derives: the call's duration, the share of its first request that was read
from a warm cache (a prefix an earlier sibling call had written), whether a warm prefix was available (a
same-agent call had finished its first request within the subagent cache lifetime before this call started),
and the cost at Claude Opus 5.5 list prices per section. Prints Markdown tables and writes ``cache_timing.csv``.

Usage: python3 cache_timing.py CALLS.csv OUT_DIR NAME=SUBAGENTS_DIR [NAME=SUBAGENTS_DIR ...]
"""
import csv, json, re, sys, statistics as st, collections
from datetime import datetime, timezone
from pathlib import Path

PRICE = {"input": 4.0, "write": 5.0, "read": 0.40, "output": 20.0}   # dollars per million tokens, Opus 5.5 list, 6 October 2026
TTL_S = 300                                                            # subagent prompt-cache lifetime by default: five minutes
PATH = re.compile(r"structure-map-2026-10-22/([^/\s]+)/tasks/round(\d)/")
BATCH = re.compile(r"\[((?:\d{4})(?:,\s*\d{4})*)\]")
SINGLE = re.compile(r"/tasks/round\d/(\d{4})\.json")


def ts(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp() if s else None


def read_call(path):
    key = None; t0 = t1 = tend = None; reqs = {}
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
            pm = PATH.search(text)
            if pm and "label_section.md" in text:
                b = BATCH.search(text); tasks = [x.strip() for x in b.group(1).split(",")] if b else sorted(set(SINGLE.findall(text)))
                key = (pm.group(1), pm.group(2), " ".join(tasks))
        if t == "assistant" and isinstance(m, dict) and isinstance(m.get("usage"), dict) and m.get("id"):
            u = m["usage"]
            if m["id"] not in reqs:
                reqs[m["id"]] = {"input": u.get("input_tokens", 0), "write": u.get("cache_creation_input_tokens", 0), "read": u.get("cache_read_input_tokens", 0), "output": 0, "t": when}
                t1 = t1 or when
            reqs[m["id"]]["output"] = max(reqs[m["id"]]["output"], u.get("output_tokens", 0))
    return key, t0, t1, tend, list(reqs.values())


def main():
    calls_csv, out = sys.argv[1], Path(sys.argv[2])
    calls = {}
    for r in csv.DictReader(open(calls_csv, encoding="utf-8")):
        calls[(r["session"], r["slug"], r["round"], r["tasks"])] = r
    rows = []
    for arg in sys.argv[3:]:
        name, sub = arg.split("=", 1)
        for p in sorted(Path(sub).glob("agent-*.jsonl")):
            key, t0, t1, tend, reqs = read_call(p)
            if key is None or not reqs or t0 is None:
                continue
            c = calls.get((name, key[0], key[1], key[2]))
            if c is None:
                continue
            first = reqs[0]
            tot = {k: sum(r[k] for r in reqs) for k in ("input", "write", "read", "output")}
            rows.append({"session": name, "agent": c["agent"], "round": c["round"], "n_tasks": int(c["n_tasks"]), "start": t0, "first_response": t1, "end": tend,
                         "duration_s": round(tend - t0, 1), "first_request_s": round((t1 or t0) - t0, 1), "requests": len(reqs),
                         "first_context": first["input"] + first["write"] + first["read"], "first_read": first["read"],
                         "warm_share": round(first["read"] / max(1, first["input"] + first["write"] + first["read"]), 3), **tot,
                         "dollars": sum(tot[k] * PRICE[k] for k in tot) / 1e6})
    rows.sort(key=lambda r: r["start"])
    # was a warm prefix available: a same-session, same-agent call whose first response arrived before this call started, within the TTL
    for i, r in enumerate(rows):
        avail = False
        for q in rows[:i]:
            if q["session"] == r["session"] and q["agent"] == r["agent"] and q["first_response"] and q["first_response"] <= r["start"] <= q["end"] + TTL_S:
                avail = True; break
        r["warm_available"] = int(avail)
    out.mkdir(parents=True, exist_ok=True)
    fields = [k for k in rows[0].keys() if k not in ("start", "first_response", "end")]
    with open(out / "cache_timing.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields); w.writeheader(); w.writerows([{k: r[k] for k in fields} for r in rows])
    lines = ["## Per call: the four token classes, duration and cache use (medians by agent, round and sections per call)\n",
             "| Agent | Round | Tasks per call | Calls | Duration, seconds | Time to first response, seconds | Uncached input | Cache write | Cache read | Output | First request read from a warm prefix | Warm prefix available at start | Dollars per call at list price | Cents per task |",
             "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    g = collections.defaultdict(list)
    for r in rows:
        g[(r["session"], r["agent"], r["round"], r["n_tasks"])].append(r)
    for k in sorted(g, key=lambda k: (k[0], k[2], k[3])):
        v = g[k]
        if len(v) < 2:
            continue
        med = lambda f: st.median(r[f] for r in v)
        lines.append(f"| {k[1]} ({k[0]}) | {k[2]} | {k[3]} | {len(v)} | {med('duration_s'):.0f} | {med('first_request_s'):.0f} | {med('input'):,.0f} | {med('write'):,.0f} | {med('read'):,.0f} | {med('output'):,.0f} | "
                     f"{100 * med('warm_share'):.0f}% | {100 * sum(r['warm_available'] for r in v) / len(v):.0f}% of calls | {med('dollars'):.3f} | {100 * med('dollars') / k[3]:.2f} |")
    lines.append("\nList prices of Claude Opus 5.5 (6 October 2026): uncached input 4, cache write 5, cache read 0.40, output 20 dollars per million tokens. The dollar figures compare designs; the runs draw on the owner's plan, whose metering is not published.\n")
    # warm availability against warm reads
    for sess in sorted({r["session"] for r in rows}):
        v = [r for r in rows if r["session"] == sess and r["round"] == "0"]
        if not v:
            continue
        avail = [r for r in v if r["warm_available"]]
        lines.append(f"- {sess}, round 0: {len(v)} calls; a warm prefix was available at the start of {len(avail)} ({100 * len(avail) / len(v):.0f}%); "
                     f"median share of the first request read from cache: {100 * st.median(r['warm_share'] for r in v):.0f}% over all calls, "
                     f"{100 * st.median(r['warm_share'] for r in avail):.0f}% when available, {100 * st.median(r['warm_share'] for r in v if not r['warm_available']):.0f}% when not." if avail and len(avail) < len(v) else
                     f"- {sess}, round 0: {len(v)} calls; a warm prefix was available at the start of {len(avail)} ({100 * len(avail) / len(v):.0f}%); median share of the first request read from cache {100 * st.median(r['warm_share'] for r in v):.0f}%.")
    # launch pattern: gaps between dispatches
    for sess in sorted({r["session"] for r in rows}):
        v = sorted([r for r in rows if r["session"] == sess], key=lambda r: r["start"])
        gaps = [v[i]["start"] - v[i - 1]["start"] for i in range(1, len(v))]
        same_second = sum(1 for x in gaps if x < 2)
        lines.append(f"- {sess}: {len(v)} calls over {(v[-1]['start'] - v[0]['start']) / 3600:.1f} hours; {same_second} of {len(gaps)} launches within 2 seconds of the previous one (a parallel batch); "
                     f"median gap between batches {st.median(x for x in gaps if x >= 2) / 60:.1f} minutes; {sum(1 for x in gaps if x > TTL_S)} gaps longer than the five-minute cache lifetime.")
    (out / "cache_timing.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
