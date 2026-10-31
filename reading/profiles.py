"""The act profiles (step S3 of the plan of 31 October 2026, D-075, D-077): one row per corpus act, and the
in-force question for the acts begun before the Gazette's online archive.

The register ``docs/data/act-profiles.csv`` has the fixed columns ``COLUMNS``; every value is from a closed
set or a count, and ``check`` refuses anything else and recomputes the frontmatter-derived columns (kind, era,
source, candidate grade) from their sources. Its rows are built by script alone: the frontmatter gives the kind
(``rango``), the era (``fecha_publicacion``: HTML from 2003, PDF 1989 to 2002, before 1989; ``unknown`` when the
act carries no date) and the source; the coverage map of 5 September 2026 gives the candidate grade (no gate has
graded any act, D-059); the raw page's blocks (``reading.splitter.split_lexbg``) give the layout counts, over the
act's own blocks only: the page's tail (from the first ``TAIL_STARTS`` line on), the subtrees the splitter drops
(``SKIP_CLASSES``) and the history and chrome lines are left out, as the checks leave them out. The
``known_defects_s2`` column stays empty until S2 reports. A corpus act whose lex.bg page holds no act (the seven
site-chrome pages) or no page at all (a stub) has a row with ``page_holds_act`` ``no`` or ``no_page`` and zero
counts. The row count is checked against the corpus files and the catalog.

The pairing: every act begun before the archive (the coverage map's grade C set, and any act whose own
publication date is before 1989) is paired by script with the Gazette's repeal materials the coverage map never
attributed to a corpus act: a material whose title carries the repeal verb before the name of an act (at the
title's head, as the resolver reads it, or anywhere in the title), and the general repeal decrees („за отменяне на
нормативни актове …“), whose titles name no act and whose bodies are fetched and scanned for the act's title
words. A title or body line is a candidate when it shares content words with the act's title (``fetcher.dv.resolver``'s
normalisation) or carries the same act number with no contradicting year. The facts given to the model are the
corpus's: lex.bg's history line of the act (the verbs „обн., изм., отм.“), the repeal marker a script reads from it,
the amendment rows, and the note that the frontmatter's ``estado`` is the bootstrap's constant, not a witness. The
model judges only the pairings, in the fixed form ``ANSWER_FORM``: ``in_force`` needs a fact that shows the act
alive in the HTML era and no candidate naming it; ``unknown`` is the verdict when the facts do not settle it;
``collect`` refuses a verdict outside the form and writes one verdict file per act. ``in_force_list`` writes
``docs/data/pre-archive-acts-in-force.yaml`` from the verdict files with the evidence of every verdict and the
limits of the method (the PDF era and the repeals carried inside other acts' provisions are not searched).
Nothing here writes a corpus file or a list entry.
"""
from __future__ import annotations

import argparse
import csv
import gzip
import json
import re
import sqlite3
import subprocess
import sys
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

import yaml
from bs4 import BeautifulSoup, NavigableString, Tag

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from fetcher.bg.text_parser import content_region  # noqa: E402
from fetcher.dv.resolver import (  # noqa: E402
    _content, clean_title, instruction_kind, names_an_act, normalise_title, numbered_key, read_frontmatter,
    strip_amending_prefix,
)
from reading.assembler import NUMBER_LINE  # noqa: E402
from reading.checks import _KNOWN_CHROME, _PROVISION_LIKE, _SEPARATOR, START_CHROME, TAIL_STARTS  # noqa: E402
from reading.splitter import HEADING_HINTS, SKIP_CLASSES, decode, split_dv, split_lexbg  # noqa: E402

CATEGORIES = ("laws", "codes", "ordinances", "regulations", "implementing")
REGISTER = "docs/data/act-profiles.csv"
IN_FORCE_LIST = "docs/data/pre-archive-acts-in-force.yaml"
COVERAGE_MAP = "docs/research/2026-09-05-dv-coverage-map"
RAW_LEXBG = ROOT / "data" / "raw" / "lexbg"
MATERIALS = ROOT / "data" / "dv" / "materials.jsonl"
DV_CACHE = ROOT / "data" / "dv" / "cache"
RUN = "act-profiles-2026-10-31"
PER_CALL = 10

COLUMNS = ("slug", "category", "kind", "era", "candidate_grade", "page_holds_act", "annex_headings", "table_rows", "images",
           "unnumbered_paragraphs", "superscript_numbers", "repeated_headings", "known_defects_s2", "source")
COUNTS = ("annex_headings", "table_rows", "images", "unnumbered_paragraphs", "superscript_numbers", "repeated_headings")
KINDS = ("закон", "кодекс", "наредба", "правилник", "правилник по прилагане")
ERAS = ("html", "pdf", "pre1989", "unknown")
GRADES = ("A", "B", "B-pending", "C", "none")
PAGE_HOLDS_ACT = ("yes", "no", "no_page")
_SOURCE = re.compile(r"^(lexbg:-?\d+|dv:\d+|strategy\.bg:\S+)$")
_DEFECT_CODE = re.compile(r"^[a-z_]+$")
_DIGITS = re.compile(r"^\d+$", re.ASCII)
VERDICTS = ("in_force", "repealed", "unknown")
LEXBG_MARKER = 0   # the pseudo-candidate id of lex.bg's own repeal marker („отм. ДВ. бр. …“ in the history line)

