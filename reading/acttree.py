"""The act as a tree of addressable lines (step F1 of the plan of 31 October 2026, part 4: the apply step's model of the text).

The corpus body is Markdown in the assembler's conventions: one provision line per paragraph, headings with hashes,
bold article and § heads, alineas „(2) …“, items „1. …“, letters „а) …“, annex headings „## Приложение …“. This module
reads such a body into ``Line`` nodes with a kind and a number, gives each the parent the numbering grammar implies
(an alinea under its article, an item under the alinea or the article, a letter under the item), and resolves the
addresses an amending instruction uses („чл. 36, ал. 1, т. 5, б. „а““, „§ 3“, „глава втора, раздел V“, „Приложение № 3“)
to nodes. It writes the tree back to the same Markdown, so a body that is read and written unchanged is byte-equal.

``to_blocks_and_map`` turns the tree into the blocks and labels that ``reading/checks.py`` reads, so the mechanical
checks of the reading architecture (numbering, nesting, addresses, reassembly) run over an engine-built body as they
run over a labelled page. Nothing here calls a model or writes a corpus file.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from .assembler import HEADING_PREFIX, NUMBER_LINE, strip_line
from .splitter import Block

KINDS = ("title", "prehistory", "part_heading", "chapter_heading", "section_heading", "subsection_heading", "provisions_heading",
         "annex_heading", "article", "sign", "alinea", "item", "letter", "annex_row", "note", "text")
_HEAD_LEVEL = {"# ": "title", "## ": "l2", "### ": "chapter_heading", "#### ": "section_heading", "##### ": "subsection_heading"}
_ART = re.compile(r"^(?:(?P<title>[^*\n]{1,160}?)\s+)?\*\*(Чл\.\s*(\d+[а-я]?(?:\d{1,2})?)\.|Член\s+единствен\.)\*\*\s*(.*)$", re.S)   # lex.bg prints an article's title before its head
_SIGN = re.compile(r"^(?:\*\*)?(§\s*(\d+[а-я]?)\.|Параграф\s+единствен\.)(?:\*\*)?\s*(.*)$", re.S)   # a plain § head is lex.bg's amending tail
_ALINEA = re.compile(r"^\((\d{1,3}[а-я]?)\)\s*(.*)$", re.S)
_ITEM = re.compile(r"^(\d{1,3}(?:[а-я]{1,2})?)\.\s+(.*)$", re.S)
_LETTER = re.compile(r"^([а-я]{1,3})\)\s+(.*)$", re.S)
_MARKER = re.compile(r"^\((?:Изм|изм|Нова|Нов|нова|нов|Доп|доп|Отм|отм|Попр|попр|Загл|Предишн|предишн|В сила|Обявен)[^()]*(?:\([^()]*\)[^()]*)*\)\s*")
_ANNEX = re.compile(r"^Приложение(?:\s*№\s*(\S+))?", re.I)
_PROVISIONS = re.compile(r"(допълнителн|преходн|заключителн)", re.I)
_WORD_LEVEL = {"част": "part_heading", "дял": "part_heading", "глава": "chapter_heading", "раздел": "section_heading", "подраздел": "subsection_heading"}


@dataclass
class Line:
    kind: str
    text: str                 # the full Markdown line as written
    n: str | None = None      # the number as written (article "36", alinea "1", item "5", letter "а", § "3", annex "3")
    parent: int | None = None
    children: list[int] = field(default_factory=list)
    marker: str | None = None  # the amendment marker after the head, without its parentheses
    title: str | None = None   # an article's own title, printed before its head (lex.bg's form)
    inline_alinea: str | None = None   # the first alinea written in the head line itself („Чл. 4. (1) …“)

    def body(self) -> str:
        """The provision's own words: the line without its head, its marker and the assembler's markers."""
        t = strip_line(self.text)
        if self.kind == "article":
            m = _ART.match(self.text)
            if m and m.group("title"):
                t = t[len(m.group("title")):].lstrip()
        for rx in (re.compile(r"^(Чл\.\s*\S+\.|Член\s+единствен\.|§\s*\S+\.|Параграф\s+единствен\.)\s*"), re.compile(r"^\(\d{1,3}[а-я]?\)\s*"),
                   re.compile(r"^\d{1,3}(?:[а-я]{1,2})?\.\s+"), re.compile(r"^[а-я]{1,3}\)\s+")):
            m = rx.match(t)
            if m and self.kind in ("article", "sign", "alinea", "item", "letter"):
                t = t[m.end():]
                break
        m = _MARKER.match(t)
        t = t[m.end():] if m else t
        if self.inline_alinea:
            m = re.match(r"^\(\d{1,3}[а-я]?\)\s*", t)
            t = t[m.end():] if m else t
            m = _MARKER.match(t)
            t = t[m.end():] if m else t
        return t


class AddressError(ValueError):
    """An address the act does not have, or one that names several places."""


@dataclass
class Tree:
    lines: list[Line]

    def to_markdown(self) -> str:
        return "\n\n".join(l.text for l in self.lines) + "\n"

    def subtree(self, i: int) -> list[int]:
        out = [i]
        for c in self.lines[i].children:
            out.extend(self.subtree(c))
        return out

    def children_of_kind(self, i: int, kind: str) -> list[int]:
        return [c for c in self.lines[i].children if self.lines[c].kind == kind]

    def articles(self) -> list[int]:
        return [k for k, l in enumerate(self.lines) if l.kind == "article"]

    def own_subtree(self, i: int) -> list[int]:
        """The head's inline first alinea and what hangs under it: the children that are not later alineas, with their subtrees."""
        out = [i]
        for c in self.lines[i].children:
            if self.lines[c].kind != "alinea":
                out.extend(self.subtree(c))
        return out

    def find(self, kind: str, n: str, under: int | None = None, inline: bool = False) -> list[int]:
        pool = (self.own_subtree(under) if inline else self.subtree(under)) if under is not None else range(len(self.lines))
        found = [k for k in pool if self.lines[k].kind == kind and self.lines[k].n == n]
        if kind == "alinea" and not found and under is not None and self.lines[under].inline_alinea == n:
            found = [under]   # „Чл. 7. (1) …“: the first alinea lives in the head line
        return found


