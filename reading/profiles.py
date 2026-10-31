"""The act profiles (step S3 of the plan of 31 October 2026, D-075): one row per corpus act, and the
in-force question for the acts begun before the Gazette's online archive.

The register ``docs/data/act-profiles.csv`` has the fixed columns ``COLUMNS``; every value is from a closed
set or a count, and ``check`` refuses anything else. Its rows are built by script alone: the frontmatter gives
the kind (``rango``), the era (``fecha_publicacion``: HTML from 2003, PDF 1989 to 2002, before 1989; ``unknown``
when the act carries no date) and the source; the coverage map of 5 September 2026 gives the candidate grade
(no gate has graded any act, D-059); the raw page's blocks (``reading.splitter.split_lexbg``) give the layout
counts; the ``known_defects_s2`` column stays empty until S2 reports. A corpus act whose lex.bg page holds no act
(the seven site-chrome pages) or no page at all (a stub) has a row with ``page_holds_act`` ``no`` or ``no_page``
and zero counts. The row count is checked against the corpus files and the catalog.

The pairing: every act begun before the archive (the coverage map's grade C set, and any act whose own
publication date is before 1989) is paired by script with the Gazette's repeal titles the coverage map never
attributed to a corpus act: a repeal title is a candidate when its target shares content words with the act's
title (``fetcher.dv.resolver``'s normalisation) or carries the same act number. The script writes each act's
facts and candidates, and task files of ``PER_CALL`` acts for the investigator, whose instructions are in the task
(the session's agents load from the main checkout, follow-up of 2026-10-31). The model judges only the pairings:
it writes one answer file per call in the form ``ANSWER_FORM``; ``collect`` loads it, refuses a verdict outside
the form, and writes one verdict file per act. ``in_force_list`` writes ``docs/data/pre-archive-acts-in-force.yaml``
from the verdict files, with the evidence of every verdict. Nothing here writes a corpus file or a list entry.
"""
from __future__ import annotations

import argparse
import csv
import gzip
import json
import re
import sqlite3
import sys
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

import yaml
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from fetcher.bg.text_parser import content_region  # noqa: E402
from fetcher.dv.resolver import (  # noqa: E402
    _content, instruction_kind, normalise_title, numbered_key, read_frontmatter, strip_amending_prefix,
)
from reading.assembler import NUMBER_LINE  # noqa: E402
from reading.checks import _PROVISION_LIKE, _SEPARATOR, START_CHROME, TAIL_STARTS  # noqa: E402
from reading.splitter import HEADING_HINTS, decode, split_lexbg  # noqa: E402

CATEGORIES = ("laws", "codes", "ordinances", "regulations", "implementing")
REGISTER = "docs/data/act-profiles.csv"
IN_FORCE_LIST = "docs/data/pre-archive-acts-in-force.yaml"
COVERAGE_MAP = "docs/research/2026-09-05-dv-coverage-map"
RAW_LEXBG = ROOT / "data" / "raw" / "lexbg"
MATERIALS = ROOT / "data" / "dv" / "materials.jsonl"
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
VERDICTS = ("in_force", "repealed", "unknown")

_ANNEX = re.compile(r"^приложени[ея]\b")
_SUPERSCRIPT = re.compile(r"[⁰¹²³⁴⁵⁶⁷⁸⁹]|\.?SU[PР]>|<sup", re.I)
# lex.bg prints six icons beside every article (assets/images/blaws*.gif) and a tracking pixel; an image of the act's own
# (a formula, a scanned annex) is anything else in the content region
_CHROME_IMG = re.compile(r"lex\.bg/assets/|facebook\.com/tr|news\.lex\.bg")
ANSWER_FORM = """# One YAML document: a mapping from each act's slug (every slug of the task, no other) to its verdict
<slug>:
  verdict: <in_force | repealed | unknown>
  repealed_by: <the material id of the candidate repeal title, only when the verdict is repealed; otherwise null>
  evidence: <the facts and lines you relied on, in one or two sentences>
"""
INSTRUCTIONS = """You investigate acts of the legalize-bg corpus that were promulgated before the Gazette's online archive begins
(1989), so no Gazette material of theirs can be read. For each act below you are given the facts the corpus holds
about it (lex.bg's witness: its title, kind, publication date, lex.bg's in-force status, its amendment history as
lex.bg records it) and the candidate repeal titles: Gazette materials from 2003 on whose title repeals an act and
that share words with this act's title. Decide from these facts alone, for each act, whether it is still in force:
`repealed` only when a candidate title names this very act (the same act, not a same-titled predecessor or a
different act whose title shares words), with that candidate's material id; `in_force` when no candidate names it
and lex.bg's record gives no sign of repeal; `unknown` when the facts do not settle it (a candidate may name it but
the title is ambiguous, or lex.bg's record contradicts the titles). A later amendment in lex.bg's history after a
candidate repeal is evidence against that repeal. Read only this file. Write exactly one file, the answer file
named below, in the form given, with every slug of this task and an evidence note for each; write nothing else, and
reply with one line: the answer file's path."""


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
    return f"lexbg:{str(fm.get('identificador') or '').strip().strip(chr(39))}"


