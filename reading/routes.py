"""The route driver: bounds and case files for every route (step S0 of the plan of 31 October 2026, D-075).

A route is a named, ordered list of known steps (``ROUTE_STEPS``, one list per route of the exceptions
list; a route that ends in a step not yet built, the engine of F1 or the source decision of S4, gains its
later steps and the write step when they exist). The driver runs a listed act through its route and stops
at a fixed point:

- the steps are used up without a committed act;
- a step changed nothing (its declared outputs hash the same as after its previous run);
- the next step is not defined (its name is not in the step registry).

A step never runs again on inputs it has already run on: the hash of each step's declared inputs, the
route's parameters and the list entry's fields is kept in the act's step record across runs
(``data/runs/route-ledger/<slug>.json``); a completed step with the same hash is skipped when the route is
walked again, ``run_step`` refuses to run it, and a step that waits on the model's answers (the labeller's,
the settler's, the investigator's) is ``pending`` and not run again until its inputs change. Each run also
keeps its own record, ``<run>/<slug>/route.json``, with the run's state.

On a stop without a committed act the driver writes a case file, ``docs/cases/<slug>.md``: a fixed YAML
frontmatter (the act, the route, the step it stopped at, the exception, what was tried across runs with the
paths of its evidence, the run, the date) and three prose parts, lessons learnt, proposal and the owner's
ruling, which the model writes and the owner reads. The driver never overwrites the prose: a case file it
cannot parse refuses the stop's write, and a case file that carries the owner's ruling on another stop is
archived under ``docs/cases/archive/`` before a new one is written. The checks that are mechanical and
block: the case file's frontmatter against its schema, a stopped act without a case file (in the run and
on the list), a step run twice on the same input hash. A third ladder round is refused by the ladder's own
limit. One session writes the list and the case files at a time (plan, section 5); the driver takes no
lock.

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
STEP_RECORDS = "route-ledger"   # under the runs folder: one file per act, every completed step of every run

# the known steps of each route, in order
ROUTE_STEPS: dict[str, tuple[str, ...]] = {
    "whole_act_from_material": ("amendment_search", "fetch_material", "prepare", "label", "ladder", "content_check", "witnesses", "write"),
    "history": ("engine",),                      # F1: not built; the route then continues through the checks and the write step
    "source_before_archive": ("source_decision",),  # S4: not built; the route then continues through the reading and the write step
    "investigate": ("investigate", "route_decision"),
}
OUTCOMES = ("done", "unchanged", "pending", "stop")
COMPLETED = ("done", "unchanged", "stop")
STOP_STEPS_USED_UP = "the route's steps are used up without a committed act"
STOP_UNCHANGED = "the step changed nothing"
STOP_UNDEFINED = "the next step is not defined"
CASE_PARTS = ("Lessons learnt", "Proposal", "The owner's ruling")
CASE_PLACEHOLDER = {"Lessons learnt": "(not yet written)", "Proposal": "(not yet written)", "The owner's ruling": "(not yet given)"}
CASE_FIELDS = ("act", "title", "route", "stopped_at", "exception", "tried", "run", "record", "date")
CASE_OPTIONAL = ("previous", "resolved")
_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_FRONT = re.compile(r"^---\n(.*?)\n---\n(.*)$", re.S)


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

    @property
    def record_path(self) -> Path:
        return self.run_root.parent / STEP_RECORDS / f"{self.slug}.json"

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


# --- hashes and the records ---------------------------------------------------------------------------

def _hash_paths(paths: list[Path], extra: str = "") -> str:
    h = hashlib.sha256(extra.encode("utf-8"))
    for p in sorted(set(Path(x) for x in paths), key=str):
        h.update(p.name.encode()); h.update(b"\0")
        if p.is_file():
            h.update(b"file\0"); h.update(p.read_bytes())
        elif p.is_dir():
            h.update(b"dir\0")
            for f in sorted(x for x in p.rglob("*") if x.is_file()):
                h.update(str(f.relative_to(p)).encode()); h.update(b"\0"); h.update(f.read_bytes()); h.update(b"\0")
        else:
            h.update(b"\0absent\0")
        h.update(b"\0")
    return h.hexdigest()


def input_hash(step: Step, ctx: Context) -> str:
    """The step's declared inputs, the route's parameters and the list entry's fields: what the step runs on."""
    entry = {k: v for k, v in ctx.entry.to_dict().items() if k in ("defect", "source", "address", "route")} if ctx.entry else {}
    extra = json.dumps({"params": ctx.params, "entry": entry}, sort_keys=True, ensure_ascii=False)
    return _hash_paths(step.inputs(ctx), extra)


