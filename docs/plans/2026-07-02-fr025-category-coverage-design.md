# FR-025 — Corpus act-type category coverage (design)

**Status:** Design approved 2026-07-02 (owner). Feeds `writing-plans` → implementation plan.
**Requirement:** FR-025 (`docs/frs/INDEX.md`). **Defect:** D-049 (`docs/sync/DECISIONS.md`).
**Related:** D-047 (per-act analogue, remediated), FR-024/D-038 (re-source), FR-026 (annex facet, carved out here), COVERAGE-FLOOR.md, D-039 (legal posture).

## 1. Problem

The 2026 bootstrap (D-002) crawls exactly five lex.bg tree slugs — hard-coded in
`fetcher/bg/discovery.py::CATEGORIES_CONFIG`:

```
laws (12 pages) · code (1) · ords (75) · regs (14) · reg_laws (2)
```

Every normative act-type that lex.bg exposes under a *different* tree slug is
therefore invisible to discovery and absent from the corpus. Confirmed omission:
**ПМС (постановления на МС)** — the corpus has zero (evidence: НСС = ПМС № 46/2005,
ldoc 2135501600, active, was entirely absent until the DRS work placed the single
adopting decree in `postanovleniya/`). Likely also omitted: тарифи, инструкции,
решения на МС, разпореждания, укази.

This is the **set-level analogue of D-047**: D-047 was a CSS-class *allowlist* that
silently dropped subdivisions *within* an act; FR-025 is a category *allowlist* that
silently drops whole act-type *sets*. The corpus is complete for the acts it holds
(post-D-047) but incomplete in *which acts exist*.

`COVERAGE-FLOOR.md` encodes the bug: it floors "all 5 lex.bg categories" and lists
"skipping an entire category" as a violation — yet the five-slug enumeration *is* the
omission.

## 2. Guiding principle

Carried from D-047: **fix the class, not the instance.** Do not just add ПМС. Instead:
enumerate the act-type categories lex.bg *actually* exposes (rather than trusting a
hand-maintained list), prove coverage with a gate, and make the enumeration
self-updating so a future new category cannot be silently dropped again.

## 3. Decisions (owner, 2026-07-02)

- **D1 — Scope = discover-then-decide.** A read-only discovery spike enumerates and
  quantifies the full gap; the owner then picks the in-scope category set from real
  numbers. No blind commitment to "all" or "curated" up front.
- **D2 — Annex facet carved out.** Acts whose substance lives in a separate
  „приложение"/annex document that the act page only references by title (e.g. НСС
  standards СС 1–42) are a *different* detection problem (a missing *sibling* document,
  not a missing category). Split to **FR-026** with its own spec. FR-025 is
  category-only.
- **D3 — `rango` precise for new types, existing coarse `rango` untouched.** New
  act-types get precise `rango` values (`постановление`, `тарифа`, `инструкция`, …).
  The existing coarse `rango` (`закон` for laws/codes/ords/regs; `правилник по
  прилагане` for implementing) is a separate, pre-existing data-quality item — noted,
  not fixed here (scope-creep guard).
- **D4 — Non-article acts need no special-casing.** Tariff/decree bodies that are not
  `Чл.`-structured are captured by existing machinery: the parser emits their
  tables/text, the per-act D-047 coverage gate proves capture, and the `provisions`
  (article) table simply stays empty for them; FTS search works on the body.
- **D5 — Discovery probes to end.** Replace trust in hard-coded per-category page
  counts with crawl-until-no-new-doc_ids, so enumeration cannot silently truncate
  (the failure mode that also let the corpus miss growth).

## 4. Architecture / touch points

Single source of truth for the category list is `fetcher/bg/discovery.py`
(`CATEGORIES_CONFIG`, `CATEGORY_DIRS`), imported by `bootstrap.py`, `refresh.py`,
`index/build.py`. Adding categories is therefore a one-place edit plus new corpus dirs;
`index/build.py` picks up new dirs automatically via `CATEGORY_DIRS`.

