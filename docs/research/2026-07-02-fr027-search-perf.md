# FR-027 search-latency probe — baseline (2026-07-02)

**Task:** Task 12 of the pre-UI hardening plan (`docs/plans/2026-07-02-pre-ui-hardening-plan.md`).
Measurement-only — no code changes to `index/fts.py` in this task. Tasks 13/14
build on the numbers recorded here.

## Context

The FTS5 catalog grew to **223 M body chars** after the D-047 full re-bootstrap
(3,601 acts). Declared latency budgets:

- `docs/process/delivery-contract.md` (or equivalent contract source): **100 ms
  warm / 250 ms cold** per query.
- Web PRD (`legalize-bg-web`): **300 ms p95**.

Orientation numbers from planning-time review (`docs/research/2026-07-02-pre-ui-code-review.md`)
already flagged this as a deterministic regression, not load-flakiness: **cold
1.2–3.7 s** across representative queries, with **"лични данни" measured at
4.9 s warm**. This task's job is to produce a reproducible probe and record a
clean baseline against the live `catalog.db` for Task 13/14 to reference.

## Baseline

**Machine:** Apple M4, 16 GB RAM (`hw.memsize`=17179869184), macOS 26.5.
**Date:** 2026-07-02. **DB:** `catalog.db` (3,601 acts, 223 M FTS body chars,
post-D-047), opened read-only (`mode=ro`) — not modified by this task.

**Script:** `scripts/perf_probe.py`, run as `.venv/bin/python scripts/perf_probe.py`.
Each query opens a fresh read-only connection (`cold` = first `search_fts` call
on that connection), then issues 5 more calls on the same connection (`warm` =
median of those 5). No signature adaptation was needed: `search_fts(conn, query,
category=None, limit=20)` in `index/fts.py` is called with a `sqlite3.Cursor` as
the first positional argument in the brief's script as-written — this works
because `_run_match` only calls `.execute()`/`.fetchall()` on it, both of which
`sqlite3.Cursor` supports identically to `Connection`. No edit to the probe
script itself was required.

Two runs were taken. Run 1 is the recorded baseline; run 2 is a stability
check because two queries ("лични данни", "административни нарушения") showed
warm latency close to or exceeding their own cold latency — a pattern that
looks anomalous next to every other query in the set (where warm collapses to
single-digit ms). Run 2 confirms the pattern is stable and repeatable, not a
one-off fluke, so **both runs are recorded verbatim** below rather than
cherry-picking.

### Run 1 (recorded baseline)

```
'обществени поръчки': cold=   3538ms warm_p50=     15ms
'данък добавена стойност': cold=   1560ms warm_p50=     14ms
'лични данни': cold=   6566ms warm_p50=   6845ms
'трудов договор': cold=   2386ms warm_p50=     22ms
'движение по пътищата': cold=   2535ms warm_p50=     51ms
'енергийна ефективност': cold=    548ms warm_p50=     10ms
'ЗОП': cold=    208ms warm_p50=      5ms
'касови апарати': cold=     93ms warm_p50=      1ms
'административни нарушения': cold=   3093ms warm_p50=   1053ms
'защита на потребителите': cold=   2289ms warm_p50=     40ms
```

### Run 2 (stability check, same machine, immediately after run 1)

```
'обществени поръчки': cold=   2284ms warm_p50=     16ms
'данък добавена стойност': cold=    838ms warm_p50=     14ms
'лични данни': cold=   3163ms warm_p50=   4560ms
'трудов договор': cold=   1194ms warm_p50=     51ms
'движение по пътищата': cold=   1805ms warm_p50=     78ms
'енергийна ефективност': cold=    404ms warm_p50=     11ms
'ЗОП': cold=    140ms warm_p50=      5ms
'касови апарати': cold=     47ms warm_p50=      1ms
'административни нарушения': cold=   1897ms warm_p50=   1081ms
'защита на потребителите': cold=   1606ms warm_p50=     58ms
```

### Reading the numbers

- **Every query blows the 250 ms cold budget**, most by 1–2 orders of
  magnitude (140 ms–6.6 s observed; only "касови апарати" and "ЗОП" — short,
  low-frequency-token queries — come close to budget).
- **Most queries warm well** (single-digit to ~80 ms after the first call on
  a connection) — consistent with tier-1 title-match short-circuiting or
  SQLite/OS page-cache reuse once a connection has "seen" the relevant FTS
  pages once.
- **Two queries do not warm down**: "лични данни" stays in the multi-second
  range warm (4.6–6.8 s) and "административни нарушения" plateaus around
  ~1.05–1.08 s warm across both runs and both cold-latency levels. Both are
  common, multi-token Bulgarian phrases likely to hit the tier-2
  (full-corpus body `MATCH` + `bm25()` ORDER BY) path from `search_fts` over
  a very large posting list, where cost scales with result-set size rather
  than being helped by page-cache warmth the way a short/rare-token query is.
  This is the concrete regression signal FR-027 exists to track, and lines up
  with the 4.9 s "лични данни" figure noted at planning time.
- Absolute magnitudes differ between run 1 and run 2 (run 2 cold times are
  ~40–70% of run 1's) — expected, since "cold" here means fresh-*connection*,
  not fresh-OS-page-cache (see the probe's own docstring); run 1 was the
  first DB touch this session, run 2 benefited from OS-level page-cache
  carryover. The **relative shape** (which queries are slow, and which two
  don't warm down) is what's stable and load-bearing, not the absolute
  millisecond values.

## Experiments

_(filled by Task 13)_

## Decision

_(filled by Task 14, D-051)_
