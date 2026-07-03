# Handover: FR-028 close-out + global MCP install + УПЗНА capture + FR-031 design (2026-07-04)

**From:** the session that merged FR-028 (REST API), captured УПЗНА, installed the global MCP server, and designed FR-031 (remote transport).
**To:** the next session. No single mandatory next task — this handover is a clean-slate status report plus three ranked options (§6).

---

## §1 State at handover

- `origin/main` = **`8c774b7c`**. Local `main` = **`6ad77692`** — **one commit ahead, NOT pushed** (`docs(frs): register FR-031 remote MCP transport + design doc`; docs-only, adds `docs/plans/2026-07-03-remote-mcp-transport-design.md` + a FRS row — zero code/schema/corpus impact). Plus this handover + the ACTIVE.md edit you're reading now, also uncommitted at the moment this section was written — see §7 for the exact sequencing.
- Full commit sequence this session (oldest→newest): `f1acce76`..`fd6d0e36` (FR-028's 9 plan tasks + fix loops, merged via PR #9 → `c4f4f454`) → `eca540d7` (`[nova]` УПЗНА corpus commit) → `8c774b7c` (D-049 addendum + ACTIVE.md, **pushed**) → `6ad77692` (FR-031 design doc + FRS registration, **not pushed**).
- Suite: **518 passed, 7 deselected** (`-m "not perf"`). Perf suite **re-verified green** this session (`tests/perf/test_warm_persistent.py` — see §3, was a real but transient miss, not a regression).
- `catalog.db`: 3,602 acts, indexed at `eca540d7` (the last commit that touched corpus data; the two docs-only commits after it don't require a reindex — confirmed current).
- CI: green on every push this session (`gh run list --branch main` — 3/3 runs `completed success`).

## §2 What shipped this session (chronological)

1. **FR-028 REST API (Phase 7.1)** — 9-task plan executed via subagent-driven-development, one real bug caught in task review (Task 5: `get_article` validated the article-spec range check in the wrong order relative to date resolution — fixed, regression-tested), a whole-branch review (2 Important + 5 Minor, fixed in one batch), then — at the user's explicit request — an **independent Fable 5 comprehensive review** that found 2 MORE Important issues three same-family (implementation-model) review passes had missed entirely: `INDEX_MISSING` (503) was mapped but structurally unreachable (fell back to a plain 500), and unhandled exceptions were invisible to `/api/v1/metrics`. Both fixed, independently re-reviewed. Shipped as **PR #9**, merged `c4f4f454`. This is now `docs/sync/DECISIONS.md` **D-052**.
2. **УПЗНА (Указ № 883/1974) captured into the corpus** — triggered by an adjacent session's task brief citing conflicting secondhand article numbers (чл. 48 vs чл. 50) for the rule governing съпътстващи изменения. Resolved by reading the act's actual full text: the correct provision is **чл. 35, ал. 2**. `estado: vigente` established by cross-reference (our own `zakon-za-normativnite-aktove.md` still actively depends on this decree via its live чл. 9(3); the decree's own text carries no repeal marker on itself). Sourced from a strategy.bg-hosted PDF that traces to APIS (flagged per D-039 as oracle-grade reference, not a clean independent source — an APIS-free capture, ideally ДВ бр. 39/1974, remains open). Live-verified via MCP `get_law`/`get_article` this session (see §5). Recorded as **D-049-addendum** in DECISIONS.md — closes ONE instance of the укази gap, not D-049 generally.
3. **`legalize-bg` MCP server installed globally** (`claude mcp add legalize-bg --scope user`) — confirmed `✔ Connected`, and this session's own `get_law` call against the new УПЗНА act (§5) is the first genuine MCP-transport (not direct-Python-import) verification of that install.
4. **FR-031 (remote MCP transport) — design only, not implementation.** New `docs/plans/2026-07-03-remote-mcp-transport-design.md`. Central finding: this is a from-scratch feature (FastMCP supports `http`/`sse`/`streamable-http`, but `mcp_server/__main__.py` has never called `.run()` with anything but the stdio default), hard-gated on **FR-029** (the MCP server's per-call connection model / D-040 global lock — FR-029's own backlog text already names "MCP-over-HTTP" as its trigger). Registered as FR-031 in `docs/frs/INDEX.md`, status `Planned — design ready`. Four blocking owner questions in the design's §7; the first one worth asking directly before anything else: **given the REST API already ships, is remote MCP actually needed?**

## §3 One thing worth double-checking, already resolved this session

`tests/perf/test_warm_persistent.py::test_search_warm_persistent_p95` was measured failing by 1.1ms (`0.0371s` vs the D-051 hard budget `0.0360s`) partway through this session, under heavy concurrent load (Playwright browser sessions + subagent dispatches running simultaneously). Flagged to the user as a possible transient, not asserted as a regression. **Re-ran it just now, standalone, at handover time: 1 passed.** Matches this exact budget's own documented history (D-051's rationale already records one prior near-miss traced to ambient machine load, not code). Treat this as resolved — no action needed — but if it flakes again, it's this specific budget, this specific test, and this is the second time.

## §4 Governance state (read before touching any of these)

- `docs/sync/DEFERRED.md` — **`D-2026-07-02-01` is still `Open`, and its trigger condition fired this session.** It was punted from Phase 1b with the explicit reasoning "revisit when FR-028's REST API introduces per-request connections." FR-028 shipped (D-052) this session. The row has NOT been re-reviewed since. This doesn't block anything on its own (Target is a later phase), but per the delivery-contract's own promotion-gate rule it's due for an implement/re-affirm/withdraw decision, not indefinite staleness. **Nobody did this yet — flagging explicitly so it doesn't get missed twice.**
- `docs/sync/DECISIONS.md` — last row is `D-049-addendum` (this session). Next fresh ID is `D-053` if a new *numbered* decision is needed (the addendum used a suffixed ID deliberately, to signal "modifies D-049," not a new independent decision).
- `docs/frs/INDEX.md` — FR-031 is the newest row (`Planned — design ready`). FR-029 (`Backlog, Low`) is FR-031's hard prerequisite — its priority has NOT been changed; that's owner call, not something I did unilaterally.
- No open `IMPLEMENTATION-PREFLIGHT-*` docs pending signature — the two this session touched (`...fr028-rest-api.md` from planning, and the corpus commit which didn't need one — `regulations/` additions via existing schema values aren't a protected-surface event) are both closed.

## §5 Live verification performed this session (not just claimed)

- FR-028: live smoke against the real 3,601→3,602-act catalog (all 9 REST routes, 404 case, metrics) at Task 9; Fable 5 review additionally ran the full suite in an isolated worktree, exercised the live server, and probed SQL injection/path traversal/40-way concurrency.
- УПЗНА: `mcp_server.queries` direct-Python smoke (resolve/version/article-lookup/search) at capture time; **this session, via the actual `mcp__legalize-bg__get_law` MCP tool** (first real MCP-transport check) — full body returned correctly, `чл. 35, ал. 2` text matches what was read from the source PDF, `estado: vigente`, `commit_hash` matches the corpus commit.
- Global MCP install: `claude mcp get legalize-bg` → `Status: ✔ Connected`.

## §6 Options for the next session (no single mandatory path)

Ranked by how "loose end" each one is, not by importance:

1. **Close the DEFERRED.md staleness (§4, first bullet).** Cheapest, most overdue. Re-review `D-2026-07-02-01` now that its trigger has fired: does the REST API's per-request connection model actually change anything about the cold/fresh-connection body-only search budget? (Educated guess: probably re-affirm as still Open/deferred, since the REST API's own perf posture per D-052 doesn't touch this specific budget — but that's a guess, not a decision; actually check.)
2. **Answer FR-031's §7 owner questions**, starting with Q1 (is remote MCP needed given REST already ships?) — if the answer is "not yet," FR-031 can sit as a design doc indefinitely with zero further cost. If yes, Q2/Q4 gate Phase B.
3. **Phase 7.2 frontend** (`legalize-bg-web` sister repo) — this was ACTIVE.md's stated "next action" before this session's detours (УПЗНА, MCP install, FR-031) intervened. Still the largest pending item per the approved Phase-7 design (`docs/plans/2026-05-11-phase7-legislation-browser-design.md` §7.2). Needs its own repo scaffolding, not started.
4. **Independent of the above:** an APIS-free source for УПЗНА (ideally ДВ бр. 39/1974 itself) remains a documented open item (D-049-addendum) if the current oracle-derived text is ever judged insufficient for upstream contribution purposes.

None of these are blocking each other. Pick per the owner's actual priority, not this list's order.

## §7 Push status of THIS handover

This document plus the ACTIVE.md banner update are committed in the same commit as (or immediately after) the `6ad77692` FR-031 doc's push — check `git log --oneline -3` on arrival to see the true HEAD; do not trust §1's stated SHAs if they're now behind HEAD. If `git status` shows anything ahead of `origin/main` on arrival, that's expected — the closing action of this handover-prep was "commit, not push" (this session's established pattern: push only on explicit request), not an oversight. Push when ready; nothing here is time-sensitive or blocks CI/other consumers by sitting local for a while.
