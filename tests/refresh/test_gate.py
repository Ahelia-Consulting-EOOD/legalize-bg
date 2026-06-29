"""Tests for the coverage gate wired into refresh().

The gate calls coverage_gate(soup, body) for every ADDED and EXISTING act.
When uncovered_chars > threshold the act must be:
  (a) NOT written to disk  — no .md file created / modified
  (b) NOT committed        — git HEAD unchanged
  (c) classified as gate-fail in the checkpoint state
  (d) present in report.gate_failures
  (e) present in the written gate-report.json

A stub gate (lambda returning uncovered_chars=999) is used to exercise the
gate path without any real HTML or parser.  The counterpart uses a pass-through
gate (uncovered_chars=0) to confirm the happy path is unaffected.
"""

import json
import os
import subprocess
from pathlib import Path

import pytest

from fetcher.bg.assembler import assemble_file
from refresh import refresh, load_state


# ---------------------------------------------------------------------------
# Shared test infrastructure
# ---------------------------------------------------------------------------

class FakeTreeTransport:
    def __init__(self, doc_ids):
        links = "".join(f'<a href="/laws/ldoc/{d}">Закон {d}</a>' for d in doc_ids)
        html = f"<html><body>{links}</body></html>"
        self._bytes = html.encode("cp1251")

    def get_tree_page(self, url):
        return self._bytes


class FakeClient:
    """Returns the doc_id int as an opaque soup token."""

    def __init__(self, available):
        self._available = set(available)

    def fetch_soup(self, doc_id):
        if doc_id not in self._available:
            raise KeyError(f"doc {doc_id} not fetchable")
        return doc_id

    def close(self):
        pass


class FakeParser:
    def __init__(self, bodies):
        self._bodies = bodies

    def convert(self, token):
        return self._bodies[token]


class FakeMeta:
    def __init__(self, metas):
        self._metas = metas

    def parse(self, token, doc_id, category):
        return dict(self._metas[token])


def _init_repo(tmp_path):
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "t@t.t"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "T"], cwd=tmp_path, check=True)


def _meta(doc_id, title):
    return {
        "titulo": title,
        "identificador": str(doc_id),
        "pais": "bg",
        "rango": "закон",
        "fecha_publicacion": "1991-07-13",
        "ultima_actualizacion": "1991-07-13",
        "estado": "vigente",
        "fuente": "lex.bg",
        "category": "laws",
        "amendment_history": [],
    }


def _head(tmp_path):
    return subprocess.run(["git", "rev-parse", "HEAD"], cwd=tmp_path,
                          check=True, capture_output=True, text=True).stdout.strip()


# ---------------------------------------------------------------------------
# Gate-failure tests (ADDED act)
# ---------------------------------------------------------------------------

def test_gate_fail_added_act_is_not_written(tmp_path):
    """An ADDED act whose gate fires must not have a .md file created."""
    _init_repo(tmp_path)

    tree = FakeTreeTransport([500])
    client = FakeClient([500])
    parser = FakeParser({500: "Член 1. Тест.\n"})
    meta = FakeMeta({500: _meta(500, "Закон петстотин")})
    fail_gate = lambda soup, body: {"uncovered_chars": 999, "buckets": {"Article": 999}}

    refresh(
        tmp_path, branch=None, crawl_config={"laws": 1}, today_iso="2026-06-21",
        tree_transport=tree, client=client, parser=parser, metadata_parser=meta,
        coverage_gate=fail_gate,
    )

    md_files = list((tmp_path / "laws").glob("*.md")) if (tmp_path / "laws").exists() else []
    assert md_files == [], f"gate-failed act must NOT be written, found: {md_files}"


