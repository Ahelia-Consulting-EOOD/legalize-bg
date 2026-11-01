"""The real steps of the routes (reading/steps.py): the parts that need no network."""
import json
from pathlib import Path

import source_exceptions as sx
from reading import routes, steps

SLUG = "zakon-za-probata"


def _ctx(tmp_path, **params):
    (tmp_path / "docs" / "data").mkdir(parents=True)
    (tmp_path / "laws").mkdir()
    (tmp_path / "laws" / f"{SLUG}.md").write_text("---\ntitulo: ЗАКОН ЗА ПРОБАТА\nidentificador: '999'\n---\n\n# x\n", encoding="utf-8")
    sx.save(tmp_path / "docs" / "data" / "source-exceptions.yaml", [sx.Entry(slug=SLUG, title="Закон за пробата", defect="dropped_section", source="dv_html",
                                                                            address="77", route="whole_act_from_material",
                                                                            evidence=[{"kind": "plan", "ref": "t"}], state="listed", added="2026-10-31")])
    ctx = routes.context(SLUG, "r", root=tmp_path, params=params)
    ctx.act_dir.mkdir(parents=True)
    return ctx


def test_the_steps_are_the_routes_steps_with_disjoint_outputs(tmp_path):
    ctx = _ctx(tmp_path)
    for route, names in routes.ROUTE_STEPS.items():
        if route == "source_before_archive":
            assert names[0] not in steps.STEPS   # not built (S4): the route stops at once
        else:
            assert all(n in steps.STEPS for n in names), route
    outs = {}
    for name in routes.ROUTE_STEPS["whole_act_from_material"]:
        for p in steps.STEPS[name].outputs(ctx):
            assert p not in outs, f"{name} and {outs[p]} both write {p}"
            outs[p] = name
    assert all(getattr(s, "version", "") for s in steps.STEPS.values())


def _entry_ctx(title):
    e = sx.Entry(slug="x", title=title, defect="dropped_section", source="dv_html", address="1", route="history",
                 evidence=[{"kind": "plan", "ref": "t"}], state="listed", added="2026-10-31")
    return routes.Context(slug="x", run="r", root=Path("."), run_root=Path("r"), list_path=Path("l"), entry=e)


def test_title_words_and_the_amending_phrase_for_a_law_and_a_code():
    c = _entry_ctx("Закон за обществения транспорт")
    assert steps._title_words(c) == "обществения транспорт" and steps._title_parts(c) == ("закон", "за", "обществения транспорт")
    amending = steps._amending_pattern(c)
    assert amending.search("§ 5. в закона за обществения транспорт (обн., дв, бр. 32 от 2026 г.) се правят следните изменения")
    assert amending.search("законът за обществения транспорт се отменя.")
    assert not amending.search("по реда на закона за обществения транспорт се издава")
    code = steps._amending_pattern(_entry_ctx("Кодекс на труда"))
    assert code.search("§ 7. в кодекса на труда (обн., дв, бр. 26 от 1986 г.) се правят следните изменения и допълнения:")
    assert steps._next_issue((2025, 100)) == ((2025, 101), (2026, 1))


def test_the_ladder_step_reads_the_last_report_and_names_the_residue(tmp_path):
    ctx = _ctx(tmp_path)
    (ctx.act_dir / "report-round0.json").write_text(json.dumps({"round": 0, "exceptions": [], "source_findings": [], "residue": [], "residue_classes": {},
                                                                 "source_finding_kinds": {}}), encoding="utf-8")
    res = steps.STEPS["ladder"].run(ctx)
    assert res.outcome == "done" and json.loads((ctx.act_dir / "ladder.json").read_text(encoding="utf-8"))["last_report"] == "report-round0.json"
    (ctx.act_dir / "report-round0.json").write_text(json.dumps({"round": 0, "exceptions": [{"block": 3, "kind": "unknown"}], "source_findings": [],
                                                                 "residue": [3], "residue_classes": {"rule_needed": 1}, "source_finding_kinds": {},
                                                                 "next_round_tasks": 0}), encoding="utf-8")
    res = steps.STEPS["ladder"].run(ctx)
    assert res.outcome == "unchanged" and "rule_needed" in res.detail
    (ctx.act_dir / "report-round0.json").write_text(json.dumps({"round": 0, "exceptions": [{"block": 3, "kind": "unknown"}], "source_findings": [],
                                                                 "residue": [3], "residue_classes": {"labeller_unsure": 1}, "source_finding_kinds": {},
                                                                 "next_round_tasks": 0}), encoding="utf-8")
    assert steps.STEPS["ladder"].run(ctx).outcome == "stop"


