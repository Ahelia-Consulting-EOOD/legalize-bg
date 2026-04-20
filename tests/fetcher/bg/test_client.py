import pathlib
import pytest
from fetcher.bg.client import LexBgClient

FIXTURES = pathlib.Path(__file__).parent.parent.parent / "fixtures" / "html"


class FakeTransport:
    """Serves fixtures from disk instead of HTTP."""

    def __init__(self, fixtures_dir: pathlib.Path):
        self._fixtures = fixtures_dir

    def get(self, doc_id: int) -> bytes:
        # Map known doc_ids to fixture files
        mapping = {2136735703: "zop.html"}
        filename = mapping.get(doc_id)
        if filename is None:
            raise FileNotFoundError(f"No fixture for doc_id {doc_id}")
        return (self._fixtures / filename).read_bytes()


def test_fetch_returns_decoded_text():
    client = LexBgClient(transport=FakeTransport(FIXTURES))
    text = client.fetch(2136735703)
    assert isinstance(text, str)
    assert "Закон" in text  # Bulgarian text, properly decoded from cp1251


def test_fetch_returns_parseable_html():
    client = LexBgClient(transport=FakeTransport(FIXTURES))
    soup = client.fetch_soup(2136735703)
    title = soup.select_one(".TitleDocument")
    assert title is not None
    assert "ОБЩЕСТВЕНИТЕ ПОРЪЧКИ" in title.get_text()
