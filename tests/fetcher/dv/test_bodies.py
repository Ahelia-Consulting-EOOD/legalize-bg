"""The `bodies` subcommand: the bulk body fetch the body scan needs.

The coverage map's ДВ-side pass reads the BODY of every HTML-era material
in the law and ministerial sections, not only its title, because most
cross-act amendments ride in another act's преходни и заключителни
разпоредби. That is roughly forty-two thousand fetches at one request per
second, so every property tested here is about not paying that bill
twice and not turning an outage into a permanent hole in the cache.

Every test runs offline against `FakeSession` and a temporary cache.
"""

import json
import logging

from fetcher.dv.__main__ import main
from fetcher.dv.materials import MATERIAL_PATH

from .conftest import FakeSession
from .test_materials import ERROR_PAGE

MINISTRY = "Министерство на здравеопазването"
MULTI_MINISTRY = (
    "Министерство на регионалното развитие и благоустройството, "
    "Министерство на вътрешните работи"
)
REGULATOR = "Комисия за регулиране на съобщенията"
CEC = "Централна избирателна комисия"


def write_materials(tmp_path, *rows, name="materials.jsonl"):
    """A materials JSONL file. Each row is (id_obj, position, id_mat, section)."""
    path = tmp_path / name
    with path.open("w", encoding="utf-8") as fh:
        for id_obj, position, id_mat, section in rows:
            fh.write(
                json.dumps(
                    {
                        "id_obj": id_obj,
                        "issue_year": 2016,
                        "issue_number": 70,
                        "issue_date": "2016-09-20",
                        "status": "ok",
                        "position": position,
                        "id_mat": id_mat,
                        "section": section,
                        "title": f"Материал {id_mat}",
                        "start_page": position,
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )
    return path


def requested(session):
    return [params["idMat"] for url, params in session.gets if url.endswith(MATERIAL_PATH)]


def bodies_session(*id_mats, body):
    return FakeSession(by_param={("idMat", m): body for m in id_mats})


# --- which materials the sweep is for -------------------------------------


def test_the_default_sections_are_parliament_the_council_and_the_ministries(
    tmp_path, material_html
):
    # The official section also carries the courts, the CEC and the sector
    # regulators. Their materials are decisions and rules, not acts of the
    # corpus, and reading their bodies would add thousands of requests for
    # nothing.
    materials = write_materials(
        tmp_path,
        (1, 1, 101, "Народно събрание"),
        (1, 2, 102, "Министерски съвет"),
        (1, 3, 103, MINISTRY),
        (1, 4, 104, MULTI_MINISTRY),
        (1, 5, 105, REGULATOR),
        (1, 6, 106, CEC),
        (1, 7, 107, "Конституционен съд"),
    )
    session = bodies_session(101, 102, 103, 104, body=material_html)
    assert (
        main(
            [
                "bodies",
                "--materials", str(materials),
                "--cache-dir", str(tmp_path / "cache"),
            ],
            session=session,
        )
        == 0
    )
    assert requested(session) == [101, 102, 103, 104]
    assert sorted(p.name for p in (tmp_path / "cache").iterdir()) == [
        "101.html", "102.html", "103.html", "104.html",
    ]


def test_sections_widens_the_default_set(tmp_path, material_html):
    materials = write_materials(
        tmp_path,
        (1, 1, 101, "Народно събрание"),
        (1, 2, 105, REGULATOR),
        (1, 3, 106, CEC),
    )
    session = bodies_session(101, 106, body=material_html)
    assert (
        main(
            [
                "bodies",
                "--materials", str(materials),
                "--cache-dir", str(tmp_path / "cache"),
                "--sections", "Централна избирателна комисия",
            ],
            session=session,
        )
        == 0
    )
    assert requested(session) == [101, 106]


def test_sections_all_takes_every_section(tmp_path, material_html):
    materials = write_materials(
        tmp_path,
        (1, 1, 101, "Народно събрание"),
        (1, 2, 105, REGULATOR),
        (1, 3, 107, "Конституционен съд"),
    )
    session = bodies_session(101, 105, 107, body=material_html)
    main(
        [
            "bodies",
            "--materials", str(materials),
            "--cache-dir", str(tmp_path / "cache"),
            "--sections", "all",
        ],
        session=session,
    )
    assert requested(session) == [101, 105, 107]


def test_rows_that_are_not_materials_are_skipped(tmp_path, material_html):
    # The materials file also holds one row per empty issue, per error page
    # and per unreadable page. None of them names a material.
    materials = tmp_path / "materials.jsonl"
    materials.write_text(
        "\n".join(
            json.dumps(row, ensure_ascii=False)
            for row in [
                {"id_obj": 1, "status": "empty"},
                {"id_obj": 2, "status": "error_page"},
                {"id_obj": 3, "status": "unrecognized"},
                {
                    "id_obj": 4,
                    "status": "ok",
                    "position": 1,
                    "id_mat": 101,
                    "section": "Народно събрание",
                },
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    session = bodies_session(101, body=material_html)
    assert (
        main(
            [
                "bodies",
                "--materials", str(materials),
                "--cache-dir", str(tmp_path / "cache"),
            ],
            session=session,
        )
        == 0
    )
    assert requested(session) == [101]


# --- deterministic order --------------------------------------------------


def test_the_order_is_by_issue_then_position(tmp_path, material_html):
    # Two runs over the same file must ask for the same things in the same
    # order, so a halted run resumes where the log says it stopped.
    materials = write_materials(
        tmp_path,
        (20, 2, 202, "Народно събрание"),
        (10, 3, 103, "Народно събрание"),
        (20, 1, 201, "Народно събрание"),
        (10, 1, 101, "Народно събрание"),
    )
    session = bodies_session(101, 103, 201, 202, body=material_html)
    main(
        [
            "bodies",
            "--materials", str(materials),
            "--cache-dir", str(tmp_path / "cache"),
        ],
        session=session,
    )
    assert requested(session) == [101, 103, 201, 202]


def test_limit_stops_after_n_materials(tmp_path, material_html):
    materials = write_materials(
        tmp_path,
        (1, 1, 101, "Народно събрание"),
        (1, 2, 102, "Народно събрание"),
        (1, 3, 103, "Народно събрание"),
    )
    session = bodies_session(101, 102, body=material_html)
    main(
        [
            "bodies",
            "--materials", str(materials),
            "--cache-dir", str(tmp_path / "cache"),
            "--limit", "2",
        ],
        session=session,
    )
    assert requested(session) == [101, 102]


# --- the cache is the resume ----------------------------------------------


def test_a_cached_body_costs_no_request(tmp_path, material_html):
    materials = write_materials(
        tmp_path,
        (1, 1, 101, "Народно събрание"),
        (1, 2, 102, "Народно събрание"),
    )
    cache = tmp_path / "cache"
    cache.mkdir()
    (cache / "101.html").write_text(material_html, encoding="utf-8")
    session = bodies_session(102, body=material_html)
    main(
        ["bodies", "--materials", str(materials), "--cache-dir", str(cache)],
        session=session,
    )
    assert requested(session) == [102]


def test_a_second_run_asks_for_nothing(tmp_path, material_html):
    materials = write_materials(
        tmp_path,
        (1, 1, 101, "Народно събрание"),
        (1, 2, 102, "Народно събрание"),
    )
    cache = tmp_path / "cache"
    first = bodies_session(101, 102, body=material_html)
    main(
        ["bodies", "--materials", str(materials), "--cache-dir", str(cache)],
        session=first,
    )
    second = FakeSession()
    assert (
        main(
            ["bodies", "--materials", str(materials), "--cache-dir", str(cache)],
            session=second,
        )
        == 0
    )
    assert second.gets == []


def test_a_stub_left_in_the_cache_is_re_fetched(tmp_path, material_html):
    # A cache written before the stub guard existed can hold „недостъпен“
    # bodies. The default run reads what it finds and heals them.
    materials = write_materials(tmp_path, (1, 1, 101, "Народно събрание"))
    cache = tmp_path / "cache"
    cache.mkdir()
    (cache / "101.html").write_text(ERROR_PAGE, encoding="utf-8")
    session = bodies_session(101, body=material_html)
    main(
        ["bodies", "--materials", str(materials), "--cache-dir", str(cache)],
        session=session,
    )
    assert requested(session) == [101]
    assert (cache / "101.html").read_text(encoding="utf-8") == material_html


def test_resume_trusts_the_cache_by_name(tmp_path, material_html):
    # Over forty-two thousand rows the default run reads every cached body
    # to check it. `--resume` skips that read, which is what a sweep
    # continued the next morning wants; the price is that it also skips a
    # stub left behind by an older run.
    materials = write_materials(tmp_path, (1, 1, 101, "Народно събрание"))
    cache = tmp_path / "cache"
    cache.mkdir()
    (cache / "101.html").write_text(ERROR_PAGE, encoding="utf-8")
    session = FakeSession()
    assert (
        main(
            [
                "bodies",
                "--materials", str(materials),
                "--cache-dir", str(cache),
                "--resume",
            ],
            session=session,
        )
        == 0
    )
    assert session.gets == []


# --- an outage is not a corpus of missing materials -----------------------


def test_a_run_of_stubs_halts_the_sweep(tmp_path, material_html):
    materials = write_materials(
        tmp_path, *[(1, i, 100 + i, "Народно събрание") for i in range(1, 9)]
    )
    session = FakeSession(get_bodies={MATERIAL_PATH: ERROR_PAGE})
    assert (
        main(
            [
                "bodies",
                "--materials", str(materials),
                "--cache-dir", str(tmp_path / "cache"),
            ],
            session=session,
        )
        != 0
    )
    assert requested(session) == [101, 102, 103, 104, 105]
    assert not (tmp_path / "cache").exists() or list((tmp_path / "cache").iterdir()) == []


def test_the_stub_run_limit_is_configurable(tmp_path):
    materials = write_materials(
        tmp_path, *[(1, i, 100 + i, "Народно събрание") for i in range(1, 9)]
    )
    session = FakeSession(get_bodies={MATERIAL_PATH: ERROR_PAGE})
    assert (
        main(
            [
                "bodies",
                "--materials", str(materials),
                "--cache-dir", str(tmp_path / "cache"),
                "--max-consecutive-errors", "2",
            ],
            session=session,
        )
        != 0
    )
    assert requested(session) == [101, 102]


def test_an_isolated_missing_material_does_not_halt(tmp_path, material_html):
    materials = write_materials(
        tmp_path, *[(1, i, 100 + i, "Народно събрание") for i in range(1, 7)]
    )
    session = FakeSession(
        by_param={
            ("idMat", 101): material_html,
            ("idMat", 102): ERROR_PAGE,
            ("idMat", 103): material_html,
            ("idMat", 104): ERROR_PAGE,
            ("idMat", 105): material_html,
            ("idMat", 106): ERROR_PAGE,
        }
    )
    assert (
        main(
            [
                "bodies",
                "--materials", str(materials),
                "--cache-dir", str(tmp_path / "cache"),
            ],
            session=session,
        )
        == 0
    )
    assert requested(session) == [101, 102, 103, 104, 105, 106]
    assert sorted(p.name for p in (tmp_path / "cache").iterdir()) == [
        "101.html", "103.html", "105.html",
    ]


def test_the_halt_names_the_last_material_that_answered(tmp_path, material_html, caplog):
    materials = write_materials(
        tmp_path, *[(1, i, 100 + i, "Народно събрание") for i in range(1, 9)]
    )
    session = FakeSession(
        by_param={("idMat", 101): material_html},
        get_bodies={MATERIAL_PATH: ERROR_PAGE},
    )
    with caplog.at_level(logging.ERROR, logger="fetcher.dv"):
        main(
            [
                "bodies",
                "--materials", str(materials),
                "--cache-dir", str(tmp_path / "cache"),
            ],
            session=session,
        )
    message = "\n".join(r.getMessage() for r in caplog.records)
    assert "101" in message
    assert "--resume" in message


# --- progress -------------------------------------------------------------


def test_progress_is_logged_every_hundred_materials(tmp_path, material_html, caplog):
    rows = [(1, i, 1000 + i, "Народно събрание") for i in range(1, 251)]
    materials = write_materials(tmp_path, *rows)
    session = bodies_session(*[1000 + i for i in range(1, 251)], body=material_html)
    with caplog.at_level(logging.INFO, logger="fetcher.dv"):
        main(
            [
                "bodies",
                "--materials", str(materials),
                "--cache-dir", str(tmp_path / "cache"),
            ],
            session=session,
        )
    progress = [r.getMessage() for r in caplog.records if "elapsed" in r.getMessage()]
    assert len(progress) == 2
    assert "100/250" in progress[0]
    assert "200/250" in progress[1]
    assert "eta" in progress[0]


def test_a_missing_material_does_not_swallow_the_progress_line(
    tmp_path, material_html, caplog
):
    # Progress is the only sign of life a twelve-hour run gives. If the
    # hundredth material happens to be one the site does not hold, the
    # line for that hundred must still appear.
    rows = [(1, i, 1000 + i, "Народно събрание") for i in range(1, 121)]
    materials = write_materials(tmp_path, *rows)
    bodies = {("idMat", 1000 + i): material_html for i in range(1, 121)}
    bodies[("idMat", 1100)] = ERROR_PAGE  # the hundredth material
    session = FakeSession(by_param=bodies)
    with caplog.at_level(logging.INFO, logger="fetcher.dv"):
        main(
            [
                "bodies",
                "--materials", str(materials),
                "--cache-dir", str(tmp_path / "cache"),
            ],
            session=session,
        )
    progress = [r.getMessage() for r in caplog.records if "elapsed" in r.getMessage()]
    assert len(progress) == 1
    assert "100/120" in progress[0]


def test_the_run_reports_what_it_fetched_and_what_it_skipped(
    tmp_path, material_html, caplog
):
    materials = write_materials(
        tmp_path,
        (1, 1, 101, "Народно събрание"),
        (1, 2, 102, "Народно събрание"),
        (1, 3, 105, REGULATOR),
    )
    cache = tmp_path / "cache"
    cache.mkdir()
    (cache / "101.html").write_text(material_html, encoding="utf-8")
    session = bodies_session(102, body=material_html)
    with caplog.at_level(logging.INFO, logger="fetcher.dv"):
        main(
            ["bodies", "--materials", str(materials), "--cache-dir", str(cache)],
            session=session,
        )
    summary = [r.getMessage() for r in caplog.records if "cached" in r.getMessage()]
    assert summary
    assert "1 fetched" in summary[-1]
    assert "1 cached" in summary[-1]


def test_a_missing_materials_file_is_rejected(tmp_path):
    try:
        main(
            [
                "bodies",
                "--materials", str(tmp_path / "nope.jsonl"),
                "--cache-dir", str(tmp_path / "cache"),
            ],
            session=FakeSession(),
        )
    except SystemExit as exc:
        assert "nope.jsonl" in str(exc)
    else:  # pragma: no cover - the call above must raise
        raise AssertionError("a missing materials file must stop the run")
