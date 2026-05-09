# Phase 1b.1 — Doc/Code Audit Gaps Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use `superpowers:executing-plans` to implement this plan task-by-task.

**Goal:** Close the 22 in-scope findings from `docs/audits/2026-05-09-phase1b1-doc-code-audit.md` (Axis A: 9, Axis B: 4, Axis C: 6, Axis D: 3) AND establish a deferral-tracking register in the Ahelia oversight stack so future deferrals don't slip out of sight. The audit drift is concentrated in pre-Phase-1b authority surfaces (`.ahelia/protected-surfaces.yaml`, `docs/data/schema-reference.md`, `docs/architecture/container-view.md` §7, `docs/architecture/runtime-flows.md` §6.3) plus three small code corrections (D-1 FR pointer, D-8 narrowed except, D-9 WARN log). No code-architecture changes — D-024/D-026/D-027 are binding; this plan adapts docs to the binding decisions, not the reverse.

**Out of scope (pending separate user decision):** D-2..D-7 (six cleanly-traced deferrals; FR-013/14/15/16/17 + 1b.2 soft-perf-assertion promotion). The deferrals are listed verbatim in Batch 7's seed for `docs/sync/DEFERRED.md`; they are NOT being implemented here, but they ARE being elevated into the session-startup read path.

**Authority docs to read before implementing:**
- `docs/audits/2026-05-09-phase1b1-doc-code-audit.md` — the audit itself
- `docs/plans/2026-05-09-phase1b-mcp-implementation.md` — prior plan shape (TDD pattern, commit message style)
- `docs/sync/DECISIONS.md` D-020..D-027 — binding decisions
- `docs/process/IMPLEMENTATION-PREFLIGHT.md` — Surface 3 (MCP signatures) and Surface 6 (index/FTS)
- `.claude/CLAUDE.md` — repo conventions

**Key constraints (non-negotiable):**
- Each task ≤ 10 minutes of execution time.
- Doc tasks have no test, but they DO have a verification step ("re-read the file and confirm X is now stated correctly").
- Code tasks are TDD: failing test → minimal change → passing test → commit. D-8 in particular needs a regression test that asserts a non-FTS5 OperationalError isn't swallowed.
- Do not introduce new tests for doc-only fixes.
- The 212/212 test suite must remain green after every batch.
- Per Protected Surface 3, response shapes are typed-dicts and additive only; this plan only updates docs to match the implementation.
- Per Protected Surface 6, `bg_normalize` symmetry and `provisions` alinea-level rows are untouched here.

## Batch overview

| Batch | Findings | Surface(s) touched | Est. |
|---|---|---|---|
| 1 | A-1, A-9 | `.ahelia/protected-surfaces.yaml` | 10 min |
| 2 | A-2, A-4, A-5, C-1, C-5 | `docs/data/schema-reference.md`, `docs/data/canonical-data-model.md`, `mcp_server/queries.py` (comment-only) | 30 min |
| 3 | A-3, A-6, A-7, A-8, B-3, C-2 | `docs/architecture/container-view.md`, `docs/architecture/runtime-flows.md`, `docs/process/COVERAGE-FLOOR.md` | 30 min |
| 4 | B-1, B-2 | `docs/process/delivery-contract.md`, `docs/testing/test-strategy.md` | 20 min |
| 5 | D-1 + FR-018, D-8, D-9, C-3, C-4, C-6 | `docs/frs/INDEX.md`, `mcp_server/server.py`, `index/fts.py`, `tests/index/test_fts.py`, `mcp_server/schemas.py` | 40 min |
| 6 | B-4, C-4 (runbook addendum), C-6 (runbook addendum) | `docs/runbook/2026-05-09-phase1b1-operator-setup.md` | 15 min |
| **7** | **Deferral oversight register** (new — not in audit, addressing user's "where in oversight logic" question) | `docs/sync/DEFERRED.md` (new), `docs/process/delivery-contract.md`, `.ahelia/protected-surfaces.yaml`, `.claude/CLAUDE.md` | **30 min** |

Total in-scope: 22 audit findings + the deferral-register infrastructure across ~15 distinct files.

## Assumptions

- The audit findings are accepted as-stated. If during execution any finding looks wrong, stop and consult the user — do not silently rewrite the audit's conclusion.
- A `.venv` exists at the repo root with `pip install -e ".[dev]"` already run (per the runbook). All `pytest` invocations use `.venv/bin/pytest` to match the prior plan's convention.
- Working tree is clean before starting. Each batch ends with a commit; subsequent batches start from that clean state.
- Doc edits should preserve the file's existing voice and Markdown conventions (table styles, heading levels, line lengths). When in doubt, mirror the closest existing section.

## References (read-once)

- Schema migrations: `index/migrations.py` (4 shipped: provisions.text, laws_fts, idx_provisions_lookup, law_versions.date_uncertain)
- `schema_version` table: created by `_ensure_schema_version_table` in `index/migrations.py`
- D-024 typed-dict schemas: `mcp_server/schemas.py` (`GetLawResponse`, `GetArticleResponse`, `SearchHit`)
- Search shape: `mcp_server/queries.py:full_text_search` returns `{law_id, identificador, title, category, title_snippet, relevance}` (NOT `{snippet, score}` as the older docs claim)
- Inclusive-`valid_to` predicate: `mcp_server/queries.py:version_at_date` uses `valid_to >= date` (citation comments at lines 174 and 295 currently point at the wrong file)
- text_hash: `index/provisions.py:_hash` is `hashlib.sha256(...).hexdigest()[:16]` — 16-char prefix, not full digest
- One-anchor-per-paragraph rule: `index/provisions.py:_extract_article_blocks` (test: `test_skip_paragraph_with_multiple_anchors_cite_list`)
- Two-tier FTS ranking: `index/fts.py:search_fts` (title-tier first, then body-tier with dedup)
- Working-tree fast path: `mcp_server/server.py:_read_law_markdown`
- `_split_frontmatter` silent fallback: `mcp_server/server.py:_split_frontmatter` (returns `({}, raw)` on missing `---\n` prefix)
- `_iso` PyYAML date coercion: `mcp_server/server.py:_iso`
- ValueError on missing identificador: `index/build.py:106-111`
- `check_same_thread=False`: `mcp_server/__main__.py:127`

---

## BATCH 1 — protected-surfaces.yaml (A-1, A-9)

### Task 1: Update `.ahelia/protected-surfaces.yaml` MCP signatures to D-024

**Audit finding:** A-1 (High), A-9 (Medium, subsumed by A-1).

**Files affected:**
- Modify: `.ahelia/protected-surfaces.yaml`

**Step 1: Verification baseline (no test).** Confirm the current file states `get_law -> str` / `get_article -> str` / `search -> list[dict]` and lists `history`/`diff`/`amendments_in_period` alongside the 1b.1 trio without phase distinction. Confirm the `protected_signatures` block is at lines 67–73 of the file (drift if numbering moves; replace by anchor not by line number).

**Step 2: Make the change.** In the `MCP Server Tool Signatures` block (under `path: "mcp/server.py (tool signatures)"`):

- Update the path string to `mcp_server/server.py (tool signatures)` to match the actual module path.
- Replace the three Phase 1b.1 signatures with the typed-dict forms:
  - `get_law(name: str, date: str | None = None) -> GetLawResponse`
  - `search(query: str, category: str | None = None, limit: int = 20) -> list[SearchHit]`
  - `get_article(law: str, article: str, date: str | None = None) -> GetArticleResponse`
- Split the three Phase 2 signatures (`history`, `diff`, `amendments_in_period`) into a separate sub-block clearly marked `phase: 2 (not yet implemented)` so a reader cannot mistake them for the current contract:

```yaml
    protected_signatures:
      phase_1b_1:
        - "get_law(name: str, date: str | None = None) -> GetLawResponse"
        - "search(query: str, category: str | None = None, limit: int = 20) -> list[SearchHit]"
        - "get_article(law: str, article: str, date: str | None = None) -> GetArticleResponse"
      phase_2:
        - "history(law: str) -> list[VersionEntry]"
        - "diff(law: str, date1: str, date2: str) -> str"
        - "amendments_in_period(from_date: str, to_date: str) -> list[AmendmentEntry]"
```

- Add a one-line `reference:` field pointing at `docs/sync/DECISIONS.md` D-024 so future readers can trace the rationale.
- Leave the SQLite Schema block, frontmatter block, and Legalize-fetcher block untouched (out of scope for this audit).

**Step 3: Verification.** Re-read `.ahelia/protected-surfaces.yaml`; confirm:
- All three current tool signatures end in a typed-dict / `list[SearchHit]`, not bare `-> str`.
- The three Phase 2 tools are visibly under a `phase_2` (or equivalent) sub-key with a phase marker.
- The `path:` field references `mcp_server/server.py`, not the legacy `mcp/server.py`.
- A pointer to D-024 exists.
- Run `python -c "import yaml; yaml.safe_load(open('.ahelia/protected-surfaces.yaml'))"` to confirm the YAML still parses.

**Commit:**

```
docs(protected-surfaces): sync MCP tool signatures to D-024 typed-dicts

Phase 1b.1 ships GetLawResponse / GetArticleResponse / list[SearchHit] per
D-024; the protected-surfaces machine-readable contract was still claiming
the pre-D-024 bare-string return shapes (audit A-1, High).

Also splits the Phase 2 trio (history / diff / amendments_in_period) into
a separate sub-block so they can't be misread as the current contract
(audit A-9, subsumed by A-1).

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
```

---

## BATCH 2 — schema-reference + canonical-data-model + queries.py code comments (A-2, A-4, A-5, C-1, C-5)

### Task 2: Add Section 3 to `schema-reference.md` covering migrations, the inclusive-`valid_to` predicate, and the SHA-256-prefix `text_hash`

**Audit findings:** A-2 (High), A-4 (Medium), A-5 (Low).

**Files affected:**
- Modify: `docs/data/schema-reference.md`

**Step 1: Verification baseline.** Confirm `docs/data/schema-reference.md` currently has Section 1 (YAML Frontmatter) and Section 2 (SQLite Schema) only, and that Section 2's `provisions.text_hash` row claims "SHA-256 hash" without the 16-char prefix qualifier. Confirm the SQL-DDL block in Section 2 lacks the `text` column on `provisions`, has no `laws_fts` virtual-table definition, no `idx_provisions_lookup`, no `date_uncertain` column on `law_versions`, and no `schema_version` table.

**Step 2: Make the change.**

a) In Section 2 — `provisions` table — fix the `text_hash` row description to read **"First 16 hex characters of the SHA-256 digest of the provision's text content (`hashlib.sha256(...).hexdigest()[:16]`). Used for change detection — if the hash changes between versions, the text was amended. ~64-bit collision domain, adequate for ~125k provisions across 3,573 acts."**

