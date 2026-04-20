"""Tests for transport hardening: retry, logging, Cloudflare detection.

Contract references (docs/process/delivery-contract.md "Rate Limiting Protocol"):
- Line 153: max 3 retries with exponential backoff on 429/5xx
- Line 154: stop immediately on Cloudflare challenges
- Line 155: log timestamp, URL, status code, response time
"""

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
