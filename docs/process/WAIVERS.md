# Waivers

Dated, owner-signed exceptions to `docs/process/OWNER-DIRECTIVES.md` and to the floors in
`docs/process/COVERAGE-FLOOR.md`. A waiver names the directive or floor element it suspends, the
exact acts or surfaces it covers (enumerated, never described), the reason, the expiry condition,
and the owner's signature date. Report-only gates need a waiver here (Directive 12); a class with a
non-zero violation count is closed only if every remaining instance is listed here (correctness
floor, acceptance rule 3).

The enumerated per-act exception sets that the corpus-integrity checks consume live in
`docs/data/waivers.yaml` (PR #23 Part II Task 2) and are reconciled by equality on every run; this
file records the rulings that create them.

| ID | Date | Directive or floor element | Scope (enumerated) | Reason | Expiry condition | Owner |
|---|---|---|---|---|---|---|
