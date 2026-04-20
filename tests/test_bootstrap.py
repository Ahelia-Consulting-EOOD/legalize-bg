import pathlib
import subprocess

import pytest

from bootstrap import _git_push, _unique_slug
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
