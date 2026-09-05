"""The issue-contents listing paginates at thirty rows.

Found on 2026-09-05, after the full sweep left eleven issues
`unrecognized`: `materiali.faces?idObj=N` prints „Намерени резултати: 65“
and lists thirty of them, with the rest behind the same JSF page select
the issue list uses. The count-based discriminator did its job — it
refused to call thirty of sixty-five a complete reading — and this is the
fix it was asking for.

Page 2 is a POST inside the SAME session as the GET, because that GET is
what bound the issue to the server session (the binding found the same
day). So the jar is cleared once, before the first page of an issue, and
never between its pages.

Page 3 is built here from page 2 rather than captured: five rows, ids of
its own and its own ViewState, which is enough to prove the walk carries
the latest token and stops when the rows reach the reported count.
"""

import json
import re

import pytest
from bs4 import BeautifulSoup

from fetcher.dv.client import DvUnavailable
from fetcher.dv.issues import PaginationError
from fetcher.dv.__main__ import main
from fetcher.dv.materials import (
    MATERIALS_URL,
    build_material_page_post_body,
    classify_page,
    classify_pages,
    fetch_all_materials_pages,
    parse_material_current_page,
    parse_material_page_count,
    parse_material_view_state,
    parse_materials,
    parse_materials_all,
)

from .conftest import FakeSession, read_fixture

ERROR_PAGE = read_fixture("materiali-idObj6000-error.html")

#: idObj of бр. 102/2022, the issue both captures belong to.
PAGINATED_ID_OBJ = 10984

#: The ViewState given to the synthetic third page, so a test can tell
#: which response a POST's token came from.
PAGE3_VIEW_STATE = "rO0ABXVyABNbTGphdmEubGFuZy5PYmplY3Q7-page3"


def make_page3(page2_html: str, *, rows: int = 5, shift: int = 500) -> str:
    """The last page of the issue: five materials of its own.

    Derived from the page-2 capture because the site would not hand out
    a third page after the session that produced these two had expired.
    Everything that the walk reads is changed the way the site changes
    it: the rows, their idMat values, the selected option and the
    ViewState.
    """
    soup = BeautifulSoup(page2_html, "lxml")
    body = soup.find("table", id="material_form:dataTable1").find("tbody")
    for tr in body.find_all("tr", recursive=False)[rows:]:
        tr.decompose()
    for anchor in body.find_all("a", href=True):
        anchor["href"] = re.sub(
            r"idMat=(\d+)",
            lambda m: f"idMat={int(m.group(1)) + shift}",
            anchor["href"],
        )
    for select in soup.find_all("select", id=re.compile(r"material_form:selectPage")):
        for option in select.find_all("option"):
            del option["selected"]
            if option["value"] == "3":
                option["selected"] = "selected"
    for field in soup.find_all("input", attrs={"name": "javax.faces.ViewState"}):
        field["value"] = PAGE3_VIEW_STATE
    return str(soup)


@pytest.fixture
def materials_page3_html(materials_page2_html) -> str:
    return make_page3(materials_page2_html)


def paginated_session(page1, page2, page3=None):
    """A session that serves the issue the way the site does."""
    return FakeSession(
        by_param={("idObj", PAGINATED_ID_OBJ): page1},
        post_bodies={2: page2, **({3: page3} if page3 is not None else {})},
        page_key="material_form:selectPage",
    )


class PerIssueSession(FakeSession):
    """Serves every issue the same three pages, with idMat values of its own.

    The page fakes are keyed by page number alone, so a sweep of many
    issues would otherwise hand every issue the same materials and trip
    the leak guard. Shifting the ids by the idObj of the GET that opened
    the issue keeps the sweep honest: many issues, none of them sharing a
    material, all of them paginated.
    """

    def __init__(self, pages):
        super().__init__(page_key="material_form:selectPage")
        self._pages = list(pages)
        self._current = 0

    def get(self, url: str, *, params=None, timeout: int = 30) -> str:
        self._current = int(dict(params or {})["idObj"])
        self.gets.append((url, dict(params) if params else None))
        self.events.append(("get", dict(params) if params else None))
        return self._own_ids(self._pages[0])

    def post(self, url: str, data, *, timeout: int = 30) -> str:
        self.posts.append((url, dict(data)))
        self.events.append(("post", dict(data)))
        return self._own_ids(self._pages[int(dict(data)[self._page_key]) - 1])

    def _own_ids(self, html: str) -> str:
        return re.sub(
            r"idMat=(\d+)",
            lambda m: f"idMat={int(m.group(1)) + self._current * 1_000_000}",
            html,
        )


