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
| HTML-era universe: 2,515 acts have their whole chain at or after бр. 43/2005; 1,055 of them are single-issue acts (the pre-engine grade A candidate set); 160 acts carry no `amendment_history` at all and need an explicit rule | computed over frontmatter, 2026-09-05 (design review) |
| Cross-act amendments ride inside other acts' ПЗР: a narrow pattern (a `**§ N.**` anchor followed by „В Закона / Кодекса / Наредба ... се“) finds 1,980 such instructions inside the bodies of 337 corpus acts; the true count is higher | measured on `origin/main`, 2026-09-05 (design review) |
| No Legalize country self-consolidates; the only national site known to consolidate from raw amending acts at scale runs an editorial process with a published backlog | I1 research; precedents research (section 12) |
| The LawVM model (forward replay, 4-operation kernel, two-level validation) is the ratified engine model | D-060, synthesis brief 2026-06-22 |

Two consequences follow. A full rebuild from the Gazette is real for most of the corpus and impossible for the civil-law backbone, which is why the model is graded. And the chain the coverage map starts from is lex.bg's; the map must therefore also scan the Gazette side independently (the body of every HTML-era material, not only its title) so that lex.bg's omissions in the chain are found, not inherited.

## 4. The graded model

### 4.1 Source class per amendment event

Every amendment event (a row of `amendment_history`, or a Gazette instruction the body scan of 5.2 attributes to the act) carries:

| Field | Values | Meaning |
|---|---|---|
| `source` | `dv_html`, `dv_pdf`, `dv_offline`, `unlocated` | where the event's text comes from: a Gazette HTML material; a Gazette issue PDF (read by vision); a Gazette issue not online (before 1989); or an event lex.bg's history block claims that the coverage map could not locate on the ДВ side. An unlocated event is never recorded as „lex.bg-sourced“: it is `unlocated`, `pending`, and carries `chain_unconfirmed` |
| `locator` | `{id_mat}` or `{id_file_att, pages}` or null | the Gazette material identifier, or the issue attachment plus page range for a PDF-era event |
| `applied` | `replayed`, `verified`, `not_incorporated`, `pending` | how the event reached the current text: the operation stream was replayed by the engine; the text was verified against the material without replay (5.6); the instruction could not be applied because it addresses a provision that does not exist or replaces words that are not present, and is recorded without changing the text, the Australian „misdescribed amendment“ pattern (section 12), a terminal state that never blocks a grade and always surfaces as a warning; or the material is located but not yet read, replayed or verified |
| `verified_against` | text hash or null | the hash of the snapshot text a `verified` state was established against; any change to the snapshot resets the event to `pending` |
| `uncertainty` | list, may be empty | flags per correctness property 5: `title_ambiguous`, `chain_unconfirmed`, `date_uncertain`, `partial_read`, `operation_unresolved` |

The base of the act carries its own record: `base: {source, state, locator, issue, year, frozen_at, audited, declared_at, chain_scanned_through, chain_inherited_before}` where `source` takes the event values (`unlocated` when the promulgation is cited but the material was not found, and, for the 121 acts that cite no promulgation at all, `unlocated` with the uncertainty `promulgation_unknown`), the **promulgation is online** exactly when `source in {dv_html, dv_pdf}`, `state` is `rebuilt` (a Gazette HTML material converted through the write gate), `read` (a Gazette PDF text read by vision and taken as the base) or `snapshot` (the lex.bg photograph), `frozen_at` is the date the Directive 14 repair sweep and the FR-041 reference capture ran on the snapshot (null until then; a rebuilt or read base counts as frozen at its write), `audited` records whether the base structural audit of 5.6 passed, `declared_at` is an optional declared base date (section 10, the UK fallback) before which Gazette events are not carried and are listed as such, `chain_scanned_through: {issue, year, date}` is the last HTML-era issue the body scan of 5.2 has covered for this act (so `chain_scan_complete` in 4.2 is the tree-checkable predicate `chain_scanned_through = checked_through`), and `chain_inherited_before: date` names the date before which the act's chain is inherited from lex.bg because the Gazette side has no materials list (2005 for every act until the table-of-contents reading of P3 runs; null once it has).

### 4.2 Grade per act: the decision procedure