b) In Section 2 — `law_versions` table — add the `date_uncertain` column to the DDL block AND the column-table documentation, marked Nullable INTEGER (0/1 boolean) with description **"§7.2 marker: 1 when `fecha_publicacion` was null at index time and `valid_from` fell back to bootstrap-run date. Read by `mcp_server/queries.version_with_warnings` to attach a `DATE_UNCERTAIN` warning to every response."**

c) In Section 2 — at the bottom of the SQLite section, before the indexes — add a new sentence under a "Predicate semantics" mini-heading that states: **"`valid_to` is INCLUSIVE — a version with `valid_to = '2020-12-31'` is in force ON 2020-12-31. The in-force predicate is `valid_from <= date AND (valid_to IS NULL OR valid_to >= date)` (note `>=`, not `>`, which would silently exclude the boundary day). Authoritative consumer: `mcp_server/queries.version_at_date`."**

d) Add a new top-level **Section 3 — Migrations & Schema Evolution** at the bottom of the file. Section 3 lists, in version order, the four shipped migrations from `index/migrations.py` plus the supporting `schema_version` table:

```sql
CREATE TABLE schema_version (
    version INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

| Version | Name | Effect | Decision |
|---|---|---|---|
| 1 | `provisions_text_column` | `ALTER TABLE provisions ADD COLUMN text TEXT;` | D-023 |
| 2 | `laws_fts_virtual_table` | `CREATE VIRTUAL TABLE laws_fts USING fts5(... tokenize='unicode61 remove_diacritics 2')` | D-022 |
| 3 | `provisions_lookup_index` | `CREATE INDEX idx_provisions_lookup ON provisions(law_id, article, paragraph, valid_from)` | (perf) |
| 4 | `law_versions_date_uncertain` | `ALTER TABLE law_versions ADD COLUMN date_uncertain INTEGER DEFAULT 0;` | §7.2 surfacing |

Add a short prose note: **"Migrations are forward-only and idempotent. Never edit a shipped migration; add a new one. `migrate(conn)` is safe to call repeatedly. See D-025."**

e) In Section 2 — `provisions` table DDL block — add `text TEXT` to the column list (post-migration shape) so the documented schema matches the live shape.

**Step 3: Verification.**
- Re-read `docs/data/schema-reference.md`; confirm Sections 1, 2, 3 are present in that order and that Section 3 names all four migrations and the `schema_version` table.
- Confirm `provisions.text_hash` description now mentions "16 hex" and "SHA-256".
- Confirm the inclusive-`valid_to` sentence appears with the exact predicate `valid_from <= date AND (valid_to IS NULL OR valid_to >= date)`.
- Run `grep -n "schema_version\|laws_fts\|date_uncertain\|idx_provisions_lookup" docs/data/schema-reference.md` and confirm at least one hit each.

**Commit:**

```
docs(schema-reference): add Section 3 migrations + inclusive valid_to + text_hash prefix

- Adds Section 3 listing the four Phase 1b.1 migrations and the
  schema_version table (audit A-2, High).
- States the inclusive-valid_to predicate by name with the exact SQL
  in-force expression queries.py depends on (audit A-4, Medium).
- Corrects the provisions.text_hash description from "SHA-256 hash"
  to "first 16 hex chars of SHA-256" matching index/provisions._hash
  (audit A-5, Low).
- Surfaces law_versions.date_uncertain (Migration 004) which the
  schema docs had never picked up.

