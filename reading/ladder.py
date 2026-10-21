"""The bounded exception ladder of decision D-069.

Round 0 labels every section. The checks turn failures into exceptions on
blocks. Round 1 re-labels each excepted block together with its previous and
next block; round 2 once more. What is still excepted after round 2 is the
residue for a whole-act read by a Fable model or the owner. The residue is
sorted by what another round could change: a block whose last two answers
agree is a reading the labeller holds and the checks refuse, so it needs a
rule, not a round; any other block is the labeller's doubt. The ladder only
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
SOURCE_FINDINGS = frozenset({"empty_section", "fragment", "article_gap", "sign_gap", "malformed_head"})


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


def classify_residue(residue: list[int], rounds: list[tuple[dict[int, dict], list[dict]]],
                     exceptions: list[dict]) -> list[dict]:
    """Sort the residue into ``rule_needed`` and ``labeller_unsure`` from each round's own answers.

    ``rounds`` holds, per round, the map of that round's answers alone and the validator's problems.
    A refused answer (a label or number the validator rejects) counts as an answer, so a number
    the grammar cannot read, given twice, is also a rule the checks lack.
    """
    out = []
    for i in residue:
        seq: list[list | None] = []
        for got, problems in rounds:
            if i in got:
                seq.append([got[i]["label"], got[i].get("n")])
            else:
                kinds = sorted({p["kind"] for p in problems if p.get("block") == i and p["kind"] in ("bad_label", "bad_number")})
                seq.append(["refused", ",".join(kinds)] if kinds else None)
        answered = [a for a in seq if a is not None]
        last = next((got[i] for got, _ in reversed(rounds) if i in got), {})
        out.append({"block": i,
                    "class": "rule_needed" if len(answered) >= 2 and answered[-1] == answered[-2] else "labeller_unsure",
                    "labels": seq, "kinds": sorted({e["kind"] for e in exceptions if e.get("block") == i}),
                    "note": last.get("note", "")})
    return out