**Protected surfaces touched → IMPLEMENTATION-PREFLIGHT required before code:**
`fetcher/bg/` interfaces, YAML frontmatter schema (`rango`), SQLite schema (if any),
commit-message format (new `[nova]` acts use the existing format — no change expected).

## 5. Phased plan

### Phase 1 — Discovery & quantification spike (read-only)
- Scrape lex.bg's tree-navigation index to enumerate **every** act-type tree slug it
  exposes (not the hard-coded five). For each slug: human name, page count (probe to
  end), act count, count already in corpus, count omitted.
- Emit a gap report: `docs/research/2026-07-02-fr025-category-gap.md` with a per-slug
  table and totals. Uses the CF-hardened `RateLimitedSession` (D-047 Task 9 path A;
  cookie mint/re-mint via Playwright).
- **Owner scope-gate:** owner selects the in-scope categories from the table. Record as
  a DECISIONS addendum to D-049.

### Phase 2 — Governance + preflight
- IMPLEMENTATION-PREFLIGHT doc for the protected surfaces above.
- Rewrite `COVERAGE-FLOOR.md`: replace the fixed "5 categories" floor with "every
  enumerated in-scope lex.bg category is represented, or has a dated waiver in
  `WAIVERS.md`."
- Record the scope decision (Phase-1 outcome) in `DECISIONS.md`.

### Phase 3 — Structure & plumbing (TDD)
- Add in-scope categories to `CATEGORIES_CONFIG` + `CATEGORY_DIRS`; create corpus dirs
  (`postanovleniya/` already exists).
- **Probe-to-end discovery (D5):** crawl each category until a page yields no new
  doc_ids, instead of trusting a static page count. Tests for the probe termination and
  for slug→dir mapping (slug-stability invariant, D-030).
- Add precise `rango` values for the new types (D3).

### Phase 4 — Corpus-level coverage gate (TDD) — the durable guarantee
- A set-level analogue of the D-047 per-act gate: a check (wired into CI and/or the
  bootstrap/refresh close-out) asserting every enumerated lex.bg category is either
  represented in the corpus or explicitly waived; fail otherwise.
- This is what stops a *future* new lex.bg category from being silently dropped.

### Phase 5 — Fetch in-scope categories
- Run the in-scope categories through the CF-hardened, coverage-gated pipeline used for
  the D-047 bulk: cookie mint/re-mint, per-act D-047 coverage gate, HALT-and-triage on
  gate failures, `[nova]` commits (author-date = legislative date, committer-date real
  per D-048).
- **Dependency:** overlaps FR-024 (re-source). The net-new fetch should reuse whatever
  the FR-024/ДВ source decision settles rather than build a parallel path.

### Phase 6 — Rebuild catalog + verify + close-out
- `index.build` (full) + `scripts/verify_catalog.py`; per-category count probe.
- DECISIONS D-049 → addressed; FR-025 → closed; COVERAGE-FLOOR updated; memory updated.
- Optionally refresh `docs/sync/CORPUS-STATUS.json` (add per-category coverage).

## 6. Risks

- **R1 — CF fragility / cookie TTL** at scale (as in the D-047 bulk): mitigated by the
  proven mint/re-mint loop; honor ≤1 req/s, D-011 (stop-on-CF, no solver), D-039 (texts
  only).
- **R2 — unknown act-type page structure.** New categories may render differently; the
  per-act coverage gate catches under-capture, HALT-and-triage via vision (as in the
  D-047 gate-fail triage).
- **R3 — scope over-reach.** Individual/ephemeral acts (укази-appointments, some
  решения) may bloat the corpus with non-general-normative content. Mitigated by the
  Phase-1 gap report + owner scope-gate.
- **R4 — FR-024 coupling.** If the re-source pivots to ДВ, Phase 5 should not build a
  throwaway lex.bg path; sequence Phase 5 after the FR-024 decision or explicitly accept
  lex.bg-as-source for this pass.

## 7. Out of scope
- Annex/приложение-as-separate-document capture → FR-026.
- Fixing the existing coarse `rango` for laws/codes/ords/regs → separate data-quality
  item.
- Municipal corpus (FR-022), freshness/DV-monitor (Phase 3), consolidation (Phase 4).
