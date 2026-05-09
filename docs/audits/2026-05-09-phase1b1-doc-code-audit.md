# Phase 1b.1 — Doc/Code Sync Audit

**Date:** 2026-05-09
**Scope:** Phase 1b.1 deliverable on `main` (commits `fdbc3288..HEAD`).
**Method:** Comprehensive cross-reference of every authoritative doc against the implementation; no pre-filtering by severity.
**Audit author:** code-reviewer agent (Opus 4.7, 1M ctx) acting under the doc/code synchronization-audit prompt.

---

## Executive summary

Phase 1b.1 ships clean against its own design + implementation plan. The MCP server (3 tools), index builder, error taxonomy, schema migrations, and §7.x acceptance tests all exist and pass (212/212). Forward-looking items are well-traced via FR-012..FR-017 with no untracked deferrals discovered.

The drift is concentrated in the **older, pre-Phase-1b authority surfaces**: `.ahelia/protected-surfaces.yaml`, `docs/data/schema-reference.md`, `docs/architecture/container-view.md` §7 result-shape, and `docs/architecture/runtime-flows.md` §6.3. These were written before D-024/D-026/D-027 and were never re-synced after Phase 1b.1 landed. `docs/process/delivery-contract.md` Phase-1b DoD is also slightly stale (still mentions only the old return-string contract via the implicit "MCP tool responses" wording).

Counts per axis: **Axis A = 9**, **Axis B = 4**, **Axis C = 6**, **Axis D = 10** (6 deferral-with-FR-trace, 1 deferral-without-trace, 2 silent-fail-ish, 1 working-as-designed; 0 simplification-by-test-loosening, 0 hardcode-that-should-be-config-without-rationale).

**Top 5 to act on first:**

1. **A-1**: `.ahelia/protected-surfaces.yaml` lines 67–73 still claim `get_law -> str` / `get_article -> str`. D-024 binding decision is `GetLawResponse` / `GetArticleResponse`. The protected-surfaces file is the machine-readable contract — it currently says the implementation is in violation.
2. **A-2**: `docs/data/schema-reference.md` SQLite section is missing **all four** Phase 1b.1 schema migrations (`provisions.text`, `laws_fts`, `idx_provisions_lookup`, `law_versions.date_uncertain`) and the `schema_version` table. New maintainers reading this file get a stale picture.
3. **A-3**: `search` result fields drift. Container-view + runtime-flows + design doc say `{… , title, snippet, score}`; code returns `{… , title, category, title_snippet, relevance}`. Discoverable contract surface for the LLM is correct (the docstring); the architecture doc is wrong.
4. **A-4**: queries.py:174,295 cite "`docs/data/schema-reference.md` §3" for the inclusive-`valid_to` rule. Schema-reference has only Section 1 + Section 2; §3 lives in `canonical-data-model.md`. Worse, `canonical-data-model.md` §3 documents the **closed** convention (`valid_to = new_valid_from − 1 day`) without ever explicitly stating the in-force predicate is `>=`. The spec is ambiguous; the code chose one reading and locked it with tests, but the spec hasn't caught up.
5. **B-1**: Phase-1b DoD in `docs/process/delivery-contract.md` lines 116–120 says only "Response times under 2 seconds for single-law queries". The design doc §9 binds tighter budgets (`search<100ms`, `get_article<50ms`) and the runbook surfaces 290ms `search` p95 ("FR-016") — the contract should reflect the tightened budget so 1b.2 hard-promotion doesn't move the goalposts silently.

---

## Axis A — Doc/code drift

