"""Waiver loading and equality reconciliation.

Design decision 2 of Part II: equality, not thresholds. Waivers enumerate
exact acts and, for each, the exact number of violations the census found.
A violation on a non-waived act fails the run; a waived act that no longer
violates fails it too, so the waiver file cannot rot into a permanent amnesty;
and a waived act whose count moved in either direction fails it as well, so a
waived act is not a blind spot for new defects of the same class. This is the
mechanism that keeps Owner Directive 12 („gates block or they do not exist“)
true over time.

A waiver entry is dated, signed and names its expiry condition, because
Directive 12 permits an exception only under „a dated waiver naming its expiry
condition“. `load_waivers` refuses an entry that carries less.
"""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping

import yaml

from corpus_integrity.protocol import Violation

_DIGITS = re.compile(r"(\d+)")

# Directive 12 and COVERAGE-FLOOR acceptance rule 3: no undated, unsigned or
# open-ended waiver. A missing field is a load error, not a default.
REQUIRED_FIELDS: tuple[str, ...] = ("ruling", "owner_signed", "expires")

# `{act slug: expected violation count}`; a `None` count is count-agnostic and
# arises only from the legacy list form of `acts`.
Waived = Mapping[str, int | None]


@dataclass(frozen=True)
class CountDrift:
    """A waived act whose violation count fell without reaching zero.

    Equality is the rule, so a partial repair fails the run until the waiver
    records the new count. Reaching zero is a stale waiver instead.
    """

    slug: str
    expected: int
    actual: int


def _natural_key(text: str) -> tuple[object, ...]:
    """Sort key where embedded numbers order numerically.

    Locators read „line 2“ before „line 10“, which is what a reviewer walking
    a run diff expects.
    """
    return tuple(
        (1, int(part), "") if part.isdigit() else (0, 0, part)
        for part in _DIGITS.split(text)
        if part != ""
    )


def _expected_counts(acts: object, path: Path, check: str) -> dict[str, int | None]:
    """Read the `acts` field of one waiver entry into `{slug: expected count}`."""
    if acts is None:
        return {}
    if isinstance(acts, list):
        # Backward compatibility only. A list pins no count, so it cannot
        # catch a new violation landing in an already waived act.
        return {str(slug): None for slug in acts}
    if not isinstance(acts, dict):
        raise ValueError(
            f"{path}: waiver entry {check!r} has an 'acts' that is neither "
            "a mapping of slug to expected count nor a list"
        )
    counts: dict[str, int | None] = {}
    for slug, count in acts.items():
        if not isinstance(count, int) or isinstance(count, bool) or count < 1:
            raise ValueError(
                f"{path}: waiver entry {check!r} act {str(slug)!r} has a "
                f"non-positive expected count {count!r}"
            )
        counts[str(slug)] = count
    return counts


def load_waivers(path: Path) -> dict[str, dict[str, int | None]]:
    """Read the waiver file into `{check name: {act slug: expected count}}`."""
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError(f"{path}: waiver file is not a mapping")
    waivers: dict[str, dict[str, int | None]] = {}
    for check, entry in data.items():
        if not isinstance(entry, dict):
            raise ValueError(f"{path}: waiver entry {check!r} is not a mapping")
        for field in REQUIRED_FIELDS:
            if not entry.get(field):
                raise ValueError(
                    f"{path}: waiver entry {check!r} has no {field!r}; a waiver "
                    "is dated, signed and names its expiry condition "
                    "(Owner Directive 12)"
                )
        waivers[check] = _expected_counts(entry.get("acts"), Path(path), str(check))
    return waivers


def reconcile(
    check: str, violations: Iterable[Violation], waived: Waived | Iterable[str]
) -> tuple[list[Violation], list[str], list[CountDrift]]:
    """Split violations against a waiver set, on equality of the count.

    Returns, deterministically ordered:

    - the unwaived violations: every violation of an act the waiver does not
      cover, plus the excess when a waived act carries more violations than
      the waiver expects;
    - the stale waivers: waived slugs that no longer violate at all;
    - the count drift: waived slugs whose count fell without reaching zero.

    Any of the three fails the run. The excess rows are the trailing ones in
    locator order: which particular occurrence is new is not knowable from a
    count, so the rows identify the act and the size of the change, not the
    provenance of a line.
    """
    violations = list(violations)
    foreign = sorted({v.check for v in violations if v.check != check})
    if foreign:
        raise ValueError(f"{check}: violations from other checks: {foreign}")

    expected: dict[str, int | None] = (
        dict(waived) if isinstance(waived, Mapping) else {s: None for s in waived}
    )
    by_slug: dict[str, list[Violation]] = {}
    for v in violations:
        by_slug.setdefault(v.slug, []).append(v)

    unwaived: list[Violation] = []
    drift: list[CountDrift] = []
    for slug, found in by_slug.items():
        if slug not in expected:
            unwaived.extend(found)
            continue
        want = expected[slug]
        if want is None or want == len(found):
            continue
        if len(found) > want:
            unwaived.extend(sorted(found, key=lambda v: _natural_key(v.locator))[want:])
        else:
            drift.append(CountDrift(slug=slug, expected=want, actual=len(found)))

    unwaived.sort(key=lambda v: (v.slug, _natural_key(v.locator)))
    stale = sorted(slug for slug in expected if slug not in by_slug)
    drift.sort(key=lambda d: d.slug)
    return unwaived, stale, drift
