"""The ДВ coverage map: every corpus event against the Gazette side.

    python scripts/dv_coverage_map.py --corpus . \
        --issues data/dv/issues.jsonl --materials data/dv/materials.jsonl \
        --out docs/research/2026-09-05-dv-coverage-map/

§5.2 of `docs/plans/2026-09-05-dv-graded-source-design.md`. The map is
the first deliverable of P0 and the instrument that turns the graded
source model from a definition into numbers: which acts, which events,
how many Gazette PDF pages stand between grade B and grade A.

It is a RESEARCH ARTIFACT. It reads the corpus frontmatter and the two
JSONL tables the acquisition layer wrote, and it writes seven files under
`--out`: `coverage-map.csv`, `acts-summary.csv`, `chain-omissions.csv`,
`unresolved.csv`, `estado-disputes.csv`, `pdf-era-inventory.csv` and
`report.md`. It writes nothing into the corpus tree and derives no grade
that any consumer surface sees; the provenance block that does is P1.

What it records, per act and per event of `amendment_history`:

- the issue the event cites, and whether the `issues` table holds it;
- the material the resolver attributes to it, with the match score and
  the ambiguity flags, or the fact that nothing resolved;
- the source class of §4.1: `dv_html`, `dv_pdf`, `dv_offline` or
  `unlocated`;
- the candidate grade of §4.2, derived by `derive_grade` below;
- for PDF-era rows, an estimated page count.

Three of the outputs answer D-064, the owner's decisions of 2026-09-05.
`pdf-era-inventory.csv` is the reading budget for the 1989 to бр. 42/2005
tables of contents the owner has not bought yet (item 6); the
`dv_identifier` column carries the `dv-<idMat>` form an act with no
lex.bg document would be identified by (item 4); and
`estado-disputes.csv` records a Gazette repeal of an act the corpus still
calls current as DATA, never as a correction, because no `estado` finding
may become a commit before the single write gate exists (item 5).

**Two limits of this pass, both stated rather than hidden.**

The ДВ-side pass here is a TITLE pass. §5.2 requires a BODY scan, because
in Bulgarian drafting most cross-act amendments ride in the преходни и
заключителни разпоредби of a different act, under that act's title. The
body scan is a later leg of P0 and needs `python -m fetcher.dv bodies` to
have filled the cache; until it runs, `chain_scan_complete` is false for
every act, no act can reach grade A, and `chain-omissions.csv` carries
the column `pass` so that its title-pass rows are never mistaken for the
complete answer.

Before бр. 43 от 2005 there is no ДВ-side check at all: PDF-era issues
expose no materials list, so chains from 1989 to 2004 are inherited from
lex.bg. The report says so in as many words.

**The P0 inputs to the grade procedure are fixed and the map says why.**
Every event is `applied = pending`, every base is `state = snapshot` with
`frozen_at` null and `audited` false, and `chain_scan_complete` is false.
Under those inputs §4.2 can only reach rule 1 or rule 3, so every act
with an online promulgation comes out B-pending with its open items
enumerated, and every act with anything offline in scope comes out C.
That is not a limitation of the map; it is the honest state of the corpus
before the engine, the audits and the freeze exist.
"""

import argparse
import csv
import json
import logging
import statistics
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fetcher.dv.resolver import (  # noqa: E402
    CorpusAct,
    Resolver,
    act_type_of,
    instruction_kind,
    load_corpus_acts,
)

#: The first year Държавен вестник is online at all: dv.parliament.bg
#: holds issues from 1 January 1989. Anything earlier is `dv_offline` and
#: is a grade C track of its own (D-059).
FIRST_ONLINE_YEAR = 1989

#: The first issue with per-material HTML: бр. 43 от 20 май 2005. Before
#: it an issue is a whole-issue PDF, so its events are `dv_pdf` and its
#: chain is inherited from lex.bg.
HTML_ERA_YEAR = 2005

#: Act types the page-length medians are grouped by, per §5.2. Everything
#: else is measured together as „other“.
PAGE_ACT_TYPES = ("закон", "кодекс", "наредба", "правилник", "постановление")

#: The last issue before per-material HTML begins: бр. 42 от 2005, since
#: idMat 300 is бр. 43 от 20 май 2005. It is a probe result rather than a
#: certainty, so `--pdf-era-end` moves it without touching the code.
DEFAULT_PDF_ERA_END = (2005, 42)

log = logging.getLogger("dv_coverage_map")


# --- the grade procedure of §4.2 -----------------------------------------


