"""An issue's contents (materiali.faces) and one published material.

Two pages, two shapes.

`materiali.faces?idObj=N` lists every material of one issue. A row is a
`<td>` holding the issuing section in `<strong>`, then the material's
title as text, then a nested table with the start page („стр. 12“) and a
link to `showMaterialDV.jsp?idMat=M`. The page header of this listing
shows the CURRENT issue of the site, not the issue being listed, so the
issue identity never comes from here: it comes from the list row that
supplied `idObj`, or from the material page itself.

`showMaterialDV.jsp?idMat=M` is one material. Its header does carry its
own issue identity („брой: 88, от дата 4.11.2005 г.“), the section path
(„Официален раздел / МИНИСТЕРСТВА И ДРУГИ ВЕДОМСТВА“), the start page
and the issuing body, and its text sits in a single content division.

An issue with no HTML materials answers with „Намерени резултати: 0“,
which is the signal that the issue exists only as a PDF. An idObj that
does not exist answers with HTTP 500 and a 489-byte stub saying the site
is unavailable; `DvSession` returns that body instead of retrying it and
`classify_page` names it, so a gap in the sparse idObj space costs one
request and is recorded as a fact about the id.

`classify_page` is also the guard against reading a redesign as a fact
about the Gazette: markup it cannot read is `"unrecognized"`, which is a
statement about this module, never about the issue.
"""

import logging
import re
from dataclasses import dataclass
from pathlib import Path

from bs4 import BeautifulSoup, Tag

from fetcher.dv.client import is_dv_error_body, url_for
from fetcher.dv.issues import parse_result_count

MATERIALS_PATH = "materiali.faces"
MATERIAL_PATH = "showMaterialDV.jsp"
MATERIALS_URL = url_for(MATERIALS_PATH)
MATERIAL_URL = url_for(MATERIAL_PATH)

_TABLE_ID = "material_form:dataTable1"

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class MaterialRow:
    """One material as the issue-contents page lists it."""

    id_mat: int
    section: str
    title: str
    start_page: int | None
    #: 1-based position in the listing, which is the order of publication
    #: inside the issue and the only stable ordering key the page gives.
    position: int


@dataclass(frozen=True)
class MaterialHeader:
    """The issue identity a material page states about itself."""

    issue_number: int
    issue_date: str  # ISO 8601, yyyy-mm-dd
    section_path: str
    start_page: int | None
    body_org: str


_START_PAGE_RE = re.compile(r"стр\.?\s*(\d+)")
_ID_MAT_RE = re.compile(r"idMat=(\d+)")
_HEADER_RE = re.compile(
    r"брой:\s*(\d+),\s*от\s+дата\s*(\d{1,2})\.(\d{1,2})\.(\d{4})\s*(?:г\.)?"
)


def classify_page(html: str) -> str:
    """What an answer to `materiali.faces?idObj=N` actually is.

    Four outcomes, and the distinction between the last two is the point:

    - `"materials"`: a listing whose rows were all read.
    - `"empty"`: a listing that says „Намерени резултати: 0“. A true
      statement about the issue: it is online as a whole-issue PDF only.
    - `"error_page"`: the „недостъпен“ stub. A statement about the id,
      which is sparse, so this is the ordinary answer for a gap in it.
    - `"unrecognized"`: markup this module cannot read. A statement about
      THIS CODE, never about the Gazette.

    The old check collapsed the last two, so a renamed result table would
    have written „this issue does not exist“ for all 4,146 issues and the
    coverage map would have concluded the Gazette holds no HTML at all.
    That is the failure shape D-058 records four times: a check that
    measures a proxy rather than the property.

    The property here is measurable, because the page states its own row
    count. A listing is believed only when the number of rows parsed
    equals the „Намерени резултати“ the page printed; any disagreement,
    including a missing count, is `"unrecognized"`.
    """
    if is_dv_error_body(html):
        return "error_page"
    try:
        expected = parse_result_count(html)
    except ValueError:
        log.warning("no „Намерени резултати“ count in this response")
        return "unrecognized"
    found = len(parse_materials(html))
    if found != expected:
        log.warning(
            "page reports %d materials, %d parsed; not reading it", expected, found
        )
        return "unrecognized"
    return "materials" if found else "empty"


def parse_materials(html: str) -> list[MaterialRow]:
    """Every material of one issue, in listing order."""
    soup = BeautifulSoup(html, "lxml")
    table = soup.find("table", id=_TABLE_ID)
    if table is None:
        return []
    body = table.find("tbody") or table
    rows: list[MaterialRow] = []
    for position, tr in enumerate(body.find_all("tr", recursive=False), start=1):
        cell = tr.find("td", recursive=False)
        if cell is None:
            continue
        strong = cell.find("strong")
        inner = cell.find("table")
        if strong is None or inner is None:
            continue
        link = inner.find("a", href=_ID_MAT_RE)
        if link is None:
            continue
        page_match = _START_PAGE_RE.search(inner.get_text(" ", strip=True))
        rows.append(
            MaterialRow(
                id_mat=int(_ID_MAT_RE.search(link["href"]).group(1)),
                section=strong.get_text(" ", strip=True),
                title=_title_between(strong),
                start_page=int(page_match.group(1)) if page_match else None,
                position=position,
            )
        )
    return rows


