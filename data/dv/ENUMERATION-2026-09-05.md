# ДВ enumeration of 2026-09-05

Produced by `python -m fetcher.dv issues` (415 JSF pages) and `python -m fetcher.dv materials` (one fresh
server session per issue, PR #32) plus one `--resume` pass, at one request per second.

| Item | Value |
|---|---|
| issues in `issues.jsonl` | 4146 (1989 to 2026; 368 extraordinary) |
| issues with HTML materials | 2476 |
| material rows / distinct idMat | 31636 / 31636 |
| first issue with HTML materials | бр. 1/2003 (2003-01-03) |
| issues before it (PDF era, `empty`) | 1583 |
| status lines | {'empty': 1582, 'unrecognized': 11} |

Known gap: the 11 issues still `unrecognized` after the resume pass print more
materials than the page lists (the materials list is paginated at 30 rows; the client reads page 1
only). Their first 30 materials are NOT in this table either, since an unrecognised page is not
written. Fix and re-run for those issues before the coverage map's body pass.

`materials.jsonl.gz` is the committed form; `gunzip -k` to use. `data/dv/cache/` (bodies) is never committed.
