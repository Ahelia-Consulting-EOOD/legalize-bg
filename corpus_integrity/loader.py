"""Corpus iteration and frontmatter/body split, with no database.

Design decision 1 of Part II: the checker reads the committed Markdown tree
only. That is what lets it gate every pull request, where `catalog.db` is
absent and 21 real-corpus tests self-skip.
"""

import re
from pathlib import Path
from typing import Iterator

import yaml

from corpus_integrity.protocol import Act

# Every corpus directory, in a fixed order so a run diff is reviewable.
# A directory that a checkout does not carry is skipped silently: the
# categories are added over time and an absent one is not a defect.
CATEGORY_DIRS: tuple[str, ...] = (
    "laws",
    "codes",
    "ordinances",
    "regulations",
    "implementing",
    "postanovleniya",
)

_DELIMITER = "---\n"

# The closing delimiter is a LINE that is exactly `---`, never a substring. A
# plain `raw.split("---\n", 2)` ends the frontmatter on an indented `---`
# inside a YAML block scalar, silently dropping every field after it into the
# body with no error at all.
_CLOSING = re.compile(r"(?m)^---$\n?")


def iter_acts(root: Path) -> Iterator[Act]:
    """Yield every act under `root`, ordered by category then by file name."""
    root = Path(root)
    for category in CATEGORY_DIRS:
        directory = root / category
        if not directory.is_dir():
            continue
        for path in sorted(directory.glob("*.md"), key=lambda p: p.name):
            yield _read_act(path, category)


def _read_act(path: Path, category: str) -> Act:
    try:
        raw = path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        # lex.bg serves windows-1251 and the pipeline transcodes, so a decode
        # slip is a real possibility. A byte offset with no file name is
        # unusable across 3,624 acts.
        raise ValueError(f"{path}: not valid UTF-8: {exc}") from exc
    return act_from_text(path, raw, category=category)


def act_from_text(path: Path, raw: str, *, category: str | None = None) -> Act:
    """Split one act's serialised text exactly as the corpus walk splits it.

    Public because the write gate checks an act before it is a file: reusing
    this split is what makes a locator the gate prints identical to the one CI
    prints for the same act, line for line.
    """
    path = Path(path)
    category = category if category is not None else path.parent.name
    if not raw.startswith(_DELIMITER):
        raise ValueError(f"{path}: missing YAML frontmatter")
    rest = raw[len(_DELIMITER) :]
    closing = _CLOSING.search(rest)
    if closing is None:
        raise ValueError(f"{path}: unterminated YAML frontmatter")
    frontmatter_text, body = rest[: closing.start()], rest[closing.end() :]
    try:
        frontmatter = yaml.safe_load(frontmatter_text) or {}
    except yaml.YAMLError as exc:
        raise ValueError(f"{path}: unparsable YAML frontmatter: {exc}") from exc
    if not isinstance(frontmatter, dict):
        raise ValueError(f"{path}: frontmatter is not a mapping")
    return Act(
        slug=path.stem,
        path=path,
        category=category,
        frontmatter=frontmatter,
        body=body,
    )
