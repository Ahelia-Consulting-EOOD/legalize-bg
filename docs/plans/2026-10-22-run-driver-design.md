# The run driver: the design for legalize-bg's model runs and its cost per section

Who this is for: the repository owner, who pays for every model call of legalize-bg through Claude subscription plans, adopted the reading architecture on 21 October 2026 and objected on 22 October to a run that spent about 18 million tokens on fixed context. Read on screen; the decisions are in section 10.

## 1. The decision this document asks for

Adopt one run driver for every model run of the corpus. The runs it will drive are plan step 6 itself, the audit of every act in the corpus (plan step 7), the reading of the State Gazette's materials (plan steps 5 and 9) and the daily update loop (plan step 8). The driver is the lean [labeller](#glossary) agent started without the instruction files, with its cache kept warm for an hour. Each call carries eight [sections](#glossary) of an act inside the prompt in a tab-separated form and writes one compact answer file. Each [ladder](#glossary) call handles twenty-five re-labels. On the test set, a labelled section cost 28,990 tokens under the first driver (the general-purpose agent) and 7,676 under the lean driver as it ran; under this design it costs about 4,100 tokens counted once, scaled to the corpus's sections. Weighted at list price per API request, the same three figures are 40,300, 19,300 and about 7,400. Over the whole corpus that is 192 million tokens counted once instead of 1,286 million, in 5,894 calls instead of 15,719. What the model judges and what the checks test do not change.

The measurements that support this are in sections 4 to 9, each with the file that holds its raw figures. Section 10 lists the owner's decisions in one batch. Nothing in this document reopens decision D-069 (the model returns only a structure map, a script assembles and checks), the choice of Claude Opus 5.5, the lean agent rule, the rejected lister route, or the ladder of two rounds.

## 2. The owner's words, read back

The owner approved this read-back before the first measurement. Each item names its source.

