"""The route driver (reading/routes.py, step S0) and the exceptions list (source_exceptions.py, step S1)."""
import json
from pathlib import Path

import pytest
import yaml

import source_exceptions as sx
from reading import routes
from reading.routes import RouteRefused, StepResult, check_case_file, check_run, run_route, run_step

SLUG = "zakon-za-probata"


class FakeStep:
    def __init__(self, name, fn, inputs=(), outputs=()):
        self.name, self.fn, self._in, self._out = name, fn, list(inputs), list(outputs)
        self.calls = 0

    def inputs(self, ctx):
        return [ctx.act_dir / p for p in self._in]

    def outputs(self, ctx):
        return [ctx.act_dir / p for p in self._out]

    def run(self, ctx):
        self.calls += 1
        return self.fn(ctx)


def _writes(name, text="x"):
    def fn(ctx):
        ctx.act_dir.mkdir(parents=True, exist_ok=True)
        (ctx.act_dir / name).write_text(text, encoding="utf-8")
        return StepResult("done", f"wrote {name}", [f"data/runs/r/{SLUG}/{name}"])
    return fn


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


def _ctx(root, run="r"):
    return routes.context(SLUG, run, root=root)


ROUTES = {"whole_act_from_material": ("a", "b", "c")}  # the real route name with test steps, so the case file passes its schema


def test_stop_when_the_steps_are_used_up_writes_a_case_file_and_moves_the_entry(root):
    steps = {"a": FakeStep("a", _writes("a.txt"), outputs=["a.txt"]), "b": FakeStep("b", _writes("b.txt"), outputs=["b.txt"]),
             "c": FakeStep("c", _writes("c.txt"), outputs=["c.txt"])}
    out = run_route(_ctx(root), steps, "whole_act_from_material", routes=ROUTES)
    assert out.state == "stopped" and out.step == "c" and out.detail == routes.STOP_STEPS_USED_UP
    case = root / "docs" / "cases" / f"{SLUG}.md"
    assert out.case_file == f"docs/cases/{SLUG}.md" and case.exists()
    assert check_case_file(case) == []
    fm, prose = routes.split_case_file(case.read_text(encoding="utf-8"))
    assert fm["act"] == SLUG and fm["route"] == "whole_act_from_material" and fm["stopped_at"] == "c" and [t["step"] for t in fm["tried"]] == ["a", "b", "c"]
    assert fm["tried"][0]["evidence"] == [f"data/runs/r/{SLUG}/a.txt"]
    assert "## Lessons learnt" in prose and "## Proposal" in prose and "## The owner's ruling" in prose
    e = sx.listed(SLUG, root / "docs" / "data" / "source-exceptions.yaml")
    assert e.state == "stopped" and e.case_file == f"docs/cases/{SLUG}.md"
    assert check_run(root / "data" / "runs" / "r", root) == []


def test_stop_when_a_step_changes_nothing(root):
    ctx = _ctx(root)
    ctx.act_dir.mkdir(parents=True)
    (ctx.act_dir / "b.txt").write_text("x", encoding="utf-8")  # b rewrites the same content: nothing changes
    steps = {"a": FakeStep("a", _writes("a.txt"), outputs=["a.txt"]), "b": FakeStep("b", _writes("b.txt"), outputs=["b.txt"]),
             "c": FakeStep("c", _writes("c.txt"), outputs=["c.txt"])}
    out = run_route(ctx, steps, "whole_act_from_material", routes=ROUTES)
    assert out.state == "stopped" and out.step == "b" and out.detail == f"{routes.STOP_UNCHANGED}: b"
    assert steps["c"].calls == 0
    ledger = json.loads(ctx.ledger_path.read_text(encoding="utf-8"))
    assert [e["outcome"] for e in ledger["entries"]] == ["done", "unchanged"] and ledger["state"] == "stopped"


def test_stop_when_the_next_step_is_not_defined(root):
    steps = {"a": FakeStep("a", _writes("a.txt"), outputs=["a.txt"])}
    out = run_route(_ctx(root), steps, "whole_act_from_material", routes=ROUTES)
    assert out.state == "stopped" and out.step == "b" and out.detail == f"{routes.STOP_UNDEFINED}: b"
    assert (root / "docs" / "cases" / f"{SLUG}.md").exists()


def test_the_real_routes_stop_where_the_engine_and_s4_do_not_exist(root):
    steps = {}
    assert run_route(_ctx(root), steps, "history").detail == f"{routes.STOP_UNDEFINED}: engine"
    out = run_route(_ctx(root, "r2"), steps, "source_before_archive")
    assert out.detail == f"{routes.STOP_UNDEFINED}: source_decision"


def test_a_repeated_step_on_the_same_inputs_is_refused(root):
    ctx = _ctx(root)
    ctx.act_dir.mkdir(parents=True)
    (ctx.act_dir / "in.txt").write_text("1", encoding="utf-8")
    step = FakeStep("a", _writes("a.txt"), inputs=["in.txt"], outputs=["a.txt"])
    run_step(ctx, step)
    with pytest.raises(RouteRefused, match="already ran on these inputs"):
        run_step(ctx, step)
    (ctx.act_dir / "in.txt").write_text("2", encoding="utf-8")
    run_step(ctx, step)  # new inputs: runs
    assert step.calls == 2


