"""CLI contract: hard fail, deterministic enumeration, machine-readable summary.

Design decision 3 of Part II: exit code 1 on any violation. There is no report
mode (Owner Directive 12).
"""

import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]

_SIGNED = "  ruling: r\n  owner_signed: 2026-09-05\n  expires: when repaired\n"


def _run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "corpus_integrity", *args],
        capture_output=True,
        text=True,
        cwd=REPO,
    )


def _corpus(tmp_path: Path, body: str, name: str = "bad", waivers: str = "{}\n") -> Path:
    d = tmp_path / "laws"
    d.mkdir(exist_ok=True)
    (d / f"{name}.md").write_text(f"---\ntitulo: X\n---\n{body}\n", encoding="utf-8")
    (tmp_path / "waivers.yaml").write_text(waivers, encoding="utf-8")
    return tmp_path


def test_exit_code_1_on_violation(tmp_path: Path):
    root = _corpus(tmp_path, "**Чл. 1.**/span>.")
    r = _run("--root", str(root), "--waivers", str(root / "waivers.yaml"))
    assert r.returncode == 1
    assert "tag_remnants" in r.stdout


def test_exit_code_0_when_clean(tmp_path: Path):
    root = _corpus(tmp_path, "**Чл. 1.** Текст.", name="ok")
    r = _run("--root", str(root), "--waivers", str(root / "waivers.yaml"))
    assert r.returncode == 0


def test_waived_act_passes(tmp_path: Path):
    root = _corpus(
        tmp_path,
        "**Чл. 1.**/span>.",
        waivers="tag_remnants:\n" + _SIGNED + "  acts:\n    bad: 1\n",
    )
    r = _run("--root", str(root), "--waivers", str(root / "waivers.yaml"))
    assert r.returncode == 0, r.stdout


def test_a_new_violation_in_a_waived_act_fails_the_run(tmp_path: Path):
    """The waiver pins a count, so a waived act is not a blind spot."""
    root = _corpus(
        tmp_path,
        "**Чл. 1.**/span>.\n**Чл. 2.**/span>.",
        waivers="tag_remnants:\n" + _SIGNED + "  acts:\n    bad: 1\n",
    )
    r = _run("--root", str(root), "--waivers", str(root / "waivers.yaml"), "--json")
    assert r.returncode == 1
    assert json.loads(r.stdout)["checks"]["tag_remnants"]["violations"] == 1


def test_a_partial_repair_of_a_waived_act_fails_as_count_drift(tmp_path: Path):
    root = _corpus(
        tmp_path,
        "**Чл. 1.**/span>.",
        waivers="tag_remnants:\n" + _SIGNED + "  acts:\n    bad: 4\n",
    )
    r = _run("--root", str(root), "--waivers", str(root / "waivers.yaml"))
    assert r.returncode == 1
    assert "COUNT_DRIFT" in r.stdout
    assert "bad" in r.stdout


def test_stale_waiver_fails_the_run(tmp_path: Path):
    root = _corpus(
        tmp_path,
        "**Чл. 1.** Текст.",
        name="ok",
        waivers="tag_remnants:\n" + _SIGNED + "  acts:\n    gone: 2\n",
    )
    r = _run("--root", str(root), "--waivers", str(root / "waivers.yaml"))
    assert r.returncode == 1
    assert "STALE_WAIVER" in r.stdout
    assert "gone" in r.stdout


def test_stale_and_drift_rows_keep_the_slug_in_the_second_column(tmp_path: Path):
    """Regenerating a waiver list from `--enumerate` must not read a row label
    as an act slug: every row is `label<TAB>slug<TAB>locator<TAB>detail`."""
    d = tmp_path / "laws"
    d.mkdir()
    (d / "drifted.md").write_text("---\ntitulo: X\n---\nx/span>\n", encoding="utf-8")
    (tmp_path / "waivers.yaml").write_text(
        "tag_remnants:\n" + _SIGNED + "  acts:\n    drifted: 3\n    gone: 1\n",
        encoding="utf-8",
    )
    r = _run(
        "--root", str(tmp_path),
        "--waivers", str(tmp_path / "waivers.yaml"),
        "--check", "tag_remnants",
        "--enumerate",
    )
    rows = [line.split("\t") for line in r.stdout.splitlines() if "\t" in line]
    assert [(row[0], row[1]) for row in rows] == [
        ("STALE_WAIVER", "gone"),
        ("COUNT_DRIFT", "drifted"),
    ]
    assert all(len(row) == 4 for row in rows)


def test_enumerate_prints_tab_separated_rows_in_a_deterministic_order(tmp_path: Path):
    d = tmp_path / "laws"
    d.mkdir()
    (d / "b.md").write_text("---\ntitulo: X\n---\nx/span>\n", encoding="utf-8")
    (d / "a.md").write_text(
        "---\ntitulo: X\n---\n" + "\n" * 9 + "x/span>\nx/span>\n", encoding="utf-8"
    )
    (tmp_path / "waivers.yaml").write_text("{}\n", encoding="utf-8")
    r = _run(
        "--root", str(tmp_path),
        "--waivers", str(tmp_path / "waivers.yaml"),
        "--check", "tag_remnants",
        "--enumerate",
    )
    rows = [line for line in r.stdout.splitlines() if "\t" in line]
    assert [row.split("\t")[:3] for row in rows] == [
        ["tag_remnants", "a", "line 10"],
        ["tag_remnants", "a", "line 11"],
        ["tag_remnants", "b", "line 1"],
    ]


