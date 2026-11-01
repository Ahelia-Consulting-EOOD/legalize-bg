"""The register of lex.bg's defect kinds, ``docs/data/lexbg-defect-kinds.yaml`` (step S2 of the plan of 31 October 2026).

One entry per kind of error lex.bg makes against the Gazette, from the closed set the plan names (``reading.defects.KINDS``;
it grows only by the owner's word): the kind, its description, its evidence (where it was seen or named), its detector
where the form allows one (a script and the rule in it, or the check of the reading path that finds it) and, where it
does not, why a script can only point, and the acts whose verdict confirmed it. The form is fixed, so its check is
mechanical and blocks: the file loads against the schema here, its kinds are exactly the closed set, every detector
names a script that exists and carries the rule's name, a kind marked ``confirmed`` has at least one example, and every
example is a confirmed verdict of that kind in the run the file names. What the prose fields say is read, not checked.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from reading import defects  # noqa: E402

DEFAULT_PATH = ROOT / "docs" / "data" / "lexbg-defect-kinds.yaml"
STATUSES = ("confirmed", "named")
EVIDENCE_KINDS = ("plan", "register", "audit", "verdict", "decision", "case_file")
FIELDS = ("kind", "status", "description", "evidence", "detector", "examples")
DETECTOR_FIELDS = ("script", "rule", "form")

HEADER = """# docs/data/lexbg-defect-kinds.yaml: the register of lex.bg's defect kinds (plan of 31 October 2026, step S2; D-075, D-076).
#
# One entry per kind of error lex.bg makes against the Държавен вестник. The kinds are the plan's closed set, held in
# reading/defects.py (KINDS), and grow only by the owner's word. The file is written by reading/defect_kinds.py (sync fills
# the examples from a run's verdicts); the prose fields are the session's, the rest is checked mechanically (check).
#
# status:   confirmed (at least one act's verdict confirmed the kind) | named (in the closed set, not yet seen)
# evidence: a list of {kind: plan | register | audit | verdict | decision | case_file, ref: <where>}
# detector: {script: <path>, rule: <name the script carries>, form: <what fixed form the rule reads>} or null, with
#           no_detector: <why a script can only point at places to read> when null
# examples: the slugs whose verdict in the run named by `run` confirmed the kind
"""


class RegisterError(ValueError):
    """The register does not load against its schema; the message names every problem."""


def load(path: Path | str | None = None) -> dict:
    path = Path(path or DEFAULT_PATH)
    try:
        doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise RegisterError(f"{path}: not YAML: {exc}") from None
    if not isinstance(doc, dict) or not isinstance(doc.get("kinds"), list) or not isinstance(doc.get("run"), str):
        raise RegisterError(f"{path}: the document is not a mapping with a `run` name and a `kinds` list")
    problems = _problems(doc)
    if problems:
        raise RegisterError(f"{path}: " + "; ".join(problems))
    return doc


def _problems(doc: dict) -> list[str]:
    out: list[str] = []
    seen: list[str] = []
    for k, e in enumerate(doc["kinds"]):
        where = f"entry {k} ({e.get('kind', '?') if isinstance(e, dict) else '?'})"
        if not isinstance(e, dict):
            out.append(f"entry {k}: not a mapping")
            continue
        for f in FIELDS:
            if f not in e:
                out.append(f"{where}: missing {f}")
        if e.get("kind") not in defects.KINDS:
            out.append(f"{where}: kind {e.get('kind')!r} is not one of {sorted(defects.KINDS)}")
        seen.append(str(e.get("kind")))
        if e.get("status") not in STATUSES:
            out.append(f"{where}: status {e.get('status')!r} is not one of {STATUSES}")
        if not isinstance(e.get("description"), str) or not e["description"].strip():
            out.append(f"{where}: description is empty")
        ev = e.get("evidence")
        if not isinstance(ev, list) or not ev or any(not isinstance(x, dict) or x.get("kind") not in EVIDENCE_KINDS or not isinstance(x.get("ref"), str) or not x["ref"].strip() for x in ev):
            out.append(f"{where}: evidence is not a non-empty list of {{kind: one of {EVIDENCE_KINDS}, ref: text}}")
        det = e.get("detector")
        if det is None:
            if not isinstance(e.get("no_detector"), str) or not e["no_detector"].strip():
                out.append(f"{where}: a kind without a detector says why (no_detector)")
        elif not isinstance(det, dict) or any(not isinstance(det.get(f), str) or not det[f].strip() for f in DETECTOR_FIELDS):
            out.append(f"{where}: detector is not {{script, rule, form}}")
        else:
            script = ROOT / det["script"]
            if not script.is_file():
                out.append(f"{where}: detector script {det['script']} does not exist")
            elif det["rule"] not in script.read_text(encoding="utf-8"):
                out.append(f"{where}: detector script {det['script']} does not carry the rule {det['rule']!r}")
        ex = e.get("examples")
        if not isinstance(ex, list) or any(not isinstance(s, str) or not re.match(r"^-?[a-z0-9][a-z0-9-]*$", s) for s in ex):
            out.append(f"{where}: examples is not a list of slugs")
        elif e.get("status") == "confirmed" and not ex:
            out.append(f"{where}: a confirmed kind has at least one example")
        elif e.get("status") == "named" and ex:
            out.append(f"{where}: a named kind has no example; mark it confirmed")
        for key in e:
            if key not in FIELDS + ("no_detector",):
                out.append(f"{where}: unknown field {key}")
    missing = sorted(set(defects.KINDS) - set(seen))
    extra = sorted(k for k in set(seen) if seen.count(k) > 1)
    if missing:
        out.append(f"kinds of the closed set without an entry: {missing}")
    if extra:
        out.append(f"kinds with two entries: {extra}")
    return out


def check(path: Path | str | None = None, root: Path = ROOT) -> list[str]:
    """Every problem a mechanical check finds: the schema, and the examples against the run's verdicts."""
    path = Path(path or DEFAULT_PATH)
    try:
        doc = load(path)
    except RegisterError as exc:
        return [str(exc)]
    out: list[str] = []
    run_root = root / "data" / "runs" / doc["run"]
    if not (run_root / "candidates.json").exists():
        return out + [f"the run {doc['run']} has no candidates.json under {run_root}"] if any(e["examples"] for e in doc["kinds"]) else out
    c = defects.count(run_root)
    confirmed: dict[str, list[str]] = {}
    for slug in c["confirmed"]:
        v = defects._read_json(defects.verdict_path(run_root, slug))
        confirmed.setdefault(v["kind"], []).append(slug)
    for e in doc["kinds"]:
        have = sorted(confirmed.get(e["kind"], []))
        if sorted(e["examples"]) != have:
            out.append(f"{e['kind']}: examples {sorted(e['examples'])} are not the run's confirmed verdicts of the kind {have} (run sync)")
    return out