def layout_features(raw: bytes) -> tuple[dict[str, int], bool]:
    """The six layout counts of a lex.bg page, from its blocks, and whether the page holds an act (a spine)."""
    act = split_lexbg(raw)
    counts = {k: 0 for k in COUNTS}
    region, _ = content_region(BeautifulSoup(decode(raw), "lxml"))
    counts["table_rows"] = len(region.find_all("tr"))
    counts["images"] = sum(1 for i in region.find_all("img") if not _CHROME_IMG.search(i.get("src") or ""))
    counts["superscript_numbers"] = len(region.find_all("sup"))
    cells = {_ws(c.get_text()) for c in region.find_all(("td", "th"))}   # a table cell is a row's part, not a paragraph
    prev_heading: str | None = None
    for b in act.blocks:
        t = b.text
        low = t.casefold()
        if _ANNEX.match(low) and len(t) <= 200:
            counts["annex_headings"] += 1
        if _SUPERSCRIPT.search(t):
            counts["superscript_numbers"] += 1
        m = NUMBER_LINE.match(t)
        key = m.group(0).casefold() if m else (low if b.hint in HEADING_HINTS and len(t) <= 200 else None)
        if key is not None and key == prev_heading:
            counts["repeated_headings"] += 1
        prev_heading = key if key is not None else (None if b.hint in HEADING_HINTS else prev_heading)
        if b.hint not in HEADING_HINTS and not m and not _PROVISION_LIKE.match(t) and not _SEPARATOR.match(t) \
                and not START_CHROME.match(t) and t not in TAIL_STARTS and not _ANNEX.match(low) and t not in cells:
            counts["unnumbered_paragraphs"] += 1
    return counts, act.has_spine


def _ws(text: str) -> str:
    return re.sub(r"[ \t\xa0\r\n]+", " ", text).strip()


def _grades(root: Path) -> dict[str, str]:
    p = root / COVERAGE_MAP / "acts-summary.csv"
    if not p.exists():
        return {}
    with p.open(encoding="utf-8") as f:
        return {r["law_id"]: r["candidate_grade"] for r in csv.DictReader(f)}


def _one_row(args: tuple[str, str, Path, str, Path | None]) -> dict:
    slug, category, path, grade, raw_path = args
    fm = read_frontmatter(path) or {}
    row = {"slug": slug, "category": category, "kind": str(fm.get("rango") or "").strip(), "era": era_of(fm.get("fecha_publicacion")),
           "candidate_grade": grade or "none", "page_holds_act": "no_page", **{k: 0 for k in COUNTS}, "known_defects_s2": "",
           "source": source_of(fm)}
    if raw_path is not None and raw_path.exists():
        raw = raw_path.read_bytes()
        counts, has_act = layout_features(raw)
        row.update(counts)
        row["page_holds_act"] = "yes" if has_act else "no"
        if not has_act:
            row.update({k: 0 for k in COUNTS})
    return row


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
        fm = read_frontmatter(p) or {}
        doc_id = str(fm.get("identificador") or "").strip()
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
    """The form check: fixed columns, closed sets and counts, one row per corpus file, the catalog's rows the same set."""
    problems: list[str] = []
    seen: Counter = Counter(r.get("slug", "") for r in rows)
    for s, n in seen.items():
        if n > 1:
            problems.append(f"{s}: {n} rows")
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
            if not str(r[k]).isdigit():
                problems.append(f"{s}: {k} {r[k]!r} is not a count")
            elif r["page_holds_act"] != "yes" and int(r[k]) != 0:
                problems.append(f"{s}: {k} {r[k]} on a page without an act")
        if r["known_defects_s2"] and not all(_DEFECT_CODE.match(c) for c in r["known_defects_s2"].split(";")):
            problems.append(f"{s}: known_defects_s2 {r['known_defects_s2']!r} is not a ;-list of codes")
        if not _SOURCE.match(r["source"]):
            problems.append(f"{s}: source {r['source']!r}")
    files = {(s, c) for s, c, _ in corpus_files(root)}
    have = {(r.get("slug"), r.get("category")) for r in rows}
    for s, c in sorted(files - have):
        problems.append(f"{s}: corpus file in {c} without a row")
    for s, c in sorted(have - files):
        problems.append(f"{s}: row without a corpus file in {c}")
    if catalog is not None:
        cat = catalog_slugs(catalog)
        for s in sorted(cat - set(seen)):
            problems.append(f"{s}: in the catalog without a row")
        for s in sorted(set(seen) - cat):
            problems.append(f"{s}: row without a catalog entry")
    return problems


