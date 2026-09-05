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
{"year": 2026, "number": 81, "date": "2026-09-04", "id_obj": 12640, "section": 1, "extraordinary": null}
```

`number` is the issue number inside its year and `id_obj` the identifier
`materiali.faces` takes. `id_obj` is sparse and not chronological, so it
is never derived, only recorded. `extraordinary` is `null` unless the row
says otherwise, which it does not today; the flag is there because the
list form can filter on it and a later capture may expose it per row.

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

The issue identity on every line comes from the issue list row, never
from the contents page header, which shows the site's current issue
rather than the issue being listed.

## `cache/`

Raw `showMaterialDV.jsp` responses, one file per material, named
`<id_mat>.html`. A promulgated text does not change once published, so a
cache hit is served without a request and the cache is a permanent local
record rather than an expiring one. It is large, it is reproducible from
the ids in `materials.jsonl`, and it is never committed.

## Re-running

Both enumerations are resumable. `--resume` appends to the output and
skips the ids already in it, so an interrupted run continues where it
stopped without re-fetching. Without `--resume` the output file is
rewritten from scratch. The issue enumeration also takes `--start-page`
so a run can jump straight back to the page it died on.

Politeness is not optional: one request per second, a descriptive
User-Agent, every request logged, and a bot challenge halts the run.
