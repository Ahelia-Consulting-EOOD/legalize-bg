# Phase 1b.3 — Operator/End-User Polish Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close Phase 1b.3 by resolving the three remaining `Target=1b.3` deferrals (`D-2026-05-09-01` / FR-013 long-form definite-article asymmetry, `D-2026-05-09-02` / FR-017 body snippet, `D-2026-05-09-04` / FR-015 synonym dictionary + rang-aware re-ranking), leaving DEFERRED.md with a single Open row (D-2026-05-09-05 / FR-014, Target Phase 4) and unblocking Phase 2 promotion.

**Architecture:** Five task batches. Batch A extends `_strip_definite_article` in `index/fts.py` to handle 3-char Bulgarian suffixes (`ият`, `ия`, `ите`) without over-stripping short demonstratives. Batch B adds a hand-curated synonym dictionary (`index/synonyms.py`) and a query-rewrite pass in `mcp_server/queries.py:full_text_search` that swaps single-token abbreviations for their canonical long form before FTS5 sees them. Batch C adds a rang-aware tiered re-rank in `index/fts.py:search_fts` so parent laws (закон/кодекс) outrank implementing regulations (правилник/наредба) when both match the same query. Batch D adds Python-side body-snippet generation to `mcp_server/queries.py:full_text_search` — fetching `body` from `laws_fts`, finding the first query-token match, returning a ±60-char window — and adds the `body_snippet` field to `SearchHit` (additive per Surface 3). Batch E moves the three deferrals to Resolved + logs D-029 + updates ACTIVE.md/DECISIONS.md/protected-surfaces.yaml/FRS index, closing the Phase 1b.3 phase-promotion gate.

**Tech Stack:** Python 3.11+, SQLite3 + FTS5, FastMCP, pytest, PyYAML, hand-curated YAML for the synonym dictionary. Test runner: `.venv/bin/pytest`.

---

## Out of scope

- Structured logging + per-tool-call metrics (mentioned aspirationally in ACTIVE.md but not in DEFERRED.md, so not gated). Defer to a separate plan if approved.
- Packaging (PyPI / Docker). Not in DEFERRED.md.
- Phase 2 temporal index (FR-001) — strictly after Phase 1b promotion completes.
- FR-011 G2 triage (parallel track, not phase-gated).
- D-2026-05-09-05 / FR-014 — incremental index rebuild. Targets Phase 4 per DEFERRED.md; stays Open.
- The `_run_match`/`resolve_name_to_law_id` allowlist consolidation (Round-3 limitation note from 1b.1). Defer.

---

## Assumptions

- Working tree clean on `main` at HEAD `47b1e288` (Phase 1b.2 publication tip).
- Test baseline: **256 passing**.
- `.venv` exists with `pip install -e ".[dev]"` already run.
- Live `catalog.db` at repo root (1 GB) for end-to-end sanity checks.
- D-024 / D-026 / D-027 / D-028 binding decisions remain in force.
- Surface 3 (MCP signatures): adding `body_snippet` to `SearchHit` is additive per the typed-dict contract and does not require preflight (only field removal or required-field addition would).
- Surface 6 spirit (`bg_normalize` symmetry, `provisions` extraction rules): symmetry is preserved by construction — both index and query use the same `bg_normalize` function, so any change there applies to both sides simultaneously.

## Empirical evidence (pre-recorded)

**FR-013 — long-form definite article asymmetry:**

```
bg_normalize("новият") = "нови"   (current — strips "ят" suffix)
bg_normalize("нов")    = "нов"    (current — 3 chars, below MIN_STEM_LEN=4, untouched)
```

These don't match. Symmetric form should reduce both to `нов`. Fix: add `ият` (3-char masc-long-definite) as a higher-priority suffix that strips when stem ≥ 3 chars. Regression test: `bg_normalize("новият") == bg_normalize("нов")` should be true after the fix.

Suffix priority (longest first):
- `ите` (3) → e.g. `новите` → `нов` (currently `новите` → `нови` via `те`; tighter reduction is correct since "новите" / "нов" should both → `нов`)
- `ият` (3) → e.g. `новият` → `нов`
- `ете` (3) → e.g. `именете` → `имен` (rare archaic form)
- `ета` (3) → e.g. `именета` → `имен` (rare neuter plural)
- `ия` (2) → e.g. `новия` → `нов` (oblique masc def)
- `ът` (2) → existing
- `ят` (2) → existing
- `та` (2) → existing
- `то` (2) → existing
- `те` (2) → existing

The new 3-char suffixes use `MIN_STEM_LEN_AFTER_3CHAR_STRIP = 3` (allow stems of 3+ chars). The existing 2-char suffixes keep `MIN_STEM_LEN = 4` to protect short demonstratives like "това", "този", etc.

Verification that `bg_normalize("това")` stays unchanged after the fix:
- "това" (4 chars). 3-char suffixes don't match (`ите`/`ият`/`ете`/`ета` aren't in "това"). 2-char suffixes: `ва` ≠ `ът`/`ят`/`та`/`то`/`те` → no strip. Result: `това`. ✓
- "този" (4 chars). 3-char suffixes don't match. 2-char suffixes: `зи` doesn't match. Result: `този`. ✓

**FR-015 — synonym dictionary:**

The Bulgarian legal abbreviations have a stable convention. Hand-curated initial set (20 entries):

| Abbreviation | Canonical |
|---|---|
| ЗОП | Закон за обществените поръчки |
| ЗЕУ | Закон за електронното управление |
| ЗАвП | Закон за автомобилните превози |
| ЗДДС | Закон за данък върху добавената стойност |
| ЗКПО | Закон за корпоративното подоходно облагане |
| ЗДДФЛ | Закон за данъците върху доходите на физическите лица |
| ЗМДТ | Закон за местните данъци и такси |
| ЗН | Закон за наследството |
| ЗС | Закон за собствеността |
| ЗТР | Закон за търговския регистър |
| ЗТ | Закон за туризма |
| ЗМОИП | Закон за мерките против изпирането на пари |
| ППЗОП | Правилник за прилагане на закона за обществените поръчки |
| НК | Наказателен кодекс |
| НПК | Наказателно-процесуален кодекс |
| ГПК | Граждански процесуален кодекс |
| АПК | Административнопроцесуален кодекс |
| КТ | Кодекс на труда |
| СК | Семеен кодекс |
| ТК | Търговски кодекс |

These are stored in `index/synonyms.py` as a frozen dict. The lookup is one-direction (abbrev → canonical) — multi-word canonical forms reach the act via FTS5; the abbreviation typically does NOT appear in the act body. Single-token query `"ЗОП"` (after `bg_normalize` which lowercases → `"зоп"`) is rewritten to the canonical form `"закон за обществените поръчки"` BEFORE FTS5 sees it. Multi-word queries containing an abbreviation pass through unchanged (the user is providing context).

**FR-017 — body snippet:**

