#!/usr/bin/env python3
"""Class-AGNOSTIC coverage ledger — answers "did any source text fail to reach output?"
without trusting any enumeration of classes.

Method: within the legal-content region (LCA of the content spine), every text node is
either COVERED (an ancestor's class is in the included CLASS_MAP), EXCLUDED (ancestor class
is mapped but include=False, e.g. HistoryOfDocument), or UNCOVERED (no mapped ancestor).
UNCOVERED Cyrillic text is the danger zone — it is exactly what the parser silently drops,
regardless of whether we ever "knew" the class. We report uncovered text bucketed by the
nearest class, so the residual gap is named, not guessed.
"""
import sys, re
from pathlib import Path
from collections import defaultdict
from bs4 import BeautifulSoup, NavigableString, Tag, Comment

ROOT = Path("/Users/ekimir/swprj/legalize-bg"); sys.path.insert(0, str(ROOT))
import fetcher.bg.text_parser as TP

FIX = {"AdditionalEdicts": ("## ", True), "FinalEdictsArticle": ("", True), "FinalEdicts": ("## ", True)}
SOURCES = [
    ("ЗУО", Path("/Users/ekimir/swprj/drs-business-work/source-extracts/national-law/zuo-lexbg-2026-06-21.html")),
    ("ЗЕУ", ROOT/"tests/fixtures/html/zeu.html"), ("ГПК", ROOT/"tests/fixtures/html/gpk.html"),
    ("ЗОП", ROOT/"tests/fixtures/html/zop.html"), ("ППЗ-Акцизи", ROOT/"tests/fixtures/html/ppz-aktsizi.html"),
    ("Правилник-съдилища", ROOT/"tests/fixtures/html/pravilnik-sadilishta.html"),
    ("Наредба-4-14", ROOT/"tests/fixtures/html/naredba-04-14.html"),
]
SPINE = {"TitleDocument","Part","Heading","Section","Article","TransitionalFinalEdicts",
         "AdditionalEdicts","FinalEdicts","FinalEdictsArticle","PreHistory"}
CYR = re.compile(r"[А-Яа-я]")

def lca(elements):
    if not elements: return None
    chains = []
    for el in elements:
        chain = []
        for p in el.parents:
            chain.append(id(p))
        chains.append(set(chain))
    # walk first element's ancestors closest->root; first that is ancestor of all = LCA
    common = set.intersection(*chains) if chains else set()
    for p in elements[0].parents:
        if id(p) in common:
            return p
    return None

def nearest_class(node):
    for anc in node.parents:
        cls = anc.get("class") if isinstance(anc, Tag) else None
        if cls: return "+".join(cls)
        if isinstance(anc, Tag) and anc.name in ("script","style"): return f"<{anc.name}>"
    return "<no-class>"

def ledger(name, path, css_map):
    raw = path.read_bytes().decode("cp1251","replace")
    soup = BeautifulSoup(raw, "html.parser")
    included = {c for c,(p,inc) in css_map.items() if inc}
    excluded = {c for c,(p,inc) in css_map.items() if not inc}
    spine_els = [e for e in soup.find_all(True) if set(e.get("class") or []) & SPINE]
    region = lca(spine_els) or soup
    cov=exc=unc=0
    unc_buckets = defaultdict(int)
    for tn in region.descendants:
        if not isinstance(tn, NavigableString): continue
        if isinstance(tn, Comment): continue
        parent = tn.parent
        if isinstance(parent, Tag) and parent.name in ("script","style"): continue
        s = str(tn).strip()
        if not s: continue
        n = len(s)
        anc_classes=set()
        for anc in tn.parents:
            for c in (anc.get("class") or []) if isinstance(anc,Tag) else []:
                anc_classes.add(c)
        if anc_classes & included: cov += n
        elif anc_classes & excluded: exc += n
        else:
            unc += n
            if CYR.search(s):                       # only Cyrillic = potential legal text
                unc_buckets[nearest_class(tn)] += n
    return name, cov, exc, unc, dict(unc_buckets)

def run(css_map, title):
    print(f"\n{'='*100}\n{title}\n{'='*100}")
    print(f"{'act':20s} {'covered':>10s} {'excluded':>9s} {'UNCOVERED(cyr)':>14s}   top uncovered buckets")
    print("-"*100)
    grand = defaultdict(int)
    for name, path in SOURCES:
        if not path.exists(): print(f"{name:20s} MISSING"); continue
        nm,cov,exc,unc,buckets = ledger(name, path, css_map)
        cyr_unc = sum(buckets.values())
        top = sorted(buckets.items(), key=lambda x:-x[1])[:4]
        topstr = "  ".join(f"{k}={v}" for k,v in top)
        print(f"{nm:20s} {cov:10d} {exc:9d} {cyr_unc:14d}   {topstr[:60]}")
        for k,v in buckets.items(): grand[k]+=v
    print("-"*100)
    print("UNION of uncovered Cyrillic buckets across all acts (the complete residual gap):")
    for k,v in sorted(grand.items(), key=lambda x:-x[1]):
        print(f"   {v:9d}  {k}")

if __name__ == "__main__":
    run(dict(TP.CLASS_MAP), "BASELINE — current parser (allowlist as shipped)")
    fixed = dict(TP.CLASS_MAP); fixed.update(FIX)
    run(fixed, "FIXED — current + {AdditionalEdicts, FinalEdicts, FinalEdictsArticle}")
