"""The coverage map: every corpus event against the ДВ side, graded.

§5.2 and §4.2 of `docs/plans/2026-09-05-dv-graded-source-design.md`. The
map is a research artifact that writes no corpus file, and it is the
instrument that turns the grade model from a definition into numbers, so
these tests are about the numbers being the right ones rather than about
the file being produced.

The corpus files are the real ones, frontmatter copied verbatim into a
temporary tree; the issue and material tables are synthetic, because the
real ones are being written by a live enumeration and the map must be
testable without either.
"""

import csv
import importlib.util
import json
import pathlib
import sys

import pytest

SCRIPT = pathlib.Path(__file__).resolve().parents[2] / "scripts" / "dv_coverage_map.py"
CORPUS = pathlib.Path(__file__).resolve().parents[2]


def load():
    spec = importlib.util.spec_from_file_location("dv_coverage_map", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def cmap():
    return load()


# --- a corpus of real frontmatter ----------------------------------------

REAL_ACTS = [
    ("laws", "zakon-za-obshtestveniya-transport"),
    ("laws", "zakon-za-zadalzheniyata-i-dogovorite"),
    ("laws", "zakon-za-sabraniyata-mitingite-i-manifestatsiite"),
    ("codes", "etichen-kodeks-na-sadebnite-sluzhiteli"),
    ("ordinances", "-549676032"),
]


def copy_frontmatter(root: pathlib.Path, category: str, law_id: str) -> None:
    """Copy one act's YAML header, and nothing of its body.

    The frontmatter must be the real one, since the whole point is that
    the map reads what the corpus actually records; the body is 500 KB of
    Кодекс that the map never opens.
    """
    source = (CORPUS / category / f"{law_id}.md").read_text(encoding="utf-8")
    end = source.index("\n---", 3) + len("\n---")
    (root / category).mkdir(parents=True, exist_ok=True)
    (root / category / f"{law_id}.md").write_text(
        source[:end] + "\n\n# тяло\n", encoding="utf-8"
    )


def synthetic_act(root: pathlib.Path, category: str, law_id: str, body: str) -> None:
    (root / category).mkdir(parents=True, exist_ok=True)
    (root / category / f"{law_id}.md").write_text(
        f"---\n{body}---\n\n# тяло\n", encoding="utf-8"
    )


@pytest.fixture
def corpus(tmp_path):
    root = tmp_path / "corpus"
    for category, law_id in REAL_ACTS:
        copy_frontmatter(root, category, law_id)
    # An act whose promulgation names an issue the table does not hold.
    synthetic_act(
        root,
        "laws",
        "zakon-za-lipsvashtiya-broy",
        "titulo: ЗАКОН ЗА ЛИПСВАЩИЯ БРОЙ\n"
        "rango: закон\n"
        "fecha_publicacion: '2020-12-01'\n"
        "dv_issue: '99'\n"
        "dv_year: 2020\n"
        "amendment_history:\n- dv: 99/2020\n  date: '2020-12-01'\n",
    )
    return root


ISSUES = [
    # (year, number, date, id_obj)
    (1990, 10, "1990-02-02", 10),
    (1998, 11, "1998-01-30", 11),
    (2010, 24, "2010-03-26", 24),
    (2019, 52, "2019-07-02", 52),
    (2026, 32, "2026-04-01", 100),
]

MATERIALS = [
    # (id_obj, position, id_mat, section, title, start_page)
    (
        24, 1, 5001, "Народно събрание",
        "Закон за изменение и допълнение на Закона за събранията, митингите и "
        "манифестациите",
        3,
    ),
    (24, 2, 5002, "Народно събрание", "Закон за ратифициране на нещо", 9),
    (52, 1, 6001, "Народно събрание", "Закон за ратифициране на друго нещо", 4),
    (100, 1, 242220, "Народно събрание", "ЗАКОН ЗА ОБЩЕСТВЕНИЯ ТРАНСПОРТ", 2),
    (
        100, 2, 242221, "Народно събрание",
        "Закон за изменение и допълнение на Закона за задълженията и договорите",
        12,
    ),
    (100, 3, 242222, "Народно събрание", "Закон за ратифициране на трето нещо", 20),
]

#: Issues online as a whole-issue PDF only: no materials list, which is
#: the signal for the PDF era.
EMPTY_ISSUES = {10, 11}


@pytest.fixture
def tables(tmp_path):
    issues = tmp_path / "issues.jsonl"
    with issues.open("w", encoding="utf-8") as handle:
        for year, number, date, id_obj in ISSUES:
            handle.write(
                json.dumps(
                    {
                        "year": year,
                        "number": number,
                        "date": date,
                        "id_obj": id_obj,
                        "section": 1,
                        "extraordinary": False,
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )

    by_id = {id_obj: (year, number, date) for year, number, date, id_obj in ISSUES}
    materials = tmp_path / "materials.jsonl"
    with materials.open("w", encoding="utf-8") as handle:
        for id_obj in sorted(EMPTY_ISSUES):
            year, number, date = by_id[id_obj]
            handle.write(
                json.dumps(
                    {
                        "id_obj": id_obj,
                        "issue_year": year,
                        "issue_number": number,
                        "issue_date": date,
                        "status": "empty",
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )
        for id_obj, position, id_mat, section, title, start_page in MATERIALS:
            year, number, date = by_id[id_obj]
            handle.write(
                json.dumps(
                    {
                        "id_obj": id_obj,
                        "issue_year": year,
                        "issue_number": number,
                        "issue_date": date,
                        "status": "ok",
                        "position": position,
                        "id_mat": id_mat,
                        "section": section,
                        "title": title,
                        "start_page": start_page,
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )
    return issues, materials


@pytest.fixture
def outputs(cmap, corpus, tables, tmp_path):
    issues, materials = tables
    out = tmp_path / "out"
    assert (
        cmap.main(
            [
                "--corpus", str(corpus),
                "--issues", str(issues),
                "--materials", str(materials),
                "--out", str(out),
            ]
        )
        == 0
    )
    return out


def rows(path: pathlib.Path, **where):
    with path.open(encoding="utf-8", newline="") as handle:
        found = list(csv.DictReader(handle))
    for key, value in where.items():
        found = [row for row in found if row[key] == value]
    return found


# --- the files ------------------------------------------------------------


def test_the_map_writes_five_files_and_no_corpus_file(outputs, corpus):
    assert sorted(p.name for p in outputs.iterdir()) == [
        "acts-summary.csv",
        "chain-omissions.csv",
        "coverage-map.csv",
        "report.md",
        "unresolved.csv",
    ]
    # The map is a research artifact. Nothing under the corpus moved.
    assert sorted(p.name for p in (corpus / "laws").iterdir()) == [
        "zakon-za-lipsvashtiya-broy.md",
        "zakon-za-obshtestveniya-transport.md",
        "zakon-za-sabraniyata-mitingite-i-manifestatsiite.md",
        "zakon-za-zadalzheniyata-i-dogovorite.md",
    ]


def test_every_output_is_utf8_without_escapes(outputs):
    for path in outputs.iterdir():
        text = path.read_text(encoding="utf-8")
        assert "\\u04" not in text


def test_the_order_is_deterministic(cmap, corpus, tables, tmp_path):
    issues, materials = tables
    first, second = tmp_path / "a", tmp_path / "b"
    for out in (first, second):
        cmap.main(
            [
                "--corpus", str(corpus),
                "--issues", str(issues),
                "--materials", str(materials),
                "--out", str(out),
            ]
        )
    for name in ("coverage-map.csv", "acts-summary.csv", "chain-omissions.csv",
                 "unresolved.csv"):
        assert (first / name).read_bytes() == (second / name).read_bytes()


# --- a 2026 single-issue act ---------------------------------------------


def test_a_2026_act_resolves_to_its_material(outputs):
    base = rows(
        outputs / "coverage-map.csv",
        law_id="zakon-za-obshtestveniya-transport",
        row_kind="base",
    )
    assert len(base) == 1
    assert base[0]["source"] == "dv_html"
    assert base[0]["state"] == "snapshot"
    assert base[0]["locator_id_mat"] == "242220"
    assert base[0]["dv_year"] == "2026"
    assert base[0]["dv_number"] == "32"


def test_the_promulgation_row_is_not_also_an_event(outputs):
    # `amendment_history` opens with the promulgation. Counting it as an
    # event would make every act carry one pending event it does not have.
    events = rows(
        outputs / "coverage-map.csv",
        law_id="zakon-za-obshtestveniya-transport",
        row_kind="event",
    )
    assert events == []


def test_a_2026_act_is_b_pending_with_exactly_three_open_items(outputs):
    row = rows(
        outputs / "acts-summary.csv", law_id="zakon-za-obshtestveniya-transport"
    )[0]
    assert row["candidate_grade"] == "B-pending"
    assert row["pending_items"].split(";") == ["chain_scan", "base_audit", "freeze"]
    assert row["events_total"] == "0"
    assert row["base_source"] == "dv_html"
    assert row["pdf_pages_estimate"] == "0"


# --- a 1950 act -----------------------------------------------------------


def test_a_1950_act_is_grade_c(outputs):
    row = rows(
        outputs / "acts-summary.csv", law_id="zakon-za-zadalzheniyata-i-dogovorite"
    )[0]
    assert row["candidate_grade"] == "C"
    assert row["base_source"] == "dv_offline"


def test_the_offline_events_of_a_1950_act_are_counted_as_offline(outputs):
    row = rows(
        outputs / "acts-summary.csv", law_id="zakon-za-zadalzheniyata-i-dogovorite"
    )[0]
    # Its chain runs 1950 to 2021; everything before 1989 is offline.
    assert int(row["events_dv_offline"]) == 7
    assert int(row["events_total"]) == 26


def test_an_event_after_1989_of_a_grade_c_act_is_still_sourced(outputs):
    # Rule 1 gives the act grade C, but its online events are located and
    # counted exactly as for a grade B act.
    events = rows(
        outputs / "coverage-map.csv",
        law_id="zakon-za-zadalzheniyata-i-dogovorite",
        row_kind="event",
    )
    by_issue = {(row["dv_year"], row["dv_number"]): row for row in events}
    assert by_issue[("1990", "30")]["source"] == "unlocated"
    assert by_issue[("1977", "16")]["source"] == "dv_offline"


# --- a 1990 act with a 2010 event ----------------------------------------


def test_a_pdf_era_base_with_an_html_event(outputs):
    law = "zakon-za-sabraniyata-mitingite-i-manifestatsiite"
    base = rows(outputs / "coverage-map.csv", law_id=law, row_kind="base")[0]
    assert base["source"] == "dv_pdf"
    events = {
        (row["dv_year"], row["dv_number"]): row
        for row in rows(outputs / "coverage-map.csv", law_id=law, row_kind="event")
    }
    assert events[("1998", "11")]["source"] == "dv_pdf"
    assert events[("2010", "24")]["source"] == "dv_html"
    assert events[("2010", "24")]["locator_id_mat"] == "5001"
    # 2019 бр. 52 has materials, but none of them is about this act.
    assert events[("2019", "52")]["source"] == "unlocated"


def test_the_pdf_pages_estimate_comes_from_the_html_era(outputs):
    # HTML-era lengths measured here: 10 and 8 pages in бр. 32/2026, 6 in
    # бр. 24/2010; the last material of each issue has no next start page
    # and the issue table carries no page count, so it contributes none.
    # The median for a закон is 8, applied to the two PDF-era rows of this
    # act: its 1990 base and its 1998 event.
    row = rows(
        outputs / "acts-summary.csv",
        law_id="zakon-za-sabraniyata-mitingite-i-manifestatsiite",
    )[0]
    assert row["pdf_pages_estimate"] == "16"


def test_every_event_is_pending_in_p0(outputs):
    events = rows(outputs / "coverage-map.csv", row_kind="event")
    assert events
    assert {row["applied"] for row in events} == {"pending"}
    assert {row["state"] for row in rows(outputs / "coverage-map.csv", row_kind="base")} == {
        "snapshot"
    }


# --- an issue the table does not hold ------------------------------------


def test_an_act_citing_a_missing_issue_is_unlocated(outputs):
    base = rows(
        outputs / "coverage-map.csv",
        law_id="zakon-za-lipsvashtiya-broy",
        row_kind="base",
    )[0]
    assert base["source"] == "unlocated"
    assert "issue_not_in_table" in base["uncertainty"]
    row = rows(outputs / "acts-summary.csv", law_id="zakon-za-lipsvashtiya-broy")[0]
    assert row["candidate_grade"] == "B-pending"
    assert "promulgation_unlocated" in row["pending_items"].split(";")


# --- chain omissions ------------------------------------------------------


def test_a_material_the_chain_does_not_know_is_an_omission(outputs):
    # бр. 32/2026 carries a ЗИД of ЗЗД. lex.bg's chain for ЗЗД stops in
    # 2021, so the Gazette knows an event the corpus does not.
    found = rows(
        outputs / "chain-omissions.csv", law_id="zakon-za-zadalzheniyata-i-dogovorite"
    )
    assert len(found) == 1
    assert found[0]["pass"] == "title"
    assert found[0]["dv_year"] == "2026"
    assert found[0]["dv_number"] == "32"
    assert found[0]["id_mat"] == "242221"
    assert found[0]["title_kind"] == "amending"


def test_a_material_the_chain_already_knows_is_not_an_omission(outputs):
    assert not rows(
        outputs / "chain-omissions.csv", law_id="zakon-za-obshtestveniya-transport"
    )
    assert not rows(
        outputs / "chain-omissions.csv",
        law_id="zakon-za-sabraniyata-mitingite-i-manifestatsiite",
    )


# --- unresolved -----------------------------------------------------------


def test_an_act_without_a_titulo_cannot_be_resolved_and_says_so(outputs):
    found = rows(outputs / "unresolved.csv", kind="empty_titulo")
    assert [row["law_id"] for row in found] == ["-549676032"]


def test_an_act_that_cites_no_promulgation_is_listed(outputs):
    found = rows(outputs / "unresolved.csv", kind="promulgation_unknown")
    # The untitled ordinance also cites no promulgation, so it is listed
    # under both kinds: two reasons, two rows, neither hiding the other.
    assert [row["law_id"] for row in found] == [
        "-549676032",
        "etichen-kodeks-na-sadebnite-sluzhiteli",
    ]


def test_an_unlocated_event_carries_the_candidates_considered(outputs):
    found = rows(
        outputs / "unresolved.csv",
        kind="unlocated_event",
        law_id="zakon-za-sabraniyata-mitingite-i-manifestatsiite",
    )
    assert [(row["dv_year"], row["dv_number"]) for row in found] == [("2019", "52")]


def test_an_act_with_no_promulgation_is_b_pending_and_says_which_item(outputs):
    row = rows(
        outputs / "acts-summary.csv", law_id="etichen-kodeks-na-sadebnite-sluzhiteli"
    )[0]
    assert row["candidate_grade"] == "B-pending"
    assert "promulgation_unknown" in row["pending_items"].split(";")


# --- the report -----------------------------------------------------------


def test_the_report_states_the_totals_and_the_pre_2005_inheritance(outputs):
    text = (outputs / "report.md").read_text(encoding="utf-8")
    assert "B-pending" in text
    assert "C" in text
    assert "2005" in text
    assert "по десетилетие" in text or "by decade" in text
    assert "—" not in text  # no em-dashes


def test_the_report_groups_by_corpus_category(outputs):
    # „By category“ means the corpus categories, not a second copy of the
    # grade totals: the owner picks a reading order by act kind.
    text = (outputs / "report.md").read_text(encoding="utf-8")
    section = text.split("(by category)", 1)[1].split("##", 1)[0]
    assert "laws" in section
    assert "codes" in section
    assert "ordinances" in section
    # Four laws, one of them grade C (ЗЗД, 1950).
    assert "| laws | 3 | 1 |" in section


def test_the_report_counts_the_acts_whose_whole_chain_is_html(outputs):
    text = (outputs / "report.md").read_text(encoding="utf-8")
    # ЗОТ alone: base dv_html, no events.
    assert "1" in text


# --- the grade procedure of 4.2, enumerated exhaustively -----------------

BASE_SOURCES = ("dv_html", "dv_pdf", "dv_offline", "unlocated")
BASE_STATES = ("rebuilt", "read", "snapshot")
EVENT_SOURCES = ("dv_html", "dv_pdf", "dv_offline", "unlocated")
APPLIED = ("replayed", "verified", "not_incorporated", "pending")


def valid_inputs(cmap):
    """Every input of §4.2 that its domain constraints allow.

    `hypothesis` is not installed, and the input space is finite and
    small, so it is enumerated rather than sampled: 4 base sources by 3
    base states by frozen by audited by chain-scan by divergences, times
    every multiset of up to two events over the 16 (source, applied)
    pairs. The constraints §4.2 states as domain rather than as rules are
    filtered out here, which is what makes them constraints.
    """
    import itertools

    pairs = [(source, applied) for source in EVENT_SOURCES for applied in APPLIED]
    multisets = [()]
    multisets += [(pair,) for pair in pairs]
    multisets += list(itertools.combinations_with_replacement(pairs, 2))

    for source, state, frozen, audited, scanned, divergences in itertools.product(
        BASE_SOURCES, BASE_STATES, (None, "2026-01-01"), (False, True),
        (False, True), (0, 1),
    ):
        if state == "rebuilt" and source != "dv_html":
            continue
        if state == "read" and source != "dv_pdf":
            continue
        if state in ("rebuilt", "read") and frozen is None:
            continue
        if state == "snapshot" and divergences != 0:
            continue
        for events in multisets:
            if state != "snapshot" and any(
                applied == "verified" for _, applied in events
            ):
                continue
            yield dict(
                base_source=source,
                base_state=state,
                base_frozen_at=frozen,
                base_audited=audited,
                chain_scan_complete=scanned,
                divergences_unadjudicated=divergences,
                events=events,
            )


def test_the_grade_procedure_is_total(cmap):
    seen = set()
    count = 0
    for inputs in valid_inputs(cmap):
        grade, pending = cmap.derive_grade(**inputs)
        assert grade in {"A", "B", "B-pending", "C", "none"}
        assert isinstance(pending, tuple)
        seen.add(grade)
        count += 1
    # The exact size of the enumerated space, pinned so that a change to
    # the domain constraints is visible rather than silent.
    assert count == 6352
    assert seen == {"A", "B", "B-pending", "C", "none"}


def test_rule_zero_holds_a_rebuilt_act_out_of_the_corpus(cmap):
    for inputs in valid_inputs(cmap):
        if (
            inputs["base_state"] in ("rebuilt", "read")
            and inputs["divergences_unadjudicated"] > 0
        ):
            assert cmap.derive_grade(**inputs)[0] == "none"


def test_anything_offline_in_scope_is_grade_c(cmap):
    for inputs in valid_inputs(cmap):
        grade, _ = cmap.derive_grade(**inputs)
        if grade == "none":
            continue
        offline = inputs["base_source"] == "dv_offline" or any(
            source == "dv_offline" for source, _ in inputs["events"]
        )
        assert (grade == "C") == offline


def test_grade_a_implies_every_condition_of_rule_two(cmap):
    for inputs in valid_inputs(cmap):
        if cmap.derive_grade(**inputs)[0] != "A":
            continue
        assert inputs["base_state"] == "rebuilt"
        assert inputs["base_source"] == "dv_html"
        assert inputs["chain_scan_complete"]
        assert inputs["divergences_unadjudicated"] == 0
        for source, applied in inputs["events"]:
            assert source == "dv_html"
            assert applied in ("replayed", "not_incorporated")


def test_pending_items_are_named_exactly_when_something_is_open(cmap):
    for inputs in valid_inputs(cmap):
        grade, pending = cmap.derive_grade(**inputs)
        if grade == "B-pending":
            assert pending, inputs
        if grade in ("A", "B"):
            assert pending == (), inputs


def test_the_pending_items_come_from_the_fixed_vocabulary(cmap):
    allowed = {
        "events_pending",
        "chain_scan",
        "promulgation_unlocated",
        "promulgation_unknown",
        "base_audit",
        "freeze",
    }
    for inputs in valid_inputs(cmap):
        _, pending = cmap.derive_grade(**inputs)
        assert set(pending) <= allowed
        assert list(pending) == sorted(set(pending), key=list(pending).index)


def test_a_not_incorporated_event_never_blocks_a_grade(cmap):
    grade, pending = cmap.derive_grade(
        base_source="dv_html",
        base_state="snapshot",
        base_frozen_at="2026-01-01",
        base_audited=True,
        chain_scan_complete=True,
        divergences_unadjudicated=0,
        events=(("dv_html", "not_incorporated"), ("dv_html", "verified")),
    )
    assert grade == "B"
    assert pending == ()


def test_the_p0_inputs_can_only_produce_b_pending_or_c(cmap):
    # In P0 every event is `pending`, the base is a `snapshot`, nothing is
    # frozen, nothing is audited and the body scan has not run. Rules 1
    # and 3 are the only ones that can fire.
    for base_source in BASE_SOURCES:
        for events in ((), (("dv_html", "pending"),), (("dv_offline", "pending"),)):
            grade, pending = cmap.derive_grade(
                base_source=base_source,
                base_state="snapshot",
                base_frozen_at=None,
                base_audited=False,
                chain_scan_complete=False,
                divergences_unadjudicated=0,
                events=events,
            )
            assert grade in ("B-pending", "C")
            assert pending