# --- the pairing ----------------------------------------------------------------------------------------------

def repeal_titles(materials: Path = MATERIALS, root: Path = ROOT) -> list[dict]:
    """The Gazette's repeal-titled materials the coverage map never attributed to a corpus act (as a chain row or
    a predecessor material), in the index's order."""
    attributed: set[str] = set()
    cm = root / COVERAGE_MAP / "coverage-map.csv.gz"
    if cm.exists():
        with gzip.open(cm, "rt", encoding="utf-8") as f:
            attributed |= {r["locator_id_mat"] for r in csv.DictReader(f) if r.get("locator_id_mat")}
    pm = root / COVERAGE_MAP / "predecessor-materials.csv"
    if pm.exists():
        with pm.open(encoding="utf-8") as f:
            attributed |= {r["id_mat"] for r in csv.DictReader(f) if r.get("id_mat")}
    out = []
    with materials.open(encoding="utf-8") as f:
        for line in f:
            m = json.loads(line)
            if m.get("status") != "ok" or instruction_kind(m.get("title")) != "repeal" or str(m["id_mat"]) in attributed:
                continue
            target = strip_amending_prefix(m["title"])
            out.append({"id_mat": int(m["id_mat"]), "issue": f"{m['issue_number']}/{m['issue_year']}", "date": m.get("issue_date"),
                        "title": m["title"], "target": target, "words": sorted(_content(normalise_title(target))),
                        "key": _key(target)})
    return out


def _key(title: str, year: int | None = None) -> dict | None:
    """The act type, number and year a numbered title names; the year from the title, else the one given."""
    k = numbered_key(title)
    return {"type": k.act_type, "number": k.number, "year": k.year if k.year is not None else year} if k else None


def same_number(a: dict | None, b: dict | None) -> bool:
    """The same numbered act: type and number equal, and the years equal where both are known."""
    return bool(a and b and a["type"] == b["type"] and a["number"] == b["number"]
                and (a["year"] is None or b["year"] is None or a["year"] == b["year"]))


def act_facts(slug: str, category: str, fm: dict) -> dict:
    hist = [h for h in (fm.get("amendment_history") or []) if isinstance(h, dict)]
    title = str(fm.get("titulo") or "").strip()
    return {"slug": slug, "category": category, "title": title, "kind": str(fm.get("rango") or ""),
            "fecha_publicacion": str(fm.get("fecha_publicacion") or "") or None, "estado_lexbg": fm.get("estado"),
            "ultima_actualizacion": str(fm.get("ultima_actualizacion") or "") or None,
            "amendments_recorded": len(hist), "last_amendments": [{"dv": h.get("dv"), "date": str(h.get("date") or "")} for h in hist[-3:]],
            "words": sorted(_content(normalise_title(title))), "key": _key(title, _year(fm.get("fecha_publicacion")))}


def _year(fecha) -> int | None:
    y = str(fecha or "")[:4]
    return int(y) if y.isdigit() else None


def candidates_for(act: dict, titles: list[dict], limit: int = 12) -> list[dict]:
    """The repeal titles paired with an act: two shared content words, one when the act's title has at most two,
    or the same act number; the strongest first."""
    words = set(act["words"])
    out = []
    for t in titles:
        shared = sorted(words & set(t["words"]))
        same_key = same_number(act["key"], t["key"])
        if same_key or len(shared) >= 2 or (shared and len(words) <= 2):
            out.append({**{k: t[k] for k in ("id_mat", "issue", "date", "title")}, "shared_words": shared, "same_number": same_key,
                        "score": round((len(shared) / max(len(words), 1)) + (1.0 if same_key else 0.0), 3)})
    out.sort(key=lambda c: (-c["score"], c["id_mat"]))
    return out[:limit]


