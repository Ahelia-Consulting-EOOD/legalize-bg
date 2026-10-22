# The owner's intent of 22 October 2026: source defects, source diversity and act profiles

**What this is.** This is the starting point for the work after the write path. It holds the owner's wishes and the findings behind them, as one list. The owner gave them on 22 October 2026, in the write-path session of the run-design worktree, after reading the diagram of the reading and write path (`docs/plans/2026-10-22-reading-write-path-diagram.html`). The text is the session's reading of what the owner said, not the owner's words. The owner approved points 1 to 8 as read and asked that the readings be kept in place of the words. Points 9 and 10 are the owner's additions of the same day. The findings under each point come from the project's own records, which are named in each case.

**What comes next.** In order: this record; then what needs to be done; then the owner's agreement; then a plan. This record proposes no work.

## The owner's wishes

**1. lex.bg's own content errors pass straight through.** lex.bg is known to hold some acts wrong, for example acts whose transitional and final provisions (преходни и заключителни разпоредби) are missing or wrong. The reading step copies lex.bg's text character for character and judges only formatting, meaning what each line is. It cannot see an error in the content, so such an error reaches git looking correct.

**2. The source model is not yet a sustainable one.** "Read lex.bg once, then make the State Gazette the main source" is not drawn out as a working model. There is no defined way to mark an act that lex.bg holds wrong, or to obtain its correct text from elsewhere.

**3. The coverage is too narrow.** The current approach classifies about 25 typical issues. It does not show how the model behaves across more than 3,000 acts, many of them laid out in ways not yet seen. Наредби (ordinances) carry more special cases than laws: tables, diagrams and other attachments. The problem is wider than a mechanical approach covers. Saving tokens matters, but completeness comes first: no act is done until it matches the real act exactly.

**4. Treat each act by its own nature, along two axes.**
- **Structure and formatting:** what kind of act it is, and which layout conventions it uses. Those conventions are partly historical.
- **Gazette history:** whether the act's changes fall in the Gazette's HTML era, its PDF era, or before both. This includes a complete list of every act still in force (neither superseded nor repealed) that began before the Gazette's online archive. Закон за задълженията и договорите is one such act.

**5. A register of each act's peculiarities is the basis for everything else.** Without it the work can be neither deterministic enough nor efficient enough. Classifiers built on that register are what bring the efficiency.

**6. The corpus is the authority.** The Legalize framework's rules for its 40 or more countries are one source of information. Our own acts are the single source of truth for what is done and planned, and the corpus is studied in a structured way.

**7. Parked: whether the Legalize way of recording acts suits this corpus.** It is recorded for later investigation and kept out of the current work (`docs/followups/2026-10-22-legalize-format-suitability.md`).

**8. Order of work:** this record, then what needs to be done, then agreement, then a plan.

**9. Find out what kinds of content error lex.bg has.**
- Errors found from other projects showed that some of the problems are in lex.bg itself, not in how this project processes lex.bg. That is how the owner learnt of them.
- The owner wants the provenance of each known case traced and discussed.
- Above all, the owner wants to know which types of content misrepresentation lex.bg has, as distinct from formatting differences.

**10. Use several sources.** Three routes for a second starting point and for checking problem acts:
- a paid consolidated-law service such as APIS, subscribed for a short period until the provenance of the problem acts has been checked;
- the Ministry of Justice portal, whose texts may count as an authoritative source, consolidated or not;
- for the acts still in force that began before the Gazette's online archive, a decision on which sources count as authoritative for each.

Указ № 883 of 1974, which implements the Закон за нормативните актове, is the example: the owner's legislation repositories spent much time finding a full, authoritative text of it, and the owner no longer remembers where it was found. That is to be traced and settled.

## Findings from the record

**The transport-law case (point 9).**
- The case is the Закон за обществения транспорт (lex.bg document 2137259781), found from the takt-plan programme.
- On 5 September 2026, lex.bg's page showed the heading "Допълнителна разпоредба" (additional provision) with no text under it, followed directly by § 2 of the final provisions. The page's raw HTML holds no hidden § 1.
- The Gazette's text of the act as promulgated (ДВ бр. 32 от 1.4.2026 г., material 242220) carries § 1 with twelve definitions.
- The other 106 articles match the Gazette, apart from lex.bg's own notes, its dashes, and two places where lex.bg prints "и" for the Gazette's "й".
- The same gap was confirmed on the Закон за прозрачност при представителство на интереси (lex.bg document 2137259673).
- A scan for this pattern found 25 files with an empty additional-provisions section and 95 candidate acts in all. It was later revised to 33 empty sections and 103 candidates.
- Evidence: PR #24 (closed); the audit `docs/audits/2026-09-05-source-dropped-additional-provisions.md`; the detector `scripts/structure_gaps.py` (PR #27); the class registered as FR-042.
- The owner ruled on 5 September that the missing § 1 is to come from rebuilding the act from the Gazette through the pipeline, not from a hand edit (decision D-063). The act was chosen as the first grade A pilot for that rebuild.

