# Structure map, results of the test set (21 and 22 October 2026)

Who this is for: the owner, reading this on 22 October 2026 to decide what the reading pipeline does with the residue and the corpus defects it found, before plan step 4 (the write gate) is built.

## What ran

The pipeline of plan step 3 (decision D-069, the reading architecture of 21 October 2026) was built during the night of 21 to 22 October and run on the sixteen acts of the test set, all on Claude Opus 5.5 under this session's plan: the structure map per section (one model call per run of up to 60 blocks), the assembler that copies the blocks under the labels, the mechanical checks, and the exception ladder (round 1 and round 2 re-label an excepted block with its neighbours; what remains after round 2 is the residue for a person). Nothing was written to the corpus; every output is kept per act in the run folder named in the Provenance section (blocks, tasks, the model's maps, the staged Markdown, the diff against the corpus file, a report per round).

Six acts ran in the night through a general-purpose subagent, one section per call. The other ten ran on 22 October through the lean project agent the owner asked for (the agent reads and writes files and nothing else), eight sections per call in round 0 and ten re-label tasks per call in the later rounds. The two ladder rounds the night had left open on Наредба № 04-14 and Закон за задълженията и договорите ran the same way. The lean agent cost about 7,500 tokens of plan usage per section against about 70,000 in the night; the figures are in the section on cost.

