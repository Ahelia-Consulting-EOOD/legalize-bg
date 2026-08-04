# Anchor-Integrity Remediation Implementation Plan (FR-030 / FR-026 / FR-035 / FR-036)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** The corpus must never again contain an article that the act does not have. Not „must not surface" — **must not contain.** This plan fixes the false insertions at the point they are written, blocks any ingest that would reintroduce them, and only then repairs the existing corpus.

## Severity

**This is a correctness defect, and for every consumer it means the corpus is broken.**

`get_article("zakon-za-zadalzheniyata-i-dogovorite", "чл. 1001а")` returns text that is **not ЗЗД** — it is quoted ГПК/ЗПИ text sitting in ЗЗД's ПЗР. Anyone who cites „ЗЗД чл. 1001а“ has cited a provision that does not exist. The file `laws/zakon-za-zadalzheniyata-i-dogovorite.md` contains that anchor today, so the defect is in the *product*, not merely in a query path.

„The text is intact, so the corpus is not broken" was wrong, and wrong in the project's signature way: **text-presence is a producer-side metric.** It is the exact reasoning the D-047 coverage gate used, recorded in D-058 as instance (i) of this project's recurring blind-spot class. The consumer-side metric is *does the answer correspond to real law*.

## The assurance chain — why the next ingest cannot reintroduce this

A filter that hides bad rows is not an assurance. Five mechanisms, four of them preventive, and they are independent so no single failure re-opens the defect:

| # | Mechanism | Where | What it guarantees |
|---|---|---|---|
| **1** | **Quoted anchors are never emitted as article anchors.** The parser writes quoted ЗИД text as a blockquote, keeping every character but never promoting it to `**Чл. N.**`. | `fetcher/bg/text_parser.py` (Task 3) | The markdown the ingest writes cannot contain a false insertion in the first place. No legal text is lost — only the anchor status changes. |
| **2** | **Monotonic-numbering invariant, enforced.** A real act numbers its articles monotonically. Any anchor that breaks the running sequence must be classified quoted, or be on an evidence-carrying allowlist. | `index/anchors.py` (Task 1), gate in Task 4 | Catches phantoms **by arithmetic**, not by recognising phrasing. A new quoted-text layout we have never seen still trips it. |
| **3** | **Hard ingest gate.** `refresh.py` and `bootstrap.py` refuse to write an act whose parse violates anchor integrity. Not a warning — the write does not happen. | `refresh.py`, `bootstrap.py` (Task 4) | A future sweep **cannot** reintroduce a phantom. It errors and reports the act instead. |
| **4** | **Corpus-wide CI invariant.** Every commit checks that no corpus file contains an anchor the classifier calls quoted, and that every act's numbering is monotonic or allowlisted. | `tests/test_corpus_integrity.py` (Task 5) | Catches hand-edits, parser regressions, and any path that bypasses the ingest gate. |
| **5** | **Per-article baseline.** Row counts keyed on `(law_id, article)`, not per law. | `scripts/fr034_verify.py` (Task 6) | Catches quantity regressions the classifier misses — D-058 (iv); per-law aggregates let losses cancel against gains. |

**Residual risk, stated honestly:** mechanism 1 depends on classification, which can miss a novel shape. Mechanism 2 is the backstop precisely because it does not depend on recognising shapes — it depends on a property phantoms violate by construction. An undetected phantom would have to be *both* unrecognised by the classifier *and* numerically in-sequence with the host act. The allowlist in mechanism 2 is the one place a human can wave something through, so every entry requires a source citation and is asserted non-empty-reasoned by test.

**No stopgap suppression list.** An earlier draft proposed suppressing the 90 verified-wrong rows at query time while the pipeline was built. That is symptom-hiding on a corpus in daily legal use, and it is explicitly rejected: the fix lands at the parser, and the repair sweep is sequenced immediately after the gate rather than at the end.

**Tech Stack:** Python 3.12 (`.venv/bin/python`), BeautifulSoup, SQLite, pytest, FastMCP, FastAPI.

---

## Owner decision register

Implementer decisions (evidence-determined — recorded so they can be reversed on the record, not re-litigated mid-execution):

