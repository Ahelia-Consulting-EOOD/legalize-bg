# Active Work

**Current phase:** Phase 2 — **complete on `main` 2026-06-21**. Phase 1b is fully shipped (1b.1 + 1b.2 + 1b.3).
**Current owner:** ekimir
**Started:** 2026-06-21 (Phase 2 temporal index).
**Next action:** Batch **2.x-a — current-corpus agent UX** (FR-019 Cyrillic title lookup [lead] · FR-018 article ranges · Bulgarian stemmer · FR-011 triage), per the owner-set **MCP-first roadmap** — full sequence + task detail in `docs/sync/HANDOFFS/2026-06-21-post-phase2-mcp-roadmap.md` (2.x-a → 2.x-c operability → Phase 3 freshness → FR-020 time machine → Phase 7 web). The corpus re-scrape (D-030) is merged (3,599 acts). **Accuracy note:** `diff()` / historical `get_law(date)` still return single-version output even post-re-scrape — `index/build.py` writes one `law_versions` row per act (commit_hash = HEAD), so `version_at_date` resolves to a single commit. The re-scrape supplied per-act `[reforma]`/`[popravka]` git commits; materializing those into multiple `law_versions` rows (a row per commit, valid_from = its author-date) is the follow-up that actually enables multi-version temporal diffs (tracked as **FR-020**).

**🆕 Owner re-prioritization (2026-06-21): MUNICIPAL CORPUS — ASAP.** Building out a proper **municipal** legislation corpus is now a prioritized, near-term SEPARATE track (was Phase 6 per D-006). Trigger: FR-011 triage found 104 of the 121 null-pub acts are municipal council acts present only as lex.bg local entries; municipal acts DO appear in Държавен вестник, so they warrant a dedicated corpus with authoritative metadata, not a permanent waiver. Tracked as **FR-022** / **D-035** (supersedes D-006 timing). NOT folded into 2.x-a — needs its own brainstorm → plan → phased scrape (265 municipalities, per-site variance; the `municipal/` directory is already a reserved protected surface). **Re-sequenced (owner 2026-06-21): finish the MCP track first; municipal executes after PR #3 merges + MCP work done.** Live investigation + global-workflow plan complete: `docs/plans/2026-06-21-fr022-municipal-corpus.md`. Key findings: municipal acts publish LOCALLY not ДВ by default (ЗНА чл. 37(3) / ЗМСМА чл. 22(2); ДВ only "когато това е предвидено със закон"); `obshtini.bg` is APIS's commercial JSON-API SaaS (`web-api.apis.bg`, version-aware, has the dates our lex.bg-sourced acts lack) — scrapable but ToS-gated. Phase-0 of execution = resolve the APIS ToS / source decision.

