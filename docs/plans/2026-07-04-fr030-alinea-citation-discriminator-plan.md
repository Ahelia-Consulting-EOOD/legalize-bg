# FR-030 alinea/citation discriminator — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. **Standing project rule (owner, 2026-07-04):** every task, when green, passes a fresh-subagent code review → receive → fix → re-review until clean before advancing (memory: `per-task-fresh-subagent-review-loop`).

**Goal:** Stop `index/provisions.py` from mis-parsing parenthesised citation numbers (`чл. 8 (3)`, `четири (4)`, treaty/standard/grade refs) as alinea markers, without dropping real alineas.

**Architecture:** Replace "split on every `(N)` marker" with a two-signal discriminator — (1) sequence continuity (real alineas are contiguous from 1) and (2) a citation-context guard on the token preceding the marker. Both signals must pass for a marker to open an alinea. Design + empirical basis: `docs/plans/2026-07-04-fr030-alinea-citation-discriminator-design.md`.

**Tech Stack:** Python 3.12, stdlib `re`, pytest. Run tests with `.venv/bin/python -m pytest`.

## Global Constraints

- Change surface is `index/provisions.py` ONLY. No change to `_ALINEA_MARKER_RE`, `parse()` row shape, the `Provision` dataclass, the SQLite schema, or any MCP tool signature.
- No corpus markdown edits — this is a parse-time fix; `catalog.db` is derived/gitignored.
- Bulgarian source text; keep all Cyrillic literals exactly as written.
- TDD: no production code without a failing test first. Frequent commits.

---

### Task 1: Citation-context guard `_is_citation_context`

**Files:**
- Modify: `index/provisions.py` (add helper + module constants near `_ALINEA_MARKER_RE`, line ~167)
- Test: `tests/index/test_alinea_discriminator.py` (create)

**Interfaces:**
- Produces: `_is_citation_context(body: str, marker_start: int) -> bool` — True when the `(` at `body[marker_start]` is preceded by a citation token (digit-ending token, Roman numeral, cross-ref abbrev, or Cyrillic cardinal word); False when it opens a clause.

- [ ] **Step 1: Write the failing tests**

```python
# tests/index/test_alinea_discriminator.py
from index.provisions import _is_citation_context


def _at(body: str, needle: str = "(") -> int:
    return body.index(needle)


def test_citation_after_cross_ref_digit():
    # "чл. 8 (3)" — preceding token "8" ends in a digit
    body = "информацията по чл. 8 (3) от Регламент"
    assert _is_citation_context(body, _at(body)) is True


def test_citation_after_roman_numeral():
    body = "за прилагане на чл. III (1) и (4) от Договора"
    assert _is_citation_context(body, _at(body)) is True


def test_citation_after_cardinal_word():
    body = "четири (4) на сто от частта"
    assert _is_citation_context(body, _at(body)) is True


def test_clause_opener_after_word_is_not_citation():
    # ЗОП чл.196 real alinea (5): preceded by a word, no period
    body = "обявлението за доброволна прозрачност (5) На обжалване"
    assert _is_citation_context(body, _at(body)) is False


def test_clause_opener_at_start_is_not_citation():
    assert _is_citation_context("(1) Задълженията по тази глава", 0) is False
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/python -m pytest tests/index/test_alinea_discriminator.py -q`
Expected: FAIL with `ImportError: cannot import name '_is_citation_context'`

- [ ] **Step 3: Write the implementation**

Add near the top of `index/provisions.py` (after the imports, and before `_ALINEA_MARKER_RE`):

