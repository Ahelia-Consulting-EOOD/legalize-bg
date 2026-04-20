import os
import pathlib
import subprocess

import pytest

from bootstrap import _format_author_date, _git_commit, _git_push, _unique_slug
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


def test_format_author_date_converts_iso_date_to_git_iso_timestamp():
    """Git rejects bare YYYY-MM-DD in GIT_AUTHOR_DATE with
    'fatal: invalid date format'. The full run of Task 11 hit this and
    silently bundled 3,573 files into 121 commits with wrong dates."""
    assert _format_author_date("2016-02-16") == "2016-02-16T00:00:00+00:00"
    assert _format_author_date("1955-09-09") == "1955-09-09T00:00:00+00:00"


def test_format_author_date_returns_none_for_empty_or_none():
    assert _format_author_date(None) is None
    assert _format_author_date("") is None


def test_format_author_date_rejects_obviously_malformed_input():
    # Wrong length / wrong separator — just don't crash; return None so
    # caller skips setting GIT_AUTHOR_DATE rather than passing garbage to git.
    assert _format_author_date("2016") is None
    assert _format_author_date("not-a-date") is None


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
