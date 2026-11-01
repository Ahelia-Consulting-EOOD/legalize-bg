"""The act as a tree of addressable lines (step F1 of the plan of 31 October 2026, part 4: the apply step's model of the text).

The corpus body is Markdown in the assembler's conventions: one provision line per paragraph, headings with hashes,
bold article and § heads, alineas „(2) …“, items „1. …“, letters „а) …“, annex headings „## Приложение …“. This module
reads such a body into ``Line`` nodes with a kind and a number, gives each the parent the numbering grammar implies
(a section under its chapter, an alinea under its article, an item under the alinea or the article, a letter under the
item), and resolves the addresses an amending instruction uses („чл. 36, ал. 1, т. 5, б. „а““, „§ 3“, „глава втора,
раздел V“, „Приложение № 3“, „наименованието“, „навсякъде“) to lines. An address part the grammar does not know is
refused, never dropped (review of 1 November 2026, B3). A first alinea written in the head line („Чл. 6. (1) …“) is
its own line in the tree and is joined back to the head on output, so an operation on „чл. 6, ал. 1“ touches the
alinea and nothing else (B1). The §§ lex.bg prints after a „… КЪМ …“ provisions heading are another act's and are not
addressable (M3). A body that is read and written unchanged is byte-equal when its paragraphs are separated by one
blank line, which is what the assembler writes; the apply step asserts it before the first material.

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
ACT = -1   # the address of the whole act („навсякъде“, „в целия закон“)
_HEAD_LEVEL = {"# ": "title", "## ": "l2", "### ": "chapter_heading", "#### ": "section_heading", "##### ": "subsection_heading"}
_ART = re.compile(r"^(?:(?P<title>[^*\n]{1,800}?)\s+)?\*\*(Чл\.\s*(\d+[а-я]?(?:\d{1,2})?)\.|Член\s+единствен\.)\*\*\s*(.*)$", re.S)   # a title of the Family Code's length (615 characters, чл. 127б) is still a title   # lex.bg prints an article's title before its head
_SIGN = re.compile(r"^(?:\*\*)?(§\s*(\d+[а-я]?)\.|Параграф\s+единствен\.)(?:\*\*)?\s*(.*)$", re.S)   # a plain § head is lex.bg's amending tail
_ALINEA = re.compile(r"^\((\d{1,3}[а-я]?)\)\s*(.*)$", re.S)
_ITEM = re.compile(r"^(\d{1,3}(?:[а-я]{1,2})?)\.(?:\s+|(?=[А-Яа-я(„\"]))(.*)$", re.S)   # „1.главния“: the Gazette prints an item without its space (a malformed head, D-072 ruling 7)
_LETTER = re.compile(r"^([а-я]{1,3})\)\s+(.*)$", re.S)
_MARKER = re.compile(r"^\((?:Изм|изм|Нова|Нов|нова|нов|Доп|доп|Отм|отм|Попр|попр|Загл|Предишн|предишн|В сила|Обявен)[^()]*(?:\([^()]*\)[^()]*)*\)\s*")
_INLINE_ALINEA = re.compile(r"^((?:\([^()]*(?:\([^()]*\)[^()]*)*\)\s*)*)(\(\d{1,3}\)\s*.*)$", re.S)   # after an editorial note in parentheses
_ANNEX = re.compile(r"^Приложение(?:\s*№\s*(\S+))?", re.I)
_ANNEX_REF = re.compile(r"^Приложение\s*(?:№\s*\S+)?\s*към\s+((?:(?:чл|ал|т)\.\s*\d+[а-я]?|§\s*\d+[а-я]?|,\s*|\bи\b\s*|\s)+)", re.I)


def _annex_n(heading: str) -> str | None:
    """An annex's identity: its number („Приложение № 3 към чл. 6“ → "3"), or, unnumbered, the provision it belongs to
    („Приложение към чл. 19г, ал. 2“ → "към чл. 19г, ал. 2"); lex.bg's „Приложениекъм чл. 8“ reads the same."""
    m = _ANNEX.match(heading)
    if not m:
        return None
    if m.group(1):
        return m.group(1).strip("„“\"") or None
    r = _ANNEX_REF.match(heading)
    if not r:
        return None
    return "към " + _norm_ref(r.group(1))