**Batch 2.x-a — MERGED to `main` (PR #3, 2026-06-21).** Plan: `docs/plans/2026-06-21-2.x-a-agent-ux.md`.
- **FR-019 (Done):** Cyrillic case-insensitive title resolution via the `pylower` UDF (`queries.register_query_functions`, called in `build_app` + test `conn` fixture). Smoke-verified on live catalog for ЗОП mixed case.
- **FR-018 (Done):** new `get_articles` tool for article ranges + `get_article` now rejects a range with `INVALID_ARTICLE_SPEC` (no silent drop). `tools.json` 1.1.0→1.2.0; Surface-3 preflight filed; no new error codes.
- **Stemmer (deferred → FR-021 / D-032):** aggressive Bulgarian stemmer scoped out (D-022 conflict + full-corpus regression risk + needs eval harness); no `bg_normalize` change.
- **FR-011 (triaged → D-034):** 121 degenerate acts categorized + WAIVERS registry (`docs/data/fr-011-degenerate-triage.md`); no invented data. Municipal portion → FR-022.
- **Tests:** non-perf suite green; the 2 perf budget tests remain load-flaky (non-regression).

**FR-023 — MERGED to `main` (PR #4, 2026-06-21).** Connection-concurrency safety: serialize the shared sqlite connection behind a lock in `build_app` (D-040; review C1 root cause). Closes the deadlock + the pre-existing InterfaceError race.

**Batch 2.x-c (operability) — DELIVERED on `feat/2.x-c-operability` (2026-06-21), all 3 items, pending owner PR.**
- **Item 1 (logging+metrics):** per-tool-call structured logs (`tool=… ok=… duration_ms=…`) + `handle.metrics_snapshot()` via the `_register` wrapper. No schema/tool change.
- **Item 2 (packaging):** `[build-system]` + `[project.scripts] legalize-bg-mcp` + Dockerfile (+.dockerignore). Verified: `legalize-bg-mcp --help` + `docker build`/`run` (355 MB image).
- **Item 3 (FR-014 incremental rebuild, D-041):** `build(..., incremental=True)` / `--incremental` — git-diff indexed-commit→HEAD, re-index only changed acts, full-rebuild fallback; oracle-verified == full rebuild. **Closes the last open deferral (D-2026-05-09-05) — DEFERRED.md now has no active rows.**
- **State:** DECISIONS up to **D-041**; FRS up to **FR-024**; tools.json 1.2.0 (7 tools). Next roadmap step after 2.x-c merges + FR-022 municipal: Phase 3 freshness → FR-020 time machine → Phase 7 web.

## Status

**Phase 1a** (national legislation corpus, 3,573 acts) — complete on `main`.

**Phase 1b.1** (MCP server) — complete on `main`:
- 3 tools (`get_law` / `search` / `get_article`) over FastMCP/stdio, accessible to Claude Code, Claude Desktop, OpenAI Codex.
- **221 tests passing** across unit, component, integration (FastMCP in-memory), real-corpus acceptance (§7.1/7.2/7.3), FTS regression, and soft perf-budget tiers (216 after the audit-gaps batch on 2026-05-09; 221 after the review-fixes commit added 5 parametrizations of the FTS5 user-input regression).
- **Three formal code-review rounds; 27/27 findings closed**: 18 from Rounds 1–2 in-batch (forward-looking items recorded as FR-012 through FR-017 in `docs/frs/INDEX.md` per Ahelia conventions), and 9 from the third post-audit-gaps round closed in `docs/plans/2026-05-09-phase1b1-review-fixes.md` (FTS5 user-input allowlist regression; two `schema-reference.md` constraint mismatches the audit-fix itself introduced; a stale `runtime-flows.md` §6.3.4 predicate; the duplicate Session Model gap; four Minor doc/test polish items). Phase 1b.1 docs and code are publication-ready.
- SQLite catalog migrated to schema v4 with `provisions.text`, `laws_fts` virtual table, `idx_provisions_lookup`, and `law_versions.date_uncertain` columns.
- §7 data-quality semantics encoded as server-enforced contracts (D-026 error taxonomy with 8 codes; ambiguous-name candidates carry distinct identificadors; date_uncertain warning rides in successful responses).
- Operator runbook at `docs/runbook/2026-05-09-phase1b1-operator-setup.md`.
- Smoke-verified end-to-end: search/get_law/get_article all work against the live 3,573-act catalog. Build time 45 s. p95 latencies: get_law 3.4 ms, get_article 0.3 ms, search ~290 ms (soft warning on the "наредба" pathological query — FR-016 tracks the 1b.2 hardening).

**Phase 1b.2** (structured backend hardening) — complete on `main` 2026-05-09:
- **FR-016 closed** via the `QUERY_TOO_BROAD` reject path: single-word category queries (`наредба`, `закон`, `правилник`, `кодекс`, `постановление`) now short-circuit before FTS5 — the rejection runs in <1 ms instead of the 437 ms cold-call FTS5 ranking over 2,604 ordinances. 9th error code, additive per Surface 3.
- **D-027 closed**: `tests/perf/test_budgets.py` soft assertions promoted to hard via `_hard_assert(pytest.fail)`. New `tests/perf/test_cold_calls.py` adds first-user-hit coverage with fresh-connection-per-query. Shared `tests/perf/conftest.py` warmer keeps OS file cache hot across both files so the budgets measure SQLite/FTS5, not disk I/O.
- **`tools.json` published** (version 1.0.0) — full input/output JSON schemas for all 3 tools plus the 9-code error taxonomy. Source of truth: `mcp_server/export_tools.py`. CI parity test in `tests/mcp_server/test_export_tools.py` enforces no drift via `--check` mode.
- **Error taxonomy formalized**: `docs/api/error-codes.md` (humans) + `docs/api/error-codes.json` (machines), both at version 1.0.0, parity-tested against runtime `ERROR_CODES`.
- **Idempotency contract documented** in the runbook (read-only at request time; build path explicitly non-idempotent — FR-014 tracks the incremental rebuild).
- Test count: 221 → 244.

**Phase 1b.3** (operator/end-user polish) — complete on `main` 2026-05-09:
- **FR-013 closed**: long-form masc adjective definite article (`новият`/`нов` asymmetry) resolved by per-suffix MIN_STEM_LEN model in `index/fts.py:_BG_DEFINITE_SUFFIXES`. New 3-char `ият` suffix at MIN_STEM=3, ordered before 2-char `ят` so longest-match wins. Multi-syllable cases (`българският`) require a proper Bulgarian stemmer and stay out of scope per FR-013 text.
- **FR-015 closed** in two parts: (a) hand-curated synonym dictionary in `index/synonyms.py` (22 Bulgarian legal abbreviations) — single-token queries (`ЗОП`, `НК`, `ГПК`) auto-expand to canonical long form before FTS5; (b) rang-aware tier sort in `search_fts` — parent laws (laws/codes) outrank implementing regs (regulations/implementing/ordinances). Locked test: `search("обществени поръчки")` puts ЗОП at top despite shorter implementing-reg titles.
- **FR-017 closed** as opt-in: new `include_body=True` parameter on `search` populates `body_snippet` for the top 2 hits (Python-side ±60-char window with `<b>...</b>` highlighting). Default off — preserves the 100ms warm + 250ms cold p95 budgets. Largest indexed bodies are 1+ MB on the live catalog so even TOP_N=2 fetches cost ~150 ms (paid only when explicitly requested). New `body_snippet` field on `SearchHit` (additive per Surface 3).
- Test count: 256 → 286 (+30 new across the three FRs).
- D-029 captures the design choices in `DECISIONS.md`.

DEFERRED.md now has a single Open row (D-2026-05-09-05 / FR-014, Phase 4 incremental rebuild). Phase 2 promotion is no longer gated on Phase 1b deferrals.

**Phase 1b design** is recorded in `docs/plans/2026-05-09-phase1b-mcp-design.md`; D-020 through D-029 in `DECISIONS.md`. Phase 1b.2 plan: `docs/plans/2026-05-09-phase1b2-hardening.md`. Phase 1b.3 plan: `docs/plans/2026-05-09-phase1b3-polish.md`.

**Phase 2** (temporal index, FR-001) — **complete on `main` 2026-06-21**:
- 3 new MCP tools: `history()`, `diff()`, `amendments_in_period()`.
- `amendments` table populated from `amendment_history` YAML frontmatter field in index build.
- **306 tests passing** (was 287 at Phase 1b close; +19 previously-skipped real-corpus/perf tests now run against the live catalog.db).
- Time-travel tools (`diff`, historical `get_law`) are wired but show single-version output until the parallel corpus re-scrape (see `docs/sync/HANDOFFS/2026-06-21-corpus-rescrape-refresh.md`) accumulates more text versions. This is honest single-version semantics (D-031) — `diff()` and `get_law(date)` return correct-but-limited results rather than fabricating historical data.
- Smoke-tested against ЗОП via slug `zakon-za-obshtestvenite-porachki` (identificador lookup): 32 amendment events + real commit hash confirmed. (Title-based lookup `"Закон за обществените поръчки"` raises LAW_NOT_FOUND due to the SQLite `LOWER()` Cyrillic gap — awaits FR-019.)
- D-031 captures the temporal semantics decision in `DECISIONS.md`.

## Blockers

None.

## Pending

- **Corpus re-scrape** — parallel effort to accumulate multi-version text so `diff()` and historical `get_law(date)` return rich output. See `docs/sync/HANDOFFS/2026-06-21-corpus-rescrape-refresh.md`.
- **Phase 1b polish (optional, not gated)** — items mentioned aspirationally but not in DEFERRED.md: structured logging + per-tool-call metrics, packaging (PyPI / Docker image), proper Bulgarian Snowball stemmer (would close the multi-syllable-stem cases FR-013 left out, e.g. `българският`/`български`).
- **FR-011 G2 triage** of the ~128 degenerate acts (7 empty-titulo + 121 null-pub-date) — needed before Phase 5 upstream contribution; Phase 1b.1 surfaces these correctly so triage can proceed in parallel.

## Forward-looking items added in 1b.1 (FRS index)

- FR-012 — Phase 4 amendment-detection needs `body_text_minus_preamble` projection.
- FR-013 — Phase 1b.3 stemmer: adjective long-form definite article asymmetry.
- FR-014 — Phase 4 incremental rebuild path (vs current full DELETE-then-INSERT).
- FR-015 — Phase 1b.3 synonym dictionary + rang-aware re-ranking.
- FR-016 — Phase 1b.2 single-word category query stop-words.
- FR-017 — Phase 1b.3 body-snippet generation (currently title-snippet only for perf).

## Parallel track: corpus re-scrape (2026-06-21) — COMPLETE on `refresh/2026-06`

Wholesale lex.bg re-photograph per `docs/sync/HANDOFFS/2026-06-21-corpus-rescrape-refresh.md`, run in parallel with Phase 2. No code overlap: this track = `fetcher/bg` (read-only) + new `refresh.py` + corpus `.md`; Phase 2 = `mcp_server/` / `index/`.

- **Result:** 26 `[nova]` + 184 `[reforma]` + 66 `[popravka]` = **276 corpus commits**; 3,305 acts effectively unchanged; **18 acts gone from lex.bg's tree KEPT** (repealed/superseded — `estado` untouched, report-only); 0 errors; 0 Cloudflare. Corpus 3,573 → **3,599 acts**.
- **Tooling:** new `refresh.py` + 43 tests on the branch. No protected surface modified (`fetcher/bg` interfaces, frontmatter schema, commit format, SQLite schema all untouched).
- **Gates (handover §9):** pytest green (the two FTS5 perf-budget tests are load-flaky and pass in isolation); `export_tools --check` OK; G2 frontmatter clean (0 missing mandatory keys, 0 cp1251/UTF-8 artifacts, FR-011 degenerates unchanged at 7 empty-titulo + 121 null-pubdate); smoke test (search / get_law / get_article on a changed act + a nova act) OK; SQLite index rebuilt (3,599 acts).
- **Coordination (handover §8):** rebuild the SQLite index once more AFTER both this branch and Phase 2 merge, so it sees the freshest `amendment_history`. `catalog.db` is gitignored/derived.
- **MISSING acts — evaluated + actioned + resolved** (`docs/sync/HANDOFFS/2026-06-21-missing-acts-evaluation.md`): 17 confirmed repeals flipped to `estado: derogado` via 17 `[otmyana]` commits, each author-dated at the real repeal date. The 1 outlier `2137255124` (Union of Architects private bylaw, no ДВ) is **kept-but-marked** `derogado` as a scope exclusion (owner decision) with a YAML-comment note. Index rebuilt → **18 `derogado`** (17 repeals + 1 scope-mark).
- **Open items for the owner:** (1) **merge order** — see the evaluation in the close-out; recommend PR #1 (refresh) → PR #2 (Phase 2) → one final `index.build`. (2) 16 acts classified as changed but re-assembled byte-identical (idempotent guard absorbed them, 0 empty commits) — benign report over-count; candidate FR only if it recurs. (3) optional non-ДВ corpus sweep (see report §3).
- **Decision:** D-030. **Branch `refresh/2026-06` is ready for review/merge — NOT pushed.**