def outputs_hash(step: Step, ctx: Context) -> str:
    return _hash_paths(step.outputs(ctx))


def _read_json(p: Path, default: dict) -> dict:
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else default


def _write_json(p: Path, d: dict) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")


def load_ledger(ctx: Context) -> dict:
    return _read_json(ctx.ledger_path, {"slug": ctx.slug, "run": ctx.run, "route": None, "state": None, "entries": []})


def save_ledger(ctx: Context, ledger: dict) -> None:
    _write_json(ctx.ledger_path, ledger)


def load_record(ctx: Context) -> dict:
    """The act's step record across runs."""
    return _read_json(ctx.record_path, {"slug": ctx.slug, "steps": []})


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def same_inputs(record: dict, step: str, h: str) -> list[dict]:
    return [e for e in record["steps"] if e["step"] == step and e["input_sha256"] == h]


def run_step(ctx: Context, step: Step, ledger: dict | None = None) -> dict:
    """Run one step and record it in the run's ledger and the act's record; refused when it already ran on these inputs."""
    ledger = load_ledger(ctx) if ledger is None else ledger
    record = load_record(ctx)
    h = input_hash(step, ctx)
    for e in same_inputs(record, step.name, h):
        if e["outcome"] in COMPLETED:
            raise RouteRefused(f"{ctx.slug}: step {step.name} already ran on these inputs ({h[:12]}) in run {e['run']} with outcome "
                               f"{e['outcome']}; a step never runs again on inputs it has already run on")
        if e["outcome"] == "pending":
            raise RouteRefused(f"{ctx.slug}: step {step.name} is pending on these inputs ({h[:12]}) since run {e['run']}; "
                               f"it runs again when its inputs change")
        if e["outcome"] == "running":
            raise RouteRefused(f"{ctx.slug}: step {step.name} was interrupted on these inputs ({h[:12]}) in run {e['run']} "
                               f"(started {e['started']}); read the record before running it again")
    previous = [e for e in record["steps"] if e["step"] == step.name and e["outcome"] in COMPLETED]
    entry = {"step": step.name, "run": ctx.run, "input_sha256": h, "outputs_sha256": None, "outcome": "running", "detail": "",
             "evidence": [], "committed": None, "started": _now(), "ended": None}
    record["steps"].append(entry)
    _write_json(ctx.record_path, record)   # a crash inside the step leaves its trace
    try:
        res = step.run(ctx)
    except BaseException:
        record["steps"].remove(entry)
        entry["outcome"] = "interrupted"
        entry["ended"] = _now()
        record["steps"].append(entry)
        _write_json(ctx.record_path, record)
        raise
    after = outputs_hash(step, ctx)
    outcome = res.outcome
    if outcome == "done" and previous and after == previous[-1]["outputs_sha256"] and not res.committed:
        outcome = "unchanged"   # the same answer twice: the step changed nothing since its last run
    entry.update({"outputs_sha256": after, "outcome": outcome, "detail": res.detail, "evidence": list(res.evidence),
                  "committed": res.committed, "ended": _now()})
    _write_json(ctx.record_path, record)
    ledger["entries"].append({k: v for k, v in entry.items() if k != "run"})
    save_ledger(ctx, ledger)
    return entry


