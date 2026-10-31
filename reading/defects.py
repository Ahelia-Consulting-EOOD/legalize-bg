"""Step S2 of the plan of 31 October 2026 (D-075, D-076): what lex.bg gets wrong.

The dropped-section detector of FR-042 (``scripts/structure_gaps.py``) reads the corpus Markdown; here its two rules
run over every raw lex.bg page of the raw store, block by block through the splitter, with no model:

- ``additional-empty``: a block that is the heading „Допълнителна разпоредба“ (or the plural) followed, after lex.bg's
  own qualifier lines (a „КЪМ …“ line, an „(обн. …)“ line, a repeated copy of the heading, decision D-072 ruling 1),
  by a transitional or final provisions heading: the section has no text under it;
- ``paragraph-start-above-1``: the lowest § number that opens a block of the act's own provisions tail is above 1 (the
  corpus detector took the lowest bold § of the file; on the page, the tails lex.bg appends for later amending acts carry
  only the §§ that concern the act, so their numbers say nothing, and an act whose own tail is a „Параграф единствен“ is
  no candidate); where the page has no provisions heading at all, the lowest § of the page.

Each candidate the scan lists is checked against the Gazette: ``fetch`` takes the act's promulgation material from
the coverage map's attribution (``docs/research/2026-09-05-dv-coverage-map/acts-summary.csv``), or, where the map
attributed none, from a title search of the Gazette index in the issue the act cites, and fetches it into the Gazette
cache at one request per second. ``tasks`` cuts both texts to the act's own provisions tail (from the first
additional, transitional or final provisions heading to the point where lex.bg's tails of later amending acts begin,
with three blocks before it) and packs several candidates into one call file for the ``investigator``, whose
instructions are in the call file itself (the follow-up of 2026-10-31: the session's agents load from the main
checkout). ``collect`` holds every answer to the closed sets and writes one verdict file per candidate; a candidate
whose material cannot be retrieved gets its verdict ``unverified`` from the script, never from an aggregator.
``count`` prints the verdict files against the candidates. ``list`` puts every confirmed act on the exceptions list
through the route driver and walks its route, which stops with a case file where the engine of F1 is not built.

The closed sets: ``VERDICTS`` per candidate and ``KINDS`` of lex.bg's errors (the plan's five; they grow only by the
owner's word, and the register ``docs/data/lexbg-defect-kinds.yaml`` holds one entry per kind, see
``reading/defect_kinds.py``). Nothing here writes a corpus file or calls a model.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import source_exceptions as sx  # noqa: E402
from reading.splitter import Block, split_dv, split_lexbg  # noqa: E402

RUN_NAME = "s2-lexbg-defects-2026-10-31"
RAW_LEXBG = Path("data/raw/lexbg")                                            # every store path is relative to the root given
DV_CACHE = Path("data/dv/cache")
DV_INDEX = Path("data/dv/materials.jsonl")
SUMMARY = Path("docs/research/2026-09-05-dv-coverage-map/acts-summary.csv")
REGISTER = "docs/data/lexbg-defect-kinds.yaml"

RULES = ("additional-empty", "paragraph-start-above-1")
VERDICTS: dict[str, str] = {
    "confirmed": "the Gazette carries, in the act's own provisions, what lex.bg lacks or prints wrong; `kind` names the error",
    "not_a_defect": "lex.bg carries the act's provisions as the Gazette does (the § numbering starts above 1 because the §§ belong to the adopting act, or the heading lex.bg prints is the Gazette's own)",
    "unverified": "the texts do not settle it (the material could not be retrieved, or its tail does not hold the act's provisions)",
    "needs_whole_text": "the tails do not settle it and the whole texts may; one whole-text call follows, never a second",
}
KINDS: dict[str, str] = {
    "dropped_section": "lex.bg prints a section heading with no text under it, or omits the section, whose text the Gazette carries (in the promulgation material, or in the amending material that added the section: lex.bg's form is the same)",
    "dropped_provision": "lex.bg omits one or more provisions (§ or article) of a section it does print, which the Gazette carries",
    "wrong_number": "lex.bg prints a provision the Gazette carries under another number",
    "wrong_text": "lex.bg's text of a provision differs in its words from the Gazette's, beyond an amendment lex.bg marks",
    "missing_amendment": "lex.bg's text lacks an amendment the Gazette published after the promulgation",
}
STAGES = ("tails", "whole", "amendment", "script")
STAGE_RANK = {"script": 0, "tails": 1, "whole": 2, "amendment": 2}   # a later stage's verdict is never written over by an earlier stage's answer
PER_CALL = 8            # candidates per call at most
CAP_TOKENS = 40_000     # estimated content tokens per call at most (the measured safe range of a lean call is 25,000 of task text)
BYTES_PER_TOKEN = 3.44  # the Read rate fitted in the run-driver study of 21 October 2026
CONTEXT_BLOCKS = 3
MOST_WHOLE_TOKENS = 60_000   # a whole-text or amendment call beyond this is not made; one above CAP_TOKENS is marked on its verdict

PROVISIONS = re.compile(r"^(допълнителн[аи](\s+и\s+заключителн[аи])?|преходн[аи](\s+и\s+заключителн[аи])?|заключителн[аи])\s+разпоредб[аи]\b", re.I)
ADDITIONAL = re.compile(r"^допълнителн[аи]\s+разпоредб[аи]\.?$", re.I)
FINAL = re.compile(r"^(преходн[аи](\s+и\s+заключителн[аи])?|заключителн[аи])\s+разпоредб[аи]\b", re.I)
QUALIFIER = re.compile(r"^(КЪМ\s|\(\s*(?i:обн)|\(\s*(?i:загл))")
KYM = re.compile(r"^КЪМ\s")
SIGN = re.compile(r"^§\s*(\d+)\s*\.")
ARTICLE = re.compile(r"^Чл\.\s*\d")
ANNEX = re.compile(r"^Приложение\s*(№|към|\d)", re.I)
# the title line of an act in a material: the kind in capitals, at most its number and date ("ЗАКОН", "НАРЕДБА № Н-4 от 30 март 2026 г.")
KIND_TITLE = re.compile(r"^(ЗАКОН|КОДЕКС|НАРЕДБА|ПРАВИЛНИК|УСТРОЙСТВЕН ПРАВИЛНИК|ИНСТРУКЦИЯ|ПОСТАНОВЛЕНИЕ|УКАЗ|РЕШЕНИЕ|ТАРИФА|ПРАВИЛА|ПОЛОЖЕНИЕ|МЕТОДИКА)"
                        r"(\s+№\s*\S+)?(\s+(?i:от)\s+\d{1,2}\s+\S+\s+\d{4}\s*(?i:г)\.?)?(\s+(на|за|относно|по)\s.*)?\s*$")   # the name may follow on the line
CHAPTER = re.compile(r"^(Глава|Раздел|Част|Дял)\s", re.I)
_WORD = re.compile(r"[^\w\s]+", re.U)
_NUMBER_KEY = re.compile(r"^(наредба|правилник|постановление|инструкция|указ|закон|кодекс)\s+№?\s*([\w-]+)\s+от\s+.*?(\d{4})", re.I)
WORD_SHARE = 0.7    # of the act's distinctive words, the share a row's title must carry to be the act's material
STOP_WORDS = frozenset("за на и в по от с към при или до под над г".split())


class DefectsError(ValueError):
    """A file outside its form or a request outside the bounds; the message names every problem."""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _tokens(text: str) -> int:
    return int(len(text.encode("utf-8")) / BYTES_PER_TOKEN)


def _read_json(p: Path) -> dict | list:
    return json.loads(Path(p).read_text(encoding="utf-8"))


def _write_json(p: Path, d) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_name(p.name + ".tmp")
    tmp.write_text(json.dumps(d, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    tmp.replace(p)


# --- the detector over blocks -----------------------------------------------------------------------------------

def own_tail(blocks: list[Block]) -> tuple[int, int] | None:
    """(start, end) of the act's own provisions tail on a lex.bg page: from its first provisions heading to the first
    provisions heading of a later amending act (a „КЪМ …“ line in it or right after it), to the first annex, or to the
    end. None without a heading."""
    heads = [b.i for b in blocks if PROVISIONS.match(b.text)]
    start = next((i for i in heads if not _is_amending_tail(blocks, i)), None)
    if start is None:
        return None
    end = next((i for i in heads if i > start and _is_amending_tail(blocks, i)), len(blocks))
    annex = next((b.i for b in blocks[start:end] if ANNEX.match(b.text)), None)
    return start, (annex if annex is not None else end)


def material_tail(blocks: list[Block]) -> tuple[int, int] | None:
    """(start, end) of the act's own provisions tail in a Gazette material: the first provisions heading after the act's own
    title line (a decree that adopts a regulation prints its own final provisions before the regulation's title and
    articles), to the first annex or the end; without a title line, the first provisions heading after the last article.
    None without a heading."""
    base = max((b.i for b in blocks if KIND_TITLE.match(b.text)), default=-1)   # the act's own title line: the last one, since a
    first_annex = next((b.i for b in blocks if b.i > base and ANNEX.match(b.text)), len(blocks))   # decree prints its own text and annex first
    if base >= 0:   # the act's own title line: its provisions follow it, or there are none
        start = next((b.i for b in blocks[:first_annex] if b.i > base and PROVISIONS.match(b.text)), None)
    else:   # no title line of its own: the first provisions heading after the last article; a „Чл.“ line that
        last_article = -1   # follows a § under a provisions heading is quoted by that § and is no article
        under_sign = False
        for b in blocks[:first_annex]:
            if PROVISIONS.match(b.text) or CHAPTER.match(b.text) or KIND_TITLE.match(b.text):
                under_sign = False
            elif SIGN.match(b.text) or b.text.startswith("Параграф единствен"):
                under_sign = True
            elif ARTICLE.match(b.text) and not under_sign:
                last_article = b.i
        start = next((b.i for b in blocks[:first_annex] if b.i > last_article and PROVISIONS.match(b.text)), None)
    if start is None:
        return None
    annex = next((b.i for b in blocks[start:] if ANNEX.match(b.text)), None)
    return start, (annex if annex is not None else len(blocks))


def _is_amending_tail(blocks: list[Block], i: int) -> bool:
    """A provisions heading of a later amending act: a „КЪМ …“ line in it, or before or after it through lex.bg's qualifier
    lines and the repeated copies of the heading (decision D-072, ruling 1)."""
    if re.search(r"\sКЪМ\s", blocks[i].text):
        return True
    for step in (1, -1):   # lex.bg prints: heading, „КЪМ …“, „(ОБН. …)“, the heading again; never another act's heading between
        j = i + step
        while 0 <= j < len(blocks) and QUALIFIER.match(blocks[j].text):
            if KYM.match(blocks[j].text):
                return True
            j += step
    return False


def own_scope(blocks: list[Block]) -> tuple[int, int] | None:
    """What the rules read when the page has no own provisions tail: the blocks before the first amending act's tail (its
    heading or its „КЪМ“ line); None when nothing of the act's own precedes it, so the page makes no candidate."""
    first_amending = next((b.i for b in blocks if KYM.match(b.text) or (PROVISIONS.match(b.text) and _is_amending_tail(blocks, b.i))), len(blocks))
    return (0, first_amending) if first_amending > 0 else None