No schema changes; this aligns the docs with shipped code.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
```

### Task 3: Update `mcp_server/queries.py` code comments to point at the corrected schema-reference section

**Audit finding:** A-4 (Medium) — code-side half of the same fix.

**Files affected:**
- Modify: `mcp_server/queries.py`

**Step 1: Verification baseline.** Confirm `mcp_server/queries.py` lines ~174–176 and ~295–296 contain the docstring/comment "Per `docs/data/schema-reference.md` §3, `valid_to` is INCLUSIVE" referencing a section that didn't exist before Task 2.

**Step 2: Make the change.** Update both code comments so they now point at `docs/data/schema-reference.md` §2 "Predicate semantics" (the new mini-heading added in Task 2). Keep the predicate restatement in the docstring intact — the docstring is the load-bearing local explanation; the cross-reference is the breadcrumb.

Recommended wording (mirror the existing tone):

```
`valid_to` is INCLUSIVE per `docs/data/schema-reference.md` §2 ("Predicate
semantics") — a version with valid_to='2020-12-31' is in force ON
2020-12-31. So the in-force predicate is `valid_from <= date AND
(valid_to IS NULL OR valid_to >= date)` (NOT `>`, which would exclude the
boundary day).
```

**Step 3: Verification.**
- Run `.venv/bin/pytest -q tests/mcp_server/test_queries.py 2>&1 | tail -3`. Expected: same number passed as before (no behavioral change).
- Diff inspection: the only line changes inside `mcp_server/queries.py` are inside `version_at_date`'s docstring and the article_lookup comment block; no executable lines should change.

**Commit:**

```
docs(queries): retarget valid_to docstring at the corrected schema-reference §2

The pointer "schema-reference §3" was wrong — schema-reference had only
sections 1 and 2 until the audit fix. With Section 2 now carrying the
explicit "Predicate semantics" sub-heading, retarget the breadcrumb.
Comment-only; no behavioral change (audit A-4 code half).

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
```

### Task 4: Document the one-anchor-per-paragraph and missing-identificador heuristics in `canonical-data-model.md`

**Audit findings:** C-1 (Medium), C-5 (Low).

**Files affected:**
- Modify: `docs/data/canonical-data-model.md`

**Step 1: Verification baseline.** Confirm `canonical-data-model.md` §4 (Amendment Model) currently has no mention of provision-extraction heuristics, and that §7.4 (Surfacing mechanism) does not document the build-time refusal on missing/zero `identificador`.

**Step 2: Make the change.**

a) Add a new sub-section **§4a Provisions Extraction Heuristics** (or §4.1, depending on the existing numbering style) between §4 and §5. Keep it short — the heuristic is one sentence + one rationale paragraph:

> **Exactly-one-anchor-per-paragraph article extraction.** `index/provisions._extract_article_blocks` only emits an article row for paragraphs containing exactly one `**Чл. N.**` anchor. Paragraphs with two or more anchors (cite-lists like "В чл. 14, ал. 1, чл. 15, ал. 2 ...", template enumerations) are skipped — they reference articles in passing but do not constitute the article body. Test: `tests/index/test_provisions.py::test_skip_paragraph_with_multiple_anchors_cite_list`.

b) Extend §7.4 (or add a new §7.5) with a sentence on the build-time refusal:

> **Missing/zero `identificador` is a hard build error, not a soft warning.** `index/build._iter_corpus_files` raises `ValueError` when an `.md` file has `identificador` ∈ {None, "", 0, "0"}. Collapsing such acts to `doc_id=0` would cause silent dedup against any future zero-id row. The fetcher always populates `identificador` from lex.bg's URL pattern; a missing value is a data bug surfaced at index time rather than at query time.

**Step 3: Verification.**
- Re-read `canonical-data-model.md`; confirm §4a and §7.4/§7.5 additions are present.
- `grep -n "anchor\|identificador" docs/data/canonical-data-model.md` should now return new hits in §4a and §7.4/§7.5.

**Commit:**

```
docs(data-model): surface two implicit Phase 1b.1 contracts

- §4a documents the "exactly one Чл. N. anchor per paragraph" rule
  used by index/provisions._extract_article_blocks (audit C-1).
- §7.5 documents the build-time hard-error on missing/zero
  identificador in index/build.py (audit C-5).

Both are domain-specific heuristics not derivable from the YAML
frontmatter alone; documenting them so the next maintainer doesn't
have to read the code to learn they exist.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
```

---

## BATCH 3 — container-view + runtime-flows + COVERAGE-FLOOR (A-3, A-6, A-7, A-8, B-3, C-2)

### Task 5: Sync `search` result shape and tool-phase split in `container-view.md` §7

**Audit findings:** A-3 (Medium), A-6 (Low), A-7 (Low), A-8 (Low).

**Files affected:**
- Modify: `docs/architecture/container-view.md`

**Step 1: Verification baseline.** Confirm:
- container-view.md:159 says **"Phase 1b (basic), Phase 2 (temporal)"** as the MCP block phase tag.
- container-view.md:167 documents `search` returning `{law_id, identificador, title, snippet, score}` (the pre-rename fields).
- container-view.md:167 does not mention the 50-result cap.
- container-view.md:167 does not qualify "snippet" as title-only.

**Step 2: Make the change.** In §7 MCP Server table:

a) Replace `Phase 1b (basic), Phase 2 (temporal)` with `Phase 1b.1 (3 tools), Phase 2 (3 more tools — temporal)` to reflect that 1b.1 ships exactly 3 tools and Phase 2 strictly defers the other 3.

b) In the `search` tool row, replace the result-shape sentence:
- Was: `Each hit: {law_id, identificador, title, snippet, score}.`
- Becomes: `Each hit: {law_id, identificador, title, category, title_snippet, relevance}. The snippet is over the act's TITLE only (not body) — title-snippet runs in ~75 ms vs ~700 ms for body-snippet. Body-snippet generation is tracked as FR-017 for Phase 1b.3. The relevance score is the negated SQLite bm25 (higher = better). Empty-titulo acts (§7.3) get <doc_id=N> substituted in title.`

c) In the `search` tool row, append a sentence on the limit cap: **"`limit` defaults to 20 and is capped at 50 (defensive — FTS5 with very large limits can OOM on a million-row catalog; 50 is plenty for an LLM caller)."**

d) Phase column for the `search` row stays `1b.1`; for `history`/`diff`/`amendments_in_period`, ensure the phase column reads `2` and the description includes "deferred to Phase 2 — depends on FR-001 temporal index" so they're visibly out of the 1b.1 contract.

e) The `get_law` row description (line ~166) already correctly references `GetLawResponse` and D-024 — leave that intact. Verify no drift introduced.

**Step 3: Verification.**
- Re-read `container-view.md` §7; confirm the four edits above are present.
- `grep -n "title_snippet\|relevance\|capped at 50\|Phase 1b.1 (3 tools)" docs/architecture/container-view.md` returns new hits.
- `grep -n "snippet, score" docs/architecture/container-view.md` returns 0 hits (the old shape is gone).

**Commit:**

```
docs(container-view): sync §7 MCP table to shipped Phase 1b.1 contract

- search result shape: {snippet, score} → {category, title_snippet,
  relevance} (audit A-3, Medium); deliberate field renames + category
  additive, locked by tests/mcp_server/test_search.py.
- "snippet" qualified as title-only with FR-017 forward pointer
  (audit A-6, Low).
- limit cap (default 20, max 50) documented (audit A-7, Low).
- Phase tags split: 1b.1 ships 3 tools; history/diff/
  amendments_in_period strictly Phase 2 per D-027 (audit A-8, Low).

No code change; doc catches up to the implementation.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
```

### Task 6: Sync `runtime-flows.md` §6.3.3 to the actual search shape and document the two-tier ranker

**Audit findings:** A-3 (Medium, runtime-flows half), C-2 (Medium).

**Files affected:**
- Modify: `docs/architecture/runtime-flows.md`

**Step 1: Verification baseline.** Confirm runtime-flows.md §6.3.3 ASCII diagram (around line 244) shows the search response as `[{law_id, identificador, title, snippet, score}]`. Confirm there is no description of the two-tier ranker (title-restricted then body fallback) anywhere in §6.3.

**Step 2: Make the change.**

a) Update the §6.3.3 ASCII diagram's response line to read `[{law_id, identificador, title, category, title_snippet, relevance}]`. Preserve indentation and column widths so the diagram still aligns.

b) Below the ASCII diagram, add a new paragraph titled **"Two-tier ranking"** (or insert as a footnote under the existing D-022 paragraph):