def _route_of(ctx: Context, route: str | None) -> str:
    if ctx.entry is None:
        raise RouteRefused(f"{ctx.slug}: not on the exceptions list; an act enters a route through its entry (routes.py add)")
    if route is not None and route != ctx.entry.route:
        raise RouteRefused(f"{ctx.slug}: the list names the route {ctx.entry.route!r}, not {route!r}; the route is changed on the list, not on the command line")
    return ctx.entry.route


def run_route(ctx: Context, steps: dict[str, Step], route: str | None = None,
              routes: dict[str, tuple[str, ...]] = ROUTE_STEPS) -> Outcome:
    """Walk the act's route: skip the steps already done on the same inputs, run the next, stop at the bounds."""
    route = _route_of(ctx, route)
    if route not in routes:
        raise RouteRefused(f"{ctx.slug}: unknown route {route!r}; one of {sorted(routes)}")
    ledger = load_ledger(ctx)
    if ledger.get("route") not in (None, route):
        raise RouteRefused(f"{ctx.slug}: the run already carries route {ledger['route']!r}; a route is not changed inside a run")
    ledger["route"] = route
    record = load_record(ctx)
    if ledger.get("state") == "committed":
        last = next(e for e in reversed(ledger["entries"]) if e.get("committed"))
        return _committed(ctx, ledger, last)
    name = routes[route][-1] if routes[route] else ""
    for name in routes[route]:
        if name not in steps:
            return _stop(ctx, ledger, name, f"{STOP_UNDEFINED}: {name}")
        step = steps[name]
        h = input_hash(step, ctx)
        same = same_inputs(record, name, h)
        if same:
            e = same[-1]
            if e["outcome"] == "done":
                if e.get("committed"):
                    return _committed(ctx, ledger, e)
                if outputs_hash(step, ctx) != e["outputs_sha256"]:
                    if e["run"] != ctx.run:
                        raise RouteRefused(f"{ctx.slug}: step {name} already ran on these inputs in run {e['run']}, whose folder holds "
                                           f"its outputs; continue in that run, or change the inputs (a step never runs again on the same inputs)")
                    raise RouteRefused(f"{ctx.slug}: the outputs of step {name} changed since it ran in run {e['run']}; "
                                       f"the run folder was altered, read the record before going on")
                continue   # the result stands
            if e["outcome"] == "pending":
                ledger["state"] = "pending"
                save_ledger(ctx, ledger)
                return Outcome("pending", name, e["detail"])
            if e["outcome"] in ("running", "interrupted"):
                raise RouteRefused(f"{ctx.slug}: step {name} was interrupted in run {e['run']}; read the record before running it again")
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
    if ctx.entry.state != "committed" or ctx.entry.commit != e["committed"]:
        ctx.entry = sx.update(ctx.list_path, ctx.slug, state="committed", commit=e["committed"], case_file="")
    case = case_path(ctx.root, ctx.slug)
    if case.exists():
        fm, prose = split_case_file(case.read_text(encoding="utf-8"))
        if fm is not None and fm.get("resolved") != e["committed"]:
            fm["resolved"] = e["committed"]   # the stop the case file describes is over: the act is committed
            _write_case(case, fm, prose)
    return Outcome("committed", e["step"], e["detail"], commit=e["committed"])


def _stop(ctx: Context, ledger: dict, step: str, exception: str) -> Outcome:
    ledger["state"] = "stopped"
    ledger["stopped_at"] = step
    ledger["exception"] = exception
    case = write_case_file(ctx, ledger, step, exception)
    ledger["case_file"] = ctx.rel(case)
    save_ledger(ctx, ledger)
    ctx.entry = sx.update(ctx.list_path, ctx.slug, state="stopped", case_file=ctx.rel(case))
    return Outcome("stopped", step, exception, case_file=ctx.rel(case))


def add_entry(list_path: Path, entry: sx.Entry) -> sx.Entry:
    """Put an act on the list through the driver; a second entry for the same act is refused by the list."""
    sx.add(list_path, entry)
    return entry


# --- case files ---------------------------------------------------------------------------------------

def case_path(root: Path, slug: str) -> Path:
    return Path(root) / CASES / f"{slug}.md"


