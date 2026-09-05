"""Corpus iteration and frontmatter/body split, with no database.

Design decision 1 of Part II: the checker reads the committed Markdown tree
only. That is what lets it gate every pull request, where `catalog.db` is
absent and 21 real-corpus tests self-skip.
"""

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
    raw = path.read_text(encoding="utf-8")
    if not raw.startswith(_DELIMITER):
        raise ValueError(f"{path}: missing YAML frontmatter")
    parts = raw.split(_DELIMITER, 2)
    if len(parts) < 3:
        raise ValueError(f"{path}: unterminated YAML frontmatter")
    _, frontmatter_text, body = parts
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