def test_the_content_check_lists_an_act_with_lost_text_for_investigation(tmp_path):
    ctx = _ctx(tmp_path)
    (ctx.act_dir / "ladder.json").write_text(json.dumps({"last_report": "report-round2.json"}), encoding="utf-8")
    (ctx.act_dir / "report-round2.json").write_text(json.dumps({"round": 2, "exceptions": [], "source_finding_kinds": {"sign_start": 1},
                                                                 "source_findings": [{"block": 531, "kind": "sign_start", "detail": "the first § of the provisions block is § 2"}]}), encoding="utf-8")
    res = steps.STEPS["content_check"].run(ctx)
    assert res.outcome == "stop" and "lost text (sign_start)" in res.detail and "route investigate" in res.detail
    assert sx.listed(SLUG, ctx.list_path).route == "investigate"
    assert json.loads((ctx.act_dir / "content-check.json").read_text(encoding="utf-8"))["lost_text"][0]["block"] == 531
    (ctx.act_dir / "report-round2.json").write_text(json.dumps({"round": 2, "exceptions": [], "source_finding_kinds": {"malformed_head": 1},
                                                                 "source_findings": [{"block": 9, "kind": "malformed_head", "detail": "x"}]}), encoding="utf-8")
    assert steps.STEPS["content_check"].run(ctx).outcome == "done"


def test_the_investigators_answer_is_held_to_the_form(tmp_path, monkeypatch):
    ctx = _ctx(tmp_path)
    monkeypatch.setattr(steps, "RAW_LEXBG", tmp_path / "nowhere")
    monkeypatch.setattr(steps.raw_fetch_moj, "fetch_one", lambda doc_id, out, **kw: {"outcome": "absent", "status": 500, "url": "u", "fetched_at": "t"})
    sx.update(ctx.list_path, SLUG, source="moj_portal", address="https://justice.government.bg/home/normdoc/999")   # no Gazette material: nothing to fetch
    ctx.entry = sx.listed(SLUG, ctx.list_path)
    step = steps.STEPS["investigate"]
    assert step.run(ctx).outcome == "pending" and (ctx.act_dir / "investigate-task.md").exists()
    (ctx.act_dir / "investigate-answer.yaml").write_text("defect: wrong_text\nsource: nowhere\naddress: ''\nroute: history\nevidence: {}\n", encoding="utf-8")
    res = step.run(ctx)
    assert res.outcome == "stop" and "source 'nowhere'" in res.detail and "address missing" in res.detail and "evidence notes missing" in res.detail
    (ctx.act_dir / "investigate-answer.yaml").write_text("defect: wrong_text\nsource: dv_html\naddress: '242221'\nroute: history\n"
                                                         "evidence:\n  defect: l. 5\n  source: l. 1\n  route: l. 9\n", encoding="utf-8")
    assert step.run(ctx).outcome == "done"
    res = steps.STEPS["route_decision"].run(ctx)
    e = sx.listed(SLUG, ctx.list_path)
    assert res.outcome == "stop" and e.route == "history" and e.state == "investigated" and e.address == "242221" and e.evidence[-1]["kind"] == "case_file"


def test_the_label_step_reads_only_the_labellers_answer_files(tmp_path):
    ctx = _ctx(tmp_path)
    mdir = ctx.act_dir / "maps" / "round0"
    mdir.mkdir(parents=True)
    (mdir / "abcdefabcdef-0000-0007.json").write_text("{}", encoding="utf-8")
    (mdir / "abcdefabcdef-0000-0007.split.json").write_text("{}", encoding="utf-8")
    (mdir / "0003.json").write_text("[]", encoding="utf-8")
    ins = steps.STEPS["label"].inputs(ctx)
    assert [p.name for p in ins if p.parent == mdir] == ["abcdefabcdef-0000-0007.json"]   # the split's files are not the step's inputs
    assert ctx.act_dir / "map.json" in steps.STEPS["ladder"].outputs(ctx) and ctx.act_dir / "staged.md" in steps.STEPS["ladder"].outputs(ctx)
