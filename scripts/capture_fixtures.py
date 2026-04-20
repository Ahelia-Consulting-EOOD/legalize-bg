"""Capture HTML fixtures from lex.bg for the test suite.

Per docs/testing/test-strategy.md, fixtures cover structural diversity.
Rate-limited to 1 req/sec.
"""

import time
import requests
from pathlib import Path

FIXTURES_DIR = Path(__file__).parent.parent / "tests" / "fixtures" / "html"

# Representative acts covering all 5 corpus categories.
# One fixture per category catches structural divergence in CSS classes
# and metadata shapes between кодекси / наредби / правилници / etc.
FIXTURES = {
    # laws
    "zop.html": 2136735703,           # ЗОП — large law, many amendments
    "zeu.html": 2135555445,           # ЗЕУ — medium law, IT domain
    # codes
    "gpk.html": 2135558368,           # Граждански процесуален кодекс
    # ordinances
    "naredba-04-14.html": 2137197056, # Modern наредба (2019)
    # regulations
    "pravilnik-sadilishta.html": 2137175683,  # Правилник за администрацията в съдилищата
    # implementing regulations
    "ppz-aktsizi.html": 2135526226,   # Правилник за прилагане на закона за акцизите
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