def _kind_of(text: str) -> tuple[str, str | None]:
    for prefix, kind in _HEAD_LEVEL.items():
        if text.startswith(prefix):
            body = text[len(prefix):]
            if kind == "l2":
                if _ANNEX.match(body):
                    m = _ANNEX.match(body)
                    return "annex_heading", (m.group(1) or "").strip("„“\"") or None
                if _PROVISIONS.search(body):
                    return "provisions_heading", None
                return "part_heading", None
            if kind == "title":
                return "title", None
            m = re.match(r"^(Част|Дял|Глава|Раздел|Подраздел)\s+(\S+)", body, re.I)
            if m:
                return _WORD_LEVEL.get(m.group(1).lower(), kind), m.group(2).rstrip(".")
            return kind, None
    if text.startswith("*") and text.endswith("*") and not text.startswith("**"):
        return "prehistory", None
    m = _ART.match(text)
    if m:
        return "article", m.group(3) or "единствен"
    m = _SIGN.match(text)
    if m:
        return "sign", m.group(2) or "единствен"
    m = _ALINEA.match(text)
    if m:
        return "alinea", m.group(1)
    m = _ITEM.match(text)
    if m:
        return "item", m.group(1)
    m = _LETTER.match(text)
    if m:
        return "letter", m.group(1)
    if _MARKER.match(text) and "ДВ" in text[:60]:
        return "note", None
    return "text", None


