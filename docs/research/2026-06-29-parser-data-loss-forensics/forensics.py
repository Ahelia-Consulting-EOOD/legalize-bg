#!/usr/bin/env python3
"""Forensic harness for the legalize-bg parser data-loss defect.

Three evidence layers, all read-only:
  (1) SOURCE class census    — every CSS class in each source HTML; mapped vs dropped;
                               dropped element count + dropped text volume per act/type.
  (2) ORACLE diff            — REAL parser (current) vs in-memory FIXED map, per source;
                               proves what the fix recovers (chars, definitions, § provisions).
  (3) CORPUS audit           — all bootstrapped .md files; structural anomaly census + aggregates.

Does NOT edit fetcher/bg/text_parser.py. The "fixed" variant patches the module-level
CLASS_MAP dict IN MEMORY only (sandbox), then restores it.
"""
import json, re, sys, glob, os, html as _html
from pathlib import Path
from collections import Counter, defaultdict

ROOT = Path("/Users/ekimir/swprj/legalize-bg")
SWPRJ = Path("/Users/ekimir/swprj")
sys.path.insert(0, str(ROOT))

from bs4 import BeautifulSoup, Tag                      # noqa
import fetcher.bg.text_parser as TP                     # the protected parser (read-only use)

OUT = ROOT / "docs/research/2026-06-29-parser-data-loss-forensics"
OUT.mkdir(parents=True, exist_ok=True)

# ---- source HTML inventory (fixtures + the ZUO capture) -------------------------------
SOURCES = [
    ("ЗУО (Закон за управление на отпадъците)", "закон",
     SWPRJ / "drs-business-work/source-extracts/national-law/zuo-lexbg-2026-06-21.html"),
    ("ЗЕУ (Закон за електронното управление)", "закон", ROOT / "tests/fixtures/html/zeu.html"),
    ("ГПК (Граждански процесуален кодекс)",     "кодекс", ROOT / "tests/fixtures/html/gpk.html"),
    ("ЗОП (Закон за обществените поръчки)",      "закон", ROOT / "tests/fixtures/html/zop.html"),
    ("ППЗ Акцизи (правилник)",                   "правилник", ROOT / "tests/fixtures/html/ppz-aktsizi.html"),
    ("Правилник съдилища",                       "правилник", ROOT / "tests/fixtures/html/pravilnik-sadilishta.html"),
    ("Наредба № 4-14",                           "наредба", ROOT / "tests/fixtures/html/naredba-04-14.html"),
]

# Classes we (the analyst) consider data-bearing legal content (not chrome).
CONTENT_HINT = re.compile(r"(Edict|Article|Part|Heading|Section|Title|Document|History|Preamble|Razdel|Glava)", re.I)

def load_html(p: Path) -> BeautifulSoup:
    raw = p.read_bytes().decode("cp1251", errors="replace")
    return BeautifulSoup(raw, "html.parser")

# ---- LAYER 1: source class census ----------------------------------------------------
def class_census(soup: BeautifulSoup):
    rows = {}  # class -> {elements, text_chars}
    for el in soup.find_all(True):
        for cls in (el.get("class") or []):
            r = rows.setdefault(cls, {"elements": 0, "text_chars": 0})
            r["elements"] += 1
            r["text_chars"] += len(el.get_text(strip=True))
    return rows

# ---- LAYER 2: oracle diff (current vs in-memory fixed) --------------------------------
FIX_ADDED = {
    "AdditionalEdicts": ("## ", True),       # Допълнителни разпоредби heading
    "FinalEdictsArticle": ("", True),        # § definition / transitional bodies
    "FinalEdicts": ("## ", True),            # Заключителни разпоредби (КЪМ ...) heading variant
}
def parse_current(soup):
    return TP.HtmlToMarkdown().convert(soup)