> **Two-tier ranking.** `search_fts` issues two FTS5 MATCH queries in sequence. Tier 1 is a column-restricted match against `title:` (e.g. `title:обществен title:поръчк`) — high precision; documents whose title contains every query token are almost always the right answer. Tier 2 is general FTS5 over title+body — recall, catches body-only matches and abbreviations. Tier 2 is **skipped when tier 1 already filled the limit** (saves ~100 ms per query). Results are deduplicated by `law_id` (title-tier wins). Implemented in `index/fts.py:search_fts`; rationale: BM25 alone over title+body would invert canonical-title rankings (a law's implementing regulation, with a denser body match, would outrank the law itself). FR-015 tracks the Phase 1b.3 stemmer + synonym dictionary that will further refine ranking.

**Step 3: Verification.**
- Re-read §6.3.3; confirm the ASCII diagram now mentions `title_snippet` and `relevance`.
- Confirm a "Two-tier ranking" paragraph exists.
- `grep -n "title_snippet\|two-tier\|Tier 1\|Tier 2" docs/architecture/runtime-flows.md` returns new hits.

**Commit:**

```
docs(runtime-flows): sync §6.3.3 search shape and document two-tier ranker

- ASCII diagram updated to {category, title_snippet, relevance}
  (audit A-3 runtime-flows half).
- New "Two-tier ranking" paragraph documents the title-tier-then-body
  strategy implemented in index/fts.py:search_fts (audit C-2). The
  design doc only said "FTS5 + BM25"; the actual ranker is a two-stage
  pipeline whose rationale (BM25 inversions) is non-obvious from code.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
```

### Task 7: Update `COVERAGE-FLOOR.md` to clarify Phase 1b.1 ships 3 tools, Phase 2 adds 3

**Audit finding:** B-3 (Low).

**Files affected:**
- Modify: `docs/process/COVERAGE-FLOOR.md`

**Step 1: Verification baseline.** Confirm `COVERAGE-FLOOR.md` line ~21 reads "MCP server with at minimum: `get_law`, `search`, `get_article` tools (Phase 1b); extended with `history`, `diff`, `amendments_in_period` (Phase 2+); ..." — it correctly lists tools but doesn't tell a casual reader that Phase 1b.1 ships exactly the first three.

**Step 2: Make the change.** Insert a one-line clarification after the existing bullet:

> **Phase scoping (per D-027):** Phase 1b.1 ships exactly 3 tools (`get_law`, `search`, `get_article`); Phase 2 adds the other 3 (`history`, `diff`, `amendments_in_period`) once the temporal index (FR-001) is populated. The `get_municipal_ordinance` tool is Phase 6.

**Step 3: Verification.**
- Re-read `COVERAGE-FLOOR.md`; confirm the new line is present and references D-027.
- `grep -n "Phase 1b.1 ships exactly 3" docs/process/COVERAGE-FLOOR.md` returns 1 hit.

**Commit:**

```
docs(coverage-floor): clarify Phase 1b.1 vs Phase 2 MCP tool split (D-027)

The floor correctly enumerated the eventual six tools but didn't tell a
reader that 1b.1 ships exactly three. Adds a one-line phase-scoping
note pointing at D-027 (audit B-3, Low).

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
```

---

## BATCH 4 — process docs (B-1, B-2)

### Task 8: Tighten Phase-1b DoD in `delivery-contract.md` to point at the design doc §9 perf budgets

**Audit finding:** B-1 (Medium).

**Files affected:**
- Modify: `docs/process/delivery-contract.md`

**Step 1: Verification baseline.** Confirm `delivery-contract.md` lines ~116–120 (Phase 1b DoD) end with "Response times under 2 seconds for single-law queries" — the loose 2 s budget. Confirm the design doc §9 budget table (`docs/plans/2026-05-09-phase1b-mcp-design.md` lines ~336–343) lists `search<100ms`, `get_law historical<500ms`, `get_article<50ms` and that this is currently soft-asserted.

**Step 2: Make the change.** Replace the single "Response times under 2 seconds for single-law queries" line with a tighter, 1b.1-aligned bullet that:

a) States the budget table explicitly:

> Per-tool p95 latency budgets (soft assertions in 1b.1, hard in 1b.2 per D-027): `search` < 100 ms, `get_law` (current) < 100 ms, `get_law` (historical) < 500 ms, `get_article` < 50 ms.

b) Adds a forward pointer:

> Authoritative source: `docs/plans/2026-05-09-phase1b-mcp-design.md` §9. The "naredba" pathological single-word category query currently exceeds the 100 ms budget at ~290 ms p95 — tracked as FR-016 for Phase 1b.2 hardening.

c) Leave the other Phase 1b DoD bullets (`get_law()/search()/get_article()` working, Claude Code access) intact.

**Step 3: Verification.**
- Re-read `delivery-contract.md` Phase 1b DoD section; confirm the new bullet is present, the 2-second loose claim is gone, and a pointer to design §9 + FR-016 is present.
- `grep -n "100 ms\|FR-016\|design.md" docs/process/delivery-contract.md` should now return new hits.

**Commit:**

```
docs(delivery-contract): tighten Phase 1b DoD to design §9 perf budgets

The DoD said "<2s single-law" while the design doc and runbook bind
much tighter budgets (search<100ms, get_article<50ms, get_law<100ms).
1b.2 hardens these from soft to hard assertions per D-027; the contract
should already reflect the tightened numbers so 1b.2 hardening doesn't
look like scope creep (audit B-1, Medium).

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
```

### Task 9: Add a Phase 1b.1 testing-layers subsection to `test-strategy.md`

**Audit finding:** B-2 (Low).

**Files affected:**
- Modify: `docs/testing/test-strategy.md`

**Step 1: Verification baseline.** Confirm `test-strategy.md` §1 (Test Layers) has Unit / Integration / Validation / Contract sections, and that the Integration section's "MCP tool responses" bullet only says "Verify that `get_law()`, `search()`, `get_article()` return correct data for known laws in the test corpus" — no mention of FastMCP, in-memory `Client`, the `_AppHandle.call_tool_sync` shortcut, the perf-budget tier, or §7 acceptance suite.

**Step 2: Make the change.** Insert a new sub-section **"Phase 1b.1 testing layers"** under §1 (between Validation and Contract, or as a §1.5):

> **Phase 1b.1 testing layers.** The MCP server uses four practical testing layers, all running against an in-memory FastMCP app (no separate server process):
>
> - **L1 — Unit:** Pure functions. `bg_normalize`, `parse_article_spec`, `_legal_article_sort_key`, schema dataclass round-trips. Files under `tests/index/test_fts.py`, `tests/mcp_server/test_queries.py`, `tests/mcp_server/test_schemas.py`.
> - **L2 — Component:** Per-tool tests via the `_AppHandle.call_tool_sync(name, args)` shortcut. Skips JSON-RPC serialization; bound to a populated in-memory SQLite from the `populated_conn` fixture. Files: `tests/mcp_server/test_get_law.py`, `test_search.py`, `test_get_article.py`, `test_errors.py`.
> - **L3 — In-memory FastMCP `Client`:** Tests that exercise the JSON-RPC envelope itself, using `fastmcp.Client(handle.mcp)`. File: `tests/mcp_server/test_tools_e2e.py`.
> - **L4 — Acceptance:** §7 data-quality cases (slug ≠ title, null `fecha_publicacion`, empty titulo) and the perf-budget tier in `tests/mcp_server/test_data_quality_acceptance.py` and the soft-perf-assertion suite. Soft in 1b.1, promoted to hard in 1b.2 per D-027.
>
> The `populated_conn` conftest fixture stamps `current_commit = "a"*40` (FAKE_COMMIT_HASH) so the working-tree fast path in `_read_law_markdown` works against `tmp_path` without needing a real git repo.

**Step 3: Verification.**
- Re-read `test-strategy.md`; confirm the new sub-section is present.
- `grep -n "FastMCP Client\|call_tool_sync\|FAKE_COMMIT_HASH\|L1.*Unit" docs/testing/test-strategy.md` returns new hits.

**Commit:**

```
docs(test-strategy): describe the actual Phase 1b.1 testing layers

The strategy doc said MCP tests "verify tools return correct data";
the real harness is FastMCP Client + in-memory SQLite + the
_AppHandle.call_tool_sync shortcut. Adds a 4-layer breakdown so the
next maintainer understands the L1/L2/L3/L4 split before adding
tests (audit B-2, Low).

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
```

---

## BATCH 5 — code corrections + their docstrings (D-1+FR-018, D-8, D-9, C-3, C-4, C-6)

### Task 10: File FR-018 in `docs/frs/INDEX.md` for `get_article` range expansion

**Audit finding:** D-1 (deferral-without-trace) — the FR half.

**Files affected:**
- Modify: `docs/frs/INDEX.md`

**Step 1: Verification baseline.** Confirm `docs/frs/INDEX.md` table currently ends at FR-017. Confirm `mcp_server/server.py` `get_article` docstring around line 248 says "full range support tracked in FR-001 Phase 2" (which is wrong — FR-001 is the temporal index, not range support).

