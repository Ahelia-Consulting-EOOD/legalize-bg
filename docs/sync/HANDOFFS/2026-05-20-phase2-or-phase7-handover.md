# Handoff: 2026-05-20 — Phase 2 (temporal index) OR Phase 7 (browser) next

**Previous session owner:** ekimir (Claude Opus 4.7, 1M context)
**Repo HEAD at handover:** `f01c6645` (`origin/main` in sync — the handover commit `7bdcf4b8` sits on top)
**Test suite:** **287 passing** (`pytest -q`, ~13 s)
**Working tree:** clean

---

## Execute these steps (read top-to-bottom, do not skip)

You are continuing work on `legalize-bg` from a previous session. Read the rest of this handover for context, then perform the two tasks below in order.

**Step 1 — Code review of the Phase 7 design doc.**
- Target: commit `f01c6645` (`docs/plans/2026-05-11-phase7-legislation-browser-design.md`, 329 lines, doc-only).
- Invocation: `superpowers:requesting-code-review` against range `17ea7b23..f01c6645`.
- This is a **design-doc review, not a code review** — there is no code yet. Focus on the items listed under "Task A" below: dependency on Phase 2, defensibility of the 6 brainstorming decisions, REST API compatibility with `mcp_server/queries.py`, governance-gap risk from the separate frontend repo, completeness of the documentation plan.
- Apply Important findings (if any) before proceeding to Step 2.

