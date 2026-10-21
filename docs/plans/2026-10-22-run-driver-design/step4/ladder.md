## Rounds 1 and 2: tokens per call by tasks per call (one task = one target block with its two neighbours)

| Agent | Round | Tasks per call | Calls | Median tokens per call | Tokens per task |
|---|---|---|---|---|---|
| labeller (lean) | 1 | 1 | 2 | 19,815 | 19,815 |
| labeller (lean) | 1 | 5 | 2 | 25,862 | 5,172 |
| labeller (lean) | 1 | 6 | 2 | 26,300 | 4,383 |
| labeller (lean) | 1 | 8 | 1 | 28,809 | 3,601 |
| labeller (lean) | 1 | 9 | 2 | 30,407 | 3,378 |
| labeller (lean) | 1 | 10 | 44 | 31,780 | 3,178 |
| labeller (lean) | 2 | 2 | 1 | 21,731 | 10,865 |
| labeller (lean) | 2 | 6 | 3 | 27,796 | 4,632 |
| labeller (lean) | 2 | 7 | 1 | 29,060 | 4,151 |
| labeller (lean) | 2 | 9 | 3 | 31,645 | 3,516 |
| labeller (lean) | 2 | 10 | 4 | 31,131 | 3,113 |
| general-purpose (night) | 1 | 1 | 1 | 69,248 | 69,248 |
| general-purpose (night) | 1 | 3 | 1 | 71,648 | 23,882 |
| general-purpose (night) | 1 | 4 | 1 | 73,199 | 18,299 |
| general-purpose (night) | 1 | 6 | 11 | 76,485 | 12,747 |
| general-purpose (night) | 1 | 7 | 1 | 76,870 | 10,981 |
| general-purpose (night) | 2 | 1 | 1 | 69,328 | 69,328 |
| general-purpose (night) | 2 | 9 | 1 | 80,631 | 8,959 |
| general-purpose (night) | 2 | 10 | 1 | 81,504 | 8,150 |
| general-purpose(default) (night) | 1 | 1 | 27 | 68,405 | 68,405 |

Fit for labeller (lean), rounds 1 and 2, 65 calls: tokens per call = 19,392 + 1,240 x tasks. Projected per task: at 10 tasks 3,179; at 20 tasks 2,210; at 30 tasks 1,886; at 40 tasks 1,725.

Fit for general-purpose (night), rounds 1 and 2, 18 calls: tokens per call = 67,855 + 1,394 x tasks. Projected per task: at 10 tasks 8,179; at 20 tasks 4,787; at 30 tasks 3,656; at 40 tasks 3,090.

Round-1 task files: 579 files, median 1,511 bytes, mean 1,594 bytes (three blocks, the context headings, the exceptions and the neighbours' labels).

## Round 1: targets still excepted after the round, by position within the call

| Agent | Tasks per call | Position | Targets | Still excepted after round 1 | Share |
|---|---|---|---|---|---|
| labeller (lean) | 10 | 1 | 44 | 8 | 18% |
| labeller (lean) | 10 | 2 | 44 | 7 | 16% |
| labeller (lean) | 10 | 3 | 44 | 6 | 14% |
| labeller (lean) | 10 | 4 | 44 | 7 | 16% |
| labeller (lean) | 10 | 5 | 44 | 9 | 20% |
| labeller (lean) | 10 | 6 | 44 | 10 | 23% |
| labeller (lean) | 10 | 7 | 44 | 9 | 20% |
| labeller (lean) | 10 | 8 | 44 | 9 | 20% |
| labeller (lean) | 10 | 9 | 44 | 6 | 14% |
| labeller (lean) | 10 | 10 | 44 | 8 | 18% |
| general-purpose (night) | 6 | 1 | 11 | 2 | 18% |
| general-purpose (night) | 6 | 2 | 11 | 4 | 36% |
| general-purpose (night) | 6 | 3 | 11 | 5 | 45% |
| general-purpose (night) | 6 | 4 | 11 | 4 | 36% |
| general-purpose (night) | 6 | 5 | 11 | 3 | 27% |
| general-purpose (night) | 6 | 6 | 11 | 2 | 18% |

All round-1 targets attributed to a call: 579; still excepted after round 1: 110 (19%).