def test_walking_the_route_again_skips_done_steps_and_keeps_a_stop(root):
    steps = {"a": FakeStep("a", _writes("a.txt"), outputs=["a.txt"]), "b": FakeStep("b", _writes("b.txt"), outputs=["b.txt"]),
             "c": FakeStep("c", _writes("c.txt"), outputs=["c.txt"])}
    ctx = _ctx(root)
    run_route(ctx, steps, "whole_act_from_material", routes=ROUTES)
    out = run_route(ctx, steps, "whole_act_from_material", routes=ROUTES)
    assert out.state == "stopped" and out.detail == routes.STOP_STEPS_USED_UP
    assert all(s.calls == 1 for s in steps.values())
    with pytest.raises(RouteRefused, match="not changed inside a run"):
        run_route(ctx, steps, "history")


def test_a_stopped_act_without_a_case_file_is_refused_by_the_check(root):
    steps = {"a": FakeStep("a", _writes("a.txt"), outputs=["a.txt"])}
    run_route(_ctx(root), steps, "history")
    case = root / "docs" / "cases" / f"{SLUG}.md"
    case.unlink()
    problems = check_run(root / "data" / "runs" / "r", root)
    assert problems and "without a case file" in problems[0]
    case.write_text("---\nact: other\nroute: nowhere\n---\n\n## Proposal\n", encoding="utf-8")
    problems = check_case_file(case)
    assert any("missing stopped_at" in p for p in problems) and any("route 'nowhere'" in p for p in problems)
    assert any("not named after the act" in p for p in problems) and any("prose parts" in p for p in problems)


def test_a_pending_step_halts_without_a_case_file_and_continues_later(root):
    ctx = _ctx(root)
    answered = {"yes": False}

    def waits(c):
        if not answered["yes"]:
            return StepResult("pending", "waiting for the answer")
        return _writes("b.txt")(c)
    steps = {"a": FakeStep("a", _writes("a.txt"), outputs=["a.txt"]), "b": FakeStep("b", waits, inputs=["answer.json"], outputs=["b.txt"]),
             "c": FakeStep("c", lambda c: StepResult("done", "committed", committed="abc1234"), outputs=["c.txt"])}
    out = run_route(ctx, steps, "whole_act_from_material", routes=ROUTES)
    assert out.state == "pending" and out.step == "b"
    assert not (root / "docs" / "cases" / f"{SLUG}.md").exists()
    ledger = json.loads(ctx.ledger_path.read_text(encoding="utf-8"))
    assert ledger["state"] == "pending" and ledger["entries"][-1]["outcome"] == "pending"
    answered["yes"] = True
    (ctx.act_dir / "answer.json").write_text("{}", encoding="utf-8")
    out = run_route(ctx, steps, "whole_act_from_material", routes=ROUTES)
    assert out.state == "committed" and out.commit == "abc1234" and steps["a"].calls == 1
    e = sx.listed(SLUG, root / "docs" / "data" / "source-exceptions.yaml")
    assert e.state == "committed" and e.commit == "abc1234"
    assert run_route(ctx, steps, "whole_act_from_material", routes=ROUTES).state == "committed"  # nothing runs again
    assert steps["c"].calls == 1
    text = routes.report(root / "data" / "runs" / "r", root)
    assert "committed at c, commit abc1234" in text and "distance left: 0 of 1" in text


def test_a_second_stop_keeps_the_case_files_prose(root):
    steps = {"a": FakeStep("a", _writes("a.txt"), outputs=["a.txt"])}
    ctx = _ctx(root)
    run_route(ctx, steps, "history")
    case = root / "docs" / "cases" / f"{SLUG}.md"
    text = case.read_text(encoding="utf-8").replace("(not yet written)", "The engine is F1's.", 1)
    case.write_text(text, encoding="utf-8")
    ctx2 = _ctx(root, "r2")
    run_route(ctx2, steps, "history")
    fm, prose = routes.split_case_file(case.read_text(encoding="utf-8"))
    assert fm["run"] == "r2" and "The engine is F1's." in prose


def test_the_report_lists_a_runs_case_files_and_the_distance(root):
    steps = {"a": FakeStep("a", _writes("a.txt"), outputs=["a.txt"])}
    run_route(_ctx(root), steps, "history")
    text = routes.report(root / "data" / "runs" / "r", root)
    assert f"{SLUG}: route history, stopped at engine: {routes.STOP_UNDEFINED}: engine" in text
    assert f"case files to read together (1):\n  docs/cases/{SLUG}.md" in text
    assert "distance left: 1 of 1 entries not yet committed" in text


def test_route_names_are_the_lists_closed_set():
    assert set(routes.ROUTE_STEPS) == set(sx.ROUTES)
    assert all(steps[-1] == "write" for name, steps in routes.ROUTE_STEPS.items() if name == "whole_act_from_material")


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


def test_the_repositorys_list_passes_its_checks_and_every_entry_names_a_route():
    assert sx.check() == []
    entries = sx.load()
    assert [e.slug for e in entries][:1] == ["zakon-za-obshtestveniya-transport"]
    assert all(e.route in sx.ROUTES for e in entries)
    assert sx.report().startswith("distance left:")


def test_an_unlisted_act_without_a_route_is_refused(root):
    ctx = routes.context("drug-zakon", "r", root=root)
    with pytest.raises(RouteRefused, match="not on the exceptions list"):
        run_route(ctx, {}, None)