def derive_grade(
    *,
    base_source: str,
    base_state: str,
    base_frozen_at: str | None,
    base_audited: bool,
    chain_scan_complete: bool,
    divergences_unadjudicated: int,
    events,
    promulgation_cited: bool = True,
) -> tuple[str, tuple[str, ...]]:
    """The grade of one act, and the items still open on it.

    The decision procedure of §4.2, rule by rule, first match deciding.
    `events` is the multiset of (source, applied) pairs IN SCOPE: the
    caller has already dropped anything before `base.declared_at`, which
    no act carries today, and has already separated the promulgation from
    the events.

    Returns the grade („A“, „B“, „B-pending“, „C“, or „none“ for an act
    rule 0 holds in staging outside the corpus tree) and the open items,
    in a fixed order so two runs agree.

    The open items are computed the same way whatever the grade, because
    §4.2 says a grade C act's online events are still sourced and
    verified as for B and the pending counter still applies. They decide
    the grade only through rule 3.
    """
    pending: list[str] = []
    if any(applied == "pending" for _, applied in events):
        pending.append("events_pending")
    if not chain_scan_complete:
        pending.append("chain_scan")
    if base_source == "unlocated":
        # §4.1 keeps both cases in one source class and tells them apart
        # by the uncertainty: a promulgation cited and not found, against
        # the 121 acts that cite none at all.
        pending.append(
            "promulgation_unlocated" if promulgation_cited else "promulgation_unknown"
        )
    if (
        base_state == "snapshot"
        and base_source in ("dv_html", "dv_pdf")
        and not base_audited
    ):
        pending.append("base_audit")
    if base_state == "snapshot" and base_frozen_at is None:
        pending.append("freeze")
    items = tuple(pending)

    # Rule 0: a rebuilt or read base with open divergences is not a
    # committed file at all, so it has no grade.
    if base_state in ("rebuilt", "read") and divergences_unadjudicated > 0:
        return "none", items

    # Rule 1: anything offline in scope.
    if base_source == "dv_offline" or any(
        source == "dv_offline" for source, _ in events
    ):
        return "C", items

    # Rule 2: ДВ-complete.
    if (
        base_state == "rebuilt"
        and base_source == "dv_html"
        and chain_scan_complete
        and divergences_unadjudicated == 0
        and all(
            source == "dv_html" and applied in ("replayed", "not_incorporated")
            for source, applied in events
        )
    ):
        return "A", items

    # Rule 3: anything open.
    if items:
        return "B-pending", items

    # Rule 4: everything else.
    return "B", items


# --- reading the tables ---------------------------------------------------


@dataclass(frozen=True)
class Issue:
    """One row of the `issues` table, with what `materials` said about it."""

    year: int
    number: int
    date: str | None
    id_obj: int
    extraordinary: bool
    #: „ok“ when the issue has a materials list, „empty“ when it answered
    #: „Намерени резултати: 0“ (the PDF-era signal), „error_page“ or
    #: „unrecognized“, and None when the materials sweep has not reached
    #: it yet, which is not the same as any of those.
    status: str | None


@dataclass(frozen=True)
class Material:
    """One row of the `materials` table."""

    id_obj: int
    year: int
    number: int
    date: str | None
    position: int
    id_mat: int
    section: str
    title: str
    start_page: int | None


def read_jsonl(path: Path) -> list[dict]:
    rows = []
    with Path(path).open(encoding="utf-8") as handle:
        for number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as error:
                raise SystemExit(f"{path} line {number} is not JSON: {error}") from None
    return rows


def read_issues(path: Path, materials) -> dict[tuple[int, int], Issue]:
    """The `issues` table keyed by (year, number), carrying its status.

    The status comes from the `materials` table, which holds one row per
    empty, unreachable or unreadable issue and one row per material of
    every other. An issue the materials sweep has not reached carries no
    status at all, and the map must not read that silence as „no HTML“.
    """
    status_by_id: dict[int, str] = {}
    for material in materials:
        id_obj = material.get("id_obj")
        status = material.get("status")
        if id_obj is None or status is None:
            continue
        # „ok“ wins over anything else recorded for the same issue.
        if status == "ok" or id_obj not in status_by_id:
            status_by_id[id_obj] = status

    issues: dict[tuple[int, int], Issue] = {}
    for row in read_jsonl(path):
        year, number = row.get("year"), row.get("number")
        if year is None or number is None:
            continue
        issues[(int(year), int(number))] = Issue(
            year=int(year),
            number=int(number),
            date=row.get("date"),
            id_obj=row.get("id_obj"),
            extraordinary=bool(row.get("extraordinary")),
            status=status_by_id.get(row.get("id_obj")),
        )
    return issues


def read_materials(rows) -> list[Material]:
    materials = []
    for row in rows:
        if row.get("status") != "ok" or row.get("id_mat") is None:
            continue
        year, number = row.get("issue_year"), row.get("issue_number")
        if year is None or number is None:
            continue
        materials.append(
            Material(
                id_obj=row.get("id_obj"),
                year=int(year),
                number=int(number),
                date=row.get("issue_date"),
                position=row.get("position") or 0,
                id_mat=int(row["id_mat"]),
                section=row.get("section") or "",
                title=row.get("title") or "",
                start_page=row.get("start_page"),
            )
        )
    materials.sort(key=lambda m: (m.year, m.number, m.position, m.id_mat))
    return materials


# --- the chain of one act -------------------------------------------------


@dataclass(frozen=True)
class ChainRow:
    """One row of an act's chain: its base, or one amendment event."""

    kind: str  # "base" or "event"
    position: int
    year: int | None
    number: int | None
    date: str | None


