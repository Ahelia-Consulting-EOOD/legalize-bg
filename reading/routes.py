"""The route driver: bounds and case files for every route (step S0 of the plan of 31 October 2026, D-075).

A route is a named, ordered list of known steps (``ROUTE_STEPS``, one list per route of the exceptions
list). The driver runs an act through its route and stops at a fixed point:

- the steps are used up without a committed act;
- a step changed nothing (its declared outputs hash the same before and after it ran);
- the next step is not defined (its name is not in the step registry: no engine yet, no S4 yet).

A step never runs again on inputs it has already run on: the hash of each step's declared inputs is kept
in the act's ledger (``<run>/<slug>/route.json``), a completed step with the same hash is skipped when the
route is walked again, and ``run_step`` refuses to run it. A step that waits on the model's answers (the
labeller's, the settler's, the investigator's) returns ``pending``: the route halts without a stop and
continues when it is walked again with the answers on disk.

On a stop without a committed act the driver writes a case file, ``docs/cases/<slug>.md``: a fixed YAML
frontmatter (the act, the route, the step it stopped at, the exception, what was tried with the paths of
its evidence, the run, the date) and three prose parts, lessons learnt, proposal and the owner's ruling,
which the model writes and the owner reads; the driver never overwrites the prose. The checks that are
mechanical and block: the case file's frontmatter against its schema, a stopped act without a case file,
a step run twice on the same input hash. A third ladder round is refused by the ladder's own limit.

The real steps live in ``reading/steps.py``; tests pass their own. The driver makes no model call and
writes no corpus file: the write step goes through ``reading/write.py`` and the gate.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Protocol

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import source_exceptions as sx  # noqa: E402

CASES = "docs/cases"
LEDGER = "route.json"

# the known steps of each route, in order; the write path is the last step of every route that commits
ROUTE_STEPS: dict[str, tuple[str, ...]] = {
    "whole_act_from_material": ("amendment_search", "fetch_material", "prepare", "label", "ladder", "content_check", "witnesses", "write"),
    "history": ("engine",),
    "source_before_archive": ("source_decision",),
    "investigate": ("investigate", "route_decision"),
}
OUTCOMES = ("done", "unchanged", "pending", "stop")
STOP_STEPS_USED_UP = "the route's steps are used up without a committed act"
STOP_UNCHANGED = "the step changed nothing"
STOP_UNDEFINED = "the next step is not defined"
CASE_PARTS = ("Lessons learnt", "Proposal", "The owner's ruling")
CASE_PLACEHOLDER = {"Lessons learnt": "(not yet written)", "Proposal": "(not yet written)", "The owner's ruling": "(not yet given)"}
_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


class RouteRefused(Exception):
    """A bound of the driver: the request is refused and nothing of the act changes."""


@dataclass
class StepResult:
    outcome: str
    detail: str = ""
    evidence: list[str] = field(default_factory=list)   # paths relative to the root
    committed: str | None = None                        # the commit, when the step committed the act

    def __post_init__(self) -> None:
        if self.outcome not in OUTCOMES:
            raise ValueError(f"unknown outcome {self.outcome!r}")


class Step(Protocol):
    name: str

    def inputs(self, ctx: "Context") -> list[Path]: ...
    def outputs(self, ctx: "Context") -> list[Path]: ...
    def run(self, ctx: "Context") -> StepResult: ...


@dataclass
class Context:
    slug: str
    run: str
    root: Path
    run_root: Path
    list_path: Path
    entry: sx.Entry | None = None
    params: dict = field(default_factory=dict)

    @property
    def act_dir(self) -> Path:
        return self.run_root / self.slug

    @property
    def ledger_path(self) -> Path:
        return self.act_dir / LEDGER

    def rel(self, p: Path) -> str:
        try:
            return str(Path(p).resolve().relative_to(self.root.resolve()))
        except ValueError:
            return str(p)


@dataclass
class Outcome:
    state: str                 # "committed" | "pending" | "stopped"
    step: str
    detail: str = ""
    case_file: str | None = None
    commit: str | None = None


def context(slug: str, run: str, *, root: Path | str = ROOT, run_root: Path | str | None = None,
            list_path: Path | str | None = None, params: dict | None = None) -> Context:
    root = Path(root)
    list_path = Path(list_path) if list_path else root / "docs" / "data" / "source-exceptions.yaml"
    run_root = Path(run_root) if run_root else root / "data" / "runs" / run
    entry = sx.listed(slug, list_path) if list_path.exists() else None
    return Context(slug=slug, run=run, root=root, run_root=run_root, list_path=list_path, entry=entry, params=params or {})


# --- hashes and the ledger ----------------------------------------------------------------------------

def _hash_paths(paths: list[Path]) -> str:
    h = hashlib.sha256()
    for p in sorted(set(Path(x) for x in paths), key=str):
        h.update(p.name.encode()); h.update(b"\0")
        if p.is_file():
            h.update(p.read_bytes())
        elif p.is_dir():
            for f in sorted(x for x in p.rglob("*") if x.is_file()):
                h.update(str(f.relative_to(p)).encode()); h.update(b"\0"); h.update(f.read_bytes()); h.update(b"\0")
        else:
            h.update(b"missing")
        h.update(b"\0")
    return h.hexdigest()


def input_hash(step: Step, ctx: Context) -> str:
    return _hash_paths(step.inputs(ctx))


def outputs_hash(step: Step, ctx: Context) -> str:
    return _hash_paths(step.outputs(ctx))


def load_ledger(ctx: Context) -> dict:
    p = ctx.ledger_path
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    return {"slug": ctx.slug, "run": ctx.run, "route": None, "state": None, "entries": []}


def save_ledger(ctx: Context, ledger: dict) -> None:
    ctx.act_dir.mkdir(parents=True, exist_ok=True)
    ctx.ledger_path.write_text(json.dumps(ledger, ensure_ascii=False, indent=1), encoding="utf-8")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def completed(ledger: dict, step: str) -> list[dict]:
    return [e for e in ledger["entries"] if e["step"] == step and e["outcome"] in ("done", "unchanged", "stop")]


def run_step(ctx: Context, step: Step, ledger: dict | None = None) -> dict:
    """Run one step and record it; refused when the step already ran on these inputs."""
    ledger = load_ledger(ctx) if ledger is None else ledger
    h = input_hash(step, ctx)
    for e in completed(ledger, step.name):
        if e["input_sha256"] == h:
            raise RouteRefused(f"{ctx.slug}: step {step.name} already ran on these inputs ({h[:12]}) with outcome "
                               f"{e['outcome']}; a step never runs again on inputs it has already run on")
    before = outputs_hash(step, ctx)
    started = _now()
    res = step.run(ctx)
    after = outputs_hash(step, ctx)
    outcome = res.outcome
    if outcome == "done" and after == before and not res.committed:
        outcome = "unchanged"
    entry = {"step": step.name, "input_sha256": h, "outputs_sha256": after, "outcome": outcome, "detail": res.detail,
             "evidence": list(res.evidence), "committed": res.committed, "started": started, "ended": _now()}
    ledger["entries"] = [e for e in ledger["entries"] if not (e["step"] == step.name and e["outcome"] == "pending")]
    ledger["entries"].append(entry)
    save_ledger(ctx, ledger)
    return entry


def run_route(ctx: Context, steps: dict[str, Step], route: str | None = None,
              routes: dict[str, tuple[str, ...]] = ROUTE_STEPS) -> Outcome:
    """Walk the act's route: skip the steps already done on the same inputs, run the next, stop at the bounds."""
    route = route or (ctx.entry.route if ctx.entry else None)
    if route is None:
        raise RouteRefused(f"{ctx.slug}: not on the exceptions list and no route given")
    if route not in routes:
        raise RouteRefused(f"{ctx.slug}: unknown route {route!r}; one of {sorted(routes)}")
    ledger = load_ledger(ctx)
    if ledger.get("route") not in (None, route):
        raise RouteRefused(f"{ctx.slug}: the run already carries route {ledger['route']!r}; a route is not changed inside a run")
    ledger["route"] = route
    if ledger.get("state") == "committed":
        last = next(e for e in reversed(ledger["entries"]) if e.get("committed"))
        return Outcome("committed", last["step"], last["detail"], commit=last["committed"])
    name = routes[route][-1] if routes[route] else ""
    for name in routes[route]:
        if name not in steps:
            return _stop(ctx, ledger, name, f"{STOP_UNDEFINED}: {name}")
        step = steps[name]
        h = input_hash(step, ctx)
        same = [e for e in completed(ledger, name) if e["input_sha256"] == h]
        if same:
            e = same[-1]
            if e["outcome"] == "done":
                if e.get("committed"):
                    return _committed(ctx, ledger, e)
                continue
            # the step changed nothing or stopped on these inputs: the stop stands
            return _stop(ctx, ledger, name, e["detail"] if e["outcome"] == "stop" else f"{STOP_UNCHANGED}: {name}")
        e = run_step(ctx, step, ledger)
        if e["outcome"] == "pending":
            ledger["state"] = "pending"
            save_ledger(ctx, ledger)
            return Outcome("pending", name, e["detail"])
        if e["outcome"] == "unchanged":
            return _stop(ctx, ledger, name, f"{STOP_UNCHANGED}: {name}")
        if e["outcome"] == "stop":
            return _stop(ctx, ledger, name, e["detail"])
        if e.get("committed"):
            return _committed(ctx, ledger, e)
    return _stop(ctx, ledger, name, STOP_STEPS_USED_UP)


