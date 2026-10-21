# Structure map, first test results (night of 21 to 22 October 2026)

Who this is for: the owner, reading this on the morning of 22 October 2026 before running the rest of the test set with the session.

## What ran

The pipeline of plan step 3 (decision D-069, the reading architecture of 21 October 2026) was built during the night and run on six acts of the test set, all on Claude Opus 5.5 through this session's plan: the structure map per section (one subagent call per section of up to 60 blocks), the assembler that copies the blocks under the labels, the mechanical checks, and the exception ladder (round 1 re-labels an excepted block with its neighbours). Nothing was written to the corpus; every output is kept per act in the run folder named in the Provenance section (blocks, tasks, the model's maps, the staged Markdown, the diff against the corpus file, a report per round).

The raw fetch of all 3,624 lex.bg act pages (plan step 2) ran in parallel at one request per second and ended at 05:25 with 3,623 pages in the raw store (1.6 GB) and no Cloudflare halt. The one page missing is Указ № 883 от 1974 г. за прилагане на Закона за нормативните актове: lex.bg answers its address with a server error („Unauthorized … Error retrieving document!"), on two tries; its corpus file was never from lex.bg (its source field says strategy.bg), so it stays an act outside the lex.bg path.

## Results per act

| Act | Blocks | Sections (calls) | Exceptions after round 0 → round 1 | Source findings | Diff lines against the corpus | State |
|---|---|---|---|---|---|---|
| Закон за обществения транспорт (ЗОТ; cases N1 and E8 of the test set) | 572 | 17 | 0 | 2 on one omission: the heading „Допълнителна разпоредба" has no § 1 under it, and the first § of the act's own provisions is § 2; this is the known lex.bg omission, now caught by its own number and not only by the empty heading | 39 | done |
| Конституция (case N3) | 615 | 15 | 5 low-confidence → 0 | none | 12 | done |
| Закон за изплащане на задълженията, уговорени в злато (case N7) | 3 | 1 | 3 (a "Член единствен" the vocabulary lacked) → 0 | none | 0 | done |
| Наредба № 04-14 от 2019 г. (case E7) | 554 | 9 | 29 low-confidence annex rows → 21 | none | 20 | round 1 collected; 21 annex rows still low-confidence because the first tasks lacked the annex heading as context (fixed in the driver after the run); their labels are all `annex_row`, which is right |
| Закон за задълженията и договорите (ЗЗД, 1950; cases E1 and E2) | 932 | 26 | 101: 95 low-confidence heading levels, 2 list lines without numbers, 2 unknown → 99: the 95, plus the 4 unmarked quoted articles (Чл. 1001а to 1001г) the anchoring rule sends to the residue | 2 empty headings; 2 markup fragments („Чл. 5./span>", „Чл. 10./span>") printed in the page itself | 184 | round 0 collected; round 1 run only on the 2 hard blocks; the 95 are a formatting policy question, below |
| Наредба № 1 от 2013 г. за съхраняване на запаси от нефт и нефтопродукти (case N4; five annex forms) | 663 | 14 | 1 low-confidence (the issuer line under the title, which the vocabulary did not name) → 0 | none | 1,696 | done; every one of its 342 annex rows labelled `annex_row` with high confidence once the driver gave the annex heading as context |

Label errors found by the checks and corrected in the night: none on ЗОТ and the Constitution after round 1. The tiny act needed one vocabulary addition (`Член единствен`) and ЗЗД two (`unnumbered_item`, `Параграф единствен`). Наредба № 1 needs one more: the issuer line „Издадена от …" under a title belongs to the publication lines, and the vocabulary named only the in-force line.

## What the diffs show

Every diff line was read. They fall into five kinds, none of them a wording change:

1. **The corpus holds lex.bg chrome.** ЗОТ's corpus file ends with the "Релевантни актове от Европейското законодателство" list of EU regulations, which is lex.bg navigation; the pipeline drops it (label `drop` with a reason). This is the defect class FR-036 of the future-requirements register (site chrome in act bodies), found again by the new path.
2. **The corpus has a heading stored as plain text or at the wrong level.** ЗОТ's „Допълнителна разпоредба" is plain text in the corpus; the Constitution's title is a level-3 heading in the corpus and a level-1 heading in the staged file.
3. **A corpus wording defect.** Наредба № 04-14's issuing line reads „министъра наздравеопазването" in the corpus (a space lost at an inline element boundary by the old parser); the staged file has „на здравеопазването", copied from the source.
4. **The corpus has lost the paragraph topology of an act.** Наредба № 1's corpus file holds every article as one line: its alineas „(1)", „(2)" and its items „1.", „2." run together in one paragraph; the staged file has one line per provision, as the source has. This is the paragraph-topology defect that decision D-058 names, and it alone makes 1,696 diff lines for this act. The same file lacks the repeal note of May 2026 that the source now carries (the corpus frontmatter says the act is repealed but its body was last updated on 15 July 2025), and its chapter headings read „Глава първа.ОБЩИ ПОЛОЖЕНИЯ" with the space lost after the full stop.
5. **Formatting conventions that differ and need the owner's word.** The § provisions are bold in the staged files (the current convention) and plain in older corpus files; „Член единствен." and „Параграф единствен." are bold like every other article and § opener, where the corpus has them plain (the whole diff of the tiny act); annex headings on two lines are joined into one heading line; ЗЗД's pre-1974 structure („ОБЩА ЧАСТ", Roman and Arabic numbered divisions, lettered subdivisions) is rendered at four heading levels where the corpus had all of them at level 3.

## What the night found about the pipeline itself

- **lex.bg wraps words of the act in advertising links** (`<a class="contextads">строител</a>ните`). The first splitter dropped them, losing words in every fixture but ЗЗД; it now keeps the text of any inline element whatever its class, and a test asserts character-for-character equality between the page's content region and the blocks on five fixtures.
- **Four clean-context reviews on Opus 5.5, then the loop stopped.** The first found 22 defects (4 blocking, 9 major) in the first version. The second found 0 blocking and 2 major, the third 0 and 4, the fourth 0 and 2. Every major was a deeper form of the same two holes: a line of the act losing its address under a label that is not a head, and a line of the act dropped without an exception. Both are now closed by fixed-form rules. A line opening with an article or § number carries only `article_head`, `paragraph_sign` or `quoted`. A quoted block that opens like a provision starts with a quotation mark or stands inside a quotation an earlier quoted block opened with one. A drop is allowed only for lex.bg's dashed separator, the single button before the title and the EU-acts list after the act; everything else dropped is an exception. A gap in article or § numbers, a malformed § head and the page's chrome under a content label are findings. The majors did not fall for two rounds (2, 4, 2), which is the rule's signal to change method rather than run a fifth round, so the fourth round's five minors (a quoted address of another act read as a gap, a theoretical case the reviewer could not find in the corpus; the seven chrome-only pages; malformed § heads; chrome under a content label; dot lines) were fixed where cheap and the rest is listed below for your ruling. 19 tests cover the package.
- **Unmarked quotations go to the whole-act read by design.** ЗЗД's transitional provision reprints four articles of the 1952 civil procedure act (Чл. 1001а to 1001г) with no quotation marks, as old sources did. The anchoring rule sends them through the ladder to the residue, where a person confirms they are quoted text; the four are listed in ЗЗД's row. The fourth reviewer sampled 600 raw pages: after an amending colon, lex.bg opens the quoted run with a quotation mark in 265 of 266 runs that start with an address, so the residue from this rule is small and old.
- **Seven lex.bg pages hold no act.** The raw store has seven pages that are site chrome only (53 blocks of navigation, no title, no article): the corpus files with lex.bg identifiers -549676032, 2135625007, 2136890603, 2137254795, 2137254802, 2137254803 and 2137254804. The run driver refuses them. They are a source finding: whatever those corpus files hold did not come from these pages as they are today.
- **Cost of the run driver as subagents:** about 70,000 tokens of plan usage per labelling call, of which the section's content is 3,000 to 8,000; the rest is the subagent's fixed context. About 100 calls were made during the night. A leaner driver (a workflow with a minimal prompt, or batching several small sections per call) would cut this several times; it is a how, and it is noted for step 6.

## Decisions for the owner this morning

1. **Heading levels for pre-1974 acts** (ЗЗД and its kind): accept the four-level rendering the model proposed, or keep one level as the corpus has. The 95 low-confidence labels of ЗЗД are this one question; the model's labels are consistent with each other.
2. **§ provisions bold** in every act (the current convention), **„Член единствен." bold** like „Чл. N.", and **two-line annex headings joined**: confirm these as the corpus convention, or say otherwise.
3. **The corpus defects found** (chrome kept, headings as plain text, a lost space, lost paragraph topology, a missing repeal note): they are corrected by the staged files; they enter the corpus only through step 4's gate and your merge.
4. **The review loop.** Four rounds closed every blocking and major finding; the method rule says stop when majors do not fall for two rounds. Say whether a fifth round on a different model (Fable, the session's own) is worth its cost before the remaining test-set acts run, or whether the remaining acts' real results are the better check.

## What is left of the test set

Not yet labelled, all prepared (split into blocks and tasks): Кодекс на труда (107 calls), Наказателен кодекс (78), Данъчно-осигурителен процесуален кодекс (158), Търговски закон (184), Кодекс за социално осигуряване (192), Кодекс на търговското корабоплаване (87), Закон за данък върху добавената стойност (119, re-split after the table-cell fix), Граждански процесуален кодекс (131), Правилник за организацията и дейността на Народното събрание (19; the repealed-act case E15), and Наредба № 5 от 1999 г. за структурата на записа в цифров вид на кадастралните планове (79; 6,030 blocks, nearly all annex rows). Together about 1,154 calls on the current driver. The order is yours; the pipeline is ready and resumable per act and per round.

## Glossary

- **Structure map**: the list of labels the model returns, one per block of a page's text, saying what each block is (heading, article, paragraph, item, annex row, chrome); the model writes no text.
- **Block**: one line of the page's text as the deterministic splitter cuts it; every character of the act lands in exactly one block.
- **Section (calls)**: a run of up to 60 blocks sent to the model in one call.
- **Exception**: a block that a mechanical check rejected or that the model labelled with low confidence; the ladder re-labels it with its neighbours in up to two rounds; what remains is the residue for a whole-act read.
- **Source finding**: a check result that describes the source, not a label (a heading with nothing under it), recorded and never re-labelled.
- **Staged file**: the Markdown the pipeline assembled from the blocks, kept outside the corpus.
- **D-069**: the decision of 21 October 2026 in the repository's decision log that adopted this way of reading.
- **FR-036**: the registered defect class "lex.bg site chrome inside an act body".
- **D-058**: the decision in the repository's decision log that the Markdown must keep an act's paragraph topology (one line per alinea and item).
- **Cases N1 to N8 and E1 to E16**: the rows of the test-set document (References).
- **lex.bg**: the private consolidated-law site the corpus was photographed from; its pages are the raw source of this run.

## References

- The test set: `docs/testing/2026-10-22-structure-map-test-set.md` in this repository, 21 October 2026.
- The plan of record: `docs/plans/2026-10-21-reasoning-driven-corpus.md`, step 3.

## Provenance

Run folder: `data/runs/structure-map-2026-10-22/<act>/` (untracked). Raw fetch log: `data/runs/raw-fetch-lexbg-2026-10-21.log`; raw store `data/raw/lexbg/` (ignored by git until the owner decides where it lives). Summary table: `.venv/bin/python reading/summary.py --md`. Code: `reading/` and `scripts/raw_fetch_lexbg.py` on branch `plan/2026-10-21-reasoning-driven-corpus`.
