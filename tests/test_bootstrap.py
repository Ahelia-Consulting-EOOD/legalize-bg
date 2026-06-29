import json
import os
import pathlib
import subprocess

import pytest
from bs4 import BeautifulSoup

from bootstrap import _format_author_date, _git_commit, _git_push, _unique_slug
from fetcher.bg.client import LexBgClient
from fetcher.bg.discovery import CatalogCrawler
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


def test_git_push_retries_on_transient_failure(tmp_path, monkeypatch):
    """_git_push should retry failed pushes with backoff (transient network)."""
    calls = []
    sleep_calls = []

    def fake_run(cmd, cwd, check, capture_output, text=False):
        calls.append(cmd)
        # First two pushes fail, third succeeds
        if len(calls) < 3:
            raise subprocess.CalledProcessError(
                returncode=128, cmd=cmd, stderr=b"network unreachable"
            )
        return subprocess.CompletedProcess(cmd, 0, stdout=b"", stderr=b"")

    monkeypatch.setattr(subprocess, "run", fake_run)
    _git_push(cwd=tmp_path, branch="bootstrap/test", retries=3, sleep=sleep_calls.append)

    assert len(calls) == 3, f"expected 3 attempts, got {len(calls)}"
    assert len(sleep_calls) == 2, "expected 2 backoff sleeps between 3 attempts"
    # Exponential backoff
    assert sleep_calls[1] > sleep_calls[0]


def test_git_push_raises_after_max_retries(tmp_path, monkeypatch):
    def always_fail(cmd, cwd, check, capture_output, text=False):
        raise subprocess.CalledProcessError(
            returncode=128, cmd=cmd, stderr=b"rejected"
        )

    monkeypatch.setattr(subprocess, "run", always_fail)
    with pytest.raises(subprocess.CalledProcessError):
        _git_push(cwd=tmp_path, branch="bootstrap/test", retries=2, sleep=lambda s: None)


def test_git_push_succeeds_first_try(tmp_path, monkeypatch):
    calls = []

    def fake_run(cmd, cwd, check, capture_output, text=False):
        calls.append(cmd)
        return subprocess.CompletedProcess(cmd, 0, stdout=b"", stderr=b"")

    monkeypatch.setattr(subprocess, "run", fake_run)
    _git_push(cwd=tmp_path, branch="bootstrap/test", retries=3, sleep=lambda s: None)
    assert len(calls) == 1


def test_bootstrap_requires_branch_when_push_every_is_set(tmp_path):
    """--push-every without --branch would push half-bootstrapped commits to
    the current branch (likely main); delivery-contract.md:97 says main
    history is sacred. Guard at the entry point, before any lex.bg traffic."""
    from bootstrap import bootstrap
    with pytest.raises(ValueError, match="--branch"):
        bootstrap(tmp_path, db_path=":memory:", push_every=250)


def test_format_author_date_converts_iso_date_to_git_iso_timestamp():
    """Git rejects bare YYYY-MM-DD in GIT_AUTHOR_DATE with
    'fatal: invalid date format'. The full run of Task 11 hit this and
    silently bundled 3,573 files into 121 commits with wrong dates."""
    assert _format_author_date("2016-02-16") == "2016-02-16T00:00:00+00:00"
    assert _format_author_date("1975-11-28") == "1975-11-28T00:00:00+00:00"


def test_format_author_date_returns_none_for_empty_or_none():
    assert _format_author_date(None) is None
    assert _format_author_date("") is None


def test_format_author_date_rejects_obviously_malformed_input():
    # Wrong length / wrong separator — just don't crash; return None so
    # caller skips setting GIT_AUTHOR_DATE rather than passing garbage to git.
    assert _format_author_date("2016") is None
    assert _format_author_date("not-a-date") is None


def test_format_author_date_clamps_pre_1970_to_epoch():
    """Git rejects pre-1970 dates in every input format. Clamp to 1970-01-01
    so the commit still succeeds; the true publication date remains in the
    Source-Date body line."""
    assert _format_author_date("1947-06-27") == "1970-01-01T00:00:00+00:00"
    assert _format_author_date("1964-09-08") == "1970-01-01T00:00:00+00:00"
    # Boundary: 1970-01-01 itself is accepted unchanged
    assert _format_author_date("1970-01-01") == "1970-01-01T00:00:00+00:00"
    # Post-1970 unchanged
    assert _format_author_date("1970-01-02") == "1970-01-02T00:00:00+00:00"


def test_git_commit_accepts_pre_1970_pub_date(tmp_path):
    """Historical Bulgarian laws (e.g. 1947 Amnesty Act) must commit cleanly
    — without the epoch clamp they silently fail and bundle into the next
    successful commit."""
    _init_tmp_repo(tmp_path)
    f = tmp_path / "laws" / "old.md"
    f.parent.mkdir()
    f.write_text("body")

    _git_commit(filepath=f, title="Old Act", doc_id=1,
                pub_date="1947-06-27", cwd=tmp_path)

    log = subprocess.run(
        ["git", "log", "-1", "--format=%aI|%B"],
        cwd=tmp_path, check=True, capture_output=True, text=True,
    ).stdout.strip()
    author_iso, _, body = log.partition("|")
    # Author date clamped to epoch
    assert author_iso.startswith("1970-01-01"), f"expected epoch floor, got {author_iso}"
    # True publication date preserved in body
    assert "Source-Date: 1947-06-27" in body


