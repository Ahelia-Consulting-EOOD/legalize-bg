"""HTTP session for dv.parliament.bg (Държавен вестник).

Why this is not `fetcher.bg.client.RateLimitedSession`: that session has
GET only and decodes cp1251, and the ДВ issue list is a JSF form whose
pagination is a POST. This session keeps the same politeness contract
(one request per second, three retries with 2/4/8 second backoff, halt
on a bot challenge, every request logged) and adds POST, a shared cookie
jar and UTF-8 decoding, which is what dv.parliament.bg serves and
declares.

The rate-limit floor is one monotonic timestamp shared by GET and POST,
so a page fetch followed by a pagination POST still waits a full second.

Politeness rationale is §5.1 of the design: the site is the official
publication of the Republic, its texts are public domain under ЗАПСП
чл. 4, and the acquisition run must look like a slow, identifiable
reader rather than a crawler.
"""

import logging
import time
from urllib.parse import urljoin

import requests

from fetcher.bg.client import (
    MAX_RETRIES,
    RATE_LIMIT_SECONDS,
    RETRY_BASE_SECONDS,
    USER_AGENT,
    CloudflareChallenge,
    is_cloudflare_challenge,
)

BASE = "https://dv.parliament.bg/DVWeb/"
ENCODING = "utf-8"

log = logging.getLogger(__name__)


def url_for(path: str) -> str:
    """Absolute URL for a page of the ДВ web application."""
    return urljoin(BASE, path)


class DvSession:
    """Rate-limited GET and POST against dv.parliament.bg.

    Both verbs return the response body decoded as UTF-8 and share one
    `requests.Session`, so the JSESSIONID minted by the first GET rides
    on every later pagination POST, which is what the JSF form requires.

    Decoding is strict on purpose: dv.parliament.bg declares UTF-8 in the
    Content-Type of every page seen so far, and a decode error is a loud
    signal that the site changed rather than a body silently peppered
    with replacement characters.
    """

    def __init__(
        self,
        user_agent: str = USER_AGENT,
        rate_limit_sec: float = RATE_LIMIT_SECONDS,
        max_retries: int = MAX_RETRIES,
        retry_base_sec: float = RETRY_BASE_SECONDS,
        sleep=time.sleep,
        clock=time.monotonic,
    ):
        self._session = requests.Session()
        self._session.headers["User-Agent"] = user_agent
        self._rate_limit_sec = rate_limit_sec
        self._max_retries = max_retries
        self._retry_base_sec = retry_base_sec
        self._sleep = sleep
        self._clock = clock
        # None until the first request, so the very first call does not
        # pay a second it does not owe.
        self._last: float | None = None

    @property
    def headers(self):
        """The request headers of the underlying session."""
        return self._session.headers

    @property
    def cookies(self):
        """The cookie jar shared by every request of this session."""
        return self._session.cookies

    def _do_request(self, method: str, url: str, *, params=None, data=None, timeout=30):
        """Low-level HTTP call. The one seam tests override."""
        return self._session.request(
            method, url, params=params, data=data, timeout=timeout
        )

    def _wait_for_the_floor(self) -> None:
        if self._last is None:
            return
        elapsed = self._clock() - self._last
        if elapsed < self._rate_limit_sec:
            self._sleep(self._rate_limit_sec - elapsed)

    def _request(self, method: str, url: str, *, params=None, data=None, timeout=30) -> str:
        attempt = 0
        while True:
            self._wait_for_the_floor()
            start = self._clock()
            try:
                resp = self._do_request(
                    method, url, params=params, data=data, timeout=timeout
                )
            except (requests.Timeout, requests.ConnectionError) as e:
                duration_ms = int((self._clock() - start) * 1000)
                self._last = self._clock()
                log.warning("%s %s failed: %s (%d ms)", method, url, e, duration_ms)
                if attempt < self._max_retries:
                    backoff = self._retry_base_sec * (2 ** attempt)
                    log.warning(
                        "retrying %s in %.1fs (attempt %d/%d)",
                        url, backoff, attempt + 1, self._max_retries,
                    )
                    self._sleep(backoff)
                    attempt += 1
                    continue
                raise

            duration_ms = int((self._clock() - start) * 1000)
            self._last = self._clock()

            # dv.parliament.bg sits behind an F5 device, not Cloudflare, but
            # the challenge markers are cheap to check and the contract is the
            # same one D-011 fixed for lex.bg: a challenge halts the run.
            if is_cloudflare_challenge(resp):
                log.error(
                    "bot challenge detected; stopping. url=%s status=%d",
                    url, resp.status_code,
                )
                raise CloudflareChallenge(
                    f"Bot challenge at {url} (status {resp.status_code})"
                )

            log.info(
                "%s %s -> %d (%d ms)", method, url, resp.status_code, duration_ms
            )

            if resp.status_code == 429 or 500 <= resp.status_code < 600:
                if attempt < self._max_retries:
                    backoff = self._retry_base_sec * (2 ** attempt)
                    log.warning(
                        "retrying %s in %.1fs (attempt %d/%d) status=%d",
                        url, backoff, attempt + 1, self._max_retries, resp.status_code,
                    )
                    self._sleep(backoff)
                    attempt += 1
                    continue

            resp.raise_for_status()
            return resp.content.decode(ENCODING)

    def get(self, url: str, *, params=None, timeout: int = 30) -> str:
        """Rate-limited, retried GET returning the body as text."""
        return self._request("GET", url, params=params, timeout=timeout)

    def post(self, url: str, data, *, timeout: int = 30) -> str:
        """Rate-limited, retried form POST returning the body as text."""
        return self._request("POST", url, data=data, timeout=timeout)

    def close(self) -> None:
        self._session.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
