"""The engine's apply step and the write path's rebuild (reading/steps.py Apply, reading/write.py rebuild_engine), with no network."""
import json

import source_exceptions as sx
from reading import routes, steps, write
from reading.splitter import Block

BODY = """# ЗАКОН за пробата

**Чл. 1.** Този закон урежда пробата.

**Чл. 2.** (1) Пробата е:

1. първа;

2. втора, до 30 000 лв.

(2) Втора алинея.
"""
HTML = ('<html><body><div style=" width: 100%;"><p style="text-align: center">ЗАКОН</p><p style="text-align: center">за изменение на Закона за пробата</p>'
        '<p style="text-align: center">(обн., ДВ, бр. 1 от 2020 г.)</p><p>§ 1. В чл. 2, ал. 1, т. 2 думите „до 30 000 лв.“ се заменят с „до 1 000 000 евро“.</p>'
        '<p>§ 2. Създава се чл. 3:</p><p>„Чл. 3. Нов член.“</p><p>§ 3. Законът влиза в сила от 1 януари 2027 г.</p>'
        '<p>Законът е приет от 52-рото Народно събрание.</p><p style="text-align: right">Председател на Народното събрание: Х</p><p>4984</p></div></body></html>')
ANSWER = {"material": 77, "operations": [
    {"id": "§1", "kind": "replace_words", "address": "чл. 2, ал. 1, т. 2", "old": "q1", "new": "q2"},
    {"id": "§2", "kind": "insert_provision", "address": "чл. 3", "after": "чл. 2", "blocks": [5, 5]},
    {"id": "§3", "kind": "no_text_change", "note": "entry into force"}]}
SLUG = "zakon-za-probata"


def _setup(tmp_path, monkeypatch):
    (tmp_path / "docs" / "data").mkdir(parents=True)
    (tmp_path / "laws").mkdir()
    (tmp_path / "laws" / f"{SLUG}.md").write_text("---\ntitulo: ЗАКОН ЗА ПРОБАТА\nidentificador: '999'\n---\n\n" + BODY, encoding="utf-8")
    sx.save(tmp_path / "docs" / "data" / "source-exceptions.yaml", [sx.Entry(slug=SLUG, title="Закон за пробата", defect="representative", source="dv_html", address="70",
                                                                            route="history", evidence=[{"kind": "plan", "ref": "F1"}], state="listed", added="2026-11-01")])
    cache = tmp_path / "cache"
    cache.mkdir()
    (cache / "77.html").write_text(HTML, encoding="utf-8")
    monkeypatch.setattr(steps, "DV_CACHE", cache)
    ctx = routes.context(SLUG, "r", root=tmp_path)
    ctx.act_dir.mkdir(parents=True)
    (ctx.act_dir / "staged.md").write_text(BODY, encoding="utf-8")
    (ctx.act_dir / "chain.json").write_text(json.dumps({"act": SLUG, "promulgation": {"material": 70, "issue": "1/2020", "date": "2020-01-03"},
                                                        "materials": [{"material": 77, "issue": "96/2026", "date": "2026-11-20", "scopes": ["title"], "kind": "law", "status": "amends_corpus_act", "findings": []}],
                                                        "lexbg_issues": ["1/2020", "96/2026"], "unexplained_lexbg_issues": [], "extra_issues": []}), encoding="utf-8")
    return ctx, cache


