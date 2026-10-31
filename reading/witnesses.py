"""The witnesses: an act's assembled body against the lex.bg page text and the Ministry of Justice portal's text
(step S1 of the plan of 31 October 2026, item 4; decision D-061: witnesses are compared with, never trusted).

The comparison is mechanical and at the block level. Each witness page is cut into blocks by the lex.bg splitter
(the portal's markup carries lex.bg's classes), the page's known chrome is left out, a heading number line is
joined to its title line as the assembler joins ours, and every line of both sides is normalised by the rules in
``NORMALISATION`` (whitespace, quotation marks, dashes, the dot that closes a heading number). The two sides are
then compared line by line (``difflib``): a line the witness has and we lack, or we have and the witness lacks,
is one *difference*; a run of lines that differ is compared word by word inside, each run of differing words one
difference, and a run whose words are equal but whose line boundaries differ is a *structure* difference (an
alinea joined or split). Each difference carries our text, the witness's, the text around it and the lines on
both sides. The differences go to ``witness-diff.json`` in the act's run folder, with the file's own SHA-256.

Whether a difference is the source's error, the witness's error, a timing difference or our own reading's error
is a reading of free text: the ``settler`` agent reads the task the driver writes (``witness-task.md``) and
answers ``witness-answer.json`` with one verdict per difference from ``VERDICTS`` and the diff's hash it answered.
``record`` refuses an answer for another diff, a verdict outside the closed set, a difference left unsettled or a
difference the diff does not have, and writes ``witness-record.json`` beside the act's run record, which the write
path commits with the act. A ``reading_error`` verdict says our body is wrong: the witness step stops on it.
Nothing here writes a corpus file or calls a model.

The plan names three verdicts (the source's error, the witness's error, a timing difference); the fourth and the
fifth are this session's additions, recorded here: lex.bg's own editorial lines (an in-force note, a separator)
are the same text in another form, and a wrong split or label of ours must be nameable and must stop the write.
"""
from __future__ import annotations

import difflib
import hashlib
import json
import re
from pathlib import Path

from .assembler import NUMBER_LINE, strip_line
from .checks import START_CHROME, TAIL_STARTS, _PROVISION_LIKE
from .splitter import split_lexbg

