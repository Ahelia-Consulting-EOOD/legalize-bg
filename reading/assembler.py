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
_ART = re.compile(r"^(Чл\.\s*\d+[а-яa-z]?\d?\.|Член\s+единствен\.)")
_SIGN = re.compile(r"^(§\s*\d+[а-яa-z]?\.|Параграф\s+единствен\.)")


JOIN_PREVIOUS = {"continuation"}
# a heading line that is only a number, e.g. "Глава първа." or "Раздел I.", takes the name line that follows
_NUMBERED_HEADING_ONLY = re.compile(r"^(Част|Дял|Глава|Раздел|Подраздел)\s+[\wIVXLC]+(\s*\"[а-я]\")?\.?$")
# the second line of a provisions heading: "КЪМ ЗАКОНА ЗА ИЗМЕНЕНИЕ …"
_KAM = re.compile(r"^(КЪМ|Към|към)\s")
_HEADING_WORD = re.compile(r"^(Част|Дял|Глава|Раздел|Подраздел|Допълнителн|Преходни|Заключителни|Приложение)")


def assemble(blocks: list[Block], smap: dict[int, dict]) -> tuple[str, list[int], list[int]]:
    """Return (markdown, placed block indices in order, dropped block indices)."""
    lines, placed, dropped = assemble_lines(blocks, smap)
    return "\n\n".join(line for line, _ in lines) + "\n", placed, dropped


def assemble_lines(blocks: list[Block], smap: dict[int, dict]) -> tuple[list[tuple[str, list[int]]], list[int], list[int]]:
    """Return ([(markdown line, block indices it copies)], placed, dropped).

    Two deterministic joins reproduce the corpus convention: consecutive blocks
    with the same heading label form one heading line (lex.bg prints "Глава
    първа." and its name on two lines), and a ``continuation`` block joins the
    previous line. An ``article_title`` joins the article head that follows it.
    """
    lines: list[tuple[str, list[int]]] = []
    placed: list[int] = []
    dropped: list[int] = []
    pending_title: tuple[str, int] | None = None
    last_label: str | None = None
    for b in blocks:
        e = smap.get(b.i)
        label = e["label"] if e else "unknown"
        if label == "drop":
            dropped.append(b.i)
            continue
        placed.append(b.i)
        if pending_title is not None and label != "article_head":
            lines.append((pending_title[0], [pending_title[1]]))
            pending_title = None
            last_label = "article_title"
        if (label in HEADING_PREFIX and last_label == label and lines
                and ((_NUMBERED_HEADING_ONLY.match(strip_line(lines[-1][0])) and not _HEADING_WORD.match(b.text))
                     or _KAM.match(b.text)
                     or (label == "annex_heading" and strip_line(lines[-1][0]).startswith("Приложение") and not b.text.startswith("Приложение")))):
            text, idxs = lines[-1]
            lines[-1] = (f"{text} {b.text}", idxs + [b.i])
        elif label in JOIN_PREVIOUS and lines and last_label != "prehistory":
            text, idxs = lines[-1]
            lines[-1] = (f"{text} {b.text}", idxs + [b.i])
        elif label in HEADING_PREFIX:
            lines.append((HEADING_PREFIX[label] + b.text, [b.i]))
        elif label == "prehistory":
            lines.append((f"*{b.text}*", [b.i]))
        elif label == "article_title":
            pending_title = (b.text, b.i)
        elif label == "article_head":
            m = _ART.match(b.text)
            body = f"**{m.group(1)}**{b.text[m.end():]}" if m else b.text
            idxs = [b.i]
            if pending_title is not None:
                body = f"{pending_title[0]} {body}"
                idxs = [pending_title[1], b.i]
                pending_title = None
            lines.append((body, idxs))
        elif label == "paragraph_sign":
            m = _SIGN.match(b.text)
            lines.append((f"**{m.group(1)}**{b.text[m.end():]}" if m else b.text, [b.i]))
        else:
            lines.append((b.text, [b.i]))
        last_label = label
    if pending_title is not None:
        lines.append((pending_title[0], [pending_title[1]]))
    return lines, placed, dropped


def strip_line(line: str) -> str:
    """Remove exactly the markers the assembler adds to one line."""
    line = re.sub(r"^#{1,5} ", "", line)
    if line.startswith("*") and line.endswith("*") and not line.startswith("**"):
        line = line[1:-1]
    return line.replace("**", "")


def strip_markers(markdown: str) -> str:
    return "\n".join(strip_line(l.rstrip("\n")) for l in markdown.split("\n\n"))