def scan_blocks(blocks: list[Block]) -> list[dict]:
    """The two rules of FR-042 over the act's own provisions tail (over the whole page when it has no provisions heading):
    every finding, or none. A finding outside the own tail (an amending act's empty heading further down the page) is
    returned with ``outside_own_tail`` set and makes no candidate: the investigator reads the own tail against the act's
    promulgation material, which cannot hold a later amending act's provisions."""
    out: list[dict] = []
    tail = own_tail(blocks) or own_scope(blocks)
    if tail is None:
        return []   # every heading on the page is a later amending act's: nothing of the act's own provisions to read
    scope = blocks[tail[0]:tail[1]]
    for i, b in enumerate(blocks):
        if not ADDITIONAL.match(b.text):
            continue
        j = i + 1
        while j < len(blocks) and (QUALIFIER.match(blocks[j].text) or ADDITIONAL.match(blocks[j].text)):
            j += 1
        if j < len(blocks) and FINAL.match(blocks[j].text):
            inside = tail[0] <= i < tail[1] and j < tail[1]   # both headings the act's own: a later amending act's heading closes nothing of its own
            out.append({"rule": "additional-empty", "block": i, "detail": f"block {i} '{b.text[:60]}' is followed by '{blocks[j].text[:60]}' at block {j}"
                        + ("" if inside else f" (outside the act's own provisions, blocks {tail[0]} to {tail[1] - 1}: a later amending act's)"),
                        **({} if inside else {"outside_own_tail": True})})
            if inside:
                break   # one finding per act: the rule lists acts to adjudicate, not every empty section
    numbers = [(int(m.group(1)), b.i) for b in scope if (m := SIGN.match(b.text))]
    if numbers:
        low, at = min(numbers)
        if low > 1:
            where = (f"in the act's own provisions (blocks {tail[0]} to {tail[1] - 1})" if own_tail(blocks)
                     else f"on the page before its first amending act's tail (blocks {tail[0]} to {tail[1] - 1}), which has no provisions heading of its own")
            out.append({"rule": "paragraph-start-above-1", "block": at, "detail": f"lowest § is {low} (block {at}) {where}"})
    return out


def scan_page(raw: bytes) -> tuple[list[dict], dict]:
    """The findings of one raw page and what the investigator needs of it: the own tail and its lowest §."""
    act = split_lexbg(raw)
    if not act.has_spine:
        return [], {"has_spine": False}
    findings = scan_blocks(act.blocks)
    tail = own_tail(act.blocks) or own_scope(act.blocks)
    facts = {"has_spine": True, "blocks": len(act.blocks), "own_tail": None}
    if tail:
        nums = [int(m.group(1)) for b in act.blocks[tail[0]:tail[1]] if (m := SIGN.match(b.text))]
        facts["own_tail"] = {"start": tail[0], "end": tail[1], "lowest_sign": min(nums) if nums else None}
    return findings, facts