def write_issues(tmp_path, *id_objs):
    path = tmp_path / "issues.jsonl"
    with path.open("w", encoding="utf-8") as handle:
        for n, id_obj in enumerate(id_objs):
            handle.write(
                json.dumps(
                    {
                        "year": 2022,
                        "number": 102 - n,
                        "date": f"2022-12-{20 + n:02d}",
                        "id_obj": id_obj,
                        "section": 1,
                        "extraordinary": False,
                    }
                )
                + "\n"
            )
    return path


# --- the defect, stated as a fact about page 1 ----------------------------


def test_page_one_lists_thirty_of_sixty_five(materials_page1_html):
    assert len(parse_materials(materials_page1_html)) == 30


def test_page_one_alone_is_not_a_complete_reading(materials_page1_html):
    # The status eleven issues were written with on 2026-09-05. It is the
    # count discriminator working, not a parser defect.
    assert classify_page(materials_page1_html) == "unrecognized"


# --- the pager ------------------------------------------------------------


def test_page_count_is_read_from_the_material_select(materials_page1_html):
    assert parse_material_page_count(materials_page1_html) == 3


def test_current_page_is_the_selected_option(
    materials_page1_html, materials_page2_html
):
    assert parse_material_current_page(materials_page1_html) == 1
    assert parse_material_current_page(materials_page2_html) == 2


def test_a_listing_without_a_pager_is_one_page(materials_html, materials_empty_html):
    # idObj 6121 fits on one page and prints no select at all; absence of
    # a pager is „one page“, not „unreadable“.
    assert parse_material_page_count(materials_html) == 1
    assert parse_material_current_page(materials_html) == 1
    assert parse_material_page_count(materials_empty_html) == 1


def test_a_pager_that_marks_no_page_still_raises(materials_page1_html):
    # A select with nothing selected is markup this code cannot read, and
    # must not be silently taken for page 1.
    mutated = materials_page1_html.replace(' selected="selected"', "")
    with pytest.raises(ValueError):
        parse_material_current_page(mutated)


def test_view_state_comes_from_the_material_form(
    materials_page1_html, materials_page2_html
):
    first = parse_material_view_state(materials_page1_html)
    second = parse_material_view_state(materials_page2_html)
    assert first and second and first != second


def test_the_page_post_body_replays_the_form(materials_page1_html):
    body = build_material_page_post_body(
        parse_material_view_state(materials_page1_html), 2
    )
    assert body["material_form_SUBMIT"] == "1"
    assert body["material_form:_idcl"] == "material_form:chP"
    assert body["material_form:selectPage"] == "2"
    assert body["material_form:selectPageTop"] == "2"
    assert body["javax.faces.ViewState"] == parse_material_view_state(
        materials_page1_html
    )


# --- walking the pages ----------------------------------------------------


def test_all_three_pages_are_fetched(
    materials_page1_html, materials_page2_html, materials_page3_html
):
    session = paginated_session(
        materials_page1_html, materials_page2_html, materials_page3_html
    )
    pages = fetch_all_materials_pages(session, PAGINATED_ID_OBJ)
    assert len(pages) == 3
    assert [g[1]["idObj"] for g in session.gets] == [PAGINATED_ID_OBJ]
    assert [d["material_form:selectPage"] for _, d in session.posts] == ["2", "3"]
    assert all(url == MATERIALS_URL for url, _ in session.posts)


def test_each_post_carries_the_previous_response_s_view_state(
    materials_page1_html, materials_page2_html, materials_page3_html
):
    session = paginated_session(
        materials_page1_html, materials_page2_html, materials_page3_html
    )
    fetch_all_materials_pages(session, PAGINATED_ID_OBJ)
    tokens = [d["javax.faces.ViewState"] for _, d in session.posts]
    assert tokens == [
        parse_material_view_state(materials_page1_html),
        parse_material_view_state(materials_page2_html),
    ]


def test_the_jar_is_cleared_once_and_not_between_pages(
    materials_page1_html, materials_page2_html, materials_page3_html
):
    # The GET binds the issue to the server session; clearing the jar
    # between pages would unbind it and page 2 would be another issue.
    session = paginated_session(
        materials_page1_html, materials_page2_html, materials_page3_html
    )
    fetch_all_materials_pages(session, PAGINATED_ID_OBJ)
    assert [kind for kind, _ in session.events] == ["clear", "get", "post", "post"]
    assert session.cookies.clears == 1


def test_a_single_page_issue_makes_one_get_and_no_post(materials_html):
    session = FakeSession(
        by_param={("idObj", 6121): materials_html},
        page_key="material_form:selectPage",
    )
    assert fetch_all_materials_pages(session, 6121) == [materials_html]
    assert not session.posts


