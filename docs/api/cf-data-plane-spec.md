# Cloudflare Data-Plane Specification (cf-data-plane-spec)

**Version: 2.0** (2026-07-24)
**Status: normative.** Enforcing code: `export_cf/` (emitter and `--verify`
self-check), consumed by `cf-worker/` (D1/R2 serving plane).
**History note:** versions 1.0 through 1.3.2 of this spec were cited
throughout PRs #12, #13 and #14 and in `export_cf` docstrings but were never
committed to any repository. This document closes that gap (FR-032 design,
section 6) and is the first committed edition; the v1.x rules it absorbs are
reconstructed from the merged commits listed in section 9.

## 1. Purpose

The legalize-bg corpus is served from two planes:

- the **index plane**: the git-tracked Markdown corpus plus the derived
  `catalog.db` (SQLite, schema version 5), built by `python -m index.build`
  and served locally by FastAPI/MCP;
- the **Cloudflare data plane**: a D1 database (metadata + FTS) and an R2
  bucket (article payloads), served by the `cf-worker` with FastAPI-parity
  semantics.

`export_cf` is the one-way bridge: a read-only pass over `catalog.db` and the
corpus checkout that emits importable artifacts. This spec fixes the artifact
formats, the emission rules, and the import semantics so that the exporter,
the importer (`wrangler d1 execute` / R2 upload), and the worker can evolve
independently.

## 2. Artifact tree

```
cf-export/
  d1-schema.sql            D1 schema (section 3)
  d1-meta-NNNN.sql         copied-table INSERT series (section 4)
  d1-fts-laws-NNNN.sql     laws_fts title rows, idempotent (section 5)
  d1-fts-articles-NNNN.sql articles_fts segment rows, idempotent (section 5)
  manifest.json            counts, guards, hashes (section 7)
  r2/
    acts/<law_id>.json     act payload with baked articles map
    versions/<law_id>/...  historical version payloads
    meta/stats.json        precomputed /stats payload
```

`NNNN` is a 1-based zero-padded sequence per series. Chunk files are at most
12,000,000 bytes (12 MB; 50 MB chunks kept D1's import long-poll open long
enough to hit transient "fetch failed" aborts) and break ONLY at statement
boundaries: string literals contain raw newlines (legal text), so the only
safe split points are the `;\n` statement ends, and every emitted chunk is
independently executable in sequence.

## 3. D1 schema

`d1-schema.sql` contains, in order, with every statement normalized to
`CREATE ... IF NOT EXISTS` so the file is re-runnable:

1. The four copied tables, DDL read verbatim from the source catalog's
   `sqlite_master` (post-migration shape, e.g. `law_versions.date_uncertain`
   from migration 004): `laws`, `law_versions`, `amendments`,
   `schema_version`.
2. The two carried indexes: `idx_versions_date`, `idx_amendments_target`.
   (`provisions` and its indexes are never exported; article text lives in
   R2.)
3. Both FTS5 virtual tables, declared IDENTICALLY to `index/migrations.py`
   migration 005 (the worker copies its MATCH SQL from `index/fts.py`, so
   column names, order and tokenizer must not drift):

```sql
CREATE VIRTUAL TABLE IF NOT EXISTS laws_fts USING fts5(
    law_id UNINDEXED,
    title,
    category UNINDEXED,
    tokenize='unicode61 remove_diacritics 2'
);

CREATE VIRTUAL TABLE IF NOT EXISTS articles_fts USING fts5(
    law_id UNINDEXED,
    seg_no UNINDEXED,
    kind UNINDEXED,
    label UNINDEXED,
    body,
    category UNINDEXED,
    tokenize='unicode61 remove_diacritics 2'
);
```

`laws_fts` is title-only (one row per act). `articles_fts` holds one row per
body segment produced by `index/segments.py`: `seg_no` is the per-act
0-based emission order, stored as TEXT; `kind` is one of `article`, `para`,
`annex`, `preamble`, `other`; `label` is an advisory display hint (for
example `чл. 5`, `§ 3`, `приложение 1`). `title` and `body` carry
`bg_normalize()`d text, byte-identical to what the index builder wrote.

The raw FTS shadow tables (`laws_fts_data`, `articles_fts_idx`, ...) are
never exported; D1 builds its own clean index from the INSERTs.

## 4. Emission rules

- **No transaction control.** D1's import path rejects BEGIN/COMMIT; each
  statement is atomic on D1.
- **Statement budget: 90,000 UTF-8 bytes**, strict and total (head + tuples
  + separators + terminator). D1 rejects statements over roughly 100 KB with
  SQLITE_TOOBIG; the 10 KB margin absorbs accounting drift.
- **Row order: source rowid order** for every series. FastAPI parity
  requires D1 to preserve catalog insertion order (AMBIGUOUS_NAME candidate
  lists and no-ORDER-BY scans follow it). For `articles_fts` this equals
  per-act `seg_no` emission order.
- **d1-meta series:** plain multi-row `INSERT INTO t (cols) VALUES ...`
  statements, at most 500 rows per statement, byte budget enforced first.
- **d1-fts-laws series:** one guarded single-row statement per act (section
  5). Titles (live maximum about 1.6 KB) never approach the budget; a title
  that would overflow it aborts the export.
- **d1-fts-articles series:** one guarded statement group per segment row.
  A row whose lone INSERT fits the budget emits as one statement. A row
  whose body is too large (segments run up to 400,000 bytes, well past the
  statement budget) is **sliced**: the INSERT carries the largest
  char-boundary prefix whose SQL-escaped form fits, and each remaining slice
  is appended with a guarded
  `UPDATE articles_fts SET body = body || '<slice>' ...` statement. Slices
  are raw substrings, so their concatenation reproduces the body
  byte-exactly. On the live corpus (2026-07-24 build: 3,602 acts, 182,084
  segment rows) about 456 segments exceed the effective budget and slice.

