# Structure map, first test results (night of 21 to 22 October 2026)

Who this is for: the owner, reading this on the morning of 22 October 2026 before running the rest of the test set with the session.

## What ran

The pipeline of plan step 3 (decision D-069, the reading architecture of 21 October 2026) was built during the night and run on five acts of the test set, all on Claude Opus 5.5 through this session's plan: the structure map per section (one subagent call per section of up to 60 blocks), the assembler that copies the blocks under the labels, the mechanical checks, and the exception ladder (round 1 re-labels an excepted block with its neighbours). Nothing was written to the corpus; every output is kept per act in the run folder named in the Provenance section (blocks, tasks, the model's maps, the staged Markdown, the diff against the corpus file, a report per round).

The raw fetch of all 3,624 lex.bg act pages (plan step 2) ran in parallel and was still fetching at the time of writing; its log (Provenance) says where it ended.

## Results per act

| Act | Blocks | Sections (calls) | Exceptions after round 0 → round 1 | Source findings | Diff lines against the corpus | State |
|---|---|---|---|---|---|---|
| Закон за обществения транспорт (ЗОТ; cases N1 and E8 of the test set) | 572 | 17 | 0 | 1: the heading „Допълнителна разпоредба" has no § 1 under it, which is the known lex.bg omission | 39 | done |
| Конституция (case N3) | 615 | 15 | 5 low-confidence → 0 | none | 12 | done |
| Закон за изплащане на задълженията, уговорени в злато (case N7) | 3 | 1 | 3 (a "Член единствен" the vocabulary lacked) → 0 | none | 0 | done |
| Наредба № 04-14 от 2019 г. (cases N4 and E7) | 554 | 9 | 29 low-confidence annex rows → 21 | none | 20 | round 1 collected; 21 annex rows still low-confidence because the first tasks lacked the annex heading as context (fixed in the driver after the run); their labels are all `annex_row`, which is right |
| Закон за задълженията и договорите (ЗЗД, 1950; cases E1 and E2) | 932 | 26 | 101: 95 low-confidence heading levels, 2 list lines without numbers, 2 unknown | 2 empty headings | 182 | round 0 collected; round 1 run only on the 2 hard blocks; the 95 are a formatting policy question, below |

Label errors found by the checks and corrected in the night: none on ЗОТ and the Constitution after round 1; the tiny act needed one vocabulary addition (`Член единствен`); ЗЗД needed two (`unnumbered_item`, `Параграф единствен`).

## What the diffs show

Every diff line was read. They fall into four kinds, none of them a wording change:

1. **The corpus holds lex.bg chrome.** ЗОТ's corpus file ends with the "Релевантни актове от Европейското законодателство" list of EU regulations, which is lex.bg navigation; the pipeline drops it (label `drop` with a reason). This is the defect class FR-036 of the future-requirements register (site chrome in act bodies), found again by the new path.
2. **The corpus has a heading stored as plain text or at the wrong level.** ЗОТ's „Допълнителна разпоредба" is plain text in the corpus; the Constitution's title is a level-3 heading in the corpus and a level-1 heading in the staged file.
3. **A corpus wording defect.** Наредба № 04-14's issuing line reads „министъра наздравеопазването" in the corpus (a space lost at an inline element boundary by the old parser); the staged file has „на здравеопазването", copied from the source.
4. **Formatting conventions that differ and need the owner's word.** The § provisions are bold in the staged files (the current convention) and plain in older corpus files; annex headings on two lines are joined into one heading line; ЗЗД's pre-1974 structure („ОБЩА ЧАСТ", Roman and Arabic numbered divisions, lettered subdivisions) is rendered at four heading levels where the corpus had all of them at level 3.

## What the night found about the pipeline itself

- **lex.bg wraps words of the act in advertising links** (`<a class="contextads">строител</a>ните`). The first splitter dropped them, losing words in every fixture but ЗЗД; it now keeps the text of any inline element whatever its class, and a test asserts character-for-character equality between the page's content region and the blocks on five fixtures.
- **A clean-context review found 22 defects** (4 blocking, 9 major) in the first version; all are fixed and covered by 12 tests; a second review was requested before the morning.
- **Cost of the run driver as subagents:** about 70,000 tokens of plan usage per labelling call, of which the section's content is 3,000 to 8,000; the rest is the subagent's fixed context. About 100 calls were made during the night. A leaner driver (a workflow with a minimal prompt, or batching several small sections per call) would cut this several times; it is a how, and it is noted for step 6.

## Decisions for the owner this morning

1. **Heading levels for pre-1974 acts** (ЗЗД and its kind): accept the four-level rendering the model proposed, or keep one level as the corpus has. The 95 low-confidence labels of ЗЗД are this one question; the model's labels are consistent with each other.
2. **§ provisions bold** in every act (the current convention) and **two-line annex headings joined**: confirm both as the corpus convention, or say otherwise.
3. **The corpus defects found** (chrome kept, headings as plain text, a lost space): they are corrected by the staged files; they enter the corpus only through step 4's gate and your merge.

## What is left of the test set

Not yet labelled: Кодекс на труда (107 calls), Наказателен кодекс (78), Данъчно-осигурителен процесуален кодекс (158), Търговски закон (184), Кодекс за социално осигуряване (192), Кодекс на търговското корабоплаване (87), Закон за данък върху добавената стойност (118), Граждански процесуален кодекс (131), Наредба № 1 от 2013 г. (14), and the two acts whose raw pages were not fetched when the run started (Наредба № 5 от 1999, Правилник на НС). Together about 1,070 calls on the current driver. The order is yours; the pipeline is ready and resumable per act and per round.

## Glossary

- **Structure map**: the list of labels the model returns, one per block of a page's text, saying what each block is (heading, article, paragraph, item, annex row, chrome); the model writes no text.
- **Block**: one line of the page's text as the deterministic splitter cuts it; every character of the act lands in exactly one block.
- **Section (calls)**: a run of up to 60 blocks sent to the model in one call.
- **Exception**: a block that a mechanical check rejected or that the model labelled with low confidence; the ladder re-labels it with its neighbours in up to two rounds; what remains is the residue for a whole-act read.
- **Source finding**: a check result that describes the source, not a label (a heading with nothing under it), recorded and never re-labelled.
- **Staged file**: the Markdown the pipeline assembled from the blocks, kept outside the corpus.
- **D-069**: the decision of 21 October 2026 in the repository's decision log that adopted this way of reading.
- **FR-036**: the registered defect class "lex.bg site chrome inside an act body".
- **Cases N1 to N8 and E1 to E16**: the rows of the test-set document (References).
- **lex.bg**: the private consolidated-law site the corpus was photographed from; its pages are the raw source of this run.

## References

- The test set: `docs/testing/2026-10-22-structure-map-test-set.md` in this repository, 21 October 2026.
- The plan of record: `docs/plans/2026-10-21-reasoning-driven-corpus.md`, step 3.

## Provenance

Run folder: `data/runs/structure-map-2026-10-22/<act>/` (untracked). Raw fetch log: `data/runs/raw-fetch-lexbg-2026-10-21.log`; raw store `data/raw/lexbg/` (ignored by git until the owner decides where it lives). Summary table: `.venv/bin/python reading/summary.py --md`. Code: `reading/` and `scripts/raw_fetch_lexbg.py` on branch `plan/2026-10-21-reasoning-driven-corpus`.
