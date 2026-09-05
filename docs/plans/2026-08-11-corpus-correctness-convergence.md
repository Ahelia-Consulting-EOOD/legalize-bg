# Corpus Correctness Convergence Plan

> **For agentic workers:** REQUIRED SUB-SKILL: `superpowers:subagent-driven-development` to
> execute this plan task-by-task. Process design follows `legal-corpus:iterative-doc-train`;
> read that skill before dispatching any leg. Steps use checkbox (`- [ ]`) syntax.

> **Amended 2026-09-05 for the graded source model (D-059).** The owner adopted approach C: acts are
> rebuilt from Държавен вестник wherever the Gazette text is online (grade A) and graded B or C
> otherwise; see `docs/plans/2026-09-05-dv-graded-source-design.md` and the CPD
> `docs/cpd/CPD-2026-09-05-graded-source-model.md`. Parts I to IV stand unchanged: the machine floor,
> the write gate and the per-class ladders are source-agnostic and are the base of grades B and C.
> Part V's single sweep is re-scoped to the acts that keep a lex.bg base; grade A acts are repaired by
> rebuild. A tenth class, C10 provenance integrity, is added. Owner decisions O-5, O-6, O-8, O-9, O-10
> and O-11 are resolved by PR #25 and noted in place.

**Goal:** Drive the corpus to a state where every article and alinea address resolves to
exactly the text the act carries at that address, prove it by exhaustive corpus-wide checks
that hard-fail in CI, and make the guarantee binding on every future ingestion path,
including ДВ, not only lex.bg re-scrapes.

**Architecture:** Three layers, in this order. (1) A **machine floor**: one corpus-integrity
module with per-class detectors that runs over every act, needs no `catalog.db`, and hard-fails
in CI. (2) A **single write gate**: no code path may write a corpus `.md` except through one
function that asserts the invariants, so every source adapter (lex.bg today, ДВ tomorrow,
municipal later) inherits the guarantee by construction rather than by discipline. (3) **Per-class
remediation** driven by a convergence train with adjudication, paper pre-checks and an invariant
catalogue, so fixes stop manufacturing the next round's defects.

**Tech Stack:** Python 3.12, pytest, SQLite (read-only for measurement only), GitHub Actions.
No new runtime dependencies.

## Global Constraints

Copied verbatim from the authorities that bind this work. Every task's requirements implicitly
include this section.

- **Zero errors is the acceptance standard.** A single wrong article address is a defect, not a
  statistic (`docs/process/OWNER-DIRECTIVES.md` D-9).
- **Detection precedes repair.** No fix, sweep or closure before exhaustive corpus-wide detection
  for that class has run over every act (D-10).
- **Write-time enforcement only.** No query-time filtering, no suppression lists, no consumer-side
  exclusion, including temporarily (D-11).
- **Gates block or they do not exist.** Report-only mode requires a dated waiver naming its expiry
  condition (D-12).
- **Every defect class registered before work proceeds** as an FR row plus a follow-up entry (D-13).
- **One repair sweep per pipeline generation**; all parser fixes land before the sweep (D-14).
- **The five correctness properties** are defined in `docs/process/COVERAGE-FLOOR.md` section
  "Correctness floor": no fabricated address, no lost address, no ambiguous address, no
  contaminated or truncated text, no silent uncertainty.
- **Protected surfaces** (`fetcher/bg/text_parser.py`, `index/provisions.py`, the SQLite schema,
  MCP tool signatures, commit message format) require an IMPLEMENTATION-PREFLIGHT before change,
  per `.claude/CLAUDE.md`.
- **Corpus `.md` files are written only by the pipeline.** Never hand-edited, never hand-committed.
- **Bulgarian text uses „…“** (U+201E opener, U+201C closer); verify balance whole-file.
- **Any branch carrying corpus commits merges with a merge commit, never squash** (FR-020 derives
  version boundaries from per-act trailers).
- **Test runner is `.venv/bin/python -m pytest`**; system python cannot import the code.
- **Never run `scripts/fr034_verify.py baseline`**; `.fr034-baseline.json` and
  `.article-baseline.json` are irreplaceable pre-repair floors.

---

## Part I — Train design

This corpus has already run the naive loop and shown its signature: FR-034 fixed the flattening
and its own fix **amplified** the ЗЗД phantom (implicit алинеи were emitted onto an article that
does not exist); FR-030 was implemented in full and then retired after full-corpus validation
proved it destroyed more than it repaired; a class declared out of scope in one FR reappeared as
another FR's Defect C. Those are the documented failure signatures of an unconverging train:
*findings attack the previous round's fixes*, *closed issues reopen*, *individually-correct fixes
collide*. The train below is designed against exactly those.

### I.1 Roles

Distinct roles, never merged in one agent:

| Role | Does | Never does |
|---|---|---|
| **Orchestrator** | sequences legs, holds the catalogue, records rulings | writes code, takes design decisions inside a leg |
| **Detector author** | implements a class detector to an adjudicated spec | decides what counts as a defect |
| **Adjudicator** | turns each class into a decision procedure + acceptance test | implements |
| **Attacker** (2 to 4 per class) | refutes the decision procedure **on paper**, before code | proposes replacements |
| **Fix writer** | implements the parser change for one class | resolves ambiguity by improvising; ambiguity becomes a contested row |
| **Reviewer, closed lens** | clause-level fidelity: does the fix do exactly what the ruling said | explores |
| **Reviewer, open lens** | hostile: corner acts, crossings, what the ruling forgot | checks fidelity |

Model policy carried from the anchor-integrity handover: execution agents Opus 5; final
whole-branch review on a different model for decorrelation.

### I.2 The unit of work is a class, and every class runs the same five stages

**Plan → Research → Solve → Apply → Guarantee.** No stage may be skipped, and the order is
load-bearing:

1. **Plan.** Adjudicate the class into a *decision procedure*: the exact rule that separates a
   real address from a defect, written as a complete enumeration with an **explicit excluded
   boundary** (what the rule deliberately does not decide). Produce an acceptance test: the
   concrete walk that must close.
2. **Research.** Attack the decision procedure on paper with 2 to 4 independent attackers, each
   given real corpus text, before a line of code exists. This is the step whose absence cost
   FR-030 a full implementation cycle. Attackers must produce counter-examples from the corpus,
   not opinions. Amend the procedure; re-attack until an attack round produces nothing new.
3. **Solve.** Implement the detector first, then the fix. The detector is what makes the class
   measurable, and Directive 10 forbids repairing before it exists. TDD, one class per leg.
4. **Apply.** The fix changes the parser; the corpus is only repaired by the single sweep in
   Part V. Applying is therefore: land the parser change, re-run the detector, and record the
   remaining count as the pre-sweep floor for that class.
5. **Guarantee.** Write the invariant catalogue entry (I.3) and wire the check into the write
   gate and CI. A class is not closed until its check would refuse the write that reintroduces it.

### I.3 The invariant catalogue

`docs/process/INVARIANT-CATALOGUE.md`. Every closure becomes a numbered entry. An entry without
a NOT-covered boundary is treated as actively misleading and is rejected in review.

```markdown
### INV-007: superscript article indices are distinct addresses

- invariant: an article index carrying a superscript suffix resolves to an address distinct
  from its base article, and neither shadows the other.
- covered space: all acts in the 5 browsable categories; suffix forms `SUP>N`, `<sup>N</sup>`,
  and the canonical form chosen in ADJ-004.
- NOT covered: superscript suffixes on § markers; suffixes in annex/table cells; any act whose
  source markup does not distinguish the suffix at all (enumerated: none as of 2026-08-11).
- dependency anchors: INV-003 (article-key uniqueness), INV-009 (tag-remnant absence).
- last verified: <commit>, detector run <date>, violations 0 / 3,624 acts.
- re-runnable enumeration: `python -m corpus_integrity --check superscript --enumerate`
```

### I.4 Crossed tests: the classes are not independent

The dominant late-stage defect class is *individually-correct fixes colliding*. This corpus has
already produced one such collision (implicit алинеи emitted onto a phantom article). Semantic
dependencies here mean **classes that touch the same address space or the same paragraph state**:

| Pair | Why they collide | Crossed test required |
|---|---|---|
| C6 headings × C1 anchors | anchor rules keyed on heading state are unreliable while heading state leaks to EOF | run C1's acceptance test on acts fixed by C6, before and after |
| C4 tag remnants × C5 collisions | fixing superscripts **splits** keys, changing the collision census | re-run C5 detection after every C4 landing; the count must fall, never rise |
| C1 phantoms × C7 implicit rows | implicit alinea emission amplifies a phantom into several fabricated addresses | assert zero implicit rows on any address C1 removes |
| C2 citation-as-alinea × C7 implicit rows | both decide which paragraphs become alineas | crossed on the pre-1974 doctrinal acts and on annex-bearing acts |
| C3 chrome × C1 anchors | chrome headlines manufacture article anchors | C1 detection re-run after chrome removal |

