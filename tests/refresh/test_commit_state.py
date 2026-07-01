"""Tests for the typed corpus commit and the resume checkpoint."""

import subprocess
from pathlib import Path

import pytest

from refresh import _git_commit_typed, load_state, save_state


def _init_repo(tmp_path: Path) -> Path:
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "t@t.t"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "T"], cwd=tmp_path, check=True)
    return tmp_path


def _log(tmp_path: Path, fmt: str) -> str:
    return subprocess.run(
        ["git", "log", "-1", f"--format={fmt}"],
        cwd=tmp_path, check=True, capture_output=True, text=True,
    ).stdout.strip()


# --- _git_commit_typed ------------------------------------------------------


def test_commit_reforma_subject_and_metadata(tmp_path):
    _init_repo(tmp_path)
    f = tmp_path / "laws" / "act.md"
    f.parent.mkdir()
    f.write_text("content", encoding="utf-8")
    _git_commit_typed(f, "reforma", "Закон за тест", doc_id=123,
                      date="2024-08-06", cwd=tmp_path)
    assert _log(tmp_path, "%s") == "[reforma] Закон за тест"
    body = _log(tmp_path, "%b")
    assert "Source-Id: lexbg-123" in body
    assert "Source-Date: 2024-08-06" in body
    assert "Norm-Id: 123" in body


def test_commit_sets_author_date_from_legislative_date(tmp_path):
    _init_repo(tmp_path)
    f = tmp_path / "laws" / "act.md"
    f.parent.mkdir()
    f.write_text("content", encoding="utf-8")
    _git_commit_typed(f, "nova", "Нов закон", doc_id=9,
                      date="2026-06-01", cwd=tmp_path)
    # %ad short = author date; must reflect the legislative date, not today.
    assert _log(tmp_path, "%ad").startswith("") and "2026-06-01" in _log(tmp_path, "%ai")


def test_commit_does_not_backdate_committer_date(tmp_path):
    """D-048: only author-date is backdated to the legislative date; committer
    date stays at real commit time so shared-main `git log` ordering and
    date-based freshness monitoring work. Regression guard against re-introducing
    GIT_COMMITTER_DATE backdating (which made origin/main appear to move
    backwards for the DRS consumer)."""
    _init_repo(tmp_path)
    f = tmp_path / "laws" / "act.md"
    f.parent.mkdir()
    f.write_text("content", encoding="utf-8")
    _git_commit_typed(f, "popravka", "Стар закон", doc_id=7,
                      date="2019-01-01", cwd=tmp_path)
    assert _log(tmp_path, "%aI").startswith("2019-01-01")       # author = legislative
    assert not _log(tmp_path, "%cI").startswith("2019-01-01")   # committer = real (not backdated)


def test_commit_null_date_emits_unknown_source_date(tmp_path):
    _init_repo(tmp_path)
    f = tmp_path / "laws" / "act.md"
    f.parent.mkdir()
    f.write_text("content", encoding="utf-8")
    _git_commit_typed(f, "nova", "Без дата", doc_id=5, date=None, cwd=tmp_path)
    assert "Source-Date: unknown" in _log(tmp_path, "%b")


def test_commit_typed_is_noop_when_nothing_staged(tmp_path):
    # Resume idempotency: re-committing an act whose file already matches HEAD
    # must be a no-op (no error, no second commit), so a crash-then-resume that
    # re-processes an already-committed act does not blow up on "nothing to
    # commit".
    _init_repo(tmp_path)
    f = tmp_path / "laws" / "act.md"
    f.parent.mkdir()
    f.write_text("content", encoding="utf-8")
    _git_commit_typed(f, "nova", "Закон", doc_id=1, date="2026-01-01", cwd=tmp_path)
    head1 = _log(tmp_path, "%H")
    # Identical content -> nothing staged -> must not raise, must not commit.
    _git_commit_typed(f, "nova", "Закон", doc_id=1, date="2026-01-01", cwd=tmp_path)
    assert _log(tmp_path, "%H") == head1


def test_commit_otmyana_subject(tmp_path):
    _init_repo(tmp_path)
    f = tmp_path / "laws" / "act.md"
    f.parent.mkdir()
    f.write_text("content", encoding="utf-8")
    _git_commit_typed(f, "otmyana", "Отменен закон", doc_id=7,
                      date="2026-06-21", cwd=tmp_path)
    assert _log(tmp_path, "%s") == "[otmyana] Отменен закон"


# --- checkpoint state -------------------------------------------------------


def test_load_state_missing_file_returns_empty(tmp_path):
    assert load_state(tmp_path / "nope.json") == {}


def test_save_then_load_state_roundtrips(tmp_path):
    p = tmp_path / "state.json"
    save_state(p, {100: "nova", 200: "reforma"})
    assert load_state(p) == {100: "nova", 200: "reforma"}


def test_state_keys_are_ints_after_reload(tmp_path):
    p = tmp_path / "state.json"
    save_state(p, {42: "unchanged"})
    reloaded = load_state(p)
    assert 42 in reloaded  # int key, not "42"
    assert reloaded[42] == "unchanged"