def _norm_ref(ref: str) -> str:
    ref = re.sub(r"(чл|ал|т)\.\s*", r"\1. ", ref)
    ref = re.sub(r"§\s*", "§ ", ref)
    return re.sub(r"\s+", " ", ref).strip().rstrip(",").strip()
_PROVISIONS = re.compile(r"^(допълнителн|преходн|заключителн)\S*(\s+и\s+\S+)?\s+разпоредб", re.I)
HEADING_NUMBER = r"((?:[\wIVXLC]+)(?:\s+и\s+[\w]+)?(?:\s*[„\"][а-я][“\"])?)"   # първа, двадесет и първа, единадесета „а“, I, IIIа
_PART = re.compile(r"^(Част|Дял)\s+" + HEADING_NUMBER, re.I)
_HEADING_WORD = re.compile(r"^(Част|Дял|Глава|Раздел|Подраздел)\s+" + HEADING_NUMBER, re.I)
_TAIL_HEADING = re.compile(r"^(ЗАКОН|ЗАКОНА|КОДЕКС|КОДЕКСА|УКАЗ|ПОСТАНОВЛЕНИЕ)\b")   # lex.bg opens an amending act's tail with its title in capitals
_OBN = re.compile(r"^\(\s*ОБН\.", re.I)
_WORD_LEVEL = {"част": "part_heading", "дял": "part_heading", "глава": "chapter_heading", "раздел": "section_heading", "подраздел": "subsection_heading"}
_RANK = {"part_heading": 1, "chapter_heading": 2, "section_heading": 3, "subsection_heading": 4}
_HEADINGS = ("title", "part_heading", "chapter_heading", "section_heading", "subsection_heading", "provisions_heading", "annex_heading")
_KAM = re.compile(r"\b(КЪМ|Към|към)\b")


@dataclass
class Line:
    kind: str
    text: str                 # the Markdown line as written (an inline alinea: its own part, joined to the head on output)
    n: str | None = None      # the number as written (article "36", alinea "1", item "5", letter "а", § "3", annex "3", chapter "първа")
    parent: int | None = None
    children: list[int] = field(default_factory=list)
    title: str | None = None   # an article's own title, printed before its head (lex.bg's form)
    inline: bool = False       # an alinea written in the head line of its article or §
    addressable: bool = True   # False in lex.bg's amending tails after a „КЪМ …“ heading

    def head(self) -> str:
        """The line's head: the title, the bold number and the marker; what precedes the provision's own words."""
        return self.text[: len(self.text) - len(self.body())]

    def body(self) -> str:
        """The provision's own words: the line without its title, its head, its marker and the assembler's markers."""
        t = strip_line(self.text)
        if self.kind == "article":
            m = _ART.match(self.text)
            if m and m.group("title"):
                t = t[len(m.group("title")):].lstrip()
        for rx in (re.compile(r"^(Чл\.\s*\S+\.|Член\s+единствен\.|§\s*\S+\.|Параграф\s+единствен\.)\s*"), re.compile(r"^\(\d{1,3}[а-я]?\)\s*"),
                   re.compile(r"^\d{1,3}(?:[а-я]{1,2})?\.(?:\s+|(?=[А-Яа-я(„\"]))"), re.compile(r"^[а-я]{1,3}\)\s+")):
            m = rx.match(t)
            if m and self.kind in ("article", "sign", "alinea", "item", "letter"):
                t = t[m.end():]
                break
        m = _MARKER.match(t)
        return t[m.end():] if m else t

    def marker(self) -> str | None:
        """The marker after the head, without its parentheses, or None."""
        t = strip_line(self.text)
        if self.kind == "article":
            m = _ART.match(self.text)
            if m and m.group("title"):
                t = t[len(m.group("title")):].lstrip()
        for rx in (re.compile(r"^(Чл\.\s*\S+\.|Член\s+единствен\.|§\s*\S+\.|Параграф\s+единствен\.)\s*"), re.compile(r"^\(\d{1,3}[а-я]?\)\s*"),
                   re.compile(r"^\d{1,3}(?:[а-я]{1,2})?\.(?:\s+|(?=[А-Яа-я(„\"]))"), re.compile(r"^[а-я]{1,3}\)\s+")):
            m = rx.match(t)
            if m and self.kind in ("article", "sign", "alinea", "item", "letter"):
                t = t[m.end():]
                break
        m = _MARKER.match(t)
        if not m:
            return None
        inner = m.group(0).strip()
        return inner[1:-1] if inner.endswith(")") else inner[1:]


