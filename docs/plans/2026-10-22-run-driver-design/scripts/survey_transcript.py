"""Extract the Agent dispatches and the task notifications (with their token figures) from an exported session transcript.

Usage: python3 survey_transcript.py TRANSCRIPT.jsonl OUT.json
The export comes from the desktop app (Export transcript), a zip in Downloads; the zip is not kept in the repository.
"""
import json, re, collections, sys
path = sys.argv[1]; out = sys.argv[2]
agent_calls = {}
notifs = {}
with open(path, encoding="utf-8") as f:
    for line in f:
        try: j = json.loads(line)
        except Exception: continue
        m = j.get("message")
        if not isinstance(m, dict): continue
        c = m.get("content")
        if not isinstance(c, list): continue
        for b in c:
            if not isinstance(b, dict): continue
            if b.get("type") == "tool_use" and b.get("name") == "Agent":
                inp = b.get("input", {})
                agent_calls.setdefault(b.get("id"), {"id": b.get("id"), "ts": j.get("timestamp"), "type": inp.get("subagent_type"), "model": inp.get("model"), "desc": inp.get("description"), "prompt": inp.get("prompt","")})
            if b.get("type") == "text" and "<task-notification>" in b.get("text",""):
                for tn in re.finditer(r"<task-notification>(.*?)</task-notification>", b["text"], re.S):
                    s = tn.group(1)
                    g = lambda tag: (re.search(rf"<{tag}>(.*?)</{tag}>", s, re.S) or [None, None])[1]
                    notifs.setdefault(g("tool-use-id"), {"task": g("task-id"), "tool_use": g("tool-use-id"), "status": g("status"), "summary": g("summary"), "tokens": g("subagent_tokens"), "tool_uses": g("tool_uses"), "ms": g("duration_ms")})
print("agent calls:", len(agent_calls), "notifications:", len(notifs), "joined:", sum(1 for k in agent_calls if k in notifs))
print("by type/model:", collections.Counter((a["type"], a["model"]) for a in agent_calls.values()))
json.dump({"agent_calls": list(agent_calls.values()), "notifications": list(notifs.values())}, open(out,"w"), ensure_ascii=False, indent=1)