def scan(root: Path = ROOT, run_root: Path | None = None, manifest: Path | None = None, raw_dir: Path | None = None) -> list[dict]:
    """Every raw page of the store through the two rules; ``candidates.json`` in the run folder; the candidates."""
    raw_dir = Path(raw_dir or Path(root) / RAW_LEXBG)
    manifest = Path(manifest or raw_dir / "manifest.jsonl")
    run_root = Path(run_root or Path(root) / "data" / "runs" / RUN_NAME)
    rows = [json.loads(l) for l in manifest.read_text(encoding="utf-8").splitlines() if l.strip()]
    latest: dict[str, dict] = {}
    for r in rows:
        if r.get("status") == "ok":
            latest[str(r["doc_id"])] = r
    pages = no_act = 0
    out: list[dict] = []
    for doc_id, r in sorted(latest.items(), key=lambda kv: kv[1]["slug"]):
        page = raw_dir / f"{doc_id}.html"
        if not page.exists():
            continue
        raw = page.read_bytes()
        pages += 1
        findings, facts = scan_page(raw)
        if not facts["has_spine"]:
            no_act += 1
            continue
        inside = [f for f in findings if not f.get("outside_own_tail")]
        if inside:
            out.append({"slug": r["slug"], "doc_id": doc_id, "category": r["category"], "page_sha256": _sha(raw),
                        "rules": sorted({f["rule"] for f in inside}), "findings": findings, "own_tail": facts["own_tail"], "blocks": facts["blocks"]})
    by_rule = {rule: sum(1 for c in out if rule in c["rules"]) for rule in RULES}
    doc = {"run": run_root.name, "scanned_at": _now(), "pages": pages, "pages_without_act": no_act, "candidates": len(out), "by_rule": by_rule,
           "rules": list(RULES), "entries": out}
    _write_json(run_root / "candidates.json", doc)
    return out


def load_candidates(run_root: Path) -> list[dict]:
    doc = _read_json(run_root / "candidates.json")
    return doc["entries"]


# --- the promulgation material ------------------------------------------------------------------------------------

def _norm_title(s: str) -> str:
    return re.sub(r"\s+", " ", _WORD.sub(" ", s.lower().replace("ѝ", "и"))).strip()


def _number_key(title: str) -> tuple[str, str, str] | None:
    """("наредба", "н-4", "2026") of a title "НАРЕДБА № Н-4 от 30 март 2026 г. …", read before the punctuation goes, or None."""
    m = _NUMBER_KEY.match(re.sub(r"\s+", " ", title.strip()))
    return (m.group(1).lower(), m.group(2).lower(), m.group(3)) if m else None


def _words(norm_title: str) -> frozenset[str]:
    return frozenset(w for w in norm_title.split() if len(w) >= 4 and w not in STOP_WORDS and not w.isdigit())


def _frontmatter(root: Path, slug: str) -> dict:
    p = sx.corpus_file(root, slug)
    if p is None:
        raise DefectsError(f"{slug}: no corpus file")
    text = p.read_text(encoding="utf-8")
    return yaml.safe_load(text.split("---\n", 2)[1]) or {}


def attribute(slug: str, root: Path = ROOT, summary: Path | None = None, index_rows: list[dict] | None = None) -> dict:
    """The act's promulgation material: the coverage map's attribution, else one title hit in the cited issue, else none."""
    summary = Path(summary or Path(root) / SUMMARY)
    row = next((r for r in csv.DictReader(summary.open(encoding="utf-8")) if r["law_id"] == slug), None)
    base = (row or {}).get("base_source", "no-row")
    dv_id = (row or {}).get("dv_identifier", "")
    if dv_id.startswith("dv-") and dv_id[3:].isdigit():
        return {"id_mat": int(dv_id[3:]), "how": "coverage_map", "base_source": base}
    fm = _frontmatter(root, slug)
    issue, year = str(fm.get("dv_issue") or "").strip(), fm.get("dv_year")
    if not issue.isdigit() or not year:
        return {"id_mat": None, "how": None, "base_source": base, "reason": "the act cites no promulgation issue"}
    if index_rows is None:
        index_rows = [json.loads(l) for l in (Path(root) / DV_INDEX).read_text(encoding="utf-8").splitlines() if l.strip()]
    in_issue = [r for r in index_rows if r.get("status") == "ok" and r.get("issue_year") == int(year) and r.get("issue_number") == int(issue)]
    title = _norm_title(str(fm.get("titulo") or ""))
    hits = [r for r in in_issue if _norm_title(r.get("title") or "") == title]
    if not hits:
        hits = [r for r in in_issue if title and _norm_title(r.get("title") or "").startswith(title)]
    if not hits:   # a regulation adopted by a decree is listed under the decree's title, "Постановление № … за приемане на Устройствен правилник …"
        hits = [r for r in in_issue if title and title in _norm_title(r.get("title") or "")]
    how = "index_title"
    if not hits:   # the Gazette lists the act's original title, lex.bg its current one: the act's number and year, then its distinctive words
        key = _number_key(str(fm.get("titulo") or ""))
        if key:
            hits = [r for r in in_issue if _number_key(r.get("title") or "") == key]
            how = "index_number"
    if not hits:
        words = _words(title)
        scored = [(len(words & _words(_norm_title(r.get("title") or ""))) / len(words), r) for r in in_issue if words]
        hits = [r for score, r in scored if score >= WORD_SHARE]
        how = "index_words"
    if len(hits) == 1:
        return {"id_mat": hits[0]["id_mat"], "how": how, "base_source": base, "issue": f"{issue}/{year}"}
    if not in_issue:
        return {"id_mat": None, "how": None, "base_source": base, "reason": f"the index holds no HTML material of бр. {issue}/{year}" +
                (" (PDF era)" if int(year) < 2003 else "")}
    return {"id_mat": None, "how": None, "base_source": base,
            "reason": f"{len(hits)} title hits among {len(in_issue)} materials of бр. {issue}/{year}" + (": " + "; ".join(str(h["id_mat"]) for h in hits[:5]) if hits else "")}


def fetch(run_root: Path, root: Path = ROOT, fetch_one=None, cache_dir: Path | None = None, summary: Path | None = None,
          index_rows: list[dict] | None = None) -> dict:
    """Each candidate's material into the Gazette cache and ``materials.json``; a material already recorded is not asked for again."""
    cache_dir = Path(cache_dir or Path(root) / DV_CACHE)
    path = run_root / "materials.json"
    recorded = _read_json(path) if path.exists() else {}
    if fetch_one is None:
        from fetcher.dv.client import DvSession
        from fetcher.dv.materials import fetch_material, is_dv_error_body
        session = DvSession()

        def fetch_one(id_mat: int) -> str | None:   # noqa: E306
            html = fetch_material(session, id_mat, cache_dir=cache_dir)
            return None if is_dv_error_body(html) else html
    for c in load_candidates(run_root):
        slug = c["slug"]
        if slug in recorded and recorded[slug].get("outcome") == "ok":
            continue
        a = attribute(slug, root, summary, index_rows)
        rec = {"slug": slug, **a, "fetched_at": _now()}
        if a["id_mat"] is None:
            rec["outcome"] = "not_retrieved"
        else:
            cached = (cache_dir / f"{a['id_mat']}.html").exists()
            html = fetch_one(a["id_mat"])
            if html is None:
                rec["outcome"] = "error"
                rec["reason"] = f"the Gazette answers its error view for material {a['id_mat']}"
            else:
                on_disk = (cache_dir / f"{a['id_mat']}.html").read_bytes()
                rec["outcome"] = "ok"
                rec["cached"] = cached
                rec["sha256"] = _sha(on_disk)   # the file as the cache holds it, which is what tasks reads
                rec["bytes"] = len(on_disk)
                try:
                    from fetcher.dv.materials import parse_material_header
                    head = parse_material_header(html)
                    rec["issue"] = f"{head.issue_number}/{head.issue_date[:4]}"
                    rec["body_org"] = head.body_org
                except Exception as exc:  # the header is a convenience; the hash is the record
                    rec["header"] = f"unread: {exc}"
        recorded[slug] = rec
        _write_json(path, recorded)
    return recorded


