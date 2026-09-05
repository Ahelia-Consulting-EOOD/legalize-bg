"""Waiver contract: equality, not thresholds, and equality on the count.

Design decision 2 of Part II. A violation on a non-waived act fails the run,
and a waived act that no longer violates fails it too, so the waiver file
cannot rot into a permanent amnesty. A waiver pins an expected violation count
per act, so a waived act is not a blind spot: a new remnant landing in one
fails the run as an excess, and a partial repair fails it as count drift until
the waiver is updated.
"""

from pathlib import Path

import pytest

from corpus_integrity.protocol import Violation
from corpus_integrity.waivers import load_waivers, reconcile

_REQUIRED = "  ruling: r\n  owner_signed: 2026-09-05\n  expires: when repaired\n"


def _v(slug: str, locator: str = "1") -> Violation:
    return Violation(check="c", slug=slug, detail="d", locator=locator)


def test_waived_act_is_not_reported():
    unwaived, stale, drift = reconcile("c", [_v("a"), _v("b")], {"a": 1})
    assert [v.slug for v in unwaived] == ["b"]
    assert stale == []
    assert drift == []


def test_stale_waiver_is_reported():
    # 'z' is waived but no longer violates: the waiver has rotted and must fail the run
    unwaived, stale, drift = reconcile("c", [_v("a")], {"a": 1, "z": 3})
    assert unwaived == []
    assert stale == ["z"]
    assert drift == []


def test_a_waived_act_at_its_expected_count_passes():
    unwaived, stale, drift = reconcile("c", [_v("a", "1"), _v("a", "2")], {"a": 2})
    assert (unwaived, stale, drift) == ([], [], [])


def test_a_new_violation_in_a_waived_act_is_reported_as_an_excess():
    """A waiver covers a census, not the act: a new remnant must fail the gate."""
    given = [_v("a", "line 1"), _v("a", "line 2"), _v("a", "line 3")]
    unwaived, stale, drift = reconcile("c", given, {"a": 2})
    assert [v.locator for v in unwaived] == ["line 3"]
    assert stale == []
    assert drift == []


def test_a_partial_repair_of_a_waived_act_is_reported_as_count_drift():
    """Equality is the rule: a count that fell but is not zero fails the run."""
    unwaived, stale, drift = reconcile("c", [_v("a", "line 1")], {"a": 3})
    assert unwaived == []
    assert stale == []
    assert [(d.slug, d.expected, d.actual) for d in drift] == [("a", 3, 1)]


def test_count_agnostic_waivers_accept_any_non_zero_count():
    """The legacy list form pins no count, so only a fall to zero is stale."""
    unwaived, stale, drift = reconcile("c", [_v("a", "1"), _v("a", "2")], {"a": None})
    assert (unwaived, stale, drift) == ([], [], [])


def test_unwaived_violations_are_deterministically_ordered():
    """Line numbers sort numerically, so a run diff is reviewable."""
    given = [
        _v("b", "line 2"),
        _v("a", "line 10"),
        _v("a", "line 2"),
        _v("a", "line 1"),
    ]
    unwaived, _, _ = reconcile("c", given, {})
    assert [(v.slug, v.locator) for v in unwaived] == [
        ("a", "line 1"),
        ("a", "line 2"),
        ("a", "line 10"),
        ("b", "line 2"),
    ]


def test_stale_waivers_and_drift_are_sorted():
    _, stale, drift = reconcile("c", [_v("d", "1")], {"m": 1, "a": 1, "z": 1, "d": 4})
    assert stale == ["a", "m", "z"]
    assert [d.slug for d in drift] == ["d"]


def test_reconcile_refuses_violations_from_another_check():
    with pytest.raises(ValueError, match="violations from other checks"):
        reconcile("c", [Violation(check="other", slug="a", detail="d", locator="1")], {})


def test_violation_requires_a_locator():
    with pytest.raises(ValueError, match="locator must not be empty"):
        Violation(check="c", slug="a", detail="d", locator="")


def test_load_waivers_reads_an_expected_count_per_act(tmp_path: Path):
    path = tmp_path / "waivers.yaml"
    path.write_text(
        "empty_body:\n" + _REQUIRED + "  acts:\n    one: 3\n    two: 1\n",
        encoding="utf-8",
    )
    assert load_waivers(path) == {"empty_body": {"one": 3, "two": 1}}


