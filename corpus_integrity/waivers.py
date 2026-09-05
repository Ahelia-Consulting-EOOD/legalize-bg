"""Waiver loading and equality reconciliation.

Design decision 2 of Part II: equality, not thresholds. Waivers enumerate
exact acts. A violation on a non-waived act fails the run, and a waived act
that no longer violates fails it too, so the waiver file cannot rot into a
permanent amnesty. This is the mechanism that keeps Owner Directive 12
(„gates block or they do not exist“) true over time.
"""

import re
from pathlib import Path
from typing import Iterable

import yaml

from corpus_integrity.protocol import Violation

_DIGITS = re.compile(r"(\d+)")


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


def load_waivers(path: Path) -> dict[str, set[str]]:
    """Read the waiver file into `{check name: waived act slugs}`."""
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError(f"{path}: waiver file is not a mapping")
    waivers: dict[str, set[str]] = {}
    for check, entry in data.items():
        if not isinstance(entry, dict):
            raise ValueError(f"{path}: waiver entry {check!r} is not a mapping")
        acts = entry.get("acts") or []
        if not isinstance(acts, list):
            raise ValueError(f"{path}: waiver entry {check!r} has a non-list 'acts'")
        waivers[check] = {str(slug) for slug in acts}
    return waivers


def reconcile(
    check: str, violations: Iterable[Violation], waived: set[str]
) -> tuple[list[Violation], list[str]]:
    """Split violations against a waiver set.

    Returns the unwaived violations, deterministically ordered, and the stale
    waivers: waived slugs that no longer violate and must be removed.
    """
    violations = list(violations)
    foreign = sorted({v.check for v in violations if v.check != check})
    if foreign:
        raise ValueError(f"{check}: violations from other checks: {foreign}")
    violating = {v.slug for v in violations}
    unwaived = sorted(
        (v for v in violations if v.slug not in waived),
        key=lambda v: (v.slug, _natural_key(v.locator)),
    )
    stale = sorted(waived - violating)
    return unwaived, stale
