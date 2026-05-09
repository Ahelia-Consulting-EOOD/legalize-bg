import pytest
from mcp_server.queries import (
    parse_article_spec,
    ArticleSpec,
    InvalidArticleSpec,
    resolve_name_to_law_id,
    LawNotFound,
    AmbiguousName,
    version_at_date,
    version_with_warnings,
    NoVersionAtDate,
)


@pytest.mark.parametrize("spec,expected", [
    ("чл. 14",          ArticleSpec(article="14", paragraph=None, range_end=None)),
    ("Чл. 14",          ArticleSpec(article="14", paragraph=None, range_end=None)),
    ("14",              ArticleSpec(article="14", paragraph=None, range_end=None)),
    ("чл. 14а",         ArticleSpec(article="14а", paragraph=None, range_end=None)),
    ("14а",             ArticleSpec(article="14а", paragraph=None, range_end=None)),
    ("чл. 14, ал. 2",   ArticleSpec(article="14", paragraph="2", range_end=None)),
    ("Чл. 14 ал. 2",    ArticleSpec(article="14", paragraph="2", range_end=None)),
    ("14.2",            ArticleSpec(article="14", paragraph="2", range_end=None)),
    ("14, ал. 2",       ArticleSpec(article="14", paragraph="2", range_end=None)),
    ("чл. 14-16",       ArticleSpec(article="14", paragraph=None, range_end="16")),
    ("чл. 14 - 16",     ArticleSpec(article="14", paragraph=None, range_end="16")),
    ("чл. 14, ал. 2а",  ArticleSpec(article="14", paragraph="2а", range_end=None)),
])
def test_valid_specs(spec, expected):
    assert parse_article_spec(spec) == expected


@pytest.mark.parametrize("spec", [
    "",
    "garbage",
    "чл.",
    "ал. 2",
    "чл. abc",
])
def test_invalid_specs_raise(spec):
    with pytest.raises(InvalidArticleSpec):
        parse_article_spec(spec)


# Edge-case lockdown for whitespace and trailing punctuation. Locked in
# this batch (rather than later) so Tasks 8/9/10 build on stable parsing
# semantics — silent regressions in the spec parser would surface as
# misleading 'ARTICLE_NOT_FOUND' downstream rather than as parser bugs.
@pytest.mark.parametrize("spec,expected_article,expected_paragraph", [
    ("чл. 14 ",         "14",  None),   # trailing space
    (" чл. 14",         "14",  None),   # leading space
    ("Чл.14",           "14",  None),   # no space after dot
    ("чл.  14",         "14",  None),   # multiple spaces
    ("ЧЛ. 14",          "14",  None),   # all caps prefix
    ("  чл. 14, ал. 2 ", "14", "2"),    # surrounded whitespace + alinea
])
def test_valid_specs_with_whitespace_and_case_edges(
    spec, expected_article, expected_paragraph,
):
    result = parse_article_spec(spec)
    assert result.article == expected_article
    assert result.paragraph == expected_paragraph


@pytest.mark.parametrize("spec", [
    "чл. 14.",          # bare trailing dot — parser must NOT confuse with alinea separator
    "14.",              # bare digit + dot
    "чл. 14, ал. ",     # incomplete alinea
    "чл. 14, ал. abc",  # alinea with non-numeric
    "чл. 14 - ",        # incomplete range
    "чл. 14-",          # incomplete range, no whitespace
])
def test_invalid_specs_edge_cases(spec):
    with pytest.raises(InvalidArticleSpec):
        parse_article_spec(spec)


# ────────────────────────────── resolve_name_to_law_id ──────────────────────


def test_resolve_by_identificador(populated_conn):
    assert resolve_name_to_law_id(populated_conn, "100") == "zakon-a"


def test_resolve_by_negative_identificador(populated_conn):
    """§7.3 phantom act with negative doc_id — identificador is the only
    handle that can address it, since titulo is empty."""
    assert resolve_name_to_law_id(populated_conn, "-549676032") == "phantom"


def test_resolve_by_exact_slug(populated_conn):
    assert resolve_name_to_law_id(populated_conn, "zakon-a") == "zakon-a"


def test_resolve_by_unique_title(populated_conn):
    assert resolve_name_to_law_id(populated_conn, "Закон за А") == "zakon-a"


def test_ambiguous_title_raises_with_candidates(populated_conn):
    """§7.1 — multiple acts with identical title surface as
    AMBIGUOUS_NAME with the full candidate list including identificador
    (the disambiguating handle)."""
    with pytest.raises(AmbiguousName) as exc:
        resolve_name_to_law_id(populated_conn, "Наредба № 7 за нещо")
    assert len(exc.value.candidates) == 2
    ids = {c["law_id"] for c in exc.value.candidates}
    assert ids == {"naredba-7", "naredba-7-2"}
    for c in exc.value.candidates:
        assert "identificador" in c


def test_unknown_name_raises_LawNotFound_with_suggestions(populated_conn):
    with pytest.raises(LawNotFound) as exc:
        resolve_name_to_law_id(populated_conn, "напълно непознат акт")
    assert "напълно непознат акт" in exc.value.name
    assert hasattr(exc.value, "suggestions")


# ────────────────────────────── version_at_date (§7.2) ──────────────────────


def test_version_at_date_returns_commit_for_current(populated_conn):
    commit = version_at_date(populated_conn, "zakon-a", date=None)
    assert len(commit) == 40  # SHA-1 hex


def test_version_at_date_for_date_after_validity(populated_conn):
    """Date after valid_from returns the version that's still in force
    (valid_to is NULL for current versions)."""
    commit = version_at_date(populated_conn, "zakon-a", date="2024-12-31")
    assert commit


def test_version_at_date_for_date_before_validity_raises(populated_conn):
    with pytest.raises(NoVersionAtDate) as exc:
        version_at_date(populated_conn, "zakon-a", date="1900-01-01")
    assert exc.value.law_id == "zakon-a"
    assert exc.value.earliest_available  # earliest valid_from for the law


def test_version_at_date_for_unknown_law_raises_NoVersion(populated_conn):
    with pytest.raises(NoVersionAtDate):
        version_at_date(populated_conn, "nonexistent", date=None)


def test_version_with_warnings_attaches_DATE_UNCERTAIN_for_null_pub_date(populated_conn):
    """§7.2: an act whose valid_from equals today (the bootstrap-run-date
    fallback used when fecha_publicacion was null) returns a successful
    response with a DATE_UNCERTAIN warning attached."""
    from datetime import date as _date
    today = _date.today().isoformat()
    populated_conn.execute(
        "UPDATE law_versions SET valid_from = ? WHERE law_id = 'phantom'",
        (today,),
    )
    populated_conn.commit()

    commit, warnings = version_with_warnings(populated_conn, "phantom", date=None)
    codes = [w["code"] for w in warnings]
    assert "DATE_UNCERTAIN" in codes
