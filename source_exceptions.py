"""The exceptions list: the acts whose text is not taken from lex.bg (step S1 of the plan of 31 October 2026, D-075).

The list is a data file, ``docs/data/source-exceptions.yaml``, with a fixed form, so its checks are
mechanical and block: the file loads against the schema here (every field from its closed set, one entry
per act), every entry names a route, the write gate refuses a listed act on the lex.bg path by name, and
``report`` prints each entry's distance to its commit. Being on the list is not an outcome: an entry whose
act is not yet committed from its route is distance left, and every report states it first.

This module imports only the YAML reader and the corpus loader, so the gate can use it without the
reading path. Nothing here writes a corpus file.
"""
from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field, asdict
from datetime import date
from pathlib import Path

import yaml

from corpus_integrity.loader import CATEGORY_DIRS

ROOT = Path(__file__).resolve().parent
DEFAULT_PATH = ROOT / "docs" / "data" / "source-exceptions.yaml"

# the closed sets of the plan's S1, item 1; a value outside them is a schema error, not a free label
DEFECTS: dict[str, str] = {
    "dropped_section": "lex.bg drops a promulgated section of the act (FR-042)",
    "wrong_text": "lex.bg's text of a provision differs from the Gazette's",
    "page_without_act": "the lex.bg page holds no act, only site chrome",
    "server_error": "lex.bg answers an error for the act's page",
    "source_before_archive": "the act's text comes from before the Gazette's online archive, so lex.bg is not its base",
}
SOURCES: dict[str, str] = {
    "dv_html": "the Gazette's HTML material (dv.parliament.bg, from бр. 1/2003)",
    "dv_pdf": "the Gazette's issue PDF (1989 to 2002)",
    "moj_portal": "the Ministry of Justice portal (justice.government.bg/home/normdoc/{id})",
    "strategy_bg": "the public-consultation portal strategy.bg",
    "paid_service": "a paid consolidated-law service (a spending decision of the owner)",
    "unknown": "not yet decided: the act was listed by the content check and the investigator records the source",
}
ROUTES: dict[str, str] = {
    "whole_act_from_material": "the act read whole from its promulgation material (an act never amended)",
    "history": "the act's history rebuilt through the engine of F1",
    "source_before_archive": "the source decided in S4 and the text read from it",
    "investigate": "one run of the investigator, which records the defect, the source and the route",
}
STATES: tuple[str, ...] = ("listed", "investigated", "committed", "stopped")
EVIDENCE_KINDS: tuple[str, ...] = ("decision", "audit", "case_file", "register", "plan")

_SLUG = re.compile(r"^-?[a-z0-9][a-z0-9-]*$")
_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

HEADER = """# docs/data/source-exceptions.yaml: the exceptions list (plan of 31 October 2026, step S1; D-075, D-076).
#
# One entry per act whose text is not taken from lex.bg. Every field is from a closed set defined in
# source_exceptions.py; the file is written by that module only (the route driver adds entries and moves
# their state), never by hand. An entry is not an outcome: its act counts only once it is committed
# correct from its route, and `python source_exceptions.py report` prints the distance left first.
#
# defect: dropped_section | wrong_text | page_without_act | server_error | source_before_archive
# source: dv_html | dv_pdf | moj_portal | strategy_bg | paid_service | unknown; address: a material id (dv_html, dv_pdf), a URL, or unknown
# route:  whole_act_from_material | history | source_before_archive | investigate
# state:  listed | investigated | committed | stopped
# evidence: a list of {kind: decision | audit | case_file | register | plan, ref: <where>}
# absent_witnesses: a list of {witness: lexbg | moj, reason, owner}: a witness the act cannot be compared with, only on
#   the owner's word (the plan compares both witnesses); without it the write refuses an act whose record lacks a witness
"""


class ListError(ValueError):
    """The list does not load against its schema; the message names every problem."""


