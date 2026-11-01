"""The route driver (reading/routes.py, step S0) and the exceptions list (source_exceptions.py, step S1)."""
import json
from pathlib import Path

import pytest
import yaml

import source_exceptions as sx
from reading import routes
from reading.routes import RouteRefused, StepResult, check_case_file, check_list, check_run, run_route, run_step

SLUG = "zakon-za-probata"
REPO = Path(__file__).resolve().parents[2]


class FakeStep:
    def __init__(self, name, fn, inputs=(), outputs=()):
        self.name, self.fn, self._in, self._out = name, fn, list(inputs), list(outputs)
        self.calls = 0

    def inputs(self, ctx):
        return [Path(p) if Path(p).is_absolute() else ctx.act_dir / p for p in self._in]

    def outputs(self, ctx):
        return [ctx.act_dir / p for p in self._out]

    def run(self, ctx):
        self.calls += 1
        return self.fn(ctx)


def _writes(name, text="x"):
    def fn(ctx):
        ctx.act_dir.mkdir(parents=True, exist_ok=True)
        (ctx.act_dir / name).write_text(text, encoding="utf-8")
        return StepResult("done", f"wrote {name}", [f"data/runs/{ctx.run}/{SLUG}/{name}"])
    return fn


def _steps(*names):
    return {n: FakeStep(n, _writes(f"{n}.txt"), outputs=[f"{n}.txt"]) for n in names}


def _entry(**kw):
    base = dict(slug=SLUG, title="Закон за пробата", defect="dropped_section", source="dv_html", address="1",
                route="whole_act_from_material", evidence=[{"kind": "plan", "ref": "the test"}], state="listed", added="2026-10-31")
    return sx.Entry(**{**base, **kw})


@pytest.fixture
def root(tmp_path):
    (tmp_path / "laws").mkdir()
    (tmp_path / "laws" / f"{SLUG}.md").write_text("---\ntitulo: x\n---\n\n# x\n", encoding="utf-8")
    (tmp_path / "docs" / "data").mkdir(parents=True)
    sx.save(tmp_path / "docs" / "data" / "source-exceptions.yaml", [_entry()])
    return tmp_path


def _ctx(root, run="r", **params):
    return routes.context(SLUG, run, root=root, params=params)


def _list(root):
    return root / "docs" / "data" / "source-exceptions.yaml"


# the real route and step names with test steps behind them, so the case files pass their schema
A, B, C = "amendment_search", "fetch_material", "prepare"
ROUTES = {"whole_act_from_material": (A, B, C)}
HIST = {"history": ("engine",)}


def test_stop_when_the_steps_are_used_up_writes_a_case_file_and_moves_the_entry(root):
    steps = _steps(A, B, C)
    out = run_route(_ctx(root), steps, routes=ROUTES)
    assert out.state == "stopped" and out.step == C and out.detail == routes.STOP_STEPS_USED_UP
    case = root / "docs" / "cases" / f"{SLUG}.md"
    assert out.case_file == f"docs/cases/{SLUG}.md" and case.exists()
    assert check_case_file(case, root) == []
    fm, prose = routes.split_case_file(case.read_text(encoding="utf-8"))
    assert fm["act"] == SLUG and fm["route"] == "whole_act_from_material" and fm["stopped_at"] == C
    assert [(t["run"], t["step"]) for t in fm["tried"]] == [("r", A), ("r", B), ("r", C)]
    assert fm["tried"][0]["evidence"] == [f"data/runs/r/{SLUG}/{A}.txt"] and fm["record"] == f"data/runs/route-ledger/{SLUG}.json"
    assert "## Lessons learnt" in prose and "## Proposal" in prose and "## The owner's ruling" in prose
    e = sx.listed(SLUG, _list(root))
    assert e.state == "stopped" and e.case_file == f"docs/cases/{SLUG}.md"
    assert check_run(root / "data" / "runs" / "r", root) == [] and check_list(_list(root), root) == []


