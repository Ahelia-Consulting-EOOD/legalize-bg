"""Tests for transport hardening: retry, logging, Cloudflare detection.

Contract references (docs/process/delivery-contract.md "Rate Limiting Protocol"):
- Line 153: max 3 retries with exponential backoff on 429/5xx
- Line 154: stop immediately on Cloudflare challenges
- Line 155: log timestamp, URL, status code, response time
"""

import json
import logging
import pytest
import requests

from fetcher.bg.client import (
    CloudflareChallenge,
    RateLimitedSession,
    is_cloudflare_challenge,
)


class FakeResponse:
    def __init__(self, status_code: int, content: bytes = b"", url: str = "http://test"):
        self.status_code = status_code
        self.content = content
        self.url = url

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"{self.status_code}")


def _make_session(responses):
    """Build a RateLimitedSession whose _do_get yields from `responses` in order."""
    idx = [0]
    sess = RateLimitedSession(
        rate_limit_sec=0.0,
        sleep=lambda s: None,
        clock=lambda counter=[0.0]: (counter.__setitem__(0, counter[0] + 0.01) or counter[0]),
    )

    def fake_get(url, timeout=30):
        r = responses[idx[0]]
        idx[0] += 1
        return r

    sess._do_get = fake_get
    sess._call_count = lambda: idx[0]
    return sess


def test_retries_on_429_then_succeeds():
    sess = _make_session([FakeResponse(429), FakeResponse(429), FakeResponse(200, b"ok")])
    assert sess.get_bytes("http://x") == b"ok"
    assert sess._call_count() == 3


def test_retries_on_503_then_succeeds():
    sess = _make_session([FakeResponse(503), FakeResponse(200, b"ok")])
    assert sess.get_bytes("http://x") == b"ok"
    assert sess._call_count() == 2


def test_gives_up_after_max_retries():
    # 1 initial + 3 retries = 4 attempts
    sess = _make_session([FakeResponse(429)] * 4)
    with pytest.raises(requests.HTTPError):
        sess.get_bytes("http://x")
    assert sess._call_count() == 4


def test_success_on_first_try_no_retry():
    sess = _make_session([FakeResponse(200, b"ok")])
    assert sess.get_bytes("http://x") == b"ok"
    assert sess._call_count() == 1


def test_cloudflare_challenge_raises_immediately():
    # Status 503 + CF marker in body = stop, do not retry
    body = b"<html><body>Just a moment... checking your browser...</body></html>"
    sess = _make_session([FakeResponse(503, content=body)])
    with pytest.raises(CloudflareChallenge):
        sess.get_bytes("http://x")
    assert sess._call_count() == 1  # did NOT retry


def test_cloudflare_challenge_detection_covers_known_markers():
    assert is_cloudflare_challenge(FakeResponse(503, b"<html>Just a moment...</html>"))
    assert is_cloudflare_challenge(FakeResponse(403, b'<div id="challenge-platform"></div>'))
    assert is_cloudflare_challenge(FakeResponse(403, b"Attention Required! | Cloudflare"))
    # Plain 403 without CF markers is NOT a CF challenge
    assert not is_cloudflare_challenge(FakeResponse(403, b"Forbidden"))
    # 200 is never a CF challenge
    assert not is_cloudflare_challenge(FakeResponse(200, b"Just a moment..."))


def test_logs_request_with_status_and_elapsed(caplog):
    sess = _make_session([FakeResponse(200, b"ok")])
    with caplog.at_level(logging.INFO, logger="fetcher.bg.client"):
        sess.get_bytes("http://example.com/doc")
    matches = [r for r in caplog.records if "http://example.com/doc" in r.message]
    assert matches, "expected at least one log record for the URL"
    # The log line should include status code
    assert any("200" in r.message for r in matches)


def test_logs_retry_warning(caplog):
    sess = _make_session([FakeResponse(500), FakeResponse(200, b"ok")])
    with caplog.at_level(logging.WARNING, logger="fetcher.bg.client"):
        sess.get_bytes("http://x")
    assert any(r.levelno == logging.WARNING for r in caplog.records)


