## What a call really sends: API requests per call, by agent, round and sections per call

| Agent | Round | Tasks per call | Calls | Median requests per call | Harness figure (context once) | Written to cache | Re-read from cache | Output | Cost-weighted | Cost-weighted per task |
|---|---|---|---|---|---|---|---|---|---|---|
| labeller (lean) | 0 | 3 | 2 | 6 | 33,413 | 32,271 | 113,368 | 3,719 | 70,273 | 23,424 |
| labeller (lean) | 0 | 7 | 2 | 9 | 72,705 | 71,420 | 349,620 | 13,472 | 191,597 | 27,371 |
| labeller (lean) | 0 | 8 | 96 | 10 | 61,414 | 61,932 | 347,324 | 9,440 | 164,461 | 20,557 |
| labeller (lean) | 1 | 1 | 2 | 3 | 19,815 | 17,607 | 37,860 | 441 | 28,002 | 28,002 |
| labeller (lean) | 1 | 5 | 2 | 7 | 25,862 | 24,497 | 139,323 | 1,895 | 54,031 | 10,806 |
| labeller (lean) | 1 | 6 | 2 | 8 | 26,300 | 23,850 | 163,070 | 1,863 | 55,437 | 9,239 |
| labeller (lean) | 1 | 9 | 2 | 11 | 30,407 | 28,069 | 250,002 | 3,837 | 79,271 | 8,807 |
| labeller (lean) | 1 | 10 | 44 | 12 | 31,780 | 29,914 | 275,404 | 3,430 | 81,420 | 8,142 |
| labeller (lean) | 2 | 6 | 3 | 8 | 27,796 | 25,340 | 158,499 | 3,019 | 65,185 | 10,864 |
| labeller (lean) | 2 | 9 | 3 | 11 | 31,645 | 29,343 | 254,898 | 4,170 | 81,541 | 9,060 |
| labeller (lean) | 2 | 10 | 4 | 12 | 31,131 | 28,654 | 263,098 | 3,868 | 82,288 | 8,228 |
| general-purpose(default) (night) | 0 | 1 | 99 | 3 | 72,043 | 39,518 | 165,293 | 1,921 | 76,586 | 76,586 |
| general-purpose (night) | 0 | 1 | 2 | 3 | 71,531 | 38,240 | 165,938 | 1,838 | 73,586 | 73,586 |
| general-purpose (night) | 0 | 3 | 84 | 5 | 86,972 | 54,419 | 332,487 | 4,822 | 128,456 | 42,818 |
| general-purpose (night) | 0 | 8 | 14 | 10 | 108,049 | 74,633 | 809,385 | 10,102 | 226,098 | 28,262 |
| general-purpose(default) (night) | 1 | 1 | 27 | 3 | 68,405 | 35,084 | 162,740 | 886 | 64,561 | 64,561 |
| general-purpose (night) | 1 | 6 | 11 | 8 | 76,485 | 43,133 | 529,807 | 2,524 | 120,945 | 20,157 |

Medians over the calls of each row. 411 subagent transcripts matched to a dispatch. A call makes one API request per batch of tool calls: the lean agent at 8 sections typically makes 10 to 11 requests (reads and writes partly batched), and each request re-reads the whole context so far from the cache.

Weights: cache write 1.25, cache read 0.1, output 5, relative to one uncached input token, from the Claude Opus 5.5 list prices (input 4, cache write 5, cache read 0.4, output 20 dollars per million). The harness's figure per call counts the context once and is what the task notifications show; the plan's own metering is not published, so both are given.
