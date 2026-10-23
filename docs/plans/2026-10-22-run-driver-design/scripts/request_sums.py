"""What a call really sends: per-request sums over a subagent's API requests (the harness figure counts the context once).

For each subagent transcript: the number of API requests, the tokens newly written to the cache, the tokens re-read
from the cache, and the output tokens; then the cost-weighted total at Claude Opus 5.5 list prices relative to one
input token (cache write 1.25, cache read 0.1, output 5). Groups the lean run's calls by tasks per call.

Usage: python3 request_sums.py CALLS.csv OUT.md NAME=SUBAGENTS_DIR [NAME=SUBAGENTS_DIR ...]
"""
import csv, json, sys, statistics as st, collections, re
from pathlib import Path

W_WRITE, W_READ, W_OUT = 1.25, 0.1, 5.0


PATH = re.compile(r"structure-map-2026-10-22/([^/\s]+)/tasks/round(\d)/")
BATCH = re.compile(r"\[((?:\d{4})(?:,\s*\d{4})*)\]")
SINGLE = re.compile(r"/tasks/round\d/(\d{4})\.json")


def sums(path):
    seen = {}
    key = None
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            j = json.loads(line)
        except Exception:
            continue
        m = j.get("message")
        if key is None and j.get("type") == "user" and isinstance(m, dict):
            c = m.get("content")
            text = c if isinstance(c, str) else "".join(b.get("text", "") for b in c if isinstance(b, dict)) if isinstance(c, list) else ""
            pm = PATH.search(text)
            if pm and "label_section.md" in text:
                b = BATCH.search(text)
                tasks = [t.strip() for t in b.group(1).split(",")] if b else sorted(set(SINGLE.findall(text)))
                key = (pm.group(1), pm.group(2), " ".join(tasks))
        if j.get("type") == "assistant" and isinstance(m, dict) and isinstance(m.get("usage"), dict) and m.get("id"):
            u = m["usage"]
            r = seen.setdefault(m["id"], {"w": u.get("cache_creation_input_tokens", 0) + u.get("input_tokens", 0), "r": u.get("cache_read_input_tokens", 0), "o": 0})
            r["o"] = max(r["o"], u.get("output_tokens", 0))
    n = len(seen)
    return key, {"requests": n, "written": sum(r["w"] for r in seen.values()), "read": sum(r["r"] for r in seen.values()), "output": sum(r["o"] for r in seen.values())}


def main():
    calls_csv, out = sys.argv[1], sys.argv[2]
    calls = {}
    for r in csv.DictReader(open(calls_csv, encoding="utf-8")):
        calls[(r["session"], r["slug"], r["round"], r["tasks"])] = r
    rows = []
    for arg in sys.argv[3:]:
        name, sub = arg.split("=", 1)
        for p in sorted(Path(sub).glob("agent-*.jsonl")):
            key, s = sums(p)
            if key is None:
                continue
            c = calls.get((name, key[0], key[1], key[2]))
            if c is None:
                continue
            rows.append({"session": name, "agent": c["agent"], "round": c["round"], "n_tasks": int(c["n_tasks"]), "harness": int(c["tokens"]) if c["tokens"] else 0,
                         **s, "weighted": s["written"] * W_WRITE + s["read"] * W_READ + s["output"] * W_OUT})
    with open(Path(out).with_suffix(".csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    lines = ["## What a call really sends: API requests per call, by agent, round and sections per call\n",
             "| Agent | Round | Tasks per call | Calls | Median requests per call | Harness figure (context once) | Written to cache | Re-read from cache | Output | Cost-weighted | Cost-weighted per task |",
             "|---|---|---|---|---|---|---|---|---|---|---|"]
    g = collections.defaultdict(list)
    for r in rows:
        g[(r["session"], r["agent"], r["round"], r["n_tasks"])].append(r)
    for k in sorted(g, key=lambda k: (k[0], k[2], k[3])):
        v = g[k]
        if len(v) < 2:
            continue
        med = lambda f: int(st.median(r[f] for r in v))
        lines.append(f"| {k[1]} ({k[0]}) | {k[2]} | {k[3]} | {len(v)} | {med('requests')} | {med('harness'):,} | {med('written'):,} | {med('read'):,} | {med('output'):,} | {med('weighted'):,} | {int(med('weighted') / k[3]):,} |")
    lines.append(f"\nMedians over the calls of each row. {len(rows)} subagent transcripts matched to a dispatch. "
                 "A call makes one API request per batch of tool calls: the lean agent at 8 sections typically makes 10 to 11 requests (reads and writes partly batched), and each request re-reads the whole context so far from the cache.")
    lines.append(f"\nWeights: cache write 1.25, cache read 0.1, output 5, relative to one uncached input token, from the Claude Opus 5.5 list prices (input 4, cache write 5, cache read 0.4, output 20 dollars per million). The harness's figure per call counts the context once and is what the task notifications show; the plan's own metering is not published, so both are given.")
    Path(out).write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
