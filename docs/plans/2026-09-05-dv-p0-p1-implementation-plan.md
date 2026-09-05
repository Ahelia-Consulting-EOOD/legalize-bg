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
- **Bulgarian text uses „…“** (U+201E opener, U+201C closer) in this repository's docs, docstrings and comments. **The Gazette source does not:** measured on `tests/fixtures/dv/showMaterial-idMat300-zid.html`, the material carries the entities `&ldquo;` and `&rdquo;` 108 times each, which decode to U+201C and U+201D, and zero U+201E. The corpus body keeps its established ASCII `"` convention, so the material parser and the witness normaliser share ONE constant covering all four typographic quote characters (U+201E, U+201C, U+201D, U+00AB, U+00BB) and map every one of them to ASCII `"`, recorded as an editorial change.
- **Test runner is `.venv/bin/python -m pytest -q -p no:cacheprovider`**; system python cannot import the code. Run `--ignore=tests/perf` for the suite.
- **Never `git add -A`**; add files by name. **Any branch carrying corpus commits merges with a merge commit, never squash.**
- **Commit trailer:** `Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>`.

**Amendment note 1 (the promulgation row is not an event).** Design 4.1 says the base of the act carries its own record, and the merged coverage map already separates the two with `row_kind = base`. This plan makes that explicit for the whole event multiset of design 4.2: **the events of an act are its `amendment_history` rows MINUS the promulgation row, and the promulgation row is the one whose `dv` equals `f"{base.issue}/{base.year}"`.** Exactly one helper implements the filter, `provenance.model.events_of(fm, base) -> list[Event]`, and `Provenance.from_frontmatter` (B2), the backfill (B6), the metadata builder (B9) and the C10 check (B3) all go through it. Without this a single-issue act derives `B-pending` from its own promulgation and the pilot can never reach A. Design 4.1 gains one sentence saying so; the design file is on `origin/main` and this PR is docs-only for the plan, so the edit is listed as a one-line step in Task B12.

**Amendment note 2 (`checked_through` has one meaning).** `checked_through` is **the last Gazette issue whose materials were attributed to this act by the coverage map**, that is, the scan currency mark for the act, NOT the date of the last amendment. `ultima_actualizacion` keeps the amendment meaning (design 4.3). This is what makes `chain_scan_complete` (`base.chain_scanned_through == checked_through`) a decidable predicate: an act last amended in 2011 whose scan ran through 2026 still satisfies the equality. For a freshly rebuilt act the two are equal by construction. The Surface 2 preflight (B1 Step 1) and the `provenance/model.py` docstring (B2) both state it in these words.

**Amendment note 3 (one derivation).** `provenance/derive.py` is the single implementation of design 4.2 and the single source of the `pending_items` vocabulary. The copy inside `scripts/dv_coverage_map.py` is deleted by Task B2 Step 6 and replaced with an import. Two implementations of the canonical procedure is the C10 / INV-010 hazard the design names, and `docs/process/COVERAGE-FLOOR.md` requires the procedure to be implemented once and property-tested.