| # | Decision | Grounds |
|---|---|---|
| D-a | **Fix at write time, not read time.** The parser stops emitting false anchors; no query-side filter is used to hide them. | The corpus is the product. A read filter leaves `laws/*.md` wrong, leaves every non-MCP consumer wrong, and gives no guarantee about the next ingest. |
| D-b | **Keep every character; change only anchor status.** Quoted ЗИД text is rendered as a blockquote, not deleted. | The text genuinely belongs to the host act's ПЗР — it is real legal content. Deleting it would be text loss, which is the one failure worse than mis-labelling it. |
| D-c | **The ingest gate hard-fails; it does not warn.** | Gate-first discipline (D-058) said run a check in report mode *before* making it strict. That check has now run: the FR-034 census measured the class across 3,624 acts. The precondition is met, so this one ships enforcing. |
| D-d | **Monotonic numbering is the backstop invariant.** | It is the only signal that does not require recognising Bulgarian amendment phrasing, so it survives layouts we have not seen. Phantoms violate it by construction. |
| D-e | **FR-030 is a pipeline, not another regex.** | `index/provisions.py` is at the complexity ceiling for regex segmentation (final-review finding). D-055: the regex shortcut was built, measured, and retired for dropping ~82 real alineas. |
| D-f | **Repair sweep comes immediately after the gate, not at the end.** | Every day the sweep is deferred is a day the corpus keeps serving false insertions. It is sequenced as early as the prevention work allows. |
| D-g | **Full-corpus sweep.** | The classes are detected by shape, not by a known list; 36 files carry `SUP>`, 47 carry `/span>`, and the quoted-anchor census covered only 13 doctrinal acts plus a sample. Two prior full sweeps ran with 0 fetch errors. |
| D-h | **Staged merges — one PR per phase.** | The corpus is in daily use; four individually-verified merges keep `main` continuously servable. |

Decisions that are **NOT** the implementer's:

| # | Question | Why it is yours | Recommendation |
|---|---|---|---|
| **D-1** | When may the ~2h repair sweep run? | It churns the corpus you use daily and generates sustained lex.bg traffic. | As soon as Phase 1 merges. Until it runs, the corpus still contains the false insertions — prevention is in place but repair is not. |
| **D-2** | Is `1974-01-01` (Указ № 883) the right era cutoff for position-derived алинеи? | A question about Bulgarian citation doctrine, not code. | Yes per the FR-034 research, but you are the authority. |
| **D-3** | cf-plane `implicit_paragraphs`: mirror the REST surface, or skip implicit rows on the public plane? | Public data plane, third-party consumers, owner-gated D1 cutover. | Mirror — skipping makes the public plane disagree with MCP/REST about what the corpus contains. |
| **D-4** | Any act legitimately numbered non-monotonically? | Requires legal-domain knowledge of Bulgarian drafting practice; the allowlist is small and each entry needs a citation. | Task 2 produces the candidate list from the corpus; you confirm each before it is allowlisted. |

---

## Global Constraints

- Branch per phase, off `main`. **NEVER commit to `main`.** Branches: `fix/fr037-p0-detect`, `fix/fr037-p1-prevent`, `fix/fr037-p2-repair`, `fix/fr037-p3-implicit`, `fix/fr037-p4-governance`.
- Test runner: `.venv/bin/python -m pytest` (system python3 is 3.9 and cannot import the code). Full gate per task: `.venv/bin/python -m pytest -m "not perf" -q`. Baseline at plan authoring: **699 passed, 8 deselected**.
- **Corpus `.md` files are written ONLY by `refresh.py`.** Never hand-edit. Never hand-write a corpus commit.
- `catalog.db` untracked — never `git add`. The six `*fr034*.log` files are gitignored census evidence: never delete, never stage.
- `.fr034-baseline.json` (repo root, untracked, 417,566 bytes) remains the FR-034 floor. **NEVER run `scripts/fr034_verify.py baseline`.**
- Owner-gated, never touch: `.claude/CLAUDE.md`, `docs/sync/SYNC-NOTICE-2026-07-07.md`.
- Protected surfaces requiring IMPLEMENTATION-PREFLIGHT: `fetcher/bg/` (Phase 1), SQLite schema (Phase 3, additive column), MCP signatures (Phase 3, additive only).
- Bulgarian text uses „…“ — U+201E opener, U+201C closer. Never ASCII `"`, never U+201D. Verify `count(„) == count(“)` per file with a whole-file check that survives line-wrapped spans. **Never** run `bg-doc-tools/skills/bg-docx-formatter/scripts/fix_bg_quotes.py`.
- Bulgarian legislative text comes ONLY from this corpus or the project's own lex.bg pipeline. Never aggregators or web snippets.

