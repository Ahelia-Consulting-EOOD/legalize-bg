Corpus: 3,616 act pages with an act (7 pages of site chrome only), 2,538,140 blocks, 47,156 sections, 399,658,027 bytes of text; 8,475 bytes of text per section against 9,008 in the test set (scale 0.94).

## Derived constants

- Lean agent's fixed context: median 14,470 tokens over the lean run's 166 calls; this session's lean call 16,686 tokens for 42,230 characters (2.53 characters per token).
- Instruction files and memory index: 72% of the lean agent's startup characters, so the fixed context without them is 4,068 tokens.
- The first-principles hook: 4,644 characters, about 1,835 tokens per call; over 5,894 round-0 calls about 11 million.
- Task text rate: 3.44 bytes per token (56 reads); the instructions file 4,895 bytes, about 1,424 tokens.
- Per section: task in form C 2,888 tokens, answer in form B 698 tokens (step 3).
- Of the lean agent's first request, 12% (2,042 tokens: the system prompt and the tool schemas) was read from a sibling call's warm cache; the instruction files, the hook and the git status were written on every call. Without the instruction files the per-call written part is 2,026 tokens.
- The recommended round-0 call: 34,187 tokens counted once, 65,281 cost-weighted, 2 API requests; the lean driver as measured 61,414 and 164,462.
- The recommended ladder call: 25 tasks of 499 tokens, 19,478 counted once, 30,096 cost-weighted.

## Round 0 over the whole corpus

| Driver | Calls | Tokens per section (context once) | Total, context once | Tokens per section, cost-weighted | Total, cost-weighted | Basis |
|---|---|---|---|---|---|---|
| Current driver: general-purpose subagent, 3 sections per call | 15,719 | 27,277 | 1,286 million | 40,287 | 1,900 million | 84 calls of the night of 21 to 22 October |
| Lean driver as measured: labeller, 8 sections per call, one Read and one Write per task | 5,894 | 7,223 | 341 million | 19,342 | 912 million | 96 calls of the lean run |
| Recommended: labeller without instruction files, warm cache, 8 sections inline, one compact answer file, 2 requests per call | 5,894 | 4,021 | 190 million | 7,678 | 362 million | derived above |

## Round 0: the four token classes per call, dollars at list price, duration

| Driver | Uncached input | Cache write | Cache read | Output | Dollars per call | Cents per section | Dollars over the corpus | Duration per call, seconds |
|---|---|---|---|---|---|---|---|---|
| Current: general-purpose, 3 sections per call (84 calls measured) | 10 | 54,410 | 332,488 | 4,822 | 0.514 | 16.1 | 7,599 | 68 |
| Lean as measured: labeller, 8 sections per call (96 calls measured) | 20 | 61,912 | 347,324 | 9,440 | 0.658 | 7.7 | 3,648 | 89 |
| Recommended, warm prefix (a sibling call warmed the system part within the cache lifetime) | 0 | 26,857 | 36,229 | 5,617 | 0.261 | 3.1 | 1,448 | about 89 (assumed as measured) |
| Recommended, cold prefix (first call of a batch, or after a gap longer than the cache lifetime) | 0 | 28,900 | 34,187 | 5,617 | 0.271 | 3.2 | 1,500 | about 89 (assumed as measured) |

Wall time of round 0 at 8 calls in flight: 5,894 calls of about 89 seconds, about 18 hours. Calls launched back to back keep the five-minute subagent cache warm; a one-hour cache lifetime in the agent definition keeps it warm across the collect steps between batches. The warm prefix saves only the system part (2,042 tokens per call): the difference between the two recommended rows.

## The ladder over the whole corpus (rounds 1 and 2)

Round-1 targets at 1.5% of blocks: 38,072; round-2 targets at 19% of those: 7,234.

| Driver | Tasks per call | Calls | Tokens per task (context once) | Total, context once | Tokens per task, cost-weighted | Total, cost-weighted |
|---|---|---|---|---|---|---|
| Lean as measured | 10 | 4,531 | 3,178 | 144 million | 8,142 | 369 million |
| Recommended | 25 | 1,812 | 779 | 35 million | 1,204 | 55 million |

Ladder dollars at list price: lean as measured 1,475 (3.3 cents per re-label, 37 seconds per call of 10); recommended 218 (0.5 cents per re-label).

## The two proposed measurements

- Sixteen sections per call: 6 calls of 62,882 tokens counted once (124,971 cost-weighted, 0.50 dollars at list price), about 377,291 tokens in all.
- The labeller inside a workflow, on the tiny and the known task of step 1: 2 calls, about 40,355 tokens in all at the lean agent's measured fixed context.

## Assumptions

- The recommended call makes two API requests: the prompt (instructions and sections inline) and the one Write of the answer file, then the one-line reply. Its system part is read from a sibling's cache when one has run within the cache lifetime; the hook, the git status and the prompt are written once; request 2 re-reads everything once.
- The recommended call's duration is assumed equal to the lean call's measured median; it makes fewer requests but one long output.
- Exception rates are the lean run's at 8 sections per call over the sixteen test-set acts, which include the hardest cases on purpose; the corpus at large is expected at or below them.
- The reads of what survives round 2 are decided per batch and not estimated.
- Thinking tokens are counted in the output of the measured rows; the estimate assumes the same share.