1. "You should have been much more diligent in the run design re token optimization." The study measures before it runs. Every step names its cost first and prints its evidence. No run of the driver starts without a per-section token figure in its goal line. (Owner, 22 October 2026.)
2. "Why not combine the batches, as for a few sentences batch we stuff few k tokens system part of a prompt, this is very inefficient." The study measures the system part of a call (section 4), and the right number of sections per call for labelling (section 5) and for the ladder's re-labels (section 7), against the exception rate. (Owner, 22 October 2026.)
3. "This agent stays as a rule for future runs." The lean agent is the baseline of every design compared here; it is not itself under study. (Owner, 22 October 2026; owner fact of 22 October in the project's instruction file.)
4. "This is a total failure of the application of the first principles." The design is checked against the principles as a whole before the first call. The owner decides every spend. Every figure is measured and printed. The alternatives are compared on one measured number, tokens per labelled section. Every encoding or density chosen is cheap to change. (Owner, 22 October 2026.)
5. "Do not just record the failure, run a complete design session, well planned." This document is that session's plan of record. (Owner, 22 October 2026.)
6. A general-purpose subagent call carried about 65,000 tokens of fixed context for 3,000 to 8,000 tokens of section content; about 260 calls and about 18 million tokens before the owner objected. (Evidence: the follow-up record of 22 October 2026 and the results document of the test set.)
7. Measured plan usage from the task notifications: 69,000 to 97,000 tokens per general-purpose call at one to three sections; 102,000 to 122,000 at eight; round-1 calls 73,000 to 82,000. (Evidence: the figures relayed by the session that started this study; section 5 confirms them from the transcripts and attributes the eight-section figure to the general-purpose agent.)
8. The model returns only a structure map; a script assembles and checks; the ladder re-labels excepted blocks with their neighbours for two rounds. The study changes none of these roles. (Evidence: decision D-069 and section 5 of the plan of record of 21 October 2026.)
9. The owner rejected, on 21 October 2026, a [lister route](#glossary): a script that would assign labels from the lex.bg classes alone in place of the model's judgement. The lex.bg classes are counted in section 8 as evidence only. (Evidence: the plan of record's read-back, item 2, and the brief of this study.)
10. Every answer is a file. A run stops when no further batch is launched, and it resumes when the script that lists the tasks still without an answer is run again. Every alternative in section 9 is judged against this. (Evidence: the description at the head of that listing script.)
11. My addition: the token counts of the encodings in section 6 come from rates fitted on the lean run's own API records, bytes per token of what the model read and wrote, because no token counter is available without an API key. The fit and its error are printed.
12. My addition: sections 5 to 8 and the corpus count of section 9 needed no model call. They run on the test set's run data and on the raw store, reading only.
13. My addition: the study labelled no new act. The sixteen acts of the test set are its only labelled data.
14. My addition: the code changes come only after the owner's go on the recommendation, with tests, and a reviewer on a different model from this session's.

## 3. The goal contract and what the study spent

**Objective.** A plan of record for the run driver that gives, for each design, measured tokens per labelled section and its reliability, and one recommendation, so that every later run starts at a cost per section the owner has seen and agreed.

**Done-condition.** The [reader gate](#glossary) prints `items: N, judged: N` on this document, meaning that every place it flagged has been read and judged. A fresh agent's cold read names the decision and no unknown term. Every figure in the tables is printed by a script in the measurement folder. The full-corpus table gives tokens and calls for the current, the lean and the recommended driver. A draft pull request against the plan branch is open.

**Non-goals.** No change to D-069's roles. No API key. No corpus write. No reopening of what the owner decided. No labelling beyond the test set. No code before the owner's go.

**Spent so far.** Four subagent calls for the measurements, 134,000 tokens by the harness's count (the budget line was 250,000), and one call for the cold read, 52,527 tokens (the budget line was 100,000). Every other figure came from the two labelling sessions' exported transcripts (411 calls matched to their dispatches), the run data and the raw store. Not yet spent: the workflow measurement of section 9 (two calls, about 60,000), waiting for the owner's go. This session's own usage is not metered by the harness; it is estimated at 1.5 million tokens.

## 4. What a call is made of

**Cost of this step:** four calls, 134,000 tokens, approved by the owner before they ran. **Evidence:** the step 1 files of the measurement folder (Provenance): the fixed-context note and the per-request sums.

A general-purpose call starts with 65,771 tokens before it reads anything; a lean call with 16,680. Two thirds of the lean agent's fixed context is the owner's global instruction file, the project's instruction file and the memory index: 30,988 of about 46,300 characters. A custom agent loads them by default. The `omitClaudeMd` field of its definition removes them (Claude Code 2.1.271 and later; 2.1.306 is installed). The first principles and the work line, injected by the SubagentStart hook, are 16 percent; they reach every subagent by the owner's rule, so only the owner can exempt the labeller (decision 2 in section 10). The rest, about 8,000 characters, cannot go: the tool schemas of Read and Write and the two the harness adds, the agent's own prompt, the git status snapshot that every custom agent receives, and the harness's reminders.

The harness's figure per call counts the context once. What a call sends is larger: every batch of tool calls is one API request, and every request re-reads the whole context so far. A lean call of eight sections makes ten to eleven requests and re-reads 347,000 tokens from the cache for 62,000 written and 9,400 of output. Weighted at the Claude Opus 5.5 list prices relative to one uncached input token (a cache write 1.25, a cache read 0.1, an output token 5), such a call costs 164,000 token-equivalents, 20,600 per section, against 7,676 counted once. The plan's own metering is not published, so both figures are carried through this document.

Two more facts shape the design. First, output is the dear part: the 9,400 output tokens of a call weigh as much as 47,000 input tokens. Second, a sibling call can read the fixed prefix that an earlier call warmed. The night's general-purpose calls wrote only 39,500 of their 72,000 tokens. The lean run's calls wrote all of theirs: they were launched eight at a time, with gaps longer than the five-minute subagent cache lifetime between batches. The agent definition can request a one-hour cache lifetime (`experimental.cacheTtl`), and the first call of a batch can be launched alone to warm it.

One caution on the measurement: the general-purpose call of this step ran on Fable 5.1, this session's model, because the dispatch did not name a model; the night's general-purpose calls named Opus, and the lean agent's definition names Opus. The fixed context's size does not depend on the model.

## 5. Sections per call against reliability

**Cost of this step:** no model call. **Evidence:** the step 2 files: the density tables, the calls table (435 calls) and the sections table (1,236 sections).

| Agent and sections per call | Calls | Sections | Tokens per call, counted once (median) | Tokens per section | Exceptions per 100 blocks |
|---|---|---|---|---|---|
| General-purpose, 1 (night) | 84 | 84 | 72,318 | 72,318 | 4.2 |
| General-purpose, 3 (night) | 83 | 252 | 86,972 | 28,990 | 0.7 |
| General-purpose, 8 (night) | 14 | 102 | 107,630 | 13,453 | 1.8 |
| Lean, 8 (22 October) | 96 | 768 | 61,414 | 7,676 | 0.9 |

The exception rate is the round-0 count of label exceptions (low confidence, answer defects, check failures) over the blocks of those sections. It differs by act far more than by density: 0.0 per 100 blocks on the transport law, 10.8 on the 1950 obligations act. The night and the day labelled different acts, so the rows are not a clean comparison of densities. The clean measure is the position within a call, which holds the act constant:

| Agent, 8 sections per call | Position 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 |
|---|---|---|---|---|---|---|---|---|
| Lean, 96 calls, exceptions per 100 blocks | 1.1 | 0.7 | 1.0 | 0.6 | 1.0 | 0.9 | 0.9 | 1.1 |
| General-purpose, 14 calls | 0.0 | 1.1 | 1.8 | 1.8 | 1.8 | 2.1 | 2.8 | 3.7 |

At eight sections per call (about 290 blocks and 25,000 tokens of task text) the lean agent shows no drift from the first section to the last. The general-purpose agent, with 65,000 tokens of fixed context ahead of the same content, shows a rise, on fourteen calls only. Answer defects (a missing or malformed entry) were 0.01 per 100 blocks in the lean run. So eight sections per call is still safe. Where the limit lies is unknown, because no call carried more. The smallest measurement that can is six lean calls of sixteen sections each over acts already labelled, with the new labels compared against the existing maps and the exception rate read by position. It costs about 360,000 tokens counted once under the recommended encoding (decision 3 in section 10).

## 6. The size of the task and the answer

**Cost of this step:** no model call. **Evidence:** the step 3 files: the encoding tables and the calibration records.

The rates were fitted on the lean run's own records. A task file read with the Read tool cost 366 tokens plus one token per 3.44 bytes of the rendered text (56 reads, median error 114 tokens). A written answer cost 118 tokens plus one per 2.12 bytes (143 writes, median error 49 tokens). The rendered text of a Read carries a line number on every line, and the current task file has one line per field.

| Task (input) per section, 1,236 sections | Bytes | Tokens | Share |
|---|---|---|---|
| A. Current: indented JSON file, read with the Read tool | 12,967 | 4,135 | 100% |
| B. Compact JSON, one line per block, keys i, h, t, inline in the prompt | 10,591 | 3,079 | 82% |
| C. Tab-separated lines, index, hint, text, inline in the prompt | 9,936 | 2,888 | 77% |

| Answer (output) per section | Bytes | Tokens | Share |
|---|---|---|---|
| A. Current: i, label, n, conf, note on every entry | 2,429 | 1,264 | 100% |
| B. Compact: i and label always; n only on numbered labels; conf and note only on low confidence, drop and unknown | 1,230 | 698 | 51% |

Nothing the checks read is lost: the block indices, the hints, the verbatim text, every label, every number where the label is numbered, every low-confidence mark with its note, and the reason on every drop and unknown. What encoding B of the answer leaves out is 5,149 notes on high-confidence entries, such as "opens with (1) on the same line", which no check reads. The bytes removed are keys, indentation and line numbers, which the tokenizer packs less densely than Bulgarian text, so the token share saved is at least the byte share.

What changes in the code. The driver writes tasks in form C and assembles the dispatch prompt with the instructions and the tasks inline. The collect step reads one answer file per call, splits it per task and accepts the short keys. The ladder's task builder uses the same form. The validator maps the short keys to the long ones before validating. The label vocabulary, the numbering grammar and every check stay as they are.

## 7. The ladder's calls

**Cost of this step:** no model call. **Evidence:** the step 4 files: the ladder tables and the round-1 targets (579 targets).

A round-1 task is one target block with its two neighbours, the headings before it, the exceptions raised on it and the labels its neighbours carry: 1,511 bytes median. Over 65 lean calls of rounds 1 and 2, tokens per call fit 19,392 plus 1,240 per task, so a re-labelled block costs 3,178 tokens at ten tasks per call, 2,210 at twenty and 1,886 at thirty, counted once; cost-weighted, 8,142 at ten. Position within a call of ten made no difference: 14 to 23 percent of targets were still excepted after round 1 at every position (19 percent over all 579). Twenty-five tasks per call, delivered inline in form C with compact answers, holds the prompt at about 13,500 tokens, inside the range round 0 has already proved at eight sections, and brings a re-label to about 800 tokens counted once and 1,100 cost-weighted.

## 8. The lex.bg classes as evidence

**Cost of this step:** no model call. **Evidence:** the step 5 files: the agreement note and the crosstab.

Over the 44,101 blocks with a final label, the model's label lies in the family the lex.bg class names in 85.1 percent. By class: 99.2 percent for Title (the act's title and every heading), 99.5 percent for the class of the final provisions, and 79.5 percent for Article, whose misses are annex rows (6,110 blocks) and site chrome (304). Only one class names a single label, the in-force line, and there the class matched in 16 of 17 blocks. For the other 44,084 blocks the class alone never names the label. Title does not say which heading level. Article does not say whether a line opens an article, a paragraph, an item or a letter, continues one, or is quoted text, and that is the whole judgement. This is reported as a measurement; the owner rejected the lister route on 21 October, and nothing here reopens it.

## 9. The alternatives in this harness, and the full-corpus estimate

**Cost of this step:** no model call so far. The workflow measurement, two calls of about 60,000 tokens together, waits for the go. **Evidence:** the step 7 files: the estimate and the block count of 3,623 pages; the Claude Code documentation on subagents, workflows and caching, fetched on 21 October 2026.

Four ways to drive a call exist here. Each is judged on tokens per section and on what it changes in stopping, resuming and reviewing.

1. **One subagent per section.** The night's driver, at 72,318 tokens per section. Every answer is a file. Nothing else recommends it.
2. **Several sections per subagent, each read and written as a file.** The lean run: 7,676 per section counted once, 20,600 weighted, because every read and write is a request that re-reads the context. Every answer a file; resumable by listing.
3. **One subagent that loops over a task list it reads itself, resumed between batches.** A resumed subagent reads the cache it warmed. But its context grows with every task, and every request re-reads all of it, so the re-read cost grows with the square of the tasks. Worse than 2 beyond a handful of tasks, and one long transcript instead of one file per call.
4. **The Workflow tool.** A script fans out agents deterministically and can name the labeller as the agent type. It holds the agents of a fan-out so that they read the first agent's warm prefix, runs under a concurrency cap, and resumes by run id with finished agents' results replayed from its journal. The script has no file access, so the answers are still written by the agent, and the run folder stays the record; the parent session receives one result per workflow instead of one per call. The cost per section is that of design 2 with the recommended encoding, less the fixed prefix write on all but the first call of a batch.

The recommended call, under 2 or 4, is the labeller without the instruction files (about 4,800 tokens of fixed context), the instructions and eight sections inline in form C (24,300 tokens), one compact answer file (5,600 tokens of output), and two API requests. That is about 34,700 tokens counted once and 62,700 weighted: 4,300 and 7,800 per section on the test set, whose sections are 6 percent longer than the corpus's, so 4,100 and 7,400 over the corpus. The evidence supports the call as designed under either dispatcher. The workflow is preferred for the audit's scale, subject to one measurement that the labeller inside a workflow carries the same fixed context, which is the two-call spend of decision 4.

The corpus holds 3,624 acts; the raw store holds 3,623 of their lex.bg pages (one act was never on lex.bg), and 7 of those pages are site chrome with no act on them. The 3,616 pages with an act, counted with the splitter, hold 2,538,140 blocks, 47,156 sections and 400 million bytes of text. A section holds 8,475 bytes of text against 9,008 in the test set, so per-section figures are scaled by 0.94.

| Driver, round 0 over the whole corpus | Calls | Tokens per section, counted once | Total, counted once | Tokens per section, weighted | Total, weighted |
|---|---|---|---|---|---|
| Current: general-purpose, 3 sections per call | 15,719 | 27,276 | 1,286 million | 40,286 | 1,900 million |
| Lean as measured: labeller, 8 sections, a read and a write per task | 5,894 | 7,222 | 341 million | 19,342 | 912 million |
| Recommended: labeller without instruction files, warm cache, 8 sections inline, one compact answer, 2 requests | 5,894 | 4,080 | 192 million | 7,368 | 347 million |

The ladder adds 45,300 re-labels, assuming 1.5 percent of blocks excepted in round 0 (the lean run's 0.9 per 100 blocks, raised for safety) and 19 percent of those surviving to round 2. Under the lean driver at ten per call that is 144 million tokens counted once; under the recommended design at twenty-five per call, 36 million (369 and 50 million weighted). The reads of what survives round 2 (a person or a stronger model reading the whole act) are decided per batch and not estimated. The assumptions are listed in full in the estimate file.

## 10. The owner's decisions

1. **The driver.** Adopt the recommended design for plan step 6 and every later run. That is the labeller with `omitClaudeMd: true` and a one-hour cache lifetime, sections and tasks inline in form C, one compact answer file per call in form B, eight sections per round-0 call, and twenty-five tasks per ladder call. Options: adopt it; keep the lean driver as measured, at 2.4 times the tokens; adopt it with a different density. Recommendation: adopt. On the go, the code changes land with tests and a fresh-context review on Opus 5.5.
2. **The first principles in labeller calls.** The hook adds about 2,000 tokens to every call, about 12 million over the audit's round 0. Options: keep (the owner's rule that the principles reach every subagent); exempt the labeller, which judges nothing the principles govern and reads only its task. Recommendation: exempt, recorded as the owner's exception for this agent; the rule stands for every other agent.
3. **Where the reliable range ends.** Six lean calls of sixteen sections over acts already labelled, about 360,000 tokens, to learn whether sixteen per call holds as eight does; if it does, round 0 of the audit halves its calls. Options: run it after the driver lands; stay at eight. Recommendation: run it.
4. **The workflow measurement.** Two labeller calls inside a workflow, about 60,000 tokens, to confirm the fixed context and the shared prefix before the audit's driver is built on the Workflow tool. Options: run it with the code changes; build on plain subagent dispatch and skip it. Recommendation: run it.
5. **The cold read of this document.** Done, on the owner's goal line. A fresh agent named the decision and the four smaller ones. It found two undefined terms (the reader gate, the lister), three inconsistencies in figures and dates, and five stilted sentences. All were fixed in this version. No decision left.

## Glossary

- **Block**: one line of a lex.bg act page as the splitter cuts it; every character of the act lands in exactly one block.
- **Section**: a run of up to 60 blocks that starts at a heading, the unit a labelling task covers; the corpus has 47,156.
- **Structure map**: the model's answer, one label per block (title, heading, article head, paragraph, item, annex row, chrome and so on); the model writes no text.
- **Labeller**: the project agent defined for labelling calls, with the Read and Write tools only, on Claude Opus 5.5; the owner's rule of 22 October 2026.
- **Fixed context**: what a call carries before it reads its task: the agent's prompt, the tool schemas, the instruction files, the hook output, the git status.
- **Counted once**: the harness's figure for a call, the context counted once plus the output, as the task notifications show it.
- **Cost-weighted**: every API request's tokens weighted at the Claude Opus 5.5 list prices relative to an uncached input token: a cache write 1.25, a cache read 0.1, an output token 5.
- **Exception**: a block whose label a check rejected or the model marked low confidence; the ladder re-labels it with its neighbours in up to two rounds; what remains is the residue.
- **Ladder**: the two re-labelling rounds of decision D-069; a round-1 task is one target block with its two neighbours. What is still excepted after round 2 is the residue, read whole-act by a person or a stronger model.
- **Lister route**: a design the owner rejected on 21 October 2026, in which a script assigns labels from the lex.bg classes alone instead of the model.
- **Reader gate**: the script of the self-contained-deliverable skill that indexes the places in a document a reader may stumble on (a bare number, a long sentence, an internal path) and passes once every item has a recorded verdict; it prints `items: N, judged: N`.
- **Fable 5.1**: Claude Fable 5.1, the model this study's session runs on; the labelling runs on Claude Opus 5.5.
- **Work line**: the owner's standing instruction that the first principles are applied to the plan and the deliverable as they are made, which the SubagentStart hook injects together with the principles.
- **Hint**: the lex.bg CSS class of a block's nearest classified ancestor (Title, Article, FinalEdictsArticle, PreHistory), given to the model as a hint and never as a verdict.
- **Form B, form C**: the compact encodings of section 6; B is compact JSON with short keys, C is tab-separated lines.
- **Workflow tool**: the harness's deterministic fan-out of subagents from a script, resumable by run id.
- **D-069**: the decision of 21 October 2026 in the repository's decision log that adopted the reading architecture.
- **Plan step 6**: the run driver step of the plan of record of 21 October 2026.

## References

- The plan of record: `docs/plans/2026-10-21-reasoning-driven-corpus.md`, 21 October 2026, section 5.
- The failure record: `docs/followups/2026-10-22-labelling-run-without-token-design.md`.
- The test set and its results: `docs/testing/2026-10-22-structure-map-test-set.md` and `docs/testing/2026-10-22-structure-map-results.md`.
- Claude Code documentation, fetched 21 October 2026: Subagents (what loads at startup, frontmatter fields `omitClaudeMd` and `experimental.cacheTtl`, model resolution), Costs (plan usage), Prompt caching (subagents and the cache, workflow fan-outs). Online at code.claude.com/docs.
- The Workflow authoring reference bundled with Claude Code (agent types, schema output, resume by run id, no file access from the script).

## Provenance

Measurement folder `docs/plans/2026-10-22-run-driver-design/`: `step1/` (the three task files, the four answers, `fixed-context.md`, `requests.md` and `requests.csv`), `step2/` (`calls.csv`, `tasks.csv`, `density.md`), `step3/` (`calibration.csv`, `encoding.md`), `step4/` (`ladder.md`, `round1_targets.csv`), `step5/` (`hints.md`, `crosstab.json`), `step7/` (`corpus_blocks.csv`, `corpus_blocks.log`, `estimate.md`), and `scripts/` with one script per figure. The calls table comes from `survey_transcript.py` and `calls_from_transcripts.py` over the two sessions' exported transcripts, which live in the owner's Downloads folder and are not kept in the repository. The other figures come from `request_sums.py`, `calibrate_tokens.py`, `density.py`, `encoding.py`, `ladder_density.py`, `hint_agreement.py`, `corpus_blocks.py` and `estimate.py`. The run data is `data/runs/structure-map-2026-10-22/` in the main checkout (untracked, read-only for this study); the raw store is `data/raw/lexbg/`. The four measurement calls of section 4 ran in this session on 21 October 2026 between 11:30 and 11:35 Sofia time by this machine's clock. The test-set documents date the lean labelling run and the owner's words 22 October 2026; by the clock that run also fell on 21 October, a few hours before this study. This document keeps the documents' dates for the owner's words and the file names, and the clock's date for its own calls.
