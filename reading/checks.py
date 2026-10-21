"""Mechanical checks over a structure map. None of them reads meaning.

``coverage``: every block is placed once or dropped once.
``reassembly``: the assembled Markdown, markers removed, equals the placed
blocks' text joined, and a block that is not placed carries the ``drop`` label.
``numbering``: article numbers do not go backwards; alineas restart at (1) per
article and increase by one; items restart per paragraph; § numbers restart
per provisions heading and increase.
``nesting``: an alinea only after an article head; an item only inside an
article, alinea or §; a letter only inside an item.
``addresses``: one Чл. N per act, one § N per provisions block.
``fragments``: no literal markup fragment in placed text.
``confidence``: a block labelled ``unknown`` or with low confidence.
Every failure is an exception ``{"block", "kind", "detail"}`` on one block.
"""
from __future__ import annotations

import re

from .assembler import assemble, strip_markers
from .splitter import Block

FRAGMENTS = ("SUP>", "</span>", "<span", "</div>", "<div", "&nbsp;", "<br")
_ARTNUM = re.compile(r"^(\d+)([а-яa-z]?)(\d?)$")


def _art_key(n: str) -> tuple[int, str, int]:
    m = _ARTNUM.match(n)
    return (int(m.group(1)), m.group(2), int(m.group(3) or 0)) if m else (0, n, 0)


def run_all(blocks: list[Block], smap: dict[int, dict]) -> tuple[str, list[dict]]:
    md, placed, dropped = assemble(blocks, smap)
    ex: list[dict] = []
    # coverage
    idx = {b.i for b in blocks}
    touched = set(placed) | set(dropped)
    for i in sorted(idx - touched):
        ex.append({"block": i, "kind": "not_covered", "detail": "neither placed nor dropped"})
    # reassembly
    if strip_markers(md).rstrip("\n") != "\n".join(blocks[i].text for i in placed):
        ex.append({"block": -1, "kind": "reassembly", "detail": "assembled text differs from the placed blocks"})
    for i in dropped:
        if smap.get(i, {}).get("label") != "drop":
            ex.append({"block": i, "kind": "dropped_without_label", "detail": "left out without a drop label"})
    # confidence and unknown
    for i in placed:
        e = smap.get(i)
        if e is None or e["label"] == "unknown":
            ex.append({"block": i, "kind": "unknown", "detail": (e or {}).get("note", "no label")})
        elif e.get("conf") == "low":
            ex.append({"block": i, "kind": "low_confidence", "detail": e.get("note", "")})
    # fragments
    for i in placed:
        t = blocks[i].text
        for f in FRAGMENTS:
            if f in t:
                ex.append({"block": i, "kind": "fragment", "detail": f"contains {f!r}"})
                break
    # numbering, nesting, addresses
    last_art: tuple[int, str, int] | None = None
    seen_art: dict[str, int] = {}
    seen_sign: dict[str, int] = {}
    in_article = False
    in_sign = False
    last_alinea = 0
    last_item = 0
    last_letter = ""
    item_parent_ok = False
    for i in placed:
        e = smap.get(i)
        if not e:
            continue
        label, n = e["label"], e.get("n")
        if label in ("part_heading", "chapter_heading", "section_heading", "subsection_heading", "provisions_heading", "annex_heading", "title"):
            in_article = in_sign = False
            last_alinea = last_item = 0
            last_letter = ""
            item_parent_ok = False
            if label == "provisions_heading":
                seen_sign = {}
        elif label == "article_head":
            key = _art_key(n)
            if last_art is not None and key < last_art:
                ex.append({"block": i, "kind": "article_order", "detail": f"Чл. {n} after Чл. {last_art[0]}{last_art[1]}{last_art[2] or ''}"})
            if n in seen_art:
                ex.append({"block": i, "kind": "duplicate_address", "detail": f"Чл. {n} already at block {seen_art[n]}"})
            seen_art[n] = i
            last_art = key
            in_article, in_sign = True, False
            last_alinea = last_item = 0
            last_letter = ""
            item_parent_ok = True
        elif label == "paragraph_sign":
            if n in seen_sign:
                ex.append({"block": i, "kind": "duplicate_address", "detail": f"§ {n} already at block {seen_sign[n]} in this provisions block"})
            seen_sign[n] = i
            in_sign, in_article = True, False
            last_alinea = last_item = 0
            last_letter = ""
            item_parent_ok = True
        elif label == "alinea":
            if not (in_article or in_sign):
                ex.append({"block": i, "kind": "nesting", "detail": "alinea outside an article or §"})
            num = int(re.match(r"\d+", n).group(0)) if n and re.match(r"\d+", n) else 0
            if last_alinea and num != last_alinea + 1 and not re.search(r"[а-я]$", n or ""):
                ex.append({"block": i, "kind": "alinea_order", "detail": f"({n}) after ({last_alinea})"})
            last_alinea = num or last_alinea
            last_item = 0
            last_letter = ""
            item_parent_ok = True
        elif label == "item":
            if not item_parent_ok:
                ex.append({"block": i, "kind": "nesting", "detail": "item outside an article, alinea or §"})
            num = int(re.match(r"\d+", n).group(0)) if n and re.match(r"\d+", n) else 0
            if last_item and num != last_item + 1 and not re.search(r"[а-я]$", n or ""):
                ex.append({"block": i, "kind": "item_order", "detail": f"{n}. after {last_item}."})
            last_item = num or last_item
            last_letter = ""
        elif label == "letter":
            if not last_item:
                ex.append({"block": i, "kind": "nesting", "detail": "letter outside an item"})
            if last_letter and n and ord(n) != ord(last_letter) + 1:
                ex.append({"block": i, "kind": "letter_order", "detail": f"{n}) after {last_letter})"})
            last_letter = n or last_letter
    return md, ex
