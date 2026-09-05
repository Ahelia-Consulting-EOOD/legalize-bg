# CPD-2026-09-05: State Gazette gap fill for provisions lex.bg omits

**Status:** SUPERSEDED 2026-09-05 by the graded source model (D-059, D-063). The detector and the
audit stand; the proposed process does not. Under approach C an act whose promulgated text lex.bg
omits is rebuilt from the Gazette through the sanctioned write gate (grade A) or has its Gazette
events audited (grade B); no corpus file is hand-edited and no `gap_fill` frontmatter extension is
adopted. The hand-edited `[popravka]` commit for Закон за обществения транспорт that accompanied the
first version of this proposal (PR #24) was not merged; that act is the first grade A pilot. The
class is registered as FR-042. The three owner questions below are answered by D-059: no `gap_fill`
field, the scanner runs strict only once its candidates are adjudicated, provenance is exposed via
the per-act grade.
**Origin:** takt-plan programme, TP-001 review round 1 finding F1 and follow-up FU-002 (the definitions section of Закон за обществения транспорт renders empty); confirmed 2026-09-05 against the State Gazette
**Author:** Claude session on owner (ekimir) dispatch, 2026-09-05
**Evidence:** `docs/audits/2026-09-05-source-dropped-additional-provisions.md`
**Directives touched:** OWNER-DIRECTIVES 2 (lex.bg = bootstrap only; DV = ongoing source) and 3 (lex.bg = validation oracle for the consolidation engine)

## Problem

lex.bg drops the additional provisions of some acts entirely: the heading survives, its § 1 (and
sometimes more) does not, and the final provisions start at § 2. The bootstrap copied that
faithfully, so the corpus presents an act as complete while its statutory definitions are missing.
For Закон за обществения транспорт the missing § 1 holds twelve definitions ("Редовна линия",
"Възел за достъп", "Eдинен превозен документ" and others) that downstream consumers need; the
takt-plan programme had to carry the gap as a follow-up for four months.

The scanner `scripts/structure_gaps.py` finds 95 candidate acts, 25 of them with an empty
additional-provisions section.

## Proposal

1. **Detection in the gate.** Run `scripts/structure_gaps.py --warn` in CI and publish its table;
   promote a rule to strict once its candidate list is adjudicated and an allow-list exists for the
   legitimate cases of `paragraph-start-above-1`.
2. **Gap fill from the State Gazette, marked.** For a section lex.bg omits, insert the text from the
   promulgated act in the State Gazette (dv.parliament.bg), normalised to the corpus conventions
   (ASCII quotes, hyphens, Cyrillic homoglyphs corrected), and record the provenance in a new
   optional frontmatter extension `gap_fill:` (a list of `section`, `source`, `dv_issue`,
   `dv_year`, `url`, `fetched`, `reason`). Directive 2 already makes the Gazette the ongoing
   source; the extension is additive, so IMPLEMENTATION-PREFLIGHT surface 2 allows it without a
   preflight. The commit is a `[popravka]` with `Source-Id: dv-<material id>`.
3. **Oracle rule.** The consolidation oracle (directive 3) compares against lex.bg; a gap-filled
   section is expected to be absent there. The oracle comparison skips the sections listed under
   `gap_fill` instead of reporting them as drift.
4. **Adjudication.** The 24 remaining empty sections are checked against the Gazette one by one
   in a follow-up batch; each confirmed omission is filled the same way, each legitimate case is
   allow-listed with its reason.

## Questions for the owner

- Q1: is `gap_fill` the right name and shape for the provenance extension, or should the filled
  text carry an inline marker as well?
- Q2: should the scanner run strict on `additional-empty` now (25 files, all candidates) or only
  after the batch adjudication?
- Q3: does the index need to expose `gap_fill` provenance to consumers (MCP `get_law` metadata)?

## This change

- `scripts/structure_gaps.py` and `tests/test_structure_gaps.py` (red first, four tests, self-test).
- `docs/audits/2026-09-05-source-dropped-additional-provisions.md` (results and evidence).
- `docs/cpd/CPD-2026-09-05-dv-gap-fill-additional-provisions.md`: this proposal, marked superseded
  (D-059, D-063).