def test_stop_when_a_step_says_it_changed_nothing_but_not_when_new_inputs_give_the_same_outputs(root):
    ctx = _ctx(root)
    ctx.act_dir.mkdir(parents=True)
    (ctx.act_dir / "in.txt").write_text("1", encoding="utf-8")
    (ctx.act_dir / f"{B}.txt").write_text("x", encoding="utf-8")  # the output exists before the first run: not a stop (review 1, finding 2)
    steps = _steps(A, B, C)
    steps[B] = FakeStep(B, _writes(f"{B}.txt"), inputs=["in.txt"], outputs=[f"{B}.txt"])
    steps[C] = FakeStep(C, lambda c: StepResult("pending", "waiting"), inputs=["answer.json"], outputs=["c.txt"])
    out = run_route(ctx, steps, routes=ROUTES)
    assert out.state == "pending" and out.step == C and steps[B].calls == 1
    (ctx.act_dir / "in.txt").write_text("2", encoding="utf-8")  # the index grew, the same answer: the route goes on (review 2, finding 1)
    out = run_route(ctx, steps, routes=ROUTES)
    assert out.state == "pending" and out.step == C and steps[A].calls == 1 and steps[B].calls == 2
    rec = json.loads(ctx.record_path.read_text(encoding="utf-8"))
    assert [(e["step"], e["outcome"]) for e in rec["steps"] if e["step"] == B] == [(B, "done"), (B, "done")]
    (ctx.act_dir / "in.txt").write_text("3", encoding="utf-8")
    steps[B] = FakeStep(B, lambda c: StepResult("unchanged", "the labeller holds its reading"), inputs=["in.txt"], outputs=[f"{B}.txt"])
    out = run_route(ctx, steps, routes=ROUTES)   # the step itself says it changed nothing: the second fixed point
    assert out.state == "stopped" and out.step == B and out.detail == f"{routes.STOP_UNCHANGED}: {B}"
    assert ctx.record_path == root / "data" / "runs" / "route-ledger" / f"{SLUG}.json"
    assert routes.context(SLUG, "r9", root=root, run_root=root / "elsewhere").record_path == ctx.record_path   # one record per act (finding 6)


def test_stop_when_the_next_step_is_not_defined(root):
    out = run_route(_ctx(root), _steps(A), routes=ROUTES)
    assert out.state == "stopped" and out.step == B and out.detail == f"{routes.STOP_UNDEFINED}: {B}"
    assert (root / "docs" / "cases" / f"{SLUG}.md").exists()


def test_the_real_routes_stop_where_the_engine_and_s4_do_not_exist(root):
    sx.update(_list(root), SLUG, route="history")
    assert run_route(_ctx(root), {}).detail == f"{routes.STOP_UNDEFINED}: engine"
    sx.update(_list(root), SLUG, route="source_before_archive")
    assert run_route(_ctx(root, "r2"), {}).detail == f"{routes.STOP_UNDEFINED}: source_decision"


def test_a_repeated_step_on_the_same_inputs_is_refused_across_runs_and_params_are_inputs(root):
    ctx = _ctx(root)
    shared = root / "shared.txt"   # an input outside the run folder, as the raw store and the material cache are
    shared.write_text("1", encoding="utf-8")
    step = FakeStep(A, _writes("a.txt"), inputs=[shared], outputs=["a.txt"])
    run_step(ctx, step)
    with pytest.raises(RouteRefused, match="already ran on these inputs"):
        run_step(ctx, step)
    with pytest.raises(RouteRefused, match="in run r with outcome done"):
        run_step(_ctx(root, "r2"), step)   # another run, the same inputs: the bound holds across runs (review 1, finding 1)
    with pytest.raises(RouteRefused):
        run_step(_ctx(root, "r2", material="2"), step)   # a parameter the step does not declare changes nothing (round 3, finding 1)
    step.params = ("material",)
    run_step(_ctx(root, "r2", material="2"), step)   # a declared parameter is an input (finding 6)
    shared.write_text("2", encoding="utf-8")
    run_step(ctx, step)
    sx.update(_list(root), SLUG, address="9")   # the entry's fields are inputs too
    run_step(_ctx(root), step)
    assert step.calls == 4