# --- the tails and the calls ---------------------------------------------------------------------------------------

def tail_text(blocks: list[Block], span: tuple[int, int] | None, context: int = CONTEXT_BLOCKS) -> tuple[str, str]:
    """(text, note) of a provisions tail with its context before; the last blocks of the act when it has no heading."""
    if span is None:
        n = min(len(blocks), 60)
        return "\n".join(b.text for b in blocks[-n:]), f"no provisions heading found: the last {n} of {len(blocks)} blocks"
    start, end = span
    lo = max(0, start - context)
    return "\n".join(b.text for b in blocks[lo:end]), f"blocks {lo} to {end - 1} of {len(blocks)} (the act's own provisions from block {start})"


def texts_for(c: dict, material_html: str | None, raw: bytes, whole: bool = False) -> dict:
    """The two texts of a candidate (tails, or whole), with their notes and sizes."""
    lex = split_lexbg(raw)
    if whole:
        lt, ln = lex.source_text, f"the whole lex.bg text, {len(lex.blocks)} blocks"
    else:
        lt, ln = tail_text(lex.blocks, own_tail(lex.blocks))
    out = {"lexbg": {"text": lt, "note": ln, "tokens": _tokens(lt)}}
    if material_html is not None:
        dv = split_dv(material_html)
        if whole:
            dt, dn = dv.source_text, f"the whole material, {len(dv.blocks)} blocks"
        else:
            dt, dn = tail_text(dv.blocks, material_tail(dv.blocks))
        out["dv"] = {"text": dt, "note": dn, "tokens": _tokens(dt)}
    return out


INSTRUCTIONS = """# Investigate what lex.bg gets wrong: {n} candidate act(s)

You investigate acts of the legalize-bg corpus whose text lex.bg may hold wrong. The detector of FR-042 flagged each act
below because lex.bg prints an additional-provisions heading with nothing under it, or because the lowest § number of
its page is above 1. For each candidate you get two texts: the act's own provisions (additional, transitional and final)
as lex.bg prints them today, with a few blocks before them, and the same part of the act as the Държавен вестник
promulgated it (the promulgation material; where the acts were later amended, lex.bg's text is the consolidated one and
the Gazette's is the original, so an amendment lex.bg marks, such as „(Изм. - ДВ, бр. …)“, is not an error).

Decide from the texts alone, for each candidate, one verdict from this closed set:
{verdicts}

For a `confirmed` verdict also give the `kind` of lex.bg's error, from this closed set:
{kinds}

Rules: read only this file and write only the answer file. Never rewrite, correct or quote the act's text beyond the
evidence note. A difference that is an amendment lex.bg marks is not an error. Where lex.bg prints the heading twice
(an old and a new title), that alone is not an error. Where the §§ of an ordinance belong to the decree or order that
adopted it and the Gazette shows the same, the verdict is `not_a_defect`. Where lex.bg marks the empty heading as added
by a later amendment („Нова - ДВ, бр. …“), the promulgation text cannot hold it: the verdict is `unverified` naming the
issue, unless the Gazette text given is that amending material, in which case the kind is `dropped_section` as for a
promulgated section. Where the Gazette's text given here does not hold the act's provisions at all, the verdict is
`unverified`, and where the whole texts would settle it, `needs_whole_text`.

Write exactly one JSON object to `{answer}`: one key per candidate slug, exactly the {n} slugs below, each value an
object `{{"verdict": "<one of the four>", "kind": "<one of the five, only with confirmed, else null>",
"gazette": "<for confirmed: a noun phrase, not a sentence: what the Gazette carries that lex.bg lacks or prints wrong, with the § or article numbers>",
"note": "<short evidence note naming the lines you relied on>"}}`. Nothing else: no prose, no code fence.
"""


def _call_id(slugs: list[str], stage: str, materials: dict[str, int] | None = None) -> str:
    key = "\n".join(f"{s}:{(materials or {}).get(s, '')}" for s in sorted(slugs)) + stage
    return "call-" + stage + "-" + _sha(key.encode())[:8]


def write_call(run_root: Path, slugs: list[str], stage: str, texts: dict[str, dict], candidates: dict[str, dict]) -> dict:
    materials = {s: texts[s]["id_mat"] for s in slugs}
    cid = _call_id(slugs, stage, materials)
    calls = run_root / "calls"
    call_path, answer_path = calls / f"{cid}.md", calls / f"{cid}.answer.json"
    parts = [INSTRUCTIONS.format(n=len(slugs), answer=answer_path, verdicts="\n".join(f"- `{k}`: {v}" for k, v in VERDICTS.items()),
                                 kinds="\n".join(f"- `{k}`: {v}" for k, v in KINDS.items()))]
    for k, slug in enumerate(slugs, 1):
        c, t = candidates[slug], texts[slug]
        parts.append(f"\n## Candidate {k}: `{slug}`\n\nFlagged by: {', '.join(c['rules'])} ({'; '.join(f['detail'] for f in c['findings'])}).\n")
        parts.append(f"### lex.bg text of `{slug}` ({t['lexbg']['note']})\n\n{t['lexbg']['text']}\n")
        parts.append(f"### Gazette text of `{slug}` (material {t['id_mat']}, {t['dv']['note']})\n\n{t['dv']['text']}\n")
    calls.mkdir(parents=True, exist_ok=True)
    call_path.write_text("\n".join(parts), encoding="utf-8")
    tokens = sum(texts[s]["lexbg"]["tokens"] + texts[s]["dv"]["tokens"] for s in slugs)
    rec = {"call": cid, "stage": stage, "slugs": slugs, "materials": materials, "call_file": str(call_path), "answer_file": str(answer_path),
           "content_tokens": tokens, "written_at": _now()}
    _write_json(calls / f"{cid}.json", rec)
    return rec


def verdict_path(run_root: Path, slug: str) -> Path:
    return run_root / "verdicts" / f"{slug}.json"


def final_verdict(run_root: Path, slug: str) -> dict | None:
    """The candidate's verdict when it is final (not ``needs_whole_text`` at the tails stage)."""
    p = verdict_path(run_root, slug)
    if not p.exists():
        return None
    v = _read_json(p)
    return None if v["verdict"] == "needs_whole_text" else v


