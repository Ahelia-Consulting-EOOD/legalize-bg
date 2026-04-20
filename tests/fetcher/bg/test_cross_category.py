"""Smoke tests across all 5 corpus categories.

One fixture per category catches structural divergence in lex.bg markup
between кодекс / наредба / правилник / implementing правилник. These
tests don't deep-check content — they verify the pipeline doesn't crash
and produces the minimum viable output for each category.
"""

import pathlib

import pytest
from bs4 import BeautifulSoup

from fetcher.bg.assembler import assemble_file, generate_slug
from fetcher.bg.metadata import MetadataParser
from fetcher.bg.text_parser import HtmlToMarkdown


FIXTURES = pathlib.Path(__file__).parent.parent.parent / "fixtures" / "html"


# (fixture_filename, doc_id, corpus_dir, expected_rango)
CASES = [
    ("zop.html", 2136735703, "laws", "закон"),
    ("zeu.html", 2135555445, "laws", "закон"),
    ("gpk.html", 2135558368, "codes", "кодекс"),
    ("naredba-04-14.html", 2137197056, "ordinances", "наредба"),
    ("pravilnik-sadilishta.html", 2137175683, "regulations", "правилник"),
    ("ppz-aktsizi.html", 2135526226, "implementing", "правилник по прилагане"),
]


@pytest.mark.parametrize("filename,doc_id,corpus_dir,rango", CASES)
def test_pipeline_smoke_per_category(filename, doc_id, corpus_dir, rango):
    """Each category fixture must round-trip through the full pipeline."""
    html = (FIXTURES / filename).read_bytes().decode("cp1251")
    soup = BeautifulSoup(html, "lxml")

    body = HtmlToMarkdown().convert(soup)
    meta = MetadataParser().parse(soup, doc_id=doc_id, category=corpus_dir)

    # Metadata invariants
    assert meta["titulo"], f"{filename}: empty title"
    assert meta["identificador"] == str(doc_id)
    assert meta["pais"] == "bg"
    assert meta["rango"] == rango, f"{filename}: rango mismatch"
    assert meta["category"] == corpus_dir
    assert meta["fuente"] == "lex.bg"
    assert meta["eli"].startswith(f"/eli/bg/{rango}/")
    assert meta["eli"].endswith("/con")

    # Body structure
    assert body.startswith("# "), f"{filename}: body should start with H1"

    # Full-file assembly
    slug = generate_slug(meta["titulo"]) or str(doc_id)
    assert slug, f"{filename}: empty slug"
    content = assemble_file(meta, body)
    assert content.startswith("---\n")
    assert "\n---\n" in content
    assert meta["titulo"] in content