def test_walking_the_route_again_skips_done_steps_and_keeps_a_stop(root):
    steps = _steps(A, B, C)
    ctx = _ctx(root)
    run_route(ctx, steps, routes=ROUTES)
    out = run_route(_ctx(root), steps, routes=ROUTES)   # walked again: nothing runs again, the stop stands
    assert out.state == "stopped" and out.detail == routes.STOP_STEPS_USED_UP
    assert all(s.calls == 1 for s in steps.values())
    with pytest.raises(RouteRefused, match="whose folder holds its outputs"):
        run_route(_ctx(root, "r2"), steps, routes=ROUTES)   # a new run on the same inputs: refused, not run again (finding 1)
    with pytest.raises(RouteRefused, match="the list names the route"):
        run_route(ctx, steps, "history")   # the route comes from the list, never from the command line (finding 3)


def test_altered_outputs_of_a_done_step_are_refused_not_skipped(root):
    steps = _steps(A, B)
    ctx = _ctx(root)
    run_route(ctx, steps, routes={"whole_act_from_material": (A, B)})
    (ctx.act_dir / f"{A}.txt").unlink()
    with pytest.raises(RouteRefused, match=f"outputs of step {A} changed"):
        run_route(_ctx(root), steps, routes={"whole_act_from_material": (A, B)})


def test_a_stopped_act_without_a_case_file_is_refused_by_the_checks(root):
    sx.update(_list(root), SLUG, route="history")
    run_route(_ctx(root), _steps(A))
    case = root / "docs" / "cases" / f"{SLUG}.md"
    case.unlink()
    problems = check_run(root / "data" / "runs" / "r", root)
    assert problems and "without a case file" in problems[0]
    assert check_list(_list(root), root) == [f"{case}: missing"]
    case.write_text("---\nact: other\nroute: nowhere\nexception: ''\n---\n\n## Proposal\n", encoding="utf-8")
    problems = check_case_file(case, root)
    for needle in ("missing stopped_at", "route 'nowhere'", "not named after the act", "prose parts", "exception is empty"):
        assert any(needle in p for p in problems), needle
    case.write_text("---\nact: zakon-za-probata\ntitle: t\nroute: history\nstopped_at: write\nexception: x\ntried: []\nrun: r\nrecord: nowhere.json\ndate: 2026-10-31\n---\n\n"
                    "## Lessons learnt\n\n### a deeper heading is the writer's\n\n## Proposal\n\n## The owner's ruling\n", encoding="utf-8")
    problems = check_case_file(case, root)
    assert problems == [f"{case}: stopped_at 'write' is not a step of the route history", f"{case}: the record nowhere.json does not exist"]


def test_a_pending_step_halts_without_a_case_file_and_is_not_run_again_until_its_inputs_change(root):
    ctx = _ctx(root)
    answered = {"yes": False}

    def waits(c):
        if not answered["yes"]:
            return StepResult("pending", "waiting for the answer")
        return _writes("b.txt")(c)
    steps = {A: FakeStep(A, _writes("a.txt"), outputs=["a.txt"]), B: FakeStep(B, waits, inputs=["answer.json"], outputs=["b.txt"]),
             C: FakeStep(C, lambda c: StepResult("done", "committed", committed="abc1234"), outputs=["c.txt"])}
    out = run_route(ctx, steps, routes=ROUTES)
    assert out.state == "pending" and out.step == B
    assert not (root / "docs" / "cases" / f"{SLUG}.md").exists()
    assert run_route(_ctx(root), steps, routes=ROUTES).state == "pending" and steps[B].calls == 1   # finding 5
    with pytest.raises(RouteRefused, match="is pending on these inputs"):
        run_step(ctx, steps[B])
    ledger = json.loads(ctx.ledger_path.read_text(encoding="utf-8"))
    assert ledger["state"] == "pending" and ledger["entries"][-1]["outcome"] == "pending"
    answered["yes"] = True
    (ctx.act_dir / "answer.json").write_text("{}", encoding="utf-8")
    out = run_route(ctx, steps, routes=ROUTES)
    assert out.state == "committed" and out.commit == "abc1234" and steps[A].calls == 1 and steps[B].calls == 2
    e = sx.listed(SLUG, _list(root))
    assert e.state == "committed" and e.commit == "abc1234"
    assert run_route(ctx, steps, routes=ROUTES).state == "committed" and steps[C].calls == 1   # nothing runs again
    text = routes.report(root / "data" / "runs" / "r", root)
    assert f"committed at {C}, commit abc1234" in text and "distance left: 0 of 1" in text


