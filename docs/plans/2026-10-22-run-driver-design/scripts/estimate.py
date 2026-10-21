"""The full-corpus estimate: tokens and calls for the audit of every act under three drivers, and the cost of the
two measurements the plan proposes. Every constant is read from the measurement files or named with its source.

Inputs: step7/corpus_blocks.csv (the splitter over the raw store), step1/requests.csv (the per-request sums of
every measured call), step8/cache_timing.csv (the four token classes, durations and warm-prefix share per
call), step3/calibration.csv (the lean run's first-request sizes and the bytes-per-token fits),
step1/composition.csv (the lean agent's startup context by part), step3/encoding.json (tokens per section by
encoding), and the labelling instructions file. Three accountings: the harness figure (context counted once),
the four token classes at Claude Opus 5.5 list prices (uncached input 4, cache write 5, cache read 0.40,
output 20 dollars per million), and the cost-weighted figure (the same prices relative to one uncached input
token: cache write 1.25, cache read 0.1, output 5). Call durations give the wall time of a run and whether the
cache stays warm between calls.

Usage: python3 estimate.py MEASUREMENT_DIR PROMPT_FILE OUT.md
"""
import csv, json, sys, statistics as st
from pathlib import Path

W_WRITE, W_READ, W_OUT = 1.25, 0.1, 5.0
PRICE = {"input": 4.0, "write": 5.0, "read": 0.40, "output": 20.0}   # dollars per million tokens
PARALLEL = 8          # calls in flight at once, as the lean run ran them
TTL_DEFAULT_S, TTL_LONG_S = 300, 3600
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