def test_json_summary_reports_per_check_counts(tmp_path: Path):
    root = _corpus(tmp_path, "**Чл. 1.**/span>.")
    r = _run("--root", str(root), "--waivers", str(root / "waivers.yaml"), "--json")
    payload = json.loads(r.stdout)
    assert payload["acts"] == 1
    assert payload["checks"]["tag_remnants"] == {
        "violations": 1,
        "stale_waivers": [],
        "count_drift": [],
    }
    assert payload["checks"]["chrome"]["violations"] == 0
    assert payload["inert_waivers"] == []


def test_json_stays_valid_json_when_a_waiver_is_stale(tmp_path: Path):
    """A machine consumer must not break on the very event it reports."""
    root = _corpus(
        tmp_path,
        "**Чл. 1.** Текст.",
        name="ok",
        waivers="tag_remnants:\n" + _SIGNED + "  acts:\n    gone: 2\n",
    )
    r = _run("--root", str(root), "--waivers", str(root / "waivers.yaml"), "--json")
    assert r.returncode == 1
    payload = json.loads(r.stdout)
    assert payload["checks"]["tag_remnants"]["stale_waivers"] == ["gone"]


def test_json_carries_count_drift(tmp_path: Path):
    root = _corpus(
        tmp_path,
        "**Чл. 1.**/span>.",
        waivers="tag_remnants:\n" + _SIGNED + "  acts:\n    bad: 4\n",
    )
    r = _run("--root", str(root), "--waivers", str(root / "waivers.yaml"), "--json")
    assert r.returncode == 1
    assert json.loads(r.stdout)["checks"]["tag_remnants"]["count_drift"] == [
        {"slug": "bad", "expected": 4, "actual": 1}
    ]


def test_json_and_enumerate_together_stay_valid_json(tmp_path: Path):
    root = _corpus(tmp_path, "**Чл. 1.**/span>.")
    r = _run(
        "--root", str(root),
        "--waivers", str(root / "waivers.yaml"),
        "--json",
        "--enumerate",
    )
    assert json.loads(r.stdout)["checks"]["tag_remnants"]["violations"] == 1


def test_a_waiver_without_a_detector_is_reported_as_inert(tmp_path: Path):
    """A seeded entry no check can reach is neither honoured nor stale."""
    root = _corpus(
        tmp_path,
        "**Чл. 1.** Текст.",
        name="ok",
        waivers="empty_body:\n" + _SIGNED + "  acts:\n    x: 1\n",
    )
    r = _run("--root", str(root), "--waivers", str(root / "waivers.yaml"))
    assert r.returncode == 0
    assert "empty_body: waived without a detector; entry is inert" in r.stdout


def test_check_filter_runs_only_the_named_check(tmp_path: Path):
    root = _corpus(tmp_path, "**Чл. 1.**/span>.")
    r = _run(
        "--root", str(root),
        "--waivers", str(root / "waivers.yaml"),
        "--check", "chrome",
        "--json",
    )
    assert r.returncode == 0
    assert list(json.loads(r.stdout)["checks"]) == ["chrome"]


def test_unknown_check_name_is_refused(tmp_path: Path):
    root = _corpus(tmp_path, "**Чл. 1.** Текст.", name="ok")
    r = _run("--root", str(root), "--waivers", str(root / "waivers.yaml"),
             "--check", "no_such_check")
    assert r.returncode == 2
    assert "no_such_check" in r.stderr


def test_missing_waiver_file_is_refused(tmp_path: Path):
    """A mistyped path must not pass silently.

    Tolerating it would run the gate with no waiver set at all, and stale
    waivers, the half of reconciliation that keeps the file honest, would
    never be reported.
    """
    root = _corpus(tmp_path, "**Чл. 1.** Текст.", name="ok")
    r = _run("--root", str(root), "--waivers", str(root / "nope.yaml"))
    assert r.returncode == 2
    assert "nope.yaml" in r.stderr


def test_an_unsigned_waiver_entry_is_refused(tmp_path: Path):
    """Directive 12: the schema error is a usage error, not a traceback."""
    root = _corpus(
        tmp_path,
        "**Чл. 1.** Текст.",
        name="ok",
        waivers="tag_remnants:\n  ruling: r\n  acts: []\n",
    )
    r = _run("--root", str(root), "--waivers", str(root / "waivers.yaml"))
    assert r.returncode == 2
    assert "owner_signed" in r.stderr
    assert "Traceback" not in r.stderr


def test_an_empty_corpus_root_is_refused(tmp_path: Path):
    """A gate that reports success on zero coverage is not a gate."""
    (tmp_path / "waivers.yaml").write_text("{}\n", encoding="utf-8")
    r = _run("--root", str(tmp_path), "--waivers", str(tmp_path / "waivers.yaml"))
    assert r.returncode == 2
    assert "zero acts" in r.stderr


def test_the_real_corpus_passes_with_the_committed_waivers():
    """The gate CI runs: green on the corpus at HEAD, or the PR cannot merge."""
    if not (REPO / "laws").is_dir():
        import pytest

        pytest.skip("no corpus in this checkout")
    r = _run("--root", str(REPO), "--waivers", str(REPO / "docs/data/waivers.yaml"))
    assert r.returncode == 0, r.stdout