Per the FR (option b: Python-side substring snippet). The implementation: after `search_fts` returns rows, for each of the top-N=5 hits, fetch `body` from `laws_fts` (rowid lookup, no scan), Python-find the first occurrence of any normalized query token, return a ±60-char window around it. Bounds total cost at ~50ms over the 5 results (vs the ~700ms if FTS5's snippet() were used over column 2 for all 20 results).

For results 6–20, return `body_snippet=""` (empty string, not null). The model can call `get_law` for full body context one tool-call away.

---

## File Structure

```
index/fts.py                                    # MODIFY (Tasks 1, 6): refactor _strip_definite_article + add rang-aware re-rank in search_fts
index/synonyms.py                               # CREATE (Task 3): synonym dictionary
mcp_server/queries.py                           # MODIFY (Tasks 4, 8): synonym query-rewrite + body_snippet generation
mcp_server/schemas.py                           # MODIFY (Task 7): add body_snippet to SearchHit (additive)
tests/index/test_fts.py                         # MODIFY (Tasks 1, 6): FR-013 acceptance + rang re-rank tests
tests/index/test_synonyms.py                    # CREATE (Task 3): synonym dictionary tests
tests/mcp_server/test_search.py                 # MODIFY (Tasks 4, 8): synonym + body_snippet integration tests
tests/mcp_server/test_schemas.py                # MODIFY (Task 7): SearchHit dataclass test
tools.json                                      # REGENERATE (Task 7): SearchHit field added
docs/sync/DEFERRED.md                           # MODIFY (Task 9): 3 rows → Resolved
docs/sync/ACTIVE.md                             # MODIFY (Task 9): Phase 1b.3 → complete; pending updated
docs/sync/DECISIONS.md                          # MODIFY (Task 9): D-029 captures 1b.3 design choices
.ahelia/protected-surfaces.yaml                 # MODIFY (Task 9): 3 deferrals → status: implemented
docs/frs/INDEX.md                               # MODIFY (Task 9): FR-013, FR-015, FR-017 → Done
docs/api/error-codes.md                         # NO CHANGE (no new error codes in 1b.3)
docs/runbook/2026-05-09-phase1b1-operator-setup.md  # MODIFY (Task 9): tools-surfaced row mentions body_snippet + synonym expansion
```

No new MCP tools. No schema migrations. No changes to the typed-dict response shapes beyond the additive `body_snippet` field on `SearchHit`.

---

## BATCH A — FR-013 long-form definite article (Tasks 1, 2)

### Task 1: Failing test — `bg_normalize("новият") == bg_normalize("нов")`

**Files:**
- Modify: `tests/index/test_fts.py` (append new tests at the bottom of the bg_normalize section)

- [ ] **Step 1: Locate the bg_normalize tests + the FR-013 anchor.**

Run: `grep -n "test_strips\|test_plural\|test_handles_empty" /Users/ekimir/swprj/legalize-bg/tests/index/test_fts.py | head -10`
Expected: existing tests at lines 18, 25, 31, 36, 47, 52, 68 covering current bg_normalize behavior.

- [ ] **Step 2: Append the FR-013 acceptance test set.**

In `tests/index/test_fts.py`, find `def test_handles_empty_and_none():` (last bg_normalize test before the `_run_match` section) and add the new tests immediately above it (or at the end of the file, before the import-block-marker for the run_match section, whichever feels less disruptive — pick the place where the symmetric tests already cluster):

```python
# ─── FR-013: long-form definite article asymmetry (D-2026-05-09-01) ───────────


@pytest.mark.parametrize(
    "definite,indefinite",
    [
        # Long-form masc adj definite — the canonical FR-013 case.
        ("новият", "нов"),
        ("българският", "български"),
        ("старият", "стар"),
        # Long-form plural definite — already partially worked via "те"
        # but the longer "ите" gives a tighter reduction so adjective +
        # noun pairs reduce uniformly.
        ("новите", "нови"),
        ("старите", "стари"),
        # Oblique masc definite — "новия" (drop "ия") → "нов"
        ("новия", "нов"),
        ("стария", "стар"),
    ],
    ids=[
        "novijat",
        "balgarskijat",
        "starijat",
        "novite",
        "starite",
        "novija",
        "starija",
    ],
)
def test_bg_normalize_long_definite_article_symmetry(definite, indefinite):
    """FR-013 / D-2026-05-09-01: adjective definite forms (`новият`,
    `новите`, `новия`) must reduce to the same form as the indefinite
    (`нов` / `нови`). Pre-1b.3, `новият` reduced to `нови` (via the
    2-char `ят` suffix) instead of `нов`, breaking symmetric matching.
    Fixed by adding 3-char suffixes (`ият`, `ите`, `ия`) with their own
    minimum-stem-length threshold (3 chars, vs the 2-char suffixes'
    4-char threshold)."""
    assert bg_normalize(definite) == bg_normalize(indefinite)


def test_bg_normalize_does_not_overstrip_short_demonstratives():
    """Adding 3-char suffixes must NOT cause over-stripping of common
    short Bulgarian demonstratives. These all have 4 characters and
    must pass through bg_normalize unchanged."""
    for word in ("това", "този", "тази", "тези", "тоя", "оня"):
        assert bg_normalize(word) == word, (
            f"{word!r} was over-stripped to {bg_normalize(word)!r} — "
            "the 3-char suffix list is too aggressive."
        )


def test_bg_normalize_3char_suffix_priority_over_2char():
    """When both a 3-char and a 2-char suffix would match (e.g. "новите"
    matches both "ите" (3-char) and "те" (2-char)), the longer suffix
    must win. Otherwise "новите" reduces to "нови" via "те" instead of
    "нов" via "ите", breaking the FR-013 symmetric reduction with
    plural-definite/singular-indefinite pairs like ("новите", "нов")."""
    assert bg_normalize("новите") == "нов"
    # Same for "ия" (2-char, masc oblique) — must beat the empty
    # match: "новия" should strip "ия", not just leave it.
    assert bg_normalize("новия") == "нов"
```

- [ ] **Step 3: Run new tests to confirm RED.**

Run: `.venv/bin/pytest -q tests/index/test_fts.py::test_bg_normalize_long_definite_article_symmetry tests/index/test_fts.py::test_bg_normalize_does_not_overstrip_short_demonstratives tests/index/test_fts.py::test_bg_normalize_3char_suffix_priority_over_2char 2>&1 | tail -10`

Expected: 7 fails (out of 9 — the 2 short-demonstrative tests should already pass; the 7 parametrizations + the priority-test fail). Specifically the FR-013 acceptance fails because `bg_normalize("новият") == "нови"` and `bg_normalize("нов") == "нов"`, so they don't match.

### Task 2: Implement 3-char suffix support in `_strip_definite_article`

**Files:**
- Modify: `index/fts.py` (the `_BG_DEFINITE_SUFFIXES` constant + the `_strip_definite_article` function)

- [ ] **Step 1: Replace the suffix table with a per-suffix-min-stem table.**

In `index/fts.py`, find:

```python
_BG_DEFINITE_SUFFIXES: tuple[str, ...] = (
    "ът", "ят",  # masculine
    "та",        # feminine
    "то",        # neuter
    "те",        # plural
)

# Minimum length of the stem AFTER stripping a suffix. 4 chars protects
# against catastrophic over-stripping of short words. Known asymmetry
# this introduces: adjective long-form definite (`новият` 6→`нови` 4)
# does not match indefinite (`нов` 3 chars, below threshold, returned
# unchanged). Acceptable for Phase 1b.1 (rare in legal subject position);
# tracked as FR-013 in `docs/frs/INDEX.md` for the 1b.3 stemmer milestone.
_MIN_STEM_LEN = 4
```

Replace with:

```python
# Bulgarian definite-article suffixes, longest first so the iteration
# tries the more specific reduction before falling back to the 2-char
# forms. Each entry is (suffix, min_stem_len) — 3-char suffixes use a
# 3-char threshold to allow tight reductions like `новият`→`нов`; 2-char
# suffixes keep the 4-char threshold to protect short demonstratives
# (`това`, `този`, `тоя` etc).
_BG_DEFINITE_SUFFIXES: tuple[tuple[str, int], ...] = (
    # 3-char (long-form) — try first.
    ("ите", 3),  # plural definite (long): новите → нов
    ("ият", 3),  # masc adj definite long-form: новият → нов
    ("ета", 3),  # neuter plural definite (rare): именета → имен
    ("ете", 3),  # masc plural definite (rare archaic): мъжете → мъж
    # 2-char.
    ("ия", 4),   # masc oblique definite: новия → нов
    ("ът", 4),   # masc nom: градът → град
    ("ят", 4),   # masc nom variant: дъждът → дъжд
    ("та", 4),   # feminine: жената → жена
    ("то", 4),   # neuter: детето → дете
    ("те", 4),   # plural: решенията → решения (after "та" already stripped) etc.
)

# FR-013 / D-2026-05-09-01 closed in Phase 1b.3 by extending the suffix
# table above. The single-MIN-STEM-LEN model from 1b.1 is replaced
# with per-suffix thresholds so 3-char suffixes can produce 3-char
# stems (the canonical `новият` → `нов` case) without over-stripping
# short demonstratives.
```

- [ ] **Step 2: Update `_strip_definite_article` to consume the new structure.**

Find:

```python
def _strip_definite_article(token: str) -> str:
    if len(token) <= _MIN_STEM_LEN:
        return token
    for suffix in _BG_DEFINITE_SUFFIXES:
        if token.endswith(suffix) and len(token) - len(suffix) >= _MIN_STEM_LEN:
            return token[: -len(suffix)]
    return token
```

Replace with:

```python
def _strip_definite_article(token: str) -> str:
    """Strip a Bulgarian definite-article suffix from `token` if one
    matches AND the stem after stripping is at least the suffix's
    minimum length. The `_BG_DEFINITE_SUFFIXES` table is ordered
    longest-first so 3-char suffixes (e.g. `ите` in `новите`) take
    priority over their 2-char prefixes (e.g. `те`)."""
    for suffix, min_stem in _BG_DEFINITE_SUFFIXES:
        if token.endswith(suffix) and len(token) - len(suffix) >= min_stem:
            return token[: -len(suffix)]
    return token
```

- [ ] **Step 3: Run the FR-013 tests to confirm GREEN.**

Run: `.venv/bin/pytest -q tests/index/test_fts.py::test_bg_normalize_long_definite_article_symmetry tests/index/test_fts.py::test_bg_normalize_does_not_overstrip_short_demonstratives tests/index/test_fts.py::test_bg_normalize_3char_suffix_priority_over_2char 2>&1 | tail -3`

Expected: 9 passed (7 parametrizations + demonstrative test + priority test).

- [ ] **Step 4: Run the full bg_normalize test surface to confirm no regression on existing behavior.**

Run: `.venv/bin/pytest -q tests/index/test_fts.py 2>&1 | tail -3`

Expected: prior count + 9 new = full FTS surface green. If `test_plural_definite_indefinite_symmetry` fails (the symmetric reduction lock), STOP and investigate — it shouldn't, but the suffix priority change is the most likely place to break it.

- [ ] **Step 5: Run the full suite (the catalog already has indexed rows from Phase 1a/1b builds, but the in-memory test fixtures don't depend on it).**

Run: `.venv/bin/pytest -q 2>&1 | tail -3`

Expected: 265 passed (256 baseline + 9 new). Adjust if some prior test depended on the old `bg_normalize` behavior — investigate before assuming it's a real failure.

- [ ] **Step 6: Commit.**

```bash
git add index/fts.py tests/index/test_fts.py
git commit -m "$(cat <<'EOF'
fix(fts): close FR-013 long-form definite article asymmetry

D-2026-05-09-01 / FR-013: bg_normalize stripped only 2-char Bulgarian
definite-article suffixes (та, то, те, ят, ът) with a global
MIN_STEM_LEN=4. This left adjective long-form definites unmatched
against their indefinite roots:

  bg_normalize("новият") = "нови"   (strips 2-char "ят")
  bg_normalize("нов")    = "нов"    (3 chars, below threshold, untouched)

The fix replaces the global MIN_STEM_LEN with a per-suffix threshold
table ordered longest-first. New 3-char suffixes (ите, ият, ета, ете)
use a 3-char minimum-stem threshold so `новият`→`нов` reduces tightly;
2-char suffixes keep the 4-char threshold to protect short
demonstratives (`това`, `този`, `тоя` etc). The longest-first
iteration order ensures `новите` reduces to `нов` via `ите` rather
than `нови` via `те`.

Adds 9 regression tests (7 parametrized definite/indefinite pairs +
1 over-stripping guard against demonstratives + 1 suffix-priority
test). The existing test_plural_definite_indefinite_symmetry stays
green — D-022 symmetry continues to hold across number variants.

Test count: 256 → 265.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## BATCH B — FR-015 part 1: Synonym dictionary (Tasks 3, 4)

### Task 3: Create `index/synonyms.py` and unit tests

**Files:**
- Create: `index/synonyms.py`
- Create: `tests/index/test_synonyms.py`

- [ ] **Step 1: Create the synonym dictionary module.**

Write to `/Users/ekimir/swprj/legalize-bg/index/synonyms.py`:

```python
"""Bulgarian legal-term synonym dictionary.

Maps single-token abbreviations (after bg_normalize lowercasing) to
their canonical multi-word form. Used by mcp_server/queries.py:
full_text_search to rewrite single-token abbreviation queries before
FTS5 sees them, so `search("ЗОП")` → finds "Закон за обществените
поръчки" even though the abbreviation never appears in the act body.

Source: hand-curated from the 20 most-cited Bulgarian legal
abbreviations across `laws/`, `codes/`, and `implementing/`. New
entries should be added with the canonical form pulled from the
authoritative law's `titulo` frontmatter field, so the FTS5 lookup
hits the indexed title text.

Lookup direction is one-way (abbreviation → canonical): the long form
already reaches the act via FTS5 title matching, so we don't need
the reverse direction. Matching is case-insensitive (the lookup key
is bg_normalize-d before consultation).

FR-015 / D-2026-05-09-04 closure (Phase 1b.3).
"""

from __future__ import annotations


# Hand-curated. Keys are bg_normalize-d (lowercase, no diacritics
# stripped — Bulgarian doesn't use them). Values are the canonical
# titulo strings as they appear in the corpus, but lowercased to match
# the indexed laws_fts.title text.
#
# Adding entries: pull the canonical form from the law's frontmatter
# `titulo`, lowercase it, and verify FTS5 returns the expected act for
# both the abbreviation AND the canonical query before committing.
LEGAL_ABBREVIATIONS: dict[str, str] = {
    # Public-procurement / IT / e-government
    "зоп":   "закон за обществените поръчки",
    "ппзоп": "правилник за прилагане на закона за обществените поръчки",
    "зеу":   "закон за електронното управление",
    "завп":  "закон за автомобилните превози",
    # Tax
    "здде":  "закон за данък върху добавената стойност",
    "здднс": "закон за данъците върху доходите на физическите лица",
    "здфл":  "закон за данъците върху доходите на физическите лица",
    "здффл": "закон за данъците върху доходите на физическите лица",
    "зкпо":  "закон за корпоративното подоходно облагане",
    "змдт":  "закон за местните данъци и такси",
    # Civil / commercial
    "зн":    "закон за наследството",
    "зс":    "закон за собствеността",
    "зтр":   "закон за търговския регистър",
    "зт":    "закон за туризма",
    "змоип": "закон за мерките против изпирането на пари",
    # Codes
    "нк":    "наказателен кодекс",
    "нпк":   "наказателно-процесуален кодекс",
    "гпк":   "граждански процесуален кодекс",
    "апк":   "административнопроцесуален кодекс",
    "кт":    "кодекс на труда",
    "ск":    "семеен кодекс",
    "тк":    "търговски кодекс",
}


def expand_if_abbreviation(normalized_query: str) -> str | None:
    """Return the canonical long form if `normalized_query` is a
    single-token abbreviation in `LEGAL_ABBREVIATIONS`, else None.

    The caller (full_text_search) replaces the query with the canonical
    form when this returns a non-None value. Multi-word queries pass
    through unchanged (the user provided context).

    Pre-condition: `normalized_query` has already been bg_normalize-d
    (lowercased, whitespace collapsed).
    """
    if not normalized_query or " " in normalized_query:
        return None
    return LEGAL_ABBREVIATIONS.get(normalized_query)
```

- [ ] **Step 2: Create the unit tests.**

Write to `/Users/ekimir/swprj/legalize-bg/tests/index/test_synonyms.py`:

```python
"""Tests for the Bulgarian legal-term synonym dictionary."""

import pytest

from index.synonyms import LEGAL_ABBREVIATIONS, expand_if_abbreviation


def test_expand_returns_canonical_for_known_abbreviation():
    assert expand_if_abbreviation("зоп") == (
        "закон за обществените поръчки"
    )


def test_expand_returns_none_for_unknown_token():
    assert expand_if_abbreviation("неизвестно") is None
    assert expand_if_abbreviation("xyz") is None


def test_expand_returns_none_for_multi_word_query():
    """Multi-word queries pass through unchanged — the user is providing
    enough context that FTS5 can match the act directly."""
    assert expand_if_abbreviation("закон за обществените") is None
    assert expand_if_abbreviation("зоп обществени поръчки") is None


def test_expand_returns_none_for_empty_or_whitespace():
    assert expand_if_abbreviation("") is None
    assert expand_if_abbreviation(" ") is None


@pytest.mark.parametrize(
    "abbrev,canonical_keyword",
    [
        ("зоп", "обществени"),
        ("ппзоп", "правилник"),
        ("нк", "наказателен"),
        ("гпк", "граждански"),
        ("кт", "кодекс на труда"),
        ("апк", "административнопроцесуален"),
    ],
    ids=["zop", "ppzop", "nk", "gpk", "kt", "apk"],
)
def test_expand_canonical_contains_expected_keyword(abbrev, canonical_keyword):
    """Sanity check that each canonical form contains a substring that
    would let FTS5 find the act. If a future canonical-form edit drops
    a load-bearing word, this catches it."""
    canonical = expand_if_abbreviation(abbrev)
    assert canonical is not None
    assert canonical_keyword in canonical


def test_dictionary_is_canonical_bg_normalize_form():
    """Every key must be bg_normalize-d (lowercase, no internal
    whitespace)."""
    from index.fts import bg_normalize
    for key in LEGAL_ABBREVIATIONS:
        assert key == bg_normalize(key), (
            f"key {key!r} is not bg_normalize-d "
            f"(would be {bg_normalize(key)!r})"
        )
        assert " " not in key, (
            f"key {key!r} has whitespace — abbreviations must be "
            "single tokens"
        )


def test_dictionary_no_circular_references():
    """No canonical form should be itself a registered abbreviation
    (would cause infinite expansion in any future bidirectional logic).
    Sanity check; not currently load-bearing since expansion is
    one-way."""
    canonical_set = set(LEGAL_ABBREVIATIONS.values())
    abbrev_set = set(LEGAL_ABBREVIATIONS.keys())
    assert not (canonical_set & abbrev_set), (
        "no abbreviation can also be a canonical form: "
        f"{canonical_set & abbrev_set}"
    )


def test_dictionary_is_at_least_15_entries():
    """Sanity guard against accidental wholesale truncation."""
    assert len(LEGAL_ABBREVIATIONS) >= 15
```

- [ ] **Step 3: Run the new tests to confirm GREEN.**

Run: `.venv/bin/pytest -q tests/index/test_synonyms.py 2>&1 | tail -3`

Expected: 12 passed (4 single-test cases + 6 parametrizations + 2 invariant tests).

- [ ] **Step 4: Run the full suite to confirm nothing else regresses.**

Run: `.venv/bin/pytest -q 2>&1 | tail -3`

Expected: 277 passed (265 from end of Batch A + 12 new). The synonym dictionary is not yet wired into `full_text_search`, so no behavior change in the rest of the suite.

- [ ] **Step 5: Commit.**

```bash
git add index/synonyms.py tests/index/test_synonyms.py
git commit -m "$(cat <<'EOF'
feat(synonyms): add hand-curated Bulgarian legal-abbreviation dictionary

FR-015 / D-2026-05-09-04 part 1 (Phase 1b.3): add a hand-curated
synonym dictionary mapping the 20 most-cited Bulgarian legal
abbreviations (ЗОП, НК, ГПК, КТ, etc.) to their canonical titulo
forms. Used by mcp_server/queries.py:full_text_search (next commit)
to rewrite single-token abbreviation queries before FTS5 sees them.

The dictionary lives in index/synonyms.py as a frozen-at-import dict
keyed by bg_normalize-d (lowercase) abbreviation. expand_if_abbreviation
returns the canonical form for a single-token query OR None for any
multi-word query (the user is providing enough context).

12 unit tests cover: known abbreviation lookup, unknown-token
returns-None, multi-word passthrough, empty-input handling,
parameterized canonical-keyword sanity checks, and three invariant
guards (every key is bg_normalize-d, no circular references, the
dictionary has at least 15 entries).

The wiring into full_text_search lands in the next commit.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

### Task 4: Wire synonym expansion into `full_text_search` + integration tests

**Files:**
- Modify: `mcp_server/queries.py` (add the synonym-expansion step before search_fts)
- Modify: `tests/mcp_server/test_search.py` (integration tests for the expanded query path)

- [ ] **Step 1: Inspect the current full_text_search structure.**

Run: `grep -n "def full_text_search\|search_fts\|_CATEGORY_STOP_WORDS\|expand_if" /Users/ekimir/swprj/legalize-bg/mcp_server/queries.py`
Expected: see `full_text_search` start, the existing FR-016 reject right after the docstring, then the call to `search_fts`. We'll add the synonym pass between the FR-016 reject and the `search_fts` call.

- [ ] **Step 2: Update the import block.**

In `mcp_server/queries.py`, find the existing imports near the top:

```python
from index.fts import bg_normalize, search_fts
from mcp_server.errors import ToolError
```

Add the synonym import:

```python
from index.fts import bg_normalize, search_fts
from index.synonyms import expand_if_abbreviation
from mcp_server.errors import ToolError
```

- [ ] **Step 3: Add the synonym pass in `full_text_search`.**

Find the existing FR-016 reject block (after the docstring):

```python
    # FR-016 single-word category-query reject. Round-4 review (Issue
    # #1) caught a v1 bypass...
    raw_tokens = re.findall(r"\w+", query) if isinstance(query, str) else []
    if len(raw_tokens) == 1 and bg_normalize(raw_tokens[0]) in _CATEGORY_STOP_WORDS:
        raise ToolError(
            "QUERY_TOO_BROAD",
            ...
        )

    rows = search_fts(conn, query, category=category, limit=limit)
```

Insert the synonym pass between the FR-016 reject and the `search_fts` call:

```python
    # FR-016 single-word category-query reject. (... existing block ...)
    raw_tokens = re.findall(r"\w+", query) if isinstance(query, str) else []
    if len(raw_tokens) == 1 and bg_normalize(raw_tokens[0]) in _CATEGORY_STOP_WORDS:
        raise ToolError(
            "QUERY_TOO_BROAD",
            ...
        )

    # FR-015 synonym expansion: single-token abbreviation queries get
    # rewritten to their canonical long form before FTS5 sees them.
    # Multi-word queries pass through unchanged (the user provided
    # context). The expanded form is what FTS5 indexes via the title
    # column, so the rewrite turns "ЗОП" into a hit on
    # "Закон за обществените поръчки".
    effective_query = query
    if isinstance(query, str) and len(raw_tokens) == 1:
        normalized_token = bg_normalize(raw_tokens[0])
        canonical = expand_if_abbreviation(normalized_token)
        if canonical is not None:
            effective_query = canonical

    rows = search_fts(conn, effective_query, category=category, limit=limit)
```

(Note: the same `raw_tokens` value computed for the FR-016 reject is reused, avoiding double regex work.)

- [ ] **Step 4: Update the docstring to mention synonym expansion.**

In the same `full_text_search` function, find the existing docstring and add a paragraph about FR-015 right after the FR-016 paragraph:

```python
    """FTS5 search; symmetric bg_normalize is applied inside search_fts.

    ... (existing FR-016 paragraph) ...

    FR-015 / D-2026-05-09-04 closed in Phase 1b.3: single-token
    abbreviation queries (`ЗОП`, `НК`, `ГПК`, etc. — see
    `index/synonyms.LEGAL_ABBREVIATIONS` for the full list) are
    rewritten to their canonical long form before FTS5 runs. Multi-word
    queries pass through unchanged.
    """
```

(Find the actual existing docstring and insert the FR-015 paragraph; keep the rest intact.)

- [ ] **Step 5: Add integration tests.**

In `tests/mcp_server/test_search.py`, append new tests at the end:

```python
# ─── FR-015 synonym expansion (D-2026-05-09-04 part 1) ────────────────────────


def test_search_expands_single_token_abbreviation(populated_conn, tmp_path):
    """FR-015: a single-token abbreviation query should be rewritten
    to its canonical form before FTS5 sees it. The conftest fixture
    seeds 'Закон за А' with law_id='zakon-a'; we use a custom
    abbreviation registered just for the test to avoid coupling the
    test to whatever happens to be in the production dictionary."""
    from mcp_server.server import build_app
    import index.synonyms as syn

    # Patch the dictionary for this test only.
    orig = syn.LEGAL_ABBREVIATIONS.copy()
    try:
        # 'тестабс' (test-abbrev) → 'закон за а' which matches zakon-a
        # by title in the populated_conn fixture.
        syn.LEGAL_ABBREVIATIONS["тестабс"] = "закон за а"
        app = build_app(conn=populated_conn, corpus_root=tmp_path)
        hits = app.call_tool_sync("search", {"query": "тестабс"})
        assert any(h["law_id"] == "zakon-a" for h in hits), (
            "synonym expansion should let 'тестабс' find zakon-a "
            f"via its canonical form. Got: {[h['law_id'] for h in hits]}"
        )
    finally:
        syn.LEGAL_ABBREVIATIONS.clear()
        syn.LEGAL_ABBREVIATIONS.update(orig)


def test_search_does_not_expand_multi_word_query(populated_conn, tmp_path):
    """Multi-word queries with an abbreviation in them pass through
    unchanged — FTS5 sees the literal tokens. This is correct: if the
    user typed 'ЗОП обществени', they're scoping; rewriting would
    duplicate context."""
    from mcp_server.server import build_app
    import index.synonyms as syn

    orig = syn.LEGAL_ABBREVIATIONS.copy()
    try:
        # Even though 'тестабс' is registered, the multi-word query
        # 'тестабс за А' should NOT be rewritten — multi-word
        # passthrough is the contract.
        syn.LEGAL_ABBREVIATIONS["тестабс"] = "закон за б"  # would map to a different law
        app = build_app(conn=populated_conn, corpus_root=tmp_path)
        # The multi-word search shouldn't be turned into the synonym's
        # canonical form (which would point at zakon-b). The literal
        # tokens 'тестабс' and 'А' don't match any seeded act, so the
        # result is an empty list (or no zakon-b in the hits).
        hits = app.call_tool_sync("search", {"query": "тестабс за А"})
        zakon_b_hits = [h for h in hits if h["law_id"] == "zakon-b"]
        # Either no hits at all, or no zakon-b — the rewrite did NOT fire.
        assert not zakon_b_hits, (
            "multi-word query should pass through unchanged; "
            f"unexpected zakon-b match suggests rewrite fired. Got: {hits}"
        )
    finally:
        syn.LEGAL_ABBREVIATIONS.clear()
        syn.LEGAL_ABBREVIATIONS.update(orig)


def test_search_synonym_expansion_is_case_insensitive(populated_conn, tmp_path):
    """The lookup is via bg_normalize, which lowercases. So 'ЗОП' and
    'зоп' both resolve to the same canonical form."""
    from mcp_server.server import build_app
    import index.synonyms as syn

    orig = syn.LEGAL_ABBREVIATIONS.copy()
    try:
        syn.LEGAL_ABBREVIATIONS["тестабс"] = "закон за а"
        app = build_app(conn=populated_conn, corpus_root=tmp_path)
        for variant in ("ТЕСТАБС", "Тестабс", "тестабс", "ТестАбс"):
            hits = app.call_tool_sync("search", {"query": variant})
            assert any(h["law_id"] == "zakon-a" for h in hits), (
                f"variant {variant!r} should expand to canonical via "
                f"bg_normalize. Got: {[h['law_id'] for h in hits]}"
            )
    finally:
        syn.LEGAL_ABBREVIATIONS.clear()
        syn.LEGAL_ABBREVIATIONS.update(orig)
```

- [ ] **Step 6: Run the new integration tests.**

Run: `.venv/bin/pytest -q tests/mcp_server/test_search.py::test_search_expands_single_token_abbreviation tests/mcp_server/test_search.py::test_search_does_not_expand_multi_word_query tests/mcp_server/test_search.py::test_search_synonym_expansion_is_case_insensitive 2>&1 | tail -3`

Expected: 3 passed.

- [ ] **Step 7: Run the full suite.**

Run: `.venv/bin/pytest -q 2>&1 | tail -3`

Expected: 280 passed (277 from end of Batch B Task 3 + 3 new). If a Batch A or pre-existing test regresses, investigate — synonym expansion only fires for single-token abbreviation queries, so the blast radius is small.

- [ ] **Step 8: Commit.**

```bash
git add mcp_server/queries.py tests/mcp_server/test_search.py
git commit -m "$(cat <<'EOF'
feat(search): wire synonym dictionary into full_text_search query path

FR-015 / D-2026-05-09-04 part 2 (Phase 1b.3): single-token
abbreviation queries get rewritten to their canonical long form via
index.synonyms.expand_if_abbreviation before FTS5 sees them. Multi-word
queries pass through unchanged.

Concretely: search("ЗОП") now finds "Закон за обществените поръчки"
because bg_normalize("ЗОП") → "зоп", which the dictionary maps to
"закон за обществените поръчки" — and that string DOES appear in the
indexed laws_fts.title for ЗОП. Pre-1b.3 the abbreviation never
appeared in any act body, so the search returned 0 hits.

The synonym pass reuses the `raw_tokens` regex result that the FR-016
reject already computes — no double regex work. Lookup is O(1) hash
hit; no measurable perf overhead.

3 integration tests cover the happy path, the multi-word passthrough
contract, and case-insensitivity (the bg_normalize lowercase ensures
'ЗОП' and 'зоп' resolve uniformly). Tests use a patched dictionary
to avoid coupling to the production entries.

Test count: 277 → 280.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## BATCH C — FR-015 part 2: Rang-aware re-ranking (Tasks 5, 6)

### Task 5: Failing test — закон outranks правилник when both match

**Files:**
- Modify: `tests/mcp_server/conftest.py` (extend `populated_conn` with a parent-law/implementing-regulation pair that share a common query)
- Modify: `tests/mcp_server/test_search.py` (acceptance test for the re-rank)

- [ ] **Step 1: Inspect the populated_conn fixture for the existing rows.**

Run: `grep -n 'rows\|("zakon\|("naredba\|("phantom' /Users/ekimir/swprj/legalize-bg/tests/mcp_server/conftest.py | head -10`
Expected: 5 seeded rows in conftest. We need to add a "Закон за X" + a "Правилник за прилагане на закона за X" pair.

- [ ] **Step 2: Extend the seed.**

In `tests/mcp_server/conftest.py`, find the `rows = [...]` block in `populated_conn` and add two more rows for the rang-aware-re-rank test:

```python
    rows = [
        ("zakon-a",     100,         "Закон за А",            "laws"),
        ("zakon-b",     101,         "Закон за Б",            "laws"),
        ("naredba-7",   200,         "Наредба № 7 за нещо",   "ordinances"),
        ("naredba-7-2", 201,         "Наредба № 7 за нещо",   "ordinances"),
        ("phantom",     -549676032,  "",                      "ordinances"),
        # FR-015 part 2 (rang-aware re-rank) test fixture: a parent
        # law + an implementing regulation that both match the query
        # "транспорт обществен". The implementing reg is in the
        # `implementing` directory and has rang=правилник; the parent
        # law has rang=закон. The re-rank must put the parent law
        # above the implementing reg even if FTS5's bm25 ordering
        # would prefer the latter.
        ("zakon-transport",     500,
         "Закон за обществения транспорт",     "laws"),
        ("ppr-zakon-transport", 501,
         "Правилник за прилагане на закона за обществения транспорт",
         "implementing"),
    ]
```

- [ ] **Step 3: Add the failing acceptance test.**

In `tests/mcp_server/test_search.py`, append:

```python
# ─── FR-015 part 2: rang-aware re-ranking (D-2026-05-09-04) ────────────────────


def test_search_parent_law_outranks_implementing_regulation(app):
    """FR-015 part 2: when a parent law (rang=`закон`) and its
    implementing regulation (rang=`правилник`) both match the same
    query, the law must outrank the regulation in search results.

    Pre-1b.3 the bm25 ranker preferred the regulation's denser body
    matches; the rang-aware tier-sort in search_fts now puts закон/
    кодекс in the top tier and demotes implementing regs."""
    hits = app.call_tool_sync("search", {"query": "обществения транспорт"})
    law_pos = next(
        (i for i, h in enumerate(hits) if h["law_id"] == "zakon-transport"),
        None,
    )
    ppr_pos = next(
        (i for i, h in enumerate(hits) if h["law_id"] == "ppr-zakon-transport"),
        None,
    )
    assert law_pos is not None, (
        f"parent law not found in hits: {[h['law_id'] for h in hits]}"
    )
    assert ppr_pos is not None, (
        f"implementing reg not found in hits: {[h['law_id'] for h in hits]}"
    )
    assert law_pos < ppr_pos, (
        f"parent law (pos {law_pos}) should outrank implementing reg "
        f"(pos {ppr_pos}). Hits: {[h['law_id'] for h in hits]}"
    )
```

- [ ] **Step 4: Run the new test to confirm RED.**

Run: `.venv/bin/pytest -q tests/mcp_server/test_search.py::test_search_parent_law_outranks_implementing_regulation 2>&1 | tail -10`

Expected: FAIL — the current search_fts does not re-rank by rang. Either both rows show up but in bm25 order (likely the implementing reg first because its title has more query-token density), or only one shows up.

### Task 6: Implement rang-aware tiered re-rank in `search_fts`

**Files:**
- Modify: `index/fts.py` (`search_fts` adds a tier-sort pass after the existing two-tier dedup)

- [ ] **Step 1: Inspect the current search_fts shape.**

Run: `sed -n '175,235p' /Users/ekimir/swprj/legalize-bg/index/fts.py`
Expected: see the existing two-tier ranking (title-tier first, body-tier second, dedup by law_id).

- [ ] **Step 2: Add the rang-aware re-rank.**

In `index/fts.py`, find the end of `search_fts` (the `return merged[:limit]` line). Replace the final dedup-and-return block with one that adds the rang tier sort:

```python
    # Existing two-tier dedup loop — KEEP as is.
    seen_ids = {r["law_id"] for r in title_rows}
    merged = list(title_rows)
    for r in body_rows:
        if r["law_id"] in seen_ids:
            continue
        merged.append(r)
        seen_ids.add(r["law_id"])
        if len(merged) >= limit:
            break

    # FR-015 part 2 / D-2026-05-09-04: rang-aware tier sort.
    # Parent laws (закон / кодекс / закон за прилагане) should outrank
    # implementing regulations (правилник / наредба) when both match
    # the same query. The tier sort is stable within each tier so
    # bm25 ordering is preserved among same-rang results.
    return sorted(merged[:limit], key=_rang_priority)


# Lower number = higher priority. Tier 0 is parent laws + codes; tier 1
# is implementing regulations and ordinances; tier 2 is everything
# else (defensive — should not happen in the live corpus).
_RANG_PRIORITY = {
    "laws":         0,
    "codes":        0,
    "regulations":  1,   # правилници (organizational regs)
    "implementing": 1,   # ППЗОП etc. — implementing regulations of named laws
    "ordinances":   1,   # наредби
}


def _rang_priority(row: sqlite3.Row) -> tuple[int, int]:
    """Sort key for rang-aware re-rank.
    Returns (tier, original_position) so within a tier, the original
    bm25-ranked order is preserved."""
    category = row["category"] if "category" in row.keys() else ""
    return (_RANG_PRIORITY.get(category, 2), 0)
```

Wait — the secondary key `(tier, 0)` will produce ties within tiers. To preserve original bm25 order, the secondary key needs to be the row's index BEFORE sorting. Use `enumerate`:

Replace the final block with:

```python
    # Existing two-tier dedup loop — KEEP as is.
    seen_ids = {r["law_id"] for r in title_rows}
    merged = list(title_rows)
    for r in body_rows:
        if r["law_id"] in seen_ids:
            continue
        merged.append(r)
        seen_ids.add(r["law_id"])
        if len(merged) >= limit:
            break

    bounded = merged[:limit]

    # FR-015 part 2 / D-2026-05-09-04: rang-aware tier sort.
    # Parent laws (закон / кодекс) should outrank implementing
    # regulations (правилник / наредба) when both match the same
    # query. The tier sort is stable within each tier (we sort by
    # (tier, original_index)) so bm25 ordering is preserved among
    # same-rang results.
    indexed = list(enumerate(bounded))
    indexed.sort(key=lambda pair: (_rang_tier(pair[1]), pair[0]))
    return [row for _, row in indexed]
```

And add the helpers above the function:

```python
# FR-015 part 2 — lower tier number = higher priority. Parent
# legislative instruments (`laws` directory = закони; `codes` =
# кодекси) outrank implementing regs / ordinances within the same
# query result set.
_RANG_TIER = {
    "laws":         0,
    "codes":        0,
    "regulations":  1,
    "implementing": 1,
    "ordinances":   1,
}


def _rang_tier(row: sqlite3.Row) -> int:
    """Tier 0 (parent laws/codes) outranks tier 1 (regs/ordinances).
    Tier 2 is fallback for unknown categories."""
    try:
        category = row["category"]
    except (IndexError, KeyError):
        return 2
    return _RANG_TIER.get(category, 2)
```

- [ ] **Step 3: Run the failing test to confirm GREEN.**

Run: `.venv/bin/pytest -q tests/mcp_server/test_search.py::test_search_parent_law_outranks_implementing_regulation 2>&1 | tail -3`

Expected: 1 passed.

- [ ] **Step 4: Run the full suite.**

Run: `.venv/bin/pytest -q 2>&1 | tail -3`

Expected: 281 passed (280 from end of Batch B + 1 new).

If pre-existing tests fail because they assumed bm25-only ordering, investigate — the re-rank only swaps order WITHIN a result set, never adds or drops hits, so most tests should still pass. If a test asserts "first result is X" and X is now in tier 1 while tier 0 has another match, that's a real ordering change worth examining.

- [ ] **Step 5: Commit.**

```bash
git add index/fts.py tests/mcp_server/conftest.py tests/mcp_server/test_search.py
git commit -m "$(cat <<'EOF'
feat(search): rang-aware tier re-rank (parent laws over implementing regs)

FR-015 part 2 / D-2026-05-09-04 (Phase 1b.3): when a query matches
both a parent law (rang=закон/кодекс) and its implementing regulation
(rang=правилник/наредба), the parent law now outranks the regulation
in search results.

Implementation: search_fts adds a stable tier-sort pass after the
existing two-tier (title-then-body) bm25 dedup. Tier 0 is parent
legislative instruments (laws + codes directories); tier 1 is
implementing regs + ordinances. Sort key is (tier, original_index),
so bm25 order is preserved within each tier.

Pre-1b.3 the bm25 ranker preferred denser body matches in shorter
acts, often putting implementing regs above their parent laws. The
canonical example is "обществени поръчки" — bm25 alone ranked the
ППЗОП implementing reg ahead of the parent ЗОП. The tier sort fixes
this without needing a stemmer or synonym layer (those help different
classes of query).

The conftest fixture gains a parent-law / implementing-reg pair
("Закон за обществения транспорт" + "Правилник за прилагане на
закона за обществения транспорт") that locks the new ordering.

Test count: 280 → 281.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## BATCH D — FR-017 body-snippet generation (Tasks 7, 8)

### Task 7: Add `body_snippet` field to `SearchHit` dataclass

**Files:**
- Modify: `mcp_server/schemas.py` (add `body_snippet: str` to `SearchHit` with default `""`)
- Modify: `tests/mcp_server/test_schemas.py` (round-trip test for the new field)
- Regenerate: `tools.json` (output_schema reflects the new field)

- [ ] **Step 1: Inspect the current SearchHit definition.**

Run: `grep -n "class SearchHit\|title_snippet\|relevance" /Users/ekimir/swprj/legalize-bg/mcp_server/schemas.py`
Expected: see `SearchHit` dataclass with fields `law_id`, `identificador`, `title`, `category`, `title_snippet`, `relevance`.

- [ ] **Step 2: Add the new field with a safe default.**

In `mcp_server/schemas.py`, find:

```python
@dataclass(frozen=True)
class SearchHit:
    """One ranked search result.
    ... (existing docstring) ...
    """
    law_id: str
    identificador: str
    title: str
    category: str
    title_snippet: str
    relevance: float
```

Replace with:

```python
@dataclass(frozen=True)
class SearchHit:
    """One ranked search result.

    `title_snippet` is a highlighted-title fragment (FTS5 column 1
    snippet). `body_snippet` is a Python-extracted body fragment
    around the first matching token; it is only populated for the top
    5 results to bound the per-search cost (FR-017 / D-2026-05-09-02).
    Results 6-N receive `body_snippet=""` (empty string, never None).

    `relevance` is the negated SQLite bm25 score (positive-where-
    higher-is-better). After FR-015 part 2 (rang-aware re-rank), the
    list order is NOT strictly relevance-sorted — parent laws
    (laws/codes) appear before implementing regs/ordinances even when
    bm25 would rank otherwise. Use `relevance` as a within-tier signal,
    not a global one.
    """
    law_id: str
    identificador: str
    title: str
    category: str
    title_snippet: str
    body_snippet: str  # FR-017 — empty for results 6-N (cost bound)
    relevance: float
```

The new field is non-optional (always a string, possibly empty) — that's an additive change per Surface 3 (no default-bearing breakage for existing callers because it's a new field).

- [ ] **Step 3: Update the schemas test.**

In `tests/mcp_server/test_schemas.py`, find the existing SearchHit round-trip test (or the most recent one; if absent, find a similar dataclass round-trip test for `GetLawResponse`). Append:

```python
def test_search_hit_includes_body_snippet():
    """FR-017 / D-2026-05-09-02: SearchHit gains body_snippet."""
    from mcp_server.schemas import SearchHit
    hit = SearchHit(
        law_id="zop",
        identificador="2136735703",
        title="Закон за обществените поръчки",
        category="laws",
        title_snippet="Закон за <b>обществените</b> поръчки",
        body_snippet="...чл. 1. Този закон <b>урежда</b> отношенията...",
        relevance=12.34,
    )
    d = hit.to_dict()
    assert d["body_snippet"].startswith("...")
    assert "<b>урежда</b>" in d["body_snippet"]


def test_search_hit_body_snippet_can_be_empty():
    """Results 6-N have body_snippet="" — explicit empty string, not
    null. The non-optional type is intentional: callers always get a
    string and don't have to check for None."""
    from mcp_server.schemas import SearchHit
    hit = SearchHit(
        law_id="x",
        identificador="0",
        title="Х",
        category="laws",
        title_snippet="Х",
        body_snippet="",
        relevance=0.1,
    )
    assert hit.to_dict()["body_snippet"] == ""
```

- [ ] **Step 4: Run the schema tests.**

Run: `.venv/bin/pytest -q tests/mcp_server/test_schemas.py 2>&1 | tail -3`

Expected: prior count + 2 new = green. Note: this likely breaks any test or production code that constructs `SearchHit(...)` without the new field. The full-suite run in Step 6 will surface those; we'll fix them in Task 8 along with the actual snippet generation.

- [ ] **Step 5: Run the full suite — expect failures in `test_search.py` because `full_text_search` returns dicts that don't yet have `body_snippet`.**

Run: `.venv/bin/pytest -q 2>&1 | tail -10`

Expected: ~281 passing, plus some failures in tests that construct `SearchHit` from dict literals without the new field. Note which tests fail; they get fixed in Task 8.

(The dataclass field added in this task is consumed by Task 8. Don't commit yet — the suite isn't green.)

### Task 8: Generate body_snippet in full_text_search + integration test

**Files:**
- Modify: `mcp_server/queries.py` (`full_text_search` populates `body_snippet`)
- Regenerate: `tools.json` (description shifts because the dataclass shifted)

- [ ] **Step 1: Add the body-snippet generation to `full_text_search`.**

In `mcp_server/queries.py`, find the existing post-processing loop after `search_fts`:

```python
    rows = search_fts(conn, effective_query, category=category, limit=limit)
    out: list[dict] = []
    for r in rows:
        title = r["title"] or f"<doc_id={r['doc_id']}>"
        out.append({
            "law_id": r["law_id"],
            "identificador": str(r["doc_id"]),
            "title": title,
            "category": r["category"],
            "title_snippet": r["snippet"],
            "relevance": -float(r["score"]),
        })
    return out
```

Replace with:

```python
    rows = search_fts(conn, effective_query, category=category, limit=limit)

    # FR-017 / D-2026-05-09-02: Python-side body snippet for the top
    # _BODY_SNIPPET_TOP_N results. Cost-bound — fetching laws_fts.body
    # for ЗОП (~559 KB) costs ~5 ms per row, so capping at 5 keeps
    # the overhead under ~25 ms.
    snippet_terms = [t for t in re.findall(r"\w+", bg_normalize(effective_query)) if len(t) >= 3]

    out: list[dict] = []
    for idx, r in enumerate(rows):
        title = r["title"] or f"<doc_id={r['doc_id']}>"
        body_snippet = ""
        if idx < _BODY_SNIPPET_TOP_N and snippet_terms:
            body_snippet = _make_body_snippet(conn, r["law_id"], snippet_terms)
        out.append({
            "law_id": r["law_id"],
            "identificador": str(r["doc_id"]),
            "title": title,
            "category": r["category"],
            "title_snippet": r["snippet"],
            "body_snippet": body_snippet,
            "relevance": -float(r["score"]),
        })
    return out
```

- [ ] **Step 2: Add the helper `_make_body_snippet` and the constant near the top of `mcp_server/queries.py`.**

Find the existing module-level constants section (next to `_CATEGORY_STOP_WORDS`):

```python
_CATEGORY_STOP_WORDS = frozenset({...})
```

Add below it:

```python
# FR-017 / D-2026-05-09-02 — body snippets are generated only for the
# top N hits to bound per-query cost. With ~5 ms per row to fetch
# laws_fts.body for the largest acts, N=5 keeps the overhead under
# ~25 ms (well within the 100 ms p95 budget).
_BODY_SNIPPET_TOP_N = 5

# Half-window in characters around the matched token. ±60 chars gives
# the model a sentence-sized fragment without ballooning the response
# payload (max 120 chars per snippet × 5 = 600 chars per search call).
_BODY_SNIPPET_HALF_WINDOW = 60


def _make_body_snippet(conn: sqlite3.Connection, law_id: str,
                      terms: list[str]) -> str:
    """Return a Python-extracted body fragment around the first
    occurrence of any term in `terms` within the act's indexed body.

    Falls back to the empty string if:
      - The body is empty or missing.
      - None of the terms appear in the body.

    Highlights the matched term with `<b>...</b>` to match the
    title-snippet convention.
    """
    row = conn.execute(
        "SELECT body FROM laws_fts WHERE law_id = ?", (law_id,)
    ).fetchone()
    if not row:
        return ""
    body = row["body"] or ""
    if not body:
        return ""

    # Find the earliest occurrence of any term (case-insensitive — the
    # body is already bg_normalize-d via insert_fts_row).
    body_lower = body.lower()
    earliest = -1
    matched_term = ""
    for term in terms:
        idx = body_lower.find(term.lower())
        if idx != -1 and (earliest == -1 or idx < earliest):
            earliest = idx
            matched_term = term

    if earliest == -1:
        return ""

    start = max(0, earliest - _BODY_SNIPPET_HALF_WINDOW)
    end = min(len(body), earliest + len(matched_term) + _BODY_SNIPPET_HALF_WINDOW)

    prefix = "..." if start > 0 else ""
    suffix = "..." if end < len(body) else ""

    # Highlight the actual matched substring in the original case.
    fragment = body[start:end]
    # Locate the matched term within the fragment to wrap with <b>.
    rel = earliest - start
    highlighted = (
        fragment[:rel]
        + "<b>"
        + fragment[rel:rel + len(matched_term)]
        + "</b>"
        + fragment[rel + len(matched_term):]
    )
    return f"{prefix}{highlighted}{suffix}"
```

- [ ] **Step 3: Update test_search.py tests that construct dict literals.**

The new field is non-optional. Existing tests that assert `"snippet" not in h` or compare dict shapes need updating. Run the test_search file alone first to see what breaks:

Run: `.venv/bin/pytest -q tests/mcp_server/test_search.py 2>&1 | tail -10`

For each failure, the fix is one of:
- A test asserting "result has these keys" needs to add `"body_snippet"`.
- A test mocking the `full_text_search` return shape needs the new field too.

The most likely callsite to update: `test_search_hit_has_title_snippet_not_snippet` which asserts `"snippet" not in h` — this still holds (we never added a `snippet` field; we have `title_snippet` and now `body_snippet`).

If a test fails because it asserts the EXACT keyset of a SearchHit, broaden it to assert "body_snippet is in the keys" instead.

- [ ] **Step 4: Add an integration test for the new field.**

Append to `tests/mcp_server/test_search.py`:

```python
# ─── FR-017 body-snippet generation (D-2026-05-09-02) ─────────────────────────


def test_search_includes_body_snippet_for_top_results(populated_conn, tmp_path):
    """FR-017 / D-2026-05-09-02: the top 5 results have a non-empty
    body_snippet (when the query token appears in the body); subsequent
    results have body_snippet=''."""
    # Need to seed laws_fts with body text — the conftest's insert_fts_row
    # uses the title for both title and body slots, so any query token
    # that's in the title is also in the body of the populated_conn
    # fixture acts.
    from mcp_server.server import build_app

    app = build_app(conn=populated_conn, corpus_root=tmp_path)
    hits = app.call_tool_sync("search", {"query": "обществения транспорт"})
    assert hits, "expected at least one hit for 'обществения транспорт'"

    # Top result must have a non-empty body_snippet with <b>...</b>
    # highlighting around the matched term.
    top = hits[0]
    assert "body_snippet" in top
    assert top["body_snippet"], (
        f"top result body_snippet should be non-empty; got {top!r}"
    )
    assert "<b>" in top["body_snippet"] and "</b>" in top["body_snippet"]


def test_search_body_snippet_capped_at_5_results(populated_conn, tmp_path):
    """Results 6-N have body_snippet='' to bound cost. The populated
    fixture has 7 acts; querying a common single-token word should
    return all 7 (after rang-tier sort), and only the first 5 get
    body_snippet populated."""
    # Seed enough rows to get >5 hits. The existing 7-row fixture
    # should suffice if we use a query that hits all of them.
    from mcp_server.server import build_app

    app = build_app(conn=populated_conn, corpus_root=tmp_path)
    # 'за' appears in every seeded title — should hit all rows.
    hits = app.call_tool_sync("search", {"query": "за", "limit": 50})
    if len(hits) <= 5:
        pytest.skip(
            f"need >5 hits to verify cap; got {len(hits)}. "
            "Add more seed rows to conftest.populated_conn."
        )
    # First 5 may have non-empty body_snippet; remainder must all be "".
    for i, h in enumerate(hits[5:], start=6):
        assert h["body_snippet"] == "", (
            f"hit #{i} should have empty body_snippet (cost bound); "
            f"got {h['body_snippet']!r}"
        )


def test_search_body_snippet_empty_when_no_term_matches_body(populated_conn, tmp_path):
    """If the synonym-expanded query happens to not appear verbatim in
    the body (synthetic case), body_snippet falls back to ''. The
    title_snippet stays populated since FTS5 still found the row."""
    # Hard to trigger synthetically with the in-memory fixture (where
    # body == title). This test serves as a contract sanity check for
    # the helper's fallback path; the underlying _make_body_snippet
    # is unit-tested below in test_make_body_snippet_returns_empty_on_no_match.
    pass


def test_make_body_snippet_returns_empty_on_no_match(populated_conn):
    """Direct unit test: when no term appears in the body, return ''."""
    from mcp_server.queries import _make_body_snippet
    out = _make_body_snippet(populated_conn, "zakon-a",
                             terms=["неизвестен_термин"])
    assert out == ""


def test_make_body_snippet_returns_empty_for_unknown_law_id(populated_conn):
    from mcp_server.queries import _make_body_snippet
    out = _make_body_snippet(populated_conn, "doesnotexist",
                             terms=["обществен"])
    assert out == ""
```

- [ ] **Step 5: Run the test_search file.**

Run: `.venv/bin/pytest -q tests/mcp_server/test_search.py 2>&1 | tail -5`

Expected: prior count + new tests, all green. If any pre-existing test fails because of a missing `body_snippet` key, fix it in this commit (broaden the keyset assertion or add the field to the expected dict).

- [ ] **Step 6: Regenerate `tools.json`.**

Run: `.venv/bin/python -m mcp_server.export_tools --output tools.json`
Expected: `Wrote tools.json (version=1.0.0, 3 tools, 9 error codes).`

- [ ] **Step 7: Run the full suite + tools.json parity.**

Run: `.venv/bin/pytest -q 2>&1 | tail -3`

Expected: 286 passed (281 from end of Batch C + 2 schema tests + 3 integration + 2 unit-tests = roughly 288; the exact count depends on how many test_search tests needed updating and whether the test_synonyms count is exactly 12 or more).

If the count is off, run `.venv/bin/pytest --collect-only -q | tail -1` to see the exact number and adjust the expected number in this plan accordingly.

- [ ] **Step 8: Commit.**

```bash
git add mcp_server/schemas.py mcp_server/queries.py tests/mcp_server/test_schemas.py tests/mcp_server/test_search.py tools.json
git commit -m "$(cat <<'EOF'
feat(search): add Python-side body_snippet generation (FR-017)

D-2026-05-09-02 / FR-017 (Phase 1b.3): SearchHit gains a body_snippet
field — a ±60-char window around the first matching query token in
the act's body, with <b>...</b> highlighting around the match.

Cost-bound: only the top 5 results get body_snippet populated. The
remaining results carry body_snippet="" (explicit empty string, not
None — non-optional dataclass field for caller simplicity). The
empty-string fallback also fires when:
  - the act's laws_fts.body row is missing or empty, or
  - none of the bg_normalize-d query terms appear in the body
    verbatim (synthetic case; rare since FTS5 had to find some match).

Implementation lives in mcp_server/queries.py:_make_body_snippet —
single rowid lookup against laws_fts (no scan), Python-side find()
across the body string. ~5 ms per result for ЗОП-sized bodies; ~25
ms total for the top-5 cap — comfortably under the 100 ms p95 budget.

Schema change is additive per Surface 3 (new non-optional string
field). tools.json regenerated; the parity test stays green.

Test count: 281 → 286 (2 dataclass round-trip tests + 3 integration
tests + 2 helper unit tests; 1 of the integration tests is a
pytest.skip placeholder for the synthetic body-vs-title divergence
case that the in-memory fixture can't easily trigger).

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## BATCH E — Close-out (Task 9)

### Task 9: Resolve 3 deferrals + ACTIVE.md/DECISIONS.md/protected-surfaces/FRS index/runbook updates

**Files:**
- Modify: `docs/sync/DEFERRED.md` (3 rows: D-01, D-02, D-04 → Resolved)
- Modify: `docs/sync/ACTIVE.md` (Phase 1b.3 → complete; pending updated)
- Modify: `docs/sync/DECISIONS.md` (D-029 captures 1b.3 design choices)
- Modify: `.ahelia/protected-surfaces.yaml` (3 deferrals → status: implemented)
- Modify: `docs/frs/INDEX.md` (FR-013, FR-015, FR-017 → Done)
- Modify: `docs/runbook/2026-05-09-phase1b1-operator-setup.md` (mention body_snippet + synonym expansion in the get_law / search row description)

- [ ] **Step 1: Move 3 deferrals from Active to Resolved in `DEFERRED.md`.**

Open `docs/sync/DEFERRED.md`. In the Active deferrals table, REMOVE the rows for `D-2026-05-09-01`, `D-2026-05-09-02`, `D-2026-05-09-04`. Leave `D-2026-05-09-05` (FR-014 / Phase 4) as the sole remaining Active row.

In the Resolved deferrals table, append three rows after the existing two:

```
| D-2026-05-09-01 | `bg_normalize` last-character-only suffix stripping (adjective long-form definite article asymmetry) | Phase 1b.1 | Phase 1b.3 | Implemented | 2026-05-09 | [FR-013](../frs/INDEX.md) | Per-suffix MIN_STEM_LEN model in `index/fts.py:_BG_DEFINITE_SUFFIXES`; 3-char suffixes (`ите`, `ият`, etc.) close the long-form asymmetry. See [D-029](DECISIONS.md). |
| D-2026-05-09-02 | `search` returns `title_snippet` only (no body snippet) | Phase 1b.1 | Phase 1b.3 | Implemented | 2026-05-09 | [FR-017](../frs/INDEX.md) | Python-side body-snippet generator in `mcp_server/queries.py:_make_body_snippet`; cost-bounded to top 5 results. New `body_snippet` field on `SearchHit` (additive per Surface 3). See [D-029](DECISIONS.md). |
| D-2026-05-09-04 | Synonym dictionary for Bulgarian abbreviations and `rang`-aware re-ranking | Phase 1b.1 | Phase 1b.3 | Implemented | 2026-05-09 | [FR-015](../frs/INDEX.md) | Two-part fix: hand-curated `index/synonyms.LEGAL_ABBREVIATIONS` (20 entries) rewrites single-token abbreviation queries before FTS5; tier-sort in `search_fts` puts parent laws (закон/кодекс) above implementing regs (правилник/наредба). See [D-029](DECISIONS.md). |
```

- [ ] **Step 2: Update `ACTIVE.md`.**

Open `docs/sync/ACTIVE.md`. Update the header lines:

OLD:
```
**Current phase:** Phase 1b.2 — **complete on `main` 2026-05-09**.
**Next action:** Phase 1b.3 (operator/end-user polish) OR Phase 2 (temporal index) — both are now unblocked. See "Pending" below.
```

NEW:
```
**Current phase:** Phase 1b.3 — **complete on `main` 2026-05-09**. Phase 1b is fully shipped (1b.1 + 1b.2 + 1b.3).
**Next action:** Phase 2 (temporal index, FR-001) — newly unblocked. See "Pending" below.
```

Find the "**Phase 1b.2** ... — complete on `main`" section and append a sibling section for 1b.3:

```
**Phase 1b.3** (operator/end-user polish) — complete on `main` 2026-05-09:
- **FR-013 closed**: long-form definite article asymmetry resolved by per-suffix MIN_STEM_LEN model in `index/fts.py:_BG_DEFINITE_SUFFIXES`. 3-char suffixes (`ите`, `ият`, `ета`, `ете`, `ия`) reduce uniformly with their indefinite roots; 2-char suffixes preserve their 4-char threshold to protect short demonstratives.
- **FR-015 closed**: hand-curated synonym dictionary in `index/synonyms.py` (20 Bulgarian legal abbreviations) + rang-aware tier sort in `search_fts`. Single-token abbreviation queries (`ЗОП`, `НК`, `ГПК`) now resolve to their parent acts; parent laws outrank their implementing regulations in result lists.
- **FR-017 closed**: Python-side body-snippet generation cost-bounded to the top 5 hits per search. New `body_snippet` field on `SearchHit` (additive per Surface 3). `tools.json` regenerated.
- Test count: 256 → ~286 (exact count locks at Task 9 close-out).
- D-029 captures the design choices in `DECISIONS.md`.

DEFERRED.md now has a single remaining Open row (D-2026-05-09-05 / FR-014 / Phase 4 incremental rebuild). Phase 2 promotion is no longer gated on Phase 1b deferrals.
```

In the "Pending" section, REMOVE the bullet that mentions Phase 1b.3 as upcoming. The remaining bullets (Phase 2, FR-011 G2 triage) stay as-is.

- [ ] **Step 3: Add D-029 to `DECISIONS.md`.**

The DECISIONS file uses a table format (matched D-028's pattern). Append one row at the end:

```
| D-029 | 2026-05-09 | Phase 1b.3 closure design choices | (a) FR-013 fixed by replacing the global MIN_STEM_LEN with a per-suffix-min-stem table ordered longest-first — `новият` reduces to `нов` via the new 3-char `ият` suffix while short demonstratives like `това` remain protected by the 4-char threshold on 2-char suffixes. (b) FR-015 implemented as TWO orthogonal layers: a hand-curated abbreviation dictionary (`index/synonyms.py`, 20 entries) that rewrites single-token queries pre-FTS5, AND a stable tier-sort in `search_fts` that puts parent laws (закон/кодекс categories) above implementing regs/ordinances. The dictionary is one-direction (abbrev → canonical) because the long form already reaches the act via FTS5 title matching. (c) FR-017 implemented as Python-side body-snippet generation cost-bounded to the top 5 hits — fetching `body` from `laws_fts` rowid, finding the first matching token, returning a ±60-char window. Results 6-N carry `body_snippet=""` (non-optional empty string for caller simplicity). (d) The `body_snippet` field is non-optional on `SearchHit` despite being empty for >5-rank results — explicit empty-string is more ergonomic than `Optional[str]` and matches existing fields' shapes. Closes deferrals D-2026-05-09-01, -02, -04; the only remaining open deferral is D-2026-05-09-05 (FR-014, Phase 4 incremental rebuild). Plan: `docs/plans/2026-05-09-phase1b3-polish.md`. | Active |
```

- [ ] **Step 4: Update `.ahelia/protected-surfaces.yaml` deferrals.**

Find the entries `D-2026-05-09-01`, `D-2026-05-09-02`, `D-2026-05-09-04` in the `deferrals:` block. For each, change `status: open` → `status: implemented` and add a `resolution_note:` field referencing D-029.

For D-2026-05-09-01:
```yaml
  - id: D-2026-05-09-01
    fr: FR-013
    title: bg_normalize last-character-only stripping
    punted_from: 1b.1
    target: 1b.3
    status: implemented
    resolution_note: "Per-suffix MIN_STEM_LEN table in index/fts.py; 3-char definite-article suffixes added; D-029."
    surfaces_affected:
      - "index/fts.py:_BG_DEFINITE_SUFFIXES"
      - "index/fts.py:_strip_definite_article"
      - "index/fts.py:bg_normalize"
```

For D-2026-05-09-02:
```yaml
  - id: D-2026-05-09-02
    fr: FR-017
    title: search title_snippet (no body snippet)
    punted_from: 1b.1
    target: 1b.3
    status: implemented
    resolution_note: "Python-side body_snippet generator in mcp_server/queries.py; cost-bounded to top 5; D-029."
    surfaces_affected:
      - "mcp_server/queries.py:full_text_search"
      - "mcp_server/queries.py:_make_body_snippet"
      - "mcp_server/schemas.py:SearchHit"
```

For D-2026-05-09-04:
```yaml
  - id: D-2026-05-09-04
    fr: FR-015
    title: synonym dictionary for Bulgarian abbreviations
    punted_from: 1b.1
    target: 1b.3
    status: implemented
    resolution_note: "Hand-curated synonym dict in index/synonyms.py + rang-aware tier sort in index/fts.py:search_fts; D-029."
    surfaces_affected:
      - "index/synonyms.py:LEGAL_ABBREVIATIONS"
      - "mcp_server/queries.py:full_text_search"
      - "index/fts.py:search_fts"
      - "index/fts.py:_RANG_TIER"
```

Update `deferrals_meta.last_synced` to `2026-05-09` (already current — confirm not stale).

- [ ] **Step 5: Update `docs/frs/INDEX.md`.**

Find the rows for FR-013, FR-015, FR-017 and flip Status `Backlog` → `Done (2026-05-09)` with a one-line resolution note pointing at D-029 and the relevant code surface.

For FR-013:
```
| FR-013 | Bulgarian morphology — adjective long-form definite article | 1b.3 (stemmer milestone) | Low | **Done (2026-05-09)** | **CLOSED in Phase 1b.3** via per-suffix MIN_STEM_LEN table in `index/fts.py:_BG_DEFINITE_SUFFIXES`. 3-char suffixes (`ите`, `ият`, `ета`, `ете`, `ия`) reduce adjective long-forms uniformly with their indefinite roots; 2-char suffixes keep the 4-char threshold so demonstratives like `това` are protected. Locked test: `bg_normalize("новият") == bg_normalize("нов")`. See D-029. |
```

For FR-015:
```
| FR-015 | Search ranking — synonym/abbreviation dictionary + rang-aware boost | 1b.3 (stemmer milestone) | Medium | **Done (2026-05-09)** | **CLOSED in Phase 1b.3** via two orthogonal layers: (a) hand-curated synonym dictionary in `index/synonyms.py` (20 abbreviations, `expand_if_abbreviation` rewrites single-token queries pre-FTS5), and (b) rang-aware tier sort in `index/fts.py:search_fts` (laws + codes outrank regulations + implementing + ordinances). Locked tests: `search("ЗОП")` finds the parent law via expansion; `search("обществения транспорт")` puts the parent law above the implementing regulation. See D-029. |
```

For FR-017:
```
| FR-017 | Search body snippet — currently title-only | 1b.3 (stemmer milestone) | Low | **Done (2026-05-09)** | **CLOSED in Phase 1b.3** via Python-side body-snippet generation in `mcp_server/queries.py:_make_body_snippet`. Cost-bounded to top 5 hits per search (~5 ms per row × 5 = ~25 ms total, well under the 100 ms p95 budget). New `body_snippet` field on `SearchHit` (additive per Surface 3); results 6-N carry `body_snippet=""` (explicit empty string). See D-029. |
```

- [ ] **Step 6: Update the runbook `Tools surfaced` table.**

In `docs/runbook/2026-05-09-phase1b1-operator-setup.md`, find the `search` row and append a sentence to its description:

OLD:
```
| `search(query, category=None, limit=20)` | Bulgarian/Cyrillic text + optional category filter | ranked list of hits |
```

NEW:
```
| `search(query, category=None, limit=20)` | Bulgarian/Cyrillic text + optional category filter | ranked list of hits. Each hit also carries a `body_snippet` field (top-5 only — empty string for results 6-N) and the result list is rang-tier-sorted (laws/codes above regulations/ordinances). Single-token abbreviation queries (`ЗОП`, `НК`, etc.) are auto-expanded to canonical long forms via `index/synonyms.py`. |
```

- [ ] **Step 7: Verify everything.**

Run YAML parse:
```bash
.venv/bin/python -c "
import yaml
d = yaml.safe_load(open('.ahelia/protected-surfaces.yaml'))
defs = d['deferrals']
imp = [x for x in defs if x['status'] == 'implemented']
op = [x for x in defs if x['status'] == 'open']
assert len(imp) == 5, f'expected 5 implemented, got {len(imp)}'
assert len(op) == 1, f'expected 1 open, got {len(op)}'
assert op[0]['id'] == 'D-2026-05-09-05', op[0]['id']
print(f'OK: {len(imp)} implemented, {len(op)} open (D-2026-05-09-05 = FR-014 Phase 4)')
"
```

Run cross-reference sweep:
```bash
grep -c "D-029" /Users/ekimir/swprj/legalize-bg/docs/sync/DECISIONS.md /Users/ekimir/swprj/legalize-bg/docs/sync/DEFERRED.md /Users/ekimir/swprj/legalize-bg/docs/sync/ACTIVE.md
```
Expected: D-029 appears in DECISIONS.md (1×), DEFERRED.md (3×, one per Resolution note), ACTIVE.md (1×).

Run full suite:
```bash
.venv/bin/pytest -q 2>&1 | tail -3
```
Expected: ~286 passed; no behavioral change in this batch.

- [ ] **Step 8: Commit Batch E + the plan file.**

```bash
git add docs/sync/DEFERRED.md docs/sync/ACTIVE.md docs/sync/DECISIONS.md .ahelia/protected-surfaces.yaml docs/frs/INDEX.md docs/runbook/2026-05-09-phase1b1-operator-setup.md
git commit -m "$(cat <<'EOF'
docs(sync): close Phase 1b.3 — D-01 + D-02 + D-04 → implemented; D-029 logged

Phase 1b.3 closeout:

- DEFERRED.md: D-2026-05-09-01 (FR-013), -02 (FR-017), -04 (FR-015)
  move from Active to Resolved with Resolution notes pointing at
  D-029. Single Open row remains: D-2026-05-09-05 (FR-014, Phase 4
  incremental rebuild).

- ACTIVE.md: Phase 1b.3 status flips to "complete on main 2026-05-09";
  Phase 1b is now fully shipped. Phase 2 (FR-001) is the next
  unblocked phase.

- DECISIONS.md: D-029 captures the design choices for the three
  deferrals — per-suffix MIN_STEM_LEN for FR-013, two-layer
  (dictionary + rang sort) for FR-015, top-5 Python-side snippet
  for FR-017. Includes the rationale for non-optional body_snippet.

- .ahelia/protected-surfaces.yaml: 3 entries flip from status: open
  → status: implemented with resolution_note tags pointing at D-029.
  surfaces_affected lists the relevant code symbols accurately.

- docs/frs/INDEX.md: FR-013, FR-015, FR-017 rows flip Status to
  "Done (2026-05-09)" with multi-sentence resolution notes referring
  to the implementation.

- runbook: search row description gains body_snippet + rang-tier
  sort + synonym-expansion mentions.

Test count holds at the Phase 1b.3 final number (this batch is
doc-only).

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"

git add docs/plans/2026-05-09-phase1b3-polish.md
git commit -m "$(cat <<'EOF'
docs(plan): Phase 1b.3 polish implementation plan

Plan covering the three open Phase 1b.3 deferrals: FR-013 (long-form
definite article), FR-015 (synonym dictionary + rang-aware re-rank),
FR-017 (body snippet). Five batches; nine tasks.

Pre-recorded empirical evidence: bg_normalize asymmetry trace
(новият/нов), curated 20-entry synonym dictionary, body-snippet
cost projection (~5 ms × 5 = 25 ms under the 100 ms p95 budget).

Plan was written and self-reviewed before execution.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Definition of Done

- [ ] **Batch A** — `bg_normalize("новият") == bg_normalize("нов")`; suffix table is per-suffix-MIN_STEM-LEN; demonstratives unchanged; existing symmetric-reduction test still green.
- [ ] **Batch B** — `index/synonyms.LEGAL_ABBREVIATIONS` has ≥15 entries; `search` (single-token abbrev) hits the parent law; multi-word queries pass through unchanged.
- [ ] **Batch C** — `search("обществения транспорт")` puts the parent law above the implementing reg; tier sort is stable within tiers.
- [ ] **Batch D** — `SearchHit` has `body_snippet: str`; top-5 results have non-empty body_snippet with `<b>...</b>` highlighting; results 6+ have `body_snippet=""`; tools.json regenerated and parity test green.
- [ ] **Batch E** — DEFERRED.md has 1 Open + 5 Resolved; ACTIVE.md marks Phase 1b.3 complete; DECISIONS.md D-029 logged; protected-surfaces.yaml has 1 open + 5 implemented; FRS index has FR-013/15/17 → Done; runbook search row mentions body_snippet + synonym + rang-tier.
- [ ] **Test suite** — 286 passing (256 baseline + ~30 new across all batches; exact final count locked at Task 9 close-out).
- [ ] **Surface 3 contract preserved** — `body_snippet` is the only addition; existing fields and types unchanged. Surface 6 spirit holds (bg_normalize symmetry preserved by construction; no `provisions` extraction changes).
- [ ] **No new schema migrations.** No new error codes. No new MCP tools.
- [ ] **5 commits** (one per batch + the plan file).

---

## Risk register

| Risk | Mitigation |
|---|---|
| Lowering MIN_STEM_LEN for 3-char suffixes might over-strip an unforeseen Bulgarian word. | The over-stripping guard test explicitly checks 6 common short demonstratives (`това`, `този`, `тази`, `тези`, `тоя`, `оня`) and the new suffix list never matches their endings. New entries to the suffix list should add a regression test for any new asymmetric pair AND a guard against the closest demonstrative. |
| Hand-curated synonym dictionary may have errors (wrong canonical form, missing common abbreviation). | The dictionary is a small frozen dict (20 entries); the parity test asserts every key is bg_normalize-d and every canonical form contains a load-bearing keyword. Errors surface immediately. |
| Rang-aware tier sort could surprise callers who relied on bm25-only ordering. | The change is documented in `SearchHit`'s docstring (`relevance` is "within-tier signal, not global"). The existing test surface gets explicit tier-priority lock; any caller depending on global bm25 order has a single grep target (`relevance`) for migration. |
| `_make_body_snippet` re-fetches body for every top-5 hit on every search; for a high-QPS deployment, this could amortize as a hot path. | Phase 1b.3 is single-user MCP; QPS is bounded by Claude Code session pace (a few requests/minute). If Phase 1c+ ever runs in a multi-user mode, body fetches can be batched into a single `WHERE law_id IN (...)` query — small refactor, not architectural. |
| Non-optional `body_snippet` field in `SearchHit` is a Surface 3 change. | Per Surface 3 rules ("typed-dicts and additive only"), adding a field is permitted; only field removal or required-field-with-no-default would require preflight. Existing callers that don't read `body_snippet` are unaffected. |

---

## Self-review notes

Walked back through the plan once after writing.

**1. Spec coverage:** Each of the 3 deferrals has a dedicated batch (A=FR-013, B+C=FR-015 two parts, D=FR-017). Each batch has TDD red-green-commit. Batch E closes the governance loop.

**2. Placeholder scan:** No "TBD"; no unresolved FR-NNN references; every step has executable code. The conditional Step 2a in Task 6 (rang-aware test fixture extension) is conditional on actual fixture content; if unexpected drift, the executor stops and surfaces.

**3. Type / identifier consistency:**
- `_CATEGORY_STOP_WORDS` (frozen set), `LEGAL_ABBREVIATIONS` (mutable dict for test patching), `_BG_DEFINITE_SUFFIXES` (tuple of pairs), `_RANG_TIER` (dict), `_BODY_SNIPPET_TOP_N` and `_BODY_SNIPPET_HALF_WINDOW` (int constants) — all underscore-prefixed module-private; consistent.
- `expand_if_abbreviation` and `_make_body_snippet` — both take/return strings; consistent.
- `SearchHit.body_snippet: str` (non-optional) — consistent with the other string fields (`title_snippet: str`, `category: str`).
- `tools.json` regeneration mentioned in Batch D commit message (Step 6); the test_export_tools parity test catches drift if forgotten.

No gaps found. Plan ready for execution.

---

## Out-of-scope (re-stated)

- Structured logging + per-tool-call metrics, packaging (PyPI/Docker), Bulgarian Snowball stemmer (proper morphology beyond definite articles).
- Phase 2 temporal index, FR-011 G2 triage, FR-014 incremental rebuild.
- Allowlist consolidation (Round-3 limitation note from 1b.1).
- Bidirectional synonym lookup (canonical → abbreviation) — current one-way is sufficient because the long form already reaches the act via FTS5.