class AddressError(ValueError):
    """An address the act does not have, one that names several places, or one with a part the grammar does not know."""


@dataclass
class Tree:
    lines: list[Line]

    def to_markdown(self) -> str:
        out: list[str] = []
        for l in self.lines:
            if l.inline and out:
                out[-1] = f"{out[-1]} {l.text}".rstrip() if l.text else out[-1]
            else:
                out.append(l.text)
        return "\n\n".join(out) + "\n"

    def subtree(self, i: int) -> list[int]:
        out = [i]
        for c in self.lines[i].children:
            out.extend(self.subtree(c))
        return out

    def find(self, kind: str, n: str, under: int | None = None) -> list[int]:
        pool = self.subtree(under) if under is not None else range(len(self.lines))
        return [k for k in pool if self.lines[k].kind == kind and self.lines[k].addressable and _same_n(self.lines[k].n, n)]

    def addressable_lines(self) -> list[int]:
        return [k for k, l in enumerate(self.lines) if l.addressable and l.kind not in ("title", "prehistory", "note")]


def _same_n(a: str | None, b: str) -> bool:
    norm = lambda x: re.sub(r"\s+", " ", re.sub(r"[„“”\"]", "", x.lower().rstrip(".")))   # „глава втора „а““: the marks around a letter are print
    return a is not None and norm(a) == norm(b)


def _kind_of(text: str) -> tuple[str, str | None]:
    for prefix, kind in _HEAD_LEVEL.items():
        if text.startswith(prefix):
            body = text[len(prefix):]
            if kind == "l2":
                if _ANNEX.match(body):
                    return "annex_heading", _annex_n(body)
                if _PROVISIONS.match(body):
                    return "provisions_heading", None
                m = _PART.match(body)
                return "part_heading", (m.group(2).rstrip(".") if m else None)
            if kind == "title":
                return "title", None
            m = _HEADING_WORD.match(body)
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


def _split_inline(line: Line) -> Line | None:
    """Cut the first alinea out of a head line: the head keeps its title, number and marker; the alinea becomes its own line."""
    m = _ART.match(line.text) if line.kind == "article" else _SIGN.match(line.text)
    if not m:
        return None
    rest = m.group(4) if line.kind == "article" else m.group(3)
    mm = _INLINE_ALINEA.match(rest or "")
    if not mm or not re.match(r"^\(\d{1,3}\)", mm.group(2)):
        return None
    marker_part, alinea_part = mm.group(1), mm.group(2)
    head_text = line.text[: len(line.text) - len(rest)] + marker_part.rstrip()
    line.text = head_text.rstrip()
    n = re.match(r"^\((\d{1,3})\)", alinea_part).group(1)
    return Line("alinea", alinea_part.strip(), n, inline=True)


def parse(markdown: str) -> Tree:
    """Read a body in the assembler's Markdown into lines with parents; an annex's lines are rows, never addresses."""
    raw = [p for p in markdown.split("\n\n") if p.strip()]
    lines: list[Line] = []
    for t in raw:
        t = t.rstrip("\n")
        kind, n = _kind_of(t)
        line = Line(kind=kind, text=t, n=n)
        if kind == "article":
            m = _ART.match(t)
            if m and m.group("title"):
                line.title = m.group("title")
        lines.append(line)
        if kind in ("article", "sign"):
            inline = _split_inline(line)
            if inline is not None:
                lines.append(inline)
    tree = Tree(lines)
    last: dict[str, int | None] = {"article": None, "sign": None, "alinea": None, "item": None, "heading": None}
    ranks: dict[int, int] = {}   # the open heading of each rank
    in_annex: int | None = None
    tail = False   # after a „… КЪМ …“ provisions heading: lex.bg's print of another act's §§
    for k, l in enumerate(lines):
        if l.kind == "annex_heading":
            in_annex = k
            tail = False
            last = {"article": None, "sign": None, "alinea": None, "item": None, "heading": k}
            continue
        if in_annex is not None and l.kind != "provisions_heading":
            l.kind = "annex_row" if l.kind != "note" else l.kind
            l.n = None
            l.parent = in_annex
            lines[in_annex].children.append(k)
            continue
        in_annex = None if l.kind == "provisions_heading" else in_annex
        if l.kind == "part_heading" and l.n is None and _TAIL_HEADING.match(strip_line(l.text)):
            tail = True   # another act's title printed as a heading: lex.bg's tail of an amending act
            l.addressable = False
            last = {"article": None, "sign": None, "alinea": None, "item": None, "heading": k}
            continue
        if l.kind == "note" and _OBN.match(l.text):
            tail = True
        if l.kind in _HEADINGS:
            if l.kind == "provisions_heading":
                tail = bool(_KAM.search(l.text))
                ranks = {}
            rank = _RANK.get(l.kind)
            if rank is not None:
                for r in [r for r in ranks if r >= rank]:
                    del ranks[r]
                above = [ranks[r] for r in sorted(ranks) if r < rank]
                if above:
                    l.parent = above[-1]
                    lines[above[-1]].children.append(k)
                ranks[rank] = k
            last = {"article": None, "sign": None, "alinea": None, "item": None, "heading": k}
            continue
        if l.kind == "prehistory":
            continue
        if tail:
            l.addressable = False
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