def act_chain(act: CorpusAct) -> list[ChainRow]:
    """The base and the events of one act, in order.

    `amendment_history` opens with the act's own promulgation, and that
    row is the BASE, not an event: counting it as one would give every
    act a pending event it does not have and would double-count the
    promulgation in every total. It is recognised by its (year, number)
    matching `dv_issue`/`dv_year`, and failing that by being the first
    row, which is how the 160 acts without a `dv_issue` still get a base.

    A row that names no issue („dv“ absent or unparseable) keeps its date,
    which is enough to tell the offline era from the online one.
    """
    promulgation = act.promulgation
    rows = list(act.amendment_history)

    base_index = None
    for index, (reference, _date) in enumerate(rows):
        if promulgation is not None and reference == promulgation:
            base_index = index
            break
    if base_index is None and promulgation is None and rows:
        base_index = 0

    chain: list[ChainRow] = []
    if promulgation is not None:
        chain.append(
            ChainRow("base", 0, promulgation[0], promulgation[1], act.fecha_publicacion)
        )
    elif base_index is not None:
        reference, date = rows[base_index]
        chain.append(
            ChainRow(
                "base",
                0,
                reference[0] if reference else _year_of(date),
                reference[1] if reference else None,
                date,
            )
        )
    else:
        chain.append(ChainRow("base", 0, None, None, act.fecha_publicacion))

    position = 0
    for index, (reference, date) in enumerate(rows):
        if index == base_index:
            continue
        position += 1
        chain.append(
            ChainRow(
                "event",
                position,
                reference[0] if reference else _year_of(date),
                reference[1] if reference else None,
                date,
            )
        )
    return chain


def _year_of(date: str | None) -> int | None:
    if not date:
        return None
    try:
        return int(str(date)[:4])
    except ValueError:
        return None


# --- classifying one row --------------------------------------------------


@dataclass(frozen=True)
class Classification:
    source: str
    id_mat: int | None
    score: float
    flags: tuple[str, ...]
    uncertainty: tuple[str, ...]
    candidates: tuple[str, ...]


def classify(
    row: ChainRow,
    act: CorpusAct,
    issues: dict[tuple[int, int], Issue],
    attributed: dict[tuple[int, int, str], Material],
    scores: dict[int, tuple[float, tuple[str, ...], tuple[str, ...]]],
) -> Classification:
    """The source class of one base or event row, per §4.1 and §5.2.

    Order matters. The offline test comes first, because an act
    promulgated in 1950 is grade C whatever the issue table says about
    the number it cites, and because before 1989 the table holds nothing
    to look up.
    """
    if row.year is None:
        return Classification("unlocated", None, 0.0, (), ("promulgation_unknown",), ())
    if row.year < FIRST_ONLINE_YEAR:
        return Classification("dv_offline", None, 0.0, (), (), ())
    if row.number is None:
        return Classification(
            "unlocated", None, 0.0, (), ("issue_number_unknown",), ()
        )

    key = (row.year, row.number)
    issue = issues.get(key)
    if issue is None:
        return Classification("unlocated", None, 0.0, (), ("issue_not_in_table",), ())

    material = attributed.get((row.year, row.number, act.law_id))
    if material is not None:
        score, flags, _candidates = scores.get(material.id_mat, (1.0, (), ()))
        return Classification("dv_html", material.id_mat, score, flags, (), ())

    if issue.status == "ok":
        # The issue has an HTML materials list and nothing in it is about
        # this act. That is `unlocated`, never „lex.bg-sourced“.
        return Classification(
            "unlocated", None, 0.0, (), ("chain_unconfirmed",), ()
        )
    if issue.status == "empty":
        return Classification("dv_pdf", None, 0.0, (), (), ())
    if issue.status is None and row.year < HTML_ERA_YEAR:
        # The materials sweep has not reached it, and it is older than
        # the HTML era, so PDF is what it is.
        return Classification("dv_pdf", None, 0.0, (), (), ())
    return Classification(
        "unlocated", None, 0.0, (), ("materials_not_enumerated",), ()
    )


# --- the page estimate ----------------------------------------------------


@dataclass(frozen=True)
class PageMeasurements:
    """What the HTML era says a Gazette issue is shaped like.

    Everything the PDF-era estimate is built from, measured rather than
    assumed, and kept as raw samples so the report can print the spread
    instead of a single number the reader has to trust.
    """

    #: Material lengths in pages, by (act type, decade).
    lengths: dict[tuple[str, int], list[int]]
    #: Pages of table of contents per issue: the first material starts on
    #: page N, so pages 1 to N-1 are the contents and the masthead.
    toc_samples: list[int]
    #: The start page of each issue's last material, which bounds the
    #: issue from below once one material length is added to it.
    last_start_pages: list[int]


