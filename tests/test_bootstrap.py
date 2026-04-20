import pathlib

from bootstrap import _unique_slug
from fetcher.bg.client import LexBgClient
from fetcher.bg.text_parser import HtmlToMarkdown
from fetcher.bg.metadata import MetadataParser
from fetcher.bg.assembler import assemble_file, generate_slug


FIXTURES = pathlib.Path(__file__).parent / "fixtures" / "html"


class FakeTransport:
    def get(self, doc_id: int) -> bytes:
        # Serve ZOP fixture for any doc_id
        return (FIXTURES / "zop.html").read_bytes()


def test_single_act_pipeline():
    """End-to-end: fetch → parse → convert → assemble → verify."""
    client = LexBgClient(transport=FakeTransport())
    parser = HtmlToMarkdown()
    metadata_parser = MetadataParser()

    soup = client.fetch_soup(2136735703)

    body = parser.convert(soup)
    meta = metadata_parser.parse(soup, doc_id=2136735703, category="laws")

    content = assemble_file(meta, body)

    assert content.startswith("---\n")
    assert "\n---\n" in content
    assert "titulo:" in content
    assert "identificador:" in content
    assert "# " in content
    assert "**Чл." in content

    slug = generate_slug(meta["titulo"])
    assert slug
    filepath = f"{meta['category']}/{slug}.md"
    assert filepath.startswith("laws/")
    assert filepath.endswith(".md")


def test_unique_slug_no_collision():
    used: set[str] = set()
    assert _unique_slug("zakon-x", used) == "zakon-x"
    assert "zakon-x" in used


def test_unique_slug_appends_counter_on_collision():
    used: set[str] = set()
    assert _unique_slug("naredba-7", used) == "naredba-7"
    assert _unique_slug("naredba-7", used) == "naredba-7-2"
    assert _unique_slug("naredba-7", used) == "naredba-7-3"
    # Different slug stays clean
    assert _unique_slug("naredba-8", used) == "naredba-8"
    # Original pattern continues correctly
    assert _unique_slug("naredba-7", used) == "naredba-7-4"
