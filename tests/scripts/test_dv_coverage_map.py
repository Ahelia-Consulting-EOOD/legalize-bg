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
        "estado: vigente\n"
        "fecha_publicacion: '2020-12-01'\n"
        "dv_issue: '99'\n"
        "dv_year: 2020\n"
        "amendment_history:\n- dv: 99/2020\n  date: '2020-12-01'\n",
    )
    # An act whose base resolves to a material and whose one event does
    # not: the case that has a `dv_identifier` AND an unresolved row.
    synthetic_act(
        root,
        "laws",
        "zakon-za-probniya-sluchay",
        "titulo: ЗАКОН ЗА ПРОБНИЯ СЛУЧАЙ\n"
        "rango: закон\n"
        "estado: vigente\n"
        "fecha_publicacion: '2019-07-02'\n"
        "dv_issue: '52'\n"
        "dv_year: 2019\n"
        "amendment_history:\n"
        "- dv: 52/2019\n  date: '2019-07-02'\n"
        "- dv: 32/2026\n  date: '2026-04-01'\n",
    )
    # `fecha_publicacion` but no ДВ citation: the 39 acts whose three
    # output rows used to disagree with one another.
    synthetic_act(
        root,
        "laws",
        "zakon-bez-tsitirane",
        "titulo: ЗАКОН БЕЗ ЦИТИРАНЕ\n"
        "rango: закон\n"
        "estado: vigente\n"
        "fecha_publicacion: '2015-05-05'\n"
        "amendment_history:\n- date: '2015-05-05'\n",
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
    (52, 2, 6002, "Народно събрание", "ЗАКОН ЗА ПРОБНИЯ СЛУЧАЙ", 10),
    (100, 1, 242220, "Народно събрание", "ЗАКОН ЗА ОБЩЕСТВЕНИЯ ТРАНСПОРТ", 2),
    (
        100, 2, 242221, "Народно събрание",
        "Закон за изменение и допълнение на Закона за задълженията и договорите",
        12,
    ),
    (100, 3, 242222, "Народно събрание", "Закон за ратифициране на трето нещо", 20),
    (
        100, 4, 242223, "Народно събрание",
        "Закон за отмяна на Закона за събранията, митингите и манифестациите",
        26,
    ),
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


def test_the_map_writes_seven_files_and_no_corpus_file(outputs, corpus):
    assert sorted(p.name for p in outputs.iterdir()) == [
        "acts-summary.csv",
        "chain-omissions.csv",
        "coverage-map.csv",
        "estado-disputes.csv",
        "pdf-era-inventory.csv",
        "report.md",
        "unresolved.csv",
    ]
    # The map is a research artifact. Nothing under the corpus moved.
    assert sorted(p.name for p in (corpus / "laws").iterdir()) == [
        "zakon-bez-tsitirane.md",
        "zakon-za-lipsvashtiya-broy.md",
        "zakon-za-obshtestveniya-transport.md",
        "zakon-za-probniya-sluchay.md",
        "zakon-za-sabraniyata-mitingite-i-manifestatsiite.md",
        "zakon-za-zadalzheniyata-i-dogovorite.md",
    ]


def test_every_output_is_utf8_without_escapes(outputs):
    for path in outputs.iterdir():
        text = path.read_text(encoding="utf-8")
        assert "\\u04" not in text


def test_the_order_is_deterministic(cmap, corpus, tables, tmp_path):
    # Two runs in ONE process cannot catch a set-iteration dependency,
    # since hash randomisation is per process. The resolver removes the
    # one such dependency at the source by iterating `title_variants`
    # sorted, so `Resolution.candidates` reads the same in every run.
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
                 "unresolved.csv", "pdf-era-inventory.csv", "estado-disputes.csv"):
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
    # HTML-era lengths measured here: 6 in бр. 24/2010, 6 in бр. 52/2019,
    # and 10, 8, 6 in бр. 32/2026. The last material of each issue has no
    # next start page and the issue table carries no page count, so it
    # contributes none. The median for a закон is 6, applied to the two
    # PDF-era rows of this act: its 1990 base and its 1998 event.
    row = rows(
        outputs / "acts-summary.csv",
        law_id="zakon-za-sabraniyata-mitingite-i-manifestatsiite",
    )[0]
    assert row["pdf_pages_estimate"] == "12"


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
    # ЗОТ's own promulgation, and the 2010 ЗИД of the assemblies act, are
    # both in their acts' chains already.
    assert not rows(
        outputs / "chain-omissions.csv", law_id="zakon-za-obshtestveniya-transport"
    )
    assert not rows(
        outputs / "chain-omissions.csv", law_id="zakon-za-probniya-sluchay"
    )
    found = rows(
        outputs / "chain-omissions.csv",
        law_id="zakon-za-sabraniyata-mitingite-i-manifestatsiite",
    )
    assert [(row["dv_year"], row["id_mat"]) for row in found] == [("2026", "242223")]


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
        "zakon-bez-tsitirane",
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
    # Six laws, one of them grade C (ЗЗД, promulgated in 1950).
    assert "| laws | 5 | 1 |" in section


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

    for source, state, frozen, audited, scanned, divergences, cited in (
        itertools.product(
            BASE_SOURCES, BASE_STATES, (None, "2026-01-01"), (False, True),
            (False, True), (0, 1), (True, False),
        )
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
                promulgation_cited=cited,
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
    assert count == 12704
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


# --- the PDF-era inventory (D-064 item 6) --------------------------------


def test_the_inventory_holds_one_row_per_pdf_era_issue_and_a_total(outputs):
    found = rows(outputs / "pdf-era-inventory.csv")
    assert [(row["year"], row["number"]) for row in found] == [
        ("1990", "10"), ("1998", "11"), ("TOTAL", ""),
    ]


def test_the_html_era_issues_are_not_in_the_inventory(outputs):
    # The inventory is the reading budget for the era with no materials
    # list. An issue that has one is not part of it.
    numbers = {(row["year"], row["number"]) for row in rows(outputs / "pdf-era-inventory.csv")}
    assert ("2010", "24") not in numbers
    assert ("2026", "32") not in numbers


def test_the_boundary_issue_is_a_parameter(cmap, corpus, tables, tmp_path):
    # бр. 42/2005 is the last issue before per-material HTML begins, and
    # the exact boundary is a probe result rather than a certainty, so it
    # moves without touching the code.
    issues, materials = tables
    out = tmp_path / "narrow"
    cmap.main(
        [
            "--corpus", str(corpus),
            "--issues", str(issues),
            "--materials", str(materials),
            "--out", str(out),
            "--pdf-era-end", "1995:1",
        ]
    )
    assert [(row["year"], row["number"]) for row in rows(out / "pdf-era-inventory.csv")] == [
        ("1990", "10"), ("TOTAL", ""),
    ]


def test_the_inventory_carries_the_issue_identity(outputs):
    row = rows(outputs / "pdf-era-inventory.csv", year="1990")[0]
    assert row["number"] == "10"
    assert row["date"] == "1990-02-02"
    assert row["id_obj"] == "10"
    assert row["extraordinary"] == "false"


def test_the_inventory_counts_the_corpus_rows_that_cite_the_issue(outputs):
    # бр. 10/1990 is the promulgation of the assemblies act and бр. 11/1998
    # one of its events: one corpus row each.
    for number in ("10", "11"):
        row = rows(outputs / "pdf-era-inventory.csv", number=number)[0]
        assert row["corpus_events_citing"] == "1"


def test_the_page_model_is_measured_on_the_html_era(outputs):
    # Table of contents pages per issue = the first material's start page
    # minus one: 2 in бр. 24/2010, 3 in бр. 52/2019, 1 in бр. 32/2026.
    # The median is 2, and it is what every PDF-era row carries.
    # Issue pages = the last material's start page plus the median
    # material length (6): 15, 16 and 32, whose median is 16.
    row = rows(outputs / "pdf-era-inventory.csv", number="10")[0]
    assert row["toc_pages_est"] == "2"
    assert row["issue_pages_est"] == "16"
    # One закон cites this issue and the median закон is 6 pages long.
    assert row["corpus_material_pages_est"] == "6"


def test_the_inventory_total_sums_the_three_estimates(outputs):
    total = rows(outputs / "pdf-era-inventory.csv", year="TOTAL")[0]
    assert total["corpus_events_citing"] == "2"
    assert total["toc_pages_est"] == "4"
    assert total["corpus_material_pages_est"] == "12"
    assert total["issue_pages_est"] == "32"


def test_the_report_carries_the_token_cost_table(outputs):
    text = (outputs / "report.md").read_text(encoding="utf-8")
    section = text.split("## PDF-era inventory", 1)[1].split("\n## ", 1)[0]
    assert "| PDF-era issues | 2 |" in section
    assert "| Issues cited by the corpus | 2 |" in section
    assert "| Estimated table-of-contents pages | 4 |" in section
    assert "| Estimated corpus-referenced material pages | 12 |" in section
    assert "| Estimated issue pages | 32 |" in section


def test_the_report_gives_the_toc_distribution_and_calls_it_an_estimate(outputs):
    text = (outputs / "report.md").read_text(encoding="utf-8")
    assert "estimate" in text
    section = text.split("## PDF-era inventory", 1)[1].split("\n## ", 1)[0]
    # Three HTML-era issues measured: 1, 2, 3 pages of contents.
    assert "3 issues" in section
    assert "minimum 1" in section
    assert "median 2" in section
    assert "maximum 3" in section


# --- dv_identifier (D-064 item 4) ----------------------------------------


def test_an_act_whose_base_resolves_carries_its_dv_identifier(outputs):
    row = rows(
        outputs / "acts-summary.csv", law_id="zakon-za-obshtestveniya-transport"
    )[0]
    assert row["dv_identifier"] == "dv-242220"


def test_an_act_whose_base_does_not_resolve_carries_none(outputs):
    for law_id in (
        "zakon-za-zadalzheniyata-i-dogovorite",
        "zakon-za-sabraniyata-mitingite-i-manifestatsiite",
        "zakon-za-lipsvashtiya-broy",
    ):
        assert rows(outputs / "acts-summary.csv", law_id=law_id)[0]["dv_identifier"] == ""


def test_the_dv_identifier_reaches_the_unresolved_rows(outputs):
    # This act's base is a Gazette material and its 2026 event is not, so
    # the row that reports the gap can still name the act on the ДВ side.
    found = rows(
        outputs / "unresolved.csv",
        kind="unlocated_event",
        law_id="zakon-za-probniya-sluchay",
    )
    assert [row["dv_identifier"] for row in found] == ["dv-6002"]


def test_a_material_nobody_claimed_has_no_dv_identifier(outputs):
    found = rows(outputs / "unresolved.csv", kind="unattributed_material")
    assert found
    assert {row["dv_identifier"] for row in found} == {""}


# --- estado disputes ------------------------------------------------------


def test_a_gazette_repeal_of_an_act_the_corpus_calls_current_is_a_dispute(outputs):
    found = rows(outputs / "estado-disputes.csv")
    assert len(found) == 1
    row = found[0]
    assert row["pass"] == "title"
    assert row["law_id"] == "zakon-za-sabraniyata-mitingite-i-manifestatsiite"
    assert row["dv_year"] == "2026"
    assert row["dv_number"] == "32"
    assert row["id_mat"] == "242223"
    assert row["corpus_estado"] == "vigente"
    assert row["finding"] == "repeal"


def test_an_ordinary_amendment_is_not_an_estado_dispute(outputs):
    # бр. 24/2010 amends the same act. Amending is not repealing.
    assert not rows(outputs / "estado-disputes.csv", id_mat="5001")


def test_the_repeal_is_also_a_chain_omission(outputs):
    # Two signals, two files: the Gazette repealed the act, and lex.bg's
    # chain does not know the issue that did it.
    assert rows(outputs / "chain-omissions.csv", id_mat="242223")


def test_a_repeal_title_is_labelled_as_one(outputs):
    row = rows(outputs / "chain-omissions.csv", id_mat="242223")[0]
    assert row["title_kind"] == "repeal"


# --- I1: one definition of „the promulgation was cited“ -------------------


def test_the_three_files_agree_about_an_act_that_cites_no_issue(outputs):
    # `fecha_publicacion` is a mandatory Legalize field every act carries,
    # so it cannot stand in for a citation. What can be located on the ДВ
    # side is an issue, and this act names none. The three files used to
    # give three answers about the same 39 acts: `promulgation_unknown` in
    # the coverage map, `promulgation_unlocated` in the summary, and
    # absent from the unresolved list altogether.
    law = "zakon-bez-tsitirane"
    summary = rows(outputs / "acts-summary.csv", law_id=law)[0]
    assert "promulgation_unknown" in summary["pending_items"].split(";")
    assert "promulgation_unlocated" not in summary["pending_items"]
    assert rows(outputs / "unresolved.csv", kind="promulgation_unknown", law_id=law)
    base = rows(outputs / "coverage-map.csv", law_id=law, row_kind="base")[0]
    assert base["source"] == "unlocated"


def test_an_act_that_cites_an_issue_nobody_holds_is_unlocated_not_unknown(outputs):
    # The other side of the same predicate: this act DOES cite бр. 99/2020.
    summary = rows(outputs / "acts-summary.csv", law_id="zakon-za-lipsvashtiya-broy")[0]
    assert "promulgation_unlocated" in summary["pending_items"].split(";")
    assert "promulgation_unknown" not in summary["pending_items"]
    assert not rows(
        outputs / "unresolved.csv",
        kind="promulgation_unknown",
        law_id="zakon-za-lipsvashtiya-broy",
    )


# --- M2, M3, M7: the smaller findings ------------------------------------


def test_an_acts_own_promulgating_material_is_never_a_chain_omission(outputs):
    # An act sourced from the ДВ side has no lex.bg document and so no
    # `amendment_history` at all, which is the D-064 item 4 shape the
    # `dv_identifier` column exists for. Its own promulgation must not be
    # reported as an event its chain does not know.
    for row in rows(outputs / "chain-omissions.csv"):
        summary = rows(outputs / "acts-summary.csv", law_id=row["law_id"])[0]
        assert summary["dv_identifier"] != f"dv-{row['id_mat']}"


def test_an_event_row_is_not_given_a_base_uncertainty(outputs):
    # `promulgation_unknown` is a statement about a base. An event whose
    # issue reference cannot be read is `event_reference_unknown`.
    for row in rows(outputs / "coverage-map.csv", row_kind="event"):
        assert "promulgation_unknown" not in row["uncertainty"]


def test_a_repeal_of_an_act_with_no_estado_is_not_a_dispute(cmap, tmp_path, corpus,
                                                            tables):
    # A dispute is a contradiction. „The corpus says nothing“ contradicts
    # nothing, and filing it with an empty `corpus_estado` is noise.
    synthetic_act(
        corpus,
        "laws",
        "zakon-bez-estado",
        "titulo: ЗАКОН БЕЗ ЕСТАДО\nrango: закон\nfecha_publicacion: '2001-01-01'\n",
    )
    issues, materials = tables
    with materials.open("a", encoding="utf-8") as handle:
        handle.write(
            json.dumps(
                {
                    "id_obj": 100, "issue_year": 2026, "issue_number": 32,
                    "issue_date": "2026-04-01", "status": "ok", "position": 5,
                    "id_mat": 242224, "section": "Народно събрание",
                    "title": "Закон за отмяна на Закона без естадо",
                    "start_page": 30,
                },
                ensure_ascii=False,
            )
            + "\n"
        )
    out = tmp_path / "no-estado"
    cmap.main(
        [
            "--corpus", str(corpus), "--issues", str(issues),
            "--materials", str(materials), "--out", str(out),
        ]
    )
    assert not rows(out / "estado-disputes.csv", law_id="zakon-bez-estado")


# --- M1: the enumeration varies every input ------------------------------


def test_the_enumeration_varies_promulgation_cited(cmap):
    seen = set()
    for inputs in valid_inputs(cmap):
        seen.add(inputs["promulgation_cited"])
    assert seen == {True, False}


def test_an_uncited_promulgation_is_named_as_such_by_the_procedure(cmap):
    _, pending = cmap.derive_grade(
        base_source="unlocated",
        base_state="snapshot",
        base_frozen_at=None,
        base_audited=False,
        chain_scan_complete=False,
        divergences_unadjudicated=0,
        events=(),
        promulgation_cited=False,
    )
    assert "promulgation_unknown" in pending
    assert "promulgation_unlocated" not in pending
