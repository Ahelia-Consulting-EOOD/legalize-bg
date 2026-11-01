# Structure map, batch 1 of the audit (21 October 2026)

Who this is for: the owner. The document asks for six decisions, listed at the end: what happens to the 79 blocks the ladder (the re-label rounds 1 and 2) left for a reviewer, whether the three gaps found in the checks are fixed before batch 2, and how batch 2 runs. The owner knows the project, the reading architecture of 21 October 2026 (decision D-069) and the run-driver design of 22 October (decision D-070), and has read the test-set results of 22 October.

## The bottom line

All 34 acts of the batch have a structure map, a staged text and a report through round 2. The labeller answered every one of its 292 calls, and every answer file parsed. Of 67,251 blocks, the checks flagged 380 after round 0 (0.6 percent), 195 after round 1 and 90 after round 2; the 90 affect 79 blocks. Of those 79, 18 are gaps in the checks and not doubts about a label, and 36 are the lex.bg habit of printing a superseded heading after the current one, which the test set already put to the owner. The run cost about one third more per section than the plan estimated. By the token count visible during the run it stayed under the plan's stop line of 12 million; by the finer count made afterwards it passed that line by five percent. The reasons are known and are given in the cost section.

## What ran

The run followed the batch plan of 21 October: the lean labeller agent of this branch, one call file of eight sections per call in round 0, one compact answer file per call, and the ladder at twenty-five re-labels per call. Six calls of round 0 ran at sixteen sections for the drift measurement. The calls went out in waves through the workflow script of the plan. From the third wave on, a wave held 32 calls instead of the plan's 16: 16 calls finished in under four minutes, and the driver treats a call as running for fifteen minutes. Nothing was written to the corpus.

One mistake during the run: the last wave of round 0 was capped at 40 calls and left the final five sections of the competition law unsent. That one call ran on its own, and the act's round-0 results were rebuilt before its round 1. The figures below are from after the repair.

The round counts: round 0 made 233 calls over 1,798 sections; round 1 made 33 calls over 366 re-labels; round 2 made 26 calls over 177. No call came back defective, no answer was set aside as stale, and no task went unanswered after the repair.

## Results per act

Exceptions are counted after each round; the residue is what round 2 left for a reviewer. Source findings describe the page and are never re-labelled. The diff is the staged file against the corpus file, in changed lines. The form column is read from the final map: how the act is divided, and what it carries besides articles.

