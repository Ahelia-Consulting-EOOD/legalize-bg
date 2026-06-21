# Handoff: 2026-06-21 — Corpus re-scrape / wholesale refresh (parallel track)

**Author:** ekimir session (Claude Opus 4.8, 1M context), 2026-06-21
**Repo HEAD at handover:** `3d754027` (`main`)
**Working tree:** clean (the stray `NOTE-ukazi-coverage.md` was removed this session)
**Test suite:** 287 passing (`.venv/bin/python -m pytest -q`, ~13 s)
**Relationship to other tracks:** This runs **in parallel** with the main roadmap session, which is doing **Phase 2 (temporal index)**. The two do not touch the same code. This track touches the corpus + fetcher; Phase 2 touches `mcp_server/` + `index/`. Coordinate the SQLite index rebuild (see §8).

---

## 0. One-paragraph brief

Re-scrape lex.bg and **refill the corpus as a fresh snapshot.** Treat lex.bg's current consolidated text as ground truth. For every act: if it's **new** (doc_id on lex.bg but not in our corpus) → add it; if it's **changed** (rendered text differs from what we committed in April) → replace the file **in place** (same slug); if it's **gone** from lex.bg's tree → **leave it in the corpus** (repealed/отменен acts stay — see §4). We do **not** care about per-amendment provenance, diffs at alinea level, or historical reconstruction — that's Phase 3/4 and is explicitly out of scope here. This is a coarse "re-photograph lex.bg" pass.