def classes(timing_csv):
    """Median four-class tokens, dollars and duration per call of the measured drivers (step8/cache_timing.csv)."""
    rows = list(csv.DictReader(open(timing_csv, encoding="utf-8")))
    def med(session, agent, rnd, n):
        v = [r for r in rows if r["session"] == session and r["agent"] == agent and r["round"] == rnd and int(r["n_tasks"]) == n]
        return {k: st.median(float(r[k]) for r in v) for k in ("input", "write", "read", "output", "dollars", "duration_s", "warm_share", "first_context")}, len(v)
    return {"D0": med("night", "general-purpose", "0", 3), "D1": med("lean", "labeller", "0", 8), "L1": med("lean", "labeller", "1", 10)}


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

    cl = classes(mdir / "step8" / "cache_timing.csv")
    warm_tok = cl["D1"][0]["warm_share"] * cl["D1"][0]["first_context"]      # the part of a lean first request read from a sibling's cache: system prompt and tool schemas
    per_call_fixed = max(0.0, fixed_d2 - warm_tok)                           # hook, git status, reminders: written on every call

    def call(n_sections, task_tok, ans_tok, fixed, warm=True):
        """Four token classes of the recommended call: request 1 (prompt, then the one Write) and request 2 (the reply)."""
        prompt = instr + n_sections * task_tok; out_t = n_sections * ans_tok
        shareable = warm_tok if warm else 0.0
        r1_write = (fixed - shareable) + prompt; r1_read = shareable
        r2_read = fixed + prompt + out_t; r2_write = 300
        c = {"input": 0.0, "write": r1_write + r2_write, "read": r1_read + r2_read, "output": out_t + 30}
        once = fixed + prompt + out_t
        weighted = c["write"] * W_WRITE + c["read"] * W_READ + c["output"] * W_OUT
        dollars = sum(c[k] * PRICE[k] for k in c) / 1e6
        return once, weighted, c, dollars

    d2_once, d2_w, d2_c, d2_d = call(SECTIONS, task_c, ans_b, fixed_d2)
    d2cold_once, d2cold_w, d2cold_c, d2cold_d = call(SECTIONS, task_c, ans_b, fixed_d2, warm=False)
    l2_task_tok = 1_511 / task_bpt + 60   # a round-1 task file, median 1,511 bytes (step4/ladder.md)
    l2_once, l2_w, l2_c, l2_d = call(L2_TASKS, l2_task_tok, L2_ANS, fixed_d2)
    t1 = blocks * TARGET_SHARE_R1; t2 = t1 * R2_SHARE
    # the two proposed measurements
    m16_once, m16_w, _, m16_d = call(16, task_c, ans_b, fixed_d2); m16_calls = 6
    wf_once = 2 * (fixed_lean + instr + (1 / 36 + 42 / 36) / 2 * (task_c + ans_b) * 2)
    # durations: the lean 8-section call measured; the recommended call assumed the same (fewer requests, one long output)
    dur = cl["D1"][0]["duration_s"]
    wall_h = sections / SECTIONS * dur / PARALLEL / 3600
    lines = [f"Corpus: {len(ok):,} act pages with an act ({len(blocks_rows) - len(ok)} pages of site chrome only), {blocks:,} blocks, {sections:,} sections, {tbytes:,} bytes of text; "
             f"{tbytes / sections:,.0f} bytes of text per section against {TEST_TEXT_BYTES / TEST_SECTIONS:,.0f} in the test set (scale {scale:.2f}).\n",
             "## Derived constants\n",
             f"- Lean agent's fixed context: median {fixed_lean:,.0f} tokens over the lean run's {sum(1 for r in cal if r['kind'] == 'fixed')} calls; this session's lean call {lean_fixed_this:,} tokens for {total_chars:,} characters ({chars_per_token:.2f} characters per token).",
             f"- Instruction files and memory index: {100 * claudemd_share:.0f}% of the lean agent's startup characters, so the fixed context without them is {fixed_d2:,.0f} tokens.",
             f"- The first-principles hook: {hook_chars:,} characters, about {hook_tokens:,.0f} tokens per call; over {sections / SECTIONS:,.0f} round-0 calls about {hook_tokens * sections / SECTIONS / 1e6:,.0f} million.",
             f"- Task text rate: {task_bpt:.2f} bytes per token ({len(reads)} reads); the instructions file {len(prompt_file.read_bytes()):,} bytes, about {instr:,.0f} tokens.",
             f"- Per section: task in form C {task_c:,.0f} tokens, answer in form B {ans_b:,.0f} tokens (step 3).",
             f"- Of the lean agent's first request, {100 * cl['D1'][0]['warm_share']:.0f}% ({warm_tok:,.0f} tokens: the system prompt and the tool schemas) was read from a sibling call's warm cache; the instruction files, the hook and the git status were written on every call. Without the instruction files the per-call written part is {per_call_fixed:,.0f} tokens.",
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
    lines += ["\n## Round 0: the four token classes per call, dollars at list price, duration\n",
              "| Driver | Uncached input | Cache write | Cache read | Output | Dollars per call | Cents per section | Dollars over the corpus | Duration per call, seconds |",
              "|---|---|---|---|---|---|---|---|---|"]
    for name, (c, n), per in (("Current: general-purpose, 3 sections per call", cl["D0"], 3), ("Lean as measured: labeller, 8 sections per call", cl["D1"], 8)):
        lines.append(f"| {name} ({n} calls measured) | {c['input']:,.0f} | {c['write']:,.0f} | {c['read']:,.0f} | {c['output']:,.0f} | {c['dollars']:.3f} | {100 * c['dollars'] / per * scale:.1f} | {c['dollars'] / per * scale * sections:,.0f} | {c['duration_s']:.0f} |")
    for name, c, d in (("Recommended, warm prefix (a sibling call warmed the system part within the cache lifetime)", d2_c, d2_d), ("Recommended, cold prefix (first call of a batch, or after a gap longer than the cache lifetime)", d2cold_c, d2cold_d)):
        lines.append(f"| {name} | {c['input']:,.0f} | {c['write']:,.0f} | {c['read']:,.0f} | {c['output']:,.0f} | {d:.3f} | {100 * d / SECTIONS * scale:.1f} | {d / SECTIONS * scale * sections:,.0f} | about {dur:.0f} (assumed as measured) |")
    lines += [f"\nWall time of round 0 at {PARALLEL} calls in flight: {sections / SECTIONS:,.0f} calls of about {dur:.0f} seconds, about {wall_h:,.0f} hours. "
              f"Calls launched back to back keep the five-minute subagent cache warm; a one-hour cache lifetime in the agent definition keeps it warm across the collect steps between batches. "
              f"The warm prefix saves only the system part ({warm_tok:,.0f} tokens per call): the difference between the two recommended rows.",
              "\n## The ladder over the whole corpus (rounds 1 and 2)\n",
              f"Round-1 targets at {100 * TARGET_SHARE_R1:.1f}% of blocks: {t1:,.0f}; round-2 targets at {100 * R2_SHARE:.0f}% of those: {t2:,.0f}.\n",
              "| Driver | Tasks per call | Calls | Tokens per task (context once) | Total, context once | Tokens per task, cost-weighted | Total, cost-weighted |",
              "|---|---|---|---|---|---|---|",
              f"| Lean as measured | 10 | {(t1 + t2) / 10:,.0f} | {m['L1'][0]:,.0f} | {m['L1'][0] * (t1 + t2) / 1e6:,.0f} million | {m['L1'][1]:,.0f} | {m['L1'][1] * (t1 + t2) / 1e6:,.0f} million |",
              f"| Recommended | {L2_TASKS} | {(t1 + t2) / L2_TASKS:,.0f} | {l2_once / L2_TASKS:,.0f} | {l2_once / L2_TASKS * (t1 + t2) / 1e6:,.0f} million | {l2_w / L2_TASKS:,.0f} | {l2_w / L2_TASKS * (t1 + t2) / 1e6:,.0f} million |",
              f"\nLadder dollars at list price: lean as measured {cl['L1'][0]['dollars'] / 10 * (t1 + t2):,.0f} ({100 * cl['L1'][0]['dollars'] / 10:.1f} cents per re-label, {cl['L1'][0]['duration_s']:.0f} seconds per call of 10); recommended {l2_d / L2_TASKS * (t1 + t2):,.0f} ({100 * l2_d / L2_TASKS:.1f} cents per re-label).",
              "\n## The two proposed measurements\n",
              f"- Sixteen sections per call: {m16_calls} calls of {m16_once:,.0f} tokens counted once ({m16_w:,.0f} cost-weighted, {m16_d:.2f} dollars at list price), about {m16_calls * m16_once:,.0f} tokens in all.",
              f"- The labeller inside a workflow, on the tiny and the known task of step 1: 2 calls, about {wf_once:,.0f} tokens in all at the lean agent's measured fixed context.",
              "\n## Assumptions\n",
              "- The recommended call makes two API requests: the prompt (instructions and sections inline) and the one Write of the answer file, then the one-line reply. Its system part is read from a sibling's cache when one has run within the cache lifetime; the hook, the git status and the prompt are written once; request 2 re-reads everything once.",
              "- The recommended call's duration is assumed equal to the lean call's measured median; it makes fewer requests but one long output.",
              "- Exception rates are the lean run's at 8 sections per call over the sixteen test-set acts, which include the hardest cases on purpose; the corpus at large is expected at or below them.",
              "- The reads of what survives round 2 are decided per batch and not estimated.",
              "- Thinking tokens are counted in the output of the measured rows; the estimate assumes the same share.",
              ]
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