_ANNEX = re.compile(r"^приложени[ея]\s*(№|n|\d|към|$)")
_SUPERSCRIPT = re.compile(r"[⁰¹²³⁴⁵⁶⁷⁸⁹]|\.?SU[PР]>")   # a unicode superscript digit, or lex.bg's leaked tag remnant (D-072 ruling 13)
_HEAD_PREFIX = re.compile(r"^(Част|Дял|Глава|Раздел|Подраздел)\s+[\wIVXLC]+(?:\s+[а-я]+){0,3}\.?")   # a heading's number line, with or without its title after it
_HISTORY_HINTS = frozenset({"PreHistory", "HistoryOfDocument"})
# lex.bg prints six icons beside every article (assets/images/blaws*.gif) and a tracking pixel; an image of the act's own
# (a formula, a scanned annex) is anything else in the kept region
_CHROME_IMG = re.compile(r"lex\.bg/assets/|facebook\.com/tr|news\.lex\.bg")
_LIST_NUMBER = re.compile(r"^\d+[а-я]?[.)]\s*")
_BLOCK_TAGS = ("div", "p", "li", "tr", "td", "th", "table", "h1", "h2", "h3", "h4", "br")
# lex.bg's repeal marker in the history line, as refresh.py reads it
_LEXBG_REPEAL = re.compile(r"отм\.\s*ДВ\.?\s*бр\.?\s*\d+\s*от\s*\d{1,2}\s+[А-Яа-я]+\s*\d{4}\s*г?\.?", re.IGNORECASE)
# the repeal verb anywhere in a title, followed by what it repeals
_REPEAL_ANYWHERE = re.compile(r"\bза\s+(?:отмяна|отменяне)\s+на\s+(.+)$", re.IGNORECASE | re.DOTALL)
# a general repeal decree: its title names no act, its body lists them
_GENERAL_REPEAL = re.compile(r"\bза\s+(?:отмяна|отменяне)\s+на\s+(?:някои\s+)?(?:нормативни\s+актове|наредби|правилници|актове|постановления|инструкции|подзаконови)", re.IGNORECASE)

ANSWER_FORM = """# One YAML document: a mapping from each act's slug (every slug of the task, no other) to its verdict
<slug>:
  verdict: <in_force | repealed | unknown>
  repealed_by: <the material id of the candidate that repeals it, or 0 for lex.bg's own repeal marker, only when the verdict is repealed; otherwise null>
  evidence: <the facts and lines you relied on, in one or two sentences>
"""
INSTRUCTIONS = """You investigate acts of the legalize-bg corpus that were promulgated before the Gazette's online archive begins
(1989), so no Gazette material of theirs can be read. For each act below you are given the facts the corpus holds
about it and the candidate repeals a script paired with it. The facts: the act's title and kind; its publication
date; lex.bg's history line of the act, which names every publication lex.bg records with its verb („обн.“
promulgated, „изм.“ amended, „доп.“ supplemented, „отм.“ repealed; the line is a witness, not an authority), and
the repeal marker a script read from that line, if any; the last amendment rows of the corpus. The corpus's own
in-force field is the bootstrap's constant „vigente“ for every act and is no evidence, so it is not shown. The
candidates: Gazette materials from 2003 on whose title repeals an act and shares words or the act number with this
act's title, and lines of the general repeal decrees (titles that name no act) whose body lines share words with
this title. Decide from these facts alone, for each act:
- `repealed`, only when a candidate names this very act (the same act, not a same-titled predecessor or a different
  act whose title shares words, and with no later amendment in the history line that contradicts it), with that
  candidate's material id; or when lex.bg's history line carries the repeal marker, with 0;
- `in_force`, only when a fact shows the act alive in the HTML era (an amendment or publication of 2003 or later in
  the history line or the amendment rows) and no candidate names it;
- `unknown` otherwise: when the only evidence is that nothing was found, when the history ends before 2003, or when
  a candidate may name it but the title is ambiguous.
What the pairing cannot see, and you must not guess: repeals published in 1989 to 2002 (the Gazette's PDF era,
not searched) and repeals carried inside another act's transitional and final provisions. Read only this file.
Write exactly one file, the answer file named below, in the form given, with every slug of this task and an
evidence note for each; write nothing else, and reply with one line: the answer file's path."""


# --- the register ---------------------------------------------------------------------------------------------

def era_of(fecha: str | None) -> str:
    y = str(fecha or "")[:4]
    if not y.isdigit():
        return "unknown"
    return "html" if int(y) >= 2003 else "pdf" if int(y) >= 1989 else "pre1989"


def source_of(fm: dict) -> str:
    fuente = str(fm.get("fuente") or "")
    base = (fm.get("provenance") or {}).get("base") or {}
    if fuente == "dv.parliament.bg" and base.get("material"):
        return f"dv:{base['material']}"
    if fuente == "strategy.bg":
        return f"strategy.bg:{fm.get('fuente_url') or fm.get('url') or 'unknown'}"
    return f"lexbg:{_doc_id(fm)}"


def _doc_id(fm: dict) -> str:
    return str(fm.get("identificador") or "").strip().strip(chr(39))


def _ws(text: str) -> str:
    return re.sub(r"[ \t\xa0\r\n]+", " ", text).strip()


def _in_skipped(node, region: Tag) -> bool:
    """Inside a subtree the splitter drops, below the content region (what wraps the region itself does not count)."""
    for p in node.parents:
        if p is region:
            return False
        if set(p.get("class") or []) & SKIP_CLASSES:
            return True
    return False


def _cell_lines(cells: list[Tag]) -> set[str]:
    """Every line a table cell prints, as the splitter cuts it (at a break or a block-level child)."""
    out: set[str] = set()
    for c in cells:
        for t in c.find_all(_BLOCK_TAGS):
            t.insert_before("\n")
            t.insert_after("\n")
        out |= {_ws(x) for x in c.get_text().split("\n") if _ws(x)}
    return out


