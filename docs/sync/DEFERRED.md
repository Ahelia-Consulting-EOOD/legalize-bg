# Deferred Items

Items punted from a completed phase that need explicit revisit at phase boundaries. **Distinct from `docs/frs/INDEX.md`**, which is the broader future-work register including always-scheduled items (e.g., FR-001 was always Phase 2; it's not a deferral).

This file is read at session startup per the protocol in `.claude/CLAUDE.md`. Phase entry conditions in `docs/process/delivery-contract.md` require reviewing every row before promoting a phase.

## Format

Each row links the deferral to its FR (or DECISION) trace, the phase it was punted FROM, and the phase it's targeted FOR. Status column is one of:

- **Open** — deferral active, not yet revisited.
- **Re-affirmed** — explicitly reviewed at a phase boundary, kept deferred (date stamped). Re-affirmation requires a new `docs/sync/DECISIONS.md` entry stating why.
- **Implemented** — closed; FR row in `docs/frs/INDEX.md` updated to status "Done"; the row migrates to the "Resolved deferrals" section below.
- **Withdrawn** — decided not to do this work at all; rationale recorded in `docs/sync/DECISIONS.md`; the FR row in INDEX.md gets Status=Withdrawn too.

## Active deferrals

| ID | Title | Punted from | Target | Status | Last reviewed | FR / Decision |
|---|---|---|---|---|---|---|
| D-2026-05-09-01 | `bg_normalize` last-character-only suffix stripping (adjective long-form definite article asymmetry) | Phase 1b.1 | Phase 1b.3 | Open | 2026-05-09 (filed) | [FR-013](../frs/INDEX.md) |
| D-2026-05-09-02 | `search` returns `title_snippet` only (no body snippet) | Phase 1b.1 | Phase 1b.3 | Open | 2026-05-09 (filed) | [FR-017](../frs/INDEX.md) |
| D-2026-05-09-03 | Single-word category queries (`наредба`) overrun the 100 ms p95 search budget | Phase 1b.1 | Phase 1b.2 | Open | 2026-05-09 (filed) | [FR-016](../frs/INDEX.md) |
| D-2026-05-09-04 | Synonym dictionary for Bulgarian abbreviations (ЗОП ↔ Закон за обществените поръчки) and `rang`-aware re-ranking | Phase 1b.1 | Phase 1b.3 | Open | 2026-05-09 (filed) | [FR-015](../frs/INDEX.md) |
| D-2026-05-09-05 | Incremental index rebuild (currently full DELETE-then-INSERT each time, ~45 s for 3,573 acts) | Phase 1b.1 | Phase 4 | Open | 2026-05-09 (filed) | [FR-014](../frs/INDEX.md) |
| D-2026-05-09-06 | Soft perf assertions (`tests/perf/test_budgets.py` logs warnings, doesn't fail) — promote to hard | Phase 1b.1 | Phase 1b.2 | Open | 2026-05-09 (filed) | [D-027](DECISIONS.md) |

## Resolved deferrals

(empty — Phase 1b.1 is the first phase to register deferrals in this file.)

> **Row schema for resolved entries.** When an Open row is resolved at a phase boundary it migrates here with the same columns; only the values change. The `Status` column flips from `Open` to one of `Implemented` / `Re-affirmed` / `Withdrawn`; `Last reviewed` becomes the resolution date; an extra column "Resolution note" can be added inline with a one-sentence explanation and a link to the closing `DECISIONS.md` entry. Example row format (kept as a template, not an actual deferral):
>
> | ID | Title | Punted from | Target | Status | Last reviewed | FR / Decision | Resolution note |
> |---|---|---|---|---|---|---|---|
> | D-YYYY-MM-DD-NN | _example title_ | _from-phase_ | _target-phase_ | Implemented | YYYY-MM-DD | [FR-NNN](../frs/INDEX.md) | _One-sentence resolution; link to_ [_DECISIONS.md_](DECISIONS.md) _entry._ |

## Phase-boundary review protocol

Before promoting from Phase X to Phase Y, the human reviews every Open row whose Target column is X (or earlier). For each:

1. **Implement** — do the work; mark Status=Implemented; update the FR row in `docs/frs/INDEX.md` to Done; move the row to "Resolved deferrals"; commit.
2. **Re-affirm** — explicitly choose to keep deferred for documented reasons; update `Last reviewed`; optionally bump `Target` to a later phase. The re-affirmation rationale goes into a new `DECISIONS.md` entry.
3. **Withdraw** — decide not to do this work at all; mark Status=Withdrawn in this file AND in the FR row; new `DECISIONS.md` entry explaining why.

**Phase promotion is blocked** while any Open row in this file has Target ≤ X.

## Process notes

- **ID format:** `D-YYYY-MM-DD-NN` — D for deferral, audit/origin date, sequence within that day. Independent from FR numbering: an item has both a deferral ID (here) and an FR ID (in `frs/INDEX.md`). The two life-cycles are distinct — an item can have an FR but no deferral (FR-001 was always Phase 2, never punted), and conceivably the reverse (a deferral filed before its FR is named).
- **New deferrals** get added at the bottom of the Active table, not interleaved with existing rows. Resolved items move to "Resolved deferrals" with a final `Last reviewed` date.
- **Mirror in `.ahelia/protected-surfaces.yaml`** — the `deferrals:` block there is the machine-readable form of this file, used by future CI / pre-commit hooks to flag changes touching code surfaces with an open deferral against them. Source of truth stays here; the YAML is regenerated when this file changes.
- **Session-startup integration** — the protocol in `.claude/CLAUDE.md` lists this file in the read path; sessions should glance at it for phase-relevant Open rows before starting work.