VERDICTS: dict[str, str] = {
    "source_error": "the source's text is wrong here (a misprint in the Gazette, for example); our body keeps it, the record names it",
    "witness_error": "the witness's text is wrong here; lex.bg or the portal, not the source",
    "timing": "the witness carries an amendment, or lacks one, that the source text does not yet or no longer reflect",
    "same_text_other_form": "the same text in another form: a line the witness adds that is not the act's (an editorial note, a separator), a numbering style, a character the normalisation does not cover",
    "reading_error": "our body is wrong here: the split, a label or a join of ours lost or moved text; the write stops",
}
STOPPING = frozenset({"reading_error"})
NORMALISATION = (
    "whitespace runs become one space; leading and trailing whitespace is removed",
    "quotation marks „ “ ” « » ' are all written as \"",
    "the dashes – and — are written as -",
    "the dot that closes a heading number (Глава първа., Раздел I.) is removed, and a heading number line is joined to its title line",
    "nothing else: a Latin letter for a Cyrillic one, a missing word, a different number, a line joined or split are differences",
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
    """A witness page's act text as lines: the page's blocks, its known chrome left out, heading numbers joined to their titles."""
    act = split_lexbg(raw_page)
    texts = [b.text for b in act.blocks]
    start = 0
    while start < len(texts) and START_CHROME.match(texts[start]):
        start += 1
    end = next((k for k, t in enumerate(texts) if t in TAIL_STARTS and k > start), len(texts))
    lines: list[str] = []
    for t in texts[start:end]:
        if not t.strip():
            continue
        if lines and NUMBER_LINE.match(lines[-1].rstrip()) and not _PROVISION_LIKE.match(t) and not NUMBER_LINE.match(t.strip()):
            lines[-1] = f"{lines[-1]} {t}"
        else:
            lines.append(t)
    return [normalise_line(l) for l in lines], {"blocks": len(texts), "chrome_before": start, "chrome_after": len(texts) - end, "has_spine": act.has_spine}


def _words(lines: list[str]) -> list[str]:
    return [w for l in lines for w in l.split(" ") if w]


def compare(ours: list[str], theirs: list[str]) -> list[dict]:
    """The differences between two line lists: lines first, then the words inside a run of differing lines."""
    out: list[dict] = []

    def add(kind: str, mine: str, witness: str, i: int, j: int, before: str = "", after: str = "") -> None:
        out.append({"n": len(out) + 1, "kind": kind, "ours": mine, "witness": witness, "before": before, "after": after,
                    "our_line": i, "witness_line": j})

    sm = difflib.SequenceMatcher(a=ours, b=theirs, autojunk=False)
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            continue
        if tag == "insert":
            for j in range(j1, j2):
                add("witness_line", "", theirs[j], i1, j, ours[i1 - 1] if i1 else "", ours[i1] if i1 < len(ours) else "")
            continue
        if tag == "delete":
            for i in range(i1, i2):
                add("our_line", ours[i], "", i, j1, ours[i - 1] if i else "", ours[i + 1] if i + 1 < len(ours) else "")
            continue
        a, b = _words(ours[i1:i2]), _words(theirs[j1:j2])
        inner = difflib.SequenceMatcher(a=a, b=b, autojunk=False)
        found = False
        for t2, p1, p2, q1, q2 in inner.get_opcodes():
            if t2 == "equal":
                continue
            found = True
            add(t2, " ".join(a[p1:p2]), " ".join(b[q1:q2]), i1 + _line_of(ours[i1:i2], p1), j1 + _line_of(theirs[j1:j2], q1),
                " ".join(a[max(0, p1 - CONTEXT):p1]), " ".join(a[p2:p2 + CONTEXT]))
        if not found or (i2 - i1) != (j2 - j1):
            add("structure", " | ".join(ours[i1:i2]), " | ".join(theirs[j1:j2]), i1, j1,
                "", f"{i2 - i1} line(s) of ours against {j2 - j1} of the witness, the same words")
    return out


def _line_of(lines: list[str], word_index: int) -> int:
    """The line (within ``lines``) that holds the word at ``word_index`` of their joined words."""
    seen = 0
    for k, l in enumerate(lines):
        n = len([w for w in l.split(" ") if w])
        if word_index < seen + n:
            return k
        seen += n
    return max(0, len(lines) - 1)


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
    body = json.dumps(out, ensure_ascii=False, indent=1)
    p = run_dir / "witness-diff.json"
    p.write_text(body, encoding="utf-8")
    return p


def diff_sha256(run_dir: Path) -> str:
    return hashlib.sha256((run_dir / "witness-diff.json").read_bytes()).hexdigest()


def task_text(diff: dict, slug: str, answer_path: Path, sha256: str) -> str:
    """The settler's task: every difference of every witness, numbered, the diff's hash and the answer form."""
    lines = [f"# Witness differences of {slug}", "",
             "Settle every difference below: for each, one verdict from the closed set, and a short evidence note naming what you relied on.",
             "The source is the text the act was read from (the Gazette material); the witness is lex.bg or the Ministry of Justice portal. "
             "Our body is the source's text as we read it, so a difference can also be our own reading's error.",
             "Verdicts: " + "; ".join(f"`{k}`: {v}" for k, v in VERDICTS.items()) + ".",
             "Both sides were normalised before the comparison: " + "; ".join(NORMALISATION) + ".",
             f"Write exactly one JSON object to `{answer_path}`: its first key `\"diff_sha256\"` with the value `\"{sha256}\"` (the hash of the "
             "diff you are answering), then one key per witness name, its value an object keyed by the difference number as a string, "
             'each value `{"verdict": "<one of the five>", "note": "<short evidence note>"}`. Nothing else: no prose, no code fence.', ""]
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
            if d["before"] or d["after"]:
                lines.append(f"- around: `{d['before']} [...] {d['after']}`")
        lines.append("")
    return "\n".join(lines)


def record(run_dir: Path, answer: dict | None = None) -> Path:
    """Load the settler's answer against the diff, refuse what is outside the form, write witness-record.json."""
    diff = json.loads((run_dir / "witness-diff.json").read_text(encoding="utf-8"))
    sha = diff_sha256(run_dir)
    if answer is None:
        answer = json.loads((run_dir / "witness-answer.json").read_text(encoding="utf-8"))
    if not isinstance(answer, dict):
        raise ValueError("the settler's answer is not a JSON object")
    problems: list[str] = []
    answered_for = answer.get("diff_sha256")
    if sum(w["count"] for w in diff["witnesses"]) and answered_for != sha:
        raise ValueError(f"the settler's answer is for another diff ({str(answered_for)[:12]}, this one is {sha[:12]}); it is not applied")
    names = {w["witness"] for w in diff["witnesses"]}
    for key in answer:
        if key != "diff_sha256" and key not in names:
            problems.append(f"{key}: not a witness of this diff")
    rec = {"normalisation": diff["normalisation"], "witnesses": []}
    for w in diff["witnesses"]:
        name = w["witness"]
        if w.get("absent"):
            rec["witnesses"].append({"witness": name, "absent": w["absent"], "differences": 0, "verdicts": {}})
            if name in answer and answer[name]:
                problems.append(f"{name}: absent, nothing to settle, yet answered")
            continue
        got = answer.get(name)
        if not isinstance(got, dict):
            problems.append(f"{name}: no answer object")
            got = {}
        numbers = {str(d["n"]) for d in w["differences"]}
        for key in got:
            if key not in numbers:
                problems.append(f"{name}: difference {key} is not in the diff")
        verdicts: dict[str, dict] = {}
        for d in w["differences"]:
            v = got.get(str(d["n"]))
            if not isinstance(v, dict) or v.get("verdict") not in VERDICTS:
                problems.append(f"{name}: difference {d['n']} has no verdict from {sorted(VERDICTS)}")
                continue
            if set(v) - {"verdict", "note"}:
                problems.append(f"{name}: difference {d['n']} carries keys outside the form: {sorted(set(v) - {'verdict', 'note'})}")
            verdicts[str(d["n"])] = {"verdict": v["verdict"], "note": str(v.get("note", "")), "kind": d["kind"], "ours": d["ours"],
                                     "witness": d["witness"], "our_line": d["our_line"], "witness_line": d["witness_line"]}
        counts: dict[str, int] = {}
        for v in verdicts.values():
            counts[v["verdict"]] = counts.get(v["verdict"], 0) + 1
        rec["witnesses"].append({"witness": name, "page_sha256": w["page_sha256"], "fetched_at": w["fetched_at"],
                                 "differences": w["count"], "verdicts": verdicts, "counts": counts})
    if problems:
        raise ValueError("the settler's answer does not settle every difference: " + "; ".join(problems))
    rec["diff_sha256"] = sha
    rec["stops"] = sorted({v["verdict"] for w in rec["witnesses"] for v in w.get("verdicts", {}).values() if v["verdict"] in STOPPING})
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
            out.append(f"{w['witness']}: {w['differences']} difference(s), settled " + (", ".join(f"{k} {v}" for k, v in sorted(w["counts"].items())) or "none"))
    return "; ".join(out)
