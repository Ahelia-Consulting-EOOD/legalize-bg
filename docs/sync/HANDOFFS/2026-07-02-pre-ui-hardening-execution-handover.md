# Handover: Pre-UI Hardening Plan — Execution Session (2026-07-02)

**From:** planning session of 2026-07-02 (orientation → comprehensive code review → plan; D-050).
**To:** the next session, whose ONLY job is to EXECUTE `docs/plans/2026-07-02-pre-ui-hardening-plan.md` task-by-task via **superpowers:subagent-driven-development** (owner-chosen mode: fresh subagent per task, orchestrator reviews between tasks).

---

## §1 Kickoff prompt (paste as the first user message)

> Execute `docs/plans/2026-07-02-pre-ui-hardening-plan.md` with subagent-driven development (fresh subagent per task, review between tasks). Read this handover (`docs/sync/HANDOFFS/2026-07-02-pre-ui-hardening-execution-handover.md`) §2–§6 first for operational traps. Work directly on `main` (established convention). Stop for me only at Task 14 Step 1 (FR-027 perf option ratification → D-051) and before any `git push` (Task 15 needs one — ask first).

## §2 What to read (in order, before dispatching anything)

1. `docs/plans/2026-07-02-pre-ui-hardening-plan.md` — THE plan. 18 tasks; recommended order 1→18 (batches A→B→E→C→D). Each task is self-contained with code, but subagents get NO context you don't embed — copy the task text verbatim into each subagent prompt, plus §3 of this handover.
2. `docs/research/2026-07-02-pre-ui-code-review.md` — the verified findings the plan remediates (for your review judgment between tasks, not for the subagents).
3. `docs/sync/DECISIONS.md` D-050 — the ratified scope decisions (what's in, what's parked, why).

## §3 Operational facts every subagent prompt MUST carry

- **Interpreter:** there is NO system `python`/`pytest` on PATH. Always `.venv/bin/python -m pytest ...` / `.venv/bin/python -m ...` from the repo root `/Users/ekimir/swprj/legalize-bg`.
- **Suite baseline:** `.venv/bin/python -m pytest -q --ignore=tests/perf` = **437 passed, ~34 s** (green at handover). It must stay green after every task.
- **Live catalog:** `catalog.db` at repo root, **1.2 GB**, gitignored, currently at HEAD. Full rebuild ≈ 40 s (`.venv/bin/python -m index.build --corpus . --db catalog.db`). Tasks 2/3/4 change what a rebuild produces — the plan batches ONE rebuild in Task 4 Step 5.
- **Bulgarian text in code/tests:** UTF-8 literals, never escaped sequences.
- **Commit style:** conventional commits for pipeline code (each task ends with its own commit — messages are given in the plan). No corpus-format (`[reforma]`-style) commits anywhere in this plan; the single corpus file move (Task 3 Step 1) uses the conventional message given there.
- **Protected surfaces:** Batch B's contract deltas are covered by ONE preflight doc the plan creates (Task 5 Step 1). Nothing else in the plan touches a protected surface — if a subagent's fix wants to (e.g. SQLite schema in Batch C option (b)), that's a STOP-and-report, not a do.

## §4 Traps discovered while planning (not fully visible in the plan text)

- **Perf measurements need a QUIET machine.** This session initially measured perf failures at 14× while 4 review agents were hammering the disk; the clean re-run still failed at 12× (that's why FR-027 exists). For Tasks 12–14: no parallel subagents running, nothing else heavy on the machine, or the numbers are garbage. Run perf probes/tests from the orchestrator (sequentially), NOT inside a parallel-dispatch phase.
- **Tasks 10 and 11 test bodies are deliberately contract-only.** The refresh test modules (`tests/refresh/test_gate.py`, `test_orchestrator.py`) have an existing fake-`_fetch_assemble` harness; the subagent must READ those modules and complete the test bodies against the real fixture names. Same for `tests/fetcher/bg/test_client.py`'s fake-response helper (actual name may differ from `_FakeResponse` — mirror what's there). The assertions listed in the plan are the contract; inventing new harnesses instead of reusing the module's is a review-reject.
- **Task 5 (ToolError → JSON message):** some existing tests may assert the old `"CODE: {...}"` message format via `str(e)` — the plan says update them to `json.loads(str(e))["code"]`. Watch `tests/mcp_server/test_errors.py` specifically. `.code`/`.payload`/`to_dict()` semantics are unchanged.
- **Task 6:** FTS5 user-input `sqlite3.OperationalError`s are ALREADY suppressed inside `index/fts.py:_run_match` and `queries.resolve_name_to_law_id` — the new `_register`-level INDEX_MISSING mapping must key on catalog-level markers only (list in the plan). Don't let a subagent "simplify" to catch-all.
- **Task 8 (TypedDict output schemas):** FastMCP will VALIDATE returns against the schema. The plan's Step 5 live smoke is mandatory; the contingency (loosen the specific offending field to the observed union, note in preflight) is the only allowed fallback — never disable validation. `dv_year`/`dv_issue` are prime suspects for type variance in live frontmatter.
- **Task 8 order:** it regenerates `tools.json` (1.3.0) and must land AFTER Tasks 5–7 (their `ERROR_CODES` additions feed the same file). The plan already orders it last in Batch B — keep it that way if re-ordering anything else.
- **Task 15 (CI) requires `git push`** for the workflow to run — the push policy is explicit-owner-authorization. Ask before pushing; the plan's `gh run watch` step assumes the push happened.
- **Task 14 is an OWNER CHECKPOINT** (perf option (a)/(b)/(c) ratification → D-051 + budget re-lock). Do not let a subagent pick the option; the orchestrator presents the measured numbers and waits.
- **Edit-tool discipline for governance files:** `docs/sync/DECISIONS.md` is a 49-line single-line-per-row table (append after D-050); `docs/frs/INDEX.md` rows FR-026..029 already exist (added at planning) — Task 18 only flips FR-027's status.

## §5 State at handover

- `main` @ `371a8e48` (planning commits `87509f8d` + `371a8e48` local, **NOT pushed** — origin is at `b3b3d3d7`). Working tree clean.
- Governance already done at planning time (do NOT redo): D-050 row; FR-026 (reserved) / FR-027 / FR-028 / FR-029 rows; ACTIVE.md banner + next-action. The plan's Task 18 handles only the CLOSE-OUT updates (statuses, D-050 outcome note, D-051 cross-refs).
- Review agents' full raw reports live only in the planning-session transcript; everything load-bearing was verified and captured in the review doc — treat `docs/research/2026-07-02-pre-ui-code-review.md` as the authoritative findings record.
- Nothing running in the background. `catalog.db` fresh at HEAD. Perf suite currently FAILS deterministically (expected — that's FR-027; it becomes green at Task 14).

## §6 Definition of done for the execution session

All 18 task checklists ticked; Task 18 gates pass verbatim (`-m "not perf"` suite green; perf suite 6/6 green on ratified D-051 budgets on a quiet machine; `export_tools --check` OK at 1.3.0; CI green after owner-authorized push; the seven-tool live smoke + the Task-2 truncation spot-check pass); governance close-out committed. Then the next-next action per ACTIVE.md: **write the FR-028 REST API plan** (design: `docs/plans/2026-05-11-phase7-legislation-browser-design.md`) — planning only, fresh brainstorm not needed (design approved), but its Surface preflight is.