**The write path committed that defect again (points 1 and 2).**
- On 22 October 2026 the write path committed the Закон за обществения транспорт (commit 2ed79019c) with the additional-provisions section still empty.
- The reading step noticed the empty section. It recorded it as one of five `empty_section` findings across the 50 acts, as decision D-072 ruling 7 provides, and did not refuse the act.
- So a known content defect is now committed through the new path. It is a concrete instance of point 1.

**What the record already decides on sources (point 2).**
- Decision D-059 (5 September 2026) makes the Gazette the source of truth wherever its text is online. lex.bg is a starting snapshot and a cross-check, never the truth.
- Decision D-068 (21 October 2026) ends this stage only when every act's history from бр. 1/2003 comes from the Gazette and lex.bg is no longer needed.
- The Gazette path is plan step 5 of `docs/plans/2026-10-21-reasoning-driven-corpus.md`. It is not built yet.

**Gazette eras and the acts before the archive (point 4).**
- The Gazette's per-material HTML starts with бр. 1/2003. Issue PDFs run from 1 January 1989 to 2002. Nothing before 1989 is online.
- The coverage map of 6 September 2026 (`docs/research/2026-09-05-dv-coverage-map/acts-summary.csv`) puts 107 acts in grade C, meaning their base text is from before the online archive. They are 41 ordinances, 30 laws, 27 regulations, 6 implementing acts and 3 codes. Among them are the Закон за задълженията и договорите, the Закон за нормативните актове, the Кодекс на труда and the Наказателен кодекс.
- All 107 are marked in force in their frontmatter. That status comes from lex.bg and has not been checked against the Gazette; the coverage map also found 202 repeal titles in the Gazette that it never attributed to an act. So the complete list that point 4 asks for does not exist yet.

**The Ministry of Justice portal (point 10).**
- The research of 22 June 2026 (`docs/research/2026-06-22-I4-official-consolidation.md`) found that the portal (`justice.government.bg/home/normdoc/{id}`) publishes full consolidated texts, with amendment notes on each element and earlier versions of each element.
- It covers a selected set of acts, mostly those close to the ministry: the Закон за нормативните актове, the Constitution, citizenship, the judiciary, civil procedure, the Кодекс на труда and the trade register. The Закон за обществените поръчки was not found there.
- It has no API and no bulk access.
- Its consolidation is done by a private vendor, Ciela Norma, under a 2017 contract, not by the state.
- The project already names it as a witness that the corpus is compared against and never deferred to (`docs/plans/2026-10-21-reasoning-driven-corpus.md`).

**Указ № 883 of 1974 (point 10).**
- Decision D-049-addendum (3 July 2026) records that lex.bg has no path to this act.
- The corpus text was taken from a PDF on strategy.bg, a government domain, whose page footers show it came from the APIS platform.
- It was used as a verified reference text only, with an invented identifier and `fuente: strategy.bg`. The list of abbreviations in its § 3 was left out because the source showed only a fragment of it.
- A capture independent of APIS, ideally ДВ бр. 39/1974 itself, is recorded as still open.
- The night run of 21 to 22 October 2026 again found lex.bg answering this act's address with a server error.

**APIS and the legal position (point 10).**
- APIS is the oldest Bulgarian legal-information vendor.
- Decisions D-038 and D-039 (21 June 2026) record that lex.bg and APIS both claim a database right over their collections. The project fetches only the legislative texts, which are in the public domain, and builds its own structure from them, reusing none of a provider's database.
- A paid subscription would cost money, and its terms of use would need reading against D-039. Both are the owner's to decide.

## The owner's agreement of 22 October 2026, and the next set of work

Later the same day the owner agreed with the record above and set the first two tasks of the next set of work, in this order. As above, these are readings.

**A. A kept exceptions list comes first.** Some acts must be taken from a source other than lex.bg, so the project keeps a list of them, each with its source and the reason. Today two such acts exist with nothing to mark them: Указ № 883, taken from strategy.bg, and the Закон за обществения транспорт, whose lex.bg text lacks § 1.

**B. Then the full fetch of the Закон за обществения транспорт from the State Gazette.** The owner uses this act in daily work, so its text must be right first. "Full" means the act as promulgated (ДВ бр. 32 от 1.4.2026 г., material 242220) and every later Gazette material that amends it. The Gazette index in `data/dv/materials.jsonl` reaches бр. 96/2026 and lists no amendment of it, so today the act as promulgated is the whole text; the fetch checks again for issues after бр. 96.

The proposed steps to build both, and the later steps for the rest of the record, are in the diagram `docs/plans/2026-10-22-reading-write-path-diagram.html`, section 6. They are a proposal: the owner's agreement turns them into a plan.

## Still open for the owner

- **The proposed steps** in the diagram's section 6, for agreement.
- **Point 10's subscription** (service, length, cost) is a spending decision for the owner.
- **The frontmatter of an act taken from the Gazette** (`fuente`, `identificador`, the provenance base) is a protected surface of the project, so it goes through the project's preflight before step S2 writes it.