| Act | Type | Blocks | Form | Exceptions after round 0, 1, 2 | Residue | Source findings | Diff lines |
|---|---|---|---|---|---|---|---|
| Закон за обществените поръчки | law | 4,333 | large; parts; 38 annex headings with 1,249 annex rows; article titles | 10, 9, 8 | 8: four pairs of superseded headings | none | 932 |
| Закон за нормативните актове | law | 166 | small; chapters only | 4, 3, 2 | 2: items written „1)“ and „2)“ | none | 11 |
| Закон за устройство на територията | law | 2,673 | large; parts | 12, 8, 8 | 6: a repeated section heading (2 blocks), two § written without the sign, an amending law's title over its provisions, item 86 after 84 | none | 1,409 |
| Административнопроцесуален кодекс | code | 2,158 | medium; parts; 72 quoted provision lines; article titles | 4, 2, 0 | 0 | 1 fragment | 927 |
| Наказателно-процесуален кодекс | code | 3,490 | large; parts; article titles | 19, 7, 0 | 0 | 12 fragments | 1,635 |
| Изборен кодекс | code | 3,646 | large; parts; 15 annex headings with 144 rows; article titles | 21, 6, 0 | 0 | 5 empty headings | 1,627 |
| Кодекс за застраховането | code | 6,186 | very large; parts and subsections; 6 annex headings with 366 rows; article titles | 19, 15, 2 | 2: a heading-level doubt, item 58 twice | none | 2,110 |
| Семеен кодекс | code | 975 | medium; chapters and sections; article titles | 1, 0, 0 | 0 | 6 fragments | 473 |
| Кодекс на международното частно право | code | 599 | small; parts; article titles | 0, 0, 0 | 0 | none | 341 |
| Закон за местното самоуправление и местната администрация | law | 680 | small; chapters only | 3, 0, 0 | 0 | none | 66 |
| Закон за администрацията | law | 542 | small; chapters only | 4, 1, 2 | 1: alinea (11) twice in § 16 | none | 68 |
| Закон за държавния служител | law | 1,314 | medium; chapters and sections; article titles | 3, 3, 0 | 0 | none | 677 |
| Закон за съдебната власт | law | 3,430 | large; chapters and sections | 19, 15, 16 | 15: fourteen superseded heading lines, one alinea written „(2“ | 2 empty headings | 253 |
| Закон за публичните финанси | law | 1,601 | medium; chapters and sections; 107 quoted provision lines | 6, 0, 0 | 0 | none | 25 |
| Закон за държавната собственост | law | 764 | medium; chapters and sections | 3, 0, 0 | 0 | 1 empty heading | 130 |
| Закон за общинската собственост | law | 650 | small; chapters only | 0, 0, 0 | 0 | none | 55 |
| Закон за достъп до обществена информация | law | 551 | small; chapters and sections; article titles | 5, 0, 0 | 0 | 2 fragments | 195 |
| Закон за електронното управление | law | 835 | medium; chapters and sections; article titles | 19, 19, 1 | 1: a stray repeated section line | none | 368 |
| Закон за защита на личните данни | law | 743 | medium; chapters and sections | 14, 1, 1 | 1: a repeated section line | none | 102 |
| Закон за юридическите лица с нестопанска цел | law | 433 | small; chapters and sections; article titles | 2, 2, 0 | 0 | 1 empty heading | 171 |
| Закон за данъците върху доходите на физическите лица | law | 1,537 | medium; parts; one annex heading; article titles | 12, 5, 5 | 5: two superseded headings (4 blocks), a chapter title carrying its repeal | none | 488 |
| Закон за корпоративното подоходно облагане | law | 4,042 | large; parts; 10 annex headings with 107 rows; 62 table rows in provisions; article titles | 20, 21, 8 | 8: a numbered list inside a definition (4), letters restarting after prose (4) | 40 fragments | 1,827 |
| Закон за местните данъци и такси | law | 2,415 | medium; chapters and sections; 6 annex headings with 815 rows; 199 table rows in provisions | 15, 1, 1 | 1: an article opening at (2) | none | 7,207 |
| Закон за кадастъра и имотния регистър | law | 993 | medium; parts; 40 quoted provision lines | 3, 2, 0 | 0 | 4 fragments | 73 |
| Закон за собствеността | law | 312 | small; chapters and sections; unnumbered paragraphs of the older drafting | 6, 2, 2 | 1: Art. 99 printed without „Чл.“ | none | 68 |
| Закон за енергетиката | law | 3,782 | large; chapters and sections | 24, 25, 16 | 10: three items numbered 27аа, 34дд, 66аа (dropped by the check), three superseded headings (5 blocks), the separator before the adoption formula, alinea (3) twice | 1 fragment, 3 empty headings | 262 |
| Закон за опазване на околната среда | law | 2,982 | large; chapters and sections; 14 annex headings with 749 rows | 7, 0, 0 | 0 | 1 malformed § head, 2 empty headings | 299 |
| Закон за управление на отпадъците | law | 2,269 | medium; chapters and sections; 9 annex headings with 391 rows | 25, 15, 14 | 14: annex rows with footnote markers, a check artefact | none | 183 |
| Закон за автомобилните превози | law | 1,673 | medium; chapters and sections; 3 annex headings | 24, 1, 0 | 0 | 1 fragment | 240 |
| Закон за движението по пътищата | law | 2,890 | large; chapters and sections; 2 annex headings with 83 rows; 55 table rows in provisions | 14, 2, 2 | 2: item 11 without its dot, Чл. 166¹ read as 1661 | 3 fragments, 2 empty headings, 1 article gap | 369 |
| Закон за пътищата | law | 1,324 | medium; chapters only; 3 annex headings with 113 rows; 18 table rows; 23 quoted lines | 5, 3, 0 | 0 | 3 fragments | 154 |
| Закон за концесиите | law | 2,250 | medium; chapters and sections; 20 annex headings with 429 rows; 131 quoted lines | 7, 5, 0 | 0 | none | 127 |
| Закон за електронните съобщения | law | 3,587 | large; chapters and sections | 36, 10, 1 | 1: alinea (6) twice | 1 fragment, 6 empty headings | 359 |
| Закон за защита на конкуренцията | law | 1,426 | medium; parts; article titles | 14, 12, 1 | 1: a repeated chapter number line | none | 470 |

Seventeen acts ended with no residue. This batch adds no form beyond those the test set had already run: every act is a law or a code divided into chapters, with or without sections or parts, some with annexes and tables. The forms that were clean in the test set are clean here too: the four chapters-only laws and the small code with parts (the private international law code) ended with no residue, and the last of them had no exception in any round.

## The residue, for the owner

The 90 exceptions on 79 blocks fall into five kinds. Each block, its text and the labeller's note are in the round-2 report of its act (see Provenance).

1. **Superseded headings printed by lex.bg: 36 blocks in eight acts, 23 dropped and 13 kept as notes.** When a chapter or section was renamed, lex.bg prints the current heading and then the old number line and the old title again. The labeller dropped them in the public procurement law (8 blocks), the judiciary law (14 blocks, five of them cut to a fragment such as „Дис“ or „У“) and the personal data law (1 block). The check reports each as a drop inside the act. In five other acts the labeller kept them as editorial notes with low confidence: the spatial planning law 2, the energy law 5, the personal income tax law 4, e-government 1, competition 1. This is the same reading the test set put to the owner. The owner's decision settles all of them: a drop, an editorial note, or a heading. Until then, the staged text of these acts has them dropped where the labeller dropped them and kept as notes where it did not.
2. **Three gaps in the checks, not in the labelling: 18 blocks.** The labeller read these right and the check refused the answer. In the energy law, three definition items are numbered 27аа, 34дд and 66аа, inserted by an amendment of 2023 between 27а and 27б; the number grammar allows a doubled letter on a lettered item but not on a numbered one, so the entry was discarded and the block went unlabelled in every round, although the labeller gave the same answer three times. In the road traffic law, Чл. 166¹ is written with a superscript on a bare number; the instructions say to write the number as 1661, and the order check then reads 1661 as larger than 166а and reports an article gap. In the waste law, fourteen annex rows carry footnote markers written as two or more asterisks, which the reassembly check strips as bold markup before comparing, so it reports a difference where the staged text matches the page exactly. Fixing the three is a change to the checks, which the batch plan put outside this batch; the staged texts are right as they stand, except that the three energy items have no label.
3. **Irregularities the acts themselves carry: 13 blocks.** The administration law has two alineas (11) in § 16, both from the Gazette: one added in 2025, one added in 2026 and repealed in July 2026. The insurance code has item 58 twice, the energy law alinea (3) twice, the electronic communications law alinea (6) twice. The spatial planning law has item 86 after 84 and two § written without the sign (35 and 48). The property law has Art. 99 without „Чл.“. The judiciary law has „(2“ without its closing bracket. The road traffic law has item 11 without its dot. The local taxes law has an article that opens at (2). The normative acts law writes two items as „1)“ and „2)“. The labels are right, and the checks report what the page says. These are source findings in all but name, and a reviewer decides whether the corpus text keeps the page's form.
4. **Forms the vocabulary does not name: 8 blocks.** In the corporate income tax law a definition item holds a numbered list of four, which the labeller called continuation lines in all three rounds because the vocabulary has no item under an item; and four lettered sub-items restart at а) after a paragraph of prose inside a definition, which the order check reads as a fault. The test set met the first form in the social security code. Whether such a list is an item or a continuation is a convention for the owner.
5. **Minor doubts: 4 blocks.** The dashed separator before the adoption formula of the energy law, kept as an editorial note where a drop is also plausible (the test set left the same line in the parliament's rules). A line „Общи положения“ in the insurance code that may be a section heading or an article title. The title of an amending law printed over its own transitional provisions in the spatial planning law. A chapter title of the personal income tax law that carries its repeal marker.

## Source findings

The checks recorded 131 findings about the pages, none of them a label:

- **74 fragments of markup in article heads.** They are of two kinds. The first is a closing tag left in the text, „Чл. 26./span>.“, already seen in the test set: the criminal procedure code has 12, the family code 6, the cadastre law 4, and four acts one each. The second is a superscript written as „Чл. 260я.SUP>1.“: the corporate income tax law has 40, the roads laws and others a few each. The corpus files carry the same fragments.
- **55 empty headings.** A heading with nothing under it before the next heading. Most are sections repealed as a whole whose heading remains with its repeal note (the judiciary law's two specialised criminal courts, the electronic communications law's six sections on infrastructure rights). The electoral code's five are the heading „МЕТОДИКА“ of its annexes, printed on its own line before the annex. None is the missing-§ case of the test set.
- **One malformed § head** („§ 93.Този закон“, the space lost) and **one article gap** that is the superscript case of the road traffic law above.

## What the diffs show

The 34 diffs hold the same kinds the test set named, and no wording change by the pipeline. The bulk of every code's diff is the corpus file's lost paragraph topology (decision D-058). The corpus has an article's title, head, alineas and items on one line, where the staged file has one line per provision. The insurance code has 91 such lines, the electoral code 44, the corporate income tax law 33. Every act's corpus file ends with lex.bg's list of related EU acts, which the pipeline drops (defect class FR-036). Bold § openers and bold article heads against plain ones in the corpus are convention differences awaiting the owner's word, as in the test set.

One diff needs a check this batch did not do: the local taxes law shows 7,207 changed lines. Most are rows of its annex tables and of the tables inside its provisions, and their cell values differ from the corpus file (a range „от 147 до 441“ against „от 342 до 1026“ in the same row). The corpus file was last updated on 16 June 2026. Whether the page carries a later amendment of the tables or the old parser read them differently is not settled here.

## Cost and duration against the plan's estimate

Every figure below is read from the usage records of the 292 subagent transcripts. The four token classes are given per call as medians. Dollars are at the Claude Opus 5.5 list price of 6 October 2026: uncached input 4, five-minute cache write 5, cache read 0.40, output 20 dollars per million tokens. They compare the run with the plan's estimate. The runs draw on the owner's plan, whose metering is not published.

| Measure, round 0 at eight sections per call | Plan's estimate (warm cache) | Measured, median over 227 calls |
|---|---|---|
| API requests per call | 3 | 3 |
| Uncached input, tokens | 0 | 6 |
| Cache write, five-minute, tokens | 25,614 | 34,023 |
| Cache write, one-hour, tokens | 0 | 0 |
| Cache read, tokens | 43,908 | 39,878 |
| Output, tokens (of which thinking) | 5,707 | 7,879 (1,650) |
| Context counted once, tokens per call | 34,341 | 46,141 |
| Dollars per call | 0.260 | 0.347 |
| Cents per section | 3.1 | 5.0 |
| Duration per call, seconds | about 89 | 55 |
| Share of the first request read from a warm cache | 12 percent (the system part only) | 63 percent |

A sixteen-section call made 4 requests in 118 seconds, wrote 68,368 tokens, read 92,434 and produced 17,288, at 0.711 dollars per call and 4.6 cents per section (medians over the six). A ladder call cost 0.102 dollars for ten re-labels in round 1 (0.9 cents per re-label) and 0.061 for five in round 2 (1.0 cents). The plan estimated 0.5 cents per re-label at twenty-five per call, and the batch's rounds had fewer re-labels per act than that.

Over the whole batch: 9.45 million tokens written to the five-minute cache (47.25 dollars), 14.47 million read (5.79), 2.07 million output of which 0.40 million thinking (41.45), 1,960 uncached (0.01); 94.50 dollars at list price. Round 0 cost 6,550 tokens per section counted once and 4.97 cents; the plan said 4,039 and 3.1 to 3.3.

**The budget.** The plan's budget was about 9 million tokens counted once and a stop line at 12 million. Two counts exist. The workflow harness reports a figure per wave, which was the one visible during the run: 10.59 million over the batch (9.81 million in round 0), under the stop line throughout. The finer count from the transcripts, the largest request's context of each call plus every output token, gives 12.65 million, five percent past the line. By either count the run went about a third over the estimate. The difference has three causes the records show. The cache write per call is a third above the estimate (34,023 against 25,614). The first request's context is 6,164 tokens and not 4,068: the labelling instructions now live in the agent definition, as the plan recommended, and add about 1,600 tokens to it, and the workflow harness adds its own header. The output per call is 38 percent above the estimate (7,879 against 5,707), of which 1,650 tokens are thinking the estimate did not separate. And on 94 of the 227 calls the agent made four or five requests instead of the estimate's three. What the measurement showed in the plan's favour: the warm prefix covers 63 percent of the first request against the 12 percent estimated, because the agent definition with the instructions is shared across sibling calls. The saving the plan hoped for from moving the instructions is real, and the call takes 55 seconds against 89.

**Wall time.** Round 0 ran from 21:57 to 22:36 local time, 39 minutes against the plan's 50; the whole batch with its ladder ended at 22:50.

**The fixed context.** The first request of the first call carried 6,376 tokens of context, written to the cache in full; the median first request of all calls carried 6,164 tokens, of which 63 percent was read from the cache. The first-principles text was not in it: the exemption that decision D-070 gives the labeller also applies when it runs inside a workflow.

**The drift measurement.** The six sixteen-section calls labelled the first 96 sections of the public procurement law. Their exception rate after round 0 was 0.25 percent of blocks (9 of 3,627), against 0.58 percent over the 227 eight-section calls (371 of 63,624). Their second half showed no rise (0.10 percent against 0.44 in the first). The comparison is weak: one act, a clean modern law, against 33 others. What the eight-section calls show on their own is stronger. The exception rate rises with the position of the section in the call, from 0.33 percent at the first position to 0.96 percent at the eighth, and from 0.44 percent in the first half to 0.74 in the second. Six calls do not settle whether a sixteen-section call labels as well as an eight-section one. The rise by position within eight is a finding for batch 2 to test on more than one act.

## Decisions for the owner

1. **The superseded headings** (36 blocks here, and the bulk of the residue in the test set): drop, editorial note, or heading. One ruling settles both batches.
2. **The three check gaps** (doubled letters on item numbers, superscripts on bare article numbers, footnote asterisks in the reassembly check): fix them before batch 2, or carry them as known residue. The fix is to the checks, not to the vocabulary; the plan put check changes outside this batch.
3. **Lists inside definitions**: a numbered list under a definition item is an item or a continuation; letters that restart after prose inside a definition are a new list or an order fault. One convention for both.
4. **The irregularities the pages carry** (13 blocks: duplicate numbers, missing signs and dots): confirm that the corpus keeps the page's form, as the pipeline does now, with each one recorded as a source finding; or ask for a correction path.
5. **Batch 2's settings**: eight sections per call stay unless the owner wants the sixteen-section comparison run on several acts; the measured cost of about 5 cents per section at list price, not 3, is the figure to plan with.
6. **The local taxes diff**: decide whether a reviewer checks the annex tables against the page before that act's staged text is relied on, or the act waits for the Gazette path.

## References

- The 34 acts, as lex.bg publishes them: the pages fetched on 21 October 2026 into the project's raw store (the plan's step 2), one page per act, identified by the act's lex.bg document number recorded in its corpus file.
- The batch plan: `docs/plans/2026-10-22-run-driver-design/batch-1.md`, 21 October 2026, in this repository.
- The test-set results the batch is compared with: `docs/testing/2026-10-22-structure-map-results.md`, 22 October 2026, in this repository.
- The plan's cost estimate: `docs/plans/2026-10-22-run-driver-design/step7/estimate.md`, in this repository.

