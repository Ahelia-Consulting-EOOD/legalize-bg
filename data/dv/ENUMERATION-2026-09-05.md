# ДВ enumeration of 2026-09-05

Produced by `python -m fetcher.dv issues` (415 JSF pages) and `python -m fetcher.dv materials` (one fresh
server session per issue, PR #32; paginated lists read in full, PR fix/dv-materials-pagination), at one
request per second.

| Item | Value |
|---|---|
| issues in `issues.jsonl` | 4146 (1989 to 2026; 368 extraordinary) |
| issues with HTML materials | 2487 |
| material rows / distinct idMat | 32117 / 32117 |
| first issue with HTML materials | бр. 1/2003 (2003-01-03) |
| issues before it (PDF era, `empty`) | 1583 |
| status lines | {'empty': 1582} |

`materials.jsonl.gz` is the committed form; `gunzip -k` to use. `data/dv/cache/` (bodies) is never committed.
