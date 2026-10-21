"""The size of the task and the answer under the current encoding and two leaner ones, without loss of meaning.

Reads every round-0 task file and answer file of the run (read-only). Encodings of a task: (A) the current file
as the Read tool renders it (indented JSON plus a line-number prefix per line); (B) compact JSON, one line per
block, short keys (i, h, t), delivered inline in the prompt (no line numbers); (C) tab-separated lines
``i<TAB>hint<TAB>text`` under a one-line header, inline. Encodings of an answer: (A) the current JSON array,
one object per block with i, label, n, conf, note; (B) compact JSON with short keys (i, l; n only where the
label is numbered; c only when low; note only when low). Every encoding keeps the block indices, the hints,
the verbatim text, every label, every number, every low-confidence mark and every note on a low-confidence
entry, which is all that ``reading/checks.py`` and ``reading/labels.py`` read. Token figures use the rates
measured in ``calibrate_tokens.py`` (bytes per token of the rendered Read text and of the written answer).

Usage: python3 encoding.py RUN_ROOT OUT_DIR
"""
import json, sys, statistics as st
from pathlib import Path

READ_PREFIX = 7      # bytes the Read tool adds per line (line number and arrow)
TASK_BPT = 3.44      # bytes per token, Read-rendered task JSON (calibration, 56 reads)
TASK_FIXED = 366     # tokens per Read result that do not scale with size (framing)
ANS_BPT = 2.12       # bytes per token, written answer JSON (calibration, 143 writes)
ANS_FIXED = 118
NUMBERED = {"article_head", "alinea", "item", "letter", "paragraph_sign"}


def task_a(task):
    s = json.dumps(task, ensure_ascii=False, indent=1)
    return len(s.encode("utf-8")) + READ_PREFIX * (s.count("\n") + 1)


def task_b(task):
    lines = []
    if task.get("context"):
        lines.append(json.dumps({"context": task["context"]}, ensure_ascii=False, separators=(",", ":")))
    for b in task["blocks"]:
        d = {"i": b["i"], "h": b["hint"], "t": b["text"]}
        for k in ("current_label", "current_n"):
            if k in b and b[k] is not None:
                d[k[:9]] = b[k]
        lines.append(json.dumps(d, ensure_ascii=False, separators=(",", ":")))
    return len("\n".join(lines).encode("utf-8"))


def task_c(task):
    lines = []
    if task.get("context"):
        lines.append("# context: " + " | ".join(task["context"]))
    for b in task["blocks"]:
        extra = f"\t{b['current_label']}" if b.get("current_label") else ""
        lines.append(f"{b['i']}\t{b['hint']}\t{b['text']}{extra}")
    return len("\n".join(lines).encode("utf-8"))


def answer_a(entries):
    return len(("[\n" + ",\n".join(json.dumps(e, ensure_ascii=False) for e in entries) + "\n]\n").encode("utf-8"))


def answer_b(entries):
    out = []
    for e in entries:
        d = {"i": e["i"], "l": e["label"]}
        if e["label"] in NUMBERED and e.get("n") is not None:
            d["n"] = e["n"]
        if e.get("conf") == "low":
            d["c"] = "low"
            if e.get("note"):
                d["note"] = e["note"]
        elif e["label"] in ("drop", "unknown") and e.get("note"):
            d["note"] = e["note"]
        out.append(json.dumps(d, ensure_ascii=False, separators=(",", ":")))
    return len(("[" + ",\n".join(out) + "]").encode("utf-8"))


def main():
    run_root, out_dir = Path(sys.argv[1]), Path(sys.argv[2])
    ta = tb = tc = aa = ab = 0; n_tasks = n_blocks = n_ans = 0; notes_kept = notes_dropped = 0
    per_task = []
    for d in sorted(run_root.iterdir()):
        tdir = d / "tasks" / "round0"; mdir = d / "maps" / "round0"
        if not tdir.exists():
            continue
        for tf in sorted(tdir.glob("*.json")):
            task = json.loads(tf.read_text(encoding="utf-8"))
            a, b, c = task_a(task), task_b(task), task_c(task)
            ta += a; tb += b; tc += c; n_tasks += 1; n_blocks += len(task["blocks"])
            per_task.append((a, b, c, len(task["blocks"])))
            af = mdir / tf.name
            if af.exists():
                try:
                    entries = json.loads(af.read_text(encoding="utf-8").strip().strip("`").replace("json\n", "", 1))
                except Exception:
                    continue
                if isinstance(entries, list) and all(isinstance(e, dict) and "label" in e for e in entries):
                    aa += answer_a(entries); ab += answer_b(entries); n_ans += len(entries)
                    for e in entries:
                        if e.get("note"):
                            if e.get("conf") == "low" or e["label"] in ("drop", "unknown"):
                                notes_kept += 1
                            else:
                                notes_dropped += 1
    tok = lambda by, bpt, fixed, n: int(by / bpt + fixed * n)
    lines = [f"Round-0 task files read: {n_tasks:,} ({n_blocks:,} blocks, {n_blocks / n_tasks:.0f} per section); answer entries read: {n_ans:,}.\n",
             "## Task (input) per section, three encodings\n",
             "| Encoding | Bytes per section | Estimated tokens per section | Share of A |", "|---|---|---|---|",
             f"| A: current indented JSON file, read with the Read tool | {ta / n_tasks:,.0f} | {tok(ta, TASK_BPT, TASK_FIXED, n_tasks) / n_tasks:,.0f} | 100% |",
             f"| B: compact JSON, one line per block, short keys, inline in the prompt | {tb / n_tasks:,.0f} | {tok(tb, TASK_BPT, 0, n_tasks) / n_tasks:,.0f} | {100 * tb / ta:.0f}% |",
             f"| C: tab-separated lines, inline in the prompt | {tc / n_tasks:,.0f} | {tok(tc, TASK_BPT, 0, n_tasks) / n_tasks:,.0f} | {100 * tc / ta:.0f}% |",
             "\n## Answer (output) per section, two encodings\n",
             "| Encoding | Bytes per section | Estimated tokens per section | Share of A |", "|---|---|---|---|",
             f"| A: current JSON, i, label, n, conf, note on every entry | {aa / n_tasks:,.0f} | {tok(aa, ANS_BPT, ANS_FIXED, n_tasks) / n_tasks:,.0f} | 100% |",
             f"| B: compact JSON, i and l always; n only on numbered labels; c and note only on low confidence, drop and unknown | {ab / n_tasks:,.0f} | {tok(ab, ANS_BPT, ANS_FIXED, n_tasks) / n_tasks:,.0f} | {100 * ab / aa:.0f}% |",
             f"\nNotes on high-confidence entries that encoding B drops: {notes_dropped:,} (they explain a label the checks accept, such as 'opens with (1) on the same line'); notes kept: {notes_kept:,}.",
             "\nThe token estimate applies the measured bytes-per-token rate of the current encoding to the leaner ones. The bytes removed are mostly ASCII scaffolding (keys, indentation, line numbers), which the tokenizer packs less densely than it packs the Bulgarian text, so the token share saved is at least the byte share shown.",
             ]
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "encoding.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
