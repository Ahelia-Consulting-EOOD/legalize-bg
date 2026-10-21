"""Write corpus Markdown from blocks and their structure map, copying every block's text.

The assembler adds markers only (heading hashes, bold article and § numbers,
italics for the in-force line) and never changes a block's characters. A block
labelled ``drop`` is left out and listed; everything else is placed once, in
block order. ``strip_markers`` removes exactly the markers the assembler adds,
so ``checks.reassembly`` can compare the assembled text with the blocks.
"""
from __future__ import annotations

import re

from .splitter import Block

HEADING_PREFIX = {
    "title": "# ",
    "part_heading": "## ",
    "chapter_heading": "### ",
    "section_heading": "#### ",
    "subsection_heading": "##### ",
    "provisions_heading": "## ",
    "annex_heading": "## ",
}
_ART = re.compile(r"^(Чл\.\s*\d+[а-яa-z]?\d?\.)")
_SIGN = re.compile(r"^(§\s*\d+[а-я]?\.)")


def assemble(blocks: list[Block], smap: dict[int, dict]) -> tuple[str, list[int], list[int]]:
    """Return (markdown, placed block indices in order, dropped block indices)."""
    lines: list[str] = []
    placed: list[int] = []
    dropped: list[int] = []
    pending_title: str | None = None
    for b in blocks:
        e = smap.get(b.i)
        label = e["label"] if e else "unknown"
        if label == "drop":
            dropped.append(b.i)
            continue
        placed.append(b.i)
        if label in HEADING_PREFIX:
            lines.append(HEADING_PREFIX[label] + b.text)
        elif label == "prehistory":
            lines.append(f"*{b.text}*")
        elif label == "article_title":
            pending_title = b.text
        elif label == "article_head":
            m = _ART.match(b.text)
            body = f"**{m.group(1)}**{b.text[m.end():]}" if m else b.text
            if pending_title is not None:
                body = f"{pending_title} {body}"
                pending_title = None
            lines.append(body)
        elif label == "paragraph_sign":
            m = _SIGN.match(b.text)
            lines.append(f"**{m.group(1)}**{b.text[m.end():]}" if m else b.text)
        else:
            if pending_title is not None:
                lines.append(pending_title)
                pending_title = None
            lines.append(b.text)
    if pending_title is not None:
        lines.append(pending_title)
    return "\n\n".join(lines) + "\n", placed, dropped


def strip_markers(markdown: str) -> str:
    out = []
    for line in markdown.split("\n\n"):
        line = line.rstrip("\n")
        line = re.sub(r"^#{1,5} ", "", line)
        if line.startswith("*") and line.endswith("*") and not line.startswith("**"):
            line = line[1:-1]
        line = line.replace("**", "")
        out.append(line)
    return "\n".join(out)