_ADDR_PART = re.compile(r"(чл\.|член|ал\.|алинея|т\.|точка|б\.|буква|§|параграф|глава|раздел|част|дял|подраздел|приложение|изречение|изр\.)\s*(№\s*)?"
                        r"((?:[\w„“\"]+(?:\s+и\s+[\w]+)?(?:\s*[„\"][а-я][“\"])?))", re.I)
_LEAD = re.compile(r"\b(?:в\s+)?(?:текст(?:а|ът)\s+преди\s+т\.\s*\d+[а-я]?|основния\s+текст|основният\s+текст|уводното\s+изречение)", re.I)
_PART_KIND = {"чл.": "article", "член": "article", "ал.": "alinea", "алинея": "alinea", "т.": "item", "точка": "item", "б.": "letter", "буква": "letter",
              "§": "sign", "параграф": "sign", "глава": "chapter_heading", "раздел": "section_heading", "част": "part_heading", "дял": "part_heading",
              "подраздел": "subsection_heading", "приложение": "annex_heading", "изречение": "sentence", "изр.": "sentence"}
_ORDINALS = {"първо": 1, "второ": 2, "трето": 3, "четвърто": 4, "пето": 5, "шесто": 6, "последно": -1}
# what may stand in an address besides its parts: separators and the phrases that name the scope the parts lie in
_FILLER = re.compile(r"^(?:[\s,;:()„“\"]|\b(?:и|от|на|в|във|към|по|за|преходните|заключителните|допълнителните|допълнителната|преходната|заключителната|"
                     r"разпоредби|разпоредба|закона|кодекса|наредбата|правилника|този|тази)\b)*$", re.I)


