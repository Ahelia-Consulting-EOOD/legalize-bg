# Preflight: FR-032 — per-article (per-segment) FTS5 index

Filed 2026-07-21 with the plan PR (design: `docs/plans/2026-07-21-fr032-per-article-fts-design.md`;
CPD: `docs/cpd/CPD-2026-07-21-per-article-fts.md`). Template: `docs/process/IMPLEMENTATION-PREFLIGHT.md`.
Status: **UNBLOCKED 2026-07-23** — plan PR #15 merged; owner ratified D-056 with design §11
Q1–Q5 answered (see the CPD's Ratification section). Implementation proceeding on
`feat/fr032-per-article-fts`.

- **protected surface:** 4 (SQLite schema) — primary; touches Surface 3 (MCP tool
  interfaces) only additively; Surface 6 (index builder / FTS normalizer) per-act
  segmentation added, `bg_normalize` itself UNCHANGED.
- **authoritative source:** `docs/data/schema-reference.md` (schema v4 today);
  `index/migrations.py` (D-025 forward-only); design doc §5.
- **hard constraint confirmed:** yes. The 4 core tables (`laws`, `law_versions`,
  `amendments`, `provisions`) and their PK/FK relationships are UNTOUCHED; the
  protected indexes (`idx_versions_date`, `idx_amendments_target`,
  `idx_provisions_article`) are UNTOUCHED. What changes is FTS-virtual-table DDL
  only: `laws_fts` is dropped and recreated title-only (FTS5 cannot be ALTERed) and
  `articles_fts` is added — both via a new forward-only migration 005, never by
  editing shipped migrations 001–004.
- **what is changing:**
  1. Migration 005: `DROP TABLE laws_fts` → recreate `laws_fts(law_id UNINDEXED,
     title, category UNINDEXED)` → create `articles_fts(law_id UNINDEXED, seg_no
     UNINDEXED, kind UNINDEXED, label UNINDEXED, body, category UNINDEXED)`; same
     tokenizer `unicode61 remove_diacritics 2` (D-022) on both.
  2. `index/fts.py`: `insert_fts_row` → `insert_title_row` + `insert_segment_rows`;
     `FTS_BODY_MAX_BYTES`/`_cap_utf8` (PR #13, spec v1.2) retired — superseded by
     `SEG_MAX_BYTES` segment chunking (design Decision 2).
  3. New `index/segments.py` (pure body→segments function) with the corpus-wide
     coverage invariant *concat(segments) == body* as a build/verify gate.
  4. `search_fts` tier 2 re-targeted to `articles_fts` with best-segment (MIN bm25)
     act aggregation; tier 1 unchanged on title-only `laws_fts`.
  5. `index/build.py` full + FR-014 incremental paths write/delete `articles_fts`
     rows; `catalog.db` requires one full rebuild post-migration (derived artifact).
  6. Downstream, same release: `export_cf` D1 emission + committed cf-data-plane
     spec v2.0; `cf-worker` search port + recaptured parity goldens.
- **violation risk:** (a) recall loss if segmentation drops text → coverage
  invariant is a hard machine gate, full-corpus; (b) ranking regression → locked
  ranking tests must pass UNCHANGED + golden-diff owner review (design §7); (c)
  cross-plane float drift → parity gate recaptured once, then float-exact; (d)
  destructive-migration hazard → `laws_fts` content is derived (rebuilt from the
  corpus in ~1 min), no source-of-truth data is destroyed; core tables untouched.
- **allowed scope confirmed:** partially additive. Adding `articles_fts` = "adding
  new tables" (allowed). Recreating `laws_fts` without its `body` column is a
  destructive DDL change to a documented (derived) table → per Surface 4, filed
  as requiring preflight + migration script; migration 005 IS that script, and the
  full-rebuild requirement is documented in the design (§5) and will be in the
  schema-reference update + runbook.
- **waiver required:** no for `articles_fts`; the `laws_fts` recreation rides this
  preflight (destructive-in-form, non-destructive-in-substance: the table is a
  derived index over git-tracked corpus text, and the "rebuild script tested against
  full corpus before deploy" follow-up in the Surface-4 template is an explicit
  implementation gate).
- **owner confirmation:** direction agreed 2026-07-21 (dispatch for this plan);
  ratification = merge of the plan PR + answers to design §11 Q1–Q5.
- **implementation may proceed:** YES (2026-07-23, D-056 ratified). Discipline: TDD,
  measurement spike first (design §8), full-corpus rebuild gate, standing
  fresh-subagent per-task review loop, coordinated four-component rollout (§12).
