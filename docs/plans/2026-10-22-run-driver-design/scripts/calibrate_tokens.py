"""Calibrate a bytes-to-tokens estimate from the lean agents' own API usage records.

Walks the subagent transcripts of an exported session. For every API request whose new content since
the previous request is exactly one Read tool result, pairs the request's newly cached tokens
(``cache_creation_input_tokens`` + ``input_tokens``) with the rendered text the model saw (the tool
result's bytes) and the file it came from. For every request whose output is one Write of an answer
file, pairs ``output_tokens`` with the written content's bytes (thinking tokens, when present, are
included in the output count and reported separately). Prints the fit and the per-kind ratios.

Usage: python3 calibrate_tokens.py SUBAGENTS_DIR OUT.csv
"""
import csv, json, sys, statistics as st
from pathlib import Path


def cyr(text):
    return sum(1 for ch in text if "\u0400" <= ch <= "\u04ff")


def fit2(rows):
    """Least squares tokens = a + b*cyr + c*other, by the normal equations."""
    import itertools
    X = [[1.0, r["cyr"], r["other"]] for r in rows]; y = [r["tokens"] for r in rows]
    A = [[sum(X[k][i] * X[k][j] for k in range(len(X))) for j in range(3)] for i in range(3)]
    b = [sum(X[k][i] * y[k] for k in range(len(X))) for i in range(3)]
    for i in range(3):
        piv = A[i][i]
        for j in range(i, 3): A[i][j] /= piv
        b[i] /= piv
        for r in range(3):
            if r != i:
                f = A[r][i]
                for j in range(i, 3): A[r][j] -= f * A[i][j]
                b[r] -= f * b[i]
    return b


def requests_of(path):
    """Ordered API requests of one subagent: [(message_id, usage, assistant_blocks, user_blocks_before)]."""
    reqs = []
    pending_user = []
    seen = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            j = json.loads(line)
        except Exception:
            continue
        t = j.get("type"); m = j.get("message")
        if not isinstance(m, dict):
            continue
        c = m.get("content")
        if t == "user" and isinstance(c, list):
            pending_user.extend(b for b in c if isinstance(b, dict))
        elif t == "assistant" and isinstance(m.get("usage"), dict) and m.get("id"):
            mid = m["id"]
            if mid in seen:
                r = seen[mid]
                r["out"] = max(r["out"], m["usage"].get("output_tokens", 0))
                r["blocks"].extend(b for b in (c or []) if isinstance(b, dict))
                continue
            u = m["usage"]
            r = {"id": mid, "new": u.get("cache_creation_input_tokens", 0) + u.get("input_tokens", 0),
                 "read": u.get("cache_read_input_tokens", 0), "out": u.get("output_tokens", 0),
                 "blocks": [b for b in (c or []) if isinstance(b, dict)], "before": pending_user}
            pending_user = []
            seen[mid] = r
            reqs.append(r)
    return reqs


def main():
    sub, out = Path(sys.argv[1]), sys.argv[2]
    rows = []
    for p in sorted(sub.glob("agent-*.jsonl")):
        reqs = requests_of(p)
        tool_inputs = {}
        for k, r in enumerate(reqs):
            for b in r["blocks"]:
                if b.get("type") == "tool_use":
                    tool_inputs[b.get("id")] = (b.get("name"), b.get("input", {}))
            if k == 0:
                rows.append({"agent": p.stem, "kind": "fixed", "bytes": 0, "lines": 0, "cyr": 0, "other": 0, "tokens": r["new"], "file": ""})
                continue
            results = [b for b in r["before"] if b.get("type") == "tool_result"]
            prev_out = reqs[k - 1]
            # new content = previous assistant output + these tool results; take only the clean single-Read case
            if len(results) == 1 and len([b for b in prev_out["blocks"] if b.get("type") == "tool_use"]) == 1:
                tu = [b for b in prev_out["blocks"] if b.get("type") == "tool_use"][0]
                name, inp = tool_inputs.get(tu.get("id"), (None, {}))
                content = results[0].get("content")
                text = content if isinstance(content, str) else "".join(x.get("text", "") for x in content if isinstance(x, dict))
                if name == "Read" and "/tasks/" in str(inp.get("file_path", "")):
                    rows.append({"agent": p.stem, "kind": "read_task", "bytes": len(text.encode("utf-8")), "lines": text.count("\n") + 1,
                                 "cyr": cyr(text), "other": len(text) - cyr(text),
                                 "tokens": r["new"] - prev_out["out"], "file": inp.get("file_path", "")})
            # outputs: a single Write of an answer file
            tus = [b for b in r["blocks"] if b.get("type") == "tool_use"]
            thinking = sum(len(b.get("thinking", "")) for b in r["blocks"] if b.get("type") == "thinking")
            if len(tus) == 1 and tus[0].get("name") == "Write" and "/maps/" in str(tus[0].get("input", {}).get("file_path", "")):
                content = tus[0]["input"].get("content", "")
                rows.append({"agent": p.stem, "kind": "write_answer" if not thinking else "write_answer_with_thinking",
                             "bytes": len(content.encode("utf-8")), "lines": content.count("\n") + 1,
                             "cyr": cyr(content), "other": len(content) - cyr(content), "tokens": r["out"],
                             "file": tus[0]["input"].get("file_path", "")})
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["agent", "kind", "bytes", "lines", "cyr", "other", "tokens", "file"]); w.writeheader(); w.writerows(rows)
    for kind in ("fixed", "read_task", "write_answer", "write_answer_with_thinking"):
        g = [r for r in rows if r["kind"] == kind and (r["bytes"] > 0 or kind == "fixed")]
        if not g:
            continue
        if kind == "fixed":
            toks = [r["tokens"] for r in g]
            print(f"{kind}: n={len(g)} median tokens {int(st.median(toks))} min {min(toks)} max {max(toks)}")
            continue
        ratios = [r["bytes"] / r["tokens"] for r in g if r["tokens"] > 0]
        # least squares tokens = a + b*bytes
        n = len(g); sx = sum(r["bytes"] for r in g); sy = sum(r["tokens"] for r in g)
        sxx = sum(r["bytes"] ** 2 for r in g); sxy = sum(r["bytes"] * r["tokens"] for r in g)
        b = (n * sxy - sx * sy) / (n * sxx - sx * sx); a = (sy - b * sx) / n
        resid = [r["tokens"] - (a + b * r["bytes"]) for r in g]
        print(f"{kind}: n={n} median bytes/token {st.median(ratios):.2f}; fit tokens = {a:.0f} + {b:.4f} * bytes "
              f"(i.e. {1 / b:.2f} bytes per token), residual median abs {st.median(abs(x) for x in resid):.0f} tokens; "
              f"median bytes {int(st.median(r['bytes'] for r in g))}, median lines {int(st.median(r['lines'] for r in g))}")
        a2, b2, c2 = fit2(g)
        resid2 = [r["tokens"] - (a2 + b2 * r["cyr"] + c2 * r["other"]) for r in g]
        print(f"  two-rate fit: tokens = {a2:.0f} + {b2:.3f} * cyrillic chars + {c2:.3f} * other chars "
              f"({1 / b2:.2f} Cyrillic chars per token, {1 / c2:.2f} other chars per token); residual median abs {st.median(abs(x) for x in resid2):.0f}")
    print(f"{len(rows)} rows written to {out}")


if __name__ == "__main__":
    main()
