"""Verify catalog.json against COVERAGE-FLOOR.md expectations.

Gate for Task 11 (full bootstrap): the dry-run catalog must look sane
before we spend 2 hours fetching 3,574 act pages.
"""

import json
import sys
from collections import Counter
from pathlib import Path


EXPECTED = {
    "laws": (300, 500, 394),        # (min, max, target)
    "code": (15, 40, 24),
    "ords": (2000, 3200, 2604),
    "regs": (350, 650, 490),
    "reg_laws": (40, 100, 61),
}
EXPECTED_TOTAL = 3574  # target; acceptable band is sum of category mins/maxes


def verify(path: Path) -> int:
    catalog = json.loads(path.read_text(encoding="utf-8"))
    failures = 0

    print(f"Total entries: {len(catalog)}")
    print(f"Expected total (target): ~{EXPECTED_TOTAL}")
    print()

    # Per-category counts
    per_cat: Counter = Counter(e["category"] for e in catalog)
    print("Per-category counts:")
    for cat, (lo, hi, target) in EXPECTED.items():
        got = per_cat.get(cat, 0)
        status = "OK" if lo <= got <= hi else "FAIL"
        if status == "FAIL":
            failures += 1
        print(f"  {cat:<10} {got:>5}  (target ~{target}, range {lo}-{hi}) [{status}]")

    # Unknown categories
    unknown = set(per_cat) - set(EXPECTED)
    if unknown:
        failures += 1
        print(f"\nFAIL: unexpected categories: {unknown}")

    # Empty names
    empty_names = [e for e in catalog if not e.get("name", "").strip()]
    if empty_names:
        failures += 1
        print(f"\nFAIL: {len(empty_names)} entries have empty name")
        for e in empty_names[:3]:
            print(f"  doc_id={e['doc_id']} category={e['category']}")

    # Duplicate doc_ids across the whole catalog
    doc_id_counts = Counter(e["doc_id"] for e in catalog)
    duplicates = {did: n for did, n in doc_id_counts.items() if n > 1}
    if duplicates:
        # Not necessarily a failure — lex.bg puts Конституция on every tree
        # page as a sidebar link. Report the details so bootstrap can dedup.
        print(f"\nINFO: {len(duplicates)} distinct doc_ids appear more than once")
        print(f"      total duplicate entries: {sum(duplicates.values()) - len(duplicates)}")
        top = sorted(duplicates.items(), key=lambda x: -x[1])[:5]
        for did, n in top:
            names = set(e["name"] for e in catalog if e["doc_id"] == did)
            cats = set(e["category"] for e in catalog if e["doc_id"] == did)
            print(f"  doc_id={did:>12} appears {n}× across {len(cats)} categories")
            print(f"      names: {list(names)[:2]}")
            print(f"      categories: {sorted(cats)}")

    # Unique doc_ids
    unique_docs = len(doc_id_counts)
    print(f"\nUnique doc_ids: {unique_docs}")
    print(f"Expected unique (target): ~{EXPECTED_TOTAL}")
    delta = unique_docs - EXPECTED_TOTAL
    print(f"Delta vs target: {delta:+d} ({100.0 * delta / EXPECTED_TOTAL:+.1f}%)")

    print()
    if failures == 0:
        print("VERDICT: OK — catalog shape looks sane, safe to proceed to Task 11")
        print("         (dedup duplicate doc_ids in the crawler or bootstrap loop first)")
    else:
        print(f"VERDICT: FAIL — {failures} issue(s); investigate before Task 11")
    return failures


if __name__ == "__main__":
    path = Path(sys.argv[1] if len(sys.argv) > 1 else "catalog.json")
    sys.exit(verify(path))
