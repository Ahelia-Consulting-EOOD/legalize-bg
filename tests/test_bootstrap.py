import pathlib

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