Rule: after any class lands, every class sharing a dependency anchor re-runs its acceptance test.
A rising count in a neighbouring class blocks the landing.

### I.5 Assurance matrix

`docs/process/ASSURANCE-MATRIX.md`: surfaces down, lenses across, each cell holding the commit at
which that surface was last swept for that lens. Surfaces: fetch, parse, frontmatter, index,
export, serve, **records**. Lenses: the five correctness properties, plus record-truthfulness.
Adding a lens marks every surface unswept for it, which is the mechanism that prevents a new
defect class from being quietly assumed absent elsewhere.

### I.6 Two decorrelated review tracks

Every fix leg is reviewed twice, by different models: a **closed-lens** track checking one row
per changed rule against the quoted ruling, and an **open-lens hostile** track walking corner acts
and crossings. Their trajectories are read separately. Where the tracks contradict each other,
neither wins by authority: **walk the disputed act and let the walk decide**, then record the
resolution as an honest override in place.

### I.7 Convergence metrics and the exit band

Recorded per round in the plan's progress ledger:

- **injection ratio** = findings attacking this round's fixes ÷ this round's dispositions. Target
  below 0,3; the measured failure baseline was 0,64 to 0,89.
- **reopened closures** — target 0. Any reopening triggers a catalogue-entry review, because a
  reopening means a NOT-covered boundary was wrong.
- **detector violation counts per class** — the only number that may be cited as closure, and only
  at zero.
- **inside/outside share** — findings inside the enumerated space versus outside it. Rising outside
  share means discovery is still running and the class is not ready to close.

**Exit band.** A class exits when its detector reports zero over all 3,624 acts, both review tracks
return zero critical and zero important findings, its catalogue entry carries a boundary, and its
check hard-fails in CI. Editorial findings do not block exit and are cleared in one final pass.

### I.8 Honesty controls, binding on every leg

- Every claim of a fix landing is verified on disk before it is written in a commit message or a
  status line. Commit messages never claim unlanded changes.
- Whitespace-normalise before grepping legal prose; line-wrapped citations produce false refutations.
- Percentages and rates are diagnostic only. Closure is a count, and the count is zero.
- A record that falls states why, in place. No silent supersession.
- Bulgarian legislative text comes only from this corpus or this project's own pipeline; never
  from aggregators or search snippets, and „lex.bg is blocked“ is never a stopping point.

## Part II — Phase 0: the machine floor

Directive 10 makes this the precondition for everything else. Nothing in Part III may start
until Part II is merged and green.

**Design decisions, fixed here so no leg re-litigates them:**

1. **No `catalog.db` dependency.** The checker reads the committed Markdown tree only. This is
   what lets it run in CI on every pull request, which is where the current suite fails: 21
   real-corpus tests self-skip in CI because the database is absent.
2. **Equality, not thresholds.** Waivers enumerate exact acts. A violation on a non-waived act
   fails the run **and** a waived act that no longer violates fails it too, so the waiver file
   cannot rot into a permanent amnesty.
3. **Hard fail.** Exit code 1 on any violation. There is no report mode (Directive 12).
4. **Deterministic ordering** in all output, so a run diff is reviewable.
5. **One check protocol**, so every later class plugs in without touching the runner.

### File structure

- Create `corpus_integrity/__init__.py` — package marker; no exports.
- Create `corpus_integrity/loader.py` — corpus iteration and frontmatter/body split, no DB.
- Create `corpus_integrity/protocol.py` — the `Check` protocol and `Violation` record.
- Create `corpus_integrity/waivers.py` — waiver loading and equality reconciliation.
- Create `corpus_integrity/checks/` — one module per defect class (Part III supplies each spec).
- Create `corpus_integrity/__main__.py` — CLI, exit codes, `--enumerate`, `--json`.
- Create `docs/data/waivers.yaml` — the enumerated, owner-signed exception sets.
- Modify `.github/workflows/ci.yml` — add the corpus-integrity job.

### Task 1: Loader and check protocol

**Files:**
- Create: `corpus_integrity/__init__.py`, `corpus_integrity/protocol.py`, `corpus_integrity/loader.py`
- Test: `tests/corpus_integrity/test_loader.py`

**Interfaces:**
- Produces: `Act(slug: str, path: Path, category: str, frontmatter: dict, body: str)`;
  `iter_acts(root: Path) -> Iterator[Act]`; `Violation(check: str, slug: str, detail: str,
  locator: str)`; `Check` protocol with `name: str` and
  `run(acts: Iterable[Act]) -> list[Violation]`.
- Consumed by: every check module and the CLI.

- [ ] **Step 1: Write the failing test**

```python
# tests/corpus_integrity/test_loader.py
from pathlib import Path
from corpus_integrity.loader import iter_acts

def test_iter_acts_reads_frontmatter_and_body(tmp_path: Path):
    d = tmp_path / "laws"
    d.mkdir()
    (d / "test-act.md").write_text(
        "---\ntitulo: ТЕСТОВ ЗАКОН\nidentificador: 12345\n---\n\n**Чл. 1.** Текст.\n",
        encoding="utf-8",
    )
    acts = list(iter_acts(tmp_path))
    assert len(acts) == 1
    assert acts[0].slug == "test-act"
    assert acts[0].category == "laws"
    assert acts[0].frontmatter["identificador"] == 12345
    assert acts[0].body.strip() == "**Чл. 1.** Текст."

def test_iter_acts_is_deterministically_ordered(tmp_path: Path):
    d = tmp_path / "laws"
    d.mkdir()
    for name in ("b-act", "a-act", "c-act"):
        (d / f"{name}.md").write_text("---\ntitulo: X\n---\nтекст\n", encoding="utf-8")
    assert [a.slug for a in iter_acts(tmp_path)] == ["a-act", "b-act", "c-act"]
```

- [ ] **Step 2: Run it and confirm it fails**

Run: `.venv/bin/python -m pytest tests/corpus_integrity/test_loader.py -v`
Expected: FAIL, `ModuleNotFoundError: No module named 'corpus_integrity'`

- [ ] **Step 3: Implement the loader and protocol**

```python
# corpus_integrity/protocol.py
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Protocol

@dataclass(frozen=True)
class Act:
    slug: str
    path: Path
    category: str
    frontmatter: dict
    body: str

@dataclass(frozen=True)
class Violation:
    check: str
    slug: str
    detail: str
    locator: str  # line number, article key, or byte offset — never empty

class Check(Protocol):
    name: str
    def run(self, acts: Iterable[Act]) -> list[Violation]: ...
```

```python
# corpus_integrity/loader.py
from pathlib import Path
from typing import Iterator
import yaml
from corpus_integrity.protocol import Act

CATEGORY_DIRS = ("laws", "codes", "ordinances", "regulations", "implementing")

def iter_acts(root: Path) -> Iterator[Act]:
    for category in CATEGORY_DIRS:
        d = root / category
        if not d.is_dir():
            continue
        for path in sorted(d.glob("*.md")):
            raw = path.read_text(encoding="utf-8")
            if not raw.startswith("---\n"):
                raise ValueError(f"{path}: missing YAML frontmatter")
            _, fm_text, body = raw.split("---\n", 2)
            yield Act(
                slug=path.stem,
                path=path,
                category=category,
                frontmatter=yaml.safe_load(fm_text) or {},
                body=body,
            )
```

- [ ] **Step 4: Run the tests and confirm they pass**

Run: `.venv/bin/python -m pytest tests/corpus_integrity/test_loader.py -v`
Expected: 2 passed

- [ ] **Step 5: Commit**

```bash
git add corpus_integrity/__init__.py corpus_integrity/protocol.py \
        corpus_integrity/loader.py tests/corpus_integrity/test_loader.py
git commit -m "feat(corpus-integrity): act loader and check protocol"
```

### Task 2: Waiver reconciliation

**Files:**
- Create: `corpus_integrity/waivers.py`, `docs/data/waivers.yaml`
- Test: `tests/corpus_integrity/test_waivers.py`

**Interfaces:**
- Consumes: `Violation` from Task 1.
- Produces: `reconcile(check: str, violations: list[Violation], waived: set[str]) ->
  tuple[list[Violation], list[str]]` returning unwaived violations and **stale** waivers
  (waived slugs that no longer violate).

- [ ] **Step 1: Write the failing test**

```python
# tests/corpus_integrity/test_waivers.py
from corpus_integrity.protocol import Violation
from corpus_integrity.waivers import reconcile

def _v(slug): return Violation(check="c", slug=slug, detail="d", locator="1")

def test_waived_act_is_not_reported():
    unwaived, stale = reconcile("c", [_v("a"), _v("b")], {"a"})
    assert [v.slug for v in unwaived] == ["b"]
    assert stale == []

def test_stale_waiver_is_reported():
    # 'z' is waived but no longer violates: the waiver has rotted and must fail the run
    unwaived, stale = reconcile("c", [_v("a")], {"a", "z"})
    assert unwaived == []
    assert stale == ["z"]
```

