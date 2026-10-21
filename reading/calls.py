"""Call files and answer files of the run driver (plan step 6, decision D-070 of 21 October 2026).

A *call* is one subagent run of the ``labeller`` agent. It reads one call file, writes one answer file
and replies with one line, so a call is three API requests whatever the number of tasks it carries.

The call file is plain text, one line per block, tab-separated (form C of the design study): it is the
same content as the task files, without their JSON scaffolding, so the model reads about a quarter fewer
tokens per section. The answer file is one JSON object keyed by task number, with compact entries (form
B): ``i`` and ``l`` always, ``n`` only on numbered labels, ``c`` only when low, ``note`` only with low
confidence, ``drop`` or ``unknown``. Nothing the checks read is lost: ``decode_entries`` turns a compact
entry into the long form that ``labels.validate_entries`` reads, and the long form is still accepted.

The wording of the act is never taken from a call file: the assembler copies it from ``blocks.json``.
A tab inside a block's text is written as a space in the call file, which changes nothing the model
judges.
"""
from __future__ import annotations

import json
import re

TASK_HEAD = re.compile(r"^## task (\d{4,})$")
SET_HEAD = re.compile(r"^# task set: ([0-9a-f]{12})$")
CALL_NAME = re.compile(r"([0-9a-f]{12})-(\d{4,})-(\d{4,})")   # <task set>-<first task>-<last task>: the stem of a call file and of its answer file
KEY = re.compile(r"\s*(?:task\s*)?(\d+)\s*", re.ASCII)
SHORT_KEYS = {"l": "label", "c": "conf"}


def encode_tasks(tasks: list[dict], task_set: str | None = None) -> str:
    """The call file text for a list of task dicts (the same dicts ``ladder`` writes as JSON).

    ``task_set`` is the id of the round's task set (``task_set_id``); the split refuses an answer whose call
    file names another set, so an answer to a task set that a re-collect replaced is never filed under the new
    tasks of the same numbers.
    """
    out: list[str] = []
    if task_set:
        out.append(f"# task set: {task_set}")
    for t in tasks:
        out.append(f"## task {t['task']:04d}")
        if t.get("target") is not None:
            out.append(f"# target: {t['target']}")
            if t.get("previous_label"):
                out.append(f"# previous label of the target: {t['previous_label']}")
            for e in t.get("exceptions", []):
                out.append(f"# exception on the target: {e.get('kind', '?')}: {_one_line(e.get('detail', ''))}")
        for c in t.get("context", []):
            out.append(f"# context: {_one_line(c)}")
        out.append("# i\thint\ttext" + ("\tcurrent label" if t.get("target") is not None else ""))
        for b in t["blocks"]:
            line = f"{b['i']}\t{b['hint']}\t{_one_line(b['text'])}"
            if t.get("target") is not None and b["i"] != t["target"]:
                cur = b.get("current_label") or ""
                if cur and b.get("current_n"):
                    cur += f" {b['current_n']}"
                line += f"\t{cur}"
            out.append(line)
        out.append("")
    return "\n".join(out)


def _one_line(s: str) -> str:
    return " ".join(str(s).replace("\t", " ").splitlines())


def task_names(call_text: str) -> list[str]:
    return [m.group(1) for line in call_text.splitlines() if (m := TASK_HEAD.match(line))]


def task_set_of(call_text: str) -> str | None:
    for line in call_text.splitlines()[:2]:
        m = SET_HEAD.match(line)
        if m:
            return m.group(1)
    return None


def task_set_id(task_files: list) -> str:
    """A short hash of a round's task files (names and contents), the identity of the task set."""
    import hashlib
    h = hashlib.sha256()
    for f in sorted(task_files, key=lambda f: f.name):
        h.update(f.name.encode()); h.update(b"\0"); h.update(f.read_bytes()); h.update(b"\0")
    return h.hexdigest()[:12]


def decode_entries(entries) -> list:
    """Compact or long entries to the long form the validator reads; a non-list is returned as is."""
    if not isinstance(entries, list):
        return entries
    out = []
    for e in entries:
        if not isinstance(e, dict):
            out.append(e)
            continue
        d = {}
        for k, v in e.items():
            d[SHORT_KEYS.get(k, k)] = v
        d.setdefault("conf", "high")
        out.append(d)
    return out


def decode_answer_file(text: str, expected_tasks: list[str]) -> dict[str, object]:
    """The per-task answers of an answer file.

    The file is a JSON object keyed by task number (``"0003"`` or ``3``), each value an array of entries.
    A bare array is accepted for a call of one task. A task without a key, or a file that does not parse,
    yields a value that is not a list, which the validator turns into exceptions on the task's blocks.
    """
    text = text.strip()
    text = re.sub(r"^```(?:json)?|```$", "", text, flags=re.M).strip()
    try:
        obj = json.loads(text)
    except json.JSONDecodeError as exc:
        return {t: f"unparsable answer file: {exc}" for t in expected_tasks}
    if isinstance(obj, list):
        if len(expected_tasks) == 1:
            return {expected_tasks[0]: decode_entries(obj)}
        return {t: "the answer file is one array, but the call had several tasks" for t in expected_tasks}
    if not isinstance(obj, dict):
        return {t: "the answer file is neither an object nor an array" for t in expected_tasks}
    found: dict[str, object] = {}
    by_int = {int(t): t for t in expected_tasks if t.isdigit()}
    for k, v in obj.items():
        m = KEY.fullmatch(str(k))
        name = by_int.get(int(m.group(1)), str(k)) if m else str(k)
        found[name] = decode_entries(v)
    return {t: found.get(t, f"no answer for task {t} in the answer file") for t in expected_tasks}


DISPATCH_PROMPT = (
    "Read {call_file} (the call file: one or more tasks, one line per block). Label every block of every task "
    "as your instructions say, and write the answers with the Write tool to {answer_file} as one JSON object "
    "keyed by task number, nothing else. Read no other file. Reply with one line: the task numbers answered."
)
