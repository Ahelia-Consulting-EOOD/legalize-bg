# Waivers

Dated, owner-signed exceptions to `docs/process/OWNER-DIRECTIVES.md` and to the floors in
`docs/process/COVERAGE-FLOOR.md`. A waiver names the directive or floor element it suspends, the
exact acts or surfaces it covers (enumerated, never described), the reason, the expiry condition,
and the owner's signature date. Report-only gates need a waiver here (Directive 12); a class with a
non-zero violation count is closed only if every remaining instance is listed here (correctness
floor, acceptance rule 3).

The enumerated per-act exception sets that the corpus-integrity checks consume will live in
`docs/data/waivers.yaml` once PR #23 Part II lands, reconciled by equality on every run; this file
records the rulings that create them.

| ID | Date | Directive or floor element | Scope (enumerated) | Reason | Expiry condition | Owner |
|---|---|---|---|---|---|---|
| W-001 | 2026-09-05 | Directive 12 (gates block or they do not exist) | `fetcher/bg/coverage.py:structure_mismatches`, the structural paragraph-topology gate, in REPORT mode since 2026-08-04 (D-058 e); 51 acts in the structure-mismatch census, families A/B/C/D (`docs/research/2026-08-02-fr034-sweep-report.md` §10) | Flipping the gate strict on an unmeasured corpus would hard-fail 51 acts for defects owned by FR-035, FR-030/FR-037 and FR-026, blocking the very sweep that cleans them | Hard-fail flip once families A, C and D of the census are adjudicated (PR #23 phases 2, 3 and 6) | ekimir, ratified by the merge of PR #25 |