The grade is derived, never set by hand. The canonical grade definitions live in `docs/process/COVERAGE-FLOOR.md`, section Provenance floor; this procedure is their decision procedure, the one `checks/provenance.py` (5.8) implements and property-tests over every combination of its inputs. Inputs: `base.source`, `base.state`, `base.frozen_at`, `base.audited`, `base.declared_at`, `chain_scan_complete` (`base.chain_scanned_through = checked_through`, that is, the ДВ-side body scan of 5.2 has run over every HTML-era issue in the act's lifetime), the multiset of event `applied` states over the act's events, and `divergences_unadjudicated` (the count from the offline witness diff of 5.6). Domain constraints the property test enforces rather than enumerates: `rebuilt` implies `base.source = dv_html`; `read` implies `dv_pdf`; `frozen_at` is non-null for `rebuilt` and `read`; `verified` events exist only against a `snapshot` base; `divergences_unadjudicated` is 0 for a `snapshot` base (the snapshot is the witness) and for every committed file. Events dated before `base.declared_at` are excluded from the multiset and listed as not carried. Rules apply in order; the first match decides.

| # | Condition | Grade |
|---|---|---|
| 0 | a rebuilt or read base with `divergences_unadjudicated > 0` | no grade, because no committed file: the act is held in staging outside the corpus tree until adjudication reaches zero (I6, C2 case 4) |
| 1 | `base.source = dv_offline`, or any event in scope has `source = dv_offline` | **C, pre-1989 base**. Online events are still sourced and verified as for B, and the pending counter applies |
| 2 | `base.state = rebuilt`, `base.source = dv_html`, `chain_scan_complete`, every event `source = dv_html` with `applied in {replayed, not_incorporated}`, `divergences_unadjudicated = 0` | **A, ДВ-complete** (until the engine exists, only acts with no events in scope qualify) |
| 3 | any event `applied = pending` (this includes every `unlocated` event), or `chain_scan_complete` false, or `base.source = unlocated` (the promulgation cited but not found, or not cited at all: `promulgation_unknown`), or `base.state = snapshot` with the promulgation online (`base.source in {dv_html, dv_pdf}`) and `base.audited` false, or `base.state = snapshot` with `base.frozen_at` null | **B-pending**, with the pending items enumerated in the record: unread or unverified events, the missing chain scan, the unlocated or unidentified promulgation, the missing base audit, the freeze not yet run |
| 4 | everything else (a frozen and audited snapshot base or a read base, every event in scope `replayed`, `verified` or `not_incorporated`, chain scan complete; within the domain constraints no other history reaches this rule) | **B, ДВ-audited** |

The procedure is total: rule 1 catches every offline history, rule 2 the Gazette-complete ones, rule 3 every open item, and rule 4 the rest. Case checks from the review: two HTML events verified before the sweep has run is B-pending (rule 3, freeze null), which is the honest state for every act audited before owner decision O-3; a `not_incorporated` event blocks nothing and warns everywhere; a 2003 act whose base is a PDF-era promulgation keeps its snapshot base and is B-pending until the base structural audit has been done by vision against the issue PDF (`base.audited`, without replacing the base; `read` replaces the base only for acts with no events, since a read 2003 text is the unamended act), or, if the owner declares 2005 as its base date, grades B on its post-2005 events with the declaration surfaced; an act that cites no promulgation (121 today, mostly the FR-011 municipal acts routed to FR-022) is B-pending with `promulgation_unknown` until a P0 task locates it on the ДВ side by title or the owner waives it; an HTML-era event the resolver cannot attribute is `unlocated` and `pending`, so it blocks B; a rebuilt act with open divergences is never a committed file.

**ДВ-anchored** means grade A or B. B-pending and C acts are not anchored; lex.bg re-scrape stays permitted for them and is recorded per act (Directive 2), except that a snapshot that has been frozen is never re-scraped again: a frozen act that receives a new Gazette event from the Phase 3 poller becomes B-pending on that one event, stays frozen, and is served stale with a truthful `checked_through` until the engine replays the event (I4).

### 4.3 Where the grade lives

- Frontmatter: a `provenance` block holding `grade`, `derived_at`, the `base` record of 4.1, `checked_through: {issue, year, date}` (the last Gazette issue whose materials were attributed to the act, the bounded currency statement in the legislation.gov.uk form), `in_force_as_of: date`, `events_not_in_force: n` (Gazette events attributed but not yet in force, which lex.bg prints inline with a note), `events_pending: n`, `pdf_pages_estimate`, and a fixed `status` line stating that the consolidated text has no official value and the Gazette prevails on any discrepancy; plus the per-event fields of 4.1 on `amendment_history` rows. `ultima_actualizacion`, a mandatory Legalize field, keeps its meaning: the date of the latest event applied to the text. Additive; frontmatter is protected **Surface 2**, so an IMPLEMENTATION-PREFLIGHT precedes the schema change, the eight Legalize mandatory fields are untouched, and every act is backfilled at introduction (Directive 4 as amended). `fuente` follows `base.state`: `rebuilt` or `read` gives `dv.parliament.bg`, `snapshot` keeps `lex.bg` (Directive 4's „Gazette-sourced acts“); this closes the former open decision 4. Acts found on the ДВ side with no lex.bg document have no `identificador` or `eli` source today; the Surface 2 preflight settles their identifier form (M10).
- Index: `laws.provenance_grade`, `laws.events_pending`, and an `amendment_events` table with the per-event fields (SQLite schema is protected Surface 4; preflight).
- MCP and REST: `get_law` and the search hit carry `provenance_grade`, `checked_through` and `chain_inherited_before`; a warning rides in every successful response for any grade other than A, B-pending included, in the shape settled by owner decision 3, the way `IMPLICIT_ALINEA` does (D-058), so a consumer never receives snapshot text unlabelled; the disclaimer and tie-break rule travel in `tools.json` response metadata so that dropping them is a visible contract violation (BOE obliges reusers to carry its label and update date; section 12).
- cf-plane: the act payload carries the grade; the worker mirrors the REST warning (the same label-or-skip question as FR-032's implicit rows, decided together).

## 5. Architecture

Five components, in dependency order. The first two produce knowledge before any corpus file changes.

### 5.1 ДВ acquisition layer (`fetcher/dv/`)

Sibling of `fetcher/bg/`, sharing the rate ceiling (1 request per second across both hosts), the backoff rule and the descriptive User-Agent, but with its own session: dv.parliament.bg sits behind an F5 BIG-IP front end (`f5_cspm` instrumentation, `jsessionid` URL rewriting), so the Cloudflare-specific halt markers and the `.lex.bg` cookie code of `RateLimitedSession` do not carry over; the ДВ session has its own challenge markers and treats the site's outage stub (an HTTP 500 whose body reads „Сайтът е недостъпен в момента“) as a terminal answer that is never retried and never cached. Implemented test-first on `feat/dv-acquisition` (PR #29).

- **Issue enumeration.** Drive the JSF issue list once: GET `broeveList.faces` for the session cookie and `javax.faces.ViewState`, then POST page by page (`broi_form:selectPage=N`, the page-change control id, the ViewState), parsing each row's submit parameters (`broi_`, `idObj`, `date_izd_`, `razdel_`) into an `issues` table: year, number, date, `idObj`, extraordinary flag. About 415 requests. The date-range filter of the same form is the fallback if global pagination proves unstable: one query per year, about 11 pages each. Re-run incrementally from the newest page for the Phase 3 poller.
- **Materials enumeration.** GET `materiali.faces?idObj=N` for every issue in the table; parse section, title, start page, `idMat` into a `materials` table. About 4,150 requests. Issues before the HTML era return zero materials, which is itself the signal that the issue is PDF-only.
- **Material fetch.** GET `showMaterialDV.jsp?idMat=M`, UTF-8, cache the raw HTML (never re-fetch an immutable promulgated text), and record the material's own header (issue number, date, section, page) as the authority for issue identity. **Cost:** the body scan of 5.2 needs the body of every HTML-era material in the law and ministerial sections, not only the issue pages: on the order of forty-two thousand material fetches (about 2,340 HTML-era issues at up to 18 materials each), which with the issue pages and the list pages is about 12.4 hours at one request per second on a ceiling shared with lex.bg, a one-time cost the cache makes permanent. The materials sweep halts on a run of consecutive outage stubs and on an unrecognised-markup ratio, so an outage or a markup change cannot be written down as thousands of Gazette gaps.
- **Issue PDF fetch.** The whole-issue attachment behind the download control (`fileUploadShowing.jsp?idFileAtt=...`); needed for PDF-era events and for annexes published only as attachments. Fetched on demand per event, never in bulk.
- **Politeness.** One request per second, descriptive UA, log every request; a challenge or a 5xx burst is a halt, not a retry storm. The site is an official publication with public-domain texts (ЗАПСП чл. 4); the raw issues carry no database-right problem (D-039).

### 5.2 Coverage map (`scripts/dv_coverage_map.py`, outputs under `docs/research/2026-09-05-dv-coverage-map/`)

The first deliverable and the instrument that turns the grade model from a definition into numbers.

Inputs: the corpus frontmatter (every act, its promulgation issue, every `amendment_history` row), the `issues` and `materials` tables, and the cached body of every HTML-era material in the Народно събрание, Министерски съвет and ministerial sections.

For every act and every event it records: the referenced issue (year, number), whether the issue exists in the table, whether it has HTML materials, which material the resolver attributes to the event (with match score and ambiguity flag), or that no material matched (`unlocated`), or that the issue is PDF-only, or that the issue is not online. It then derives the candidate grade per act by the procedure of 4.2 and, for PDF-era events, an estimated page count. The estimate in the first version comes from the HTML era: consecutive materials' start pages give the length of every ЗИД and promulgated act in pages (the last material of an issue is bounded by the issue's page count), and the median by act type and decade is applied to PDF-era events; the second version replaces the estimate by the exact count from the issue PDF's table of contents for the events that matter.

**The ДВ-side pass is a body scan, not a title scan.** In Bulgarian drafting most cross-act amendments and repeals ride in the преходни и заключителни разпоредби of a different act: a ЗИД of act X amends acts Y and Z in its own §§, and a new law amends a dozen others in its ПЗР, under the new law's title. A title pass never attributes those events, so the chain would remain lex.bg's, the very thing section 3 forbids. The map therefore fetches the body of every HTML-era material, segments its ПЗР with the ЗИД segmenter of 5.4, extracts every „В <act> ... се изменя / се създава / се отменя“ and „<act> се отменя“ instruction, and resolves each target through 5.3; the title is the first key, the body the second. Every attributed instruction that does **not** appear in the target act's `amendment_history` is a chain omission on lex.bg's side and is listed separately; every repeal so found feeds `estado`, which for grade A acts is derived from the ДВ side and never from lex.bg's history text. Per act, `chain_scan_complete` becomes true only when the body scan has covered every HTML-era issue in the act's lifetime; without it „no events“ is lex.bg's assertion, not the Gazette's, and the act cannot be grade A (4.2 rule 2).

**Before 2005 there is no ДВ-side check.** PDF-era issues expose no materials list, so chains in 1989 to 2004 are inherited from lex.bg and the grade record says so; reading the issue table-of-contents pages by vision (about 1,600 issues) is the owner-decided way to close that gap for grade B acts (section 8, P3), and until it runs the inheritance is stated, not hidden.

Instructions the segmenter of 5.4 cannot classify are not dropped: they go to `segmenter-residue.csv` with their material and position, a reasoning pass in the D-055 shape resolves each to a target and an operation, to „no target“ or to „unresolvable“ (recorded with `operation_unresolved`), and corpus-wide residue of zero unresolved rows is a condition of the P2 exit gate, because an instruction both lex.bg and the segmenter missed would otherwise leave `chain_scan_complete` true and let an act reach A. Where the scan finds a repeal or a Gazette event that contradicts lex.bg's `estado` for a grade B or C act (lex.bg says vigente and the Gazette repeals, or the reverse), the act carries the uncertainty `estado_disputed`, surfaced as a warning, and the row goes to the adjudication queue; owner decision 5 covers whether such findings become `[reforma]` or `[otmyana]` events before the engine exists.

Outputs: `coverage-map.csv` (one row per event), `acts-summary.csv` (one row per act with candidate grade, pending items, page estimate), `chain-omissions.csv`, `unresolved.csv` (events and instructions the resolver could not attribute, the seven corpus acts with an empty `titulo`, which cannot be resolved by title at all, and the 121 acts that cite no promulgation, which a P0 task tries to locate on the ДВ side by title), `segmenter-residue.csv`, `estado-disputes.csv`, and a short report with the totals by grade and by decade. The map is regenerated by the pipeline whenever the tables change; it is a research artifact until the provenance block ships, then it becomes the derivation input for the grade.

### 5.3 Act-name resolver (shared design spine, D-062; delivered in P0)

Turns the act named in a ЗИД title or in a ПЗР instruction into a corpus act, and belongs to P0 because every attribution, every chain-omission row and every candidate grade of the coverage map depends on it. Two keys. **Laws and codes** are named by a declined title (Закон за изменение и допълнение на Закона за обществените поръчки): casefold (the FR-019 Cyrillic casefold), strip punctuation and the ЗИД prefix, lower the definite genitive of the act-type noun (Закона, Кодекса, Наредбата, Правилника, Постановлението) to its nominative, then exact match on the normalised corpus title, then a bounded fuzzy match. **Numbered acts** are named by number and year: 1,671 of the 2,645 corpus ordinances are titled „НАРЕДБА № N ОТ <date> Г. ЗА ...“ and an amending instruction cites „Наредба № N от YYYY г.“ with no issuing ministry in either, so the key is (act type, number, year) plus the title tail, and the act type is gated by the Gazette section the material sits in (Народно събрание, Министерски съвет, a ministry). The inline promulgation citation (ДВ, бр. N от YYYY г.) disambiguates by cross-check against the act's `fecha_publicacion` and its chain. Two or more candidates above threshold, or none, is `title_ambiguous`: the event is recorded `unlocated` and `pending` with the flag and queued for a reasoning pass that reads the material and emits `{id_mat, instruction, law_id, verdict, reason}` as data, cached and re-runnable, exactly the flagger-reasoner-applier shape D-055 chose for FR-030. The resolver never guesses. The seven corpus acts with an empty `titulo` are listed as resolver-blocked in `unresolved.csv` until they carry a title.

### 5.4 Gazette material parser (`fetcher/dv/text_parser.py`)

Converts a promulgated act's HTML material into the corpus Markdown structure (title, preamble, ГЛАВА / Раздел headings, `**Чл. N.**` anchors, numbered алинеи, точки, ПЗР with `**§ N.**`, annexes). It is a second `TextParser` implementation against a much more regular source than lex.bg: one document, one era's drafting conventions (Указ 883 numbering is the norm for everything promulgated after 1974), no consolidation notes, no chrome. It emits through the same write gate as the lex.bg path and is measured by the same corpus-integrity checks; its own structural gate is source-block-to-paragraph parity per article, the check D-058 introduced in report mode, which here can be strict from day one because the corpus it guards is empty at the start.

For a ЗИД material the parser produces not Markdown but the operation stream FR-003 consumes: the amending act's own structure (§ paragraphs, each targeting an address in the amended act with an instruction) plus its ПЗР (in-force dates, transitional rules, reference repairs). Lowering the instruction prose to kernel operations is FR-003's job; this parser stops at the segmented, addressed instruction with its quoted text intact.

### 5.5 Replay engine boundary (Phase 4, not designed here)

The engine receives: a base version (grade A: the parsed promulgated act; grade B: the lex.bg snapshot), an ordered list of operation streams with in-force dates, and the address space of the base as `index/provisions.py` builds it. It produces a new version through the write gate, a per-operation ledger (resolved address, precondition results), and a divergence report against the witnesses. Its hard-failing invariants are those of D-060. Until it exists, `applied` cannot take the value `replayed`; the pilot and the first grade A batch therefore consist of acts whose current text **is** a promulgated text with no amendments yet, which is why single-issue acts come first.

### 5.6 Snapshot audit (grade B before the engine exists)

Two audits, both deterministic with a reasoning pass for the ambiguous cases, both recorded against the snapshot's text hash.

**Base structural audit.** Where the promulgated material is online, the address inventory of that material (articles, the § of ДР and ПЗР, annexes) must appear in the snapshot or be accounted for by a located later event (a repeal, a renumbering). This is the check that catches the FR-042 class for snapshot acts: the omission that started this track sits in the promulgated base, not in an event, and 1,460 acts have their promulgated material online while keeping a lex.bg base (2,515 whole-chain HTML-era acts minus the 1,055 single-issue ones that go to grade A). Passing it sets `base.audited`. Where the promulgation is `dv_html` the audit is deterministic; where it is `dv_pdf` the address inventory is read from the issue PDF by vision (5.7) and the audit sets `base.audited` without replacing the snapshot base, so an amended act keeps its consolidated text; replacing the base by a `read` text is reserved for acts with no events, since a read promulgation is the unamended act. Until the audit has run the act is B-pending.

**Event verification.** For each attributed event, `applied = verified` means: the material was fetched, its instructions were segmented, and each instruction's quoted target text and replacement text were located in the snapshot at the addressed position (or their absence explained by a later event). It produces exactly the evidence PR #24 produced by hand for one act: lex.bg has or has not applied this Gazette event correctly. It is weaker than replay and honest about that in the grade record. The state is a property of (event, snapshot text hash): `verified_against` records the hash, and any change to the snapshot text resets the event to `pending`. Results recorded before the Directive 14 sweep has frozen the snapshot are provisional, which is why an unfrozen snapshot keeps the act at B-pending (4.2 rule 3).

**Witnesses.** The witness for any gate is the committed lex.bg snapshot already in the corpus tree, diffed offline; a live lex.bg fetch is never a gate input (D-061: a check that cannot block is not a gate), and the Ministry of Justice witness is advisory for the gate. A divergence is a **candidate** finding until a Gazette material resolves it, and **confirmed** only then, the vocabulary LawVM uses for its oracle comparisons (section 12); the adjudication lanes of D-061 record which. A rebuilt act with open candidates is held in staging and is not a committed file.

### 5.7 Vision reading of PDF-era material

For events whose issue is PDF-only (2,260 events in 1989 to 2004, plus up to 144 events in 2005 issues 1 to 42 whose HTML availability the map fixes, so 2,260 to about 2,400), the deterministic pipeline fetches the issue PDF, splits the pages the table of contents assigns to the material, and hands them to the orchestrating session, which reads each page and emits structured Markdown (or an operation stream) with a per-page `partial_read` flag where a scan is illegible. No external OCR library, per the global rule. The coverage map's page estimate is the budget for this work and the owner decides how much of it to buy and in what order (by act importance, by decade). Annexes, tariffs and tables in the scan era that do not survive transcription are stored as page images with a visible marker and graded accordingly, the Normattiva treatment of graphic parts (section 12), rather than forced into lossy text.

### 5.8 Write gate and corpus-integrity checks

Unchanged from PR #23 Parts II and IV: one function writes corpus files, it runs the same checks CI runs, there is no force flag, and a static test forbids a second writer. Both the lex.bg refresh path and the ДВ paths call it. The provenance block is validated by a new check (`checks/provenance.py`): a grade must be derivable from the recorded events, and no consumer-facing field may disagree with the derivation.

### 5.9 Corrections ledger and editorial-changes report

Two channels, kept apart as every system studied keeps them (section 12). Gazette-side corrigenda
(поправка, published in ДВ) are absorbed into the base or the affected event and are not counted as
amendments, but each is recorded with its ДВ citation on the event it corrects. Consolidator-side
corrections, where our own pipeline changed a text for a reason other than a Gazette event, are
stored as data with the error's first appearance, its correction, the fixing commit and a severity
class (can mislead a legal reader, or not). Parser normalisations that alter form without altering
law (a superscript index written as `260и¹`, a position-derived алинея number, quotation-mark
normalisation) are editorial changes in the Australian sense and are listed per act in a running
editorial-changes report generated by the pipeline. Neither channel changes any grade; both make the
record truthful under FR-040.

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
3. The write gate accepts the file; `fuente` becomes `dv.parliament.bg`; the provenance block records grade A with base `dv_html`, `locator` `{id_mat: 242220}`, `chain_scanned_through` equal to `checked_through`.
4. Offline witness diff against the committed lex.bg snapshot of the act: the expected divergences are exactly the § 1 definitions, the en-dash versus hyphen style, the two й/и typos and lex.bg's consolidation notes; each is adjudicated into a lane (source pathology on lex.bg's side for the omission and the typos, editorial for the rest); the file stays in staging until the unadjudicated count is 0. The body scan of 5.2 has run over ДВ бр. 32/2026 onward for this act, so `chain_scan_complete` holds; ЗОТ's own ПЗР amendments to other acts are attributed to those acts' chains by the same scan.
5. `get_article` answers § 1. This is not a small change: `index/provisions.py` has no § anchors and treats `**§ N.**` as an article closer, `parse_article_spec` rejects any spec that is not чл. N [ал. M] (a Surface 3 grammar change), `index/segments.py` already labels § segments for search so search knows § and `get_article` does not, and 227 corpus acts carry „§ 1“ two or more times because every appended ПЗР restarts numbering, so naive § rows would create an FR-038-class collision set on day one. § rows are therefore keyed by section context (ДР, ПЗР of the promulgated act, ПЗР of amending act N) with a `kind` column, the instrument FR-026 already registers; the pilot scopes them to the promulgated act's own ДР and ПЗР; the work is its own task with Surface 3 and Surface 4 preflights.
6. The commit carries `Source-Id: dv-242220` and `Source-Date: 2026-04-01` and is made by the pipeline, never by hand; its commit type and the `Norm-Id` form for Gazette-sourced acts are settled in the Surface 5 IMPLEMENTATION-PREFLIGHT the delivery contract now requires before the pilot (PR #25).

Acceptance for the pilot as a whole: every step above passes with the gates strict, the act is grade A in frontmatter, index, MCP and REST, and the takt-plan programme's follow-up FU-002 can close against it.

## 8. Sequencing

| Phase | Content | Exit gate | Owner decision |
|---|---|---|---|
| **P0** | Coverage map (5.1 enumeration and body fetch, 5.2 body scan, 5.3 resolver with its reasoning pass, the ДВ-side title search for the 121 acts that cite no promulgation), read-only; PR #23 Part II machine floor and write gate | map published with every act's candidate grade by the 4.2 procedure, the chain-omission list, the unresolved list and the page estimates; floor green in CI | fetch permission (given 2026-09-05) |
| **P1** | Material parser for promulgated acts; provenance block (preflight Surfaces 2 and 4); MCP/REST/cf grade exposure; the § rows task (Surfaces 3 and 4); the pilot | pilot acceptance in section 7, and every one of the 3,624 acts backfilled with exactly one grade by the 4.2 procedure (mostly B-pending and C) | preflight sign-off |
| **P2** | Grade A batch: every single-issue act whose material is `dv_html`; then multi-event acts as the engine matures (Phase 4) | detector zero over the batch; witness divergences adjudicated to zero; corpus-wide segmenter residue resolved to zero unresolved rows | batch order |
| **P3** | Grade B audits over the remaining acts (base structural audit, event verification, provisional until the Directive 14 sweep freezes the snapshot); PDF-era reading in owner-chosen order, including the table-of-contents pages that close the pre-2005 chain gap | every online event `verified`, `not_incorporated` or `pending` with a page estimate; every online promulgation audited | reading budget; whether to read the PDF-era tables of contents |
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
| Title resolution mis-attributes an event to the wrong act | resolver never guesses; ambiguity is a flag and a reasoning queue; the numbered-act key and the Gazette section gate handle наредби; the inline promulgation citation is a hard cross-check; attribution is data, reviewable |
| The body scan misses an instruction form (irregular drafting, an amendment inside an annex) | the segmenter's unrecognised forms are counted and flagged, never dropped; the chain-omission list is compared against lex.bg's chain in both directions, so a form lex.bg saw and the scan did not shows up as an unexplained lex.bg event |
| lex.bg's chain is incomplete and the map inherits it | the ДВ-side body scan of every HTML-era material is mandatory and its unmatched residue is a first-class output |
| The Gazette material parser develops its own blind spots | strict structural gate from day one on an empty corpus; goldens per act type from the first ten acts; the corpus-integrity checks run on every write |
| PDF-era reading is larger than budgeted | the page estimate is published before any reading starts; reading is ordered by owner priority and each page carries a `partial_read` flag rather than a guess |
| Grade exposure changes consumer behaviour (a B warning on most acts today) | additive fields and a warning class, like `IMPLICIT_ALINEA`; consumers that ignore warnings see unchanged payloads; the DRS status file documents the semantics |
| The provenance block is hand-edited or drifts from events | `checks/provenance.py` derives the grade from events and fails on disagreement; the write gate refuses |
| The PDF-era rebuild (1989 to 2004) is more ambitious than any national precedent; every system studied declared a base edition instead (section 12) | grade B-pending makes the unread events honest instead of hidden; the owner buys reading page by page against the map's estimate; if the cost proves prohibitive, the owner declares 2005 as `base.declared_at` for those acts: their pre-2005 events are listed as not carried, they grade B at best on their post-2005 events, and the declaration is surfaced with the grade, exactly the UK 1991 model |

## 11. Open decisions for the owner

1. **Order of the grade A batch after the pilot**: single-issue acts by recency, or by consumer priority (the DRS and takt-plan act lists)?
2. **PDF-era reading order for grade B**: by act importance, by decade descending, or by event count?
3. **Warning shape on the wire**: one `PROVENANCE_GRADE` warning carrying the grade, or one warning class per grade?
4. **Identifier form for ДВ-only acts**: an act found on the ДВ side with no lex.bg document has no `identificador` or `eli` source today; the Surface 2 preflight needs the owner's choice of identifier scheme (former decision 4 on `fuente` is closed in 4.3: `fuente` follows `base.source`).
5. **Whether the coverage map's chain-omission and `estado` dispute lists trigger immediate `[reforma]` or `[otmyana]` events** for HTML-era findings lex.bg missed, or wait for the engine.
6. **Whether to read the PDF-era tables of contents by vision** (about 1,600 issues) so that 1989 to 2004 chains stop being inherited from lex.bg, and in what order.

## 12. Precedents

Source: `docs/research/2026-09-05-consolidation-precedents.md` and its source log (96 extract rows, 14 logged negatives), covering legislation.gov.uk, Normattiva, RIS, Finlex and LawVM, wetten.overheid.nl, the eCFR and U.S. Code, BOE and Légifrance as contrast, and the graded systems of Australia, Canada, Estonia, Germany, Ireland and New Zealand. The findings below are the research's; the design decisions they drove are marked.

**Divergence is prevented procedurally, never detected by diffing.** No state system compares its consolidation against another consolidator's text. Each analyses the amending act into a typed effects record first, applies it second, and publishes a bounded currency claim rather than a correctness claim: the UK's „up to date with all changes known to be in force on or before“ a date, the eCFR's „current within two business days“, Finlex's „up to and including statute N“. Only legislation.gov.uk publishes the effects machine-readably with an applied status, and only for changes since 2002. *Adopted:* the event table of 4.1 is the effects record and comes before any text change; `checked_through` in 4.3 is the currency statement; the witness comparison of D-061 stays, but as adjudication of candidates (5.6), since it has no state precedent to copy.

**Every quality or provenance grade found is categorical and rule-backed.** Applied versus requires-applied per effect (UK), authorised version and „(md not incorp)“ per amendment (Australia), „textlich nachgewiesen, dokumentarisch noch nicht abschließend bearbeitet“ per act (Germany), prima facie versus positive law per title (U.S. Code), evidence with the original prevailing (Canada). No system publishes a numeric confidence. *Adopted:* grades A, B, B-pending and C are tiers with gates, never a percentage; the `not_incorporated` state of 4.1 is the misdescribed-amendment pattern (the term is in Australia's primary glossary; the „(md not incorp)“ marker rests on a flagged search snippet), recorded without guessing and without a statutory editorial power to fix the text, which this project does not have.

**Nobody rebuilds pre-digital history from the gazette.** Every system with history declares a base edition and date and lists what it does not carry: the UK at 1 February 1991 from Statutes in Force, the Netherlands at 2002, Canada at 2003 and 2006, Estonia at 1990. Normattiva alone claims multivigenza from 1861 (how its 19th-century histories were built was not verified by the research) and it versions graphic PDF parts as marked images inside the same point-in-time model. Finland's state bought the copyright of its vendor consolidation in 2025 rather than rebuild it. *Adopted:* grade C is a declared base edition (the lex.bg photograph as of the bootstrap date) with the earliest verified ДВ item stated per act, and the two Gazette boundaries, 2005 for HTML and 1989 for scans, are grade boundaries rather than one base; the PDF-era rebuild is kept but named as beyond precedent in section 10, with the UK model as the fallback.

**Versioning is per provision with validity intervals, and the act at a date is a query.** RIS stores one document per paragraph, article or annex with entry and exit dates; BWB stores article states with a per-article history row naming the Staatsblad item; CLML marks each section's validity window. Provenance is always the gazette item, never the consolidator's edit. *Deferred to Phase 4:* the replay engine's address and lineage model; this design keeps act-level versions (FR-020) and records provenance per event, which is what the provision-level model needs as input.

**Corrections run in two channels.** Gazette errata are absorbed into the original and not counted as amendments (Normattiva, BOE); consolidator-side corrections are either a statutory editorial power with a public report (Australia, New Zealand) or a data resource with dates and citations (eCFR) or a measured error class (BWB's A-fouten). *Adopted:* 5.9.

**The legal-status ladder is climbed by statute, not by quality.** Estonia, New Zealand and Canada made consolidations official by amending their gazette or legislation acts. Until Bulgaria's Закон за нормативните актове does anything similar, this corpus sits on the bottom rung with Normattiva, BOE and Légifrance, and the honest label is the disclaimer with the tie-break rule carried into every response (4.3). Whether that rung should ever change is a policy question outside this design.

## 13. Self-review notes

Completed 2026-09-05 after the research leg reported, after PR #25 forced one canonical grade definition, and after the fresh-context design review of PR #28 (two Critical, nine Important, ten Minor, all accepted).

- **Placeholders:** none.
- **Totality of the grade derivation:** 4.2 is now an ordered procedure over named inputs with a first-match rule; every history the review constructed lands on exactly one outcome (staging, C, A, B-pending, B), and `checks/provenance.py` property-tests the input space.
- **Chain independence:** the ДВ-side pass is a body scan of every HTML-era material, so ПЗР-embedded cross-act amendments and repeals are attributed and `estado` for grade A acts comes from the Gazette; the pre-2005 inheritance from lex.bg is stated, with the table-of-contents reading as the owner-decided remedy.
- **Internal consistency:** 4.1's `applied` values (`replayed`, `verified`, `not_incorporated`, `pending`) are exactly the ones 4.2 and the coverage floor use; `rebuilt`, `read` and `snapshot` are base states, not event states; 5.6 defines both `verified` and the base audit that 4.2 references; 7's pilot steps reference the staging rule and the § task; 8's phases carry the resolver in P0 and the backfill in P1; the surface numbers match the preflight checklist (frontmatter is Surface 2).
- **Scope:** P0 and P1 are one implementation plan; P2 to P4 are later plans. The replay engine, historical re-derivation, grade C sourcing and municipal acts are named non-goals.
- **Evidence status:** the ДВ facts in 3 were verified live on 2026-09-05 and independently reproduced by the reviewer; the chain and universe statistics are computed over frontmatter with the method stated; the precedents are cited to a source log with their evidence grade where it is weak.
