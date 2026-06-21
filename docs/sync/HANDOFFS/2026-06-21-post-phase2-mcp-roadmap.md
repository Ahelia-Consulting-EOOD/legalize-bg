# Handoff: 2026-06-21 — Post-Phase-2, MCP-first roadmap (start 2.x-a)

**Author:** ekimir session (Claude Opus 4.8, 1M context), 2026-06-21
**`origin/main` HEAD at handover:** `5b90aa8c` (in sync; local main == origin/main)
**Corpus:** **3,599 acts** · **6 MCP tools** · error taxonomy 11 codes (`tools.json` v1.1.0)
**Tests:** **357 passing** combined (Phase 2 + refresh suites), 0 skipped/0 failed when `catalog.db` exists. ⚠️ `tests/perf/test_budgets.py::test_search_p95` (and `test_search_cold_p95`) are **load-flaky** under a busy machine — they pass in isolation; NOT regressions.
**Working tree:** clean.

---

## Execute these steps (read top-to-bottom)

You are continuing `legalize-bg` from a previous session. Phase 2 and a wholesale corpus re-scrape both just merged. The owner's directive resets priorities: **the MCP server is THE product; top usage is AI agents querying the CURRENT corpus; the web UI is "show-off" and comes last.**

**Next task: start batch 2.x-a — current-corpus agent-UX improvements.** Lead item is **FR-019** (it's the most direct fix for how agents actually call the server). Then FR-018, the stemmer, and FR-011 triage.

**How to proceed:** `superpowers:brainstorming` (FR-018 is a contract change → needs a design decision) → `superpowers:writing-plans` → `superpowers:subagent-driven-development` in an **isolated git worktree** (see the Worktree gotcha below — it bit the last session) → `superpowers:requesting-code-review` (clean-context rounds) → PR → merge after explicit owner OK. Plans go in `docs/plans/YYYY-MM-DD-<feature>.md`.

---

## The agreed MCP-first roadmap (owner-set this session)

1. **2.x-a — Current-corpus agent UX** ← START HERE
   FR-019 Cyrillic title lookup (LEAD) · FR-018 article ranges · Bulgarian Snowball stemmer (search recall) · FR-011 triage of the ~128 degenerate acts
2. **2.x-c — Operability**
   structured logging + per-tool-call metrics · packaging (`[project.scripts]` console entry + `[build-system]` + Dockerfile so the server is `pip install`/`docker run`-able) · FR-014 incremental index rebuild
3. **3 — Freshness**
   periodic `refresh.py` re-scrape now → Phase 3 DV monitor (→ Phase 4 consolidation later)
4. **2.x-b — FR-020 time machine** (deliberately MOVED to after freshness)
   populate `law_versions` per git commit → `diff()` + historical `get_law(date)` go live on the accumulated commit history
5. **7 — REST API + Next.js web** (show-off, last)

**Why FR-020 is deferred (dependency check, confirmed):** FR-020 has no upstream dependency on Phase 3 — it only needs version commits in git, which already exist (the re-scrape made them) and grow over time (re-scrapes / Phase 4 create commits; the Phase 3 monitor only *detects*). Building it later = richer history to time-travel, and the current-corpus priority makes the historical layer lower-priority. See `ACTIVE.md` + FR-020.

---

## 2.x-a task detail (enough to start)

### FR-019 — Cyrillic case-insensitive title resolution (LEAD; biggest agent-UX win)
- **Problem:** `mcp_server/queries.py:resolve_name_to_law_id` step 3 matches titles via `WHERE LOWER(title) = LOWER(?)`. SQLite's built-in `LOWER()` is **ASCII-only** — it does NOT fold Cyrillic. So `get_law("Закон за обществените поръчки")` (mixed case) raises `LAW_NOT_FOUND`; only identificador (step 1) and exact-slug (step 2) resolve. Agents naturally call by title → this fails for them today.
- **Recommended fix (no schema change):** register a Python UDF on the connection — `conn.create_function("pylower", 1, lambda s: s.lower() if s else s)` — and query `WHERE pylower(title) = pylower(?)`. `str.lower()` is full-Unicode, so it folds Cyrillic. O(n) scan over 3,599 rows is <5 ms; fine. The connection is created in `mcp_server/__main__.py` (and the test conftest) — register the UDF there, or inside `build_app`/queries so tests get it too.
- **Alternative (indexed, schema touch = Protected Surface preflight):** add a `laws.title_normalized` column populated by `index.build` (via `str.lower()`/`bg_normalize`) and match on it. Faster but bigger blast radius. The UDF route is the YAGNI choice; brainstorm if perf ever demands the column.
- **Tests:** add a mixed-case Cyrillic title lookup to `tests/mcp_server/test_get_law.py` (and the shared resolver tests). The `populated_conn` fixture titles are like "Закон за А" — seed an all-caps variant and look it up mixed-case.

### FR-018 — `get_article` range expansion (contract change → brainstorm first)
- `mcp_server.queries.parse_article_spec("чл. 14-16")` already parses the range (`range_end`), but `mcp_server.server.get_article` returns only `article=14`; 15–16 are silently dropped.
- This is a **Protected Surface 3** change (MCP tool signature/response shape) → needs IMPLEMENTATION-PREFLIGHT + a design decision: (a) `get_article` returns `list[ArticleEntry]` when the spec is a range, OR (b) a new `get_articles` tool taking a list. Interacts with D-024's response shape and `version_at_date`/`valid_to`. Brainstorm before coding.

### Bulgarian Snowball stemmer — search recall (careful, load-bearing)
- 1b.3 added only the 3-char `ият` definite-article suffix (`index/fts.py:_BG_DEFINITE_SUFFIXES`). Multi-syllable consonant-stem cases (`българският`/`български`) need a real stemmer. **`bg_normalize` symmetry is load-bearing** — index AND query must use the SAME normalization, so any change requires a **full re-index** (~45 s). Read the `_BG_DEFINITE_SUFFIXES` rationale block first (it documents which suffixes were deliberately REJECTED to avoid mangling plural-noun endings). Consider a vetted Bulgarian Snowball lib vs hand-expanding the suffix table. Scope/brainstorm carefully — this is the riskiest 2.x-a item.

### FR-011 — triage the ~128 degenerate acts (data quality; partly manual)
- ~128 acts flagged at bootstrap (7 empty `titulo` + 121 null `fecha_publicacion`). **Re-count against the live 3,599-act catalog first** — the re-scrape may have fixed some. For each: drop (WAIVERS), backfill from DV/parliament.bg, or mark deprecated. Required before G2 (frontmatter validation) passes 100% — a Phase 5 pre-gate, but it also means agents get blank/odd hits on these acts today. Uses the embedded-vision OCR approach (render + read), NOT external OCR libs (per global rules).

---

## What shipped THIS session

| Item | Result |
|---|---|
| **Phase 2 temporal index** (PR #2) | merged — `history` / `amendments_in_period` / `diff` tools; `amendments` table populated from `amendment_history`; INVALID_DATE_RANGE + DIFF_FAILED codes; honest single-version semantics (**D-031**) |
| **Corpus wholesale re-scrape** (PR #1) | merged — corpus 3,573 → **3,599** acts; `refresh.py` + `tests/refresh/`; decision **D-030** |
| Merge order | PR #1 first, then PR #2 (DECISIONS stays sequential D-029→D-030→D-031) |
| Live `catalog.db` | rebuilt on `main`: 3,599 acts, **19,939** amendments (3,440 `enacted`); smoke-verified `history(ЗОП)`=35 entries |
| **FR-020** | filed (multi-version `law_versions` from git history — the deferred time-machine write-side) |
| Merged PR branches | `refresh/2026-06`, `feat/phase2-temporal-index` deleted |
| **Mirror** | `github.com/theoremus-business/legalize-bg` (PRIVATE, one-time full mirror — main + bootstrap/phase-1a, identical SHAs; does NOT auto-sync) |

---

## Carry-forward facts & gotchas (READ before coding)

- **Interpreter:** `.venv/bin/python` everywhere. There is **no system `python`/`pytest`**.
- **🔴 Worktree gotcha (bit the last session):** this repo has a **STRICT editable install** (`.venv/lib/.../__editable___legalize_bg_*_finder.py`, a meta-path finder) that hardcodes the main checkout. A git worktree at another path will, with the main venv, import **main-checkout code** — silently defeating isolation. So a worktree MUST get its **own fresh venv** (`python -m venv .venv && .venv/bin/pip install -e ".[dev]"`) and you must verify `mcp_server.__file__` resolves to the worktree before trusting tests. `EnterWorktree` branches from `origin/main` (`fresh`) by default — that's the clean Phase-1b+Phase-2 tip now.
- **`.superpowers/` is now gitignored** (added this session) — SDD scratch (briefs, reports, review packages, ledger) no longer leaks into commits. Use it freely.
- **Perf tests are load-flaky:** `test_search_p95` / `test_search_cold_p95` fail under concurrent machine load (search path unchanged); confirm in isolation before treating any failure as real.
- **`tools.json` is generated** — never hand-edit; regenerate `.venv/bin/python -m mcp_server.export_tools --output tools.json`. CI parity test (`tests/mcp_server/test_export_tools.py`) fails on drift. Currently 6 tools, 11 error codes, v1.1.0.
- **Error taxonomy parity:** new code → `mcp_server/errors.py:ERROR_CODES` + `docs/api/error-codes.md` (`### \`CODE\`` heading) + `docs/api/error-codes.json` (md/json versions must match). Enforced by `tests/mcp_server/test_error_codes_doc.py`.
- **Protected surfaces** (`.ahelia/protected-surfaces.yaml`): YAML frontmatter schema, `fetcher/bg/` interfaces, MCP tool signatures (Surface 3), SQLite schema, commit format, directory structure. Changes need IMPLEMENTATION-PREFLIGHT. FR-018 hits Surface 3; FR-019 UDF route does NOT.
- **DECISIONS.md** is single-line table `| D-NNN | date | title | rationale | Active |`, now up to **D-031**. **FRS index** up to **FR-020**.
- **Direct-to-main** is accepted for small doc/planning commits (end messages with the `Co-Authored-By: Claude Opus 4.8 (1M context)` trailer). Feature work goes via PR, merged after explicit owner OK (proven: PR #1, #2 this session).
- **`refresh.py`** (top-level) is the freshness interim — re-run it periodically to keep the corpus current until Phase 3/4. Its handoff/spec: `docs/sync/HANDOFFS/2026-06-21-corpus-rescrape-refresh.md`.
- **Vision/OCR** (for FR-011): use the embedded Read-the-rendered-page approach, never external OCR libs (global rule).

---

## Session-startup protocol reminder (from `.claude/CLAUDE.md`)

Read: `.claude/CLAUDE.md` → `docs/sync/ACTIVE.md` → `docs/sync/DEFERRED.md` (one open: D-2026-05-09-05/FR-014, target Phase 4 — not gating 2.x) → `docs/process/delivery-contract.md` → this handoff → `docs/frs/INDEX.md` (FR-018/019/020 are the near-term backlog). Phase-promotion gate is clean.