**Step 2: Make the change.** Append a new row to the FR table, immediately after FR-017:

| ID | Title | Phase | Priority | Status | Description |
|----|-------|-------|----------|--------|-------------|
| FR-018 | `get_article` range expansion | 2 (or 1b.3 if usage demands it) | Low | Backlog | `mcp_server.queries.parse_article_spec` already accepts `чл. 14-16`, but `mcp_server.server.get_article` returns only the row for `article=14`; the second and third articles in the range are silently dropped. Phase 1b.1 chose this rather than ship a partial range implementation that would interact awkwardly with `version_at_date` and the `valid_to` predicate. Future work: change `get_article` to return a `list[ArticleEntry]` when the spec parses to a range, OR add a separate `get_articles` tool that accepts a list of article numbers. Either path interacts with D-024's response shape and is therefore a contract change requiring preflight (Surface 3). Test scaffold for that milestone: `parse_article_spec("чл. 14-16")` should expand to a list of 3 articles. |

**Step 3: Verification.**
- Re-read `docs/frs/INDEX.md`; confirm FR-018 is now the last row and references the spec parser, the server-side handler, and the Surface 3 implication.
- `grep -n "FR-018" docs/frs/INDEX.md` returns 1 hit.

**Commit:**

```
docs(frs): file FR-018 for get_article range expansion

mcp_server/server.py:248 cited "FR-001 Phase 2" for the range deferral,
but FR-001 is the temporal index — range support had no FR (audit D-1,
the only deferred-without-FR finding). Adds FR-018 as the canonical
trace.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
```

### Task 11: Update `mcp_server/server.py` `get_article` docstring to point at FR-018

**Audit finding:** D-1 (code half).

**Files affected:**
- Modify: `mcp_server/server.py`

**Step 1: Verification baseline.** Confirm `mcp_server/server.py` `get_article` docstring around line 248 contains "full range support tracked in FR-001 Phase 2".

**Step 2: Make the change.** Replace `FR-001 Phase 2` with `FR-018` (and adjust the surrounding text so the docstring reads cleanly). Recommended:

```
"чл. 14-16" — range (only article=14 is returned in 1b.1; full range
    support tracked in FR-018).
```

**Step 3: Verification.**
- `grep -n "FR-018" mcp_server/server.py` returns 1 hit.
- `grep -n "FR-001 Phase 2" mcp_server/server.py` returns 0 hits (the old, wrong pointer is gone).
- `.venv/bin/pytest -q tests/mcp_server/ 2>&1 | tail -3` — same number passing as before (docstring-only change).

**Commit:**

```
docs(server): retarget get_article range deferral pointer at FR-018

The docstring cited "FR-001 Phase 2" but FR-001 is the temporal index;
range support is FR-018 per the audit (D-1). Comment-only change.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
```

### Task 12: Narrow `_run_match`'s `OperationalError` catch in `index/fts.py`

**Audit findings:** D-8 (silent-fail mild), C-3 (Low — partial overlap).

**Files affected:**
- Modify: `index/fts.py`
- Modify: `tests/index/test_fts.py`

**Step 1: Write failing test.** Add to `tests/index/test_fts.py`:

```python
import pytest
import sqlite3
from index.fts import _run_match, search_fts, create_laws_fts_table


def test_run_match_swallows_fts5_syntax_errors():
    """A query with FTS5-special syntax (lone '*', unbalanced quote) must
    return [] rather than raise — the resolver and search both depend on
    this fallback."""
    conn = sqlite3.connect(":memory:")
    create_laws_fts_table(conn)
    # Empty result is fine; what matters is no exception bubbles out.
    assert _run_match(conn, "*", category=None, limit=20) == []


def test_run_match_does_not_swallow_corrupt_index_errors():
    """A non-FTS5 OperationalError (e.g. table missing entirely, mirroring
    a corrupted/dropped FTS5 index) MUST propagate so the operator sees
    INDEX_STALE / INDEX_MISSING instead of silent empty results."""
    conn = sqlite3.connect(":memory:")
    # Deliberately do NOT create laws_fts; expect OperationalError to
    # propagate. The narrowed catch only suppresses fts5/syntax errors.
    with pytest.raises(sqlite3.OperationalError):
        _run_match(conn, "поръчки", category=None, limit=20)
```

Run: `.venv/bin/pytest -q tests/index/test_fts.py::test_run_match_does_not_swallow_corrupt_index_errors`. Expected to FAIL — current `_run_match` catches `sqlite3.OperationalError` unconditionally and would return `[]` instead of raising.

**Step 2: Make the change.** In `index/fts.py:_run_match`, narrow the `except` to mirror the resolver pattern at `mcp_server/queries.py:135-143`:

```python
    try:
        return conn.execute(sql, params).fetchall()
    except sqlite3.OperationalError as e:
        # FTS5 raises OperationalError for malformed query terms (special
        # chars '*', ':', unbalanced quotes, empty-after-tokenization).
        # Suppress those — the user gave us a string we can't tokenize,
        # so treat as no results. Other OperationalErrors (table missing,
        # DB locked, disk full, corruption) must propagate so callers
        # see INDEX_STALE / INDEX_MISSING instead of silent empty
        # results. Mirrors mcp_server.queries.resolve_name_to_law_id.
        msg = str(e).lower()
        if "fts5" not in msg and "syntax error" not in msg:
            raise
        return []
```

**Step 3: Verification.**
- Run both new tests — expected: 2 passed.
- Run full FTS test suite: `.venv/bin/pytest -q tests/index/test_fts.py tests/index/test_fts_regression.py 2>&1 | tail -3`. Expected: same green count plus the two new tests.
- Diff inspection: only the `except` block in `_run_match` changes; the SQL builder above is untouched.

**Commit:**

```
fix(fts): narrow _run_match OperationalError catch to FTS5 syntax only

The resolver in queries.py:resolve_name_to_law_id already narrows its
fallback catch to fts5/syntax-error messages so non-FTS5
OperationalErrors (e.g. table-missing on a corrupted index) propagate
as INDEX_STALE / INDEX_MISSING signals. _run_match was catching all
OperationalErrors and returning [], silently swallowing those signals
(audit D-8, silent-fail mild; C-3 partial overlap).

Adds two regression tests:
  - syntax-error path still returns []
  - missing-table path now raises OperationalError

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
```

### Task 13: Add WARN-level log to `mcp_server.server._split_frontmatter` on missing-frontmatter fallback

**Audit finding:** D-9 (silent-fail mild).

**Files affected:**
- Modify: `mcp_server/server.py`
- Modify: `tests/mcp_server/test_get_law.py` (or a new `tests/mcp_server/test_split_frontmatter.py` if cleaner)

**Step 1: Write failing test.** Add to the existing `test_get_law.py` (or split into a new file if isolation feels right):

```python
def test_split_frontmatter_warns_on_missing_delimiter(caplog):
    """When a Markdown file lacks the leading `---\\n` frontmatter
    delimiter, _split_frontmatter falls back to ({}, raw) — but it must
    emit a WARN log so operators see drift between the working-tree fast
    path and the build-time invariant (build raises on missing fm)."""
    import logging
    from mcp_server.server import _split_frontmatter

    raw_no_frontmatter = "# Just a body, no YAML frontmatter\n\nХ.\n"
    with caplog.at_level(logging.WARNING, logger="mcp_server.server"):
        fm, body = _split_frontmatter(raw_no_frontmatter)

    assert fm == {}
    assert body == raw_no_frontmatter
    assert any(
        "frontmatter" in rec.message.lower()
        and rec.levelname == "WARNING"
        for rec in caplog.records
    ), f"expected a WARN about missing frontmatter, got: {[(r.levelname, r.message) for r in caplog.records]}"
```

Run: `.venv/bin/pytest -q tests/mcp_server/test_get_law.py::test_split_frontmatter_warns_on_missing_delimiter`. Expected to FAIL — current `_split_frontmatter` returns silently.

