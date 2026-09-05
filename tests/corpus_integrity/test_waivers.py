"""Waiver contract: equality, not thresholds.

Design decision 2 of Part II. A violation on a non-waived act fails the run,
and a waived act that no longer violates fails it too, so the waiver file
cannot rot into a permanent amnesty.
"""

from pathlib import Path

import pytest

from corpus_integrity.protocol import Violation
from corpus_integrity.waivers import load_waivers, reconcile


def _v(slug: str, locator: str = "1") -> Violation:
    return Violation(check="c", slug=slug, detail="d", locator=locator)


def test_waived_act_is_not_reported():
    unwaived, stale = reconcile("c", [_v("a"), _v("b")], {"a"})
    assert [v.slug for v in unwaived] == ["b"]
    assert stale == []


def test_stale_waiver_is_reported():
    # 'z' is waived but no longer violates: the waiver has rotted and must fail the run
    unwaived, stale = reconcile("c", [_v("a")], {"a", "z"})
    assert unwaived == []
    assert stale == ["z"]


def test_unwaived_violations_are_deterministically_ordered():
    """Line numbers sort numerically, so a run diff is reviewable."""
    given = [
        _v("b", "line 2"),
        _v("a", "line 10"),
        _v("a", "line 2"),
        _v("a", "line 1"),
    ]
    unwaived, _ = reconcile("c", given, set())
    assert [(v.slug, v.locator) for v in unwaived] == [
        ("a", "line 1"),
        ("a", "line 2"),
        ("a", "line 10"),
        ("b", "line 2"),
    ]


def test_stale_waivers_are_sorted():
    _, stale = reconcile("c", [], {"m", "a", "z"})
    assert stale == ["a", "m", "z"]


def test_load_waivers_reads_act_sets_per_check(tmp_path: Path):
    path = tmp_path / "waivers.yaml"
    path.write_text(
        "empty_body:\n"
        '  ruling: "stub pages"\n'
        "  owner_signed: 2026-08-11\n"
        "  acts: [one, two]\n",
        encoding="utf-8",
    )
    assert load_waivers(path) == {"empty_body": {"one", "two"}}


def test_load_waivers_tolerates_an_empty_act_list(tmp_path: Path):
    """A seeded entry whose detector does not exist yet carries no acts."""
    path = tmp_path / "waivers.yaml"
    path.write_text("empty_body:\n  ruling: x\n  acts:\n", encoding="utf-8")
    assert load_waivers(path) == {"empty_body": set()}


def test_load_waivers_of_an_empty_file_is_empty(tmp_path: Path):
    path = tmp_path / "waivers.yaml"
    path.write_text("", encoding="utf-8")
    assert load_waivers(path) == {}


def test_load_waivers_rejects_a_malformed_entry(tmp_path: Path):
    path = tmp_path / "waivers.yaml"
    path.write_text("empty_body: [one, two]\n", encoding="utf-8")
    with pytest.raises(ValueError, match="empty_body"):
        load_waivers(path)


def test_the_repository_waiver_file_loads():
    """The committed waiver file is the one CI runs against."""
    repo = Path(__file__).resolve().parents[2]
    waivers = load_waivers(repo / "docs" / "data" / "waivers.yaml")
    assert {"frontmatter_dates", "empty_body", "no_article_anchor"} <= set(waivers)