def parse(markdown: str) -> Tree:
    """Read a body in the assembler's Markdown into lines with parents; an annex's lines are rows, never addresses."""
    raw = [p for p in markdown.split("\n\n") if p.strip()]
    lines: list[Line] = []
    for t in raw:
        t = t.rstrip("\n")
        kind, n = _kind_of(t)
        line = Line(kind=kind, text=t, n=n)
        if kind in ("article", "sign"):
            m = _ART.match(t) if kind == "article" else None
            if m and m.group("title"):
                line.title = m.group("title")
            rest = (m.group(4) if m else _SIGN.match(t).group(3)) or ""
            mm = re.match(r"^(?:\([^()]*(?:\([^()]*\)[^()]*)*\)\s*)*\((\d{1,3})\)", rest)   # after an editorial note in parentheses
            if mm:
                line.inline_alinea = mm.group(1)
        lines.append(line)
    tree = Tree(lines)
    # parents by the numbering grammar, as checks.py nests them
    last: dict[str, int | None] = {"article": None, "sign": None, "alinea": None, "item": None, "heading": None}
    in_annex: int | None = None
    for k, l in enumerate(lines):
        if l.kind == "annex_heading":
            in_annex = k
            last = {"article": None, "sign": None, "alinea": None, "item": None, "heading": k}
            continue
        if in_annex is not None and l.kind not in ("provisions_heading",):
            # inside an annex every line is a row of it (an annex's own articles are not the act's addresses)
            l.kind = "annex_row" if l.kind not in ("note",) else l.kind
            l.n = None
            l.parent = in_annex
            lines[in_annex].children.append(k)
            continue
        in_annex = None if l.kind == "provisions_heading" else in_annex
        if l.kind in ("title", "part_heading", "chapter_heading", "section_heading", "subsection_heading", "provisions_heading"):
            last = {"article": None, "sign": None, "alinea": None, "item": None, "heading": k}
            continue
        if l.kind == "prehistory":
            continue
        if l.kind in ("article", "sign"):
            l.parent = last["heading"]
            if last["heading"] is not None:
                lines[last["heading"]].children.append(k)
            last.update({"article": k if l.kind == "article" else None, "sign": k if l.kind == "sign" else None, "alinea": None, "item": None})
            continue
        head = last["alinea"] if l.kind in ("item", "letter", "text", "note") and last["alinea"] is not None else (last["article"] if last["article"] is not None else last["sign"])
        if l.kind == "alinea":
            head = last["article"] if last["article"] is not None else last["sign"]
            last["alinea"] = k
            last["item"] = None
        elif l.kind == "item":
            last["item"] = k
        elif l.kind == "letter" and last["item"] is not None:
            head = last["item"]
        if head is None:
            head = last["heading"]
        l.parent = head
        if head is not None:
            lines[head].children.append(k)
    return tree


_ADDR_PART = re.compile(r"(чл\.|член|ал\.|алинея|т\.|точка|б\.|буква|§|параграф|глава|раздел|част|дял|подраздел|приложение)\s*(№\s*)?([\w„“\"]+)", re.I)
_PART_KIND = {"чл.": "article", "член": "article", "ал.": "alinea", "алинея": "alinea", "т.": "item", "точка": "item", "б.": "letter", "буква": "letter",
              "§": "sign", "параграф": "sign", "глава": "chapter_heading", "раздел": "section_heading", "част": "part_heading", "дял": "part_heading",
              "подраздел": "subsection_heading", "приложение": "annex_heading"}


def parse_address(text: str) -> list[tuple[str, str]]:
    """„чл. 36, ал. 1, т. 5, б. „а““ → [("article", "36"), ("alinea", "1"), ("item", "5"), ("letter", "а")]; „наименованието“ → [("title", "")]."""
    t = text.strip().strip(".")
    if re.match(r"^(наименованието|заглавието)", t, re.I):
        return [("title", "")]
    out: list[tuple[str, str]] = []
    for m in _ADDR_PART.finditer(t):
        kind = _PART_KIND[m.group(1).lower()]
        n = m.group(3).strip("„“\"").rstrip(".,;:")
        out.append((kind, n))
    if not out:
        raise AddressError(f"no address in {text!r}")
    return out


