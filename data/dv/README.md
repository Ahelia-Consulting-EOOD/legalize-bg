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
| `cache/` | `python -m fetcher.dv bodies`, `python -m fetcher.dv material` | never (`.gitignore`) |

The coverage map itself is not written here. It reads these files and
writes seven research artifacts under
`docs/research/2026-09-05-dv-coverage-map/`; see „The coverage map“ at
the end of this file.

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

One line per material published in an issue, plus exactly one line for an
issue that carries no HTML materials, that does not resolve, or whose
page this parser could not read. Around 4,150 requests, one per issue.

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

`error_page` and `unrecognized` are both read downstream as claims about
what the Gazette holds, so neither may be produced in bulk by a bad
afternoon.

- **Five „недостъпен“ stubs in a row** (`--max-consecutive-errors`,
  default 5) are an outage, not five neighbouring gaps in a sparse id
  space. The run logs at ERROR naming the last issue that answered,
  **discards that run of stub rows instead of writing them**, and exits
  non-zero. `--resume` picks it up when the site is back.
- **Too many unreadable pages** mean the site's markup has changed: more
  than ten inside the first fifty issues, or more than five percent of a
  longer run. The run halts the same way, so a redesign cannot write
  „this issue holds nothing“ 4,146 times.

An isolated gap trips neither guard. A single stub between two issues
that answered is recorded and the sweep continues.

## `cache/`

Raw `showMaterialDV.jsp` responses, one flat file per material, named
`<id_mat>.html`, UTF-8, exactly as the site served it. A promulgated text
does not change once published, so a cache hit is served without a
request and the cache is a permanent local record rather than an
expiring one. It is large, it is reproducible from the ids in
`materials.jsonl`, and it is never committed.

Because it is permanent, the „недостъпен“ stub never enters it: a stub
is not written, and a stub found on disk counts as a miss and is
re-fetched. Otherwise one maintenance window during a sweep would make
every material fetched during it unreachable for good, with no request
ever made again to find out.

## `python -m fetcher.dv bodies`: filling the cache

```
python -m fetcher.dv bodies --materials data/dv/materials.jsonl \
    --cache-dir data/dv/cache [--sections NAME ...] [--resume] \
    [--limit N] [--max-consecutive-errors N]
```

The ДВ-side pass of §5.2 is a **body** scan, not a title scan. In
Bulgarian drafting most cross-act amendments ride in the преходни и
заключителни разпоредби of a different act: a ЗИД of act X amends acts Y
and Z in its own §§, under X's title. A title pass never attributes those
events, so the chain would stay lex.bg's, which is the thing the design
forbids. The scan therefore needs the body of every HTML-era material in
the sections that issue corpus acts.

That is on the order of forty-two thousand fetches, about 11.7 hours at
one request per second. The cache makes it a one-time cost. This
subcommand writes no JSONL: its output is the cache.

**Which materials.** By default every material whose section is Народно
събрание, Министерски съвет, or names a ministry. The rest of the
официален раздел, the courts, the Централна избирателна комисия and the
sector regulators, issues decisions and rules that are not corpus acts.
`--sections` **widens** that set and never narrows it, since a scan that
skipped a default section would leave `chain_scan_complete` claiming a
coverage it has not got; `--sections all` reads every section.

**Order.** By `(id_obj, position)`, which is issue by issue and, inside
an issue, the order of publication. Two runs over the same file ask for
the same materials in the same order, so the log line of a halted run
names a real resume point.

**Progress.** Every hundred materials, with the count fetched, the count
served from the cache, the elapsed time and an ETA at one request per
second. The ETA counts the materials not yet in the cache when the run
started, so it is one second optimistic per stub an older run left
behind.

**Resuming.** The cache is the resume: a material already in it costs no
request, so the plain command continues yesterday's run. `--resume`
additionally trusts the cache by file name instead of reading each cached
body to check it, which over forty-two thousand files is the difference
between a fast start and a slow one; the price is that it also skips a
„недостъпен“ stub an older run stored, so run without it once after an
outage.

**Halting.** Five „недостъпен“ answers in a row (`--max-consecutive-errors`,
default 5) are an outage rather than five missing materials. The run logs
at ERROR naming the last material that answered and exits non-zero.
Nothing is cached for those five, so the outage leaves no trace to
mistake for a Gazette gap later. An isolated missing material does not
trip the guard: it costs one request per run and is asked for again.

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

## The coverage map

```
python scripts/dv_coverage_map.py --corpus . \
    --issues data/dv/issues.jsonl --materials data/dv/materials.jsonl \
    --out docs/research/2026-09-05-dv-coverage-map/
```

Reads the corpus frontmatter and the two tables above, and writes eight
files. It is a **research artifact**: it writes nothing into the corpus
tree and no consumer surface reads it. The provenance block that does is
P1.

| Output | One row per |
|---|---|
| `coverage-map.csv` | act base, and act amendment event |
| `acts-summary.csv` | act |
| `chain-omissions.csv` | Gazette material the act's chain does not know |
| `predecessor-materials.csv` | Gazette material older than the act it names |
| `unresolved.csv` | event, act or material nothing could be said about |
| `estado-disputes.csv` | Gazette repeal of an act the corpus calls current |
| `pdf-era-inventory.csv` | Gazette issue online only as a PDF |
| `report.md` | the totals, in prose |