def test_an_error_stub_costs_one_request(error_page_html):
    session = FakeSession(
        by_param={("idObj", 6000): error_page_html},
        page_key="material_form:selectPage",
    )
    assert fetch_all_materials_pages(session, 6000) == [error_page_html]
    assert not session.posts


def test_a_page_this_code_cannot_read_is_not_paginated_after(materials_page1_html):
    # No count to walk towards: one request, and the caller is told the
    # page was unreadable rather than being handed a walk it cannot end.
    mutated = materials_page1_html.replace("Намерени резултати", "Found results")
    session = FakeSession(
        by_param={("idObj", PAGINATED_ID_OBJ): mutated},
        page_key="material_form:selectPage",
    )
    pages = fetch_all_materials_pages(session, PAGINATED_ID_OBJ)
    assert pages == [mutated]
    assert not session.posts
    assert classify_pages(pages) == "unrecognized"


def test_a_wrong_page_in_the_answer_stops_the_walk(
    materials_page1_html, materials_page2_html
):
    # An expired ViewState makes the server serve page 1 again. Accepting
    # it would duplicate thirty rows and lose the other thirty-five.
    session = paginated_session(materials_page1_html, materials_page1_html)
    with pytest.raises(PaginationError) as excinfo:
        fetch_all_materials_pages(session, PAGINATED_ID_OBJ)
    assert "page 2" in str(excinfo.value)
    assert str(PAGINATED_ID_OBJ) in str(excinfo.value)


def test_a_stub_answer_to_a_pagination_post_is_named_as_an_outage(
    materials_page1_html,
):
    session = paginated_session(materials_page1_html, ERROR_PAGE)
    with pytest.raises(DvUnavailable):
        fetch_all_materials_pages(session, PAGINATED_ID_OBJ)


def test_the_walk_stops_when_the_pages_run_out(
    materials_page1_html, materials_page2_html
):
    # Sixty of sixty-five and no third page: the walk ends rather than
    # POSTing forever, and the shortfall is the caller's to classify.
    def drop_third_option(html):
        return html.replace('<option value="3">страница: 3</option>', "")

    session = paginated_session(
        drop_third_option(materials_page1_html), drop_third_option(materials_page2_html)
    )
    pages = fetch_all_materials_pages(session, PAGINATED_ID_OBJ)
    assert len(pages) == 2
    assert len(parse_materials_all(pages)) == 60
    assert classify_pages(pages) == "unrecognized"


# --- reading the pages as one listing -------------------------------------


def test_the_two_captured_pages_do_not_overlap(
    materials_page1_html, materials_page2_html
):
    first = {r.id_mat for r in parse_materials(materials_page1_html)}
    second = {r.id_mat for r in parse_materials(materials_page2_html)}
    assert len(first) == len(second) == 30
    assert not first & second


def test_the_whole_issue_is_sixty_five_materials(
    materials_page1_html, materials_page2_html, materials_page3_html
):
    rows = parse_materials_all(
        [materials_page1_html, materials_page2_html, materials_page3_html]
    )
    assert len(rows) == 65
    assert len({r.id_mat for r in rows}) == 65


def test_positions_run_on_across_the_pages(
    materials_page1_html, materials_page2_html, materials_page3_html
):
    rows = parse_materials_all(
        [materials_page1_html, materials_page2_html, materials_page3_html]
    )
    assert [r.position for r in rows] == list(range(1, 66))
    assert rows[30].id_mat == parse_materials(materials_page2_html)[0].id_mat


def test_the_page_order_is_kept(materials_page1_html, materials_page2_html):
    rows = parse_materials_all([materials_page1_html, materials_page2_html])
    assert [r.id_mat for r in rows[:30]] == [
        r.id_mat for r in parse_materials(materials_page1_html)
    ]


def test_a_material_repeated_across_pages_is_read_once(materials_page1_html):
    # The site would repeat rows if a page were served twice; the listing
    # is a set of materials, so the second copy is dropped and positions
    # stay contiguous.
    rows = parse_materials_all([materials_page1_html, materials_page1_html])
    assert len(rows) == 30
    assert [r.position for r in rows] == list(range(1, 31))


def test_the_concatenation_is_classified_as_materials(
    materials_page1_html, materials_page2_html, materials_page3_html
):
    pages = [materials_page1_html, materials_page2_html, materials_page3_html]
    assert classify_pages(pages) == "materials"


def test_classify_pages_of_a_single_page_is_classify_page(
    materials_html, materials_empty_html, error_page_html
):
    for html in (materials_html, materials_empty_html, error_page_html):
        assert classify_pages([html]) == classify_page(html)


# --- the sweep ------------------------------------------------------------


