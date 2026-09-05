# ДВ coverage map, title pass of 2026-09-05

The first run of the coverage-map instrument (design section 5.2, plan Task A4 Step 2) over the whole corpus and the whole Държавен вестник enumeration. A research artifact: it writes no corpus file and no consumer surface reads it. `report.md` is the instrument's own summary; this note records what went in, what came out, and what the run does not claim.

## Inputs

| Input | Value |
| --- | --- |
| Corpus | `main` at `a29e809ed` (after PR #43), 3,624 acts |
| Issues table | `data/dv/issues.jsonl`, 4,146 issues 1989 to 2026, from `python -m fetcher.dv issues` on 2026-09-05 |
| Materials table | `data/dv/materials.jsonl`, 32,117 `ok` materials and 1,582 `empty` issue rows, from `python -m fetcher.dv materials` on 2026-09-05 with the pagination fix of PR #41 |
| Instrument | `scripts/dv_coverage_map.py` at `a29e809ed` (PR #35 tooling, PR #43 fixes) |
| Run | 2026-09-06 01:14 Sofia, 40 s, default PDF-era boundary бр. 120/2002 |

Both tables live on branch `data/dv-enumeration-2026-09-05` (PR #37, the owner decides whether data tables enter git); the enumeration note there records how they were produced. The command, run from the repository root with the tables in place:

```
.venv/bin/python scripts/dv_coverage_map.py --corpus . --issues data/dv/issues.jsonl --materials data/dv/materials.jsonl --out docs/research/2026-09-05-dv-coverage-map/
```

The instrument is deterministic: two runs on the same inputs were byte-identical across all eight files, and the run committed here is byte-identical to the run the PR #43 reviewer made.

## Files

| File | Rows | What it is |
| --- | --- | --- |
| `report.md` | | The instrument's summary: grades, event and base sources, unlocated rows by uncertainty, reading budget, predecessor acts, estado disputes with their denominator, PDF-era inventory |
| `acts-summary.csv` | 3,624 | One row per act: candidate grade, pending items, event counts by source, base source, page estimate, `dv_identifier` |
| `coverage-map.csv.gz` | 20,266 | One row per chain row (16,642 events, 3,624 bases): source, locator, score, flags, uncertainty. Gzipped (2.7 MB plain) |
| `chain-omissions.csv` | 23 | Title-pass materials that resolved to an act at an issue its chain lacks, `pass = title` |
| `predecessor-materials.csv` | 722 | Materials about a same-titled predecessor act the corpus does not hold, with the `reason` that routed each (FR-043) |
| `unresolved.csv.gz` | 34,175 | Every row the pass could not settle: 23,689 unattributed materials, 10,319 unlocated events, 160 acts citing no promulgation, 7 acts with no title. Gzipped (13.3 MB plain) |
| `estado-disputes.csv` | 0 | Repeal titles against acts the corpus holds as `vigente`; the report states the denominator |
| `pdf-era-inventory.csv` | 1,583 + 1 | One row per PDF-only issue 1989 to 2002 with the page estimates for the reading budget, plus a final `TOTAL` row (`year = TOTAL`, no date) whose page columns are the column sums |

The command writes `coverage-map.csv` and `unresolved.csv` plain; they were gzipped afterwards with `gzip -9 -n`, and `gunzip -k` restores them. On the data branch the materials table is stored as `materials.jsonl.gz` and must be gunzipped before the command runs. Every CSV is UTF-8 with a header row.

## What the run found

- **Grades.** 3,517 acts B-pending, 107 C, none A or B. In P0 every event is `pending` and the body scan has not run, so no act can grade higher yet; this is the honest state, not a limit of the instrument.
- **Located by title.** 5,185 events and 2,496 bases sit in HTML-era materials the resolver attributed; 1,014 events and 528 bases are PDF-era; 124 events and 107 bases are pre-1989 and offline.
- **Unlocated.** 10,319 events and 493 bases. 939 of those rows are an acquisition or citation gap, not a failed match: 773 sit in issues that expose no materials online, 6 cite an issue the enumeration does not hold, 160 acts cite no promulgation. The remaining 9,873 are `chain_unconfirmed`: the issue has materials and none of their titles names the act, which is the body-scan case by design, since cross-act amendments ride inside other acts' преходни и заключителни разпоредби.
- **Chain omissions.** 23, all after the act's own promulgation. The first preview reported 737; 712 of them were materials about same-titled predecessor acts and two more were repeals of a predecessor published beside the successor. That class is now `predecessor-materials.csv` and FR-043.
- **Predecessor acts.** 722 materials over 207 corpus acts name a same-titled act the corpus does not hold: 719 published before the successor, 1 in the successor's own promulgation issue, 2 repeals the successor outlived. Whether repealed predecessors enter the corpus is an owner decision (FR-043, follow-up of 2026-09-05).
- **Estado disputes.** 0 of 7 attributed repeal titles; 202 repeal titles were never attributed and sit in `unresolved.csv` with their candidates. The zero is not evidence of agreement.
- **Refused near misses.** 314 unattributed materials scored 0.90 or more against a candidate and were refused by the margin, the digit guard or the content guard; their `candidates` column names the act. They are the reasoning pass's first input (plan Task A5).
- **Reading budget.** 1,481 acts have a whole chain in HTML-era materials, base included (grade A candidates once the body scan confirms the chain). The PDF era holds 1,583 issues, 700 of them cited by the corpus, an estimated 4,827 material pages to read for the cited events and bases; every figure is an estimate until an issue PDF is opened (D-064 item 6).

## What this pass does not cover

- **It is a title pass.** Every omission row carries `pass = title`, `chain_scan_complete` is false for every act, and no act can reach grade A from this run. The body pass (`--cache-dir`, after the 12-hour body fetch the owner scheduled for a new session) re-runs the instrument over the material bodies and adds omissions found inside ПЗР instructions, segmenter residue and estado findings from in-force dates.
- **Before бр. 1 от 2003 there is no ДВ-side check.** PDF-era chains are inherited from lex.bg and stated as inherited; the inventory is the reading budget for closing that gap by vision.
- **Before 1989 the Gazette is not online.** Those acts are grade C and a separate track (D-059).
- **Attribution is by title.** A material whose title differs from the corpus title by a content word is refused (or flagged `content_mismatch` on the numbered branch) and never silently attributed; the price is the 314 near misses above, which the reasoning pass adjudicates as data.

## Known instrument limits registered

- `numbered_key` reads a cited regulation's number as the act's own for 7 of 1,987 keyed acts (follow-up of 2026-09-05); contained by the resolver's bounds, zero wrong attributions measured.
- The refusal flags do not say whether a near miss exists. `no_candidate` means the resolver chose nothing from an empty candidate list; `ambiguous_candidates` means it chose nothing from a non-empty one (52 unattributed materials, every one at score 1.000, so they sit inside the 314 near misses). Filter by `resolver_score` and read `candidates`; a filter on `no_candidate` alone drops the highest-confidence rows.
