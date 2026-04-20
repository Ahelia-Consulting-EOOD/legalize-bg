"""Content Fetcher — Legalize LegislativeClient interface for lex.bg."""

import time
from dataclasses import dataclass

import requests
from bs4 import BeautifulSoup


LEX_BG_BASE = "https://lex.bg/laws/ldoc"
ENCODING = "cp1251"
RATE_LIMIT_SECONDS = 1.0
USER_AGENT = "legalize-bg/0.1 (https://github.com/Ahelia-Consulting-EOOD/legalize-bg)"


class HttpTransport:
    """Live HTTP transport with rate limiting."""

    def __init__(self):
        self._session = requests.Session()
        self._session.headers["User-Agent"] = USER_AGENT
        self._last_request_time = 0.0

    def get(self, doc_id: int) -> bytes:
        elapsed = time.monotonic() - self._last_request_time
        if elapsed < RATE_LIMIT_SECONDS:
            time.sleep(RATE_LIMIT_SECONDS - elapsed)
        url = f"{LEX_BG_BASE}/{doc_id}"
        resp = self._session.get(url, timeout=30)
        self._last_request_time = time.monotonic()
        resp.raise_for_status()
        return resp.content

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
