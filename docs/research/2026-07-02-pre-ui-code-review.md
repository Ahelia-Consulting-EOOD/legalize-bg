# Pre-UI Comprehensive Code Review — Software Stack (2026-07-02)

**Scope:** the full software stack — `mcp_server/`, `index/`, `fetcher/bg/`, `bootstrap.py`, `refresh.py`, `scripts/`, `tests/`, packaging, ops — reviewed for readiness to (a) build the web UI (`legalize-bg-web`, Phase 7) on top and (b) use the MCP server daily "for real".
**Method:** 4 parallel module reviewers (mcp, index, fetcher, tests/ops) + orchestrator adversarial verification. Every P0 below was **verified first-hand** in code and/or against the live `catalog.db` / a real `fastmcp.Client` before being accepted. Corpus `.md` files were treated as data, not reviewed.
**Baseline:** `main` @ `b3b3d3d7`, working tree clean, non-perf suite 437 passed / 34 s.
**Disposition:** all accepted findings are planned in `docs/plans/2026-07-02-pre-ui-hardening-plan.md`; decisions in D-050. REST API (Phase 7.1) is the follow-on plan.

---

## 1. Verdict

Well-built and unusually well-tested at the unit level, but **not ready for a UI or unattended daily use**. Six P0-class defects (all verified) + one deterministic search-performance regression. None are architectural; all are fixable in days.

## 2. P0 findings (verified)

| # | Location | Defect | Failure |
|---|---|---|---|
| P0-1 | `mcp_server/errors.py:24` | `ToolError(Exception)` does not subclass `fastmcp.exceptions.ToolError` → FastMCP's `call_tool` wraps it (`except Exception`) into one free-text string; payload rendered as Python dict-repr, not JSON. Verified live over `fastmcp.Client`. | The entire D-026 error taxonomy (candidates, suggestions, available_articles, hints) is invisible to any non-LLM caller. UI cannot branch on or render errors. The e2e guard test only asserted a substring — passed in both worlds. |
| P0-2 | `index/provisions.py:152` | `_ALINEA_MARKER_RE` treats any `(NNNN)` as an alinea boundary; parenthesised years/citations (`(1969)`, `(2003)`, `(2020)`) split real alineas. | **Live catalog corrupted now:** 116 bogus paragraph rows across 22 acts (incl. ЗРТ чл. 19; Наредба № 3/2004 tonnage чл. 8/10). Paragraph-level `get_article` serves truncated text. Article-as-whole rows unaffected. |
| P0-3 | `index/build.py:84` | `_drop_content_rows` commits the `DELETE FROM` of all 5 content tables *before* the reindex loop. Full rebuild (the default CLI path) is not crash-atomic. | Any mid-rebuild failure (bad act, OOM, Ctrl-C) durably leaves **0 acts** — every MCP tool returns "nothing found". Reproduced by a reviewer against a copy of the live catalog. Incremental path is correctly atomic. |
| P0-4 | `fetcher/bg/coverage.py:232-235` | Gate checks only `t[:100] in M and t[-100:] in M` for nodes >200 chars — middles unchecked. Reproduced: 445-char node with 113 chars dropped from the middle → `uncovered_chars: 0`. | The sole post-D-047 per-act safety net cannot detect mid-node truncation — the exact D-047 failure class can recur silently. |
| P0-5 | `fetcher/bg/client.py:37-41` + gate | CF detection requires status 403/503; a challenge/interstitial served with HTTP 200 passes as content, parses to an empty act (`titulo=""`), and **passes the gate** (gate only inspects Cyrillic nodes). No titulo-presence precondition exists. | Wrong/blank pages committable as acts in future sourcing runs. |
| P0-6 | `fetcher/bg/metadata.py:100` + `refresh.py` | `estado: "vigente"` unconditionally hardcoded on parse; `derogado` flipped only in the MISSING branch. A repealed act still listed on lex.bg is silently un-repealed on its next EXISTING re-scrape (committed as `[popravka]`). | Corrupts the field consumers trust most ("does this law apply?"). |

## 3. Deterministic performance regression (verified, quiet machine)

`tests/perf` fails **deterministically**, not load-flakily (the ACTIVE.md "load-flaky" label is stale): `search` cold p95 = 3.0 s vs 0.25 s budget; warm budget also fails. Live probes: cold 1.2–3.7 s per query; `"лични данни"` **4.9 s warm** (CPU-bound bm25 over huge posting lists). Root cause: the D-047 re-bootstrap restored Допълнителни разпоредби across 1,826 acts → FTS body corpus now **223 M chars** (`catalog.db` 1.2 GB, avg body 62 k). Web PRD requires search < 300 ms p95. Tracked as **FR-027**.

