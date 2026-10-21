## Per call: the four token classes, duration and cache use (medians by round and sections per call)

| Round | Sections or tasks per call | Calls | Requests | Duration, s | Time to first response, s | Uncached input | Cache write, 5-minute | Cache write, 1-hour | Cache read | Output (of which thinking) | Context counted once | Cost-weighted | First request read from a warm prefix | Warm prefix available at start | Dollars per call | Cents per section or task |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 16 | 6 | 4 | 118 | 2.0 | 8 | 68,368 | 0 | 92,434 | 17,288 (3,765) | 86,282 | 177,712 | 61% | 0% of calls | 0.711 | 4.58 |
| 0 | 8 | 227 | 3 | 55 | 2.1 | 6 | 34,023 | 0 | 39,878 | 7,879 (1,650) | 46,141 | 86,688 | 63% | 99% of calls | 0.347 | 5.00 |
| 1 | 10 | 33 | 3 | 20 | 2.1 | 6 | 10,138 | 0 | 22,135 | 1,971 (1,009) | 15,978 | 25,407 | 63% | 100% of calls | 0.102 | 0.89 |
| 2 | 5.0 | 26 | 3 | 11 | 2.1 | 6 | 6,504 | 0 | 19,488 | 946 (404) | 11,320 | 15,280 | 63% | 100% of calls | 0.061 | 1.03 |

Over all 292 calls: uncached input 1,960 tokens (0.01 dollars), five-minute cache writes 9,450,756 (47.25), one-hour cache writes 0 (0.00), cache reads 14,468,645 (5.79), output 2,072,374 of which thinking 401,886 (41.45); 94.50 dollars at list price in all. Context counted once 12,649,011 tokens; cost-weighted 23,624,140.
Round 0: 1798 sections in 233 calls; counted once 6,550 tokens per section, cost-weighted 12,433, 4.97 cents per section.
Rounds 1 and 2: 543 re-labels in 59 calls; counted once 1,606 tokens per re-label, 0.94 cents per re-label.
Wall time: first call started 2026-10-21T21:57:44, last call ended 2026-10-21T22:50:22 (local time).

## The fixed context

First request of the first call: 6,376 tokens of context (70,191 written over the call in all); the agent definition with the labelling instructions, the tool schemas and the workflow harness header. Median first-request context over all calls: 6,164.
