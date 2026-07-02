"""FR-027 search-latency probe. Cold = fresh read-only connection (OS
page cache NOT controlled — true cold needs a reboot/purge; the fresh-
connection number is still the operative regression signal). Run on a
quiet machine."""

import sqlite3
import statistics
import sys
import time

sys.path.insert(0, ".")
from index.fts import search_fts  # noqa: E402

QUERIES = [
    "обществени поръчки", "данък добавена стойност", "лични данни",
    "трудов договор", "движение по пътищата", "енергийна ефективност",
    "ЗОП", "касови апарати", "административни нарушения",
    "защита на потребителите",
]


def probe(db: str = "catalog.db", runs: int = 5) -> None:
    for q in QUERIES:
        conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        t0 = time.perf_counter()
        search_fts(cur, q, limit=10)
        cold = time.perf_counter() - t0
        warm = []
        for _ in range(runs):
            t0 = time.perf_counter()
            search_fts(cur, q, limit=10)
            warm.append(time.perf_counter() - t0)
        conn.close()
        print(f"{q!r}: cold={cold * 1000:7.0f}ms "
              f"warm_p50={statistics.median(warm) * 1000:7.0f}ms")


if __name__ == "__main__":
    probe(*sys.argv[1:2])