**Step 2: Make the change.** Update `mcp_server/server.py:_split_frontmatter`:

```python
def _split_frontmatter(raw: str) -> tuple[dict, str]:
    """Split a Markdown file with YAML frontmatter into (frontmatter, body).
    Mirrors `index.build._parse_md` so the read path matches the write
    path; if the corpus invariant changes, both fix together.

    Behavior on missing `---\\n` prefix: returns ({}, raw) and emits a
    WARN log. The build path raises on missing frontmatter; the query
    path doesn't, because the working-tree fast path may legitimately
    encounter a hand-edited file mid-edit. Without the WARN, an operator
    could silently get titulo="" / eli=None responses (audit D-9).
    """
    if not raw.startswith("---\n"):
        log.warning(
            "frontmatter delimiter '---' missing at start of markdown; "
            "returning empty frontmatter dict (working-tree may be dirty "
            "or the file is hand-edited — re-run index.build if so)"
        )
        return {}, raw
    after_open = raw[4:]
    parts = after_open.split("\n---\n", 1)
    fm = yaml.safe_load(parts[0]) or {}
    body = parts[1] if len(parts) > 1 else ""
    return fm, body.lstrip("\n")
```

**Step 3: Verification.**
- Run the new test — expected: 1 passed.
- Run full MCP test suite: `.venv/bin/pytest -q tests/mcp_server/ 2>&1 | tail -3`. Expected: same green + 1 new.
- Diff inspection: only the early-return branch in `_split_frontmatter` and its docstring change; behavior on the happy path (with `---\n`) is identical.

**Commit:**

```
fix(server): WARN log on missing frontmatter fallback in _split_frontmatter

The build path (index/build._parse_md) raises on missing frontmatter,
but the query path silently returned ({}, raw) and produced get_law
responses with titulo="", eli=None. The intentional asymmetry (working-
tree may be mid-edit) stays — the new WARN log surfaces drift instead
of hiding it (audit D-9, silent-fail mild).

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
```

### Task 14: Document `_iso` PyYAML date coercion in `mcp_server/schemas.py` (C-4)

**Audit finding:** C-4 (Low).

**Files affected:**
- Modify: `mcp_server/schemas.py`

**Step 1: Verification baseline.** Confirm `mcp_server/schemas.py` `GetLawResponse` (around line 30+) lists `fecha_publicacion: str | None`, `ultima_actualizacion: str | None`, `effective_date: str | None` as ISO strings, and that there is no comment in either the dataclass or `mcp_server/server.py:_iso` explaining why PyYAML's `datetime.date` is coerced.

**Step 2: Make the change.** Add a short docstring sentence on the relevant fields of `GetLawResponse` (or one comprehensive comment at the top of the dataclass):

> All date fields are ISO 8601 strings (YYYY-MM-DD), not `datetime.date`. PyYAML parses unquoted ISO date scalars to `datetime.date`; `mcp_server.server._iso` coerces them back to strings so JSON-RPC consumers don't see Python objects. Quoted-string YAML date fields pass through unchanged.

**Step 3: Verification.**
- Re-read `mcp_server/schemas.py`; confirm the comment is present on `GetLawResponse` (or the date fields explicitly).
- Run `.venv/bin/pytest -q tests/mcp_server/test_schemas.py 2>&1 | tail -3` — same green (comment-only change).

**Commit:**

```
docs(schemas): document _iso PyYAML date coercion on GetLawResponse

Surfaces the implicit invariant that all date fields are ISO strings
(coerced from datetime.date when PyYAML returns them) so JSON-RPC
consumers never see Python objects (audit C-4, Low).

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
```

---

## BATCH 6 — runbook + remaining doc updates (B-4, C-4 runbook line, C-6)

### Task 15: Make the runbook smoke-test deterministic + document `check_same_thread=False`

**Audit findings:** B-4 (Low), C-6 (Low).

**Files affected:**
- Modify: `docs/runbook/2026-05-09-phase1b1-operator-setup.md`

**Step 1: Verification baseline.** Confirm:
- `docs/runbook/2026-05-09-phase1b1-operator-setup.md` lines ~95–99 use the wording "Expected: succeeds with `titulo: ""` ... and a `DATE_UNCERTAIN` warning if the act is also one of the 121 §7.2 acts." The "if" makes the smoke test non-deterministic.
- The runbook does not mention `check_same_thread=False` in `__main__.py:127` (the conftest does too) — operators have no explanation for why the SQLite connection skips the thread check.

**Step 2: Make the change.**

a) **Smoke-test determinism (B-4).** Pick a known §7.2 doc_id from the live catalog. Two options:
- Run `sqlite3 catalog.db "SELECT doc_id FROM laws WHERE law_id IN (SELECT law_id FROM law_versions WHERE date_uncertain = 1) LIMIT 1;"` to find one (do this locally; bake the result into the runbook).
- OR cite the test fixture pattern: `tests/mcp_server/conftest.py` already grabs one with `WHERE date_uncertain=1 LIMIT 1`; pull a real one and pin it.

Replace the third smoke-test line with the deterministic form:

> > What's the publication date of doc_id `<PINNED_DOC_ID>`?
>
> Expected: succeeds with a `DATE_UNCERTAIN` warning in the response (`source_date_marker: "unknown"`); `fecha_publicacion` may be null. This act is one of the 121 §7.2 acts whose lex.bg page had no parseable `.PreHistory`/`.HistoryOfDocument`.

If picking a pinned doc_id is not feasible at plan-execution time (e.g., the catalog hasn't been built), record a TODO at the top of Batch 6 saying "execute Step 2(a) only after running `python -m index.build` locally and capturing a real doc_id from `WHERE date_uncertain=1`". Do not ship the runbook with `<PINNED_DOC_ID>` unresolved.

b) **`check_same_thread=False` rationale (C-6).** Add a short paragraph to the runbook's "Server runtime" section (or, if no such section exists, add a new "Server runtime" sub-section just below "MCP host configuration"):

> **SQLite connection threading.** `mcp_server/__main__.py` opens the catalog connection with `check_same_thread=False`. FastMCP serves tool calls on a worker thread; SQLite would otherwise raise "SQLite objects created in a thread can only be used in that same thread." All writes happen at index-build time on a separate connection, so the runtime connection is read-mostly — no concurrent-write hazard. Tests use the same setting via the `populated_conn` conftest fixture.

c) **`_iso` coercion runbook line (C-4 runbook half — optional one-liner).** In the "Tools surfaced" table, append a sentence to the `get_law` row description: "Date fields are ISO strings (PyYAML's `datetime.date` is coerced by `mcp_server.server._iso`)."

**Step 3: Verification.**
- Re-read the runbook; confirm:
  - The third smoke-test prompt has a real doc_id (no `<PINNED_DOC_ID>` placeholder).
  - The "if" disclaimer is gone — the expected output is deterministic.
  - A "Server runtime" / `check_same_thread=False` paragraph is present.
  - The `get_law` row mentions ISO-string date coercion.
- `grep -n "check_same_thread\|_iso\|date_uncertain" docs/runbook/2026-05-09-phase1b1-operator-setup.md` returns hits.

**Commit:**

```
docs(runbook): deterministic smoke test + check_same_thread rationale

- Smoke test 3 now pins a real §7.2 doc_id instead of "if also §7.2"
  (audit B-4, Low). Operators get a yes/no result, not a maybe.
- New "Server runtime" paragraph documents check_same_thread=False
  (FastMCP worker thread); production AND conftest both use it
  (audit C-6, Low).
- get_law row mentions ISO-string date coercion via _iso (audit C-4
  runbook half).

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
```

---

## BATCH 7 — Deferral oversight register (NEW)

