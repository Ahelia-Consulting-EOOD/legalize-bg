Corpus: 3,616 act pages with an act (7 pages of site chrome only), 2,538,140 blocks, 47,156 sections, 399,658,027 bytes of text; 8,475 bytes of text per section against 9,008 in the test set (scale 0.94).

## Derived constants

- Lean agent's fixed context: median 14,470 tokens over the lean run's 166 calls; this session's lean call 16,686 tokens for 42,230 characters (2.53 characters per token).
- Instruction files and memory index: 72% of the lean agent's startup characters, so the fixed context without them is 4,068 tokens.
- The first-principles hook: 4,644 characters, about 1,835 tokens per call; over 5,894 round-0 calls about 11 million.
- Task text rate: 3.44 bytes per token (56 reads); the instructions file 4,895 bytes, about 1,424 tokens.
- Per section: task in form C 2,888 tokens, answer in form B 698 tokens (step 3).
- The recommended round-0 call: 34,187 tokens counted once, 62,801 cost-weighted, 2 API requests; the lean driver as measured 61,414 and 164,462.
- The recommended ladder call: 25 tasks of 499 tokens, 19,478 counted once, 27,616 cost-weighted.

## Round 0 over the whole corpus

| Driver | Calls | Tokens per section (context once) | Total, context once | Tokens per section, cost-weighted | Total, cost-weighted | Basis |
|---|---|---|---|---|---|---|
| Current driver: general-purpose subagent, 3 sections per call | 15,719 | 27,277 | 1,286 million | 40,287 | 1,900 million | 84 calls of the night of 21 to 22 October |
| Lean driver as measured: labeller, 8 sections per call, one Read and one Write per task | 5,894 | 7,223 | 341 million | 19,342 | 912 million | 96 calls of the lean run |
| Recommended: labeller without instruction files, warm cache, 8 sections inline, one compact answer file, 2 requests per call | 5,894 | 4,021 | 190 million | 7,386 | 348 million | derived above |

## The ladder over the whole corpus (rounds 1 and 2)

Round-1 targets at 1.5% of blocks: 38,072; round-2 targets at 19% of those: 7,234.

| Driver | Tasks per call | Calls | Tokens per task (context once) | Total, context once | Tokens per task, cost-weighted | Total, cost-weighted |
|---|---|---|---|---|---|---|
| Lean as measured | 10 | 4,531 | 3,178 | 144 million | 8,142 | 369 million |
| Recommended | 25 | 1,812 | 779 | 35 million | 1,105 | 50 million |

## The two proposed measurements

- Sixteen sections per call: 6 calls of 62,882 tokens counted once (122,491 cost-weighted), about 377,291 tokens in all.
- The labeller inside a workflow, on the tiny and the known task of step 1: 2 calls, about 40,355 tokens in all at the lean agent's measured fixed context.

## Assumptions

- The recommended call makes two API requests: the prompt (instructions and sections inline) and the one Write of the answer file, then the one-line reply; the fixed prefix is read from the cache, not written, because the cache is kept warm for an hour and the first call of a batch warms it.
- Exception rates are the lean run's at 8 sections per call over the sixteen test-set acts, which include the hardest cases on purpose; the corpus at large is expected at or below them.
- The reads of what survives round 2 are decided per batch and not estimated.
- Thinking tokens are counted in the output of the measured rows; the estimate assumes the same share.