def parse_address(text: str) -> list[tuple[str, str]]:
    """„чл. 36, ал. 1, т. 5, б. „а““ → [("article", "36"), ("alinea", "1"), ("item", "5"), ("letter", "а")]; „наименованието“ → [("title", "")];
    „навсякъде“ → [("act", "")]; „чл. 5, ал. 2, изречение второ“ ends with ("sentence", "2"). Anything else in the text refuses it."""
    t = text.strip().strip(".")
    tail: list[tuple[str, str]] = []
    # „наименованието на чл. 27“, „приложение …, наименованието“: the provision's or the annex's own title words
    tm = re.search(r"(?:^|,\s*|\s+)(?:в\s+)?(наименованието|заглавието)(?:\s+на)?(?=\s|,|$)", t, re.I)
    if tm:
        rest = (t[:tm.start()] + " " + t[tm.end():]).strip(" ,")
        if not rest.strip():
            return [("title", "")]
        t = rest
        tail.append(("article_title", ""))
    # „…, ред „Областна дирекция „Земеделие“ – Варна““: a row of an annex table, named by its words
    # „т. 5.15“: a sub-item numbered inside an item's text (the Gazette's flattened hierarchy); the item is the address, the
    # sub-item the scope of the words operation
    lm = re.search(r",?\s*(?:буква|б\.)\s*[„(]?([a-zа-я])[“)]?\s*$", t)
    if lm and re.match(r"^(?:Приложението|Приложение)\s", t, re.I):
        tail.insert(0, ("annex_letter", lm.group(1)))   # a lettered entry of an annex form („(d) …“)
        t = t[:lm.start()].strip(" ,")
    sm = re.search(r"\b(т\.|точка)\s*(\d+)\.(\d+)(?=\s|,|$)", t)
    if sm:
        tail.append(("subitem", f"{sm.group(2)}.{sm.group(3)}"))
        t = t[:sm.start()] + f"т. {sm.group(2)}" + t[sm.end():]
    rm = re.search(r",?\s*(?:на\s+)?ред\s+„(.+)“\s*$", t)
    if rm:
        tail.insert(0, ("annex_row", rm.group(1).strip()))
        t = t[:rm.start()].strip(" ,")
    if re.match(r"^(навсякъде|в целия|в цялата|в целия текст|в текста на целия)", t, re.I) or \
            re.fullmatch(r"(?:навсякъде\s+)?(?:в\s+)?(?:наредбата|закона|кодекса|правилника|устройствения правилник|инструкцията)(?:\s+и\s+(?:в\s+)?приложени(?:ето|ята)\s+към\s+(?:нея|него))?", t, re.I):
        return [("act", "")]   # „навсякъде в наредбата и в приложенията към нея“: the whole act
    unnumbered = re.fullmatch(r"(?:Приложението|Приложение)\s+към\s+(.+)", t, re.I)
    if unnumbered:
        # an unnumbered annex is named by the provision it belongs to; the parts after „към“ are its name, not a path into it
        ref = _norm_ref(unnumbered.group(1))
        if not re.fullmatch(r"(?:(?:чл|ал|т)\. \d+[а-я]?|§ \d+[а-я]?)(?:(?:, | и )(?:(?:чл|ал|т)\. \d+[а-я]?|§ \d+[а-я]?))*", ref):
            raise AddressError(f"the annex reference in {text!r} is not a provision the grammar reads: {ref!r}")
        return [("annex_heading", "към " + ref)] + tail
    t = re.sub(r"^Приложението\b", "Приложение", t)
    out: list[tuple[str, str]] = []
    rest = t
    lead = _LEAD.search(t)
    if lead:
        rest = rest.replace(lead.group(0), " ", 1)
        t = re.sub(r"\bпреди\s+т\.\s*\d+[а-я]?", " ", t)   # the item the lead-in stands before is not an address part
    for m in _ADDR_PART.finditer(t):
        kind = _PART_KIND[m.group(1).lower()]
        n = m.group(3).strip("„“\"").rstrip(".,;:")
        if kind == "sentence":
            if n.lower() not in _ORDINALS:
                raise AddressError(f"the sentence {n!r} in {text!r} is not an ordinal the grammar knows")
            n = str(_ORDINALS[n.lower()])
        out.append((kind, n))
        rest = rest.replace(m.group(0), " ", 1)
    if not out:
        raise AddressError(f"no address in {text!r}")
    if not _FILLER.match(rest):
        raise AddressError(f"the address {text!r} carries a part the grammar does not read: {rest.strip()!r}")
    if lead:
        out.append(("lead", ""))   # the provision's own words before its items
    out.extend(tail)
    sentences = [p for p in out if p[0] == "sentence"]
    if len(sentences) > 1 or (sentences and out[-1][0] not in ("sentence", "lead")):
        raise AddressError(f"a sentence part stands last and once in {text!r}")
    return out


def subitem_of(address: str) -> str | None:
    """The sub-item („5.15“) an address names inside an item's text, or None."""
    parts = [p for p in parse_address(address) if p[0] == "subitem"]
    return parts[0][1] if parts else None


def title_part(address: str) -> bool:
    """Whether the address names the provision's (or the annex's) own title words („наименованието на чл. 27“)."""
    return any(p[0] == "article_title" for p in parse_address(address))


def _row_equal(have: str, want: str) -> bool:
    """A table row's name equals the instruction's, word by word; a word the act abbreviates („В.“) matches the word the
    instruction writes in full („Велико“)."""
    a, b = have.split(), want.split()
    if len(a) != len(b):
        return False
    for x, y in zip(a, b):
        if x == y:
            continue
        if x.endswith(".") and len(x) > 1 and y.startswith(x[:-1]):
            continue
        if y.endswith(".") and len(y) > 1 and x.startswith(y[:-1]):
            continue
        return False
    return True


def _norm_row(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace("„", "\"").replace("“", "\"").replace("”", "\"").replace("–", "-").replace("—", "-")).strip().rstrip(".").lower()


