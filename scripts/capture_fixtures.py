"""Capture HTML fixtures from lex.bg for the test suite.

Per docs/testing/test-strategy.md, fixtures cover structural diversity.
Rate-limited to 1 req/sec.
"""

import time
import requests
from pathlib import Path

FIXTURES_DIR = Path(__file__).parent.parent / "tests" / "fixtures" / "html"

# Representative acts from test strategy.
# Additional doc IDs will be discovered from catalog crawl (Task 10).
FIXTURES = {
    "zop.html": 2136735703,   # ЗОП — large law, frequent amendments
    "zeu.html": 2135555445,   # ЗЕУ — medium law, IT domain
}

USER_AGENT = "legalize-bg/0.1 fixture-capture"


def capture():
    session = requests.Session()
    session.headers["User-Agent"] = USER_AGENT

    for filename, doc_id in FIXTURES.items():
        filepath = FIXTURES_DIR / filename
        if filepath.exists():
            print(f"  SKIP {filename} (already exists)")
            continue
        print(f"  FETCH {filename} (doc_id={doc_id})...")
        resp = session.get(f"https://lex.bg/laws/ldoc/{doc_id}", timeout=30)
        resp.raise_for_status()
        filepath.write_bytes(resp.content)
        print(f"  SAVED {len(resp.content)} bytes")
        time.sleep(1.0)

    print("Done.")


if __name__ == "__main__":
    capture()
