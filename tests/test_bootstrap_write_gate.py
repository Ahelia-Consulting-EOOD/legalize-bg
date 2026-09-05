"""bootstrap() writes only through the corpus write gate.

The coverage gate stays where it is and fires first; the write gate is the
second layer, and it catches what coverage cannot see — a body that reproduces
every source character faithfully and carries a markup remnant while doing it.
"""

import json
import subprocess
from pathlib import Path

from bs4 import BeautifulSoup

import bootstrap as bootstrap_module
from bootstrap import bootstrap
from fetcher.bg.client import LexBgClient
from fetcher.bg.discovery import CatalogCrawler
from fetcher.bg.text_parser import HtmlToMarkdown

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "html"


def _soup(name: str) -> BeautifulSoup:
    raw = (FIXTURES / name).read_bytes().decode("cp1251", errors="replace")
    return BeautifulSoup(raw, "lxml")


def _no_git(monkeypatch):
    def fake_git(cmd, cwd=None, check=False, capture_output=False,
                 text=False, env=None, **kw):
        if isinstance(cmd, list) and "rev-parse" in cmd and "HEAD" in cmd:
            return subprocess.CompletedProcess(cmd, 0, stdout=b"deadbeef\n", stderr=b"")
        return subprocess.CompletedProcess(cmd, 0, stdout=b"", stderr=b"")

    monkeypatch.setattr(subprocess, "run", fake_git)


def test_a_remnant_in_a_fully_covered_body_is_refused_at_the_write_gate(
    tmp_path, monkeypatch
):
    soup = _soup("zop.html")
    monkeypatch.setattr(LexBgClient, "fetch_soup", lambda self, doc_id: soup)
    monkeypatch.setattr(
        CatalogCrawler, "crawl_all",
        lambda self, t: [
            {"doc_id": 9001, "name": "Развален закон", "category": "laws"},
            {"doc_id": 9002, "name": "Чист закон", "category": "laws"},
        ],
    )
    real_convert = HtmlToMarkdown.convert
    seen: list[int] = []

    def convert(self, s):
        seen.append(len(seen))
        text = real_convert(self, s)
        # The first act carries a remnant; coverage cannot see it, because
        # every source character is still present.
        return text + "\n\n**Чл. 999.**/span> Допълнение.\n" if len(seen) == 1 else text

    monkeypatch.setattr(HtmlToMarkdown, "convert", convert)
    _no_git(monkeypatch)
    (tmp_path / "laws").mkdir()

    bootstrap(tmp_path, db_path=":memory:")

    written = sorted(p.name for p in (tmp_path / "laws").glob("*.md"))
    assert len(written) == 1, f"the refused act must not be written: {written}"

    refusals = json.loads(
        (tmp_path / "write-gate-refusals.json").read_text(encoding="utf-8")
    )
    assert [r["doc_id"] for r in refusals] == [9001]
    assert "tag_remnants" in refusals[0]["violations"][0]

    # The coverage report is unaffected: this is a different gate.
    assert json.loads((tmp_path / "gate-report.json").read_text(encoding="utf-8")) == []


def test_the_exit_code_is_non_zero_when_an_act_was_refused(tmp_path, monkeypatch):
    monkeypatch.setattr(bootstrap_module, "bootstrap", lambda *a, **k: [])
    (tmp_path / "write-gate-refusals.json").write_text(
        json.dumps([{"doc_id": 1, "slug": "x", "violations": ["tag_remnants@line 2: x"]}]),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        "sys.argv", ["bootstrap.py", "--output", str(tmp_path), "--db", ":memory:"]
    )
    assert bootstrap_module.main() == 1


def test_a_dry_run_ignores_a_refusal_file_left_by_an_earlier_run(tmp_path, monkeypatch):
    """A dry run writes nothing, so a stale file says nothing about it."""
    monkeypatch.setattr(bootstrap_module, "bootstrap", lambda *a, **k: [])
    (tmp_path / "write-gate-refusals.json").write_text(
        json.dumps([{"doc_id": 1, "slug": "x", "violations": ["old"]}]), encoding="utf-8"
    )
    monkeypatch.setattr(
        "sys.argv",
        ["bootstrap.py", "--output", str(tmp_path), "--db", ":memory:", "--dry-run"],
    )
    assert bootstrap_module.main() == 0


def test_the_exit_code_is_zero_when_nothing_was_refused(tmp_path, monkeypatch):
    monkeypatch.setattr(bootstrap_module, "bootstrap", lambda *a, **k: [])
    (tmp_path / "write-gate-refusals.json").write_text("[]", encoding="utf-8")
    monkeypatch.setattr(
        "sys.argv", ["bootstrap.py", "--output", str(tmp_path), "--db", ":memory:"]
    )
    assert bootstrap_module.main() == 0