def tasks(run_root: Path, root: Path = ROOT, stage: str = "tails", raw_dir: Path | None = None, cache_dir: Path | None = None,
          per: int = PER_CALL, cap: int = CAP_TOKENS) -> tuple[list[dict], list[dict]]:
    """The calls to make for the candidates without a final verdict: (calls written, candidates settled by the script).

    ``tails``: every candidate with a material and no verdict yet; ``whole``: every candidate whose tails verdict says
    ``needs_whole_text``, one per call. A candidate without a material gets its ``unverified`` verdict here, by the script.
    """
    raw_dir, cache_dir = Path(raw_dir or Path(root) / RAW_LEXBG), Path(cache_dir or Path(root) / DV_CACHE)
    if stage not in ("tails", "whole"):
        raise DefectsError(f"stage {stage!r} is not tails or whole")
    cands = {c["slug"]: c for c in load_candidates(run_root)}
    mats = _read_json(run_root / "materials.json") if (run_root / "materials.json").exists() else {}
    settled: list[dict] = []
    todo: list[str] = []
    texts: dict[str, dict] = {}
    for slug, c in cands.items():
        existing = verdict_path(run_root, slug)
        v = _read_json(existing) if existing.exists() else None
        m = mats.get(slug)
        have_material = m is not None and m.get("outcome") == "ok"
        if stage == "tails" and v is not None and not (v.get("stage") == "script" and v.get("material") is None and have_material):
            continue   # settled; a script verdict for a material not retrieved then is re-tasked once the material is there
        if stage == "whole" and (v is None or v["verdict"] != "needs_whole_text" or v.get("stage") != "tails"):
            continue
        if stage == "whole" and _later_calls(run_root, slug):
            continue   # an amendment call is out for it: one such call, never a second
        if not have_material:
            reason = (m or {}).get("reason") or "the material is not recorded: run fetch first"
            rec = {"slug": slug, "verdict": "unverified", "kind": None, "gazette": None, "stage": "script",
                   "note": f"the promulgation material was not retrieved: {reason}", "material": None, "call": None, "answered_at": _now(),
                   **({"tails_note": v["note"]} if v and v.get("stage") == "tails" else {})}
            _write_json(existing, rec)
            settled.append(rec)
            continue
        on_disk = (cache_dir / f"{m['id_mat']}.html").read_bytes()
        if _sha(on_disk) != m["sha256"]:
            raise DefectsError(f"{slug}: the cached material {m['id_mat']} no longer hashes as materials.json recorded it")
        raw = (raw_dir / f"{c['doc_id']}.html").read_bytes()
        if _sha(raw) != c["page_sha256"]:
            raise DefectsError(f"{slug}: the raw page {c['doc_id']} no longer hashes as candidates.json recorded it; scan again")
        t = texts_for(c, on_disk.decode("utf-8"), raw, whole=(stage == "whole"))
        t["id_mat"] = m["id_mat"]
        if stage == "whole" and t["lexbg"]["tokens"] + t["dv"]["tokens"] > MOST_WHOLE_TOKENS:
            rec = {"slug": slug, "verdict": "unverified", "kind": None, "gazette": None, "stage": "script", "material": m["id_mat"], "call": None,
                   "note": f"the whole texts are {t['lexbg']['tokens'] + t['dv']['tokens']} estimated tokens, beyond one call's range; "
                           f"the tails did not settle it: {v['note']}", "answered_at": _now()}
            _write_json(existing, rec)
            settled.append(rec)
            continue
        texts[slug] = t
        todo.append(slug)
    tdir = run_root / "texts"
    tdir.mkdir(parents=True, exist_ok=True)
    for slug in todo:
        for side in ("lexbg", "dv"):
            (tdir / f"{slug}.{stage}.{side}.txt").write_text(texts[slug][side]["text"] + "\n", encoding="utf-8")
    calls: list[dict] = []
    if stage == "whole":
        groups = [[s] for s in todo]
    else:
        groups, cur, size = [], [], 0
        for slug in sorted(todo, key=lambda s: texts[s]["lexbg"]["tokens"] + texts[s]["dv"]["tokens"]):
            n = texts[slug]["lexbg"]["tokens"] + texts[slug]["dv"]["tokens"]
            if cur and (len(cur) >= per or size + n > cap):
                groups.append(cur)
                cur, size = [], 0
            cur.append(slug)
            size += n
        if cur:
            groups.append(cur)
    existing_calls = {p.stem for p in (run_root / "calls").glob("call-*.md")} if (run_root / "calls").exists() else set()
    for g in groups:
        cid = _call_id(g, stage, {s: texts[s]["id_mat"] for s in g})
        if cid in existing_calls and (run_root / "calls" / f"{cid}.answer.json").exists():
            continue   # answered, not yet collected: collect first
        calls.append(write_call(run_root, g, stage, texts, cands))
    return calls, settled


def _later_calls(run_root: Path, slug: str) -> list[str]:
    """The whole-text or amendment calls that hold the act, collected or not."""
    if not (run_root / "calls").exists():
        return []
    out = []
    for p in sorted((run_root / "calls").glob("call-*.json")):
        if p.name.endswith(".answer.json"):
            continue
        rec = _read_json(p)
        if rec.get("stage") in ("whole", "amendment") and slug in rec.get("slugs", []):
            out.append(rec["call"])
    return out


def amendment_call(run_root: Path, slug: str, id_mat: int, root: Path = ROOT, raw_dir: Path | None = None, cache_dir: Path | None = None,
                   fetch_one=None) -> dict:
    """One call for an act whose flagged section a later amendment added (lex.bg marks the heading „Нова - ДВ, бр. …“): the lex.bg
    tail against the whole text of that amending material, which the promulgation material cannot show. Bounded to one call."""
    raw_dir, cache_dir = Path(raw_dir or Path(root) / RAW_LEXBG), Path(cache_dir or Path(root) / DV_CACHE)
    cands = {c["slug"]: c for c in load_candidates(run_root)}
    if slug not in cands:
        raise DefectsError(f"{slug}: not a candidate of this run")
    c = cands[slug]
    vp = verdict_path(run_root, slug)
    v = _read_json(vp) if vp.exists() else None
    if v is None or v.get("stage") != "tails" or v["verdict"] not in ("needs_whole_text", "unverified"):
        raise DefectsError(f"{slug}: an amendment call follows a tails verdict of needs_whole_text or unverified, not {v and v['verdict']!r} at stage {v and v.get('stage')!r}")
    later = _later_calls(run_root, slug)
    if later:
        raise DefectsError(f"{slug}: a whole-text or amendment call exists already ({', '.join(later)}); one such call, never a second")
    if fetch_one is None:
        from fetcher.dv.client import DvSession
        from fetcher.dv.materials import fetch_material, is_dv_error_body
        session = DvSession()
        fetch_one = lambda i: (lambda h: None if is_dv_error_body(h) else h)(fetch_material(session, i, cache_dir=cache_dir))   # noqa: E731
    if fetch_one(id_mat) is None:
        raise DefectsError(f"{slug}: the Gazette answers its error view for material {id_mat}")
    html = (cache_dir / f"{id_mat}.html").read_bytes()
    raw = (raw_dir / f"{c['doc_id']}.html").read_bytes()
    if _sha(raw) != c["page_sha256"]:
        raise DefectsError(f"{slug}: the raw page {c['doc_id']} no longer hashes as candidates.json recorded it; scan again")
    lex = split_lexbg(raw)
    lt, ln = tail_text(lex.blocks, own_tail(lex.blocks))
    dv = split_dv(html.decode("utf-8"))
    t = {"lexbg": {"text": lt, "note": ln, "tokens": _tokens(lt)},
         "dv": {"text": dv.source_text, "note": f"the whole amending material {id_mat}, {len(dv.blocks)} blocks, sha256 {_sha(html)[:12]}", "tokens": _tokens(dv.source_text)},
         "id_mat": id_mat}
    if t["lexbg"]["tokens"] + t["dv"]["tokens"] > MOST_WHOLE_TOKENS:
        raise DefectsError(f"{slug}: the texts are {t['lexbg']['tokens'] + t['dv']['tokens']} estimated tokens, beyond one call's range ({MOST_WHOLE_TOKENS})")
    (run_root / "texts").mkdir(parents=True, exist_ok=True)
    for side in ("lexbg", "dv"):
        (run_root / "texts" / f"{slug}.amendment.{side}.txt").write_text(t[side]["text"] + "\n", encoding="utf-8")
    return write_call(run_root, [slug], "amendment", {slug: t}, cands)