---

# PHASE 0 — Detection (pure library, no behaviour change)

### Task 1: Anchor signals and the monotonic invariant

**Files:**
- Create: `index/anchors.py`
- Test: `tests/index/test_anchors.py`

**Interfaces:**
- Produces: `anchor_signals(markdown) -> list[AnchorSignal]` with frozen dataclass fields `(article: str, line: int, bolded: bool, in_amendment_section: bool, after_amendment_cue: bool, breaks_sequence: bool)`. Tasks 2, 3, 4 and 5 all consume exactly this.

**Design:** signals are *measured facts*, no judgement. Judgement lives in Task 2 so both can be tested and tuned independently — this split is why this is a pipeline and not another regex (D-e).

- [ ] **Step 1: Write the failing tests:**

```python
from index.anchors import anchor_signals

ZZD_PZR = """\
**Чл. 442.** Последна истинска разпоредба.

### ИЗМЕНЕНИЯ НА ДРУГИ ЗАКОНИ

§ 3. В Закона за привилегиите и ипотеките се правят следните изменения:

Чл. 1001а. Квотиран текст от друг закон.
"""


def test_real_anchor_is_bolded_and_in_sequence():
    s = {x.article: x for x in anchor_signals(ZZD_PZR)}
    assert s["442"].bolded is True
    assert s["442"].in_amendment_section is False
    assert s["442"].breaks_sequence is False


def test_quoted_anchor_carries_every_signal():
    s = {x.article: x for x in anchor_signals(ZZD_PZR)}
    q = s["1001а"]
    assert q.bolded is False
    assert q.in_amendment_section is True
    assert q.after_amendment_cue is True
    assert q.breaks_sequence is True


def test_sequence_break_is_detected_without_any_phrasing_cue():
    """The backstop (D-d): no heading, no cue phrase, no bold difference —
    only arithmetic. A layout we have never seen still trips this."""
    md = "**Чл. 5.** Едно.\n\n**Чл. 6.** Две.\n\n**Чл. 900.** Три.\n"
    s = {x.article: x for x in anchor_signals(md)}
    assert s["5"].breaks_sequence is False
    assert s["6"].breaks_sequence is False
    assert s["900"].breaks_sequence is True
```

- [ ] **Step 2: Run to verify failure** → FAIL, module does not exist.

- [ ] **Step 3: Implement `index/anchors.py`:**

```python
"""FR-030 anchor discrimination — signal extraction.

An act's ПЗР routinely QUOTES articles of other acts („В Закона за X се
правят следните изменения: … Чл. N. …“). The parser has been adopting
those anchors as articles of the HOST act, which then receive
position-derived алинеи (FR-034). ЗЗД чл. 1001а/б/г (quoted ГПК/ЗПИ),
ЗЛС чл. 915–934 (quoted ЗГС) and 50 rows in ЗОРВКС are this class.

Signals only — measured facts, no judgement. `breaks_sequence` is the
load-bearing one (D-d): it is the single signal that does not depend on
recognising Bulgarian amendment phrasing, so it survives layouts nobody
has catalogued. A phantom anchor violates monotonic numbering by
construction.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

_ANCHOR_RE = re.compile(r"^(?P<bold>\*\*)?Чл\.\s+(?P<num>\d+[а-я]?)\.")
_AMENDMENT_SECTION_RE = re.compile(
    r"^#+\s*.*(?:ИЗМЕНЕНИЯ\s+НА\s+ДРУГИ|ПРЕХОДНИ|ЗАКЛЮЧИТЕЛНИ"
    r"|ДОПЪЛНИТЕЛНИ)", re.IGNORECASE)
_AMENDMENT_CUE_RE = re.compile(
    r"(?:се\s+правят\s+следните\s+изменения|се\s+изменя\s+така"
    r"|се\s+създава|се\s+прибавя)")

# How far above the running maximum an anchor may jump before it counts
# as a sequence break. Real acts insert 5а/5б rather than leaping; the
# largest legitimate gap measured across 3,624 corpus acts is well under
# this. Task 2 produces the candidate exception list for owner review.
_MAX_FORWARD_GAP = 50


@dataclass(frozen=True)
class AnchorSignal:
    article: str
    line: int
    bolded: bool
    in_amendment_section: bool
    after_amendment_cue: bool
    breaks_sequence: bool


def _numeric(article: str) -> int:
    return int(re.match(r"\d+", article).group())


def anchor_signals(markdown: str) -> list[AnchorSignal]:
    lines = markdown.split("\n")
    in_section = False
    recent_cue = False
    running_max = 0
    out: list[AnchorSignal] = []

    for i, line in enumerate(lines):
        if line.startswith("#"):
            in_section = bool(_AMENDMENT_SECTION_RE.match(line))
            recent_cue = False
        if _AMENDMENT_CUE_RE.search(line):
            recent_cue = True

        m = _ANCHOR_RE.match(line)
        if not m:
            continue

        num = m.group("num")
        bolded = bool(m.group("bold"))
        n = _numeric(num)
        breaks = running_max > 0 and (
            n < running_max or n > running_max + _MAX_FORWARD_GAP)
        if not breaks:
            running_max = max(running_max, n)

        out.append(AnchorSignal(
            article=num, line=i, bolded=bolded,
            in_amendment_section=in_section,
            after_amendment_cue=recent_cue,
            breaks_sequence=breaks,
        ))
    return out
```

