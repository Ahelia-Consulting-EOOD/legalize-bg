# CPD-2026-09-05: graded source model (approach C), re-anchoring the corpus on Държавен вестник

**Status:** PROPOSED 2026-09-05; direction ratified by the owner the same day (D-059 to D-063, PR #25). This CPD records the cross-cutting change so every affected component is changed together and none by surprise.
**Origin:** owner review of 2026-09-05 after PR #24 proved that lex.bg omits promulgated sections and after six correction sweeps failed to bound lex.bg's parser blind-spot classes.
**Author:** Claude session on owner (ekimir) dispatch, 2026-09-05.
**Design:** `docs/plans/2026-09-05-dv-graded-source-design.md`.
**Directives touched:** OWNER-DIRECTIVES 2 and 3 (rewritten in PR #25), 4 (provenance fields as further extensions; field names aligned in PR #28); Directives 9 to 14 apply unchanged.

## Problem

The corpus is a photograph of a private consolidation it cannot verify and whose rendering it does not control. The Gazette is authoritative but not consolidated and only partly online. The pipeline, the data model and every consumer surface assume one source and one level of trust; none can express "this act is Gazette-verified, that one is a snapshot".

## Change, component by component

| Component | Change | Protected surface | Preflight |
|---|---|---|---|
| `fetcher/dv/` (new) | ДВ acquisition layer: issue enumeration over the JSF list, materials enumeration, material fetch with cache, issue PDF fetch; own rate-limited session sharing the UA and the request ceiling, with its own challenge markers and outage-stub handling (F5 front end, not Cloudflare) | none changed; `fetcher/bg/` untouched. The Legalize `LegislativeClient`/`TextParser` interfaces gain a second implementation, not a change | none for the layer itself; a note in the Phase 5 upstream plan |
| `fetcher/dv/text_parser.py` (new) | Gazette material to corpus Markdown; ЗИД material to segmented instruction stream | same as above | none |
| Coverage map `scripts/dv_coverage_map.py` (new) + `data/dv/` tables | per-act, per-event Gazette availability, resolver attribution, chain omissions, page estimates | none | none |
| YAML frontmatter | additive `provenance` block (grade, base record with `chain_scanned_through` and `chain_inherited_before`, `checked_through`, `in_force_as_of`, `events_not_in_force`, `events_pending`, `pdf_pages_estimate`, status line); additive per-event fields `source`, `locator`, `applied`, `verified_against`, `uncertainty` on `amendment_history` rows; `fuente` follows `base.state` (`rebuilt` or `read` gives `dv.parliament.bg`); every one of the 3,624 acts backfilled with exactly one grade at introduction (Directive 4); identifier form for ДВ-only acts to be settled. The eight mandatory Legalize fields are untouched | **Surface 2** | **required** before the first write |
| SQLite schema | `laws.provenance_grade`, `laws.events_pending`; new `amendment_events` table; § provision rows with a `kind` column; migration 007 | **Surface 4** | **required** |
| MCP tools | `get_law` and search hits carry `provenance_grade` and `checked_through`; one warning class `PROVENANCE_GRADE` carrying the grade for any grade other than A (D-064) riding in successful responses; `get_article` gains § addressing keyed by section context with a `kind` column (design 7.5, own task); `tools.json` minor bump | **Surface 3** (additive) | **required**, additive path |
| REST API | same fields and warning on `/laws/{slug}` and `/search`; OpenAPI contract regenerated with `api.export_openapi --check` | contract file | with the MCP preflight |
| cf-plane | act payload carries the grade; worker mirrors the warning; spec version bump; decided together with the FR-032 implicit-rows label-or-skip question | `docs/api/cf-data-plane-spec.md` | with the D1 cutover decision |
| Commit conventions | `Source-Id: dv-<idMat>` for Gazette-sourced commits (already used once in PR #24's rejected commit). **Proposed for the Surface 5 preflight, not decided here:** the commit type for a Gazette rebuild that replaces a snapshot, for a first Gazette-sourced promulgation and for a replayed amendment, and the `Norm-Id` form for acts without a lex.bg document. Preflight input: `index/build.py` excludes `[popravka]` from `law_versions` boundaries (FR-020 D4), so a rebuild committed as `[popravka]` would create no version row | **Surface 5** | **required** before the pilot commit |
| Write gate and corpus-integrity | unchanged from PR #23 Parts II and IV; new check `checks/provenance.py` (grade derivable from events; consumer fields agree) | none | none |
| Corrections ledger and editorial-changes report (new, design 5.9) | two channels: Gazette поправка recorded on the event they correct; consolidator-side corrections and parser normalisations listed per act by the pipeline | none | none |
| `docs/sync/CORPUS-STATUS.json` | already carries `correctness_grade` and `source_model` (PR #25); gains per-grade act counts when the block ships | DRS S5 surface (D-048) | announce via `/sync-drs` |
| PR #23 plan | Part V sweep re-scoped to grade B and C acts; class C10 provenance integrity; O-5/O-6/O-8/O-9/O-10/O-11 marked resolved | none | none |

## Sequencing

P0 coverage map with the body scan and the resolver, and PR #23 Part II (no corpus write) → P1 material parser, provenance block with corpus-wide backfill, exposure, § rows, pilot → P2 grade A batch → P3 grade B audits and PDF-era reading → P4 grade C track. Full table in the design, section 8.

## Decisions (D-064, 2026-09-05)

The six questions of design section 11 are decided: grade A batch order by consumer priority; PDF-era reading by act importance; one warning class `PROVENANCE_GRADE` with the grade in its payload; `identificador = dv-<idMat>` for ДВ-only acts; chain-omission and `estado` findings recorded as data until the write gate exists, then `[otmyana]` in one batch and `[reforma]` only with the engine; the PDF-era tables of contents inventoried with page totals for a token-cost evaluation, not read yet.

## Not in this CPD

The replay engine (FR-003, Phase 4, own design), municipal acts (FR-022), grade C sourcing (D-038/D-039 revisit).