def _init_tmp_repo(tmp_path):
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "test@test"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "commit.gpgsign", "false"], cwd=tmp_path, check=True)
    # Initial commit so HEAD exists
    (tmp_path / "README.md").write_text("init")
    subprocess.run(["git", "add", "README.md"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=tmp_path, check=True)


def test_git_commit_accepts_backdated_pub_date(tmp_path):
    """End-to-end: _git_commit with a YYYY-MM-DD pub_date must succeed
    and backdate the commit (author date = pub_date)."""
    _init_tmp_repo(tmp_path)
    f = tmp_path / "laws" / "test.md"
    f.parent.mkdir()
    f.write_text("body")

    _git_commit(filepath=f, title="Test Act", doc_id=42,
                pub_date="2016-02-16", cwd=tmp_path)

    log = subprocess.run(
        ["git", "log", "-1", "--format=%aI|%s"],
        cwd=tmp_path, check=True, capture_output=True, text=True,
    ).stdout.strip()
    author_iso, subject = log.split("|", 1)
    assert subject == "[bootstrap] Test Act"
    assert author_iso.startswith("2016-02-16T00:00:00"), (
        f"expected commit backdated to 2016-02-16, got {author_iso}"
    )


def test_git_commit_handles_null_pub_date(tmp_path):
    """When pub_date is None, commit still succeeds (uses current date)
    and the message shows 'unknown' not the string 'None'."""
    _init_tmp_repo(tmp_path)
    f = tmp_path / "laws" / "test.md"
    f.parent.mkdir()
    f.write_text("body")

    _git_commit(filepath=f, title="Dateless Act", doc_id=99,
                pub_date=None, cwd=tmp_path)

    body = subprocess.run(
        ["git", "log", "-1", "--format=%B"],
        cwd=tmp_path, check=True, capture_output=True, text=True,
    ).stdout
    assert "Source-Date: unknown" in body
    assert "Source-Date: None" not in body


# ---------------------------------------------------------------------------
# Coverage gate tests (Task 5)
# ---------------------------------------------------------------------------


def _make_soup_from_fixture(name: str) -> BeautifulSoup:
    html = (FIXTURES / name).read_bytes().decode("cp1251")
    return BeautifulSoup(html, "lxml")


def test_coverage_gate_blocks_write_on_drop(tmp_path, monkeypatch):
    """Bootstrap: a parser that drops most content triggers the coverage gate.

    The act's .md file must NOT be written, and the failure must appear
    in gate-report.json next to the output directory.
    """
    from bootstrap import bootstrap

    # Serve zop.html soup for any fetch
    fake_soup = _make_soup_from_fixture("zop.html")
    monkeypatch.setattr(LexBgClient, "fetch_soup", lambda self, doc_id: fake_soup)

    # Crawler returns a single-act catalog
    fake_catalog = [{"doc_id": 9001, "name": "Закон за тест", "category": "laws"}]
    monkeypatch.setattr(CatalogCrawler, "crawl_all", lambda self, t: fake_catalog)

    # Parser stub: drops almost all content → uncovered_chars >> 64
    monkeypatch.setattr(
        HtmlToMarkdown, "convert",
        lambda self, soup: "## Заглавие\n\nМалко текст.",
    )

    # No real git operations needed: gate fires before write/commit
    # But subprocess.run is still called for git setup; monkeypatch to no-op.
    monkeypatch.setattr(
        subprocess, "run",
        lambda *a, **k: subprocess.CompletedProcess(a[0], 0, stdout=b"", stderr=b""),
    )

    (tmp_path / "laws").mkdir()
    bootstrap(tmp_path, db_path=":memory:")

    # (a) .md must NOT be written
    written = list((tmp_path / "laws").glob("*.md"))
    assert written == [], f"Expected no .md written, got: {written}"

    # (b) failure must appear in gate-report.json
    report_path = tmp_path / "gate-report.json"
    assert report_path.exists(), "gate-report.json must be written"
    failures = json.loads(report_path.read_text(encoding="utf-8"))
    assert len(failures) == 1, f"Expected 1 gate failure, got: {failures}"
    assert failures[0]["doc_id"] == 9001
    assert failures[0]["uncovered_chars"] > 64


def test_coverage_gate_allows_complete_act(tmp_path, monkeypatch):
    """Bootstrap: a fully-captured act passes the gate and its .md is written."""
    from bootstrap import bootstrap

    fake_soup = _make_soup_from_fixture("zop.html")
    monkeypatch.setattr(LexBgClient, "fetch_soup", lambda self, doc_id: fake_soup)

    fake_catalog = [{"doc_id": 9002, "name": "Закон за тест 2", "category": "laws"}]
    monkeypatch.setattr(CatalogCrawler, "crawl_all", lambda self, t: fake_catalog)

    # Real parser — zop.html should pass the gate (uncovered_chars ≤ 64)
    # (HtmlToMarkdown not monkeypatched)

    # Monkeypatch git to avoid real subprocess in tmp_path
    def fake_git(cmd, cwd=None, check=False, capture_output=False,
                 text=False, env=None, **kw):
        if isinstance(cmd, list) and "rev-parse" in cmd and "HEAD" in cmd:
            return subprocess.CompletedProcess(cmd, 0, stdout=b"deadbeef\n", stderr=b"")
        return subprocess.CompletedProcess(cmd, 0, stdout=b"", stderr=b"")

    monkeypatch.setattr(subprocess, "run", fake_git)

    (tmp_path / "laws").mkdir()
    bootstrap(tmp_path, db_path=":memory:")

    # .md must be written
    written = list((tmp_path / "laws").glob("*.md"))
    assert len(written) == 1, f"Expected exactly one .md, got: {written}"

    # gate-report.json must exist with 0 failures
    report_path = tmp_path / "gate-report.json"
    assert report_path.exists(), "gate-report.json must always be written"
    failures = json.loads(report_path.read_text(encoding="utf-8"))
    assert failures == [], f"Expected no gate failures, got: {failures}"