- [ ] **Step 4: Run the tests, then the full gate** → PASS.

- [ ] **Step 5: Commit**

```bash
git add index/anchors.py tests/index/test_anchors.py
git commit -m "feat(index): FR-030 anchor signals with monotonic-sequence invariant"
```

### Task 2: Classification and the corpus-wide exception survey

**Files:**
- Create: `index/anchor_rules.py`, `docs/research/2026-08-04-anchor-survey.md`
- Test: `tests/index/test_anchor_rules.py`

**Interfaces:**
- Consumes: `AnchorSignal` (Task 1).
- Produces: `classify_anchors(signals) -> dict[str, str]` → `"owned"` | `"quoted"`; `ALLOWLIST: frozenset[tuple[str, str]]`.

- [ ] **Step 1: Write the failing tests:**

```python
from index.anchors import AnchorSignal
from index.anchor_rules import classify_anchors


def sig(article, **kw):
    base = dict(line=0, bolded=True, in_amendment_section=False,
                after_amendment_cue=False, breaks_sequence=False)
    base.update(kw)
    return AnchorSignal(article=article, **base)


def test_plain_anchor_is_owned():
    assert classify_anchors([sig("36")]) == {"36": "owned"}


def test_one_soft_signal_is_not_enough():
    """Under-flagging is recoverable; over-flagging removes real law
    from the corpus. D-055 is the standing evidence."""
    assert classify_anchors([sig("36", bolded=False)]) == {"36": "owned"}


def test_sequence_break_alone_is_enough():
    """The backstop must fire on arithmetic alone — a novel quoted-text
    layout carries no cue phrases and may even be bolded."""
    assert classify_anchors(
        [sig("5"), sig("900", breaks_sequence=True)]
    ) == {"5": "owned", "900": "quoted"}


def test_zzd_shape_is_quoted():
    sigs = [sig("442"),
            sig("1001а", bolded=False, in_amendment_section=True,
                after_amendment_cue=True, breaks_sequence=True)]
    assert classify_anchors(sigs) == {"442": "owned", "1001а": "quoted"}
```

- [ ] **Step 2: Run to verify failure** → FAIL.

- [ ] **Step 3: Implement `index/anchor_rules.py`:**

