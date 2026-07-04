# Design: alinea/citation discriminator (FR-030)

**Status:** ⛔ **SUPERSEDED / RETIRED (2026-07-05, D-055).** This script-based
hybrid-discriminator design was executed in full and RETIRED: Task 3's
full-corpus rebuild-diff proved it drops ~82 real alineas (real legal-text loss)
because `"[ref] N (M)"` is byte-identical for a citation (`"чл. 8 (3)"`) and a
real alinea after a numeric reference (`"по ал. 4 (6)"`) — a regex cannot
separate them. **DO NOT re-attempt the script approach.** FR-030 is redirected to
a reasoning-based flagger→agentic-reasoner→applier pipeline (D-055, `docs/frs/INDEX.md`
FR-030). This document is retained only as the record of why the pattern approach
fails; the sections below describe the retired design.

**Requirement:** FR-030 (`docs/frs/INDEX.md`). **Origin:** the pre-UI hardening
plan's P0-2 (`index/provisions.py` `_ALINEA_MARKER_RE`) fixed the 4-digit-year
false positives with a `\d{1,3}` digit cap; that cap admits 3-digit
citation-style numbers it can't distinguish from real alineas. Finding:
`docs/research/2026-07-02-fr030-3digit-alinea-false-positives.md`.

---

## 1. Problem

`index/provisions.py:_split_alineas` treats **every** `(N)` match of
`_ALINEA_MARKER_RE` (`r"\(\s*(\d{1,3}[а-я]?)\s*\)"`) as an alinea boundary. Real
alinea openers (`(1) (2) (3)…`) and parenthesised citation numbers in running
prose (`чл. 8 (3)`, `четири (4) на сто`, `код на страната (100)`) are
syntactically identical — digits in parens. The result is bogus `provisions`
rows with `paragraph` = a citation number, corrupting `get_article` and article
lookups.

Two mechanical fixes were already tried and **rejected**: a bigger digit cap
(admits 3-digit citations) and a letter-boundary/preceding-punctuation heuristic
(drops real alineas whose preceding text lacks terminal punctuation — see §2).

## 2. Empirical evidence (2026-07-04 read-only scan of the 3,602-act catalog)

A whole-corpus scan of every article-as-whole body (`provisions` where
`paragraph IS NULL`, 146,577 rows) extracting the ordered `(N)` sequence, walked
against a candidate "sequence-only" rule (start at 1; next ∈ {current,
current+1}):

- 83,825 articles carry ≥1 `(N)` marker; 304,486 markers, of which the
  sequence-only rule would reject 636 as out-of-sequence.
- **All 8 documented false-positive values rejected** (100, 230, 400, 401, 505,
  506, 601, 660 → 100%).
- **But 105 "small forward jump" cases** (`(1)→(4)`, `(1)→(3)`, `(2)→(6)`…) in
  real laws looked like they might be genuine alinea gaps.

**Vision inspection of the small-jump cases (the decisive step)** showed they are
NOT gaps — real alinea sequences are contiguous; the jumps are **citations
interleaved inside a contiguous real sequence**:

- `ЗАЕ чл.5` seq `[1,4]`: *"за прилагане на чл. III **(1)** и **(4)** от
  Договора"* — **both** are citations (treaty-article refs); the article has no
  real alineas. A sequence-only rule would still wrongly accept the leading `(1)`.
- `ЗПУПС чл.9`: real alineas `(1)…(7)` **contiguous**, interleaved with
  *"четири **(4)** на сто"*, *"едно **(1)** на сто"* citations.
- `ЗЗВВХВС чл.7`: real `(1)(2)`, with *"чл. 8 **(3)** от Регламент"* between them
  — a sequence-only rule accepts this citation because it equals current+1.
- `ЗПУО чл.122`: real `(1)(2)(3)`, with a grade citation *"среден **(3)**"* mid-body.
- `ЗКНВП чл.18а`: real `(1)…(4)` interleaved with many `чл. N(M)` regulation refs.