def _tags_of_the_act(region: Tag) -> dict[str, list[Tag]]:
    """The rows, images, superscripts and cells of the act's own markup: in document order, outside the subtrees the
    splitter drops, and before the page's tail (the first text that is a ``TAIL_STARTS`` line)."""
    out: dict[str, list[Tag]] = {"tr": [], "img": [], "sup": [], "td": [], "th": []}
    for node in region.descendants:
        if isinstance(node, Tag):
            if node.name in out and not _in_skipped(node, region):
                out[node.name].append(node)
        elif type(node) is NavigableString and _ws(str(node)) in TAIL_STARTS and not _in_skipped(node, region):
            break
    return out


def layout_features(raw: bytes) -> tuple[dict[str, int], bool]:
    """The six layout counts of a lex.bg page, from the act's own blocks, and whether the page holds an act (a spine)."""
    act = split_lexbg(raw)
    counts = {k: 0 for k in COUNTS}
    region, _ = content_region(BeautifulSoup(decode(raw), "lxml"))
    tags = _tags_of_the_act(region)
    counts["table_rows"] = len(tags["tr"])
    counts["images"] = sum(1 for i in tags["img"] if not _CHROME_IMG.search(i.get("src") or ""))
    sup_tags = len(tags["sup"])
    cells = _cell_lines(tags["td"] + tags["th"])   # a table cell is a row's part, not a paragraph
    prev_heading: str | None = None
    sup_blocks = 0
    for b in act.blocks:
        t = b.text
        if t in TAIL_STARTS:
            break   # the page's tail: the EU-acts list or the news-and-forum footer (checks.py reads it the same way)
        low = t.casefold()
        if b.hint in _HISTORY_HINTS or START_CHROME.match(t) or _SEPARATOR.match(t) or _KNOWN_CHROME.match(t):
            continue
        heading_like = b.hint in HEADING_HINTS or NUMBER_LINE.match(t) is not None
        if _ANNEX.match(low) and len(t) <= 120 and t not in cells:
            counts["annex_headings"] += 1   # a short line opening „Приложение № …“ or „Приложение към …“: the annex's own heading, whatever class lex.bg gives it
        if _SUPERSCRIPT.search(t):
            sup_blocks += 1
        m = _HEAD_PREFIX.match(t)
        key = m.group(0).rstrip(".").casefold() if m and heading_like else (low if heading_like and len(t) <= 200 else None)
        if key is not None and key == prev_heading:
            counts["repeated_headings"] += 1   # a heading number printed twice in a row, with or without its title (D-072 ruling 1)
        if heading_like:
            prev_heading = key
        elif not _PROVISION_LIKE.match(t) and not _ANNEX.match(low) and t not in cells:
            counts["unnumbered_paragraphs"] += 1
    # the unit: a superscript lex.bg printed as a tag in the kept region, or a block carrying one as a unicode digit or a
    # leaked remnant (which the page prints as text, never as a tag, so the two paths count different superscripts)
    counts["superscript_numbers"] = sup_tags + sup_blocks
    return counts, act.has_spine


def _grades(root: Path) -> dict[str, str]:
    p = root / COVERAGE_MAP / "acts-summary.csv"
    if not p.exists():
        return {}
    with p.open(encoding="utf-8") as f:
        return {r["law_id"]: r["candidate_grade"] for r in csv.DictReader(f)}


def _frontmatter_columns(slug: str, category: str, fm: dict, grade: str) -> dict:
    return {"slug": slug, "category": category, "kind": str(fm.get("rango") or "").strip(), "era": era_of(fm.get("fecha_publicacion")),
            "candidate_grade": grade or "none", "source": source_of(fm)}


def _one_row(args: tuple[str, str, Path, str, Path | None]) -> dict:
    slug, category, path, grade, raw_path = args
    fm = read_frontmatter(path) or {}
    row = {**_frontmatter_columns(slug, category, fm, grade), "page_holds_act": "no_page", **{k: 0 for k in COUNTS}, "known_defects_s2": ""}
    if raw_path is not None and raw_path.exists():
        counts, has_act = layout_features(raw_path.read_bytes())
        row["page_holds_act"] = "yes" if has_act else "no"
        if has_act:
            row.update(counts)
    return {k: row[k] for k in COLUMNS}


def corpus_files(root: Path) -> list[tuple[str, str, Path]]:
    out = []
    for cat in CATEGORIES:
        for p in sorted((root / cat).glob("*.md")):
            out.append((p.stem, cat, p))
    return out


def build(root: Path = ROOT, raw_dir: Path = RAW_LEXBG, workers: int = 1) -> list[dict]:
    grades = _grades(root)
    jobs = []
    for slug, cat, p in corpus_files(root):
        doc_id = _doc_id(read_frontmatter(p) or {})
        jobs.append((slug, cat, p, grades.get(slug, ""), raw_dir / f"{doc_id}.html" if doc_id else None))
    if workers > 1:
        with ProcessPoolExecutor(workers) as ex:
            rows = list(ex.map(_one_row, jobs, chunksize=8))
    else:
        rows = [_one_row(j) for j in jobs]
    return sorted(rows, key=lambda r: r["slug"])


def write_register(rows: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS, lineterminator="\n")
        w.writeheader()
        for r in rows:
            w.writerow({k: r[k] for k in COLUMNS})


def load_register(path: Path) -> list[dict]:
    with path.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        if tuple(reader.fieldnames or ()) != COLUMNS:
            raise ValueError(f"the register's columns are {reader.fieldnames}, not {list(COLUMNS)}")
        return list(reader)


def catalog_slugs(db: Path) -> set[str]:
    con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    try:
        return {r[0] for r in con.execute("select law_id from laws")}
    finally:
        con.close()


