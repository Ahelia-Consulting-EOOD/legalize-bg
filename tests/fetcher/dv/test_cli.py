"""The `python -m fetcher.dv` command line, driven by a fake session."""

import json

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
        "extraordinary": None,
    }
    assert rows[-1]["id_obj"] == 12599


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
                        "extraordinary": None,
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
    issues = write_issues(tmp_path, 6121, 5000)
    out = tmp_path / "materials.jsonl"
    session = FakeSession(by_param={("idObj", 6121): materials_html})
    main(
        ["materials", "--issues", str(issues), "--out", str(out), "--limit", "1"],
        session=session,
    )

    session2 = FakeSession(by_param={("idObj", 5000): materials_empty_html})
    main(
        ["materials", "--issues", str(issues), "--out", str(out), "--resume"],
        session=session2,
    )
    rows = read_jsonl(out)
    assert len(rows) == 19
    assert [g[1]["idObj"] for g in session2.gets] == [5000]


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
