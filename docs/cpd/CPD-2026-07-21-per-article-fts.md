# CPD-2026-07-21: Per-Article (Per-Segment) FTS5 Index

**Status:** RATIFIED 2026-07-23 (plan PR #15 merged by owner; design §11 Q1–Q5 answered — see Ratification below)
**Origin:** D1 2 MB value cap → PR #13 body truncation of 3 acts; lineage D-051 option (b) / D-054
**Author:** Claude session on owner (ekimir) dispatch, 2026-07-21
**Design:** `docs/plans/2026-07-21-fr032-per-article-fts-design.md` (authoritative for all technical detail)
**FR:** FR-032

> First CPD-style record in this repo. legalize-bg normally records decisions as
> `docs/sync/DECISIONS.md` rows; this change is *cross-cutting* (index builder,
> FastAPI query layer, Cloudflare exporter, API Worker, and the cf-data-plane spec
> across three open PRs), which is exactly the situation the DRS portfolio handles
> with a CPD. The D-056 row stays the canonical ledger entry and points here.

## Ratification (2026-07-23)

Owner merged plan PR #15 and approved implementation "as proposed", adopting the
design §11 recommendations:

- **Q1 (aggregation):** MIN — best-segment bm25 is the act-level relevance.
- **Q2 (sequencing):** merge #13 → #12 → #14 first — **already executed** on main
  (`e1d4e5d0`, `3b62505c`, `3aedaa36`) before ratification, plus #16 (float-exact
  parity goldens) and #17 (CORS); the v1 capped baseline is live.
- **Q3 (additive `matched: {kind, label}` field):** YES, in this implementation
  cycle; minor-version bump on tools.json and openapi-rest.json (additive,
  Surface 3).
- **Q4 (`SEG_MAX_BYTES`):** start at 400,000 UTF-8 bytes; final value calibrated by
  the §8 spike.
- **Q5 (DEFERRED `D-2026-07-02-01` disposition):** decided by spike data at landing.

**Q1 AMENDED (2026-07-23, post-spike, owner):** plain MIN showed a measured
short-segment bias (Кодекс на труда #31 for "трудов договор", ЗАНН #6 for
"административни нарушения"). Act score = best-segment bm25 **− 4·n/(n+5)**
(n = matching segments within the fixed 500-row overscan window; rational form for
cross-plane float parity). Evidence: `docs/research/2026-07-23-fr032-spike.md` §5.

Implementation branch: `feat/fr032-per-article-fts`.

## Problem

`laws_fts` indexes each act as ONE FTS5 document (whole normalized body). This
produces three coupled defects: (1) Cloudflare D1's 2,000,000-byte value cap forces
truncating the indexed body of 3 acts (spec v1.2 / PR #13) — a real recall loss, ~95%
of the largest capped act's mass is appendix text; (2) body-only queries scan a 223M-
char single-document-per-act index (5.4–6.5 s cold, accepted under D-051/D-054 with
"split body FTS index" named as the structural remedy); (3) snippets cannot come from
FTS5 over the body (1 MB documents), so body snippets are a Python ±60-char window.

Measured blocker for the naive fix: the `provisions` table covers only 57% of body
text (§-paragraphs, appendices, preambles, headings are outside its `Чл. N` anchors;
132 acts have zero provisions). Indexing "provisions" instead of "the segmented body"
would re-create D-047-class silent recall loss.

## Decision

1. Split the search index: `laws_fts` → title-only (tier-1 ranking unchanged by
   construction); new `articles_fts` = one row per body **segment** (article, §,
   appendix, preamble/residual), produced by a new full-coverage segmenter whose
   machine-checked invariant is *concat(segments) == body* per act.
2. Oversized segments (appendices) are chunked at `SEG_MAX_BYTES` (~400 KB) — this,
   not per-article rows alone, is what structurally retires the 2 MB cap
   (`FTS_BODY_MAX_BYTES` from PR #13 is superseded and removed).
3. Tier-2 act relevance = best-segment bm25 (MIN); snippets come from the winning
   segment via FTS5 `snippet()`; `_make_body_snippet`/`makeBodySnippet` are retired.
4. bm25 float values and body-tier orderings change; managed by the three-layer
   ranking-parity strategy (locked tests unchanged → golden-diff review → cross-plane
   float-exact parity, sanctioned-temporary tolerance only during rollout).
5. Coordinated rollout: merge the open v1 PRs (#13, #12, #14) first as the parity-
   gated baseline, then one `feat/fr032-per-article-fts` branch changes all four
   components + bumps the (to-be-committed) cf-data-plane spec to v2.0; D1 cutover
   via a fresh database + binding flip, v1 kept until production parity passes.

## Contract Changes

None breaking. tools.json (1.3.0) and `docs/api/openapi-rest.json` shapes unchanged.
Open question Q3 proposes one additive search-hit field `matched: {kind, label}`
(minor version bump both contracts) — owner decides at ratification.

## Spec Changes

- cf-data-plane spec: v1.3.2 → **v2.0** (articles_fts DDL, segment/chunking rules,
  idempotent per-segment emission). The spec file itself — currently referenced by
  PRs #12–#14 but committed nowhere — is committed as
  `docs/api/cf-data-plane-spec.md` in the implementation phase.
- `docs/data/schema-reference.md`: schema v5 (migration 005: laws_fts recreated
  title-only; articles_fts added). Protected Surface 4 preflight filed:
  `docs/process/IMPLEMENTATION-PREFLIGHT-2026-07-21-fr032-per-article-fts.md`.

## Process Changes

- FR-032 registered in `docs/frs/INDEX.md` (Planned); D-056 row in
  `docs/sync/DECISIONS.md` records direction + this CPD.
- Perf budgets re-ratified after the mandatory measurement spike (D-051 discipline);
  DEFERRED `D-2026-07-02-01` is dispositioned with real numbers at landing (Q5).

## Consequences

- **Gain:** full search recall on both planes (cap retired), FTS5-quality per-segment
  snippets, article-level match attribution for the Phase 7.2 web UI, a finally-
  lockable body-only perf budget, and removal of the permanent-truncation caveat from
  the Cloudflare port.
- **Cost:** one-time bm25/ordering shift on body-tier queries (reviewed, not silent);
  parity goldens recaptured once; ~165–175K FTS rows vs 3,602 (D1 size +5–10%);
  four components must move in one coordinated release.
- **Risk accepted:** quoted `Чл.` anchors inside ПЗР create mislabeled (never lost)
  segments — labels are advisory; `get_article` still resolves via `provisions`.

## Alternatives Rejected

Provisions-as-index (57% coverage), alinea granularity (bm25 distortion, 2× rows),
contentless/external-content FTS5 (breaks snippet or duplicates content stores),
title-in-segment-rows single table (tier-1 re-weighting), SUM/AVG aggregation
(length-bias inversion), and waiting for the D-051 latency trigger (the cap is a
correctness regression now). Details: design §10.
