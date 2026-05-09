import sqlite3
import subprocess
import pathlib
import pytest

from index.build import build
from index.migrations import current_version


@pytest.fixture
def fake_corpus(tmp_path):
    """Tiny git-tracked corpus with 2 fixture-derived .md files."""
    (tmp_path / "laws").mkdir()
    (tmp_path / "ordinances").mkdir()

    from bs4 import BeautifulSoup
    from fetcher.bg.text_parser import HtmlToMarkdown
    from fetcher.bg.metadata import MetadataParser
    from fetcher.bg.assembler import assemble_file, generate_slug

    repo_root = pathlib.Path(__file__).parent.parent.parent
    for fixture_name, doc_id, corpus_dir in [
        ("zop", 2136735703, "laws"),
        ("naredba-04-14", 2137197056, "ordinances"),
    ]:
        html = (repo_root / "tests/fixtures/html" / f"{fixture_name}.html").read_bytes().decode("cp1251")
        soup = BeautifulSoup(html, "lxml")
        body = HtmlToMarkdown().convert(soup)
        meta = MetadataParser().parse(soup, doc_id=doc_id, category=corpus_dir)
        slug = generate_slug(meta["titulo"])
        content = assemble_file(meta, body)
        (tmp_path / corpus_dir / f"{slug}.md").write_text(content, encoding="utf-8")

    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "test@test"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "commit.gpgsign", "false"], cwd=tmp_path, check=True)
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "fixtures"], cwd=tmp_path, check=True)
    return tmp_path


def test_build_runs_migrations(fake_corpus, tmp_path):
    db_path = str(tmp_path / "test.db")
    build(corpus_root=fake_corpus, db_path=db_path)
    conn = sqlite3.connect(db_path)
    assert current_version(conn) >= 3


def test_build_populates_laws_and_versions(fake_corpus, tmp_path):
    db_path = str(tmp_path / "test.db")
    build(corpus_root=fake_corpus, db_path=db_path)
    conn = sqlite3.connect(db_path)
    laws_count = conn.execute("SELECT COUNT(*) FROM laws").fetchone()[0]
    assert laws_count == 2
    versions_count = conn.execute("SELECT COUNT(*) FROM law_versions").fetchone()[0]
    assert versions_count == 2


def test_build_populates_provisions_with_alineas(fake_corpus, tmp_path):
    db_path = str(tmp_path / "test.db")
    build(corpus_root=fake_corpus, db_path=db_path)
    conn = sqlite3.connect(db_path)
    article_rows = conn.execute(
        "SELECT COUNT(*) FROM provisions WHERE paragraph IS NULL"
    ).fetchone()[0]
    alinea_rows = conn.execute(
        "SELECT COUNT(*) FROM provisions WHERE paragraph IS NOT NULL"
    ).fetchone()[0]
    assert article_rows > 50  # ZOP alone has ~285
    assert alinea_rows > article_rows  # most articles have multiple alineas


def test_build_populates_fts_with_normalized_text(fake_corpus, tmp_path):
    db_path = str(tmp_path / "test.db")
    build(corpus_root=fake_corpus, db_path=db_path)
    conn = sqlite3.connect(db_path)
    fts_count = conn.execute("SELECT COUNT(*) FROM laws_fts").fetchone()[0]
    assert fts_count == 2
    body = conn.execute("SELECT body FROM laws_fts LIMIT 1").fetchone()[0]
    assert body == body.lower()  # bg_normalize lowercases


def test_build_is_idempotent(fake_corpus, tmp_path):
    db_path = str(tmp_path / "test.db")
    build(corpus_root=fake_corpus, db_path=db_path)
    build(corpus_root=fake_corpus, db_path=db_path)
    conn = sqlite3.connect(db_path)
    laws_count = conn.execute("SELECT COUNT(*) FROM laws").fetchone()[0]
    assert laws_count == 2  # rebuild replaced rows, didn't append


def test_build_records_current_commit(fake_corpus, tmp_path):
    db_path = str(tmp_path / "test.db")
    build(corpus_root=fake_corpus, db_path=db_path)
    conn = sqlite3.connect(db_path)
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=fake_corpus,
        check=True, capture_output=True, text=True,
    ).stdout.strip()
    rows = conn.execute("SELECT DISTINCT current_commit FROM laws").fetchall()
    assert len(rows) == 1 and rows[0][0] == head