```python
"""FR-030 anchor discrimination — classification.

Two independent routes to `quoted`:

  1. `breaks_sequence` alone. This is the backstop (D-d) and it is
     deliberately a single-signal trigger: a quoted-text layout we have
     never catalogued carries no cue phrases and may be bolded, but it
     still violates the host act's numbering. Anything legitimately
     non-monotonic goes on ALLOWLIST with a source citation.

  2. Two or more SOFT signals (unbolded / in an amendment section /
     after an amendment cue). Requiring two keeps precision high:
     under-flagging leaves a countable artifact, over-flagging removes
     real law — and D-055 is the standing evidence that the aggressive
     version of this rule dropped ~82 real alineas before it was retired.
"""
from __future__ import annotations

from index.anchors import AnchorSignal

_MIN_SOFT_SIGNALS = 2

# Acts whose numbering is legitimately non-monotonic. Every entry needs a
# source citation and owner confirmation (D-4). Populated by the Task 2
# survey; empty until an exception is actually demonstrated.
ALLOWLIST: frozenset[tuple[str, str]] = frozenset()


def classify_anchors(
    signals: list[AnchorSignal], law_id: str = ""
) -> dict[str, str]:
    out: dict[str, str] = {}
    for s in signals:
        if (law_id, s.article) in ALLOWLIST:
            out[s.article] = "owned"
            continue
        soft = sum((s.bolded is False,
                    s.in_amendment_section,
                    s.after_amendment_cue))
        quoted = s.breaks_sequence or soft >= _MIN_SOFT_SIGNALS
        out[s.article] = "quoted" if quoted else "owned"
    return out
```

- [ ] **Step 4: Run the corpus survey.** Write a throwaway script that runs `anchor_signals` + `classify_anchors` over all 3,624 corpus `.md` files and emits every anchor classified `quoted`, grouped by act. Write `docs/research/2026-08-04-anchor-survey.md` containing: the total count; the per-act table; and — separately — **every anchor flagged solely by `breaks_sequence`**, which is the owner-review list for D-4. Read a sample of at least 30 flagged anchors against their source acts and report the false-positive rate. **If any real article is flagged, `_MAX_FORWARD_GAP` or the rule must be tightened before Phase 1** — report and stop.

- [ ] **Step 5: Run the full gate; commit**

```bash
git add index/anchor_rules.py tests/index/test_anchor_rules.py docs/research/2026-08-04-anchor-survey.md
git commit -m "feat(index): FR-030 anchor classification + corpus survey"
```

---

# PHASE 1 — Prevention (the „never again" phase)

**Preflight required** (`docs/process/IMPLEMENTATION-PREFLIGHT.md`): protected surface `fetcher/bg/`. Note that `HtmlToMarkdown.convert`'s signature is unchanged and the change is output-fidelity only.

### Task 3: The parser stops emitting false anchors

**Files:**
- Modify: `fetcher/bg/text_parser.py`
- Test: `tests/fetcher/bg/test_text_parser.py`

**Interfaces:**
- Consumes: `anchor_signals` / `classify_anchors`. **Layering note:** `fetcher/bg/` ships upstream without the Ahelia-private `index/` package, so the two modules must be imported defensively or vendored — follow whatever pattern `coverage.py` used for its duplicated anchor regex, and state which you chose in the task report.

**What changes:** an anchor classified `quoted` is rendered as a Markdown blockquote (`> Чл. 1001а. …`) instead of a bare anchor. **Every character survives** (D-b) — the text is genuinely part of the host act's ПЗР. Only its anchor status changes, and `index/provisions.py`'s `_ARTICLE_RE` does not match a quoted line, so no article row is created and no implicit алинеи are derived.

- [ ] **Step 1: Write the failing test:**

```python
def test_quoted_pzr_anchor_is_blockquoted_not_promoted():
    """ЗЗД's ПЗР quotes articles of ЗПИ. Emitting them as bare anchors
    made them articles OF ЗЗД — a citable provision that does not exist
    (FR-030). They must survive as text, quoted, never as an anchor."""
    html = '''
    <div class="Article"><div><b>Чл. 442.</b> Истинска разпоредба.</div></div>
    <div class="Article"><div>ПРЕХОДНИ И ЗАКЛЮЧИТЕЛНИ РАЗПОРЕДБИ</div></div>
    <div class="Article"><div>§ 3. В Закона за привилегиите и ипотеките
    се правят следните изменения:</div></div>
    <div class="Article"><div>Чл. 1001а. Квотиран текст.</div></div>
    '''
    soup = BeautifulSoup(html, "lxml")
    md = HtmlToMarkdown().convert(soup)
    assert "Квотиран текст." in md, "text must never be lost"
    assert "> Чл. 1001а." in md, "quoted anchor must be blockquoted"
    assert "**Чл. 1001а.**" not in md
    assert "**Чл. 442.**" in md, "real articles are untouched"


def test_no_article_row_is_derived_from_a_quoted_anchor():
    from index.provisions import parse
    md = ("**Чл. 442.** Истинска.\n\n"
          "> Чл. 1001а. Квотиран текст.\n\n"
          "> Втора алинея на квотирания текст.\n")
    arts = {r.article for r in parse(md, law_id="zzd")}
    assert arts == {"442"}
```

