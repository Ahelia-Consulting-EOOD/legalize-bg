Corpus: 3,616 act pages with an act (7 pages of site chrome only), 2,538,140 blocks, 47,156 sections, 399,658,027 bytes of text; 8,475 bytes of text per section against 9,008 in the test set (scale 0.94).

## Derived constants

- Lean agent's fixed context: median 14,470 tokens over the lean run's 166 calls; this session's lean call 16,686 tokens for 42,230 characters (2.53 characters per token).
- Instruction files and memory index: 72% of the lean agent's startup characters, so the fixed context without them is 4,068 tokens.
- The first-principles hook: 4,644 characters, about 1,835 tokens per call; over 5,894 round-0 calls about 11 million.
- Task text rate: 3.44 bytes per token (56 reads); the instructions file 5,426 bytes, about 1,578 tokens.
- Per section: task in form C 2,888 tokens, answer in form B 698 tokens (step 3).
- Of the lean agent's first request, 12% (2,042 tokens: the system prompt and the tool schemas) was read from a sibling call's warm cache; the instruction files, the hook and the git status were written on every call. Without the instruction files the per-call written part is 2,026 tokens. With the labelling instructions moved into the agent's system prompt, the shareable part becomes 3,620 tokens.
- The recommended round-0 call: 34,341 tokens counted once, 64,944 cost-weighted, 3 API requests; the lean driver as measured 61,414 and 164,462.
- The recommended ladder call: 25 tasks of 499 tokens, 19,632 counted once, 29,759 cost-weighted.

## Round 0 over the whole corpus

| Driver | Calls | Tokens per section (context once) | Total, context once | Tokens per section, cost-weighted | Total, cost-weighted | Basis |
|---|---|---|---|---|---|---|
| Current driver: general-purpose subagent, 3 sections per call | 15,719 | 27,277 | 1,286 million | 40,287 | 1,900 million | 84 calls of the night of 21 to 22 October |
| Lean driver as measured: labeller, 8 sections per call, one Read and one Write per task | 5,894 | 7,223 | 341 million | 19,342 | 912 million | 96 calls of the lean run |
| Recommended: labeller without instruction files, instructions in its system prompt, 8 sections per call file, one compact answer file, 3 requests per call | 5,894 | 4,039 | 190 million | 7,638 | 360 million | derived above |

## Round 0: the four token classes per call, dollars at list price, duration

| Driver | Uncached input | Cache write, 5-minute | Cache write, 1-hour | Cache read | Output | Dollars per call | Cents per section | Dollars over the corpus | Duration per call, seconds |
|---|---|---|---|---|---|---|---|---|---|
| Current: general-purpose, 3 sections per call (84 calls measured) | 10 | 54,410 | 0 | 332,488 | 4,822 | 0.514 | 16.1 | 7,599 | 68 |
| Lean as measured: labeller, 8 sections per call (96 calls measured) | 20 | 61,912 | 0 | 347,324 | 9,440 | 0.658 | 7.7 | 3,648 | 89 |
| Recommended, five-minute cache, warm system part (a sibling call ran within five minutes) | 0 | 25,614 | 0 | 43,908 | 5,707 | 0.260 | 3.1 | 1,441 | about 89 (assumed as measured) |
| Recommended, five-minute cache, cold (first call of a batch, or after a gap over five minutes) | 0 | 29,234 | 0 | 40,288 | 5,707 | 0.276 | 3.3 | 1,533 | about 89 (assumed as measured) |
| Rejected: one-hour cache lifetime, warm (every write at twice the price) | 0 | 0 | 25,614 | 43,908 | 5,707 | 0.388 | 4.6 | 2,151 | about 89 (assumed as measured) |

Wall time of round 0 at 8 calls in flight: 5,894 calls of about 89 seconds, about 18 hours. Calls launched back to back keep the five-minute subagent cache warm by themselves. The warm prefix saves only the system part (2,042 tokens per call), 1.7 cents per call: the difference between the first two recommended rows. A one-hour lifetime would double the price of every write to save that, 12.8 cents more per call, so the five-minute default stays.

## The ladder over the whole corpus (rounds 1 and 2)

Round-1 targets at 1.5% of blocks: 38,072; round-2 targets at 19% of those: 7,234.

| Driver | Tasks per call | Calls | Tokens per task (context once) | Total, context once | Tokens per task, cost-weighted | Total, cost-weighted |
|---|---|---|---|---|---|---|
| Lean as measured | 10 | 4,531 | 3,178 | 144 million | 8,142 | 369 million |
| Recommended | 25 | 1,812 | 785 | 36 million | 1,190 | 54 million |

Ladder dollars at list price: lean as measured 1,475 (3.3 cents per re-label, 37 seconds per call of 10); recommended 216 (0.5 cents per re-label).

## What the first batch of the real run measures (no separate measurement run: the owner's word of 21 October 2026)

- The fixed context of the labeller without the instruction files, read from the first call's usage record; expected 4,068 tokens.
- Whether the labeller inside a workflow carries the same fixed context, read from the first workflow agent's record.
- Whether sixteen sections per call hold as eight do: the first batch runs 6 of its calls at sixteen sections (63,036 tokens counted once each, 0.50 dollars at list price) and reads the exception rate by position; these calls label acts the audit needs anyway, so nothing is spent on measurement alone.

## Assumptions

- The recommended call makes three API requests: the dispatch prompt names the call file and the answer file; the agent reads the call file (eight sections as tab-separated lines) and writes the answer file; then it replies with one line. The labelling instructions live in the agent's system prompt, so a sibling call that ran within the cache lifetime reads them and the tool schemas from the cache; the git status and the call file's content are written once each; the last request re-reads everything once. The tasks do not travel in the dispatch prompt itself, because the parent session would then carry them in its own context at its own price.
- The recommended call's duration is assumed equal to the lean call's measured median; it makes fewer requests but one long output.
- Exception rates are the lean run's at 8 sections per call over the sixteen test-set acts, which include the hardest cases on purpose; the corpus at large is expected at or below them.
- The reads of what survives round 2 are decided per batch and not estimated.
- Thinking tokens are counted in the output of the measured rows; the estimate assumes the same share.
