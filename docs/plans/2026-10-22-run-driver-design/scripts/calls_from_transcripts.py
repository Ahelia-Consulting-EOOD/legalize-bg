"""Build the table of labelling calls from the two sessions' transcript extracts.

Input: one or more extract JSON files (``{"agent_calls": [...], "notifications": [...]}``) produced by
``survey.py`` over an exported session transcript. Output: ``calls.csv`` with one row per subagent call
that labelled structure-map tasks: session, time, agent type, model, slug, round, tasks, tokens
(the harness's ``subagent_tokens`` figure of the task notification), tool uses, duration.

Usage: python3 calls_from_transcripts.py OUT.csv NAME=EXTRACT.json [NAME=EXTRACT.json ...]
"""
import csv, json, re, sys

PATH = re.compile(r"structure-map-2026-10-22/([^/\s]+)/tasks/round(\d)/")
BATCH = re.compile(r"\[((?:\d{4})(?:,\s*\d{4})*)\]")
SINGLE = re.compile(r"/tasks/round\d/(\d{4})\.json")


def rows(name, path):
    d = json.load(open(path, encoding="utf-8"))
    notes = {n["tool_use"]: n for n in d["notifications"]}
    for a in d["agent_calls"]:
        p = a.get("prompt") or ""
        m = PATH.search(p)
        if not m or "label_section.md" not in p:
            continue
        slug, rnd = m.group(1), int(m.group(2))
        b = BATCH.search(p)
        tasks = [t.strip() for t in b.group(1).split(",")] if b else sorted(set(SINGLE.findall(p)))
        n = notes.get(a["id"], {})
        yield {"session": name, "ts": a.get("ts") or "", "agent": a.get("type") or "general-purpose(default)",
               "model": a.get("model") or "(definition)", "slug": slug, "round": rnd, "n_tasks": len(tasks),
               "tasks": " ".join(tasks), "tokens": n.get("tokens") or "", "tool_uses": n.get("tool_uses") or "",
               "ms": n.get("ms") or "", "status": n.get("status") or "no notification"}


def main():
    out = sys.argv[1]
    allrows = []
    for arg in sys.argv[2:]:
        name, path = arg.split("=", 1)
        allrows.extend(rows(name, path))
    allrows.sort(key=lambda r: (r["ts"] or "9", r["slug"]))
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(allrows[0].keys()))
        w.writeheader(); w.writerows(allrows)
    print(f"{len(allrows)} calls written to {out}")


if __name__ == "__main__":
    main()