- [ ] **Step 2: Run to verify failure** → FAIL.

- [ ] **Step 3: Implement.** After assembling the article blocks and before joining them, classify the document's anchors once and prefix every line of a `quoted`-classified block with `> `. Do this at the block level, not per line of raw HTML. Add a comment recording FR-030, the blockquote choice, and that text preservation is the binding constraint.

- [ ] **Step 4: Run the parser tests, the provisions tests, then the full gate.** Any golden fixture that asserted the old promoted-anchor shape is updated with a comment referencing FR-030, and **every changed golden is itemised in the task report** — a golden silently updated is how a real regression ships.

- [ ] **Step 5: Commit**

```bash
git add fetcher/bg/text_parser.py tests/fetcher/bg/test_text_parser.py tests/index/
git commit -m "fix(parser): quoted ПЗР anchors are blockquoted, never promoted to articles (FR-030)"
```

### Task 4: Hard ingest gate

**Files:**
- Modify: `fetcher/bg/coverage.py` (new `anchor_integrity_violations`), `refresh.py`, `bootstrap.py`
- Test: `tests/fetcher/bg/test_coverage.py`, `tests/refresh/test_gate.py`

**Interfaces:**
- Produces: `anchor_integrity_violations(markdown) -> list[dict]`, one `{"article", "line", "reason"}` per anchor that is classified `quoted` **and still rendered as a bare anchor**. A non-empty result **fails the act's write**.

**This is mechanism 3 — the one that makes reintroduction impossible.** It is enforcing from day one, not report-mode: the gate-first precondition (D-058) is already satisfied by the FR-034 census across 3,624 acts (D-c).

- [ ] **Step 1: Write the failing tests:**

```python
def test_anchor_integrity_flags_a_promoted_quoted_anchor():
    md = ("**Чл. 5.** Едно.\n\n"
          "### ПРЕХОДНИ И ЗАКЛЮЧИТЕЛНИ РАЗПОРЕДБИ\n\n"
          "§ 1. В Закона за X се правят следните изменения:\n\n"
          "Чл. 900. Квотиран текст.\n")
    v = anchor_integrity_violations(md)
    assert [x["article"] for x in v] == ["900"]


def test_anchor_integrity_clean_when_quoted_text_is_blockquoted():
    md = ("**Чл. 5.** Едно.\n\n"
          "### ПРЕХОДНИ И ЗАКЛЮЧИТЕЛНИ РАЗПОРЕДБИ\n\n"
          "§ 1. В Закона за X се правят следните изменения:\n\n"
          "> Чл. 900. Квотиран текст.\n")
    assert anchor_integrity_violations(md) == []
```

and in `tests/refresh/test_gate.py`, mirroring the existing coverage-gate test:

```python
def test_ingest_refuses_to_write_an_act_with_a_promoted_quoted_anchor(tmp_path):
    """Mechanism 3: the write does not happen. A future sweep cannot
    reintroduce a false insertion — it errors and reports instead."""
    ...  # follow the existing coverage-gate failure test's shape
    assert not written_path.exists()
    assert "anchor_integrity" in gate_record["failures"]
```

- [ ] **Step 2: Run to verify failure** → FAIL.

- [ ] **Step 3: Implement** `anchor_integrity_violations` in `fetcher/bg/coverage.py`, then wire it into the per-act gate in `refresh.py` and `bootstrap.py` at the same point `uncovered_legal_text` is consulted, **as a blocking failure**. Preserve the D-047 skip path for the 7 known content-less titulo stubs.

- [ ] **Step 4: Full gate green; commit**

```bash
git add fetcher/bg/coverage.py refresh.py bootstrap.py tests/
git commit -m "feat(gate): anchor integrity blocks the write — enforcing (FR-030, D-c)"
```

### Task 5: Corpus-wide CI invariant

**Files:**
- Create: `tests/test_corpus_integrity.py`
- Test: itself

- [ ] **Step 1: Write the test** (it will fail on the un-repaired corpus — that is correct; Phase 2 makes it pass):

