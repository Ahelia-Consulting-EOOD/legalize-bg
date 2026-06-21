# Preflight: FR-014 — incremental index rebuild

Filed 2026-06-21 (batch 2.x-c, item 3). Template: `docs/process/IMPLEMENTATION-PREFLIGHT.md` §"Approval Template".

- **protected surface:** 6 (Index Builder + FTS Normalizer)
- **authoritative source:** `docs/process/IMPLEMENTATION-PREFLIGHT.md` §"Protected Surface 6"; `.ahelia/protected-surfaces.yaml`; `docs/plans/2026-05-09-phase1b-mcp-design.md` §6.1.
- **hard constraint confirmed:** yes. `index/build.py` must stay idempotent and rebuildable from any git ref; `bg_normalize` symmetry untouched; `provisions` populated to article+alinea level (D-023); FTS5 tokenizer unchanged. Closes open deferral **D-2026-05-09-05** (FR-014).
- **what is changing:**
  1. **DRY refactor (behavior-preserving):** extract the per-act insert logic from `build()`'s loop into `_reindex_act(conn, cat, path, head, today_iso)` and `_delete_act_rows(conn, law_id)`. The full-build path calls the same helper, so full-build output is byte-identical (verified by the existing `tests/index/` suite + an oracle check).
  2. **New incremental mode:** `build(..., incremental=True)` (default `False` → unchanged full DELETE-then-INSERT). When `incremental=True` AND the catalog already holds a single consistent indexed commit `base`:
     - compute changed acts via `git diff --name-status base HEAD -- <category dirs>` → Added / Modified / Deleted `law_id`s;
     - Deleted → `_delete_act_rows`; Added/Modified → `_delete_act_rows` then `_reindex_act` (commit_hash = HEAD);
     - bump unchanged acts' commit pointers: `UPDATE laws SET current_commit = HEAD` and `UPDATE law_versions SET commit_hash = HEAD WHERE commit_hash = base` (an unchanged act's file is byte-identical at HEAD, so re-pointing is correct and preserves the working-tree fast path + staleness check);
     - **fallback to full build** when: catalog empty, `base` unreadable / non-unique, or `base == HEAD` short-circuits to a no-op pointer-bump.
- **`bg_normalize` / FTS:** UNCHANGED. `_reindex_act` calls the same `insert_fts_row` (symmetric `bg_normalize`); no normalization or tokenizer change → no re-index-of-the-world required for THIS change (the incremental path is opt-in; full build remains the default and is unchanged).
- **SQLite schema:** UNCHANGED (no new columns/tables/indexes). Change detection uses git, not a new hash column — so no Surface-4 schema touch.
- **violation risk:** the danger is silent catalog corruption (stale/missing rows, commit-pointer inconsistency). Mitigations: (a) the incremental result is verified **equal to a full rebuild** of the same HEAD via an oracle test (dump all content tables, compare); (b) idempotence retained (re-running incremental is a no-op); (c) full build stays the default, so existing operators/CI are unaffected unless they opt in; (d) FR-020 interaction noted (when multi-version `law_versions` lands, the `WHERE commit_hash = base` pointer-bump must be revisited).
- **allowed scope confirmed:** yes — Surface 6 allows additive build-path changes that preserve idempotence + symmetry + D-023. No `bg_normalize` semantics change → no waiver.
- **waiver required:** no.
- **owner confirmation:** ekimir — via review of the 2.x-c PR (owner-merge).
- **implementation may proceed:** yes (TDD; oracle-verified vs full rebuild; clean-context review before merge).