| # | Title | Doc claim | Code reality | Severity | Fix |
|---|---|---|---|---|---|
| **A-1** | protected-surfaces.yaml MCP signatures stale | `.ahelia/protected-surfaces.yaml` L67–73: `get_law -> str`, `get_article -> str` | `mcp_server/server.py:128,237` returns `GetLawResponse.to_dict()` / `GetArticleResponse.to_dict()` (typed-dict per D-024) | **High** — this is the machine-readable preflight contract; out-of-date here means the next change-controlled review doesn't have anything to enforce against. | Update doc. Add `history/diff/amendments_in_period` are unimplemented (Phase 2) so they should be marked phase=2 not "protected" today. |
| **A-2** | schema-reference.md missing 4 migrations | `docs/data/schema-reference.md` §2 SQLite Schema shows only the original Phase-1a tables + 3 indexes; no `text` column, no `laws_fts`, no `idx_provisions_lookup`, no `date_uncertain`, no `schema_version` | `index/migrations.py:31-69` ships 4 migrations; live `catalog.db` confirms `schema_version` 1..4 applied + `laws_fts*` tables | **High** — schema-reference is the canonical reader for downstream consumers. | Update doc. Add Section 3 "Migrations & Schema Evolution" listing the four migrations + the `schema_version` table. |
| **A-3** | `search` result shape | container-view.md:167 + runtime-flows.md:244 + design.md:279 say `{law_id, identificador, title, snippet, score}` | `mcp_server/queries.py:268-280` emits `{law_id, identificador, title, category, title_snippet, relevance}`. Field renames (`snippet`→`title_snippet`, `score`→`relevance`) are deliberate (covered by `tests/mcp_server/test_search.py:19-39`) and `category` is additive. | **Medium** — docs disagree with the actual MCP response. | Update container-view.md, runtime-flows.md, design doc retroactively. The rename is a legitimate decision; just record it as D-028 or an addendum. |
| **A-4** | "schema-reference §3" pointer is wrong | `mcp_server/queries.py:174-176, 295-296` say "Per `docs/data/schema-reference.md` §3, `valid_to` is INCLUSIVE" | `schema-reference.md` has only §1 (YAML) and §2 (SQL); the §3 referenced is in `canonical-data-model.md`. Furthermore `canonical-data-model.md` §3 only states the closed-interval convention by example and does not name the predicate. | **Medium** — invariant the code depends on is not anywhere stated by name. | Add an explicit "valid_to is inclusive; in-force predicate is `valid_to IS NULL OR valid_to >= date`" sentence to `schema-reference.md` §2 and fix the code comments to point there. |
| **A-5** | text_hash spec drift | `docs/data/schema-reference.md` table for `provisions.text_hash` says "SHA-256 hash of the provision's text content" | `index/provisions.py:_hash` is `hashlib.sha256(...).hexdigest()[:16]` — a 16-char SHA-256 prefix, not the full digest | **Low** (cosmetic but real) | Either change code to store full digest, or update doc to "SHA-256 hex prefix (16 chars)". The 16-char prefix gives ~64-bit collision domain — adequate for change-detection at 3,573 acts × ~125k articles. Doc fix is the right move. |
| **A-6** | `search` snippet is title-only, undocumented in container-view | container-view.md:167 says "snippet" with no qualifier | `schemas.py:42-48` documents this in the `SearchHit` docstring (FR-017 traced) | **Low** | Add "title-snippet only; FR-017" to container-view.md row. |
| **A-7** | `search` `limit` cap (50) undocumented | container-view.md says `limit=20` default | `mcp_server/server.py:228`: `min(max(1, int(limit)), 50)` | **Low** | Document the cap in runbook + container-view. |
| **A-8** | container-view §7 still labels MCP block "Phase 1b (basic), Phase 2 (temporal)" | container-view.md:159 | Phase 1b.1 ships 3 tools only; Phase 2 strictly out per D-027 | **Low** | Split row labels — Phase 1b.1 vs Phase 2. |
| **A-9** | protected-surfaces is the only place that locks signatures, and it locks the pre-D-024 form (overlaps A-1) | `.ahelia/protected-surfaces.yaml` line 67-73 | typed-dict per D-024 in code | **Medium** | Subsumed by A-1 fix. |

---

## Axis B — Documented but not implemented

