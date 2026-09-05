"""Issue-contents and material-page parsing against the captured fixtures."""

import pytest

from fetcher.dv.materials import (
    MATERIALS_PATH,
    MATERIAL_PATH,
    MaterialHeader,
    MaterialRow,
    classify_page,
    fetch_material,
    fetch_materials,
    material_body_html,
    parse_material_header,
    parse_materials,
)

from .conftest import FakeSession, read_fixture

#: The 489-byte body dv.parliament.bg serves, with status 500, for an
#: idObj that does not exist. Captured live for idObj 6000 on 2026-09-05.
ERROR_PAGE = read_fixture("materiali-idObj6000-error.html")


# --- issue contents -------------------------------------------------------


def test_issue_6121_has_eighteen_materials(materials_html):
    rows = parse_materials(materials_html)
    assert len(rows) == 18
    assert all(isinstance(r, MaterialRow) for r in rows)


def test_first_material_fields(materials_html):
    first = parse_materials(materials_html)[0]
    assert first.id_mat == 107486
    assert first.section == "Народно събрание"
    assert first.start_page == 2
    assert first.position == 1
    assert first.title.startswith(
        "Закон за ратифициране на Споразумението за предоставяне"
    )


def test_fourth_material_is_the_apk_amendment(materials_html):
    fourth = parse_materials(materials_html)[3]
    assert fourth.position == 4
    assert fourth.id_mat == 107549
    assert fourth.start_page == 12
    assert fourth.section == "Народно събрание"
    assert (
        fourth.title
        == "Закон за изменение и допълнение на Административнопроцесуалния кодекс"
    )


def test_sections_change_down_the_issue(materials_html):
    rows = parse_materials(materials_html)
    assert rows[4].section == "Министерски съвет"
    assert rows[4].id_mat == 107598
    assert rows[4].start_page == 14
    assert rows[9].section == "Министерство на здравеопазването"
    assert rows[-1].section == "Централна избирателна комисия"
    assert rows[-1].id_mat == 107575
    assert rows[-1].start_page == 116


def test_positions_are_one_based_and_contiguous(materials_html):
    rows = parse_materials(materials_html)
    assert [r.position for r in rows] == list(range(1, 19))


def test_an_issue_with_no_html_materials_parses_to_nothing(materials_empty_html):
    assert parse_materials(materials_empty_html) == []


# --- classifying an issue-contents response -------------------------------


def test_the_stub_is_classified_as_an_error_page(error_page_html):
    assert classify_page(error_page_html) == "error_page"
    # A stub, not a page: half a kilobyte with no result table in it.
    assert len(error_page_html) < 1000
    assert "Сайтът е недостъпен в момента" in error_page_html


def test_the_stub_is_recognised_by_its_title_alone():
    # The Bulgarian sentence may be reworded; the JSF error view's title
    # is the second, independent marker.
    assert (
        classify_page("<html><head><title>ErrorPage</title></head></html>")
        == "error_page"
    )


def test_an_issue_with_materials_is_classified_as_materials(materials_html):
    assert classify_page(materials_html) == "materials"


def test_an_issue_that_lists_nothing_is_classified_as_empty(materials_empty_html):
    # „Намерени резултати: 0“ is a true statement about the issue: it is
    # online as a whole-issue PDF only.
    assert classify_page(materials_empty_html) == "empty"


def test_a_renamed_result_table_is_unrecognized_rather_than_empty(materials_html):
    # The page still says it found eighteen materials; the parser reads
    # none. That is a defect in this module, not a fact about the issue,
    # and calling it „empty“ or „error_page“ would write a false claim
    # about the Gazette for every one of the 4,146 issues.
    mutated = materials_html.replace("material_form:dataTable1", "material_form:grid1")
    assert parse_materials(mutated) == []
    assert classify_page(mutated) == "unrecognized"


def test_a_page_without_the_result_count_is_unrecognized(materials_html):
    mutated = materials_html.replace("Намерени резултати", "Found results")
    assert classify_page(mutated) == "unrecognized"


def test_markup_from_somewhere_else_entirely_is_unrecognized():
    assert classify_page("<html><body>hello</body></html>") == "unrecognized"


def test_a_short_listing_under_a_larger_count_is_unrecognized(materials_html):
    # One row's link renamed, so seventeen of the eighteen parse. The
    # page's own count and the parse disagree, which is the signal: a
    # silent partial read is the shape D-058 keeps finding.
    mutated = materials_html.replace("?idMat=107486", "?idDoc=107486")
    assert len(parse_materials(mutated)) == 17
    assert classify_page(mutated) == "unrecognized"


# --- material header ------------------------------------------------------


def test_material_header_of_idmat_1000(material_html):
    header = parse_material_header(material_html)
    assert isinstance(header, MaterialHeader)
    assert header.issue_number == 88
    assert header.issue_date == "2005-11-04"
    assert "МИНИСТЕРСТВА И ДРУГИ ВЕДОМСТВА" in header.section_path
    assert header.section_path.startswith("Официален раздел")
    assert header.start_page == 30
    assert header.body_org == "Министерство на околната среда и водите"