And the three articles the **punctuation heuristic** dropped real alineas on
(`ЗОП чл.196`, `ЗЕУ чл.5`, `ЗАДС чл.78`) are **perfectly contiguous with no
interleaved citations** — the heuristic failed only because some real alineas
follow a word, not a period (e.g. ЗОП's real `(5)` after *"…доброволна
прозрачност (5)"*, ЗЕУ's real `(4)` after *"…дигиталната трансформация (4)"*).

**Conclusion:** the two naive rules fail on *disjoint* cases. Sequence handles
the punctuation-failure articles; punctuation-context handles the
interleaved-citation articles. A hybrid of both is required — and the problem is
general citation-vs-alinea discrimination (~600+ markers corpus-wide), not the
8 documented rows.

## 3. Design — hybrid discriminator (two signals, both must pass)

For each `(N[а-я]?)` marker, accept it as a real alinea iff **Signal 1 AND
Signal 2** pass. `current` advances only on accept.

**Signal 1 — sequence continuity.** `current` starts at 0 (not started).
- While `current == 0`: qualify only if `n == 1`.
- Once started: qualify if `n == current` (letter-suffix sub-alinea, e.g.
  4 → 4а) or `n == current + 1`.
- Anything else is out-of-sequence → not an alinea (and does NOT advance
  `current`, so a citation can't derail the real sequence that follows).

**Signal 2 — citation-context guard.** Even a sequence-qualifying marker is a
citation (reject) if the token immediately preceding `(` (skipping one space) is:
- a token **ending in a digit** or a **Roman numeral** (`чл. 8 (3)`,
  `чл. III (1)`, `т. 5 (2)`);
- a **cross-reference abbreviation**: `чл`, `ал`, `т`, `буква`/`бук`, `§`,
  `изр`, `Регламент`, `Директива` (with or without a following `№`);
- a **Cyrillic cardinal-number word**: `нула, едно/една, две/два, три, четири,
  пет, шест, седем, осем, девет, десет` (extend from the rebuild-diff evidence).

Otherwise the marker is not a citation context.

**Worked examples** (all resolve correctly):

| Article | markers | result |
|---|---|---|
| ЗОП чл.196 | 1,2,3,4,5 (contiguous, some after words) | all 5 alineas kept (S1 seq; S2 clean) |
| ЗПУПС чл.9 | 1,**4**,**1**,2,**1**,3,4,5,6,7 | alineas 1–7; `четири(4)`/`едно(1)` rejected (S2 cardinal word; or S1) |
| ЗЗВВХВС чл.7 | 1,**3**,2,**3** | alineas 1,2; `чл.8(3)` rejected (S1 out-of-seq / S2 digit) |
| ЗПУО чл.122 | 1,**3**,2,3 | alineas 1,2,3; `среден(3)` rejected (S1 out-of-seq) |
| ЗАЕ чл.5 | **1**,**4** | no alineas; `чл. III (1)` rejected (S2 Roman), `(4)` rejected (S1) |

## 4. Implementation location

`index/provisions.py` only. `_split_alineas` changes from "split on every marker"
to "walk markers, apply the discriminator, split on accepted markers." Add a
pure helper `_is_citation_context(body, marker_start) -> bool` (Signal 2) and a
sequence walker (Signal 1) — both unit-testable in isolation. `_ALINEA_MARKER_RE`
is unchanged (still the candidate generator). No change to `parse()`'s row shape
or `Provision`.

## 5. Validation strategy (the real safety net)

1. **Full `index.build` rebuild** on the real corpus with the new parser.
2. **Diff `provisions` alinea rows** (`paragraph IS NOT NULL`) before vs after:
   - Removed set = citations no longer mislabeled (expect ~600+, incl. the 8).
   - **Confirm no article lost a real alinea** — vision-verify a sample of
     removed markers (especially any small-forward-jump removals) and spot-check
     that high-alinea articles retain their full real set.
   - Investigate any *added/changed* alinea rows (should be none).
3. **Oracle validation** still passes (existing consolidation gate).
4. The catalog is derived/gitignored — no corpus commits; the deliverable is
   parser code + tests. A deployer rebuilds `catalog.db`.

## 6. Testing (TDD)

- Unit tests for `_is_citation_context` and the sequence walker.
- Discriminator tests: the ~8 inspected articles (§2) as fixtures, each asserting
  the **exact accepted-alinea set** (real alineas kept, citations dropped).
- Characterization test: the 8 documented FP values never appear as `paragraph`.
- Existing `tests/index/` provisions tests stay green.

## 7. Risks & mitigations

- **False negative (drop a real alinea):** a real alinea preceded by a
  digit/number-word would be wrongly guarded. Low probability (real alineas
  follow clause text, not a bare number). The rebuild-diff + vision pass is the
  net; if found, tighten Signal 2 (e.g. require the digit to be adjacent, or
  scope the cardinal-word list).
- **Cardinal-word list completeness:** start from the inspected cases; finalize
  from the rebuild-diff evidence, not guesswork.
- **Roman-numeral over-match:** limit to `[IVXLC]+` tokens of length ≤ 4 to avoid
  matching ordinary text.

## 8. Non-goals

- No change to `_ALINEA_MARKER_RE`, `parse()` row shape, `Provision`, the SQLite
  schema, or any MCP tool signature.
- No corpus markdown edits (this is a parse-time fix).
- Not fixing `чл. N(M)` *rendering* in body text — only its mis-parse into an
  alinea row.

## 9. Governance

- `index/provisions.py` alinea parsing is **not** a protected surface (no
  frontmatter/schema/tool-sig/commit-format change) → no IMPLEMENTATION-PREFLIGHT;
  gated instead by the §5 rebuild-diff + oracle validation.
- New `DECISIONS.md` entry (next id `D-055`) records the hybrid discriminator and
  the empirical basis. FR-030 → Done on completion.
