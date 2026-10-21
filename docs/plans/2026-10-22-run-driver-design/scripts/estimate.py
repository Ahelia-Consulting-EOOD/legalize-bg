"""The full-corpus estimate: tokens and calls for the audit of every act under three drivers.

Every input is a named constant with its source. Per-section figures are scaled by the ratio of text bytes per
section in the corpus to the test set (the token cost of a section follows its text). Two accountings are
given: the harness figure (the context counted once, as the task notifications show it) and the cost-weighted
figure (every API request's cache writes at 1.25, cache reads at 0.1 and output at 5, relative to one
uncached input token, from the Claude Opus 5.5 list prices).

Usage: python3 estimate.py CORPUS_BLOCKS.csv OUT.md
"""
import csv, sys
from pathlib import Path

# corpus (corpus_blocks.py over the raw store, 21 October 2026)
# test set (step 2 and step 3 over the run data)
TEST_BYTES_PER_SECTION = 11_133_685 / 1_236
# measured per-section figures, round 0 (step 1 requests.md and step 2 density.md)
D0 = {"name": "Current driver: general-purpose subagent, 3 sections per call", "per_call": 3, "once": 28_990, "weighted": 42_818, "source": "84 calls of the night of 21 to 22 October"}
D1 = {"name": "Lean driver as measured: labeller, 8 sections per call, one Read and one Write per task", "per_call": 8, "once": 7_676, "weighted": 20_557, "source": "96 calls of 22 October"}
# recommended design: labeller without CLAUDE.md files, cache kept warm, instructions and 8 tasks inline (encoding C),
# one compact answer file per call (encoding B), two API requests per call
FIXED_LEAN = 14_469          # median first-request tokens of the lean run (calibration.csv, 166 calls)
CLAUDEMD_SHARE = 0.67        # CLAUDE.md files and memory index: 30,988 of 46,200 characters of the lean agent's startup context (step 1)
FIXED_D2 = int(FIXED_LEAN * (1 - CLAUDEMD_SHARE))
INSTR = 1_225                # the labelling instructions, 4,208 characters at 3.44 bytes per token
TASK_C = 2_888               # encoding C per section (step 3)
ANS_B = 698                  # encoding B per section (step 3)
SECTIONS = 8


def d2_call(sections=SECTIONS):
    prompt = INSTR + sections * TASK_C
    out = sections * ANS_B
    written = prompt + 300                              # prompt and the Write tool result; the fixed prefix is read, not written, once warm
    read = FIXED_D2 + (FIXED_D2 + prompt + out)         # request 1 reads the warm prefix; request 2 re-reads everything
    once = FIXED_D2 + prompt + out
    weighted = written * 1.25 + read * 0.1 + out * 5
    return once, weighted


# the ladder (step 4): targets as a share of blocks, and per-task costs
TARGET_SHARE_R1 = 0.015      # lean run: 0.9 exceptions per 100 blocks at 8 sections, up to 1.8 on the hardest acts; 1.5 assumed
R2_SHARE = 0.19              # share of round-1 targets still excepted after round 1 (579 targets)
L1 = {"once": 3_178, "weighted": 8_142, "per_call": 10}            # lean, 10 tasks per call, measured
L2_TASKS = 25
L2_TASK_TOKENS = 1_511 / 3.44 + 60                                  # a round-1 task file at the Read rate, plus framing
L2_ANS = 60


def l2_call(tasks=L2_TASKS):
    prompt = INSTR + tasks * L2_TASK_TOKENS
    out = tasks * L2_ANS
    once = FIXED_D2 + prompt + out
    weighted = (prompt + 300) * 1.25 + (FIXED_D2 + FIXED_D2 + prompt + out) * 0.1 + out * 5
    return once, weighted


