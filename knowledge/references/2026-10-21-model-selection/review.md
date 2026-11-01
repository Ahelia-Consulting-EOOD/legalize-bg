---
type: Run Review
title: "Review of 2026-10-21-model-selection"
generated: { by: claude-code/claude-opus-5-5 (reviewer) and claude-code/claude-fable-5-1 (dispositions), at: "2026-10-21T05:20:00+03:00" }
---

# Review of 2026-10-21-model-selection

Reviewer: a clean-context agent on Claude Opus 5.5, given the run folder, the hub, the concept, the root index, the log and the pre-run look-up, and nothing else. Base compared against: the merge-base with `origin/main`, `10df0ca5d906`, which holds no `knowledge/` folder, so the diff is the whole bundle. The reviewer reported 32 findings; the session fixed every one and re-ran the checks. Dispositions below, grouped by the reviewer's questions.

## Question 1: sourcing, tables, data

1. Extract#24 began "None" and the report quoted batch limits no extract held. Fixed: the extract is taken from the copy by exact substring; the report cites it.
2. Extracts #11 to #13 have no copy (a PDF). Accepted as the skill allows: the reason `pdf` is logged and the extracts were taken from the PDF read with the Read tool.
3. The "Used in section" column did not match the report. Fixed for every row against the rewritten report.
4. No search row explained how U2 and U6 to U10 were found. Fixed: row W9 records that they were opened from links on U1 and the Claude API reference, not found by search.
5. "18 models", "908 pairs" and "fine-tuned small model generating the whole amended article" lay outside the cited extracts. Fixed: extracts #33, #34 and #35 added; the French method is described in the source's words ("light quantized generative model, finetuned with LoRA … amended texts").
6. "690 Finnish statutes", "every residual divergence was a finding", the list of countries, Spain "the largest" and "built from the BOE API" had no extract. Fixed: extracts #36 to #39 added; "the largest" removed.
7. "The only controlled study". Fixed: "the study the search found", and the French study is named beside it.
8. "Wrong about half the time". Fixed: the report and the hub state the figures as the study gives them (50.3 percent single-step, 20.51 percent multi-step, 2.36 to 75.93 by code, 78 percent trivial corrections, one model, GPT-4.1-mini), and "not an exact match" is no longer called "wrong".
9. Two inferences stood as findings in section 3. Fixed: section 3 now points to Reasoning items 1 and 2, which carry them and say they are the run's.
10. "Every source says the same three things". Fixed: "The sources that bear on each point agree", with the point-by-point attribution.
11. The 850 and 2,200 comparison figures were underived. Fixed: Reasoning item 7 derives 864 and 2,184 from the stated token figures and extract#15.
12. Extract#8 (abstention) applied to Haiku 5.5. Fixed: Reasoning item 4 says it concerns Sonnet 4 and Opus 4 and is not applied.
13. Citations described as character offsets. Fixed, and this was the one finding that changed the design: extracts #42 to #44 added; plain-text documents are cited by sentence, custom content blocks by block index; the design now sends the splitter's blocks as custom content blocks and checks re-assembly over block indices.
14. Fable 5.1 prices not in the cited extracts. Fixed: extract#40 added and cited.
15. Backfill row did not follow (400 million input). Fixed: 32,117 materials at about 5,300 tokens is about 170 million; the row is 22 dollars list, 11 in batch; output volumes are stated as assumptions with their ratios.
16. Counts 69, 35, 32,117 and "two of 151" unsourced. Fixed: 32,117 is extract#41 (the coverage-map README); the others are the session's measurements, now listed in Reasoning item 5 with their files.
17. The under-100,000-token claim did not hold for whole materials. Fixed: materials are read block by block too (attribution from the title and opening blocks, instructions one block at a time), so the threshold holds by construction; the table's unit for those rows is "block".

## Question 2: the concept against the run

18. "The failure that consolidation studies measured" with a chain footnote. Fixed: the sentence now cites the similarity and exact-match extract and the generated-output extract, says "the one measured study", and carries the inference footnote for the re-emission reading.
19. "Distractors degrade every model", an inference under an extract footnote, "text first" unfootnoted. Fixed: "the models tested"; the neighbouring-provisions claim carries an inference footnote; "text first, question last" cites extract#1.
20. "Fivefold" footnoted to an extract with no figure. Fixed: the prices are stated and footnoted to extract#15.

## Question 3: answering the question from the index, the hub and the concept

21. The hub never named a model. Fixed: the "Current answer" names the tiers and the escalation, with the Haiku extract and an inference footnote.
22. Undecoded terms. Fixed: the hub's opening paragraph defines the reasoning run and the session; the concept has a Terms section covering leg, catch-up, backfill, daily loop, tag-stripped source, block, NLLP, Chroma and Legalize; the Gazette is named in Bulgarian and English in both. The reviewer's own answer from the three files agreed with the run's description.

## Question 4: the topic and the look-up

23. The saved look-up was made after the bundle existed. Fixed: `look-up.txt` now holds the listing made before the run, recorded from the session transcript, with a note saying so.
24. The log named the wrong marked files. Fixed: the log names the two marked source logs (I1 and I4) and says where each report is used or not.
25. I4 was dismissed unexamined. Fixed: I4 was read (source log row D4, outcome negative with the reason: it inventories Bulgarian official sources and says nothing about how a reader processes text) and the log says so.
26. The hub credited I2 with a "witness-not-truth model". Fixed: the hub and the log both say the Finland numbers.
27. "No country consolidates" overstated extract#28. Fixed: "no Legalize country self-consolidates from a raw amendment stream" wherever it appears.
Disputes: none among the sources; the reviewer noted that the only reversal is of the session's own earlier whole-act proposal, now derived in Reasoning item 7.

## Question 5: confidence words and inference footnotes

28. "Strong" on one Chroma study of older models. Fixed: "moderate", and the generation of the models is stated.
29. "Strong" on one study of one model. Fixed: "moderate", with the figures as given.
30. Inference halves under extract footnotes. Fixed: every "Current answer" bullet is split into its sourced part and its inference part, each with its own footnote kind.
31. "Production consolidators" generalised from one jurisdiction. Fixed: "The United Kingdom's state consolidator".
32. The cost inference had no Reasoning item. Fixed: Reasoning item 7 states and derives it; the hub's cost bullet points there and stays "weak".

Open findings: 0