**Amendment note 4 (`feat/dv-coverage-map` must be current before it runs).** `git merge-base origin/main feat/dv-coverage-map` is `0858a2f30`, which predates `a74df2ace` (PR #32, `fix/dv-materials-fresh-session`). On the branch as it stands, `forget_session_state` and `fetch_materials_page` are gone from `fetcher/dv/materials.py` and the material-leak halt (`seen_ids` / `_written_material_ids`) is gone from `cmd_materials`, so merging it as-is silently reverts both guards that Tasks A2 and A4 rely on. **Precondition on A2 and A4: `feat/dv-coverage-map` is rebased on or merged with `origin/main`, and `tests/fetcher/dv/test_session_binding.py` still exists and passes, before the map is run.**

## Dependency map

| Task | Needs merged first | Gated |
|---|---|---|
| A1 instruction segmenter | nothing | no |
| A2 body-scan integration | `feat/dv-coverage-map` rebased on `origin/main` (amendment note 4), A1, B2 (the canonical `pending_items` strings) | real run GATED on the body fetch |
| A3 candidates for the uncited acts | `feat/dv-coverage-map` rebased on `origin/main` | no |
| A4 coverage-map run and report | A2, A3, a valid `data/dv/materials.jsonl` | body pass GATED |
| A5 resolver reasoning pass | A4 title pass (it consumes `unresolved.csv`), A3 (the `uncited_corpus` fixture its tests share) | no |
| B0 `corpus_commit` package | nothing | no |
| B1 four preflights | nothing | no |
| B2 provenance package | nothing for Steps 1 to 5; `feat/dv-coverage-map` merged for Step 6 (deleting the map's copy) | no |
| B3 provenance check (INV-010) | PR #23 Part II Tasks 1 to 5 (registry), B2 | no |
| B4 index migration 007 | B1 (Surface 4), B2 | no |
| B5 MCP and REST exposure | B1 (Surface 3), B4 | no |
| B5b cf-plane grade exposure | B4, B5 | no |
| B6 corpus-wide backfill | PR #23 Part II Task 6 (write gate) **with the runner's waiver reconciliation applied inside the gate**, A4 title pass, A5, B0, B2, B3 | no |
| B7 § rows with section kind | B1 (Surfaces 3 and 4), B4 | no |
| B8 Gazette material parser | nothing (one material fetch in Step 0) | no |
| B9 metadata for a rebuilt act | B2, B8 | no |
| B10 rebuild command, staging, witness diff | B1 (Surface 5), B0, Part II Task 6, B8, B9 | no |
| B11 pilot | B5, B5b, B6, B7, B10, **and `chain_scan_complete` for the pilot act** | **GATED**: grade A needs the body scan (see B11's preconditions) |
| B12 governance close-out | B11 | no |

Three rows carry a condition that is easy to lose and expensive to discover late.

**B2 Step 6 and the merge order.** Step 6 deletes the coverage map's own `derive_grade` and rewrites the map's property tests against the canonical one, so it needs `feat/dv-coverage-map` merged; A2 in turn needs B2 for the canonical `pending_items` strings. The order is therefore: merge the map, then B2 Step 6, then A2. Steps 1 to 5 of B2 depend on nothing and can land first.

**B6 and the write gate.** `corpus_gate.write_act` runs the whole registered `CHECKS` set on the act it is writing and raises `CorpusIntegrityError` on any violation, so a backfill of 3,624 acts walks every act past every registered class. Waiver reconciliation lives in the runner (`corpus_integrity/waivers.py`), not in the gate, so without a change the first act carrying any outstanding violation of any class aborts the batch. **Requirement on PR #23 Part II Task 6: the write gate applies the same waiver reconciliation as the runner, count-equality per act (the PR #34 fix round), so a waived act writes while keeping its expected violation count and an act that regressed past its waived count still fails.** With that in place the backfill passes and the 81 waived acts keep their expected counts. B6's own tests do not change.

**B11 and the body scan.** Grade A requires `chain_scan_complete`, which is `base.chain_scanned_through == checked_through`, which only the ДВ-side body scan can establish (design 5.2, and design 7 step 4 says so for the pilot in terms). See B11's preconditions for the two ways to satisfy it, both owner decisions.

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
- Modify: `fetcher/dv/__main__.py` (the `bodies` subcommand gains `--from-issue`)
- Create: `tests/scripts/test_dv_coverage_map_body_scan.py`

**Interfaces:**
- Consumes: `fetcher.dv.instructions.segment_instructions`; `fetcher.dv.resolver.Resolver.resolve(title, *, section=None, dv_citation=None) -> Resolution(law_id, candidates, score, flags, method)` (**five** fields, not four: `method` is the last, verified on `feat/dv-coverage-map:fetcher/dv/resolver.py`); **`fetcher.dv.sections.selected(section, extra)`** for the section predicate; **`fetcher.dv.materials.cached_material(cache_dir, id_mat)`** for reading a cached body; the materials table rows (`id_obj`, `id_mat`, `section`, `title`, `issue_year`, `issue_number`, `status`); the issues table.
- Produces: new CLI flags `--cache-dir PATH` and `--sections NAME ...`; `chain-omissions.csv` rows with `pass = body`; `segmenter-residue.csv`; `estado-disputes.csv` rows with `pass = body`; a per-act `chain_scanned_through` column on `acts-summary.csv` and the corpus-wide value in `report.md`.

**Three interface rules this task must not invent around.**

1. **The section predicate is `fetcher.dv.sections.selected`, imported, not re-derived.** `cmd_bodies` selects the materials it fetches with `selected(row.get("section"), extra)` (casefolded, `министерств` stem, joint issuance, an `extra` widening set). A prefix tuple such as `("Народно събрание", "Министерски съвет", "Министерство", "Министър")` desynchronises the denominator of `chain_scanned_through` from the set the body fetch actually read: a joint-ministry section not starting with `Министерство`, a section path printed in capitals on the material page, or any `--sections` widening makes `chain_scan_complete` permanently false or falsely true. The map therefore takes the same `--sections` widening the body fetch was run with, so the two runs are provably paired.
2. **A cached body is read through `cached_material`, never with `path.read_text`.** That helper exists precisely because a file holding the site's „недостъпен“ stub is not a hit. Read raw, a stub parses to zero instructions and increments the covered counter, so an outage window silently becomes „this issue carries no cross-act amendments“ and raises `chain_scanned_through` over it.
3. **`covered` is seeded from the issues table, not from the material rows.** `materials.jsonl` also holds rows with `status` `empty`, `error_page` and `unrecognized`. An issue whose listing was unrecognised contributes no key at all, so a high-water-mark loop built only from `id_mat` rows walks straight over it. That is the D-058 failure shape four times over: measuring a proxy (bodies cached for the materials we know about) instead of the property (every HTML-era issue in the act's lifetime has been read). Every HTML-era issue starts at `(0, 1)`; only a `status: empty` row (PDF-only, legitimately nothing to read) may be marked complete without a body; `unrecognized` and `error_page` stay incomplete and stop the mark.

**CSV field lists.** The body pass writes through the same `csv.DictWriter` writers as the title pass, and `writerow` raises `ValueError: dict contains fields not in fieldnames` on any key the header lacks. The merged headers are `OMISSION_FIELDS = ["pass", "law_id", "dv_year", "dv_number", "id_mat", "section", "title", "title_kind", "resolver_score", "resolver_flags"]` and `DISPUTE_FIELDS = [..., "corpus_estado", "finding", "resolver_score", "resolver_flags"]`. **Body rows use the existing names (`dv_year`, `dv_number`, `resolver_score`, `resolver_flags`), and this task explicitly appends `paragraph`, `kind` and `target_text` to `OMISSION_FIELDS`.** `SUMMARY_FIELDS` gains `chain_scanned_through`, and Task A4 adds the six columns B6 reads (`base_issue`, `base_year`, `base_locator`, `checked_through`, `checked_through_date`, `chain_inherited_before`). A new `RESIDUE_FIELDS = ["id_mat", "dv_year", "dv_number", "paragraph", "text"]` writes `segmenter-residue.csv`. No row may carry a key absent from its writer's field list.

**Pending-item vocabulary.** `acts-summary.csv`'s `pending_items` column carries the canonical strings of `provenance.derive` (Task B2 Step 6 deletes the map's own copy of `derive_grade` and its snake_case tokens). The strings are `events pending: N`, `chain scan incomplete`, `promulgation unlocated`, `promulgation unknown`, `base not audited`, `snapshot not frozen`, `events before declared base not carried: N` and `witness divergences unadjudicated`, joined by `; `. This is why A2 lists B2 as a dependency.

**A companion flag on the fetcher.** Add `--from-issue YEAR:NUMBER` to the `bodies` subcommand in `fetcher/dv/__main__.py`: it skips every material whose issue is older than the given one, so a scoped scan over one act's lifetime window is possible without the full 12-hour sweep. Task B11's precondition depends on it. The flag narrows the FETCH, never the section set, and the map records the window it was given so `chain_scanned_through` is never claimed below it.

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
    assert body and body[0]["law_id"] == "zakon-za-markite" and body[0]["dv_number"] == "43"
    assert body[0]["paragraph"] and body[0]["kind"] == "amend_titular"
    residue = list(csv.DictReader((out / "segmenter-residue.csv").open(encoding="utf-8")))
    assert all(r["id_mat"] == "300" for r in residue)
    summary = {r["law_id"]: r for r in csv.DictReader((out / "acts-summary.csv").open(encoding="utf-8"))}
    assert summary["zakon-za-markite"]["chain_scanned_through"] == "2005/43"


def test_pending_items_use_the_canonical_derive_strings(tmp_path: Path):
    """The map's vocabulary is provenance.derive's, not a second one (B2 Step 6)."""
    (tmp_path / "laws").mkdir()
    (tmp_path / "laws" / "zakon-za-markite.md").write_text(ACT, encoding="utf-8")
    issues = tmp_path / "issues.jsonl"; issues.write_text("", encoding="utf-8")
    materials = tmp_path / "materials.jsonl"; materials.write_text("", encoding="utf-8")
    out = tmp_path / "out"
    assert main(["--corpus", str(tmp_path), "--issues", str(issues),
                 "--materials", str(materials), "--out", str(out)]) == 0
    row = next(r for r in csv.DictReader((out / "acts-summary.csv").open(encoding="utf-8"))
               if r["law_id"] == "zakon-za-markite")
    items = [p.strip() for p in row["pending_items"].split(";") if p.strip()]
    assert "chain scan incomplete" in items
    assert all(" " in item for item in items), "prose items, not snake_case tokens"


def test_an_unrecognized_listing_stops_the_high_water_mark(tmp_path: Path):
    """I4: an issue this parser could not read is NOT covered (D-058 proxy shape)."""
    (tmp_path / "laws").mkdir()
    (tmp_path / "laws" / "zakon-za-markite.md").write_text(ACT, encoding="utf-8")
    issues = tmp_path / "issues.jsonl"
    issues.write_text("".join(json.dumps(
        {"year": 2005, "number": n, "date": f"2005-05-{n:02d}", "id_obj": 700 + n,
         "section": 1, "extraordinary": False}) + "\n" for n in (43, 44, 45)), encoding="utf-8")
    materials = tmp_path / "materials.jsonl"
    materials.write_text(
        json.dumps({"id_obj": 743, "issue_year": 2005, "issue_number": 43, "status": "ok",
                    "position": 1, "id_mat": 300, "section": "Народно събрание",
                    "title": "Закон за изменение и допълнение на Закона за марките и географските означения",
                    "start_page": 19}) + "\n"
        + json.dumps({"id_obj": 744, "issue_year": 2005, "issue_number": 44,
                      "status": "unrecognized"}) + "\n"
        + json.dumps({"id_obj": 745, "issue_year": 2005, "issue_number": 45, "status": "empty"}) + "\n",
        encoding="utf-8")
    cache = tmp_path / "cache"; cache.mkdir()
    (cache / "300.html").write_text(read_fixture("showMaterial-idMat300-zid.html"), encoding="utf-8")
    out = tmp_path / "out"
    assert main(["--corpus", str(tmp_path), "--issues", str(issues), "--materials", str(materials),
                 "--cache-dir", str(cache), "--out", str(out)]) == 0
    summary = {r["law_id"]: r for r in csv.DictReader((out / "acts-summary.csv").open(encoding="utf-8"))}
    assert summary["zakon-za-markite"]["chain_scanned_through"] == "2005/43", \
        "бр. 44 was unreadable, so coverage stops there and never reaches бр. 45"


def test_an_outage_stub_in_the_cache_is_not_a_covered_material(tmp_path: Path):
    """I3: cached_material rejects the site's error stub, so the issue stays incomplete."""
    (tmp_path / "laws").mkdir()
    (tmp_path / "laws" / "zakon-za-markite.md").write_text(ACT, encoding="utf-8")
    issues = tmp_path / "issues.jsonl"
    issues.write_text(json.dumps({"year": 2005, "number": 43, "date": "2005-05-20",
                                  "id_obj": 777, "section": 1, "extraordinary": False}) + "\n",
                      encoding="utf-8")
    materials = tmp_path / "materials.jsonl"
    materials.write_text(json.dumps({"id_obj": 777, "issue_year": 2005, "issue_number": 43,
                                     "status": "ok", "position": 1, "id_mat": 300,
                                     "section": "Народно събрание", "title": "Закон за пример",
                                     "start_page": 19}) + "\n", encoding="utf-8")
    cache = tmp_path / "cache"; cache.mkdir()
    (cache / "300.html").write_text(read_fixture("materiali-idObj6000-error.html"), encoding="utf-8")
    out = tmp_path / "out"
    assert main(["--corpus", str(tmp_path), "--issues", str(issues), "--materials", str(materials),
                 "--cache-dir", str(cache), "--out", str(out)]) == 0
    summary = {r["law_id"]: r for r in csv.DictReader((out / "acts-summary.csv").open(encoding="utf-8"))}
    assert summary["zakon-za-markite"]["chain_scanned_through"] == ""
```

- [ ] **Step 2: Run it and confirm it fails**

Run: `.venv/bin/python -m pytest -q -p no:cacheprovider tests/scripts/test_dv_coverage_map_body_scan.py`
Expected: FAIL (unknown argument `--cache-dir`, or no `pass = body` rows)

- [ ] **Step 3: Implement the body pass in the script**

Add to `scripts/dv_coverage_map.py`, next to the title pass:

```python
from fetcher.dv.instructions import is_zid_title, segment_instructions
from fetcher.dv.materials import cached_material, material_body_html
from fetcher.dv.sections import selected

HTML_ERA_START = (2005, 43)  # the first issue with a materials list


def _seed_covered(issues: list, materials: list[dict], extra: tuple[str, ...]
                  ) -> dict[tuple[int, int], tuple[int, int]]:
    """Every HTML-era issue starts uncovered; only `empty` needs no body.

    The denominator is the issues table, not the material rows. An issue whose
    listing this parser could not read („unrecognized“) or that answered with
    the site's error page contributes no material row at all, and a covered map
    built from material rows alone would walk straight over it and claim
    coverage through a later issue. That is the D-058 proxy shape: measuring
    „bodies cached for materials we know about“ instead of „every HTML-era
    issue in the act's lifetime has been read“.
    """
    status = {(m["issue_year"], m["issue_number"]): m.get("status")
              for m in materials if "id_mat" not in m}
    covered: dict[tuple[int, int], tuple[int, int]] = {}
    for issue in issues:
        key = (issue.year, issue.number)
        if key < HTML_ERA_START:
            continue
        covered[key] = (1, 1) if status.get(key) == "empty" else (0, 1)
    for m in materials:
        if "id_mat" not in m or not selected(m.get("section"), extra):
            continue
        key = (m["issue_year"], m["issue_number"])
        got, total = covered.get(key, (0, 0))
        covered[key] = (got, total + 1) if total else (0, 1)
    return covered


def _body_scan(issues, materials: list[dict], cache_dir: Path, resolver,
               chains: dict[str, set[tuple[int, int]]], estado: dict[str, str],
               extra: tuple[str, ...] = ()):
    """Yield (omissions, residue, disputes, covered) from cached bodies.

    An instruction whose target resolves to a corpus act, dated an issue the
    act's chain lacks, is a chain omission (pass=body). Titular §§ of a ЗИД
    target the act named by the material title. Unclassified §§ are residue,
    never dropped. A repeal against an act still `vigente` is an estado dispute.
    """
    omissions, residue, disputes = [], [], []
    covered = _seed_covered(issues, materials, extra)
    for row in materials:
        if "id_mat" not in row or not selected(row.get("section"), extra):
            continue
        key = (row["issue_year"], row["issue_number"])
        got, total = covered.get(key, (0, 1))
        stored = cached_material(cache_dir, row["id_mat"])
        if stored is None:
            # No file, or a file holding the site's „недостъпен“ stub: an
            # outage is not the Gazette's answer and must not raise the mark.
            continue
        covered[key] = (got + 1, total)
        body = material_body_html(stored)
        title = row["title"]
        titular = resolver.resolve(title, section=row["section"]) if is_zid_title(title) else None
        for ins in segment_instructions(body, material_title=title):
            base = {"id_mat": row["id_mat"], "dv_year": key[0], "dv_number": key[1],
                    "paragraph": ins.paragraph}
            if ins.kind == "unknown":
                residue.append({**base, "text": ins.text[:500]})
                continue
            if ins.kind == "self":
                continue
            if ins.kind == "amend_titular":
                res = titular
            else:
                res = resolver.resolve(
                    ins.target_text or "", section=row["section"],
                    dv_citation=(ins.dv_citation.issue, ins.dv_citation.year) if ins.dv_citation else None)
            if res is None or res.law_id is None:
                residue.append({**base, "text": f"UNRESOLVED {ins.kind}: {ins.target_text or title}"})
                continue
            if key not in chains.get(res.law_id, set()):
                omissions.append({"pass": "body", "law_id": res.law_id, "dv_year": key[0],
                                  "dv_number": key[1], "id_mat": row["id_mat"],
                                  "section": row["section"], "title": title, "title_kind": "",
                                  "paragraph": ins.paragraph, "kind": ins.kind,
                                  "target_text": ins.target_text or title,
                                  "resolver_score": f"{res.score:.3f}",
                                  "resolver_flags": ";".join(res.flags)})
            if ins.kind == "repeal" and estado.get(res.law_id) == "vigente":
                disputes.append({"pass": "body", "law_id": res.law_id, "dv_year": key[0],
                                 "dv_number": key[1], "id_mat": row["id_mat"],
                                 "section": row["section"], "title": title, "title_kind": "",
                                 "corpus_estado": "vigente", "finding": "repealed",
                                 "resolver_score": f"{res.score:.3f}",
                                 "resolver_flags": ";".join(res.flags)})
    return omissions, residue, disputes, covered


def _scanned_through(covered: dict[tuple[int, int], tuple[int, int]],
                     since: tuple[int, int] | None = None) -> tuple[int, int] | None:
    """The high-water mark: the last issue with every selected body cached.

    `since` is the act's lifetime start (its promulgation issue), so an act
    promulgated in 2026 is not held back by 2005 issues nobody fetched.
    """
    mark = None
    for key in sorted(covered):
        if since is not None and key < since:
            continue
        got, total = covered[key]
        if got != total:
            break
        mark = key
    return mark
```

Wire `--cache-dir` (optional; when absent the body pass is skipped and `report.md` says so) and `--sections NAME ...` (passed straight to `selected` as `extra`, the same widening the body fetch was run with). Append `paragraph`, `kind` and `target_text` to `OMISSION_FIELDS` and merge the body omissions into `chain-omissions.csv` on that header; write `segmenter-residue.csv` on `RESIDUE_FIELDS`; append body disputes to `estado-disputes.csv` on `DISPUTE_FIELDS`; add `chain_scanned_through` to `SUMMARY_FIELDS`, computed per act as `_scanned_through(covered, since=<the act's promulgation issue>)` formatted `"YYYY/N"` or empty; write the corpus-wide mark, the residue count and the body-omission count into `report.md`. Every dict written must carry exactly the keys of its field list.

- [ ] **Step 4: Add `--from-issue` to the `bodies` subcommand**

In `fetcher/dv/__main__.py`, `bodies` gains `--from-issue YEAR:NUMBER` (default none): `cmd_bodies` skips every material whose `(issue_year, issue_number)` sorts before the given pair, after the `selected` filter, never instead of it. A test in `tests/fetcher/dv/test_cli.py` passes three materials across two issues and asserts only the newer issue's materials are fetched. This is what lets Task B11 satisfy its precondition with a scoped fetch of about 50 issues instead of the gated 12-hour sweep.

- [ ] **Step 5: Run the tests and confirm they pass**

Run: `.venv/bin/python -m pytest -q -p no:cacheprovider tests/scripts tests/fetcher/dv`
Expected: all passed, including the four new map tests and the `--from-issue` test.

- [ ] **Step 6: Commit**

```bash
git add scripts/dv_coverage_map.py fetcher/dv/__main__.py tests/scripts/test_dv_coverage_map_body_scan.py tests/fetcher/dv/test_cli.py
git commit -m "feat(coverage-map): body scan of cached Gazette materials; chain omissions by body, segmenter residue, estado disputes, chain_scanned_through; bodies --from-issue"
```

### Task A3: candidates for the 121 acts that cite no promulgation

**The rows already exist; only the `candidates` column is empty.** The merged script writes both classes into `unresolved.csv` keyed on the machine field `kind`, with prose in `reason`:

```python
{"kind": "promulgation_unknown", ..., "reason": "the act cites no promulgation"}
{"kind": "empty_titulo",         ..., "reason": "no titulo: the act cannot be resolved by title at all"}
```

and `tests/scripts/test_dv_coverage_map.py` pins them (`rows(..., kind="empty_titulo")`, `rows(..., kind="promulgation_unknown")`). Renaming those fields to `reason = promulgation_unknown` / `reason = no_title` would break the merged tests for nothing. **This task's whole delta is populating `candidates` for the `kind = promulgation_unknown` rows**, which the merged writer currently leaves as `""`.

**Files:**
- Modify: `scripts/dv_coverage_map.py`
- Create: `tests/scripts/conftest.py` (the `uncited_corpus` fixture, shared with Task A5)
- Test: `tests/scripts/test_dv_coverage_map_uncited.py`

**Interfaces:**
- Consumes: `Resolver.resolve`; the materials table titles.
- Produces: the `candidates` column of every `kind = promulgation_unknown` row filled with up to three `id_mat:dv_year/dv_number:score` entries joined by `;`, ordered by descending score. `kind` and `reason` keep the merged values, and the `kind = empty_titulo` rows are untouched (an act with no `titulo` cannot be resolved by title, so it gets no candidates).

- [ ] **Step 1: Write the failing test**

```python
# tests/scripts/conftest.py
import json
from pathlib import Path

import pytest

UNCITED = "---\ntitulo: НАРЕДБА ЗА ПРИМЕР\nidentificador: '1'\npais: bg\nrango: наредба\nfecha_publicacion: null\nultima_actualizacion: null\nestado: vigente\nfuente: lex.bg\ncategory: ordinances\namendment_history: []\n---\n\n**Чл. 1.** Текст.\n"
NOTITLE = "---\ntitulo: ''\nidentificador: '2'\npais: bg\nrango: наредба\nfecha_publicacion: null\nultima_actualizacion: null\nestado: vigente\nfuente: lex.bg\ncategory: ordinances\namendment_history: []\n---\n\n**Чл. 1.** Текст.\n"


@pytest.fixture
def uncited_corpus(tmp_path: Path) -> tuple[Path, Path, Path]:
    """One act that cites no promulgation, one with no titulo, and the single
    issue and material they are resolved against.

    Returns `(corpus_root, issues_jsonl, materials_jsonl)`. Shared by A3, which
    asserts the `candidates` column on the `promulgation_unknown` row, and A5,
    which applies a resolution record to that same row. Two tasks reading one
    fixture is what keeps their row identities in agreement.
    """
    (tmp_path / "ordinances").mkdir()
    (tmp_path / "ordinances" / "naredba-za-primer.md").write_text(UNCITED, encoding="utf-8")
    (tmp_path / "ordinances" / "no-title.md").write_text(NOTITLE, encoding="utf-8")
    issues = tmp_path / "issues.jsonl"
    issues.write_text(json.dumps({"year": 2011, "number": 5, "date": "2011-01-18",
                                  "id_obj": 9, "section": 1, "extraordinary": False}) + "\n",
                      encoding="utf-8")
    materials = tmp_path / "materials.jsonl"
    materials.write_text(json.dumps({"id_obj": 9, "issue_year": 2011, "issue_number": 5,
                                     "issue_date": "2011-01-18", "status": "ok", "position": 1,
                                     "id_mat": 55, "section": "Министерство на финансите",
                                     "title": "Наредба за пример", "start_page": 3}) + "\n",
                         encoding="utf-8")
    return tmp_path, issues, materials
```

```python
# tests/scripts/test_dv_coverage_map_uncited.py
import csv
from pathlib import Path

from scripts.dv_coverage_map import main


def test_uncited_acts_get_candidates_from_material_titles(tmp_path: Path, uncited_corpus):
    corpus, issues, materials = uncited_corpus
    out = tmp_path / "out"
    assert main(["--corpus", str(corpus), "--issues", str(issues),
                 "--materials", str(materials), "--out", str(out)]) == 0
    rows = {(r["kind"], r["law_id"]): r
            for r in csv.DictReader((out / "unresolved.csv").open(encoding="utf-8"))}
    assert rows[("promulgation_unknown", "naredba-za-primer")]["candidates"].startswith("55:2011/5:")
    assert ("empty_titulo", "no-title") in rows
    assert rows[("empty_titulo", "no-title")]["candidates"] == ""
```

- [ ] **Step 2: Run it and confirm it fails**

Run: `.venv/bin/python -m pytest -q -p no:cacheprovider tests/scripts/test_dv_coverage_map_uncited.py`
Expected: FAIL on the `candidates` assertion (the row exists; its `candidates` is `""`).

- [ ] **Step 3: Implement**

In the script, where the `kind = promulgation_unknown` rows are built: build a second `Resolver` over the material titles (the resolver already normalises a title; index the non-ЗИД material titles by normalised form and by numbered key), call it with the act's own `titulo`, and write the top three candidates as `id_mat:dv_year/dv_number:score` joined by `;` into the existing `candidates` column. `kind` and `reason` are not touched, and neither are the `empty_titulo` rows. Every such act keeps `base.source = unlocated` and the pending item `promulgation unknown` in `acts-summary.csv`.

Run `.venv/bin/python -m pytest -q -p no:cacheprovider tests/scripts/test_dv_coverage_map.py` as well: the merged tests that pin `kind` must still pass, which is the proof that this task added a column value and renamed nothing.

- [ ] **Step 4: Run the tests and confirm they pass**

Run: `.venv/bin/python -m pytest -q -p no:cacheprovider tests/scripts`
Expected: all passed.

- [ ] **Step 5: Commit**

```bash
git add scripts/dv_coverage_map.py tests/scripts/conftest.py tests/scripts/test_dv_coverage_map_uncited.py
git commit -m "feat(coverage-map): candidates for the 121 acts that cite no promulgation"
```

### Task A4: run the coverage map and commit its outputs (title pass now, body pass GATED)

**Files:**
- Modify: `scripts/dv_coverage_map.py` (the six summary columns of Step 0)
- Create: `docs/research/2026-09-05-dv-coverage-map/` with `coverage-map.csv`, `acts-summary.csv`, `chain-omissions.csv`, `unresolved.csv`, `pdf-era-inventory.csv`, `estado-disputes.csv`, `segmenter-residue.csv`, `report.md`
- Data: `data/dv/issues.jsonl` and `data/dv/materials.jsonl` committed on the data branch (gzip materials if over 15 MB)

- [ ] **Step 0: Extend `SUMMARY_FIELDS` with the six columns the backfill reads**

Task B6 reconstructs every act's `base` record from `acts-summary.csv`. The merged writer emits `["law_id", "title", "candidate_grade", "pending_items", "events_total", "events_dv_html", "events_dv_pdf", "events_unlocated", "events_dv_offline", "pdf_pages_estimate", "base_source", "dv_identifier"]`, plus `chain_scanned_through` from Task A2. Six of the fields B6 needs are missing. **Add `base_issue`, `base_year`, `base_locator`, `checked_through` (`"YYYY/N"`), `checked_through_date` (ISO or empty) and `chain_inherited_before` to `SUMMARY_FIELDS` and populate them**, and extend `tests/scripts/test_dv_coverage_map.py` with one assertion per new column on the existing fixture act. Keeping the CSV round trip (rather than having B6 import the map's builder) keeps the map's artifacts reviewable, which is the point of publishing them.

Note for B6: there is no `dv` column on `coverage-map.csv` and no `locator`. The event key is `dv_year` + `dv_number` and the locator column is `locator_id_mat`. B6 reads those names.

- [ ] **Step 1: Verify the branch is current and the materials table is valid, before anything else**

First: `git merge-base --is-ancestor origin/main HEAD` on the map branch must succeed, and `tests/fetcher/dv/test_session_binding.py` must exist and pass. `feat/dv-coverage-map` forked at `0858a2f30`, before PR #32 (`a74df2ace`), and merging it un-rebased reverts `forget_session_state`, `fetch_materials_page` and the material-leak halt in `cmd_materials`. This step's own reasoning („the PR #32 guard makes a leak halt the sweep“) is only true if those guards are present.

Then: `.venv/bin/python - <<'EOF'` with the check that the number of distinct `id_mat` values is in the tens of thousands and that no two issues share a material set (the PR #32 guard makes a leak halt the sweep; this confirms the file). Expected: distinct idMat count above 40,000 (about 2,340 HTML-era issues at up to 18 materials), `empty` status only for issues before бр. 43/2005.

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

### Task A5: the resolver's reasoning pass over `unresolved.csv`

Design section 8 puts „5.3 resolver **with its reasoning pass**“ inside P0, and design 5.3 says what shape it takes: a `title_ambiguous` event is recorded `unlocated` and `pending` and queued for a pass that reads the material and emits `{id_mat, instruction, law_id, verdict, reason}` as data, cached and re-runnable, exactly the flagger-reasoner-applier shape D-055 chose for FR-030. Neither the merged branch nor the rest of this plan contains one, and without it every `title_ambiguous` event stays `pending`, which pins its act at B-pending permanently. This task builds the file format and the applier; **the reasoning itself is performed at orchestration time by the session reading the material, not by code.**

**Files:**
- Create: `docs/research/2026-09-05-dv-coverage-map/resolutions.yaml`
- Modify: `scripts/dv_coverage_map.py` (`--resolutions PATH`)
- Test: `tests/scripts/test_dv_coverage_map_resolutions.py` (with the `uncited_corpus` fixture Task A3 adds to `tests/scripts/conftest.py`)

**The record key is the row's own identifying columns, read off the merged writer.** The header and the values are not the same thing, and the earlier draft keyed on values the rows do not carry:

```python
# as in scripts/dv_coverage_map.py:893 on feat/dv-coverage-map
UNRESOLVED_FIELDS = [
    "kind", "law_id", "dv_year", "dv_number", "title", "candidates",
    "resolver_score", "resolver_flags", "dv_identifier", "reason",
]
# as in scripts/dv_coverage_map.py:780-794 (the row for an act citing no promulgation)
        if not act.fecha_publicacion:
            unresolved.append(
                {
                    "kind": "promulgation_unknown",
                    "law_id": act.law_id,
                    "dv_year": "",
                    "dv_number": "",
                    "title": act.title,
                    "candidates": "",
                    ...
```

So an uncited act's row carries `dv_year` and `dv_number` EMPTY: the issue in a candidate `id_mat` belongs to the material, never to the row. The `unattributed_material` rows are the mirror image, carrying the material's issue and an empty `law_id` (`dv_coverage_map.py:849-852`).

**Interfaces:**
- The key is the five identifying columns, compared as strings after stripping: `(kind, law_id, dv_year, dv_number, title)`. For an uncited act the two issue columns are empty, so the key is in effect `(kind, law_id, title)`; for an unattributed material `law_id` is empty, so it is in effect `(kind, dv_year, dv_number, title)`. One rule covers both, defined on what the file actually holds. If two rows share a key the applier exits non-zero naming them, so a record can never land on the wrong row.
- The file is a list of records, one per unresolved row:

```yaml
- kind: promulgation_unknown   # the `kind` of the unresolved.csv row
  law_id: naredba-za-primer    # the row's law_id, or '' for a material row
  dv_year: ''                  # the ROW's issue columns, empty for an uncited act
  dv_number: ''
  title: НАРЕДБА ЗА ПРИМЕР     # the row's title column, part of the key
  id_mat: 55                   # the material the reasoning settled on, or null
  material_year: 2011          # that material's issue, recorded for the reviewer;
  material_number: 5           # not part of the key
  verdict: resolved            # resolved | no_target | unresolvable
  reason: >-
    The material title matches the act title exactly and its section is
    Министерство на финансите, which is the issuing body the act names.
```

- The applier is deterministic and total: for `verdict: resolved` the row leaves `unresolved.csv` and its attribution is written into `coverage-map.csv` with `resolver_flags` carrying `reasoned`; for `no_target` the row leaves `unresolved.csv` and is counted in `report.md` as settled with no corpus target; for `unresolvable` the row stays in `unresolved.csv` with the uncertainty `operation_unresolved`. A record naming a row that is not in `unresolved.csv` is an error, not a silent skip, so the file cannot rot.

**What this task does NOT close, stated because design 5.2 names a number that looks like it.** `segmenter-residue.csv` is written by the body pass of Task A2 and only when `--cache-dir` is given, so it does not exist until the gated run of A4 Step 4. A5 reads it **if it is there**, purely to report: `report.md` gains the residue row count next to the resolution counts, labelled as the P2 exit-gate number that this task does not close. A5's own number is the count of `unresolved.csv` rows with no record at all. Clearing residue to zero is the reasoning pass over instruction targets, which is P2 work on a file with a different shape (`RESIDUE_FIELDS = ["id_mat", "dv_year", "dv_number", "paragraph", "text"]`, no `kind` and no `law_id`), and inventing half of it here would leave an untested applier branch behind.

- [ ] **Step 1: Write the failing test**

```python
# tests/scripts/test_dv_coverage_map_resolutions.py
import csv
from pathlib import Path

import yaml

from scripts.dv_coverage_map import main

# The row this fixture produces is `kind=promulgation_unknown`,
# `law_id=naredba-za-primer`, `dv_year=''`, `dv_number=''`,
# `title=НАРЕДБА ЗА ПРИМЕР`. The record's key columns are those, not the
# candidate material's issue, which travels in material_year/material_number.
ROW_KEY = {"kind": "promulgation_unknown", "law_id": "naredba-za-primer",
           "dv_year": "", "dv_number": "", "title": "НАРЕДБА ЗА ПРИМЕР"}


def _resolutions(tmp_path: Path, record: dict) -> Path:
    res = tmp_path / "resolutions.yaml"
    res.write_text(yaml.safe_dump([record], allow_unicode=True, sort_keys=False),
                   encoding="utf-8")
    return res


def test_a_resolved_record_moves_the_row_out_of_unresolved(tmp_path: Path, uncited_corpus):
    corpus, issues, materials = uncited_corpus
    res = _resolutions(tmp_path, {**ROW_KEY, "id_mat": 55, "material_year": 2011,
                                  "material_number": 5, "verdict": "resolved",
                                  "reason": "title and issuing section both match"})
    out = tmp_path / "out"
    assert main(["--corpus", str(corpus), "--issues", str(issues), "--materials", str(materials),
                 "--resolutions", str(res), "--out", str(out)]) == 0
    unresolved = list(csv.DictReader((out / "unresolved.csv").open(encoding="utf-8")))
    assert not [r for r in unresolved
                if r["law_id"] == "naredba-za-primer" and r["kind"] == "promulgation_unknown"]
    coverage = [r for r in csv.DictReader((out / "coverage-map.csv").open(encoding="utf-8"))
                if r["law_id"] == "naredba-za-primer"]
    assert coverage and coverage[0]["locator_id_mat"] == "55"
    assert "reasoned" in coverage[0]["resolver_flags"]


def test_an_unresolvable_record_keeps_the_row_and_flags_it(tmp_path: Path, uncited_corpus):
    corpus, issues, materials = uncited_corpus
    res = _resolutions(tmp_path, {**ROW_KEY, "id_mat": None, "material_year": None,
                                  "material_number": None, "verdict": "unresolvable",
                                  "reason": "three ministries issued наредби № 3 that year"})
    out = tmp_path / "out"
    assert main(["--corpus", str(corpus), "--issues", str(issues), "--materials", str(materials),
                 "--resolutions", str(res), "--out", str(out)]) == 0
    row = next(r for r in csv.DictReader((out / "unresolved.csv").open(encoding="utf-8"))
               if r["law_id"] == "naredba-za-primer")
    assert "operation_unresolved" in row["resolver_flags"]


def test_a_record_for_a_row_that_does_not_exist_is_an_error(tmp_path: Path, uncited_corpus):
    corpus, issues, materials = uncited_corpus
    res = _resolutions(tmp_path, {**ROW_KEY, "law_id": "gone", "id_mat": 55,
                                  "verdict": "resolved", "reason": "x"})
    out = tmp_path / "out"
    assert main(["--corpus", str(corpus), "--issues", str(issues), "--materials", str(materials),
                 "--resolutions", str(res), "--out", str(out)]) != 0


def test_a_record_keyed_on_the_material_issue_instead_of_the_row_is_an_error(
        tmp_path: Path, uncited_corpus):
    """The defect this key exists to prevent: 2011/5 is the CANDIDATE's issue,
    and the row it targets carries neither column."""
    corpus, issues, materials = uncited_corpus
    res = _resolutions(tmp_path, {**ROW_KEY, "dv_year": 2011, "dv_number": 5,
                                  "id_mat": 55, "verdict": "resolved", "reason": "x"})
    out = tmp_path / "out"
    assert main(["--corpus", str(corpus), "--issues", str(issues), "--materials", str(materials),
                 "--resolutions", str(res), "--out", str(out)]) != 0
```

- [ ] **Step 2: Run them and confirm they fail**

Run: `.venv/bin/python -m pytest -q -p no:cacheprovider tests/scripts/test_dv_coverage_map_resolutions.py`
Expected: FAIL (unknown argument `--resolutions`).

- [ ] **Step 3: Implement the applier**

Load the YAML, key every record on `(kind, law_id, dv_year, dv_number, title)` with every part stripped and compared as a string, and apply it after the unresolved rows are built and before they are written. Unmatched records raise and exit non-zero with the list; two rows sharing a key is the same error. `report.md` gains a line: records applied by verdict, and the count of unresolved rows with no record at all, which is A5's exit number. If `segmenter-residue.csv` exists in the output directory from a previous body pass, add its row count on the next line, labelled as the P2 exit gate this task does not close.

- [ ] **Step 4: The reasoning procedure (orchestration, not code)**

For each unresolved row, in descending order of how many acts it blocks: read the candidate materials with `python -m fetcher.dv material --id-mat M --cache-dir data/dv/cache`, compare the material title, issuing section and date against the act, and write one record with the verdict and a reason a reviewer can check. The reason is prose, one or two sentences, naming what decided it. Batch the records into `resolutions.yaml` and re-run the map: the file is the cache, so the reasoning is done once and every later run replays it.

- [ ] **Step 5: Commit**

```bash
git add scripts/dv_coverage_map.py tests/scripts/test_dv_coverage_map_resolutions.py docs/research/2026-09-05-dv-coverage-map/resolutions.yaml
git commit -m "feat(coverage-map): reasoning-pass resolutions file and its deterministic applier (D-055 shape)"
```


---

# Part B: P1 (provenance block, exposure, § addressing, Gazette parser, pilot)

### Task B0: `corpus_commit`, the one place the three trailers are written

`refresh._git_commit_typed` hardcodes two of the three mandatory trailers:

```python
    msg = (f"[{commit_type}] {title}\n\n"
           f"Source-Id: lexbg-{doc_id}\n"
           f"Source-Date: {date if date else 'unknown'}\n"
           f"Norm-Id: {doc_id}\n")
```

Its docstring says why (`Source-Id stays lexbg-{doc_id} because this coarse pass re-pulls from lex.bg`), and that reasoning is sound for `refresh.py`. It is wrong for everything this plan commits: B6 needs `Source-Id: dvmap-2026-09`, B10 needs `Source-Id: dv-<idMat>` with `Norm-Id: <identificador>`, and B11 Step 3 asserts exactly those lines. Rather than growing keyword arguments on a lex.bg-specific helper, the trailer format gets its own module and `refresh.py` becomes one of its callers.

**Files:**
- Create: `corpus_commit/__init__.py`, `tests/test_corpus_commit.py`
- Modify: `refresh.py` (`_git_commit_typed` becomes a thin wrapper), `pyproject.toml` (`corpus_commit*` in the include list, with B2's packaging paragraph)

**A package directory, not a bare `corpus_commit.py`.** `pyproject.toml` ships code through `[tool.setuptools.packages.find]` alone (quoted in B2's Packaging paragraph), and that directive finds directories with an `__init__.py`; a single-module `corpus_commit.py` needs a `py-modules` list the repository does not have. B10's `fetcher/dv/rebuild.py` is inside the packaged `fetcher` tree and imports this module, so a bare module would ship a `fetcher.dv.rebuild` that cannot import. The import stays `from corpus_commit import commit_corpus_change` either way.

**Interfaces:**
- Produces `commit_corpus_change(path, commit_type, title, *, norm_id, source_id, source_date, cwd) -> bool` writing

```
[<commit_type>] <title>

Source-Id: <source_id>
Source-Date: <source_date or 'unknown'>
Norm-Id: <norm_id>
```

  keeping every behaviour `_git_commit_typed` already has: `commit_type` validated against `COMMIT_TYPES`, `git add` of the path relative to `cwd`, the resume-idempotency skip when nothing is staged (returns `False`), `GIT_AUTHOR_DATE` set to the legislative date while `GIT_COMMITTER_DATE` is left alone (D-048).
- `refresh._git_commit_typed(filepath, commit_type, title, doc_id, date, cwd)` keeps its signature and calls `commit_corpus_change(..., norm_id=str(doc_id), source_id=f"lexbg-{doc_id}", source_date=date, cwd=cwd)`. No caller of `refresh.py` changes.
- B6 and B10 call `commit_corpus_change` directly.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_corpus_commit.py
import subprocess
from pathlib import Path
import pytest
from corpus_commit import commit_corpus_change


def _repo(tmp_path: Path) -> Path:
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "t@t"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=tmp_path, check=True)
    (tmp_path / "laws").mkdir()
    return tmp_path


def _message(cwd: Path) -> str:
    return subprocess.run(["git", "log", "-1", "--format=%B"], cwd=cwd,
                          capture_output=True, text=True, check=True).stdout


def test_the_three_trailers_are_whatever_the_caller_says(tmp_path: Path):
    repo = _repo(tmp_path)
    target = repo / "laws" / "zot.md"
    target.write_text("**Чл. 1.** Текст.\n", encoding="utf-8")
    assert commit_corpus_change(target, "popravka", "ЗАКОН ЗА ОБЩЕСТВЕНИЯ ТРАНСПОРТ",
                                norm_id="2137259781", source_id="dv-242220",
                                source_date="2026-04-01", cwd=repo) is True
    msg = _message(repo)
    assert msg.startswith("[popravka] ЗАКОН ЗА ОБЩЕСТВЕНИЯ ТРАНСПОРТ")
    assert "\nSource-Id: dv-242220\n" in msg
    assert "\nSource-Date: 2026-04-01\n" in msg
    assert "\nNorm-Id: 2137259781\n" in msg


def test_a_missing_date_reads_unknown(tmp_path: Path):
    repo = _repo(tmp_path)
    target = repo / "laws" / "a.md"; target.write_text("x\n", encoding="utf-8")
    commit_corpus_change(target, "nova", "X", norm_id="1", source_id="dvmap-2026-09",
                         source_date=None, cwd=repo)
    assert "\nSource-Date: unknown\n" in _message(repo)


def test_an_unchanged_file_makes_no_second_commit(tmp_path: Path):
    repo = _repo(tmp_path)
    target = repo / "laws" / "a.md"; target.write_text("x\n", encoding="utf-8")
    commit_corpus_change(target, "nova", "X", norm_id="1", source_id="s", source_date=None, cwd=repo)
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=repo, capture_output=True,
                          text=True, check=True).stdout
    assert commit_corpus_change(target, "nova", "X", norm_id="1", source_id="s",
                                source_date=None, cwd=repo) is False
    assert subprocess.run(["git", "rev-parse", "HEAD"], cwd=repo, capture_output=True,
                          text=True, check=True).stdout == head


def test_an_unknown_commit_type_raises(tmp_path: Path):
    repo = _repo(tmp_path)
    target = repo / "laws" / "a.md"; target.write_text("x\n", encoding="utf-8")
    with pytest.raises(ValueError):
        commit_corpus_change(target, "invented", "X", norm_id="1", source_id="s",
                             source_date=None, cwd=repo)


def test_refresh_still_writes_the_lexbg_form(tmp_path: Path):
    from refresh import _git_commit_typed
    repo = _repo(tmp_path)
    target = repo / "laws" / "a.md"; target.write_text("x\n", encoding="utf-8")
    _git_commit_typed(target, "reforma", "X", 2134680704, "2005-05-20", repo)
    msg = _message(repo)
    assert "\nSource-Id: lexbg-2134680704\n" in msg and "\nNorm-Id: 2134680704\n" in msg
```

- [ ] **Step 2: Run them and confirm they fail**

Run: `.venv/bin/python -m pytest -q -p no:cacheprovider tests/test_corpus_commit.py`
Expected: FAIL, `ModuleNotFoundError: No module named 'corpus_commit'`.

- [ ] **Step 3: Implement**

Move the body of `refresh._git_commit_typed` into `corpus_commit/__init__.py` as `commit_corpus_change`, parameterising `Source-Id` and `Norm-Id` and returning `True`/`False` for committed/skipped. `COMMIT_TYPES` moves with it (or is imported from where it lives; do not duplicate the tuple). `refresh._git_commit_typed` keeps its docstring, shortened to say that it is the lex.bg caller of the shared helper. Note the one signature change the move makes: `refresh._git_commit_typed` returns `None`, and the shared helper returns `bool`, which is what B6 and B10 need to tell a committed act from a resume skip.

Add `corpus_commit*` to the `include` list in the same commit and run the reachability test from B2's packaging paragraph if that task has already landed; otherwise B2 picks it up.

- [ ] **Step 4: Run the tests and the refresh suite**

Run: `.venv/bin/python -m pytest -q -p no:cacheprovider tests/test_corpus_commit.py tests/test_refresh.py`
Expected: all passed. `refresh.py`'s existing commit-format tests must pass unchanged; that is the proof the move was behaviour-preserving.

- [ ] **Step 5: Commit**

```bash
git add corpus_commit/ refresh.py pyproject.toml tests/test_corpus_commit.py
git commit -m "refactor(commits): one module writes the Source-Id, Source-Date and Norm-Id trailers; refresh becomes its lex.bg caller"
```

### Task B1: the four IMPLEMENTATION-PREFLIGHT records

No code. Four files following the existing pattern (`docs/process/IMPLEMENTATION-PREFLIGHT-2026-07-21-fr032-per-article-fts.md`): Restatement (authoritative source, hard constraint, what counts as violation, allowed scope, protected files touched, waiver required) and Evidence (governing spec, related directive, related coverage floor, follow-up). Owner sign-off is the merge of the PR that carries them; Tasks B4, B5, B5b, B7 and B10 may not start before that merge.

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
    chain_scanned_through: null   # {issue, year} or null: an ISSUE, no date
    chain_inherited_before: '2005-01-01'
    uncertainty: []           # design 4.1; `promulgation_unknown` for the 121
  checked_through: {issue: '32', year: 2026, date: '2026-04-01'}
  in_force_as_of: '2026-04-16'
  events_not_in_force: 0
  events_pending: 0
  pending_items: [chain scan incomplete, base not audited, snapshot not frozen]
  pdf_pages_estimate: 0
  status: consolidated text without official value; Държавен вестник prevails on any discrepancy
```
`pending_items` carries the canonical strings of `provenance.derive` verbatim, in the order the procedure produced them, because design 4.2 rule 3 says the pending items are enumerated in the record and the index stores only the count.
and per row of `amendment_history`: `source`, `locator`, `applied` (`replayed | verified | not_incorporated | pending`), `verified_against` (text hash or null), `uncertainty` (list). What counts as violation: any act without the block after Task B6 (the floor's omission list), a grade not derivable from the recorded states (INV-010), a `fuente` that disagrees with `base.state`. Allowed scope: additive, backfilled corpus-wide in one batch by B6; `identificador = dv-<idMat>` for acts with no lex.bg document (D-064). Waiver: none.

Two definitions the preflight states in these words, because both are load-bearing and both were ambiguous in the design:

- **`checked_through` is the scan currency mark for this act**: the last Gazette issue whose materials the coverage map has attributed to it. It is NOT the date of the last amendment; `ultima_actualizacion` keeps that meaning. This is what makes `chain_scan_complete` (`base.chain_scanned_through == checked_through`) decidable for an act last amended in 2011 whose scan ran through 2026, and for a freshly rebuilt act the two values are equal by construction.

  **The two marks have two shapes and the comparison is on two keys, and this record is where that is fixed.** The block stores `base.chain_scanned_through` as `{issue, year}`, because a scan mark is an issue and carries no publication date of its own, and `checked_through` as `{issue, year, date}`, because the currency statement served to a consumer needs a date. `chain_scan_complete` is therefore `(issue, year) == (issue, year)`; a whole-dict equality would be false for every act, including a correct one, and the C10 check would report `chain scan incomplete` against a block that recorded it complete. The INDEX projects only the date: `laws.checked_through` (migration 007) holds `checked_through.date`, which is what MCP, REST and the cf act payload serve, and `laws.chain_inherited_before` holds `base.chain_inherited_before`. The issue half of the mark lives in the block alone and is read from there by `checks/provenance.py`.
- **The promulgation row of `amendment_history` is the base, not an event.** The event multiset of design 4.2 is `amendment_history` minus the row whose `dv` equals `f"{base.issue}/{base.year}"`. The row itself stays in `amendment_history`, because FR-020 and `history()` read it; it is excluded only from the grade derivation. One helper, `provenance.model.events_of(fm, base)`, implements the filter for every caller.

- [ ] **Step 2: Surface 4, the schema.** Migration 007: `ALTER TABLE laws ADD COLUMN provenance_grade TEXT`, `ADD COLUMN events_pending INTEGER NOT NULL DEFAULT 0`, `ADD COLUMN checked_through TEXT`, `ADD COLUMN chain_inherited_before TEXT`; new table `amendment_events(law_id TEXT REFERENCES laws(law_id), seq INTEGER, dv TEXT, date TEXT, source TEXT, locator TEXT, applied TEXT, verified_against TEXT, uncertainty TEXT, PRIMARY KEY(law_id, seq))`. Migration 008 (Task B7): `ALTER TABLE provisions ADD COLUMN kind TEXT NOT NULL DEFAULT 'article'`, `ADD COLUMN section_ref TEXT` and an index on `(law_id, article, kind, section_ref)`. Violation: any consumer query that breaks on the added columns; a `provisions` row whose `kind` is not in the enumerated set; two `para_amending` rows on one act sharing `(article, section_ref)`. Allowed scope: additive columns with defaults; full rebuild path unchanged.

- [ ] **Step 3: Surface 3, the tools.** Additive fields on `get_law` (`provenance_grade`, `checked_through`, `chain_inherited_before`) and on search hits (`provenance_grade`); one new warning code `PROVENANCE_GRADE` (category `warning`, raised by `get_law`, `get_article`, `get_articles`, `search`) with payload `grade`, `pending_items`, `checked_through`, `chain_inherited_before`; the address grammar of `get_article`/`get_articles` accepts `§ N`, `§N`, `§ N.` and `пар. N` (Task B7) and resolves them by section context. `tools.json` 1.5.0 → 1.6.0, `error-codes.json` and `.md` 1.5.0 → 1.6.0, REST OpenAPI regenerated. Violation: any removed or retyped field; a warning that fails to ride on a grade other than A.

  Two rules this preflight settles rather than leaving to the implementer:

  - **A new error code, not a widened one.** `AMBIGUOUS_NAME` is documented as „this law name matches N acts“. Reusing it for an ambiguous article address makes the wire code lie to a caller that switches on it. Add `AMBIGUOUS_ARTICLE_SPEC` to `ERROR_CODES` and to `docs/api/error-codes.{json,md}` in this same version bump, with payload `candidates: [{article, kind, section_ref, text_head}]`.
  - **The warning on `search` carries the weakest grade.** A search response holds hits from many acts with different grades, so one response-level warning cannot carry one act's currency. The rule: emit a single `PROVENANCE_GRADE` warning whose `grade` is the weakest among the hits (order `A` < `B` < `B-pending` < `C`, weakest last), with `checked_through` and `chain_inherited_before` set to null, and rely on the per-hit `provenance_grade` for detail. B5 adds a test with two hits of different grades.

- [ ] **Step 4: Surface 5, Gazette-sourced commits.** Proposal for ratification: a rebuild that replaces a lex.bg snapshot with the Gazette text is `[popravka]` (a correction of our copy, not a legislative event; FR-020 excludes `[popravka]` from version boundaries, which is the desired effect since the act's legislative history did not change); a first Gazette-sourced promulgation of an act absent from lex.bg is `[nova]`; a replayed amendment is `[reforma]` (engine, later); the provenance backfill of B6 is `[popravka]` per act with `Source-Id: dvmap-2026-09` and `Source-Date` the run date. `Source-Id: dv-<idMat>` for any commit whose text comes from a Gazette material; `Source-Date` the issue date; `Norm-Id` the act's `identificador` (`dv-<idMat>` for ДВ-only acts). Violation: a corpus commit without the three trailers, or a `[reforma]` without an applied text change.

  **The implementing surface is `corpus_commit.commit_corpus_change` (Task B0), the one place the three trailers are written.** `refresh._git_commit_typed` hardcodes `Source-Id: lexbg-{doc_id}` and `Norm-Id: {doc_id}`, which is correct for its own coarse lex.bg pass and cannot express any of the forms above; B0 moves the format into a shared module and leaves `refresh.py` as one of its callers. Naming the module here is part of the preflight, because a second writer of the trailer format would be exactly the Surface 5 drift this record exists to prevent.

- [ ] **Step 5: Commit**

```bash
git add docs/process/IMPLEMENTATION-PREFLIGHT-2026-09-06-*.md docs/data/schema-reference.md
git commit -m "docs(preflight): Surfaces 2, 3, 4 and 5 for the provenance block, exposure, § addressing and Gazette commits"
```

### Task B2: the `provenance` package (model and total derivation)

**Files:**
- Create: `provenance/__init__.py`, `provenance/model.py`, `provenance/derive.py`
- Modify: `pyproject.toml` (packaging, see below), `tests/test_packaging.py`
- Modify (Step 6): `scripts/dv_coverage_map.py`, `tests/scripts/test_dv_coverage_map.py`
- Test: `tests/provenance/test_derive.py`, `tests/provenance/test_model.py`

**Interfaces:**
- Produces: `Base(source, state, locator, issue, year, frozen_at, audited, declared_at, chain_scanned_through, chain_inherited_before, uncertainty)` with the property `Base.promulgation_cited`, `Event(dv, date, source, locator, applied, verified_against, uncertainty)`, `Provenance(grade, derived_at, base, events, checked_through, in_force_as_of, events_not_in_force, events_pending, pdf_pages_estimate, status)` with `to_frontmatter() -> dict` and `Provenance.from_frontmatter(fm: dict) -> Provenance | None`; **`events_of(fm: dict, base: Base) -> list[Event]`**, the one filter that turns `amendment_history` into the event multiset of design 4.2; `derive_grade(base: Base, events: list[Event], *, chain_scan_complete: bool, divergences_unadjudicated: int, promulgation_cited: bool = True) -> Derivation(grade: str | None, pending_items: list[str])` where `grade None` means staging (rule 0); `DomainError` for inputs outside the constraints of design 4.2; `EVENT_SOURCES`, `EVENT_APPLIED`, `BASE_STATES`, `GRADES` tuples.
- **The canonical `pending_items` vocabulary**, used by every consumer including the coverage map: `events pending: N`, `chain scan incomplete`, `promulgation unlocated`, `promulgation unknown`, `base not audited`, `snapshot not frozen`, `events before declared base not carried: N`, `witness divergences unadjudicated`. No second vocabulary exists after Step 6.

**Packaging.** The current declaration, read off `origin/main`:

```toml
# as in pyproject.toml:36-38
[tool.setuptools.packages.find]
include = ["fetcher*", "index*", "mcp_server*", "api*"]
exclude = ["tests*", "scripts*", "research*", "docs*"]
```

`packages.find` finds PACKAGES, that is, directories carrying an `__init__.py`. It cannot ship a bare top-level module however it is patterned, which is why Task B0 creates `corpus_commit/__init__.py` rather than `corpus_commit.py`: the repository ships nothing through `py-modules` today and adding that second mechanism for one function is the weaker trade. `corpus_integrity/` on `feat/corpus-integrity-floor` is already a package (`corpus_integrity/__init__.py`), and `corpus_gate` will be one or the other depending on how PR #23 Part II Task 6 lands.

This task adds a top-level `provenance/`, B3 extends `corpus_integrity/`, B0 adds `corpus_commit/`, B9 puts `import provenance...` inside `fetcher/dv/metadata.py` and B10 puts `from corpus_commit import ...` and `from corpus_gate import ...` inside `fetcher/dv/rebuild.py`; all three of those files are inside the packaged `fetcher` tree. A `pip install .` or the Docker image would therefore ship a `fetcher` that cannot import. The exact change:

```toml
[tool.setuptools.packages.find]
include = ["fetcher*", "index*", "mcp_server*", "api*", "provenance*",
           "corpus_integrity*", "corpus_gate*", "corpus_commit*"]
exclude = ["tests*", "scripts*", "research*", "docs*"]
```

`tests/test_packaging.py` today holds two tests (`test_console_entry_target_is_importable_and_callable` and `test_pyproject_declares_console_script_and_build_system`) over `REPO = pathlib.Path(__file__).resolve().parents[1]`, neither of which can catch this. Add two more:

- **The reachability test, which is the one that has to carry the guarantee.** Walk every top-level package the `include` patterns actually match, parse each `.py` with `ast`, collect the top-level name of every absolute `import`/`from` statement, keep the names that resolve to something in the repository root (a directory with an `__init__.py`, or a `*.py` file), and assert each of them is itself shipped, that is, matched by an `include` pattern or listed in `[tool.setuptools] py-modules` if that key ever appears. This is falsifiable against the defect: a shipped `fetcher.dv.rebuild` importing an unshipped `corpus_commit` fails it. Verified against `origin/main` as written: the four shipped packages import no unshipped local name, so the test is green the day it lands. It deliberately says nothing about `export_cf/`, `bootstrap.py` and `refresh.py`, which are top-level and unshipped today; nothing shipped imports them, so they are operator entry points rather than a packaging defect, and a test that failed on them would be reverted rather than fixed.
- **The wheel test, guarded.** `pytest.importorskip("setuptools")` first, then copy `pyproject.toml` and each matched top-level package directory into `tmp_path`, run `pip wheel --no-deps --no-build-isolation` into it, and assert the built wheel's namelist carries `provenance/derive.py` and `corpus_commit/__init__.py`. **This test skips in the current `.venv`, which has no `setuptools`**, so it is a bonus check for the CI install job and not the guarantee; do not let it stand in for the first test.

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

def test_a_grade_c_act_still_enumerates_its_open_items():
    """§4.2 rule 1 and COVERAGE-FLOOR.md: a grade C act's online events are still
    sourced and verified as for B and the pending counter still applies, so its
    record names the same open items a B-pending act's would."""
    b = _base(source="dv_offline", frozen_at=None, audited=False)
    d = derive_grade(b, [_ev(applied="pending")], chain_scan_complete=False, divergences_unadjudicated=0)
    assert d.grade == "C"
    assert "events pending: 1" in d.pending_items
    assert "chain scan incomplete" in d.pending_items
    assert "snapshot not frozen" in d.pending_items

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

def test_a_promulgation_never_cited_is_told_apart_from_one_not_found():
    """Design 4.2 rule 3 distinguishes the two; the 121 acts are the second kind."""
    b = _base(source="unlocated", frozen_at=None, audited=False)
    cited = derive_grade(b, [], chain_scan_complete=False, divergences_unadjudicated=0)
    uncited = derive_grade(b, [], chain_scan_complete=False, divergences_unadjudicated=0,
                           promulgation_cited=False)
    assert "promulgation unlocated" in cited.pending_items
    assert "promulgation unknown" in uncited.pending_items
    assert "promulgation unlocated" not in uncited.pending_items

def test_declared_base_excludes_older_events():
    b = _base(source="dv_pdf", year=1995, issue="10", frozen_at="2026-09-06", audited=True, declared_at="2005-01-01")
    d = derive_grade(b, [_ev(dv="3/1998", date="1998-01-10", source="dv_pdf", applied="pending"), _ev(dv="7/2010", applied="verified")],
                     chain_scan_complete=True, divergences_unadjudicated=0)
    assert d.grade == "B" and "events before declared base not carried: 1" in d.pending_items

def test_declared_base_compares_days_not_years():
    """Design 4.2 says „events dated before base.declared_at“, so an event in
    the declared year but before the declared day is not carried either."""
    b = _base(source="dv_pdf", year=1995, issue="10", frozen_at="2026-09-06", audited=True,
              declared_at="2005-06-01")
    d = derive_grade(b, [_ev(dv="4/2005", date="2005-01-14", source="dv_pdf", applied="pending")],
                     chain_scan_complete=True, divergences_unadjudicated=0)
    assert d.grade == "B" and "events before declared base not carried: 1" in d.pending_items

def test_two_identical_events_one_older_are_counted_once_each():
    """Value equality on a non-frozen dataclass must not over-remove: the
    excluded set is chosen by index, so the note's count and the in-scope
    multiset always agree."""
    b = _base(source="dv_pdf", year=1995, issue="10", frozen_at="2026-09-06", audited=True,
              declared_at="2005-01-01")
    old = _ev(dv="3/1998", date="1998-01-10", source="dv_pdf", applied="pending")
    same_but_recent = _ev(dv="3/1998", date="2010-01-10", source="dv_pdf", applied="pending")
    d = derive_grade(b, [old, same_but_recent], chain_scan_complete=True, divergences_unadjudicated=0)
    assert "events before declared base not carried: 1" in d.pending_items
    assert "events pending: 1" in d.pending_items, "the recent twin is still in scope and still pending"
    assert d.grade == "B-pending"

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

```python
# tests/provenance/test_model.py
from provenance.derive import derive_grade
from provenance.model import Base, Provenance, events_of

BASE = {"source": "dv_html", "state": "rebuilt", "locator": {"id_mat": 242220},
        "issue": "32", "year": 2026, "frozen_at": "2026-09-06", "audited": True,
        "declared_at": None, "chain_scanned_through": {"issue": "81", "year": 2026},
        "chain_inherited_before": None}


def _fm(history):
    return {
        "amendment_history": history,
        "provenance": {"grade": "A", "derived_at": "2026-09-06", "base": BASE,
                       "checked_through": {"issue": "81", "year": 2026, "date": "2026-09-04"},
                       "in_force_as_of": "2026-04-16", "events_not_in_force": 0,
                       "events_pending": 0, "pdf_pages_estimate": 0, "status": "x"},
    }


def test_the_promulgation_row_is_the_base_not_an_event():
    """Design 4.1: the base of the act carries its own record."""
    fm = _fm([{"dv": "32/2026", "date": "2026-04-01"}, {"dv": "70/2026", "date": "2026-08-01"}])
    assert [e.dv for e in events_of(fm, Base(**BASE))] == ["70/2026"]
    assert [e.dv for e in Provenance.from_frontmatter(fm).events] == ["70/2026"]


def test_a_single_issue_act_rebuilt_from_the_gazette_derives_a():
    """The pinning test: without the base filter this act is B-pending on its
    own promulgation and the pilot can never reach grade A."""
    fm = _fm([{"dv": "32/2026", "date": "2026-04-01"}])
    prov = Provenance.from_frontmatter(fm)
    assert prov.events == []
    d = derive_grade(prov.base, prov.events, chain_scan_complete=True, divergences_unadjudicated=0)
    assert d.grade == "A" and d.pending_items == []


def test_an_act_whose_base_issue_is_unknown_keeps_every_row_as_an_event():
    """base.issue null (the 121 uncited acts): nothing can be identified as the
    promulgation, so nothing is filtered out."""
    base = {**BASE, "source": "unlocated", "state": "snapshot", "issue": None, "year": None,
            "frozen_at": None, "audited": False, "locator": None}
    fm = {"amendment_history": [{"dv": "5/2011", "date": "2011-01-18"}],
          "provenance": {**_fm([])["provenance"], "base": base, "grade": "B-pending"}}
    assert [e.dv for e in events_of(fm, Base(**base))] == ["5/2011"]


def test_a_leading_zero_in_the_history_row_still_matches_the_base():
    """The corpus writes the issue both ways; a string comparison would count
    the act's own promulgation as a pending event."""
    base = {**BASE, "issue": "32", "year": 1999}
    fm = {"amendment_history": [{"dv": "032/1999", "date": "1999-09-14"},
                                {"dv": "70/2005", "date": "2005-08-26"}],
          "provenance": {**_fm([])["provenance"], "base": base}}
    assert [e.dv for e in events_of(fm, Base(**base))] == ["70/2005"]


def test_a_second_row_on_the_promulgation_issue_stays_an_event():
    """A corrigendum published in the same брой is an event, not the base. Only
    the FIRST matching row is the promulgation."""
    fm = _fm([{"dv": "32/2026", "date": "2026-04-01"},
              {"dv": "32/2026", "date": "2026-04-08"},
              {"dv": "70/2026", "date": "2026-08-01"}])
    assert [e.date for e in events_of(fm, Base(**BASE))] == ["2026-04-08", "2026-08-01"]


def test_the_recorded_pending_items_survive_a_round_trip():
    """`to_frontmatter` writes them, so `from_frontmatter` must read them back."""
    fm = _fm([{"dv": "32/2026", "date": "2026-04-01"}])
    fm["provenance"]["pending_items"] = ["chain scan incomplete", "snapshot not frozen"]
    prov = Provenance.from_frontmatter(fm)
    assert prov.pending_items == ["chain scan incomplete", "snapshot not frozen"]
    assert prov.to_frontmatter()["pending_items"] == prov.pending_items
```

- [ ] **Step 2: Run them and confirm they fail**

Run: `.venv/bin/python -m pytest -q -p no:cacheprovider tests/provenance`
Expected: FAIL, `ModuleNotFoundError: No module named 'provenance'`

- [ ] **Step 3: Implement the model and the derivation**

```python
# provenance/model.py
"""Provenance data model of the graded source model (design 4.1, D-059).

Two definitions this module owns, because every consumer must read them the
same way.

`checked_through` is the SCAN CURRENCY MARK for one act: the last Gazette
issue whose materials the coverage map attributed to it. It is not the date
of the last amendment, which is `ultima_actualizacion`. That is what makes
`chain_scan_complete` („base.chain_scanned_through == checked_through“)
decidable for an act last amended in 2011 whose scan ran through 2026.

The PROMULGATION ROW of `amendment_history` is the base, not an event. The
event multiset of §4.2 is the history minus the row whose `dv` reads
„<base.issue>/<base.year>“. The row stays in `amendment_history`, because
FR-020 and `history()` read it; it is excluded only from the derivation.
`events_of` is the single implementation of that filter.
"""
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
    # Design 4.1: the base carries the same uncertainty vocabulary its events
    # do. `promulgation_unknown` is the flag that tells the 121 acts citing no
    # promulgation apart from a promulgation cited and not found; without it
    # persisted, `checks/provenance.py` cannot reproduce the derivation and
    # every such act would flatten into the wrong open item.
    uncertainty: list[str] = field(default_factory=list)

    @property
    def promulgation_cited(self) -> bool:
        return "promulgation_unknown" not in (self.uncertainty or [])


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
    # §4.2 rule 3: „B-pending, with the pending items enumerated in the
    # record“. The index stores only the count, so the record is the one place
    # a reader learns WHY an act is B-pending.
    pending_items: list[str] = field(default_factory=list)

    def to_frontmatter(self) -> dict:
        d = {"grade": self.grade, "derived_at": self.derived_at, "base": asdict(self.base),
             "checked_through": self.checked_through, "in_force_as_of": self.in_force_as_of,
             "events_not_in_force": self.events_not_in_force, "events_pending": self.events_pending,
             "pending_items": list(self.pending_items),
             "pdf_pages_estimate": self.pdf_pages_estimate, "status": self.status}
        return d

    @classmethod
    def from_frontmatter(cls, fm: dict) -> "Provenance | None":
        blk = fm.get("provenance")
        if not blk:
            return None
        base = Base(**blk["base"])
        return cls(grade=blk.get("grade"), derived_at=str(blk.get("derived_at")), base=base,
                   events=events_of(fm, base), checked_through=blk.get("checked_through"),
                   in_force_as_of=blk.get("in_force_as_of"),
                   events_not_in_force=int(blk.get("events_not_in_force", 0)), events_pending=int(blk.get("events_pending", 0)),
                   pdf_pages_estimate=int(blk.get("pdf_pages_estimate", 0)), status=blk.get("status", STATUS_LINE),
                   # `to_frontmatter` writes the list, so the round trip has to
                   # read it back: `checks/provenance.py` reports the RECORDED
                   # items next to the ones it re-derives, and without this they
                   # would always read as empty.
                   pending_items=list(blk.get("pending_items") or []))


def _dv_key(dv) -> tuple[str, str] | None:
    """Normalise a Gazette citation to (issue, year) without leading zeros.

    Defensive: across the 8,097 `dv:` rows of the corpus none carries a leading zero today, but a
    Gazette-side row (a material header or a resolver result) might; both the base filter and the
    backfill join go through this key so the two paths can never disagree.
    """
    parts = str(dv or "").strip().split("/")
    if len(parts) != 2:
        return None
    issue, year = parts[0].strip(), parts[1].strip()
    return (issue.lstrip("0") or "0", year.lstrip("0") or "0")


def is_base_row(row: dict, base: Base) -> bool:
    """Whether this `amendment_history` row is the promulgation (design 4.1).

    An act whose base issue is unknown (the 121 that cite no promulgation)
    identifies nothing, so nothing is filtered: every row stays an event,
    which is the honest reading of „we do not know which one it was“.
    """
    if base.issue is None or base.year is None:
        return False
    key = _dv_key(row.get("dv"))
    return key is not None and key == _dv_key(f"{base.issue}/{base.year}")


def event_from_row(row: dict) -> Event:
    return Event(dv=str(row.get("dv")), date=row.get("date"),
                 source=row.get("source", "unlocated"), locator=row.get("locator"),
                 applied=row.get("applied", "pending"),
                 verified_against=row.get("verified_against"),
                 uncertainty=list(row.get("uncertainty") or []))


def events_of(fm: dict, base: Base) -> list[Event]:
    """The event multiset of §4.2: `amendment_history` minus the promulgation.

    THE one filter. `Provenance.from_frontmatter`, the backfill, the metadata
    builder and `checks/provenance.py` all call this and never rebuild it, so
    a single-issue act derives grade A instead of B-pending on its own
    promulgation.

    EXACTLY ONE row is removed: the FIRST that matches, in file order. An act
    can carry two rows on its promulgation issue, the promulgation and a
    corrigendum published in the same брой, and the second one is a real event
    that has to be sourced like any other. Filtering by predicate over the
    whole list would silently drop it and overstate the act's grade.
    """
    events: list[Event] = []
    taken = False
    for row in fm.get("amendment_history") or []:
        if not taken and is_base_row(row, base):
            taken = True
            continue
        events.append(event_from_row(row))
    return events
```

```python
# provenance/derive.py
"""The total grade derivation of design section 4.2 (D-059, D-064).

Ordered rules, first match decides. Inputs are the persisted base record, the
events and two computed values. Domain constraints raise DomainError so a
property test enumerates only possible states.

The open items are computed once, before the rules, and every grade carries
them: §4.2 rule 1 says a grade C act's online events are still sourced and
verified as for B and the pending counter still applies. Only rule 0 replaces
them, because a file held in staging is not in the corpus at all.
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


def _in_scope(base: Base, events: list[Event]) -> tuple[list[Event], str | None]:
    """Split off the events dated before a declared base date (design 4.2).

    Exclusion is BY INDEX, never by value: `Event` is not frozen, so two
    identical events where only one is older would remove both under `not in`
    and make the note's count disagree with the multiset. The comparison is on
    the full date, not the year: §4.2 says „events dated before
    base.declared_at“, so an event in the declared year but before the
    declared day is not carried either. An event with no date is given the
    last day of its year, the most generous reading, so an undated event is
    never dropped for a declaration made earlier that year.
    """
    if not base.declared_at:
        return list(events), None
    def _date(e: Event) -> str:
        return e.date or (f"{e.year}-12-31" if e.year is not None else "9999-12-31")
    older = [i for i, e in enumerate(events) if _date(e) < base.declared_at]
    if not older:
        return list(events), None
    kept = [e for i, e in enumerate(events) if i not in set(older)]
    return kept, f"events before declared base not carried: {len(older)}"


def derive_grade(base: Base, events: list[Event], *, chain_scan_complete: bool,
                 divergences_unadjudicated: int, promulgation_cited: bool = True) -> Derivation:
    """The grade of one act and the items still open on it.

    `events` is the multiset of §4.2, which the caller has already taken from
    `provenance.model.events_of`: the promulgation is the base, not an event.
    `promulgation_cited` tells the two unlocated cases apart: False is one of
    the 121 acts that cite no promulgation at all (`promulgation unknown`),
    True is a promulgation cited and not found (`promulgation unlocated`).
    """
    _check_domain(base, events, divergences_unadjudicated)
    pending: list[str] = []
    in_scope, declared_note = _in_scope(base, events)
    if declared_note:
        pending.append(declared_note)
    # THE OPEN ITEMS ARE COMPUTED THE SAME WAY WHATEVER THE GRADE, before any
    # rule fires. Design 4.2 rule 1 reads „C, pre-1989 base. Online events are
    # still sourced and verified as for B, and the pending counter applies“, and
    # COVERAGE-FLOOR.md's grade C definition repeats it. So a pre-1989 act keeps
    # `chain scan incomplete`, `base not audited` and `snapshot not frozen` in
    # its record; the items decide the GRADE only through rule 3.
    n_pending = sum(1 for e in in_scope if e.applied == "pending")
    if n_pending:
        pending.append(f"events pending: {n_pending}")
    if not chain_scan_complete:
        pending.append("chain scan incomplete")
    if base.source == "unlocated":
        pending.append("promulgation unlocated" if promulgation_cited else "promulgation unknown")
    online = base.source in ("dv_html", "dv_pdf")
    if base.state == "snapshot" and online and not base.audited:
        pending.append("base not audited")
    if base.state == "snapshot" and base.frozen_at is None:
        pending.append("snapshot not frozen")
    # rule 0: staging. The only rule that replaces the items rather than
    # carrying them: the file is not in the corpus, so nothing else is open yet.
    if base.state in ("rebuilt", "read") and divergences_unadjudicated > 0:
        return Derivation(None, ["witness divergences unadjudicated"])
    # rule 1: offline
    if base.source == "dv_offline" or any(e.source == "dv_offline" for e in in_scope):
        return Derivation("C", pending)
    # rule 2: ДВ-complete
    if (base.state == "rebuilt" and base.source == "dv_html" and chain_scan_complete
            and all(e.source == "dv_html" and e.applied in ("replayed", "not_incorporated") for e in in_scope)
            and divergences_unadjudicated == 0):
        return Derivation("A", pending)
    # rule 3: open items. The declared-base note is informational: it records a
    # decision the owner made, not an item still open, so it never by itself
    # forces B-pending. Tracked by identity rather than by re-deriving the
    # string, which is what made the earlier draft diverge from its own count.
    blocking = [p for p in pending if p != declared_note]
    if blocking:
        return Derivation("B-pending", pending)
    # rule 4
    return Derivation("B", pending)
```

Rule 2 can only be reached with `chain_scan_complete`, a `rebuilt` base and no pending event, so a grade A act carries at most the declared-base note; nothing else can be open under it.

- [ ] **Step 4: Run the tests and confirm they pass**

Run: `.venv/bin/python -m pytest -q -p no:cacheprovider tests/provenance tests/test_packaging.py -v`
Expected: all passed. The exhaustive test must report `seen > 500`. If `test_declared_base_excludes_older_events` fails, the rule-3 guard is not comparing against the note by identity: the declared-base note is informational and must not by itself force B-pending.

- [ ] **Step 5: Commit the package**

```bash
git add provenance/ tests/provenance/ pyproject.toml tests/test_packaging.py
git commit -m "feat(provenance): data model and the total grade derivation of design 4.2 with domain constraints and an exhaustive test"
```

- [ ] **Step 6: Delete the coverage map's second derivation and import this one**

`scripts/dv_coverage_map.py` on `feat/dv-coverage-map` carries a complete `derive_grade(*, base_source, base_state, base_frozen_at, base_audited, chain_scan_complete, divergences_unadjudicated, events, promulgation_cited)` implementing rules 0 to 4, with its own snake_case pending vocabulary (`events_pending`, `chain_scan`, `promulgation_unlocated`, `promulgation_unknown`, `base_audit`, `freeze`). Two implementations of the canonical procedure is the C10 / INV-010 hazard the design names, and `docs/process/COVERAGE-FLOOR.md` requires it implemented once and property-tested. It also means the backfill would read a `pending_items` string produced by one implementation into a block whose grade is derived by the other.

Delete the map's copy. Import `from provenance.derive import derive_grade` and `from provenance.model import Base, Event`, and adapt the single call site: the map already knows every input, so it builds a `Base` and a list of `Event` (source and applied per event row, promulgation excluded, which the map already separates with `row_kind = base`) and reads `Derivation.grade` and `Derivation.pending_items`. `pending_items` is written to the CSV joined by `; `.

**The grade C question, decided against the authorities rather than left to the executor.** The merged `derive_grade` computes the open items for every grade and says why in its docstring; the draft of `provenance/derive.py` returned only the pending-event count from rule 1, which would have stripped `chain scan incomplete`, `base not audited` and `snapshot not frozen` from every pre-1989 act's CSV row and, after B6, from its frontmatter block. `docs/process/COVERAGE-FLOOR.md` (Provenance floor, grade C) settles it: „Every online event is still sourced and verified as for B, and the pending counter applies“, and design 4.2's rule 1 row says the same. **Decision: the open items are computed once for every grade, before the rules, exactly as the merged map does it.** The derivation above implements that, and it is why one of the three failing tests below turns green rather than needing an edit.

**The merged property tests must be rewritten, not merely re-stringed.** `tests/scripts/test_dv_coverage_map.py` on `feat/dv-coverage-map` carries a generator `valid_inputs(cmap)` and eight tests that call `cmap.derive_grade(**inputs)` with the map's keyword signature and unpack a `(grade, pending)` TUPLE. After this step `cmap.derive_grade` does not exist and the canonical one returns a `Derivation` dataclass, so every one of them needs an edit. Three fail on semantics rather than on call shape, and they are named here so the executor does not discover them as a red suite:

1. **`test_the_grade_procedure_is_total`** pins `assert count == 6352` „so that a change to the domain constraints is visible rather than silent“, and asserts `seen == {"A", "B", "B-pending", "C", "none"}`. Both change. `provenance.derive._check_domain` adds one constraint the merged `valid_inputs` does not filter, „an unlocated event is always pending“ (`e.source == "unlocated" and e.applied != "pending"`), which removes 1,936 of the 6,352 enumerated inputs. **The new pin is 4,416, and it is an expected change, not a regression:** the domain got smaller because a constraint the merged map only documented is now enforced. The staging grade is `None`, not the string `"none"`.
2. **`test_the_pending_items_come_from_the_fixed_vocabulary`** allows the six snake_case tokens (`events_pending`, `chain_scan`, `promulgation_unlocated`, `promulgation_unknown`, `base_audit`, `freeze`). The canonical vocabulary is the eight prose strings, two of which carry a count, so the membership test becomes exact-match against six plus a prefix test for the two counted ones.
3. **`test_the_p0_inputs_can_only_produce_b_pending_or_c`** asserts `pending` is non-empty for every P0 input, including `base_source="dv_offline"` with `events=()`. It fails against the draft where rule 1 returned only the pending-event count, and PASSES against the derivation above, where rule 1 carries the same items as rule 3. It is the test that pins the decision recorded in this step, so it is kept unchanged in substance.

`test_pending_items_are_named_exactly_when_something_is_open` keeps passing, because the enumeration sets no `declared_at` and so no grade A or B act can carry the declared-base note; its A/B assertion is widened anyway, so it stays true if the enumeration is ever extended.

Replace the whole derivation block of `tests/scripts/test_dv_coverage_map.py` (the `BASE_SOURCES` constant through `test_the_p0_inputs_can_only_produce_b_pending_or_c`) with this. The `outputs`-based tests above it are untouched.

```python
# tests/scripts/test_dv_coverage_map.py, the derivation block
# The map's own derive_grade is gone (Task B2 Step 6); these tests exercise the
# canonical one through the inputs §4.2 names, so the enumeration stays readable.
import itertools

import pytest

from provenance.derive import DomainError, derive_grade
from provenance.model import Base, Event

BASE_SOURCES = ("dv_html", "dv_pdf", "dv_offline", "unlocated")
BASE_STATES = ("rebuilt", "read", "snapshot")
EVENT_SOURCES = ("dv_html", "dv_pdf", "dv_offline", "unlocated")
APPLIED = ("replayed", "verified", "not_incorporated", "pending")

CANONICAL = {
    "chain scan incomplete",
    "promulgation unlocated",
    "promulgation unknown",
    "base not audited",
    "snapshot not frozen",
    "witness divergences unadjudicated",
}
COUNTED = ("events pending: ", "events before declared base not carried: ")


def _derive(*, base_source, base_state, base_frozen_at, base_audited,
            chain_scan_complete, divergences_unadjudicated, events):
    base = Base(source=base_source, state=base_state, locator=None, issue="32",
                year=2026, frozen_at=base_frozen_at, audited=base_audited,
                declared_at=None, chain_scanned_through=None,
                chain_inherited_before=None)
    evs = [Event(dv=f"{i + 1}/2010", date=f"2010-01-0{i + 1}", source=source,
                 locator=None, applied=applied, verified_against=None)
           for i, (source, applied) in enumerate(events)]
    return derive_grade(base, evs, chain_scan_complete=chain_scan_complete,
                        divergences_unadjudicated=divergences_unadjudicated)


def valid_inputs():
    """Every input of §4.2 that its domain constraints allow.

    `hypothesis` is not installed, and the input space is finite and small, so
    it is enumerated rather than sampled. The constraints §4.2 states as domain
    rather than as rules are filtered out here, which is what makes them
    constraints; `provenance.derive._check_domain` raises DomainError on every
    one of them, and the last filter is the one the map's own copy documented
    but never enforced.
    """
    pairs = [(source, applied) for source in EVENT_SOURCES for applied in APPLIED]
    multisets = [()]
    multisets += [(pair,) for pair in pairs]
    multisets += list(itertools.combinations_with_replacement(pairs, 2))

    for source, state, frozen, audited, scanned, divergences in itertools.product(
        BASE_SOURCES, BASE_STATES, (None, "2026-01-01"), (False, True),
        (False, True), (0, 1),
    ):
        if state == "rebuilt" and source != "dv_html":
            continue
        if state == "read" and source != "dv_pdf":
            continue
        if state in ("rebuilt", "read") and frozen is None:
            continue
        if state == "snapshot" and divergences != 0:
            continue
        for events in multisets:
            if state != "snapshot" and any(
                applied == "verified" for _, applied in events
            ):
                continue
            if any(event_source == "unlocated" and applied != "pending"
                   for event_source, applied in events):
                continue
            yield dict(
                base_source=source,
                base_state=state,
                base_frozen_at=frozen,
                base_audited=audited,
                chain_scan_complete=scanned,
                divergences_unadjudicated=divergences,
                events=events,
            )


def test_the_grade_procedure_is_total():
    seen = set()
    count = 0
    for inputs in valid_inputs():
        d = _derive(**inputs)
        assert d.grade in {None, "A", "B", "B-pending", "C"}
        assert isinstance(d.pending_items, list)
        seen.add(d.grade)
        count += 1
    # The exact size of the enumerated space, pinned so that a change to the
    # domain constraints is visible rather than silent. It was 6,352 against the
    # map's own copy; enforcing „an unlocated event is always pending“ removes
    # 1,936 impossible inputs.
    assert count == 4416
    assert seen == {None, "A", "B", "B-pending", "C"}


def test_every_input_the_enumeration_skips_is_a_domain_error():
    """The filters above are the domain, not a convenience: the derivation
    refuses the same inputs rather than grading them."""
    base = Base(source="dv_html", state="snapshot", locator=None, issue="32",
                year=2026, frozen_at="2026-01-01", audited=True,
                declared_at=None, chain_scanned_through=None,
                chain_inherited_before=None)
    ev = Event(dv="1/2010", date="2010-01-01", source="unlocated", locator=None,
               applied="replayed", verified_against=None)
    with pytest.raises(DomainError):
        derive_grade(base, [ev], chain_scan_complete=True,
                     divergences_unadjudicated=0)


def test_rule_zero_holds_a_rebuilt_act_out_of_the_corpus():
    for inputs in valid_inputs():
        if (
            inputs["base_state"] in ("rebuilt", "read")
            and inputs["divergences_unadjudicated"] > 0
        ):
            assert _derive(**inputs).grade is None


def test_anything_offline_in_scope_is_grade_c():
    for inputs in valid_inputs():
        d = _derive(**inputs)
        if d.grade is None:
            continue
        offline = inputs["base_source"] == "dv_offline" or any(
            source == "dv_offline" for source, _ in inputs["events"]
        )
        assert (d.grade == "C") == offline


def test_a_grade_c_act_still_enumerates_its_open_items():
    """§4.2 rule 1: the pending counter and the other open items apply to a
    grade C act too, so the map's CSV row names them."""
    d = _derive(base_source="dv_offline", base_state="snapshot",
                base_frozen_at=None, base_audited=False,
                chain_scan_complete=False, divergences_unadjudicated=0,
                events=())
    assert d.grade == "C"
    assert "chain scan incomplete" in d.pending_items
    assert "snapshot not frozen" in d.pending_items


def test_grade_a_implies_every_condition_of_rule_two():
    for inputs in valid_inputs():
        if _derive(**inputs).grade != "A":
            continue
        assert inputs["base_state"] == "rebuilt"
        assert inputs["base_source"] == "dv_html"
        assert inputs["chain_scan_complete"]
        assert inputs["divergences_unadjudicated"] == 0
        for source, applied in inputs["events"]:
            assert source == "dv_html"
            assert applied in ("replayed", "not_incorporated")


def test_pending_items_are_named_exactly_when_something_is_open():
    for inputs in valid_inputs():
        d = _derive(**inputs)
        if d.grade == "B-pending":
            assert d.pending_items, inputs
        if d.grade in ("A", "B"):
            # The declared-base note is informational and never blocks; every
            # other item does, so an A or B act carries none of them.
            blocking = [p for p in d.pending_items
                        if not p.startswith(COUNTED[1])]
            assert blocking == [], inputs


def test_the_pending_items_come_from_the_fixed_vocabulary():
    for inputs in valid_inputs():
        d = _derive(**inputs)
        for item in d.pending_items:
            assert item in CANONICAL or item.startswith(COUNTED), item
        assert list(d.pending_items) == sorted(
            set(d.pending_items), key=list(d.pending_items).index
        )


def test_a_not_incorporated_event_never_blocks_a_grade():
    d = _derive(
        base_source="dv_html",
        base_state="snapshot",
        base_frozen_at="2026-01-01",
        base_audited=True,
        chain_scan_complete=True,
        divergences_unadjudicated=0,
        events=(("dv_html", "not_incorporated"), ("dv_html", "verified")),
    )
    assert d.grade == "B"
    assert d.pending_items == []


def test_the_p0_inputs_can_only_produce_b_pending_or_c():
    # In P0 every event is `pending`, the base is a `snapshot`, nothing is
    # frozen, nothing is audited and the body scan has not run. Rules 1 and 3
    # are the only ones that can fire, and both enumerate the open items.
    for base_source in BASE_SOURCES:
        for events in ((), (("dv_html", "pending"),), (("dv_offline", "pending"),)):
            d = _derive(
                base_source=base_source,
                base_state="snapshot",
                base_frozen_at=None,
                base_audited=False,
                chain_scan_complete=False,
                divergences_unadjudicated=0,
                events=events,
            )
            assert d.grade in ("B-pending", "C")
            assert d.pending_items
```

The map's CSV column keeps its name: `pending_items` now holds the canonical strings joined by `; `. This is the change that gives A2's `test_pending_items_use_the_canonical_derive_strings` something to pass against.

Run: `.venv/bin/python -m pytest -q -p no:cacheprovider tests/scripts tests/provenance`
Expected: all passed, and `grep -n "def derive_grade" scripts/dv_coverage_map.py` returns nothing. If `test_the_grade_procedure_is_total` reports a count other than 4,416, a domain constraint changed: recompute it, state the new number and why it moved, and do not adjust the assertion to whatever came out.

```bash
git add scripts/dv_coverage_map.py tests/scripts/test_dv_coverage_map.py
git commit -m "refactor(coverage-map): one derivation of design 4.2; the map imports provenance.derive"
```

### Task B3: the C10 detector `checks/provenance.py` (INV-010)

**Files:**
- Create: `corpus_integrity/checks/provenance.py`
- Test: `tests/corpus_integrity/test_provenance_check.py`
- Modify: `corpus_integrity/__main__.py` (register the check; **not in this task**. The registration is the LAST commit on Task B6's backfill branch, after the 3,624 acts carry their block. Registering it earlier makes `python -m corpus_integrity` exit 1 for the whole corpus and makes the write gate refuse every lex.bg refresh write until the batch merges.)

**Interfaces:**
- Consumes: `Act` and `Violation` (PR #23 Part II Task 1), `Provenance.from_frontmatter` (which applies `events_of`, so the promulgation row is already excluded), `derive_grade`.
- Produces: `ProvenanceCheck` (name `"provenance"`): violation when the block is missing, when the recorded grade differs from the derivation over the recorded states, when `fuente` disagrees with `base.state`, or when the derivation raises `DomainError`.
- `chain_scan_complete` is compared on `(issue, year)` only. `base.chain_scanned_through` is `{issue, year}` and `checked_through` is `{issue, year, date}`, so a whole-dict equality would be false for every act including a correct one, and the check would then contradict itself: it would report `chain scan incomplete` against a block that recorded it complete.

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

def test_the_acts_own_promulgation_row_does_not_make_it_pending(tmp_path):
    """The check reads events through events_of, so a single-issue act is not
    reported pending on its own promulgation (C1)."""
    d = tmp_path / "laws"; d.mkdir(exist_ok=True)
    (d / "a.md").write_text(
        "---\ntitulo: X\nidentificador: '1'\nfuente: lex.bg\n"
        "amendment_history:\n- dv: 32/2026\n  date: '2026-04-01'\n"
        + BLOCK.format(grade="B-pending") + "---\n\n**Чл. 1.** Текст.\n", encoding="utf-8")
    assert ProvenanceCheck().run(iter_acts(tmp_path)) == []
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


def _issue_key(value: dict | None) -> tuple[str, int] | None:
    """(issue, year) of a `{issue, year[, date]}` record, or None.

    Compared on the issue alone: `chain_scanned_through` carries no date and
    `checked_through` does, so whole-dict equality would be false for every
    act and the check would report „chain scan incomplete“ against blocks
    that correctly recorded it complete.
    """
    if not value:
        return None
    return str(value.get("issue")), int(value.get("year"))


class ProvenanceCheck:
    name = "provenance"

    def run(self, acts: Iterable[Act]) -> list[Violation]:
        out: list[Violation] = []
        for act in acts:
            prov = Provenance.from_frontmatter(act.frontmatter)
            if prov is None:
                out.append(Violation(self.name, act.slug, "no provenance block", "frontmatter"))
                continue
            scanned = _issue_key(prov.base.chain_scanned_through)
            scan_complete = scanned is not None and scanned == _issue_key(prov.checked_through)
            try:
                d = derive_grade(prov.base, prov.events, chain_scan_complete=scan_complete,
                                 divergences_unadjudicated=0,
                                 promulgation_cited=prov.base.promulgation_cited)
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
Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
git add corpus_integrity/checks/provenance.py tests/corpus_integrity/test_provenance_check.py
git commit -m "feat(corpus-integrity): provenance check (INV-010): grade equals derivation, fuente follows base state"
```

### Task B4: index migration 007 and the `amendment_events` table

**Files:**
- Modify: `index/migrations.py`, `index/catalog.py` (schema DDL for the new table), `index/build.py::_reindex_act` (read the block; populate the new columns and table; **add `import json` to the module imports**, it does not import json today)
- Test: `tests/index/test_migration_007.py`, `tests/index/test_build_provenance.py`

**Three names to get right, because the plan's first draft got them wrong.**

- **Migrations are declarative entries, not functions.** There is no `_migrate_006` to follow. The list is `MIGRATIONS: tuple[Migration, ...] = (Migration(version=6, name="provisions_implicit_column", sql=...), ...)`; this task appends `Migration(version=7, name="provenance_columns", sql=...)`. Latest version on `origin/main` is 6 and no other live branch claims 7, so the number is free.
- **There is no `_iso` in `index/build.py`.** (`_iso` exists in `mcp_server/server.py`, a different module.) The existing pattern in `build.py` is inline: `if hasattr(dv_date, "isoformat"): dv_date = dv_date.isoformat()`. Either add a real module-level `_iso(value)` helper in this task and use it in both places, or write the coercion inline; do not import a helper that is not there.
- **`_delete_act_rows` must delete the act's `amendment_events` rows** alongside its other rows, or an incremental rebuild leaves orphans behind a foreign key that SQLite does not enforce by default.

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
ultima_actualizacion: '2026-08-01'
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
- dv: 70/2026
  date: '2026-08-01'
  source: dv_html
  locator: {id_mat: 250100}
  applied: pending
  verified_against: null
  uncertainty: []
provenance:
  grade: B-pending
  derived_at: '2026-09-06'
  base: {source: dv_html, state: snapshot, locator: {id_mat: 242220}, issue: '32', year: 2026, frozen_at: null, audited: false, declared_at: null, chain_scanned_through: null, chain_inherited_before: '2005-01-01', uncertainty: []}
  checked_through: {issue: '70', year: 2026, date: '2026-08-01'}
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
    # events_pending is ONE, not two: бр. 32/2026 is the act's own promulgation
    # and the base carries it, so it is not an event (design 4.1). checked_through
    # is the scan currency mark, the last issue attributed to the act.
    assert row == ("B-pending", 1, "2026-08-01", "2005-01-01")
    # amendment_events mirrors the frontmatter list in full, promulgation
    # included, because history() reads the promulgation from it. The event
    # multiset of §4.2 is derived through events_of, never stored.
    ev = conn.execute("SELECT dv, source, applied FROM amendment_events WHERE law_id='test' ORDER BY seq").fetchall()
    assert ev == [("32/2026", "dv_html", "pending"), ("70/2026", "dv_html", "pending")]
```

- [ ] **Step 2: Run them and confirm they fail**

Run: `.venv/bin/python -m pytest -q -p no:cacheprovider tests/index/test_migration_007.py tests/index/test_build_provenance.py`
Expected: FAIL (`current_version` below 7; no such column)

- [ ] **Step 3: Implement**

In `index/migrations.py` append `Migration(version=7, name="provenance_columns", sql=...)` to `MIGRATIONS`, whose SQL is the four `ALTER TABLE laws ADD COLUMN ...` statements and:

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

`amendment_events` holds **every** `amendment_history` row including the promulgation, because the table is the index's mirror of the frontmatter list and `history()` reads the promulgation from it. The event multiset of design 4.2 is derived, not stored: `laws.events_pending` comes from the block, which was computed through `events_of`. `_iso` is either the helper this task adds to `build.py` or the inline coercion; `json` is a new import; `_delete_act_rows` also deletes the act's `amendment_events` rows.

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
- Modify: `mcp_server/schemas.py` (`GetLawResponse` and its TypedDict gain `provenance_grade: str | None`, `checked_through: str | None`, `chain_inherited_before: str | None`; `SearchHit` gains `provenance_grade: str | None`), `mcp_server/queries.py` (`provenance_warning(grade, pending_items, checked_through, chain_inherited_before) -> dict` next to `implicit_alinea_warning`; `get_law`/`search` read the new columns), `mcp_server/server.py` (attach the warning to every successful `get_law`, `get_article`, `get_articles`, `search` response whose act grade is not `A`), `mcp_server/errors.py` (`PROVENANCE_GRADE` and `AMBIGUOUS_ARTICLE_SPEC` in the code set), `docs/api/error-codes.json` and `.md` (new entries, version 1.6.0), `mcp_server/export_tools.py` (`TOOLS_JSON_VERSION` and the `x-disclaimer` block below), `tools.json` (regenerate with `mcp_server.export_tools`, version 1.6.0), `api/` models and `docs/api/openapi-rest.json` (regenerate with `api.export_openapi`)
- Test: `tests/mcp_server/test_provenance_exposure.py`, `tests/mcp_server/test_export_tools.py`

**The disclaimer travels in `tools.json`, not only inside a warning message.** Design 4.3's last MCP clause requires the disclaimer and the tie-break rule in the response metadata „so that dropping them is a visible contract violation“. Putting them only in the `message` text of a warning loses them for any consumer that filters warnings, and the contract-violation property with them. `export_tools` therefore emits a top-level `x-disclaimer` object next to `version`, `spec`, `server`, `tools` and `error_codes`:

```json
"x-disclaimer": {
  "status": "consolidated text without official value; Държавен вестник prevails on any discrepancy",
  "tie_break": "Where this text and the State Gazette differ, the State Gazette governs.",
  "source": "provenance.model.STATUS_LINE"
}
```

`status` is `provenance.model.STATUS_LINE` verbatim, so the frontmatter line and the wire metadata cannot drift. A parity test in `tests/mcp_server/test_export_tools.py` asserts the committed `tools.json` carries `x-disclaimer.status == STATUS_LINE`, which is what makes a silent removal fail CI.

**The `PROVENANCE_GRADE` warning on `search`.** One response, many acts, many grades. The rule (fixed in B1's Surface 3 preflight): one warning carrying the **weakest** grade among the hits, ordered `A` < `B` < `B-pending` < `C`, with `checked_through` and `chain_inherited_before` null because no single value is true for the whole result set; per-hit detail rides on `SearchHit.provenance_grade`. A response whose hits are all grade A carries no warning.

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

The convention is the one `tests/mcp_server/test_connection_model.py` uses: `build_app(conn=...)` or `build_app(db_path=..., corpus_root=...)` returns a handle whose tools are invoked as `handle.call_tool_sync("get_law", {"name": "999"})`, and failures are `pytest.raises(ToolError)` with `exc.value.code`. There is no `app_handle.get_law(...)` method and no `file_catalog_with_provenance` fixture; read that test file before writing these.

```python
# tests/mcp_server/test_provenance_exposure.py
import pytest

from mcp_server.errors import ERROR_CODES
from mcp_server.queries import provenance_warning
from mcp_server.server import build_app
from tests.mcp_server.conftest import FAKE_COMMIT_HASH

# The frontmatter of `zakon-a`, copied from the `app` fixture in
# tests/mcp_server/test_get_law.py:29-50 so this file exercises the same act the
# rest of the tool tests do. The provenance BLOCK is not needed here: the tools
# read the four `laws` columns migration 007 adds, not the frontmatter.
ACT_MD = (
    "---\n"
    "titulo: 'Закон за А'\n"
    "identificador: '100'\n"
    "pais: bg\n"
    "rango: закон\n"
    "fecha_publicacion: '2020-01-01'\n"
    "ultima_actualizacion: '2020-01-01'\n"
    "estado: vigente\n"
    "fuente: lex.bg\n"
    "dv_issue: '1'\n"
    "dv_year: 2020\n"
    "effective_date: '2020-01-01'\n"
    "category: laws\n"
    "eli: /eli/bg/закон/2020/1/1/zakon-a/con\n"
    "amendment_history: []\n"
    "---\n\n# ЗАКОН ЗА А\n\nТекст.\n"
)


@pytest.fixture
def prov_app(populated_conn, tmp_path):
    """The existing populated catalog, with a grade recorded on one act.

    `populated_conn` stamps every law's `current_commit` as FAKE_COMMIT_HASH,
    which is what lets `get_law`'s working-tree fast path read `tmp_path`
    without a real git repository. Same coupling, and same use-site assertion,
    as the `app` fixture in test_get_law.py.
    """
    assert FAKE_COMMIT_HASH == "a" * 40
    populated_conn.execute(
        "UPDATE laws SET provenance_grade=?, events_pending=?, checked_through=?,"
        " chain_inherited_before=? WHERE law_id='zakon-a'",
        ("B-pending", 3, "2026-04-01", "2005-01-01"),
    )
    (tmp_path / "laws").mkdir()
    (tmp_path / "laws" / "zakon-a.md").write_text(ACT_MD, encoding="utf-8")
    return build_app(conn=populated_conn, corpus_root=tmp_path)


def test_provenance_warning_shape():
    w = provenance_warning("B-pending", ["events pending: 3"], "2026-04-01", "2005-01-01")
    assert w["code"] == "PROVENANCE_GRADE" and w["grade"] == "B-pending"
    assert w["pending_items"] == ["events pending: 3"] and w["checked_through"] == "2026-04-01"


def test_get_law_carries_grade_and_warning_for_non_a(prov_app):
    r = prov_app.call_tool_sync("get_law", {"name": "100"})
    assert r["provenance_grade"] == "B-pending"
    assert r["checked_through"] == "2026-04-01"
    assert r["chain_inherited_before"] == "2005-01-01"
    assert [w for w in r["warnings"] if w["code"] == "PROVENANCE_GRADE"]


def test_a_grade_a_act_carries_the_field_and_no_warning(prov_app, populated_conn):
    populated_conn.execute("UPDATE laws SET provenance_grade='A', events_pending=0"
                           " WHERE law_id='zakon-a'")
    r = prov_app.call_tool_sync("get_law", {"name": "100"})
    assert r["provenance_grade"] == "A"
    assert not [w for w in r["warnings"] if w["code"] == "PROVENANCE_GRADE"]


def test_search_warns_with_the_weakest_grade_among_its_hits(prov_app, populated_conn):
    populated_conn.execute("UPDATE laws SET provenance_grade='B' WHERE law_id='zakon-a'")
    populated_conn.execute("UPDATE laws SET provenance_grade='C' WHERE law_id='zakon-b'")
    r = prov_app.call_tool_sync("search", {"query": "закон"})
    grades = {hit["provenance_grade"] for hit in r["results"]}
    assert {"B", "C"} <= grades, "each hit carries its own grade"
    warning = next(w for w in r["warnings"] if w["code"] == "PROVENANCE_GRADE")
    assert warning["grade"] == "C", "one warning, the weakest grade in the result set"
    assert warning["checked_through"] is None and warning["chain_inherited_before"] is None


def test_error_taxonomy_parity_includes_the_new_codes():
    assert "PROVENANCE_GRADE" in ERROR_CODES
    assert "AMBIGUOUS_ARTICLE_SPEC" in ERROR_CODES
```

`populated_conn` and the `zakon-a` / `zakon-b` law ids come from `tests/mcp_server/conftest.py:39-98`, which seeds eight acts including those two. Adapt the names to that file rather than inventing fixtures; `zakon-a` is `identificador` 100, which is why `get_law` is called with `{"name": "100"}`.

- [ ] **Step 2: Run it and confirm it fails**

Run: `.venv/bin/python -m pytest -q -p no:cacheprovider tests/mcp_server/test_provenance_exposure.py`
Expected: FAIL, `ImportError: cannot import name 'provenance_warning'`

- [ ] **Step 3: Implement** the fields, the warning, the attachment in `server.py` (read `laws.provenance_grade`, `events_pending`, `checked_through`, `chain_inherited_before` for the act; build `pending_items` as `[f"events pending: {n}"]` when `events_pending > 0`, since only the count is stored in the index and the derivation's other items live in the frontmatter block, so the warning carries the count and the two dates), the weakest-grade rule on `search`, the `x-disclaimer` block in `export_tools`, the two error-code registry entries, and regenerate `tools.json` and `docs/api/openapi-rest.json` with the existing exporters.

- [ ] **Step 4: Run the tests, the parity tests and the whole suite**

Run: `.venv/bin/python -m pytest -q -p no:cacheprovider tests/mcp_server tests/api && .venv/bin/python -m mcp_server.export_tools --check && .venv/bin/python -m api.export_openapi --check docs/api/openapi-rest.json`
Expected: all passed; both `--check` commands report no drift. `api.export_openapi`'s `--check` takes a `Path` argument and errors without one.

- [ ] **Step 5: Commit**

```bash
git add mcp_server/ api/ tools.json docs/api/error-codes.json docs/api/error-codes.md docs/api/openapi-rest.json tests/mcp_server/
git commit -m "feat(mcp,rest): provenance grade, checked_through and chain_inherited_before on get_law and search; PROVENANCE_GRADE warning; x-disclaimer in tools.json 1.6.0"
```

### Task B5b: the grade on the Cloudflare data plane

Design 4.3 requires the grade on the cf plane („the act payload carries the grade; the worker mirrors the REST warning“) and design section 8 lists P1 content as „MCP/**REST/cf** grade exposure“. `COVERAGE-FLOOR.md`, Provenance floor, counts „serving a grade B or C text without the grade at the consumer surface“ as an omission. After B6 every act is B-pending or C, so **from the moment the backfill lands the cf plane is in breach of the floor this plan enforces** unless the payload carries the grade. This task is the exporter half; the worker's response shape is an owner decision, recorded below and not implemented here.

**Files:**
- Modify: `export_cf/acts.py` (`build_act_payload`'s `meta`), `export_cf/verify.py`, `docs/api/cf-data-plane-spec.md` (version 2.1 to 2.2)
- Test: `tests/export_cf/test_acts_provenance.py`

**The payload is built from the act's file, not from a `laws` row.** Read the function before writing the change:

```python
# as in export_cf/acts.py:121
def build_act_payload(law_id: str, doc_id: int, category: str,
                      raw_markdown: str, commit_hash: str,
                      warnings: list[dict]) -> dict:
# as in export_cf/acts.py:124
    fm, body = split_frontmatter(raw_markdown)
# as in export_cf/acts.py:136 (every meta value is read off `fm`)
        "dv_issue": fm.get("dv_issue"),
```

It takes no connection and no corpus root: `export_acts` reads the markdown first (`read_law_markdown`, `acts.py:157`) and hands it in. So the two new keys come from the `provenance` block in the frontmatter the payload already parses, and no signature changes.

**Interfaces:**
- `build_act_payload`'s `meta` gains `provenance_grade: str | None` and `checked_through: str | None`, read from the block: `(fm.get("provenance") or {}).get("grade")` and `((fm.get("provenance") or {}).get("checked_through") or {}).get("date")`. The second is the DATE of the currency mark, the same projection migration 007 stores in `laws.checked_through` (Task B4), so the two surfaces carry one value. Additive: no existing key changes name, type or value, so a worker that ignores them keeps working.
- The D1 side needs nothing new, so `export_cf/ddl.py` is not touched: table DDL is read from the source catalog's `sqlite_master` (`export_cf/ddl.py:3`, and `docs/api/cf-data-plane-spec.md:59` states the same for the emitted schema), so migration 007's four columns arrive in D1 by the existing mechanism.
- `export_cf/verify.py` gains `_check_act_provenance`, in the shape of the existing per-act check:

```python
# as in export_cf/verify.py:55
def _check_act_articles(conn: sqlite3.Connection, out_dir: Path,
                        law_id: str, failures: list[str]) -> None:
# as in export_cf/verify.py:57
    path = out_dir / "r2" / "acts" / f"{law_id}.json"
```

  called next to it in the sampled loop:

```python
# as in export_cf/verify.py:297-300
        law_ids = [r[0] for r in conn.execute("SELECT law_id FROM laws")]
        sampled = _sample(law_ids, sample_n)
        for law_id in sampled:
            _check_act_articles(conn, out_dir, law_id, failures)
```

  This is a genuine cross-check, not an identity: the payload's two values come from the act's frontmatter, and `laws.provenance_grade` / `laws.checked_through` come from `index.build`'s own read of the same block (B4), so a divergence means the export and the catalog disagree about an act and `--verify` fails. That is stronger than the check the earlier draft described, which compared the payload against the row it had been copied from.
- `docs/api/cf-data-plane-spec.md` goes to 2.2 with a section-9 history entry naming the two `meta` keys, matching how v2.1 recorded `implicit_paragraphs`.

**Owner decision, listed not implemented.** Whether `cf-worker` mirrors the `PROVENANCE_GRADE` warning in its responses or skips non-A acts entirely is the same label-or-skip question design 4.3 flags for FR-032's implicit rows, and 4.3 says to decide the two together. It is recorded here as pending and belongs in FR-032's decision, not in this plan. Until it is taken, the cf plane carries the grade in the payload (so a consumer can read it) and mirrors no warning.

- [ ] **Step 1: Write the failing test**

```python
# tests/export_cf/test_acts_provenance.py
import json
import sqlite3

from export_cf.acts import build_act_payload
from export_cf.verify import _check_act_provenance
from index.migrations import migrate

WITH_BLOCK = """---
titulo: ТЕСТ
identificador: '5'
pais: bg
rango: закон
fecha_publicacion: '2026-04-01'
ultima_actualizacion: '2026-08-01'
estado: vigente
fuente: lex.bg
category: laws
amendment_history: []
provenance:
  grade: B-pending
  derived_at: '2026-09-06'
  base: {source: dv_html, state: snapshot, locator: null, issue: '32', year: 2026,
    frozen_at: null, audited: false, declared_at: null, chain_scanned_through: null,
    chain_inherited_before: '2005-01-01', uncertainty: []}
  checked_through: {issue: '70', year: 2026, date: '2026-08-01'}
  in_force_as_of: '2026-04-16'
  events_not_in_force: 0
  events_pending: 1
  pending_items: [chain scan incomplete]
  pdf_pages_estimate: 0
  status: consolidated text without official value
---

**Чл. 1.** Текст.
"""

NO_BLOCK = ("---\ntitulo: Закон за А\nidentificador: '100'\n"
            "fecha_publicacion: '2020-01-01'\n---\n\n**Чл. 1.** Текст.\n")


def test_the_act_payload_carries_the_grade_and_the_currency_mark():
    payload = build_act_payload("test", 5, "laws", WITH_BLOCK, "c" * 40, [])
    assert payload["meta"]["provenance_grade"] == "B-pending"
    assert payload["meta"]["checked_through"] == "2026-08-01"


def test_a_payload_for_an_act_without_a_block_carries_nulls():
    payload = build_act_payload("zakon-a", 100, "laws", NO_BLOCK, "c" * 40, [])
    assert payload["meta"]["provenance_grade"] is None
    assert payload["meta"]["checked_through"] is None


def test_verify_fails_when_the_payload_and_the_catalog_disagree(tmp_path):
    """The check is a cross-check: the payload came from the frontmatter, the
    columns from index.build's read of the same block."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    migrate(conn)
    conn.execute(
        "INSERT INTO laws (law_id, doc_id, title, category, current_commit,"
        " provenance_grade, checked_through) VALUES"
        " ('test', 5, 'ТЕСТ', 'laws', 'c', 'B-pending', '2026-08-01')")
    acts = tmp_path / "r2" / "acts"
    acts.mkdir(parents=True)
    (acts / "test.json").write_text(
        json.dumps({"meta": {"provenance_grade": None, "checked_through": None}}),
        encoding="utf-8")
    failures: list[str] = []
    _check_act_provenance(conn, tmp_path, "test", failures)
    assert failures and "provenance" in failures[0]


def test_verify_passes_when_they_agree(tmp_path):
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    migrate(conn)
    conn.execute(
        "INSERT INTO laws (law_id, doc_id, title, category, current_commit,"
        " provenance_grade, checked_through) VALUES"
        " ('test', 5, 'ТЕСТ', 'laws', 'c', 'B-pending', '2026-08-01')")
    acts = tmp_path / "r2" / "acts"
    acts.mkdir(parents=True)
    (acts / "test.json").write_text(
        json.dumps(build_act_payload("test", 5, "laws", WITH_BLOCK, "c" * 40, [])),
        encoding="utf-8")
    failures: list[str] = []
    _check_act_provenance(conn, tmp_path, "test", failures)
    assert failures == []
```

The first two tests need no fixture at all, which is the point: `build_act_payload` takes the markdown. `tests/export_cf/conftest.py` provides `export_corpus` and `export_run` (both module-scoped) and nothing else, so the last two build their own catalog through `index.migrations.migrate` rather than naming a fixture that does not exist.

- [ ] **Step 2: Run them and confirm they fail**

Run: `.venv/bin/python -m pytest -q -p no:cacheprovider tests/export_cf/test_acts_provenance.py`
Expected: FAIL, `KeyError: 'provenance_grade'` on the first two and `ImportError` on `_check_act_provenance`.

- [ ] **Step 3: Implement** the two `meta` keys, the `verify.py` check (called in the sampled loop next to `_check_act_articles`) and the spec bump.

- [ ] **Step 4: Run the export suite and a real verify**

Run: `.venv/bin/python -m pytest -q -p no:cacheprovider tests/export_cf` then a full `export_cf` run with `--verify` over the rebuilt `catalog.db`.
Expected: all passed; verify reports no failures.

- [ ] **Step 5: Commit**

```bash
git add export_cf/ docs/api/cf-data-plane-spec.md tests/export_cf/test_acts_provenance.py
git commit -m "feat(export-cf): provenance_grade and checked_through on the act payload; cf-data-plane-spec 2.2"
```

### Task B6: corpus-wide backfill of the provenance block through the write gate

**Preconditions, stated because the difference is weeks of sequencing.**

`corpus_gate.write_act` runs the whole registered `CHECKS` set on the act it is writing and raises `CorpusIntegrityError` on any violation. After PR #23 Part II lands, `CHECKS` holds `RemnantCheck` and `ChromeCheck`; Part III adds more. Waiver reconciliation lives in `corpus_integrity/waivers.py`, which the RUNNER calls, not the gate. A backfill of 3,624 acts walks every act past every registered class, so without a change the batch aborts on the first act with any outstanding violation of any class.

**The precondition is that PR #23 Part II Task 6's gate applies the same waiver reconciliation as the runner, count-equality per act (the PR #34 fix round).** With it, the 81 waived acts write while keeping their expected counts, an act that regressed past its waived count still fails, and the backfill passes. B6's own tests are unaffected.

The alternative, running B6 only after `python -m corpus_integrity` is green corpus-wide, is PR #23 Part V phase 7, which waits on owner decision O-3. That ordering is acceptable but much later; the gate-side reconciliation is the one that lets P1 close on its own schedule. Whichever the owner picks, this is not a decision for the executor.

**Files:**
- Create: `scripts/provenance_backfill.py`, `tests/scripts/test_provenance_backfill.py`
- Modify: `corpus_integrity/__main__.py` (register `ProvenanceCheck` in `CHECKS`; **the last commit on this branch**, see Step 6)

**Interfaces:**
- Consumes: `docs/research/2026-09-05-dv-coverage-map/acts-summary.csv` and `coverage-map.csv` (Task A4), `corpus_gate.write_act(path, frontmatter, body, *, source=SourceRef)` (PR #23 Part II Task 6), `provenance.model` (including `events_of`), `provenance.derive`, `corpus_commit.commit_corpus_change` (Task B0) with commit type `popravka`, `source_id="dvmap-2026-09"`, `source_date` = the run date, `norm_id` = the act's `identificador`; Surface 5 preflight of Task B1.
- Produces: every act carries a `provenance` block and per-event fields; `fuente` unchanged (every base is a snapshot at backfill); one `[popravka]` commit per act; `python -m corpus_integrity` reports zero `provenance` violations afterwards.

**The CSV columns are the map's, not invented ones.** `acts-summary.csv` after Task A2 and A4 Step 0 carries `law_id, title, candidate_grade, pending_items, events_total, events_dv_html, events_dv_pdf, events_unlocated, events_dv_offline, pdf_pages_estimate, base_source, dv_identifier, chain_scanned_through, base_issue, base_year, base_locator, checked_through, checked_through_date, chain_inherited_before`. `coverage-map.csv` carries `law_id, row_kind, position, dv_year, dv_number, date, source, applied, state, locator_id_mat, resolver_score, resolver_flags, uncertainty, pdf_pages_estimate`. **There is no `dv` column and no `locator` column**: the event key is `dv_year` + `dv_number`, joined as `f"{dv_number}/{dv_year}"` to match the frontmatter's `dv` form, and the locator column is `locator_id_mat`. A `build_block` reading `e["dv"]` or `e["locator"]` raises `KeyError` on the first row.

- [ ] **Step 1: Write the failing test**

The fixtures below use the REAL map headers. Copy them from `SUMMARY_FIELDS` and `COVERAGE_FIELDS` in `scripts/dv_coverage_map.py` rather than retyping, so a later column change breaks the test instead of the batch.

```python
# tests/scripts/test_provenance_backfill.py
import csv
from pathlib import Path

from scripts.dv_coverage_map import COVERAGE_FIELDS, SUMMARY_FIELDS
from scripts.provenance_backfill import backfill, build_block


def _summary(**over) -> dict:
    row = {k: "" for k in SUMMARY_FIELDS}
    row.update({"law_id": "zot", "base_source": "dv_html", "candidate_grade": "B-pending",
                "pending_items": "chain scan incomplete; base not audited; snapshot not frozen",
                "pdf_pages_estimate": "0", "chain_scanned_through": "",
                "checked_through": "2026/70", "checked_through_date": "2026-08-01",
                "chain_inherited_before": "2005-01-01", "base_issue": "32",
                "base_year": "2026", "base_locator": "242220"})
    row.update(over)
    return row


def _event(**over) -> dict:
    row = {k: "" for k in COVERAGE_FIELDS}
    row.update({"law_id": "zot", "row_kind": "event", "dv_year": "2026", "dv_number": "70",
                "date": "2026-08-01", "source": "dv_html", "applied": "pending",
                "state": "snapshot", "locator_id_mat": "250100"})
    row.update(over)
    return row


def test_build_block_from_map_rows_derives_b_pending_for_a_snapshot_act():
    events = [_event(row_kind="base", dv_number="32", date="2026-04-01",
                     locator_id_mat="242220"),
              _event()]
    fm = {"amendment_history": [{"dv": "32/2026", "date": "2026-04-01"},
                                {"dv": "70/2026", "date": "2026-08-01"}],
          "fuente": "lex.bg", "estado": "vigente"}
    block, history = build_block(_summary(), events, fm, derived_at="2026-09-06")
    assert block["grade"] == "B-pending" and block["base"]["state"] == "snapshot"
    assert block["base"]["issue"] == "32" and block["base"]["year"] == 2026
    assert block["base"]["locator"] == {"id_mat": 242220}
    assert block["checked_through"] == {"issue": "70", "year": 2026, "date": "2026-08-01"}
    # Both rows keep their per-event fields; only the DERIVATION drops the
    # promulgation, so events_pending counts бр. 70/2026 alone.
    assert len(history) == 2
    assert history[1]["applied"] == "pending" and history[1]["source"] == "dv_html"
    assert history[1]["locator"] == {"id_mat": 250100}
    assert block["events_pending"] == 1


def test_a_single_issue_act_is_not_pending_on_its_own_promulgation():
    events = [_event(row_kind="base", dv_number="32", date="2026-04-01",
                     locator_id_mat="242220")]
    fm = {"amendment_history": [{"dv": "32/2026", "date": "2026-04-01"}],
          "fuente": "lex.bg", "estado": "vigente"}
    block, history = build_block(_summary(checked_through="2026/32",
                                          checked_through_date="2026-04-01"),
                                 events, fm, derived_at="2026-09-06")
    assert block["events_pending"] == 0
    assert not any(item.startswith("events pending") for item in block["pending_items"])
    assert len(history) == 1, "the row itself stays in amendment_history"


def test_the_scan_mark_from_the_map_reaches_the_block_and_decides_the_scan(tmp_path):
    """The map measured the scan; the block records what it measured. With the
    mark equal to checked_through the act no longer says `chain scan incomplete`."""
    events = [_event(row_kind="base", dv_number="32", date="2026-04-01",
                     locator_id_mat="242220")]
    fm = {"amendment_history": [{"dv": "32/2026", "date": "2026-04-01"}],
          "fuente": "lex.bg", "estado": "vigente"}
    block, _ = build_block(_summary(chain_scanned_through="2026/70"), events, fm,
                           derived_at="2026-09-06")
    assert block["base"]["chain_scanned_through"] == {"issue": "70", "year": 2026}
    assert "chain scan incomplete" not in block["pending_items"]
    behind, _ = build_block(_summary(chain_scanned_through="2026/50"), events, fm,
                            derived_at="2026-09-06")
    assert "chain scan incomplete" in behind["pending_items"]


def test_an_act_citing_no_promulgation_gets_the_unknown_item(tmp_path):
    events = []
    fm = {"amendment_history": [], "fuente": "lex.bg", "estado": "vigente"}
    block, _ = build_block(_summary(base_source="unlocated", base_issue="", base_year="",
                                    base_locator="", pending_items="promulgation unknown"),
                           events, fm, derived_at="2026-09-06")
    assert "promulgation_unknown" in block["base"]["uncertainty"]
    assert "promulgation unknown" in block["pending_items"]


def test_backfill_writes_every_act_through_the_gate_and_never_by_hand(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr("scripts.provenance_backfill.write_act",
                        lambda path, fm, body, *, source: calls.append((path, fm["provenance"]["grade"])))
    monkeypatch.setattr("scripts.provenance_backfill.commit_corpus_change", lambda *a, **k: True)
    (tmp_path / "laws").mkdir()
    (tmp_path / "laws" / "zot.md").write_text(
        "---\ntitulo: X\nidentificador: '1'\nfuente: lex.bg\nestado: vigente\n"
        "amendment_history: []\n---\n\n**Чл. 1.** Т.\n", encoding="utf-8")
    summary = tmp_path / "acts-summary.csv"
    with summary.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=SUMMARY_FIELDS)
        w.writeheader()
        w.writerow(_summary(base_source="unlocated", base_issue="", base_year="",
                            base_locator="", checked_through="", checked_through_date="",
                            pending_items="promulgation unknown"))
    events = tmp_path / "coverage-map.csv"
    with events.open("w", encoding="utf-8", newline="") as f:
        csv.DictWriter(f, fieldnames=COVERAGE_FIELDS).writeheader()
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
from corpus_commit import commit_corpus_change
from corpus_gate import SourceRef, write_act
from provenance.derive import derive_grade
from provenance.model import Base, Provenance, STATUS_LINE, events_of

# Mirrors corpus_integrity.loader.CATEGORY_DIRS. `postanovleniya` is absent
# from the tree today and stays in the tuple deliberately: Path.glob on a
# missing directory is empty, and the day the directory appears the backfill
# covers it without a second edit.
CATEGORIES = ("laws", "codes", "ordinances", "regulations", "implementing", "postanovleniya")


def _split(text: str) -> tuple[dict, str]:
    _, fm, body = text.split("---\n", 2)
    return yaml.safe_load(fm) or {}, body


def build_block(summary: dict, events: list[dict], fm: dict, *, derived_at: str) -> tuple[dict, list[dict]]:
    """One act's provenance block and its enriched amendment_history.

    Column names are the map's: the event key is `dv_year` + `dv_number` (there
    is no `dv` column) and the locator is `locator_id_mat` (there is no
    `locator` column).
    """
    cited = bool(summary.get("base_issue"))
    # Both currency marks come from the map row, in the two shapes the block
    # stores: the scan mark is an ISSUE (no date), the currency statement is an
    # issue plus the date it was published. Hard-coding the scan mark to None
    # would record „chain scan incomplete“ on every act forever, including after
    # the body pass has covered it, and B3 re-derives the same way so nothing
    # would catch the untruth.
    cst = None
    if summary.get("chain_scanned_through"):
        y, n = summary["chain_scanned_through"].split("/")
        cst = {"issue": n, "year": int(y)}
    ct = None
    if summary.get("checked_through"):
        y, n = summary["checked_through"].split("/")
        ct = {"issue": n, "year": int(y), "date": summary.get("checked_through_date") or None}
    base = Base(source=summary["base_source"] or "unlocated", state="snapshot",
                locator={"id_mat": int(summary["base_locator"])} if summary.get("base_locator") else None,
                issue=summary.get("base_issue") or None,
                year=int(summary["base_year"]) if summary.get("base_year") else None,
                frozen_at=None, audited=False, declared_at=None, chain_scanned_through=cst,
                chain_inherited_before=summary.get("chain_inherited_before") or "2005-01-01",
                uncertainty=[] if cited else ["promulgation_unknown"])
    # The same equality B3 checks, on (issue, year): the scan mark carries no
    # date and the currency statement does.
    scan_complete = bool(cst) and ct is not None and \
        (str(cst["issue"]), int(cst["year"])) == (str(ct["issue"]), int(ct["year"]))
    by_dv = {_dv_key(e["dv_number"], e["dv_year"]): e for e in events if e.get("row_kind") != "base"}
    history = []
    for row in fm.get("amendment_history") or []:
        e = by_dv.get(_dv_key(*str(row.get("dv")).split("/")), {})
        history.append({
            **row,
            "source": e.get("source") or "unlocated",
            "locator": {"id_mat": int(e["locator_id_mat"])} if e.get("locator_id_mat") else None,
            "applied": "pending",
            "verified_against": None,
            "uncertainty": [] if e.get("source") else ["chain_unconfirmed"],
        })
    # THE event multiset: the enriched history minus the promulgation row.
    # events_of takes a frontmatter dict, so it is handed the history just
    # built. One filter, called here and nowhere reimplemented.
    ev_objs = events_of({"amendment_history": history}, base)
    d = derive_grade(base, ev_objs, chain_scan_complete=scan_complete,
                     divergences_unadjudicated=0, promulgation_cited=cited)
    prov = Provenance(grade=d.grade, derived_at=derived_at, base=base, events=ev_objs, checked_through=ct,
                      in_force_as_of=fm.get("effective_date") or fm.get("fecha_publicacion"),
                      events_not_in_force=0, events_pending=sum(1 for e in ev_objs if e.applied == "pending"),
                      pdf_pages_estimate=int(float(summary.get("pdf_pages_estimate") or 0)),
                      status=STATUS_LINE, pending_items=list(d.pending_items))
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
                commit_corpus_change(
                    path, "popravka", fm.get("titulo", law_id),
                    norm_id=str(fm.get("identificador")),
                    source_id=f"dvmap-{derived_at[:7]}",
                    source_date=derived_at, cwd=root,
                )
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
The `write_act` signature and `SourceRef` come from Part II Task 6; adapt the import names to what landed. **Do not register `ProvenanceCheck` yet** (Step 6).

- [ ] **Step 4: Run the tests; then a dry run over the real corpus**

Run: `.venv/bin/python -m pytest -q -p no:cacheprovider tests/scripts/test_provenance_backfill.py` then `.venv/bin/python scripts/provenance_backfill.py --summary docs/research/2026-09-05-dv-coverage-map/acts-summary.csv --events docs/research/2026-09-05-dv-coverage-map/coverage-map.csv --dry-run`
Expected: tests pass; the dry run prints 3,624 and no `NO MAP ROW` lines (every act must have a map row; if one is missing, fix the map, not the script).

**One more number the dry run must print: how many acts with a known `base_issue` filtered no row.** `events_of` removes the promulgation by matching `dv`; an act whose history writes the issue in a form the normaliser does not recognise keeps its own promulgation as a pending event and reads one grade worse than it is. The count belongs in the dry-run output because it is silent otherwise, and the whole corpus passes through this script exactly once. A non-zero count is investigated against the offending rows before the real run, not waived.

- [ ] **Step 5: Commit the tooling WITHOUT the registration**

```bash
git add scripts/provenance_backfill.py tests/scripts/test_provenance_backfill.py
git commit -m "feat(provenance): corpus-wide backfill of the provenance block through the write gate"
```

The registration is deliberately not in this commit. Registering `ProvenanceCheck` before every act carries a block makes `python -m corpus_integrity` exit 1 for 3,624 acts and makes the write gate refuse every lex.bg refresh write, so CI would be red and the pipeline blocked for the whole interval between the tooling commit and the batch merge.

- [ ] **Step 6: The real backfill (one batch, on the same branch, merge commit)**

Run without `--dry-run` on branch `data/provenance-backfill-2026-09`. Then, as the LAST commit on the branch, register `ProvenanceCheck()` in `corpus_integrity/__main__.py` `CHECKS`:

```bash
git add corpus_integrity/__main__.py
git commit -m "feat(corpus-integrity): register the provenance check now that every act carries a block"
```

The branch is then green at every commit from the batch onward, and the gate turns on with the data already in place. Verify before opening the PR: `.venv/bin/python -m corpus_integrity --check provenance` reports 0 violations, `.venv/bin/python -m corpus_integrity` is green corpus-wide, and `python -m index.build --incremental` rebuilds. **Merge with a merge commit, never squash** (3,624 corpus commits carry trailers).

### Task B7: § rows keyed by section context, with a `kind` column, and § in the address grammar

The corpus carries „§ 1“ two or more times in 227 acts because every appended ПЗР restarts numbering. Naive § rows would create an FR-038-class collision set. Rows are therefore keyed by section context and carry a `kind`. Protected surfaces 3 and 4; preflights from Task B1.

**Files:**
- Modify: `index/provisions.py` (protected: read the FR-034 comments first; add § handling without changing any article rule), `index/migrations.py` (migration 008), `index/catalog.py` (DDL), `index/build.py` (write `kind`), `mcp_server/queries.py` (`_FULL_RE`, `parse_article_spec`, `ArticleSpec.kind`, the lookup), `mcp_server/schemas.py` (`GetArticleResponse.kind`), `api/` (same), `docs/api/*`, `tools.json`
- Test: `tests/index/test_provisions_paragraphs.py`, `tests/mcp_server/test_paragraph_addressing.py`

**Interfaces:**
- Produces: `Provision.kind: str` with values `article` (default), `para_dr` (a § under an own-act Допълнителн... heading), `para_pzr` (a § under an own-act Преходни/Заключителни heading without a `КЪМ` qualifier), `para_amending` (a § under a heading carrying a `КЪМ <act>` qualifier, i.e. an appended amending act's provisions); § rows have `article = "§ N"` (with the sign and one space), `paragraph = None`; `parse_article_spec("§ 1")`, `("§1")`, `("§ 1.")`, `("пар. 1")` return `ArticleSpec(article="§ 1", paragraph=None, range_end=None, kind="para")`; `get_article` on a § spec returns the single own-act row (`para_dr` or `para_pzr`) when exactly one exists, and raises `AMBIGUOUS_ARTICLE_SPEC` with the candidate rows (each with `kind`, `section_ref` and a text head) otherwise; `para_amending` rows are never returned for a bare `§ N` spec and are reachable only through `get_articles` with `kind="para_amending"` (owner decision: the amending act's provisions are that act's, not this one's).
- **`Provision.section_ref: str | None`**, the normalised heading text of the section the § sits under (empty for `article` rows). This is what keeps distinct amending acts distinct.

**Why `section_ref` is not optional.** Design 7.5 keys § rows by „(ДР, ПЗР of the promulgated act, **ПЗР of amending act N**)“. Collapsing every appended amending section into one `kind = "para_amending"` loses the N. An act with three appended ЗИД ПЗР, each opening at § 1, then carries three rows on `(law_id, "§ 1", "para_amending")` with nothing to tell them apart, and migration 008's index is exactly on that triple. `provisions` has no unique constraint, so the collision is silent: `get_articles(kind="para_amending")` returns N indistinguishable rows. Given FR-038's history (698 colliding article keys), reintroducing that shape while claiming to have solved it is the wrong trade.

So: migration 008 adds `section_ref TEXT` alongside `kind`, the index is `(law_id, article, kind, section_ref)`, the parser writes the normalised heading text (whitespace collapsed, case preserved) into it, and a test with two appended ПЗР both starting at § 1 asserts the rows are distinguishable.

**No corpus-wide address change without a corpus-wide measurement.** Directive 10 is „detection precedes repair“, and this task's own preamble says 227 acts carry `§ 1` two or more times. Nobody yet knows how many acts have an ambiguous OWN-ACT § after the `para_amending` split, so nobody knows whether `get_article(law, "§ 1")` raises for three acts or three hundred, and the pilot's acceptance („`get_article` answers § 1“) is unfalsifiable at corpus scale until they do. Step 3b measures it.

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

## Преходни разпоредби КЪМ ЗАКОНА ЗА ИЗМЕНЕНИЕ НА ЗАКОНА ЗА ПРИМЕР ОТ 2028 Г.

**§ 1.** В чл. 1 думите "определя" се заменят с "регламентира".
"""

def test_paragraph_rows_carry_kind_by_section_context():
    rows = parse(DOC, "primer")
    paras = [(r.article, r.kind, r.text[:20]) for r in rows if r.article.startswith("§")]
    assert paras == [
        ("§ 1", "para_dr", "**§ 1.** По смисъла "),
        ("§ 2", "para_pzr", "**§ 2.** Законът вли"),
        ("§ 1", "para_amending", "**§ 1.** В чл. 1 дум"),
        ("§ 2", "para_amending", "**§ 2.** Законът вли"),
        ("§ 1", "para_amending", "**§ 1.** В чл. 1 дум"),
    ]

def test_two_appended_amending_acts_both_starting_at_para_1_stay_distinguishable():
    """Design 7.5 keys § rows by the amending act too; without section_ref
    these two rows collide on (law_id, article, kind), the FR-038 shape."""
    rows = [r for r in parse(DOC, "primer")
            if r.article == "§ 1" and r.kind == "para_amending"]
    assert len(rows) == 2
    assert rows[0].section_ref != rows[1].section_ref
    assert "2028" in rows[1].section_ref

def test_definition_items_belong_to_their_paragraph():
    rows = parse(DOC, "primer")
    dr = next(r for r in rows if r.article == "§ 1" and r.kind == "para_dr")
    assert '1. "Възел за достъп" е място.' in dr.text

def test_article_rows_are_unchanged_by_paragraph_support():
    rows = parse(DOC, "primer")
    arts = [r for r in rows if r.kind == "article"]
    assert [r.article for r in arts] == ["1"] and arts[0].paragraph is None
    assert arts[0].section_ref in (None, "")
```

The first expected value is `"**§ 1.** По смисъла "` with a trailing space: `"**§ 1.** По смисъла на този закон:"[:20]` is twenty characters ending in a space, while the other tuples happen to end exactly on a word.

```python
# tests/mcp_server/test_paragraph_addressing.py
import subprocess

import pytest

from index.build import build
from mcp_server.errors import ToolError
from mcp_server.queries import parse_article_spec
from mcp_server.server import build_app
# The § document lives in the index test that pins the parser, and this file
# addresses the SAME text through the tools. Cross-importing a fixture document
# is the established shape here:
#   # as in tests/mcp_server/conftest.py:143
#   from tests.index.test_provisions import ZZD_STYLE_MD
from tests.index.test_provisions_paragraphs import DOC

FM = ("---\ntitulo: {titulo}\nidentificador: '{ident}'\npais: bg\n"
      "rango: закон\nfecha_publicacion: '2026-04-01'\n"
      "ultima_actualizacion: '2026-04-01'\nestado: vigente\nfuente: lex.bg\n"
      "category: laws\namendment_history: []\n---\n\n")

PRIMER_MD = FM.format(titulo="Закон за пример", ident="700") + DOC

# The same body with a SECOND own-act section opening at § 1, so the act carries
# a `para_dr` § 1 AND a `para_pzr` § 1: the ambiguity `get_article` must refuse
# to guess at. Its own identificador, or the two acts collide in the catalog.
PRIMER_DUP_MD = FM.format(titulo="Закон за пример дубъл", ident="701") + DOC + (
    "\n## Преходни разпоредби\n\n"
    "**§ 1.** Заварените производства се довършват по досегашния ред.\n"
)


@pytest.fixture
def para_app(tmp_path):
    """A REAL one-commit corpus with both acts, indexed by `index.build`.

    Built the way `tests/mcp_server/conftest.py`'s `file_catalog` builds its
    corpus (git init, one commit, then `build`), because the § rows have to come
    from the parser through the real provisions path; hand-inserted rows would
    test the fixture rather than the change.
    """
    corpus = tmp_path / "corpus"
    (corpus / "laws").mkdir(parents=True)
    (corpus / "laws" / "primer.md").write_text(PRIMER_MD, encoding="utf-8")
    (corpus / "laws" / "primer-dup.md").write_text(PRIMER_DUP_MD, encoding="utf-8")
    subprocess.run(["git", "init", "-q"], cwd=corpus, check=True)
    subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t",
                    "add", "."], cwd=corpus, check=True)
    subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t",
                    "commit", "-qm", "[bootstrap] § fixture"], cwd=corpus, check=True)
    db = str(corpus / "catalog.db")
    build(corpus, db)
    return build_app(db_path=db, corpus_root=corpus)


@pytest.mark.parametrize("spec", ["§ 1", "§1", "пар. 1", "§ 1."])
def test_paragraph_specs_parse(spec):
    s = parse_article_spec(spec)
    assert s.article == "§ 1" and s.kind == "para" and s.paragraph is None


def test_article_specs_keep_kind_article():
    assert parse_article_spec("чл. 5, ал. 2").kind == "article"


def test_get_article_returns_the_own_act_paragraph(para_app):
    r = para_app.call_tool_sync("get_article", {"name": "primer", "article": "§ 1"})
    assert r["kind"] == "para_dr" and "По смисъла" in r["text"]


def test_an_amending_paragraph_is_not_reachable_by_a_bare_spec(para_app):
    """DOC has two para_amending § 1 rows; neither may answer `§ 1`."""
    r = para_app.call_tool_sync("get_article", {"name": "primer", "article": "§ 1"})
    assert r["kind"] != "para_amending"
    rows = para_app.call_tool_sync("get_articles", {"name": "primer", "kind": "para_amending"})
    refs = [a["section_ref"] for a in rows["articles"] if a["article"] == "§ 1"]
    assert len(refs) == 2 and len(set(refs)) == 2


def test_two_own_act_paragraphs_with_one_number_are_an_error_not_a_first_row(para_app):
    with pytest.raises(ToolError) as exc:
        para_app.call_tool_sync("get_article", {"name": "primer-dup", "article": "§ 1"})
    assert exc.value.code == "AMBIGUOUS_ARTICLE_SPEC"
    assert len(exc.value.payload["candidates"]) == 2
```

The `call_tool_sync` shape comes from `tests/mcp_server/test_connection_model.py`, and `build_app(db_path=...)` from the `file_catalog` fixture in `tests/mcp_server/conftest.py:112-131`, whose docstring says why a file DB is needed („Per-call `mode=ro` connections (FR-029, via build_app(db_path=)) require a file DB“). Read both before writing this one. There is no `app_handle.get_article(...)` method and no `paragraph_catalog` fixture. `populated_conn` is deliberately not used here: its rows are hand-inserted and carry no `provisions`, so it cannot answer a § lookup at all.

- [ ] **Step 2: Run them and confirm they fail**

Run: `.venv/bin/python -m pytest -q -p no:cacheprovider tests/index/test_provisions_paragraphs.py tests/mcp_server/test_paragraph_addressing.py`
Expected: FAIL (`Provision` has no `kind`; `§ 1` rejected by `_FULL_RE`)

- [ ] **Step 3: Implement to the specification**

Specification the executor must meet: in `index/provisions.py`, track the current section heading while iterating paragraphs (a `## ` heading whose text matches `^(Допълнителн|Преходни|Заключителни)` sets the context; the presence of ` КЪМ ` in the heading text marks `para_amending`; a `## ` heading matching neither resets to `article`), emit one row per `**§ N.**` paragraph with its following non-heading, non-anchor paragraphs appended (the same continuation rule articles use), `article = f"§ {N}"`, `paragraph = None`, `kind` per context, `section_ref` the normalised heading text (whitespace collapsed, case preserved; empty for `article` rows); `_ARTICLE_RE` and every article rule stay byte-identical (the reviewer diffs them). Migration 008 adds `provisions.kind TEXT NOT NULL DEFAULT 'article'`, `provisions.section_ref TEXT` and index `idx_provisions_kind (law_id, article, kind, section_ref)`. In `queries.py`, `_FULL_RE` gains an alternative `^\s*(?:§|пар\.)\s*(\d+[а-я]?)\.?\s*$` (the trailing dot is accepted, matching the parametrised test) mapped to `ArticleSpec(article=f"§ {n}", kind="para")`; the lookup for `kind == "para"` selects rows with `kind IN ('para_dr', 'para_pzr')`, returns the single row or raises `AMBIGUOUS_ARTICLE_SPEC` with candidates `[{"article", "kind", "section_ref", "text_head"}]`. `GetArticleResponse.kind` and `section_ref` are additive (defaults `"article"` and null), `tools.json` bumps to 1.7.0 (or folds into B5's 1.6.0 if in the same PR).

**One existing call site to confirm, not assume.** `article_lookup`'s `ArticleNotFound` retry path runs `_legal_article_sort_key` over `SELECT DISTINCT article`, which now returns `§ N` values as well as numeric ones. Read that function and confirm it does not raise on a non-numeric article; if it does, widen it in this task with its own test, since a mixed address space is what this change creates.

- [ ] **Step 3b: Measure the corpus before shipping the grammar**

Run the new parser over the whole corpus and publish the distribution: how many acts have two or more OWN-ACT (`para_dr` or `para_pzr`) rows sharing one `§ N`, and the histogram of that count. Write it into `docs/research/2026-09-05-paragraph-ambiguity.md` with the query used. Any number is acceptable and none blocks the task; not knowing it is what blocks it, because `get_article(law, "§ N")` raising for an unknown fraction of the corpus is exactly the state Directive 10 exists to prevent. The measurement also tells B11 whether the pilot act is in the ambiguous set.

- [ ] **Step 4: Run the index and MCP suites, the parity checks, and the whole suite**

Run: `.venv/bin/python -m pytest -q -p no:cacheprovider tests/index tests/mcp_server tests/api && .venv/bin/python -m mcp_server.export_tools --check`
Expected: all passed; parity clean.

Then the FR-034 harnesses, **baselines taken BEFORE the change and the checks run after**: `scripts/fr034_verify.py check` reads `.fr034-baseline.json` and `baseline` refuses to overwrite an existing file, so a baseline taken after the change would compare the change against itself. With the pre-change baseline in place, rebuild `catalog.db` (`.venv/bin/python -m index.build`) and run `scripts/fr034_verify.py check` and `article-check`: the article rows must be unchanged (R3/R4/R5 clean, the four known residuals only), which proves the § support did not touch article extraction. R1 and R2 compare with `<`, so the added § rows do not trip them.

- [ ] **Step 5: Commit**

```bash
git add index/ mcp_server/ api/ tools.json docs/api/ tests/index/test_provisions_paragraphs.py tests/mcp_server/test_paragraph_addressing.py docs/research/2026-09-05-paragraph-ambiguity.md
git commit -m "feat(provisions,mcp): § rows keyed by section context with kind and section_ref; § in the address grammar; ambiguity is an error, never first-row"
```

### Task B8: Gazette material parser for promulgated acts

The Gazette material is Word-exported HTML: one `<p>` per paragraph, `<b>` around the `Чл. N.` and `§ N.` anchors, centred `<p>` for headings with a `<br>` between the heading label and its title (`Глава първа<br/>ОБЩИ ПОЛОЖЕНИЯ`, `Раздел I<br/><b>Предмет и цел</b>`), the promulgating decree (`УКАЗ № N ... ПОСТАНОВЯВАМ: ... Подпечатан с държавния печат.`) before the act's own title (`ЗАКОН за обществения транспорт`), and a signature block after the last provision (`Законът е приет от ... Народно събрание на <date> ...`, `Председател на Народното събрание: ...`). Measured on idMat 242220 (535 `<p>`): 484 justified body paragraphs, 24 + 6 centred headings.

**Files:**
- Create: `fetcher/dv/text_parser.py`, `tests/fetcher/dv/test_text_parser.py`
- Fixture: `tests/fixtures/dv/showMaterial-idMat242220-zot.html` (copy of the live capture; about 300 KB)

**Interfaces:**
- Produces: `GazetteAct(title: str, rango: str, decree: str | None, adopted_on: str | None, body_markdown: str, editorial_changes: list[str], structure: StructureReport)`; `parse_promulgated_act(material_html: str) -> GazetteAct`; `StructureReport(source_articles: int, emitted_articles: int, source_paragraphs: int, emitted_paragraphs: int, source_para_signs: int, emitted_para_signs: int)` with `.ok` true only when every pair is equal; `class StructuralGateError(Exception)` raised by `parse_promulgated_act(..., strict=True)`.
- Markdown conventions (must match the corpus so witness diffs are about content): `# <TITLE IN CAPITALS>` as the corpus has it (`# ЗАКОН ЗА ОБЩЕСТВЕНИЯ ТРАНСПОРТ`); `### Глава първа. ОБЩИ ПОЛОЖЕНИЯ`; `#### Раздел I. Предмет и цел`; `## Допълнителна разпоредба` / `## Заключителни разпоредби` / `## Преходни и заключителни разпоредби` in sentence case as the corpus writes them; `**Чл. N.** text`; алинеи and items as separate paragraphs; `**§ N.** text`; **every typographic quote character normalised to ASCII `"`** (see below); the en dash kept; the decree and the signature block excluded from the body and kept as metadata; `*В сила от DD.MM.YYYY г.*` emitted after the title when the ПЗР states the entry-into-force date, matching the lex.bg-derived corpus line.

**The Gazette's quote convention is U+201C and U+201D, not `„…“`.** Measured on the two ДВ material fixtures on `origin/main`:

| fixture | U+0022 | U+201E | U+201C | U+201D |
|---|---|---|---|---|
| showMaterial-idMat300-zid.html | 688 | 0 | 108 | 108 |
| showMaterial-idMat1000.html | 208 | 0 | 0 | 0 |

(the ЗИД fixture stores them as the entities `&ldquo;` and `&rdquo;`, 108 each, which is why a byte grep for the characters finds nothing; the count is after entity decoding). The material opens with U+201C and closes with U+201D. A parser that normalises only the pair this repository writes, `„` and `“`, therefore leaves every U+201D closer in the body, and the corpus is frozen on ASCII `"`, so the rebuilt act would carry mismatched quotes and the witness diff would fill with quote hunks.

One shared constant, used by this parser and by B10's witness normaliser:

```python
GAZETTE_QUOTES = "„“”«»"   # U+201E U+201C U+201D U+00AB U+00BB
_QUOTES = str.maketrans({ch: '"' for ch in GAZETTE_QUOTES})
```

`editorial_changes` records the total count of replaced characters across all five, as `quotes: 216 typographic quotes to ASCII`.

- [ ] **Step 0: Capture the fixture**

`tests/fixtures/dv/showMaterial-idMat242220-zot.html` is not in the repository (`tests/fixtures/dv/` holds eight files, none of them 242220), so without this step every test in this task fails at `read_fixture`, not at the import the plan predicted.

Run: `.venv/bin/python -m fetcher.dv material --id-mat 242220 --cache-dir data/dv/cache`, then copy `data/dv/cache/242220.html` to `tests/fixtures/dv/showMaterial-idMat242220-zot.html` and write a sibling `showMaterial-idMat242220-zot.capture.txt` recording the capture date and the URL. **One material fetch is inside the fetch permission given on 2026-09-05 and is not the gated 12-hour sweep**; this step is not GATED.

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
    from fetcher.dv.text_parser import GAZETTE_QUOTES
    act = _zot()
    # The Gazette uses U+201C and U+201D; asserting only „ and “ would pass
    # while leaving every closer in the body.
    assert not any(ch in act.body_markdown for ch in GAZETTE_QUOTES)
    assert not any(ch in act.body_markdown for ch in "„“”«»")
    assert any(c.startswith("quotes:") for c in act.editorial_changes)

def test_strict_gate_refuses_a_dropped_article(monkeypatch):
    html = read_fixture("showMaterial-idMat242220-zot.html").replace("Чл. 50. ", "Член 50. ", 1)
    import pytest
    with pytest.raises(StructuralGateError):
        parse_promulgated_act(html, strict=True)
```

- [ ] **Step 2: Run them and confirm they fail**

Run: `.venv/bin/python -m pytest -q -p no:cacheprovider tests/fetcher/dv/test_text_parser.py`
Expected: FAIL, `ModuleNotFoundError: No module named 'fetcher.dv.text_parser'`. If instead every test fails inside `read_fixture`, Step 0 was skipped.

- [ ] **Step 3: Implement to the specification**

Specification: use `material_body_html` for the content region, iterate `<p>` in order, classify each: decree paragraphs (everything before the first centred paragraph whose text starts with an act-type word in capitals followed by lowercase words: `^(ЗАКОН|КОДЕКС|НАРЕДБА|ПРАВИЛНИК|ПОСТАНОВЛЕНИЕ|УКАЗ|ТАРИФА|ИНСТРУКЦИЯ)\s+[а-я№]`), the title paragraph (capitalise the whole title for the `#` line, derive `rango` from the first word), centred headings (`Глава` → `###`, `Раздел` → `####`, `Част`/`Дял` → `##`, the ДР/ПЗР headings → `##` in the corpus wording with only the first letter capitalised), anchors (`<b>` text matching `^Чл\.\s*\d+[а-я]?\.` or `^§\s*\d+[а-я]?\.` become `**Чл. N.**` / `**§ N.**`), body paragraphs (one Markdown paragraph each, `<br>` inside a paragraph becomes a line break), the signature block (from the first paragraph matching `^Законът е приет|^Кодексът е приет|^Наредбата е|^Председател|^Министър|^Издаден в` after the last provision, kept as metadata; `adopted_on` parsed from `приет ... на <D month YYYY> г.` with the Bulgarian month table already in `fetcher/bg/metadata.py`). The structural report counts `<p>` whose text starts with `Чл.` against emitted `**Чл.` anchors, `<p>` starting with `§` against emitted `**§`, and all non-decree, non-signature `<p>` against emitted paragraphs. Quotes: translate every character of `GAZETTE_QUOTES` to `"` through the one `str.maketrans` table, count all replacements into one `editorial_changes` entry. Do not touch dashes.

- [ ] **Step 4: Run the tests and the whole suite**

Run: `.venv/bin/python -m pytest -q -p no:cacheprovider tests/fetcher/dv && .venv/bin/python -m pytest -q -p no:cacheprovider --ignore=tests/perf`
Expected: all passed.

- [ ] **Step 5: Commit**

```bash
git add fetcher/dv/text_parser.py tests/fetcher/dv/test_text_parser.py tests/fixtures/dv/showMaterial-idMat242220-zot.html tests/fixtures/dv/showMaterial-idMat242220-zot.capture.txt
git commit -m "feat(dv): Gazette material parser for promulgated acts with a strict structural gate and recorded editorial changes"
```

### Task B9: frontmatter for a Gazette-rebuilt act

**Files:**
- Create: `fetcher/dv/metadata.py`, `tests/fetcher/dv/test_metadata.py`

**Interfaces:**
- Consumes: `parse_material_header` (merged), `GazetteAct` (B8), `Provenance` / `derive_grade` / `events_of` (B2), `fetcher.bg.assembler.assemble_file` and `generate_slug` (merged), and from `fetcher.bg.metadata` the month table **`BG_MONTHS`** and **`MetadataParser._build_eli`**, which is a `@staticmethod` on `class MetadataParser`, not a module-level function: `from fetcher.bg.metadata import BG_MONTHS, MetadataParser` then `MetadataParser._build_eli(rango, issue_date, slug)`. Promoting it to a module function instead is acceptable and is an unprotected refactor; do one or the other, do not copy it.
- Produces: `build_frontmatter(header: MaterialHeader, act: GazetteAct, *, id_mat: int, existing: dict | None, chain_scanned_through: dict | None, checked_through: dict) -> dict` returning the full frontmatter: for an act already in the corpus, `identificador`, `eli`, `category`, `titulo` (corpus form) come from `existing`; for a ДВ-only act, `identificador = f"dv-{id_mat}"` (D-064) and `eli` from `_build_eli`; `fuente = "dv.parliament.bg"`; `fecha_publicacion` = the issue date; `dv_issue`, `dv_year` from the header; `effective_date` from the ПЗР entry-into-force sentence when present (`влиза в сила от D month YYYY` to ISO) else null; `estado = "vigente"`.
- **`amendment_history` keeps exactly the rows the existing act had**, promulgation row included, each `pending` unless verified. The promulgation row is not given `applied: "replayed"`, because it is not an event at all: it is the base. The DERIVATION excludes it through `events_of`, which is the same helper B2, B3 and B6 use, so a single-issue act's event multiset is empty and rule 2 can fire.
- `provenance` = the block with `base = Base(source="dv_html", state="rebuilt", locator={"id_mat": id_mat}, issue, year, frozen_at=<today>, audited=True, declared_at=None, chain_scanned_through, chain_inherited_before=None, uncertainty=[])`, the grade from `derive_grade(base, events_of(fm, base), chain_scan_complete=(chain_scanned_through matches checked_through on issue and year), divergences_unadjudicated=0)`. Divergences are zero because the caller only builds frontmatter after adjudication reached zero.

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
    # The promulgation row stays in the history (FR-020 and history() read it)
    # and is excluded from the derivation by events_of, which is what lets a
    # single-issue act reach grade A.
    assert fm["amendment_history"] == [{"dv": "32/2026", "date": "2026-04-01"}]
    assert fm["provenance"]["events_pending"] == 0
    assert fm["provenance"]["pending_items"] == []

def test_dv_only_act_gets_the_d064_identifier():
    html = read_fixture("showMaterial-idMat242220-zot.html")
    fm = build_frontmatter(parse_material_header(html), parse_promulgated_act(html), id_mat=242220, existing=None,
                           chain_scanned_through=None, checked_through={"issue": "32", "year": 2026, "date": "2026-04-01"})
    assert fm["identificador"] == "dv-242220" and fm["eli"].startswith("/eli/bg/закон/2026/4/1/")
    assert fm["provenance"]["grade"] == "B-pending"  # chain scan not complete for a fresh act
    assert "chain scan incomplete" in fm["provenance"]["pending_items"]
```

- [ ] **Step 2: Run them and confirm they fail**

Run: `.venv/bin/python -m pytest -q -p no:cacheprovider tests/fetcher/dv/test_metadata.py`
Expected: FAIL, `ModuleNotFoundError: No module named 'fetcher.dv.metadata'`

- [ ] **Step 3: Implement to the specification.** The promulgation-row question is settled by Global Constraints amendment note 1: `amendment_history` for a single-issue act stays as the corpus had it, because FR-020 and `history()` read it; the promulgation is the base in the provenance block; the filter that separates them is `provenance.model.events_of`, called here and nowhere reimplemented.

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
- Modify: `fetcher/dv/__main__.py` (subcommand `rebuild`), `tests/fetcher/dv/conftest.py` (a `read_golden` helper)
- Fixture: `tests/fixtures/golden/zot-snapshot.md` (Step 0)

**Interfaces:**
- Consumes: `fetch_material` with the cache, `parse_promulgated_act(strict=True)`, `build_frontmatter`, `assemble_file`, `corpus_gate.write_act`, **`corpus_commit.commit_corpus_change`** (Task B0, not `refresh._git_commit_typed`, which hardcodes the lex.bg `Source-Id` and `Norm-Id`).
- Produces: `python -m fetcher.dv rebuild --id-mat M --law-id SLUG --corpus ROOT --stage DIR --summary PATH [--cache-dir DIR] [--commit]`.
- **`--summary` supplies what B9 requires.** `build_frontmatter` takes `chain_scanned_through` and `checked_through` as required keyword arguments, and neither can be invented at the command line without inviting a false currency claim. The command reads both from the act's row in `acts-summary.csv` (`chain_scanned_through` and `checked_through` / `checked_through_date`, the columns Tasks A2 and A4 Step 0 add), so the value the map measured is the value the frontmatter records. A missing row, or a `--summary` pointing at a map run older than the cache, is an error and exits non-zero.
- Without `--commit`: writes `DIR/<slug>.md` (the candidate), `DIR/<slug>.witness-diff.md` (a normalised unified diff against the committed corpus file: whitespace collapsed, ASCII and typographic quotes and dashes unified, lex.bg consolidation notes `(В сила от ...)` and `(Изм. ...)` stripped before diffing), and `DIR/<slug>.adjudication.yaml` listing every diff hunk with `lane: null`.
- With `--commit`: **reads the existing adjudication file and does not regenerate it** (regenerating would discard the lanes the reviewer just set, which is the whole point of the file); refuses unless every hunk has a lane in `{source_pathology_witness, source_pathology_gazette, replay_defect, risk_signal, editorial}` and none is `replay_defect`; then writes the file through `write_act` (which runs the corpus-integrity checks), commits `[popravka]` with `Source-Id: dv-<idMat>`, `Source-Date: <issue date>`, `Norm-Id: <identificador>` (Surface 5 preflight), and prints the derived grade.
- `witness.py` exposes `normalise(text) -> str` and `diff_hunks(a, b) -> list[Hunk(header, lines)]`.

- [ ] **Step 0: Copy the golden snapshot into fixtures**

`tests/fixtures/golden/zot-snapshot.md` is referenced by Step 1's test and would otherwise only be created in Step 3, so every test fails at `read_golden` before reaching the code under test. Copy `laws/zakon-za-obshtestveniya-transport.md` at `origin/main` into it, with a sibling note recording the commit it came from. Add `read_golden(name)` to `tests/fetcher/dv/conftest.py` next to `read_fixture`, resolving `tests/fixtures/golden/`, rather than traversing out of the `dv` fixture directory with `read_fixture("../golden/...")`.

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
import csv
from pathlib import Path

import yaml

from fetcher.dv.__main__ import main
from .conftest import FakeSession, read_fixture, read_golden

SUMMARY_ROW = {"law_id": "zot", "chain_scanned_through": "2026/81",
               "checked_through": "2026/81", "checked_through_date": "2026-09-04"}


def _stage_argv(corpus: Path, stage: Path, summary: Path) -> list[str]:
    return ["rebuild", "--id-mat", "242220", "--law-id", "zot",
            "--corpus", str(corpus), "--stage", str(stage), "--summary", str(summary)]


def _fixture_corpus(tmp_path: Path) -> tuple[Path, Path, Path, FakeSession]:
    corpus = tmp_path / "corpus"
    (corpus / "laws").mkdir(parents=True)
    (corpus / "laws" / "zot.md").write_text(read_golden("zot-snapshot.md"), encoding="utf-8")
    summary = tmp_path / "acts-summary.csv"
    with summary.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(SUMMARY_ROW))
        w.writeheader(); w.writerow(SUMMARY_ROW)
    session = FakeSession(by_param={("idMat", 242220): read_fixture("showMaterial-idMat242220-zot.html")})
    return corpus, tmp_path / "stage", summary, session


def test_rebuild_stages_candidate_diff_and_adjudication_without_committing(tmp_path: Path):
    corpus, stage, summary, session = _fixture_corpus(tmp_path)
    target = corpus / "laws" / "zot.md"
    before = target.read_bytes()
    assert main(_stage_argv(corpus, stage, summary), session=session) == 0
    assert (stage / "zot.md").exists() and (stage / "zot.witness-diff.md").exists()
    adj = yaml.safe_load((stage / "zot.adjudication.yaml").read_text(encoding="utf-8"))
    assert adj["hunks"] and all(h["lane"] is None for h in adj["hunks"])
    assert target.read_bytes() == before, "nothing is written to the corpus without --commit"


def test_commit_refuses_open_or_replay_defect_lanes(tmp_path: Path):
    """Design 4.2 rule 0 made real: a rebuilt act with an open or defective
    divergence is never a committed file."""
    corpus, stage, summary, session = _fixture_corpus(tmp_path)
    target = corpus / "laws" / "zot.md"
    before = target.read_bytes()
    argv = _stage_argv(corpus, stage, summary)
    assert main(argv, session=session) == 0

    adj_path = stage / "zot.adjudication.yaml"
    adj = yaml.safe_load(adj_path.read_text(encoding="utf-8"))
    assert len(adj["hunks"]) >= 2, "the pilot diff has at least the § 1 omission and a style hunk"

    # 1. Nothing adjudicated: refuse, corpus untouched.
    assert main(argv + ["--commit"], session=session) != 0
    assert target.read_bytes() == before

    # 2. All lanes but one: still refuse. An open hunk is an open hunk.
    for hunk in adj["hunks"]:
        hunk["lane"] = "editorial"
    adj["hunks"][0]["lane"] = None
    adj_path.write_text(yaml.safe_dump(adj, allow_unicode=True, sort_keys=False), encoding="utf-8")
    assert main(argv + ["--commit"], session=session) != 0
    assert target.read_bytes() == before

    # 3. Every lane set but one is a replay_defect: refuse. The parser is
    #    wrong, and a wrong parser must not reach the corpus however well
    #    documented.
    adj["hunks"][0]["lane"] = "replay_defect"
    adj_path.write_text(yaml.safe_dump(adj, allow_unicode=True, sort_keys=False), encoding="utf-8")
    assert main(argv + ["--commit"], session=session) != 0
    assert target.read_bytes() == before
```

Steps 2 and 3 of that test only work because **`--commit` reads the existing adjudication file and does not regenerate it**; a `--commit` that re-staged would overwrite the lanes it just read. That is stated in the Interfaces block above and is the interface decision this test forces.

- [ ] **Step 2: Run them and confirm they fail**

Run: `.venv/bin/python -m pytest -q -p no:cacheprovider tests/fetcher/dv/test_witness.py tests/fetcher/dv/test_rebuild.py`
Expected: FAIL, missing modules.

- [ ] **Step 3: Implement to the specification.** `normalise` uses the **same `GAZETTE_QUOTES` constant B8 defines** (U+201E, U+201C, U+201D, U+00AB, U+00BB to `"`), maps the en dash and the em dash to `-`, removes `\(В сила от [^)]*\)` and `\((?:Изм|Доп|Нов|Отм)\.[^)]*\)`, and **collapses whitespace LAST**: run the consolidation-note removal first, or `(В сила от ...)` leaves a double space behind and the normalised texts of the witness test never compare equal. `diff_hunks` uses `difflib.unified_diff` on paragraph lists and groups by hunk header.

- [ ] **Step 4: Run the tests and the whole suite**

Run: `.venv/bin/python -m pytest -q -p no:cacheprovider tests/fetcher/dv`
Expected: all passed.

- [ ] **Step 5: Commit**

```bash
git add fetcher/dv/rebuild.py fetcher/dv/witness.py fetcher/dv/__main__.py tests/fetcher/dv/conftest.py tests/fetcher/dv/test_rebuild.py tests/fetcher/dv/test_witness.py tests/fixtures/golden/zot-snapshot.md tests/fixtures/golden/zot-snapshot.source.txt
git commit -m "feat(dv): rebuild command with staging, offline witness diff, adjudication lanes and a gated commit"
```

### Task B11: the pilot, Закон за обществения транспорт (procedure, no new code)

**Preconditions: B5, B5b, B6, B7 and B10 merged; the corpus-integrity CI job green; `catalog.db` rebuilt; and `chain_scan_complete` established for this act.**

**This task is GATED on the body scan and cannot print grade A without it.** Rule 2 of design 4.2 requires `chain_scan_complete`, which is `base.chain_scanned_through == checked_through`, which only the ДВ-side body scan establishes; design 7 step 4 says so for the pilot in terms („the body scan of 5.2 has run over ДВ бр. 32/2026 onward for this act“). The act was promulgated in бр. 32/2026, so its lifetime window runs from бр. 32/2026 to the latest issue. Two ways to satisfy it, both owner decisions:

1. **The full body fetch** (`python -m fetcher.dv bodies --materials data/dv/materials.jsonl --cache-dir data/dv/cache`), about 12 hours in a new session, the gated run of A4 Step 4. It satisfies every act's window at once.
2. **A scoped fetch over this act's window** (`python -m fetcher.dv bodies --materials data/dv/materials.jsonl --cache-dir data/dv/cache --from-issue 2026:32`), about 50 issues and about 900 materials, roughly 15 minutes at one request per second. The `--from-issue` flag is added by Task A2 Step 4. This satisfies the pilot act and no other, which is honest: `chain_scanned_through` is written per act from what was actually read.

Until one of them has run, **the pilot commits at `B-pending` with `chain scan incomplete` as the single open item.** That is a truthful and testable intermediate: every other acceptance criterion of design section 7 can be met and verified, and the act rises to A on the next map run once the scan lands. Do not fake the scan mark to reach A.

- [ ] **Step 1: Stage.** `.venv/bin/python -m fetcher.dv rebuild --id-mat 242220 --law-id zakon-za-obshtestveniya-transport --corpus . --stage data/dv/staging --summary docs/research/2026-09-05-dv-coverage-map/acts-summary.csv --cache-dir data/dv/cache`. Expected: exit 0, three files in `data/dv/staging/`. The currency values come from the map row, not from the command line.
- [ ] **Step 2: Read the witness diff in full.** Expected hunks, each adjudicated into its lane in `zakon-za-obshtestveniya-transport.adjudication.yaml`:
  - the twelve definitions of § 1 (`source_pathology_witness`: lex.bg omitted them);
  - the two `й`/`и` spellings (`source_pathology_witness`);
  - the Latin `E` in „Eдинен“ if the parser did not already normalise it (`source_pathology_gazette`, recorded as an editorial change);
  - consolidation notes and dash style (`editorial`);
  - **the `Проект: 51-602-01-7/04.02.2026 г.` line** on line 24 of the committed snapshot, a lex.bg artifact with no Gazette counterpart. Lane `source_pathology_witness` if the owner reads it as lex.bg chrome, `editorial` if as a note we choose not to carry; either is defensible, and the owner picks one in the PR;
  - **the tail of the file, a long list of EU regulations.** Expect it to diff on line wrapping and on the dash and quote styles inside the citation titles, not on content; any hunk in that tail that adds or removes a whole regulation is not style and is investigated.

  Any hunk outside this list is investigated before it gets a lane; a hunk that shows the parser dropping or reordering text is `replay_defect` and stops the pilot until the parser is fixed and the stage re-run.
- [ ] **Step 3: Commit through the gate.** Re-run with `--commit`. Expected: `write_act` accepts (zero corpus-integrity violations), one `[popravka]` commit with `Source-Id: dv-242220`, `Source-Date: 2026-04-01`, `Norm-Id: 2137259781`, and the printed grade `A` if the body scan has run, `B-pending` with `chain scan incomplete` if it has not.
- [ ] **Step 4: Rebuild the index incrementally** (`.venv/bin/python -m index.build --incremental`) and verify: `SELECT provenance_grade FROM laws WHERE law_id='zakon-za-obshtestveniya-transport'` matches the grade Step 3 printed; `get_article("zakon-za-obshtestveniya-transport", "§ 1")` returns the twelve definitions with `kind = para_dr`; `get_law` carries the grade, with no `PROVENANCE_GRADE` warning at A and one warning at B-pending; the REST route agrees; the cf act payload carries `provenance_grade` and `checked_through` (B5b); `python -m corpus_integrity` is green.
- [ ] **Step 5: Verify against the standing harnesses.** `scripts/fr034_verify.py check` and `article-check` show ЗОТ's article rows unchanged in count (106) and no loss elsewhere; `scripts/structure_gaps.py --warn` no longer flags the act.
- [ ] **Step 6: Open the PR** with the adjudication file and the witness diff attached; merge with a merge commit.

### Task B12: governance close-out

- [ ] **Step 0: One-line design edit.** `docs/plans/2026-09-05-dv-graded-source-design.md` section 4.1, in the paragraph beginning „The base of the act carries its own record“, gains one sentence: **„The promulgation row of `amendment_history` is that base record, not an event: the event multiset of 4.2 is the history minus the row whose `dv` is `<base.issue>/<base.year>`.“** The design is on `origin/main` and this plan's PR is docs-only for the plan file, so the edit lands here rather than there. Global Constraints amendment note 1 carries the same sentence in the meantime.
- [ ] **Step 1:** `docs/frs/INDEX.md`: FR-024 progress (P0 complete, P1 pilot done), FR-042 (pilot closes the confirmed instance; 32 remaining candidates routed to grade B audits), FR-026 note (§ rows carry `kind` and `section_ref`; the annex classification reuses the columns), FR-038 note (§ ambiguity is an error, never first-row), FR-032 note (the cf label-or-skip decision of design 4.3 is still open and now also governs `provenance_grade`).
- [ ] **Step 2:** `docs/sync/DECISIONS.md`: D-065, the pilot outcome and the adjudication lanes used; D-066 if the Surface 5 preflight settled the commit form differently from the proposal; D-067 recording that `provenance/derive.py` is the single derivation and `provenance.model.events_of` the single event filter, so a future reviewer sees the C10 hazard was closed deliberately.
- [ ] **Step 3:** `docs/sync/CORPUS-STATUS.json`: per-grade act counts (`grades: {A: 1, B: 0, B-pending: n, C: m}`), `text_complete_vs_gazette` stays false until FR-042's candidates are audited.
- [ ] **Step 4:** `docs/sync/ACTIVE.md` banner; the takt-plan follow-up FU-002 can be closed against the pilot commit.
- [ ] **Step 5:** Commit and open the PR.

---

## Self-review (plan against the design)

**Spec coverage.** Design 4.1 and 4.2: Task B2 (model, `events_of`, total derivation, domain constraints) and B3 (INV-010), with the promulgation-row reading recorded as Global Constraints amendment note 1 and carried into the design by B12 Step 0. 4.3: B1 (Surface 2 block), B4 (index), B5 (MCP/REST, warning shape per D-064, plus the `x-disclaimer` metadata the design's last MCP clause requires), **B5b (cf plane)**, B7 (§ addressing). 5.1: merged (PR #29, PR #32); the `bodies` command is on `feat/dv-coverage-map` and gains `--from-issue` in A2. 5.2: A2 (body scan), A3 (candidates for the uncited acts), A4 (run), with the `pdf-era-inventory.csv` of D-064 already specified to the coverage-map agent. 5.3: the deterministic resolver is on `feat/dv-coverage-map` and exercised by A2; **its reasoning pass over `unresolved.csv` is A5**, which reports but does not close the `segmenter-residue.csv` number of 5.2 (gap 5). 5.4: B8 for promulgated acts, A1 for instruction segmentation; lowering to kernel operations is FR-003 and out of scope by the design's non-goals. 5.5: out of scope (Phase 4). 5.6: the base structural audit for grade B acts is NOT in this plan; it is a P3 deliverable per the design's sequencing table and is listed as a gap to plan next. 5.7: GATED (owner). 5.8: PR #23 Part II (in flight) plus B3, with the gate-side waiver reconciliation stated as a precondition on B6. 5.9: the editorial-changes list is produced by B8 per act; the corpus-wide report file is deferred to P2 and noted as a gap. Section 7 (pilot): B11 step by step, marked GATED on the body scan with a stated B-pending intermediate. Section 8: P0 = A1 to A5 plus Part II; P1 = B0 to B12 including the backfill (B6) the review required in the P1 exit gate. Section 11 / D-064: warning shape (B5), identifier (B9), findings as data (A2, A4), inventory (A4 via the agent's addendum), reading order (P3, out of scope). Surface 5 commit format: B0 builds the one module that writes the trailers, B1 Step 4 names it.

**Gaps, stated.** Five, all deliberate:

1. **The grade B base structural audit** (design 5.6): P3 by the design's own sequencing table, its own plan.
2. **The corpus-wide editorial-changes report** (design 5.9): P2; B8 produces the per-act list this plan needs.
3. **The `cf-worker` response shape** for non-A acts (mirror the `PROVENANCE_GRADE` warning, or skip): design 4.3 says to decide it together with FR-032's implicit rows, so it is an owner decision recorded in B5b and in B12 Step 1, not implemented here. B5b closes the floor exposure by putting the grade in the act payload, so the Provenance floor is satisfied from the moment B6 lands even before that decision is taken.
4. **The body fetch and the body pass of the map** are GATED by owner instruction (2026-09-05), and B11 is GATED behind whichever fetch satisfies its window.
5. **The reasoning pass over `segmenter-residue.csv`** (design 5.2's P2 exit gate): the file exists only after the gated body pass, and its rows carry neither `kind` nor `law_id`, so the applier for them is a different shape. A5 reports the residue count next to its own number and says which is which; clearing it to zero is P2.

**Placeholder scan.** No placeholders and no deferral markers anywhere in the file, and every test fixture the plan names is now written out where it is used rather than referenced by a name that exists nowhere: `uncited_corpus` in `tests/scripts/conftest.py` (A3, shared with A5), `read_golden` and `zot-snapshot.md` (B10 Step 0), `PRIMER_MD` and `PRIMER_DUP_MD` (B7), `ACT_MD` (B5), the two markdown constants in B5b. B10's second test is written out in full, because it is the gate that makes design 4.2 rule 0 real and leaving it to the executor would leave the pilot's most consequential invariant untested.

**Interfaces quoted, not remembered.** Every function, header and fixture this plan names was read on the branch it lives on and quoted with its file and line: `build_act_payload` and `_check_act_articles` (B5b), `UNRESOLVED_FIELDS` and the uncited row the writer emits (A5), `SUMMARY_FIELDS` / `COVERAGE_FIELDS` / `OMISSION_FIELDS` / `DISPUTE_FIELDS` (A2, A4, B6), the merged `derive_grade` and its property tests (B2 Step 6), `[tool.setuptools.packages.find]` (B2 packaging), `populated_conn` and `file_catalog` (B5, B7), `refresh._git_commit_typed` (B0). Two earlier defects came from inferring an interface instead of opening the file, which is why this is now a rule of the plan rather than a habit.

**Type consistency.** `Base` (ten fields plus `uncertainty` and the `promulgation_cited` property), `Event`, `Provenance` (with `pending_items`, written by `to_frontmatter` and read back by `from_frontmatter`), `events_of(fm, base)` (which removes exactly one row, the first that matches after leading-zero normalisation), `derive_grade(base, events, *, chain_scan_complete, divergences_unadjudicated, promulgation_cited) -> Derivation(grade, pending_items)` are used identically in A2 (through the map's import), B2, B3, B6 and B9, and `provenance/derive.py` is the only implementation after B2 Step 6. The two currency marks keep their two shapes everywhere: `base.chain_scanned_through` is `{issue, year}`, `checked_through` is `{issue, year, date}`, the comparison is on `(issue, year)`, and the index projects the date alone. `Provision.kind` values (`article`, `para_dr`, `para_pzr`, `para_amending`) plus `section_ref` are the same in B7's parser, migration 008 and grammar. `write_act(path, frontmatter, body, *, source=SourceRef(kind, ident))` matches PR #23 Part II Task 6 and is used in B6 and B10. `commit_corpus_change(path, commit_type, title, *, norm_id, source_id, source_date, cwd)` is B0's and is called by B6, B10 and (wrapped) `refresh.py`. `fetch_materials_page` / `fetch_material` / `cached_material` / `sections.selected` are the merged names (PR #29, #32, `feat/dv-coverage-map`). `Resolver.resolve(title, *, section=None, dv_citation=None) -> Resolution(law_id, candidates, score, flags, method)` has **five** fields, verified against `feat/dv-coverage-map:fetcher/dv/resolver.py`. CSV headers are quoted from `SUMMARY_FIELDS`, `COVERAGE_FIELDS`, `OMISSION_FIELDS`, `UNRESOLVED_FIELDS` and `DISPUTE_FIELDS` as merged, with every addition named by the task that makes it.

**Model policy.** Every task here is implementation to a fixed specification and runs on Opus 5 with a fresh Opus 5 reviewer per task; the whole-branch review before each merge runs on the session model.