`segmenter-residue.csv`, which design 5.2 also lists, is not produced
here: it holds the instructions the ЗИД segmenter could not classify, and
the segmenter belongs to the body scan. It arrives with that leg.

`--pdf-era-end YEAR:NUMBER` (default `2002:120`) is the last issue of the
PDF era, which bounds the inventory. The default is the enumeration of
2026-09-05, which read 1,583 issues with no materials list from 1989 to
бр. 120 от 29 декември 2002 and 2,487 with one from бр. 1 от 3 януари
2003 on. The flag moves the bound without touching the code, because the
enumeration can be rerun.

**The source class** of every base and every event, per §4.1:

- `dv_html`: the issue has a materials list and the resolver attributed
  one of its materials to this act. `locator_id_mat` names it.
- `dv_pdf`: the issue is online only as a whole-issue attachment, so the
  text needs the vision reading path.
- `dv_offline`: before 1989, which is not online at all.
- `unlocated`: everything else, and never „lex.bg-sourced“. The
  `uncertainty` column says which: `issue_not_in_table`,
  `chain_unconfirmed` (the issue has materials and none is about this
  act), `issue_number_unknown`, `promulgation_unknown`,
  `materials_not_enumerated` (the sweep has not reached that issue,
  which is not the same as the issue holding nothing).

`report.md` tabulates those labels, with a gloss and the base and event
counts, because only `chain_unconfirmed` is a failed match: the rest say
the ДВ side could not be consulted at all, and no resolver closes any of
them. It also counts the unattributed materials that scored 0.90 or more,
which are the refused near misses whose `candidates` column names the act
they nearly matched, and which are the reasoning pass's first input.

**The candidate grade** is derived by the procedure of §4.2, never set by
hand. In P0 every event is `applied = pending`, every base is an unfrozen
and unaudited `snapshot`, and the body scan has not run, so only rules 1
and 3 can fire: every act with anything offline in scope is **C** and
every other act is **B-pending**, with its open items listed in
`pending_items` (`events_pending`, `chain_scan`, `promulgation_unlocated`,
`promulgation_unknown`, `base_audit`, `freeze`).

**The page estimate** is the median HTML-era length by act type and
decade, applied to every `dv_pdf` row, base rows included, because a
PDF-era base has to be read for its structural audit. Lengths come from
consecutive materials' start pages; the last material of an issue would
need the issue's page count to bound it, and the `issues` table does not
carry one, so it contributes no measurement.

**The PDF-era inventory** answers D-064 item 6: the owner has not bought
the vision reading of the 1989 to бр. 120/2002 tables of contents and
wants the size of the bill first. One row per PDF-era issue, with the
issue identity, the number of corpus chain rows that cite it (base rows
included, since a PDF-era base has to be read for its structural audit),
and three estimates, followed by a `TOTAL` row that is the line the
token-cost evaluation is done against.

| Estimate | What it would buy |
|---|---|
| `toc_pages_est` | reading only the table of contents |
| `corpus_material_pages_est` | reading only the materials this corpus cites |
| `issue_pages_est` | reading the whole issue |

The page model is measured on the HTML era, where the Gazette states its
own page numbers: contents pages are the first material's start page
minus one, a material's length is the next material's start page minus
its own, and an issue's length is its last material's start page plus one
median material. **Every figure is an estimate** until an issue PDF is
opened, and `report.md` prints the spread of the contents measurement
rather than a single number to be taken on trust.

**`dv_identifier`** is the `dv-<idMat>` of the promulgating material,
carried on every act whose base resolves to `dv_html`. It is the
identifier form D-064 item 4 settled for an act with no lex.bg document.
No corpus act is in that position today, so the column exists to fix the
form rather than to be read.

**`predecessor-materials.csv`** records a Gazette material published
before the act its title resolved to was promulgated. Bulgarian acts are
replaced by new acts of the same name and only the current one is in the
corpus, so „Закон за изменение и допълнение на Закона за горите“ in
бр. 64/2007 resolves to the Закон за горите of 2011 and cannot be an
event of it. The rows are data for the corpus-completeness question,
which repealed predecessors the corpus should hold, and never a chain
omission or an `estado` dispute of the act they resolved to; the routing
coordinate, the act's own `fecha_publicacion`, is carried in
`act_promulgated`.

**`estado-disputes.csv`** records a Gazette material whose title repeals
an act the corpus still records as `vigente`. Data, never a correction:
D-064 item 5 keeps every `estado` finding out of the corpus until the
single write gate exists. The other direction, the corpus calling an act
repealed while the Gazette goes on amending it, needs the in-force dates
the body scan reads, so the title pass does not claim it.

**Two limits, stated in the report rather than hidden.** This is a
**title** pass, so every row of `chain-omissions.csv` and of
`estado-disputes.csv` carries `pass = title`, `chain_scan_complete` is
false for every act, and no act can reach grade A from this map; the body
pass over the cache that `bodies` fills is the next leg. And before бр. 1
от 2003 there is no ДВ-side check at all, so every chain from 1989 to
2002 is inherited from lex.bg and is reported as inherited rather than as
verified.