def collect(run_root: Path) -> tuple[list[dict], list[str]]:
    """Every answer file against its call and the closed sets; one verdict file per candidate; (verdicts written, problems)."""
    written: list[dict] = []
    problems: list[str] = []
    calls = run_root / "calls"
    for rec_path in sorted(calls.glob("call-*.json")) if calls.exists() else []:
        if rec_path.name.endswith(".answer.json"):
            continue
        rec = _read_json(rec_path)
        answer_path = Path(rec["answer_file"])
        if not answer_path.exists() or rec.get("collected_at"):
            continue   # a call is collected once: a later stage's verdict is never written over by the earlier answer
        answer_sha = _sha(answer_path.read_bytes())
        if rec.get("refused_at") and rec.get("refused_sha256") == answer_sha:
            continue   # refused already, and the answer has not changed since
        try:
            got = json.loads(answer_path.read_text(encoding="utf-8"))
            errs = answer_problems(got, rec["slugs"])
        except json.JSONDecodeError as exc:
            got, errs = None, [f"the answer is not JSON: {exc}"]
        for slug in rec["slugs"] if got is not None else []:
            p = verdict_path(run_root, slug)
            prior = _read_json(p) if p.exists() else None
            if prior and prior.get("call") and prior.get("stage") == rec["stage"] and prior["call"] != rec["call"]:
                errs.append(f"{slug}: already answered by {prior['call']} at the {rec['stage']} stage; a verdict is never written over by another call")
            elif prior and prior.get("call") and rec["stage"] in ("whole", "amendment") and prior["stage"] in ("whole", "amendment") and prior["call"] != rec["call"]:
                errs.append(f"{slug}: already answered by {prior['call']} at the {prior['stage']} stage; one such call, never a second")
            elif prior and prior.get("call") and STAGE_RANK[rec["stage"]] < STAGE_RANK.get(prior.get("stage"), 0):
                errs.append(f"{slug}: answered at the {prior['stage']} stage already; a {rec['stage']} answer ranks below it and is not written over it")
        if errs:
            problems.append(f"{rec['call']}: " + "; ".join(errs))
            rec["refused_at"], rec["refused_sha256"], rec["refused_for"] = _now(), answer_sha, errs
            _write_json(rec_path, rec)   # retired until the answer changes; the problems stay on the record
            continue
        for slug in rec["slugs"]:
            a = got[slug]
            existing = verdict_path(run_root, slug)
            prior = _read_json(existing) if existing.exists() else None
            if prior and prior.get("call") == rec["call"]:
                continue   # already collected
            verdict, note = a["verdict"], a["note"]
            stage = rec["stage"]
            if stage in ("whole", "amendment") and verdict == "needs_whole_text":
                verdict, note = "unverified", f"the {stage} texts did not settle it either: " + note   # one such call, never a second
            promulgation = _material_of(run_root, slug)
            decided_on = rec.get("materials", {}).get(slug, promulgation)   # the amendment stage decides on the amending material
            out = {"slug": slug, "verdict": verdict, "kind": a.get("kind") if verdict == "confirmed" else None, "gazette": a.get("gazette") if verdict == "confirmed" else None,
                   "note": note, "stage": stage, "call": rec["call"], "material": decided_on, "promulgation_material": promulgation,
                   "call_content_tokens": rec.get("content_tokens"), "beyond_measured_range": bool(rec.get("content_tokens", 0) > CAP_TOKENS), "answered_at": _now()}
            if prior and prior.get("stage") == "tails" and stage in ("whole", "amendment"):
                out["tails_note"] = prior["note"]
            _write_json(existing, out)
            written.append(out)
        rec["collected_at"] = _now()
        _write_json(rec_path, rec)
    return written, problems


def _material_of(run_root: Path, slug: str) -> int | None:
    mats = _read_json(run_root / "materials.json") if (run_root / "materials.json").exists() else {}
    m = mats.get(slug) or {}
    return m.get("id_mat") if m.get("outcome") == "ok" else None


def answer_problems(got, slugs: list[str]) -> list[str]:
    """Every way an answer is outside its form; nothing of it is kept when one is found."""
    if not isinstance(got, dict):
        return ["not a JSON object keyed by slug"]
    errs: list[str] = []
    extra = sorted(set(got) - set(slugs))
    if extra:
        errs.append(f"slugs not in the call: {extra}")
    for slug in slugs:
        a = got.get(slug)
        if not isinstance(a, dict):
            errs.append(f"{slug}: no answer object")
            continue
        if a.get("verdict") not in VERDICTS:
            errs.append(f"{slug}: verdict {a.get('verdict')!r} is not one of {sorted(VERDICTS)}")
        if a.get("verdict") == "confirmed":
            if a.get("kind") not in KINDS:
                errs.append(f"{slug}: kind {a.get('kind')!r} is not one of {sorted(KINDS)}")
            if not isinstance(a.get("gazette"), str) or not a["gazette"].strip():
                errs.append(f"{slug}: a confirmed verdict names what the Gazette carries")
        elif a.get("kind") not in (None, ""):
            errs.append(f"{slug}: a kind is given with the verdict {a.get('verdict')!r}")
        if not isinstance(a.get("note"), str) or not a["note"].strip():
            errs.append(f"{slug}: the evidence note is missing")
        if set(a) - {"verdict", "kind", "gazette", "note"}:
            errs.append(f"{slug}: keys outside the form: {sorted(set(a) - {'verdict', 'kind', 'gazette', 'note'})}")
    return errs


def count(run_root: Path) -> dict:
    """The verdict files against the candidates: final verdicts, pending ones, missing ones, by verdict and by kind."""
    cands = [c["slug"] for c in load_candidates(run_root)]
    final, pending, missing = {}, [], []
    for slug in cands:
        p = verdict_path(run_root, slug)
        if not p.exists():
            missing.append(slug)
            continue
        v = _read_json(p)
        if v["verdict"] == "needs_whole_text":
            pending.append(slug)
        else:
            final[slug] = v
    by_verdict: dict[str, int] = {}
    by_kind: dict[str, int] = {}
    for v in final.values():
        by_verdict[v["verdict"]] = by_verdict.get(v["verdict"], 0) + 1
        if v["verdict"] == "confirmed":
            by_kind[v["kind"]] = by_kind.get(v["kind"], 0) + 1
    # a verdict file for an act the current scan does not list: a confirmed one stands (the investigator confirmed it against the
    # Gazette; a narrower rule cannot unsee it, as for an act whose whole own tail lex.bg drops), any other is withdrawn
    outside = sorted(p.stem for p in (run_root / "verdicts").glob("*.json") if p.stem not in cands) if (run_root / "verdicts").exists() else []
    kept = {s: _read_json(verdict_path(run_root, s)) for s in outside}
    kept = {s: v for s, v in kept.items() if v["verdict"] == "confirmed"}
    for v in kept.values():
        by_verdict["confirmed"] = by_verdict.get("confirmed", 0) + 1
        by_kind[v["kind"]] = by_kind.get(v["kind"], 0) + 1
    return {"candidates": len(cands), "final": len(final), "pending_whole_text": pending, "missing": missing, "by_verdict": by_verdict, "by_kind": by_kind,
            "stray_verdicts": [s for s in outside if s not in kept], "confirmed_outside_candidates": sorted(kept),
            "confirmed": sorted([s for s, v in final.items() if v["verdict"] == "confirmed"] + list(kept))}