def _committed(ctx: Context, ledger: dict, e: dict) -> Outcome:
    ledger["state"] = "committed"
    ledger["stopped_at"] = None
    save_ledger(ctx, ledger)
    if ctx.entry is not None:
        sx.update(ctx.list_path, ctx.slug, state="committed", commit=e["committed"], case_file="")
    return Outcome("committed", e["step"], e["detail"], commit=e["committed"])


def _stop(ctx: Context, ledger: dict, step: str, exception: str) -> Outcome:
    ledger["state"] = "stopped"
    ledger["stopped_at"] = step
    ledger["exception"] = exception
    case = write_case_file(ctx, ledger, step, exception)
    ledger["case_file"] = ctx.rel(case)
    save_ledger(ctx, ledger)
    if ctx.entry is not None:
        sx.update(ctx.list_path, ctx.slug, state="stopped", case_file=ctx.rel(case))
    return Outcome("stopped", step, exception, case_file=ctx.rel(case))


# --- case files ---------------------------------------------------------------------------------------

def case_path(root: Path, slug: str) -> Path:
    return Path(root) / CASES / f"{slug}.md"


def write_case_file(ctx: Context, ledger: dict, step: str, exception: str) -> Path:
    """Write the case file's frontmatter; the three prose parts are kept when the file exists, else placeholders."""
    tried = [{"step": e["step"], "outcome": e["outcome"], "detail": e["detail"], "evidence": list(e["evidence"])}
             for e in ledger["entries"] if e["outcome"] != "pending"]
    fm = {"act": ctx.slug, "title": ctx.entry.title if ctx.entry else ctx.slug, "route": ledger["route"], "stopped_at": step,
          "exception": exception, "tried": tried, "run": ctx.run, "record": ctx.rel(ctx.ledger_path), "date": date.today().isoformat()}
    path = case_path(ctx.root, ctx.slug)
    prose = None
    if path.exists():
        _, prose = split_case_file(path.read_text(encoding="utf-8"))
    if prose is None:
        prose = "\n".join(f"## {part}\n\n{CASE_PLACEHOLDER[part]}\n" for part in CASE_PARTS)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("---\n" + yaml.safe_dump(fm, allow_unicode=True, sort_keys=False, width=1000) + "---\n\n" + prose.strip("\n") + "\n", encoding="utf-8")
    return path


