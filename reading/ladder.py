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
# exceptions that describe the source, not a label: recorded as findings, never re-labelled
SOURCE_FINDINGS = frozenset({"empty_section", "fragment", "article_gap", "sign_gap"})


def _context(act: SplitAct, first: int) -> list[str]:
    """The last three heading-hinted blocks before ``first``: orientation for a section cut inside a chapter or annex."""
    from .splitter import HEADING_HINTS
    out = [b.text for b in act.blocks[:first]
           if b.hint in HEADING_HINTS or b.text.startswith("Приложение") or b.text.startswith(("Чл. ", "§ "))]
    # the last three headings or annex lines, plus the last article or § opened before the section
    heads = [t for t in out if not t.startswith(("Чл. ", "§ "))][-3:]
    opener = [t for t in out if t.startswith(("Чл. ", "§ "))][-1:]
    return heads + [t[:120] for t in opener]


def round0_tasks(act: SplitAct) -> list[dict]:
    return [{"round": 0, "task": s.k, "target": None, "context": _context(act, s.blocks[0]),
             "blocks": [_b(act.blocks[i]) for i in s.blocks]} for s in act.sections]


def _b(b: Block) -> dict:
    return {"i": b.i, "hint": b.hint, "text": b.text}


def merge(smap: dict[int, dict], answers: list[tuple[dict, list[dict]]]) -> tuple[dict[int, dict], list[dict]]:
    """Merge task answers into the map; a targeted task changes only its target block."""
    problems: list[dict] = []
    for task, entries in answers:
        expected = [b["i"] for b in task["blocks"]]
        target = task.get("target")
        got, probs = validate_entries(entries, expected, target=target)
        problems.extend(probs)
        if target is None:
            smap.update(got)
        elif target in got:
            smap[target] = got[target]
    return smap, problems


def next_round_tasks(act: SplitAct, smap: dict[int, dict], exceptions: list[dict], rnd: int) -> list[dict]:
    tasks = []
    n_blocks = len(act.blocks)
    targets = sorted({e["block"] for e in exceptions
                      if isinstance(e.get("block"), int) and 0 <= e["block"] < n_blocks and e["kind"] not in SOURCE_FINDINGS})
    for k, i in enumerate(targets):
        lo, hi = max(0, i - NEIGHBOURS), min(len(act.blocks) - 1, i + NEIGHBOURS)
        blocks = []
        for j in range(lo, hi + 1):
            d = _b(act.blocks[j])
            if j != i and j in smap:
                d["current_label"] = smap[j]["label"]
                d["current_n"] = smap[j].get("n")
            blocks.append(d)
        reasons = [e for e in exceptions if e["block"] == i and e["kind"] not in SOURCE_FINDINGS]
        tasks.append({"round": rnd, "task": k, "target": i, "context": _context(act, lo), "blocks": blocks,
                      "exceptions": reasons, "previous_label": smap.get(i, {}).get("label")})
    return tasks


def evaluate(act: SplitAct, smap: dict[int, dict], problems: list[dict]) -> tuple[str, list[dict]]:
    md, ex = run_all(act.blocks, smap)
    return md, problems + ex
