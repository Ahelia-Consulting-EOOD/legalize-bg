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
    full_text_search,
    article_lookup,
    ArticleNotFound,
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
    (the disambiguating handle). The point of D-026's payload contract
    is that the identificador values are *distinct* — a list of
    identical identificadors couldn't disambiguate anything."""
    with pytest.raises(AmbiguousName) as exc:
        resolve_name_to_law_id(populated_conn, "Наредба № 7 за нещо")
    assert len(exc.value.candidates) == 2
    law_ids = {c["law_id"] for c in exc.value.candidates}
    assert law_ids == {"naredba-7", "naredba-7-2"}
    identificadors = {c["identificador"] for c in exc.value.candidates}
    assert len(identificadors) == 2, \
        f"identificadors must be distinct for disambiguation, got {identificadors}"


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


def test_version_with_warnings_attaches_DATE_UNCERTAIN_via_persisted_flag(populated_conn):
    """§7.2: the warning fires off a persisted `date_uncertain` column
    on law_versions, set by index.build when fecha_publicacion is null
    at index time. The fix replaces the previous time-dependent check
    (valid_from == today()) which silently stopped firing the day after
    the build."""
    populated_conn.execute(
        "UPDATE law_versions SET date_uncertain = 1 WHERE law_id = 'phantom'",
    )
    populated_conn.commit()

    commit, warnings = version_with_warnings(populated_conn, "phantom", date=None)
    codes = [w["code"] for w in warnings]
    assert "DATE_UNCERTAIN" in codes


def test_version_with_warnings_no_warning_when_flag_not_set(populated_conn):
    """Acts with date_uncertain=0 (the default; pub_date was known at
    index time) must NOT emit DATE_UNCERTAIN regardless of valid_from
    value."""
    commit, warnings = version_with_warnings(populated_conn, "zakon-a", date=None)
    codes = [w["code"] for w in warnings]
    assert "DATE_UNCERTAIN" not in codes


def test_version_at_date_inclusive_valid_to_boundary(populated_conn):
    """Schema convention: valid_to is INCLUSIVE (last day in force).
    Insert two adjacent versions and verify a query on the boundary day
    returns the version that's still in force on that day, not the
    next one. Regression test for the >=/>  off-by-one."""
    fake_v1 = "v" * 40
    fake_v2 = "w" * 40
    # Replace zakon-a's single version with two adjacent versions
    populated_conn.execute("DELETE FROM law_versions WHERE law_id = 'zakon-a'")
    populated_conn.execute(
        "INSERT INTO law_versions (law_id, valid_from, valid_to, commit_hash) "
        "VALUES (?, ?, ?, ?)",
        ("zakon-a", "2020-01-01", "2020-12-31", fake_v1),
    )
    populated_conn.execute(
        "INSERT INTO law_versions (law_id, valid_from, valid_to, commit_hash) "
        "VALUES (?, ?, ?, ?)",
        ("zakon-a", "2021-01-01", None, fake_v2),
    )
    populated_conn.commit()
    # Boundary day: 2020-12-31 belongs to v1 (still in force that day)
    assert version_at_date(populated_conn, "zakon-a", "2020-12-31") == fake_v1
    # Next day: 2021-01-01 belongs to v2
    assert version_at_date(populated_conn, "zakon-a", "2021-01-01") == fake_v2


def test_article_lookup_inclusive_valid_to_boundary(populated_conn):
    """Same boundary rule applies to provisions table."""
    populated_conn.execute(
        "INSERT INTO provisions (law_id, article, paragraph, valid_from, valid_to, text, text_hash) "
        "VALUES ('zakon-a', '1', NULL, '2020-01-01', '2020-12-31', 'old', 'h_old')"
    )
    populated_conn.execute(
        "INSERT INTO provisions (law_id, article, paragraph, valid_from, valid_to, text, text_hash) "
        "VALUES ('zakon-a', '1', NULL, '2021-01-01', NULL, 'new', 'h_new')"
    )
    populated_conn.commit()
    rows = article_lookup(populated_conn, "zakon-a",
                          article="1", paragraph=None, date="2020-12-31")
    assert any(r["text"] == "old" for r in rows), \
        "boundary day must resolve to the still-in-force version"


# ────────────────────────────── full_text_search + article_lookup ──────────


def test_search_returns_matching_acts(populated_conn):
    hits = full_text_search(populated_conn, "Закон за А")
    assert any(h["law_id"] == "zakon-a" for h in hits)


def test_search_morphology_matches_definite_article(populated_conn):
    """bg_normalize symmetry: query 'наредбата' should still find
    'Наредба № 7' even though indexed form is 'наредба'."""
    hits = full_text_search(populated_conn, "наредбата")
    assert any(h["law_id"].startswith("naredba-7") for h in hits)


def test_search_filters_by_category(populated_conn):
    hits = full_text_search(populated_conn, "Закон", category="ordinances")
    assert all(h["category"] == "ordinances" for h in hits)


def test_search_phantom_act_uses_doc_id_as_title(populated_conn):
    """§7.3: phantom acts have empty titulo on lex.bg; the conftest
    seeds laws_fts with a `<doc_id=N>` substitute so they remain
    findable via identificador."""
    hits = full_text_search(populated_conn, "549676032")
    assert any(h["law_id"] == "phantom" for h in hits)


def test_article_lookup_missing_provision_raises(populated_conn):
    # No provisions seeded in conftest; any lookup should raise.
    with pytest.raises(ArticleNotFound) as exc:
        article_lookup(populated_conn, "zakon-a", article="14",
                       paragraph=None, date=None)
    assert exc.value.law_id == "zakon-a"
    assert exc.value.article == "14"


def test_article_lookup_returns_text_for_matching_provision(populated_conn):
    populated_conn.execute(
        """INSERT INTO provisions(law_id, article, paragraph,
                                  valid_from, text, text_hash)
           VALUES ('zakon-a', '14', NULL, '2020-01-01',
                   'Чл. 14 текст.', 'h1')"""
    )
    populated_conn.execute(
        """INSERT INTO provisions(law_id, article, paragraph,
                                  valid_from, text, text_hash)
           VALUES ('zakon-a', '14', '2', '2020-01-01',
                   '(2) Алинея 2.', 'h2')"""
    )
    populated_conn.commit()

    rows = article_lookup(populated_conn, "zakon-a",
                          article="14", paragraph=None, date=None)
    assert any(r["paragraph"] is None and "Чл. 14" in r["text"] for r in rows)

    rows = article_lookup(populated_conn, "zakon-a",
                          article="14", paragraph="2", date=None)
    assert len(rows) == 1
    assert rows[0]["paragraph"] == "2"
    assert "Алинея 2" in rows[0]["text"]


def test_article_lookup_available_articles_sorted_in_legal_order(populated_conn):
    """The retry-list `available_articles` must use legal-number
    ordering (1, 9, 14, 14а, 15, 100), not text-sort (which gives
    1, 14, 14а, 15, 9, 100). The ordering matters because the model
    chooses retry candidates by reading the list."""
    for art in ["1", "9", "14", "14а", "15", "100"]:
        populated_conn.execute(
            "INSERT INTO provisions (law_id, article, paragraph, valid_from, text, text_hash) "
            "VALUES ('zakon-a', ?, NULL, '2020-01-01', 'x', 'h')",
            (art,),
        )
    populated_conn.commit()
    with pytest.raises(ArticleNotFound) as exc:
        article_lookup(populated_conn, "zakon-a",
                       article="999", paragraph=None, date=None)
    assert exc.value.available_articles == ["1", "9", "14", "14а", "15", "100"]