The raw fetch of all 3,624 lex.bg act pages (plan step 2) ran in the night at one request per second and ended at 05:25 with 3,623 pages in the raw store (1.6 gigabytes) and no Cloudflare halt. The one page missing is Указ № 883 от 1974 г. за прилагане на Закона за нормативните актове: lex.bg answers its address with a server error („Unauthorized … Error retrieving document!"), on two tries; its corpus file was never from lex.bg (its source field says strategy.bg), so it stays an act outside the lex.bg path.

## Results per act

Exceptions are counted after each round; the residue is what round 2 left for a person. Source findings describe the page, not a label, and are never re-labelled. The diff is the staged file against the corpus file, in changed lines.

| Act | Blocks | Sections (calls) | Exceptions after round 0 → 1 → 2 | Residue | Source findings | Diff lines | State |
|---|---|---|---|---|---|---|---|
| Закон за обществения транспорт (ЗОТ; cases N1 and E8) | 572 | 17 | 0 | 0 | 2 on one omission: the heading „Допълнителна разпоредба" has no § 1 under it, and the first § of the act's own provisions is § 2 (the known lex.bg omission, now caught by its number and not only by the empty heading) | 39 | done |
| Конституция (case N3) | 615 | 15 | 5 → 0 | 0 | none | 12 | done |
| Закон за изплащане на задълженията, уговорени в злато (case N7) | 3 | 1 | 3 → 0 | 0 | none | 2 | done |
| Наредба № 04-14 от 2019 г. (case E7) | 554 | 9 | 29 → 9 → 0 | 0 | none | 20 | done; its round 1 was rerun on 22 October with the annex heading as context, which the night's tasks lacked |
| Закон за задълженията и договорите (ЗЗД, 1950; cases E1 and E2) | 932 | 26 | 101 → 22 → 5 | 5: the four articles Чл. 1001а to 1001г that a transitional § adds to another act with no quotation marks (the anchoring rule sends them to a person by design), and one heading line | 2 empty headings; 2 markup fragments („Чл. 5./span>", „Чл. 10./span>") in the page | 178 | done; the 95 low-confidence heading levels of the night were re-labelled through the ladder on 22 October and all came back with high confidence at the same levels, so decision 2 is a convention question and no longer a labelling one |
| Наредба № 1 от 2013 г. за запасите от нефт (case N4; five annex forms) | 663 | 14 | 1 → 0 | 0 | none | 1,696 | done |
| Правилник за организацията и дейността на Народното събрание (case E15, repealed act) | 767 | 19 | 22 → 1 → 1 | 1: the dashed separator before the adoption formula | none | 1,580 | done |
| Наредба № 5 от 1999 г. за записа на кадастралните планове (6,030 blocks, nearly all annex rows) | 6,030 | 79 | 3 → 0 | 0 | none | 158 | done |
| Наказателен кодекс (НК) | 2,996 | 78 | 55 → 19 → 13 | 13: the repeated heading of Раздел II of the terrorism chapter (2 blocks); the unnumbered „Особена разпоредба" headings inside chapters (4); the broken superscript of Чл. 278б¹; the original code's unnumbered closing line; four dotted elision lines; the number line of Раздел IX printed after its title | 1 broken superscript; 1 empty heading | 507 | done |
| Кодекс на труда (КТ) | 3,209 | 107 | 66 → 7 → 7 | 7: the repeated pre-amendment headings of Глава седемнадесета and its Раздел I (4 blocks); a title line before a repealed section; two publication lines in capitals under provisions headings | 1 markup fragment („Чл. 23а./span>") | 1,804 | done |
| Кодекс на търговското корабоплаване (КТК) | 2,445 | 87 | 25 → 9 → 3 | 3: the repeated pre-2017 heading of Глава пета (2 blocks); the original code's unnumbered closing line | 1 broken superscript (Чл. 88а¹) | 1,325 | done |
| Закон за данък върху добавената стойност (ЗДДС) | 4,328 | 119 | 51 → 6 → 6 | 6: three repeated superseded headings (Глава трета, Глава осемнадесета, Раздел IV), two blocks each | none | 1,265 | done |
| Граждански процесуален кодекс (ГПК) | 3,818 | 131 | 31 → 9 → 9 | 9: repeated superseded headings of two sections and a chapter of the European-cooperation part, a repeated chapter number line, a repeated „Допълнителни разпоредби" line | 20 markup fragments; 1 item head without its space („8.Член 708") | 2,351 | done |
| Данъчно-осигурителен процесуален кодекс (ДОПК) | 5,559 | 158 | 106 → 6 → 6 | 6: repeated superseded headings of three sections and a subsection, two blocks each | 33 broken superscripts and fragments (Чл. 142я¹ to 142я¹⁰, Чл. 143я¹ to 143я¹³, Чл. 22 to 26 of a quoted act); 1 item head without its space („2.В чл. 20:"); 4 empty headings | 2,055 | done |
| Търговски закон (ТЗ) | 5,267 | 184 | 58 → 20 → 19 | 19: repeated headings of eight sections (17 blocks), two publication lines under provisions headings | 2 broken superscripts (Чл. 260и¹, Чл. 260ъ¹); 2 empty headings | 3,110 | done |
| Кодекс за социално осигуряване (КСО) | 6,343 | 192 | 29 → 6 → 1 | 1: the second item 38 of § 1 of the additional provisions | 15 broken superscripts (Чл. 4а¹, 121д¹, 123г¹, 123е¹ and ², 123з¹ to ³, 123и¹ to ³, 229г¹ to ³, 251а¹) | 1,997 | done |

Across the ten acts of 22 October (40,762 blocks, 1,154 sections), round 0 left 446 exceptions, round 1 left 83, and round 2 left 65 blocks for a person. Of the 65, 46 are one pattern, the repeated heading described below; the rest are low-confidence labels the model got right (the elision lines, the unnumbered closing lines, the publication lines) and the two items 38 of КСО.

## The residue, in words

- **A heading printed twice.** Where an amending act changed a chapter's or section's title, lex.bg prints the heading twice: the current title with its „Загл. изм." note, then the superseded title, or the same title again in another case. The model labelled the second copy a drop (a line that is not the act) or an editorial note; the fixed-form rule refuses a drop between placed blocks, so the pair reaches the residue every time. Seven of the ten acts have it (46 blocks); the ТЗ pages of the 2023 variable-capital company chapter have it on every section. It is one decision for the owner (below), not 54.
- **Low-confidence labels that are right.** The dotted elision line lex.bg prints where an amending act's other paragraphs are left out (НК, four times); the original code's unnumbered closing line („Изпълнението на настоящия кодекс се възлага на …", НК and КТК); publication lines in capitals under a provisions heading (КТ, ТЗ); the unnumbered „Особена разпоредба" headings that НК uses inside its chapters. The labels stand; the model marked them low because the vocabulary has no word for them.
- **The two items 38 of КСО.** Two amending acts of 2023 (ДВ бр. 84 and бр. 85) each inserted an item 38 into § 1 of the additional provisions, so the act has two items with that number, one after the other. The corpus file carries both. The order check cannot tell this from a labelling slip, so it is in the residue; the page is right.

## Source findings, in words

Every source finding is a fact about the lex.bg page, found by a fixed-form check and recorded, never re-labelled:

- **Broken superscripts.** Where an article number carries a superscript (Чл. 88а¹, Чл. 143я¹³), lex.bg's page has lost the markup and prints „Чл. 88а.SUP>1." („SUP>" is the remnant of the page's superscript tag). The corpus files have the same broken text, copied from the same pages. There are 52 such article heads in six acts (ДОПК 28, КСО 15, ТЗ 2, one each in НК and КТК, and the night's two in ЗЗД). The staged files keep the text as the page has it. The article number in the structure map is the right one (88а1), so the address is right even where the text is not.
- **Leaked span fragments.** Twenty-five article heads print „Чл. 3./span>." (ГПК 20, ДОПК 5, КТ 1): a closing tag of lex.bg's markup left in the text. The corpus has them too.
- **Item heads without their space.** „8.Член 708 се изменя така:" (ГПК) and „2.В чл. 20:" (ДОПК): the page lost the space after the item number. The check reads the number and records the malformed head.
- **Empty headings.** A heading with nothing under it before the next heading. All but one are the repeated-heading pattern above seen from the other side (the first copy is empty because the second follows at once); the one of ЗОТ is the missing § 1.
- **A missing § 1 in ЗОТ**, as in the night: „Допълнителна разпоредба" is followed by nothing, and the act's own provisions start at § 2.
- **Duplicated item numbers** in the act itself (КСО, above).

## What the diffs show

Every diff of the night was read line by line; the ten diffs of the day were sampled by kind with a script and read where the kind was new. They fall into these kinds, none of them a wording change by the pipeline:

1. **The corpus holds lex.bg chrome.** The corpus files of nine acts end with the „Релевантни актове от Европейското законодателство" list of EU regulations, which is lex.bg navigation. The pipeline drops it. This is defect class FR-036 of the future-requirements register (site chrome in act bodies), found again on every act that has the list.
2. **The corpus has lost the paragraph topology of an act.** The corpus files of the codes hold an article's title, its head, its alineas and its items on one line („Социален диалог Чл. 2. (Нов - …) (1) … (2) …"); the staged file has one line per provision, as the page has. This is the defect that decision D-058 names. It is the bulk of the diff of every code (lines over 600 characters: КСО 81, ДОПК 37, КТ 31, ЗДДС 30, ТЗ 28), and it alone makes 1,696 diff lines for Наредба № 1 and most of the 1,580 of the Правилник. Headings on one line with the space lost after the number („Глава първа.ОБЩИ ПОЛОЖЕНИЯ") are the same defect (Наредба № 1, the Правилник).
3. **The corpus is older than the page.** Three codes carry amendments on the page that the corpus does not have: ДОПК up to ДВ бр. 85 от 2026 г. (corpus to бр. 69), ГПК to бр. 92 (corpus to бр. 55), КТ to бр. 89 (corpus to бр. 69). Their corpus files say they were last updated on 31 July and 16 June 2026. The staged files carry the new text; one repeal note of ДОПК is in it. Наредба № 1's corpus file says the act is repealed in its frontmatter but its body lacks the repeal note of May 2026 that the page carries.
4. **A heading stored as plain text or at the wrong level.** ЗОТ's „Допълнителна разпоредба" is plain text in the corpus; the Constitution's title is a level-3 heading in the corpus and a level-1 heading in the staged file.
5. **A corpus wording defect.** Наредба № 04-14's issuing line reads „министъра наздравеопазването" in the corpus (a space lost at an inline element boundary by the old parser); the staged file has „на здравеопазването", copied from the source.
6. **Formatting conventions that differ and need the owner's word.** The § provisions are bold in the staged files (the current convention) and plain in older corpus files (ДОПК 89, КСО 138, КТ 80, ЗДДС 71, ТЗ 65, НК 67, ГПК 37 lines); „Член единствен." and „Параграф единствен." are bold like every other article and § opener, where the corpus has them plain; annex headings on two lines are joined into one heading line; ЗЗД's pre-1974 structure is rendered at four heading levels where the corpus had all of them at level 3.

## What the day found about the pipeline itself

The ten acts brought seven forms the fixed-form rules did not yet know. Each got a rule, a test (23 tests now cover the package) and a line in the model's instructions where the vocabulary needed it:

- doubled and tripled sub-letters under a letter (аа), бб), ааа); ЗДДС and ДОПК § 1);
- article superscripts of two digits (Чл. 143я¹³), and the broken form „SUP>13" the page prints;
- lex.bg's dotted elision line, after which a list may resume at any number;
- a chapter quoted in full inside an amending §, whose first line holds a quotation inside the quotation („Глава трета „а""), and an amending line that itself opens the quotation it leaves open („… се заменят със „съотношение, както следва:");
- a numbered sub-list under an item that ends with a colon (item 41 of КСО's definitions has items 1 and 2 under it, then item 42 follows);
- an item head without its space, recorded as a source finding rather than a label error;
- the correspondence-table link lex.bg prints under the title of ГПК, a known chrome line.

Before these rules, round 0 of ЗДДС and ДОПК showed 46 and 54 exceptions that were the checks' own, not the model's; after them, the two acts' round 0 held only low-confidence labels. No rule was added for the repeated heading: it is a reading of the source, and the owner decides it.

## Cost

On the lean agent, a round-0 call of eight sections used 48,000 to 105,000 tokens of plan usage, most between 55,000 and 68,000. That is about 7,500 per section. A single-section call used 19,800, so about 17,000 of every call is the agent's fixed context (the instructions, the agent definition and the tool calls) and 5,000 to 6,000 is the section itself. A re-label call of ten tasks used about 31,000, which is 3,100 per task. The night's general-purpose subagent used about 70,000 per section at one section per call, and about 28,000 at three per call. The ten acts of the day took about 150 calls and about 7.5 million tokens of plan usage; the two reruns of the night's acts took 17 calls more. On the night's driver they would have taken about 80 million.

## Decisions for the owner

1. **The repeated heading.** lex.bg prints a superseded chapter or section title a second time after the current one (46 blocks in seven acts). There are three ways to treat it. The staged file keeps both copies as headings, faithful to the page, as the corpus is today. Or it keeps the current one and drops the repeat, which is what the model proposed; the rule would then allow this one drop. Or it keeps the repeat as an editorial note under the current heading. Until this is decided, every act with the pattern ends in the residue.
2. **Heading levels for pre-1974 acts** (ЗЗД and its kind): accept the four-level rendering the model proposed, or keep one level as the corpus has. The model holds its levels with high confidence after the ladder; the question is the corpus convention, not the labels.
3. **§ provisions bold** in every act (the current convention), **„Член единствен." bold** like „Чл. N.", and **two-line annex headings joined**: confirm these as the corpus convention, or say otherwise.
4. **The corpus defects found** (chrome kept, lost paragraph topology in every code, three codes behind the page by up to four Gazette issues, headings as plain text, a lost space, a missing repeal note): they are corrected by the staged files; they enter the corpus only through step 4's gate and your merge.
5. **The broken superscripts and span fragments** (77 article heads): the staged files keep the page's broken text. Say whether step 4 may repair the text form („Чл. 88а¹.") from the structure map's number, or whether the Gazette text decides it.
6. **The review loop.** Four clean-context reviews on Opus closed every blocking and major finding in the night; the ten acts' real results were the check of 22 October and found only fixed-form gaps, none a lost or mis-addressed line. Say whether a fifth round on a different model is still wanted before step 4.

## What is left of the test set

Nothing. All sixteen acts are through the ladder; the lister of unanswered tasks prints none in any round. What remains is the residue named above and the owner's decisions.

## Glossary

- **Structure map**: the list of labels the model returns, one per block of a page's text, saying what each block is (heading, article, paragraph, item, annex row, chrome); the model writes no text.
- **Block**: one line of the page's text as the deterministic splitter cuts it; every character of the act lands in exactly one block.
- **Section (calls)**: a run of up to 60 blocks sent to the model in one task; a call carries several tasks.
- **Exception**: a block that a mechanical check rejected or that the model labelled with low confidence; the ladder re-labels it with its neighbours in up to two rounds; what remains is the residue for a person.
- **Source finding**: a check result that describes the page, not a label (a heading with nothing under it, a broken superscript), recorded and never re-labelled.
- **Staged file**: the Markdown the pipeline assembled from the blocks, kept outside the corpus.
- **Lean agent**: the project agent `labeller` defined in the repository, which can only read and write files; every labelling call of 22 October went through it (owner fact of 22 October 2026).
- **D-069**: the decision of 21 October 2026 in the repository's decision log that adopted this way of reading.
- **FR-036**: the registered defect class "lex.bg site chrome inside an act body".
- **D-058**: the decision in the repository's decision log that the Markdown must keep an act's paragraph topology (one line per alinea and item).
- **Cases N1 to N8 and E1 to E16**: the rows of the test-set document (References).
- **lex.bg**: the private consolidated-law site the corpus was photographed from; its pages are the raw source of this run.
- **ДВ бр. N от YYYY г.**: an issue of the State Gazette (Държавен вестник), the way amendments are cited.

## References

- The test set: `docs/testing/2026-10-22-structure-map-test-set.md` in this repository, 21 October 2026.
- The plan of record: `docs/plans/2026-10-21-reasoning-driven-corpus.md`, step 3.
- The owner facts of 21 and 22 October 2026 in `.claude/CLAUDE.md` (model runs on the owner's plans; the lean project agent).

## Provenance

Run folder: `data/runs/structure-map-2026-10-22/<act>/` (untracked). **Stopping and resuming the labelling run:** every section's answer is its own file under `maps/round<R>/`, written as soon as the agent finishes it; `reading/groups.py <slugs> --per 8` lists the sections without an answer in groups of eight per call, twenty groups at a time (`--round 1 --per 10` for a later round). To stop, launch no further batch; to resume, run the listing and dispatch what it prints (the dispatch prompt is `data/runs/structure-map-2026-10-22/TASK-PROMPT.txt`). Then `reading/run.py collect --slug <act> --round <R>`, which writes the next round's tasks or the residue. Raw fetch log: `data/runs/raw-fetch-lexbg-2026-10-21.log`; raw store `data/raw/lexbg/` (ignored by git until the owner decides where it lives). Summary table: `.venv/bin/python reading/summary.py --md`. Code: `reading/` and `scripts/raw_fetch_lexbg.py` on branch `plan/2026-10-21-reasoning-driven-corpus`; the rules of 22 October are the commits of that day on the branch.