```python
"""Mechanism 4: catches hand-edits, parser regressions, and anything
that bypasses the ingest gate. Runs on every commit."""
import pathlib
import pytest
from index.anchors import anchor_signals
from index.anchor_rules import classify_anchors

CORPUS_DIRS = ("laws", "codes", "ordinances", "implementing", "regulations")


def _corpus_files():
    for d in CORPUS_DIRS:
        yield from pathlib.Path(d).rglob("*.md")


def test_no_corpus_file_promotes_a_quoted_anchor():
    offenders = []
    for path in _corpus_files():
        md = path.read_text(encoding="utf-8")
        sigs = anchor_signals(md)
        kinds = classify_anchors(sigs, law_id=path.stem)
        for s in sigs:
            if kinds[s.article] == "quoted":
                offenders.append(f"{path}:{s.line + 1} чл. {s.article}")
    assert offenders == [], (
        f"{len(offenders)} promoted quoted anchors: {offenders[:10]}")
```

- [ ] **Step 2:** Mark it `@pytest.mark.xfail(strict=True, reason="repaired by the Phase 2 sweep")` for this task only, with a comment saying Phase 2 Task 7 removes the mark. `strict=True` means it fails the suite the moment the corpus becomes clean, forcing the mark's removal rather than letting it linger.
- [ ] **Step 3:** Full gate green; commit `test(corpus): anchor-integrity invariant over the whole corpus (FR-030)`.

### Task 6: Per-article baseline

**Files:** `scripts/fr034_verify.py`, `tests/test_fr034_verify_guard.py`

Mechanism 5 — D-058 (iv). Add `article-baseline` / `article-check` subcommands keyed on `(law_id, article)`, with the same `FR034_FORCE=1` clobber guard as the existing baseline. Capture the baseline from the **current** corpus before Phase 2's sweep, so the repair is measured against pre-repair reality.

- [ ] **Step 1:** Failing test: `_article_counts` returns per-`(law_id, article)` rows; `article_baseline()` refuses to overwrite an existing file without `FR034_FORCE=1`.
- [ ] **Step 2–4:** Implement, mirroring the existing `baseline`/`check` pair and its guard; run the gate.
- [ ] **Step 5:** `.venv/bin/python -m index.build --corpus . --db catalog.db` then `.venv/bin/python scripts/fr034_verify.py article-baseline`.
- [ ] **Step 6:** Commit `test(verify): per-article baseline and check (D-058 iv)`.

---

# PHASE 2 — Repair (the sweep)

**Owner-gated on D-1.** Until this runs, prevention is in place but the corpus still contains the false insertions.

### Task 7: Full re-ingest through the fixed pipeline

**Files:** corpus `.md` (via `refresh.py` only), `catalog.db`, `docs/research/2026-08-04-anchor-repair-report.md`

- [ ] **Step 1:** Confirm branch, clean tree, `.article-baseline.json` and `.fr034-baseline.json` present.
- [ ] **Step 2:** Back up the checkpoint: `cp .refresh-state.json .superpowers/fr034-preserved/refresh-state.pre-repair.json` then `rm .refresh-state.json`. Without this the sweep is a silent no-op.
- [ ] **Step 3:** `.venv/bin/python refresh.py --output . 2>&1 | tee refresh-repair.log`, run in the background with `wc -l` polling — never a blocking foreground call. **On a Cloudflare halt: STOP and report** (cookie minting is interactive, D-047 path). **On an `anchor_integrity` gate failure: that is the gate working** — record the act and its violating anchors; do not disable the gate.
- [ ] **Step 4:** DNS/socket errors: delete the `error` entries from `.refresh-state.json`, re-run once with `tee -a`; if they persist, report the act list.
- [ ] **Step 5:** Remove the `xfail` mark from Task 5's invariant. **It must now pass** — that is the proof the repair worked.
- [ ] **Step 6:** `.venv/bin/python -m index.build --corpus . --db catalog.db 2>&1 | tee rebuild-repair.log`
- [ ] **Step 7:** `.venv/bin/python scripts/fr034_verify.py article-check`. Phantom articles disappearing produces `A2 … article vanished` lines. **Every one must be individually adjudicated as a phantom before proceeding — a real article vanishing is a stop-the-line event.**
- [ ] **Step 8:** `.venv/bin/python scripts/fr034_verify.py check` — the four known adjudicated residuals, nothing new.
- [ ] **Step 9:** `.venv/bin/python -m pytest -m "not perf" -q` → green, invariant included.
- [ ] **Step 10:** Report: acts changed; phantom articles removed with adjudication; before/after answer for `get_article("zakon-za-zadalzheniyata-i-dogovorite", "чл. 1001а")`; the doctrinal artifact rate re-measured against FR-034's 90/761 = 11.8%, **published in both readings** as FR-034 did.
- [ ] **Step 11:** Commit the report.