- [ ] **Step 2: Run it and confirm it fails**

Run: `.venv/bin/python -m pytest tests/corpus_integrity/test_waivers.py -v`
Expected: FAIL, `ModuleNotFoundError: No module named 'corpus_integrity.waivers'`

- [ ] **Step 3: Implement**

```python
# corpus_integrity/waivers.py
from pathlib import Path
from typing import Iterable
import yaml
from corpus_integrity.protocol import Violation

def load_waivers(path: Path) -> dict[str, set[str]]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return {check: set(entry["acts"]) for check, entry in data.items()}

def reconcile(
    check: str, violations: Iterable[Violation], waived: set[str]
) -> tuple[list[Violation], list[str]]:
    violations = list(violations)
    violating = {v.slug for v in violations}
    unwaived = sorted((v for v in violations if v.slug not in waived),
                      key=lambda v: (v.slug, v.locator))
    stale = sorted(waived - violating)
    return unwaived, stale
```

- [ ] **Step 4: Run the tests and confirm they pass**

Run: `.venv/bin/python -m pytest tests/corpus_integrity/test_waivers.py -v`
Expected: 2 passed

- [ ] **Step 5: Seed `docs/data/waivers.yaml` with the adjudicated sets**

The four sets already adjudicated in the record. Each entry carries the ruling that created it.
Act lists are produced by running the detectors and pasting their enumeration, never hand-typed.

```yaml
# docs/data/waivers.yaml
# Enumerated exceptions to the correctness floor. Equality is enforced:
# an act that stops violating must be removed here, or the run fails.
frontmatter_dates:
  ruling: "FR-011 triage — faithful to lex.bg, which carries no date signal for these acts"
  owner_signed: 2026-08-11
  acts: []  # fill from: python -m corpus_integrity --check frontmatter_dates --enumerate
empty_body:
  ruling: "lex.bg content-less stub pages; surfaced to callers as <doc_id=N>"
  owner_signed: 2026-08-11
  acts: []
no_article_anchor:
  ruling: "single-§ instruments (денонсиране, оттегляне на резерва, опрощаване) and ethics codes"
  owner_signed: 2026-08-11
  acts: []
```

- [ ] **Step 6: Commit**

```bash
git add corpus_integrity/waivers.py tests/corpus_integrity/test_waivers.py docs/data/waivers.yaml
git commit -m "feat(corpus-integrity): waiver reconciliation with stale-waiver detection"
```

### Task 3: First two detectors — tag remnants and chrome

These two are chosen first because their rules are unambiguous, their counts are already known
exactly, and they therefore validate the harness end to end without needing an adjudication round.
Expected counts at HEAD, which the tests pin: `/span>` 577 occurrences over 47 acts, `SUP>` 190
over 36, `/STRONG>` 1 act, chrome marker `Посети форума` 1 act, `© Lex.bg` 0.

**Files:**
- Create: `corpus_integrity/checks/__init__.py`, `corpus_integrity/checks/remnants.py`,
  `corpus_integrity/checks/chrome.py`
- Test: `tests/corpus_integrity/test_remnants.py`, `tests/corpus_integrity/test_chrome.py`

**Interfaces:**
- Consumes: `Act`, `Violation`, `Check` from Task 1.
- Produces: `RemnantCheck` (name `"tag_remnants"`), `ChromeCheck` (name `"chrome"`), both
  satisfying `Check`.

- [ ] **Step 1: Write the failing tests**

```python
# tests/corpus_integrity/test_remnants.py
from pathlib import Path
from corpus_integrity.checks.remnants import RemnantCheck
from corpus_integrity.loader import iter_acts

def _corpus(tmp_path: Path, body: str) -> Path:
    d = tmp_path / "laws"; d.mkdir(exist_ok=True)
    (d / "act.md").write_text(f"---\ntitulo: X\n---\n{body}\n", encoding="utf-8")
    return tmp_path

def test_flags_bare_span_remnant(tmp_path):
    root = _corpus(tmp_path, "**Чл. 3.**/span>. Участващите в производството.")
    v = RemnantCheck().run(iter_acts(root))
    assert len(v) == 1 and "/span>" in v[0].detail

def test_flags_sup_remnant(tmp_path):
    root = _corpus(tmp_path, "**Чл. 14н.**SUP>1. Нова разпоредба.")
    v = RemnantCheck().run(iter_acts(root))
    assert len(v) == 1 and "SUP>" in v[0].detail

def test_clean_act_passes(tmp_path):
    root = _corpus(tmp_path, "**Чл. 1.** Този закон урежда.")
    assert RemnantCheck().run(iter_acts(root)) == []
```

```python
# tests/corpus_integrity/test_chrome.py
from pathlib import Path
from corpus_integrity.checks.chrome import ChromeCheck
from corpus_integrity.loader import iter_acts

def test_flags_forum_sidebar(tmp_path):
    d = tmp_path / "ordinances"; d.mkdir()
    (d / "n.md").write_text(
        "---\ntitulo: X\n---\n**Чл. 1.** Текст.\n\nПосети форума\n", encoding="utf-8")
    v = ChromeCheck().run(iter_acts(tmp_path))
    assert len(v) == 1 and "Посети форума" in v[0].detail
```

- [ ] **Step 2: Run them and confirm they fail**

Run: `.venv/bin/python -m pytest tests/corpus_integrity/test_remnants.py tests/corpus_integrity/test_chrome.py -v`
Expected: FAIL, `ModuleNotFoundError: No module named 'corpus_integrity.checks'`

- [ ] **Step 3: Implement both checks**

```python
# corpus_integrity/checks/remnants.py
import re
from typing import Iterable
from corpus_integrity.protocol import Act, Violation

# Bare closing-tag text nodes that lex.bg emits without an opening '<'.
# These are reproduced verbatim by the converter and collide article keys.
REMNANTS = ("/span>", "SUP>", "/STRONG>", "/sup>", "/B>")

class RemnantCheck:
    name = "tag_remnants"

    def run(self, acts: Iterable[Act]) -> list[Violation]:
        out: list[Violation] = []
        for act in acts:
            for lineno, line in enumerate(act.body.splitlines(), start=1):
                for marker in REMNANTS:
                    if marker in line:
                        out.append(Violation(
                            check=self.name, slug=act.slug,
                            detail=f"markup remnant {marker!r}", locator=f"line {lineno}"))
        return out
```

```python
# corpus_integrity/checks/chrome.py
from typing import Iterable
from corpus_integrity.protocol import Act, Violation

# Site furniture that must never enter the content region. Sidebar headlines
# containing "Чл. N" manufacture phantom articles and churn every refresh.
CHROME_MARKERS = ("Посети форума", "© Lex.bg", "Новини", "Форум за")

class ChromeCheck:
    name = "chrome"

    def run(self, acts: Iterable[Act]) -> list[Violation]:
        out: list[Violation] = []
        for act in acts:
            for lineno, line in enumerate(act.body.splitlines(), start=1):
                for marker in CHROME_MARKERS:
                    if marker in line:
                        out.append(Violation(
                            check=self.name, slug=act.slug,
                            detail=f"site chrome {marker!r}", locator=f"line {lineno}"))
        return out
```

- [ ] **Step 4: Run the tests and confirm they pass**

Run: `.venv/bin/python -m pytest tests/corpus_integrity/ -v`
Expected: all passed

- [ ] **Step 5: Run against the real corpus and record the floor**

Run: `.venv/bin/python -m corpus_integrity --check tag_remnants --enumerate > /tmp/remnants.txt`
Expected: 47 acts for `/span>`, 36 for `SUP>`, 1 for `/STRONG>`. If the counts differ from these,
**stop and report** — the corpus moved and the census must be re-verified before proceeding.

- [ ] **Step 6: Commit**

```bash
git add corpus_integrity/checks/ tests/corpus_integrity/test_remnants.py \
        tests/corpus_integrity/test_chrome.py
git commit -m "feat(corpus-integrity): tag-remnant and chrome detectors"
```

### Task 4: CLI and aggregate runner

**Files:**
- Create: `corpus_integrity/__main__.py`
- Test: `tests/corpus_integrity/test_cli.py`

**Interfaces:**
- Consumes: every registered `Check`, `reconcile`, `load_waivers`.
- Produces: exit code 0 when clean, 1 on any unwaived violation or any stale waiver;
  `--enumerate` prints one line per violation as `check<TAB>slug<TAB>locator<TAB>detail`;
  `--json` prints a machine-readable summary with per-check counts.

- [ ] **Step 1: Write the failing test**

