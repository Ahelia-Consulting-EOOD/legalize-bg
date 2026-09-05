"""Issue-list parsing and JSF pagination against the captured fixtures.

Concrete values come from the two broeveList pages captured live on
2026-09-05, so a silent change in the parser shows up as a wrong number
rather than as an empty list.
"""

import pytest

from fetcher.dv.issues import (
    ISSUE_LIST_PATH,
    IssueRow,
    PaginationError,
    build_page_post_body,
    enumerate_issues,
    parse_current_page,
    parse_issue_rows,
    parse_page_count,
    parse_result_count,
    parse_view_state,
)

from .conftest import FakeSession


# --- pure parsers ---------------------------------------------------------


def test_page1_has_ten_rows(issue_page1):
    rows = parse_issue_rows(issue_page1)
    assert len(rows) == 10
    assert all(isinstance(r, IssueRow) for r in rows)


def test_page1_first_row_fields(issue_page1):
    first = parse_issue_rows(issue_page1)[0]
    assert first.number == 81
    assert first.id_obj == 12640
    assert first.date == "2026-09-04"
    assert first.year == 2026
    assert first.section == 1
    # The row markup carries no regular/extraordinary marker, so the flag
    # stays unknown rather than being guessed.
    assert first.extraordinary is None


def test_page1_rows_are_in_document_order(issue_page1):
    numbers = [r.number for r in parse_issue_rows(issue_page1)]
    assert numbers == [81, 80, 79, 78, 77, 76, 75, 74, 73, 72]


def test_page2_first_and_last_rows(issue_page2):
    rows = parse_issue_rows(issue_page2)
    assert len(rows) == 10
    assert (rows[0].number, rows[0].id_obj, rows[0].date) == (71, 12620, "2026-08-07")
    assert (rows[-1].number, rows[-1].id_obj, rows[-1].date) == (62, 12599, "2026-07-07")


def test_download_links_are_not_mistaken_for_issue_rows(issue_page1):
    # Each row also carries an „Изтегли броя“ link whose only parameter is
    # id_; it must not produce a second IssueRow.
    assert len(parse_issue_rows(issue_page1)) == 10


def test_parse_view_state_differs_per_page(issue_page1, issue_page2):
    vs1 = parse_view_state(issue_page1)
    vs2 = parse_view_state(issue_page2)
    assert vs1.startswith("rO0ABX")
    assert vs2.startswith("rO0ABX")
    assert vs1 != vs2


def test_parse_view_state_raises_when_absent():
    with pytest.raises(ValueError):
        parse_view_state("<html><body>no form here</body></html>")


def test_parse_page_count(issue_page1, issue_page2):
    assert parse_page_count(issue_page1) == 415
    assert parse_page_count(issue_page2) == 415


def test_parse_current_page(issue_page1, issue_page2):
    assert parse_current_page(issue_page1) == 1
    assert parse_current_page(issue_page2) == 2


def test_parse_result_count(issue_page1):
    assert parse_result_count(issue_page1) == 4146


def test_parse_result_count_reads_zero(materials_empty_html):
    assert parse_result_count(materials_empty_html) == 0


# --- the POST body --------------------------------------------------------


def test_post_body_carries_page_and_view_state():
    body = build_page_post_body("VS-123", 7)
    assert body["broi_form:selectPage"] == "7"
    assert body["broi_form:selectPageTop"] == "7"
    assert body["javax.faces.ViewState"] == "VS-123"
    assert body["broi_form:_idcl"] == "broi_form:chP"
    assert body["broi_form_SUBMIT"] == "1"
    assert body["broi_form:not_first"] == "1"
    # The date-range filter stays empty: this is the global pagination path.
    assert body["broi_form:from_date"] == ""
    assert body["broi_form:to_date"] == ""


# --- the enumerator -------------------------------------------------------


def _session(issue_page1, issue_page2):
    return FakeSession(
        get_bodies={ISSUE_LIST_PATH: issue_page1},
        post_bodies={2: issue_page2},
    )


def test_enumerate_first_page_only_makes_no_post(issue_page1, issue_page2):
    session = _session(issue_page1, issue_page2)
    rows = list(enumerate_issues(session, max_pages=1))
    assert len(rows) == 10
    assert len(session.gets) == 1
    assert session.gets[0][0].endswith(ISSUE_LIST_PATH)
    assert session.posts == []


def test_enumerate_two_pages_yields_twenty_rows(issue_page1, issue_page2):
    session = _session(issue_page1, issue_page2)
    rows = list(enumerate_issues(session, max_pages=2))
    assert len(rows) == 20
    assert rows[0].id_obj == 12640
    assert rows[-1].id_obj == 12599


def test_enumerate_carries_view_state_from_previous_response(
    issue_page1, issue_page2
):
    session = _session(issue_page1, issue_page2)
    list(enumerate_issues(session, max_pages=2))
    assert len(session.posts) == 1
    url, body = session.posts[0]
    assert url.endswith(ISSUE_LIST_PATH)
    assert body["javax.faces.ViewState"] == parse_view_state(issue_page1)
    assert body["broi_form:selectPage"] == "2"


def test_enumerate_is_resumable_from_a_later_page(issue_page1, issue_page2):
    session = _session(issue_page1, issue_page2)
    rows = list(enumerate_issues(session, start_page=2, max_pages=1))
    assert [r.id_obj for r in rows] == [
        12620, 12619, 12606, 12605, 12604, 12603, 12602, 12601, 12600, 12599,
    ]
    # Page 1 is still fetched, because the ViewState and the session cookie
    # come from it, but its rows are not yielded.
    assert len(session.gets) == 1
    assert len(session.posts) == 1
    assert session.posts[0][1]["broi_form:selectPage"] == "2"


def test_enumerate_calls_on_page_hook(issue_page1, issue_page2):
    session = _session(issue_page1, issue_page2)
    seen = []
    list(enumerate_issues(session, max_pages=2, on_page=lambda p, rs: seen.append((p, len(rs)))))
    assert seen == [(1, 10), (2, 10)]


def test_enumerate_verifies_the_returned_page_number(issue_page1):
    # The server answers page 2 with page 1 (an expired ViewState does this).
    session = FakeSession(
        get_bodies={ISSUE_LIST_PATH: issue_page1},
        post_bodies={2: issue_page1},
    )
    with pytest.raises(PaginationError) as exc:
        list(enumerate_issues(session, max_pages=2))
    assert "2" in str(exc.value)


def test_enumerate_is_deterministic(issue_page1, issue_page2):
    first = list(enumerate_issues(_session(issue_page1, issue_page2), max_pages=2))
    second = list(enumerate_issues(_session(issue_page1, issue_page2), max_pages=2))
    assert first == second


def test_enumerate_stops_at_the_last_page(issue_page1, issue_page2, monkeypatch):
    # A two-page corpus: the enumerator must stop without asking for page 3.
    monkeypatch.setattr("fetcher.dv.issues.parse_page_count", lambda html: 2)
    session = _session(issue_page1, issue_page2)
    rows = list(enumerate_issues(session))
    assert len(rows) == 20
    assert [b["broi_form:selectPage"] for _, b in session.posts] == ["2"]
