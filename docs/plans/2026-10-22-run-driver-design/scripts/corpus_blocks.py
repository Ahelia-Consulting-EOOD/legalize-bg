"""Count the blocks, sections and text bytes of every act page in the raw store with the splitter (read-only).

Usage: python3 corpus_blocks.py RAW_DIR OUT.csv
Writes one row per page: doc id, has_spine, blocks, sections, text bytes (UTF-8 of all block texts),
and prints totals. Pages without a spine (site chrome only) are counted and excluded from the totals.
"""
import csv, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from reading.splitter import split_lexbg  # noqa: E402


def main():
    raw, out = Path(sys.argv[1]), sys.argv[2]
    rows = []
    t0 = time.time()
    files = sorted(raw.glob("*.html"))
    for k, p in enumerate(files, 1):
        try:
            act = split_lexbg(p.read_bytes())
            rows.append({"doc": p.stem, "spine": int(act.has_spine), "blocks": len(act.blocks), "sections": len(act.sections),
                         "bytes": sum(len(b.text.encode("utf-8")) for b in act.blocks), "error": ""})
        except Exception as exc:  # noqa: BLE001
            rows.append({"doc": p.stem, "spine": 0, "blocks": 0, "sections": 0, "bytes": 0, "error": type(exc).__name__ + ": " + str(exc)[:80]})
        if k % 500 == 0:
            print(f"{k}/{len(files)} pages, {time.time() - t0:.0f}s", flush=True)
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["doc", "spine", "blocks", "sections", "bytes", "error"]); w.writeheader(); w.writerows(rows)
    ok = [r for r in rows if r["spine"]]
    print(f"pages {len(rows)}, with an act {len(ok)}, without a spine {sum(1 for r in rows if not r['spine'] and not r['error'])}, errors {sum(1 for r in rows if r['error'])}")
    print(f"blocks {sum(r['blocks'] for r in ok):,}, sections {sum(r['sections'] for r in ok):,}, text bytes {sum(r['bytes'] for r in ok):,}")
    print(f"written to {out}")


if __name__ == "__main__":
    main()