```python
# tests/corpus_integrity/test_cli.py
import subprocess, sys
from pathlib import Path

def test_exit_code_1_on_violation(tmp_path: Path):
    d = tmp_path / "laws"; d.mkdir()
    (d / "bad.md").write_text("---\ntitulo: X\n---\n**Чл. 1.**/span>.\n", encoding="utf-8")
    (tmp_path / "waivers.yaml").write_text("{}\n", encoding="utf-8")
    r = subprocess.run(
        [sys.executable, "-m", "corpus_integrity", "--root", str(tmp_path),
         "--waivers", str(tmp_path / "waivers.yaml")],
        capture_output=True, text=True)
    assert r.returncode == 1
    assert "tag_remnants" in r.stdout

def test_exit_code_0_when_clean(tmp_path: Path):
    d = tmp_path / "laws"; d.mkdir()
    (d / "ok.md").write_text("---\ntitulo: X\n---\n**Чл. 1.** Текст.\n", encoding="utf-8")
    (tmp_path / "waivers.yaml").write_text("{}\n", encoding="utf-8")
    r = subprocess.run(
        [sys.executable, "-m", "corpus_integrity", "--root", str(tmp_path),
         "--waivers", str(tmp_path / "waivers.yaml")],
        capture_output=True, text=True)
    assert r.returncode == 0
```

- [ ] **Step 2: Run it and confirm it fails**

Run: `.venv/bin/python -m pytest tests/corpus_integrity/test_cli.py -v`
Expected: FAIL, exit code 1 expected but module has no `__main__`

- [ ] **Step 3: Implement the CLI**

```python
# corpus_integrity/__main__.py
import argparse, json, sys
from pathlib import Path
from corpus_integrity.loader import iter_acts
from corpus_integrity.waivers import load_waivers, reconcile
from corpus_integrity.checks.remnants import RemnantCheck
from corpus_integrity.checks.chrome import ChromeCheck

CHECKS = [RemnantCheck(), ChromeCheck()]  # later classes append here

def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="corpus_integrity")
    p.add_argument("--root", default=".", type=Path)
    p.add_argument("--waivers", default=Path("docs/data/waivers.yaml"), type=Path)
    p.add_argument("--check", default="all")
    p.add_argument("--enumerate", action="store_true")
    p.add_argument("--json", action="store_true")
    args = p.parse_args(argv)

    waivers = load_waivers(args.waivers) if args.waivers.exists() else {}
    acts = list(iter_acts(args.root))
    failed, summary = False, {}

    for check in CHECKS:
        if args.check not in ("all", check.name):
            continue
        unwaived, stale = reconcile(check.name, check.run(acts), waivers.get(check.name, set()))
        summary[check.name] = {"violations": len(unwaived), "stale_waivers": len(stale)}
        if unwaived or stale:
            failed = True
        if args.enumerate:
            for v in unwaived:
                print(f"{v.check}\t{v.slug}\t{v.locator}\t{v.detail}")
        for slug in stale:
            print(f"{check.name}\tSTALE WAIVER\t{slug}\tno longer violates; remove from waivers")

    if args.json:
        print(json.dumps({"acts": len(acts), "checks": summary}, ensure_ascii=False, indent=2))
    else:
        for name, s in sorted(summary.items()):
            print(f"{name}: {s['violations']} violations, {s['stale_waivers']} stale waivers")
    return 1 if failed else 0

if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run the tests and confirm they pass**

Run: `.venv/bin/python -m pytest tests/corpus_integrity/ -v`
Expected: all passed

- [ ] **Step 5: Commit**

```bash
git add corpus_integrity/__main__.py tests/corpus_integrity/test_cli.py
git commit -m "feat(corpus-integrity): CLI runner with hard-fail exit codes"
```

### Task 5: Wire into CI as a blocking job

**Files:**
- Modify: `.github/workflows/ci.yml`

- [ ] **Step 1: Add the job**

```yaml
  corpus-integrity:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        if: false  # python-only job; node not required
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - name: Install
        run: pip install pyyaml
      # Runs over the committed Markdown tree only: no catalog.db needed,
      # which is why this can gate every pull request.
      - name: Corpus integrity
        run: python -m corpus_integrity --root . --waivers docs/data/waivers.yaml
```

- [ ] **Step 2: Verify it fails on a seeded violation**

Create a scratch branch, append `/span>` to one act, push, confirm the job goes red, then delete
the branch. A gate that has never been seen to fail is not known to be a gate.

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/ci.yml
git commit -m "ci: corpus-integrity gate on every pull request"
```

### Task 6: The single corpus write gate

This is the deliverable that makes the guarantee of Part IV structural rather than procedural.
Today the anchor and coverage checks live in `fetcher/bg/coverage.py` and are wired into
`refresh.py` and `bootstrap.py` — that is, into the **lex.bg write path only**. A future ДВ patcher
writing corpus files would be a third writer, and nothing would force it through the gate. The
guarantee would lapse silently at exactly the moment the source changed. Build the gate as a
property of *writing a corpus file*, before any second writer exists.

**Files:**
- Create: `corpus_gate.py`, `tests/test_corpus_gate.py`
- Modify: `refresh.py`, `bootstrap.py` — route every corpus write through the gate

**Interfaces:**
- Consumes: `Act`, `Violation` from Task 1; the check registry from Task 4.
- Produces: `write_act(path, frontmatter, body, *, source) -> None`, raising
  `CorpusIntegrityError(path, violations)`; `SourceRef` describing the ingestion path
  (`lexbg`, `dv`, `manual`) for the commit trailer.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_corpus_gate.py
import pytest
from corpus_gate import write_act, CorpusIntegrityError, SourceRef

def test_gate_refuses_an_act_with_a_markup_remnant(tmp_path):
    with pytest.raises(CorpusIntegrityError) as exc:
        write_act(tmp_path / "laws" / "bad.md", {"titulo": "X"},
                  "**Чл. 1.**/span>. Текст.", source=SourceRef("lexbg", "123"))
    assert "tag_remnants" in str(exc.value)
    assert not (tmp_path / "laws" / "bad.md").exists()  # nothing written

def test_gate_writes_a_clean_act(tmp_path):
    (tmp_path / "laws").mkdir(parents=True)
    write_act(tmp_path / "laws" / "ok.md", {"titulo": "X"},
              "**Чл. 1.** Текст.", source=SourceRef("lexbg", "123"))
    assert (tmp_path / "laws" / "ok.md").exists()

def test_only_the_gate_writes_corpus_files():
    """Structural guarantee: no second writer may exist, now or later."""
    from corpus_gate import find_corpus_writers
    offenders = find_corpus_writers(exclude={"corpus_gate.py"})
    assert offenders == [], f"corpus write outside the gate: {offenders}"
```

- [ ] **Step 2: Run them and confirm they fail**

Run: `.venv/bin/python -m pytest tests/test_corpus_gate.py -v`
Expected: FAIL, `ModuleNotFoundError: No module named 'corpus_gate'`

- [ ] **Step 3: Implement the gate**

```python
# corpus_gate.py
import ast
from dataclasses import dataclass
from pathlib import Path
from corpus_integrity.loader import CATEGORY_DIRS
from corpus_integrity.protocol import Act, Violation
from corpus_integrity.__main__ import CHECKS

@dataclass(frozen=True)
class SourceRef:
    kind: str   # "lexbg" | "dv" | "manual"
    ident: str

class CorpusIntegrityError(Exception):
    def __init__(self, path: Path, violations: list[Violation]):
        self.path, self.violations = path, violations
        detail = "; ".join(f"{v.check}@{v.locator}: {v.detail}" for v in violations)
        super().__init__(f"{path}: {detail}")

def write_act(path: Path, frontmatter: dict, body: str, *, source: SourceRef) -> None:
    """The ONLY sanctioned writer of a corpus .md file.

    Every ingestion adapter calls this: lex.bg refresh, DV consolidation,
    manual gap-fill, municipal. There is deliberately no force flag — a
    bypass would make the guarantee advisory rather than structural.
    """
    act = Act(slug=path.stem, path=path, category=path.parent.name,
              frontmatter=frontmatter, body=body)
    violations = [v for check in CHECKS for v in check.run([act])]
    if violations:
        raise CorpusIntegrityError(path, violations)
    _atomic_write(path, frontmatter, body)

def find_corpus_writers(exclude: set[str]) -> list[str]:
    """Static scan: any module writing to a corpus category dir outside the gate."""
    offenders = []
    for py in Path(".").rglob("*.py"):
        if py.name in exclude or ".venv" in py.parts or "worktrees" in py.parts:
            continue
        src = py.read_text(encoding="utf-8")
        if "write_text" not in src and "open(" not in src:
            continue
        if any(f'"{d}' in src or f"'{d}" in src for d in CATEGORY_DIRS):
            offenders.append(str(py))
    return sorted(offenders)