def test_the_apply_step_waits_for_the_applier_then_applies_checks_and_records(tmp_path, monkeypatch):
    ctx, cache = _setup(tmp_path, monkeypatch)
    res = steps.STEPS["apply"].run(ctx)
    task = ctx.act_dir / "apply" / "01-77" / "task.md"
    assert res.outcome == "pending" and "one applier call" in res.detail and task.exists()
    text = task.read_text(encoding="utf-8")
    assert "q1: „до 30 000 лв.“" in text and "quoted block 5: „Чл. 3. Нов член.“" in text and "current text at „чл. 2, ал. 1, т. 2“" in text
    (ctx.act_dir / "apply" / "01-77" / "answer.json").write_text(json.dumps(ANSWER, ensure_ascii=False), encoding="utf-8")
    res = steps.STEPS["apply"].run(ctx)
    assert res.outcome == "done" and "replace_words" in res.detail
    applied = (ctx.act_dir / "applied.md").read_text(encoding="utf-8")
    assert "2. (изм. - ДВ, бр. 96 от 2026 г.) втора, до 1 000 000 евро." in applied and "**Чл. 3.** (Нов - ДВ, бр. 96 от 2026 г.) Нов член." in applied
    ops = json.loads((ctx.act_dir / "apply" / "01-77" / "ops.json").read_text(encoding="utf-8"))
    assert [o["kind"] for o in ops["operations"]] == ["replace_words", "insert_provision", "no_text_change"] and ops["operations"][0]["old_ref"] == "q1"
    summary = json.loads((ctx.act_dir / "apply.json").read_text(encoding="utf-8"))
    assert summary["operations_by_kind"] == {"replace_words": 1, "insert_provision": 1, "no_text_change": 1}
    # a second run applies nothing again on the same inputs
    assert steps.STEPS["apply"].run(ctx).outcome == "done"
    # the write path rebuilds the same body from the records, and refuses a body that was altered
    body, rec = write.rebuild_engine(SLUG, ctx.act_dir, cache, BODY)
    assert body == applied and rec["chain"][0]["material"] == 77 and rec["chain"][0]["operations"] == 2   # no_text_change is not counted
    (ctx.act_dir / "applied.md").write_text(applied.replace("Нов член", "Друг член"), encoding="utf-8")
    try:
        write.rebuild_engine(SLUG, ctx.act_dir, cache, BODY)
        assert False, "an altered applied.md must be refused"
    except write.WriteRefused as exc:
        assert "differs from the run's applied.md" in str(exc)
    meta = write.build_frontmatter_dv_chain({"titulo": "ЗАКОН ЗА ПРОБАТА", "identificador": "999", "amendment_history": [{"dv": "1/2020", "date": "2020-01-03"}]},
                                            {"id_mat": 70, "issue_number": 1, "issue_year": 2020, "issue_date": "2020-01-03"}, rec["chain"])
    assert meta["amendment_history"] == [{"dv": "1/2020", "date": "2020-01-03"}, {"dv": "96/2026", "date": "2026-11-20"}] and meta["ultima_actualizacion"] == "2026-11-20"


def test_a_stale_answer_is_set_aside_and_a_child_scope_is_kept(tmp_path, monkeypatch):
    ctx, cache = _setup(tmp_path, monkeypatch)
    steps.STEPS["apply"].run(ctx)
    d = ctx.act_dir / "apply" / "01-77"
    (d / "answer.json").write_text(json.dumps(ANSWER, ensure_ascii=False), encoding="utf-8")
    (ctx.act_dir / "staged.md").write_text(BODY.replace("2. втора, до 30 000 лв.", "2. втора, до 30 000 лв. днес"), encoding="utf-8")   # a provision the task shows changes under the answer
    res = steps.STEPS["apply"].run(ctx)
    # the „current text at“ sections are no part of the task's core: the answer stands, and the apply re-checks it
    assert res.outcome != "pending" and (d / "answer.json").exists() and not (d / "answer.stale-1.json").exists()
    chain = json.loads((ctx.act_dir / "chain.json").read_text(encoding="utf-8"))
    chain["materials"][0]["scopes"] = ["§1"]   # attributed through one § only: that instruction, not the whole material: the core changes
    (ctx.act_dir / "chain.json").write_text(json.dumps(chain), encoding="utf-8")
    res = steps.STEPS["apply"].run(ctx)
    assert res.outcome == "pending" and (d / "answer.stale-1.json").exists() and not (d / "answer.json").exists()
    assert "§2" not in (d / "task.md").read_text(encoding="utf-8").split("## The instructions")[1]
    chain["materials"][0]["scopes"] = ["§9"]
    (ctx.act_dir / "chain.json").write_text(json.dumps(chain), encoding="utf-8")
    assert steps.STEPS["apply"].run(ctx).outcome == "stop"


def test_a_refused_answer_and_a_failed_check_stop_the_act(tmp_path, monkeypatch):
    ctx, cache = _setup(tmp_path, monkeypatch)
    steps.STEPS["apply"].run(ctx)
    bad = {"material": 77, "operations": [{"id": "§1", "kind": "outside_set", "note": "a form the set lacks"}, {"id": "§2", "kind": "no_text_change"}, {"id": "§3", "kind": "no_text_change"}]}
    (ctx.act_dir / "apply" / "01-77" / "answer.json").write_text(json.dumps(bad), encoding="utf-8")
    res = steps.STEPS["apply"].run(ctx)
    assert res.outcome == "stop" and "outside the closed set" in res.detail and not (ctx.act_dir / "applied.md").exists()