def sync(path: Path | str | None = None, root: Path = ROOT) -> dict:
    """Fill each kind's examples and status from the run's confirmed verdicts; the prose fields are kept."""
    path = Path(path or DEFAULT_PATH)
    doc = load(path)
    run_root = root / "data" / "runs" / doc["run"]
    c = defects.count(run_root)
    confirmed: dict[str, list[str]] = {}
    for slug in c["confirmed"]:
        v = defects._read_json(defects.verdict_path(run_root, slug))
        confirmed.setdefault(v["kind"], []).append(slug)
    for e in doc["kinds"]:
        e["examples"] = sorted(confirmed.get(e["kind"], []))
        e["status"] = "confirmed" if e["examples"] else "named"
    save(path, doc)
    return doc


def save(path: Path | str, doc: dict) -> None:
    path = Path(path)
    body = yaml.safe_dump({"run": doc["run"], "kinds": doc["kinds"]}, allow_unicode=True, sort_keys=False, width=1000)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(HEADER + body, encoding="utf-8")
    tmp.replace(path)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--path", default=None)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("check")
    sub.add_parser("sync")
    args = ap.parse_args(argv)
    if args.cmd == "check":
        problems = check(args.path)
        for p in problems:
            print(p)
        print("ok" if not problems else f"{len(problems)} problem(s)")
        return 1 if problems else 0
    doc = sync(args.path)
    for e in doc["kinds"]:
        print(f"{e['kind']}: {e['status']}, {len(e['examples'])} example(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