@dataclass
class Entry:
    slug: str
    title: str
    defect: str
    source: str
    address: str
    route: str
    evidence: list[dict] = field(default_factory=list)
    state: str = "listed"
    added: str = ""
    note: str = ""
    case_file: str = ""   # the case file of a stopped entry, relative to the repository root
    commit: str = ""      # the commit of a committed entry
    absent_witnesses: list[dict] = field(default_factory=list)   # [{witness, reason, owner}]: a witness the act cannot be compared with, on the owner's word

    def to_dict(self) -> dict:
        return {k: v for k, v in asdict(self).items() if v != "" and not (k == "absent_witnesses" and not v)}


def _problems(entry: dict, k: int) -> list[str]:
    where = f"entry {k} ({entry.get('slug', '?')})"
    out: list[str] = []
    if not isinstance(entry, dict):
        return [f"entry {k}: not a mapping"]
    for key in ("slug", "title", "defect", "source", "address", "route", "evidence", "state", "added"):
        if key not in entry:
            out.append(f"{where}: missing {key}")
    for key in ("slug", "title", "address", "note", "case_file", "commit"):
        if key in entry and not isinstance(entry[key], str):
            out.append(f"{where}: {key} is not a string")
    if isinstance(entry.get("slug"), str) and not _SLUG.match(entry["slug"]):
        out.append(f"{where}: slug {entry['slug']!r} is not a corpus slug")
    for key, allowed in (("defect", DEFECTS), ("source", SOURCES), ("route", ROUTES), ("state", STATES)):
        if key in entry and entry[key] not in allowed:
            out.append(f"{where}: {key} {entry[key]!r} is not one of {sorted(allowed)}")
    address = entry.get("address")
    if isinstance(address, str) and not address.strip():
        out.append(f"{where}: address is empty")
    elif isinstance(address, str) and entry.get("source") in ("dv_html", "dv_pdf") and not address.strip().isdigit():
        out.append(f"{where}: address {address!r} is not a material id, as the source {entry['source']} needs")
    elif isinstance(address, str) and entry.get("source") in ("moj_portal", "strategy_bg", "paid_service", "unknown") and address.strip() != "unknown" and not address.strip().startswith(("http://", "https://")):
        out.append(f"{where}: address {address!r} is neither a URL nor unknown, as the source {entry['source']} needs")
    if "added" in entry and not _DATE.match(str(entry["added"])):
        out.append(f"{where}: added {entry['added']!r} is not a date YYYY-MM-DD")
    ev = entry.get("evidence")
    if "evidence" in entry:
        if not isinstance(ev, list) or not ev:
            out.append(f"{where}: evidence is not a non-empty list")
        else:
            for j, e in enumerate(ev):
                if not isinstance(e, dict) or e.get("kind") not in EVIDENCE_KINDS or not isinstance(e.get("ref"), str) or not e["ref"].strip():
                    out.append(f"{where}: evidence {j} is not {{kind: one of {list(EVIDENCE_KINDS)}, ref: text}}")
    if entry.get("state") == "stopped" and not entry.get("case_file"):
        out.append(f"{where}: a stopped entry names its case file")
    if entry.get("state") == "committed" and not entry.get("commit"):
        out.append(f"{where}: a committed entry names its commit")
    for j, w in enumerate(entry.get("absent_witnesses") or []):
        if not isinstance(w, dict) or w.get("witness") not in ("lexbg", "moj") or not str(w.get("reason", "")).strip() or not str(w.get("owner", "")).strip():
            out.append(f"{where}: absent_witnesses[{j}] is not {{witness: lexbg | moj, reason: text, owner: who said so and when}}")
    for key in entry:
        if key not in Entry.__dataclass_fields__:
            out.append(f"{where}: unknown field {key}")
    return out


