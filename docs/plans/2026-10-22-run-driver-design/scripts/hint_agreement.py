"""How often the model's label equals what the lex.bg class alone would give (evidence, not a design change).

The splitter gives every block a hint: the lex.bg class of its nearest classified ancestor (Title, Article,
FinalEdictsArticle, PreHistory, unknown). A class alone names a family of labels, not one label: Title covers
the act's title and every heading; Article covers every line of a provision; FinalEdictsArticle the lines of
the § provisions; PreHistory the in-force line. This script reads each act's final map (``map.json``, after
the ladder) and prints the crosstab hint x label, the share of blocks whose label is in the hint's family, and
the share where the hint alone would have given the exact label (only where a family has one member).

Usage: python3 hint_agreement.py RUN_ROOT OUT_DIR
"""
import json, sys, collections
from pathlib import Path

FAMILY = {
    "Title": {"title", "part_heading", "chapter_heading", "section_heading", "subsection_heading", "provisions_heading", "annex_heading", "article_title"},
    "PreHistory": {"prehistory"},
    "Article": {"article_head", "alinea", "unnumbered_alinea", "item", "unnumbered_item", "letter", "continuation", "quoted", "table_row", "editorial_note", "repeal_note"},
    "FinalEdictsArticle": {"paragraph_sign", "alinea", "item", "letter", "continuation", "quoted", "unnumbered_item", "adoption_formula", "annex_heading", "annex_row", "table_row", "editorial_note", "repeal_note"},
    "unknown": set(),
}


def main():
    run_root, out_dir = Path(sys.argv[1]), Path(sys.argv[2])
    cross = collections.defaultdict(collections.Counter)
    total = 0
    for d in sorted(run_root.iterdir()):
        bj, mj = d / "blocks.json", d / "map.json"
        if not bj.exists() or not mj.exists():
            continue
        blocks = json.loads(bj.read_text(encoding="utf-8"))["blocks"]
        smap = json.loads(mj.read_text(encoding="utf-8"))
        for b in blocks:
            e = smap.get(str(b["i"]))
            if not e:
                continue
            cross[b["hint"]][e["label"]] += 1
            total += 1
    lines = [f"Blocks with a final label over the labelled acts: {total:,}\n", "## Crosstab: lex.bg class (hint) by the model's final label\n"]
    for hint in sorted(cross, key=lambda h: -sum(cross[h].values())):
        c = cross[hint]; n = sum(c.values())
        fam = sum(v for k, v in c.items() if k in FAMILY.get(hint, set()))
        lines.append(f"**{hint}** ({n:,} blocks; {100 * fam / n:.1f}% in the class's family): " + ", ".join(f"{k} {v:,}" for k, v in c.most_common()))
    exact = 0
    for hint, c in cross.items():
        if len(FAMILY.get(hint, set())) == 1:
            exact += c.get(next(iter(FAMILY[hint])), 0)
    one_member = sum(sum(c.values()) for h, c in cross.items() if len(FAMILY.get(h, set())) == 1)
    fam_all = sum(v for h, c in cross.items() for k, v in c.items() if k in FAMILY.get(h, set()))
    lines.append(f"\nShare of blocks whose label lies in the class's family: {100 * fam_all / total:.1f}%. "
                 f"Classes with a single-member family (PreHistory): {one_member:,} blocks, of which the exact label matches in {exact:,}. "
                 f"For every other class the class alone cannot name the label: Title does not say which heading level, Article does not say head, alinea, item, letter, continuation or quoted, and that is the whole judgement.")
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "hints.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    json.dump({h: dict(c) for h, c in cross.items()}, open(out_dir / "crosstab.json", "w"), ensure_ascii=False, indent=1)
    print("\n".join(lines))


if __name__ == "__main__":
    main()