def parse_fixed(soup):
    saved = dict(TP.CLASS_MAP)
    try:
        TP.CLASS_MAP.update(FIX_ADDED)            # in-memory sandbox patch
        return TP.HtmlToMarkdown().convert(soup)
    finally:
        TP.CLASS_MAP.clear(); TP.CLASS_MAP.update(saved)

DEF_RE = re.compile(r"По смисъла на")
PARA_RE = re.compile(r"(?m)^§\s*\d")            # a real § provision line
def metrics(md: str):
    return {
        "chars": len(md),
        "has_definitions": bool(DEF_RE.search(md)),
        "dr_heading": "Допълнителни разпоредби" in md,
        "para_provisions": len(PARA_RE.findall(md)),
    }

# ---- LAYER 3: corpus structural audit ------------------------------------------------
CONCAT_RE = re.compile(r"разпоредби(?:КЪМ|Преходни|Допълнителни)")
DANGLE_RE = re.compile(r"от допълнителн[аи][ят]+ разпоредб")
def audit_corpus_file(text: str):
    body = text.split("---", 2)[-1] if text.startswith("---") else text
    return {
        "chars": len(text),
        "dr_heading": "Допълнителни разпоредби" in text,
        "definitions": bool(re.search(r"§\s*1\.\s*По смисъла", text)) or "По смисъла на този" in text,
        "pzr_headings": len(re.findall(r"Преходни и [Зз]аключителни разпоредби", text)),
        "real_para_provisions": len(PARA_RE.findall(text)),
        "concat_artifacts": len(CONCAT_RE.findall(text)),
        "dangling_dr_refs": len(DANGLE_RE.findall(text)),
        "articles": len(re.findall(r"\*\*Чл\.", text)),
    }