def measure_pages(materials) -> PageMeasurements:
    """The page model of §5.2 and D-064 item 6, measured on the HTML era.

    Consecutive materials' start pages give the length of every material
    but the last of an issue. The last one would need the issue's page
    count, and the `issues` table does not carry it, so it contributes no
    length rather than a guess; it does contribute its start page, which
    is what the issue-length estimate is built on.
    """
    by_issue: dict[tuple[int, int], list[Material]] = defaultdict(list)
    for material in materials:
        by_issue[(material.year, material.number)].append(material)

    lengths: dict[tuple[str, int], list[int]] = defaultdict(list)
    toc_samples: list[int] = []
    last_start_pages: list[int] = []
    for rows in sorted(by_issue.items()):
        rows = sorted(rows[1], key=lambda m: (m.position, m.id_mat))
        if rows and rows[0].start_page is not None and rows[0].start_page >= 1:
            toc_samples.append(rows[0].start_page - 1)
        if rows and rows[-1].start_page is not None:
            last_start_pages.append(rows[-1].start_page)
        for current, following in zip(rows, rows[1:]):
            if current.start_page is None or following.start_page is None:
                continue
            pages = following.start_page - current.start_page
            if pages <= 0:
                continue
            lengths[(page_act_type(current.title), decade_of(current.year))].append(
                pages
            )
    return PageMeasurements(
        lengths=dict(lengths),
        toc_samples=toc_samples,
        last_start_pages=last_start_pages,
    )


def page_act_type(title: str) -> str:
    act_type = act_type_of(title)
    return act_type if act_type in PAGE_ACT_TYPES else "other"


