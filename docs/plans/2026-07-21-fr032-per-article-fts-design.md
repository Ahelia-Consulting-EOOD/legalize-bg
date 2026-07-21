# FR-032 — Per-Article (Per-Segment) FTS5 Index: Design Proposal

**Date:** 2026-07-21
**Status:** PROPOSED — owner agreed with the direction 2026-07-21; implementation gated on this design's ratification (D-056) and on `IMPLEMENTATION-PREFLIGHT-2026-07-21-fr032-per-article-fts.md` (Protected Surface 4: SQLite schema).
**Decision record:** `docs/cpd/CPD-2026-07-21-per-article-fts.md`
**Lineage:** D-051 option (b) "split body FTS index" (deferred 2026-07-02) → D-054 re-affirmation with structural-remedy pointer (2026-07-04) → D1 2 MB value cap forcing body truncation of 3 acts (PR #13, spec v1.2, 2026-07-20) → this design.
**No implementation in this PR.** This document + the CPD + the preflight + ledger registration only.

---

## 1. Problem

The FTS5 search index (`laws_fts`, migration 002) holds **one row per act**: the entire
normalized markdown body of each act is a single FTS document. Three independent
pressures now point at the same structural fix:

1. **D1 recall loss (the trigger).** Cloudflare D1 rejects values ≥ 2,000,000 bytes.
   Three acts (наредба за качеството на социалните услуги, КСО, Кодекс за
   застраховането) exceed that in normalized form, so spec v1.2 / PR #13 caps the
   indexed body at 1,900,000 UTF-8 bytes **in both planes** to keep bm25 float-parity.
   The capped tail is invisible to search: for the largest capped act, measurement
   shows ~95% of its body mass sits in appendices *after* the cap-relevant region —
   text that D-047 remediation went to great lengths to restore is again partially
   unsearchable on the Cloudflare plane, and (post-#13) on the local plane too.
2. **Body-only query latency (the registered deferral).** Tier 2 of `search_fts` is a
   full-corpus MATCH over 223M chars; genuinely body-only queries measure 5.4–6.5 s
   cold (D-051 accepted this; D-054 re-affirmed the deferral naming "the structural
   body-FTS split" as the real remedy; DEFERRED row `D-2026-07-02-01` is Open on
   exactly this).
3. **Snippet quality.** `snippet()` runs on the *title* column only (body-snippet via
   FTS5 on 1 MB documents was the 1b.1 perf killer); body snippets are a Python-side
   ±60-char window over the raw stored body (`_make_body_snippet`), opt-in and capped
   at the top 2 hits. Per-segment documents make FTS5's own `snippet()` cheap and
   precise, and let search answer *"which article matched"* — a capability the web UI
   (Phase 7.2) wants for deep links.

## 2. Current state (measured 2026-07-21, catalog.db @ 3,602 acts)

| Fact | Value |
|---|---|
| `laws_fts` rows (one per act) | 3,602 |
| `laws_fts` normalized body mass | 222,950,575 chars |
| `provisions` rows | 451,699 (146,577 article-whole + 305,122 alinea) |
| Acts with ≥ 1 provision row | 3,470 / 3,602 (132 acts have zero) |
| Article-whole text mass | 127,044,399 chars = **57% of body mass** |
| Per-act coverage (article-whole ÷ body): ≥80% / 50–80% / 20–50% / <20% / zero / empty-body | 1,406 / 1,097 / 460 / 507 / 125 / 7 |
| Largest single article-whole text | 59,198 chars (~116 KB UTF-8) |
| Article-whole rows > 45,000 chars | 1 |
| Largest capped act body (наредба соц. услуги) | 1,336,598 raw chars; 57 `Чл.` anchors, 9 `§`, 25 `Приложение`; ~95% of mass after the first appendix |
| D1 plane today (PR #12 run) | 373 MB SQL → ~459 MB database; FTS 3,602 rows, 3 truncated |

**The decisive fact:** the union of `provisions` text is only 57% of the indexed body.
The missing 43% is § -numbered ПЗР/ДР paragraphs (the provisions extractor anchors on
`Чл. N` only — `index/provisions.py:_ARTICLE_RE`), appendix/приложение blocks (the
dominant mass in the low-coverage tail and in all 3 capped acts), preambles/amendment
headers, and chapter/section headings. **Any design that indexes "the provisions
table" instead of "the body, segmented" re-creates D-047-class recall loss at index
level.** This drives Decision 2 below.

## 3. Goals / non-goals

**Goals**
- G1 — **Full recall on both planes**: every character of every act's normalized body
  is indexed; the v1.2 cap (`FTS_BODY_MAX_BYTES`) is structurally retired.
- G2 — **Ranking safety**: title-tier behavior byte-identical; all locked ranking
  tests pass unchanged; body-tier act ordering changes are reviewed, not accidental.
- G3 — **Cross-plane parity**: Python/sqlite3 and D1 produce float-identical bm25 on
  the new index, as today (v1 discipline restored, no permanent tolerance).
- G4 — **Snippet quality**: body snippets come from FTS5 `snippet()` over the matched
  segment; search can attribute a hit to an article/§/appendix label.
- G5 — **A path to closing DEFERRED `D-2026-07-02-01`**: after the split, a real
  cold-connection body-only budget becomes lockable (measure first — see §8).

**Non-goals**
- Bulgarian stemmer (FR-021 — unchanged, own effort).
- Alinea-level FTS granularity (see Alternatives, §10).
- Any breaking MCP/REST contract change (tools.json stays 1.3.x-additive;
  `openapi-rest.json` response shapes unchanged).
- Historical/multi-version FTS (index stays a current-text index, as today).
- Touching the corpus, `provisions`, `law_versions`, R2 layout, or `get_article`.

## 4. Design decisions

### Decision 1 — Two-index split: act-level titles, segment-level bodies

- **`laws_fts` becomes title-only** (columns: `law_id` UNINDEXED, `title`,
  `category` UNINDEXED; same tokenizer). Tier 1 (`title:`-qualified match) runs
  against it exactly as today — same documents, same title token statistics, so
  title-tier bm25 and ordering are **unchanged by construction**, not by luck.
- **New `articles_fts`** holds one row per body *segment*:

  ```sql
  CREATE VIRTUAL TABLE articles_fts USING fts5(
      law_id   UNINDEXED,   -- act slug (join key)
      seg_no   UNINDEXED,   -- 0-based position of the segment within the act
      kind     UNINDEXED,   -- 'article' | 'para' | 'annex' | 'preamble' | 'other'
      label    UNINDEXED,   -- 'чл. 5', '§ 3', 'приложение 2', '' — display/citation label
      body,                 -- bg_normalize()-d segment text (the ONLY indexed column)
      category UNINDEXED,
      tokenize='unicode61 remove_diacritics 2'
  );
  ```

  Rationale for two tables over one segment table carrying title copies: duplicating
  the act title into every segment row would multiply title token frequencies by the
  act's segment count, silently re-weighting tier-1 ranking; the split makes G2's
  "title tier unchanged" a structural property.

### Decision 2 — Index the body via a full-coverage segmenter, not the provisions table

New module `index/segments.py` (pure function: markdown body → ordered segments),
sharing `index/provisions.py`'s article-anchor regex but with a stronger contract:

- **Coverage invariant (the load-bearing rule):** concatenating all segment texts of
  an act reproduces the act's body exactly (modulo nothing). Every character belongs
  to exactly one segment. This is a machine-checkable gate (§9) — the design's answer
  to the 57%-coverage trap and the D-047 lesson.
- Segment boundaries: `Чл. N` anchors (existing `_ARTICLE_RE`), `§ N` anchors
  (ПЗР/ДР), `Приложение …` anchors, with markdown headings and any inter-anchor
  residue glued to the *following* segment (text before the first anchor = one
  `preamble` segment; acts with no anchors at all — 125 zero-provision acts — index
  as a single `other` segment, preserving today's recall for them).
- **Oversized-segment chunking:** any segment whose normalized text exceeds
  `SEG_MAX_BYTES` (proposed 400,000 UTF-8 bytes; final value is an implementation
  calibration, see §11 Q4) is split at paragraph boundaries into continuation
  segments (`seg_no` increments; same `kind`/`label`). This is what actually retires
  the 2 MB cap: the capped acts are appendix-dominated, and a whole `Приложение` can
  exceed 2 MB on its own. Per-article rows without this rule would NOT fix the
  problem the cap was introduced for.
- Known hazard, accepted: quoted anchors inside amendment text (e.g. a `Чл. 5.`
  quoted inside a ПЗР — the duplicate-article-id case PR #14 documented) create
  spurious segment boundaries. Harmless for recall (the text is still indexed, the
  coverage invariant still holds) and harmless for ranking (two smaller docs instead
  of one); only the advisory `label` may be wrong. Labels are display metadata, not
  lookup keys — `get_article` continues to resolve via `provisions`, untouched.

### Decision 3 — Query pipeline: tier 2 aggregates segments to acts

`index/fts.py:search_fts` keeps its shape (normalize → tier 1 → early-return gate →
tier 2 → dedup → rang-tier sort). Changes:

- **Tier 1: unchanged** (runs on title-only `laws_fts`; same `_TIER2_MIN_TITLE_HITS`
  gating from D-051).
- **Tier 2** MATCHes `articles_fts` and aggregates to act level — an act's relevance
  is its **best segment's bm25** (min, since SQLite bm25 is
  lower-is-better):

  ```sql
  SELECT a.law_id, l.doc_id, l.title, a.category,
         snippet(articles_fts, 4, '<b>', '</b>', '...', 12) AS seg_snippet,
         a.label, a.kind,
         MIN(bm25(articles_fts)) AS score
    FROM articles_fts a JOIN laws l USING(law_id)
   WHERE articles_fts MATCH ?
   GROUP BY a.law_id
   ORDER BY score LIMIT ?
  ```

  SQLite defines bare columns in a MIN/MAX aggregate to come from the winning row,
  so `label`/`seg_snippet` describe the best-matching segment. **Portability caveat:**
  auxiliary functions (`snippet()`) inside a GROUP BY over an FTS5 MATCH must be
  validated on D1 during prototyping; the fallback is the *overscan* form (plain
  `ORDER BY bm25 LIMIT limit×K`, first-wins dedup by `law_id` in Python/TS — the
  dedup loop already exists in both ports). Which form ships is an implementation
  detail behind the same function signature; the prototype task (§8) decides once,
  and both planes ship the same form (parity requires identical SQL).
- **Aggregation = MIN (best segment), not SUM/AVG.** "The act contains a provision
  strongly about X" is the right act-level signal for legal search; SUM rewards long
  acts mentioning X often but diffusely (the exact inversion FR-015's rang-tiers were
  built to fight), AVG punishes comprehensive codes for having many non-matching
  articles. Recorded as an owner-visible choice (§11 Q1).
- **Body snippets:** `_make_body_snippet` (Python ±60-char window; worker
  `makeBodySnippet`) is retired. Tier-2 hits carry their segment snippet for free.
  For title-served hits with `include_body=True`, one additional `articles_fts`
  MATCH scoped by `law_id IN (top-N ids)` fetches best-segment snippets — one extra
  MATCH per opt-in search, bounded, replacing today's two ≥1 MB row materializations
  + Python scan. `body_snippet` stays a string field; no schema change.
- Unchanged and shared: `bg_normalize` symmetry (D-022), FR-016 stop-word reject,
  FR-015 synonym expansion + rang-tier sort, 512-char query cap, the
  OperationalError user-input allowlist (applies to the new MATCH identically).

### Decision 4 — bm25 semantics change is accepted and managed, not hidden

Per-segment documents change document-length statistics, so every bm25 float and the
act ordering of body-tier results will differ from v1. This is the point (per-segment
idf/length normalization is what improves precision), but it is managed by the
three-layer parity strategy in §7 — including the rule that the `relevance` field's
*semantics* ("negated bm25, higher = better, comparable within one result set only")
are already documented and remain true; absolute values were never contractual.

## 5. Schema migration

- **Migration 005** (`index/migrations.py`, forward-only per D-025):
  `DROP TABLE laws_fts` (FTS5 virtual tables cannot be ALTERed) → recreate title-only
  → `CREATE VIRTUAL TABLE articles_fts …`. Destroying-and-recreating a *derived*
  virtual table is within Surface 4's spirit (no core-table columns dropped; the four
  core tables and their indexes are untouched) but the preflight is filed anyway
  because the DDL of a schema-reference-documented table changes — see the preflight
  doc for the full checklist.
- `catalog.db` is gitignored/derived: after migrating, **a full rebuild is
  mandatory** (`python -m index.build`); the migration leaves both FTS tables empty
  rather than attempting in-place re-segmentation. The FR-014 incremental path is
  updated (`_delete_act_rows`/`_reindex_act` gain `articles_fts` handling).
- `index/fts.py`: `insert_fts_row` splits into `insert_title_row` +
  `insert_segment_rows` (driven by `index/segments.py`); `FTS_BODY_MAX_BYTES` and
  `_cap_utf8` (PR #13) are **retired** — superseded by `SEG_MAX_BYTES` chunking.
- `docs/data/schema-reference.md` updated in the implementation PR (schema v5).

## 6. Affected surfaces (coordinated four-component change)

| Component | Branch/state today | Change |
|---|---|---|
| Index builder (`index/`) | `main` (+PR #13 cap) | segmenter module, migration 005, build/incremental wiring, cap retirement |
| Query layer (`index/fts.py`, `mcp_server/queries.py`) | `main` | tier-2 rework, snippet source, `_make_body_snippet` retirement; REST (`api/`) and MCP consume it unchanged |
| Exporter (`export_cf/`) | PR #12 (`feat/cf-export`) | `ddl.py` emits both FTS DDLs; `d1.py` fts series → `articles_fts` rows (idempotent guard on `law_id`+`seg_no`; append-slicer retained for the handful of >90 KB segments); manifest counts segments; verify.py extended |
| Worker (`cf-worker/`) | PR #14 (`feat/cf-worker`) | `fts.ts` two-table port, `makeBodySnippet` retirement, parity goldens recaptured |

Contract surfaces: **no breaking change** to tools.json (1.3.0) or
`docs/api/openapi-rest.json`. Proposed *additive* field on search hits —
`matched: {kind, label}` (which article/§/appendix matched) — is §11 Q3; if
approved it is a minor-version bump on both contracts, exercised by the web UI later.

**Spec gap to close in Phase 0:** the cf-data-plane spec (v1.0→v1.3.2, cited
throughout PRs #12–#14 and in `export_cf` docstrings) is not committed to any repo.
The implementation phase commits it as `docs/api/cf-data-plane-spec.md` and bumps it
to **v2.0** (articles_fts schema, segment rules, chunking constants) as part of the
exporter task — the spec must live where its enforcing code lives.

## 7. Ranking-parity strategy (G2/G3)

Three layers, in order of hardness:

1. **Invariants (machine-enforced, must pass unchanged):** every locked ranking test
   — `tests/index/test_fts.py`, `tests/index/test_fts_regression.py`, the FR-015
   adversarial fixture ("обществени поръчки" → ЗОП above its implementing reg),
   rang-tier tests, FR-016/synonym tests — passes **without edits**. These encode the
   owner-visible ranking guarantees; per D-051 precedent (which shipped tier-gating
   with zero test edits), any needed edit here is a red flag escalated to the owner,
   not silently absorbed.
2. **Golden-diff review (human-judged, once):** before/after top-10 act orderings for
   a fixed ~30-query set (the `scripts/perf_probe.py` representative queries, the
   regression-corpus queries, plus 3 new *cap-recall* queries that match only inside
   the formerly-truncated tails of the 3 capped acts). Acceptance: title-served
   queries identical; every body-tier ordering change explained by the per-segment
   model (better article precision) in a short reviewed table in the implementation
   PR. The cap-recall queries MUST return the capped acts — the headline acceptance
   criterion of the whole effort.
3. **Cross-plane float parity (machine-enforced, permanent):** Python/sqlite3 and D1
   compute over byte-identical `articles_fts` content and identical SQL → bm25 floats
   match exactly; the cf-worker parity gate (59 goldens + new segment goldens) is
   recaptured **once** post-rebuild and then holds float-exact. During the rollout
   window the v1.2-style *sanctioned-temporary* relevance tolerance applies, with the
   same explicit removal condition (both planes on v2 index) — that mechanism already
   exists in `cf-worker/parity/run.mjs`.

## 8. Performance expectations and measurement gate

Honest prior: the token mass is identical (~223M chars either way), so tier-2 postings
work does not shrink; what changes is document structure (≈165–175K segment docs
estimated: 146,577 articles + §/annex/preamble residue vs 3,602), snippet cost
(collapses — no more MB-row materialization), and a new GROUP BY/dedup step.
Body-only cold latency (the 5.4–6.5 s case) is *expected* to improve mainly via
cheaper snippet/row handling, but **this design does not promise a number**.
Per D-051 discipline:

- The **first implementation task is a spike**: build `articles_fts` on the live
  catalog, run `scripts/perf_probe.py` A/B (both query forms from Decision 3, cold +
  warm, stdio-warm and fresh-connection), and record results in a research doc before
  the query-layer rework proceeds.
- Perf budgets are then **re-ratified** (D-051-style decision entry), including —
  finally — a lockable cold-connection body-only budget, closing DEFERRED
  `D-2026-07-02-01` (Implemented or explicitly re-affirmed with the new numbers).
- D1 plane: ~459 MB → est. +5–10% (per-row FTS overhead ≈165K rows), far under D1's
  10 GB; import time roughly proportional to dump size; export/import runbook
  unchanged in shape.

## 9. Test strategy

- **Segmenter unit tests:** coverage invariant (`"".join(seg.text) == body`) on
  synthetic acts + the real pathological set (наредба соц. услуги, КСО, Кодекс за
  застраховането, a zero-provision act, an act with quoted `Чл.` in ПЗР); chunking at
  `SEG_MAX_BYTES` with byte-exact reassembly (mirrors the PR #12 slicer test).
- **Full-corpus build gate:** every act's segment-char sum == its body-char count
  (the invariant, corpus-wide, in the build or a `verify_catalog`-style check);
  segment-count sanity vs provisions counts.
- **Ranking:** layer 1 + 2 of §7.
- **Parity:** layer 3 of §7 (vitest fixture corpus gains multi-segment acts; goldens
  recaptured; sanctioned-temporary tolerance removed at cutover).
- **Perf:** §8 spike + re-ratified `tests/perf` budgets.
- **Contract:** `tools.json --check`, `api.export_openapi --check` — both unchanged
  unless §11 Q3 approves the additive field.

## 10. Alternatives considered

| Alternative | Why rejected |
|---|---|
| Index the `provisions` table directly | 57% coverage; 132 acts invisible; §/annex/preamble text lost — index-level D-047 recurrence (§2) |
| Alinea-level granularity (305K+ rows) | Tiny documents distort bm25 length normalization; 2× row count for no retrieval-unit gain — the article is the citation unit; alineas remain served by `get_article` |
| Keep one-row-per-act + raise/split the D1 value differently (e.g. body in R2, contentless FTS) | Contentless/external-content FTS5 breaks `snippet()` or reintroduces a second content store to keep in sync across planes; doesn't help latency or snippet quality |
| Single `articles_fts` with title copied into every row | Multiplies title token stats by segment count → uncontrolled tier-1 ranking change (violates G2) |
| Act-level relevance = SUM/AVG of segment bm25 | SUM re-creates the FR-015 length-bias inversion; AVG punishes comprehensive codes (Decision 3) |
| Postpone until the D-051 option-(b) trigger ("web PRD 300 ms p95 miss") formally fires | The D1 cap already causes *recall* loss today — a correctness regression, not a latency budget; waiting couples a correctness fix to a perf trigger it doesn't depend on |

## 11. Open questions for the owner (ratify with D-056)

1. **Q1 — Aggregation:** MIN (best segment) as designed? (Recommended; alternatives
   rejected in §10.)
2. **Q2 — Sequencing vs open PRs:** recommended order is **merge #13 → #12 → #14
   first** (the ratified v1.2/v1.3 baseline, already parity-gated 59/59), then land
   FR-032 as spec v2.0 across all four components in one coordinated branch. The
   alternative — rebasing the open cf PRs onto per-article before merge — re-does
   parity goldens twice for no user-visible gain. PR #13's cap then lives one release
   and is retired by FR-032 (its 2 tests are superseded by chunking tests).
3. **Q3 — Additive `matched: {kind, label}` field** on search hits (MCP + REST),
   for web-UI deep links? (Recommended: yes, in the same implementation cycle —
   additive per Surface 3.)
4. **Q4 — `SEG_MAX_BYTES` = 400 KB** starting value (any value ≤ ~1.8 MB is safe for
   D1; smaller = finer chunks + more rows; calibrated during the §8 spike).
5. **Q5 — DEFERRED `D-2026-07-02-01` disposition** at landing: close as Implemented
   with a locked budget, or re-affirm with new numbers (decided by spike data).

## 12. Rollout (coordinated, with rollback)

0. **Phase 0 (this PR):** design + CPD + preflight + FR-032/D-056 ledger rows.
1. Merge #13/#12/#14 per Q2; production Cloudflare plane runs v1 (capped) baseline.
2. One branch `feat/fr032-per-article-fts`: spike (§8) → builder (+migration 005,
   segmenter, gates) → query layer → exporter (+committed spec v2.0) → worker, each
   task with the standing fresh-subagent review loop (per the 2026-07-04 codified
   preference), locked tests green throughout.
3. Full rebuild → `export_cf` run → import into a **fresh D1 database** (v2 name,
   not in-place) → parity gate against the local FastAPI on the rebuilt index →
   flip the Worker's `DB` binding → keep the v1 D1 database + dump until the parity
   report and the cap-recall goldens pass in production, then retire them.
4. Rollback at any point = re-point the binding to the v1 database (local plane:
   rebuild from any prior commit — `catalog.db` is derived; the corpus is never
   touched).