def check(rows: list[dict], root: Path = ROOT, catalog: Path | None = None) -> list[str]:
    """The form check: fixed columns, closed sets and counts, the frontmatter-derived columns recomputed from the
    corpus files and the coverage map, one row per corpus file, the catalog's rows the same set. The layout counts
    are not recomputed (a full pass over the raw store); ``build`` is their only writer."""
    problems: list[str] = []
    seen: Counter = Counter(r.get("slug", "") for r in rows)
    for s, n in seen.items():
        if n > 1:
            problems.append(f"{s}: {n} rows")
    files = {(s, c): p for s, c, p in corpus_files(root)}
    grades = _grades(root)
    for r in rows:
        s = r.get("slug", "?")
        if set(r) != set(COLUMNS):
            problems.append(f"{s}: columns {sorted(set(r) ^ set(COLUMNS))} outside the form")
            continue
        if r["category"] not in CATEGORIES:
            problems.append(f"{s}: category {r['category']!r}")
        if r["kind"] not in KINDS:
            problems.append(f"{s}: kind {r['kind']!r}")
        if r["era"] not in ERAS:
            problems.append(f"{s}: era {r['era']!r}")
        if r["candidate_grade"] not in GRADES:
            problems.append(f"{s}: candidate_grade {r['candidate_grade']!r}")
        if r["page_holds_act"] not in PAGE_HOLDS_ACT:
            problems.append(f"{s}: page_holds_act {r['page_holds_act']!r}")
        for k in COUNTS:
            if not _DIGITS.match(str(r[k])):
                problems.append(f"{s}: {k} {r[k]!r} is not a count")
            elif r["page_holds_act"] != "yes" and int(r[k]) != 0:
                problems.append(f"{s}: {k} {r[k]} on a page without an act")
        if r["known_defects_s2"] and not all(_DEFECT_CODE.match(c) for c in r["known_defects_s2"].split(";")):
            problems.append(f"{s}: known_defects_s2 {r['known_defects_s2']!r} is not a ;-list of codes")
        if not _SOURCE.match(r["source"]):
            problems.append(f"{s}: source {r['source']!r}")
        p = files.get((r["slug"], r["category"]))
        if p is not None:
            want = _frontmatter_columns(r["slug"], r["category"], read_frontmatter(p) or {}, grades.get(r["slug"], ""))
            for k in ("kind", "era", "candidate_grade", "source"):
                if r[k] != want[k]:
                    problems.append(f"{s}: {k} {r[k]!r} differs from its source {want[k]!r}")
    have = {(r.get("slug"), r.get("category")) for r in rows}
    for s, c in sorted(set(files) - have):
        problems.append(f"{s}: corpus file in {c} without a row")
    for s, c in sorted(have - set(files)):
        problems.append(f"{s}: row without a corpus file in {c}")
    if catalog is not None:
        cat = catalog_slugs(catalog)
        for s in sorted(cat - set(seen)):
            problems.append(f"{s}: in the catalog without a row")
        for s in sorted(set(seen) - cat):
            problems.append(f"{s}: row without a catalog entry")
    return problems


# --- the pairing ----------------------------------------------------------------------------------------------

def repeal_target(title: str | None) -> str | None:
    """What a title repeals: the act named after the repeal verb at the title's head (as the resolver reads it) or
    anywhere in the title; None when the title repeals no act (an amending title, or a repeal of a holiday)."""
    t = clean_title(title)
    if instruction_kind(t) == "repeal":
        return strip_amending_prefix(t)
    m = _REPEAL_ANYWHERE.search(t)
    if m and names_an_act(m.group(1)):
        return m.group(1).strip()
    return None


def _attributed(root: Path) -> set[str]:
    out: set[str] = set()
    cm = root / COVERAGE_MAP / "coverage-map.csv.gz"
    if cm.exists():
        with gzip.open(cm, "rt", encoding="utf-8") as f:
            out |= {r["locator_id_mat"] for r in csv.DictReader(f) if r.get("locator_id_mat")}
    pm = root / COVERAGE_MAP / "predecessor-materials.csv"
    if pm.exists():
        with pm.open(encoding="utf-8") as f:
            out |= {r["id_mat"] for r in csv.DictReader(f) if r.get("id_mat")}
    return out


def repeal_materials(materials: Path = MATERIALS, root: Path = ROOT) -> tuple[list[dict], list[dict]]:
    """(the repeal titles, the general repeal decrees): the Gazette's materials that repeal an act by title and that
    the coverage map never attributed to a corpus act (as a chain row or a predecessor material), and the decrees
    whose title names no act („за отменяне на нормативни актове …“), in the index's order."""
    attributed = _attributed(root)
    titles, general = [], []
    with materials.open(encoding="utf-8") as f:
        for line in f:
            m = json.loads(line)
            if m.get("status") != "ok" or str(m["id_mat"]) in attributed:
                continue
            rec = {"id_mat": int(m["id_mat"]), "issue": f"{m['issue_number']}/{m['issue_year']}", "date": m.get("issue_date"), "title": m["title"]}
            target = repeal_target(m.get("title"))
            if target is None:
                if _GENERAL_REPEAL.search(clean_title(m["title"])):
                    general.append(rec)
                continue
            titles.append({**rec, "target": target, "words": sorted(_content(normalise_title(target))), "key": _key(target),
                           "head": instruction_kind(m["title"]) == "repeal"})
    return titles, general


