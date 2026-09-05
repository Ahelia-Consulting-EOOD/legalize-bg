"""The `python -m fetcher.dv` command line, driven by a fake session."""

import json
import logging

import pytest

from fetcher.dv.__main__ import main
from fetcher.dv.issues import ISSUE_LIST_PATH
from fetcher.dv.materials import MATERIALS_PATH, MATERIAL_PATH

from .conftest import FakeSession
from .test_materials import ERROR_PAGE


def read_jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


# --- issues ---------------------------------------------------------------


def test_issues_writes_one_line_per_issue(tmp_path, issue_page1, issue_page2):
    out = tmp_path / "issues.jsonl"
    session = FakeSession(
        get_bodies={ISSUE_LIST_PATH: issue_page1}, post_bodies={2: issue_page2}
    )
    assert main(["issues", "--out", str(out), "--max-pages", "2"], session=session) == 0
    rows = read_jsonl(out)
    assert len(rows) == 20
    assert rows[0] == {
        "year": 2026,
        "number": 81,
        "date": "2026-09-04",
        "id_obj": 12640,
        "section": 1,
        "extraordinary": False,
    }
    assert rows[-1]["id_obj"] == 12599
    assert [r["number"] for r in rows if r["extraordinary"]] == [78, 75]


def test_issues_output_is_utf8_and_not_escaped(tmp_path, issue_page1):
    out = tmp_path / "issues.jsonl"
    session = FakeSession(get_bodies={ISSUE_LIST_PATH: issue_page1})
    main(["issues", "--out", str(out), "--max-pages", "1"], session=session)
    text = out.read_text(encoding="utf-8")
    assert "\\u" not in text


def test_issues_resume_skips_ids_already_written(tmp_path, issue_page1, issue_page2):
    out = tmp_path / "issues.jsonl"
    session = FakeSession(
        get_bodies={ISSUE_LIST_PATH: issue_page1}, post_bodies={2: issue_page2}
    )
    main(["issues", "--out", str(out), "--max-pages", "1"], session=session)
    assert len(read_jsonl(out)) == 10

    session2 = FakeSession(
        get_bodies={ISSUE_LIST_PATH: issue_page1}, post_bodies={2: issue_page2}
    )
    main(
        ["issues", "--out", str(out), "--max-pages", "2", "--resume"], session=session2
    )
    rows = read_jsonl(out)
    assert len(rows) == 20
    assert len({r["id_obj"] for r in rows}) == 20


def test_issues_without_resume_rewrites_the_file(tmp_path, issue_page1):
    out = tmp_path / "issues.jsonl"
    out.write_text('{"id_obj": 1}\n', encoding="utf-8")
    session = FakeSession(get_bodies={ISSUE_LIST_PATH: issue_page1})
    main(["issues", "--out", str(out), "--max-pages", "1"], session=session)
    rows = read_jsonl(out)
    assert len(rows) == 10
    assert 1 not in {r["id_obj"] for r in rows}


# --- materials ------------------------------------------------------------