def main():
    rows = list(csv.DictReader(open(sys.argv[1], encoding="utf-8")))
    ok = [r for r in rows if r["spine"] == "1"]
    blocks = sum(int(r["blocks"]) for r in ok); sections = sum(int(r["sections"]) for r in ok); tbytes = sum(int(r["bytes"]) for r in ok)
    scale = (tbytes / sections) / TEST_BYTES_PER_SECTION
    once2, w2 = d2_call()
    designs = [
        (D0["name"], sections / D0["per_call"], D0["once"] * scale, D0["weighted"] * scale, D0["source"]),
        (D1["name"], sections / D1["per_call"], D1["once"] * scale, D1["weighted"] * scale, D1["source"]),
        ("Recommended: labeller without CLAUDE.md, warm cache, 8 sections inline, one compact answer file, 2 requests per call", sections / SECTIONS, once2 / SECTIONS * scale, w2 / SECTIONS * scale, "estimate from the measured parts (step 1, step 3)"),
    ]
    lines = [f"Corpus: {len(ok):,} act pages with an act ({len(rows) - len(ok)} pages of site chrome only), {blocks:,} blocks, {sections:,} sections, {tbytes:,} bytes of text; "
             f"{tbytes / sections:,.0f} bytes of text per section against {TEST_BYTES_PER_SECTION:,.0f} in the test set (scale {scale:.2f}).\n",
             "## Round 0 over the whole corpus\n",
             "| Driver | Calls | Tokens per section (context once) | Total, context once | Tokens per section, cost-weighted | Total, cost-weighted | Basis |",
             "|---|---|---|---|---|---|---|"]
    for name, calls, once, w, src in designs:
        lines.append(f"| {name} | {calls:,.0f} | {once:,.0f} | {once * sections / 1e6:,.0f} million | {w:,.0f} | {w * sections / 1e6:,.0f} million | {src} |")
    t1 = blocks * TARGET_SHARE_R1; t2 = t1 * R2_SHARE
    o1, w1 = l2_call()
    lines += ["\n## The ladder over the whole corpus (rounds 1 and 2)\n",
              f"Round-1 targets at {100 * TARGET_SHARE_R1:.1f}% of blocks: {t1:,.0f}; round-2 targets at {100 * R2_SHARE:.0f}% of those: {t2:,.0f}.\n",
              "| Driver | Tasks per call | Calls | Tokens per task (context once) | Total, context once | Tokens per task, cost-weighted | Total, cost-weighted |",
              "|---|---|---|---|---|---|---|",
              f"| Lean as measured | {L1['per_call']} | {(t1 + t2) / L1['per_call']:,.0f} | {L1['once']:,} | {L1['once'] * (t1 + t2) / 1e6:,.0f} million | {L1['weighted']:,} | {L1['weighted'] * (t1 + t2) / 1e6:,.0f} million |",
              f"| Recommended | {L2_TASKS} | {(t1 + t2) / L2_TASKS:,.0f} | {o1 / L2_TASKS:,.0f} | {o1 / L2_TASKS * (t1 + t2) / 1e6:,.0f} million | {w1 / L2_TASKS:,.0f} | {w1 / L2_TASKS * (t1 + t2) / 1e6:,.0f} million |",
              "\n## Assumptions\n",
              f"- The recommended call: fixed context {FIXED_D2:,} tokens (the lean agent's {FIXED_LEAN:,} less the {100 * CLAUDEMD_SHARE:.0f}% that the CLAUDE.md files and the memory index take), instructions {INSTR:,}, {SECTIONS} sections of {TASK_C:,} tokens inline, answers {ANS_B} tokens per section, two API requests; the fixed prefix is read from the cache, not written, because the cache is kept warm for an hour and the first call of a batch warms it.",
              f"- Per call, the recommended design is {once2:,.0f} tokens counted once and {w2:,.0f} cost-weighted; the lean driver as measured is 61,414 and 164,461.",
              f"- The ladder's recommended call: {L2_TASKS} tasks of {L2_TASK_TOKENS:,.0f} tokens inline, {L2_ANS} output tokens per task, two requests: {o1:,.0f} tokens counted once, {w1:,.0f} cost-weighted.",
              "- Exception rates are the lean run's at 8 sections per call over the sixteen test-set acts, which include the hardest cases on purpose; the corpus at large is expected at or below them.",
              "- The whole-act reads of the residue (what survives round 2) are not estimated: they are the owner's reads or a Fable read per act, decided per batch.",
              "- Thinking tokens are counted in the output of the measured rows; the estimate assumes the same share.",
              ]
    Path(sys.argv[2]).write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