## Glossary

- **Block**: one line of text as the lex.bg page prints it, the unit the labeller labels.
- **Section**: a run of up to 60 blocks that one labelling task covers; round 0 labels sections, the ladder re-labels single blocks.
- **Exception**: a block the mechanical checks flag after a round: a low-confidence label, an unknown, a number out of order, a dropped line inside the act, or a line whose label does not match its text.
- **Residue**: the exceptions left after round 2, for a reviewer to read.
- **The ladder**: rounds 1 and 2, in which each excepted block is re-labelled on its own with its neighbours as context; what survives round 2 is the residue.
- **Collect**: the driver step that reads a round's answers, rebuilds the map and the staged text, runs the checks and writes the round's report and the next round's tasks.
- **Source finding**: a defect of the page itself (a markup fragment, an empty heading, a malformed head), recorded and never re-labelled.
- **Context counted once**: the tokens of a call's largest request plus every output token, the plan's measure for budgets.
- **Lean labeller**: the project agent of decision D-070 that reads one call file and writes one answer file, with no other tool.
- **D-058, D-069, D-070, FR-036**: decisions and a future-requirement entry of this repository: the paragraph topology defect of corpus files, the reading architecture of 21 October 2026, the run driver of 22 October 2026, and site chrome in act bodies.

## Provenance