def decade_of(year: int) -> int:
    return (year // 10) * 10


class PageEstimator:
    """The median page length to expect of a PDF-era act.

    By act type and decade where the HTML era measured that pair, then by
    act type alone, then over everything. The estimate exists to be the
    budget the owner buys vision reading against, so it says which
    fallback it used rather than pretending to a precision it has not got.
    """

    def __init__(self, measurements: PageMeasurements):
        lengths = measurements.lengths
        self._by_pair = {key: statistics.median(values) for key, values in lengths.items()}
        by_type: dict[str, list[int]] = defaultdict(list)
        everything: list[int] = []
        for (act_type, _decade), values in lengths.items():
            by_type[act_type].extend(values)
            everything.extend(values)
        self._by_type = {
            act_type: statistics.median(values) for act_type, values in by_type.items()
        }
        self._overall = statistics.median(everything) if everything else None

        #: Pages of table of contents in one issue, the same for every
        #: PDF-era issue because nothing in the tables distinguishes them.
        self.toc_samples = sorted(measurements.toc_samples)
        self.toc_pages = (
            round(statistics.median(self.toc_samples)) if self.toc_samples else 0
        )
        #: Pages in one issue: where its last material starts, plus one
        #: median material to carry that last material to its end.
        if measurements.last_start_pages and self._overall is not None:
            self.issue_pages = round(
                statistics.median(
                    [start + self._overall for start in measurements.last_start_pages]
                )
            )
        else:
            self.issue_pages = 0
        self.issue_samples = len(measurements.last_start_pages)

    def pages(self, act_type: str, year: int | None) -> int:
        act_type = act_type if act_type in PAGE_ACT_TYPES else "other"
        if year is not None:
            value = self._by_pair.get((act_type, decade_of(year)))
            if value is not None:
                return round(value)
        value = self._by_type.get(act_type)
        if value is not None:
            return round(value)
        return round(self._overall) if self._overall is not None else 0


# --- the PDF-era inventory (D-064 item 6) ---------------------------------


def build_inventory(issues, citing, estimator, pdf_era_end) -> list[dict]:
    """One row per Gazette issue that exists online only as a PDF.

    D-064 item 6: the owner is not buying the vision reading of the
    1989 to бр. 42/2005 tables of contents yet, and needs the size of the
    bill first. So this is a budget, not a finding, and every number in it
    is an estimate until an issue PDF is actually opened.

    Three estimates per issue, all built from the HTML era, where the
    Gazette does state its own page numbers:

    - `toc_pages_est`, the table of contents plus the masthead, which is
      what reading only the contents would cost;
    - `corpus_material_pages_est`, the pages of the materials this corpus
      actually cites in that issue, which is what reading only what we
      need would cost;
    - `issue_pages_est`, the whole issue.

    A final `TOTAL` row carries the three sums and the event count, which
    is the line the token-cost evaluation is done against.
    """
    rows = []
    for (year, number), issue in sorted(issues.items()):
        if year < FIRST_ONLINE_YEAR or (year, number) > tuple(pdf_era_end):
            continue
        cited = citing.get((year, number), [])
        material_pages = sum(
            estimator.pages(act.act_type, row.year) for act, row in cited
        )
        rows.append(
            {
                "year": year,
                "number": number,
                "date": issue.date or "",
                "id_obj": issue.id_obj if issue.id_obj is not None else "",
                "extraordinary": "true" if issue.extraordinary else "false",
                "corpus_events_citing": len(cited),
                "toc_pages_est": estimator.toc_pages,
                "corpus_material_pages_est": material_pages,
                "issue_pages_est": estimator.issue_pages,
            }
        )
    rows.append(
        {
            "year": "TOTAL",
            "number": "",
            "date": "",
            "id_obj": "",
            "extraordinary": "",
            "corpus_events_citing": sum(row["corpus_events_citing"] for row in rows),
            "toc_pages_est": sum(row["toc_pages_est"] for row in rows),
            "corpus_material_pages_est": sum(
                row["corpus_material_pages_est"] for row in rows
            ),
            "issue_pages_est": sum(row["issue_pages_est"] for row in rows),
        }
    )
    return rows


def parse_era_end(text: str) -> tuple[int, int]:
    """„YEAR:NUMBER“, the last issue of the PDF era."""
    try:
        year, number = text.split(":", 1)
        return (int(year), int(number))
    except ValueError:
        raise SystemExit(
            f"--pdf-era-end wants YEAR:NUMBER, for example 2005:42, not {text!r}"
        ) from None


# --- the map --------------------------------------------------------------


def build(corpus_root: Path, issues_path: Path, materials_path: Path,
          pdf_era_end=DEFAULT_PDF_ERA_END):
    """Read everything, attribute everything, and return the four tables."""
    acts = load_corpus_acts(corpus_root)
    log.info("read %d acts from %s", len(acts), corpus_root)
    resolver = Resolver(acts)
    by_id = {act.law_id: act for act in acts}

    material_rows = read_jsonl(materials_path)
    materials = read_materials(material_rows)
    issues = read_issues(issues_path, material_rows)
    log.info("read %d issues and %d materials", len(issues), len(materials))

    # One resolution per material, kept so the event rows and the
    # chain-omission rows agree by construction.
    attributed: dict[tuple[int, int, str], Material] = {}
    scores: dict[int, tuple[float, tuple[str, ...], tuple[str, ...]]] = {}
    resolutions: list[tuple[Material, str | None, float, tuple[str, ...], tuple[str, ...]]] = []
    for material in materials:
        result = resolver.resolve(material.title, section=material.section)
        scores[material.id_mat] = (result.score, result.flags, result.candidates)
        resolutions.append(
            (material, result.law_id, result.score, result.flags, result.candidates)
        )
        if result.law_id is not None:
            attributed.setdefault(
                (material.year, material.number, result.law_id), material
            )

    measurements = measure_pages(materials)
    estimator = PageEstimator(measurements)

    coverage: list[dict] = []
    summary: list[dict] = []
    unresolved: list[dict] = []
    #: Every corpus chain row that cites an issue, base rows included: a
    #: PDF-era base has to be read for its structural audit exactly as a
    #: PDF-era event has to be read for its instructions.
    citing: dict[tuple[int, int], list[tuple[CorpusAct, ChainRow]]] = defaultdict(list)

    for act in sorted(acts, key=lambda a: a.law_id):
        rows = act_chain(act)
        classified = [
            (row, classify(row, act, issues, attributed, scores)) for row in rows
        ]
        counts = Counter(found.source for row, found in classified if row.kind == "event")
        base_row, base_class = classified[0]
        # D-064 item 4: an act with no lex.bg document is identified by
        # the material that promulgated it. No corpus act is in that
        # position today, so the column is empty for every act whose base
        # did not resolve, and the form is fixed now rather than later.
        dv_identifier = (
            f"dv-{base_class.id_mat}" if base_class.source == "dv_html" else ""
        )
        pages = 0
        for row, found in classified:
            if row.year is not None and row.number is not None:
                citing[(row.year, row.number)].append((act, row))
            estimate = (
                estimator.pages(act.act_type, row.year) if found.source == "dv_pdf" else 0
            )
            pages += estimate
            coverage.append(
                {
                    "law_id": act.law_id,
                    "row_kind": row.kind,
                    "position": row.position,
                    "dv_year": row.year if row.year is not None else "",
                    "dv_number": row.number if row.number is not None else "",
                    "date": row.date or "",
                    "source": found.source,
                    "applied": "pending" if row.kind == "event" else "",
                    "state": "snapshot" if row.kind == "base" else "",
                    "locator_id_mat": found.id_mat if found.id_mat is not None else "",
                    "resolver_score": f"{found.score:.3f}",
                    "resolver_flags": ";".join(found.flags),
                    "uncertainty": ";".join(found.uncertainty),
                    "pdf_pages_estimate": estimate,
                }
            )
            if found.source == "unlocated" and row.kind == "event":
                unresolved.append(
                    {
                        "kind": "unlocated_event",
                        "law_id": act.law_id,
                        "dv_year": row.year if row.year is not None else "",
                        "dv_number": row.number if row.number is not None else "",
                        "title": act.title,
                        "candidates": "",
                        "resolver_score": "",
                        "resolver_flags": "",
                        "dv_identifier": dv_identifier,
                        "reason": ";".join(found.uncertainty),
                    }
                )

        grade, pending = derive_grade(
            base_source=base_class.source,
            base_state="snapshot",
            promulgation_cited=bool(act.fecha_publicacion or act.promulgation),
            base_frozen_at=None,
            base_audited=False,
            chain_scan_complete=False,
            divergences_unadjudicated=0,
            events=tuple(
                (found.source, "pending") for row, found in classified if row.kind == "event"
            ),
        )
        summary.append(
            {
                "law_id": act.law_id,
                "title": act.title,
                "candidate_grade": grade,
                "pending_items": ";".join(pending),
                "events_total": sum(counts.values()),
                "events_dv_html": counts["dv_html"],
                "events_dv_pdf": counts["dv_pdf"],
                "events_unlocated": counts["unlocated"],
                "events_dv_offline": counts["dv_offline"],
                "pdf_pages_estimate": pages,
                "base_source": base_class.source,
                "dv_identifier": dv_identifier,
            }
        )

        if not act.title:
            unresolved.append(
                {
                    "kind": "empty_titulo",
                    "law_id": act.law_id,
                    "dv_year": "",
                    "dv_number": "",
                    "title": "",
                    "candidates": "",
                    "resolver_score": "",
                    "resolver_flags": "",
                    "dv_identifier": dv_identifier,
                    "reason": "no titulo: the act cannot be resolved by title at all",
                }
            )
        if not act.fecha_publicacion:
            unresolved.append(
                {
                    "kind": "promulgation_unknown",
                    "law_id": act.law_id,
                    "dv_year": "",
                    "dv_number": "",
                    "title": act.title,
                    "candidates": "",
                    "resolver_score": "",
                    "resolver_flags": "",
                    "dv_identifier": dv_identifier,
                    "reason": "the act cites no promulgation",
                }
            )

    omissions = []
    disputes = []
    for material, law_id, score, flags, candidates in resolutions:
        if law_id is None:
            continue
        act = by_id[law_id]
        kind = instruction_kind(material.title)
        if kind == "repeal" and act.estado != "derogado":
            # The Gazette repealed an act lex.bg still records as in
            # force. Data, never a correction: D-064 item 5 keeps every
            # `estado` finding out of the corpus until the single write
            # gate exists. The other direction, lex.bg calling an act
            # repealed while the Gazette goes on amending it, needs the
            # in-force dates the body scan reads, so the title pass does
            # not claim it.
            disputes.append(
                {
                    "pass": "title",
                    "law_id": law_id,
                    "dv_year": material.year,
                    "dv_number": material.number,
                    "id_mat": material.id_mat,
                    "section": material.section,
                    "title": material.title,
                    "title_kind": kind,
                    "corpus_estado": act.estado or "",
                    "gazette_signal": "repeal",
                    "resolver_score": f"{score:.3f}",
                    "resolver_flags": ";".join(flags),
                }
            )
        if (material.year, material.number) in act.chain:
            continue
        omissions.append(
            {
                "pass": "title",
                "law_id": law_id,
                "dv_year": material.year,
                "dv_number": material.number,
                "id_mat": material.id_mat,
                "section": material.section,
                "title": material.title,
                "title_kind": kind,
                "resolver_score": f"{score:.3f}",
                "resolver_flags": ";".join(flags),
            }
        )

    for material, law_id, score, flags, candidates in resolutions:
        if law_id is not None:
            continue
        unresolved.append(
            {
                "kind": "unattributed_material",
                "law_id": "",
                "dv_year": material.year,
                "dv_number": material.number,
                "title": material.title,
                "candidates": ";".join(candidates),
                "resolver_score": f"{score:.3f}",
                "resolver_flags": ";".join(flags),
                "dv_identifier": "",
                "reason": "no corpus act resolved from this title",
            }
        )

    inventory = build_inventory(issues, citing, estimator, pdf_era_end)
    categories = {act.law_id: act.category for act in acts}
    return (coverage, summary, omissions, unresolved, disputes, inventory,
            issues, categories, estimator)


# --- writing --------------------------------------------------------------


def write_csv(path: Path, fieldnames, rows) -> None:
    """One CSV, UTF-8, LF line endings, in the order given."""
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


COVERAGE_FIELDS = [
    "law_id", "row_kind", "position", "dv_year", "dv_number", "date", "source",
    "applied", "state", "locator_id_mat", "resolver_score", "resolver_flags",
    "uncertainty", "pdf_pages_estimate",
]
SUMMARY_FIELDS = [
    "law_id", "title", "candidate_grade", "pending_items", "events_total",
    "events_dv_html", "events_dv_pdf", "events_unlocated", "events_dv_offline",
    "pdf_pages_estimate", "base_source", "dv_identifier",
]
OMISSION_FIELDS = [
    "pass", "law_id", "dv_year", "dv_number", "id_mat", "section", "title",
    "title_kind", "resolver_score", "resolver_flags",
]
UNRESOLVED_FIELDS = [
    "kind", "law_id", "dv_year", "dv_number", "title", "candidates",
    "resolver_score", "resolver_flags", "dv_identifier", "reason",
]
DISPUTE_FIELDS = [
    "pass", "law_id", "dv_year", "dv_number", "id_mat", "section", "title",
    "title_kind", "corpus_estado", "gazette_signal", "resolver_score",
    "resolver_flags",
]
INVENTORY_FIELDS = [
    "year", "number", "date", "id_obj", "extraordinary", "corpus_events_citing",
    "toc_pages_est", "corpus_material_pages_est", "issue_pages_est",
]


def write_report(path: Path, coverage, summary, omissions, unresolved, disputes,
                 inventory, issues, categories, estimator):
    """The short report of §5.2: the totals, and what they do not cover."""
    grades = Counter(row["candidate_grade"] for row in summary)
    by_source = Counter(row["source"] for row in coverage if row["row_kind"] == "event")
    base_sources = Counter(row["base_source"] for row in summary)
    pages = sum(row["pdf_pages_estimate"] for row in summary)

    by_decade: Counter = Counter()
    for row in coverage:
        if row["row_kind"] != "event" or row["dv_year"] == "":
            continue
        by_decade[(decade_of(int(row["dv_year"])), row["source"])] += 1

    # By CORPUS category, not by grade: the owner picks a reading order
    # by act kind, and a second copy of the grade totals would say
    # nothing.
    by_category: Counter = Counter()
    for row in summary:
        by_category[(categories.get(row["law_id"], ""), row["candidate_grade"])] += 1

    all_html = [
        row["law_id"]
        for row in summary
        if row["base_source"] == "dv_html"
        and row["events_total"] == row["events_dv_html"]
    ]

    lines = [
        "# ДВ coverage map",
        "",
        f"Acts: {len(summary)}. Chain rows: {len(coverage)}. "
        f"Issues in the table: {len(issues)}.",
        "",
        "Generated by `scripts/dv_coverage_map.py`. A research artifact: it "
        "writes no corpus file and no consumer surface reads it.",
        "",
        "## Candidate grade",
        "",
        "| Grade | Acts |",
        "|---|---|",
    ]
    for grade in ("A", "B", "B-pending", "C", "none"):
        lines.append(f"| {grade} | {grades.get(grade, 0)} |")

    lines += [
        "",
        "In P0 every event is `pending`, every base is an unfrozen and "
        "unaudited `snapshot`, and the body scan has not run, so rules 1 and "
        "3 of section 4.2 are the only ones that can fire. B-pending and C "
        "are therefore the only grades this map can produce, and that is the "
        "honest state of the corpus rather than a limit of the instrument.",
        "",
        "## Event source",
        "",
        "| Source | Events |",
        "|---|---|",
    ]
    for source in ("dv_html", "dv_pdf", "dv_offline", "unlocated"):
        lines.append(f"| {source} | {by_source.get(source, 0)} |")

    lines += [
        "",
        "## Base source",
        "",
        "| Source | Acts |",
        "|---|---|",
    ]
    for source in ("dv_html", "dv_pdf", "dv_offline", "unlocated"):
        lines.append(f"| {source} | {base_sources.get(source, 0)} |")

    lines += [
        "",
        "## По десетилетие (by decade)",
        "",
        "| Decade | dv_html | dv_pdf | dv_offline | unlocated |",
        "|---|---|---|---|---|",
    ]
    decades = sorted({decade for decade, _ in by_decade})
    for decade in decades:
        lines.append(
            f"| {decade}s | "
            + " | ".join(
                str(by_decade.get((decade, source), 0))
                for source in ("dv_html", "dv_pdf", "dv_offline", "unlocated")
            )
            + " |"
        )

    lines += [
        "",
        "## По категория (by category)",
        "",
        "| Category | B-pending | C | Other |",
        "|---|---|---|---|",
    ]
    for category in sorted({name for name, _ in by_category}):
        pending = by_category.get((category, "B-pending"), 0)
        offline = by_category.get((category, "C"), 0)
        other = sum(
            count for (name, _grade), count in by_category.items() if name == category
        ) - pending - offline
        lines.append(f"| {category} | {pending} | {offline} | {other} |")

    lines += [
        "",
        "## Reading budget",
        "",
        f"Acts whose whole chain is `dv_html`, base included: {len(all_html)}.",
        "",
        f"Total estimated Gazette PDF pages to read: {pages}. The estimate is "
        "the median HTML-era length by act type and decade, applied to every "
        "`dv_pdf` row, base rows included, because a PDF-era base has to be "
        "read for its structural audit. The last material of each issue "
        "contributes no measurement, since the issue table carries no page "
        "count to bound it with.",
        "",
        "## What this pass does not cover",
        "",
        "**It is a title pass.** Section 5.2 requires a body scan, because "
        "most cross-act amendments ride in the преходни и заключителни "
        "разпоредби of another act, under that act's title. Every row of "
        "`chain-omissions.csv` therefore carries `pass = title`, "
        "`chain_scan_complete` is false for every act, and no act can reach "
        "grade A from this map.",
        "",
        f"**Before бр. 43 от {HTML_ERA_YEAR} there is no ДВ-side check at "
        "all.** PDF-era issues expose no materials list, so every chain from "
        f"{FIRST_ONLINE_YEAR} to {HTML_ERA_YEAR - 1} is inherited from "
        "lex.bg and is stated as inherited rather than verified. Reading the "
        "issue tables of contents by vision is the owner-decided way to "
        "close that gap (section 8, P3).",
        "",
        f"**Before {FIRST_ONLINE_YEAR} the Gazette is not online at all.** "
        "Those acts are grade C and a separate track (D-059).",
        "",
        "## Unresolved",
        "",
        "| Kind | Rows |",
        "|---|---|",
    ]
    for kind, count in sorted(Counter(row["kind"] for row in unresolved).items()):
        lines.append(f"| {kind} | {count} |")

    lines += [
        "",
        f"Chain omissions found by the title pass: {len(omissions)}.",
        "",
        f"`estado` disputes found by the title pass: {len(disputes)}. A dispute "
        "is a Gazette material whose title repeals an act the corpus still "
        "records as `vigente`. The other direction, the corpus calling an act "
        "repealed while the Gazette goes on amending it, needs the in-force "
        "dates the body scan reads, so the title pass does not claim it. Every "
        "row is data and none of them changes a corpus file (D-064 item 5).",
        "",
    ]
    lines += _inventory_lines(inventory, estimator)
    path.write_text("\n".join(lines), encoding="utf-8")


def _inventory_lines(inventory, estimator) -> list[str]:
    """The token-cost table D-064 item 6 asks for, and the model behind it."""
    total = inventory[-1] if inventory else {}
    issues = [row for row in inventory if row["year"] != "TOTAL"]
    cited = sum(1 for row in issues if row["corpus_events_citing"])
    toc = estimator.toc_samples
    return [
        "## PDF-era inventory",
        "",
        "The reading budget for the era with no materials list, one row per "
        f"issue in `pdf-era-inventory.csv`. **Every figure is an estimate** "
        "until an issue PDF is opened.",
        "",
        "| Measure | Estimate |",
        "|---|---|",
        f"| PDF-era issues | {len(issues)} |",
        f"| Issues cited by the corpus | {cited} |",
        f"| Estimated table-of-contents pages | {total.get('toc_pages_est', 0)} |",
        "| Estimated corpus-referenced material pages | "
        f"{total.get('corpus_material_pages_est', 0)} |",
        f"| Estimated issue pages | {total.get('issue_pages_est', 0)} |",
        "",
        "The page model is measured on the HTML era, where the Gazette states "
        "its own page numbers. Table-of-contents pages are the first "
        f"material's start page minus one, over {len(toc)} issues: "
        f"minimum {min(toc) if toc else 0}, median {estimator.toc_pages}, "
        f"maximum {max(toc) if toc else 0}. A material's length is the next "
        "material's start page minus its own. An issue's length is its last "
        "material's start page plus one median material, over "
        f"{estimator.issue_samples} issues, giving {estimator.issue_pages} "
        "pages.",
        "",
    ]


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="dv_coverage_map",
        description="Map every corpus amendment event onto the ДВ side.",
    )
    parser.add_argument("--corpus", required=True, help="corpus root")
    parser.add_argument("--issues", required=True, help="issues JSONL")
    parser.add_argument("--materials", required=True, help="materials JSONL")
    parser.add_argument("--out", required=True, help="output directory")
    parser.add_argument(
        "--pdf-era-end",
        default=f"{DEFAULT_PDF_ERA_END[0]}:{DEFAULT_PDF_ERA_END[1]}",
        metavar="YEAR:NUMBER",
        help="last issue of the PDF era, the inventory's upper bound",
    )
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.INFO,
        stream=sys.stderr,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (coverage, summary, omissions, unresolved, disputes, inventory, issues,
     categories, estimator) = build(
        Path(args.corpus), Path(args.issues), Path(args.materials),
        pdf_era_end=parse_era_end(args.pdf_era_end),
    )

    coverage.sort(key=lambda row: (row["law_id"], row["position"]))
    summary.sort(key=lambda row: row["law_id"])
    omissions.sort(key=lambda row: (row["law_id"], row["dv_year"], row["dv_number"],
                                    row["id_mat"]))
    unresolved.sort(
        key=lambda row: (
            row["kind"], row["law_id"], str(row["dv_year"]), str(row["dv_number"])
        )
    )
    disputes.sort(key=lambda row: (row["law_id"], row["dv_year"], row["dv_number"],
                                   row["id_mat"]))

    write_csv(out / "coverage-map.csv", COVERAGE_FIELDS, coverage)
    write_csv(out / "acts-summary.csv", SUMMARY_FIELDS, summary)
    write_csv(out / "chain-omissions.csv", OMISSION_FIELDS, omissions)
    write_csv(out / "unresolved.csv", UNRESOLVED_FIELDS, unresolved)
    write_csv(out / "estado-disputes.csv", DISPUTE_FIELDS, disputes)
    write_csv(out / "pdf-era-inventory.csv", INVENTORY_FIELDS, inventory)
    write_report(out / "report.md", coverage, summary, omissions, unresolved,
                 disputes, inventory, issues, categories, estimator)
    log.info(
        "wrote %d chain rows, %d acts, %d omissions, %d unresolved, "
        "%d estado disputes and %d PDF-era issues to %s",
        len(coverage), len(summary), len(omissions), len(unresolved),
        len(disputes), max(len(inventory) - 1, 0), out,
    )
    return 0


if __name__ == "__main__":  # pragma: no cover - exercised by the CLI itself
    raise SystemExit(main())
