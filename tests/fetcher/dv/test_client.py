"""DvSession: one request per second across GET and POST, backoff, halt."""

import logging

import pytest
import requests

from fetcher.bg.client import USER_AGENT, CloudflareChallenge
from fetcher.dv.client import BASE, DvSession, is_dv_error_body, url_for

from .conftest import read_fixture

#: The site answers an unknown idObj with HTTP 500 and this 489-byte body.
ERROR_BODY = read_fixture("materiali-idObj6000-error.html")


class FakeResponse:
    def __init__(self, body: str = "ok", status: int = 200):
        self.content = body.encode("utf-8")
        self.status_code = status

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"status {self.status_code}")


class RecordingSession(DvSession):
    """A DvSession whose transport is a scripted list of responses."""

    def __init__(self, responses, **kwargs):
        super().__init__(**kwargs)
        self._responses = list(responses)
        self.calls: list[tuple[str, str, dict | None, dict | None]] = []

    def _do_request(self, method, url, *, params=None, data=None, timeout=30):
        self.calls.append((method, url, params, data))
        resp = self._responses.pop(0)
        if isinstance(resp, Exception):
            raise resp
        return resp


class Clock:
    """A monotonic clock that only advances when sleep is called."""

    def __init__(self):
        self.now = 0.0
        self.slept: list[float] = []

    def sleep(self, seconds):
        self.slept.append(seconds)
        self.now += seconds

    def __call__(self):
        return self.now


def make_session(responses, clock=None, **kwargs):
    clock = clock or Clock()
    session = RecordingSession(
        responses, sleep=clock.sleep, clock=clock, **kwargs
    )
    session.clock = clock
    return session


def test_base_url_points_at_the_gazette():
    assert BASE == "https://dv.parliament.bg/DVWeb/"


def test_url_for_joins_onto_the_base():
    assert url_for("materiali.faces") == "https://dv.parliament.bg/DVWeb/materiali.faces"


def test_get_decodes_utf8():
    session = make_session([FakeResponse("Държавен вестник")])
    assert session.get(url_for("x.faces")) == "Държавен вестник"


def test_default_user_agent_is_the_project_one():
    session = make_session([])
    assert session.headers["User-Agent"] == USER_AGENT
    assert "legalize-bg" in session.headers["User-Agent"]


def test_second_request_waits_a_full_second():
    session = make_session([FakeResponse(), FakeResponse()])
    session.get(url_for("a"))
    session.get(url_for("b"))
    assert session.clock.slept == [pytest.approx(1.0)]


def test_the_rate_limit_is_shared_between_get_and_post():
    session = make_session([FakeResponse(), FakeResponse()])
    session.get(url_for("a"))
    session.post(url_for("b"), {"k": "v"})
    assert session.clock.slept == [pytest.approx(1.0)]


def test_post_sends_the_form_data():
    session = make_session([FakeResponse()])
    session.post(url_for("broeveList.faces"), {"broi_form:selectPage": "2"})
    method, url, params, data = session.calls[0]
    assert method == "POST"
    assert data == {"broi_form:selectPage": "2"}


def test_server_error_is_retried_with_exponential_backoff():
    session = make_session(
        [FakeResponse(status=500), FakeResponse(status=503), FakeResponse("done")]
    )
    assert session.get(url_for("a")) == "done"
    # The first request needs no rate-limit wait; the two backoffs are 2 and 4,
    # and the rate-limit floor adds nothing because the backoff already spent it.
    assert session.clock.slept[:2] == [pytest.approx(2.0), pytest.approx(4.0)]


def test_the_sites_error_stub_is_a_permanent_answer_not_a_retry():
    # dv.parliament.bg returns HTTP 500 with its „недостъпен“ stub for an
    # idObj that does not exist. Retrying it costs four requests per gap
    # in a sparse id space and never changes the answer, so the body is
    # handed back for the caller to classify.
    session = make_session([FakeResponse(ERROR_BODY, 500)])
    body = session.get(url_for("materiali.faces"))
    assert "Сайтът е недостъпен" in body
    assert len(session.calls) == 1
    assert session.clock.slept == []


def test_a_server_error_with_a_real_body_is_still_retried():
    session = make_session(
        [FakeResponse("<html>oops</html>", 500), FakeResponse("done")]
    )
    assert session.get(url_for("a")) == "done"
    assert len(session.calls) == 2


def test_is_dv_error_body_ignores_real_pages(materials_html, material_html):
    assert is_dv_error_body(ERROR_BODY) is True
    assert is_dv_error_body(materials_html) is False
    assert is_dv_error_body(material_html) is False


def test_retries_are_bounded():
    session = make_session([FakeResponse(status=500)] * 4)
    with pytest.raises(requests.HTTPError):
        session.get(url_for("a"))
    assert len(session.calls) == 4  # one attempt plus three retries


def test_connection_error_is_retried():
    session = make_session(
        [requests.ConnectionError("boom"), FakeResponse("done")]
    )
    assert session.get(url_for("a")) == "done"


def test_a_challenge_halts_the_run():
    session = make_session([FakeResponse("<html>Just a moment...</html>", 403)])
    with pytest.raises(CloudflareChallenge):
        session.get(url_for("a"))


def test_every_request_is_logged_with_url_and_status(caplog):
    session = make_session([FakeResponse()])
    with caplog.at_level(logging.INFO, logger="fetcher.dv.client"):
        session.get(url_for("broeveList.faces"))
    assert any(
        "broeveList.faces" in r.getMessage() and "200" in r.getMessage()
        for r in caplog.records
    )
