"""The materials page binds the chosen issue to the server session.

Found live on 2026-09-05 after a full sweep: `materiali.faces?idObj=N`
honours `idObj` only on the first request of a session and afterwards keeps
serving the issue it first bound, whatever the parameter says. One
`DvSession` for 4,146 issues therefore produced 3,843 copies of брой
81/2026's twenty materials. Two defences: a fresh cookie jar before every
materials or material request, and a sweep that refuses to believe two
different issues with an identical set of materials.
"""

import json
import re

from fetcher.dv.__main__ import main
from fetcher.dv.materials import MATERIALS_URL, fetch_material, fetch_materials

from .conftest import FakeSession, read_fixture


def _write_issues(tmp_path, *id_objs):
    path = tmp_path / "issues.jsonl"
    with path.open("w", encoding="utf-8") as handle:
        for n, id_obj in enumerate(id_objs):
            handle.write(json.dumps({
                "year": 2026, "number": 80 - n, "date": f"2026-08-{10 + n:02d}",
                "id_obj": id_obj, "section": 1, "extraordinary": False,
            }) + "\n")
    return path


def _shift_id_mats(html: str, by: int) -> str:
    """The same page as if it belonged to another issue: every idMat moved."""
    return re.sub(r"idMat=(\d+)", lambda m: f"idMat={int(m.group(1)) + by}", html)


class TestFreshJar:
    def test_fetch_materials_clears_the_jar_before_each_request(self, materials_html):
        session = FakeSession(by_param={("idObj", 6121): materials_html, ("idObj", 5000): materials_html})
        fetch_materials(session, 6121)
        fetch_materials(session, 5000)
        kinds = [kind for kind, _ in session.events]
        assert kinds == ["clear", "get", "clear", "get"]
        assert session.cookies.clears == 2

    def test_fetch_material_keeps_the_session(self, material_html):
        # Measured live on 2026-09-05: showMaterialDV.jsp is not session-bound
        # (one jar served idMat 242220, 300 and 1000 as three different
        # issues), so the 42,000-body sweep must not mint a session per body.
        session = FakeSession(by_param={("idMat", 1000): material_html})
        fetch_material(session, 1000, cache_dir=None)
        assert [kind for kind, _ in session.events] == ["get"]
        assert session.cookies.clears == 0


class TestIdenticalSetGuard:
    def test_sweep_halts_when_two_issues_return_the_same_materials(self, tmp_path, materials_html, caplog):
        # A server that ignored idObj would answer every issue with the first
        # issue's page. Real issues never share a material, so an identical
        # non-empty set across two different issues is a client defect, and
        # the sweep must stop rather than write thousands of false rows.
        issues = _write_issues(tmp_path, 6121, 6122, 6123)
        out = tmp_path / "materials.jsonl"
        session = FakeSession(by_param={
            ("idObj", 6121): materials_html,
            ("idObj", 6122): materials_html,
            ("idObj", 6123): materials_html,
        })
        assert main(["materials", "--issues", str(issues), "--out", str(out)], session=session) != 0
        written = [json.loads(l) for l in out.read_text(encoding="utf-8").splitlines()]
        assert {r["id_obj"] for r in written} == {6121}, "only the first issue's rows may be written"
        assert [g[1]["idObj"] for g in session.gets] == [6121, 6122], "stops at the first repeat"
        assert "same materials" in caplog.text

    def test_sweep_accepts_two_issues_with_different_materials(self, tmp_path, materials_html):
        issues = _write_issues(tmp_path, 6121, 12640)
        out = tmp_path / "materials.jsonl"
        session = FakeSession(by_param={
            ("idObj", 6121): materials_html,
            ("idObj", 12640): _shift_id_mats(materials_html, 1_000_000),
        })
        assert main(["materials", "--issues", str(issues), "--out", str(out)], session=session) == 0
        written = [json.loads(l) for l in out.read_text(encoding="utf-8").splitlines()]
        assert {r["id_obj"] for r in written} == {6121, 12640}
        assert len({r["id_mat"] for r in written}) == 36

    def test_an_empty_issue_between_two_identical_pages_still_trips_the_guard(self, tmp_path, materials_html, materials_empty_html):
        # The comparison is against the last NON-EMPTY set, so an empty
        # PDF-era issue in between cannot reset it and hide the leak.
        issues = _write_issues(tmp_path, 6121, 5000, 6123)
        out = tmp_path / "materials.jsonl"
        session = FakeSession(by_param={
            ("idObj", 6121): materials_html,
            ("idObj", 5000): materials_empty_html,
            ("idObj", 6123): materials_html,
        })
        assert main(["materials", "--issues", str(issues), "--out", str(out)], session=session) != 0

    def test_guard_is_seeded_from_the_file_across_a_resume(self, tmp_path, materials_html, materials_empty_html):
        # First run wrote issue 6121 and then an EMPTY issue 5000 as its last
        # row. The resume drops that last issue and re-fetches it, so the
        # in-memory "previous non-empty set" would be blank; the guard must
        # still recognise 6123's leaked materials as ones already written.
        issues = _write_issues(tmp_path, 6121, 5000, 6123)
        out = tmp_path / "materials.jsonl"
        first = FakeSession(by_param={("idObj", 6121): materials_html, ("idObj", 5000): materials_empty_html})
        assert main(["materials", "--issues", str(issues), "--out", str(out), "--limit", "2"], session=first) == 0
        before = [json.loads(l) for l in out.read_text(encoding="utf-8").splitlines()]
        assert {r["id_obj"] for r in before} == {6121, 5000}
        resumed = FakeSession(by_param={("idObj", 5000): materials_empty_html, ("idObj", 6123): materials_html})
        assert main(["materials", "--issues", str(issues), "--out", str(out), "--resume"], session=resumed) != 0
        after = [json.loads(l) for l in out.read_text(encoding="utf-8").splitlines()]
        assert {r["id_obj"] for r in after} == {6121, 5000}, "nothing from the leaked issue may be written"

    def test_guard_catches_a_repeat_that_is_not_adjacent(self, tmp_path, materials_html, materials_empty_html):
        issues = _write_issues(tmp_path, 6121, 5000, 5001, 6123)
        out = tmp_path / "materials.jsonl"
        session = FakeSession(by_param={
            ("idObj", 6121): materials_html,
            ("idObj", 5000): materials_empty_html,
            ("idObj", 5001): materials_empty_html,
            ("idObj", 6123): materials_html,
        })
        assert main(["materials", "--issues", str(issues), "--out", str(out)], session=session) != 0
