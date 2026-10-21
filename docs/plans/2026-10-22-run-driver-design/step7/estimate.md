Corpus: 3,616 act pages with an act (7 pages of site chrome only), 2,538,140 blocks, 47,156 sections, 399,658,027 bytes of text; 8,475 bytes of text per section against 9,008 in the test set (scale 0.94).

## Round 0 over the whole corpus

| Driver | Calls | Tokens per section (context once) | Total, context once | Tokens per section, cost-weighted | Total, cost-weighted | Basis |
|---|---|---|---|---|---|---|
| Current driver: general-purpose subagent, 3 sections per call | 15,719 | 27,276 | 1,286 million | 40,286 | 1,900 million | 84 calls of the night of 21 to 22 October |
| Lean driver as measured: labeller, 8 sections per call, one Read and one Write per task | 5,894 | 7,222 | 341 million | 19,342 | 912 million | 96 calls of 22 October |
| Recommended: labeller without CLAUDE.md, warm cache, 8 sections inline, one compact answer file, 2 requests per call | 5,894 | 4,080 | 192 million | 7,368 | 347 million | estimate from the measured parts (step 1, step 3) |

## The ladder over the whole corpus (rounds 1 and 2)

Round-1 targets at 1.5% of blocks: 38,072; round-2 targets at 19% of those: 7,234.

| Driver | Tasks per call | Calls | Tokens per task (context once) | Total, context once | Tokens per task, cost-weighted | Total, cost-weighted |
|---|---|---|---|---|---|---|
| Lean as measured | 10 | 4,531 | 3,178 | 144 million | 8,142 | 369 million |
| Recommended | 25 | 1,812 | 799 | 36 million | 1,099 | 50 million |

## Assumptions

- The recommended call: fixed context 4,774 tokens (the lean agent's 14,469 less the 67% that the CLAUDE.md files and the memory index take), instructions 1,225, 8 sections of 2,888 tokens inline, answers 698 tokens per section, two API requests; the fixed prefix is read from the cache, not written, because the cache is kept warm for an hour and the first call of a batch warms it.
- Per call, the recommended design is 34,687 tokens counted once and 62,652 cost-weighted; the lean driver as measured is 61,414 and 164,461.
- The ladder's recommended call: 25 tasks of 499 tokens inline, 60 output tokens per task, two requests: 19,980 tokens counted once, 27,483 cost-weighted.
- Exception rates are the lean run's at 8 sections per call over the sixteen test-set acts, which include the hardest cases on purpose; the corpus at large is expected at or below them.
- The whole-act reads of the residue (what survives round 2) are not estimated: they are the owner's reads or a Fable read per act, decided per batch.
- Thinking tokens are counted in the output of the measured rows; the estimate assumes the same share.