def reconcile_with_map(titles: list[dict], root: Path = ROOT) -> dict:
    """How the set of repeal titles relates to the coverage map's unattributed repeal titles of 5 September 2026
    (the map's rows carry no material id, so they are matched by issue and title)."""
    un = root / COVERAGE_MAP / "unresolved.csv.gz"
    if not un.exists():
        return {"map_rows": 0}
    with gzip.open(un, "rt", encoding="utf-8") as f:
        rows = [r for r in csv.DictReader(f) if r["kind"] == "unattributed_material" and instruction_kind(r["title"]) == "repeal"]
    ours = {(t["issue"], _ws(t["title"])) for t in titles}
    missing = [r for r in rows if (f"{r['dv_number']}/{r['dv_year']}", _ws(r["title"])) not in ours]
    return {"map_rows": len(rows), "map_rows_in_our_set": len(rows) - len(missing),
            "map_rows_missing": [{"issue": f"{r['dv_number']}/{r['dv_year']}", "title": r["title"]} for r in missing],
            "ours": len(titles), "ours_by_head_verb": sum(1 for t in titles if t["head"]), "ours_by_verb_anywhere": sum(1 for t in titles if not t["head"]),
            "note": "the index of 21 October 2026 holds materials the map's run of 5 September did not see, and the verb-anywhere rule adds titles the resolver reads as amending"}


def fetch_general_bodies(general: list[dict], cache_dir: Path = DV_CACHE, fetch=None) -> list[dict]:
    """The body lines of the general repeal decrees, fetched into the Gazette cache (the fetcher paces its requests);
    ``fetch(id_mat) -> html`` is injectable for tests."""
    if fetch is None:
        from fetcher.dv.client import DvSession
        from fetcher.dv.materials import fetch_material
        session = DvSession()
        fetch = lambda i: fetch_material(session, i, cache_dir=cache_dir)  # noqa: E731
    out = []
    for g in general:
        html = fetch(g["id_mat"])
        out.append({**g, "lines": [b.text for b in split_dv(html).blocks]})
    return out


def _key(title: str, year: int | None = None) -> dict | None:
    """The act type, number and year a numbered title names; the year from the title, else the one given."""
    k = numbered_key(title)
    return {"type": k.act_type, "number": k.number, "year": k.year if k.year is not None else year} if k else None


def same_number(a: dict | None, b: dict | None) -> bool:
    """The same numbered act: type and number equal, and the years equal where both are known."""
    return bool(a and b and a["type"] == b["type"] and a["number"] == b["number"]
                and (a["year"] is None or b["year"] is None or a["year"] == b["year"]))


def _year(fecha) -> int | None:
    y = str(fecha or "")[:4]
    return int(y) if y.isdigit() else None


def lexbg_history(raw: bytes | None) -> tuple[str, str | None]:
    """lex.bg's history line of an act (the publications with their verbs) and its repeal marker, if any."""
    if not raw:
        return "", None
    el = BeautifulSoup(decode(raw), "lxml").find(class_="HistoryOfDocument")
    text = _ws(el.get_text(" ")) if el else ""
    m = _LEXBG_REPEAL.search(text)
    return text, (m.group(0) if m else None)


def act_facts(slug: str, category: str, fm: dict, raw: bytes | None = None) -> dict:
    hist = [h for h in (fm.get("amendment_history") or []) if isinstance(h, dict)]
    title = str(fm.get("titulo") or "").strip()
    history, marker = lexbg_history(raw)
    return {"slug": slug, "category": category, "title": title, "kind": str(fm.get("rango") or ""),
            "fecha_publicacion": str(fm.get("fecha_publicacion") or "") or None,
            "ultima_actualizacion": str(fm.get("ultima_actualizacion") or "") or None,
            "amendments_recorded": len(hist), "last_amendments": [{"dv": h.get("dv"), "date": str(h.get("date") or "")} for h in hist[-3:]],
            "lexbg_history": history, "lexbg_repeal_marker": marker,
            "words": sorted(_content(normalise_title(title))), "key": _key(title, _year(fm.get("fecha_publicacion")))}


def _score(shared: list[str], words: set[str], same_key: bool) -> float:
    return round((len(shared) / max(len(words), 1)) + (1.0 if same_key else 0.0), 3)


def candidates_for(act: dict, titles: list[dict], general: list[dict] = (), limit: int = 12) -> list[dict]:
    """The repeals paired with an act: a repeal title whose target shares two content words with the act's title
    (one when the title has at most two), or names the same act number; a line of a general repeal decree by the
    same rule; lex.bg's own repeal marker, if the history line carries one. The strongest first."""
    words = set(act["words"])
    out = []

    def shared_with(cand_words: set[str], key) -> tuple[list[str], bool] | None:
        shared = sorted(words & cand_words)
        same_key = same_number(act["key"], key)
        if same_key or len(shared) >= 2 or (shared and len(words) <= 2):
            return shared, same_key
        return None

    for t in titles:
        hit = shared_with(set(t["words"]), t["key"])
        if hit:
            out.append({"kind": "title", "id_mat": t["id_mat"], "issue": t["issue"], "date": t["date"], "title": t["title"], "line": None,
                        "shared_words": hit[0], "same_number": hit[1], "score": _score(hit[0], words, hit[1])})
    for g in general:
        best = None
        for line in g.get("lines", []):
            if len(line) > 400:
                continue
            item = _LIST_NUMBER.sub("", line)   # „2. Наредба № 1 …“: the decree's list number is not the act's
            hit = shared_with(set(_content(normalise_title(item))), _key(item))
            if hit and (best is None or len(hit[0]) + hit[1] > len(best[1]) + best[2]):
                best = (line, hit[0], hit[1])
        if best:
            out.append({"kind": "body_line", "id_mat": g["id_mat"], "issue": g["issue"], "date": g["date"], "title": g["title"], "line": best[0],
                        "shared_words": best[1], "same_number": best[2], "score": _score(best[1], words, best[2])})
    out.sort(key=lambda c: (-c["score"], c["id_mat"]))
    out = out[:limit]
    if act.get("lexbg_repeal_marker"):
        out.insert(0, {"kind": "lexbg_marker", "id_mat": LEXBG_MARKER, "issue": None, "date": None, "title": act["lexbg_repeal_marker"], "line": None,
                       "shared_words": [], "same_number": False, "score": 2.0})
    return out