def split_case_file(text: str) -> tuple[dict | None, str | None]:
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.S)
    if not m:
        return None, None
    try:
        fm = yaml.safe_load(m.group(1))
    except yaml.YAMLError:
        return None, m.group(2)
    return fm if isinstance(fm, dict) else None, m.group(2)


def check_case_file(path: Path) -> list[str]:
    """The frontmatter against its schema and the three prose parts in order; every problem, or none."""
    path = Path(path)
    if not path.exists():
        return [f"{path}: missing"]
    fm, prose = split_case_file(path.read_text(encoding="utf-8"))
    out: list[str] = []
    if fm is None:
        return [f"{path}: no YAML frontmatter"]
    for key, typ in (("act", str), ("title", str), ("route", str), ("stopped_at", str), ("exception", str), ("tried", list), ("run", str), ("record", str), ("date", str)):
        if key not in fm:
            out.append(f"{path}: missing {key}")
        elif not isinstance(fm[key], typ):
            out.append(f"{path}: {key} is not a {typ.__name__}")
    if isinstance(fm.get("route"), str) and fm["route"] not in sx.ROUTES:
        out.append(f"{path}: route {fm['route']!r} is not one of {sorted(sx.ROUTES)}")
    if isinstance(fm.get("date"), str) and not _DATE.match(fm["date"]):
        out.append(f"{path}: date {fm['date']!r} is not YYYY-MM-DD")
    if isinstance(fm.get("act"), str) and path.stem != fm["act"]:
        out.append(f"{path}: the file is not named after the act {fm['act']!r}")
    for k, t in enumerate(fm.get("tried") or []):
        if not isinstance(t, dict) or not isinstance(t.get("step"), str) or t.get("outcome") not in OUTCOMES or not isinstance(t.get("evidence"), list):
            out.append(f"{path}: tried[{k}] is not {{step, outcome, detail, evidence: [paths]}}")
    for key in fm:
        if key not in ("act", "title", "route", "stopped_at", "exception", "tried", "run", "record", "date"):
            out.append(f"{path}: unknown field {key}")
    heads = re.findall(r"^## (.+)$", prose or "", re.M)
    if heads != list(CASE_PARTS):
        out.append(f"{path}: the prose parts are {heads}, not {list(CASE_PARTS)}")
    return out