def test_a_commit_resyncs_the_list_and_resolves_an_earlier_case_file(root):
    steps = {A: FakeStep(A, lambda c: StepResult("done", "committed", committed="abc1234"), outputs=["a.txt"])}
    ctx = _ctx(root)
    run_route(ctx, {}, routes=ROUTES)   # stops: no steps; the case file is written
    case = root / "docs" / "cases" / f"{SLUG}.md"
    assert case.exists()
    out = run_route(_ctx(root, "r2"), steps, routes={"whole_act_from_material": (A,)})
    assert out.state == "committed"
    fm, _ = routes.split_case_file(case.read_text(encoding="utf-8"))
    assert fm["resolved"] == "abc1234" and check_case_file(case, root) == []
    sx.update(_list(root), SLUG, state="listed", commit="")   # the list fell behind the ledger (a crash between the two writes, finding 4)
    assert run_route(_ctx(root, "r2"), steps, routes={"whole_act_from_material": (A,)}).state == "committed"
    assert sx.listed(SLUG, _list(root)).state == "committed"


def test_a_second_stop_keeps_the_prose_unless_the_owner_ruled_on_another_stop(root):
    sx.update(_list(root), SLUG, route="history")
    ctx = _ctx(root)
    run_route(ctx, _steps(A))
    case = root / "docs" / "cases" / f"{SLUG}.md"
    text = case.read_text(encoding="utf-8").replace("(not yet written)", "The engine is F1's.", 1)
    case.write_text(text, encoding="utf-8")
    run_route(_ctx(root, "r2"), _steps(A))   # the same stop again: the prose stays, the frontmatter follows the run
    fm, prose = routes.split_case_file(case.read_text(encoding="utf-8"))
    assert fm["run"] == "r2" and "The engine is F1's." in prose and fm["tried"] == []
    case.write_text(case.read_text(encoding="utf-8").replace("(not yet given)", "Build the engine first."), encoding="utf-8")
    run_route(_ctx(root, "r3"), _steps(A))   # the same stop: the ruling stays with it
    assert "Build the engine first." in case.read_text(encoding="utf-8")
    run_route(_ctx(root, "r4"), {"engine": FakeStep("engine", lambda c: StepResult("stop", "a witness differs"), inputs=[root / "evidence.txt"], outputs=["e.txt"])}, routes=HIST)
    fm, prose = routes.split_case_file(case.read_text(encoding="utf-8"))   # another stop under written prose: the old file is archived (finding 7)
    assert fm["exception"] == "a witness differs" and "(not yet given)" in prose and "(not yet written)" in prose and fm["previous"].startswith("docs/cases/archive/")
    archived = (root / fm["previous"]).read_text(encoding="utf-8")
    assert "Build the engine first." in archived and "The engine is F1's." in archived and check_case_file(case, root) == []
    case.write_text(case.read_text(encoding="utf-8").replace("(not yet written)", "Only a proposal.", 1), encoding="utf-8")
    (root / "evidence.txt").write_text("new", encoding="utf-8")   # a new input: the step runs again (a parameter no step reads changes nothing, round 3 finding 1)
    run_route(_ctx(root, "r5"), {"engine": FakeStep("engine", lambda c: StepResult("stop", "another witness differs"), inputs=[root / "evidence.txt"], outputs=["e.txt"])}, routes=HIST)
    fm, prose = routes.split_case_file(case.read_text(encoding="utf-8"))   # a proposal alone is also written for its stop (review 2, finding 5)
    assert "Only a proposal." not in prose and "Only a proposal." in (root / fm["previous"]).read_text(encoding="utf-8")


def test_an_unparsable_case_file_is_never_written_over(root):
    sx.update(_list(root), SLUG, route="history")
    ctx = _ctx(root)
    run_route(ctx, _steps(A))
    case = root / "docs" / "cases" / f"{SLUG}.md"
    case.write_text("﻿" + case.read_text(encoding="utf-8").replace("(not yet given)", "OWNER RULING"), encoding="utf-8")
    with pytest.raises(RouteRefused, match="cannot be parsed"):
        run_route(_ctx(root, "r2"), _steps(A))
    assert "OWNER RULING" in case.read_text(encoding="utf-8")