## 4. P1 findings (accepted)

- **`git show` historical path** (`mcp_server/server.py:47-64`): no error handling (bare `check=True`), **zero test coverage** (every test uses the working-tree fast path), and path derived from the act's *current* category (latent wrong-path if an act ever changes category; zero cross-category renames exist today). The real multi-version `diff()` branch (`queries.py:684-700`) also has no two-commit test — despite 225 real multi-version acts.
- **Dead contract codes:** `INDEX_STALE` / `INDEX_MISSING` published in `tools.json` / `error-codes.json` as raised by `get_law`/`search`/`get_article` — never raised by any tool (startup preflight only). The real failure surfaces as a raw exception → flattened by P0-1.
- **No field-level output schemas:** `get_law`/`get_article`/`get_articles` export `{"additionalProperties": true}` (annotated `-> dict`). Nothing for UI codegen; `schemas.py` dataclasses never reach the export.
- **Invisible category dir:** `postanovleniya/` (ПМС № 46/2005, НСС decree) has **0 rows in catalog.db** — `_iter_corpus_files`/`_all_file_versions`/`_changed_acts` only scan `CATEGORY_DIRS`; no drift guard.
- **Global lock scope** (D-040): wraps entire tool bodies incl. git subprocesses and 1 MB body reads. Acceptable for one stdio client; a bottleneck for any concurrent fronting. Decision: REST API (7.1) manages its own per-request connections; MCP per-call connection model deferred as FR-029.
- **Pre-1970 clamp leak:** `law_versions.valid_from` = git author-date, clamped to `1970-01-01` (D-017) — Inheritance Act (1949) reports `earliest_available=1970-01-01`; historical queries 1949–1969 wrongly rejected (fails safe but wrong).
- **No CI at all** — tools.json/error-codes parity and the suite run on developer memory; test comments claim CI enforcement that doesn't exist. Perf tests have no marker to exclude them from a CI profile.
- **Ops:** `metrics_snapshot()` unreachable in production (never registered as a tool, no signal handler); runbook + README describe a 3-tool, no-Docker, no-history server; no `pip install` / Docker smoke test.
- **Acquisition robustness** (deferred to FR-025 kickoff preflight, except the P0s): bootstrap has no idempotent-commit guard / resume state (the 2026-07-01 DNS-outage recovery was manual); no dirty-tree preflight in bootstrap/refresh (write-then-commit not atomic → dirty baseline poisoning); `history_grew` detects growth only (silent `amendment_history` shrinkage commits as `[popravka]`).

## 5. P2 (recorded, not all planned)

`_changed_acts` dead `C` branch (copy-detection never fires without `--find-copies`); `CatalogIndex.initialize()` doesn't run `migrate()` (bootstrap-only DB not servable — run-order assumption); FTS `body`/`body_snippet` is lowercased (bg_normalize) — not display-faithful for a UI; `crawl_with_probe` `max_extra=25` cap indistinguishable from true end; coverage gate <8-char node exemption has no accumulation cap; `_nearest_legal_ancestor` region-boundary edge miscounts; empty-string dates treated as "today" (truthiness); no input-length caps on free-text params; `HANDOVER.md` stale tracked stub.

## 6. Test-coverage map (from the tests/ops review)

Strong: search / get_article / incremental-rebuild oracle / D-040 concurrency stress (16×20) / deploy-guard / FR-016..018 paths. **Untested:** `get_law` historical (`git show`), real two-commit `diff()`, packaging installability, Docker image, runbook parity. Fixture-only: history, amendments_in_period.

## 7. What was checked and found sound

FR-020 same-day-commit collapsing; `valid_to` INCLUSIVE arithmetic (windows can't invert); merge-commit limitation latent (zero merge commits touch category dirs); FTS5 DELETE-by-UNINDEXED-column correctness; migrations idempotency/ordering; bg_normalize suffix table (no new bugs beyond FR-021); rate-limiting rules 1-5 implemented as documented; QUERY_TOO_BROAD / synonym expansion / rang-tier sort behavior as specced.

---

**Disposition (2026-07-02, close-out):** all 6 P0s + the FR-027 perf regression + the planned P1/P2s in `docs/plans/2026-07-02-pre-ui-hardening-plan.md` were remediated in this session's commits `7dbc3af4..HEAD` (18 tasks, batches A/B/E/C/D). Plan executed to completion; see D-050/D-051 in `docs/sync/DECISIONS.md` and FR-027 in `docs/frs/INDEX.md`.
