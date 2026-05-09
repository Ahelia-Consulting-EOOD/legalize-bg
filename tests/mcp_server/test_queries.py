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