def count_text(c: dict) -> str:
    lines = [f"verdicts: {c['final']} final of {c['candidates']} candidates; {len(c['pending_whole_text'])} waiting for a whole-text call; {len(c['missing'])} without a verdict file",
             "by verdict: " + (", ".join(f"{k} {v}" for k, v in sorted(c["by_verdict"].items())) or "none"),
             "by kind: " + (", ".join(f"{k} {v}" for k, v in sorted(c["by_kind"].items())) or "none")]
    if c["confirmed_outside_candidates"]:
        lines.append(f"confirmed by an earlier scan's candidate list, kept: {c['confirmed_outside_candidates']}")
    if c["stray_verdicts"]:
        lines.append(f"verdict files for no candidate, to withdraw: {c['stray_verdicts']}")
    return "\n".join(lines)


# --- the exceptions list ------------------------------------------------------------------------------------------

def route_for(fm: dict) -> str:
    """The act's route: whole from its promulgation material when never amended, else the history route of F1."""
    hist = fm.get("amendment_history") or []
    return "whole_act_from_material" if len(hist) <= 1 else "history"


def entries_for(run_root: Path, root: Path = ROOT, added: str | None = None) -> list[sx.Entry]:
    """One list entry per confirmed candidate, from its verdict and material; the register and the verdict are its evidence."""
    out: list[sx.Entry] = []
    root = Path(root)
    c = count(run_root)
    for slug in c["confirmed"]:
        v = _read_json(verdict_path(run_root, slug))
        fm = _frontmatter(root, slug)
        if v.get("material") is None:
            raise DefectsError(f"{slug}: a confirmed verdict without a material")
        rel = verdict_path(run_root, slug).resolve().relative_to(root.resolve())
        if v.get("stage") == "amendment" and not v.get("promulgation_material"):
            raise DefectsError(f"{slug}: an amendment-stage verdict without a promulgation material; the address is the promulgation material, where every route starts")
        promulgation = v.get("promulgation_material") or v["material"]   # the address: the promulgation material, where every route starts
        out.append(sx.Entry(slug=slug, title=str(fm.get("titulo") or slug).strip(), defect=v["kind"], source="dv_html", address=str(promulgation),
                            route=route_for(fm), state="listed", added=added or datetime.now(timezone.utc).date().isoformat(),
                            evidence=[{"kind": "register", "ref": f"{REGISTER}: {v['kind']}"}, {"kind": "audit", "ref": f"{rel}: {_sentence(v['note'])}"}],
                            note=f"S2 of the plan of 31 October 2026: {_material_words(v)} carries: {v['gazette']}"))
    return out


def _sentence(text: str) -> str:
    text = (text or "").strip()
    return text if not text or text[-1] in ".!?" else text + "."


def _material_words(v: dict) -> str:
    """Which Gazette text the verdict was decided against: the promulgation material, or the amending material that added the section."""
    if v.get("stage") == "amendment":
        return f"the Gazette's amending material {v['material']} (the promulgation material is {v.get('promulgation_material')})"
    return f"the Gazette's promulgation material {v['material']}"


def case_prose(v: dict, entry: sx.Entry, run: str) -> dict[str, str]:
    """The lessons and the proposal of a confirmed act's case file, from its verdict: the session's words, the owner reads them."""
    lessons = (f"The detector of FR-042 flagged the act and the investigator confirmed it against {_material_words(v)} "
               f"(S2 run {run}): {_sentence(v['note'])} The Gazette carries: {v['gazette']}. lex.bg's text, which the corpus holds, lacks it "
               f"(kind: {v['kind']}).")
    if v.get("in_force_from"):
        lessons += (f" The section enters into force on {v['in_force_from']}; the starting state carries it as the Gazette's consolidated text does, "
                    f"since the Gazette prevails (D-059, D-074): no text is dropped for not yet applying.")
    if entry.route == "history":
        proposal = ("The act was amended after its promulgation, so its promulgation material is not the whole act and the dropped text can be "
                    "filled only by rebuilding the act's history through the engine of F1. Leave the act on the list with the route \"history\" "
                    "until the engine exists; the corpus keeps lex.bg's text with the defect, and the act counts as distance left.")
    else:
        proposal = ("The act was never amended, so its promulgation material is the whole act: the route \"whole act from its promulgation "
                    "material\" reads it through the labeller and the write path, as the transport law was read. That reading is S5's batch "
                    "work under its own budget; until then the act counts as distance left.")
    return {"Lessons learnt": lessons, "Proposal": proposal}


def list_confirmed(run_root: Path, root: Path = ROOT, run: str | None = None, until: str | None = "amendment_search") -> list[dict]:
    """Every confirmed act onto the exceptions list through the route driver, then through its route: the history route stops
    at once with a case file (the engine of F1 is not built), whose prose is written from the verdict; the whole-act route
    is halted before its first step (``until``), since its reading is S5's batch work. Returns one record per act."""
    from reading import routes
    from reading.steps import STEPS
    root, run_root = Path(root), Path(run_root)
    run = run or run_root.name
    out: list[dict] = []
    for entry in entries_for(run_root, root):
        list_path = root / "docs" / "data" / "source-exceptions.yaml"
        have = sx.listed(entry.slug, list_path)
        if have is not None:   # listed already: its route and state stand; this run does not walk it again
            if have.note.startswith("S2 of the plan") and have.note != entry.note and not _ruled(root, have):
                sx.update(list_path, entry.slug, note=entry.note)   # this run's own wording follows the verdict, until the owner rules
            if have.state == "stopped" and have.case_file:
                _fill_case(root / have.case_file, run_root, entry, run)
            out.append({"slug": entry.slug, "route": have.route, "added": False, "state": have.state, "step": "-", "detail": "already listed",
                        **({"case_file": have.case_file} if have.case_file else {})})
            continue
        routes.add_entry(list_path, entry)
        ctx = routes.context(entry.slug, run, root=root)
        outcome = routes.run_route(ctx, STEPS, until=until)
        rec = {"slug": entry.slug, "route": ctx.entry.route, "added": True, "state": outcome.state, "step": outcome.step, "detail": outcome.detail}
        if outcome.state == "stopped" and outcome.case_file:
            _fill_case(root / outcome.case_file, run_root, entry, run)
            rec["case_file"] = outcome.case_file
        out.append(rec)
    return out


def _ruled(root: Path, entry: sx.Entry) -> bool:
    """Whether the owner has ruled on the entry's case file: then neither the file nor the list's note is this run's to change."""
    from reading import routes
    if not entry.case_file or not (root / entry.case_file).exists():
        return False
    _, prose = routes.split_case_file((root / entry.case_file).read_text(encoding="utf-8"))
    parts = re.split(r"^## .+$", prose or "", flags=re.M)[1:]
    return bool(parts) and parts[-1].strip() != routes.CASE_PLACEHOLDER["The owner's ruling"]