def pre_archive_acts(root: Path = ROOT) -> list[tuple[str, str, Path]]:
    grades = _grades(root)
    out = []
    for slug, cat, p in corpus_files(root):
        fm = read_frontmatter(p) or {}
        if grades.get(slug) == "C" or era_of(fm.get("fecha_publicacion")) == "pre1989":
            out.append((slug, cat, p))
    return out


def pair(root: Path = ROOT, run_root: Path | None = None, materials: Path = MATERIALS, per_call: int = PER_CALL,
         raw_dir: Path = RAW_LEXBG, fetch=None, cache_dir: Path = DV_CACHE) -> dict:
    """Write each pre-archive act's facts and candidates, and the task files of the calls; return the summary."""
    run_root = run_root or root / "data" / "runs" / RUN
    titles, general = repeal_materials(materials, root)
    general = fetch_general_bodies(general, cache_dir, fetch)
    acts = pre_archive_acts(root)
    pairings = run_root / "pairings"
    pairings.mkdir(parents=True, exist_ok=True)
    (run_root / "repeal-titles.json").write_text(json.dumps(titles, ensure_ascii=False, indent=1), encoding="utf-8")
    (run_root / "general-repeals.json").write_text(json.dumps(general, ensure_ascii=False, indent=1), encoding="utf-8")
    (run_root / "repeal-titles-reconciliation.json").write_text(json.dumps(reconcile_with_map(titles, root), ensure_ascii=False, indent=1), encoding="utf-8")
    facts_all = []
    for slug, cat, p in acts:
        fm = read_frontmatter(p) or {}
        page = raw_dir / f"{_doc_id(fm)}.html"
        facts = act_facts(slug, cat, fm, page.read_bytes() if page.exists() else None)
        facts["candidates"] = candidates_for(facts, titles, general)
        (pairings / f"{slug}.json").write_text(json.dumps(facts, ensure_ascii=False, indent=1), encoding="utf-8")
        facts_all.append(facts)
    calls = run_root / "calls"
    calls.mkdir(exist_ok=True)
    call_slugs: dict[str, list[str]] = {}
    for k in range(0, len(facts_all), per_call):
        batch = facts_all[k:k + per_call]
        name = f"call-{k // per_call + 1:02d}"
        (calls / f"{name}.md").write_text(task_text(batch, calls / f"{name}-answer.yaml"), encoding="utf-8")
        call_slugs[name] = [f["slug"] for f in batch]
    summary = {"acts": len(facts_all), "repeal_titles": len(titles), "general_repeal_decrees": len(general), "calls": call_slugs, "per_call": per_call,
               "with_candidates": sum(1 for f in facts_all if f["candidates"]),
               "candidates_total": sum(len(f["candidates"]) for f in facts_all),
               "with_lexbg_marker": sum(1 for f in facts_all if f["lexbg_repeal_marker"]), "paired_at": _now()}
    (run_root / "pairing.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8")
    return summary


def _history_excerpt(h: str, n: int = 420) -> str:
    return h if len(h) <= n else h[:150] + " […] " + h[-(n - 150):]


def task_text(batch: list[dict], answer: Path) -> str:
    lines = ["# Investigate: are these acts, promulgated before 1989, still in force?", "", INSTRUCTIONS, "",
             f"The answer file: `{answer}`", "", "```yaml", ANSWER_FORM.strip(), "```", ""]
    for f in batch:
        lines += [f"## {f['slug']}", f"- title: {f['title']}", f"- kind: {f['kind']}; published {f['fecha_publicacion'] or 'date unknown'}",
                  f"- lex.bg's history line: {_history_excerpt(f['lexbg_history']) or 'none on the page'}",
                  f"- repeal marker read from it: {f['lexbg_repeal_marker'] or 'none'}",
                  f"- the corpus's amendment rows: {f['amendments_recorded']}, the last: "
                  + ("; ".join(f"ДВ {h['dv']} ({h['date']})" for h in f["last_amendments"]) or "none")]
        if f["candidates"]:
            lines.append("- candidates:")
            for c in f["candidates"]:
                if c["kind"] == "lexbg_marker":
                    lines.append(f"  - 0 (lex.bg's own repeal marker): {c['title']}")
                elif c["kind"] == "body_line":
                    lines.append(f"  - material {c['id_mat']}, ДВ {c['issue']} ({c['date']}), a line of the general repeal decree „{c['title']}“: {c['line']}"
                                 + (" [same act number]" if c["same_number"] else "") + f" [shared words: {', '.join(c['shared_words'])}]")
                else:
                    lines.append(f"  - material {c['id_mat']}, ДВ {c['issue']} ({c['date']}): {c['title']}"
                                 + (" [same act number]" if c["same_number"] else "") + f" [shared words: {', '.join(c['shared_words'])}]")
        else:
            lines.append("- candidates: none share words with this title, and lex.bg's history line carries no repeal marker")
        lines.append("")
    return "\n".join(lines)


_YEAR = re.compile(r"(?<!\d)(?:19|20)\d{2}(?!\d)")   # „2007г.“: a year glued to its letter


def alive_in_html_era(facts: dict) -> bool:
    """A year of 2003 or later in lex.bg's history line or in the corpus's amendment rows: the fact an in_force verdict needs."""
    years = [int(y) for y in _YEAR.findall(facts.get("lexbg_history") or "")]
    years += [int(y) for h in facts.get("last_amendments") or [] for y in _YEAR.findall(str(h.get("date") or ""))]
    return any(y >= 2003 for y in years)


