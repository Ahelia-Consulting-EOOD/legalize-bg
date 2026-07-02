# Handover: FR-028 REST API Plan — Execution Session (2026-07-02)

**From:** the pre-UI-hardening execution session of 2026-07-02 (which shipped all 18 hardening tasks and then wrote this plan on the owner's instruction).
**To:** the next session, whose ONLY job is to EXECUTE `docs/plans/2026-07-02-fr028-rest-api-plan.md` task-by-task via **superpowers:subagent-driven-development** (fresh subagent per task, review between tasks).
**Owner intent:** run this session on a CHEAPER model to spare Fable capacity — see §7 Model policy. The plan was written to be executable without judgment calls: every endpoint carries complete code, every kwarg was verified against the live signatures on 2026-07-02, every ambiguity has a stated decision rule.

---

## §1 Kickoff prompt (paste as the first user message)

> Execute `docs/plans/2026-07-02-fr028-rest-api-plan.md` with subagent-driven development (fresh subagent per task, review between tasks). Read `docs/sync/HANDOFFS/2026-07-02-fr028-rest-api-execution-handover.md` §2–§7 first for operational traps and the model policy. Work directly on `main` (established convention). Stop for me only before the first `git push` (Task 8 Step 6 — one authorization covers Task 9's push too).

## §2 What to read (in order, before dispatching anything)

1. `docs/plans/2026-07-02-fr028-rest-api-plan.md` — THE plan. 9 tasks, strict order 1→9. Subagents get NO context you don't embed — hand each its task brief (`task-brief` script) + §3 of this handover.
2. `docs/plans/2026-05-11-phase7-legislation-browser-design.md` — the approved design (for YOUR review judgment; subagents don't need it — the plan already encodes it).
3. `docs/sync/DECISIONS.md` D-050 (scope) and D-051 (perf/pragmas) rows.

## §3 Operational facts every subagent prompt MUST carry

- **Interpreter:** NO system `python`/`pytest` on PATH. Always `.venv/bin/python -m pytest ...` from repo root `/Users/ekimir/swprj/legalize-bg`.
- **Suite baseline:** `.venv/bin/python -m pytest -q -m "not perf"` = **478 passed, 7 deselected** (green at handover). Must stay green after every task. NEVER run `tests/perf` (D-051 budgets are machine-sensitive and locked).
- **catalog.db:** 1.2 GB, gitignored, 3,601 acts, at HEAD — READ-ONLY for this plan; never rebuild.
- **Corpus `.md` files are data** — never modified. Bulgarian text in code/tests: UTF-8 literals.
- **tools.json is frozen at 1.3.0** — this plan must not touch `mcp_server/export_tools.py`, `tools.json`, or MCP tool docstrings (the export embeds docstrings — even a "helpful" docstring edit breaks `--check` in CI).
- **HARD RULE for implementers:** an existing-test failure means BLOCKED-with-output, never a test/fixture edit. (One exception is pre-declared in the plan: none — this plan expects zero existing-test churn.)
- **Push policy:** ask the owner ONCE at Task 8 Step 6; that authorization covers Task 9. Branch only, never tags (a DRS consumer triggers on tags).
- Commit messages are given verbatim per task — if a task's content deviates from its planned message (an experiment dropped, a file skipped), FIX THE MESSAGE to describe reality before committing (lesson from hardening Task 13).

## §4 Traps discovered while planning (not fully visible in the plan text)

- **Task 2 is the only task that touches `mcp_server/server.py`** — a 4-helper relocation with an aliased import. The whole point is a zero-behavior-change diff; the ~190-test mcp suite is the proof. If the relocated helpers reference any OTHER server.py-private name, the implementer must BLOCK, not chain-relocate.
- **Per-request `mode=ro` connections need a FILE db** — `:memory:` cannot be reopened per request. The plan's `tests/api/conftest.py` builds a real corpus + catalog file (module-scoped) for exactly this reason. Don't let an implementer "simplify" to :memory: or to a shared connection.
- **`check_same_thread=False` in `api/deps.py` is load-bearing:** FastAPI runs sync dependencies and sync endpoints on potentially different threadpool threads. Removing it makes tests pass flakily and production fail.
- **Task 5's composition mirrors `mcp_server/server.py`'s get_law/get_article bodies — server.py is NORMATIVE.** The plan's code was transcribed from it on 2026-07-02; if they diverge at execution time, server.py wins and the diff goes in the report.
- **Task 9's runbook edit can break the runbook PARITY TEST:** the tool-table regex `^\|\s*\`(\w+)\`` matches ANY backticked word-char first column. Endpoint rows must NOT backtick a bare word (write `| GET /api/v1/laws |`, never `| \`GET\` ... |`). Run `tests/mcp_server/test_runbook_parity.py` after the runbook edit.
- **OpenAPI export determinism (Task 8):** the parity test does an exact byte comparison; the exporter serializes with `sort_keys=True` + trailing newline. If FastAPI version drift ever reorders the spec, regenerate with `--output` — never hand-edit `docs/api/openapi-rest.json`.
- **DECISIONS.md is a single-line-per-row table** — the D-052 row (Task 9) must be ONE line appended after D-051, same column count. FRS INDEX: only FR-028's row changes.
- **CI wiring (Task 8) changes the install line to `.[dev,api]`** in BOTH jobs' contexts (test job install; smoke job `pip install ".[api]"`). Miss one and CI fails on ModuleNotFoundError — that's a fix-forward `ci:` commit, max 3, then BLOCKED.
- **Suite-count arithmetic in the plan is an expectation, not a gate.** The gate is "green". If a count differs by ±1–2 because pytest collected differently, report the actual number; don't chase the prediction.

## §5 State at handover

- `main` @ `a195b54b` = origin/main, CI green (runs 28567395399 / 28568247547). Working tree clean.
- The hardening session's ledger (`.superpowers/sdd/progress.md`, git-ignored) documents all 18 prior tasks; start a fresh ledger section for FR-028 per the SDD skill.
- fastapi/uvicorn NOT yet installed (Task 1 installs them); httpx 0.28.1 already present via fastmcp.
- FR-028 row in `docs/frs/INDEX.md` says "Planned — plan ready"; ACTIVE.md next action points at executing this plan.

## §6 Definition of done

All 9 task checklists ticked; suite green (expected ~508 non-perf, 7 deselected); `api.export_openapi --check` OK; `mcp_server.export_tools --check` still OK at 1.3.0 (untouched); Task 9 live smoke against the real catalog passes verbatim; CI green after the owner-authorized push; D-052 + FR-028→Done + ACTIVE.md next-action (Phase 7.2 frontend) committed. Then the next track is Phase 7.2 in the `legalize-bg-web` sister repo.

## §7 Model policy (owner-requested evaluation, 2026-07-02)

**Run the orchestrator session on Sonnet 5 — not Opus 4.8.** Rationale:

1. **Empirical:** the 18-task hardening plan was executed with ALL implementers and reviewers on Sonnet 5 (a few pure-transcription tasks on Haiku 4.5) under a Fable orchestrator. Every real defect — including an implementer masking a regression by regenerating golden fixtures — was caught by a Sonnet 5 reviewer. The heavy lifting is in the plan + the review loop, not the orchestrator's raw intelligence.
2. **Generation beats tier here:** Sonnet 5 is the newer (Claude 5) generation; Opus 4.8 is the prior-generation flagship at a materially higher price and latency. For executing a fully-specified plan (complete code, pinned kwargs, decision rules), Sonnet 5 is at least Opus 4.8's equal, at a fraction of the cost — which is the owner's stated objective.
3. **This plan is tighter than the hardening plan:** every endpoint ships as complete code verified against live signatures; the two spots where reality could drift carry explicit "X is normative, report the diff" rules.

**Dispatch policy inside the session:**
- Implementers: **Haiku 4.5** for Tasks 1, 4, 7 (near-pure transcription); **Sonnet 5** for Tasks 2, 3, 5, 6, 8, 9.
- Task reviewers: **Sonnet 5** with named risks per task (copy the hardening session's pattern).
- Final whole-branch review: **Sonnet 5** is acceptable for this scope; use Opus 4.8 only if the owner wants a second opinion.
- **Escalation valve:** if a task returns BLOCKED twice on the same blocker, or a reviewer and implementer deadlock on a correctness question, re-dispatch that ONE task on Opus 4.8 — or park it for the owner. Do not silently continue past an unresolved correctness dispute.
