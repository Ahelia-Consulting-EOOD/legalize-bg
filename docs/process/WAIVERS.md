# Waivers

Dated, owner-signed exceptions to `docs/process/OWNER-DIRECTIVES.md` and to the floors in
`docs/process/COVERAGE-FLOOR.md`. A waiver names the directive or floor element it suspends, the
exact acts or surfaces it covers (enumerated, never described), the reason, the expiry condition,
and the owner's signature date. Report-only gates need a waiver here (Directive 12); a class with a
non-zero violation count is closed only if every remaining instance is listed here (correctness
floor, acceptance rule 3).

The enumerated per-act exception sets that the corpus-integrity checks consume live in
`docs/data/waivers.yaml`, reconciled by equality on every run; this file records the rulings that
create them. Equality there is equality on the **count**: each waived act carries the exact number
of violations its census found, so a new violation in a waived act is reported as an excess, a
partial repair is reported as count drift, and a full repair is reported as a stale waiver. All
three fail the run, so a waiver is a pinned census and never a blind spot.

| ID | Date | Directive or floor element | Scope (enumerated) | Reason | Expiry condition | Owner |
|---|---|---|---|---|---|---|
| W-001 | 2026-09-05 | Directive 12 (gates block or they do not exist) | `fetcher/bg/coverage.py:structure_mismatches`, the structural paragraph-topology gate, in REPORT mode since 2026-08-04 (D-058 e); 51 acts in the structure-mismatch census, families A/B/C/D (`docs/research/2026-08-02-fr034-sweep-report.md` §10) | Flipping the gate strict on an unmeasured corpus would hard-fail 51 acts for defects owned by FR-035, FR-030/FR-037 and FR-026, blocking the very sweep that cleans them | Hard-fail flip once families A, C and D of the census are adjudicated (PR #23 phases 2, 3 and 6) | ekimir; takes effect on the merge of PR #25, whose merge date is the signature date |
| W-002 | 2026-09-05 | Correctness floor, acceptance rule 3 (a non-zero class is closed only on a dated owner-signed waiver enumerating the exact acts), for the corpus-integrity `tag_remnants` gate | The 80 acts and their per-act occurrence counts enumerated under `tag_remnants` in `docs/data/waivers.yaml`; census of 2026-09-05 over the committed corpus, 771 occurrences over 80 acts (`SUP>` 190 over 36 acts, `/span>` 577 over 47, `/STRONG>` 4 over 1), generated from `python -m corpus_integrity --check tag_remnants --enumerate` and never hand-typed | FR-035 is a parser defect: the fix lands in `fetcher/bg/text_parser.py` and the corpus is repaired by the single Part V sweep that Directive 14 mandates. Failing the gate on all 80 acts before that sweep would make the required check permanently red, which under Directive 12 is the state in which a gate stops being read | The Part V repair sweep (PR #23 phase 7); each act is removed from `waivers.yaml` as it is repaired, and the counts make a partial repair fail the run until the file is updated | ekimir; takes effect on the merge of PR #34, whose merge date is the signature date |
| W-003 | 2026-09-05 | Correctness floor, acceptance rule 3, for the corpus-integrity `chrome` gate | The one act enumerated under `chrome` in `docs/data/waivers.yaml`, `ordinances/naredba-5-ot-10-may-1999-g-za-strukturata-na-zapisa-v-tsifrov-vid-na-kadastralni`, with its pinned count of 2; census of 2026-09-05 over the committed corpus | FR-036 is a fetcher defect: the lex.bg sidebar must be excluded from the content region in `fetcher/bg/text_parser.py` and the act re-fetched. The two marker lines are the detectable trace of a roughly 60-line sidebar block, so deleting them is not the repair; only the re-fetch is | The re-fetch of the act with the sidebar excluded, in the Part V repair sweep (PR #23 phase 7) | ekimir; takes effect on the merge of PR #34, whose merge date is the signature date |
