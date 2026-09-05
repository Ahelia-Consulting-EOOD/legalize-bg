"""The records and the one protocol every corpus-integrity check satisfies.

Design decision 5 of Part II: one check protocol, so every later defect class
plugs into the runner without touching it.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Protocol, runtime_checkable


@dataclass(frozen=True)
class Act:
    """One corpus act, split into frontmatter and body.

    `body` is the raw Markdown after the closing frontmatter delimiter, so its
    first line is line 1 for every locator a check emits.
    """

    slug: str
    path: Path
    category: str
    frontmatter: dict
    body: str


@dataclass(frozen=True)
class Violation:
    """One failure of the correctness floor, addressed precisely enough to walk.

    `locator` is a line number, an article key or a byte offset, and is never
    empty: a violation a reviewer cannot navigate to is not actionable.
    """

    check: str
    slug: str
    detail: str
    locator: str

    def __post_init__(self) -> None:
        if not self.locator:
            raise ValueError(f"{self.check}/{self.slug}: locator must not be empty")


@runtime_checkable
class Check(Protocol):
    """A defect-class detector over the whole corpus."""

    name: str

    def run(self, acts: Iterable[Act]) -> list[Violation]: ...