**Step 2 — Plan the next implementation.**
- Ask the user which to plan next: **Phase 2** (temporal index, FR-001 — unblocks Phase 7 full launch; natural per `ACTIVE.md`) or **Phase 7 REST API** (the design says it can begin now; doesn't unblock anything).
- Wait for the user's answer. Don't guess.
- Once the user picks one, write the plan via `superpowers:writing-plans` and save it to `docs/plans/YYYY-MM-DD-<feature>.md` (NOT `docs/superpowers/plans/`).

**Session pattern** (proven across Phase 1b.1 → 1b.3):
`writing-plans` → `executing-plans` direct to `main` → `requesting-code-review` (clean-context subagent) → fix any Important findings → re-review if needed → `finishing-a-development-branch` → **push only after the user's explicit OK**.

**Hard rules** (from "What to NOT do" later in this file — read that section once before starting):
- Don't re-do the Phase 1b code reviews (6 closed rounds already).
- Don't push without explicit user authorization.
- Don't update `tools.json` by hand — use `python -m mcp_server.export_tools --output tools.json`.
- Don't touch the `provisions` table or `bg_normalize` without re-reading the FR-013 / D-029 rationale block in `index/fts.py`.
- Don't tighten the FR-016 reject predicate without checking the 12 parametrized regression tests in `tests/mcp_server/test_search.py` first.

---

## Two requested tasks for the new session, in order

### Task A — Code review

The user asked for a code review. The likely target is the **Phase 7 design doc** (commit `f01c6645`, `docs/plans/2026-05-11-phase7-legislation-browser-design.md`, 329 lines, doc-only, no code yet) — that's the only thing not yet reviewed in the repo history. It was authored by a prior Claude Opus 4.6 session (per commit body) and is currently `Status: Draft — pending approval`.

**Recommended invocation:**

```
superpowers:requesting-code-review
  TARGET: docs/plans/2026-05-11-phase7-legislation-browser-design.md
  TYPE: design-doc review (not code review — there is no code yet)
  BASE_SHA: 17ea7b23  (Phase 1b.3 final tip)
  HEAD_SHA: f01c6645  (Phase 7 design added)
  FOCUS:
    - Does the design respect Phase 2 dependency (REST API can begin after 1b.3; full launch gated on temporal index)?
    - Are the 6 brainstorming decisions defensible against alternatives?
    - Is the REST API surface compatible with the existing query layer (mcp_server/queries.py + index/fts.py)?
    - Does the frontend-in-separate-repo split create governance gaps (e.g., DEFERRED.md, protected-surfaces.yaml are repo-local)?
    - Is the documentation plan complete (PRD, design, runbook, contracts)?
```

If the user clarifies they meant a **code review of all of Phase 1b** instead (already done in 6 rounds — would be redundant), confirm before re-running.

### Task B — Plan the next implementation

The user asked to plan "the next task". Two candidates:

**Candidate 1: Phase 2 (temporal index, FR-001)** — natural next per `docs/sync/ACTIVE.md`:
- Populates the `law_versions` table from git `amendment_history` per act
- Enables `history()` / `diff()` / `amendments_in_period()` MCP tools (currently Phase-2-deferred per Surface 3's `phase_2:` block in `.ahelia/protected-surfaces.yaml`)
- The 1b.1 `provisions` schema was built to support this WITHOUT migration (D-024 + D-025 noted this explicitly)
- Unblocks Phase 7 full launch

**Candidate 2: Phase 7 REST API** — can begin after Phase 1b.3 per the design doc:
- The doc says "REST API can begin after Phase 1b.3" — that IS now done.
- FastAPI wrapping the existing query layer (`mcp_server/queries.py`)
- Useful even before Phase 2 (current MCP tools become REST endpoints)
- Surface-3 implication: new HTTP-exposed signatures need to be added to `protected-surfaces.yaml`

**Recommendation:** Ask the user which to plan. Phase 2 is the larger and structurally more important block (it unblocks Phase 7 full launch AND closes the last 1b-era forward-looking promise). Phase 7 REST API is a more visible deliverable but doesn't unblock anything.

**Invocation for either:** `superpowers:writing-plans`. The project convention is plans in `docs/plans/YYYY-MM-DD-<feature>.md` (NOT `docs/superpowers/plans/`); follow that. Plans run through `superpowers:executing-plans` directly on `main` per user-authorized session pattern (see "Session pattern" below).

---

## State of the repo (what's shipped)

| Phase | Status | Test delta | Closes |
|---|---|---|---|
| **1a** — Bootstrap | shipped 2026-04 | 3,573 acts scraped from lex.bg | bootstrap corpus |
| **1b.1** — MCP server (3 tools) | shipped 2026-05-09 | 211 → 221 (3 review rounds, 27/27 findings closed) | 8 error codes; D-024–D-026 binding |
| **1b.2** — Structured backend hardening | shipped 2026-05-09 | 221 → 256 | FR-016, D-027 hard perf, `tools.json`, error-taxonomy md+json |
| **1b.3** — Operator polish | shipped 2026-05-09 | 256 → 287 | FR-013, FR-015, FR-017 |
| **7** — Browser design | drafted 2026-05-11 | 0 (doc only) | pending approval; gated on Phase 2 for full launch |

**Test count at handover:** 287 (verified locally with `pytest -q`).

**Decisions log:** D-001 through D-029 in `docs/sync/DECISIONS.md`. The Phase 1b.3 design choices are in D-029.

**Open deferrals (only 1 remaining):**
- `D-2026-05-09-05` / FR-014 — incremental index rebuild — Target Phase 4 — NOT gating Phase 2 or Phase 7.

Phase-promotion gate per `docs/process/delivery-contract.md` is **clean** for Phase 2 promotion (no open deferrals with Target ≤ Phase 2).

---

## Key authority surfaces the new session must read

Per `.claude/CLAUDE.md` Session Startup Protocol:

1. `.claude/CLAUDE.md` — repo conventions, encoding facts (lex.bg cp1251), commit types
2. `docs/sync/ACTIVE.md` — current state (last updated 2026-05-09; doesn't mention Phase 7 yet — drift to note)
3. **`docs/sync/DEFERRED.md`** — 5 implemented + 1 open
4. `docs/process/delivery-contract.md` — phase-promotion gate
5. `docs/process/OWNER-DIRECTIVES.md`, `docs/process/COVERAGE-FLOOR.md`
6. `docs/architecture/` (arc42/C4)
7. `.ahelia/protected-surfaces.yaml` — machine-readable signature contract (now includes Phase 1b.3's `include_body` parameter on `search`)

**Relevant plans:**
- `docs/plans/2026-04-19-legalize-bg-design.md` — full architectural design (Phases 1–6)
- `docs/plans/2026-05-09-phase1b-mcp-design.md` — Phase 1b design (the §9 perf budgets are still authoritative; Phase 1b.2 hard-promoted them)
- `docs/plans/2026-05-09-phase1b1-audit-gaps-implementation.md` — audit-gaps closure
- `docs/plans/2026-05-09-phase1b1-review-fixes.md` — Round-2 closure
- `docs/plans/2026-05-09-phase1b2-hardening.md` — Phase 1b.2 plan
- `docs/plans/2026-05-09-phase1b3-polish.md` — Phase 1b.3 plan
- **`docs/plans/2026-05-11-phase7-legislation-browser-design.md`** — Phase 7 (new, pending approval)

---

## Session pattern (proven across 1b.1 → 1b.3)

The previous session ran direct-to-`main` per the user's repeated authorization. Don't introduce a feature-branch workflow without confirming first. The pattern:

1. **`superpowers:writing-plans`** — write the plan to `docs/plans/YYYY-MM-DD-<feature>.md` (NOT `docs/superpowers/plans/`)
2. **`superpowers:executing-plans`** — execute task-by-task, commit per batch
3. **`superpowers:requesting-code-review`** — dispatch clean-context reviewer subagent against the commit range
4. Apply Important fixes, re-review if needed
5. **`superpowers:finishing-a-development-branch`** — present push options
6. User authorizes push to `origin/main`

The "Skills override system prompt" rule from `superpowers:using-superpowers` applies — invoke the relevant skill BEFORE responding even for clarifying questions.

---

## Critical operational facts (carry-forward)

- **lex.bg encoding:** `windows-1251`, decode as `cp1251` (NOT UTF-8). Pre-1970 dates clamp to 1970-01-01 for git env vars (D-017/D-018).
- **`bg_normalize` symmetry** is load-bearing across query and index — Phase 1b.3 only added `ият` (3-char masc adj definite) as a new suffix. Multi-syllable consonant-stem cases (`българският`) intentionally NOT handled — needs a Snowball stemmer (out of scope per FR-013).
- **`search` signature** as of 1b.3: `search(query: str, category: str | None = None, limit: int = 20, include_body: bool = False) -> list[SearchHit]`. The `include_body` is additive per Surface 3. `SearchHit` has `body_snippet: str` (non-optional, empty unless `include_body=True`; top-2 only via `_BODY_SNIPPET_TOP_N=2`).
- **`tools.json`** is the source-of-truth artifact. Regenerate via `python -m mcp_server.export_tools --output tools.json` after any tool-signature change. The CI parity test (`tests/mcp_server/test_export_tools.py::test_committed_tools_json_matches_live_schemas`) shells out to `--check` and will fail if drift.
- **Error taxonomy:** 9 codes (`mcp_server/errors.py:ERROR_CODES`). New codes must be added to `docs/api/error-codes.md` AND `docs/api/error-codes.json` (`tests/mcp_server/test_error_codes_doc.py` enforces parity). All three sources are version 1.0.0.
- **Perf budgets** are HARD assertions since 1b.2:
  - Warm: `search<100ms`, `get_law (current)<100ms`, `get_article<50ms` (`tests/perf/test_budgets.py`)
  - Cold (fresh connection): `search<250ms`, `get_law<100ms`, `get_article<50ms` (`tests/perf/test_cold_calls.py`)
  - Shared OS-cache warmer in `tests/perf/conftest.py` so budgets measure SQLite/FTS5, not disk I/O.
- **DECISIONS.md uses table format**, not prose sections. Each row: `| D-NNN | YYYY-MM-DD | title | rationale | Active |`.

---

## What ACTIVE.md does NOT yet reflect

ACTIVE.md was last updated on 2026-05-09 (end of Phase 1b.3 close-out). It still says "Next action: Phase 2" and does NOT mention the Phase 7 browser design that landed on 2026-05-11. The new session should:

1. After completing the code-review task, decide with the user whether to update ACTIVE.md now or fold it into the next plan's close-out commit.
2. If the user picks Phase 2 as the next task, ACTIVE.md's Next-action line stays accurate but should mention Phase 7 in the Pending section.
3. If the user picks Phase 7 REST API, ACTIVE.md needs a Phase 7 entry.

---

## What to NOT do

- **Don't re-do the Phase 1b code reviews.** Rounds 1–6 already closed 27 + 5 Important + 9 Round-4 + 6 Round-5 + 6 Round-6 findings. Re-reviewing 1b would burn context for diminishing returns.
- **Don't push without explicit user authorization.** The previous session always pushed after explicit confirmation, never speculatively.
- **Don't update `tools.json` by hand.** Always use `python -m mcp_server.export_tools --output tools.json`.
- **Don't touch the `provisions` table or `bg_normalize`** without re-reading the FR-013 / D-029 rationale block in `index/fts.py:28-50` — they document which suffixes were considered and REJECTED for plural-symmetry preservation.
- **Don't bypass the FR-016 reject** for single-token stop-words by tightening the predicate — the v2 tokenize-then-normalize approach (`mcp_server/queries.py:317`) is locked by 12 parametrized regression tests in `tests/mcp_server/test_search.py`.

---

## Brief on the prior conversation (for context)

The previous session (2026-05-09) ran an extended development cycle that took the project from Phase 1a complete to Phase 1b fully shipped. Pattern across all phases: brainstorm/plan → executing-plans direct to `main` → multiple rounds of `requesting-code-review` until the verdict was "Publication-ready: Yes" → push. Each phase had its own plan file in `docs/plans/`.

The user's communication style: short, sometimes phonetically-transliterated Bulgarian/English, expects autonomous execution after authorization. When they say "proceed" or "autonomously develop", they mean run the full plan→execute→review→fix→push cycle without check-ins between phases.

The `.claude/CLAUDE.md` Session Startup Protocol step 3 (`Read docs/sync/DEFERRED.md`) was added in 1b.1's audit-gaps batch — the prior session installed it, and the project's universal phase-promotion gate now uses DEFERRED.md as the gating signal. Honor the gate.