def pre_archive_acts(root: Path = ROOT) -> list[tuple[str, str, Path]]:
    grades = _grades(root)
    out = []
    for slug, cat, p in corpus_files(root):
        fm = read_frontmatter(p) or {}
        if grades.get(slug) == "C" or era_of(fm.get("fecha_publicacion")) == "pre1989":
            out.append((slug, cat, p))
    return out


def pair(root: Path = ROOT, run_root: Path | None = None, materials: Path = MATERIALS, per_call: int = PER_CALL) -> dict:
    """Write each pre-archive act's facts and candidates, and the task files of the calls; return the summary."""
    run_root = run_root or root / "data" / "runs" / RUN
    titles = repeal_titles(materials, root)
    acts = pre_archive_acts(root)
    pairings = run_root / "pairings"
    pairings.mkdir(parents=True, exist_ok=True)
    (run_root / "repeal-titles.json").write_text(json.dumps(titles, ensure_ascii=False, indent=1), encoding="utf-8")
    facts_all = []
    for slug, cat, p in acts:
        facts = act_facts(slug, cat, read_frontmatter(p) or {})
        facts["candidates"] = candidates_for(facts, titles)
        (pairings / f"{slug}.json").write_text(json.dumps(facts, ensure_ascii=False, indent=1), encoding="utf-8")
        facts_all.append(facts)
    calls = run_root / "calls"
    calls.mkdir(exist_ok=True)
    call_names = []
    for k in range(0, len(facts_all), per_call):
        batch = facts_all[k:k + per_call]
        name = f"call-{k // per_call + 1:02d}"
        (calls / f"{name}.md").write_text(task_text(batch, calls / f"{name}-answer.yaml"), encoding="utf-8")
        call_names.append(name)
    summary = {"acts": len(facts_all), "repeal_titles": len(titles), "calls": call_names, "per_call": per_call,
               "with_candidates": sum(1 for f in facts_all if f["candidates"]),
               "candidates_total": sum(len(f["candidates"]) for f in facts_all), "paired_at": _now()}
    (run_root / "pairing.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8")
    return summary


def task_text(batch: list[dict], answer: Path) -> str:
    lines = ["# Investigate: are these acts, promulgated before 1989, still in force?", "", INSTRUCTIONS, "",
             f"The answer file: `{answer}`", "", "```yaml", ANSWER_FORM.strip(), "```", ""]
    for f in batch:
        lines += [f"## {f['slug']}", f"- title: {f['title']}", f"- kind: {f['kind']}; published {f['fecha_publicacion'] or 'date unknown'}; "
                  f"lex.bg records it {f['estado_lexbg']} with {f['amendments_recorded']} amendment rows, the last: "
                  + ("; ".join(f"ДВ {h['dv']} ({h['date']})" for h in f["last_amendments"]) or "none")]
        if f["candidates"]:
            lines.append("- candidate repeal titles:")
            for c in f["candidates"]:
                lines.append(f"  - material {c['id_mat']}, ДВ {c['issue']} ({c['date']}): {c['title']}"
                             + (" [same act number]" if c["same_number"] else "") + f" [shared words: {', '.join(c['shared_words'])}]")
        else:
            lines.append("- candidate repeal titles: none share words with this title")
        lines.append("")
    return "\n".join(lines)


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
        if v["verdict"] == "repealed":
            if not isinstance(v["repealed_by"], int) or v["repealed_by"] not in ids:
                problems.append(f"{s}: repealed_by {v['repealed_by']!r} is not a candidate material of this act")
        elif v["repealed_by"] is not None:
            problems.append(f"{s}: repealed_by given with the verdict {v['verdict']}")
        if not isinstance(v["evidence"], str) or not v["evidence"].strip():
            problems.append(f"{s}: evidence missing")
    return problems