def test_load_waivers_rejects_the_legacy_count_blind_list_form(tmp_path: Path):
    """A list pins no count, so it turns a waived act back into a blind spot
    for every new violation of the same class. It is a schema error, at the
    runner and at the write gate, so it cannot be reinstated silently."""
    path = tmp_path / "waivers.yaml"
    path.write_text(
        "empty_body:\n" + _REQUIRED + "  acts: [one, two]\n", encoding="utf-8"
    )
    with pytest.raises(ValueError, match="list form is no longer accepted"):
        load_waivers(path)


def test_load_waivers_rejects_an_empty_list_too(tmp_path: Path):
    """An entry with no census yet is `{}`; `[]` is the same defect, smaller."""
    path = tmp_path / "waivers.yaml"
    path.write_text("empty_body:\n" + _REQUIRED + "  acts: []\n", encoding="utf-8")
    with pytest.raises(ValueError, match="list form is no longer accepted"):
        load_waivers(path)


def test_load_waivers_tolerates_an_absent_act_map(tmp_path: Path):
    """A seeded entry whose detector does not exist yet carries no acts."""
    path = tmp_path / "waivers.yaml"
    path.write_text("empty_body:\n" + _REQUIRED + "  acts:\n", encoding="utf-8")
    assert load_waivers(path) == {"empty_body": {}}


def test_load_waivers_tolerates_an_empty_act_map(tmp_path: Path):
    path = tmp_path / "waivers.yaml"
    path.write_text("empty_body:\n" + _REQUIRED + "  acts: {}\n", encoding="utf-8")
    assert load_waivers(path) == {"empty_body": {}}


def test_load_waivers_of_an_empty_file_is_empty(tmp_path: Path):
    path = tmp_path / "waivers.yaml"
    path.write_text("", encoding="utf-8")
    assert load_waivers(path) == {}


def test_load_waivers_rejects_a_malformed_entry(tmp_path: Path):
    path = tmp_path / "waivers.yaml"
    path.write_text("empty_body: [one, two]\n", encoding="utf-8")
    with pytest.raises(ValueError, match="empty_body"):
        load_waivers(path)


@pytest.mark.parametrize("field", ["ruling", "owner_signed", "expires"])
def test_load_waivers_rejects_an_entry_missing_a_mandatory_field(
    tmp_path: Path, field: str
):
    """Directive 12: a waiver is dated, signed and names its expiry condition."""
    lines = [line for line in _REQUIRED.splitlines(True) if not line.strip().startswith(field)]
    path = tmp_path / "waivers.yaml"
    path.write_text("empty_body:\n" + "".join(lines) + "  acts: []\n", encoding="utf-8")
    with pytest.raises(ValueError, match=field):
        load_waivers(path)


def test_load_waivers_rejects_acts_that_are_not_a_mapping(tmp_path: Path):
    path = tmp_path / "waivers.yaml"
    path.write_text("empty_body:\n" + _REQUIRED + "  acts: 12\n", encoding="utf-8")
    with pytest.raises(ValueError, match="mapping"):
        load_waivers(path)


def test_load_waivers_rejects_a_non_positive_expected_count(tmp_path: Path):
    """A count of zero is a stale waiver written down, not a waiver."""
    path = tmp_path / "waivers.yaml"
    path.write_text(
        "empty_body:\n" + _REQUIRED + "  acts:\n    one: 0\n", encoding="utf-8"
    )
    with pytest.raises(ValueError, match="one"):
        load_waivers(path)


def test_the_repository_waiver_file_loads():
    """The committed waiver file is the one CI runs against."""
    repo = Path(__file__).resolve().parents[2]
    waivers = load_waivers(repo / "docs" / "data" / "waivers.yaml")
    assert {"frontmatter_dates", "empty_body", "no_article_anchor"} <= set(waivers)


def test_the_repository_waiver_file_pins_the_census_counts():
    """W-002 and W-003: the enumerated sets the machine floor runs green against."""
    repo = Path(__file__).resolve().parents[2]
    waivers = load_waivers(repo / "docs" / "data" / "waivers.yaml")
    remnants, chrome = waivers["tag_remnants"], waivers["chrome"]
    assert (len(remnants), sum(remnants.values())) == (80, 771)
    assert (len(chrome), sum(chrome.values())) == (1, 2)