**Rationale:** Phase 1b.1 produced 6 cleanly-traced deferrals (FR-013..FR-017 + the 1b.2 perf-budget hardening). They live in `docs/frs/INDEX.md` mixed with always-scheduled future work (FR-001 etc.) and are NOT in the session-startup read path. The next operator opening this repo cannot tell which FRs are "we punted from a completed phase" vs "always Phase N+ work." This batch creates a focused register that the session protocol picks up automatically.

**Out of scope reminder:** the deferrals themselves (D-2..D-7) are NOT being implemented — they are being **registered for visibility** so the user has a single place to revisit them at every phase boundary.

### Task 16: Create `docs/sync/DEFERRED.md` register

**Files affected:**
- Create: `docs/sync/DEFERRED.md`

**Step 1: Verification baseline.** Confirm `docs/sync/` currently contains `ACTIVE.md`, `DECISIONS.md`, and the `HANDOFFS` directory. There is no `DEFERRED.md`.

**Step 2: Create the file.** Write `docs/sync/DEFERRED.md`:

```markdown
# Deferred Items

Items punted from a completed phase that need explicit revisit at phase boundaries. Distinct from `docs/frs/INDEX.md`, which is the broader future-work register including always-scheduled items (e.g., FR-001 was always Phase 2; it's not a deferral).

This file is read at session startup per the protocol in `.claude/CLAUDE.md`. Phase entry conditions in `docs/process/delivery-contract.md` require reviewing every row before promoting a phase.

## Format

Each row links the deferral to its FR (or DECISION) trace, the phase it was punted FROM, and the phase it's targeted FOR. Status column is one of:
- **Open** — deferral active, not yet revisited
- **Re-affirmed** — explicitly reviewed at a phase boundary, kept deferred (date stamped)
- **Implemented** — closed; FR row in `docs/frs/INDEX.md` updated to status "Done"
- **Withdrawn** — decided not to do; rationale recorded in `docs/sync/DECISIONS.md`

## Active deferrals

| ID | Title | Punted from | Target | Status | Last reviewed | FR / Decision |
|---|---|---|---|---|---|---|
| D-2026-05-09-01 | `bg_normalize` last-character-only suffix stripping (adjective long-form asymmetry) | Phase 1b.1 | Phase 1b.3 | Open | 2026-05-09 (filed) | [FR-013](../frs/INDEX.md) |
| D-2026-05-09-02 | `search` returns `title_snippet` (no body snippet) | Phase 1b.1 | Phase 1b.3 | Open | 2026-05-09 (filed) | [FR-017](../frs/INDEX.md) |
| D-2026-05-09-03 | Single-word category queries (`наредба`) overrun 100ms p95 budget | Phase 1b.1 | Phase 1b.2 | Open | 2026-05-09 (filed) | [FR-016](../frs/INDEX.md) |
| D-2026-05-09-04 | Synonym dictionary for Bulgarian abbreviations (ЗОП ↔ Закон за обществените поръчки) | Phase 1b.1 | Phase 1b.3 | Open | 2026-05-09 (filed) | [FR-015](../frs/INDEX.md) |
| D-2026-05-09-05 | Incremental index rebuild (currently full DELETE-then-INSERT each time) | Phase 1b.1 | Phase 4 | Open | 2026-05-09 (filed) | [FR-014](../frs/INDEX.md) |
| D-2026-05-09-06 | Soft perf assertions (test_budgets.py logs warnings, doesn't fail) | Phase 1b.1 | Phase 1b.2 | Open | 2026-05-09 (filed) | [D-027](DECISIONS.md) |

## Resolved deferrals

(empty — first phase to register deferrals is 1b.1)

## Phase-boundary review protocol

Before promoting from Phase X to Phase Y, the human reviews every Open row whose Target column is X. For each:
1. **Implement** — do the work; mark Status=Implemented; update the FR row in `docs/frs/INDEX.md`; commit.
2. **Re-affirm** — explicitly choose to keep deferred for documented reasons; update Last reviewed; optionally bump Target to a later phase. The re-affirmation rationale goes into a new `DECISIONS.md` entry.
3. **Withdraw** — decide not to do this work at all; mark Status=Withdrawn; new `DECISIONS.md` entry explaining why; the FR row in INDEX.md gets Status=Withdrawn too.

Phase promotion is blocked while any Open row in this file has Target ≤ X.

## Process notes

- ID format: `D-YYYY-MM-DD-NN` (deferral, audit/origin date, sequence within that day). Independent from FR numbering — an item has both a deferral ID (here) and an FR ID (in `frs/INDEX.md`).
- New deferrals get added at the bottom of the Active table, not interleaved with existing rows. Resolved items move to "Resolved deferrals" with a final Last-reviewed date.
- The session-startup protocol in `.claude/CLAUDE.md` lists this file in the read path; sessions should glance at it for phase-relevant Open rows.
```

**Step 3: Verification.**
- Re-read `docs/sync/DEFERRED.md`; confirm the 6 active deferrals are present, all have FR (or Decision) trace links, and the format follows the spec.
- `ls docs/sync/` shows the new file.
- The 6 deferral IDs map 1:1 to FR-013..FR-017 + D-027 (the 6 cleanly-traced deferrals from the audit).

**Commit:**

```
docs(sync): introduce DEFERRED.md register for phase-boundary revisits

Distinct from docs/frs/INDEX.md (which is the broader future-work
register including always-scheduled items): this file lists items
PUNTED from a completed phase that need explicit revisit at the next
phase boundary. Seeded with the 6 cleanly-traced deferrals from
Phase 1b.1's audit (FR-013, FR-014, FR-015, FR-016, FR-017, D-027).

Each row links to its FR/Decision trace, names the phase it was
punted from, and the phase targeted for resolution. Status workflow:
Open → Re-affirmed | Implemented | Withdrawn at every phase boundary.

Subsequent commits in this batch wire DEFERRED.md into:
  - .claude/CLAUDE.md session-startup read path
  - docs/process/delivery-contract.md per-phase DoD
  - .ahelia/protected-surfaces.yaml machine-readable deferrals block

Addresses the user's "where in oversight logic these deferrals need
more prominent recording" question.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
```

### Task 17: Wire `DEFERRED.md` into the session-startup read path in `.claude/CLAUDE.md`

**Files affected:**
- Modify: `/Users/ekimir/swprj/legalize-bg/.claude/CLAUDE.md`

**Step 1: Verification baseline.** Confirm `.claude/CLAUDE.md` "Session Startup Protocol" section reads:

```
1. Read this file
2. Read `docs/sync/ACTIVE.md` for current work state
3. Read `docs/process/delivery-contract.md` for process rules
4. Read the relevant `docs/prd/` or `docs/plans/` for task context
```

**Step 2: Make the change.** Insert step 2.5 (or renumber to 5 steps total):

```
1. Read this file
2. Read `docs/sync/ACTIVE.md` for current work state
3. Read `docs/sync/DEFERRED.md` for items punted from prior phases that may be relevant to current work
4. Read `docs/process/delivery-contract.md` for process rules
5. Read the relevant `docs/prd/` or `docs/plans/` for task context
```

**Step 3: Verification.**
- Re-read `.claude/CLAUDE.md`; confirm step 3 is now `docs/sync/DEFERRED.md`.
- `grep -n "DEFERRED.md" .claude/CLAUDE.md` returns 1 hit.

**Commit:**

```
docs(claude-md): add DEFERRED.md to session-startup read path

Sessions now see the deferral register on every startup, not just
when they go looking for it. Step 3 in the protocol; pushes the
phase-relevant Open rows in front of every operator.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
```

### Task 18: Add a Phase-DoD gate to `docs/process/delivery-contract.md`

**Files affected:**
- Modify: `docs/process/delivery-contract.md`

**Step 1: Verification baseline.** Confirm `delivery-contract.md` has per-phase DoD sections (Phase 1a, Phase 1b, Phase 2, etc.). Confirm none of them currently reference `DEFERRED.md` or "deferral review."

**Step 2: Make the change.**

a) Add a new universal sub-section just above the per-phase DoD blocks (or at the top of the "Definition of Done" section if one exists):

