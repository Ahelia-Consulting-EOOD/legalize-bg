import pytest
from mcp_server.queries import parse_article_spec, ArticleSpec, InvalidArticleSpec


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
