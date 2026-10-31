"""The witnesses: an act's assembled body against the lex.bg page text and the Ministry of Justice portal's text
(step S1 of the plan of 31 October 2026, item 4; decision D-061: witnesses are compared with, never trusted).

The comparison is mechanical. Each witness page is cut into blocks by the lex.bg splitter (the portal's markup
carries lex.bg's classes), the page's known chrome is left out, and every line of both sides is normalised by the
rules in ``NORMALISATION`` (whitespace, quotation marks, dashes, the dot that closes a heading number line), so
that a difference of form alone does not reach the settler. The two sides are then compared token by token
(``difflib``), and each run of differing tokens is one *difference*: our tokens, the witness's tokens, the text
around them, and where it lies in our body. The differences go to ``witness-diff.json`` in the act's run folder.

Whether a difference is the source's error, the witness's error, a timing difference (the witness has or lacks an
amendment) or the same text in another form is a reading of free text: the ``settler`` agent reads the task the
driver writes (``witness-task.md``) and answers ``witness-answer.json`` with one verdict per difference from
``VERDICTS``. ``record`` loads the answer, refuses a verdict outside the closed set or a difference left
unsettled, and writes ``witness-record.json`` beside the act's run record, which the write path commits with it.
Nothing here writes a corpus file or calls a model.
"""
from __future__ import annotations

import difflib
import hashlib
import json
import re
from pathlib import Path

from .assembler import strip_line
from .checks import START_CHROME, TAIL_STARTS
from .splitter import split_lexbg

VERDICTS: dict[str, str] = {
    "source_error": "the source's text is wrong here (a misprint in the Gazette, for example); our body keeps it, the record names it",
    "witness_error": "the witness's text is wrong here; lex.bg or the portal, not the source",
    "timing": "the witness carries an amendment, or lacks one, that the source text does not yet or no longer reflects",
    "same_text_other_form": "the same text in another form (a numbering style, a line break, a character the normalisation does not cover)",
}
NORMALISATION = (
    "whitespace runs become one space; leading and trailing whitespace is removed",
    "quotation marks „ “ ” « » ' are all written as \"",
    "the dashes – and — are written as -",
    "the dot that closes a heading number line (Глава първа., Раздел I.) is removed",
    "nothing else: a Latin letter for a Cyrillic one, a missing word, a different number are differences",
)
_QUOTES = str.maketrans({"„": '"', "“": '"', "”": '"', "«": '"', "»": '"', "'": '"', "–": "-", "—": "-", " ": " "})
_WS = re.compile(r"\s+")
# the dot after a heading number, at the start of a line: "Глава първа." alone (a lex.bg block) or "Глава първа. ОБЩИ ПОЛОЖЕНИЯ" (our joined line)
_HEADING_DOT = re.compile(r"^((?:Част|Дял|Глава|Раздел|Подраздел)\s+[\wIVXLC]+(?:\s+[а-я]+){0,3}(?:\s*\"[а-я]\")?)\.(?=\s|$)")
CONTEXT = 6


def normalise_line(line: str) -> str:
    t = _WS.sub(" ", line.translate(_QUOTES)).strip()
    return _HEADING_DOT.sub(r"\1", t)


def body_lines(markdown: str) -> list[str]:
    """Our body as lines of plain text: the assembler's markers removed, one line per provision line."""
    return [normalise_line(strip_line(l)) for l in markdown.split("\n") if l.strip()]


def witness_lines(raw_page: bytes) -> tuple[list[str], dict]:
    """A witness page's act text as lines: the page split into blocks, its known chrome before and after the act left out."""
    act = split_lexbg(raw_page)
    texts = [b.text for b in act.blocks]
    start = 0
    while start < len(texts) and START_CHROME.match(texts[start]):
        start += 1
    end = next((k for k, t in enumerate(texts) if t in TAIL_STARTS and k > start), len(texts))
    lines = [normalise_line(t) for t in texts[start:end] if t.strip()]
    return lines, {"blocks": len(texts), "chrome_before": start, "chrome_after": len(texts) - end, "has_spine": act.has_spine}


def _tokens(lines: list[str]) -> tuple[list[str], list[int]]:
    toks, owner = [], []
    for k, l in enumerate(lines):
        for t in l.split(" "):
            if t:
                toks.append(t)
                owner.append(k)
    return toks, owner


def compare(ours: list[str], theirs: list[str]) -> list[dict]:
    """The differences between two line lists, token by token, each with its context and its line in our body."""
    a, a_line = _tokens(ours)
    b, b_line = _tokens(theirs)
    sm = difflib.SequenceMatcher(a=a, b=b, autojunk=False)
    out: list[dict] = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            continue
        out.append({
            "n": len(out) + 1,
            "kind": tag,
            "ours": " ".join(a[i1:i2]),
            "witness": " ".join(b[j1:j2]),
            "before": " ".join(a[max(0, i1 - CONTEXT):i1]),
            "after": " ".join(a[i2:i2 + CONTEXT]),
            "our_line": a_line[i1] if i1 < len(a_line) else (a_line[-1] if a_line else 0),
            "witness_line": b_line[j1] if j1 < len(b_line) else (b_line[-1] if b_line else 0),
        })
    return out