def test_an_interrupted_step_is_a_stop_with_a_case_file_and_is_not_rerun_blindly(root):
    ctx = _ctx(root)

    def dies(c):
        raise OSError("disk full")
    step = FakeStep(A, dies, outputs=["a.txt"])
    with pytest.raises(OSError):
        run_step(ctx, step)
    rec = json.loads(ctx.record_path.read_text(encoding="utf-8"))
    assert rec["steps"][-1]["outcome"] == "interrupted"
    with pytest.raises(RouteRefused, match="was interrupted"):
        run_step(ctx, step)
    out = run_route(ctx, {A: step}, routes={"whole_act_from_material": (A,)})   # review 2, finding 3: a stop the owner reads
    assert out.state == "stopped" and out.step == A and "interrupted in run r" in out.detail and step.calls == 1
    fm, _ = routes.split_case_file((root / "docs" / "cases" / f"{SLUG}.md").read_text(encoding="utf-8"))
    assert [t["outcome"] for t in fm["tried"]] == ["interrupted"]   # round 3, finding 7
    assert sx.listed(SLUG, _list(root)).state == "stopped" and check_run(root / "data" / "runs" / "r", root) == []


def test_a_stop_that_is_over_is_cleared_from_the_list_the_ledger_and_the_case_file(root):
    ctx = _ctx(root)
    run_route(ctx, {A: FakeStep(A, _writes("a.txt"), outputs=["a.txt"])}, routes=ROUTES)   # stops: B is not defined
    case = root / "docs" / "cases" / f"{SLUG}.md"
    assert sx.listed(SLUG, _list(root)).state == "stopped" and case.exists()
    steps = {A: FakeStep(A, _writes("a.txt"), outputs=["a.txt"]), B: FakeStep(B, lambda c: StepResult("pending", "waiting"), inputs=["x"], outputs=["b.txt"])}
    out = run_route(ctx, steps, routes=ROUTES)   # B now exists and waits: the act went on (review 2, finding 4)
    assert out.state == "pending" and out.step == B
    e = sx.listed(SLUG, _list(root))
    assert e.state == "listed" and e.case_file == ""   # the state it had before the stop (round 3, finding 4)
    ledger = json.loads(ctx.ledger_path.read_text(encoding="utf-8"))
    assert ledger["state"] == "pending" and ledger["stopped_at"] is None
    fm, _ = routes.split_case_file(case.read_text(encoding="utf-8"))
    assert fm["superseded"] == "the act went on in run r" and check_case_file(case, root) == []
    assert f"{SLUG}: route whole_act_from_material, pending at {B}" in routes.report(root / "data" / "runs" / "r", root)


def test_a_committed_ledger_walked_again_holds_its_commit(root):
    steps = {A: FakeStep(A, lambda c: StepResult("done", "committed", committed="abc1234"), outputs=["a.txt"])}
    run_route(_ctx(root), steps, routes={"whole_act_from_material": (A,)})
    assert run_route(_ctx(root, "r2"), steps, routes={"whole_act_from_material": (A,)}).commit == "abc1234"   # through the skip
    assert run_route(_ctx(root, "r2"), steps, routes={"whole_act_from_material": (A,)}).commit == "abc1234"   # review 2, finding 2
    assert "committed at amendment_search, commit abc1234" in routes.report(root / "data" / "runs" / "r2", root)
    rec = json.loads((root / "data" / "runs" / "route-ledger" / f"{SLUG}.json").read_text(encoding="utf-8"))
    rec["steps"].append(dict(rec["steps"][0]))   # a record that breaks the bound is caught after the fact (finding 8)
    (root / "data" / "runs" / "route-ledger" / f"{SLUG}.json").write_text(json.dumps(rec), encoding="utf-8")
    assert any("ran twice on the same inputs" in p for p in check_run(root / "data" / "runs" / "r", root))
    assert any("ran twice on the same inputs" in p for p in check_list(_list(root), root))


