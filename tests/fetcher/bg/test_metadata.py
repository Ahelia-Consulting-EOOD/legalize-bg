import pathlib
import pytest
from bs4 import BeautifulSoup
from fetcher.bg.metadata import MetadataParser

FIXTURES = pathlib.Path(__file__).parent.parent.parent / "fixtures"


def _load_soup(name: str) -> BeautifulSoup:
    html = (FIXTURES / "html" / name).read_bytes().decode("cp1251")
    return BeautifulSoup(html, "lxml")


def test_extracts_titulo():
    soup = _load_soup("zop.html")
    meta = MetadataParser().parse(soup, doc_id=2136735703, category="laws")
    assert "ОБЩЕСТВЕНИТЕ ПОРЪЧКИ" in meta["titulo"]


def test_extracts_identificador():
    soup = _load_soup("zop.html")
    meta = MetadataParser().parse(soup, doc_id=2136735703, category="laws")
    assert meta["identificador"] == "2136735703"


def test_pais_is_bg():
    soup = _load_soup("zop.html")
    meta = MetadataParser().parse(soup, doc_id=2136735703, category="laws")
    assert meta["pais"] == "bg"


def test_rango_for_law():
    soup = _load_soup("zop.html")
    meta = MetadataParser().parse(soup, doc_id=2136735703, category="laws")
    assert meta["rango"] == "закон"


def test_fuente_is_lexbg():
    soup = _load_soup("zop.html")
    meta = MetadataParser().parse(soup, doc_id=2136735703, category="laws")
    assert meta["fuente"] == "lex.bg"


def test_extracts_effective_date():
    soup = _load_soup("zop.html")
    meta = MetadataParser().parse(soup, doc_id=2136735703, category="laws")
    assert "effective_date" in meta
    # ZOP effective date is 2016-04-15
    assert meta["effective_date"] is not None


def test_extracts_amendment_history():
    soup = _load_soup("zop.html")
    meta = MetadataParser().parse(soup, doc_id=2136735703, category="laws")
    assert "amendment_history" in meta
    assert isinstance(meta["amendment_history"], list)
    # ZOP has been amended many times
    assert len(meta["amendment_history"]) > 5
    # Each entry has dv and date
    for entry in meta["amendment_history"]:
        assert "dv" in entry
        assert "date" in entry


def test_category_to_rango_mapping():
    assert MetadataParser.CATEGORY_TO_RANGO["laws"] == "закон"
    assert MetadataParser.CATEGORY_TO_RANGO["codes"] == "кодекс"
    assert MetadataParser.CATEGORY_TO_RANGO["ordinances"] == "наредба"
    assert MetadataParser.CATEGORY_TO_RANGO["regulations"] == "правилник"
    assert MetadataParser.CATEGORY_TO_RANGO["implementing"] == "правилник по прилагане"


def test_all_13_fields_present():
    soup = _load_soup("zop.html")
    meta = MetadataParser().parse(soup, doc_id=2136735703, category="laws")
    required = [
        "titulo", "identificador", "pais", "rango",
        "fecha_publicacion", "ultima_actualizacion", "estado", "fuente",
        "dv_issue", "dv_year", "effective_date", "category", "eli",
    ]
    for field in required:
        assert field in meta, f"Missing field: {field}"


def test_eli_contains_year_month_day_and_transliterated_slug():
    """ELI must follow data-model.md format /eli/bg/{rango}/{Y}/{M}/{D}/{slug}/con.

    Uses transliterated ASCII slug (not raw Cyrillic) for URI interop.
    """
    soup = _load_soup("zop.html")
    meta = MetadataParser().parse(soup, doc_id=2136735703, category="laws")
    eli = meta["eli"]
    # ZOP fecha_publicacion is 2016-02-16
    assert eli.startswith("/eli/bg/закон/2016/2/16/"), f"ELI format wrong: {eli}"
    assert eli.endswith("/con"), f"ELI must end /con: {eli}"
    # Slug must be ASCII (transliterated), no raw Cyrillic
    slug = eli.split("/")[-2]
    assert slug.isascii(), f"ELI slug must be ASCII, got: {slug!r}"
    assert "zakon" in slug, f"expected transliterated 'zakon', got: {slug!r}"


def test_eli_with_unknown_pub_date_uses_placeholder():
    """If fecha_publicacion is None, ELI should still be well-formed."""
    from bs4 import BeautifulSoup as _BS
    empty = _BS("<html><body></body></html>", "lxml")
    meta = MetadataParser().parse(empty, doc_id=42, category="laws")
    # No crash, ELI exists
    assert meta["eli"]
    assert meta["eli"].startswith("/eli/bg/")
    assert meta["eli"].endswith("/con")


def test_missing_history_only_uses_prehistory_date():
    """Act with .PreHistory but no .HistoryOfDocument (never amended)."""
    from bs4 import BeautifulSoup as _BS
    html = (
        '<html><body>'
        '<div class="TitleDocument">НАРЕДБА № 1</div>'
        '<div class="PreHistory">В сила от 01.03.2020 г.</div>'
        '</body></html>'
    )
    meta = MetadataParser().parse(_BS(html, "lxml"), doc_id=100, category="ordinances")
    assert meta["effective_date"] == "2020-03-01"
    assert meta["amendment_history"] == []
    # fecha_publicacion may be None (no DV refs, no numeric date in prehistory),
    # but parser must not crash; ultima_actualizacion falls back to pub_date.
    assert meta["ultima_actualizacion"] == meta["fecha_publicacion"]


def test_missing_prehistory_only_uses_history_date():
    """Act with .HistoryOfDocument but no .PreHistory."""
    from bs4 import BeautifulSoup as _BS
    html = (
        '<html><body>'
        '<div class="TitleDocument">ЗАКОН</div>'
        '<div class="HistoryOfDocument">ДВ. бр.5 от 10 Януари 2019г.</div>'
        '</body></html>'
    )
    meta = MetadataParser().parse(_BS(html, "lxml"), doc_id=101, category="laws")
    assert meta["effective_date"] is None  # no "В сила от" anywhere
    assert meta["fecha_publicacion"] == "2019-01-10"
    assert meta["dv_issue"] == "5"
    assert meta["dv_year"] == 2019
    assert len(meta["amendment_history"]) == 1


def test_missing_both_sections_does_not_crash():
    """Act with neither .PreHistory nor .HistoryOfDocument — degenerate case.

    fecha_publicacion/ultima_actualizacion end up None (schema violation,
    caught by G2 gate for manual investigation), but the parser must still
    produce a complete dict without raising.
    """
    from bs4 import BeautifulSoup as _BS
    html = '<html><body><div class="TitleDocument">ЗАКОН</div></body></html>'
    meta = MetadataParser().parse(_BS(html, "lxml"), doc_id=102, category="laws")
    assert meta["titulo"] == "ЗАКОН"
    assert meta["fecha_publicacion"] is None
    assert meta["ultima_actualizacion"] is None
    assert meta["effective_date"] is None
    assert meta["dv_issue"] is None
    assert meta["dv_year"] is None
    assert meta["amendment_history"] == []
    # Still has all 13 fields + amendment_history
    for field in ("titulo", "identificador", "pais", "rango",
                  "fecha_publicacion", "ultima_actualizacion", "estado", "fuente",
                  "dv_issue", "dv_year", "effective_date", "category", "eli"):
        assert field in meta
