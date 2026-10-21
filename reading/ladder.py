"""The bounded exception ladder of decision D-069.

Round 0 labels every section. The checks turn failures into exceptions on
blocks. Round 1 re-labels each excepted block together with its previous and
next block; round 2 once more. What is still excepted after round 2 is the
residue for a whole-act read by a Fable model or the owner. The ladder only
prepares tasks and merges answers; the calls themselves are made by the run
driver (Claude Code subagents under the owner's plans).
"""
from __future__ import annotations

from .checks import run_all
from .labels import validate_entries
from .splitter import Block, SplitAct

MAX_ROUNDS = 2
NEIGHBOURS = 1


def round0_tasks(act: SplitAct) -> list[dict]:
    return [{"round": 0, "task": s.k, "target": None, "blocks": [_b(act.blocks[i]) for i in s.blocks]}
            for s in act.sections]


def _b(b: Block) -> dict:
    return {"i": b.i, "hint": b.hint, "text": b.text}


def merge(smap: dict[int, dict], answers: list[tuple[dict, list[dict]]]) -> tuple[dict[int, dict], list[dict]]:
    """Merge task answers into the map; later answers for a task's target override earlier ones."""
    problems: list[dict] = []
    for task, entries in answers:
        expected = [b["i"] for b in task["blocks"]]
        got, probs = validate_entries(entries, expected)
        problems.extend(probs)
        target = task.get("target")
        if target is None:
            smap.update(got)
        elif target in got:
            smap[target] = got[target]
        else:
            problems.append({"block": target, "kind": "missing_entry", "detail": "the target block was not labelled"})
    return smap, problems


def next_round_tasks(act: SplitAct, smap: dict[int, dict], exceptions: list[dict], rnd: int) -> list[dict]:
    tasks = []
    for k, i in enumerate(sorted({e["block"] for e in exceptions if e["block"] >= 0})):
        lo, hi = max(0, i - NEIGHBOURS), min(len(act.blocks) - 1, i + NEIGHBOURS)
        blocks = []
        for j in range(lo, hi + 1):
            d = _b(act.blocks[j])
            if j != i and j in smap:
                d["current_label"] = smap[j]["label"]
                d["current_n"] = smap[j].get("n")
            blocks.append(d)
        reasons = [e for e in exceptions if e["block"] == i]
        tasks.append({"round": rnd, "task": k, "target": i, "blocks": blocks,
                      "exceptions": reasons, "previous_label": smap.get(i, {}).get("label")})
    return tasks


def evaluate(act: SplitAct, smap: dict[int, dict], problems: list[dict]) -> tuple[str, list[dict]]:
    md, ex = run_all(act.blocks, smap)
    return md, problems + ex