def test_the_sweep_writes_every_page_of_a_paginated_issue(
    tmp_path, materials_page1_html, materials_page2_html, materials_page3_html
):
    issues = write_issues(tmp_path, PAGINATED_ID_OBJ)
    out = tmp_path / "materials.jsonl"
    session = paginated_session(
        materials_page1_html, materials_page2_html, materials_page3_html
    )
    assert (
        main(["materials", "--issues", str(issues), "--out", str(out)], session=session)
        == 0
    )
    rows = [json.loads(line) for line in out.read_text(encoding="utf-8").splitlines()]
    assert len(rows) == 65
    assert {r["status"] for r in rows} == {"ok"}
    assert [r["position"] for r in rows] == list(range(1, 66))
    assert len({r["id_mat"] for r in rows}) == 65
    assert {r["id_obj"] for r in rows} == {PAGINATED_ID_OBJ}


def test_a_paginated_issue_no_longer_trips_the_unrecognized_halt(
    tmp_path, materials_page1_html, materials_page2_html, materials_page3_html
):
    # Eleven of these in a run of fifty halted the sweep on 2026-09-05:
    # `unrecognized` was the only status a paginated issue could get, and
    # eleven inside the first fifty issues is a redesign by the rule in
    # `_too_many_unrecognized`. Twenty of them now sweep clean.
    issues = write_issues(tmp_path, *range(20_000, 20_020))
    out = tmp_path / "materials.jsonl"
    session = PerIssueSession(
        [materials_page1_html, materials_page2_html, materials_page3_html]
    )
    assert (
        main(["materials", "--issues", str(issues), "--out", str(out)], session=session)
        == 0
    )
    rows = [json.loads(line) for line in out.read_text(encoding="utf-8").splitlines()]
    assert not [r for r in rows if r["status"] == "unrecognized"]
    assert len(rows) == 20 * 65
    assert len({r["id_mat"] for r in rows}) == 20 * 65


def test_the_leak_guard_sees_the_whole_issue_not_just_its_first_page(
    tmp_path, materials_page1_html, materials_page2_html, materials_page3_html
):
    # The repeat is on page 2 only: the guard compares the issue's whole
    # set, so a leak that starts after row thirty is still caught.
    issues = write_issues(tmp_path, PAGINATED_ID_OBJ, 20_001)
    out = tmp_path / "materials.jsonl"
    other_first_page = re.sub(
        r"idMat=(\d+)",
        lambda m: f"idMat={int(m.group(1)) + 900_000}",
        materials_page1_html,
    )
    session = FakeSession(
        by_param={
            ("idObj", PAGINATED_ID_OBJ): materials_page1_html,
            ("idObj", 20_001): other_first_page,
        },
        post_bodies={2: materials_page2_html, 3: materials_page3_html},
        page_key="material_form:selectPage",
    )
    assert (
        main(["materials", "--issues", str(issues), "--out", str(out)], session=session)
        != 0
    )
    rows = [json.loads(line) for line in out.read_text(encoding="utf-8").splitlines()]
    assert {r["id_obj"] for r in rows} == {PAGINATED_ID_OBJ}


def test_a_pagination_failure_halts_the_sweep_instead_of_truncating_the_issue(
    tmp_path, materials_page1_html
):
    issues = write_issues(tmp_path, PAGINATED_ID_OBJ)
    out = tmp_path / "materials.jsonl"
    session = paginated_session(materials_page1_html, materials_page1_html)
    assert (
        main(["materials", "--issues", str(issues), "--out", str(out)], session=session)
        != 0
    )
    assert out.read_text(encoding="utf-8") == "", "half an issue is worse than none"


def test_resume_comes_back_to_an_issue_recorded_as_unrecognized(
    tmp_path, materials_page1_html, materials_page2_html, materials_page3_html
):
    # Exactly the eleven-issue situation on disk: the run before the fix
    # wrote `unrecognized`; the run after it must return and read all 65.
    issues = write_issues(tmp_path, PAGINATED_ID_OBJ)
    out = tmp_path / "materials.jsonl"
    out.write_text(
        json.dumps(
            {
                "id_obj": PAGINATED_ID_OBJ,
                "issue_year": 2022,
                "issue_number": 102,
                "issue_date": "2022-12-20",
                "status": "unrecognized",
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    session = paginated_session(
        materials_page1_html, materials_page2_html, materials_page3_html
    )
    assert (
        main(
            ["materials", "--issues", str(issues), "--out", str(out), "--resume"],
            session=session,
        )
        == 0
    )
    rows = [json.loads(line) for line in out.read_text(encoding="utf-8").splitlines()]
    assert [g[1]["idObj"] for g in session.gets] == [PAGINATED_ID_OBJ]
    assert len(rows) == 65
    assert not [r for r in rows if r["status"] == "unrecognized"]
