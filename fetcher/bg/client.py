"""Content Fetcher — Legalize LegislativeClient interface for lex.bg."""

import json
import logging
import time
from dataclasses import dataclass
from pathlib import Path

import requests
from bs4 import BeautifulSoup


LEX_BG_BASE = "https://lex.bg/laws/ldoc"
ENCODING = "cp1251"
RATE_LIMIT_SECONDS = 1.0
MAX_RETRIES = 3
RETRY_BASE_SECONDS = 2.0
USER_AGENT = "legalize-bg/0.1 (https://github.com/Ahelia-Consulting-EOOD/legalize-bg)"

log = logging.getLogger(__name__)


class CloudflareChallenge(RuntimeError):
    """Raised when a Cloudflare bot challenge is detected. Stop scraping."""


_CF_MARKERS = (
    b"just a moment",
    b"challenge-platform",
    b"cf-chl-bypass",
    b"__cf_chl_",
    b"attention required! | cloudflare",
)


def is_cloudflare_challenge(resp) -> bool:
    """Detect Cloudflare bot challenge by status + body markers."""
    if resp.status_code not in (403, 503):
        return False
    body = (resp.content or b"")[:20000].lower()
    return any(m in body for m in _CF_MARKERS)


class RateLimitedSession:
    """HTTP session with rate limiting, retry-with-backoff, logging, and
    Cloudflare challenge detection.

    Per docs/process/delivery-contract.md §Rate Limiting Protocol:
      - Max 1 req/sec
      - Max 3 retries with exponential backoff on 429/5xx
      - Stop immediately on Cloudflare challenges
      - Log timestamp (auto via logging), URL, status, response time
    """

    def __init__(
        self,
        user_agent: str = USER_AGENT,
        rate_limit_sec: float = RATE_LIMIT_SECONDS,
        max_retries: int = MAX_RETRIES,
        retry_base_sec: float = RETRY_BASE_SECONDS,
        sleep=time.sleep,
        clock=time.monotonic,
        cookie_path=None,
        cookie_wait_sec: float = 0.0,
        cookie_poll_sec: float = 15.0,
    ):
        self._session = requests.Session()
        self._session.headers["User-Agent"] = user_agent
        self._rate_limit_sec = rate_limit_sec
        self._max_retries = max_retries
        self._retry_base_sec = retry_base_sec
        self._sleep = sleep
        self._clock = clock
        self._last = 0.0
        # Cloudflare-clearance layer (D-047 Phase 3, Task 9). All OFF by default
        # so behaviour is byte-identical when cookie_path is not supplied.
        self._cookie_path = Path(cookie_path) if cookie_path else None
        self._cookie_wait_sec = cookie_wait_sec
        self._cookie_poll_sec = cookie_poll_sec
        self._cf_clearance = None
        if self._cookie_path is not None:
            # Match the real browser that minted the cookie: never advertise
            # brotli (requests can't decode it without the `brotli` package,
            # which silently corrupts the cp1251 body), and send browser-like
            # Accept headers so the cf_clearance is honoured.
            self._session.headers["Accept-Encoding"] = "gzip, deflate"
            self._session.headers["Accept"] = (
                "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
            )
            self._session.headers["Accept-Language"] = "bg,en;q=0.9"
            self._load_cookies()

    def _load_cookies(self):
        """(Re)load UA + cookie jar from the JSON cookie file onto the session.

        The file is a Playwright-minted `{user_agent, cf_clearance, cookies}`
        snapshot. Returns the current cf_clearance value (or None). Idempotent;
        called at init and again on each CF-refresh poll so an out-of-band
        re-mint is picked up.
        """
        if self._cookie_path is None or not self._cookie_path.exists():
            return self._cf_clearance
        data = json.loads(self._cookie_path.read_text(encoding="utf-8"))
        ua = data.get("user_agent")
        if ua:
            self._session.headers["User-Agent"] = ua
        cookies = data.get("cookies") or {}
        for name, val in cookies.items():
            self._session.cookies.set(name, val, domain=".lex.bg")
        self._cf_clearance = data.get("cf_clearance") or cookies.get("cf_clearance")
        return self._cf_clearance

    def _await_fresh_cookie(self, url: str) -> bool:
        """Handle a Cloudflare challenge by waiting for a fresh cf_clearance.

        Returns True if a *changed* cf_clearance was loaded from the cookie file
        (an out-of-band Playwright re-mint) so the caller should retry; False to
        fall through and raise CloudflareChallenge (the unchanged stop-on-CF
        contract). Disabled unless cookie_path is set and cookie_wait_sec > 0.

        This is NOT an automated CF bypass (D-011): the run STOPS scraping and
        waits for a human/agent to supply a fresh, legitimately browser-minted
        cookie, then resumes at <=1 req/s.
        """
        if self._cookie_path is None or self._cookie_wait_sec <= 0:
            return False
        old = self._cf_clearance
        log.error(
            "CLOUDFLARE challenge at %s — pausing; awaiting fresh cf_clearance in "
            "%s (re-mint via Playwright). Waiting up to %.0fs.",
            url, self._cookie_path, self._cookie_wait_sec,
        )
        waited = 0.0
        while waited < self._cookie_wait_sec:
            self._sleep(self._cookie_poll_sec)
            waited += self._cookie_poll_sec
            new = self._load_cookies()
            if new and new != old:
                log.info(
                    "fresh cf_clearance loaded after %.0fs — resuming %s", waited, url
                )
                self._last = self._clock()  # reset the rate-limit clock
                return True
        log.error(
            "no fresh cf_clearance within %.0fs — halting on Cloudflare (D-011).",
            self._cookie_wait_sec,
        )
        return False

    def _do_get(self, url: str, timeout: int = 30):
        """Low-level HTTP GET. Overridable for tests."""
        return self._session.get(url, timeout=timeout)

    def get_bytes(self, url: str, timeout: int = 30) -> bytes:
        """Rate-limited, retried GET returning raw bytes."""
        elapsed = self._clock() - self._last
        if elapsed < self._rate_limit_sec:
            self._sleep(self._rate_limit_sec - elapsed)

        attempt = 0
        while True:
            start = self._clock()
            try:
                resp = self._do_get(url, timeout=timeout)
            except (requests.Timeout, requests.ConnectionError) as e:
                duration_ms = int((self._clock() - start) * 1000)
                self._last = self._clock()
                log.warning("GET %s failed: %s (%d ms)", url, e, duration_ms)
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

            if is_cloudflare_challenge(resp):
                if self._await_fresh_cookie(url):
                    # A fresh, browser-minted cf_clearance was supplied out of
                    # band; retry the SAME url with the reloaded cookie. Not a
                    # backoff retry, so it does not consume the retry budget.
                    continue
                log.error(
                    "cloudflare challenge detected; stopping. url=%s status=%d",
                    url, resp.status_code,
                )
                raise CloudflareChallenge(
                    f"Cloudflare challenge at {url} (status {resp.status_code})"
                )

            log.info("GET %s -> %d (%d ms)", url, resp.status_code, duration_ms)

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
            return resp.content

    def close(self):
        self._session.close()


class HttpTransport:
    """Live HTTP transport for legislative act pages."""

    def __init__(self, session: RateLimitedSession | None = None):
        self._session = session or RateLimitedSession()

    def get(self, doc_id: int) -> bytes:
        url = f"{LEX_BG_BASE}/{doc_id}"
        return self._session.get_bytes(url)

    def close(self):
        self._session.close()


@dataclass
class LexBgClient:
    """Fetches legislative act HTML from lex.bg with cp1251 decoding."""

    transport: object  # HttpTransport or FakeTransport for tests

    def fetch(self, doc_id: int) -> str:
        """Fetch raw HTML as decoded UTF-8 string."""
        raw = self.transport.get(doc_id)
        return raw.decode(ENCODING)

    def fetch_soup(self, doc_id: int) -> BeautifulSoup:
        """Fetch and parse HTML into BeautifulSoup DOM."""
        text = self.fetch(doc_id)
        return BeautifulSoup(text, "lxml")

    def close(self):
        if hasattr(self.transport, "close"):
            self.transport.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