> **Universal phase-promotion gate.** Before promoting from any phase X to phase Y, every Open row in `docs/sync/DEFERRED.md` whose Target column is X (or earlier) must be reviewed and resolved (Implemented / Re-affirmed with date / Withdrawn). Phase promotion is blocked while any such row remains Open. Re-affirmations require a new `docs/sync/DECISIONS.md` entry stating why the deferral is being kept.

b) For each existing per-phase DoD block, add as the LAST bullet:

> - All Open rows in `docs/sync/DEFERRED.md` with Target ≤ this phase have been resolved per the universal phase-promotion gate above.

(Apply to Phase 1a, 1b, 2, 3, 4, 5, 6 DoD blocks — wherever they exist.)

**Step 3: Verification.**
- Re-read `delivery-contract.md`; confirm the universal gate paragraph is present and every per-phase DoD ends with the deferral-review bullet.
- `grep -n "DEFERRED.md\|phase-promotion gate" docs/process/delivery-contract.md` returns multiple hits.

**Commit:**

```
docs(delivery-contract): add deferral-review gate to phase promotion

Every phase X → Y promotion now requires resolving all Open rows in
docs/sync/DEFERRED.md whose Target ≤ X. Re-affirmations need an
accompanying DECISIONS.md entry. Forces explicit human review of
deferred items at every phase boundary instead of letting them slip.

Each per-phase DoD block also gains a deferral-review bullet so the
gate is visible from any phase's local checklist, not just the
universal section.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
```

### Task 19: Add machine-readable `deferrals:` block to `.ahelia/protected-surfaces.yaml`

**Files affected:**
- Modify: `.ahelia/protected-surfaces.yaml`

**Step 1: Verification baseline.** Confirm `.ahelia/protected-surfaces.yaml` has top-level `paths:` and `rules:` blocks but no `deferrals:` block. (Task 1 will have already updated the MCP signatures by the time this task runs; build on that state.)

**Step 2: Make the change.** Add a new top-level `deferrals:` block at the end of the file (after `rules:`):

```yaml
# --- Deferred Items ---
# Mirror of docs/sync/DEFERRED.md in machine-readable form so future
# CI / pre-commit hooks can flag changes touching a surface with an
# open deferral against it. Source of truth: docs/sync/DEFERRED.md;
# this YAML is regenerated when that file changes.

deferrals:
  - id: D-2026-05-09-01
    fr: FR-013
    title: bg_normalize last-character-only stripping
    punted_from: 1b.1
    target: 1b.3
    status: open
    surfaces_affected:
      - "index/fts.py:bg_normalize"

  - id: D-2026-05-09-02
    fr: FR-017
    title: search title_snippet (no body snippet)
    punted_from: 1b.1
    target: 1b.3
    status: open
    surfaces_affected:
      - "mcp_server/queries.py:full_text_search"
      - "mcp_server/schemas.py:SearchHit"

  - id: D-2026-05-09-03
    fr: FR-016
    title: single-word category queries overrun perf budget
    punted_from: 1b.1
    target: 1b.2
    status: open
    surfaces_affected:
      - "index/fts.py:search_fts"
      - "tests/perf/test_budgets.py"

  - id: D-2026-05-09-04
    fr: FR-015
    title: synonym dictionary for Bulgarian abbreviations
    punted_from: 1b.1
    target: 1b.3
    status: open
    surfaces_affected:
      - "index/fts.py:bg_normalize"
      - "mcp_server/queries.py:full_text_search"

  - id: D-2026-05-09-05
    fr: FR-014
    title: incremental index rebuild
    punted_from: 1b.1
    target: 4
    status: open
    surfaces_affected:
      - "index/build.py"

  - id: D-2026-05-09-06
    decision: D-027
    title: soft perf assertions (1b.2 hard-promote)
    punted_from: 1b.1
    target: 1b.2
    status: open
    surfaces_affected:
      - "tests/perf/test_budgets.py"

deferrals_meta:
  authoritative_source: docs/sync/DEFERRED.md
  last_synced: 2026-05-09
  promotion_rule: "Phase X → Y blocked while any open deferral has target ≤ X."
```

**Step 3: Verification.**
- Run `python -c "import yaml; yaml.safe_load(open('.ahelia/protected-surfaces.yaml'))"` — confirm the YAML still parses.
- `grep -n "deferrals:\|D-2026-05-09" .ahelia/protected-surfaces.yaml` returns multiple hits.
- Re-read the file; confirm the 6 deferrals match `docs/sync/DEFERRED.md` row-for-row.

**Commit:**

```
docs(protected-surfaces): add machine-readable deferrals block

Mirrors docs/sync/DEFERRED.md so future CI / pre-commit hooks can
flag changes touching a code surface with an open deferral against
it. Each entry lists its FR (or DECISION) trace, the phases it
spans, and the source files it locks. Source of truth stays
docs/sync/DEFERRED.md; this YAML is regenerated when that file
changes.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
```

---

## Definition of Done

A green test run plus the verification points below.

- [ ] Batch 1: `.ahelia/protected-surfaces.yaml` lists D-024 typed-dict signatures; Phase 2 tools split into a sub-block; YAML still parses.
- [ ] Batch 2: `docs/data/schema-reference.md` Section 3 lists all 4 migrations + `schema_version`; inclusive-`valid_to` predicate stated explicitly; `text_hash` documented as 16-char SHA-256 prefix; `mcp_server/queries.py` comments retargeted to §2 "Predicate semantics"; `canonical-data-model.md` documents one-anchor-per-paragraph and missing-identificador refusal.
- [ ] Batch 3: `container-view.md` §7 search row shows `{category, title_snippet, relevance}`, mentions title-only + 50-cap; Phase 2 tools tagged Phase 2; `runtime-flows.md` §6.3.3 ASCII diagram updated and two-tier ranker documented; `COVERAGE-FLOOR.md` clarifies 1b.1 ships 3 tools.
- [ ] Batch 4: `delivery-contract.md` Phase 1b DoD points at design §9 budgets; `test-strategy.md` documents L1-L4 testing layers.
- [ ] Batch 5: FR-018 filed; `mcp_server/server.py` retargets to FR-018; `_run_match` narrowed catch + 2 regression tests pass; `_split_frontmatter` WARN log + 1 regression test passes; `mcp_server/schemas.py` documents `_iso` ISO-string contract.
- [ ] Batch 6: Runbook smoke-test pinned to a real §7.2 doc_id; `check_same_thread=False` documented; `get_law` row mentions `_iso` coercion.
- [ ] Batch 7: `docs/sync/DEFERRED.md` exists with 6 active deferrals; `.claude/CLAUDE.md` session-startup protocol reads it; `delivery-contract.md` adds the universal phase-promotion gate + per-phase deferral-review bullets; `.ahelia/protected-surfaces.yaml` carries the machine-readable `deferrals:` block.
- [ ] Full test suite green: `.venv/bin/pytest -q 2>&1 | tail -3` reports 215 passed (212 existing + 3 new: 2 in `test_fts.py` for D-8, 1 in `test_get_law.py` for D-9).
- [ ] No new files outside the modifications listed; no schema migrations; no changes to `bg_normalize` or response shapes (Surface 3 + Surface 6 untouched).
- [ ] Each batch landed as its own commit (or its tasks landed as separate commits) with the trailing `Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>` line.

## Out-of-scope (re-stated for the executor's safety)

- D-2..D-7 (six cleanly-traced deferrals) — pending separate user decision. Batch 7 REGISTERS them in `DEFERRED.md` for visibility but does NOT implement them.
- Soft-perf-assertion → hard-assertion promotion — D-027 binds this to Phase 1b.2; not this plan.
- Any actual implementation of FR-013/14/15/16/17 or FR-018 — they are filed as backlog only.
- Range-expansion code in `get_article` — FR-018 is the trace; the implementation is Phase 2 / future-session.
- Any change to the `provisions` table content, `bg_normalize` rules, or MCP response shape (Protected Surfaces 3 and 6).