def load(path: Path | str | None = None) -> list[Entry]:
    """The entries, or ``ListError`` naming every problem of the file's form."""
    path = Path(path or DEFAULT_PATH)
    try:
        doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ListError(f"{path}: not YAML: {exc}") from None
    if not isinstance(doc, dict) or "entries" not in doc or not isinstance(doc["entries"], list):
        raise ListError(f"{path}: the document is not a mapping with an `entries` list")
    problems: list[str] = []
    seen: dict[str, int] = {}
    for k, e in enumerate(doc["entries"]):
        problems.extend(_problems(e, k))
        if isinstance(e, dict) and isinstance(e.get("slug"), str):
            if e["slug"] in seen:
                problems.append(f"entry {k}: a second entry for {e['slug']} (the first is entry {seen[e['slug']]})")
            seen.setdefault(e["slug"], k)
    if problems:
        raise ListError(f"{path}: " + "; ".join(problems))
    return [Entry(**{**{"note": "", "case_file": "", "commit": "", "absent_witnesses": []}, **e}) for e in doc["entries"]]


def corpus_file(root: Path, slug: str) -> Path | None:
    found = [root / cat / f"{slug}.md" for cat in CATEGORY_DIRS if (root / cat / f"{slug}.md").exists()]
    return found[0] if len(found) == 1 else None


def check(path: Path | str | None = None, root: Path | str = ROOT) -> list[str]:
    """Every problem a mechanical check finds: the schema, and a slug that names no corpus file."""
    path = Path(path or DEFAULT_PATH)
    try:
        entries = load(path)
    except ListError as exc:
        return [str(exc)]
    root = Path(root)
    return [f"{e.slug}: no corpus file under {CATEGORY_DIRS}" for e in entries if corpus_file(root, e.slug) is None]


def listed(slug: str, path: Path | str | None = None) -> Entry | None:
    """The act's entry, or None. A list that does not load is an error, never a silent None."""
    return next((e for e in load(path) if e.slug == slug), None)


def save(path: Path | str, entries: list[Entry]) -> None:
    """Write the file whole: the fixed header, then the entries in their order."""
    path = Path(path)
    body = yaml.safe_dump({"entries": [e.to_dict() for e in entries]}, allow_unicode=True, sort_keys=False, default_flow_style=False, width=1000)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(HEADER + body, encoding="utf-8")
    tmp.replace(path)


def add(path: Path | str, entry: Entry) -> None:
    """Add an entry; a second entry for the same act is refused (two writers never share an act)."""
    entries = load(path)
    if any(e.slug == entry.slug for e in entries):
        raise ListError(f"{entry.slug} is already on the list")
    problems = _problems(entry.to_dict(), len(entries))
    if problems:
        raise ListError("; ".join(problems))
    save(path, entries + [entry])


def update(path: Path | str, slug: str, **changes) -> Entry:
    """Change an entry's fields (state, route, case_file, commit, note) and save; the entry must exist."""
    entries = load(path)
    for e in entries:
        if e.slug == slug:
            for k, v in changes.items():
                if k not in Entry.__dataclass_fields__ or k == "slug":
                    raise ListError(f"{slug}: cannot change {k}")
                setattr(e, k, v)
            problems = _problems(e.to_dict(), 0)
            if problems:
                raise ListError("; ".join(problems))
            save(path, entries)
            return e
    raise ListError(f"{slug} is not on the list")


def distance(entries: list[Entry]) -> list[dict]:
    """Per entry, where it stands between listed and committed: the distance left is every row not committed."""
    return [{"slug": e.slug, "route": e.route, "state": e.state,
             "distance": "committed" if e.state == "committed" else f"not committed: {e.state}" + (f" ({e.case_file})" if e.case_file else "")}
            for e in entries]


def report(path: Path | str | None = None) -> str:
    entries = load(path)
    rows = distance(entries)
    left = [r for r in rows if r["state"] != "committed"]
    lines = [f"distance left: {len(left)} of {len(rows)} entries not yet committed; {len(rows) - len(left)} committed"]
    for r in rows:
        lines.append(f"  {r['slug']}: route {r['route']}, {r['distance']}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    cmd = args[0] if args else "report"
    path = args[1] if len(args) > 1 else None
    if cmd == "check":
        problems = check(path)
        for p in problems:
            print(p)
        print("ok" if not problems else f"{len(problems)} problem(s)")
        return 1 if problems else 0
    if cmd == "report":
        print(report(path))
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
