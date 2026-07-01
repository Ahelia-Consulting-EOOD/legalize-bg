# How we can be SURE the parser captures 100% of legal content

**Question (owner, 2026-06-29):** "How can I be SURE that we have ENUMERATED 100% completely ALL classes?"

**Short answer:** You cannot, and you should not try. Enumerating classes from a sample of acts is *induction* — a class that appears only in the Constitution, one old кодекс, or a tariff annex won't be in the sample. That is the exact mindset that produced the bug (the parser was an allowlist built from an incomplete class enumeration). Certainty comes from inverting the question.

---

## 1. The reframe: don't count classes, measure uncovered text

The thing we actually care about is not "have I seen every class" but "did any source text fail to reach the output." That question is **class-agnostic** and directly measurable. The `coverage_ledger.py` harness, within each act's legal-content region, classifies every text node:

- **COVERED** — an ancestor's class is a kept entry in `CLASS_MAP`.
- **EXCLUDED** — an ancestor is mapped but deliberately omitted (e.g. `HistoryOfDocument`).
- **UNCOVERED (Cyrillic)** — *no* mapped ancestor. This is exactly what the parser silently drops, **regardless of whether we ever knew the class name.** Reported bucketed by nearest class, so the residual is *named*, not guessed.

## 2. Result on a multi-type sample (закон/кодекс/правилник/наредба, 7 acts)

| Parser | Uncovered Cyrillic legal text (union) | Composition |
|---|---:|---|
| **Current (as shipped)** | **~254,000 chars** | `FinalEdictsArticle` 219,402 · `NewDocReference` 21,243 · `LegalDocReference` 4,507 · `Title` 4,343 · `SameDocReference` 4,182 · chrome 668 |
| **+ {AdditionalEdicts, FinalEdicts, FinalEdictsArticle}** | **375 chars** | `Title` 228 · `boxi/boxinb` 147 |

And both residual buckets are proven non-losses:
- `boxi/boxinb` (147) = the **"ДОБАВИ В МОИТЕ АКТОВЕ"** personalization button — UI chrome.
- `Title` (228, ГПК only) = article headings (`Предмет`, `Добросъвестност`, `Законност`, `Диспозитивно начало`) that lex.bg duplicates in a hidden editorial `<p class="buttons">`; the **same headings are already present in the output via the `Article` element** (verified: `"Диспозитивно начало Чл. 6. (1) …"`). Not lost.

Note how the ledger also self-corrected the naive census: `NewDocReference`/`LegalDocReference`/`SameDocReference` looked like dropped classes in the baseline, but they are *children of* `FinalEdictsArticle` — they drop to zero once FEA is mapped. The ledger distinguishes "independently dropped" from "child of a dropped parent." **Net legal text lost after the fix on this sample = 0.**

## 3. How to get ABSOLUTE certainty for the whole corpus (not a sample)

Run the coverage ledger as a **hard gate over 100% of fetched acts** during re-bootstrap. Per-act assertion:

> uncovered-Cyrillic-text(act) ⊆ a small explicit chrome whitelist (`boxi/boxinb`, button popups, …); otherwise FAIL the act and surface it.

Because the gate measures **content presence, not class names**, it catches drops caused by classes we have never seen. This is the structural oracle — it is the guarantee. Enumeration is not.

## 4. Make the default safe (architectural inversion)

Today the parser is an **allowlist**: default = drop, so an unknown class silently disappears (optimizes for clean output, risks invisible loss — the worst trade for a legal corpus). Invert it: walk the legal-content region and **keep by default, excluding only a denylist of known chrome** (`buttons`, `boxi*`, `pic*`, `History*`, `*Reference` tooltips, `script/style`). Then an unknown legal class can never silently vanish — worst case it appears as visible, reviewable text, and the coverage gate stays green because nothing is uncovered. Failure mode flips from "content silently missing" to "extra junk visible" — catchable, not catastrophic.

## 5. Belt-and-suspenders (confirmation, not the guarantee)

During the re-bootstrap fetch, also union every CSS class across **all** acts and diff against the known map, so we get the empirical full vocabulary too. Useful for mapping decisions, but secondary: the content-coverage gate (§3) + the keep-by-default inversion (§4) are what make "did we lose anything" answerable with *yes/no*, per act, across the entire corpus.

## Reproduce

```bash
cd /Users/ekimir/swprj/legalize-bg
.venv/bin/python docs/research/2026-06-29-parser-data-loss-forensics/coverage_ledger.py
```
