# Step 1: what a call is made of (measured 21 October 2026, this session)

Four subagent calls on the same kind of task, usage read from each call's API records (one line per request, de-duplicated by message id) by `scripts/step1_usage.py`, which writes `usage.csv` and `composition.csv`. The task files are in `tasks/`, the answers in `answers/`.

| Call | Agent | Model the call ran on | Task | API requests | Fixed context (first request's new tokens) | Content added by the task (later requests' new tokens) | Output tokens | Harness figure for the call |
|---|---|---|---|---|---|---|---|---|
| gp-tiny | general-purpose, no model parameter | claude-fable-5-1 (inherited from this session) | 3 blocks, 518 bytes | 3 | 65,773 | 5,065 | 513 | 70,933 |
| lean-tiny | labeller | claude-opus-5-5 | 3 blocks, 518 bytes | 3 | 16,686 | 2,656 | 510 | 19,472 |
| lean-empty | labeller | claude-opus-5-5 | 1 block, 135 bytes | 3 | 16,850 | 2,492 | 588 | 19,407 |
| lean-known | labeller | claude-opus-5-5 | 42 blocks, 8,136 bytes | 3 | 16,682 | 7,409 | 1,761 | 24,214 |

The content added by a task includes the instructions file (4,504 bytes, read once in every call) and the tool-result framing. The known task minus the empty task: 4,917 tokens of content for 8,001 more bytes of task file and 42 more answer entries.

## What the lean agent's fixed context holds (from its first request, in characters)

| Part | Characters | Share | Can it go? |
|---|---|---|---|
| The owner's global instruction file (`~/.claude/CLAUDE.md`) | 22,073 | 52% | yes: `omitClaudeMd: true` in the agent's definition (Claude Code 2.1.271 and later; installed 2.1.306) |
| The project's instruction file (`.claude/CLAUDE.md`) | 7,574 | 18% | yes, the same field |
| The memory index (`MEMORY.md`) | 709 | 2% | yes, the same field |
| The first principles and the work line, from the SubagentStart hook | 4,644 | 11% | only by the owner: the hook carries the owner's rule that the principles reach every subagent |
| Tool schemas: Read, Write, SubagentHandback, advisor | 3,718 | 9% | no: Read and Write are the task; the other two are the harness's |
| The agent's own system prompt and the harness's lines around it | 1,624 | 4% | no |
| The git status snapshot | 1,547 | 4% | no: only the built-in Explore and Plan agents skip it |
| The hand-back reminder | 341 | 1% | no |
| Total | 42,230 | 100% | 72% can go |

The figures are printed by `scripts/step1_usage.py` into `composition.csv` (and the per-request usage into `usage.csv`). The general-purpose agent's startup context was 195,552 characters: tool schemas of 44 tools 100,042, the skills listing 28,869, the deferred tool names 21,039, the agent listing 5,242, the same instruction files and hook.

The agent's own report when asked what it could see: the project instruction file, the memory index, tool definitions beyond Read and Write, the first principles, the git status; no skills listing.

## The sibling cache

The night's general-purpose calls wrote a median 39,518 tokens to the cache for a 72,043-token context: the rest of the fixed prefix was read from the cache that an earlier sibling call had warmed. The lean run's 8-section calls wrote all 61,932 tokens: its calls were launched eight at a time, all missing the cache together, with gaps longer than the five-minute subagent cache lifetime between batches. A warm prefix costs a tenth of a written one.

## Sources

`requests.md` and `requests.csv` (per-request sums of 411 calls of the two labelling sessions, matched to their dispatches); the four transcripts of this session's calls (scratchpad, not kept); the Claude Code documentation pages on subagents, costs and prompt caching, fetched on 21 October 2026.
