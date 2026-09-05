"""refresh() writes only through the corpus write gate.

A gate failure during a sweep is the gate working, so the run records the act
and its violations, skips the write and the commit, carries on with the next
act, and reports a non-zero exit at the end (D-058, anchor handover).
"""

import subprocess

from refresh import RefreshReport, main, refresh
from tests.refresh.test_orchestrator import (
    FakeClient,
    FakeMeta,
    FakeParser,
    FakeTreeTransport,
    _init_repo,
    _meta,
    _tree_html,
    _url,
)

_OPEN_GATE = {"uncovered_chars": 0, "buckets": {}}


def _commits(tmp_path) -> list[str]:
    out = subprocess.run(
        ["git", "log", "--format=%s"], cwd=tmp_path, check=True,
        capture_output=True, text=True,
    ).stdout
    return [line for line in out.splitlines() if line]


def test_a_defective_act_is_refused_and_the_run_continues(tmp_path):
    _init_repo(tmp_path)
    crawl_cfg = {"laws": 1}
    tree = FakeTreeTransport({
        _url("laws", 0): _tree_html([(100, "Развален закон"), (200, "Чист закон")]),
    })
    client = FakeClient(available=[100, 200])
    parser = FakeParser({
        100: "**Чл. 1.**/span> Развален текст.\n",
        200: "**Чл. 1.** Чист текст.\n",
    })
    meta = FakeMeta({
        100: _meta(100, "Развален закон", [{"dv": "1/2026", "date": "2026-01-01"}]),
        200: _meta(200, "Чист закон", [{"dv": "2/2026", "date": "2026-01-02"}]),
    })

    report = refresh(
        tmp_path, branch=None, crawl_config=crawl_cfg, today_iso="2026-06-21",
        tree_transport=tree, client=client, parser=parser, metadata_parser=meta,
        coverage_gate=lambda soup, body: dict(_OPEN_GATE),
    )

    # The defective act is refused: no file, no commit, and the violation is
    # named with its locator.
    assert list((tmp_path / "laws").glob("*.md")) != []
    assert [r["doc_id"] for r in report.gate_refusals] == [100]
    assert "tag_remnants" in report.gate_refusals[0]["violations"][0]
    assert not any("Развален закон" in subject for subject in _commits(tmp_path))

    # The run continued and wrote the clean act.
    assert [a["doc_id"] for a in report.added] == [200]
    assert any("[nova] Чист закон" == subject for subject in _commits(tmp_path))


def test_an_existing_act_that_turns_defective_keeps_its_committed_text(tmp_path):
    """The re-scrape is refused, so the corpus keeps the text it had."""
    from fetcher.bg.assembler import assemble_file
    from tests.refresh.test_orchestrator import _commit_initial

    _init_repo(tmp_path)
    committed = _meta(100, "Закон сто", [{"dv": "56/1991", "date": "1991-07-13"}])
    _commit_initial(tmp_path, "laws/zakon-sto.md",
                    assemble_file(committed, "**Чл. 1.** Стар текст.\n"))
    before = (tmp_path / "laws" / "zakon-sto.md").read_bytes()

    report = refresh(
        tmp_path, branch=None, crawl_config={"laws": 1}, today_iso="2026-06-21",
        tree_transport=FakeTreeTransport(
            {_url("laws", 0): _tree_html([(100, "Закон сто")])}),
        client=FakeClient(available=[100]),
        parser=FakeParser({100: "**Чл. 1.**SUP> Нов текст.\n"}),
        metadata_parser=FakeMeta({100: dict(committed)}),
        coverage_gate=lambda soup, body: dict(_OPEN_GATE),
    )

    assert [r["doc_id"] for r in report.gate_refusals] == [100]
    assert (tmp_path / "laws" / "zakon-sto.md").read_bytes() == before
    assert report.reforma == [] and report.popravka == []


def test_the_summary_and_the_exit_code_report_a_refusal(tmp_path, monkeypatch):
    report = RefreshReport()
    assert "REFUSED=0" in report.summary()
    report.gate_refusals.append({"doc_id": 1, "slug": "x", "violations": ["y"]})
    assert "REFUSED=1" in report.summary()

    monkeypatch.setattr("refresh.refresh", lambda *a, **k: report)
    monkeypatch.setattr("sys.argv", ["refresh.py", "--output", str(tmp_path)])
    assert main() == 1