def _title_between(strong: Tag) -> str:
    """The material title: everything between the section and the inner table.

    Collected node by node rather than by a regex over the cell, because
    a title can carry its own markup (an emphasised act name, a line
    break inside a long ratification title).
    """
    parts: list[str] = []
    for node in strong.next_siblings:
        if isinstance(node, Tag):
            if node.name == "table":
                break
            parts.append(node.get_text(" "))
        else:
            parts.append(str(node))
    return re.sub(r"\s+", " ", "".join(parts)).strip()


def parse_material_header(html: str) -> MaterialHeader:
    """The issue identity, section path, page and issuing body of a material.

    This is the authority for which issue a material belongs to; the
    contents page's own header is not (it shows the site's current
    issue).
    """
    soup = BeautifulSoup(html, "lxml")
    marks = soup.find_all("span", class_="mark")
    if not marks:
        raise ValueError("no header on this material page")
    head = marks[0].get_text(" ", strip=True)
    match = _HEADER_RE.search(head)
    if match is None:
        raise ValueError(f"unreadable material header: {head!r}")
    number, day, month, year = match.groups()

    # Everything after the „г.“ that closes the date is the section path.
    section_path = head[match.end():].strip()

    start_page = None
    for mark in marks[1:]:
        page_match = _START_PAGE_RE.search(mark.get_text(" ", strip=True))
        if page_match:
            start_page = int(page_match.group(1))
            break

    title_head = soup.find("div", class_="titleHead")
    body_org = title_head.get_text(" ", strip=True) if title_head else ""

    return MaterialHeader(
        issue_number=int(number),
        issue_date=f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
        section_path=section_path,
        start_page=start_page,
        body_org=body_org,
    )


def _content_div(soup: BeautifulSoup):
    """The content region of a material page.

    Every capture has exactly one `<div style=" width: 100%;">` and it
    wraps the whole published text; the header, the logo and the F5
    performance script sit outside it. Matching on the normalised style
    attribute keeps this to one rule that is easy to re-verify against a
    fresh capture.
    """
    matches = [
        div
        for div in soup.find_all("div")
        if (div.get("style") or "").replace(" ", "") == "width:100%;"
    ]
    if not matches:
        raise ValueError("no content region on this material page")
    if len(matches) > 1:
        log.warning(
            "material page has %d content regions; taking the first", len(matches)
        )
    return matches[0]


def material_body_html(html: str) -> str:
    """The published text of a material, with the page chrome stripped.

    Returns the inner HTML of the content region unchanged: the markup is
    what the Gazette text parser (§5.4 of the design) will segment, so
    nothing inside it is normalised here.
    """
    return _content_div(BeautifulSoup(html, "lxml")).decode_contents()


def forget_session_state(session) -> None:
    """Drop the cookie jar so the next request starts a new server session.

    dv.parliament.bg binds the issue a client asks for to its server-side
    session on the FIRST request and then serves that issue for every later
    `materiali.faces` call, whatever `idObj` says. Measured live on
    2026-09-05 after a full sweep: one session over 4,146 issues yielded
    3,843 copies of the first issue's twenty materials, and three fresh-jar
    probes gave three different, correct issues. The issue LIST needs its
    session (ViewState and pagination), so this is called only here, before
    each materials or material request, and the rate limiter is untouched.
    """
    jar = getattr(session, "cookies", None)
    if jar is not None:
        jar.clear()


def fetch_materials_page(session, id_obj: int) -> str:
    """GET one issue's contents page from a fresh server session."""
    forget_session_state(session)
    return session.get(MATERIALS_URL, params={"idObj": id_obj})


def fetch_materials(session, id_obj: int) -> list[MaterialRow]:
    """GET one issue's contents and parse it.

    Returns an empty list for an issue with no HTML materials, for an
    idObj that does not exist and for markup this module cannot read. A
    caller that needs to tell those apart, as the bulk enumeration does,
    fetches the body itself and asks `classify_page`.
    """
    return parse_materials(fetch_materials_page(session, id_obj))


def fetch_material(session, id_mat: int, cache_dir: Path | None = None) -> str:
    """GET one material, returning its raw HTML.

    With `cache_dir` the raw response is stored as `<id_mat>.html` and a
    later call for the same id is served from disk without a request. A
    promulgated text never changes once published, so the cache is a
    permanent record rather than an expiring one.

    Which is exactly why the site's „недостъпен“ stub never enters it. The
    stub arrives with status 500 and `DvSession` hands it back instead of
    retrying, so without this guard a five-minute maintenance window in
    the middle of a sweep would write stubs into a permanent cache and
    every one of those materials would be unreachable until someone
    deleted the files by hand. A stub already on disk, from a run of the
    code that lacked this guard, counts as a miss and is re-fetched.
    """
    cached = Path(cache_dir) / f"{id_mat}.html" if cache_dir else None
    if cached is not None and cached.exists():
        stored = cached.read_text(encoding="utf-8")
        if not is_dv_error_body(stored):
            log.info("cache hit for material %d", id_mat)
            return stored
        log.warning(
            "cached body for material %d is the site's error stub; re-fetching",
            id_mat,
        )
    forget_session_state(session)
    html = session.get(MATERIAL_URL, params={"idMat": id_mat})
    if cached is not None and not is_dv_error_body(html):
        cached.parent.mkdir(parents=True, exist_ok=True)
        cached.write_text(html, encoding="utf-8")
    return html
