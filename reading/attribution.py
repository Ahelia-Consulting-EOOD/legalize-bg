"""The attribution step: which act a Gazette material changes (step F1 of the plan of 31 October 2026, part 2).

A material names the act it changes in two places, both of a fixed form: its own title („Закон за изменение и
допълнение на Закона за частната охранителна дейност“) and, for an amendment carried inside another act's provisions,
the opening words of a § („§ 32. В Закона за данъците върху доходите на физическите лица (обн., ДВ, бр. 95 от 2006 г.; …)
се правят следните изменения“). The material parser (``reading/material.py``) extracts both with the cited history line,
whose first issue is the act's promulgation. This module resolves each cited title to a corpus act and records the
result as data: ``attribution.json`` per material, one row per target, every field from a closed set.

The resolution is mechanical, never a guess (the resolver's first rule, ``fetcher/dv/resolver.py``): the cited title
is normalised and looked up among the corpus titles; when the citation names the act's promulgation issue, the corpus
act must have been promulgated in that issue, which is what tells a predecessor of the same name from the act the
corpus holds (FR-043); a title that names several corpus acts and no promulgation is ``ambiguous``; a title that names
no corpus act is ``not_in_corpus`` (with the resolver's flags), and an act type outside the corpus (a тарифа, a
постановление) is ``not_in_corpus`` by its type. An ``ambiguous`` or ``predecessor_or_other`` row is a stop for the
engine, read by the owner, not a question for a model: the fixed form has no reading to make.

``measure`` runs the parser and the attribution over a set of cached materials with no model call and prints what the
plan asked for before the budget is stated: how many materials amend, how many targets resolve, and the tokens the
instruction step would read per material.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from fetcher.dv.resolver import (CORPUS_ACT_TYPES, CorpusAct, Resolver, act_type_of, clean_title, load_corpus_acts,  # noqa: E402
                                 normalise_title, strip_amending_prefix, title_variants)
from reading import material as M  # noqa: E402
from reading.splitter import split_dv  # noqa: E402

DV_CACHE = ROOT / "data" / "dv" / "cache"
DV_INDEX = ROOT / "data" / "dv" / "materials.jsonl"
STATUSES = ("attributed", "ambiguous", "not_in_corpus", "predecessor_or_other")
HOWS = ("title+promulgation", "title", "resolver", "type_outside_corpus", "amending_act", "none")
# the act-type word a citation opens with, before the resolver's normalisation strips a „за приемане на“ prefix (B2 of the review of 1 November 2026)
_HEAD_TYPES = {"закон": "закон", "закона": "закон", "законът": "закон", "кодекс": "кодекс", "кодекса": "кодекс", "кодексът": "кодекс",
               "наредба": "наредба", "наредбата": "наредба", "правилник": "правилник", "правилника": "правилник", "правилникът": "правилник",
               "устройствен": "правилник", "устройственият": "правилник", "устройствения": "правилник",
               "постановление": "постановление", "постановлението": "постановление", "тарифа": "тарифа", "тарифата": "тарифа",
               "инструкция": "инструкция", "инструкцията": "инструкция", "правила": "правила", "правилата": "правила", "указ": "указ", "указът": "указ", "указа": "указ",
               "решение": "решение", "решението": "решение", "методика": "методика", "методиката": "методика"}
# the full definite forms the resolver does not fold (B3): „Законът за …“, „Кодексът …“
_FULL_DEFINITE = {"законът": "закона", "кодексът": "кодекса", "правилникът": "правилника", "указът": "указа", "устройственият": "устройствения"}
_AMENDING_TITLE = re.compile(r"^(?:закон|кодекс|наредб|правилник|постановление)\S*\s+за\s+(?:изменение(?:\s+и\s+допълнение)?|допълнение)\s+на\s", re.I)
MATERIAL_STATUSES = ("amends_corpus_act", "amends_other_acts", "no_target", "not_amending", "parse_findings")


@dataclass
class Target:
    scope: str                 # "title" or the instruction id ("§32")
    cited_title: str
    cited_promulgation: list[int] | None   # [number, year]
    status: str
    how: str
    slug: str | None = None
    candidates: list[str] = field(default_factory=list)
    flags: list[str] = field(default_factory=list)
    repeal: bool = False
    note: str = ""
    act_promulgation: list[int] | None = None   # the corpus act's own promulgation [number, year], for the check


class Attributor:
    """Corpus acts in, targets out; built once per run."""

    def __init__(self, acts: list[CorpusAct]):
        self.acts = acts
        self.by_title: dict[str, list[CorpusAct]] = {}
        for a in acts:
            self.by_title.setdefault(normalise_title(a.title), []).append(a)
        self.resolver = Resolver(acts)
        self.by_id = {a.law_id: a for a in acts}

    @classmethod
    def from_root(cls, root: Path = ROOT) -> "Attributor":
        return cls(load_corpus_acts(root))

    def _exact(self, title: str) -> list[CorpusAct]:
        found: list[CorpusAct] = []
        seen: set[str] = set()
        for v in sorted(title_variants(normalise_title(title))):
            for a in self.by_title.get(v, ()):
                if a.law_id not in seen:
                    seen.add(a.law_id); found.append(a)
        return found

    def resolve(self, scope: str, title: str, promulgation: list[int] | None, repeal: bool = False) -> Target:
        title = clean_title(title)
        words = title.split()
        if words and words[0].lower() in _FULL_DEFINITE:
            title = _FULL_DEFINITE[words[0].lower()].capitalize() + title[len(words[0]):]
        prom = tuple(promulgation) if promulgation else None   # (number, year) as the Gazette writes it
        t = Target(scope=scope, cited_title=title, cited_promulgation=list(prom) if prom else None, status="not_in_corpus", how="none", repeal=repeal)
        head = _HEAD_TYPES.get(words[0].lower()) if words else None
        if head is None:
            head = act_type_of(title)
        if head is not None and head not in CORPUS_ACT_TYPES:
            t.how = "type_outside_corpus"; t.note = f"the cited act is a {head}, a type the corpus does not hold" + (f" (it names {strip_amending_prefix(title)!r})" if head == "постановление" else "")
            return t
        if _AMENDING_TITLE.match(title):
            t.how = "amending_act"; t.note = "the citation names an amending act's own provisions, which the corpus holds only as the amended act's text"
            return t
        cands = self._exact(title)
        t.candidates = [a.law_id for a in cands]
        if cands:
            if prom is not None:
                same = [a for a in cands if a.promulgation == (prom[1], prom[0])]
                blank = [a for a in cands if a.promulgation is None]
                if len(same) == 1:
                    t.status, t.how, t.slug = "attributed", "title+promulgation", same[0].law_id
                    t.act_promulgation = [same[0].promulgation[1], same[0].promulgation[0]]
                elif not same and len(blank) == 1 and len(cands) == 1:
                    t.status, t.how, t.slug = "attributed", "title", blank[0].law_id
                    t.flags = ["promulgation_unverified"]; t.note = "the corpus act cites no promulgation issue, so the cited one could not be checked"
                elif len(same) > 1:
                    t.status, t.how = "ambiguous", "title+promulgation"; t.note = "several corpus acts carry this title and this promulgation"
                else:
                    t.status, t.how = "predecessor_or_other", "title+promulgation"
                    t.note = ("the corpus holds " + ", ".join(f"{a.law_id} (promulgated {a.promulgation[1]}/{a.promulgation[0]})" if a.promulgation else a.law_id for a in cands)
                              + f"; the material cites бр. {prom[0]}/{prom[1]}")
            elif len(cands) == 1:
                t.status, t.how, t.slug = "attributed", "title", cands[0].law_id
                t.act_promulgation = [cands[0].promulgation[1], cands[0].promulgation[0]] if cands[0].promulgation else None
            else:
                t.status, t.how = "ambiguous", "title"; t.note = "several corpus acts carry this title and the material cites no promulgation"
            return t
        res = self.resolver.resolve(title, dv_citation=prom)
        t.candidates = list(res.candidates)
        t.flags = list(res.flags)
        t.how = "resolver"
        if res.law_id:
            act = self.by_id.get(res.law_id)
            if prom is not None and act is not None and act.promulgation is not None and act.promulgation != (prom[1], prom[0]):
                t.status = "predecessor_or_other"
                t.note = f"the resolver names {res.law_id} by {res.method}, promulgated {act.promulgation[1]}/{act.promulgation[0]}; the material cites бр. {prom[0]}/{prom[1]}"
            else:
                t.status, t.slug = "attributed", res.law_id
                t.act_promulgation = [act.promulgation[1], act.promulgation[0]] if act is not None and act.promulgation else None
                if prom is not None and t.act_promulgation is None:
                    t.flags.append("promulgation_unverified")
                t.note = f"by the resolver's {res.method} key" + (f" ({', '.join(t.flags)})" if t.flags else "")
        elif prom is not None:
            # the title scored under the resolver's floor, but one of the acts it considered was promulgated in the cited issue:
            # the issue identifies it (the check of the measurement found these misses, 1 November 2026)
            same = [self.by_id[c] for c in res.candidates if c in self.by_id and self.by_id[c].promulgation == (prom[1], prom[0])]
            if len(same) == 1:
                t.status, t.slug = "attributed", same[0].law_id
                t.act_promulgation = [prom[0], prom[1]]
                t.flags.append("candidate_by_promulgation")
                t.note = f"the title scored under the resolver's floor ({res.method}); the cited promulgation names the act"
            elif len(same) > 1 or "ambiguous_candidates" in res.flags:
                t.status = "ambiguous"
        elif "ambiguous_candidates" in res.flags:
            t.status = "ambiguous"
        return t

    def attribute(self, id_mat: int, mat: M.Material, index_row: dict | None = None, blocks=None) -> dict:
        targets: list[Target] = []
        if mat.target_title:
            targets.append(self.resolve("title", mat.target_title, mat.cited_history["promulgation"] if mat.cited_history else None,
                                        repeal=mat.instruction_kind == "repeal"))
        for node in mat.targets():
            targets.append(self.resolve(node.id, node.target["title"], node.target["promulgation"], repeal=node.target["repeal"]))
        hard = [f for f in mat.findings if f["kind"] != "quote_closed_by_sequence"] + M.sequence_problems(mat)
        ids = [n.id for n in mat.instructions()]
        if len(set(ids)) != len(ids):
            hard.append("duplicate instruction ids")
        if hard and (mat.amending or targets):
            status = "parse_findings"
        elif not mat.amending and not targets:
            status = "not_amending"
        elif not targets:
            status = "no_target"
        elif any(t.status == "attributed" for t in targets):
            status = "amends_corpus_act"
        else:
            status = "amends_other_acts"
        return {"material": id_mat, "title": (index_row or {}).get("title", mat.own_title), "issue": f"{index_row['issue_number']}/{index_row['issue_year']}" if index_row else None,
                "section": (index_row or {}).get("section"), "kind": mat.kind, "instruction_kind": mat.instruction_kind, "amending": mat.amending,
                "embedded": mat.embedded, "status": status, "targets": [asdict(t) for t in targets],
                "instructions": len(mat.instructions()), "signs": len(mat.nodes), "quoted_blocks": sum(len(n.quoted) for n in mat.instructions()),
                "findings": mat.findings + [{"block": -1, "kind": "sequence", "detail": p} for p in M.sequence_problems(mat)]
                + ([{"block": -1, "kind": "duplicate_id", "detail": "an instruction id occurs twice"}] if len(set(ids)) != len(ids) else []),
                "tokens_instructions": M.instruction_text_tokens(mat, blocks), "attributed_at": _now()}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def check(rec: dict, acts_by_id: dict | None = None) -> list[str]:
    """The fixed form: every status and how from its set, an attributed target names an act, a cited promulgation agrees with the act's,
    and a target not in the corpus has no candidate promulgated in the cited issue (``acts_by_id``, when given)."""
    out: list[str] = []
    for t in rec.get("targets", []):
        if acts_by_id and t.get("status") == "not_in_corpus" and t.get("cited_promulgation"):
            n, y = t["cited_promulgation"]
            hit = [c for c in t.get("candidates", []) if acts_by_id.get(c) is not None and acts_by_id[c].promulgation == (y, n)]
            if hit:
                out.append(f"material {rec['material']} {t.get('scope')}: not_in_corpus, yet {hit[0]} was promulgated in the cited бр. {n}/{y}")
    if rec.get("status") not in MATERIAL_STATUSES:
        out.append(f"material {rec.get('material')}: status {rec.get('status')!r} is not one of {MATERIAL_STATUSES}")
    for t in rec.get("targets", []):
        if t.get("status") not in STATUSES:
            out.append(f"material {rec['material']} {t.get('scope')}: status {t.get('status')!r}")
        if t.get("how") not in HOWS:
            out.append(f"material {rec['material']} {t.get('scope')}: how {t.get('how')!r}")
        if t.get("status") == "attributed" and not t.get("slug"):
            out.append(f"material {rec['material']} {t.get('scope')}: attributed without a slug")
        if t.get("status") != "attributed" and t.get("slug"):
            out.append(f"material {rec['material']} {t.get('scope')}: a slug on a target that is not attributed")
        if t.get("how") == "title+promulgation" and t.get("status") == "attributed" and t.get("act_promulgation") != t.get("cited_promulgation"):
            out.append(f"material {rec['material']} {t.get('scope')}: attributed by promulgation, but the act's {t.get('act_promulgation')} is not the cited {t.get('cited_promulgation')}")
    if rec.get("status") == "amends_corpus_act" and not any(t.get("status") == "attributed" for t in rec.get("targets", [])):
        out.append(f"material {rec['material']}: amends_corpus_act without an attributed target")
    return out


def index_rows(path: Path = DV_INDEX) -> dict[int, dict]:
    rows: dict[int, dict] = {}
    with Path(path).open(encoding="utf-8") as f:
        for line in f:
            if line.strip():
                r = json.loads(line)
                if r.get("id_mat") is not None:   # an issue with no HTML materials has a row without one
                    rows[r["id_mat"]] = r
    return rows


def attribute_cached(attr: Attributor, id_mat: int, cache_dir: Path = DV_CACHE, rows: dict[int, dict] | None = None) -> tuple[dict, M.Material]:
    html = (Path(cache_dir) / f"{id_mat}.html").read_text(encoding="utf-8")
    act = split_dv(html)
    mat = M.parse(act)
    return attr.attribute(id_mat, mat, (rows or {}).get(id_mat), act.blocks), mat


def measure(ids: list[int], out_dir: Path, attr: Attributor | None = None, cache_dir: Path = DV_CACHE) -> dict:
    """Parse and attribute every material; write one record each and a summary; no model call."""
    attr = attr or Attributor.from_root()
    rows = index_rows() if DV_INDEX.exists() else {}
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "materials").mkdir(exist_ok=True)
    recs: list[dict] = []
    problems: list[str] = []
    for id_mat in ids:
        rec, _ = attribute_cached(attr, id_mat, cache_dir, rows)
        (out_dir / "materials" / f"{id_mat}.json").write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")
        problems += check(rec, attr.by_id)
        recs.append(rec)
    by_status = Counter(r["status"] for r in recs)
    targets = [t for r in recs for t in r["targets"]]
    summary = {
        "materials": len(recs), "by_status": dict(by_status), "by_kind": dict(Counter(r["kind"] for r in recs)),
        "amending": sum(r["amending"] for r in recs), "targets": len(targets), "targets_by_status": dict(Counter(t["status"] for t in targets)),
        "targets_by_how": dict(Counter(t["how"] for t in targets)), "cross_act_targets": sum(1 for t in targets if t["scope"] != "title"),
        "cross_act_attributed": sum(1 for t in targets if t["scope"] != "title" and t["status"] == "attributed"),
        "parse_finding_kinds": dict(Counter(f["kind"] for r in recs for f in r["findings"])),
        "instructions_in_amending": sum(r["instructions"] for r in recs if r["amending"]),
        "tokens_instructions_in_amending": sum(r["tokens_instructions"] for r in recs if r["amending"]),
        "check_problems": problems, "measured_at": _now(),
    }
    (out_dir / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8")
    return summary


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    m = sub.add_parser("measure", help="parse and attribute cached materials; write records and a summary")
    m.add_argument("--ids", help="a JSON file with a list of material ids, or a catch-up manifest.json")
    m.add_argument("--out", required=True, help="the run folder under data/runs/")
    m.add_argument("id_mat", nargs="*", type=int)
    args = ap.parse_args(argv)
    ids = list(args.id_mat)
    if args.ids:
        loaded = json.loads(Path(args.ids).read_text(encoding="utf-8"))
        ids += [r["id_mat"] if isinstance(r, dict) else int(r) for r in loaded]
    summary = measure(ids, ROOT / "data" / "runs" / args.out)
    print(json.dumps(summary, ensure_ascii=False, indent=1))
    return 1 if summary["check_problems"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
