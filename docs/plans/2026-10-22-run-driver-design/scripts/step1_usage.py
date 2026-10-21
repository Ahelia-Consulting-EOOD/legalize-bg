"""Step 1: per-request usage and startup composition of the four measurement calls.

Reads the four subagent transcripts (JSONL) of this session's calls and writes ``usage.csv`` (one row per API
request: call, model, cache read, cache write, input, output) and ``composition.csv`` (one row per part of
the lean and the general-purpose agent's startup context, in characters: instruction files, hook output,
system prompt, tool schemas, git status, reminders). Prints the fixed-context table of the plan. The
transcripts live in the session's scratchpad and are not kept; the two CSV files are.

Usage: python3 step1_usage.py TASKS_DIR OUT_DIR
"""
import csv, json, sys
from pathlib import Path

CALLS = {"afc4202adde41646a": "gp-tiny", "a59d61247eeed2d07": "lean-tiny", "afbb306a57d2ce16c": "lean-empty", "ac1181dab9d7115f7": "lean-known"}


def main():
    tasks, out = Path(sys.argv[1]), Path(sys.argv[2])
    usage, comp = [], []
    for tid, name in CALLS.items():
        reqs = {}
        for line in (tasks / f"{tid}.output").read_text(encoding="utf-8").splitlines():
            try:
                j = json.loads(line)
            except Exception:
                continue
            m = j.get("message"); t = j.get("type")
            if t == "assistant" and isinstance(m, dict) and isinstance(m.get("usage"), dict) and m.get("id"):
                u = m["usage"]
                r = reqs.setdefault(m["id"], {"call": name, "model": m.get("model"), "cache_read": u.get("cache_read_input_tokens", 0),
                                               "cache_write": u.get("cache_creation_input_tokens", 0), "input": u.get("input_tokens", 0), "output": 0})
                r["output"] = max(r["output"], u.get("output_tokens", 0))
            if t == "attachment":
                a = j.get("attachment", {}); at = a.get("type")
                if at == "instructions":
                    for f in a.get("files", []):
                        comp.append({"call": name, "part": "instruction file " + Path(f.get("path", "?")).name, "chars": len(f.get("content", ""))})
                elif at == "hook_additional_context":
                    comp.append({"call": name, "part": "SubagentStart hook (first principles, work line)", "chars": sum(len(c) if isinstance(c, str) else len(json.dumps(c)) for c in a.get("content", []))})
                elif at == "skill_listing":
                    comp.append({"call": name, "part": "skills listing", "chars": len(a.get("content", ""))})
                elif at == "deferred_tools_delta":
                    comp.append({"call": name, "part": "deferred tool names", "chars": len(json.dumps(a))})
                elif at == "agent_listing_delta":
                    comp.append({"call": name, "part": "agent listing", "chars": len(json.dumps(a))})
            if t == "api-request-shape":
                sh = j.get("shape", {})
                comp.append({"call": name, "part": "system prompt", "chars": sum(len(b.get("text", "")) for b in sh.get("system", []) if isinstance(b, dict))})
                comp.append({"call": name, "part": "tool schemas (" + ", ".join(x.get("name", "?") for x in sh.get("tools", []))[:60] + ")", "chars": len(json.dumps(sh.get("tools", [])))})
            if t == "api-request-blob":
                m = j.get("message", {}); c = m.get("content")
                if isinstance(c, list):
                    for b in c:
                        if isinstance(b, dict) and b.get("type") == "text":
                            tx = b.get("text", "")
                            if tx.startswith("<system-reminder>\nAs you answer"):
                                comp.append({"call": name, "part": "git status snapshot", "chars": len(tx)})
                            elif tx.startswith("<system-reminder>\nYour final report"):
                                comp.append({"call": name, "part": "hand-back reminder", "chars": len(tx)})
                            elif tx.startswith("<system-reminder>\nAttribution"):
                                comp.append({"call": name, "part": "attribution reminder", "chars": len(tx)})
        usage.extend(reqs.values())
    out.mkdir(parents=True, exist_ok=True)
    with open(out / "usage.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["call", "model", "cache_read", "cache_write", "input", "output"]); w.writeheader(); w.writerows(usage)
    with open(out / "composition.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["call", "part", "chars"]); w.writeheader(); w.writerows(comp)
    print("| Call | Model | Requests | Fixed context (first request) | Content added later | Output |")
    print("|---|---|---|---|---|---|")
    for name in CALLS.values():
        rs = [r for r in usage if r["call"] == name]
        fixed = rs[0]["cache_write"] + rs[0]["input"]
        later = sum(r["cache_write"] + r["input"] for r in rs[1:])
        print(f"| {name} | {rs[0]['model']} | {len(rs)} | {fixed:,} | {later:,} | {sum(r['output'] for r in rs):,} |")
    for name in ("lean-tiny", "gp-tiny"):
        parts = [c for c in comp if c["call"] == name]
        tot = sum(c["chars"] for c in parts)
        print(f"\n{name}: startup context {tot:,} characters")
        for c in sorted(parts, key=lambda c: -c["chars"]):
            print(f"  {c['chars']:>7,}  {100 * c['chars'] / tot:4.0f}%  {c['part']}")
    lean = [c for c in comp if c["call"] == "lean-tiny"]
    cm = sum(c["chars"] for c in lean if c["part"].startswith("instruction file"))
    print(f"\nlean: instruction files and memory index share = {cm / sum(c['chars'] for c in lean):.3f}")


if __name__ == "__main__":
    main()