_ANNEX_SECTION = re.compile(r"(?:Раздел\s+)?([IVXLC]+|\d+)\.?")
_ANNEX_LETTER = re.compile(r"\(?([a-zа-я])\)\s")


def annex_section_span(tree: "Tree", idx: int) -> list[int]:
    """The rows of an annex from a section-head row („II.“, „Раздел II“) to the row before the next one, or the annex's end."""
    parent = tree.lines[idx].parent
    rows = tree.lines[parent].children if parent is not None else [idx]
    out = [idx]
    lettered = bool(_ANNEX_LETTER.match(tree.lines[idx].text.strip()))
    for k in rows:
        if k <= idx:
            continue
        t = tree.lines[k].text.strip()
        if _ANNEX_SECTION.fullmatch(t) or (lettered and _ANNEX_LETTER.match(t)):
            break
        out.append(k)
    return out


def sentence_of(address: str) -> int | None:
    """The sentence number an address names, or None (-1: the last sentence)."""
    parts = [p for p in parse_address(address) if p[0] == "sentence"]
    return int(parts[0][1]) if parts else None


def lead_of(address: str) -> bool:
    """Whether the address names the provision's own words before its items („текста преди т. 1“, „основния текст“)."""
    return any(p[0] == "lead" for p in parse_address(address))


def resolve(tree: Tree, address: str) -> int:
    """The one line an address names (``ACT`` for the whole act); AddressError when none or several."""
    parts = [p for p in parse_address(address) if p[0] not in ("sentence", "lead", "article_title", "subitem")]
    kind, n = parts[0]
    if kind == "act":
        return ACT
    if kind == "title":
        found = [k for k, l in enumerate(tree.lines) if l.kind == "title"]
    else:
        found = tree.find(kind, n)
    for kind, n in parts[1:]:
        nxt: list[int] = []
        for f in found:
            if tree.lines[f].kind == "annex_heading" and kind == "annex_row":
                # a table row named by its words: the row line whose text is those words, or the first of the row lines whose
                # joined text is (a cell wrapped onto two lines: „Областна дирекция „Земеделие“ –“, „Варна“)
                rows = tree.lines[f].children
                want = _norm_row(n)
                for pos, k in enumerate(rows):
                    joined = ""
                    for j in rows[pos:pos + 3]:
                        joined = (joined + " " + tree.lines[j].text).strip()
                        if _row_equal(_norm_row(joined), want):
                            nxt.append(k)
                            break
                        if len(_norm_row(joined).split()) >= len(want.split()):
                            break
            elif tree.lines[f].kind == "annex_heading" and kind == "annex_letter":
                nxt.extend(k for k in tree.lines[f].children if re.match(rf"^\(?{re.escape(n)}\)\s", tree.lines[k].text.strip()))
            elif tree.lines[f].kind == "annex_heading" and kind in ("section_heading", "chapter_heading", "part_heading"):
                # a section inside an annex („раздел II“): the row that carries the number alone, or „Раздел II“
                nxt.extend(k for k in tree.lines[f].children
                           if (m := _ANNEX_SECTION.fullmatch(tree.lines[k].text.strip())) and _same_n(m.group(1), n))
            else:
                nxt.extend(tree.find(kind, n, under=f))
        found = nxt
    if len(found) != 1:
        raise AddressError(f"{address!r} names {len(found)} place(s) in the act")
    return found[0]


_LABEL = {"article": "article_head", "sign": "paragraph_sign", "alinea": "alinea", "item": "item", "letter": "letter", "note": "editorial_note",
          "text": "continuation", "annex_row": "annex_row", "prehistory": "prehistory"}


def to_blocks_and_map(tree: Tree) -> tuple[list[Block], dict[int, dict]]:
    """The tree as the blocks and labels the checks read; a heading written on one line is one block, an article title its own block."""
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
    m = _HEADING_WORD.match(t)
    if m:
        kind = _WORD_LEVEL[m.group(1).lower()]
        return Line(kind, HEADING_PREFIX[kind] + t, m.group(2).rstrip("."))
    if _PROVISIONS.match(t) and len(t) < 80:
        return Line("provisions_heading", "## " + t, None)
    if _ANNEX.match(t) and len(t) < 120:
        return Line("annex_heading", "## " + t, _annex_n(t))
    kind, n = _kind_of(t)
    if kind == "text" and context_kind == "annex_row":
        kind = "annex_row"
    return Line(kind, t, n)
