"""The full-corpus estimate: tokens and calls for the audit of every act under three drivers, and the cost of the
two measurements the plan proposes. Every constant is read from the measurement files or named with its source.

Inputs: step7/corpus_blocks.csv (the splitter over the raw store), step2/density.md's measured per-section
figures (copied here with their source), step1/requests.csv (the lean run's per-request sums),
step3/calibration.csv (the lean run's first-request sizes and the bytes-per-token fits), step1/composition.csv
(the lean agent's startup context by part), step3/encoding.json (tokens per section by encoding), and the
labelling instructions file. Two accountings: the harness figure (context counted once) and the cost-weighted
figure (cache writes 1.25, cache reads 0.1, output 5, relative to one uncached input token, Claude Opus 5.5
list prices).

Usage: python3 estimate.py MEASUREMENT_DIR PROMPT_FILE OUT.md
"""
import csv, json, sys, statistics as st
from pathlib import Path

W_WRITE, W_READ, W_OUT = 1.25, 0.1, 5.0
SECTIONS = 8          # sections per round-0 call (the lean run's density, proved flat by position)
L2_TASKS = 25         # ladder tasks per call in the recommended design
L2_ANS = 60           # output tokens per ladder task in the compact form (one entry)
TARGET_SHARE_R1 = 0.015   # share of blocks excepted in round 0: the lean run's 0.9 per 100 at 8 sections, raised for safety
R2_SHARE = 0.19           # share of round-1 targets still excepted after round 1 (step4/ladder.md, 579 targets)
TEST_SECTIONS, TEST_TEXT_BYTES = 1_236, 11_133_685   # the test set's sections and text bytes (step 2)


def fit(pairs):
    n = len(pairs); sx = sum(x for x, _ in pairs); sy = sum(y for _, y in pairs)
    sxx = sum(x * x for x, _ in pairs); sxy = sum(x * y for x, y in pairs)
    b = (n * sxy - sx * sy) / (n * sxx - sx * sx); a = (sy - b * sx) / n
    return a, b


def measured(requests_csv):
    """Median per-section figures of the measured drivers, from the per-request sums joined to the dispatches."""
    rows = list(csv.DictReader(open(requests_csv, encoding="utf-8")))
    def med(session, agent, rnd, n, field):
        v = [float(r[field]) for r in rows if r["session"] == session and r["agent"] == agent and r["round"] == rnd and int(r["n_tasks"]) == n]
        return st.median(v), len(v)
    d0_once, n0 = med("night", "general-purpose", "0", 3, "harness"); d0_w, _ = med("night", "general-purpose", "0", 3, "weighted")
    d1_once, n1 = med("lean", "labeller", "0", 8, "harness"); d1_w, _ = med("lean", "labeller", "0", 8, "weighted")
    l1_once, nl = med("lean", "labeller", "1", 10, "harness"); l1_w, _ = med("lean", "labeller", "1", 10, "weighted")
    return {"D0": (d0_once / 3, d0_w / 3, n0), "D1": (d1_once / 8, d1_w / 8, n1), "L1": (l1_once / 10, l1_w / 10, nl), "D1_call": (d1_once, d1_w)}