| # | Item | Doc claim | Code state | Severity | Fix |
|---|---|---|---|---|---|
| **B-1** | Phase-1b DoD in `delivery-contract.md` is loose | "Response times under 2 seconds for single-law queries" (line 120) | Design doc §9 + perf budget tests bind tighter (search<100ms, get_law current<100ms, get_article<50ms — soft) | **Medium** — the contract document is the authoritative DoD; if 1b.2 promotes the soft assertions to hard, the *contract* should already mention the right number, otherwise 1b.2 looks like scope creep. | Edit delivery-contract.md to point at the `docs/plans/2026-05-09-phase1b-mcp-design.md` §9 budget table. |
| **B-2** | Test-strategy MCP coverage | `docs/testing/test-strategy.md` says MCP integration tests verify tools "return correct data for known laws in the test corpus." | The actual harness is via FastMCP `Client`; only `test_tools_e2e.py` exercises the real JSON-RPC. Test-strategy doesn't mention FastMCP, the in-memory `Client`, or the `_AppHandle.call_tool_sync` shortcut that 90% of MCP tests use. | **Low** — testing strategy is now stale w.r.t. how testing actually happens. | Add a 5-line "Phase 1b.1 testing layers" subsection (L1 unit / L2 component / L3 in-memory FastMCP Client / L4 acceptance) and reference the perf-budget tier explicitly. |
| **B-3** | Coverage-floor implies all 6 MCP tools (`get_law`, `search`, `get_article`, `history`, `diff`, `amendments_in_period`) are required | `docs/process/COVERAGE-FLOOR.md` line 21 is correct in saying "extended in Phase 2+" but the floor doesn't tell a reader that 1b.1 ships 3 only. | Phase 1b.1 ships exactly 3; the other 3 require the temporal index FR-001. | **Low** — interpretable but easy to misread | Add a one-line note to COVERAGE-FLOOR ("Phase 1b.1 ships 3; Phase 2 adds 3"). |
| **B-4** | Operator runbook: "Smoke test … doc_id -549676032 should yield DATE_UNCERTAIN if also §7.2" | runbook lines 95-99 | The phantom is **§7.3 only** (empty-titulo); whether it's also in the §7.2 set depends on the live catalog. The runbook handwaves with "if". | **Low** — wording is fine, but the smoke-test should give a deterministic expected result. | Pick a concrete §7.2 doc_id (the test fixture already grabs one with `WHERE date_uncertain=1 LIMIT 1`) and put it in the runbook. |

---

## Axis C — Implemented but not documented

| # | Item | Code | Severity | Fix |
|---|---|---|---|---|
| **C-1** | "Exactly-one-anchor-per-paragraph" article extraction rule | `index/provisions.py:_extract_article_blocks` rejects paragraphs with 2+ "Чл. N." anchors as cite-list / template (covered by `test_skip_paragraph_with_multiple_anchors_cite_list`, comment at L98–105) | **Medium** — domain-specific heuristic that next maintainer can't infer from frontmatter | Add a paragraph to `docs/data/canonical-data-model.md` §4 or a new "Provisions extraction heuristics" subsection in `schema-reference.md`. |
| **C-2** | FTS5 two-tier ranking strategy | `index/fts.py:search_fts` runs `title:tok title:tok` first, then full-corpus body — comment at L143–161 explains why | **Medium** — design doc only says "FTS5 + BM25" | Add a one-paragraph note to `docs/architecture/runtime-flows.md` §6.3.3 OR `docs/plans/2026-05-09-phase1b-mcp-design.md` §6.3 (with an anchor or footnote). |
| **C-3** | `index/fts.py` defensive `OperationalError` catch | `_run_match` returns `[]` on `sqlite3.OperationalError` (line 134) so callers don't see FTS5 syntax errors from queries with `*`/`:`/unbalanced quotes. `resolve_name_to_law_id` does the same in queries.py:135-143 (with stricter narrowing — only suppresses fts5/syntax errors). | **Low** — only weakly silent (returns empty list). The narrowing in queries.py is good; the broader catch in fts.py loses any non-syntax DB error. | Either narrow `_run_match`'s catch to match queries.py's narrowed catch, or document why it's broader. Probably narrow. |
| **C-4** | `mcp_server/server.py` `_iso()` PyYAML-date coercion | server.py:335-342 | **Low** — quietly converts YAML `datetime.date` to ISO string. Important so `body_markdown` consumers don't see Python objects, but not surfaced anywhere. | One-line comment in `docs/runbook/2026-05-09-phase1b1-operator-setup.md` "Tools surfaced" or in `schemas.py` GetLawResponse. |
| **C-5** | `index/build.py` raises ValueError on missing/zero identificador (build.py:106-111) | Defensive: refuses to silently dedup on `doc_id=0` | **Low** — good behavior, undocumented. | Note it in the runbook's "Re-indexing after corpus changes" or in the §7.4 of canonical-data-model.md. |
| **C-6** | `mcp_server/__main__.py` `check_same_thread=False` | __main__.py:127 | **Low** — necessary for FastMCP's worker thread. The conftest does this too. Comment explains why locally; nothing in the runbook tells operators why. | Mention in the Phase 1b.1 runbook "Server runtime" section. |