def _write_case(path: Path, fm: dict, prose: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("---\n" + yaml.safe_dump(fm, allow_unicode=True, sort_keys=False, width=1000) + "---\n\n" + prose.strip("\n") + "\n", encoding="utf-8")


def _ruled(prose: str) -> bool:
    """Whether the owner's ruling part holds more than its placeholder."""
    m = re.search(r"^## The owner's ruling\n(.*)$", prose, re.S | re.M)
    body = (m.group(1) if m else "").strip()
    return bool(body) and body != CASE_PLACEHOLDER["The owner's ruling"]


def write_case_file(ctx: Context, ledger: dict, step: str, exception: str) -> Path:
    """Write the case file's frontmatter; the prose parts are kept, or placeholders when the file is new.

    A case file the driver cannot parse refuses the write (the owner's text is never replaced); a case file whose
    owner's ruling answers another stop is archived first, and the new file names it under ``previous``.
    """
    record = load_record(ctx)
    tried = [{"run": e["run"], "step": e["step"], "outcome": e["outcome"], "detail": e["detail"], "evidence": list(e["evidence"])}
             for e in record["steps"] if e["outcome"] in COMPLETED]
    fm = {"act": ctx.slug, "title": ctx.entry.title if ctx.entry else ctx.slug, "route": ledger["route"], "stopped_at": step,
          "exception": exception, "tried": tried, "run": ctx.run, "record": ctx.rel(ctx.record_path), "date": date.today().isoformat()}
    path = case_path(ctx.root, ctx.slug)
    prose = None
    if path.exists():
        old_fm, prose = split_case_file(path.read_text(encoding="utf-8"))
        if old_fm is None or prose is None:
            raise RouteRefused(f"{ctx.slug}: the case file {ctx.rel(path)} cannot be parsed; it is not written over")
        if _ruled(prose) and (old_fm.get("stopped_at") != step or old_fm.get("exception") != exception):
            archive = path.parent / "archive" / f"{ctx.slug}-{old_fm.get('date', 'undated')}-{old_fm.get('run', 'run')}.md"
            archive.parent.mkdir(parents=True, exist_ok=True)
            n = 1
            while archive.exists():
                n += 1
                archive = archive.with_name(f"{archive.stem.rsplit('-', 1)[0] if n > 2 else archive.stem}-{n}.md")
            path.rename(archive)
            fm["previous"] = ctx.rel(archive)
            prose = None
        elif old_fm.get("previous"):
            fm["previous"] = old_fm["previous"]
    if prose is None:
        prose = "\n".join(f"## {part}\n\n{CASE_PLACEHOLDER[part]}\n" for part in CASE_PARTS)
    _write_case(path, fm, prose)
    return path


def split_case_file(text: str) -> tuple[dict | None, str | None]:
    m = _FRONT.match(text)
    if not m:
        return None, None
    try:
        fm = yaml.safe_load(m.group(1))
    except yaml.YAMLError:
        return None, m.group(2)
    return fm if isinstance(fm, dict) else None, m.group(2)


def check_case_file(path: Path, root: Path | None = None) -> list[str]:
    """The frontmatter against its schema and the three prose parts in order; every problem, or none."""
    path = Path(path)
    if not path.exists():
        return [f"{path}: missing"]
    fm, prose = split_case_file(path.read_text(encoding="utf-8"))
    out: list[str] = []
    if fm is None:
        return [f"{path}: no YAML frontmatter"]
    if isinstance(fm.get("date"), date):
        fm["date"] = fm["date"].isoformat()   # YAML reads an unquoted date as a date
    for key, typ in (("act", str), ("title", str), ("route", str), ("stopped_at", str), ("exception", str), ("tried", list), ("run", str), ("record", str), ("date", str)):
        if key not in fm:
            out.append(f"{path}: missing {key}")
        elif not isinstance(fm[key], typ):
            out.append(f"{path}: {key} is not a {typ.__name__}")
    route = fm.get("route")
    if isinstance(route, str) and route not in sx.ROUTES:
        out.append(f"{path}: route {route!r} is not one of {sorted(sx.ROUTES)}")
    elif isinstance(route, str) and isinstance(fm.get("stopped_at"), str) and fm["stopped_at"] not in ROUTE_STEPS[route]:
        out.append(f"{path}: stopped_at {fm['stopped_at']!r} is not a step of the route {route}")
    if isinstance(fm.get("exception"), str) and not fm["exception"].strip():
        out.append(f"{path}: the exception is empty")
    if isinstance(fm.get("date"), str) and not _DATE.match(fm["date"]):
        out.append(f"{path}: date {fm['date']!r} is not YYYY-MM-DD")
    if isinstance(fm.get("act"), str) and path.stem != fm["act"]:
        out.append(f"{path}: the file is not named after the act {fm['act']!r}")
    if root is not None and isinstance(fm.get("record"), str) and not (Path(root) / fm["record"]).exists():
        out.append(f"{path}: the record {fm['record']} does not exist")
    for k, t in enumerate(fm.get("tried") or []):
        if not isinstance(t, dict) or not isinstance(t.get("step"), str) or t.get("outcome") not in COMPLETED or not isinstance(t.get("evidence"), list):
            out.append(f"{path}: tried[{k}] is not {{run, step, outcome, detail, evidence: [paths]}}")
    for key in fm:
        if key not in CASE_FIELDS + CASE_OPTIONAL:
            out.append(f"{path}: unknown field {key}")
    heads = re.findall(r"^## (.+)$", prose or "", re.M)   # deeper headings inside a part are the writer's
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
        out.extend(check_case_file(case, root))
    return out


def check_list(list_path: Path | None = None, root: Path = ROOT) -> list[str]:
    """The list's own checks, and for every stopped entry a case file that exists and passes its schema."""
    list_path = Path(list_path) if list_path else root / "docs" / "data" / "source-exceptions.yaml"
    out = sx.check(list_path, root)
    if out:
        return out
    for e in sx.load(list_path):
        if e.state == "stopped":
            out.extend(check_case_file(root / e.case_file, root))
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
    r = sub.add_parser("run", help="walk a listed act's route (the real steps of reading/steps.py)")
    r.add_argument("slug"); r.add_argument("--run", required=True)
    r.add_argument("--param", action="append", default=[], help="key=value for the steps")
    a = sub.add_parser("add", help="put an act on the list from a YAML entry file (the investigator's answer form)")
    a.add_argument("entry_file")
    p = sub.add_parser("report"); p.add_argument("--run", required=True)
    c = sub.add_parser("check"); c.add_argument("--run", default=None, help="a run to check; without it, the list's stopped entries")
    args = ap.parse_args(argv)
    if args.cmd == "run":
        from reading.steps import STEPS  # the real steps; imported here so the driver's tests need none of them
        params = dict(kv.split("=", 1) for kv in args.param)
        ctx = context(args.slug, args.run, params=params)
        try:
            out = run_route(ctx, STEPS)
        except RouteRefused as exc:
            print(f"refused  {exc}")
            return 2
        print(f"{out.state:<9} {args.slug}: at {out.step}" + (f": {out.detail}" if out.detail else "")
              + (f" (case file {out.case_file})" if out.case_file else "") + (f" (commit {out.commit})" if out.commit else ""))
        return 0 if out.state == "committed" else 1
    if args.cmd == "add":
        d = yaml.safe_load(Path(args.entry_file).read_text(encoding="utf-8"))
        try:
            e = add_entry(sx.DEFAULT_PATH, sx.Entry(**d))
        except (TypeError, sx.ListError) as exc:
            print(f"refused  {exc}")
            return 2
        print(f"listed   {e.slug}: route {e.route}")
        return 0
    if args.cmd == "report":
        print(report(ROOT / "data" / "runs" / args.run))
        return 0
    problems = check_run(ROOT / "data" / "runs" / args.run) if args.run else check_list()
    for pr in problems:
        print(pr)
    print("ok" if not problems else f"{len(problems)} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
