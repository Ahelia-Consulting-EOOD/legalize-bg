# `data/dv/`: what the ДВ acquisition layer writes

`fetcher/dv/` reads Държавен вестник (dv.parliament.bg) and writes three
things here. Nothing in this directory is corpus text: it is the
knowledge the coverage map (§5.2 of
`docs/plans/2026-09-05-dv-graded-source-design.md`) consumes to decide
which act and which amendment event can reach which provenance grade.

| File | Written by | Committed |
|---|---|---|
| `issues.jsonl` | `python -m fetcher.dv issues` | yes, when the run is complete |
| `materials.jsonl` | `python -m fetcher.dv materials` | yes, when the run is complete |
| `cache/` | `python -m fetcher.dv material`, and any caller passing `--cache-dir` | never (`.gitignore`) |

## `issues.jsonl`

One line per issue of the Gazette, in the order the list serves it
(newest first). About 4,150 lines, 415 list pages, one request per page.

```json
{"year": 2026, "number": 81, "date": "2026-09-04", "id_obj": 12640, "section": 1, "extraordinary": false}
```

`number` is the issue number inside its year and `id_obj` the identifier
`materiali.faces` takes. `id_obj` is sparse and not chronological, so it
is never derived, only recorded.

`extraordinary` is read from the row itself, which prints the marker
after the date: „Брой 78, 26.8.2026 г. (извънреден)“. Two of the ten
rows of the captured first page carry it, брой 78 and брой 75 of 2026.
It is `false`, not `null`, for the rest: the list marks извънредни
issues explicitly and says nothing about the others, so silence is
evidence of a редовен issue rather than an absence of evidence.

`section` is `1` for официалния раздел and `null` only if a row omits
`razdel_`, which no captured row does. It is never `0`, which would be a
section that does not exist.

## `materials.jsonl`

One line per material published in an issue, plus exactly one line for
an issue that carries no HTML materials or that does not resolve. Around
4,150 requests, one per issue.

```json
{"id_obj": 6121, "issue_year": 2016, "issue_number": 74, "issue_date": "2016-09-20", "status": "ok", "position": 4, "id_mat": 107549, "section": "Народно събрание", "title": "Закон за изменение и допълнение на Административнопроцесуалния кодекс", "start_page": 12}
```

`status` is the whole point of the file:

- `ok`: a material, with its `id_mat`, section, title and start page.
- `empty`: the issue exists and lists nothing. This is the PDF-era
  signal: the issue is online only as a whole-issue attachment, so every
  event published in it needs the vision reading path, not the HTML one.
- `error_page`: the site answered its „недостъпен“ stub for this
  `id_obj`. The stub arrives as HTTP 500 with a 489-byte body, which
  looks transient and is not: it is the permanent answer for a gap in
  the sparse `id_obj` space. The client recognises it by body and hands
  it back rather than spending three retries on it, so one gap costs one
  request.
- `unrecognized`: the answer was neither. This is a statement about the
  parser, never about the Gazette, and it is written so that a reader of
  the file can tell „I could not read this page“ from „this issue does
  not exist“.

A listing is believed only when the number of rows parsed equals the
„Намерени резултати“ the page printed for itself. Any disagreement, a
missing count included, is `unrecognized`: the page states the property
being measured, so there is no need to trust a proxy for it.

The issue identity on every line comes from the issue list row, never
from the contents page header, which shows the site's current issue
rather than the issue being listed.

### The sweep stops rather than write a false map

Both statuses above are read by the coverage map as claims about what the
Gazette holds, so neither may be produced in bulk by a bad afternoon.

- **Five „недостъпен“ stubs in a row** (`--max-consecutive-errors`,
  default 5) are an outage, not five neighbouring gaps in a sparse id
  space. The run logs at ERROR naming the last issue that answered,
  **discards that run of stub rows instead of writing them**, and exits
  non-zero. `--resume` picks it up when the site is back.
- **Too many unreadable pages** — more than ten inside the first fifty
  issues, or more than five percent of a longer run — mean the site's
  markup has changed. The run halts the same way, so a redesign cannot
  write „this issue holds nothing“ 4,146 times.

An isolated gap does not trip either guard; a single stub between two
issues that answered is recorded and the sweep continues.

## `cache/`

Raw `showMaterialDV.jsp` responses, one file per material, named
`<id_mat>.html`. A promulgated text does not change once published, so a
cache hit is served without a request and the cache is a permanent local
record rather than an expiring one. It is large, it is reproducible from
the ids in `materials.jsonl`, and it is never committed.

Because it is permanent, the „недостъпен“ stub never enters it: a stub
is not written, and a stub found on disk counts as a miss and is
re-fetched. Otherwise one maintenance window during a sweep would make
every material fetched during it unreachable for good, with no request
ever made again to find out.

## Re-running

Both enumerations are resumable. `--resume` appends to the output and
skips the issues already finished in it. Without `--resume` the output
file is rewritten from scratch.

Two kinds of row are not treated as finished, and `--resume` drops them
from the file and asks the site again:

**The last issue in the output.** `materials.jsonl` holds one line per
material, so an interruption between two lines of the same issue leaves
that issue looking complete while most of its rows are missing. The last
`id_obj` in the file has all its rows removed and is fetched again, which
costs one request and cannot lose a material. The same rule runs for
`issues.jsonl`, where it costs nothing.

**Every issue recorded as `unrecognized`,** which means the parser could
not read the page. Resuming after the parser is fixed comes back to
exactly those issues instead of skipping them as done.

A final line cut in half by the kill is dropped with a warning; a
malformed line anywhere else stops the run.

`--resume` on `materials` skips the finished issues and so makes no
request for them. `--resume` on `issues` skips the rows already written
but still re-walks the list from page 1 to reach the later pages, because
the pagination is a POST chain: pass `--start-page` as well to jump
straight back to the page the run died on and pay only for what is left.

Politeness is not optional: one request per second, a descriptive
User-Agent, every request logged, and a bot challenge halts the run.