```python
_ROMAN_RE = re.compile(r"^[IVXLCM]{1,5}$")
# Cross-reference abbreviations (compared case-insensitively, trailing '.'
# stripped). A '(N)' right after one of these is a citation, not an alinea.
_CROSS_REF_TOKENS = {
    "чл", "ал", "т", "буква", "бук", "изр", "§", "регламент", "директива",
}
# Cyrillic cardinal-number words that precede an inline "(N)" gloss
# (e.g. "четири (4) на сто"). Seeded from the FR-030 scan; extend only from
# rebuild-diff evidence, never guesswork.
_CARDINAL_WORDS = {
    "нула", "едно", "една", "две", "два", "три", "четири", "пет",
    "шест", "седем", "осем", "девет", "десет",
}


def _is_citation_context(body: str, marker_start: int) -> bool:
    """True when the '(' at body[marker_start] is preceded by a citation
    token (so the "(N)" is a reference, not an alinea opener). See
    docs/plans/2026-07-04-fr030-...-design.md §3 Signal 2."""
    prefix = body[:marker_start].rstrip()
    if not prefix:
        return False  # start of body → clause opening
    prev = prefix.split()[-1]
    if prev[-1].isdigit():          # "чл. 8 (3)", "т. 5 (2)"
        return True
    if _ROMAN_RE.match(prev):       # "чл. III (1)"
        return True
    token = prev.lower().rstrip(".,:;")
    if token in _CROSS_REF_TOKENS:  # "чл.(3)"-style with no number between
        return True
    if token in _CARDINAL_WORDS:    # "четири (4)"
        return True
    return False
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/index/test_alinea_discriminator.py -q`
Expected: PASS (5 passed)

- [ ] **Step 5: Commit**

```bash
git add index/provisions.py tests/index/test_alinea_discriminator.py
git commit -m "Add citation-context guard for alinea parsing (FR-030)"
```

- [ ] **Step 6: Fresh-subagent review** of this task's diff; fix findings; re-review until clean.

---

### Task 2: The discriminator — rewrite `_split_alineas`

**Files:**
- Modify: `index/provisions.py:_split_alineas` (currently ~line 170-190)
- Test: `tests/index/test_alinea_discriminator.py` (extend)

**Interfaces:**
- Consumes: `_is_citation_context` (Task 1), `_ALINEA_MARKER_RE` (unchanged).
- Produces: `_split_alineas(body: str) -> list[tuple[str, str]]` — now returns only real alineas (paragraph_id, text), citations excluded. Same return type as before.

