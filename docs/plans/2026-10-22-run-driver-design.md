# The run driver: the design for legalize-bg's model runs and its cost per section

Who this is for: the repository owner, who pays for every model call of legalize-bg through Claude subscription plans, adopted the reading architecture on 21 October 2026 and objected on 22 October to a run that spent about 18 million tokens on fixed context. Read on screen; the decisions are in section 10.

## 1. The decision this document asks for

Adopt one run driver for every model run of the corpus. The runs it will drive are plan step 6 itself, the audit of every act in the corpus (plan step 7), the reading of the State Gazette's materials (plan steps 5 and 9) and the daily update loop (plan step 8). The driver is the lean [labeller](#glossary) agent started without the instruction files, on the default five-minute cache. Each call reads one call file holding eight [sections](#glossary) of an act as tab-separated lines and writes one compact answer file; the labelling instructions live in the agent's own prompt. Each [ladder](#glossary) call handles twenty-five re-labels. On the test set, counted once, a labelled section cost 28,990 tokens under the first driver (the general-purpose agent at three sections per call, the night run's settled form). It cost 7,676 under the lean driver as it ran on the day run. Under this design it costs about 4,300. Weighted at list price per API request, the same three figures are 42,800, 20,600 and about 8,100. In dollars at the Claude Opus 5.5 list prices, which compare the designs and are not the plan's metering, a section costs 16.1 cents, 7.7 cents and 3.1 cents. The corpus's sections are 6 percent shorter than the test set's, so over the whole corpus the design costs about 4,000 per section counted once. That is 190 million tokens instead of 1,286 million, in 5,894 calls instead of 15,719. At list price it is about 1,440 dollars instead of 7,600, and it takes about 18 hours of wall time at eight calls in flight. What the model judges and what the checks test do not change.

The measurements that support this are in sections 4 to 10, each with the file that holds its raw figures. Section 11 lists the owner's decisions in one batch. Nothing in this document reopens decision D-069 (the model returns only a structure map, a script assembles and checks), the choice of Claude Opus 5.5, the lean agent rule, the rejected lister route, or the ladder of two rounds.

## 2. The owner's words, read back

The owner approved this read-back before the first measurement. Each item names its source.

1. "You should have been much more diligent in the run design re token optimization." The study measures before it runs. Every step names its cost first and prints its evidence. No run of the driver starts without a per-section token figure in its goal line. (Owner, 22 October 2026.)
2. "Why not combine the batches, as for a few sentences batch we stuff few k tokens system part of a prompt, this is very inefficient." The study measures the system part of a call (section 4), and the right number of sections per call for labelling (section 5) and for the ladder's re-labels (section 7), against the exception rate. (Owner, 22 October 2026.)
3. "This agent stays as a rule for future runs." The lean agent is the baseline of every design compared here; it is not itself under study. (Owner, 22 October 2026; owner fact of 22 October in the project's instruction file.)
4. "This is a total failure of the application of the first principles." The design is checked against the principles as a whole before the first call. The owner decides every spend. Every figure is measured and printed. The alternatives are compared on one measured number, tokens per labelled section. Every encoding or density chosen is cheap to change. (Owner, 22 October 2026.)
5. "Do not just record the failure, run a complete design session, well planned." This document is that session's plan of record. (Owner, 22 October 2026.)
6. A general-purpose subagent call carried about 65,000 tokens of fixed context for 3,000 to 8,000 tokens of section content; about 260 calls and about 18 million tokens before the owner objected. (Evidence: the follow-up record of 22 October 2026 and the results document of the test set. The exported transcript of that session holds 245 general-purpose dispatches; the rest were calls of other kinds.)
7. Measured plan usage from the task notifications: 69,000 to 97,000 tokens per general-purpose call at one to three sections; 102,000 to 122,000 at eight; round-1 calls 73,000 to 82,000. (Evidence: the figures relayed by the session that started this study; section 5 confirms them from the transcripts and attributes the eight-section figure to the general-purpose agent.)
8. The model returns only a structure map; a script assembles and checks; the ladder re-labels excepted blocks with their neighbours for two rounds. The study changes none of these roles. (Evidence: decision D-069 and section 5 of the plan of record of 21 October 2026.)
9. The owner rejected, on 21 October 2026, a [lister route](#glossary): a script that would assign labels from the lex.bg classes alone in place of the model's judgement. The lex.bg classes are counted in section 8 as evidence only. (Evidence: the plan of record's read-back, item 2, and the brief of this study, the task the owner's session handed to this one.)
10. Every answer is a file. A run stops when no further batch is launched, and it resumes when the script that lists the tasks still without an answer is run again. Every alternative in section 10 is judged against this. (Evidence: the description at the head of that listing script.)
11. My addition: the token counts of the encodings in section 6 come from rates fitted on the lean run's own API records, bytes per token of what the model read and wrote, because no token counter is available without an API key. The fit and its error are printed.
12. My addition: sections 5 to 9 and the corpus count of section 10 needed no model call. They run on the test set's run data and on the raw store, reading only.
13. My addition: the study labelled no new act. The sixteen acts of the test set are its only labelled data.
14. My addition: the code changes come only after the owner's go on the recommendation, with tests, and a reviewer on a different model from this session's.
15. "We need to discriminate read versus write tokens, estimating time for the calls, which will lead to cache utilisation taken into account, as prices depend seriously on caching." Every cost in this document is given in the four token classes the API bills (uncached input, cache write, cache read, output), each at its list price. Every measured call carries its duration. The share of each call that was read from a warm cache is measured, not assumed (section 9). "Dollars and tokens by type, read, write, and cache hits by cache type": section 9 gives both, and says what the API does not report. (Owner, 21 October 2026, during this study.)
16. "I don't want measurement runs and wasted tokens; you estimate by previous runs' transcripts for the time being; we will measure when we start actual runs, before the full run." The two measurement spends this document proposed (sixteen sections per call; the labeller inside a workflow) are withdrawn. What they would have measured is read from the first batch of the real run, whose calls label acts the audit needs anyway, before the full run continues (section 10). The owner also asked whether the run that finished the test set's two open ladders on 21 October was measured: it was, its 17 calls are among the 65 ladder calls of section 7. (Owner, 21 October 2026, during this study.)

## 3. The goal contract and what the study spent

**Objective.** A plan of record for the run driver that gives, for each design, measured tokens per labelled section and its reliability, and one recommendation, so that every later run starts at a cost per section the owner has seen and agreed.

**Done-condition.** The [reader gate](#glossary) prints `items: N, judged: N` on this document, meaning that every place it flagged has been read and judged. A fresh agent's cold read names the decision and no unknown term. Every figure in the tables is printed by a script in the measurement folder. The full-corpus table gives tokens and calls for the current, the lean and the recommended driver. A draft pull request against the plan branch (the branch that holds the plan of record of 21 October) is open.

**Non-goals.** No change to D-069's roles. No API key. No corpus write. No reopening of what the owner decided. No labelling beyond the test set. No code before the owner's go.

**Spent so far.** Four subagent calls for the measurements, 134,000 tokens by the harness's count (the budget line was 250,000), and one call for the cold read, 52,527 tokens (the budget line was 100,000). Every other figure came from the two labelling sessions' exported transcripts (435 labelling dispatches, 411 of them with a usage figure), the run data and the raw store. No further model call is planned for the study: the owner said on 21 October that nothing is spent on measurement alone, and what remains to measure is read from the first batch of the real run. This session's own usage is not metered by the harness; it is estimated at 1.5 million tokens.

## 4. What a call is made of

**Cost of this step:** four calls, 134,000 tokens, approved by the owner before they ran. **Evidence:** the step 1 files of the measurement folder (Provenance): the fixed-context note and the per-request sums.

A general-purpose call starts with 65,773 tokens before it reads anything; a lean call with 16,686. Seventy-two percent of the lean agent's fixed context is the owner's global instruction file, the project's instruction file and the memory index: 30,356 of 42,230 characters. A custom agent loads them by default. The `omitClaudeMd` field of its definition removes them (Claude Code 2.1.271 and later; 2.1.306 is installed). The first principles and the work line, injected by the SubagentStart hook, are 11 percent; they reach every subagent by the owner's rule, so only the owner can exempt the labeller (decision 2 in section 11). The rest, about 7,200 characters, cannot go: the tool schemas of Read and Write and the two the harness adds, the agent's own prompt, the git status snapshot that every custom agent receives, and the harness's reminders.

The harness's figure per call counts the context once. What a call sends is larger: every batch of tool calls is one API request, and every request re-reads the whole context so far. A lean call of eight sections makes ten to eleven requests and re-reads 347,000 tokens from the cache for 62,000 written and 9,400 of output. Weighted at the Claude Opus 5.5 list prices relative to one uncached input token (a cache write 1.25, a cache read 0.1, an output token 5), such a call costs 164,000 token-equivalents, 20,600 per section, against 7,676 counted once. The plan's own metering is not published, so both figures are carried through this document.

Two more facts shape the design. First, output is the expensive part: the 9,400 output tokens of a call weigh as much as 47,000 input tokens. Second, a sibling call can read from the cache only the part of the prefix that is identical and ends at a cache breakpoint: the system prompt and the tool schemas. Section 9 measures it: 12 percent of a lean call's first request, 53 percent of a general-purpose one. The instruction files, the hook output and the git status sit in the first user message with the task, and are written anew on every call, warm cache or not. So the instruction files cost their full write price on every call until `omitClaudeMd` removes them. The agent definition could request a one-hour cache lifetime, but that doubles the price of every write to keep 2,000 tokens warm, so the five-minute default stays (section 9).

One caution on the measurement: the general-purpose call of this step ran on Fable 5.1, this session's model, because the dispatch did not name a model; the night's general-purpose calls named Opus, and the lean agent's definition names Opus. The fixed context's size does not depend on the model.

## 5. Sections per call against reliability

**Cost of this step:** no model call. **Evidence:** the step 2 files: the density tables, the calls table (435 dispatches, 411 with a usage figure) and the sections table (1,236 sections). The rows below show the groups large enough to compare; the smaller groups are in the files.

| Agent and sections per call | Calls | Sections | Tokens per call, counted once (median) | Tokens per section | Exceptions per 100 blocks |
|---|---|---|---|---|---|
| General-purpose, 1 (night) | 84 | 84 | 72,318 | 72,318 | 4.2 |
| General-purpose, 3 (night) | 83 | 252 | 86,972 | 28,990 | 0.7 |
| General-purpose, 8 (night) | 14 | 102 | 107,630 | 13,453 | 1.8 |
| Lean, 8 (22 October) | 96 | 768 | 61,414 | 7,676 | 0.9 |

The exception rate is the round-0 count of label exceptions (low confidence, answer defects, check failures) over the blocks of those sections. It differs by act far more than by density: 0.0 per 100 blocks on the transport law, 10.8 on the 1950 obligations act. The night run and the day run labelled different acts, so the rows are not a clean comparison of densities. The clean measure is the position within a call, which holds the act constant:

| Agent, 8 sections per call | Position 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 |
|---|---|---|---|---|---|---|---|---|
| Lean, 96 calls, exceptions per 100 blocks | 1.1 | 0.7 | 1.0 | 0.6 | 1.0 | 0.9 | 0.9 | 1.1 |
| General-purpose, 14 calls | 0.0 | 1.1 | 1.8 | 1.8 | 1.8 | 2.1 | 2.8 | 3.7 |

At eight sections per call (about 290 blocks and 25,000 tokens of task text) the lean agent shows no drift from the first section to the last. The general-purpose agent, with 65,000 tokens of fixed context ahead of the same content, shows a rise, on fourteen calls only. Answer defects (a missing or malformed entry) were 0.01 per 100 blocks in the lean run. So eight sections per call is still safe. Where the limit lies is unknown, because no call carried more. The first batch of the real run answers it without a separate spend: six of its calls run at sixteen sections, and the exception rate is read by position before the batch continues (read-back item 16).

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

What changed in the code, built on the owner's go of 21 October. A new `dispatch` command of the driver groups the tasks still without an answer into calls and writes one call file per call in form C. It prints the call file, the answer file and the one-line prompt for the labeller. So a run stops when no further call is launched, and resumes when the command is run again. The collect step splits each call's answer file into the per-task answer files the ladder reads, never overwriting a newer per-task answer, and accepts the short keys. The validator reads the short keys as the long ones. The labelling instructions moved into the labeller's own prompt, so sibling calls read them from the cache instead of each call reading the file; a test keeps the agent's body and the instructions file identical. The tasks do not travel inside the dispatch prompt: the parent session would then carry 25,000 tokens per call in its own context at its own price. The label vocabulary, the numbering grammar and every check are untouched.

## 7. The ladder's calls

**Cost of this step:** no model call. **Evidence:** the step 4 files: the ladder tables and the round-1 targets (579 targets).

A round-1 task is one target block with its two neighbours, the headings before it, the exceptions raised on it and the labels its neighbours carry: 1,511 bytes median. Over 65 lean calls of rounds 1 and 2, tokens per call fit 19,392 plus 1,240 per task. Among those calls are the 17 that took the two open ladders to the residue on 21 October: the 2019 certification ordinance's annex rows and the 1950 obligations act's heading levels. So a re-labelled block costs 3,178 tokens at ten tasks per call, 2,210 at twenty and 1,886 at thirty, counted once, and 8,142 cost-weighted at ten. Position within a call of ten made no difference: 14 to 23 percent of targets were still excepted after round 1 at every position (19 percent over all 579). Twenty-five tasks per call, delivered inline in form C with compact answers, holds the prompt at about 13,500 tokens, inside the range round 0 has already proved at eight sections. It brings a re-label to about 785 tokens counted once and 1,190 cost-weighted: half a cent at list price against 3.3 cents as measured.

## 8. The lex.bg classes as evidence

**Cost of this step:** no model call. **Evidence:** the step 5 files: the agreement note and the crosstab.

Over the 44,101 blocks with a final label, the model's label lies in the family the lex.bg class names in 85.1 percent. By class: 99.2 percent for Title (the act's title and every heading), 99.5 percent for the class of the final provisions, and 79.5 percent for Article, whose misses are annex rows (6,110 blocks) and site chrome (304). Only one class names a single label, the in-force line, and there the class matched in 16 of 17 blocks. For the other 44,084 blocks the class alone never names the label. Title does not say which heading level. Article does not say whether a line opens an article, a paragraph, an item or a letter, continues one, or is quoted text, and that is the whole judgement. This is reported as a measurement; the owner rejected the lister route on 21 October, and nothing here reopens it.

## 9. Read and write tokens, call durations and cache use

**Cost of this step:** no model call. **Evidence:** the step 8 files: the timing and cache tables and the per-call records (411 calls), from `cache_timing.py`; the four-class rows of the estimate file.

The API bills four kinds of token: uncached input (4 dollars per million on Claude Opus 5.5), tokens written to the prompt cache (5 for a five-minute entry, 10 for a one-hour entry), tokens read from it (0.40 whatever the entry's lifetime) and output (20). The weighted figures of this document use the five-minute ratios. The table gives the medians per call of the two measured drivers and three states of the recommended call; the dollar figures compare designs and are not the plan's metering, which is not published.

| Driver, round 0 | Uncached input | Cache write, 5-minute | Cache write, 1-hour | Cache read | Output | Dollars per call | Cents per section | Duration, seconds |
|---|---|---|---|---|---|---|---|---|
| Current: general-purpose, 3 sections per call (84 calls) | 10 | 54,410 | 0 | 332,488 | 4,822 | 0.514 | 16.1 | 68 |
| Lean as measured: labeller, 8 sections per call (96 calls) | 20 | 61,912 | 0 | 347,324 | 9,440 | 0.658 | 7.7 | 89 |
| Recommended, five-minute cache, warm system part | 0 | 25,614 | 0 | 43,908 | 5,707 | 0.260 | 3.1 | about 89 (assumed) |
| Recommended, five-minute cache, cold | 0 | 29,234 | 0 | 40,288 | 5,707 | 0.276 | 3.3 | about 89 (assumed) |
| Rejected: one-hour cache lifetime, warm | 0 | 0 | 25,614 | 43,908 | 5,707 | 0.388 | 4.6 | about 89 (assumed) |

Over all 411 measured calls of both runs: uncached input 4,837 tokens (0.02 dollars), five-minute cache writes 21,489,268 (107.45 dollars), one-hour cache writes 0, cache reads 121,620,310 (48.65 dollars), output 2,742,100 (54.84 dollars). Every cache write of both runs was a five-minute write, the subagent default. The API reports cache reads as one figure whatever the lifetime of the entry read, so hits cannot be split by cache type; the cache breakpoints of every request sit on the system blocks only.

Three things follow. First, in the lean call as it ran, cache reads are the largest class by count but the smallest by price: 347,000 reads cost 14 cents, the 62,000 writes 31 cents, the 9,400 output tokens 19 cents. Output and writes are where the money goes, and the recommended call halves the output and cuts the writes by more than half. Second, the warm cache is worth less than it looks. Of a lean call's first request, 12 percent (2,042 tokens, the system prompt and the tool schemas) was read from a sibling's cache; a general-purpose call shared 53 percent (its 38,000 tokens of tool schemas and listings). Everything after the system block, the instruction files, the hook, the git status and the task, is written on every call. In the recommended call the labelling instructions sit inside the system prompt, so they join the shared part; the difference between the warm and the cold rows is 1.7 cents. Third, timing. A lean call of eight sections takes 89 seconds, its first response arrives in 3 seconds, and the lean run launched its calls eight at a time with a median 1.2 minutes between batches and three gaps longer than the five-minute subagent cache lifetime. At eight calls in flight, round 0 over the corpus takes about 18 hours of wall time. Calls launched back to back keep the five-minute cache warm by themselves, and a first call launched a few seconds ahead of its batch lets the others read the system part, worth 1.7 cents per call. A one-hour lifetime would double the price of every write to keep that part warm across the pauses between batches: 12.8 cents more per call, so it is rejected and the five-minute default stays. The ladder's calls are shorter: 37 seconds for ten re-labels.

## 10. The alternatives in this harness, and the full-corpus estimate

**Cost of this step:** no model call. **Evidence:** the step 7 files: the estimate and the block count of 3,623 pages; the Claude Code documentation on subagents, workflows and caching, fetched on 21 October 2026.

Four ways to drive a call exist here. Each is judged on tokens per section and on what it changes in stopping, resuming and reviewing.

1. **One subagent per section.** How the night run began, at 72,318 tokens per section, before it settled on three sections per call. Every answer is a file. Nothing else recommends it.
2. **Several sections per subagent, each read and written as a file.** The lean run: 7,676 per section counted once, 20,600 weighted, because every read and write is a request that re-reads the context. Every answer a file; resumable by listing.
3. **One subagent that loops over a task list it reads itself, resumed between batches.** A resumed subagent reads the cache it warmed. But its context grows with every task, and every request re-reads all of it, so the re-read cost grows with the square of the tasks. It costs more than design 2 beyond a handful of tasks, and it leaves one long transcript instead of one file per call.
4. **The Workflow tool.** A script fans out agents deterministically and can name the labeller as the agent type. It holds the agents of a fan-out so that they read the first agent's warm prefix, runs under a concurrency cap, and resumes by run id with finished agents' results replayed from its journal. The script has no file access, so the answers are still written by the agent, and the run folder stays the record; the parent session receives one result per workflow instead of one per call. The cost per section is that of design 2 with the recommended encoding, less the fixed prefix write on all but the first call of a batch.

The recommended call, under 2 or 4, is the labeller without the instruction files (about 4,100 tokens of fixed context) and with the instructions in its own prompt (1,600 tokens, shared through the cache). It reads one call file of eight sections in form C (23,100 tokens) and writes one compact answer file (5,600 tokens of output). That is three API requests: the prompt naming the two files, the read of the call file with the write of the answer, and the one-line reply. That is about 34,300 tokens counted once and 64,900 weighted: 4,300 and 8,100 per section on the test set, whose sections are 6 percent longer than the corpus's, so 4,000 and 7,600 over the corpus. In dollars at list price, 26 cents per call and 3.1 cents per section. The evidence supports this call whether the session launches it directly or a workflow script does. The workflow is preferred for the audit's scale and for its fan-out hold, which lets the calls of a batch read the system part the first one cached. One thing is confirmed before building on it, from the usage record of the first workflow agent of the real run: that the labeller inside a workflow carries the same fixed context.

The corpus holds 3,624 acts; the raw store holds 3,623 of their lex.bg pages (one act was never on lex.bg), and 7 of those pages are site chrome with no act on them. The 3,616 pages with an act, counted with the splitter, hold 2,538,140 blocks, 47,156 sections and 400 million bytes of text. A section holds 8,475 bytes of text against 9,008 in the test set, so per-section figures are scaled by 0.94.

| Driver, round 0 over the whole corpus | Calls | Tokens per section, counted once | Total, counted once | Tokens per section, weighted | Total, weighted |
|---|---|---|---|---|---|
| Current: general-purpose, 3 sections per call | 15,719 | 27,277 | 1,286 million | 40,287 | 1,900 million |
| Lean as measured: labeller, 8 sections, a read and a write per task | 5,894 | 7,223 | 341 million | 19,342 | 912 million |
| Recommended: labeller without instruction files, instructions in its prompt, 8 sections per call file, one compact answer, 3 requests | 5,894 | 4,039 | 190 million | 7,638 | 360 million |

The ladder adds 45,300 re-labels, assuming 1.5 percent of blocks excepted in round 0 (the lean run's 0.9 per 100 blocks, raised for safety) and 19 percent of those surviving to round 2. Under the lean driver at ten per call that is 144 million tokens counted once; under the recommended design at twenty-five per call, 36 million (369 and 54 million weighted; 1,475 and 216 dollars at list price). The reads of what survives round 2 (a person or a stronger model reading the whole act) are decided per batch and not estimated. The assumptions are listed in full in the estimate file.

## 11. The owner's decisions

1. **The driver.** Adopt the recommended design for plan step 6 and every later run. That is the labeller with `omitClaudeMd: true` on the default five-minute cache and the instructions in its own prompt, one call file per call in form C, one compact answer file per call in form B, eight sections per round-0 call, and twenty-five tasks per ladder call. Adopted by the owner on 21 October 2026 and recorded in the decision log as D-070. The code is on this branch with its tests and a fresh-context review on Opus 5.5.
2. **The first principles in labeller calls.** The hook adds about 1,800 tokens to every call, about 11 million over the audit's round 0. Decided by the owner on 21 October 2026: the labeller type of agent is exempt. The hook change is proposed to the oversight repository as a pull request (an agent whose definition says `ahelia-principles: exempt` starts without the principles); the labeller's definition carries the marker. Every other agent keeps the principles.
6. **The owner's direction on act profiles, to confirm.** The owner said on 21 October: to save future tokens, label each act by its intrinsic organisation per type. For some clean acts, after the first model parse, scripts can parse cleanly, for lex.bg and for the Gazette. For the later runs, one per Gazette issue, the profiles say what to expect and whether reasoning, a script, or both parse safely. My reading has three parts. The audit's first model parse of every act is kept as that act's profile: its type from the frontmatter, its block count, its exception and residue counts, and the agreement between its map and a deterministic parse by the numbering grammar the checks already hold. The owner then selects per type, from those measured agreements, which path the Gazette runs take. For the daily loop the cheapest path of all is to carry forward the labels of unchanged blocks and send the model only the blocks an amendment touched. Evidence so far: on the test set the clean modern acts ran at 0.0 to 0.8 exceptions per 100 blocks (the transport law, the 1999 cadastre ordinance, the 2013 reserves ordinance, the Constitution, the social insurance code). The old or annex-heavy ones ran at 2.9 to 10.8 (the 1950 obligations act, the 2019 certification ordinance, the parliament's rules). The corpus is 77 percent ordinance blocks. This reopens nothing by itself: the audit runs as adopted, and the profile is one of its outputs. The owner confirms or corrects this reading; a decision follows.
3. **Where the reliable range ends.** Withdrawn on 21 October: the owner wants no measurement run. The first batch of the real run runs six of its calls at sixteen sections and reads the exception rate by position; if sixteen holds, the rest of round 0 halves its calls. No decision left.
4. **The workflow measurement.** Withdrawn on 21 October for the same reason. The first workflow agent of the real run shows in its usage record whether the labeller carries the same fixed context inside a workflow, before the batch continues. No decision left.
5. **The cold read of this document.** Done, under the owner's goal line (the instruction that set this study's done-condition and budget). A fresh agent named the decision and the four smaller ones. It found two undefined terms (the reader gate, the lister), three inconsistencies in figures and dates, and five stilted sentences. All were fixed in this version. No decision left.

## Glossary

- **Block**: one line of a lex.bg act page as the splitter cuts it; every character of the act lands in exactly one block.
- **Section**: a run of up to 60 blocks that starts at a heading, the unit a labelling task covers; the corpus has 47,156.
- **Structure map**: the model's answer, one label per block (title, heading, article head, paragraph, item, annex row, chrome and so on); the model writes no text.
- **Labeller**: the project agent defined for labelling calls, with the Read and Write tools only, on Claude Opus 5.5; the owner's rule of 22 October 2026.
- **Fixed context**: what a call carries before it reads its task: the agent's prompt, the tool schemas, the instruction files, the hook output, the git status.
- **Counted once**: the harness's figure for a call, the context counted once plus the output, as the task notifications show it.
- **Cost-weighted**: every API request's tokens weighted at the Claude Opus 5.5 list prices relative to an uncached input token: a cache write 1.25, a cache read 0.1, an output token 5.
- **Token classes**: the four kinds the API bills separately: uncached input, cache write (tokens stored in the prompt cache), cache read (tokens served from it) and output.
- **Warm prefix, cache lifetime**: a request reads from the cache the identical opening part of an earlier request, up to a cache breakpoint, while that cache is alive: five minutes for a subagent by default. A one-hour lifetime exists at twice the write price and is not used here.
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
- **D-070**: the decision of 21 October 2026 that adopted this document's run driver and exempted the labeller from the principles hook.
- **Plan step 6**: the run driver step of the plan of record of 21 October 2026.

## References

- The plan of record: `docs/plans/2026-10-21-reasoning-driven-corpus.md`, 21 October 2026, section 5.
- The failure record: `docs/followups/2026-10-22-labelling-run-without-token-design.md`.
- The test set and its results: `docs/testing/2026-10-22-structure-map-test-set.md` and `docs/testing/2026-10-22-structure-map-results.md`.
- Claude Code documentation, fetched 21 October 2026: Subagents (what loads at startup, frontmatter fields `omitClaudeMd` and `experimental.cacheTtl`, model resolution), Costs (plan usage), Prompt caching (subagents and the cache, workflow fan-outs). Online at code.claude.com/docs.
- The Workflow authoring reference bundled with Claude Code (agent types, schema output, resume by run id, no file access from the script).

## Provenance

Measurement folder `docs/plans/2026-10-22-run-driver-design/`. Its parts are one folder per step and a scripts folder. `step1/` holds the three task files, the four answers, `usage.csv`, `composition.csv` and `usage.md` from `step1_usage.py`, `fixed-context.md`, `requests.md` and `requests.csv`. `step2/` holds `calls.csv`, `tasks.csv` and `density.md`. `step3/` holds `calibration.csv`, `encoding.md` and `encoding.json`. `step4/` holds `ladder.md` and `round1_targets.csv`. `step5/` holds `hints.md` and `crosstab.json`. `step7/` holds `corpus_blocks.csv`, `corpus_blocks.log` and `estimate.md`. `step8/` holds `cache_timing.md` and `cache_timing.csv`. `scripts/` holds one script per figure. The calls table comes from `survey_transcript.py` and `calls_from_transcripts.py` over the two sessions' exported transcripts, which live in the owner's Downloads folder and are not kept in the repository. The other figures come from `step1_usage.py`, `request_sums.py`, `calibrate_tokens.py`, `density.py`, `encoding.py`, `ladder_density.py`, `hint_agreement.py`, `corpus_blocks.py`, `cache_timing.py` and `estimate.py`. The last derives every constant of sections 9 and 10 from the other files and prints the cost of the two proposed measurements. `check_plan_figures.py` reads every table of this document and confirms that each figure appears in one of those scripts' outputs. Its result on this version is in the pull request. The run data is `data/runs/structure-map-2026-10-22/` in the main checkout (untracked, read-only for this study); the raw store is `data/raw/lexbg/`. The four measurement calls of section 4 ran in this session on 21 October 2026 between 11:30 and 11:35 Sofia time by this machine's clock. The test-set documents date the lean labelling run and the owner's words 22 October 2026; by the clock that run also fell on 21 October, a few hours before this study. Here, the owner's words and the file names keep the date those documents gave them, 22 October; this study's own calls carry the clock's date, 21 October.
