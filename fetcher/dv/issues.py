"""The ДВ issue list: parsing broeveList.faces and driving its pagination.

The list is a JSF (MyFaces) form named `broi_form`. Ten issues per page,
415 pages, 4,146 issues as of 2026-09-05. Page 1 arrives on a GET; every
later page is a POST that replays the whole form, including the
`javax.faces.ViewState` token from the response that preceded it.

Each row's identity lives in the parameters of its submit link, not in
the visible text:

    oamSubmitForm('broi_form','broi_form:dataTable1:0:_idJsp101',null,
        [['broi_','81'],['idObj','12640'],
         ['date_izd_','2026-09-04'],['razdel_','1']])

`broi_` is the issue number inside its year, `idObj` the identifier the
contents page takes, `date_izd_` the publication date and `razdel_` the
section (1 is официалният раздел). The row carries no year of its own,
so the year is read from the publication date: issue numbering restarts
every calendar year and an issue is published in the year it numbers.

The second link of each row (`Изтегли броя`) carries only `id_` and is
not an issue row.
"""

import logging
import re
from collections.abc import Callable, Iterator
from dataclasses import dataclass

from bs4 import BeautifulSoup

from fetcher.dv.client import DvUnavailable, is_dv_error_body, url_for

ISSUE_LIST_PATH = "broeveList.faces"
ISSUE_LIST_URL = url_for(ISSUE_LIST_PATH)

#: The dataTable that holds the result rows.
_TABLE_ID = "broi_form:dataTable1"
#: The page-jump select; its options are one per page and one is `selected`.
_PAGE_SELECT_ID = "broi_form:selectPage"

log = logging.getLogger(__name__)


class PaginationError(RuntimeError):
    """The list answered with a page other than the one that was asked for.

    A stale or expired `javax.faces.ViewState` makes the server serve
    page 1 again; silently accepting it would duplicate rows and lose
    the rest of the corpus, so enumeration stops instead.
    """


@dataclass(frozen=True)
class IssueRow:
    """One issue of Държавен вестник as the list page describes it."""

    year: int
    number: int
    date: str  # ISO 8601, yyyy-mm-dd
    id_obj: int
    #: 1 is официалният раздел. None when the row omits `razdel_`, which
    #: no captured row does; `0` would be a section that does not exist.
    section: int | None
    #: True when the row prints „(извънреден)“ after the date, as брой 78
    #: and брой 75 of 2026 do. False otherwise: the list marks извънредни
    #: issues explicitly and says nothing about the rest, so silence is
    #: evidence of a редовен issue rather than an absence of evidence.
    extraordinary: bool


_PARAM_RE = re.compile(r"\['([A-Za-z_]+)','([^']*)'\]")

#: The row prints „Брой 78, 26.8.2026 г. (извънреден)“. Matching the
#: parenthesised word rather than the bare one keeps a title that happens
#: to contain „извънредно“ from flagging its issue.
_EXTRAORDINARY_RE = re.compile(r"\(\s*извънред", re.IGNORECASE)


def _submit_params(onclick: str) -> dict[str, str]:
    """The `[['key','value'],...]` payload of an oamSubmitForm call."""
    return dict(_PARAM_RE.findall(onclick))


def parse_issue_rows(html: str) -> list[IssueRow]:
    """Every issue row of one list page, in document order."""
    soup = BeautifulSoup(html, "lxml")
    table = soup.find("table", id=_TABLE_ID)
    if table is None:
        return []
    rows: list[IssueRow] = []
    for anchor in table.find_all("a", onclick=True):
        params = _submit_params(anchor["onclick"])
        if not {"broi_", "idObj", "date_izd_"} <= params.keys():
            continue  # the download link, which carries only id_
        date = params["date_izd_"]
        text = anchor.find_parent("td")
        markup = text.get_text(" ", strip=True) if text is not None else ""
        razdel = params.get("razdel_")
        rows.append(
            IssueRow(
                year=int(date[:4]),
                number=int(params["broi_"]),
                date=date,
                id_obj=int(params["idObj"]),
                section=int(razdel) if razdel else None,
                extraordinary=_EXTRAORDINARY_RE.search(markup) is not None,
            )
        )
    return rows


#: The form the issue list paginates. The three helpers below take the
#: form and select they read as arguments, because the issue-contents
#: page is the same MyFaces pagination under other names
#: (`material_form`) and reading it twice, once per module, is how the
#: two copies drift apart.
_FORM_NAME = "broi_form"


def parse_view_state(html: str, form: str = _FORM_NAME) -> str:
    """The `javax.faces.ViewState` token the next POST has to echo.

    A response carries one token per form; the one inside the form being
    paginated is the one its POST belongs to. They have been identical on
    every capture, but the form-scoped lookup is the correct one.
    """
    soup = BeautifulSoup(html, "lxml")
    scope = soup.find("form", attrs={"name": form}) or soup.find("form", id=form)
    if scope is None:
        scope = soup
    field = scope.find("input", attrs={"name": "javax.faces.ViewState"})
    if field is None:
        field = soup.find("input", attrs={"name": "javax.faces.ViewState"})
    if field is None or not field.get("value"):
        raise ValueError("no javax.faces.ViewState in the response")
    return field["value"]