**Why this is correct (not a hack):** lex.bg already does the legal consolidation; re-scraping yields 100%-accurate current text for free (lex.bg is the project's validation oracle). The only thing this loses vs the future Phase 4 engine is alinea-level provenance. The wholesale snapshots it produces also become a **validation oracle for Phase 4 later** (April-text + DV-patches should equal the June snapshot), so this is scaffolding, not waste.

---

## 1. The baseline (what "changed since" means)

- The corpus was scraped on **2026-04-20** (confirmed: bootstrap commit *committer* dates = 2026-04-20; corpus `.md` file mtimes = 2026-04-20). Today is 2026-06-21 → a **~62-day** delta.
- **lex.bg has no time machine** — it only ever serves *current* consolidated text. So "lex.bg as of April" cannot be re-fetched. The **only** surviving April snapshot is *our own committed corpus*. Therefore change detection = *re-scrape today* vs *the committed corpus*. Our git repo **is** the baseline.
- Commit-date convention in this repo (verified): **author date = legislative/publication date** (e.g. Конституция → `1991-07-13`), **committer date = wall-clock of the scrape**. Honor this for new commits (§5).

---

## 2. Corpus state today (the "before")

| Category dir | Count | lex.bg tree slug | tree pages |
|---|---|---|---|
| `laws/` | 395 | `laws` | 12 |
| `codes/` | 24 | `code` | 1 |
| `ordinances/` | 2604 | `ords` | 75 |
| `regulations/` | 490 | `regs` | 14 |
| `implementing/` | 60 | `reg_laws` | 2 |
| **total** | **3573** | — | **104** |

Source of these mappings: `fetcher/bg/discovery.py:CATEGORIES_CONFIG` + `CATEGORY_DIRS`.

---

## 3. Reusable tooling (≈80% already exists — do NOT rebuild these)

| Need | Use | File |
|---|---|---|
| Enumerate all current acts on lex.bg | `CatalogCrawler().crawl_all(transport)` → `[{doc_id, name, category}]` | `fetcher/bg/discovery.py` |
| Rate-limited / retried / CF-halting HTTP | `RateLimitedSession`, `HttpTransport`, `TreeTransport` | `fetcher/bg/client.py`, `bootstrap.py` |
| Fetch + cp1251-decode + parse one act | `LexBgClient(transport).fetch_soup(doc_id)` | `fetcher/bg/client.py` |
| HTML → Markdown body | `HtmlToMarkdown().convert(soup)` | `fetcher/bg/text_parser.py` |
| Extract frontmatter (incl. `amendment_history`) | `MetadataParser().parse(soup, doc_id, category)` | `fetcher/bg/metadata.py` |
| Assemble final `.md` (frontmatter + body) | `assemble_file(meta, body)` | `fetcher/bg/assembler.py` |
| Slug from title | `generate_slug(title)` | `fetcher/bg/assembler.py` |
| Git commit with legislative author-date | `bootstrap._git_commit`, `bootstrap._format_author_date` | `bootstrap.py` |
| Look up existing doc_id → slug | `SELECT law_id, doc_id, category, title, status FROM laws` | `catalog.db` / `index/catalog.py` |
| Rebuild SQLite index (full) | `python -m index.build --corpus . --db catalog.db` | `index/build.py` |

**What is MISSING and must be built:** a single **refresh orchestrator** (suggest `monitor/refresh.py` or top-level `refresh.py`) that ties these together with the algorithm in §4. Estimate: a few hundred lines + tests, ~1–2 days, plus ~75–90 min to run.

---

## 4. The algorithm

```
1. Crawl the catalog (104 tree pages, ~2 min):
     lex_now = CatalogCrawler().crawl_all(TreeTransport(session))
     lex_ids = { e['doc_id'] for e in lex_now }

2. Load the corpus catalog from SQLite:
     corpus = { row['doc_id']: row for row in laws table }   # doc_id -> {law_id(slug), category, status, title}
     corpus_ids = set(corpus.keys())

3. Partition:
     ADDED    = lex_ids - corpus_ids
     EXISTING = lex_ids & corpus_ids
     MISSING  = corpus_ids - lex_ids   # gone from lex.bg tree

4. For each ADDED doc_id:
     fetch -> convert -> parse metadata
     slug = unique_slug(generate_slug(titulo), against ALL existing slugs)   # NEW slug, deduped globally
     write category/<slug>.md ; git commit  [nova]  (author-date = fecha_publicacion)

5. For each EXISTING doc_id:
     fetch -> convert -> parse metadata -> assemble_file(meta, body) = candidate
     committed = read current category/<existing_slug>.md
     if normalize(candidate) != normalize(committed):
         overwrite category/<existing_slug>.md   # SAME slug — see §5 gotcha #1
         git commit  [reforma]  (author-date = latest amendment date from fresh amendment_history)
         # use [popravka] instead if the body changed but amendment_history did NOT grow (corrigendum)
     else: skip (unchanged)

6. For each MISSING doc_id:
     DO NOT delete the file. Log it. Optionally set estado: vigente -> derogado in frontmatter
     and commit [otmyana] (author-date = today). Expect this set to be ~0. See below.

7. After all writes: python -m index.build --corpus . --db catalog.db   (full rebuild, ~45 s)
```

**On "delete deleted (should be zero)":** a doc_id disappearing from lex.bg's browse tree almost always means the act was **repealed (отменен)**, not that it vanished. Per owner instruction, **repealed acts STAY in the corpus** — their historical text is the point. So MISSING → *keep the file*, optionally flip `estado` to `derogado` and add a `[otmyana]` marker commit. Only ever hard-delete a file if you positively confirm it was published in error (effectively never). Treat any non-empty MISSING set as something to **report and eyeball**, not auto-delete.

**Change-detection signal (step 5):** compare the freshly-*assembled* file against the committed file after light normalization (collapse whitespace, normalize quotes — same normalization the design's lex.bg-oracle comparison uses). A coarse full-file compare is fine here ("don't care about diffs"). If you want fewer false positives from cosmetic HTML churn, use the **`amendment_history` delta** as the primary signal (did the fresh metadata gain DV references the committed frontmatter lacks?) and fall back to a body hash for corrigenda. Either is acceptable; full-file compare is simplest.

---

## 5. Critical gotchas (read before writing code)

1. **🔴 SLUG STABILITY — the #1 risk.** `index/build.py` derives `law_id = path.stem`, i.e. **the filename slug IS the MCP handle.** If a refresh renames a file (because the title changed, or because `generate_slug` produces a different result, or because the `-2/-3` collision counter is assigned in a different order), the act's `law_id` silently changes and every external reference to it breaks. **Therefore: for EXISTING acts, reuse the slug already recorded in `laws.law_id` for that doc_id. Never regenerate it.** Do NOT reuse `bootstrap._unique_slug` as-is — it dedups against a *fresh in-memory set each run*, which is correct for a one-shot bootstrap but wrong for a refresh. Mint new slugs only for genuinely new doc_ids, deduped against the set of ALL existing corpus slugs.

2. **Commit dates.** Match the repo convention: `GIT_AUTHOR_DATE` = legislative date, `GIT_COMMITTER_DATE` = same (via `bootstrap._format_author_date`). For `[reforma]`, author-date = the **latest** amendment date from the freshly-scraped `amendment_history`. For `[nova]`, author-date = `fecha_publicacion`. Pre-1970 dates clamp to `1970-01-01` (D-017/D-018) — `_format_author_date` already handles this.

3. **Commit types** (from `delivery-contract.md`): `[nova]` new act · `[reforma]` amended · `[popravka]` corrigendum · `[otmyana]` repeal marker (file stays). Each corpus commit body MUST carry `Source-Id`, `Source-Date`, `Norm-Id` (see `bootstrap._git_commit` for the exact format).

4. **Rate limit is sacred.** 1 req/sec, enforced by `RateLimitedSession`. Full run ≈ 104 tree pages + 3,573 acts ≈ **~75–90 min** wall-clock (delivery-contract estimates ~2 h, conservatively). A **Cloudflare challenge halts the run** (`CloudflareChallenge` is intentionally not caught) — do not attempt to bypass; stop and report.

5. **Branch discipline — `main` history is sacred.** Do the refresh on a feature branch (e.g. `refresh/2026-06`), review, then merge. `bootstrap.py` already refuses `--push-every` without `--branch` for this reason; the refresh runner should follow the same rule.

6. **Resumability.** A ~90-min run WILL get interrupted eventually. Bootstrap has no per-act skip. Add a resume mechanism: a small state file of processed doc_ids, or check whether the act's file already reflects the fresh scrape this run. Make the run idempotent so re-invoking continues rather than re-committing.

7. **Degenerate acts (FR-011).** ~128 acts have empty `titulo` (7) or null `fecha_publicacion` (121). The refresh will re-encounter them. Handle gracefully — don't crash; preserve their existing slug; don't let a null date break `_format_author_date` (it returns `None`, callers skip the env var). These remain a Phase-5 G2 triage item, not this track's problem.

8. **Index rebuild is full DELETE-then-INSERT** (~45 s; `index/build.py:_drop_content_rows`). FR-014 (incremental rebuild) is deferred to Phase 4 — full rebuild is fine here. `catalog.db` is gitignored (derived); never commit it.

---

## 6. What to produce

1. The `refresh` orchestrator + unit/component tests (fakes for the transport, à la the existing fetcher tests in `tests/fetcher/`).
2. A **change report** at the end: counts + lists of ADDED / CHANGED / MISSING(kept), and any fetch failures.
3. The corpus commits (`[nova]` / `[reforma]` / `[popravka]` / `[otmyana]`) on a feature branch.
4. A rebuilt `catalog.db`.
5. A close-out updating `docs/sync/ACTIVE.md` + `DECISIONS.md`, and a row in this HANDOFFS index.

---

## 7. Out of scope (do NOT do these here)

- No ЗИД consolidation, no alinea-level patching (Phase 4).
- No historical-version reconstruction / reverse-apply (FR-009, Phase 5+).
- No DV (dv.parliament.bg) monitoring (Phase 3) — this is a *manual lex.bg re-pull*, not the automated differential pipeline.
- No changes to `mcp_server/` tool signatures (Protected Surface — would need IMPLEMENTATION-PREFLIGHT).
- No schema migration (the existing `laws`/`law_versions`/`provisions` schema is sufficient).

---

## 8. Coordination with the Phase 2 (temporal index) session

- **Shared artifact:** `catalog.db` (gitignored, derived). Both this track and Phase 2 rebuild it via `index.build`. Whoever lands last rebuilds; it's deterministic from the corpus + git HEAD, so order doesn't corrupt anything — just rebuild after merging both branches.
- **Corpus = input to Phase 2.** Phase 2 reads `amendment_history` frontmatter to backfill `law_versions`. This refresh *updates* that frontmatter for changed acts. **Net effect: run Phase 2's index build AFTER this refresh merges, so it sees the freshest `amendment_history`.** Not a blocker — just a sequencing note for the final index rebuild.
- **No code-file overlap.** This track: `fetcher/bg/`, new `refresh` module, corpus `.md`. Phase 2: `mcp_server/`, `index/` (new temporal query funcs). Clean separation.

---

## 9. Gates before merge

- `.venv/bin/python -m pytest -q` green (the 287 existing tests use fixtures, not the live corpus — they should stay green; add new tests for the refresh runner).
- `python -m mcp_server.export_tools --output tools.json --check` → OK (no tool-schema drift; this track shouldn't touch tools, so it must stay OK).
- Frontmatter still validates for all acts (G2): 8 mandatory fields present; valid UTF-8, no cp1251 artifacts.
- Smoke test: rebuild index, run `search` / `get_law` / `get_article` against a known changed act and confirm fresh text.
- The MISSING set was eyeballed (not auto-deleted) and any `estado` flips are deliberate.

---

## 10. Close-out (executed 2026-06-21)

Delivered on branch **`refresh/2026-06`** (off `main` @ `3d754027`). Tooling commit + 276 corpus commits; **not pushed** — ready for owner review/merge. Decision logged as **D-030**.

### Results

| Outcome | Count | Commit type |
|---|---|---|
| New acts added | 26 | `[nova]` |
| Amended (amendment_history grew) | 184 | `[reforma]` |
| Corrigenda (body changed, history did not) | 66 | `[popravka]` |
| Effectively unchanged (no on-disk change) | 3,305 | — |
| Gone from lex.bg tree — **KEPT** | 18 | — (report-only) |
| Fetch errors / Cloudflare halts | 0 | — |

Corpus **3,573 → 3,599** acts. **276** single-file corpus commits (`git rev-list 27adc2b3..HEAD`). Working tree clean; SQLite index rebuilt to 3,599 acts.

### What changed vs the plan (all improvements, none deviated from intent)

1. **Staleness probe added** (§5 risk the plan under-specified): the crawler's hardcoded `CATEGORIES_CONFIG` page counts are 62 days stale and physically cannot see acts on newer pages — exactly the new acts a refresh exists to find. `crawl_with_probe` crawls one page past each category's configured count and reports new acts found beyond it, WITHOUT editing the protected `discovery.py`. This run: **`STALE={}`** — counts still complete (the 26 new acts fit on existing pages).
2. **doc_id→file map sourced from the corpus on disk**, not `catalog.db` (gitignored/derived) — removes a stale/absent-DB dependency.
3. **Idempotent commit guard:** `_git_commit_typed` no-ops when nothing is staged. Gives resume idempotency AND absorbed **16 benign `classify_change` over-triggers** (acts flagged changed whose re-assembled bytes were identical) → 0 empty commits.

### Bug caught by code review before merge

`refresh.py` first wrote ADDED acts to the lex.bg **tree slug** dir (`ords`/`regs`) instead of the **corpus dir** (`ordinances`/`regulations`) — only `laws` maps to itself, so 25 of 26 new acts in the first run landed where the index never scans. Found by the contract-required code review, fixed under TDD (regression test uses a non-`laws` category), branch hard-reset and re-run clean.

### Open items for the owner

- **The 18 MISSING acts** (all `estado: vigente`, kept as-is) — eyeball whether any warrant an `estado: derogado` flip. Notable: `2137247022 ПРАВИЛНИК ЗА ОРГАНИЗАЦИЯТА И ДЕЙНОСТТА НА НАРОДНОТО СЪБРАНИЕ` left the tree while a **new** правилник of the same name was ADDED (slug `…-2`) — old NS rules superseded by new ones. The rest are mostly 2005–2013 veterinary/health наредби. To act: `python refresh.py --flip-missing-estado` (commits `[otmyana]`, estado→derogado, file kept). Full list:
  - `2135506845`, `2135515370`, `2135516067`, `2135518328`, `2135526211`, `2135526865`, `2135533188`, `2135535977`, `2135535978`, `2135536200`, `2135553161`, `2135576453`, `2135785028`, `2135828375`, `2135880580`, `2137240577`, `2137247022`, `2137255124`.
- **Index rebuild ordering (§8):** rebuild once more after BOTH this branch and Phase 2 merge.
- **`history_grew` over-trigger** (the 16): benign (idempotent guard catches it); file an FR only if it recurs at scale.