def resolve(tree: Tree, address: str) -> int:
    """The one line an address names; AddressError when none or several."""
    parts = parse_address(address)
    kind, n = parts[0]
    if kind == "title":
        found = [k for k, l in enumerate(tree.lines) if l.kind == "title"]
    else:
        found = tree.find(kind, n)
        if kind in ("chapter_heading", "section_heading", "part_heading", "subsection_heading"):
            found = [k for k, l in enumerate(tree.lines) if l.kind == kind and l.n is not None and l.n.lower() == n.lower()]
    prev_kind = kind
    for kind, n in parts[1:]:
        nxt: list[int] = []
        for f in found:
            inline = prev_kind == "alinea" and tree.lines[f].kind in ("article", "sign") and tree.lines[f].inline_alinea is not None
            nxt.extend(tree.find(kind, n, under=f, inline=inline))
        found = nxt
        prev_kind = kind
    if len(found) != 1:
        raise AddressError(f"{address!r} names {len(found)} place(s) in the act")
    return found[0]


_LABEL = {"article": "article_head", "sign": "paragraph_sign", "alinea": "alinea", "item": "item", "letter": "letter", "note": "editorial_note",
          "text": "continuation", "annex_row": "annex_row", "prehistory": "prehistory"}


def to_blocks_and_map(tree: Tree) -> tuple[list[Block], dict[int, dict]]:
    """The tree as the blocks and labels the checks read; a heading written on one line is one block."""
    blocks: list[Block] = []
    smap: dict[int, dict] = {}
    for l in tree.lines:
        text = strip_line(l.text)
        if l.kind == "article" and l.title:
            i = len(blocks)
            blocks.append(Block(i, l.title, "DvJustify"))
            smap[i] = {"label": "article_title", "conf": "high"}
            text = text[len(l.title):].lstrip()
        label = _LABEL.get(l.kind, l.kind)
        entry = {"label": label, "conf": "high"}
        if l.kind in ("article", "sign", "alinea", "item", "letter"):
            entry["n"] = l.n
        i = len(blocks)
        blocks.append(Block(i, text, "DvJustify"))
        smap[i] = entry
    return blocks, smap


def render_heading(kind: str, text: str) -> str:
    return HEADING_PREFIX[kind] + text


def line_from_text(text: str, context_kind: str | None = None) -> Line:
    """A new provision line from the Gazette's words (a quoted block without its quotation marks): bold head, kind, number."""
    t = text.strip()
    m = re.match(r"^(Чл\.\s*\d+[а-я]?(?:\d{1,2})?\.|Член\s+единствен\.)(.*)$", t, re.S)
    if m:
        return Line("article", f"**{m.group(1)}**{m.group(2)}", re.match(r"Чл\.\s*(\S+)\.", m.group(1)).group(1) if m.group(1).startswith("Чл") else "единствен")
    m = re.match(r"^(§\s*\d+[а-я]?\.|Параграф\s+единствен\.)(.*)$", t, re.S)
    if m:
        return Line("sign", f"**{m.group(1)}**{m.group(2)}", re.match(r"§\s*(\S+)\.", m.group(1)).group(1) if m.group(1).startswith("§") else "единствен")
    m = re.match(r"^(Част|Дял|Глава|Раздел|Подраздел)\s+(\S+)\.?(?:\s+(.*))?$", t, re.S | re.I)
    if m:
        kind = _WORD_LEVEL[m.group(1).lower()]
        return Line(kind, HEADING_PREFIX[kind] + t, m.group(2).rstrip("."))
    if _PROVISIONS.search(t) and len(t) < 80 and t == t.upper() or re.match(r"^(Допълнителн|Преходн|Заключителн)", t) and len(t) < 80:
        return Line("provisions_heading", "## " + t, None)
    if _ANNEX.match(t) and len(t) < 120:
        return Line("annex_heading", "## " + t, (_ANNEX.match(t).group(1) or "").strip("„“\"") or None)
    kind, n = _kind_of(t)
    if kind == "text" and context_kind == "annex_row":
        kind = "annex_row"
    return Line(kind, t, n)
