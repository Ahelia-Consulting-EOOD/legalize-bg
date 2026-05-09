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
| D-2026-05-09-05 | Incremental index rebuild (currently full DELETE-then-INSERT each time, ~45 s for 3,573 acts) | Phase 1b.1 | Phase 4 | Open | 2026-05-09 (filed) | [FR-014](../frs/INDEX.md) |

## Resolved deferrals

| ID | Title | Punted from | Target | Status | Last reviewed | FR / Decision | Resolution note |
|---|---|---|---|---|---|---|---|
| D-2026-05-09-03 | Single-word category queries (`наредба`) overrun the 100 ms p95 search budget | Phase 1b.1 | Phase 1b.2 | Implemented | 2026-05-09 | [FR-016](../frs/INDEX.md) | Stop-word reject path in `mcp_server/queries.py:full_text_search` raises new `QUERY_TOO_BROAD` error before FTS5; closed in Phase 1b.2 hardening plan. See [D-028](DECISIONS.md). |
| D-2026-05-09-06 | Soft perf assertions (`tests/perf/test_budgets.py` logs warnings, doesn't fail) — promote to hard | Phase 1b.1 | Phase 1b.2 | Implemented | 2026-05-09 | [D-027](DECISIONS.md) | `_soft_assert` → `_hard_assert` in `tests/perf/test_budgets.py`; new `tests/perf/test_cold_calls.py` adds first-user-hit coverage. See [D-028](DECISIONS.md). |
| D-2026-05-09-01 | `bg_normalize` last-character-only suffix stripping (adjective long-form definite article asymmetry) | Phase 1b.1 | Phase 1b.3 | Implemented | 2026-05-09 | [FR-013](../frs/INDEX.md) | Per-suffix MIN_STEM_LEN model in `index/fts.py:_BG_DEFINITE_SUFFIXES`; new 3-char `ият` suffix at MIN_STEM=3 closes the canonical `новият/нов` asymmetry. Other long-form suffixes (`ите`, `ия`) deliberately NOT added — they would conflict with plural-noun endings. See [D-029](DECISIONS.md). |
| D-2026-05-09-02 | `search` returns `title_snippet` only (no body snippet) | Phase 1b.1 | Phase 1b.3 | Implemented | 2026-05-09 | [FR-017](../frs/INDEX.md) | Python-side body-snippet generator in `mcp_server/queries.py:_make_body_snippet`; opt-in via `include_body=True` parameter on `search` (TOP_N=2 cap). New `body_snippet` field on `SearchHit` (additive per Surface 3). See [D-029](DECISIONS.md). |
| D-2026-05-09-04 | Synonym dictionary for Bulgarian abbreviations and `rang`-aware re-ranking | Phase 1b.1 | Phase 1b.3 | Implemented | 2026-05-09 | [FR-015](../frs/INDEX.md) | Two layers: hand-curated `index/synonyms.LEGAL_ABBREVIATIONS` (22 entries) rewrites single-token queries pre-FTS5; rang-aware tier sort in `index/fts.py:search_fts` puts laws/codes above implementing/regulations/ordinances. See [D-029](DECISIONS.md). |

> **Row schema for resolved entries.** When an Open row is resolved at a phase boundary it migrates here with the same columns; only the values change. The `Status` column flips from `Open` to one of `Implemented` / `Re-affirmed` / `Withdrawn`; `Last reviewed` becomes the resolution date; an extra column "Resolution note" carries a one-sentence explanation and a link to the closing `DECISIONS.md` entry.

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
