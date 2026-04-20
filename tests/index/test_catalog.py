import sqlite3
import pytest
from index.catalog import CatalogIndex


@pytest.fixture
def db():
    """In-memory SQLite database for testing."""
    idx = CatalogIndex(":memory:")
    idx.initialize()
    yield idx
    idx.close()


def test_initialize_creates_tables(db):
    tables = db.list_tables()
    assert "laws" in tables
    assert "law_versions" in tables


def test_insert_law(db):
    db.insert_law(
        law_id="zop",
        doc_id=2136735703,
        title="Закон за обществените поръчки",
        category="laws",
        commit_hash="abc123",
        effective_date="2016-04-15",
    )
    law = db.get_law("zop")
    assert law is not None
    assert law["doc_id"] == 2136735703
    assert law["title"] == "Закон за обществените поръчки"
    assert law["category"] == "laws"


def test_insert_creates_initial_version(db):
    db.insert_law(
        law_id="zop",
        doc_id=2136735703,
        title="Закон за обществените поръчки",
        category="laws",
        commit_hash="abc123",
        effective_date="2016-04-15",
    )
    versions = db.get_versions("zop")
    assert len(versions) == 1
    assert versions[0]["valid_from"] == "2016-04-15"
    assert versions[0]["valid_to"] is None  # current version
    assert versions[0]["commit_hash"] == "abc123"


def test_count_by_category(db):
    db.insert_law("zop", 1, "ЗОП", "laws", "a1", "2016-01-01")
    db.insert_law("zeu", 2, "ЗЕУ", "laws", "a2", "2017-01-01")
    db.insert_law("ppzop", 3, "ППЗОП", "implementing", "a3", "2016-01-01")
    counts = db.count_by_category()
    assert counts["laws"] == 2
    assert counts["implementing"] == 1