```

- [ ] **Step 4: Run the tests and confirm they pass**

Run: `.venv/bin/python -m pytest tests/test_corpus_gate.py -v`
Expected: 3 passed. If `test_only_the_gate_writes_corpus_files` fails, that is the point of the
task — route the offending writer through the gate rather than adding it to the exclusion set.

- [ ] **Step 5: Route the existing writers**

`refresh.py` and `bootstrap.py` currently write corpus files directly. Replace those writes with
`write_act`, keeping their existing gate calls in place; the gate becomes the single choke point
and the older checks become redundant only once they are proved equivalent.

- [ ] **Step 6: Commit**

```bash
git add corpus_gate.py tests/test_corpus_gate.py refresh.py bootstrap.py
git commit -m "feat(corpus-gate): single sanctioned writer for corpus files"
```

## Part III — Per-class ladders

Every class runs Plan, Research, Solve, Apply, Guarantee. Each class becomes its own
implementation plan, authored from its ladder below at the moment its turn comes, so that the
adjudication of the preceding class is in hand before the next is specified. The ladders are the
binding specification; the per-class plans may add detail but may not weaken a boundary.

**C0 is the reference closure.** Flattened unnumbered алинеи (pre-Указ-883 acts) is the one class
already carried to Apply: parser fixed, corpus swept in 2,923 commits, implicit алинеи addressable
and flagged. It supplies the regression invariant every later class is checked against, and it is
also the cautionary case, because its fix amplified C1 by emitting implicit алинеи onto a
fabricated article.

---

### C1 — Fabricated article anchors from quoted text

**Reference defect:** ЗЗД чл. 1001а, 1001б, 1001г, which are Закон за гражданското
съдопроизводство articles reproduced inside ЗЗД's ПЗР and adopted as ЗЗД's own; plus duplicate
keys 5, 10 and 81, where the second row is a repeal-list citation to another act.
**Registered as:** **FR-037** (2026-09-05, PR #25; re-homed from the FR-030 addendum). The working
branch `fix/fr037-p0-detect` is pushed as PR #26.

**Plan.** Adjudicate the decision procedure separating a structural anchor of *this* act from an
article number inside reproduced text. Four candidate signals, to be ruled on explicitly:
monotonic numbering as an arithmetic backstop; **bold versus unbolded emission**, since the parser
bolds only anchors whose source element begins with „Чл.“ and the ЗЗД phantoms are unbolded, so a
discriminator already exists in the file and is currently discarded; enclosing amendment-section
context; enclosing quotation. The ruling states which signals are load-bearing and which are
corroborating, and defines the **excluded boundary**: this procedure does not decide alinea-level
markers (C2) and does not decide annex or table content (C7).

**Research.** The paper attack must break these before code: `_AMENDMENT_SECTION_RE` as drafted in
the anchor plan matches „ДОПЪЛНИТЕЛНИ“ inside 123 ordinary headings across 81 acts, so
section-context alone is damaged; `_MAX_FORWARD_GAP` is near-inert because 93,8 % of sequence
breaks are backward and a thousandfold parameter sweep moves the count by 8,4 %. Attackers supply
counter-examples from mid-century acts whose bodies are amendment programmes (ЗОРВКС, ЗЛС carry 66
of the 90 known artifacts).

**Solve.** Detector `checks/anchors.py`, emitting one violation per suspected fabricated anchor
with its enclosing-section locator. Fix at `fetcher/bg/text_parser.py`: quoted text is blockquoted
and never promoted to `**Чл. N.**`. Every character survives; only anchor status changes.
Protected surface, so an IMPLEMENTATION-PREFLIGHT precedes the edit.

**Apply.** Land the parser change; re-run the detector; record the residual as C1's pre-sweep
floor. Corpus repair happens only in the Part V sweep.

**Guarantee.** INV: *no anchor is emitted for an article number occurring inside reproduced or
quoted text.* Boundary: does not cover quoted text that reproduces an article of the **same** act,
nor § markers. Bound at the write gate and in CI. Crossed with C6 (heading state) and C5 (key
uniqueness).

---

### C2 — Citation read as an alinea marker, with live text truncation

**Reference defect:** наредба 3/2004 чл. 1599, where „500(660) V“ made `(660)` an alinea marker,
**truncating the real ал. 2 mid-sentence** at „Използването на напрежение 500“ and emitting two
junk rows. Sibling voltage and code cases in наредба РД-02-20-1 чл. 62, РД-02-20-2 чл. 486,
наредба 6/2013 чл. 10 and 11.
**Registered as:** FR-030, redirected by D-055.

**Plan.** D-055 already settled the shape and it must not be re-litigated: a regex cannot do this,
proven by execution, because „информацията по чл. 8 (3)“ and „наредбата по ал. 4 (6)“ are
byte-identical in form. The adjudication is therefore of the **three-stage pipeline**: a
deterministic high-recall flagger, an agentic reasoner, a deterministic applier. The ruling fixes
what the flagger must catch (out-of-sequence markers, markers in citation context, markers whose
value is implausible as an alinea number such as 660 or 2003), what the reasoner receives, and what
the applier is permitted to do. The applier must both drop confirmed citations **and re-span the
truncated text**, because the truncation, not the junk row, is the real harm.

**Research.** Attack the flagger's recall on the corpus: any real alinea it fails to flag is an
error the reasoner never sees. Attack the applier's re-spanning on articles where two markers were
matched inside one sentence. Attack the reasoner's determinism requirement: identical input must
yield identical verdicts, so verdicts are cached per marker with their reason.

**Solve.** Detector `checks/alineas.py` implements the flagger and reports counts only. The
reasoner is an orchestrated agentic pass emitting `{marker, verdict, reason}` per flagged instance,
committed as data so it is auditable and re-runnable. The applier is deterministic.

**Apply.** Land flagger and applier; run the reasoner over the flagged set; commit verdicts;
re-run the detector. Anything the reasoner cannot decide is emitted with the uncertainty flag
required by correctness property 5, never silently kept or dropped.

**Guarantee.** INV: *every emitted alinea marker is either verified as a real marker, or carries a
recorded uncertainty flag.* Boundary: does not cover markers inside annex or table cells (C7), and
does not claim the reasoner is infallible — it claims no unlabelled verdict. Crossed with C7.

---

### C3 — lex.bg site chrome inside an act body

**Reference defect:** `ordinances/naredba-5-ot-10-may-1999-…kadastralni` carries the „Новини“ and
„Форум“ sidebar inside the act body, which manufactured a phantom whole article чл. 42 out of a
forum thread title and churns a `[popravka]` commit on every refresh because headlines change daily.
**Registered as:** FR-036, open. Blast radius one act today; the class is „site chrome reaches the
content walker“.

**Plan.** Rule on content-region selection rather than marker blacklisting, since blacklisting
chases headlines. The ruling names the container selectors that define the act body and states the
boundary: chrome that lex.bg renders *inside* the content container is out of scope for this class.

**Research.** Attack by finding acts whose legitimate text contains the marker words. Attack the
denylist seam documented in `fetcher/bg/coverage.py`: text under a denylisted ancestor is skipped by
both parser and coverage gate, so a chrome class applied to a spine element is invisible to both.

**Solve.** Detector already written in Part II Task 3 (`checks/chrome.py`). Fix in
`fetcher/bg/text_parser.py` content-region selection. Protected surface, preflight required.

**Apply.** Land; re-fetch the affected act; confirm the detector reports zero and the churn stops.

**Guarantee.** INV: *no corpus file contains a site-chrome marker.* Boundary: enumerated marker
set; a new sidebar class is a new instance, which is why the seam test from C1's crossing matters.
Bound in CI from Part II onwards, i.e. this class is guarded before it is fixed.

---

### C4 — Markup remnants collapsing distinct articles

**Reference defects:** ТЗ чл. 260и and чл. 260и¹ collapse to one key with 17 rows; ЗКПО's
Pillar-Two articles `чл. 260я¹` onward collapse 36 rows onto `260я`, making in-force 2024 tax law
unaddressable. Root cause established: lex.bg emits a bare `/span>` **text node with no opening
bracket**, and the converter reproduces it verbatim — proven by an exact 20-to-20 match between the
ГПК source fixture and the committed Markdown. **This is faithful reproduction of malformed source,
not a converter bug**, which is why the coverage gate cannot see it: the junk is in the source.
**Registered as:** FR-035, open. Two sub-classes: `SUP>` superscript indices and `/span>` stray
nodes, the latter with no superscript involved.

**Plan.** One decision the owner must make because it changes the public address space: **the
canonical form of a superscript article index** — `260и1`, the Unicode superscript `260и¹`, or a
suffix convention. Every consumer, every stored provision key and every citation the corpus has
ever answered depends on this. The ruling also fixes whether the change is a migration with an
alias table for the old collapsed key.

**Research.** Attack the canonical form against real citation practice: how do ВКС and ДВ write
these indices, and does the chosen form round-trip through search normalisation. Attack the
migration for consumers holding old keys.

**Solve.** Detector from Part II Task 3. Fix strips remnants at conversion in
`fetcher/bg/text_parser.py` and teaches both article regexes the canonical form —
`index/provisions.py:_ARTICLE_RE` and `fetcher/bg/coverage.py:_STRUCT_ARTICLE_RE`. Two protected
surfaces, preflight required.

**Apply.** Land; re-sweep the 47 plus 36 affected acts within the Part V sweep; **re-run C5's
detector immediately**, because splitting keys changes the collision census and the count must fall.

**Guarantee.** INV-007 as drafted in I.3. Boundary: § superscripts and annex-cell superscripts
excluded. Crossed with C5 mandatorily.

---

### C5 — Ambiguous addresses: one address, more than one answer

**Reference defect:** `get_article("ЗМДТ", "чл. 15")` returns two rows, and both the MCP and REST
surfaces take `rows[0]`, so which article a caller receives is decided by file order. A
three-article range returns six entries. Measured 698 colliding article keys across 144 acts;
a transcript-only count reports 2,290 ambiguous addresses across 232 acts with 4,382 shadowed rows.
**Registered as:** **FR-038** (2026-09-05, PR #25).

**Plan.** This class is partly *derived*: C1 and C4 each remove collisions. The adjudication must
therefore define the class as the **residual** after those land, and rule on what a legitimate
duplicate key would even be, enumerating any such case rather than assuming none. It must also rule
that `rows[0]` is never an acceptable resolution — the surface either returns a single row or
raises the existing `AMBIGUOUS_NAME`-style error with both candidates.

**Research.** Attack the assumption that all collisions are defects. Attack the ordering
dependence: the export already had to dump `ORDER BY rowid` for candidate order to be stable, which
means answer identity currently depends on dump order — an attacker should demonstrate that a
re-import can silently change which article a citation resolves to.

**Solve.** Detector `checks/addresses.py` over the Markdown tree, so it needs no database. Fix is
twofold: parser-side, whatever C1 and C4 leave behind; surface-side, replace first-row selection
with an explicit error carrying both candidates.

**Apply.** Land after C1 and C4; the residual is the true class size and is recorded as such.

**Guarantee.** INV: *every article address in the corpus resolves to exactly one provision, and no
surface resolves ambiguity by ordering.* Boundary: enumerated legitimate duplicates, if the
adjudication finds any. Bound at the write gate, in CI, and additionally as a serve-time contract
test on MCP and REST.

---

### C6 — Un-hashed structural headings

**Reported:** 12 751 headings across 408 acts where `ГЛАВА`, `Раздел`, `Част` and `Дял` are emitted
without a Markdown `#`, so every heading-resetting state machine leaks to end of file.
**Status:** transcript-only and **unverified**; registered as **FR-039** (2026-09-05, PR #25) with the
count marked unverified.

**Plan.** The first action is verification, not fixing: reproduce the count independently and
publish it. Only then adjudicate. This class is **upstream of C1**, because any anchor rule keyed
on heading state is unreliable while heading state leaks, which is why the anchor work stalled.
Sequencing follows from that, not from severity.

**Research.** Attack the claim itself: are these headings, or are they body text that merely begins
with a structural word. Attack the fix's blast radius, since emitting `#` changes every downstream
consumer of document structure, including the reader's table of contents.

**Solve.** Detector `checks/headings.py`. Fix in `fetcher/bg/text_parser.py` heading emission.

**Apply.** Land before C1's fix, so C1 is adjudicated against correct heading state.

**Guarantee.** INV: *every structural heading is emitted as a Markdown heading.* Boundary: excludes
headings inside annexes and quoted acts. Crossed with C1.

---

### C7 — Annex and table material emitted as provisions

**Measured:** 20 282 implicit rows across 205 acts at a 95 % artifact rate, being 96,4 % of the
implicit-row frame; the two state-budget acts alone contribute 9 266 rows.
**Registered as:** FR-026.

**Plan.** The instrument is already ruled: a `kind` or `is_annex` classification column on
`provisions`, **not deletion**. A delete-based guard was measured during FR-034 and declined — its
signals select 70,7 % of the frame with only two doctrinal hits, the same failure shape as D-055.
The open adjudication is the **eligibility gate**: whether position-derived алинеи are emitted only
for acts promulgated before Указ 883/1974, whose citation practice justifies them. This is owner
decision D-2 in the anchor-integrity plan and it is still open.

**Research.** Attack the era cutoff with acts either side of 1974. Attack the classification
signals against table-heavy modern наредби.

**Solve.** Detector counts implicit rows by stratum. Fix is a schema migration plus classification
at index time. SQLite schema is a protected surface; preflight required.

**Apply.** Land the column and the classifier; the wire behaviour follows the cf-plane decision in
Part VI.

**Guarantee.** INV: *no annex or table cell is addressable as a provision.* Boundary: the classifier
is heuristic, so every classified row carries its basis, and unclassifiable rows are flagged, not
guessed. Crossed with C2.

---

### C8 — Record-layer truthfulness

**Measured:** `docs/sync/CORPUS-STATUS.json` asserts `corpus_trustworthy: true` and reports 3 600
acts; `.ahelia/constraint-profile.yaml` and `.ahelia/protected-surfaces.yaml` say 3 574;
`.claude/CLAUDE.md` says about 3 574; the corpus holds **3 624**. The frontmatter schema gate that
`.claude/CLAUDE.md` declares **does not exist**. `gate-report.json` is gitignored, has no history
and is overwritten on every run, so a fall in gate-pass rate between runs is undetectable by
construction.
**Registered as:** **FR-040** (2026-09-05, PR #25). The counts were refreshed to 3,624 and the
declared-but-unbuilt gates struck in the same PR; the durable check remains to be built.

**Plan.** Treat documents of record as a surface with its own lens. Rule that every corpus-state
claim is machine-checkable or removed, and that the declared gates in `.claude/CLAUDE.md` are either
built or struck.

**Research.** Sweep every file asserting a corpus fact and list them; the four above are the known
set and the sweep must prove it complete.

**Solve.** A `checks/records.py` consistency check asserting the act count agrees across all
declaring files and the on-disk tree. Build the frontmatter validator that `.claude/CLAUDE.md`
already promises. Commit `gate-report.json` so it has history.

**Apply.** Land with Part II, since it needs no adjudication.

**Guarantee.** INV: *no file asserts a corpus fact that the corpus contradicts.* Boundary: covers
declared counts and gate status, not prose descriptions. Re-swept whenever any act count moves.

---

### C9 — Cross-references are not modelled at all

**Status:** registered as **FR-041** (2026-09-05, PR #25); **the invariant that would detect it
cannot be written today.** Surfaced by the ДВ path research, 2026-08-11. Under the graded source
model the capture-now decision applies to every act that keeps a lex.bg base (grades B and C);
grade A acts have their references reconstructed from Gazette text by the resolver.

**The finding.** The corpus has no reference model: `index/catalog.py` defines four tables and none
of them holds an edge. Worse, lex.bg **marks these references up** — `SameDocReference` carries
inline cross-references in 1 662 of 1 662 occurrences („чл. 5, ал. 1“) — and the converter unwraps
the spans to plain text, discarding the linkage. The edges were in hand and were thrown away.

**Why it becomes urgent under ДВ.** A renumbering cascade („досегашните чл. 15-20 стават
чл. 16-21“) relabels six nodes. Every „по чл. 17, ал. 2“ inside the act, and every „по чл. 17 от
Закона за X“ in the roughly 3 600 other acts, now denotes different content. Because references
are plain text, **nothing changes in them, and nothing detects it**: the text still parses, anchors
stay monotonic, the coverage gate passes, row counts are unchanged. The result is the exact failure
this project exists to prevent — an address that resolves to exactly one text, and the wrong one —
while violating no currently specifiable check.

Two mitigations and one aggravation, specific to Bulgarian drafting: Указ 883 practice prefers
suffix insertion (нов чл. 5а) over renumbering, which is why renumbering is only about 8 % of
operations; ЗИД ПЗР routinely carry explicit reference-repair instructions, so the drafter does
part of the work **if every operation is applied**; but the drafter repairs references *within* the
amended act only, and nobody repairs the citing acts.

**A second dependency dies with the source.** `amendment_history` is scraped from lex.bg's
`.HistoryOfDocument`, which is an APIS construct that **ДВ does not have** — ДВ carries no
amendment graph, no hyperlinks, no history section, only genitive title prose and an inline
„(ДВ, бр. N от YYYY г.)“ citation. That table feeds `history()`, `diff()` and
`amendments_in_period()`. Retiring lex.bg therefore retires the only structured act-to-act linkage
the corpus has, and it must be **reconstructed** by a title resolver rather than fetched.

**Plan.** Register the class first (Directive 13). Adjudicate whether to capture reference spans at
conversion time now, while lex.bg still marks them up and while re-photographing is still cheap.
This is a *capture-now-or-lose-it* decision, not a build-the-graph decision.

**Research.** Attack the resolver against declined genitive title prose, which the ДВ recon calls
the highest-effort risk of that phase. Attack reference capture against the denylist seam: the
`SameDocReference` class sits in `CHROME_DENYLIST` and must not be skipped inside articles, since
doing so once deleted 485 of ГПК's 745 articles.

**Solve.** Capture spans into a reference table at index time; no consumer change required yet.

**Apply.** Land before the sweep, so the sweep captures references corpus-wide in the same pass.

**Guarantee.** INV: *every intra-act reference resolves to a live address, and no relabelling
leaves a dangling or silently redirected reference.* Boundary: inter-act references are captured
but not resolved until the resolver exists. **This is the one invariant in the catalogue that is
declared and not yet implementable, and it is recorded as such rather than omitted.**

---

### C10 — Provenance integrity (added 2026-09-05, D-059)

**The class.** Under the graded source model every act carries a provenance grade (A ДВ-complete,
B ДВ-audited snapshot, C pre-1989 base) derived from the source class and application state of its
base and of every amendment event. A grade that is not derivable from the recorded events, a grade
that rose without the sourcing its definition requires, or a consumer surface (index, MCP, REST,
cf-plane) that disagrees with the frontmatter derivation is a defect of this class. So is any
grade B or C text served without its grade.
**Registered as:** the provenance floor in `docs/process/COVERAGE-FLOOR.md` (PR #25) and FR-024 as
redirected; the design is `docs/plans/2026-09-05-dv-graded-source-design.md` section 4.

**Plan.** The derivation table in the design (section 4.2) is the decision procedure; the excluded
boundary is the correctness of the text itself, which classes C1 to C7 own.

**Research.** Attack the derivation with mixed-era acts (a 1950 base with post-2005 events, a 2003
base with PDF-era events), with an act whose chain the coverage map extends beyond lex.bg's, and
with a consumer that caches payloads across a grade change.

**Solve.** Detector `checks/provenance.py` over the Markdown tree: parse the block, re-derive the
grade from the events, compare; a serve-time contract test on MCP and REST compares the wire field
to the frontmatter.

**Apply.** Lands with the provenance block (design phase P1), before the first grade A write.

**Guarantee.** INV-010: *every act's grade equals the derivation from its recorded events, and every
consumer surface reports that grade.* Boundary: does not cover the truth of the events themselves
(the coverage map and the witnesses do). Bound at the write gate and in CI.

## Part IV — The source-agnostic guarantee

### IV.1 Why today's gates cannot carry over

Every enforced gate in the pipeline today is a **fetch-time source-fidelity check**. The coverage
gate asks one question: is every Cyrillic text node of the lex.bg page present in our output? That
question is meaningful only while the source is a page that already contains the finished,
consolidated act. It is also one-directional, which is why it is blind to injected junk, to
structure-preserving loss, and to chrome, all three of which are live in the corpus now.

Under ДВ the question stops making sense. ДВ publishes **amendment acts**, not consolidated texts.
The consolidated act becomes something the pipeline **constructs** by applying operations to a base
version. There is no page to be faithful to. A fidelity gate therefore cannot be the guarantee, and
a pipeline that relies on one is a pipeline whose only real check disappears on the day the source
changes.

### IV.2 The guarantee is stated on the output, not on the source

The five correctness properties in `docs/process/COVERAGE-FLOOR.md` were deliberately written
without reference to a source. They constrain the corpus itself: no fabricated address, no lost
address, no ambiguous address, no contaminated or truncated text, no silent uncertainty. Those hold
identically whether the text was photographed from lex.bg, constructed from a ДВ amendment, filled
in by hand, or produced by a future municipal adapter.

That is the bridge, and it converts the guarantee from a promise about a scraper into an
architectural property of the corpus.

### IV.3 One write gate, many adapters

**No code path may write a corpus `.md` except through a single function that asserts the
invariants.** This is the mechanism that makes „every new scrape must implement the pipeline
properly“ true by construction instead of by discipline.

```python
# corpus_gate.py  (Phase 0 deliverable, Part V)
def write_act(path: Path, frontmatter: dict, body: str, *, source: SourceRef) -> None:
    """The only sanctioned writer of a corpus .md file.

    Every ingestion adapter — lex.bg refresh, DV consolidation, manual gap-fill,
    municipal — calls this. Violations raise; nothing is written. There is no
    force flag: a bypass would make the guarantee advisory.
    """
    act = Act.from_parts(path, frontmatter, body)
    violations = run_write_checks(act)      # the same checks CI runs corpus-wide
    if violations:
        raise CorpusIntegrityError(path, violations)
    _atomic_write(path, frontmatter, body, source)
```

Enforced mechanically, not by convention: a test walks the source tree and fails if any module
other than `corpus_gate` writes to a corpus path.

```python
def test_only_the_gate_writes_corpus_files():
    offenders = grep_for_corpus_writes(exclude={"corpus_gate.py"})
    assert offenders == [], f"corpus write outside the gate: {offenders}"
```

Defence in depth has three layers, and each catches what the one before it cannot: the **write
gate** refuses a bad act at ingestion; the **corpus-wide CI check** catches anything that reached
the tree by any other route, including a hand-edit; the **invariant catalogue** records what each
closure does and, crucially, does not cover.

### IV.4 What ДВ changes, property by property

| Property | Under lex.bg | Under ДВ | Instrument that must exist |
|---|---|---|---|
| No fabricated address | quoted text adopted as own articles | **much harder**, and needs a different instrument: an inserted чл. 5а is correct *because* no source prints it. Also, a ЗИД's body is quoted target-act text end to end, so what is a rare ПЗР edge case under lex.bg is **100 % of the input** under ДВ | licence test, not fidelity test: every anchor traces to promulgated text or to one resolved operation. **The monotonic backstop moves from input to output** — a ЗИД's quoted articles are deliberately sparse and non-monotonic, so on ЗИД input the invariant fires on every anchor and is useless; on the patched result it works unchanged |
| No lost address | flattening, collapsed superscripts | **new invisible mode**: a missed извънреден issue or a dropped operation leaves the corpus perfectly self-consistent and merely **stale**. No output-side check can see it | moves to the input side: every parsed operation consumed exactly once, and an issue cursor with no gaps in which every material is classified, never dropped |
| No ambiguous address | duplicate keys from parsing | easier to check, **harder to satisfy**: suffix-letter targets (чл. 5 versus чл. 5а), and two amendments in one issue touching one address | post-apply duplicate-sibling-label invariant needs no source; requires a real address type plus lineage, since `provisions` is keyed on the **label**, which a renumbering changes |
| No contaminated or truncated text | site chrome, markup remnants | contamination **easier** (ДВ serves plain official text); truncation **strictly harder**, with no oracle-free instrument today: „думите X се заменят с Y“ needs our stored base to contain X byte-exactly, and our base came through an HTML converter that normalises whitespace and quotes | occurrence-count precondition: X must occur exactly the declared number of times in the resolved target; 0 or unexpected N is a hard failure, never a best-effort apply |
| No silent uncertainty | one undecidable class (citation versus alinea) | **about five** classes: title-to-act resolution, operation targeting, in-force date, irregular drafting, annex applicability | transfers unchanged and becomes load-bearing; the plumbing already exists (`date_uncertain`, the `IMPLICIT_ALINEA` warning shipped through database, MCP and REST) |

**The single most dangerous operation** is the quantified one: „навсякъде в закона думите X се
заменят с Y“. It has an unbounded target set, so executed as a naive substitution over the file it
will also rewrite occurrences inside quoted text belonging to other acts, inside annexes and inside
citation strings — silently, **violating no address and passing every structural invariant**. Its
extension must be computed, enumerated and bounded before a single byte is written.

### IV.5 The dependency that makes this work foundational, not throwaway

A ДВ amendment is an instruction addressed to a location: *in чл. 5, ал. 2 the words X are replaced
by Y*. Applying it requires resolving чл. 5, ал. 2 **in our own corpus**. If the address space is
wrong — a phantom article, a collapsed superscript, two rows behind one key — the amendment is
applied to the wrong place, or to one of two candidates chosen by file order, and the error is then
baked into the consolidated text with no source page left to reveal it.

**Anchor integrity is therefore a precondition for ДВ consolidation, not a parallel concern.** The
work in Part III is not superseded when ДВ arrives; it is the foundation ДВ stands on. This also
answers the reverse question cheaply: the ДВ engine's own first integrity check is that every
operation resolves to exactly one existing address, which is properties 1 and 3 restated from the
other side.

### IV.6 Oracle honesty

Owner Directive 3 names lex.bg as the validation oracle for consolidation output. It is useful and
it is **not** the guarantee, on three independent grounds. It is Cloudflare-gated, and D-011 makes a
challenge a deliberate halt rather than a retry, so an oracle check cannot block a build — and
Directive 12 says a gate that does not block does not exist. It is legally the dependency that
FR-024 exists to retire, so wiring it into CI in perpetuity re-establishes the coupling the
re-source was chartered to remove. And it answers only „what does the page say today“, which is
nothing at all for historical replay.

There is also direct evidence that „the oracle disagrees, therefore we are wrong“ is false. In the
LawVM calibration against a frozen national oracle over 690 statutes, **22 cases were ones where
the official consolidation itself was wrong**. Divergence is therefore adjudicated, never resolved
by deference — and, under Directive 9, adjudication must end in a **count** of unresolved
divergences that is zero or fully waived, not in a residual rate.

The checks in IV.3 need no oracle at all. That is precisely why they, and not the oracle, are the
guarantee.

### IV.7 The cutover is a one-way door

Today a defect in the base text is cheap to repair: re-photograph the act. Two full corpus sweeps
have already been run on exactly that basis, the second producing 2 923 correction commits.

**The moment lex.bg is retired as a source, that repair mechanism disappears.** Forward replay
anchors on the corpus text as it stands at cutover. A phantom article, a flattened alinea or a
collapsed superscript baked into the base at that moment is baked into every subsequent version,
every diff and every historical reconstruction, and becomes repairable only by hand.

Two consequences follow, and they are the strongest argument in this plan:

1. The work in Part III is not merely *scheduled before* ДВ. It is the **last cheap opportunity**
   to fix the base at all.
2. The cutover needs an explicit **pre-cutover corpus-correctness gate**: no ingestion path may be
   switched to ДВ until every detector reports zero. Passing through that door with known defects
   converts a repairable problem into a permanent one.

*Amended 2026-09-05:* under the graded source model the door is passed **per act**, not once for the
corpus. An act moves to grade A only when the detectors report zero on it and its rebuild from the
Gazette passes the write gate; acts that keep a lex.bg base keep the re-photograph repair path and
remain subject to this gate until they move.

## Part V — Sequencing and the single sweep

Order is dictated by dependency, not by severity. Two classes are upstream of the rest, and putting
them second would mean adjudicating the anchor rules against a corrupt heading state — which is
precisely why the previous attempt stalled.

| Phase | Content | Gate to exit | Owner decision needed |
|---|---|---|---|
| **0** | Part II machine floor; C8 records; C3 chrome detector; the write gate of IV.3 | CI job green and demonstrated red on a seeded violation | none |
| **1** | C6 headings: verify the count, adjudicate, fix | detector zero; C1's acceptance test re-run | none |
| **2** | C4 remnants: canonical superscript form, strip at conversion | detector zero; C5 count falls | **canonical form** |
| **3** | C1 anchors: decision procedure, paper attack, parser fix | detector zero on the enumerated set | FR-037 registration |
| **4** | C5 addresses: residual after 1 to 3; surfaces stop resolving by order | detector zero; serve-time contract test green | none |
| **5** | C2 citation-as-alinea: flagger, reasoner, applier | every flagged marker carries a verdict or a flag | none |
| **6** | C7 annex classification; eligibility gate | classified or flagged, never guessed | **1974 cutoff** |
| **7** | **The single sweep** (re-scoped 2026-09-05: grade B and C acts only; grade A acts are repaired by rebuild from the Gazette, not by re-photograph) | full re-ingest of the snapshot-based acts through the fixed pipeline | **when it may run** |
| **8** | Close catalogue; flip every gate hard-fail; assert ДВ-readiness | zero across all detectors; both review tracks clean | none |

### The sweep, phase 7

One sweep repairs every act that keeps a lex.bg base, per Directive 14; its traffic shrinks with
every act that moves to grade A (design section 8). Preconditions, all mandatory:

- Every parser fix from phases 1 to 6 is merged to `main`.
- Every detector reports its expected pre-sweep floor, recorded per class.
- `.fr034-baseline.json` and `.article-baseline.json` are backed up outside the repo; both are
  pre-repair floors and cannot be regenerated afterwards. Copies exist in
  `.superpowers/fr034-preserved/` as of 2026-08-11.
- `.refresh-state.json` is backed up and then deleted. A surviving checkpoint makes the sweep a
  silent no-op; this has bitten two prior sessions.
- The write gate is live, so the sweep cannot itself introduce a violation: an act that fails the
  invariants is not written, and the failure is recorded for adjudication.

During the sweep, a gate failure is **the gate working**. Record the act and its violating anchors;
never disable the gate to let a write through. On a Cloudflare challenge, stop and report; cookie
minting is interactive.

After the sweep: re-run every detector, re-run both baselines' comparison scripts, and re-run the
two review tracks. Only then may a class be marked closed in the catalogue.

### Effort shape

Phase 0 is days and unblocks measurement of everything. Phases 1 to 4 are each a small number of
legs, because their rules are decidable once adjudicated. Phase 5 is the long one, since it needs an
agentic reasoning pass over every flagged marker with cached, auditable verdicts. Phase 6 is a
schema migration plus a classifier. Phase 7 is roughly two hours of fetching plus verification.
Phase 8 is a day. The critical path runs through phases 1, 2 and 3, and none of them can start
before phase 0 exists.

## Part VI — Owner decisions required

Three of these block phases; the rest can be answered as their phase approaches. Nothing in
phase 0 or phase 1 waits on any of them, so execution can begin immediately.

| # | Decision | Blocks | Why it cannot be decided by an implementer |
|---|---|---|---|
| **O-1** | **Canonical form of a superscript article index** — `260и1`, Unicode `260и¹`, or a suffix convention; and whether old collapsed keys keep an alias | phase 2 | It changes the public address space and every citation the corpus has ever answered |
| **O-2** | **Era cutoff for position-derived алинеи** — is 1974 (Указ 883) the right boundary for emitting implicit alineas | phase 6 | A doctrinal question about Bulgarian citation practice, not an engineering one |
| **O-3** | **When the repair sweep may run** — it is roughly two hours of lex.bg traffic and needs interactive Cloudflare cookie minting | phase 7 | Operational and traffic-policy judgement |
| **O-4** | **cf-plane implicit-alinea behaviour** — mirror the labelled REST surface or skip implicit rows on the public plane | the D1 regeneration, independently of this plan | Without it an unlabelled export would serve 21 043 position-derived numbers as if the legislator had printed them |
| **O-5** | **Register FR-037 or fold it into FR-030** — the working branch uses an FR number registered nowhere. *Resolved 2026-09-05: registered as FR-037 (PR #25); branch pushed as PR #26.* | phase 3 (Directive 13) | Governance identity |
| **O-6** | **Directive 2 amendment or waiver** — „lex.bg = bootstrap only; ДВ = ongoing source“ is contradicted by current practice, since `refresh.py` is an ongoing lex.bg pipeline and the ДВ monitor is Backlog. *Resolved 2026-09-05: Directive 2 rewritten to the graded source model (D-059, PR #25).* | nothing, but it misstates the operating model | Only the owner may amend a directive |
| **O-7** | **Non-monotonic allowlist** — confirm each entry with a source citation once phase 3 produces the candidate list | phase 3 closure | Each entry is an assertion about a specific act's real numbering |
| **O-8** | **Capture cross-reference spans now, or lose them** (C9) — lex.bg marks up all 1 662 inline references and the converter discards them; ДВ has no equivalent markup. *Answered 2026-09-05: yes, for every act that keeps a lex.bg base (grades B and C), before its snapshot is frozen; unnecessary for grade A acts (FR-041).* | nothing today, everything after cutover | A capture-now-or-lose-it call, not a build-the-graph call |
| **O-9** | *Resolved 2026-09-05 (D-060, PR #25): canonical = 4-operation kernel + enumerated elaboration grammar.* **Reconcile the operation taxonomy** — the coverage floor names **7** ЗИД operation types, FR-003 names **5**, and the ratified engine model is a **4-operation kernel** in which renumbering and restructuring are explicitly not operation types. A gate written against "all 7" cannot be satisfied against a 4-operation kernel | Phase 4 acceptance | Three live authority surfaces disagree; only the owner can pick the canonical set |
| **O-10** | *Resolved 2026-09-05 (D-060, PR #25): struck; Phase 4 DoD rewritten.* **Strike the percentage bar in the delivery contract** — its Phase 4 definition of done still requires "accuracy ≥ 70 % regex-only, ≥ 90 % with fallback", which Directive 9 now forbids as evidence of closure. Both are live and binding | Phase 4 acceptance | Two authority surfaces in direct contradiction |
| **O-11** | *Resolved 2026-09-05 (D-060 to D-062, PR #25).* **Record the decisions that were ratified and never written** — the LawVM two-level model was ratified in substance, its governance edits were held, and the identifiers reserved for them (D-043 to D-046) were later consumed by other work. The engine model currently has no decision record at all | Phase 4 start | Governance integrity |

### Recommendation on scope

Fold C5 and C6 into this plan rather than running them separately, which is what the frozen
anchor-integrity effort's own final session recommended before it stopped. Both are upstream of or
derived from the classes that plan already covers, and separating them guarantees either a second
sweep or an anchor rule adjudicated against a corrupt heading state.

## Progress ledger

Maintained by the orchestrator, one row per round, per I.7.

| Round | Phase | Dispositions | Findings attacking last round | Injection ratio | Reopened | Detector zeros |
|---|---|---|---|---|---|---|
| — | — | — | — | — | — | — |
