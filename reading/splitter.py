"""Cut a raw lex.bg act page into blocks: every character of the act's text lands in exactly one block.

The splitter decides nothing about meaning. It locates the legal-content region
the way the old parser did (the common ancestor of the elements with lex.bg's
semantic classes), walks it in document order, breaks text at ``<br>`` and at
block-level children, and gives each non-empty line a *hint*: the lex.bg class
of its nearest classified ancestor. Chrome elements the old parser's denylist
names are dropped before blocks are cut and counted in ``dropped_by_splitter``,
so the act text alone is what the blocks partition. Blocks are then grouped
into *sections* for the labelling call: a new section starts at every heading-
class block and a section never exceeds ``MAX_SECTION_BLOCKS``.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field, asdict

from bs4 import BeautifulSoup, NavigableString, Tag

from fetcher.bg.text_parser import CLASS_MAP, CHROME_DENYLIST, content_region

HEADING_HINTS = frozenset({
    "TitleDocument", "Title", "Portion", "Part", "Heading", "Section", "UnderSection",
    "AdditionalEdicts", "FinalEdicts", "TransitionalFinalEdicts",
})
# Classes whose text is inline content inside an article (cross-references, anchors).
INLINE_KEEP = frozenset({"NewDocReference", "SameDocReference", "LegalDocReference"})
SKIP_CLASSES = (CHROME_DENYLIST - INLINE_KEEP) | {"HistoryOfDocument"}
KNOWN = set(CLASS_MAP) | {"Title"}
MAX_SECTION_BLOCKS = 60
MIN_SECTION_BLOCKS = 25
_WS = re.compile(r"[ \t ]+")


@dataclass
class Block:
    i: int
    text: str
    hint: str


@dataclass
class Section:
    k: int
    blocks: list[int]


@dataclass
class SplitAct:
    blocks: list[Block]
    sections: list[Section]
    dropped_by_splitter: dict[str, int] = field(default_factory=dict)
    has_spine: bool = True

    @property
    def source_text(self) -> str:
        return "\n".join(b.text for b in self.blocks)

    def to_dict(self) -> dict:
        return {
            "has_spine": self.has_spine,
            "dropped_by_splitter": self.dropped_by_splitter,
            "blocks": [asdict(b) for b in self.blocks],
            "sections": [asdict(s) for s in self.sections],
        }


def decode(raw: bytes) -> str:
    try:
        return raw.decode("cp1251")
    except UnicodeDecodeError:
        return raw.decode("utf-8", errors="replace")


def _classes(el: Tag) -> set[str]:
    return set(el.get("class") or [])


def split_lexbg(raw: bytes) -> SplitAct:
    soup = BeautifulSoup(decode(raw), "lxml")
    region, has_spine = content_region(soup)
    lines: list[tuple[str, str]] = []  # (text, hint)
    dropped: dict[str, int] = {}
    buf: list[str] = []
    cur_hint = ["unknown"]

    def flush() -> None:
        text = _WS.sub(" ", "".join(buf)).strip()
        if text:
            lines.append((text, cur_hint[0]))
        buf.clear()

    def walk(node: Tag, hint: str) -> None:
        for child in node.children:
            if isinstance(child, Tag):
                cls = _classes(child)
                skip = cls & SKIP_CLASSES
                if skip and not (cls & INLINE_KEEP):
                    flush()
                    for c in skip:
                        dropped[c] = dropped.get(c, 0) + 1
                    continue
                known = cls & KNOWN
                child_hint = next(iter(known)) if known else hint
                if child.name == "br":
                    flush()
                elif child.name in ("div", "p", "li", "tr", "table", "h1", "h2", "h3", "h4"):
                    flush()
                    prev = cur_hint[0]
                    cur_hint[0] = child_hint
                    walk(child, child_hint)
                    flush()
                    cur_hint[0] = prev
                else:
                    if known and child_hint != cur_hint[0]:
                        flush()
                        prev = cur_hint[0]
                        cur_hint[0] = child_hint
                        walk(child, child_hint)
                        flush()
                        cur_hint[0] = prev
                    else:
                        walk(child, hint)
            elif type(child) is NavigableString:
                buf.append(str(child))

    walk(region, "unknown")
    flush()
    blocks = [Block(i, t, h) for i, (t, h) in enumerate(lines)]
    return SplitAct(blocks=blocks, sections=_sections(blocks), dropped_by_splitter=dropped, has_spine=has_spine)


_ARTICLE_START = re.compile(r"^(Чл\.|§)\s*\d")


def _sections(blocks: list[Block]) -> list[Section]:
    sections: list[Section] = []
    cur: list[int] = []
    for b in blocks:
        starts = b.hint in HEADING_HINTS and (not cur or blocks[cur[-1]].hint not in HEADING_HINTS)
        if starts and cur:
            sections.append(Section(len(sections), cur))
            cur = []
        if len(cur) >= MAX_SECTION_BLOCKS and (_ARTICLE_START.match(b.text) or len(cur) >= MAX_SECTION_BLOCKS + 20):
            sections.append(Section(len(sections), cur))
            cur = []
        cur.append(b.i)
    if cur:
        sections.append(Section(len(sections), cur))
    # merge small adjacent sections so a labelling call sees a few provisions of context
    merged: list[Section] = []
    for s in sections:
        if merged and len(merged[-1].blocks) + len(s.blocks) <= MAX_SECTION_BLOCKS and len(merged[-1].blocks) < MIN_SECTION_BLOCKS:
            merged[-1].blocks.extend(s.blocks)
        else:
            merged.append(Section(len(merged), list(s.blocks)))
    return merged