def test_the_report_lists_a_runs_case_files_and_the_distance(root):
    sx.update(_list(root), SLUG, route="history")
    run_route(_ctx(root), _steps(A))
    text = routes.report(root / "data" / "runs" / "r", root)
    assert f"{SLUG}: route history, stopped at engine: {routes.STOP_UNDEFINED}: engine" in text
    assert f"case files to read together (1):\n  docs/cases/{SLUG}.md" in text
    assert "distance left: 1 of 1 entries not yet committed" in text


def test_route_names_are_the_lists_closed_set_and_the_write_step_closes_the_built_route():
    assert set(routes.ROUTE_STEPS) == set(sx.ROUTES)
    assert routes.ROUTE_STEPS["whole_act_from_material"][-1] == "write"


def test_an_unlisted_act_is_refused_and_enters_through_add(root):
    ctx = routes.context("drug-zakon", "r", root=root)
    with pytest.raises(RouteRefused, match="not on the exceptions list"):
        run_route(ctx, {})
    routes.add_entry(_list(root), _entry(slug="drug-zakon", route="history"))
    with pytest.raises(sx.ListError, match="already on the list"):
        routes.add_entry(_list(root), _entry(slug="drug-zakon", route="history"))
    out = run_route(routes.context("drug-zakon", "r", root=root), {})
    assert out.state == "stopped" and "drug-zakon" in routes.report(root / "data" / "runs" / "r", root)


# --- the exceptions list ------------------------------------------------------------------------------

def test_the_list_loads_against_its_schema_and_refuses_what_is_outside_it(tmp_path):
    p = tmp_path / "x.yaml"
    sx.save(p, [_entry()])
    assert [e.slug for e in sx.load(p)] == [SLUG] and p.read_text(encoding="utf-8").startswith(sx.HEADER)
    bad = yaml.safe_load(p.read_text(encoding="utf-8"))
    bad["entries"][0]["route"] = "somewhere"
    bad["entries"][0]["defect"] = "bad"
    del bad["entries"][0]["evidence"]
    bad["entries"].append(dict(bad["entries"][0], route="history", defect="wrong_text", evidence=[{"kind": "plan", "ref": "x"}]))
    p.write_text(yaml.safe_dump(bad, allow_unicode=True), encoding="utf-8")
    with pytest.raises(sx.ListError) as exc:
        sx.load(p)
    msg = str(exc.value)
    assert "route 'somewhere'" in msg and "defect 'bad'" in msg and "missing evidence" in msg and "a second entry for" in msg
    with pytest.raises(sx.ListError, match="entries"):
        p.write_text("- a\n", encoding="utf-8"); sx.load(p)


def test_add_refuses_a_second_entry_and_update_keeps_the_form(tmp_path):
    p = tmp_path / "x.yaml"
    sx.save(p, [])
    sx.add(p, _entry())
    with pytest.raises(sx.ListError, match="already on the list"):
        sx.add(p, _entry())
    with pytest.raises(sx.ListError, match="state 'gone'"):
        sx.update(p, SLUG, state="gone")
    with pytest.raises(sx.ListError, match="a stopped entry names its case file"):
        sx.update(p, SLUG, state="stopped")
    sx.update(p, SLUG, state="stopped", case_file="docs/cases/x.md")
    assert sx.listed(SLUG, p).case_file == "docs/cases/x.md"
    assert sx.listed("other", p) is None
    rows = sx.distance(sx.load(p))
    assert rows[0]["distance"] == "not committed: stopped (docs/cases/x.md)"


def test_the_repositorys_list_runs_and_case_files_pass_their_checks():
    """The checks that block, over what the repository tracks: the list, every stopped entry's case file, every run's stopped acts."""
    assert check_list(sx.DEFAULT_PATH, REPO) == []
    entries = sx.load()
    assert [e.slug for e in entries][:1] == ["zakon-za-obshtestveniya-transport"]
    assert all(e.route in sx.ROUTES for e in entries)
    assert sx.report().startswith("distance left:")
    for run_root in sorted((REPO / "data" / "runs").glob("*")):
        if run_root.is_dir() and run_root.name != routes.STEP_RECORDS:
            assert check_run(run_root, REPO) == [], run_root.name
    for case in sorted((REPO / "docs" / "cases").glob("*.md")):
        assert check_case_file(case, REPO) == [], case.name


