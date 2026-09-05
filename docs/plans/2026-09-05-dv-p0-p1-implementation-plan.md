# Graded Source Model P0/P1 Implementation Plan (coverage map completion, provenance block, pilot)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. Simpler tasks run on Opus 5 agents; design questions and final whole-branch review on the session model (owner instruction 2026-09-05).

**Goal:** Finish phase P0 of the graded source model (a coverage map whose chain check is a body scan of Gazette materials) and deliver phase P1 (the provenance block on every act, its exposure on every consumer surface, § addressing, the Gazette material parser, and the first grade A rebuild: Закон за обществения транспорт).

**Architecture:** Three new packages on top of what is merged: `fetcher/dv/` gains an instruction segmenter, a promulgated-act parser, a metadata builder and a `rebuild` command that writes only through the single corpus write gate into a staging area first; a `provenance/` package holds the data model and the total grade derivation of design 4.2 and is imported by the coverage map, the index builder and the C10 check; the index, MCP and REST surfaces gain the grade, the currency statement, one warning class and § addressing keyed by section context. Every corpus write goes through `corpus_gate.write_act` (PR #23 Part II Task 6). No corpus file is hand-edited.

**Tech Stack:** Python 3.12, pytest, requests, beautifulsoup4, lxml, PyYAML, SQLite; GitHub Actions. No new runtime dependency.

**Spec:** `docs/plans/2026-09-05-dv-graded-source-design.md` (sections 4, 5, 7, 8, 11) with `docs/process/COVERAGE-FLOOR.md` section Provenance floor as the canonical grade definitions and `docs/sync/DECISIONS.md` D-059 to D-064. Executors read the spec with this plan.

## Global Constraints

Copied from the authorities that bind this work. Every task's requirements implicitly include this section.

- **Zero errors is the acceptance standard** (Directive 9); percentages are diagnostics, never closure.
- **Detection precedes repair** (Directive 10): no corpus write before the corpus-wide detector for the class exists and has run.
- **Write-time enforcement only** (Directive 11); **gates block or they do not exist** (Directive 12).
- **Every defect class registered before work proceeds** (Directive 13).
- **One repair sweep per pipeline generation** (Directive 14); a Gazette rebuild of an act is a new pipeline generation for that act, not a repair sweep (Directive 2 as amended).
- **Corpus `.md` files are written ONLY through `corpus_gate.write_act`** (PR #23 Part II Task 6), never hand-edited, never hand-committed; a rebuilt act stays in staging until its witness divergences are adjudicated to zero (design 4.2 rule 0).
- **Grades are earned by gates, never assigned by source**; canonical definitions in `docs/process/COVERAGE-FLOOR.md`, Provenance floor; the decision procedure is design 4.2 and it is total.
- **Protected surfaces need an IMPLEMENTATION-PREFLIGHT before the change:** Surface 2 YAML frontmatter (the provenance block), Surface 3 MCP tool signatures (new fields, the `PROVENANCE_GRADE` warning, § in the address grammar), Surface 4 SQLite schema (migrations 007 and 008), Surface 5 commit format (Gazette-sourced commits). Task B1 writes them; no task that touches those surfaces starts before its preflight is committed.
- **ДВ politeness:** 1 request per second shared with lex.bg, descriptive UA, halt on outage stubs; the materials-list page needs a fresh server session per request (PR #32), the material page does not.
- **No live requests in tests.** Fixtures under `tests/fixtures/dv/`; fake sessions from `tests/fetcher/dv/conftest.py`.
- **The 12-hour body fetch (design step P0 bodies) is gated on a new session by owner instruction (2026-09-05).** Tasks marked GATED can be implemented and tested with fixtures now but their real run waits.
- **Owner decisions D-064 apply:** grade A batch by consumer priority; PDF-era reading by importance; one warning class `PROVENANCE_GRADE`; `identificador = dv-<idMat>` for ДВ-only acts; findings recorded as data until the write gate, then `[otmyana]` in one batch, `[reforma]` only with the engine; PDF-era tables of contents inventoried, not read.
- **Bulgarian text uses „…“** (U+201E opener, U+201C closer) in docs, docstrings and comments; the corpus body keeps its established ASCII `"` convention, so the material parser normalises Gazette „…“ to ASCII `"` in the Markdown body and records that as an editorial change.
- **Test runner is `.venv/bin/python -m pytest -q -p no:cacheprovider`**; system python cannot import the code. Run `--ignore=tests/perf` for the suite.
- **Never `git add -A`**; add files by name. **Any branch carrying corpus commits merges with a merge commit, never squash.**
- **Commit trailer:** `Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>`.

## Dependency map

| Task | Needs merged first | Gated |
|---|---|---|
| A1 instruction segmenter | nothing | no |
| A2 body-scan integration | PR `feat/dv-coverage-map` (step 1), A1 | real run GATED on the body fetch |
| A3 uncited-act title search | `feat/dv-coverage-map` | no |
| A4 coverage-map run and report | A2, A3, a valid `data/dv/materials.jsonl` | body pass GATED |
| B1 four preflights | nothing | no |
| B2 provenance package | nothing | no |
| B3 provenance check (INV-010) | PR #23 Part II Tasks 1 to 5 (registry), B2 | no |
| B4 index migration 007 | B1 (Surface 4), B2 | no |
| B5 MCP and REST exposure | B1 (Surface 3), B4 | no |
| B6 corpus-wide backfill | PR #23 Part II Task 6 (write gate), A4 title pass, B2, B3 | no |
| B7 § rows with section kind | B1 (Surfaces 3 and 4), B4 | no |
| B8 Gazette material parser | nothing | no |
| B9 metadata for a rebuilt act | B2, B8 | no |
| B10 rebuild command, staging, witness diff | B1 (Surface 5), Part II Task 6, B8, B9 | no |
| B11 pilot | B5, B6, B7, B10 | no |
| B12 governance close-out | B11 | no |

---

# Part A: P0 remainder (the coverage map's body scan)

### Task A1: ПЗР instruction segmenter for Gazette materials

The body scan of design 5.2 needs to read every instruction a Gazette material carries about other acts. A ЗИД's own §§ amend the act named in its title; the преходни и заключителни разпоредби of any act may amend or repeal other acts by name. This task turns a material body into a list of typed instructions with the act they name; it does not lower instructions to operations (FR-003).

**Files:**
- Create: `fetcher/dv/instructions.py`
- Create: `tests/fetcher/dv/test_instructions.py`
- Fixture: `tests/fixtures/dv/showMaterial-idMat300-zid.html` (exists; a ЗИД of Закона за марките и географските означения, бр. 43/2005)

**Interfaces:**
- Consumes: `fetcher.dv.materials.material_body_html(html) -> str` (merged, PR #29).
- Produces: `Instruction(position: int, paragraph: str, kind: str, target_text: str | None, dv_citation: DvCitation | None, text: str)`; `DvCitation(issue: int, year: int)`; `segment_instructions(body_html: str, *, material_title: str) -> list[Instruction]`; `is_zid_title(title: str) -> bool`. `kind` is one of `amend_titular` (a § of a ЗИД targeting the act in the title), `amend` (a § naming another act), `repeal` (a § repealing a named act), `self` (a § about this act: entry into force, delegation), `unknown` (residue).

- [ ] **Step 1: Write the failing tests**

```python
# tests/fetcher/dv/test_instructions.py
from fetcher.dv.instructions import (
    DvCitation, Instruction, is_zid_title, segment_instructions,
)
from fetcher.dv.materials import material_body_html

from .conftest import read_fixture

P = '<p style="text-align:justify"><span>{}</span></p>'


def _html(*paras: str) -> str:
    return "<html><body><div>" + "".join(P.format(p) for p in paras) + "</div></body></html>"


def test_zid_title_detection():
    assert is_zid_title("Закон за изменение и допълнение на Закона за марките и географските означения")
    assert is_zid_title("ЗАКОН за изменение на Кодекса на труда")
    assert not is_zid_title("Закон за обществения транспорт")


def test_titular_paragraphs_of_a_zid_target_the_titled_act():
    body = _html("<b>§ 1.</b> В чл. 5, ал. 2 думите „три месеца“ се заменят с „шест месеца“.",
                 "<b>§ 2.</b> Създава се чл. 5а:")
    out = segment_instructions(body, material_title="Закон за изменение на Закона за марките")
    assert [i.kind for i in out] == ["amend_titular", "amend_titular"]
    assert out[0].paragraph == "1" and out[0].target_text is None


def test_cross_act_amendment_in_final_provisions_names_its_target():
    body = _html("ПРЕХОДНИ И ЗАКЛЮЧИТЕЛНИ РАЗПОРЕДБИ",
                 "<b>§ 20.</b> В Закона за движението по пътищата (обн., ДВ, бр. 20 от 1999 г.; изм., бр. 1 от 2000 г.) се правят следните изменения:",
                 "1. В чл. 140 се създава ал. 5.",
                 "<b>§ 21.</b> Наредба № 33 от 1999 г. за обществен превоз на пътници и товари се отменя.",
                 "<b>§ 22.</b> Законът влиза в сила от 1 януари 2027 г.")
    out = segment_instructions(body, material_title="Закон за обществения транспорт")
    kinds = {i.paragraph: i.kind for i in out}
    assert kinds == {"20": "amend", "21": "repeal", "22": "self"}
    amend = next(i for i in out if i.paragraph == "20")
    assert amend.target_text == "Закона за движението по пътищата"
    assert amend.dv_citation == DvCitation(issue=20, year=1999)
    assert "1. В чл. 140" in amend.text, "the numbered items belong to the § that opened them"
    repeal = next(i for i in out if i.paragraph == "21")
    assert repeal.target_text.startswith("Наредба № 33 от 1999 г.")


def test_unclassifiable_paragraph_is_residue_not_dropped():
    body = _html("ЗАКЛЮЧИТЕЛНИ РАЗПОРЕДБИ",
                 "<b>§ 3.</b> Изпълнението на закона се възлага на министъра.",
                 "<b>§ 4.</b> Досегашният текст на приложението става приложение № 1 към чл. 7.")
    out = segment_instructions(body, material_title="Закон за X")
    assert [i.kind for i in out] == ["self", "unknown"]


def test_real_zid_material_segments_and_reports_no_silent_drop():
    html = read_fixture("showMaterial-idMat300-zid.html")
    body = material_body_html(html)
    out = segment_instructions(
        body, material_title="Закон за изменение и допълнение на Закона за марките и географските означения")
    assert out, "a ЗИД material carries at least one instruction"
    assert all(i.kind in {"amend_titular", "amend", "repeal", "self", "unknown"} for i in out)
    assert any(i.kind == "amend_titular" for i in out)
    # Every § paragraph of the body became exactly one instruction.
    import re
    n_para = len(re.findall(r"§\s*\d+[а-я]?\.", body))
    assert len(out) == n_para
```

- [ ] **Step 2: Run them and confirm they fail**

Run: `.venv/bin/python -m pytest -q -p no:cacheprovider tests/fetcher/dv/test_instructions.py`
Expected: FAIL, `ModuleNotFoundError: No module named 'fetcher.dv.instructions'`

- [ ] **Step 3: Implement**

```python
# fetcher/dv/instructions.py
"""Segment the §§ of a Gazette material into typed instructions.

A ЗИД's own paragraphs amend the act its title names; the преходни и
заключителни разпоредби of any act may amend („В Закона за X ... се“) or
repeal („... се отменя“) other acts by name. Only the naming is done here;
lowering the instruction prose to kernel operations is FR-003.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from bs4 import BeautifulSoup

ACT_NOUNS = ("Закона", "Кодекса", "Наредбата", "Наредба", "Правилника", "Правилник",
             "Постановлението", "Постановление", "Указа", "Указ", "Тарифата", "Тарифа",
             "Инструкцията", "Инструкция", "Закон", "Кодекс")

_ZID_RE = re.compile(r"^\s*закон\s+за\s+(изменение(?:\s+и\s+допълнение)?|допълнение|отмяна)\s+на\s+", re.I)
_PARA_RE = re.compile(r"^§\s*(\d+[а-я]?)\.\s*(.*)$", re.S)
_CITATION_RE = re.compile(r"\((?:обн\.,?\s*)?ДВ,?\s*бр\.\s*(\d+)\s*от\s*(\d{4})\s*г\.", re.I)
_CROSS_RE = re.compile(
    r"^В\s+((?:%s)\b[^(]*?)\s*(\([^)]*\))?\s*(?:се\s+(?:правят|прав[ия]|създава|изменя|отменя|заменя)|думите|чл\.|в\s+чл\.|навсякъде)"
    % "|".join(re.escape(n) for n in ACT_NOUNS), re.S)
_REPEAL_RE = re.compile(
    r"^((?:%s)\b[^(]*?)\s*(\([^)]*\))?\s+се\s+отменя[т]?\b" % "|".join(re.escape(n) for n in ACT_NOUNS), re.S)
_SELF_RE = re.compile(r"^(Законът|Кодексът|Наредбата|Правилникът|Постановлението|Указът|Изпълнението|Този закон|Тази наредба)\b", re.S)
_HEADING_RE = re.compile(r"^(ПРЕХОДНИ|ЗАКЛЮЧИТЕЛНИ|ДОПЪЛНИТЕЛН)", re.I)


@dataclass(frozen=True)
class DvCitation:
    issue: int
    year: int


@dataclass(frozen=True)
class Instruction:
    position: int
    paragraph: str
    kind: str
    target_text: str | None
    dv_citation: DvCitation | None
    text: str


def is_zid_title(title: str) -> bool:
    return bool(_ZID_RE.match(title or ""))


def _paragraph_texts(body_html: str) -> list[str]:
    soup = BeautifulSoup(body_html, "lxml")
    out: list[str] = []
    for p in soup.find_all("p"):
        t = " ".join(p.get_text(" ", strip=True).split())
        if t:
            out.append(t)
    if not out:  # a body that is plain text already
        out = [" ".join(l.split()) for l in body_html.splitlines() if l.strip()]
    return out


def _citation(paren: str | None) -> DvCitation | None:
    if not paren:
        return None
    m = _CITATION_RE.search(paren)
    return DvCitation(int(m.group(1)), int(m.group(2))) if m else None


def _classify(text: str, *, in_final: bool, zid: bool) -> tuple[str, str | None, DvCitation | None]:
    m = _CROSS_RE.match(text)
    if m:
        return "amend", m.group(1).strip().rstrip(","), _citation(m.group(2))
    m = _REPEAL_RE.match(text)
    if m:
        return "repeal", m.group(1).strip().rstrip(","), _citation(m.group(2))
    if _SELF_RE.match(text):
        return "self", None, None
    if zid and not in_final:
        return "amend_titular", None, None
    return "unknown", None, None


def segment_instructions(body_html: str, *, material_title: str) -> list[Instruction]:
    zid = is_zid_title(material_title)
    paras = _paragraph_texts(body_html)
    out: list[Instruction] = []
    in_final = False
    current: list[str] | None = None
    current_no: str | None = None
    pos = 0

    def flush() -> None:
        nonlocal current, current_no
        if current is None:
            return
        text = " ".join(current)
        head = text  # text after the § marker
        kind, target, cit = _classify(head, in_final=in_final, zid=zid)
        out.append(Instruction(pos, current_no or "", kind, target, cit, text))
        current, current_no = None, None

    for t in paras:
        if _HEADING_RE.match(t):
            flush()
            in_final = True
            continue
        m = _PARA_RE.match(t)
        if m:
            flush()
            pos += 1
            current_no, current = m.group(1), [m.group(2).strip()]
        elif current is not None:
            current.append(t)
    flush()
    return out
```

- [ ] **Step 4: Run the tests and confirm they pass**

Run: `.venv/bin/python -m pytest -q -p no:cacheprovider tests/fetcher/dv/test_instructions.py -v`
Expected: 5 passed. If the real-fixture test fails on the § count, inspect `material_body_html` on that fixture: the body region may contain the promulgation decree's own text; narrow `_paragraph_texts` to paragraphs after the first `§` if needed and keep the assertion (every § becomes one instruction).

- [ ] **Step 5: Commit**

```bash
git add fetcher/dv/instructions.py tests/fetcher/dv/test_instructions.py
git commit -m "feat(dv): segment Gazette material §§ into typed instructions (amend, repeal, self, titular, residue)"
```

### Task A2: body scan in the coverage map (GATED real run)

**Files:**
- Modify: `scripts/dv_coverage_map.py` (on `feat/dv-coverage-map` after it merges; the script already writes `coverage-map.csv`, `acts-summary.csv`, `chain-omissions.csv` with `pass = title`, `unresolved.csv`, `pdf-era-inventory.csv`, `estado-disputes.csv`, `report.md`)
- Create: `tests/scripts/test_dv_coverage_map_body_scan.py`

**Interfaces:**
- Consumes: `fetcher.dv.instructions.segment_instructions`, `fetcher.dv.resolver.Resolver.resolve(title, *, section=None, dv_citation=None) -> Resolution(law_id, candidates, score, flags)`, the materials table rows (`id_obj`, `id_mat`, `section`, `title`, `issue_year`, `issue_number`), the cache directory layout `cache_dir/<id_mat>.html`.
- Produces: new CLI flag `--cache-dir PATH`; `chain-omissions.csv` rows with `pass = body` and columns `law_id, issue_year, issue_number, id_mat, paragraph, kind, target_text, score`; `segmenter-residue.csv` (`id_mat, issue_year, issue_number, paragraph, text`); `estado-disputes.csv` rows with `pass = body`; a corpus-wide `chain_scanned_through` (year, number) written into `report.md` and into `acts-summary.csv` as a column, defined as the latest issue such that every material of the law, Council of Ministers and ministry sections of every HTML-era issue up to it has a cached body.

- [ ] **Step 1: Write the failing test**

```python
# tests/scripts/test_dv_coverage_map_body_scan.py
import csv, json
from pathlib import Path

from scripts.dv_coverage_map import main  # the script exposes main(argv)
from tests.fetcher.dv.conftest import read_fixture

ACT = """---
titulo: ЗАКОН ЗА МАРКИТЕ И ГЕОГРАФСКИТЕ ОЗНАЧЕНИЯ
identificador: '2134680704'
pais: bg
rango: закон
fecha_publicacion: '1999-09-14'
ultima_actualizacion: '2005-05-20'
estado: vigente
fuente: lex.bg
dv_issue: '81'
dv_year: 1999
category: laws
amendment_history:
- dv: 81/1999
  date: '1999-09-14'
---

**Чл. 1.** Текст.
"""


def test_body_scan_attributes_a_titular_zid_the_chain_lacks(tmp_path: Path):
    (tmp_path / "laws").mkdir()
    (tmp_path / "laws" / "zakon-za-markite.md").write_text(ACT, encoding="utf-8")
    issues = tmp_path / "issues.jsonl"
    issues.write_text(json.dumps({"year": 2005, "number": 43, "date": "2005-05-20", "id_obj": 777, "section": 1, "extraordinary": False}) + "\n", encoding="utf-8")
    materials = tmp_path / "materials.jsonl"
    materials.write_text(json.dumps({"id_obj": 777, "issue_year": 2005, "issue_number": 43, "issue_date": "2005-05-20", "status": "ok", "position": 1, "id_mat": 300, "section": "Народно събрание",
                                     "title": "Закон за изменение и допълнение на Закона за марките и географските означения", "start_page": 19}) + "\n", encoding="utf-8")
    cache = tmp_path / "cache"; cache.mkdir()
    (cache / "300.html").write_text(read_fixture("showMaterial-idMat300-zid.html"), encoding="utf-8")
    out = tmp_path / "out"
    assert main(["--corpus", str(tmp_path), "--issues", str(issues), "--materials", str(materials), "--cache-dir", str(cache), "--out", str(out)]) == 0
    rows = list(csv.DictReader((out / "chain-omissions.csv").open(encoding="utf-8")))
    body = [r for r in rows if r["pass"] == "body"]
    assert body and body[0]["law_id"] == "zakon-za-markite" and body[0]["issue_number"] == "43"
    residue = list(csv.DictReader((out / "segmenter-residue.csv").open(encoding="utf-8")))
    assert all(r["id_mat"] == "300" for r in residue)
    summary = {r["law_id"]: r for r in csv.DictReader((out / "acts-summary.csv").open(encoding="utf-8"))}
    assert summary["zakon-za-markite"]["chain_scanned_through"] == "2005/43"
```

- [ ] **Step 2: Run it and confirm it fails**

Run: `.venv/bin/python -m pytest -q -p no:cacheprovider tests/scripts/test_dv_coverage_map_body_scan.py`
Expected: FAIL (unknown argument `--cache-dir`, or no `pass = body` rows)

- [ ] **Step 3: Implement the body pass in the script**

Add to `scripts/dv_coverage_map.py`, next to the title pass:

```python
from fetcher.dv.instructions import is_zid_title, segment_instructions
from fetcher.dv.materials import material_body_html

LAW_SECTIONS_PREFIX = ("Народно събрание", "Министерски съвет", "Министерство", "Министър")


def _body_scan(materials: list[dict], cache_dir: Path, resolver, chains: dict[str, set[tuple[int, int]]],
               estado: dict[str, str]):
    """Yield (omissions, residue, disputes, scanned_through) from cached bodies.

    An instruction whose target resolves to a corpus act, dated an issue the
    act's chain lacks, is a chain omission (pass=body). Titular §§ of a ЗИД
    target the act named by the material title. Unclassified §§ are residue,
    never dropped. A repeal against an act still `vigente` is an estado dispute.
    """
    omissions, residue, disputes = [], [], []
    covered: dict[tuple[int, int], tuple[int, int]] = {}  # issue -> (with_body, total) over law sections
    for row in materials:
        if "id_mat" not in row or not row["section"].startswith(LAW_SECTIONS_PREFIX):
            continue
        key = (row["issue_year"], row["issue_number"])
        got, total = covered.get(key, (0, 0))
        path = cache_dir / f"{row['id_mat']}.html"
        if not path.exists():
            covered[key] = (got, total + 1)
            continue
        covered[key] = (got + 1, total + 1)
        body = material_body_html(path.read_text(encoding="utf-8"))
        title = row["title"]
        titular = resolver.resolve(title, section=row["section"]) if is_zid_title(title) else None
        for ins in segment_instructions(body, material_title=title):
            if ins.kind == "unknown":
                residue.append({"id_mat": row["id_mat"], "issue_year": key[0], "issue_number": key[1],
                                "paragraph": ins.paragraph, "text": ins.text[:500]})
                continue
            if ins.kind == "self":
                continue
            if ins.kind == "amend_titular":
                res = titular
            else:
                res = resolver.resolve(ins.target_text or "", section=row["section"],
                                       dv_citation=(ins.dv_citation.issue, ins.dv_citation.year) if ins.dv_citation else None)
            if res is None or res.law_id is None:
                residue.append({"id_mat": row["id_mat"], "issue_year": key[0], "issue_number": key[1],
                                "paragraph": ins.paragraph, "text": f"UNRESOLVED {ins.kind}: {ins.target_text or title}"})
                continue
            if key not in chains.get(res.law_id, set()):
                omissions.append({"law_id": res.law_id, "issue_year": key[0], "issue_number": key[1],
                                  "id_mat": row["id_mat"], "paragraph": ins.paragraph, "kind": ins.kind,
                                  "target_text": ins.target_text or title, "score": f"{res.score:.3f}", "pass": "body"})
            if ins.kind == "repeal" and estado.get(res.law_id) == "vigente":
                disputes.append({"law_id": res.law_id, "corpus_estado": "vigente", "finding": "repealed",
                                 "id_mat": row["id_mat"], "issue_year": key[0], "issue_number": key[1], "pass": "body"})
    complete = sorted(k for k, (g, t) in covered.items() if t and g == t)
    scanned_through = None
    for k in sorted(covered):
        if covered[k][0] != covered[k][1]:
            break
        scanned_through = k
    return omissions, residue, disputes, scanned_through
```

Wire `--cache-dir` (optional; when absent the body pass is skipped and `report.md` says so), merge the body omissions into `chain-omissions.csv` (keep the `pass` column), write `segmenter-residue.csv`, append body disputes to `estado-disputes.csv`, add `chain_scanned_through` (`"YYYY/N"` or empty) to every `acts-summary.csv` row and to `report.md`, and count residue and body omissions in `report.md`.

- [ ] **Step 4: Run the tests and confirm they pass**

Run: `.venv/bin/python -m pytest -q -p no:cacheprovider tests/scripts`
Expected: all passed, including the new test.

- [ ] **Step 5: Commit**

```bash
git add scripts/dv_coverage_map.py tests/scripts/test_dv_coverage_map_body_scan.py
git commit -m "feat(coverage-map): body scan of cached Gazette materials; chain omissions by body, segmenter residue, estado disputes, chain_scanned_through"
```

### Task A3: locate the 121 acts that cite no promulgation

**Files:**
- Modify: `scripts/dv_coverage_map.py`
- Test: `tests/scripts/test_dv_coverage_map_uncited.py`

**Interfaces:**
- Consumes: `Resolver.resolve`; the materials table titles.
- Produces: rows in `unresolved.csv` with `reason = promulgation_unknown` and a `candidates` column (up to 3 `id_mat:issue_year/number:score` entries) for every act with `fecha_publicacion` null and no `amendment_history`; the seven empty-`titulo` acts get `reason = no_title`.

- [ ] **Step 1: Write the failing test**

```python
# tests/scripts/test_dv_coverage_map_uncited.py
import csv, json
from pathlib import Path
from scripts.dv_coverage_map import main

UNCITED = "---\ntitulo: НАРЕДБА ЗА ПРИМЕР\nidentificador: '1'\npais: bg\nrango: наредба\nfecha_publicacion: null\nultima_actualizacion: null\nestado: vigente\nfuente: lex.bg\ncategory: ordinances\namendment_history: []\n---\n\n**Чл. 1.** Текст.\n"
NOTITLE = "---\ntitulo: ''\nidentificador: '2'\npais: bg\nrango: наредба\nfecha_publicacion: null\nultima_actualizacion: null\nestado: vigente\nfuente: lex.bg\ncategory: ordinances\namendment_history: []\n---\n\n**Чл. 1.** Текст.\n"


def test_uncited_acts_get_candidates_from_material_titles(tmp_path: Path):
    (tmp_path / "ordinances").mkdir()
    (tmp_path / "ordinances" / "naredba-za-primer.md").write_text(UNCITED, encoding="utf-8")
    (tmp_path / "ordinances" / "no-title.md").write_text(NOTITLE, encoding="utf-8")
    issues = tmp_path / "issues.jsonl"
    issues.write_text(json.dumps({"year": 2011, "number": 5, "date": "2011-01-18", "id_obj": 9, "section": 1, "extraordinary": False}) + "\n", encoding="utf-8")
    materials = tmp_path / "materials.jsonl"
    materials.write_text(json.dumps({"id_obj": 9, "issue_year": 2011, "issue_number": 5, "issue_date": "2011-01-18", "status": "ok", "position": 1, "id_mat": 55, "section": "Министерство на финансите", "title": "Наредба за пример", "start_page": 3}) + "\n", encoding="utf-8")
    out = tmp_path / "out"
    assert main(["--corpus", str(tmp_path), "--issues", str(issues), "--materials", str(materials), "--out", str(out)]) == 0
    rows = {r["law_id"]: r for r in csv.DictReader((out / "unresolved.csv").open(encoding="utf-8"))}
    assert rows["naredba-za-primer"]["reason"] == "promulgation_unknown"
    assert rows["naredba-za-primer"]["candidates"].startswith("55:2011/5:")
    assert rows["no-title"]["reason"] == "no_title"
```

- [ ] **Step 2: Run it and confirm it fails**

Run: `.venv/bin/python -m pytest -q -p no:cacheprovider tests/scripts/test_dv_coverage_map_uncited.py`
Expected: FAIL (no `candidates` column or no row for the uncited act)

- [ ] **Step 3: Implement**

In the script, after chain extraction: for each act with no promulgation citation, if `titulo` is empty write `reason = no_title`; otherwise build a second `Resolver` over the material titles (the resolver already normalises a title; index the non-ЗИД material titles by normalised form and by numbered key), call it with the act's own `titulo`, and write the top three candidates as `id_mat:issue_year/issue_number:score` joined by `;`. Every such act keeps `base.source = unlocated` with `promulgation_unknown` in `acts-summary.csv`.

- [ ] **Step 4: Run the tests and confirm they pass**

Run: `.venv/bin/python -m pytest -q -p no:cacheprovider tests/scripts`
Expected: all passed.

- [ ] **Step 5: Commit**

```bash
git add scripts/dv_coverage_map.py tests/scripts/test_dv_coverage_map_uncited.py
git commit -m "feat(coverage-map): candidates for the 121 acts that cite no promulgation; no_title rows for the seven untitled acts"
```

### Task A4: run the coverage map and commit its outputs (title pass now, body pass GATED)

**Files:**
- Create: `docs/research/2026-09-05-dv-coverage-map/` with `coverage-map.csv`, `acts-summary.csv`, `chain-omissions.csv`, `unresolved.csv`, `pdf-era-inventory.csv`, `estado-disputes.csv`, `segmenter-residue.csv`, `report.md`
- Data: `data/dv/issues.jsonl` and `data/dv/materials.jsonl` committed on the data branch (gzip materials if over 15 MB)

- [ ] **Step 1: Verify the materials table is valid before anything else**

Run: `.venv/bin/python - <<'EOF'` with the check that the number of distinct `id_mat` values is in the tens of thousands and that no two issues share a material set (the PR #32 guard makes a leak halt the sweep; this confirms the file). Expected: distinct idMat count above 40,000 (about 2,340 HTML-era issues at up to 18 materials), `empty` status only for issues before бр. 43/2005.

- [ ] **Step 2: Title pass**

Run: `.venv/bin/python scripts/dv_coverage_map.py --corpus . --issues data/dv/issues.jsonl --materials data/dv/materials.jsonl --out docs/research/2026-09-05-dv-coverage-map/`
Expected: exit 0; `report.md` states the totals by candidate grade (every act with an online promulgation is B-pending, pre-1989 acts are C), the PDF-era inventory totals for the owner's token-cost evaluation, and „body pass not run“.

- [ ] **Step 3: Commit the outputs and the data**

```bash
git checkout -b data/dv-coverage-map-2026-09
git add docs/research/2026-09-05-dv-coverage-map/
git commit -m "research(coverage-map): title pass over 4,146 issues; candidate grades, PDF-era inventory, chain omissions by title"
```
Commit `data/dv/issues.jsonl` and `data/dv/materials.jsonl` (or `.jsonl.gz`) on the same branch, open the PR; the owner decides whether large data files stay in git or move to a release asset.

- [ ] **Step 4 (GATED): body pass**

After the body fetch has run (`python -m fetcher.dv bodies --materials data/dv/materials.jsonl --cache-dir data/dv/cache`, about 12 hours, owner-scheduled in a new session): re-run Step 2 with `--cache-dir data/dv/cache`; the report gains `chain_scanned_through`, body omissions, residue and disputes. Commit as a second research commit.


---

# Part B: P1 (provenance block, exposure, § addressing, Gazette parser, pilot)

### Task B1: the four IMPLEMENTATION-PREFLIGHT records

No code. Four files following the existing pattern (`docs/process/IMPLEMENTATION-PREFLIGHT-2026-07-21-fr032-per-article-fts.md`): Restatement (authoritative source, hard constraint, what counts as violation, allowed scope, protected files touched, waiver required) and Evidence (governing spec, related directive, related coverage floor, follow-up). Owner sign-off is the merge of the PR that carries them; Tasks B4, B5, B7 and B10 may not start before that merge.

**Files:**
- Create: `docs/process/IMPLEMENTATION-PREFLIGHT-2026-09-06-provenance-frontmatter.md` (Surface 2)
- Create: `docs/process/IMPLEMENTATION-PREFLIGHT-2026-09-06-provenance-schema.md` (Surface 4: migrations 007 and 008)
- Create: `docs/process/IMPLEMENTATION-PREFLIGHT-2026-09-06-provenance-mcp.md` (Surface 3)
- Create: `docs/process/IMPLEMENTATION-PREFLIGHT-2026-09-06-gazette-commits.md` (Surface 5)
- Modify: `docs/data/schema-reference.md` (document the block; the pending note there points to it)

- [ ] **Step 1: Surface 2, the frontmatter block.** Hard constraint: the eight Legalize mandatory fields keep name, type and meaning; `fuente` takes the additional literal `dv.parliament.bg` for acts whose `provenance.base.state` is `rebuilt` or `read` (D-064); the five existing extensions are untouched; the new extension is one optional-then-backfilled block:

```yaml
provenance:
  grade: B-pending            # A | B | B-pending | C
  derived_at: '2026-09-06'
  base:
    source: dv_html           # dv_html | dv_pdf | dv_offline | unlocated
    state: snapshot           # rebuilt | read | snapshot
    locator: {id_mat: 242220} # or {id_file_att: N, pages: [a, b]} or null
    issue: '32'
    year: 2026
    frozen_at: null           # date the Directive 14 sweep and FR-041 capture ran
    audited: false
    declared_at: null         # UK-model declared base date, if any
    chain_scanned_through: null   # {issue, year, date} or null
    chain_inherited_before: '2005-01-01'
  checked_through: {issue: '32', year: 2026, date: '2026-04-01'}
  in_force_as_of: '2026-04-16'
  events_not_in_force: 0
  events_pending: 0
  pdf_pages_estimate: 0
  status: consolidated text without official value; Държавен вестник prevails on any discrepancy
```
and per row of `amendment_history`: `source`, `locator`, `applied` (`replayed | verified | not_incorporated | pending`), `verified_against` (text hash or null), `uncertainty` (list). What counts as violation: any act without the block after Task B6 (the floor's omission list), a grade not derivable from the recorded states (INV-010), a `fuente` that disagrees with `base.state`. Allowed scope: additive, backfilled corpus-wide in one batch by B6; `identificador = dv-<idMat>` for acts with no lex.bg document (D-064). Waiver: none.

- [ ] **Step 2: Surface 4, the schema.** Migration 007: `ALTER TABLE laws ADD COLUMN provenance_grade TEXT`, `ADD COLUMN events_pending INTEGER NOT NULL DEFAULT 0`, `ADD COLUMN checked_through TEXT`, `ADD COLUMN chain_inherited_before TEXT`; new table `amendment_events(law_id TEXT REFERENCES laws(law_id), seq INTEGER, dv TEXT, date TEXT, source TEXT, locator TEXT, applied TEXT, verified_against TEXT, uncertainty TEXT, PRIMARY KEY(law_id, seq))`. Migration 008 (Task B7): `ALTER TABLE provisions ADD COLUMN kind TEXT NOT NULL DEFAULT 'article'` and an index on `(law_id, article, kind)`. Violation: any consumer query that breaks on the added columns; a `provisions` row whose `kind` is not in the enumerated set. Allowed scope: additive columns with defaults; full rebuild path unchanged.

- [ ] **Step 3: Surface 3, the tools.** Additive fields on `get_law` (`provenance_grade`, `checked_through`, `chain_inherited_before`) and on search hits (`provenance_grade`); one new warning code `PROVENANCE_GRADE` (category `warning`, raised by `get_law`, `get_article`, `get_articles`, `search`) with payload `grade`, `pending_items`, `checked_through`, `chain_inherited_before`; the address grammar of `get_article`/`get_articles` accepts `§ N`, `§N` and `пар. N` (Task B7) and resolves them by section context, raising the existing `AMBIGUOUS_NAME`-class error with candidates when two own-act paragraphs share a number. `tools.json` 1.5.0 → 1.6.0, `error-codes.json` and `.md` 1.5.0 → 1.6.0, REST OpenAPI regenerated. Violation: any removed or retyped field; a warning that fails to ride on a grade other than A.

- [ ] **Step 4: Surface 5, Gazette-sourced commits.** Proposal for ratification: a rebuild that replaces a lex.bg snapshot with the Gazette text is `[popravka]` (a correction of our copy, not a legislative event; FR-020 excludes `[popravka]` from version boundaries, which is the desired effect since the act's legislative history did not change); a first Gazette-sourced promulgation of an act absent from lex.bg is `[nova]`; a replayed amendment is `[reforma]` (engine, later); the provenance backfill of B6 is `[popravka]` per act with `Source-Id: dvmap-2026-09` and `Source-Date` the run date. `Source-Id: dv-<idMat>` for any commit whose text comes from a Gazette material; `Source-Date` the issue date; `Norm-Id` the act's `identificador` (`dv-<idMat>` for ДВ-only acts). Violation: a corpus commit without the three trailers, or a `[reforma]` without an applied text change.

- [ ] **Step 5: Commit**

```bash
git add docs/process/IMPLEMENTATION-PREFLIGHT-2026-09-06-*.md docs/data/schema-reference.md
git commit -m "docs(preflight): Surfaces 2, 3, 4 and 5 for the provenance block, exposure, § addressing and Gazette commits"
```

### Task B2: the `provenance` package (model and total derivation)

**Files:**
- Create: `provenance/__init__.py`, `provenance/model.py`, `provenance/derive.py`
- Test: `tests/provenance/test_derive.py`, `tests/provenance/test_model.py`

**Interfaces:**
- Produces: `Base(source, state, locator, issue, year, frozen_at, audited, declared_at, chain_scanned_through, chain_inherited_before)`, `Event(dv, date, source, locator, applied, verified_against, uncertainty)`, `Provenance(grade, derived_at, base, events, checked_through, in_force_as_of, events_not_in_force, events_pending, pdf_pages_estimate, status)` with `to_frontmatter() -> dict` and `Provenance.from_frontmatter(fm: dict) -> Provenance | None`; `derive_grade(base: Base, events: list[Event], *, chain_scan_complete: bool, divergences_unadjudicated: int) -> Derivation(grade: str | None, pending_items: list[str])` where `grade None` means staging (rule 0); `DomainError` for inputs outside the constraints of design 4.2; `EVENT_SOURCES`, `EVENT_APPLIED`, `BASE_STATES`, `GRADES` tuples.

- [ ] **Step 1: Write the failing tests**

```python
# tests/provenance/test_derive.py
import itertools
import pytest
from provenance.model import Base, Event
from provenance.derive import DomainError, derive_grade

def _base(**kw):
    d = dict(source="dv_html", state="snapshot", locator=None, issue="32", year=2026, frozen_at=None,
             audited=False, declared_at=None, chain_scanned_through=None, chain_inherited_before="2005-01-01")
    d.update(kw); return Base(**d)

def _ev(source="dv_html", applied="pending", **kw):
    d = dict(dv="1/2010", date="2010-01-05", source=source, locator=None, applied=applied,
             verified_against=None, uncertainty=[]); d.update(kw); return Event(**d)

def test_single_issue_rebuilt_act_is_grade_a():
    b = _base(state="rebuilt", frozen_at="2026-09-06", audited=True)
    d = derive_grade(b, [], chain_scan_complete=True, divergences_unadjudicated=0)
    assert d.grade == "A" and d.pending_items == []

def test_rebuilt_act_with_open_divergences_has_no_grade_it_is_staging():
    b = _base(state="rebuilt", frozen_at="2026-09-06", audited=True)
    assert derive_grade(b, [], chain_scan_complete=True, divergences_unadjudicated=2).grade is None

def test_pre_1989_base_is_c_even_with_verified_events():
    b = _base(source="dv_offline", frozen_at="2026-09-06", audited=True)
    d = derive_grade(b, [_ev(applied="verified")], chain_scan_complete=True, divergences_unadjudicated=0)
    assert d.grade == "C"

def test_verified_events_before_the_sweep_are_b_pending_with_the_freeze_listed():
    b = _base(audited=True)  # frozen_at None
    d = derive_grade(b, [_ev(applied="verified"), _ev(dv="2/2011", applied="verified")], chain_scan_complete=True, divergences_unadjudicated=0)
    assert d.grade == "B-pending" and "snapshot not frozen" in d.pending_items

def test_not_incorporated_never_blocks_b():
    b = _base(frozen_at="2026-09-06", audited=True)
    d = derive_grade(b, [_ev(applied="verified"), _ev(dv="2/2011", applied="not_incorporated")], chain_scan_complete=True, divergences_unadjudicated=0)
    assert d.grade == "B"

def test_unlocated_event_is_pending_and_blocks_b():
    b = _base(frozen_at="2026-09-06", audited=True)
    d = derive_grade(b, [_ev(source="unlocated", applied="pending", uncertainty=["chain_unconfirmed"])], chain_scan_complete=True, divergences_unadjudicated=0)
    assert d.grade == "B-pending" and any("pending" in p for p in d.pending_items)

def test_pdf_promulgation_unaudited_is_b_pending_and_audited_is_b():
    b = _base(source="dv_pdf", frozen_at="2026-09-06", audited=False)
    assert derive_grade(b, [_ev(applied="verified")], chain_scan_complete=True, divergences_unadjudicated=0).grade == "B-pending"
    b2 = _base(source="dv_pdf", frozen_at="2026-09-06", audited=True)
    assert derive_grade(b2, [_ev(applied="verified")], chain_scan_complete=True, divergences_unadjudicated=0).grade == "B"

def test_uncited_promulgation_is_b_pending_with_the_reason():
    b = _base(source="unlocated", frozen_at=None, audited=False)
    d = derive_grade(b, [], chain_scan_complete=False, divergences_unadjudicated=0)
    assert d.grade == "B-pending" and "promulgation unlocated" in d.pending_items

def test_declared_base_excludes_older_events():
    b = _base(source="dv_pdf", year=1995, issue="10", frozen_at="2026-09-06", audited=True, declared_at="2005-01-01")
    d = derive_grade(b, [_ev(dv="3/1998", date="1998-01-10", source="dv_pdf", applied="pending"), _ev(dv="7/2010", applied="verified")],
                     chain_scan_complete=True, divergences_unadjudicated=0)
    assert d.grade == "B" and "events before declared base not carried: 1" in d.pending_items

def test_domain_constraints_are_enforced():
    with pytest.raises(DomainError):
        derive_grade(_base(state="rebuilt", source="dv_pdf", frozen_at="2026-09-06"), [], chain_scan_complete=True, divergences_unadjudicated=0)
    with pytest.raises(DomainError):
        derive_grade(_base(state="rebuilt", frozen_at="2026-09-06"), [_ev(applied="verified")], chain_scan_complete=True, divergences_unadjudicated=0)
    with pytest.raises(DomainError):
        derive_grade(_base(), [], chain_scan_complete=True, divergences_unadjudicated=1)

def test_every_valid_input_combination_yields_exactly_one_outcome():
    sources = ("dv_html", "dv_pdf", "dv_offline", "unlocated"); states = ("rebuilt", "read", "snapshot")
    applied = ("replayed", "verified", "not_incorporated", "pending"); ev_sources = ("dv_html", "dv_pdf", "dv_offline", "unlocated")
    seen = 0
    for src, st, frozen, aud, decl, scan, div in itertools.product(sources, states, (None, "2026-09-06"), (False, True), (None, "2005-01-01"), (False, True), (0, 1)):
        for ev in [()] + [((es, ap),) for es in ev_sources for ap in applied]:
            base = _base(source=src, state=st, frozen_at=frozen, audited=aud, declared_at=decl)
            events = [_ev(source=es, applied=ap) for es, ap in ev]
            try:
                d = derive_grade(base, events, chain_scan_complete=scan, divergences_unadjudicated=div)
            except DomainError:
                continue
            assert d.grade in (None, "A", "B", "B-pending", "C")
            seen += 1
    assert seen > 500, "the domain must not be empty; the constraints only remove impossible states"
```

- [ ] **Step 2: Run them and confirm they fail**

Run: `.venv/bin/python -m pytest -q -p no:cacheprovider tests/provenance`
Expected: FAIL, `ModuleNotFoundError: No module named 'provenance'`

- [ ] **Step 3: Implement the model and the derivation**

```python
# provenance/model.py
"""Provenance data model of the graded source model (design 4.1, D-059)."""
from __future__ import annotations
from dataclasses import dataclass, field, asdict

EVENT_SOURCES = ("dv_html", "dv_pdf", "dv_offline", "unlocated")
EVENT_APPLIED = ("replayed", "verified", "not_incorporated", "pending")
BASE_STATES = ("rebuilt", "read", "snapshot")
GRADES = ("A", "B", "B-pending", "C")
STATUS_LINE = ("consolidated text without official value; Държавен вестник prevails "
               "on any discrepancy")


@dataclass
class Base:
    source: str
    state: str
    locator: dict | None
    issue: str | None
    year: int | None
    frozen_at: str | None
    audited: bool
    declared_at: str | None
    chain_scanned_through: dict | None
    chain_inherited_before: str | None


@dataclass
class Event:
    dv: str
    date: str | None
    source: str
    locator: dict | None
    applied: str
    verified_against: str | None
    uncertainty: list[str] = field(default_factory=list)

    @property
    def year(self) -> int | None:
        try:
            return int(self.dv.split("/")[1])
        except (IndexError, ValueError):
            return None


@dataclass
class Provenance:
    grade: str | None
    derived_at: str
    base: Base
    events: list[Event]
    checked_through: dict | None
    in_force_as_of: str | None
    events_not_in_force: int
    events_pending: int
    pdf_pages_estimate: int
    status: str = STATUS_LINE

    def to_frontmatter(self) -> dict:
        d = {"grade": self.grade, "derived_at": self.derived_at, "base": asdict(self.base),
             "checked_through": self.checked_through, "in_force_as_of": self.in_force_as_of,
             "events_not_in_force": self.events_not_in_force, "events_pending": self.events_pending,
             "pdf_pages_estimate": self.pdf_pages_estimate, "status": self.status}
        return d

    @classmethod
    def from_frontmatter(cls, fm: dict) -> "Provenance | None":
        blk = fm.get("provenance")
        if not blk:
            return None
        events = [Event(dv=str(r.get("dv")), date=r.get("date"), source=r.get("source", "unlocated"),
                        locator=r.get("locator"), applied=r.get("applied", "pending"),
                        verified_against=r.get("verified_against"), uncertainty=list(r.get("uncertainty") or []))
                  for r in (fm.get("amendment_history") or [])]
        return cls(grade=blk.get("grade"), derived_at=str(blk.get("derived_at")), base=Base(**blk["base"]),
                   events=events, checked_through=blk.get("checked_through"), in_force_as_of=blk.get("in_force_as_of"),
                   events_not_in_force=int(blk.get("events_not_in_force", 0)), events_pending=int(blk.get("events_pending", 0)),
                   pdf_pages_estimate=int(blk.get("pdf_pages_estimate", 0)), status=blk.get("status", STATUS_LINE))
```

```python
# provenance/derive.py
"""The total grade derivation of design section 4.2 (D-059, D-064).

Ordered rules, first match decides. Inputs are the persisted base record, the
events and two computed values. Domain constraints raise DomainError so a
property test enumerates only possible states.
"""
from __future__ import annotations
from dataclasses import dataclass
from provenance.model import Base, Event, BASE_STATES, EVENT_APPLIED, EVENT_SOURCES


class DomainError(ValueError):
    """An input combination that cannot occur; the caller's data is wrong."""


@dataclass(frozen=True)
class Derivation:
    grade: str | None          # None = staging (rule 0), never a committed file
    pending_items: list[str]


def _check_domain(base: Base, events: list[Event], divergences: int) -> None:
    if base.state not in BASE_STATES or base.source not in EVENT_SOURCES:
        raise DomainError(f"unknown base state/source {base.state}/{base.source}")
    if base.state == "rebuilt" and base.source != "dv_html":
        raise DomainError("a rebuilt base comes only from a Gazette HTML material")
    if base.state == "read" and base.source != "dv_pdf":
        raise DomainError("a read base comes only from a Gazette issue PDF")
    if base.state in ("rebuilt", "read") and base.frozen_at is None:
        raise DomainError("a rebuilt or read base counts as frozen at its write")
    if base.state == "snapshot" and divergences:
        raise DomainError("the snapshot is the witness; it has no divergences against itself")
    for e in events:
        if e.source not in EVENT_SOURCES or e.applied not in EVENT_APPLIED:
            raise DomainError(f"unknown event source/applied {e.source}/{e.applied}")
        if e.applied == "verified" and base.state != "snapshot":
            raise DomainError("verified is defined against a snapshot base")
        if e.source == "unlocated" and e.applied != "pending":
            raise DomainError("an unlocated event is always pending")


def derive_grade(base: Base, events: list[Event], *, chain_scan_complete: bool,
                 divergences_unadjudicated: int) -> Derivation:
    _check_domain(base, events, divergences_unadjudicated)
    pending: list[str] = []
    in_scope = events
    if base.declared_at:
        cutoff = int(base.declared_at[:4])
        older = [e for e in events if e.year is not None and e.year < cutoff]
        in_scope = [e for e in events if e not in older]
        if older:
            pending.append(f"events before declared base not carried: {len(older)}")
    # rule 0: staging
    if base.state in ("rebuilt", "read") and divergences_unadjudicated > 0:
        return Derivation(None, ["witness divergences unadjudicated"])
    # rule 1: offline
    if base.source == "dv_offline" or any(e.source == "dv_offline" for e in in_scope):
        n = sum(1 for e in in_scope if e.applied == "pending")
        if n:
            pending.append(f"events pending: {n}")
        return Derivation("C", pending)
    # rule 2: ДВ-complete
    if (base.state == "rebuilt" and base.source == "dv_html" and chain_scan_complete
            and all(e.source == "dv_html" and e.applied in ("replayed", "not_incorporated") for e in in_scope)
            and divergences_unadjudicated == 0):
        return Derivation("A", pending)
    # rule 3: open items
    n_pending = sum(1 for e in in_scope if e.applied == "pending")
    if n_pending:
        pending.append(f"events pending: {n_pending}")
    if not chain_scan_complete:
        pending.append("chain scan incomplete")
    if base.source == "unlocated":
        pending.append("promulgation unlocated")
    online = base.source in ("dv_html", "dv_pdf")
    if base.state == "snapshot" and online and not base.audited:
        pending.append("base not audited")
    if base.state == "snapshot" and base.frozen_at is None:
        pending.append("snapshot not frozen")
    if pending and any(p != f"events before declared base not carried: {len(events) - len(in_scope)}" for p in pending):
        return Derivation("B-pending", pending)
    # rule 4
    return Derivation("B", pending)
```

- [ ] **Step 4: Run the tests and confirm they pass**

Run: `.venv/bin/python -m pytest -q -p no:cacheprovider tests/provenance -v`
Expected: all passed. The exhaustive test must report `seen > 500`; if the `derive_grade` declared-base handling makes `test_declared_base_excludes_older_events` fail, the rule-3 guard is comparing the wrong string: the declared-base note is informational and must not by itself force B-pending.

- [ ] **Step 5: Commit**

```bash
git add provenance/ tests/provenance/
git commit -m "feat(provenance): data model and the total grade derivation of design 4.2 with domain constraints and an exhaustive test"
```

### Task B3: the C10 detector `checks/provenance.py` (INV-010)

**Files:**
- Create: `corpus_integrity/checks/provenance.py`
- Test: `tests/corpus_integrity/test_provenance_check.py`
- Modify: `corpus_integrity/__main__.py` (register the check; do this in Task B6's PR, after the backfill, because every act without a block would fail before it)

**Interfaces:**
- Consumes: `Act` and `Violation` (PR #23 Part II Task 1), `Provenance.from_frontmatter`, `derive_grade`.
- Produces: `ProvenanceCheck` (name `"provenance"`): violation when the block is missing, when the recorded grade differs from the derivation over the recorded states, when `fuente` disagrees with `base.state`, or when the derivation raises `DomainError`.

- [ ] **Step 1: Write the failing test**

```python
# tests/corpus_integrity/test_provenance_check.py
from pathlib import Path
from corpus_integrity.checks.provenance import ProvenanceCheck
from corpus_integrity.loader import iter_acts

BLOCK = """provenance:
  grade: {grade}
  derived_at: '2026-09-06'
  base: {{source: dv_html, state: snapshot, locator: null, issue: '32', year: 2026, frozen_at: null, audited: false, declared_at: null, chain_scanned_through: null, chain_inherited_before: '2005-01-01'}}
  checked_through: {{issue: '32', year: 2026, date: '2026-04-01'}}
  in_force_as_of: '2026-04-16'
  events_not_in_force: 0
  events_pending: 0
  pdf_pages_estimate: 0
  status: consolidated text without official value
"""

def _act(tmp_path: Path, grade: str, fuente: str = "lex.bg") -> Path:
    d = tmp_path / "laws"; d.mkdir(exist_ok=True)
    (d / "a.md").write_text(f"---\ntitulo: X\nidentificador: '1'\nfuente: {fuente}\namendment_history: []\n{BLOCK.format(grade=grade)}---\n\n**Чл. 1.** Текст.\n", encoding="utf-8")
    return tmp_path

def test_missing_block_is_a_violation(tmp_path):
    d = tmp_path / "laws"; d.mkdir()
    (d / "a.md").write_text("---\ntitulo: X\nidentificador: '1'\n---\n\n**Чл. 1.** Т.\n", encoding="utf-8")
    v = ProvenanceCheck().run(iter_acts(tmp_path))
    assert len(v) == 1 and "no provenance block" in v[0].detail

def test_recorded_grade_must_equal_the_derivation(tmp_path):
    v = ProvenanceCheck().run(iter_acts(_act(tmp_path, "B")))      # unfrozen, unaudited snapshot derives B-pending
    assert len(v) == 1 and "B-pending" in v[0].detail
    assert ProvenanceCheck().run(iter_acts(_act(tmp_path, "B-pending"))) == []

def test_fuente_must_follow_base_state(tmp_path):
    v = ProvenanceCheck().run(iter_acts(_act(tmp_path, "B-pending", fuente="dv.parliament.bg")))
    assert len(v) == 1 and "fuente" in v[0].detail
```

- [ ] **Step 2: Run it and confirm it fails**

Run: `.venv/bin/python -m pytest -q -p no:cacheprovider tests/corpus_integrity/test_provenance_check.py`
Expected: FAIL, `ModuleNotFoundError: No module named 'corpus_integrity.checks.provenance'`

- [ ] **Step 3: Implement**

```python
# corpus_integrity/checks/provenance.py
"""INV-010: every act's grade equals the derivation from its recorded states."""
from typing import Iterable
from corpus_integrity.protocol import Act, Violation
from provenance.derive import DomainError, derive_grade
from provenance.model import Provenance

_FUENTE_FOR_STATE = {"rebuilt": "dv.parliament.bg", "read": "dv.parliament.bg", "snapshot": "lex.bg"}


class ProvenanceCheck:
    name = "provenance"

    def run(self, acts: Iterable[Act]) -> list[Violation]:
        out: list[Violation] = []
        for act in acts:
            prov = Provenance.from_frontmatter(act.frontmatter)
            if prov is None:
                out.append(Violation(self.name, act.slug, "no provenance block", "frontmatter"))
                continue
            scan_complete = bool(prov.base.chain_scanned_through) and prov.base.chain_scanned_through == prov.checked_through
            try:
                d = derive_grade(prov.base, prov.events, chain_scan_complete=scan_complete, divergences_unadjudicated=0)
            except DomainError as exc:
                out.append(Violation(self.name, act.slug, f"impossible provenance state: {exc}", "frontmatter.provenance"))
                continue
            if d.grade != prov.grade:
                out.append(Violation(self.name, act.slug, f"recorded grade {prov.grade!r}, derived {d.grade!r} ({'; '.join(d.pending_items)})", "frontmatter.provenance.grade"))
            want = _FUENTE_FOR_STATE.get(prov.base.state)
            if want and act.frontmatter.get("fuente") != want:
                out.append(Violation(self.name, act.slug, f"fuente {act.frontmatter.get('fuente')!r} disagrees with base.state {prov.base.state!r}", "frontmatter.fuente"))
        return out
```

- [ ] **Step 4: Run the tests and confirm they pass**

Run: `.venv/bin/python -m pytest -q -p no:cacheprovider tests/corpus_integrity/test_provenance_check.py -v`
Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add corpus_integrity/checks/provenance.py tests/corpus_integrity/test_provenance_check.py
git commit -m "feat(corpus-integrity): provenance check (INV-010): grade equals derivation, fuente follows base state"
```

### Task B4: index migration 007 and the `amendment_events` table

**Files:**
- Modify: `index/migrations.py` (add `_migrate_007` following the `_migrate_006` pattern), `index/catalog.py` (schema DDL for the new table), `index/build.py::_reindex_act` (read the block; populate the new columns and table)
- Test: `tests/index/test_migration_007.py`, `tests/index/test_build_provenance.py`

**Interfaces:**
- Produces: columns `laws.provenance_grade TEXT`, `laws.events_pending INTEGER NOT NULL DEFAULT 0`, `laws.checked_through TEXT` (ISO date), `laws.chain_inherited_before TEXT`; table `amendment_events(law_id, seq, dv, date, source, locator, applied, verified_against, uncertainty)`; `schema_version` 7.

- [ ] **Step 1: Write the failing tests**

```python
# tests/index/test_migration_007.py
import sqlite3
from index.migrations import migrate, current_version

def test_migration_007_adds_columns_and_table():
    conn = sqlite3.connect(":memory:")
    migrate(conn)
    assert current_version(conn) >= 7
    cols = {r[1] for r in conn.execute("PRAGMA table_info(laws)")}
    assert {"provenance_grade", "events_pending", "checked_through", "chain_inherited_before"} <= cols
    assert conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='amendment_events'").fetchone()
    # pre-migration rows read back a default
    conn.execute("INSERT INTO laws (law_id, doc_id, title, category, current_commit) VALUES ('x', 1, 't', 'laws', 'c')")
    assert conn.execute("SELECT events_pending FROM laws WHERE law_id='x'").fetchone()[0] == 0
```

```python
# tests/index/test_build_provenance.py
import sqlite3, subprocess
from pathlib import Path
from index.build import build

ACT = """---
titulo: ТЕСТ
identificador: '5'
pais: bg
rango: закон
fecha_publicacion: '2026-04-01'
ultima_actualizacion: '2026-04-01'
estado: vigente
fuente: lex.bg
category: laws
amendment_history:
- dv: 32/2026
  date: '2026-04-01'
  source: dv_html
  locator: {id_mat: 242220}
  applied: pending
  verified_against: null
  uncertainty: []
provenance:
  grade: B-pending
  derived_at: '2026-09-06'
  base: {source: dv_html, state: snapshot, locator: {id_mat: 242220}, issue: '32', year: 2026, frozen_at: null, audited: false, declared_at: null, chain_scanned_through: null, chain_inherited_before: '2005-01-01'}
  checked_through: {issue: '32', year: 2026, date: '2026-04-01'}
  in_force_as_of: '2026-04-16'
  events_not_in_force: 0
  events_pending: 1
  pdf_pages_estimate: 0
  status: consolidated text without official value
---

**Чл. 1.** Текст.
"""

def test_build_reads_the_provenance_block(tmp_path: Path):
    (tmp_path / "laws").mkdir(); (tmp_path / "laws" / "test.md").write_text(ACT, encoding="utf-8")
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t", "add", "."], cwd=tmp_path, check=True)
    subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "[bootstrap] test"], cwd=tmp_path, check=True)
    db = tmp_path / "catalog.db"
    build(tmp_path, str(db))
    conn = sqlite3.connect(db)
    row = conn.execute("SELECT provenance_grade, events_pending, checked_through, chain_inherited_before FROM laws WHERE law_id='test'").fetchone()
    assert row == ("B-pending", 1, "2026-04-01", "2005-01-01")
    ev = conn.execute("SELECT dv, source, applied FROM amendment_events WHERE law_id='test'").fetchall()
    assert ev == [("32/2026", "dv_html", "pending")]
```

- [ ] **Step 2: Run them and confirm they fail**

Run: `.venv/bin/python -m pytest -q -p no:cacheprovider tests/index/test_migration_007.py tests/index/test_build_provenance.py`
Expected: FAIL (`current_version` below 7; no such column)

- [ ] **Step 3: Implement**

In `index/migrations.py` add, after `_migrate_006`, a `_migrate_007` registered in the migration list with the four `ALTER TABLE laws ADD COLUMN ...` statements and:

```sql
CREATE TABLE IF NOT EXISTS amendment_events (
    law_id TEXT REFERENCES laws(law_id),
    seq INTEGER NOT NULL,
    dv TEXT,
    date TEXT,
    source TEXT NOT NULL,
    locator TEXT,
    applied TEXT NOT NULL,
    verified_against TEXT,
    uncertainty TEXT,
    PRIMARY KEY (law_id, seq)
);
```

In `index/build.py::_reindex_act`, after the `INSERT INTO laws` statement and the existing `amendments` population loop, add:

```python
    prov = meta.get("provenance") or {}
    if prov:
        ct = (prov.get("checked_through") or {}).get("date")
        conn.execute(
            "UPDATE laws SET provenance_grade=?, events_pending=?, checked_through=?, chain_inherited_before=? WHERE law_id=?",
            (prov.get("grade"), int(prov.get("events_pending", 0)), ct,
             (prov.get("base") or {}).get("chain_inherited_before"), law_id),
        )
    conn.execute("DELETE FROM amendment_events WHERE law_id=?", (law_id,))
    for i, entry in enumerate(meta.get("amendment_history") or []):
        conn.execute(
            "INSERT INTO amendment_events (law_id, seq, dv, date, source, locator, applied, verified_against, uncertainty) VALUES (?,?,?,?,?,?,?,?,?)",
            (law_id, i, str(entry.get("dv")), _iso(entry.get("date")), entry.get("source") or "unlocated",
             json.dumps(entry.get("locator"), ensure_ascii=False) if entry.get("locator") else None,
             entry.get("applied") or "pending", entry.get("verified_against"),
             json.dumps(entry.get("uncertainty") or [], ensure_ascii=False)),
        )
```
(`_iso` is the existing date coercion helper in `build.py`; `_delete_act_rows` must also delete the act's `amendment_events` rows.)

- [ ] **Step 4: Run the tests and confirm they pass; run the full index test module**

Run: `.venv/bin/python -m pytest -q -p no:cacheprovider tests/index`
Expected: all passed.

- [ ] **Step 5: Commit**

```bash
git add index/migrations.py index/catalog.py index/build.py tests/index/test_migration_007.py tests/index/test_build_provenance.py
git commit -m "feat(index): migration 007: provenance columns on laws and the amendment_events table, populated from the frontmatter block"
```

### Task B5: MCP and REST exposure with the `PROVENANCE_GRADE` warning

**Files:**
- Modify: `mcp_server/schemas.py` (`GetLawResponse` and its TypedDict gain `provenance_grade: str | None`, `checked_through: str | None`, `chain_inherited_before: str | None`; `SearchHit` gains `provenance_grade: str | None`), `mcp_server/queries.py` (`provenance_warning(grade, pending_items, checked_through, chain_inherited_before) -> dict` next to `implicit_alinea_warning`; `get_law`/`search` read the new columns), `mcp_server/server.py` (attach the warning to every successful `get_law`, `get_article`, `get_articles`, `search` response whose act grade is not `A`), `mcp_server/errors.py` (`PROVENANCE_GRADE` in the code set), `docs/api/error-codes.json` and `.md` (new entry, version 1.6.0), `tools.json` (regenerate with `mcp_server.export_tools`, version 1.6.0), `api/` models and `docs/api/openapi-rest.json` (regenerate with `api.export_openapi`)
- Test: `tests/mcp_server/test_provenance_exposure.py`

**Interfaces:**
- Produces the warning entry:

```python
def provenance_warning(grade: str, pending_items: list[str], checked_through: str | None,
                       chain_inherited_before: str | None) -> dict:
    return {
        "code": "PROVENANCE_GRADE",
        "grade": grade,
        "pending_items": list(pending_items),
        "checked_through": checked_through,
        "chain_inherited_before": chain_inherited_before,
        "message": ("Текстът не е изведен изцяло от Държавен вестник; степен на произход "
                    f"{grade}. / Text not fully derived from the State Gazette; provenance grade {grade}. "
                    "Държавен вестник има предимство при разлика."),
    }
```

- [ ] **Step 1: Write the failing test**

```python
# tests/mcp_server/test_provenance_exposure.py
from mcp_server.queries import provenance_warning

def test_provenance_warning_shape():
    w = provenance_warning("B-pending", ["events pending: 3"], "2026-04-01", "2005-01-01")
    assert w["code"] == "PROVENANCE_GRADE" and w["grade"] == "B-pending"
    assert w["pending_items"] == ["events pending: 3"] and w["checked_through"] == "2026-04-01"

def test_get_law_carries_grade_and_warning_for_non_a(file_catalog_with_provenance, app_handle):
    # fixture: a catalog built from the Task B4 test act (grade B-pending)
    resp = app_handle.get_law("test")
    assert resp["provenance_grade"] == "B-pending"
    assert any(w["code"] == "PROVENANCE_GRADE" for w in resp["warnings"])

def test_error_taxonomy_parity_includes_the_new_code():
    from mcp_server.errors import ERROR_CODES
    assert "PROVENANCE_GRADE" in ERROR_CODES
```
Build the `file_catalog_with_provenance` fixture in `tests/mcp_server/conftest.py` from the Task B4 test act (same git-init recipe) and `app_handle` from the existing `build_app(conn=...)` pattern used by `tests/mcp_server/test_connection_model.py`.

- [ ] **Step 2: Run it and confirm it fails**

Run: `.venv/bin/python -m pytest -q -p no:cacheprovider tests/mcp_server/test_provenance_exposure.py`
Expected: FAIL, `ImportError: cannot import name 'provenance_warning'`

- [ ] **Step 3: Implement** the fields, the warning, the attachment in `server.py` (read `laws.provenance_grade`, `events_pending`, `checked_through`, `chain_inherited_before` for the act; build `pending_items` as `[f"events pending: {n}"]` when `events_pending > 0` plus the derivation's other items are not stored, so the warning carries the count and the two dates), the error-code registry entries, and regenerate `tools.json` and `docs/api/openapi-rest.json` with the existing exporters.

- [ ] **Step 4: Run the tests, the parity tests and the whole suite**

Run: `.venv/bin/python -m pytest -q -p no:cacheprovider tests/mcp_server tests/api && .venv/bin/python -m mcp_server.export_tools --check && .venv/bin/python -m api.export_openapi --check`
Expected: all passed; both `--check` commands report no drift.

- [ ] **Step 5: Commit**

```bash
git add mcp_server/ api/ tools.json docs/api/error-codes.json docs/api/error-codes.md docs/api/openapi-rest.json tests/mcp_server/
git commit -m "feat(mcp,rest): provenance grade, checked_through and chain_inherited_before on get_law and search; PROVENANCE_GRADE warning; tools.json 1.6.0"
```

### Task B6: corpus-wide backfill of the provenance block through the write gate

**Files:**
- Create: `scripts/provenance_backfill.py`, `tests/scripts/test_provenance_backfill.py`
- Modify: `corpus_integrity/__main__.py` (register `ProvenanceCheck` in `CHECKS`, in this PR only)

**Interfaces:**
- Consumes: `docs/research/2026-09-05-dv-coverage-map/acts-summary.csv` and `coverage-map.csv` (Task A4), `corpus_gate.write_act(path, frontmatter, body, *, source=SourceRef)` (PR #23 Part II Task 6), `provenance.model`, `provenance.derive`, `refresh._git_commit_typed` (commit type `popravka`, Source-Id `dvmap-2026-09`, Source-Date = run date, Norm-Id = identificador; Surface 5 preflight of Task B1).
- Produces: every act carries a `provenance` block and per-event fields; `fuente` unchanged (every base is a snapshot at backfill); one `[popravka]` commit per act; `python -m corpus_integrity` reports zero `provenance` violations afterwards.

- [ ] **Step 1: Write the failing test**

```python
# tests/scripts/test_provenance_backfill.py
import csv
from pathlib import Path
from scripts.provenance_backfill import build_block, backfill

def test_build_block_from_map_rows_derives_b_pending_for_a_snapshot_act():
    summary = {"law_id": "zot", "base_source": "dv_html", "candidate_grade": "B-pending",
               "pending_items": "chain scan incomplete; base not audited; snapshot not frozen",
               "pdf_pages_estimate": "0", "checked_through": "2026/32", "checked_through_date": "2026-04-01",
               "chain_inherited_before": "2005-01-01", "base_issue": "32", "base_year": "2026", "base_locator": "242220"}
    events = [{"law_id": "zot", "dv": "32/2026", "date": "2026-04-01", "source": "dv_html", "locator": "242220", "applied": "pending", "row_kind": "base"}]
    fm = {"amendment_history": [{"dv": "32/2026", "date": "2026-04-01"}], "fuente": "lex.bg", "estado": "vigente"}
    block, history = build_block(summary, events, fm, derived_at="2026-09-06")
    assert block["grade"] == "B-pending" and block["base"]["state"] == "snapshot"
    assert history[0]["applied"] == "pending" and history[0]["source"] == "dv_html"

def test_backfill_writes_every_act_through_the_gate_and_never_by_hand(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr("scripts.provenance_backfill.write_act", lambda path, fm, body, *, source: calls.append((path, fm["provenance"]["grade"])))
    monkeypatch.setattr("scripts.provenance_backfill.commit_act", lambda *a, **k: None)
    (tmp_path / "laws").mkdir()
    (tmp_path / "laws" / "zot.md").write_text("---\ntitulo: X\nidentificador: '1'\nfuente: lex.bg\nestado: vigente\namendment_history: []\n---\n\n**Чл. 1.** Т.\n", encoding="utf-8")
    summary = tmp_path / "acts-summary.csv"
    with summary.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["law_id", "base_source", "candidate_grade", "pending_items", "pdf_pages_estimate", "checked_through", "checked_through_date", "chain_inherited_before", "base_issue", "base_year", "base_locator"])
        w.writeheader(); w.writerow({"law_id": "zot", "base_source": "unlocated", "candidate_grade": "B-pending", "pending_items": "promulgation unlocated", "pdf_pages_estimate": "0", "checked_through": "", "checked_through_date": "", "chain_inherited_before": "2005-01-01", "base_issue": "", "base_year": "", "base_locator": ""})
    events = tmp_path / "coverage-map.csv"
    events.write_text("law_id,dv,date,source,locator,applied,row_kind\n", encoding="utf-8")
    n = backfill(tmp_path, summary, events, derived_at="2026-09-06", dry_run=False)
    assert n == 1 and calls and calls[0][1] == "B-pending"
```

- [ ] **Step 2: Run it and confirm it fails**

Run: `.venv/bin/python -m pytest -q -p no:cacheprovider tests/scripts/test_provenance_backfill.py`
Expected: FAIL, `ModuleNotFoundError: No module named 'scripts.provenance_backfill'`

- [ ] **Step 3: Implement**

```python
# scripts/provenance_backfill.py
"""Backfill the provenance block into every corpus act from the coverage map.

Every base is a lex.bg snapshot at backfill time, so every act derives to
B-pending or C by design 4.2; the block records WHY (pending items). Writes go
only through corpus_gate.write_act; commits are [popravka] per act with
Source-Id dvmap-<run> (Surface 5 preflight).
"""
from __future__ import annotations
import csv, sys
from datetime import date
from pathlib import Path
import yaml
from corpus_gate import SourceRef, write_act
from provenance.derive import derive_grade
from provenance.model import Base, Event, Provenance, STATUS_LINE
from refresh import _git_commit_typed as _commit

CATEGORIES = ("laws", "codes", "ordinances", "regulations", "implementing", "postanovleniya")


def commit_act(path: Path, title: str, doc_id: str, run: str, cwd: Path) -> None:
    _commit(path, "popravka", title, doc_id, run, cwd)  # Source-Id form per the Surface 5 preflight


def _split(text: str) -> tuple[dict, str]:
    _, fm, body = text.split("---\n", 2)
    return yaml.safe_load(fm) or {}, body


def build_block(summary: dict, events: list[dict], fm: dict, *, derived_at: str) -> tuple[dict, list[dict]]:
    base = Base(source=summary["base_source"] or "unlocated", state="snapshot",
                locator={"id_mat": int(summary["base_locator"])} if summary.get("base_locator") else None,
                issue=summary.get("base_issue") or None, year=int(summary["base_year"]) if summary.get("base_year") else None,
                frozen_at=None, audited=False, declared_at=None, chain_scanned_through=None,
                chain_inherited_before=summary.get("chain_inherited_before") or "2005-01-01")
    by_dv = {e["dv"]: e for e in events if e.get("row_kind") != "base"}
    history = []
    ev_objs = []
    for row in fm.get("amendment_history") or []:
        e = by_dv.get(str(row.get("dv")), {})
        rec = {**row, "source": e.get("source") or "unlocated",
               "locator": {"id_mat": int(e["locator"])} if e.get("locator") else None,
               "applied": "pending", "verified_against": None, "uncertainty": [] if e.get("source") else ["chain_unconfirmed"]}
        history.append(rec)
        ev_objs.append(Event(dv=str(row.get("dv")), date=str(row.get("date")) if row.get("date") else None,
                             source=rec["source"], locator=rec["locator"], applied="pending", verified_against=None,
                             uncertainty=rec["uncertainty"]))
    d = derive_grade(base, ev_objs, chain_scan_complete=False, divergences_unadjudicated=0)
    ct = None
    if summary.get("checked_through"):
        y, n = summary["checked_through"].split("/")
        ct = {"issue": n, "year": int(y), "date": summary.get("checked_through_date") or None}
    prov = Provenance(grade=d.grade, derived_at=derived_at, base=base, events=ev_objs, checked_through=ct,
                      in_force_as_of=fm.get("effective_date") or fm.get("fecha_publicacion"),
                      events_not_in_force=0, events_pending=sum(1 for e in ev_objs if e.applied == "pending"),
                      pdf_pages_estimate=int(float(summary.get("pdf_pages_estimate") or 0)), status=STATUS_LINE)
    return prov.to_frontmatter(), history


def backfill(root: Path, summary_csv: Path, events_csv: Path, *, derived_at: str, dry_run: bool) -> int:
    summaries = {r["law_id"]: r for r in csv.DictReader(summary_csv.open(encoding="utf-8"))}
    events: dict[str, list[dict]] = {}
    for r in csv.DictReader(events_csv.open(encoding="utf-8")):
        events.setdefault(r["law_id"], []).append(r)
    n = 0
    for cat in CATEGORIES:
        for path in sorted((root / cat).glob("*.md")):
            law_id = path.stem
            s = summaries.get(law_id)
            if s is None:
                print(f"NO MAP ROW: {law_id}", file=sys.stderr); continue
            fm, body = _split(path.read_text(encoding="utf-8"))
            block, history = build_block(s, events.get(law_id, []), fm, derived_at=derived_at)
            fm["amendment_history"] = history
            fm["provenance"] = block
            if not dry_run:
                write_act(path, fm, body, source=SourceRef("dv", f"dvmap-{derived_at[:7]}"))
                commit_act(path, fm.get("titulo", law_id), str(fm.get("identificador")), derived_at, root)
            n += 1
    return n


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--corpus", default=".", type=Path)
    p.add_argument("--summary", required=True, type=Path)
    p.add_argument("--events", required=True, type=Path)
    p.add_argument("--dry-run", action="store_true")
    a = p.parse_args()
    print(backfill(a.corpus, a.summary, a.events, derived_at=date.today().isoformat(), dry_run=a.dry_run))
```
Then register `ProvenanceCheck()` in `corpus_integrity/__main__.py` `CHECKS`. The `write_act` signature and `SourceRef` come from Part II Task 6; adapt the import names to what landed.

- [ ] **Step 4: Run the tests; then a dry run over the real corpus**

Run: `.venv/bin/python -m pytest -q -p no:cacheprovider tests/scripts/test_provenance_backfill.py` then `.venv/bin/python scripts/provenance_backfill.py --summary docs/research/2026-09-05-dv-coverage-map/acts-summary.csv --events docs/research/2026-09-05-dv-coverage-map/coverage-map.csv --dry-run`
Expected: tests pass; the dry run prints 3,624 and no `NO MAP ROW` lines (every act must have a map row; if one is missing, fix the map, not the script).

- [ ] **Step 5: The real backfill (one batch, on a branch, merge commit)**

Run without `--dry-run` on branch `data/provenance-backfill-2026-09`; then `.venv/bin/python -m corpus_integrity --check provenance` must report 0 violations; `python -m index.build --incremental` rebuilds; open the PR; **merge with a merge commit, never squash** (3,624 corpus commits carry trailers).

- [ ] **Step 6: Commit the tooling** (before the batch)

```bash
git add scripts/provenance_backfill.py tests/scripts/test_provenance_backfill.py corpus_integrity/__main__.py
git commit -m "feat(provenance): corpus-wide backfill through the write gate; register the provenance check"
```

### Task B7: § rows keyed by section context, with a `kind` column, and § in the address grammar

The corpus carries „§ 1“ two or more times in 227 acts because every appended ПЗР restarts numbering. Naive § rows would create an FR-038-class collision set. Rows are therefore keyed by section context and carry a `kind`. Protected surfaces 3 and 4; preflights from Task B1.

**Files:**
- Modify: `index/provisions.py` (protected: read the FR-034 comments first; add § handling without changing any article rule), `index/migrations.py` (migration 008), `index/catalog.py` (DDL), `index/build.py` (write `kind`), `mcp_server/queries.py` (`_FULL_RE`, `parse_article_spec`, `ArticleSpec.kind`, the lookup), `mcp_server/schemas.py` (`GetArticleResponse.kind`), `api/` (same), `docs/api/*`, `tools.json`
- Test: `tests/index/test_provisions_paragraphs.py`, `tests/mcp_server/test_paragraph_addressing.py`

**Interfaces:**
- Produces: `Provision.kind: str` with values `article` (default), `para_dr` (a § under an own-act Допълнителн... heading), `para_pzr` (a § under an own-act Преходни/Заключителни heading without a `КЪМ` qualifier), `para_amending` (a § under a heading carrying a `КЪМ <act>` qualifier, i.e. an appended amending act's provisions); § rows have `article = "§ N"` (with the sign and one space), `paragraph = None`; `parse_article_spec("§ 1")`, `("§1")`, `("пар. 1")` return `ArticleSpec(article="§ 1", paragraph=None, range_end=None, kind="para")`; `get_article` on a § spec returns the single own-act row (`para_dr` or `para_pzr`) when exactly one exists, and raises the existing ambiguous-name error class with the candidate rows (each with `kind` and the heading text) otherwise; `para_amending` rows are never returned for a bare `§ N` spec and are reachable only through `get_articles` with `kind="para_amending"` (owner decision: the amending act's provisions are that act's, not this one's).

- [ ] **Step 1: Write the failing tests** (the hard part of this task; the executor writes the implementation to make exactly these pass)

```python
# tests/index/test_provisions_paragraphs.py
from index.provisions import parse

DOC = """# ЗАКОН ЗА ПРИМЕР

**Чл. 1.** Този закон урежда.

## Допълнителна разпоредба

**§ 1.** По смисъла на този закон:

1. "Възел за достъп" е място.

## Заключителни разпоредби

**§ 2.** Законът влиза в сила от 16 април 2026 г.

## Преходни и Заключителни разпоредби КЪМ ЗАКОНА ЗА ИЗМЕНЕНИЕ И ДОПЪЛНЕНИЕ НА ЗАКОНА ЗА ПРИМЕР

**§ 1.** В чл. 1 думите "урежда" се заменят с "определя".

**§ 2.** Законът влиза в сила от 1 януари 2027 г.
"""

def test_paragraph_rows_carry_kind_by_section_context():
    rows = parse(DOC, "primer")
    paras = [(r.article, r.kind, r.text[:20]) for r in rows if r.article.startswith("§")]
    assert paras == [
        ("§ 1", "para_dr", "**§ 1.** По смисъла"),
        ("§ 2", "para_pzr", "**§ 2.** Законът вли"),
        ("§ 1", "para_amending", "**§ 1.** В чл. 1 дум"),
        ("§ 2", "para_amending", "**§ 2.** Законът вли"),
    ]

def test_definition_items_belong_to_their_paragraph():
    rows = parse(DOC, "primer")
    dr = next(r for r in rows if r.article == "§ 1" and r.kind == "para_dr")
    assert '1. "Възел за достъп" е място.' in dr.text

def test_article_rows_are_unchanged_by_paragraph_support():
    rows = parse(DOC, "primer")
    arts = [r for r in rows if r.kind == "article"]
    assert [r.article for r in arts] == ["1"] and arts[0].paragraph is None
```

```python
# tests/mcp_server/test_paragraph_addressing.py
import pytest
from mcp_server.queries import parse_article_spec, InvalidArticleSpec

@pytest.mark.parametrize("spec", ["§ 1", "§1", "пар. 1", "§ 1."])
def test_paragraph_specs_parse(spec):
    s = parse_article_spec(spec)
    assert s.article == "§ 1" and s.kind == "para" and s.paragraph is None

def test_article_specs_keep_kind_article():
    assert parse_article_spec("чл. 5, ал. 2").kind == "article"

def test_get_article_returns_the_own_act_paragraph_and_refuses_ambiguity(paragraph_catalog, app_handle):
    # fixture built from DOC above: own-act § 1 (para_dr) and an amending § 1 (para_amending)
    r = app_handle.get_article("primer", "§ 1")
    assert r["kind"] == "para_dr" and "По смисъла" in r["text"]
    # a second own-act § 1 makes the address ambiguous: fixture variant with two para_pzr § 1
    with pytest.raises(Exception) as exc:
        app_handle.get_article("primer-dup", "§ 1")
    assert "AMBIGUOUS" in str(exc.value).upper()
```

- [ ] **Step 2: Run them and confirm they fail**

Run: `.venv/bin/python -m pytest -q -p no:cacheprovider tests/index/test_provisions_paragraphs.py tests/mcp_server/test_paragraph_addressing.py`
Expected: FAIL (`Provision` has no `kind`; `§ 1` rejected by `_FULL_RE`)

- [ ] **Step 3: Implement to the specification**

Specification the executor must meet: in `index/provisions.py`, track the current section heading while iterating paragraphs (a `## ` heading whose text matches `^(Допълнителн|Преходни|Заключителни)` sets the context; the presence of ` КЪМ ` in the heading text marks `para_amending`; a `## ` heading matching neither resets to `article`), emit one row per `**§ N.**` paragraph with its following non-heading, non-anchor paragraphs appended (the same continuation rule articles use), `article = f"§ {N}"`, `paragraph = None`, `kind` per context; `_ARTICLE_RE` and every article rule stay byte-identical (the reviewer diffs them). Migration 008 adds `provisions.kind TEXT NOT NULL DEFAULT 'article'` and index `idx_provisions_kind (law_id, article, kind)`. In `queries.py`, `_FULL_RE` gains an alternative `^\s*(?:§|пар\.)\s*(\d+[а-я]?)\.?\s*$` mapped to `ArticleSpec(article=f"§ {n}", kind="para")`; the lookup for `kind == "para"` selects rows with `kind IN ('para_dr', 'para_pzr')`, returns the single row or raises the ambiguous error with candidates `[{"article", "kind", "text_head"}]`. `GetArticleResponse.kind` is additive (default `"article"`), `tools.json` bumps to 1.7.0 (or folds into B5's 1.6.0 if in the same PR).

- [ ] **Step 4: Run the index and MCP suites, the parity checks, and the whole suite**

Run: `.venv/bin/python -m pytest -q -p no:cacheprovider tests/index tests/mcp_server tests/api && .venv/bin/python -m mcp_server.export_tools --check`
Expected: all passed; parity clean. Then rebuild `catalog.db` (`.venv/bin/python -m index.build`) and run `scripts/fr034_verify.py check` and `article-check`: the article rows must be unchanged (R3/R4/R5 clean, the four known residuals only), which proves the § support did not touch article extraction.

- [ ] **Step 5: Commit**

```bash
git add index/ mcp_server/ api/ tools.json docs/api/ tests/index/test_provisions_paragraphs.py tests/mcp_server/test_paragraph_addressing.py
git commit -m "feat(provisions,mcp): § rows keyed by section context with a kind column; § in the address grammar; ambiguity is an error, never first-row"
```

### Task B8: Gazette material parser for promulgated acts

The Gazette material is Word-exported HTML: one `<p>` per paragraph, `<b>` around the `Чл. N.` and `§ N.` anchors, centred `<p>` for headings with a `<br>` between the heading label and its title (`Глава първа<br/>ОБЩИ ПОЛОЖЕНИЯ`, `Раздел I<br/><b>Предмет и цел</b>`), the promulgating decree (`УКАЗ № N ... ПОСТАНОВЯВАМ: ... Подпечатан с държавния печат.`) before the act's own title (`ЗАКОН за обществения транспорт`), and a signature block after the last provision (`Законът е приет от ... Народно събрание на <date> ...`, `Председател на Народното събрание: ...`). Measured on idMat 242220 (535 `<p>`): 484 justified body paragraphs, 24 + 6 centred headings.

**Files:**
- Create: `fetcher/dv/text_parser.py`, `tests/fetcher/dv/test_text_parser.py`
- Fixture: `tests/fixtures/dv/showMaterial-idMat242220-zot.html` (copy of the live capture; about 300 KB)

**Interfaces:**
- Produces: `GazetteAct(title: str, rango: str, decree: str | None, adopted_on: str | None, body_markdown: str, editorial_changes: list[str], structure: StructureReport)`; `parse_promulgated_act(material_html: str) -> GazetteAct`; `StructureReport(source_articles: int, emitted_articles: int, source_paragraphs: int, emitted_paragraphs: int, source_para_signs: int, emitted_para_signs: int)` with `.ok` true only when every pair is equal; `class StructuralGateError(Exception)` raised by `parse_promulgated_act(..., strict=True)`.
- Markdown conventions (must match the corpus so witness diffs are about content): `# <TITLE IN CAPITALS>` as the corpus has it (`# ЗАКОН ЗА ОБЩЕСТВЕНИЯ ТРАНСПОРТ`); `### Глава първа. ОБЩИ ПОЛОЖЕНИЯ`; `#### Раздел I. Предмет и цел`; `## Допълнителна разпоредба` / `## Заключителни разпоредби` / `## Преходни и заключителни разпоредби` in sentence case as the corpus writes them; `**Чл. N.** text`; алинеи and items as separate paragraphs; `**§ N.** text`; Gazette „…“ normalised to ASCII `"` (recorded in `editorial_changes` as `quotes: „“ to ASCII (n)`); the en dash kept; the decree and the signature block excluded from the body and kept as metadata; `*В сила от DD.MM.YYYY г.*` emitted after the title when the ПЗР states the entry-into-force date, matching the lex.bg-derived corpus line.

- [ ] **Step 1: Write the failing tests**

```python
# tests/fetcher/dv/test_text_parser.py
import re
from fetcher.dv.text_parser import parse_promulgated_act, StructuralGateError
from .conftest import read_fixture

def _zot():
    return parse_promulgated_act(read_fixture("showMaterial-idMat242220-zot.html"), strict=True)

def test_title_rango_and_decree_are_separated_from_the_body():
    act = _zot()
    assert act.title == "ЗАКОН ЗА ОБЩЕСТВЕНИЯ ТРАНСПОРТ" and act.rango == "закон"
    assert act.decree.startswith("УКАЗ № 139")
    assert "ПОСТАНОВЯВАМ" not in act.body_markdown and "Подпечатан" not in act.body_markdown
    assert act.adopted_on == "2026-03-19"
    assert "Председател на Народното събрание" not in act.body_markdown

def test_all_106_articles_and_the_two_paragraph_sections_are_emitted():
    act = _zot()
    anchors = re.findall(r"^\*\*Чл\. (\d+[а-я]?)\.\*\* ", act.body_markdown, re.M)
    assert len(anchors) == 106 and anchors[0] == "1" and anchors[-1] == "106"
    assert "## Допълнителна разпоредба\n\n**§ 1.** По смисъла на този закон:" in act.body_markdown
    assert '1. "Възел за достъп" е предварително определено място' in act.body_markdown
    assert "## Заключителни разпоредби\n\n**§ 2.**" in act.body_markdown

def test_headings_follow_the_corpus_conventions():
    act = _zot()
    assert "### Глава първа. ОБЩИ ПОЛОЖЕНИЯ" in act.body_markdown
    assert "#### Раздел I. Предмет и цел" in act.body_markdown

def test_alineas_are_separate_paragraphs_of_their_article():
    act = _zot()
    i = act.body_markdown.index("**Чл. 2.** (1) Обществен транспорт")
    j = act.body_markdown.index("**Чл. 3.**")
    block = act.body_markdown[i:j]
    assert "\n\n(2) Превозът на пътници се изпълнява като услуга:" in block

def test_structural_gate_counts_source_and_output():
    act = _zot()
    s = act.structure
    assert s.ok and s.source_articles == s.emitted_articles == 106 and s.source_para_signs == s.emitted_para_signs == 2

def test_quotes_are_normalised_and_recorded_as_editorial_changes():
    act = _zot()
    assert "„" not in act.body_markdown and "“" not in act.body_markdown
    assert any(c.startswith("quotes:") for c in act.editorial_changes)

def test_strict_gate_refuses_a_dropped_article(monkeypatch):
    html = read_fixture("showMaterial-idMat242220-zot.html").replace("Чл. 50. ", "Член 50. ", 1)
    import pytest
    with pytest.raises(StructuralGateError):
        parse_promulgated_act(html, strict=True)
```

- [ ] **Step 2: Run them and confirm they fail**

Run: `.venv/bin/python -m pytest -q -p no:cacheprovider tests/fetcher/dv/test_text_parser.py`
Expected: FAIL, `ModuleNotFoundError: No module named 'fetcher.dv.text_parser'`

- [ ] **Step 3: Implement to the specification**

Specification: use `material_body_html` for the content region, iterate `<p>` in order, classify each: decree paragraphs (everything before the first centred paragraph whose text starts with an act-type word in capitals followed by lowercase words: `^(ЗАКОН|КОДЕКС|НАРЕДБА|ПРАВИЛНИК|ПОСТАНОВЛЕНИЕ|УКАЗ|ТАРИФА|ИНСТРУКЦИЯ)\s+[а-я№]`), the title paragraph (capitalise the whole title for the `#` line, derive `rango` from the first word), centred headings (`Глава` → `###`, `Раздел` → `####`, `Част`/`Дял` → `##`, the ДР/ПЗР headings → `##` in the corpus wording with only the first letter capitalised), anchors (`<b>` text matching `^Чл\.\s*\d+[а-я]?\.` or `^§\s*\d+[а-я]?\.` become `**Чл. N.**` / `**§ N.**`), body paragraphs (one Markdown paragraph each, `<br>` inside a paragraph becomes a line break), the signature block (from the first paragraph matching `^Законът е приет|^Кодексът е приет|^Наредбата е|^Председател|^Министър|^Издаден в` after the last provision, kept as metadata; `adopted_on` parsed from `приет ... на <D month YYYY> г.` with the Bulgarian month table already in `fetcher/bg/metadata.py`). The structural report counts `<p>` whose text starts with `Чл.` against emitted `**Чл.` anchors, `<p>` starting with `§` against emitted `**§`, and all non-decree, non-signature `<p>` against emitted paragraphs. Quotes: replace „ and “ with `"`, count the replacements into `editorial_changes`. Do not touch dashes.

- [ ] **Step 4: Run the tests and the whole suite**

Run: `.venv/bin/python -m pytest -q -p no:cacheprovider tests/fetcher/dv && .venv/bin/python -m pytest -q -p no:cacheprovider --ignore=tests/perf`
Expected: all passed.

- [ ] **Step 5: Commit**

```bash
git add fetcher/dv/text_parser.py tests/fetcher/dv/test_text_parser.py tests/fixtures/dv/showMaterial-idMat242220-zot.html
git commit -m "feat(dv): Gazette material parser for promulgated acts with a strict structural gate and recorded editorial changes"
```

### Task B9: frontmatter for a Gazette-rebuilt act

**Files:**
- Create: `fetcher/dv/metadata.py`, `tests/fetcher/dv/test_metadata.py`

**Interfaces:**
- Consumes: `parse_material_header` (merged), `GazetteAct` (B8), `Provenance`/`derive_grade` (B2), `fetcher.bg.assembler.assemble_file` and `generate_slug` (merged), `fetcher.bg.metadata` month table and `_build_eli` (import, do not copy).
- Produces: `build_frontmatter(header: MaterialHeader, act: GazetteAct, *, id_mat: int, existing: dict | None, chain_scanned_through: dict | None, checked_through: dict) -> dict` returning the full frontmatter: for an act already in the corpus, `identificador`, `eli`, `category`, `titulo` (corpus form) come from `existing`; for a ДВ-only act, `identificador = f"dv-{id_mat}"` (D-064) and `eli` from `_build_eli(rango, issue_date, slug)`; `fuente = "dv.parliament.bg"`; `fecha_publicacion` = the issue date; `dv_issue`, `dv_year` from the header; `effective_date` from the ПЗР entry-into-force sentence when present (`влиза в сила от D month YYYY` → ISO) else null; `estado = "vigente"`; `amendment_history` = `[{dv: f"{issue}/{year}", date, source: "dv_html", locator: {id_mat}, applied: "replayed" is WRONG for a promulgation: the promulgation is the base, not an event, so the history keeps exactly the rows the existing act had for LATER issues, each `pending` unless verified}]`; `provenance` = the block with `base = Base(source="dv_html", state="rebuilt", locator={"id_mat": id_mat}, issue, year, frozen_at=<today>, audited=True, declared_at=None, chain_scanned_through, chain_inherited_before=None)` and the grade from `derive_grade` with `divergences_unadjudicated=0` (the caller only builds frontmatter after adjudication reached zero).

- [ ] **Step 1: Write the failing tests**

```python
# tests/fetcher/dv/test_metadata.py
from fetcher.dv.materials import parse_material_header
from fetcher.dv.metadata import build_frontmatter
from fetcher.dv.text_parser import parse_promulgated_act
from .conftest import read_fixture

def test_frontmatter_for_the_pilot_act_keeps_identity_and_is_grade_a():
    html = read_fixture("showMaterial-idMat242220-zot.html")
    header = parse_material_header(html); act = parse_promulgated_act(html)
    existing = {"identificador": "2137259781", "eli": "/eli/bg/закон/2026/4/1/zakon-za-obshtestveniya-transport/con",
                "category": "laws", "titulo": "ЗАКОН ЗА ОБЩЕСТВЕНИЯ ТРАНСПОРТ", "amendment_history": [{"dv": "32/2026", "date": "2026-04-01"}]}
    fm = build_frontmatter(header, act, id_mat=242220, existing=existing,
                           chain_scanned_through={"issue": "81", "year": 2026, "date": "2026-09-04"},
                           checked_through={"issue": "81", "year": 2026, "date": "2026-09-04"})
    assert fm["identificador"] == "2137259781" and fm["fuente"] == "dv.parliament.bg"
    assert fm["fecha_publicacion"] == "2026-04-01" and fm["dv_issue"] == "32" and fm["dv_year"] == 2026
    assert fm["effective_date"] == "2026-04-16"
    assert fm["provenance"]["grade"] == "A" and fm["provenance"]["base"]["state"] == "rebuilt"
    assert fm["amendment_history"] == [{"dv": "32/2026", "date": "2026-04-01"}] or fm["amendment_history"] == []

def test_dv_only_act_gets_the_d064_identifier():
    html = read_fixture("showMaterial-idMat242220-zot.html")
    fm = build_frontmatter(parse_material_header(html), parse_promulgated_act(html), id_mat=242220, existing=None,
                           chain_scanned_through=None, checked_through={"issue": "32", "year": 2026, "date": "2026-04-01"})
    assert fm["identificador"] == "dv-242220" and fm["eli"].startswith("/eli/bg/закон/2026/4/1/")
    assert fm["provenance"]["grade"] == "B-pending"  # chain scan not complete for a fresh act
```

- [ ] **Step 2: Run them and confirm they fail**

Run: `.venv/bin/python -m pytest -q -p no:cacheprovider tests/fetcher/dv/test_metadata.py`
Expected: FAIL, `ModuleNotFoundError: No module named 'fetcher.dv.metadata'`

- [ ] **Step 3: Implement to the specification** (the promulgation row question in the interface block is settled thus: `amendment_history` for a single-issue act stays as the corpus had it, because FR-020 and `history()` read it; the promulgation is the base in the provenance block).

- [ ] **Step 4: Run the tests and the whole suite**

Run: `.venv/bin/python -m pytest -q -p no:cacheprovider tests/fetcher/dv`
Expected: all passed.

- [ ] **Step 5: Commit**

```bash
git add fetcher/dv/metadata.py tests/fetcher/dv/test_metadata.py
git commit -m "feat(dv): frontmatter for a Gazette-rebuilt act; dv-<idMat> identifier for acts without a lex.bg document (D-064)"
```

### Task B10: the `rebuild` command: staging, offline witness diff, adjudication, gated write

**Files:**
- Create: `fetcher/dv/rebuild.py`, `fetcher/dv/witness.py`, `tests/fetcher/dv/test_rebuild.py`, `tests/fetcher/dv/test_witness.py`
- Modify: `fetcher/dv/__main__.py` (subcommand `rebuild`)

**Interfaces:**
- Consumes: `fetch_material` with the cache, `parse_promulgated_act(strict=True)`, `build_frontmatter`, `assemble_file`, `corpus_gate.write_act`, `refresh._git_commit_typed`.
- Produces: `python -m fetcher.dv rebuild --id-mat M --law-id SLUG --corpus ROOT --stage DIR [--cache-dir DIR] [--commit]`. Without `--commit`: writes `DIR/<slug>.md` (the candidate), `DIR/<slug>.witness-diff.md` (a normalised unified diff against the committed corpus file: whitespace collapsed, ASCII and typographic quotes and dashes unified, lex.bg consolidation notes `(В сила от ...)` and `(Изм. ...)` stripped before diffing), and `DIR/<slug>.adjudication.yaml` listing every diff hunk with `lane: null`. With `--commit`: refuses unless every hunk in the adjudication file has a lane in `{source_pathology_witness, source_pathology_gazette, replay_defect, risk_signal, editorial}` and none is `replay_defect`; then writes the file through `write_act` (which runs the corpus-integrity checks), commits `[popravka]` with `Source-Id: dv-<idMat>`, `Source-Date: <issue date>`, `Norm-Id: <identificador>` (Surface 5 preflight), and prints the derived grade. `witness.py` exposes `normalise(text) -> str` and `diff_hunks(a, b) -> list[Hunk(header, lines)]`.

- [ ] **Step 1: Write the failing tests**

```python
# tests/fetcher/dv/test_witness.py
from fetcher.dv.witness import normalise, diff_hunks

def test_normalise_unifies_quotes_dashes_whitespace_and_strips_consolidation_notes():
    a = '**Чл. 1.** (В сила от 16.04.2026 г.) Този  закон – урежда „нещо“.'
    b = '**Чл. 1.** Този закон - урежда "нещо".'
    assert normalise(a) == normalise(b)

def test_diff_hunks_isolate_the_missing_definitions():
    old = "## Допълнителна разпоредба\n\n## Заключителни разпоредби\n\n**§ 2.** Текст.\n"
    new = "## Допълнителна разпоредба\n\n**§ 1.** По смисъла на този закон:\n\n1. \"Възел\" е място.\n\n## Заключителни разпоредби\n\n**§ 2.** Текст.\n"
    hunks = diff_hunks(normalise(old), normalise(new))
    assert len(hunks) == 1 and any("§ 1." in l for l in hunks[0].lines)
```

```python
# tests/fetcher/dv/test_rebuild.py
import yaml
from pathlib import Path
from fetcher.dv.__main__ import main
from .conftest import FakeSession, read_fixture

def test_rebuild_stages_candidate_diff_and_adjudication_without_committing(tmp_path: Path):
    corpus = tmp_path / "corpus"; (corpus / "laws").mkdir(parents=True)
    (corpus / "laws" / "zot.md").write_text(read_fixture("../golden/zot-snapshot.md"), encoding="utf-8")  # the committed lex.bg snapshot, copied into fixtures
    session = FakeSession(by_param={("idMat", 242220): read_fixture("showMaterial-idMat242220-zot.html")})
    stage = tmp_path / "stage"
    assert main(["rebuild", "--id-mat", "242220", "--law-id", "zot", "--corpus", str(corpus), "--stage", str(stage)], session=session) == 0
    assert (stage / "zot.md").exists() and (stage / "zot.witness-diff.md").exists()
    adj = yaml.safe_load((stage / "zot.adjudication.yaml").read_text(encoding="utf-8"))
    assert adj["hunks"] and all(h["lane"] is None for h in adj["hunks"])
    assert not (corpus / "laws" / "zot.md").read_text(encoding="utf-8").startswith("---\ntitulo: ЗАКОН ЗА ОБЩЕСТВЕНИЯ ТРАНСПОРТ\nidentificador: '2137259781'\npais: bg\nrango: закон\nfecha_publicacion: '2026-04-01'\nultima_actualizacion: '2026-04-01'\nestado: vigente\nfuente: dv.parliament.bg"), "nothing is written to the corpus without --commit"

def test_commit_refuses_open_or_replay_defect_lanes(tmp_path: Path):
    # stage first (as above), then leave one hunk unadjudicated and call --commit
    ...  # the executor completes this test with the staging recipe above; expected: non-zero exit, corpus untouched
```

- [ ] **Step 2: Run them and confirm they fail**

Run: `.venv/bin/python -m pytest -q -p no:cacheprovider tests/fetcher/dv/test_witness.py tests/fetcher/dv/test_rebuild.py`
Expected: FAIL, missing modules.

- [ ] **Step 3: Implement to the specification.** The committed snapshot of ЗОТ is copied into `tests/fixtures/golden/zot-snapshot.md` from `laws/zakon-za-obshtestveniya-transport.md` at `origin/main` (with a comment file stating the commit it came from). `normalise` collapses whitespace, maps the typographic quote characters U+201E, U+201C, U+201D, U+00AB and U+00BB to `"`, the en dash and the em dash to `-`, removes `\(В сила от [^)]*\)` and `\((?:Изм|Доп|Нов|Отм)\.[^)]*\)`. `diff_hunks` uses `difflib.unified_diff` on paragraph lists and groups by hunk header.

- [ ] **Step 4: Run the tests and the whole suite**

Run: `.venv/bin/python -m pytest -q -p no:cacheprovider tests/fetcher/dv`
Expected: all passed.

- [ ] **Step 5: Commit**

```bash
git add fetcher/dv/rebuild.py fetcher/dv/witness.py fetcher/dv/__main__.py tests/fetcher/dv/test_rebuild.py tests/fetcher/dv/test_witness.py tests/fixtures/golden/zot-snapshot.md
git commit -m "feat(dv): rebuild command with staging, offline witness diff, adjudication lanes and a gated commit"
```

### Task B11: the pilot, Закон за обществения транспорт (procedure, no new code)

Preconditions: B5, B6, B7 and B10 merged; the corpus-integrity CI job green; `catalog.db` rebuilt.

- [ ] **Step 1: Stage.** `.venv/bin/python -m fetcher.dv rebuild --id-mat 242220 --law-id zakon-za-obshtestveniya-transport --corpus . --stage data/dv/staging --cache-dir data/dv/cache`. Expected: exit 0, three files in `data/dv/staging/`.
- [ ] **Step 2: Read the witness diff in full.** Expected hunks, each adjudicated into its lane in `zakon-za-obshtestveniya-transport.adjudication.yaml`: the twelve definitions of § 1 (`source_pathology_witness`: lex.bg omitted them), the two `й`/`и` spellings (`source_pathology_witness`), the Latin `E` in „Eдинен“ if the parser did not already normalise it (`source_pathology_gazette`, recorded as an editorial change), consolidation notes and dash style (`editorial`). Any other hunk is investigated before it gets a lane; a hunk that shows the parser dropping or reordering text is `replay_defect` and stops the pilot until the parser is fixed and the stage re-run.
- [ ] **Step 3: Commit through the gate.** Re-run with `--commit`. Expected: `write_act` accepts (zero corpus-integrity violations), one `[popravka]` commit with `Source-Id: dv-242220`, `Source-Date: 2026-04-01`, `Norm-Id: 2137259781`, and the printed grade `A`.
- [ ] **Step 4: Rebuild the index incrementally** (`.venv/bin/python -m index.build --incremental`) and verify: `SELECT provenance_grade FROM laws WHERE law_id='zakon-za-obshtestveniya-transport'` is `A`; `get_article("zakon-za-obshtestveniya-transport", "§ 1")` returns the twelve definitions with `kind = para_dr`; `get_law` carries `provenance_grade: "A"` and no `PROVENANCE_GRADE` warning; the REST route agrees; `python -m corpus_integrity` is green.
- [ ] **Step 5: Verify against the standing harnesses.** `scripts/fr034_verify.py check` and `article-check` show ЗОТ's article rows unchanged in count (106) and no loss elsewhere; `scripts/structure_gaps.py --warn` no longer flags the act.
- [ ] **Step 6: Open the PR** with the adjudication file and the witness diff attached; merge with a merge commit.

### Task B12: governance close-out

- [ ] **Step 1:** `docs/frs/INDEX.md`: FR-024 progress (P0 complete, P1 pilot done), FR-042 (pilot closes the confirmed instance; 32 remaining candidates routed to grade B audits), FR-026 note (§ rows carry `kind`; the annex classification reuses the column), FR-038 note (§ ambiguity is an error, never first-row).
- [ ] **Step 2:** `docs/sync/DECISIONS.md`: D-065, the pilot outcome and the adjudication lanes used; D-066 if the Surface 5 preflight settled the commit form differently from the proposal.
- [ ] **Step 3:** `docs/sync/CORPUS-STATUS.json`: per-grade act counts (`grades: {A: 1, B: 0, B-pending: n, C: m}`), `text_complete_vs_gazette` stays false until FR-042's candidates are audited.
- [ ] **Step 4:** `docs/sync/ACTIVE.md` banner; the takt-plan follow-up FU-002 can be closed against the pilot commit.
- [ ] **Step 5:** Commit and open the PR.

---

## Self-review (plan against the design)

**Spec coverage.** Design 4.1 and 4.2: Task B2 (model, total derivation, domain constraints) and B3 (INV-010). 4.3: B1 (Surface 2 block), B4 (index), B5 (MCP/REST, warning shape per D-064), B7 (§ addressing). 5.1: merged (PR #29, PR #32); the `bodies` command is on `feat/dv-coverage-map`. 5.2: A2 (body scan), A3 (uncited acts), A4 (run), with the `pdf-era-inventory.csv` of D-064 already specified to the coverage-map agent. 5.3: on `feat/dv-coverage-map`, exercised by A2. 5.4: B8 for promulgated acts, A1 for instruction segmentation; lowering to kernel operations is FR-003 and out of scope by the design's non-goals. 5.5: out of scope (Phase 4). 5.6: the base structural audit for grade B acts is NOT in this plan; it is a P3 deliverable per the design's sequencing table and is listed as a gap to plan next. 5.7: GATED (owner). 5.8: PR #23 Part II (in flight) plus B3. 5.9: the editorial-changes list is produced by B8 per act; the corpus-wide report file is deferred to P2 and noted as a gap. Section 7 (pilot): B11 step by step. Section 8: P0 = A1 to A4 plus Part II; P1 = B1 to B12 including the backfill (B6) the review required in the P1 exit gate. Section 11 / D-064: warning shape (B5), identifier (B9), findings as data (A2, A4), inventory (A4 via the agent's addendum), reading order (P3, out of scope).

**Gaps, stated:** the grade B base structural audit (5.6) and the corpus-wide editorial-changes report (5.9) are P2/P3 work and get their own plan; the body fetch and the body pass of the map are GATED by owner instruction.

**Placeholder scan.** Task B10's second test is marked for the executor to complete with the staging recipe given in the first test; every other step carries its content. No placeholder markers remain.

**Type consistency.** `Base`, `Event`, `Provenance`, `derive_grade(...) -> Derivation(grade, pending_items)` are used identically in B2, B3, B6 and B9; `Provision.kind` values (`article`, `para_dr`, `para_pzr`, `para_amending`) are the same in B7's parser, migration and grammar; `write_act(path, frontmatter, body, *, source=SourceRef(kind, ident))` matches PR #23 Part II Task 6 and is used in B6 and B10; `fetch_materials_page` / `fetch_material` are the merged names (PR #29, #32); `Resolver.resolve(title, *, section=None, dv_citation=None) -> Resolution(law_id, candidates, score, flags)` is the interface the coverage-map agent reported.

**Model policy.** Every task here is implementation to a fixed specification and runs on Opus 5 with a fresh Opus 5 reviewer per task; the whole-branch review before each merge runs on the session model.