- [ ] **Step 1: Write the failing tests** (exact accepted-alinea sets from the design's §2 inspected cases)

```python
# append to tests/index/test_alinea_discriminator.py
from index.provisions import _split_alineas


def _ids(body: str) -> list[str]:
    return [pid for pid, _ in _split_alineas(body)]


def test_contiguous_alineas_after_words_all_kept():
    # ЗОП чл.196 shape: (5) follows a word, no terminal period — still real
    body = ("Чл. 196. (1) На обжалване. 4. конкурс за проект. (2) Не подлежат. "
            "(3) Решенията по ал. 1. (4) (Доп.) документ. "
            "обявлението за доброволна прозрачност (5) На обжалване")
    assert _ids(body) == ["1", "2", "3", "4", "5"]


def test_interleaved_cardinal_and_ref_citations_dropped():
    # ЗПУПС чл.9 shape: real 1..7 with "четири (4)" / "едно (1)" citations
    body = ("Чл. 9. (1) капитал. четири (4) на сто. едно (1) на сто. "
            "(2) Коефициентът. едно (1) когато. (3) капитал. (4) капитал. "
            "(5) Въз основа. (6) размер. (7) отчети.")
    assert _ids(body) == ["1", "2", "3", "4", "5", "6", "7"]


def test_regulation_ref_between_alineas_dropped():
    # ЗЗВВХВС чл.7 shape: "чл. 8 (3) от Регламент" between real (1),(2)
    body = ("(1) Всяко лице. информацията по чл. 8 (3) от Регламент. "
            "(2) Уведомлението по чл. 8 (3) от Регламент се подава.")
    assert _ids(body) == ["1", "2"]


def test_grade_citation_out_of_sequence_dropped():
    # ЗПУО чл.122: "среден (3)" appears before real (2),(3)
    body = ('Чл. 122. (1) има оценки най-малко "среден (3)" по предмети. '
            "(2) продължава в следващия клас. (3) в началния етап.")
    assert _ids(body) == ["1", "2", "3"]


def test_citation_only_article_yields_no_alineas():
    # ЗАЕ чл.5: "чл. III (1) и (4)" — both citations, no real alinea
    body = "за прилагане на чл. III (1) и (4) от Договора за неразпространение"
    assert _ids(body) == []


def test_letter_suffix_subalinea_kept():
    body = "Чл. 1. (1) първо. (2) второ. (2а) допълнение. (3) трето."
    assert _ids(body) == ["1", "2", "2а", "3"]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/python -m pytest tests/index/test_alinea_discriminator.py -q`
Expected: FAIL — current `_split_alineas` accepts citations (e.g. the ЗАЕ case returns `["1"]`, ЗПУПС returns extra ids).

- [ ] **Step 3: Rewrite `_split_alineas`**

Replace the body of `_split_alineas` with:

```python
def _split_alineas(body: str) -> list[tuple[str, str]]:
    """Split an article body into (paragraph_id, text) pairs for its REAL
    alineas. A "(N)" marker opens an alinea only if it (1) continues the
    contiguous sequence and (2) is not in a citation context — FR-030,
    design §3. Citations that sit inside an alinea's text stay in that
    text (the span runs to the next ACCEPTED marker)."""
    matches = list(_ALINEA_MARKER_RE.finditer(body))
    if not matches:
        return []
    accepted: list[re.Match] = []
    current = 0
    for m in matches:
        n = int(re.match(r"\d+", m.group(1)).group())  # integer part of "4"/"4а"
        # Signal 1 — sequence continuity.
        if current == 0:
            in_seq = (n == 1)
        else:
            in_seq = (n == current or n == current + 1)
        if not in_seq:
            continue
        # Signal 2 — citation-context guard.
        if _is_citation_context(body, m.start()):
            continue
        accepted.append(m)
        current = n
    if not accepted:
        return []
    out: list[tuple[str, str]] = []
    for i, m in enumerate(accepted):
        paragraph_id = m.group(1)
        start = m.end()
        end = accepted[i + 1].start() if i + 1 < len(accepted) else len(body)
        text = body[start:end].strip()
        text = re.sub(r"^[\s\.,]+", "", text)
        out.append((paragraph_id, text))
    return out
```

- [ ] **Step 4: Run the new tests + the existing provisions suite**

Run: `.venv/bin/python -m pytest tests/index/test_alinea_discriminator.py tests/index/test_provisions.py -q`
Expected: PASS. If an existing `test_provisions.py` case fails, inspect it — a legitimately changed case gets its expectation updated with a comment; a real regression means the discriminator is wrong.

- [ ] **Step 5: Run the full suite**

Run: `.venv/bin/python -m pytest -q -m "not perf" 2>&1 | tail -3`
Expected: all pass (current baseline 529 + the new tests).

- [ ] **Step 6: Commit**

```bash
git add index/provisions.py tests/index/test_alinea_discriminator.py
git commit -m "Discriminate real alineas from citations in _split_alineas (FR-030)"
```

- [ ] **Step 7: Fresh-subagent review**; fix; re-review until clean.

---

### Task 3: Full-corpus rebuild validation (the safety gate)

**Files:**
- Create: `scripts/fr030_validate.py` (throwaway allowed, but commit it for reproducibility)
- No production code change — this task produces EVIDENCE.

**Interfaces:** none (validation only).

- [ ] **Step 1: Snapshot the current (pre-fix) alinea rows**

The working tree already has the new parser, but `catalog.db` still holds pre-fix rows until rebuilt. Capture them first:

```bash
.venv/bin/python -c "import sqlite3; c=sqlite3.connect('file:catalog.db?mode=ro',uri=True); \
rows=c.execute('SELECT law_id||\"|\"||article||\"|\"||paragraph FROM provisions WHERE paragraph IS NOT NULL').fetchall(); \
open('/tmp/fr030_before.txt','w').write('\n'.join(sorted(r[0] for r in rows)))"
wc -l /tmp/fr030_before.txt
```

- [ ] **Step 2: Rebuild the catalog with the new parser**

Run: `.venv/bin/python -m index.build --db catalog.db --corpus .`
Expected: completes without error (minutes; 3,602 acts). Note the reported act count.

- [ ] **Step 3: Snapshot post-fix rows and diff**

```bash
.venv/bin/python -c "import sqlite3; c=sqlite3.connect('file:catalog.db?mode=ro',uri=True); \
rows=c.execute('SELECT law_id||\"|\"||article||\"|\"||paragraph FROM provisions WHERE paragraph IS NOT NULL').fetchall(); \
open('/tmp/fr030_after.txt','w').write('\n'.join(sorted(r[0] for r in rows)))"
echo '=== REMOVED (citations dropped) ==='; comm -23 /tmp/fr030_before.txt /tmp/fr030_after.txt | tee /tmp/fr030_removed.txt | wc -l
echo '=== ADDED (should be ~0) ==='; comm -13 /tmp/fr030_before.txt /tmp/fr030_after.txt | tee /tmp/fr030_added.txt | wc -l
echo '=== confirm the 8 documented FP values are gone ==='; grep -E '\|(100|230|400|401|505|506|601|660)$' /tmp/fr030_after.txt | wc -l
```

Expected: REMOVED ≈ 600+ (citations), ADDED ≈ 0, the 8 FP-value grep = 0.

- [ ] **Step 4: Vision-verify — no real alinea was dropped**

Read `/tmp/fr030_removed.txt`. For a sample (all rows whose paragraph is a *small* number 2-9, plus 20 random others), pull the article body and confirm each removed marker is genuinely a citation, not a real alinea:

```bash
# For each suspicious (law_id, article, paragraph), dump the body window:
.venv/bin/python scripts/fr030_dump_removed.py   # adapt the §2 dump script
```

Read the windows directly (Claude vision at orchestration time — per the OCR/vision rule, no external tooling). If ANY removed marker is a real alinea, STOP: the discriminator has a false negative → return to Task 1/2 and tighten the guard (add the pattern to a test first).

- [ ] **Step 5: Oracle + smoke**

Run: `.venv/bin/python -m pytest -q -m "not perf" 2>&1 | tail -3` (full suite green) and a `get_article` smoke on a previously-corrupt act (e.g. `naredba-3-ot-9-yuni-2004-...` чл. 1195) confirming no `paragraph=660` row is returned.

- [ ] **Step 6: Commit the validation script + evidence note**

```bash
git add scripts/fr030_validate.py
git commit -m "Add FR-030 rebuild-diff validation script + evidence"
```

- [ ] **Step 7: Fresh-subagent review** of the validation logic + evidence.

---

### Task 4: Governance close-out

**Files:**
- Modify: `docs/sync/DECISIONS.md` (add D-055)
- Modify: `docs/frs/INDEX.md` (FR-030 → Done)
- Modify: `docs/sync/ACTIVE.md` (banner)

- [ ] **Step 1: DECISIONS D-055** — record the hybrid discriminator, the empirical basis (scan + vision), the two signals, and the rebuild-diff validation result (removed count, zero real alineas dropped). Reference the design + this plan.

- [ ] **Step 2: FR-030 → Done** in `docs/frs/INDEX.md`, noting the fix is general citation discrimination (~600+ markers), not just the 8 rows, and the validation evidence.

- [ ] **Step 3: ACTIVE.md banner** — FR-030 complete; next up FR-026, then Phase 3/4.

- [ ] **Step 4: Commit**

```bash
git add docs/sync/DECISIONS.md docs/frs/INDEX.md docs/sync/ACTIVE.md
git commit -m "Record FR-030 alinea discriminator (D-055); FR-030 Done"
```

---

## Self-review notes (author)

- **Spec coverage:** Signal 1 → Task 2; Signal 2 → Task 1; validation (design §5) → Task 3; governance (design §9) → Task 4. All design sections mapped.
- **Type consistency:** `_is_citation_context(body, marker_start) -> bool` used identically in Task 1 (def) and Task 2 (call). `_split_alineas` return type unchanged.
- **Residual risk carried forward:** a semantic citation that both continues the sequence AND lacks a structural preceding token (e.g. a grade `"(3)"` right after real alinea (2)) can slip through — Task 3's vision pass is the net; if one is found, add a test and extend the guard.
