"""Shared fixtures and fakes for the ДВ acquisition tests.

Every test in this package runs offline. The fakes below serve the HTML
captured from dv.parliament.bg on 2026-09-05 and record what was asked
for, so the tests can assert on the request shape as well as the parse.
"""

import pathlib

import pytest

FIXTURES = pathlib.Path(__file__).resolve().parents[2] / "fixtures" / "dv"


def read_fixture(name: str) -> str:
    """Read a captured ДВ page. The site serves UTF-8 and says so."""
    return (FIXTURES / name).read_text(encoding="utf-8")


@pytest.fixture
def issue_page1() -> str:
    return read_fixture("broeveList-page1.html")


@pytest.fixture
def issue_page2() -> str:
    return read_fixture("broeveList-page2.html")


@pytest.fixture
def materials_html() -> str:
    """Съдържание of idObj 6121, which lists eighteen materials."""
    return read_fixture("materiali-idObj6121.html")


@pytest.fixture
def materials_empty_html() -> str:
    """A valid issue page with „Намерени резултати: 0“, the PDF-era signal."""
    return read_fixture("materiali-idObj5000-empty.html")


@pytest.fixture
def error_page_html() -> str:
    """The stub the site serves for an idObj that does not exist.

    489 bytes, HTTP 500, „Сайтът е недостъпен в момента“. Captured live
    for idObj 6000 on 2026-09-05.
    """
    return read_fixture("materiali-idObj6000-error.html")


@pytest.fixture
def material_html() -> str:
    """idMat 1000, an annex published in брой 88 от 4.11.2005."""
    return read_fixture("showMaterial-idMat1000.html")


@pytest.fixture
def material_zid_html() -> str:
    """idMat 300, a ЗИД promulgated in брой 43 от 20.5.2005."""
    return read_fixture("showMaterial-idMat300-zid.html")


class FakeJar:
    """Stand-in for the requests cookie jar; records every clear()."""

    def __init__(self, owner):
        self._owner = owner
        self.clears = 0

    def clear(self) -> None:
        self.clears += 1
        self._owner.events.append(("clear", None))


class FakeSession:
    """A DvSession stand-in that serves canned bodies and records calls.

    ``get_bodies`` maps a URL suffix to a body; ``post_bodies`` maps the
    requested page number (read out of the form data) to a body.
    """

    def __init__(self, get_bodies=None, post_bodies=None, page_key=None, by_param=None):
        self._get_bodies = dict(get_bodies or {})
        self._post_bodies = dict(post_bodies or {})
        self._by_param = dict(by_param or {})
        self._page_key = page_key or "broi_form:selectPage"
        self.gets: list[tuple[str, dict | None]] = []
        self.posts: list[tuple[str, dict]] = []
        # Ordered record of jar clears and requests, so a test can assert
        # that a clear happened BEFORE a request and not merely somewhere.
        self.events: list[tuple[str, object]] = []
        self.cookies = FakeJar(self)

    def get(self, url: str, *, params=None, timeout: int = 30) -> str:
        self.gets.append((url, dict(params) if params else None))
        self.events.append(("get", dict(params) if params else None))
        for key, value in (params or {}).items():
            if (key, value) in self._by_param:
                return self._by_param[(key, value)]
        for suffix, body in self._get_bodies.items():
            if url.endswith(suffix):
                return body
        raise AssertionError(f"FakeSession has no GET body for {url!r} {params!r}")

    def post(self, url: str, data, *, timeout: int = 30) -> str:
        self.posts.append((url, dict(data)))
        page = int(dict(data)[self._page_key])
        if page not in self._post_bodies:
            raise AssertionError(f"FakeSession has no POST body for page {page}")
        return self._post_bodies[page]

    def close(self) -> None:  # pragma: no cover - nothing to release
        pass