def diff_witness(name: str, ours: list[str], raw_page: bytes, page_sha256: str, fetched_at: str) -> dict:
    theirs, shape = witness_lines(raw_page)
    diffs = compare(ours, theirs)
    return {"witness": name, "page_sha256": page_sha256, "fetched_at": fetched_at, "page": shape,
            "our_lines": len(ours), "witness_lines": len(theirs), "differences": diffs, "count": len(diffs)}


def write_diff(run_dir: Path, body_markdown: str, witnesses: list[dict]) -> Path:
    """``witnesses``: [{name, raw, page_sha256, fetched_at}] or [{name, absent: <why>}] per witness; writes witness-diff.json."""
    ours = body_lines(body_markdown)
    out = {"normalisation": list(NORMALISATION), "our_lines": len(ours), "witnesses": []}
    for w in witnesses:
        if w.get("absent"):
            out["witnesses"].append({"witness": w["name"], "absent": w["absent"], "count": 0, "differences": []})
        else:
            out["witnesses"].append(diff_witness(w["name"], ours, w["raw"], w["page_sha256"], w["fetched_at"]))
    p = run_dir / "witness-diff.json"
    p.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    return p


def task_text(diff: dict, slug: str, answer_path: Path) -> str:
    """The settler's task: every difference of every witness, numbered, and the answer form."""
    lines = [f"# Witness differences of {slug}", "",
             "Settle every difference below: for each, one verdict from the closed set, and a short evidence note naming what you relied on.",
             "The source is the text the act was read from (the Gazette material); the witness is lex.bg or the Ministry of Justice portal.",
             "Verdicts: " + "; ".join(f"`{k}`: {v}" for k, v in VERDICTS.items()) + ".",
             "Both sides were normalised before the comparison: " + "; ".join(NORMALISATION) + ".",
             f"Write exactly one JSON object to `{answer_path}`: one key per witness name, its value an object keyed by the difference number as a string, "
             'each value `{"verdict": "<one of the four>", "note": "<short evidence note>"}`. Nothing else: no prose, no code fence.', ""]
    for w in diff["witnesses"]:
        lines.append(f"## witness {w['witness']}")
        if w.get("absent"):
            lines.append(f"(absent: {w['absent']}; nothing to settle)")
            lines.append("")
            continue
        lines.append(f"{w['count']} difference(s); our body {w['our_lines']} lines, the witness {w['witness_lines']} lines")
        for d in w["differences"]:
            lines.append(f"### {d['n']} ({d['kind']}, our line {d['our_line']}, witness line {d['witness_line']})")
            lines.append(f"- ours: `{d['ours']}`")
            lines.append(f"- witness: `{d['witness']}`")
            lines.append(f"- around: `{d['before']} [...] {d['after']}`")
        lines.append("")
    return "\n".join(lines)


def record(run_dir: Path, answer: dict | None = None) -> Path:
    """Load the settler's answer against the diff, refuse what is outside the form, write witness-record.json."""
    diff = json.loads((run_dir / "witness-diff.json").read_text(encoding="utf-8"))
    if answer is None:
        answer = json.loads((run_dir / "witness-answer.json").read_text(encoding="utf-8"))
    if not isinstance(answer, dict):
        raise ValueError("the settler's answer is not a JSON object")
    rec = {"normalisation": diff["normalisation"], "witnesses": []}
    problems: list[str] = []
    for w in diff["witnesses"]:
        name = w["witness"]
        if w.get("absent"):
            rec["witnesses"].append({"witness": name, "absent": w["absent"], "differences": 0, "verdicts": {}})
            continue
        got = answer.get(name)
        if not isinstance(got, dict):
            problems.append(f"{name}: no answer object")
            got = {}
        verdicts: dict[str, dict] = {}
        for d in w["differences"]:
            v = got.get(str(d["n"]))
            if not isinstance(v, dict) or v.get("verdict") not in VERDICTS:
                problems.append(f"{name}: difference {d['n']} has no verdict from {sorted(VERDICTS)}")
                continue
            verdicts[str(d["n"])] = {"verdict": v["verdict"], "note": str(v.get("note", "")), "ours": d["ours"], "witness": d["witness"], "our_line": d["our_line"]}
        counts: dict[str, int] = {}
        for v in verdicts.values():
            counts[v["verdict"]] = counts.get(v["verdict"], 0) + 1
        rec["witnesses"].append({"witness": name, "page_sha256": w["page_sha256"], "fetched_at": w["fetched_at"],
                                 "differences": w["count"], "verdicts": verdicts, "counts": counts})
    if problems:
        raise ValueError("the settler's answer does not settle every difference: " + "; ".join(problems))
    rec["diff_sha256"] = hashlib.sha256((run_dir / "witness-diff.json").read_bytes()).hexdigest()
    p = run_dir / "witness-record.json"
    p.write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")
    return p


def summary(run_dir: Path) -> str:
    rec = json.loads((run_dir / "witness-record.json").read_text(encoding="utf-8"))
    out = []
    for w in rec["witnesses"]:
        if w.get("absent"):
            out.append(f"{w['witness']}: absent ({w['absent']})")
        else:
            out.append(f"{w['witness']}: {w['differences']} difference(s), settled " + ", ".join(f"{k} {v}" for k, v in sorted(w["counts"].items())))
    return "; ".join(out)
