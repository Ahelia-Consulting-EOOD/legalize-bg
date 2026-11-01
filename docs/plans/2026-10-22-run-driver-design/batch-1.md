# Batch 1 of the audit: 34 acts through the adopted run driver

Who this is for: the owner, who decides when this batch starts, and the session that runs it. Written 21 October 2026 on the owner's word ("plan the work for the list, just not start it yet"). Nothing here has run.

## What the batch is

The first batch of the real run under decision D-070: the labeller agent of this branch, one call file of eight sections per call, one compact answer file per call, the ladder at twenty-five re-labels per call. It labels 34 acts the owner chose: the public procurement, normative acts and spatial planning laws, six codes not yet labelled, and 25 laws of public administration, taxes, property, energy, environment and transport. The list with each act's size is `batch-1-acts.json` beside this file (1,798 sections, 67,251 blocks). Two acts the owner named, the transport law and the commercial law, were labelled in the test set and are not repeated; so was the VAT law.

## What it costs, from the measured figures

| Part | Calls | Tokens counted once | Dollars at list price | Wall time at 8 calls in flight |
|---|---|---|---|---|
| Round 0 | about 225 | about 7.7 million | about 58 | about 50 minutes |
| Rounds 1 and 2, at 1.5 percent of blocks excepted | about 40 | about 0.8 million | about 11 | about 10 minutes |
| Six calls of round 0 at sixteen sections instead of eight (the drift measurement) | included above | about 0.2 million more | about 1 | |

The dollar figures compare designs and are not the plan's metering. The batch reads its own usage records to measure what the study could not: the fixed context of the labeller without its instruction files, the labeller's context inside a workflow, the drift by position at sixteen sections, and the four token classes, cache use and duration per call.

## What must be true before it starts

1. The session runs on this branch (or on the plan branch after pull request 48 is merged into it): the new labeller definition lives here. The main checkout still holds the old one.
2. The session is new: an agent definition loads at session start.
3. The oversight pull request 136 is merged, or the owner accepts that every call still carries the first principles (about 1,800 tokens each, about 400,000 over the batch).
4. The raw store of 21 October is reachable from the session's folder (`data/raw/lexbg/`; in a worktree, a link to the main checkout's folder).

## The steps the session runs

1. `prepare` for every act of the list (the splitter: blocks, sections, round-0 task files; refuses a page without an act).
2. `dispatch SLUGS --round 0 --json --max 16`, then the workflow script `batch-1.workflow.js` with that list as its arguments; six of the first calls with `--per 16` for the drift measurement, the rest at eight; repeat until dispatch lists nothing.
3. `collect --round 0` per act: the map, the staged text, the checks, the exceptions, the round-1 tasks, the call defects.
4. Rounds 1 and 2 the same way with `--per 25`.
5. Measurement: export the session's transcript and run the study's scripts (`request_sums.py`, `cache_timing.py`) on it; read the fixed context of the first labeller call and of the first workflow agent; compare the exception rate by position of the sixteen-section calls with the eight-section ones.
6. Results: one row per act (blocks, exceptions per round, residue, source findings, diff lines), the act's profile fields (type, form, exceptions, residue), and the measured cost per section against the plan's estimate. The residue goes to the owner.

## The goal line for that session

```
/goal Batch 1 of the structure-map audit (docs/plans/2026-10-22-run-driver-design/batch-1.md): done when every act of batch-1-acts.json has a map, a staged text and a report through round 2, the results table and the profile fields are written, and the measured tokens per section (four classes), cache use, duration and the sixteen-section drift are printed beside the plan's estimate. Budget: about 265 labeller calls, about 9 million tokens counted once; stop and report if a round's call defects exceed 5 percent of its calls or the tokens pass 12 million. Non-goals: no corpus write, no API key, no change to the vocabulary or the checks, no reopening of D-069 or D-070.
```

## Where state lives

The run folder `data/runs/structure-map-2026-10-22/<act>/` (untracked): blocks, tasks, call files, answer files, sidecars, maps, staged text, reports. The results document and the profile fields in `docs/testing/`. Nothing in the corpus folders.