def test_a_stop_reached_again_on_the_same_inputs_stands_without_running_the_step(root):
    step = FakeStep(A, lambda c: StepResult("stop", "an amendment found"), outputs=["a.txt"])
    ctx = _ctx(root)
    run_route(ctx, {A: step}, routes={"whole_act_from_material": (A, B)})
    for k in range(3):
        out = run_route(_ctx(root, f"r{k}", attempt=str(k)), {A: step}, routes={"whole_act_from_material": (A, B)})   # the plan's second fixed point
        assert out.state == "stopped" and out.detail == "an amendment found"
    assert step.calls == 1 and check_run(root / "data" / "runs" / "r", root) == []
    held = FakeStep(B, lambda c: StepResult("unchanged", "the labeller holds its reading"), outputs=["b.txt"])
    a2 = FakeStep(A, _writes("a.txt"), outputs=["a.txt"])
    a2.version = "2"   # a changed step runs again on the same files
    ctx2 = routes.context(SLUG, "s", root=root)
    sx.update(_list(root), SLUG, state="listed", case_file="")
    run_route(ctx2, {A: a2, B: held}, routes={"whole_act_from_material": (A, B)})
    out = run_route(ctx2, {A: a2, B: held}, routes={"whole_act_from_material": (A, B)})
    assert out.detail == f"{routes.STOP_UNCHANGED}: {B}" and held.calls == 1


def test_the_drivers_own_files_are_never_a_steps_input(root):
    step = FakeStep(A, lambda c: StepResult("stop", "x"), inputs=[Path(".")], outputs=["a.txt"])
    step._in = []
    step.inputs = lambda ctx: [ctx.act_dir]   # the whole run folder, the ledger included (round 3, finding 3)
    ctx = _ctx(root)
    for _ in range(3):
        run_route(ctx, {A: step}, routes={"whole_act_from_material": (A,)})
    assert step.calls == 1


def test_a_finished_stops_prose_is_archived_before_a_new_stop_with_the_same_words(root):
    held = FakeStep(A, lambda c: StepResult("unchanged", "held"), inputs=[root / "in.txt"], outputs=["a.txt"])
    (root / "in.txt").write_text("1", encoding="utf-8")
    ctx = _ctx(root)
    run_route(ctx, {A: held}, routes={"whole_act_from_material": (A,)})
    case = root / "docs" / "cases" / f"{SLUG}.md"
    case.write_text(case.read_text(encoding="utf-8").replace("(not yet given)", "RULING-1"), encoding="utf-8")
    (root / "in.txt").write_text("2", encoding="utf-8")
    done = FakeStep(A, lambda c: StepResult("done", "committed", committed="c0ffee"), inputs=[root / "in.txt"], outputs=["a.txt"])
    assert run_route(_ctx(root, "r2"), {A: done}, routes={"whole_act_from_material": (A,)}).state == "committed"
    assert routes.split_case_file(case.read_text(encoding="utf-8"))[0]["resolved"] == "c0ffee"
    (root / "in.txt").write_text("3", encoding="utf-8")
    sx.update(_list(root), SLUG, state="listed", commit="")
    run_route(_ctx(root, "r3"), {A: held}, routes={"whole_act_from_material": (A,)})   # the same stop words, after a finished stop (round 3, finding 2)
    fm, prose = routes.split_case_file(case.read_text(encoding="utf-8"))
    assert "RULING-1" not in prose and "resolved" not in fm and fm["previous"].startswith("docs/cases/archive/")
    assert "RULING-1" in (root / fm["previous"]).read_text(encoding="utf-8")
    assert [t["outcome"] for t in fm["tried"]].count("interrupted") == 0


def test_a_walk_halts_before_a_named_step_without_a_stop(root):
    steps = _steps(A, B, C)
    out = run_route(_ctx(root), steps, routes=ROUTES, until=C)
    assert out.state == "halted" and out.step == C and steps[C].calls == 0 and steps[B].calls == 1
    assert not (root / "docs" / "cases" / f"{SLUG}.md").exists() and sx.listed(SLUG, _list(root)).state == "listed"
    assert json.loads(_ctx(root).ledger_path.read_text(encoding="utf-8"))["state"] == "halted"
    out = run_route(_ctx(root), steps, routes=ROUTES)
    assert out.state == "stopped" and steps[C].calls == 1