def test_gate_fail_added_act_is_not_committed(tmp_path):
    """An ADDED act whose gate fires must not produce a git commit."""
    _init_repo(tmp_path)
    # Make an initial commit so HEAD exists
    initial = tmp_path / "README"
    initial.write_text("init")
    subprocess.run(["git", "add", "README"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=tmp_path, check=True)
    head_before = _head(tmp_path)

    tree = FakeTreeTransport([500])
    client = FakeClient([500])
    parser = FakeParser({500: "Член 1. Тест.\n"})
    meta = FakeMeta({500: _meta(500, "Закон петстотин")})
    fail_gate = lambda soup, body: {"uncovered_chars": 999, "buckets": {"Article": 999}}

    refresh(
        tmp_path, branch=None, crawl_config={"laws": 1}, today_iso="2026-06-21",
        tree_transport=tree, client=client, parser=parser, metadata_parser=meta,
        coverage_gate=fail_gate,
    )

    assert _head(tmp_path) == head_before, "gate-failed act must NOT produce a commit"


def test_gate_fail_added_act_sets_state_gate_fail(tmp_path):
    """An ADDED act whose gate fires must record state=='gate-fail' in the checkpoint."""
    _init_repo(tmp_path)

    tree = FakeTreeTransport([500])
    client = FakeClient([500])
    parser = FakeParser({500: "Член 1. Тест.\n"})
    meta = FakeMeta({500: _meta(500, "Закон петстотин")})
    fail_gate = lambda soup, body: {"uncovered_chars": 999, "buckets": {"Article": 999}}

    refresh(
        tmp_path, branch=None, crawl_config={"laws": 1}, today_iso="2026-06-21",
        tree_transport=tree, client=client, parser=parser, metadata_parser=meta,
        coverage_gate=fail_gate,
    )

    state = load_state(tmp_path / ".refresh-state.json")
    assert state[500] == "gate-fail"


def test_gate_fail_added_act_appears_in_report_gate_failures(tmp_path):
    """An ADDED act whose gate fires must appear in report.gate_failures."""
    _init_repo(tmp_path)

    tree = FakeTreeTransport([500])
    client = FakeClient([500])
    parser = FakeParser({500: "Член 1. Тест.\n"})
    meta = FakeMeta({500: _meta(500, "Закон петстотин")})
    fail_gate = lambda soup, body: {"uncovered_chars": 999, "buckets": {"Article": 999}}

    report = refresh(
        tmp_path, branch=None, crawl_config={"laws": 1}, today_iso="2026-06-21",
        tree_transport=tree, client=client, parser=parser, metadata_parser=meta,
        coverage_gate=fail_gate,
    )

    assert len(report.gate_failures) == 1
    rec = report.gate_failures[0]
    assert rec["doc_id"] == 500
    assert rec["uncovered_chars"] == 999


def test_gate_fail_added_act_appears_in_gate_report_json(tmp_path):
    """An ADDED act whose gate fires must appear in the written gate-report.json."""
    _init_repo(tmp_path)

    tree = FakeTreeTransport([500])
    client = FakeClient([500])
    parser = FakeParser({500: "Член 1. Тест.\n"})
    meta = FakeMeta({500: _meta(500, "Закон петстотин")})
    fail_gate = lambda soup, body: {"uncovered_chars": 999, "buckets": {"Article": 999}}

    refresh(
        tmp_path, branch=None, crawl_config={"laws": 1}, today_iso="2026-06-21",
        tree_transport=tree, client=client, parser=parser, metadata_parser=meta,
        coverage_gate=fail_gate,
    )

    report_path = tmp_path / "gate-report.json"
    assert report_path.exists()
    records = json.loads(report_path.read_text(encoding="utf-8"))
    doc_ids = [r["doc_id"] for r in records]
    assert 500 in doc_ids


# ---------------------------------------------------------------------------
# Gate-failure tests (EXISTING act)
# ---------------------------------------------------------------------------

def _commit_initial(tmp_path, rel, text):
    p = tmp_path / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")
    subprocess.run(["git", "add", str(rel)], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-q", "-m", f"[bootstrap] {rel}"],
                   cwd=tmp_path, check=True)


def test_gate_fail_existing_act_is_not_overwritten(tmp_path):
    """An EXISTING act whose gate fires must leave the committed file unchanged."""
    _init_repo(tmp_path)
    m = _meta(100, "Закон сто")
    original_text = assemble_file(m, "Член 1. Оригинал.\n")
    _commit_initial(tmp_path, "laws/zakon-sto.md", original_text)

    tree = FakeTreeTransport([100])
    client = FakeClient([100])
    parser = FakeParser({100: "Член 1. Нов текст.\n"})
    meta = FakeMeta({100: _meta(100, "Закон сто")})
    fail_gate = lambda soup, body: {"uncovered_chars": 999, "buckets": {"Article": 999}}

    refresh(
        tmp_path, branch=None, crawl_config={"laws": 1}, today_iso="2026-06-21",
        tree_transport=tree, client=client, parser=parser, metadata_parser=meta,
        coverage_gate=fail_gate,
    )

    on_disk = (tmp_path / "laws" / "zakon-sto.md").read_text(encoding="utf-8")
    assert "Оригинал" in on_disk, "gate-failed EXISTING act must NOT overwrite the committed file"
    assert "Нов текст" not in on_disk


def test_gate_fail_existing_act_sets_state_gate_fail(tmp_path):
    """An EXISTING act whose gate fires must record state=='gate-fail'."""
    _init_repo(tmp_path)
    m = _meta(100, "Закон сто")
    _commit_initial(tmp_path, "laws/zakon-sto.md", assemble_file(m, "Член 1.\n"))

    tree = FakeTreeTransport([100])
    client = FakeClient([100])
    parser = FakeParser({100: "Член 1. Нов текст.\n"})
    meta = FakeMeta({100: _meta(100, "Закон сто")})
    fail_gate = lambda soup, body: {"uncovered_chars": 999, "buckets": {"Article": 999}}

    refresh(
        tmp_path, branch=None, crawl_config={"laws": 1}, today_iso="2026-06-21",
        tree_transport=tree, client=client, parser=parser, metadata_parser=meta,
        coverage_gate=fail_gate,
    )

    state = load_state(tmp_path / ".refresh-state.json")
    assert state[100] == "gate-fail"


def test_gate_fail_existing_act_appears_in_report_gate_failures(tmp_path):
    """An EXISTING act whose gate fires must appear in report.gate_failures."""
    _init_repo(tmp_path)
    m = _meta(100, "Закон сто")
    _commit_initial(tmp_path, "laws/zakon-sto.md", assemble_file(m, "Член 1.\n"))

    tree = FakeTreeTransport([100])
    client = FakeClient([100])
    parser = FakeParser({100: "Член 1. Нов текст.\n"})
    meta = FakeMeta({100: _meta(100, "Закон сто")})
    fail_gate = lambda soup, body: {"uncovered_chars": 999, "buckets": {"Article": 999}}

    report = refresh(
        tmp_path, branch=None, crawl_config={"laws": 1}, today_iso="2026-06-21",
        tree_transport=tree, client=client, parser=parser, metadata_parser=meta,
        coverage_gate=fail_gate,
    )

    assert len(report.gate_failures) == 1
    rec = report.gate_failures[0]
    assert rec["doc_id"] == 100
    assert rec["slug"] == "zakon-sto"


# ---------------------------------------------------------------------------
# Resume: prior gate-fail entries must survive in the rewritten gate-report.json
# ---------------------------------------------------------------------------

def test_resume_gate_report_includes_prior_gate_fail_entries(tmp_path):
    """On a re-run, doc_ids that were gate-fail in a prior run and are SKIPPED
    (because they already have a checkpoint entry) must still appear in the
    rewritten gate-report.json.

    Regression: the first run writes gate-report.json with doc 500.  A second
    run skips doc 500 (state already has it) and writes a fresh gate-report.json
    that contains only the current-run failures — doc 500 vanishes, under-reporting.
    """
    _init_repo(tmp_path)

    tree = FakeTreeTransport([500])
    client = FakeClient([500])
    parser = FakeParser({500: "Член 1. Тест.\n"})
    meta = FakeMeta({500: _meta(500, "Закон петстотин")})
    fail_gate = lambda soup, body: {"uncovered_chars": 999, "buckets": {"Article": 999}}

    # First run: doc 500 fails the gate → written to gate-report.json
    refresh(
        tmp_path, branch=None, crawl_config={"laws": 1}, today_iso="2026-06-21",
        tree_transport=tree, client=client, parser=parser, metadata_parser=meta,
        coverage_gate=fail_gate,
    )
    state_after_run1 = load_state(tmp_path / ".refresh-state.json")
    assert state_after_run1[500] == "gate-fail"
    report1 = json.loads((tmp_path / "gate-report.json").read_text(encoding="utf-8"))
    assert any(r["doc_id"] == 500 for r in report1), "doc 500 must appear after first run"

    # Second run (resume): doc 500 is skipped because state already has it.
    refresh(
        tmp_path, branch=None, crawl_config={"laws": 1}, today_iso="2026-06-21",
        tree_transport=tree, client=client, parser=parser, metadata_parser=meta,
        coverage_gate=fail_gate,
    )
    report2 = json.loads((tmp_path / "gate-report.json").read_text(encoding="utf-8"))
    assert any(r["doc_id"] == 500 for r in report2), (
        "doc 500 must still appear in gate-report.json after a re-run "
        "(prior gate-fail entries must not be erased on resume)"
    )


# ---------------------------------------------------------------------------
# Passing-gate counterpart
# ---------------------------------------------------------------------------

def test_passing_gate_added_act_is_written_and_committed(tmp_path):
    """An ADDED act whose gate passes must be written and committed normally."""
    _init_repo(tmp_path)

    tree = FakeTreeTransport([500])
    client = FakeClient([500])
    parser = FakeParser({500: "Член 1. Тест.\n"})
    meta = FakeMeta({500: _meta(500, "Закон петстотин")})
    pass_gate = lambda soup, body: {"uncovered_chars": 0, "buckets": {}}

    report = refresh(
        tmp_path, branch=None, crawl_config={"laws": 1}, today_iso="2026-06-21",
        tree_transport=tree, client=client, parser=parser, metadata_parser=meta,
        coverage_gate=pass_gate,
    )

    assert len(report.added) == 1
    assert report.added[0]["doc_id"] == 500
    assert report.gate_failures == []
    slug = report.added[0]["slug"]
    assert (tmp_path / "laws" / f"{slug}.md").exists()


def test_passing_gate_existing_act_is_classified(tmp_path):
    """An EXISTING act whose gate passes must be classified normally."""
    _init_repo(tmp_path)
    m = _meta(100, "Закон сто")
    _commit_initial(tmp_path, "laws/zakon-sto.md", assemble_file(m, "Член 1. Стар.\n"))

    tree = FakeTreeTransport([100])
    client = FakeClient([100])
    parser = FakeParser({100: "Член 1. Нов текст.\n"})
    meta = FakeMeta({100: _meta(100, "Закон сто")})
    pass_gate = lambda soup, body: {"uncovered_chars": 0, "buckets": {}}

    report = refresh(
        tmp_path, branch=None, crawl_config={"laws": 1}, today_iso="2026-06-21",
        tree_transport=tree, client=client, parser=parser, metadata_parser=meta,
        coverage_gate=pass_gate,
    )

    assert report.gate_failures == []
    # Body changed, same history → popravka
    assert [p["doc_id"] for p in report.popravka] == [100]


# ---------------------------------------------------------------------------
# Threshold validation (T5-#1): bad LEGALIZE_COVERAGE_THRESHOLD must not crash
# ---------------------------------------------------------------------------

def test_bad_threshold_env_var_falls_back_to_64(tmp_path, monkeypatch):
    """A non-numeric LEGALIZE_COVERAGE_THRESHOLD must not abort the run.

    Currently `int(os.environ.get(...))` would raise ValueError after up to
    thousands of network requests.  The fix: parse once at function entry with
    try/except and fall back to 64 with a warning.
    """
    _init_repo(tmp_path)

    monkeypatch.setenv("LEGALIZE_COVERAGE_THRESHOLD", "not-a-number")

    tree = FakeTreeTransport([500])
    client = FakeClient([500])
    parser = FakeParser({500: "Член 1. Тест.\n"})
    meta = FakeMeta({500: _meta(500, "Закон петстотин")})
    pass_gate = lambda soup, body: {"uncovered_chars": 0, "buckets": {}}

    # Must not raise — should fall back to threshold=64 gracefully
    report = refresh(
        tmp_path, branch=None, crawl_config={"laws": 1}, today_iso="2026-06-21",
        tree_transport=tree, client=client, parser=parser, metadata_parser=meta,
        coverage_gate=pass_gate,
    )
    # With threshold=64 (fallback) and uncovered_chars=0 the act passes
    assert len(report.added) == 1
    assert report.errors == []
