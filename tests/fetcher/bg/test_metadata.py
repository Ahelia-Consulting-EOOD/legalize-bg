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