def test_4xx_other_than_429_does_not_retry():
    # 404 should raise_for_status without retrying
    sess = _make_session([FakeResponse(404)])
    with pytest.raises(requests.HTTPError):
        sess.get_bytes("http://x")
    assert sess._call_count() == 1


# --- CF-clearance cookie support (D-047 Phase 3 / Task 9) -------------------

_FAKE_CLOCK = lambda counter=[0.0]: (counter.__setitem__(0, counter[0] + 0.01) or counter[0])


def _write_cookie_file(path, token, ua="Mozilla/5.0 TestUA"):
    path.write_text(json.dumps({
        "user_agent": ua,
        "cf_clearance": token,
        "cookies": {"cf_clearance": token, "PHPSESSID": "sess-abc"},
    }), encoding="utf-8")


def _bind_get(sess, responses):
    idx = [0]

    def fake_get(url, timeout=30):
        r = responses[idx[0]]
        idx[0] += 1
        return r

    sess._do_get = fake_get
    sess._call_count = lambda: idx[0]
    return sess


def test_cookie_file_sets_user_agent_and_cookie_jar(tmp_path):
    cf = tmp_path / "cf.json"
    _write_cookie_file(cf, "TOKEN1", ua="Mozilla/5.0 RealBrowser")
    sess = RateLimitedSession(cookie_path=cf, rate_limit_sec=0.0, sleep=lambda s: None)
    assert sess._session.headers["User-Agent"] == "Mozilla/5.0 RealBrowser"
    # never advertise brotli — requests can't decode it without the package
    assert sess._session.headers.get("Accept-Encoding") == "gzip, deflate"
    jar = {c.name: c.value for c in sess._session.cookies}
    assert jar.get("cf_clearance") == "TOKEN1"
    assert jar.get("PHPSESSID") == "sess-abc"


def test_cf_challenge_waits_for_refreshed_cookie_then_retries(tmp_path):
    cf = tmp_path / "cf.json"
    _write_cookie_file(cf, "OLD")
    body = b"<html><body>Just a moment...</body></html>"
    sess = RateLimitedSession(
        cookie_path=cf, cookie_wait_sec=60, cookie_poll_sec=15,
        rate_limit_sec=0.0,
        # simulate the out-of-band Playwright re-mint on the first poll-sleep
        sleep=lambda s: _write_cookie_file(cf, "NEW"),
        clock=_FAKE_CLOCK,
    )
    _bind_get(sess, [FakeResponse(503, content=body), FakeResponse(200, b"ok")])
    assert sess.get_bytes("http://x") == b"ok"
    assert sess._call_count() == 2          # CF challenge, then success after refresh
    assert sess._cf_clearance == "NEW"      # reloaded the fresh token


def test_cf_challenge_halts_if_cookie_never_refreshes(tmp_path):
    cf = tmp_path / "cf.json"
    _write_cookie_file(cf, "STALE")
    body = b"<html><body>Just a moment...</body></html>"
    sess = RateLimitedSession(
        cookie_path=cf, cookie_wait_sec=30, cookie_poll_sec=15,
        rate_limit_sec=0.0,
        sleep=lambda s: None,               # cookie file never changes
        clock=_FAKE_CLOCK,
    )
    _bind_get(sess, [FakeResponse(503, content=body)])
    with pytest.raises(CloudflareChallenge):
        sess.get_bytes("http://x")


def test_cf_challenge_still_raises_when_wait_disabled(tmp_path):
    # cookie_path set but cookie_wait_sec=0 (default) => unchanged stop-on-CF contract
    cf = tmp_path / "cf.json"
    _write_cookie_file(cf, "X")
    body = b"<html><body>Just a moment...</body></html>"
    sess = RateLimitedSession(cookie_path=cf, rate_limit_sec=0.0, sleep=lambda s: None)
    _bind_get(sess, [FakeResponse(503, content=body)])
    with pytest.raises(CloudflareChallenge):
        sess.get_bytes("http://x")
    assert sess._call_count() == 1          # did NOT retry