def find_page_select(html: str, select_id: str = _PAGE_SELECT_ID):
    """The page-jump select, or None when the response prints no pager.

    A caller that treats „no pager“ as „one page“ needs to tell it apart
    from a pager it could not read, which `_page_select` cannot: both
    arrive as ValueError.
    """
    return BeautifulSoup(html, "lxml").find("select", id=select_id)


def _page_select(html: str, select_id: str = _PAGE_SELECT_ID):
    select = find_page_select(html, select_id)
    if select is None:
        raise ValueError(f"no <select id={select_id!r}> in the response")
    return select


def parse_page_count(html: str, select_id: str = _PAGE_SELECT_ID) -> int:
    """How many pages the list has: one option per page."""
    return len(_page_select(html, select_id).find_all("option"))


def parse_current_page(html: str, select_id: str = _PAGE_SELECT_ID) -> int:
    """The page this response actually is, from the `selected` option."""
    for option in _page_select(html, select_id).find_all("option"):
        if option.has_attr("selected"):
            return int(option["value"])
    raise ValueError("no page is marked selected in the response")


_RESULT_COUNT_RE = re.compile(r"Намерени резултати:\s*(\d+)")


def parse_result_count(html: str) -> int:
    """The „Намерени резултати“ total.

    Present on every ДВ result page, so it also reads the material count
    of an issue-contents page.
    """
    match = _RESULT_COUNT_RE.search(BeautifulSoup(html, "lxml").get_text(" "))
    if match is None:
        raise ValueError("no result count in the response")
    return int(match.group(1))


def build_page_post_body(view_state: str, page: int) -> dict[str, str]:
    """The form POST that moves the list to `page`.

    Replays every field of `broi_form` the way the browser does, with the
    page-change control (`broi_form:chP`) named as the source of the
    submit and the ViewState taken from the response that produced it.
    The date-range fields stay empty: this is the global pagination path,
    and the per-year filter is the documented fallback if it breaks.
    """
    return {
        "broi_form_SUBMIT": "1",
        "broi_form:_link_hidden_": "",
        "broi_form:_idcl": "broi_form:chP",
        "broi_form:not_first": "1",
        "broi_form:selectPage": str(page),
        "broi_form:selectPageTop": str(page),
        "broi_form:_idJsp61": "",
        "broi_form:_idJsp67": "",
        "broi_form:_idJsp69": "",  # редовен / извънреден filter, empty = all
        "broi_form:period_": "",
        "broi_form:from_date": "",
        "broi_form:to_date": "",
        "active_tab": "2",
        "javax.faces.ViewState": view_state,
    }


def _demand_a_page(html: str, what: str) -> str:
    """The body, unless the site answered with its „недостъпен“ view.

    Without this the outage surfaces at the top of the next loop as „no
    <select id='broi_form:selectPage'> in the response“, which names an
    element this code went looking for rather than the reason it is not
    there. The run stopped either way; only the log was misleading.
    """
    if is_dv_error_body(html):
        raise DvUnavailable(
            f"the issue list served its „недостъпен“ view for {what}; "
            "the site is down"
        )
    return html


def enumerate_issues(
    session,
    *,
    max_pages: int | None = None,
    start_page: int = 1,
    on_page: Callable[[int, list[IssueRow]], None] | None = None,
) -> Iterator[IssueRow]:
    """Yield every issue row of the list, page by page, in document order.

    Page 1 is always fetched, because the session cookie and the first
    ViewState come from it; with `start_page > 1` its rows are skipped
    and the run jumps straight to that page, which makes a stopped
    enumeration resumable without replaying what it already wrote.

    `max_pages` counts pages actually yielded, starting at `start_page`.
    `on_page` is called with the page number and its rows as soon as the
    page is parsed, which gives a caller a checkpoint per page.

    Raises `PaginationError` when a response is not the page that was
    asked for.
    """
    if start_page < 1:
        raise ValueError(f"start_page must be 1 or more, got {start_page}")

    html = _demand_a_page(session.get(ISSUE_LIST_URL), "the first page")
    total_pages = parse_page_count(html)
    if total_pages < 1:
        raise ValueError(
            "the issue list offered no pages at all; its markup has changed"
        )
    if start_page > total_pages:
        raise ValueError(
            f"start_page {start_page} is past the last page ({total_pages})"
        )
    log.info(
        "issue list: %d pages, %d issues", total_pages, parse_result_count(html)
    )

    page = start_page
    if start_page != 1:
        html = _demand_a_page(
            session.post(
                ISSUE_LIST_URL, build_page_post_body(parse_view_state(html), start_page)
            ),
            f"page {start_page}",
        )

    yielded = 0
    while True:
        actual = parse_current_page(html)
        if actual != page:
            raise PaginationError(
                f"asked for page {page} of the issue list, got page {actual}"
            )
        rows = parse_issue_rows(html)
        if on_page is not None:
            on_page(page, rows)
        yield from rows
        yielded += 1

        if max_pages is not None and yielded >= max_pages:
            return
        if page >= total_pages:
            return
        page += 1
        html = _demand_a_page(
            session.post(
                ISSUE_LIST_URL, build_page_post_body(parse_view_state(html), page)
            ),
            f"page {page}",
        )
