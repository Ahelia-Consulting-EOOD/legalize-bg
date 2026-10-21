```
Reader:        the repository owner, who pays for every model call of legalize-bg through Claude subscription plans, set the reading architecture on 21 October 2026 and objected on 22 October to a run that spent about 18 million tokens on fixed context
Already knows: the corpus, the plan of record of 21 October 2026 (decision D-069: a script splits, the model labels, a script assembles and checks, a bounded ladder re-labels exceptions), the lean project agent rule of 22 October, that tokens are money
Decision:      which run driver design legalize-bg adopts for step 6 of the plan, the audit of all 3,624 acts, the Gazette reading and the daily loop; and the owner's go at each spend of this study
Language:      English, written, read on screen; plain sentences; no internal ids without their words
Mode:          internal
Check:         python3 /Users/ekimir/swprj/my-claude-skills/plugins/global-workflow/skills/self-contained-deliverable/scripts/check_reader_ready.py --length-target 3500 docs/plans/2026-10-22-run-driver-design.md ; cold read by a fresh agent (decision named, no unknown term)
Length target: 3500 body words
```

# The run driver: how every token of a model run buys labelling

Status: draft, step 0 of the study. The read-back and the goal contract below await the owner's go. No model call has been made for this study.

## 1. The owner's words, read back

The study turns the owner's words of 22 October 2026 into a goal. Each item names its source: the owner's words, an extract of evidence already recorded, or "my addition".