def check_answer(got: object, batch: list[dict]) -> list[str]:
    problems = []
    if not isinstance(got, dict):
        return ["the answer is not a mapping"]
    slugs = {f["slug"]: f for f in batch}
    for s in sorted(set(slugs) - set(got)):
        problems.append(f"{s}: not answered")
    for s in sorted(set(got) - set(slugs)):
        problems.append(f"{s}: not in the task")
    for s, v in got.items():
        if s not in slugs:
            continue
        if not isinstance(v, dict) or set(v) != {"verdict", "repealed_by", "evidence"}:
            problems.append(f"{s}: keys outside the form")
            continue
        if v["verdict"] not in VERDICTS:
            problems.append(f"{s}: verdict {v['verdict']!r}")
        ids = {c["id_mat"] for c in slugs[s]["candidates"]}
        by = v["repealed_by"]
        if v["verdict"] == "repealed":
            if isinstance(by, bool) or not isinstance(by, int) or by not in ids:
                problems.append(f"{s}: repealed_by {by!r} is not a candidate of this act")
        elif by is not None:
            problems.append(f"{s}: repealed_by given with the verdict {v['verdict']}")
        if v["verdict"] == "in_force":   # the fixed-form part of the rule: a script refuses what the facts cannot carry
            if slugs[s].get("lexbg_repeal_marker"):
                problems.append(f"{s}: in_force with lex.bg's repeal marker on the act")
            if not alive_in_html_era(slugs[s]):
                problems.append(f"{s}: in_force without a year of 2003 or later in the history line or the amendment rows")
        if not isinstance(v["evidence"], str) or not v["evidence"].strip():
            problems.append(f"{s}: evidence missing")
    return problems


def collect(run_root: Path, name: str) -> dict:
    """Load one call's answer, check it against the form and against the call's acts as the pairing assigned them,
    write a verdict file per act; refuse a call outside the form."""
    task = run_root / "calls" / f"{name}.md"
    answer = run_root / "calls" / f"{name}-answer.yaml"
    assigned = json.loads((run_root / "pairing.json").read_text(encoding="utf-8"))["calls"].get(name)
    if assigned is None:
        raise ValueError(f"{name}: not a call of this pairing")
    slugs = re.findall(r"^## (\S+)$", task.read_text(encoding="utf-8"), re.M)
    if slugs != assigned:
        raise ValueError(f"{name}: the task's acts {slugs} are not the ones the pairing assigned {assigned}")
    batch = [json.loads((run_root / "pairings" / f"{s}.json").read_text(encoding="utf-8")) for s in slugs]
    got = yaml.safe_load(answer.read_text(encoding="utf-8"))
    problems = check_answer(got, batch)
    if problems:
        raise ValueError(f"{name}: the answer is outside the form: " + "; ".join(problems))
    verdicts = run_root / "verdicts"
    verdicts.mkdir(exist_ok=True)
    paired_at = json.loads((run_root / "pairing.json").read_text(encoding="utf-8"))["paired_at"]
    for f in batch:
        v = got[f["slug"]]
        by = next((c for c in f["candidates"] if c["id_mat"] == v["repealed_by"]), None) if v["verdict"] == "repealed" else None
        (verdicts / f"{f['slug']}.json").write_text(json.dumps({
            "slug": f["slug"], "title": f["title"], "verdict": v["verdict"], "repealed_by": by, "evidence": v["evidence"].strip(),
            "candidates": len(f["candidates"]), "call": name, "paired_at": paired_at, "answered_at": _now()}, ensure_ascii=False, indent=1), encoding="utf-8")
    return {"call": name, "acts": len(batch), "verdicts": Counter(got[f["slug"]]["verdict"] for f in batch)}


LIMITS = [
    "The Gazette's PDF era (1989 to бр. 120/2002) was not searched: its issues expose no materials list, so a repeal published then is not seen.",
    "A repeal carried inside another act's transitional and final provisions is not seen: only materials whose title repeals an act, and the "
    "bodies of the general repeal decrees, were paired.",
    "lex.bg's history line is a witness, never an authority (D-061); the corpus's estado field is the bootstrap's constant and was not used.",
    "A verdict in_force rests on a fact that shows the act alive in the HTML era and on no candidate naming it; unknown says that nothing "
    "found is not evidence of force.",
]


def _entry(v: dict, verdict_file: str) -> dict:
    by = v["repealed_by"]
    return {"slug": v["slug"], "title": v["title"], "verdict": v["verdict"],
            "repealed_by": ({"kind": by["kind"], "material": by["id_mat"], "issue": by["issue"], "title": by["title"], "line": by.get("line")} if by else None),
            "evidence": v["evidence"], "candidates": v["candidates"], "verdict_file": verdict_file}


def _entries(run_root: Path) -> tuple[list[dict], list[str]]:
    """The entries from the verdict files of the current pairing; a verdict of an earlier pairing (another ``paired_at``
    stamp, or none) counts as missing, so a re-pair never carries an old verdict forward."""
    paired = sorted(p.stem for p in (run_root / "pairings").glob("*.json"))
    paired_at = json.loads((run_root / "pairing.json").read_text(encoding="utf-8"))["paired_at"]
    rows, missing = [], []
    for s in paired:
        p = run_root / "verdicts" / f"{s}.json"
        if not p.exists():
            missing.append(s)
            continue
        v = json.loads(p.read_text(encoding="utf-8"))
        if v.get("paired_at") != paired_at:
            missing.append(s)
            continue
        rows.append(_entry(v, str(p.relative_to(run_root.parents[2]))))
    return rows, missing