## 5. Idempotent import semantics

D1 import success is not reliably observable client-side: a "fetch failed"
attempt may have committed server-side (the v1.3.2 double-application
incident). The series therefore split by retry class:

- **d1-meta is NOT idempotent.** Import it exactly once, into EMPTY tables
  (drop and recreate via `d1-schema.sql` first). It is a separate series
  precisely so a partially loaded database can reload it without touching
  the FTS series.
- **Both fts series are FULLY idempotent.** Blind retries of any chunk, any
  number of times, at any point, are safe:
  - `laws_fts` INSERTs are per-row
    `INSERT ... SELECT ... WHERE NOT EXISTS (SELECT 1 FROM laws_fts WHERE
    law_id = ...)`.
  - `articles_fts` INSERTs carry the same guard at **(law_id, seg_no)**
    granularity:
    `WHERE NOT EXISTS (SELECT 1 FROM articles_fts WHERE law_id = ... AND
    seg_no = ...)`.
  - Append UPDATEs are keyed on the same (law_id, seg_no) pair AND guarded
    by `length(CAST(body AS BLOB)) = <bytes-before-this-slice>`, so every
    slice applies exactly once regardless of retries or partial prefixes.
  - Statements are keyed on column values, never rowids: D1 import has no
    `last_insert_rowid` persistence across statements.

## 6. Segment size contract (retires the v1.2 body cap)

`index/segments.py` chunks every emitted segment so its normalized body is
at most **SEG_MAX_BYTES = 400,000 UTF-8 bytes** (ratified D-056 Q4; the
spike measured a 1.83 MB single annex, so chunking, not per-article rows
alone, is load-bearing). Consequences for this plane:

- **Nothing is ever truncated.** The v1.2 rule ("indexed FTS body =
  bg_normalize(body) truncated to 1,900,000 bytes") and the
  `FTS_BODY_MAX_BYTES` constant are retired; FTS recall no longer diverges
  for any act.
- **D1's 2,000,000-byte value cap is structurally unreachable** (the
  largest possible value is 5x smaller; live maximum 399,891 bytes).
- The exporter TRUSTS the contract but enforces it: any `articles_fts` body
  over 400,000 bytes aborts the export (it means a mis-built catalog, and
  the fix is `python -m index.build`, not exporter-side truncation).

## 7. manifest.json keys

| Key | Meaning |
|---|---|
| `exported_at` | the ONLY timestamp in the export (determinism rule) |
| `counts` | per-table D1 row counts, including `laws_fts` (titles) and `articles_fts` (segments), plus `acts_json` / `versions_json` file counts |
| `max_fts_body_bytes` | largest emitted `articles_fts` body; must be at most 400,000 (replaces the retired `fts_truncated` list) |
| `max_statement_bytes` | largest emitted SQL statement; must be at most 90,000 |
| `fts_guards` | `{"inserts": N, "updates": N}` guarded-statement counts across BOTH fts series |
| `files` | sha256 per top-level artifact (`d1-*.sql`, `r2/meta/stats.json`) |
| `classes` | per artifact class (`acts`, `versions`): file count + aggregate sha256 over sorted `relpath sha256` lines |

## 8. Verification (`--verify`)

The self-check recounts every table against `catalog.db` (including
`articles_fts` parity), enforces the section 6 body-size contract, re-hashes
every artifact and class aggregate, rescans all emitted SQL quote-aware
(statement budget + per-statement guards in both fts series), reimports both
fts series into a scratch SQLite database to prove row-count parity and
spot-hash sampled segment bodies against the catalog, and samples 25 acts'
R2 JSON against live `provisions` lookups. Any failure raises with the full
failure list.

## 9. Version history

Versions 1.0 to 1.3.2 are reconstructed from the merged commit trail
(PRs #12 and #13); they were never committed as a document.

- **v1.0** (PR #12): initial data plane. d1-schema + single d1-data INSERT
  series, R2 acts/versions/stats payloads, manifest with per-class sha256
  aggregates, `--verify` self-check.
- **v1.1** (PR #12 parity fixes): rowid-order emission and first-wins
  article semantics locked to FastAPI parity; D1 2 MB value cap identified.
- **v1.2** (PR #13): indexed FTS body defined as bg_normalize(body)
  truncated to 1,900,000 UTF-8 bytes at a char boundary; truncated acts
  reported in `fts_truncated`.
- **v1.3** (PR #13): 90,000-byte per-statement budget; oversized laws_fts
  bodies sliced into INSERT + UPDATE appends.
- **v1.3.1** (PR #13): 12 MB chunk files; statement-boundary chunking
  invariant locked.
- **v1.3.2** (PR #13): idempotent import semantics; d1-data split into
  d1-meta (non-idempotent) + d1-fts (guarded); byte-offset append guards.
- **v2.0** (FR-032 / D-056, this document): two-index split. `laws_fts`
  becomes title-only; new `articles_fts` with one row per body segment
  (schema version 5, migration 005); the fts emission becomes two series
  (`d1-fts-laws`, `d1-fts-articles`) with the idempotency guard moved to
  (law_id, seg_no) granularity; the v1.2 truncation cap and `fts_truncated`
  are retired in favor of the SEG_MAX_BYTES = 400,000 chunking contract and
  the `max_fts_body_bytes` guard; verify gains articles_fts parity and
  segment spot-hashing.