1. "You should have been much more diligent in the run design re token optimization." The study measures before it runs: every step below names its cost first and prints its evidence, and no run of the driver starts without a per-section token figure in its goal line. (Owner, 22 October 2026.)
2. "Why not combine the batches, as for a few sentences batch we stuff few k tokens system part of a prompt, this is very inefficient." The study measures the system part of a call (step 1), and the right number of sections per call for labelling (step 2) and for the ladder's re-labels (step 4), against the exception rate, so that the density is chosen from evidence, not guessed. (Owner, 22 October 2026.)
3. "This agent stays as a rule for future runs." The lean project agent (Read and Write only, Opus) is the baseline of every design the study compares; it is not itself under study. (Owner, 22 October 2026; owner fact of 22 October in the project's instruction file.)
4. "This is a total failure of the application of the first principles." The study checks its own design against the principles as a whole before the first call: the owner decides every spend (the human owns the intent); every figure is measured and printed (evidence over assertion); the alternatives are compared on one measured number, tokens per labelled section, and nothing is built for a future the measurements do not reach (don't over-engineer); every encoding or density chosen is cheap to change (embrace uncertainty). (Owner, 22 October 2026.)
5. "Do not just record the failure, run a complete design session, well planned." This document is that session's plan of record; the failure record of 22 October stays as it is and is not rewritten here. (Owner, 22 October 2026.)
6. A general-purpose subagent call carried about 65,000 tokens of fixed context (the session's tool catalogue, system prompt and instruction files) for 3,000 to 8,000 tokens of section content; about 260 calls and about 18 million tokens before the owner objected. (Evidence: the follow-up record of 22 October 2026 and the results document of the test set.)
7. Measured plan usage from task notifications: 69,000 to 97,000 tokens per general-purpose call at one to three sections; 102,000 to 122,000 at eight sections; round-1 re-label calls (three blocks per task, six to ten tasks per call) 73,000 to 82,000. Whether the eight-section figure was measured on the general-purpose or the lean agent is not recorded; step 1 settles it. (Evidence: the figures relayed by the session that started this study, 22 October 2026.)
8. The model returns only a structure map (one label per block); a script assembles the Markdown and runs the checks; the ladder re-labels excepted blocks with their neighbours for two rounds. The study changes none of these roles. (Evidence: decision D-069 and section 5 of the plan of record of 21 October 2026.)
9. The owner rejected a route where a lister replaces the model's judgement, on 21 October 2026. The lex.bg CSS classes are counted in step 5 as evidence of agreement with the model, and nothing is proposed on them that changes the model's role. (Evidence: the owner's correction recorded in the plan of record's read-back, item 2, and the brief of this study.)
10. Every answer is a file, a run stops by not launching the next batch, and resumes by listing the tasks without an answer. Every alternative in step 6 is judged against this. (Evidence: the group lister's own description in `reading/groups.py`.)
11. My addition: the study counts the tokens of task and answer encodings (step 3) with a local estimate calibrated against the measured input of a labeller call with known content, because no token counter is available without an API key and the owner's rule forbids one. The calibration and its error are printed.
12. My addition: steps 3, 4, 5 and 7 need no model call; they run on the test-set data already labelled and on the raw store, read-only.
13. My addition: the study labels no new act. The sixteen test-set acts, labelled by the parallel run, are its only labelled data.
14. My addition: the code changes to the driver come only after the owner's go on the recommendation, with tests, and a reviewer on a different model from this session's.

## 2. The goal contract

**Objective.** A plan of record for the run driver that gives, for each design, measured tokens per labelled section and its reliability, and one recommendation, so that step 6 of the plan, the audit of 3,624 acts, the Gazette reading and the daily loop run at a cost per section the owner has seen and agreed.

**Done-condition, printed as evidence.**

- The reader gate prints `items: N, judged: N` on this document, and a fresh agent's cold read names the decision and no unknown term.
- Every figure in this document's tables is printed by a script under `docs/plans/2026-10-22-run-driver-design/`, re-runnable on the run data and the raw store, with its raw figures beside it.
- The full-corpus table (step 7) gives tokens and calls for the current driver, the lean driver as measured, and the recommended design, with every assumption written out.
- A draft pull request against the plan branch exists and its address is printed; nothing is merged.

**Non-goals.** No change to D-069's roles of script and model. No API key. No corpus write. No reopening of what the owner decided (the model Opus 5.5, the lean agent, the rejected lister route, the ladder of two rounds). No labelling of acts beyond the sixteen of the test set. No code change before the owner's go on the recommendation.

**Budget for the study's own model calls.** Tokens are the owner's plan usage. Each line is one spend the owner approves; a step that needs none says so.

| Step | Calls | Tokens, estimated | What each call is for |
|---|---|---|---|
| 1. What a call is made of | 4 | about 250,000 | one general-purpose call and one lean (labeller) call on the same tiny task, to read both totals from the task notifications; two more lean calls, one with an almost empty task and one with a known content size, to separate the fixed part from the content and calibrate the token estimate of item 11 |
| 2. Sections per call against reliability | 0 | 0 | the existing run data; if it cannot answer, the smallest measurement is proposed with its cost and waits for the go |
| 3. Task and answer encoding | 0 | 0 | scripts over the task and answer files |
| 4. The ladder's density | 0 | 0 | scripts over the round-1 and round-2 files and the figures of item 7 |
| 5. CSS hints as evidence | 0 | 0 | scripts over blocks and maps |
| 6. Alternatives in this harness | 2 | about 150,000 | one workflow of two lean agents on two tiny tasks, only if the authoring reference says a workflow agent can be the project agent; otherwise 0 calls and the reference is cited |
| 7. Full-corpus estimate | 0 | 0 | the splitter over the raw store, read-only |
| Cold read of this document | 1 | about 100,000 | a fresh agent reads the document and nothing else |
| Total before the owner's go on the recommendation | 7 | about 500,000 | |
| Code changes, after the go | up to 3 | about 450,000 | fresh-context reviews on Opus 5.5 (a different model from this session's); stop rule: a closing round with open majors filed, or majors not falling for two rounds, or the owner's ruling |

This session's own reading and writing (a Fable 5.1 session) is estimated at 1.5 to 2 million tokens over the study. Work past any line of this table waits for the owner's go.

**Where state lives.** This worktree and its branch; the plan document and the measurement folder under `docs/plans/`; the run data and the raw store are read in the main checkout and never written.

## 3. The proposed goal line

```
/goal Run-driver design study (docs/plans/2026-10-22-run-driver-design.md): done when the reader gate prints "items: N, judged: N" on the plan, a fresh agent's cold read names the decision, every figure in the plan's tables is printed by a script under docs/plans/2026-10-22-run-driver-design/, the full-corpus table gives tokens and calls for the current, the lean and the recommended driver, and a draft PR against plan/2026-10-21-reasoning-driven-corpus is open with its address printed. Budget: 7 model calls, about 500,000 tokens, before the owner's go on the recommendation, each step's calls approved by the owner first; after that go, code with tests and up to 3 review rounds on Opus 5.5 (about 450,000 tokens; stop at a closing round with open majors filed, majors not falling for two rounds, or the owner's ruling). Non-goals: D-069's roles, API keys, corpus writes, the owner's recorded decisions.
```

## 4. The study's steps

To be written as each step runs, with its cost named first and its evidence printed. Steps 1 to 7 are listed in the goal contract's budget table.

## Glossary

To be completed with the measurements.

## Provenance

To be completed with the measurements.