- Dates: this document is dated by the clock of the session that ran the batch (21 October 2026). The run folder and the design documents it cites carry the 22 October name they were created under.
- The run folder is `data/runs/structure-map-2026-10-22/<act>/` in this worktree (untracked): `blocks.json`, `tasks/round0..2/`, `calls/round0..2/` (the call files), `maps/round0..2/` (the answer files and their sidecars), `map.json`, `staged.md`, `diff.txt`, `report-round0.json` to `report-round2.json`. Each report's `exceptions` list holds the residue blocks with the labeller's label and note.
- The acts and their sizes: `docs/plans/2026-10-22-run-driver-design/batch-1-acts.json`; the plan: `batch-1.md` beside it.
- The usage measurement: `docs/plans/2026-10-22-run-driver-design/scripts/batch1_usage.py`, run over the session's workflow subagent transcripts; its outputs `calls.csv` (one row per call), `usage.md` and `drift.md` are in `docs/plans/2026-10-22-run-driver-design/batch-1/`.
- The plan's estimate the measurements are compared with: `docs/plans/2026-10-22-run-driver-design/step7/estimate.md`; the test-set figures: `docs/testing/2026-10-22-structure-map-results.md`.
- The workflow runs, in order: wf_f3d7e7c7, wf_dce3f046, wf_6c4d1651, wf_bc94f82a, wf_96c8be31, wf_793aac55, wf_a7070965, wf_2e68f280 (round 0), wf_871b5a94 (the repair call), wf_61be6462 and wf_79c9fa58 (round 1), wf_77ebe3fb (round 2), under the session's `subagents/workflows/` folder.
