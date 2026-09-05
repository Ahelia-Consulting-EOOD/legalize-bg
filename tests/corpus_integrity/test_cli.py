"""CLI contract: hard fail, deterministic enumeration, machine-readable summary.

Design decision 3 of Part II: exit code 1 on any violation. There is no report
mode (Owner Directive 12).
"""

import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


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
        waivers="tag_remnants:\n  ruling: r\n  acts: [bad]\n",
    )
    r = _run("--root", str(root), "--waivers", str(root / "waivers.yaml"))
    assert r.returncode == 0, r.stdout


def test_stale_waiver_fails_the_run(tmp_path: Path):
    root = _corpus(
        tmp_path,
        "**Чл. 1.** Текст.",
        name="ok",
        waivers="tag_remnants:\n  ruling: r\n  acts: [gone]\n",
    )
    r = _run("--root", str(root), "--waivers", str(root / "waivers.yaml"))
    assert r.returncode == 1
    assert "STALE WAIVER" in r.stdout
    assert "gone" in r.stdout


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
    assert payload["checks"]["tag_remnants"] == {"violations": 1, "stale_waivers": 0}
    assert payload["checks"]["chrome"] == {"violations": 0, "stale_waivers": 0}
    assert payload["inert_waivers"] == []


def test_a_waiver_without_a_detector_is_reported_as_inert(tmp_path: Path):
    """A seeded entry no check can reach is neither honoured nor stale."""
    root = _corpus(
        tmp_path,
        "**Чл. 1.** Текст.",
        name="ok",
        waivers="empty_body:\n  ruling: r\n  acts: [x]\n",
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