def check_run(run_root: Path, root: Path = ROOT) -> list[str]:
    """Every stopped act of a run has a case file that passes its schema; every problem, or none."""
    out: list[str] = []
    for ledger_path in sorted(Path(run_root).glob(f"*/{LEDGER}")):
        ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
        if ledger.get("state") != "stopped":
            continue
        slug = ledger_path.parent.name
        case = case_path(root, slug)
        if not case.exists():
            out.append(f"{slug}: stopped at {ledger.get('stopped_at')} without a case file ({case.relative_to(root) if case.is_relative_to(root) else case})")
            continue
        out.extend(check_case_file(case))
    return out


def report(run_root: Path, root: Path = ROOT, list_path: Path | None = None) -> str:
    """The run's acts with their state, the case files to read together, then the list's distance."""
    lines = [f"run {Path(run_root).name}"]
    cases: list[str] = []
    for ledger_path in sorted(Path(run_root).glob(f"*/{LEDGER}")):
        ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
        slug = ledger_path.parent.name
        state = ledger.get("state") or "not run"
        where = ledger.get("stopped_at") or (ledger["entries"][-1]["step"] if ledger["entries"] else "-")
        line = f"  {slug}: route {ledger.get('route')}, {state} at {where}"
        if state == "stopped":
            line += f": {ledger.get('exception')}"
            cases.append(ledger.get("case_file") or str(case_path(root, slug)))
        elif state == "committed":
            commit = next((e["committed"] for e in reversed(ledger["entries"]) if e.get("committed")), "?")
            line += f", commit {commit}"
        lines.append(line)
    lines.append(f"case files to read together ({len(cases)}):")
    lines.extend(f"  {c}" for c in cases)
    lp = list_path or (root / "docs" / "data" / "source-exceptions.yaml")
    if Path(lp).exists():
        lines.append(sx.report(lp))
    return "\n".join(lines)


# --- command line --------------------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run", help="walk an act's route (the real steps of reading/steps.py)")
    r.add_argument("slug"); r.add_argument("--run", required=True); r.add_argument("--route", default=None)
    r.add_argument("--param", action="append", default=[], help="key=value for the steps")
    p = sub.add_parser("report"); p.add_argument("--run", required=True)
    c = sub.add_parser("check"); c.add_argument("--run", required=True)
    args = ap.parse_args(argv)
    if args.cmd == "run":
        from reading.steps import STEPS  # noqa: WPS433  (the real steps; imported here so tests need none of them)
        params = dict(kv.split("=", 1) for kv in args.param)
        ctx = context(args.slug, args.run, params=params)
        try:
            out = run_route(ctx, STEPS, args.route)
        except RouteRefused as exc:
            print(f"refused  {exc}")
            return 2
        print(f"{out.state:<9} {args.slug}: at {out.step}" + (f": {out.detail}" if out.detail else "")
              + (f" (case file {out.case_file})" if out.case_file else "") + (f" (commit {out.commit})" if out.commit else ""))
        return 0 if out.state == "committed" else 1
    run_root = ROOT / "data" / "runs" / args.run
    if args.cmd == "report":
        print(report(run_root))
        return 0
    problems = check_run(run_root)
    for pr in problems:
        print(pr)
    print("ok" if not problems else f"{len(problems)} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