def write_issues(tmp_path, *id_objs):
    path = tmp_path / "issues.jsonl"
    with path.open("w", encoding="utf-8") as fh:
        for i, id_obj in enumerate(id_objs):
            fh.write(
                json.dumps(
                    {
                        "year": 2016,
                        "number": 70 + i,
                        "date": "2016-09-20",
                        "id_obj": id_obj,
                        "section": 1,
                        "extraordinary": False,
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )
    return path


def test_materials_writes_one_line_per_material(
    tmp_path, materials_html, materials_empty_html
):
    issues = write_issues(tmp_path, 6121, 5000, 9999)
    out = tmp_path / "materials.jsonl"
    session = FakeSession(
        by_param={
            ("idObj", 6121): materials_html,
            ("idObj", 5000): materials_empty_html,
            ("idObj", 9999): ERROR_PAGE,
        }
    )
    assert (
        main(
            ["materials", "--issues", str(issues), "--out", str(out)], session=session
        )
        == 0
    )
    rows = read_jsonl(out)
    assert len(rows) == 20  # 18 materials + one empty + one error page
    ok = [r for r in rows if r["status"] == "ok"]
    assert len(ok) == 18
    assert ok[0]["id_mat"] == 107486
    assert ok[0]["id_obj"] == 6121
    assert ok[0]["issue_number"] == 70
    assert ok[3]["title"].endswith("Административнопроцесуалния кодекс")

    empties = [r for r in rows if r["status"] == "empty"]
    assert [r["id_obj"] for r in empties] == [5000]
    assert "id_mat" not in empties[0]

    errors = [r for r in rows if r["status"] == "error_page"]
    assert [r["id_obj"] for r in errors] == [9999]


def test_materials_limit_stops_early(tmp_path, materials_html, materials_empty_html):
    issues = write_issues(tmp_path, 6121, 5000)
    out = tmp_path / "materials.jsonl"
    session = FakeSession(
        by_param={
            ("idObj", 6121): materials_html,
            ("idObj", 5000): materials_empty_html,
        }
    )
    main(
        ["materials", "--issues", str(issues), "--out", str(out), "--limit", "1"],
        session=session,
    )
    assert {r["id_obj"] for r in read_jsonl(out)} == {6121}
    assert len(session.gets) == 1


def test_materials_resume_skips_issues_already_done(
    tmp_path, materials_html, materials_empty_html
):
    issues = write_issues(tmp_path, 6121, 5000, 9999)
    out = tmp_path / "materials.jsonl"
    session = FakeSession(
        by_param={
            ("idObj", 6121): materials_html,
            ("idObj", 5000): materials_empty_html,
        }
    )
    main(
        ["materials", "--issues", str(issues), "--out", str(out), "--limit", "2"],
        session=session,
    )
    assert len(read_jsonl(out)) == 19

    session2 = FakeSession(
        by_param={
            ("idObj", 5000): materials_empty_html,
            ("idObj", 9999): ERROR_PAGE,
        }
    )
    main(
        ["materials", "--issues", str(issues), "--out", str(out), "--resume"],
        session=session2,
    )
    rows = read_jsonl(out)
    assert len(rows) == 20
    # 6121 was finished before the last issue started, so it is not asked
    # for again; 5000 was last in the file and may have been cut short.
    assert [g[1]["idObj"] for g in session2.gets] == [5000, 9999]


def test_materials_records_an_isolated_gap_without_halting(
    tmp_path, materials_html, materials_empty_html
):
    # Four gaps around good issues: sparse ids, not an outage.
    issues = write_issues(tmp_path, 6121, 9001, 9002, 5000, 9003, 9004)
    out = tmp_path / "materials.jsonl"
    session = FakeSession(
        by_param={
            ("idObj", 6121): materials_html,
            ("idObj", 5000): materials_empty_html,
            ("idObj", 9001): ERROR_PAGE,
            ("idObj", 9002): ERROR_PAGE,
            ("idObj", 9003): ERROR_PAGE,
            ("idObj", 9004): ERROR_PAGE,
        }
    )
    assert (
        main(["materials", "--issues", str(issues), "--out", str(out)], session=session)
        == 0
    )
    rows = read_jsonl(out)
    assert [r["id_obj"] for r in rows if r["status"] == "error_page"] == [
        9001, 9002, 9003, 9004,
    ]
    assert len(session.gets) == 6


# --- an outage is not a corpus of gaps ------------------------------------


def test_a_run_of_error_pages_halts_the_sweep(tmp_path, materials_html):
    # Six stubs in a row is an outage, not six neighbouring gaps in a
    # sparse id space. Recording them would be a permanent false claim
    # that the Gazette holds nothing for those issues.
    issues = write_issues(tmp_path, 6121, *range(9001, 9007))
    out = tmp_path / "materials.jsonl"
    session = FakeSession(
        by_param={("idObj", 6121): materials_html},
        get_bodies={MATERIALS_PATH: ERROR_PAGE},
    )
    assert (
        main(["materials", "--issues", str(issues), "--out", str(out)], session=session)
        != 0
    )
    # It stopped at the fifth stub rather than walking all six.
    assert [g[1]["idObj"] for g in session.gets] == [6121, 9001, 9002, 9003, 9004, 9005]


def test_the_halt_names_the_last_good_issue(tmp_path, materials_html, caplog):
    issues = write_issues(tmp_path, 6121, *range(9001, 9007))
    out = tmp_path / "materials.jsonl"
    session = FakeSession(
        by_param={("idObj", 6121): materials_html},
        get_bodies={MATERIALS_PATH: ERROR_PAGE},
    )
    with caplog.at_level(logging.ERROR, logger="fetcher.dv"):
        main(["materials", "--issues", str(issues), "--out", str(out)], session=session)
    message = "\n".join(r.getMessage() for r in caplog.records)
    assert "6121" in message
    assert "--resume" in message


def test_the_stub_run_that_halts_is_not_recorded(tmp_path, materials_html):
    # The whole point of halting is that those rows are probably false, so
    # they must not survive into the output for the coverage map to read.
    issues = write_issues(tmp_path, 6121, *range(9001, 9007))
    out = tmp_path / "materials.jsonl"
    session = FakeSession(
        by_param={("idObj", 6121): materials_html},
        get_bodies={MATERIALS_PATH: ERROR_PAGE},
    )
    main(["materials", "--issues", str(issues), "--out", str(out)], session=session)
    rows = read_jsonl(out)
    assert {r["status"] for r in rows} == {"ok"}
    assert {r["id_obj"] for r in rows} == {6121}


def test_the_consecutive_error_limit_is_configurable(tmp_path, materials_html):
    issues = write_issues(tmp_path, 6121, *range(9001, 9007))
    out = tmp_path / "materials.jsonl"
    session = FakeSession(
        by_param={("idObj", 6121): materials_html},
        get_bodies={MATERIALS_PATH: ERROR_PAGE},
    )
    assert (
        main(
            [
                "materials",
                "--issues", str(issues),
                "--out", str(out),
                "--max-consecutive-errors", "2",
            ],
            session=session,
        )
        != 0
    )
    assert [g[1]["idObj"] for g in session.gets] == [6121, 9001, 9002]


def test_a_halted_run_is_resumable(tmp_path, materials_html, materials_empty_html):
    issues = write_issues(tmp_path, 6121, *range(9001, 9007))
    out = tmp_path / "materials.jsonl"
    down = FakeSession(
        by_param={("idObj", 6121): materials_html},
        get_bodies={MATERIALS_PATH: ERROR_PAGE},
    )
    assert main(
        ["materials", "--issues", str(issues), "--out", str(out)], session=down
    ) != 0

    healthy = FakeSession(
        by_param={("idObj", 6121): materials_html},
        get_bodies={MATERIALS_PATH: materials_empty_html},
    )
    assert (
        main(
            ["materials", "--issues", str(issues), "--out", str(out), "--resume"],
            session=healthy,
        )
        == 0
    )
    rows = read_jsonl(out)
    assert sorted(r["id_obj"] for r in rows if r["status"] == "empty") == list(
        range(9001, 9007)
    )
    assert len([r for r in rows if r["status"] == "ok"]) == 18


# --- unreadable markup is not a fact about the Gazette --------------------


def test_unrecognized_markup_is_written_as_its_own_status(
    tmp_path, materials_html, materials_empty_html
):
    broken = materials_html.replace("material_form:dataTable1", "material_form:grid1")
    issues = write_issues(tmp_path, 6121, 5000)
    out = tmp_path / "materials.jsonl"
    session = FakeSession(
        by_param={("idObj", 6121): broken, ("idObj", 5000): materials_empty_html}
    )
    assert (
        main(["materials", "--issues", str(issues), "--out", str(out)], session=session)
        == 0
    )
    rows = read_jsonl(out)
    assert [(r["id_obj"], r["status"]) for r in rows] == [
        (6121, "unrecognized"),
        (5000, "empty"),
    ]


def test_resume_comes_back_to_the_pages_it_could_not_read(
    tmp_path, materials_html, materials_empty_html
):
    # `unrecognized` means „fix the parser and try again“, so resuming
    # must not treat it as an issue already done. Otherwise the run after
    # the fix skips exactly the issues the fix was for.
    broken = materials_html.replace("material_form:dataTable1", "material_form:grid1")
    issues = write_issues(tmp_path, 6121, 5000, 9999)
    out = tmp_path / "materials.jsonl"
    session = FakeSession(
        by_param={
            ("idObj", 6121): broken,
            ("idObj", 5000): materials_empty_html,
            ("idObj", 9999): materials_empty_html,
        }
    )
    main(["materials", "--issues", str(issues), "--out", str(out)], session=session)
    assert [r["status"] for r in read_jsonl(out)] == [
        "unrecognized", "empty", "empty",
    ]

    fixed = FakeSession(
        by_param={
            ("idObj", 6121): materials_html,
            ("idObj", 9999): materials_empty_html,
        }
    )
    main(
        ["materials", "--issues", str(issues), "--out", str(out), "--resume"],
        session=fixed,
    )
    # 6121 because it was unreadable, 9999 because it was last in the file.
    assert [g[1]["idObj"] for g in fixed.gets] == [6121, 9999]
    rows = read_jsonl(out)
    assert len([r for r in rows if r["id_obj"] == 6121 and r["status"] == "ok"]) == 18
    assert not [r for r in rows if r["status"] == "unrecognized"]


def test_a_run_of_unrecognized_pages_halts_the_sweep(tmp_path, materials_html):
    # A markup rename would otherwise write 4,146 false rows. Eleven
    # unreadable pages inside the first fifty is already a redesign.
    broken = materials_html.replace("material_form:dataTable1", "material_form:grid1")
    issues = write_issues(tmp_path, *range(9001, 9021))
    out = tmp_path / "materials.jsonl"
    session = FakeSession(get_bodies={MATERIALS_PATH: broken})
    assert (
        main(["materials", "--issues", str(issues), "--out", str(out)], session=session)
        != 0
    )
    assert len(session.gets) == 11
    assert len(read_jsonl(out)) == 11


# --- resume must not trust a half-written issue ---------------------------


def test_resume_refetches_the_issue_whose_listing_was_cut_in_half(
    tmp_path, materials_html, materials_empty_html
):
    # The 18-material issue truncated to five rows stands for a run killed
    # between two lines of the same issue. Marking that issue done would
    # lose thirteen materials silently and for good.
    issues = write_issues(tmp_path, 6121, 5000)
    out = tmp_path / "materials.jsonl"
    session = FakeSession(by_param={("idObj", 6121): materials_html})
    main(
        ["materials", "--issues", str(issues), "--out", str(out), "--limit", "1"],
        session=session,
    )
    kept = out.read_text(encoding="utf-8").splitlines()[:5]
    out.write_text("\n".join(kept) + "\n", encoding="utf-8")

    session2 = FakeSession(
        by_param={("idObj", 6121): materials_html, ("idObj", 5000): materials_empty_html}
    )
    assert (
        main(
            ["materials", "--issues", str(issues), "--out", str(out), "--resume"],
            session=session2,
        )
        == 0
    )
    rows = read_jsonl(out)
    assert [g[1]["idObj"] for g in session2.gets] == [6121, 5000]
    assert len([r for r in rows if r["id_obj"] == 6121]) == 18
    assert [r["position"] for r in rows if r["id_obj"] == 6121] == list(range(1, 19))
    assert [r["id_obj"] for r in rows if r["status"] == "empty"] == [5000]


def test_resume_drops_a_truncated_final_line(
    tmp_path, materials_html, materials_empty_html
):
    # A kill between the write and the flush leaves half a JSON object on
    # the last line. That is the interruption, not corruption to die on.
    issues = write_issues(tmp_path, 6121, 5000)
    out = tmp_path / "materials.jsonl"
    session = FakeSession(by_param={("idObj", 6121): materials_html})
    main(
        ["materials", "--issues", str(issues), "--out", str(out), "--limit", "1"],
        session=session,
    )
    with out.open("a", encoding="utf-8") as fh:
        fh.write('{"id_obj": 5000, "status": "o')

    session2 = FakeSession(
        by_param={("idObj", 6121): materials_html, ("idObj", 5000): materials_empty_html}
    )
    assert (
        main(
            ["materials", "--issues", str(issues), "--out", str(out), "--resume"],
            session=session2,
        )
        == 0
    )
    assert [g[1]["idObj"] for g in session2.gets] == [6121, 5000]


def test_an_issues_file_row_without_an_id_is_rejected(tmp_path):
    issues = tmp_path / "issues.jsonl"
    issues.write_text('{"year": 2016, "number": 70}\n', encoding="utf-8")
    out = tmp_path / "materials.jsonl"
    with pytest.raises(SystemExit) as exc:
        main(
            ["materials", "--issues", str(issues), "--out", str(out)],
            session=FakeSession(),
        )
    assert "id_obj" in str(exc.value)


# --- one material ---------------------------------------------------------


def test_material_prints_the_header_as_json(tmp_path, capsys, material_html):
    session = FakeSession(get_bodies={MATERIAL_PATH: material_html})
    assert (
        main(
            ["material", "--id-mat", "1000", "--cache-dir", str(tmp_path)],
            session=session,
        )
        == 0
    )
    printed = json.loads(capsys.readouterr().out)
    assert printed["id_mat"] == 1000
    assert printed["issue_number"] == 88
    assert printed["issue_date"] == "2005-11-04"
    assert printed["start_page"] == 30
    assert printed["body_org"] == "Министерство на околната среда и водите"
    assert (tmp_path / "1000.html").exists()


def test_material_uses_the_cache_on_the_second_call(tmp_path, capsys, material_html):
    session = FakeSession(get_bodies={MATERIAL_PATH: material_html})
    main(["material", "--id-mat", "1000", "--cache-dir", str(tmp_path)], session=session)
    capsys.readouterr()
    session2 = FakeSession(get_bodies={})
    main(
        ["material", "--id-mat", "1000", "--cache-dir", str(tmp_path)], session=session2
    )
    assert json.loads(capsys.readouterr().out)["issue_number"] == 88
    assert session2.gets == []


def test_unknown_command_is_rejected():
    with pytest.raises(SystemExit):
        main(["nonsense"])