def main():
    report = {"sources": [], "corpus": {}, "corpus_files": []}

    # ---- LAYER 1 + 2 over each source ----
    for name, kind, path in SOURCES:
        if not path.exists():
            report["sources"].append({"name": name, "kind": kind, "missing": str(path)})
            continue
        soup = load_html(path)
        census = class_census(soup)
        mapped = set(TP.CLASS_MAP.keys())
        dropped_content = {c: v for c, v in census.items()
                           if c not in mapped and CONTENT_HINT.search(c) and v["text_chars"] > 0}
        cur = metrics(parse_current(soup))
        fix = metrics(parse_fixed(soup))
        report["sources"].append({
            "name": name, "kind": kind,
            "AdditionalEdicts": census.get("AdditionalEdicts", {}).get("elements", 0),
            "FinalEdicts": census.get("FinalEdicts", {}).get("elements", 0),
            "TransitionalFinalEdicts": census.get("TransitionalFinalEdicts", {}).get("elements", 0),
            "FinalEdictsArticle": census.get("FinalEdictsArticle", {}).get("elements", 0),
            "FinalEdictsArticle_chars": census.get("FinalEdictsArticle", {}).get("text_chars", 0),
            "AdditionalEdicts_chars": census.get("AdditionalEdicts", {}).get("text_chars", 0),
            "dropped_content_classes": {c: v for c, v in sorted(dropped_content.items())},
            "current": cur, "fixed": fix,
            "recovered_chars": fix["chars"] - cur["chars"],
        })

    # ---- LAYER 3 over the whole corpus ----
    files = sorted(glob.glob(str(ROOT / "laws/**/*.md"), recursive=True)) + \
            sorted(glob.glob(str(ROOT / "code/**/*.md"), recursive=True)) + \
            sorted(glob.glob(str(ROOT / "ords/**/*.md"), recursive=True)) + \
            sorted(glob.glob(str(ROOT / "regs/**/*.md"), recursive=True)) + \
            sorted(glob.glob(str(ROOT / "reg_laws/**/*.md"), recursive=True))
    agg = Counter()
    sums = Counter()
    per = []
    for f in files:
        t = Path(f).read_text(encoding="utf-8", errors="replace")
        a = audit_corpus_file(t)
        per.append({"file": os.path.relpath(f, ROOT), **a})
        agg["total"] += 1
        agg["with_dr_heading"] += a["dr_heading"]
        agg["with_definitions"] += a["definitions"]
        agg["with_pzr_headings"] += (a["pzr_headings"] > 0)
        agg["with_real_provisions"] += (a["real_para_provisions"] > 0)
        agg["with_concat_artifacts"] += (a["concat_artifacts"] > 0)
        agg["with_dangling_refs"] += (a["dangling_dr_refs"] > 0)
        sums["pzr_headings"] += a["pzr_headings"]
        sums["concat_artifacts"] += a["concat_artifacts"]
        sums["dangling_dr_refs"] += a["dangling_dr_refs"]
        sums["articles"] += a["articles"]
    report["corpus"] = {"aggregate": dict(agg), "sums": dict(sums)}
    report["corpus_files"] = per

    (OUT / "forensics.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    # ---- console summary ----
    print("="*92)
    print("LAYER 1+2  SOURCE CLASS CENSUS  &  CURRENT-vs-FIXED ORACLE DIFF")
    print("="*92)
    print(f"{'act':28s} {'type':9s} {'AE':>3s} {'FEA':>4s} {'FEAchars':>9s} | "
          f"{'cur_ch':>7s} {'fix_ch':>7s} {'recov':>7s} {'def:cur→fix':>12s} {'§:cur→fix':>10s}")
    print("-"*120)
    for s in report["sources"]:
        if s.get("missing"):
            print(f"{s['name'][:28]:28s} MISSING {s['missing']}"); continue
        print(f"{s['name'][:28]:28s} {s['kind']:9s} {s['AdditionalEdicts']:3d} {s['FinalEdictsArticle']:4d} "
              f"{s['FinalEdictsArticle_chars']:9d} | {s['current']['chars']:7d} {s['fixed']['chars']:7d} "
              f"{s['recovered_chars']:7d} {str(s['current']['has_definitions'])[0]+'→'+str(s['fixed']['has_definitions'])[0]:>12s} "
              f"{str(s['current']['para_provisions'])+'→'+str(s['fixed']['para_provisions']):>10s}")
    print()
    print("Other DROPPED content-bearing classes found across sources (union):")
    union = defaultdict(lambda: [0,0])
    for s in report["sources"]:
        for c, v in s.get("dropped_content_classes", {}).items():
            union[c][0] += v["elements"]; union[c][1] += v["text_chars"]
    for c, (e, ch) in sorted(union.items(), key=lambda x:-x[1][1]):
        print(f"   {c:26s} elements={e:5d}  text_chars={ch:9d}")
    print()
    print("="*92)
    print("LAYER 3  CORPUS STRUCTURAL AUDIT")
    print("="*92)
    a = report["corpus"]["aggregate"]; sm = report["corpus"]["sums"]
    n = a["total"] or 1
    def pct(k): return f"{a[k]:4d}/{n}  ({100*a[k]/n:5.1f}%)"
    print(f"  bootstrapped acts ........................ {a['total']}")
    print(f"  with base ДР heading ..................... {pct('with_dr_heading')}")
    print(f"  with §-definitions (По смисъла) .......... {pct('with_definitions')}")
    print(f"  with any ПЗР heading ..................... {pct('with_pzr_headings')}")
    print(f"  with ANY real § provision body ........... {pct('with_real_provisions')}")
    print(f"  with concatenation artifacts ............. {pct('with_concat_artifacts')}")
    print(f"  with dangling 'от допълнителните...' refs . {pct('with_dangling_refs')}")
    print(f"  totals: ПЗР headings={sm['pzr_headings']}  concat={sm['concat_artifacts']}  "
          f"dangling={sm['dangling_dr_refs']}  articles={sm['articles']}")
    print()
    print(f"JSON written: {OUT/'forensics.json'}")

if __name__ == "__main__":
    main()
