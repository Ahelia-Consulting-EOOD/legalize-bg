## Per call: the four token classes, duration and cache use (medians by agent, round and sections per call)

| Agent | Round | Tasks per call | Calls | Duration, seconds | Time to first response, seconds | Uncached input | Cache write | Cache read | Output | First request read from a warm prefix | Warm prefix available at start | Dollars per call at list price | Cents per task |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| labeller (lean) | 0 | 3 | 2 | 36 | 3 | 12 | 32,260 | 113,368 | 3,720 | 6% | 50% of calls | 0.281 | 9.37 |
| labeller (lean) | 0 | 7 | 2 | 107 | 5 | 19 | 71,401 | 349,620 | 13,472 | 6% | 50% of calls | 0.766 | 10.95 |
| labeller (lean) | 0 | 8 | 96 | 89 | 3 | 20 | 61,912 | 347,324 | 9,440 | 12% | 100% of calls | 0.658 | 8.22 |
| labeller (lean) | 1 | 1 | 2 | 8 | 2 | 6 | 17,602 | 37,860 | 442 | 12% | 100% of calls | 0.112 | 11.20 |
| labeller (lean) | 1 | 5 | 2 | 24 | 2 | 15 | 24,482 | 139,323 | 1,896 | 6% | 50% of calls | 0.216 | 4.32 |
| labeller (lean) | 1 | 6 | 2 | 114 | 3 | 17 | 23,834 | 163,070 | 1,864 | 12% | 100% of calls | 0.222 | 3.70 |
| labeller (lean) | 1 | 9 | 2 | 38 | 2 | 23 | 28,046 | 250,002 | 3,837 | 12% | 100% of calls | 0.317 | 3.52 |
| labeller (lean) | 1 | 10 | 44 | 37 | 2 | 24 | 29,890 | 275,404 | 3,430 | 12% | 80% of calls | 0.326 | 3.26 |
| labeller (lean) | 2 | 6 | 3 | 31 | 2 | 16 | 25,324 | 158,499 | 3,019 | 12% | 100% of calls | 0.261 | 4.35 |
| labeller (lean) | 2 | 9 | 3 | 40 | 2 | 22 | 29,331 | 254,898 | 4,170 | 12% | 100% of calls | 0.326 | 3.62 |
| labeller (lean) | 2 | 10 | 4 | 38 | 2 | 24 | 28,630 | 263,098 | 3,868 | 12% | 100% of calls | 0.329 | 3.29 |
| general-purpose(default) (night) | 0 | 1 | 99 | 20 | 4 | 6 | 39,512 | 165,293 | 1,921 | 54% | 83% of calls | 0.306 | 30.63 |
| general-purpose (night) | 0 | 1 | 2 | 103 | 85 | 6 | 38,234 | 165,938 | 1,838 | 53% | 50% of calls | 0.294 | 29.43 |
| general-purpose (night) | 0 | 3 | 84 | 68 | 12 | 10 | 54,410 | 332,488 | 4,822 | 53% | 54% of calls | 0.514 | 17.13 |
| general-purpose (night) | 0 | 8 | 14 | 132 | 32 | 20 | 74,612 | 809,386 | 10,102 | 53% | 100% of calls | 0.904 | 11.30 |
| general-purpose(default) (night) | 1 | 1 | 27 | 13 | 3 | 6 | 35,078 | 162,740 | 886 | 53% | 100% of calls | 0.258 | 25.82 |
| general-purpose (night) | 1 | 6 | 11 | 36 | 5 | 16 | 43,117 | 529,807 | 2,524 | 53% | 100% of calls | 0.484 | 8.06 |

List prices of Claude Opus 5.5 (6 October 2026): uncached input 4, cache write 5, cache read 0.40, output 20 dollars per million tokens. The dollar figures compare designs; the runs draw on the owner's plan, whose metering is not published.

- lean, round 0: 101 calls; a warm prefix was available at the start of 99 (98%); median share of the first request read from cache: 12% over all calls, 12% when available, 0% when not.
- night, round 0: 200 calls; a warm prefix was available at the start of 143 (72%); median share of the first request read from cache: 53% over all calls, 53% when available, 53% when not.
- lean: 166 calls over 1.0 hours; 145 of 165 launches within 2 seconds of the previous one (a parallel batch); median gap between batches 1.2 minutes; 3 gaps longer than the five-minute cache lifetime.
- night: 245 calls over 6.0 hours; 230 of 244 launches within 2 seconds of the previous one (a parallel batch); median gap between batches 4.0 minutes; 5 gaps longer than the five-minute cache lifetime.