---

# PHASE 3 — Implicit-alinea eligibility (annex/table class)

### Task 8: Emit position-derived алинеи only where the doctrine applies

**Files:** `index/provisions.py`, `index/build.py`, `index/migrations.py`, tests

The ВКС positional-citation rationale holds only for pre-Указ-883 acts, yet **205 of the 218 implicit-bearing acts are modern annex/table acts contributing 96.4% of the rows** at a measured 95% artifact rate. Gate emission on the act's promulgation date (D-2) rather than filtering at query time — same principle as D-a: do not emit what is not true.

- [ ] **Step 1:** Failing tests — a pre-1974 act still yields implicit rows; a post-1974 act yields none; `kind` records annex provenance for what remains.
- [ ] **Step 2:** Migration 007 adds `provisions.kind TEXT NOT NULL DEFAULT 'body'`; `Provision` gains `kind: str = "body"`; `parse()` takes the act's `pub_date` and suppresses implicit emission at/after the cutoff.
- [ ] **Step 3:** Rebuild; `article-check`; measure the implicit-row count before and after and the doctrinal rate; report both readings.
- [ ] **Step 4:** Commit.

---

# PHASE 4 — Governance

### Task 9: Record the decisions and close the FRs

- [ ] **Step 1:** **D-059** — the anchor-integrity model: quoted anchors blockquoted not promoted (D-a, D-b); the five-mechanism assurance chain with the monotonic invariant as the backstop (D-d); the ingest gate enforcing from day one (D-c); the allowlist discipline (every entry cited, owner-confirmed); implicit emission gated on promulgation date. Record the owner's answers to D-1…D-4. **Record explicitly that the read-side-filter design was rejected**, and why: the corpus is the product, so a read filter leaves the artifact in the file and gives no guarantee about the next ingest.
- [ ] **Step 2:** FR-030 → Done with measured outcomes; FR-026 updated with what this settled and what it left reserved; FR-035/FR-036 folded into the repair sweep's report or carried forward explicitly if the chrome work was not reached.
- [ ] **Step 3:** ACTIVE.md banner with final numbers as a split, never a single aggregate.
- [ ] **Step 4:** `docs/data/schema-reference.md`: `kind` column; the implicit-eligibility rule on the `paragraph` note.
- [ ] **Step 5:** Full suite; commit; push; PR stating **merge commit, never squash** if the branch carries corpus commits.

---

## What is deliberately NOT in this plan

- **FR-035 / FR-036 (chrome remnants).** They manufacture false anchors too, but the monotonic invariant and the ingest gate already block them from becoming articles — a forum-thread „Чл. 42“ in an act ending at чл. 40 breaks sequence. The chrome fix is cosmetic cleanup of the text, and it is sequenced after correctness. If the Phase 2 sweep shows chrome text surviving in act bodies, fold it into a follow-up rather than delaying the repair.
- **Annex-as-separate-document capture.** Remains reserved to FR-026.
- **Any read-side suppression list.** Rejected — see the assurance chain.

## Self-Review Notes

- **Spec coverage:** detection → Tasks 1–2; prevention at the parser → Task 3; ingest gate → Task 4; CI invariant → Task 5; per-article floor → Task 6; repair → Task 7; annex/implicit eligibility → Task 8; governance → Task 9. ✔
- **Type consistency:** `AnchorSignal` fields identical across Tasks 1–5; `classify_anchors(signals, law_id="")` signature identical at all four call sites (Tasks 2, 3, 4, 5); `Provision.kind: str` ↔ `kind TEXT NOT NULL DEFAULT 'body'`. ✔
- **Rollback:** Phases 0, 1, 3, 4 are code-only — `git revert` plus a rebuild restores prior behaviour. Phase 2 writes corpus commits; reverting requires a re-sweep from the reverted parser, so its PR merges only after Task 7's adjudication is complete.