def in_force_list(run_root: Path, out: Path) -> dict:
    """The list of the pre-archive acts with their verdicts and evidence, from the verdict files; one verdict per paired act."""
    rows, missing = _entries(run_root)
    counts = Counter(r["verdict"] for r in rows)
    doc = {"what": "The acts of the corpus promulgated before the Gazette's online archive (1989), with the investigator's verdict on "
                   "whether each is still in force, from the pairing of its title with the Gazette's unattributed repeal titles and the "
                   "general repeal decrees, and from lex.bg's history line (S3, D-077). No Gazette text of these acts exists online.",
           "limits": LIMITS, "run": run_root.name, "written_at": _now(), "acts": len(rows) + len(missing),
           "verdicts": dict(sorted(counts.items())), "unanswered": missing, "entries": rows}
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(yaml.safe_dump(doc, allow_unicode=True, sort_keys=False, width=1000), encoding="utf-8")
    return {"acts": len(rows) + len(missing), "verdicts": dict(counts), "unanswered": missing}


def check_in_force_list(path: Path, run_root: Path) -> list[str]:
    """The list against the verdict files, entry by entry: an edited list, a missing pairing or a verdict outside the form is refused."""
    doc = yaml.safe_load(path.read_text(encoding="utf-8")) if path.exists() else None
    if not isinstance(doc, dict) or not isinstance(doc.get("entries"), list):
        return ["the list is empty or not a mapping with entries"]
    problems = []
    rows, missing = _entries(run_root)
    want = {r["slug"]: r for r in rows}
    entries = doc["entries"]
    if any(not isinstance(e, dict) for e in entries):
        problems.append("an entry is not a mapping")
    got = {e.get("slug"): e for e in entries if isinstance(e, dict)}
    if len(got) != len(entries):
        problems.append("an entry's slug is repeated")
    for s in sorted(set(want) - set(got)):
        problems.append(f"{s}: paired with a verdict, no entry")
    for s in sorted(set(got) - set(want)):
        problems.append(f"{s}: entry without a verdict file of this pairing")
    for s in sorted(set(want) & set(got)):
        if got[s] != want[s]:
            problems.append(f"{s}: the entry differs from its verdict file")
        if got[s].get("verdict") not in VERDICTS:
            problems.append(f"{s}: verdict {got[s].get('verdict')!r}")
        if (got[s].get("verdict") == "repealed") != (got[s].get("repealed_by") is not None):
            problems.append(f"{s}: repealed_by does not match the verdict")
        if not str(got[s].get("evidence") or "").strip():
            problems.append(f"{s}: no evidence")
    if not problems and entries != rows:
        problems.append("the entries are not the verdict files' entries in their order")
    if doc.get("acts") != len(rows) + len(missing) or doc.get("verdicts") != dict(sorted(Counter(r["verdict"] for r in rows).items())):
        problems.append("the header's counts differ from the entries")
    if doc.get("unanswered") != missing:
        problems.append(f"unanswered {doc.get('unanswered')} differs from the pairings without a verdict {missing}")
    if missing:
        problems.append(f"{len(missing)} act(s) unanswered")
    if doc.get("limits") != LIMITS:
        problems.append("the limits of the method are not stated as the module states them")
    return problems


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build", help="build the register from the corpus, the coverage map and the raw store")
    b.add_argument("--workers", type=int, default=1)
    b.add_argument("--out", default=str(ROOT / REGISTER))
    c = sub.add_parser("check", help="the form check of the register, against the corpus files and the catalog")
    c.add_argument("--register", default=str(ROOT / REGISTER))
    c.add_argument("--catalog", default=None, help="catalog.db; the main checkout's when this is a worktree")
    p = sub.add_parser("pair", help="pair the pre-archive acts with the unattributed repeals and write the call tasks")
    p.add_argument("--run", default=RUN)
    p.add_argument("--per-call", type=int, default=PER_CALL)
    co = sub.add_parser("collect", help="load one call's answer and write the verdict files")
    co.add_argument("--run", default=RUN)
    co.add_argument("call")
    li = sub.add_parser("list", help="write the in-force list from the verdict files and check it")
    li.add_argument("--run", default=RUN)
    li.add_argument("--out", default=str(ROOT / IN_FORCE_LIST))
    a = ap.parse_args(argv)
    if a.cmd == "build":
        rows = build(workers=a.workers)
        write_register(rows, Path(a.out))
        print(f"{len(rows)} rows written to {a.out}: " + ", ".join(f"{k} {v}" for k, v in sorted(Counter(r['era'] for r in rows).items()))
              + "; page_holds_act " + ", ".join(f"{k} {v}" for k, v in sorted(Counter(r['page_holds_act'] for r in rows).items())))
        return 0
    if a.cmd == "check":
        catalog = Path(a.catalog) if a.catalog else next((p for p in (ROOT / "catalog.db", _common_root() / "catalog.db") if p.exists()), None)
        rows = load_register(Path(a.register))
        problems = check(rows, ROOT, catalog)
        print(f"{len(rows)} rows, catalog {catalog}, {len(problems)} problem(s)")
        for x in problems[:50]:
            print(" ", x)
        return 1 if problems else 0
    run_root = ROOT / "data" / "runs" / a.run
    if a.cmd == "pair":
        s = pair(ROOT, run_root, per_call=a.per_call)
        print(json.dumps({k: v for k, v in s.items() if k != "calls"}, ensure_ascii=False), f"calls {len(s['calls'])}")
        return 0
    if a.cmd == "collect":
        print(collect(run_root, a.call))
        return 0
    if a.cmd == "list":
        print(in_force_list(run_root, Path(a.out)))
        problems = check_in_force_list(Path(a.out), run_root)
        print(f"{len(problems)} problem(s)" + ("".join("\n  " + x for x in problems[:30])))
        return 1 if problems else 0
    return 2


def _common_root() -> Path:
    """The main checkout of a worktree (the catalog lives there, out of git)."""
    out = subprocess.run(["git", "rev-parse", "--git-common-dir"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    return Path(out).resolve().parent if out else ROOT


if __name__ == "__main__":
    raise SystemExit(main())