def collect(run_root: Path, name: str) -> dict:
    """Load one call's answer, check it against the form, write a verdict file per act; refuse a call outside the form."""
    task = run_root / "calls" / f"{name}.md"
    answer = run_root / "calls" / f"{name}-answer.yaml"
    slugs = re.findall(r"^## (\S+)$", task.read_text(encoding="utf-8"), re.M)
    batch = [json.loads((run_root / "pairings" / f"{s}.json").read_text(encoding="utf-8")) for s in slugs]
    got = yaml.safe_load(answer.read_text(encoding="utf-8"))
    problems = check_answer(got, batch)
    if problems:
        raise ValueError(f"{name}: the answer is outside the form: " + "; ".join(problems))
    verdicts = run_root / "verdicts"
    verdicts.mkdir(exist_ok=True)
    for f in batch:
        v = got[f["slug"]]
        by = next((c for c in f["candidates"] if c["id_mat"] == v["repealed_by"]), None)
        (verdicts / f"{f['slug']}.json").write_text(json.dumps({
            "slug": f["slug"], "title": f["title"], "verdict": v["verdict"], "repealed_by": by, "evidence": v["evidence"].strip(),
            "candidates": len(f["candidates"]), "call": name, "answered_at": _now()}, ensure_ascii=False, indent=1), encoding="utf-8")
    return {"call": name, "acts": len(batch), "verdicts": Counter(got[f["slug"]]["verdict"] for f in batch)}


def in_force_list(run_root: Path, out: Path) -> dict:
    """The list of the pre-archive acts with their verdicts and evidence, from the verdict files; one verdict per paired act."""
    paired = sorted(p.stem for p in (run_root / "pairings").glob("*.json"))
    rows = []
    missing = []
    for s in paired:
        p = run_root / "verdicts" / f"{s}.json"
        if not p.exists():
            missing.append(s)
            continue
        v = json.loads(p.read_text(encoding="utf-8"))
        rows.append({"slug": s, "title": v["title"], "verdict": v["verdict"],
                     "repealed_by": ({"material": v["repealed_by"]["id_mat"], "issue": v["repealed_by"]["issue"], "title": v["repealed_by"]["title"]}
                                     if v["repealed_by"] else None),
                     "evidence": v["evidence"], "candidates": v["candidates"], "verdict_file": str(p.relative_to(run_root.parents[2]))})
    counts = Counter(r["verdict"] for r in rows)
    doc = {"what": "The acts of the corpus promulgated before the Gazette's online archive (1989), with the investigator's verdict on "
                   "whether each is still in force, from the pairing of its title with the Gazette's unattributed repeal titles (S3, D-075). "
                   "The evidence is lex.bg's witness record and the Gazette's titles; no Gazette text of these acts exists online.",
           "run": run_root.name, "written_at": _now(), "acts": len(paired), "verdicts": dict(sorted(counts.items())),
           "unanswered": missing, "entries": rows}
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(yaml.safe_dump(doc, allow_unicode=True, sort_keys=False, width=1000), encoding="utf-8")
    return {"acts": len(paired), "verdicts": dict(counts), "unanswered": missing}


def check_in_force_list(path: Path, run_root: Path) -> list[str]:
    doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    problems = []
    paired = {p.stem for p in (run_root / "pairings").glob("*.json")}
    got = {e["slug"] for e in doc.get("entries", [])}
    for s in sorted(paired - got - set(doc.get("unanswered", []))):
        problems.append(f"{s}: paired without an entry")
    for s in sorted(got - paired):
        problems.append(f"{s}: entry without a pairing")
    for e in doc.get("entries", []):
        if e.get("verdict") not in VERDICTS:
            problems.append(f"{e.get('slug')}: verdict {e.get('verdict')!r}")
        if (e.get("verdict") == "repealed") != (e.get("repealed_by") is not None):
            problems.append(f"{e.get('slug')}: repealed_by does not match the verdict")
        if not str(e.get("evidence") or "").strip():
            problems.append(f"{e.get('slug')}: no evidence")
        if not (run_root.parents[2] / str(e.get("verdict_file"))).exists():
            problems.append(f"{e.get('slug')}: verdict file {e.get('verdict_file')} missing")
    if doc.get("unanswered"):
        problems.append(f"{len(doc['unanswered'])} act(s) unanswered")
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
    p = sub.add_parser("pair", help="pair the pre-archive acts with the unattributed repeal titles and write the call tasks")
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
        print(json.dumps(s, ensure_ascii=False))
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
    import subprocess
    out = subprocess.run(["git", "rev-parse", "--git-common-dir"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    return Path(out).resolve().parent if out else ROOT


if __name__ == "__main__":
    raise SystemExit(main())
