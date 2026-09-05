# Design: the graded source model (approach C), a ДВ-anchored corpus

**Status:** DESIGN, owner-ratified in direction on 2026-09-05 (D-059 to D-063); written 2026-09-05 for owner review before the implementation plan.
**Owner:** ekimir. **Author:** Claude session of 2026-09-05.
**Supersedes for planning purposes:** the sourcing assumptions of `docs/plans/2026-07-02-fr025-delegation-discovery-design.md` and Part V of `docs/plans/2026-08-11-corpus-correctness-convergence.md` (PR #23), which is amended to match this design.
**Companion records:** CPD `docs/cpd/CPD-2026-09-05-graded-source-model.md`; research `docs/research/2026-09-05-consolidation-precedents.md`; authority changes in PR #25.

---

## 0. Summary

The corpus today is a photograph of lex.bg, a private consolidation. Two facts established on 2026-09-05 make that base untenable as the only base: lex.bg's text diverges from the promulgated Gazette text (omitted sections, typos, a private amendment graph), and lex.bg's heterogeneous rendering of act eras has produced six correction sweeps and a still-open list of parser blind-spot classes. Държавен вестник (ДВ, the State Gazette) publishes the authoritative text, but only as promulgated acts and amending acts, online since 1989 as issue PDFs and since about 2005 as per-act HTML. No official consolidation exists in Bulgaria.

This design re-anchors the corpus on the Gazette wherever the Gazette text is online and grades everything else. Every act carries a provenance grade **A** (ДВ-complete), **B** (ДВ-audited snapshot) or **C** (pre-1989 base), and every amendment event a source class. A grade is earned by gates, never assigned by source. The lex.bg base survives only where the Gazette is not online, and even there it is audited against every Gazette event that is.

The design adds four components (a ДВ acquisition layer, a coverage map, a Gazette-material parser, and a provenance data model), reuses two that PR #23 already specifies (the single corpus write gate and the corpus-integrity checks), and defers the replay engine to Phase 4 while fixing its interfaces here. The first act rebuilt is Закон за обществения транспорт, whose missing definitions are the confirmed lex.bg omission.

## 1. The two problems, with evidence

**Problem 1: lex.bg is not the Gazette.** Закон за обществения транспорт (lex.bg ldoc 2137259781) renders the heading Допълнителна разпоредба with no text and starts its final provisions at § 2; ДВ бр. 32/2026 (material idMat 242220) carries § 1 with twelve statutory definitions. The same omission was verified live for a second act (ldoc 2137259673). The detector `scripts/structure_gaps.py` flags 95 candidate acts, 25 with an empty additional-provisions section (PR #27, FR-042). lex.bg also prints й as и in at least two places of the same act, and its amendment history block is an APIS construct with no Gazette counterpart (I3 research, 2026-06-22). None of this is visible to a source-fidelity gate, because the corpus faithfully reproduces what lex.bg shows.

**Problem 2: lex.bg's rendering is an unbounded blind-spot generator.** Six corpus sweeps and 6,980 corrigendum commits since April 2026. Each fix exposed a class the previous gate could not see: dropped subdivision classes (D-047), flattened unnumbered алинеи in pre-1974 acts (FR-034), fabricated anchors from quoted text (FR-037), superscript indices collapsed by stray tag remnants (FR-035), forum chrome inside an act body (FR-036), citations read as alinea markers (FR-030), 698 colliding article keys (FR-038). D-058 records four instances of the same failure shape: the check measured a proxy, not the property. The final FR-034 reviewer's verdict was that `index/provisions.py` is at the complexity ceiling for regex segmentation.

Both problems share a root: the corpus reproduces a rendering it does not control, of a consolidation it cannot verify.

## 2. Goals and non-goals

Goals:

1. Every act's text traces to the Gazette wherever the Gazette text is online, through a pipeline this project controls end to end.
2. Every act and every amendment event carries machine-readable provenance, surfaced at every consumer surface (frontmatter, index, MCP, REST, cf-plane), so no consumer can mistake a snapshot for verified text.
3. The correctness floor of `docs/process/COVERAGE-FLOOR.md` holds identically for Gazette-derived and snapshot text, enforced at write time by one gate (PR #23 Part IV).
4. The cost of the remaining lex.bg dependence is measured (which acts, which events, how many Gazette PDF pages stand between grade B and grade A) and shrinks monotonically.
5. lex.bg and the Ministry of Justice portal remain useful as witnesses (D-061) and nothing else.

Non-goals, deliberately:

1. Designing the replay engine itself (Phase 4, FR-003). This design fixes what the engine consumes and produces; the engine is its own design.
2. Full historical re-derivation of every version of every act (FR-009). Forward replay from the Gazette makes it possible later; it is not required for a grade.
3. Grade C sourcing. The pre-1989 base is a separate track and a separate owner decision (D-059).
4. Municipal acts (FR-022).

## 3. Facts the design rests on

Verified live on 2026-09-05 unless noted.

| Fact | Evidence |
|---|---|
| dv.parliament.bg holds issues from 1 January 1989; full-text search from 2009; free access since 1 July 2008 | the site's own history page (`dv130.faces`) |
| Per-material HTML exists at least from May 2005 (idMat 300 = бр. 43 от 20.5.2005); idMat 1 and 100 are empty | direct probes |
| Materials are UTF-8 server-rendered HTML; no Cloudflare; no robots.txt | headers and I3 research |
| The issue list (`broeveList.faces`) is a JSF form: 4,146 issues, 10 per page, each row carrying issue number, `idObj`, date and section in its submit parameters; pagination is a POST with `javax.faces.ViewState` | page source, 2026-09-05 |
| `idObj` is sparse and not chronological (6121 = a September 2016 issue; 6000, 3000, 1000 return an error page) | direct probes |
| An issue-contents page (`materiali.faces?idObj=N`) lists every material with section, title, start page and `idMat`; its header shows the current issue, not its own, so the issue identity comes from the list row or from a material page | page source, idObj 6121 |
| The corpus frontmatter records 20,106 amendment events over 3,290 distinct issues; 94.8 % of events are from 2000 on, 98.8 % from 1990 on; 3,055 of 3,624 acts have their whole chain from 2000 on and 2,244 from 2007 on; 116 acts were first published before 1990 | computed from `amendment_history` and `fecha_publicacion`, 2026-09-05 |
| The amendment chain itself comes from lex.bg's history block, an APIS construct | I3 research; `fetcher/bg/metadata.py` |
| No Legalize country self-consolidates; the only national site known to consolidate from raw amending acts at scale runs an editorial process with a published backlog | I1 research; precedents research (section 12) |
| The LawVM model (forward replay, 4-operation kernel, two-level validation) is the ratified engine model | D-060, synthesis brief 2026-06-22 |

Two consequences follow. A full rebuild from the Gazette is real for most of the corpus and impossible for the civil-law backbone, which is why the model is graded. And the chain the coverage map starts from is lex.bg's; the map must therefore also enumerate the Gazette side independently (every ЗИД title in every issue) so that lex.bg's omissions in the chain are found, not inherited.

## 4. The graded model

### 4.1 Source class per amendment event

Every amendment event (a row of `amendment_history`, or a Gazette material the resolver attributes to the act) carries:

| Field | Values | Meaning |
|---|---|---|
| `source` | `dv_html`, `dv_pdf`, `dv_offline`, `lexbg` | where the event's text comes from: a Gazette HTML material, a Gazette issue PDF (read by vision), a Gazette issue not online, or only lex.bg's history block |
| `id_mat` | integer or null | the Gazette material identifier when `source` is `dv_html` |
| `applied` | `rebuilt`, `replayed`, `verified`, `snapshot`, `pending` | how the event reached the current text: the act was rebuilt from this material as its base; the operation stream was replayed; the lex.bg text was verified against the material without replay; the event is present only through the lex.bg snapshot; the material is located but not yet processed |
| `uncertainty` | list, may be empty | flags per correctness property 5: `title_ambiguous`, `date_uncertain`, `partial_read`, `operation_unresolved` |

### 4.2 Grade per act

The grade is derived, never set by hand, as the weakest link over the act's base and events. The
canonical definitions live in `docs/process/COVERAGE-FLOOR.md`, section Provenance floor (PR #25);
this table restates them with the derivation in terms of the event fields of 4.1.

| Grade | Derivation | Gate that earns it |
|---|---|---|
| **A, ДВ-complete** | base `source = dv_html`, `applied = rebuilt`; every event `source = dv_html`, `applied = replayed` (until the engine exists, only acts with no events qualify) | write gate accepts; replay invariants pass; unadjudicated witness divergences = 0 |
| **B, ДВ-audited** | base is a lex.bg snapshot (`source = lexbg`) or a PDF-read Gazette text (`source = dv_pdf`); every event with `source in {dv_html, dv_pdf}` has `applied in {replayed, verified}`; no event `pending` | snapshot frozen only after the single lex.bg repair sweep (Directive 14) and the FR-041 capture ran on it; every online event's `applied` state recorded |
| **B-pending** | as B, but at least one online event is `pending` (located, not yet read, replayed or verified); the record carries the pending count and the estimated Gazette pages to read | none yet; a grade in its own right, held by most older acts during the transition |
| **C, pre-1989 base** | the promulgation or at least one event has `source = dv_offline`; every online event is still sourced and verified as for B, and the pending counter applies | separate track; never rises without a sourcing decision (D-038/D-039 revisit) |

**ДВ-anchored** means grade A or B. B-pending and C acts are not anchored; lex.bg re-scrape stays
permitted for them and is recorded per act (Directive 2). A rebuilt single-issue act is grade A the
moment its base passes the gates. An act promulgated in 2003 and amended twelve times since is
B-pending until its 2003 base has been read from the issue PDF and every event verified, B after
that, and A only if a clean replay from a Gazette base replaces the snapshot. ЗЗД (1950) is C for as
long as its origin is offline, with every post-1989 event nevertheless sourced and verified.

### 4.3 Where the grade lives

- Frontmatter: a `provenance` block (`grade`, `derived_at`, `base: {source, id_mat, issue, year}`, `events_pending`, `pdf_pages_estimate`) and per-event `source` / `id_mat` / `applied` / `uncertainty` on `amendment_history` rows. Additive; frontmatter is protected surface 1, so an IMPLEMENTATION-PREFLIGHT precedes the schema change, and the eight Legalize mandatory fields are untouched. `fuente` becomes `dv.parliament.bg` for grade A acts and stays `lex.bg` otherwise.
- Index: `laws.provenance_grade`, `laws.events_pending`, and an `amendment_events` table with the per-event fields (SQLite schema is protected surface 4; preflight).
- MCP and REST: `get_law` and the search hit carry `provenance_grade`; a `PROVENANCE_GRADE_B` or `_C` warning rides in successful responses the way `IMPLICIT_ALINEA` does (D-058), so a consumer never receives snapshot text unlabelled. Additive per surface 3; `tools.json` minor bump.
- cf-plane: the act payload carries the grade; the worker mirrors the REST warning (the same label-or-skip question as FR-032's implicit rows, decided together).

## 5. Architecture

Five components, in dependency order. The first two produce knowledge before any corpus file changes.

### 5.1 ДВ acquisition layer (`fetcher/dv/`)

Sibling of `fetcher/bg/`, sharing `RateLimitedSession` (1 request per second across both hosts, backoff, halt on challenge) and the descriptive User-Agent.

- **Issue enumeration.** Drive the JSF issue list once: GET `broeveList.faces` for the session cookie and `javax.faces.ViewState`, then POST page by page (`broi_form:selectPage=N`, the page-change control id, the ViewState), parsing each row's submit parameters (`broi_`, `idObj`, `date_izd_`, `razdel_`) into an `issues` table: year, number, date, `idObj`, extraordinary flag. About 415 requests. The date-range filter of the same form is the fallback if global pagination proves unstable: one query per year, about 11 pages each. Re-run incrementally from the newest page for the Phase 3 poller.
- **Materials enumeration.** GET `materiali.faces?idObj=N` for every issue in the table; parse section, title, start page, `idMat` into a `materials` table. About 4,150 requests. Issues before the HTML era return zero materials, which is itself the signal that the issue is PDF-only.
- **Material fetch.** GET `showMaterialDV.jsp?idMat=M`, UTF-8, cache the raw HTML under a content hash (never re-fetch an immutable promulgated text), and record the material's own header (issue number, date, section, page) as the authority for issue identity.
- **Issue PDF fetch.** The whole-issue attachment behind the download control (`fileUploadShowing.jsp?idFileAtt=...`); needed for PDF-era events and for annexes published only as attachments. Fetched on demand per event, never in bulk.
- **Politeness.** One request per second, descriptive UA, log every request; a challenge or a 5xx burst is a halt, not a retry storm. The site is an official publication with public-domain texts (ЗАПСП чл. 4); the raw issues carry no database-right problem (D-039).

### 5.2 Coverage map (`scripts/dv_coverage_map.py`, outputs under `docs/research/2026-09-05-dv-coverage-map/`)

The first deliverable and the instrument that turns the grade model from a definition into numbers.

Inputs: the corpus frontmatter (every act, its promulgation issue, every `amendment_history` row) and the `issues` and `materials` tables.

For every act and every event it records: the referenced issue (year, number), whether the issue exists in the table, whether it has HTML materials, which material the resolver attributes to the event (with match score and ambiguity flag), or that no material matched, or that the issue is PDF-only, or that the issue is not online. It then derives the candidate grade per act and, for PDF-era events, an estimated page count. The estimate in the first version comes from the HTML era: consecutive materials' start pages give the length of every ЗИД and promulgated act in pages, and the median by act type and decade is applied to PDF-era events; the second version replaces the estimate by the exact count from the issue PDF's table of contents for the events that matter.

The map also runs the other way: every material whose title is a ЗИД, a corrigendum or a repeal of a corpus act, resolved by title, that does **not** appear in that act's `amendment_history`, is a chain omission on lex.bg's side and is listed separately. This is the check that keeps the map from inheriting lex.bg's gaps.

Outputs: `coverage-map.csv` (one row per event), `acts-summary.csv` (one row per act with candidate grade, pending count, page estimate), `chain-omissions.csv`, `unresolved.csv` (events the resolver could not attribute), and a short report with the totals by grade and by decade. The map is regenerated by the pipeline whenever the tables change; it is a research artifact until the provenance block ships, then it becomes the derivation input for the grade.

### 5.3 Act-name resolver (shared design spine, D-062)

Turns the declined act name in a ЗИД title (Закон за изменение и допълнение на Закона за обществените поръчки) into a corpus act. Normalisation: casefold (the FR-019 Cyrillic casefold), strip punctuation and the ЗИД prefix, lower the definite genitive of the act-type noun (Закона, Кодекса, Наредбата, Правилника, Постановлението) to its nominative, then exact match on the normalised corpus title, then a bounded fuzzy match. The inline promulgation citation (ДВ, бр. N от YYYY г.) disambiguates by cross-check against the act's `fecha_publicacion` and its chain. Two or more candidates above threshold, or none, is `title_ambiguous`: the event is recorded with the flag and queued for a reasoning pass that reads the material and emits `{id_mat, law_id, verdict, reason}` as data, cached and re-runnable, exactly the flagger-reasoner-applier shape D-055 chose for FR-030. The resolver never guesses.

### 5.4 Gazette material parser (`fetcher/dv/text_parser.py`)

Converts a promulgated act's HTML material into the corpus Markdown structure (title, preamble, ГЛАВА / Раздел headings, `**Чл. N.**` anchors, numbered алинеи, точки, ПЗР with `**§ N.**`, annexes). It is a second `TextParser` implementation against a much more regular source than lex.bg: one document, one era's drafting conventions (Указ 883 numbering is the norm for everything promulgated after 1974), no consolidation notes, no chrome. It emits through the same write gate as the lex.bg path and is measured by the same corpus-integrity checks; its own structural gate is source-block-to-paragraph parity per article, the check D-058 introduced in report mode, which here can be strict from day one because the corpus it guards is empty at the start.

For a ЗИД material the parser produces not Markdown but the operation stream FR-003 consumes: the amending act's own structure (§ paragraphs, each targeting an address in the amended act with an instruction) plus its ПЗР (in-force dates, transitional rules, reference repairs). Lowering the instruction prose to kernel operations is FR-003's job; this parser stops at the segmented, addressed instruction with its quoted text intact.

### 5.5 Replay engine boundary (Phase 4, not designed here)

The engine receives: a base version (grade A: the parsed promulgated act; grade B: the lex.bg snapshot), an ordered list of operation streams with in-force dates, and the address space of the base as `index/provisions.py` builds it. It produces a new version through the write gate, a per-operation ledger (resolved address, precondition results), and a divergence report against the witnesses. Its hard-failing invariants are those of D-060. Until it exists, `applied` cannot take the value `replayed`; the pilot and the first grade A batch therefore consist of acts whose current text **is** a promulgated text with no amendments yet, which is why single-issue acts come first.

### 5.6 Snapshot audit (grade B before the engine exists)

For an act with a lex.bg base, `applied = verified` for an event means: the material was fetched, its instructions were segmented, and each instruction's quoted target text and replacement text were located in the lex.bg text at the addressed position (or their absence explained by a later event). This is a deterministic witness check with a reasoning pass for the ambiguous cases, and it produces exactly the evidence PR #24 produced by hand for one act: lex.bg has or has not applied this Gazette event correctly. It is weaker than replay and it is honest about that in the grade record.

### 5.7 Vision reading of PDF-era material

For events whose issue is PDF-only (1989 to 2004, about 2,250 events), the deterministic pipeline fetches the issue PDF, splits the pages the table of contents assigns to the material, and hands them to the orchestrating session, which reads each page and emits structured Markdown (or an operation stream) with a per-page `partial_read` flag where a scan is illegible. No external OCR library, per the global rule. The coverage map's page estimate is the budget for this work and the owner decides how much of it to buy and in what order (by act importance, by decade).

### 5.8 Write gate and corpus-integrity checks

Unchanged from PR #23 Parts II and IV: one function writes corpus files, it runs the same checks CI runs, there is no force flag, and a static test forbids a second writer. Both the lex.bg refresh path and the ДВ paths call it. The provenance block is validated by a new check (`checks/provenance.py`): a grade must be derivable from the recorded events, and no consumer-facing field may disagree with the derivation.

## 6. Data flow

1. Acquisition builds `issues` and `materials` (once, then incrementally).
2. The coverage map attributes every corpus event to a material or records why not, lists chain omissions, and derives candidate grades and page estimates.
3. For each act in the grade A candidate set (chain entirely `dv_html`), the material parser rebuilds the base; for single-issue acts that is the whole act; the write gate accepts or refuses; the grade record is written; the witnesses are diffed and divergences adjudicated.
4. For each grade B act, events are located and verified against the snapshot; pending counts and page estimates are recorded.
5. The index rebuild reads the provenance block; MCP, REST and cf-plane surface the grade.
6. Phase 3's poller is the incremental run of steps 1 and 2 on new issues; Phase 4's engine turns `verified` into `replayed` and lets grade B acts rise.

## 7. The pilot: Закон за обществения транспорт

A 2026 act, promulgated in ДВ бр. 32/2026 (idMat 242220), with a one-issue chain and a confirmed lex.bg omission. Steps and acceptance:

1. Acquisition fetches the material; its header identifies the issue.
2. The material parser produces Markdown; the structural gate (source blocks to paragraphs per article) is strict.
3. The write gate accepts the file; `fuente` becomes `dv.parliament.bg`; the provenance block records grade A with base `dv_html`, `id_mat` 242220.
4. Witness diff against lex.bg: the expected divergences are exactly the § 1 definitions, the en-dash versus hyphen style, the two й/и typos and lex.bg's consolidation notes; each is adjudicated into a lane (source pathology on lex.bg's side for the omission and the typos, editorial for the rest); unadjudicated count 0.
5. `get_article` answers § 1 through the provisions index (which today carries no § rows for any act; adding them is a small provisions change registered in the plan, since the pilot's whole point is a § the corpus lacked).
6. The commit carries `Source-Id: dv-242220` and `Source-Date: 2026-04-01` and is made by the pipeline, never by hand; its commit type and the `Norm-Id` form for Gazette-sourced acts are settled in the Surface 5 IMPLEMENTATION-PREFLIGHT the delivery contract now requires before the pilot (PR #25).

Acceptance for the pilot as a whole: every step above passes with the gates strict, the act is grade A in frontmatter, index, MCP and REST, and the takt-plan programme's follow-up FU-002 can close against it.

## 8. Sequencing

| Phase | Content | Exit gate | Owner decision |
|---|---|---|---|
| **P0** | Coverage map (5.1 enumeration + 5.2), read-only; PR #23 Part II machine floor and write gate | map published with grade candidates and page estimates; floor green in CI | fetch permission (given 2026-09-05) |
| **P1** | Material parser for promulgated acts; provenance block (preflight surfaces 1 and 4); MCP/REST/cf grade exposure; the pilot | pilot acceptance in section 7 | preflight sign-off |
| **P2** | Grade A batch: every single-issue act whose material is `dv_html`; then multi-event acts as the engine matures (Phase 4) | detector zero over the batch; witness divergences adjudicated to zero | batch order |
| **P3** | Grade B audit over the remaining acts; PDF-era reading in owner-chosen order | every 1989-or-later event `verified` or `pending` with a page estimate | reading budget |
| **P4** | Grade C track | separate design | source decision (D-038/D-039 revisit) |

PR #23's remaining phases (heading state, remnants, anchors, addresses, citations, annex classification) run on the snapshot acts as before, since they are the base of grades B and C, and they are the pre-cutover gate for any act that stays snapshot-based. Its single repair sweep (Part V phase 7) is re-scoped to the acts that keep a lex.bg base; grade A acts are repaired by rebuild, not by re-photograph. A Gazette rebuild is a new pipeline generation for the act, not a repair sweep under Directive 14, and a grade B or C snapshot is frozen only after that sweep and the FR-041 capture have run on it (Directive 2 as amended).

## 9. Changes to PR #23

- Part IV.7 (the one-way door) now applies per act: an act is cut over to grade A only when the detectors report zero on it; snapshot acts keep the re-photograph path.
- Part V phase 7: the sweep covers grade B and C acts only. Its owner decision O-3 (when the sweep may run) is unchanged; its traffic estimate shrinks with every act that moves to grade A.
- A tenth class **C10, provenance integrity**: a grade not derivable from recorded events, or a consumer surface disagreeing with the derivation. Detector `checks/provenance.py`, invariant INV-010, bound at the write gate.
- O-6 (Directive 2) is resolved by PR #25; O-5 (FR-037) is resolved by PR #25; O-8 (capture cross-references now) is answered yes for every act that keeps a snapshot base, and is unnecessary for grade A acts, whose references the resolver reconstructs from Gazette text.

## 10. Risks and mitigations

| Risk | Mitigation |
|---|---|
| JSF pagination breaks mid-enumeration (ViewState expiry, session churn) | re-acquire ViewState per page; fall back to the date-range filter per year; the table is append-only and resumable |
| Title resolution mis-attributes an event to the wrong act | resolver never guesses; ambiguity is a flag and a reasoning queue; the inline promulgation citation is a hard cross-check; attribution is data, reviewable |
| lex.bg's chain is incomplete and the map inherits it | the ДВ-side enumeration of every ЗИД title is mandatory and its unmatched residue is a first-class output |
| The Gazette material parser develops its own blind spots | strict structural gate from day one on an empty corpus; goldens per act type from the first ten acts; the corpus-integrity checks run on every write |
| PDF-era reading is larger than budgeted | the page estimate is published before any reading starts; reading is ordered by owner priority and each page carries a `partial_read` flag rather than a guess |
| Grade exposure changes consumer behaviour (a B warning on most acts today) | additive fields and a warning class, like `IMPLICIT_ALINEA`; consumers that ignore warnings see unchanged payloads; the DRS status file documents the semantics |
| The provenance block is hand-edited or drifts from events | `checks/provenance.py` derives the grade from events and fails on disagreement; the write gate refuses |

## 11. Open decisions for the owner

1. **Order of the grade A batch after the pilot**: single-issue acts by recency, or by consumer priority (the DRS and takt-plan act lists)?
2. **PDF-era reading order for grade B**: by act importance, by decade descending, or by event count?
3. **Warning shape on the wire**: one `PROVENANCE_GRADE` warning carrying the grade, or one warning class per grade?
4. **`fuente` semantics**: switch to `dv.parliament.bg` only at grade A, or record both sources in the provenance block and keep `fuente` as the base source?
5. **Whether the coverage map's chain-omission list triggers immediate `[reforma]` events** for HTML-era omissions lex.bg missed, or waits for the engine.

## 12. Precedents

*Filled from `docs/research/2026-09-05-consolidation-precedents.md` when the research leg reports; the section is a stub until then and must not be read as evidence.*

## 13. Self-review notes

*Completed after the first full draft.*