---

## Axis D — Cut corners, deferrals, simplifications, silent-fail signals

| # | Item | Class | Notes |
|---|---|---|---|
| **D-1** | Range queries: `parse_article_spec` accepts `чл. 14-16` but `get_article` returns only article=14 | **deferral-with-FR-trace** | `mcp_server/server.py:248` says "full range support tracked in FR-001 Phase 2". FR-001 in INDEX.md is about the temporal index, NOT range support. Range support has **no FR**. *Action*: file a new FR-018 ("get_article range expansion: spec parses 14-16 but only 14 returned in 1b.1") OR add a sub-bullet to FR-001. |
| **D-2** | `bg_normalize` strips only last-character suffixes (та/то/те/ят/ът) | **deferral-with-FR-trace** | FR-013 explicitly covers the long-form definite-article asymmetry. Test at `test_fts.py:test_strips_long_definite_article_ETO_ITE` was renamed in spirit (`управлението` → `управление` is achieved via the trailing "то"); actual stripping of "ето"/"ите" is intentionally NOT done. Code matches design correctly. |
| **D-3** | `search` body snippet deferred | **deferral-with-FR-trace** | FR-017. Cleanly traced. |
| **D-4** | Single-word category queries (`наредба`) blow the 290ms p95 budget | **deferral-with-FR-trace** | FR-016. Cleanly traced. |
| **D-5** | Synonym dictionary / abbreviation resolution (`ЗОП` → ЗОП) | **deferral-with-FR-trace** | FR-015. Even the regression-yaml comments out the `ЗОП` case explicitly with a forward pointer. |
| **D-6** | Incremental rebuild | **deferral-with-FR-trace** | FR-014. Phase 4 work. |
| **D-7** | Soft perf assertions | `test_budgets.py` — soft (logs warning, doesn't fail). | **deferral-with-FR-trace** (D-027 binds 1b.2 to promote). However the *only* soft-assertion in the codebase is this one — no other "1b.1 only" loosening was found. Good discipline. |
| **D-8** | `_run_match` swallows all `sqlite3.OperationalError` → `[]` | **silent-fail (mild)** | `index/fts.py:134-137`. Better-narrowed sibling exists in `queries.py:resolve_name_to_law_id`. Specific risk: a corrupted FTS5 index produces "table laws_fts has no column" `OperationalError` and the search silently returns no hits instead of surfacing INDEX_STALE. *Action*: narrow the except like the resolver does. |
| **D-9** | `mcp_server/server.py:_split_frontmatter` returns `({}, raw)` on missing frontmatter | **silent-fail (mild)** | server.py:65-71. If a hand-edited `.md` lost its `---` block, `get_law` returns `titulo=""`, `eli=None`, etc. silently. The build path raises, but the query path doesn't. The mismatch is intentional (doc says working-tree fast path), but worth a WARN log. |
| **D-10** | `get_law` working-tree fast path: read working-tree file when `commit_hash == current_commit` | **other (working-as-designed)** | server.py:50-58. If the working tree is dirty (operator edited a file but didn't re-index), the query returns the dirty content. Operator runbook addresses this via the INDEX_STALE pre-flight. Confirming this is the intended trade-off, not a hidden failure mode. |

---

## Recommendations

Prioritized list. Sizes: **S** ≤ 1h, **M** ≤ half-day, **L** ≥ half-day.

1. **A-1 + A-9**: Update `.ahelia/protected-surfaces.yaml` to the D-024 typed-dict signatures and split `history/diff/amendments_in_period` into a "Phase 2" sub-block. (S)
2. **A-2 + A-4 + A-5**: Add Section 3 to `docs/data/schema-reference.md` covering migrations, the inclusive-`valid_to` predicate, and the SHA-256-prefix `text_hash` reality. Re-cite from queries.py code comments. (M)
3. **A-3 + A-6 + A-8**: Sync the `search` result shape and tool-phase breakdown in `docs/architecture/container-view.md` §7 + `docs/architecture/runtime-flows.md` §6.3.3 to match the SearchHit dataclass. Mark `history/diff/amendments_in_period` as Phase 2. (S)
4. **B-1**: Tighten the Phase-1b DoD line in `docs/process/delivery-contract.md` to point at the design doc §9 budgets. (S)
5. **D-1**: File FR-018 for "get_article range expansion" (or amend FR-001) — currently the only deferred-without-trace finding. (S)
6. **C-1 + C-2**: Surface the two undocumented heuristics (one-anchor-per-paragraph; two-tier FTS ranking) into design.md/runtime-flows.md so the next maintainer doesn't have to read code to know they exist. (S)
7. **D-8**: Narrow `_run_match`'s `OperationalError` catch in `index/fts.py` so corrupted-index conditions surface instead of returning `[]`. (S)
8. **C-3 + D-9**: Audit pass for over-broad excepts; add WARN log on `_split_frontmatter`'s frontmatter-missing fallback. (S)
9. **B-2**: Update `docs/testing/test-strategy.md` Phase-1b paragraph to describe the four real testing layers. (S)
10. **B-3 + B-4**: Minor cleanups in COVERAGE-FLOOR.md and the runbook smoke-test. (S each)

---

## What's NOT a finding

- **`bg_normalize` not stripping "ите"/"ето"/"ия" longer suffixes** — I initially read this as a regression vs the design doc, but the design explicitly defers the asymmetry to FR-013, and the tests `test_plural_definite_indefinite_symmetry` lock the symmetric reduction (`обществените` ≡ `обществени`) the code achieves with last-character stripping. Working as designed.
- **`provisions` table includes article preamble in the article-as-whole row** — flagged in FR-012 with explicit rationale. Not a regression; intentional contract for 1b.1 search.
- **Soft perf assertions** — D-027 binds 1b.2 to harden them; the runbook + plan say "soft in 1b.1, hard in 1b.2" consistently. Not a corner cut.
- **Negative `doc_id` for §7.3 phantom acts** — looked weird until I traced the resolver's regex `-?\d+` and the conftest's `-549676032` fixture; it's a real lex.bg-derived 32-bit signed integer pattern from §7.3 acts.
- **CategoryDIRS imported from `fetcher/bg/discovery`** — looked like a layering smell (index depending on fetcher), but the only thing imported is the immutable `{laws, codes, ordinances, regulations, implementing}` mapping. Acceptable until the directory list is hoisted somewhere neutral.
- **No `tools.json` schema file** — explicitly Phase 1b.2 (D-027). Not a 1b.1 deliverable.
- **`amendments` table is empty in the live catalog** — Phase 4 populates it; 1b.1 just preserves the schema. Per FR-001 + COVERAGE-FLOOR.