def _fill_case(case: Path, run_root: Path, entry: sx.Entry, run: str) -> None:
    """The lessons and the proposal from the verdict, written while the owner has not ruled; the owner's ruling is never touched."""
    from reading import routes
    fm, prose = routes.split_case_file(case.read_text(encoding="utf-8"))
    if fm is None or prose is None or fm.get("run") != run:
        return   # another run's stop, or a file the driver cannot parse: not this run's to write
    parts = re.split(r"^(## .+)$", prose, flags=re.M)   # ["", "## Lessons learnt", text, "## Proposal", text, "## The owner's ruling", text]
    heads = parts[1::2]
    texts = [t.strip() for t in parts[2::2]]
    if heads != [f"## {p}" for p in routes.CASE_PARTS]:
        raise DefectsError(f"{case}: the prose parts are {heads}, not the case file's three")
    if texts[2] != routes.CASE_PLACEHOLDER["The owner's ruling"]:
        return   # the owner has ruled: the file is the owner's now
    v = _read_json(verdict_path(run_root, entry.slug))
    new = case_prose(v, entry, run)
    texts[0], texts[1] = new["Lessons learnt"], new["Proposal"]
    out = "\n".join(f"{h}\n\n{t}\n" for h, t in zip(heads, texts))
    if out.strip() != prose.strip():
        routes._write_case(case, fm, out)
        _, written = routes.split_case_file(case.read_text(encoding="utf-8"))
        if written is None or not routes._written(written):
            raise DefectsError(f"{case}: the prose was not filled")


def token_report(run_root: Path, budget: int = 2_000_000) -> str:
    """The calls of the run from ``usage.jsonl`` (one line per call, written by the session from the harness's figures)."""
    path = run_root / "usage.jsonl"
    rows = [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()] if path.exists() else []
    by_kind: dict[str, dict] = {}
    for r in rows:
        k = by_kind.setdefault(r.get("kind", "investigator"), {"calls": 0, "tokens": 0, "content": 0, "candidates": 0, "ms": 0})
        k["calls"] += 1
        k["tokens"] += r["tokens"]
        k["content"] += r.get("content_tokens", 0)
        k["candidates"] += r.get("candidates", 0)
        k["ms"] += r.get("duration_ms", 0)
    total = sum(r["tokens"] for r in rows)
    lines = [f"token report of {run_root.name}: {len(rows)} calls, {total:,} tokens counted once (the harness's figure per call) against the budget of {budget:,}"]
    short = [r for r in rows if r.get("content_tokens", 0) > r["tokens"]]
    for kind, k in by_kind.items():
        lines.append(f"  {kind}: {k['calls']} calls, {k['tokens']:,} tokens, {k['content']:,} of content estimated" +
                     (f", {k['candidates']} candidates, {k['tokens'] / k['candidates']:,.0f} per candidate" if k["candidates"] else "") + f", {k['ms'] / 1000:,.0f} s")
    by_stage: dict[str, list[dict]] = {}
    for r in rows:
        if r.get("content_tokens") and r not in short:
            by_stage.setdefault(r["call"].split("-")[1] if r["call"].startswith("call-") else r.get("kind", "other"), []).append(r)
    for stage, rs in by_stage.items():
        fixed = sum(r["tokens"] - r["content_tokens"] for r in rs) / len(rs)
        lines.append(f"  {stage} calls: {len(rs)}, about {fixed:,.0f} per call beyond the content (fixed context and the answer)")
    if short:
        lines.append("  rows whose estimated content exceeds the harness's figure, so that figure may not count everything the call read: "
                     + ", ".join(f"{r['call']} ({r['content_tokens']:,} content, {r['tokens']:,} tokens)" for r in short))
    return "\n".join(lines)


# --- command line -------------------------------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--run", default=RUN_NAME, help="the run folder under data/runs")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("scan", help="the two rules over every raw page; candidates.json")
    sub.add_parser("fetch", help="each candidate's promulgation material into the Gazette cache; materials.json")
    t = sub.add_parser("tasks", help="the call files for the investigator")
    t.add_argument("--stage", default="tails", choices=("tails", "whole"))
    sub.add_parser("collect", help="the answers into one verdict file per candidate")
    sub.add_parser("count", help="the verdict files against the candidates")
    sub.add_parser("entries", help="print the list entries the confirmed verdicts give (the driver adds them: routes.py)")
    sub.add_parser("list", help="every confirmed act onto the exceptions list through the route driver and through its route")
    rp = sub.add_parser("report", help="the token report from usage.jsonl against the budget")
    am = sub.add_parser("amendment", help="one call: the lex.bg tail of an act against the whole text of the amending material that added its section")
    am.add_argument("slug"); am.add_argument("id_mat", type=int)
    rp.add_argument("--budget", type=int, default=2_000_000)
    args = ap.parse_args(argv)
    run_root = ROOT / "data" / "runs" / args.run
    if args.cmd == "scan":
        out = scan(ROOT, run_root)
        doc = _read_json(run_root / "candidates.json")
        print(f"{doc['pages']} pages scanned, {doc['pages_without_act']} without an act; {len(out)} candidates: " + ", ".join(f"{k} {v}" for k, v in doc["by_rule"].items()))
        return 0
    if args.cmd == "fetch":
        rec = fetch(run_root)
        by = {}
        for r in rec.values():
            by[r["outcome"]] = by.get(r["outcome"], 0) + 1
        how = {}
        for r in rec.values():
            how[r.get("how")] = how.get(r.get("how"), 0) + 1
        print(f"{len(rec)} candidates: " + ", ".join(f"{k} {v}" for k, v in sorted(by.items())) + "; attributed by " + ", ".join(f"{k} {v}" for k, v in how.items()))
        for r in rec.values():
            if r["outcome"] != "ok":
                print(f"  {r['slug']}: {r['outcome']}: {r.get('reason')}")
        return 0
    if args.cmd == "tasks":
        calls, settled = tasks(run_root, stage=args.stage)
        for s in settled:
            print(f"settled by the script: {s['slug']}: {s['verdict']}: {s['note']}")
        for c in calls:
            print(f"{c['call']} ({len(c['slugs'])} candidates, about {c['content_tokens']} content tokens): read {c['call_file']}, write {c['answer_file']}")
        print(f"{len(calls)} call(s) to make, {sum(len(c['slugs']) for c in calls)} candidates, about {sum(c['content_tokens'] for c in calls)} content tokens")
        return 0
    if args.cmd == "collect":
        written, problems = collect(run_root)
        for w in written:
            print(f"{w['slug']}: {w['verdict']}" + (f" ({w['kind']})" if w["kind"] else ""))
        for p in problems:
            print(f"refused  {p}")
        print(f"{len(written)} verdict(s) written, {len(problems)} answer(s) refused")
        return 1 if problems else 0
    if args.cmd == "count":
        c = count(run_root)
        print(count_text(c))
        return 0 if c["final"] == c["candidates"] else 1
    if args.cmd == "list":
        for r in list_confirmed(run_root):
            print(f"{r['slug']}: route {r['route']}, {'added' if r['added'] else 'already listed'}, {r['state']} at {r['step']}" + (f", case file {r['case_file']}" if r.get("case_file") else ""))
        print(sx.report())
        return 0
    if args.cmd == "report":
        print(token_report(run_root, args.budget))
        return 0
    if args.cmd == "amendment":
        c = amendment_call(run_root, args.slug, args.id_mat)
        print(f"{c['call']} (about {c['content_tokens']} content tokens): read {c['call_file']}, write {c['answer_file']}")
        return 0
    if args.cmd == "entries":
        for e in entries_for(run_root):
            print(yaml.safe_dump(e.to_dict(), allow_unicode=True, sort_keys=False, width=1000))
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
