# CPD-2026-09-05: graded source model (approach C), re-anchoring the corpus on Държавен вестник

**Status:** PROPOSED 2026-09-05; direction ratified by the owner the same day (D-059 to D-063, PR #25). This CPD records the cross-cutting change so every affected component is changed together and none by surprise.
**Origin:** owner review of 2026-09-05 after PR #24 proved that lex.bg omits promulgated sections and after six correction sweeps failed to bound lex.bg's parser blind-spot classes.
**Author:** Claude session on owner (ekimir) dispatch, 2026-09-05.
**Design:** `docs/plans/2026-09-05-dv-graded-source-design.md`.
**Directives touched:** OWNER-DIRECTIVES 2 and 3 (rewritten in PR #25); Directives 9 to 14 apply unchanged.

## Problem

The corpus is a photograph of a private consolidation it cannot verify and whose rendering it does not control. The Gazette is authoritative but not consolidated and only partly online. The pipeline, the data model and every consumer surface assume one source and one level of trust; none can express "this act is Gazette-verified, that one is a snapshot".

## Change, component by component

| Component | Change | Protected surface | Preflight |
|---|---|---|---|
| `fetcher/dv/` (new) | ДВ acquisition layer: issue enumeration over the JSF list, materials enumeration, material fetch with cache, issue PDF fetch; own rate-limited session sharing the UA and the halt-on-challenge check | none changed; `fetcher/bg/` untouched. The Legalize `LegislativeClient`/`TextParser` interfaces gain a second implementation, not a change | none for the layer itself; a note in the Phase 5 upstream plan |
| `fetcher/dv/text_parser.py` (new) | Gazette material to corpus Markdown; ЗИД material to segmented instruction stream | same as above | none |
| Coverage map `scripts/dv_coverage_map.py` (new) + `data/dv/` tables | per-act, per-event Gazette availability, resolver attribution, chain omissions, page estimates | none | none |
| YAML frontmatter | additive `provenance` block; additive per-event fields `source`, `id_mat`, `applied`, `uncertainty` on `amendment_history` rows; `fuente` takes `dv.parliament.bg` for grade A acts. The eight mandatory Legalize fields are untouched | **Surface 1** | **required** before the first write |
| SQLite schema | `laws.provenance_grade`, `laws.events_pending`; new `amendment_events` table; migration 007 | **Surface 4** | **required** |
| MCP tools | `get_law` and search hits carry `provenance_grade`; new warning class `PROVENANCE_GRADE` (shape per owner decision 3 of the design) riding in successful responses; `tools.json` minor bump | **Surface 3** (additive) | **required**, additive path |
| REST API | same fields and warning on `/laws/{slug}` and `/search`; OpenAPI contract regenerated with `api.export_openapi --check` | contract file | with the MCP preflight |
| cf-plane | act payload carries the grade; worker mirrors the warning; spec version bump; decided together with the FR-032 implicit-rows label-or-skip question | `docs/api/cf-data-plane-spec.md` | with the D1 cutover decision |
| Commit conventions | `Source-Id: dv-<idMat>` for Gazette-sourced commits (already used once in PR #24's rejected commit); `[popravka]` for a rebuild that corrects a snapshot, `[nova]` for a first Gazette-sourced promulgation, `[reforma]` for a replayed amendment | **Surface 5** (additive namespace) | note in the preflight, no format change |
| Write gate and corpus-integrity | unchanged from PR #23 Parts II and IV; new check `checks/provenance.py` (grade derivable from events; consumer fields agree) | none | none |
| Corrections ledger and editorial-changes report (new, design 5.9) | two channels: Gazette поправка recorded on the event they correct; consolidator-side corrections and parser normalisations listed per act by the pipeline | none | none |
| `docs/sync/CORPUS-STATUS.json` | already carries `correctness_grade` and `source_model` (PR #25); gains per-grade act counts when the block ships | DRS S5 surface (D-048) | announce via `/sync-drs` |
| PR #23 plan | Part V sweep re-scoped to grade B and C acts; class C10 provenance integrity; O-5/O-6/O-8/O-9/O-10/O-11 marked resolved | none | none |

## Sequencing

P0 coverage map and PR #23 Part II (no corpus write) → P1 material parser, provenance block, exposure, pilot → P2 grade A batch → P3 grade B audit → P4 grade C track. Full table in the design, section 8.

## Owner questions

The five open decisions in the design, section 11: batch order after the pilot; PDF-era reading order; warning shape; `fuente` semantics; whether HTML-era chain omissions found by the map trigger `[reforma]` events before the engine exists.

## Not in this CPD

The replay engine (FR-003, Phase 4, own design), municipal acts (FR-022), grade C sourcing (D-038/D-039 revisit).