def test_material_header_of_the_zid(material_zid_html):
    header = parse_material_header(material_zid_html)
    assert header.issue_number == 43
    assert header.issue_date == "2005-05-20"
    assert "НАРОДНО СЪБРАНИЕ" in header.section_path
    assert header.start_page == 19
    assert header.body_org == "Народно събрание"


def test_material_header_raises_on_an_error_page():
    with pytest.raises(ValueError):
        parse_material_header(ERROR_PAGE)


# --- material body --------------------------------------------------------


def test_material_body_keeps_the_act_and_drops_the_chrome(material_zid_html):
    body = material_body_html(material_zid_html)
    assert "§ 1." in body
    assert "Закона за марките и географските означения" in body
    # Page chrome lives outside the content region.
    assert "f5_cspm" not in body
    assert "<title>" not in body
    assert "logoDVhead" not in body


def test_material_body_of_an_annex(material_html):
    body = material_body_html(material_html)
    assert "ПРИЛОЖЕНИЕ VI" in body
    assert "f5_cspm" not in body


def test_material_body_raises_when_the_region_is_absent():
    with pytest.raises(ValueError):
        material_body_html(ERROR_PAGE)


# --- fetch helpers --------------------------------------------------------


def test_fetch_materials_asks_for_the_issue_and_parses_it(materials_html):
    session = FakeSession(get_bodies={MATERIALS_PATH: materials_html})
    rows = fetch_materials(session, 6121)
    assert len(rows) == 18
    url, params = session.gets[0]
    assert url.endswith(MATERIALS_PATH)
    assert params == {"idObj": 6121}


def test_fetch_material_returns_raw_html(material_html):
    session = FakeSession(get_bodies={MATERIAL_PATH: material_html})
    html = fetch_material(session, 1000)
    assert html == material_html
    url, params = session.gets[0]
    assert url.endswith(MATERIAL_PATH)
    assert params == {"idMat": 1000}


def test_fetch_material_writes_the_cache(tmp_path, material_html):
    session = FakeSession(get_bodies={MATERIAL_PATH: material_html})
    fetch_material(session, 1000, cache_dir=tmp_path)
    cached = tmp_path / "1000.html"
    assert cached.exists()
    assert cached.read_text(encoding="utf-8") == material_html


def test_cache_hit_makes_no_request(tmp_path, material_html):
    (tmp_path / "1000.html").write_text(material_html, encoding="utf-8")
    session = FakeSession(get_bodies={})
    html = fetch_material(session, 1000, cache_dir=tmp_path)
    assert html == material_html
    assert session.gets == []


def test_second_fetch_of_the_same_material_is_served_from_the_cache(
    tmp_path, material_html
):
    session = FakeSession(get_bodies={MATERIAL_PATH: material_html})
    first = fetch_material(session, 1000, cache_dir=tmp_path)
    second = fetch_material(session, 1000, cache_dir=tmp_path)
    assert first == second
    assert len(session.gets) == 1


# --- the cache never keeps a stub -----------------------------------------


def test_the_error_stub_is_never_cached(tmp_path):
    # The stub arrives with status 500 and the session hands it back
    # rather than retrying it. Writing it to a permanent cache would make
    # the material unreachable for good.
    session = FakeSession(get_bodies={MATERIAL_PATH: ERROR_PAGE})
    assert fetch_material(session, 1000, cache_dir=tmp_path) == ERROR_PAGE
    assert not (tmp_path / "1000.html").exists()


def test_a_cached_stub_is_treated_as_a_miss_and_refetched(tmp_path, material_html):
    # An earlier run of the previous code, or a stub written by hand, must
    # not shadow the material once the site is healthy again.
    (tmp_path / "1000.html").write_text(ERROR_PAGE, encoding="utf-8")
    session = FakeSession(get_bodies={MATERIAL_PATH: material_html})
    assert fetch_material(session, 1000, cache_dir=tmp_path) == material_html
    assert len(session.gets) == 1
    assert (tmp_path / "1000.html").read_text(encoding="utf-8") == material_html


def test_a_stubbed_run_followed_by_a_healthy_one_gets_the_material(
    tmp_path, material_html
):
    # Two runs, one cache directory: the site is down for the first and
    # healthy for the second, and the second must reach the material.
    down = FakeSession(get_bodies={MATERIAL_PATH: ERROR_PAGE})
    assert fetch_material(down, 1000, cache_dir=tmp_path) == ERROR_PAGE

    healthy = FakeSession(get_bodies={MATERIAL_PATH: material_html})
    assert fetch_material(healthy, 1000, cache_dir=tmp_path) == material_html
    assert len(healthy.gets) == 1