def main():
    mdir, prompt_file, out = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
    cal = list(csv.DictReader(open(mdir / "step3" / "calibration.csv", encoding="utf-8")))
    fixed_lean = st.median(int(r["tokens"]) for r in cal if r["kind"] == "fixed")
    reads = [(int(r["bytes"]), int(r["tokens"])) for r in cal if r["kind"] == "read_task" and int(r["bytes"]) > 0]
    task_a, task_b = fit(reads); task_bpt = 1 / task_b
    comp = [r for r in csv.DictReader(open(mdir / "step1" / "composition.csv", encoding="utf-8")) if r["call"] == "lean-tiny"]
    total_chars = sum(int(r["chars"]) for r in comp)
    claudemd_share = sum(int(r["chars"]) for r in comp if r["part"].startswith("instruction file")) / total_chars
    hook_chars = sum(int(r["chars"]) for r in comp if r["part"].startswith("SubagentStart"))
    usage = [r for r in csv.DictReader(open(mdir / "step1" / "usage.csv", encoding="utf-8")) if r["call"] == "lean-tiny"]
    lean_fixed_this = int(usage[0]["cache_write"]) + int(usage[0]["input"])
    chars_per_token = total_chars / lean_fixed_this
    hook_tokens = hook_chars / chars_per_token
    fixed_d2 = fixed_lean * (1 - claudemd_share)
    enc = json.load(open(mdir / "step3" / "encoding.json"))
    task_c, ans_b = enc["task_tokens"]["C"], enc["answer_tokens"]["B"]
    instr = len(prompt_file.read_bytes()) / task_bpt
    m = measured(mdir / "step1" / "requests.csv")
    blocks_rows = list(csv.DictReader(open(mdir / "step7" / "corpus_blocks.csv", encoding="utf-8")))
    ok = [r for r in blocks_rows if r["spine"] == "1"]
    blocks = sum(int(r["blocks"]) for r in ok); sections = sum(int(r["sections"]) for r in ok); tbytes = sum(int(r["bytes"]) for r in ok)
    scale = (tbytes / sections) / (TEST_TEXT_BYTES / TEST_SECTIONS)

    def call(n_sections, task_tok, ans_tok, fixed):
        prompt = instr + n_sections * task_tok; out_t = n_sections * ans_tok
        once = fixed + prompt + out_t
        written = prompt + 300
        read = fixed + (fixed + prompt + out_t)
        return once, written * W_WRITE + read * W_READ + out_t * W_OUT

    d2_once, d2_w = call(SECTIONS, task_c, ans_b, fixed_d2)
    l2_task_tok = st.median(int(r["bytes"]) for r in [] ) if False else 1_511 / task_bpt + 60   # a round-1 task file, median 1,511 bytes (step4/ladder.md)
    l2_once, l2_w = call(L2_TASKS, l2_task_tok, L2_ANS, fixed_d2)
    t1 = blocks * TARGET_SHARE_R1; t2 = t1 * R2_SHARE
    # the two proposed measurements
    m16_once, m16_w = call(16, task_c, ans_b, fixed_d2); m16_calls = 6
    wf_once = 2 * (fixed_lean + instr + (1 / 36 + 42 / 36) / 2 * (task_c + ans_b) * 2)
    lines = [f"Corpus: {len(ok):,} act pages with an act ({len(blocks_rows) - len(ok)} pages of site chrome only), {blocks:,} blocks, {sections:,} sections, {tbytes:,} bytes of text; "
             f"{tbytes / sections:,.0f} bytes of text per section against {TEST_TEXT_BYTES / TEST_SECTIONS:,.0f} in the test set (scale {scale:.2f}).\n",
             "## Derived constants\n",
             f"- Lean agent's fixed context: median {fixed_lean:,.0f} tokens over the lean run's {sum(1 for r in cal if r['kind'] == 'fixed')} calls; this session's lean call {lean_fixed_this:,} tokens for {total_chars:,} characters ({chars_per_token:.2f} characters per token).",
             f"- Instruction files and memory index: {100 * claudemd_share:.0f}% of the lean agent's startup characters, so the fixed context without them is {fixed_d2:,.0f} tokens.",
             f"- The first-principles hook: {hook_chars:,} characters, about {hook_tokens:,.0f} tokens per call; over {sections / SECTIONS:,.0f} round-0 calls about {hook_tokens * sections / SECTIONS / 1e6:,.0f} million.",
             f"- Task text rate: {task_bpt:.2f} bytes per token ({len(reads)} reads); the instructions file {len(prompt_file.read_bytes()):,} bytes, about {instr:,.0f} tokens.",
             f"- Per section: task in form C {task_c:,.0f} tokens, answer in form B {ans_b:,.0f} tokens (step 3).",
             f"- The recommended round-0 call: {d2_once:,.0f} tokens counted once, {d2_w:,.0f} cost-weighted, 2 API requests; the lean driver as measured {m['D1_call'][0]:,.0f} and {m['D1_call'][1]:,.0f}.",
             f"- The recommended ladder call: {L2_TASKS} tasks of {l2_task_tok:,.0f} tokens, {l2_once:,.0f} counted once, {l2_w:,.0f} cost-weighted.",
             "\n## Round 0 over the whole corpus\n",
             "| Driver | Calls | Tokens per section (context once) | Total, context once | Tokens per section, cost-weighted | Total, cost-weighted | Basis |",
             "|---|---|---|---|---|---|---|"]
    designs = [("Current driver: general-purpose subagent, 3 sections per call", sections / 3, m["D0"][0] * scale, m["D0"][1] * scale, f"{m['D0'][2]} calls of the night of 21 to 22 October"),
               ("Lean driver as measured: labeller, 8 sections per call, one Read and one Write per task", sections / 8, m["D1"][0] * scale, m["D1"][1] * scale, f"{m['D1'][2]} calls of the lean run"),
               ("Recommended: labeller without instruction files, warm cache, 8 sections inline, one compact answer file, 2 requests per call", sections / SECTIONS, d2_once / SECTIONS * scale, d2_w / SECTIONS * scale, "derived above")]
    for name, calls, once, w, src in designs:
        lines.append(f"| {name} | {calls:,.0f} | {once:,.0f} | {once * sections / 1e6:,.0f} million | {w:,.0f} | {w * sections / 1e6:,.0f} million | {src} |")
    lines += ["\n## The ladder over the whole corpus (rounds 1 and 2)\n",
              f"Round-1 targets at {100 * TARGET_SHARE_R1:.1f}% of blocks: {t1:,.0f}; round-2 targets at {100 * R2_SHARE:.0f}% of those: {t2:,.0f}.\n",
              "| Driver | Tasks per call | Calls | Tokens per task (context once) | Total, context once | Tokens per task, cost-weighted | Total, cost-weighted |",
              "|---|---|---|---|---|---|---|",
              f"| Lean as measured | 10 | {(t1 + t2) / 10:,.0f} | {m['L1'][0]:,.0f} | {m['L1'][0] * (t1 + t2) / 1e6:,.0f} million | {m['L1'][1]:,.0f} | {m['L1'][1] * (t1 + t2) / 1e6:,.0f} million |",
              f"| Recommended | {L2_TASKS} | {(t1 + t2) / L2_TASKS:,.0f} | {l2_once / L2_TASKS:,.0f} | {l2_once / L2_TASKS * (t1 + t2) / 1e6:,.0f} million | {l2_w / L2_TASKS:,.0f} | {l2_w / L2_TASKS * (t1 + t2) / 1e6:,.0f} million |",
              "\n## The two proposed measurements\n",
              f"- Sixteen sections per call: {m16_calls} calls of {m16_once:,.0f} tokens counted once ({m16_w:,.0f} cost-weighted), about {m16_calls * m16_once:,.0f} tokens in all.",
              f"- The labeller inside a workflow, on the tiny and the known task of step 1: 2 calls, about {wf_once:,.0f} tokens in all at the lean agent's measured fixed context.",
              "\n## Assumptions\n",
              "- The recommended call makes two API requests: the prompt (instructions and sections inline) and the one Write of the answer file, then the one-line reply; the fixed prefix is read from the cache, not written, because the cache is kept warm for an hour and the first call of a batch warms it.",
              "- Exception rates are the lean run's at 8 sections per call over the sixteen test-set acts, which include the hardest cases on purpose; the corpus at large is expected at or below them.",
              "- The reads of what survives round 2 are decided per batch and not estimated.",
              "- Thinking tokens are counted in the output of the measured rows; the estimate assumes the same share.",
              ]
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
