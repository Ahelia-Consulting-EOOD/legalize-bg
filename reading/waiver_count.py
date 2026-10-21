"""Lower one act's count in the waiver file, as a waiver's expiry provides ("each act leaves the waiver as it is repaired").

A text edit, not a YAML round trip, so the file's comments and order stay as they are.
This module writes the waiver file only; it neither names a corpus directory nor assembles acts.
"""
from __future__ import annotations

import re
from pathlib import Path

_SECTION = re.compile(r"^(\w+):\s*$")
_ACTS = re.compile(r"^\s+acts:\s*$")
_ENTRY = re.compile(r"^(\s+)([\w-]+):\s*(\d+)\s*$")


def lower_count(waivers_path: Path, check: str, slug: str, count: int) -> str | None:
    """Set the act's count under ``check`` to ``count`` when that is lower, removing the act at zero.

    Returns the file's text before the change, for ``restore``, or None when nothing changed.
    A count is only ever lowered: a text with more violations than waived is the gate's to refuse.
    """
    before = waivers_path.read_text(encoding="utf-8")
    lines = before.split("\n")
    section, head = None, None
    for k, line in enumerate(lines):
        if _SECTION.match(line):
            section, head = _SECTION.match(line).group(1), None
            continue
        if section == check and _ACTS.match(line):
            head = k
            continue
        m = _ENTRY.match(line)
        if section != check or head is None or not m or m.group(2) != slug or count >= int(m.group(3)):
            continue
        if count:
            lines[k] = f"{m.group(1)}{slug}: {count}"
        else:
            del lines[k]
            rest = lines[head + 1:]
            end = next((j for j, r in enumerate(rest) if _SECTION.match(r)), len(rest))
            if not any(_ENTRY.match(r) for r in rest[:end]):
                lines[head] = lines[head].rstrip() + " {}"  # the last act left: an empty map, not a null
        waivers_path.write_text("\n".join(lines), encoding="utf-8")
        return before
    return None


def restore(waivers_path: Path, before: str) -> None:
    """Put the waiver file back as ``lower_count`` found it, when the write it was lowered for is refused."""
    waivers_path.write_text(before, encoding="utf-8")
