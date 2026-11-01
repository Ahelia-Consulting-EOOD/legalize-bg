"""The operation form of the instruction step and the apply step (step F1 of the plan of 31 October 2026, parts 3 and 4).

The model reads an amending material's instructions (``reading/material.py``) and answers, per instruction, one or more
operations in the fixed form below. The wording of the act is never typed by the model: a new text is a reference to
the material's quoted blocks, an old or new string inside an instruction is a reference to a quoted segment the parser
numbered (``q1``, ``q2`` …), and the address is written in the Gazette's own grammar, which ``reading/acttree.py``
resolves. The script checks the form and applies the operations (D-069): the kind is in the closed set, every
reference exists, the address names exactly one place in the act, an old string occurs exactly once in the addressed
provision (or everywhere, when the instruction says „навсякъде“), a new text begins with a quotation mark in the
material. A failed check is a refusal of the whole material: nothing of it is applied, and the route stops with a case
file. The amendment marker is written in the corpus's convention, which is lex.bg's, without the entry-into-force
clause (decision recorded with F1).

Answer form (one JSON object per material, ``ops.json``)::

    {"material": 246470, "operations": [
       {"id": "§1", "kind": "insert_provision", "address": "чл. 4, ал. 4", "after": "чл. 4, ал. 3", "blocks": [12, 12]},
       {"id": "§3.1", "kind": "replace_words", "address": "чл. 36, ал. 1", "old": "q1", "new": "q2"},
       {"id": "§2", "kind": "repeal", "address": "чл. 5, ал. 1, т. 5"},
       {"id": "§6", "kind": "no_text_change", "note": "entry into force"}]}

Nothing here calls a model or writes a corpus file.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from . import acttree as T
from .material import Material, Node
from .splitter import Block, text_with_joins

KINDS: dict[str, str] = {
    "replace_provision": "the addressed provision (article, alinea, item, letter, §) is replaced whole by the quoted text (blocks)",
    "replace_words": "inside the addressed provision the words old are replaced by new; everywhere: true when the instruction says „навсякъде“",
    "delete_words": "inside the addressed provision the words old are deleted",
    "insert_words": "inside the addressed provision new is inserted after the words anchor, or at the end (where: end) or the start (where: start)",
    "insert_provision": "a new provision (blocks) is inserted after the sibling named by after, at the address it will carry",
    "repeal": "the addressed provision is repealed: its number stays with the repeal marker, its text and children go",
    "renumber": "the addressed provision becomes the number in to (досегашната ал. 2 става ал. 3)",
    "replace_heading": "the addressed heading, or the act's title (address наименованието), takes the words in new (a quoted segment or blocks)",
    "insert_heading": "a new heading (blocks) is inserted after the provision or heading named by after",
    "replace_annex": "the annex named by address is replaced whole by the quoted blocks",
    "insert_annex": "a new annex (blocks) is appended after the annex named by after, or at the end of the act",
    "repeal_annex": "the annex named by address is repealed: its heading stays with the repeal marker, its rows go",
    "corrigendum": "a corrigendum: inside the addressed provision the words old are replaced by new, marked Попр.",
    "no_text_change": "the instruction changes no text of this act (entry into force, a transitional rule, an instruction for another act)",
    "outside_set": "the instruction changes this act's text in a way none of the kinds above expresses; the note says what it does, and the script stops the act for the owner",
}
MARKERS = {"replace_sentence": "Изм.", "replace_provision": "Изм.", "replace_words": "Изм.", "delete_words": "Изм.", "insert_words": "Доп.", "insert_provision": "Нова",
           "repeal": "Отм.", "renumber": "Предишна", "replace_heading": "Изм.", "insert_heading": "Нова", "replace_annex": "Изм.",
           "insert_annex": "Ново", "repeal_annex": "Отм.", "corrigendum": "Попр."}
QUOTE_OPEN = "„“\"«"
QUOTE_CLOSE = "“”\"»"
_Q = re.compile(r"^q(\d+)$")


EXTRA_KINDS = {"replace_sentence": "the sentence the address names (изречение първо, второ, …, последно) is replaced whole by new (a segment reference, a text reference or blocks)"}


class FormError(ValueError):
    """The answer is outside the form or does not fit the act: the material is refused, nothing applied."""


def _resolve(tree: T.Tree, address: str, what: str) -> int:
    try:
        return T.resolve(tree, address)
    except T.AddressError as exc:
        raise FormError(f"{what}: {exc}") from None


@dataclass
class Applied:
    material: int
    issue: str
    operations: list[dict]
    markdown: str
    log: list[str] = field(default_factory=list)


def _node_by_id(mat: Material) -> dict[str, Node]:
    return {n.id: n for n in mat.instructions()}


def _closed_by_sequence(mat: Material, node: Node) -> bool:
    """The parser closed the instruction's quoted run by the sequence (a heading or the next § follows), not by a mark: the
    Gazette's text lost its closer; the finding is recorded on the material, and the run is taken as the parser closed it."""
    if not node.quoted:
        return False
    end = max(node.quoted)
    return any(f.get("kind") == "quote_closed_by_sequence" and f.get("block") == end + 1 for f in getattr(mat, "findings", []) or [])


def _quoted_text(blocks: list[Block], first: int, last: int, run: list[int] | None = None, plain: list[int] | None = None,
                 closed_by_sequence: bool = False) -> list[str]:
    """The lines of a quoted run without the quotation marks that enclose it (and the amending act's punctuation after the closer).

    ``run`` is the instruction's whole quoted run; a range inside it (a new section's heading, then its articles, each its own
    operation) need not open or close the quotation itself: the run does, at its first and last block."""
    if first > last or first < 0 or last >= len(blocks):
        raise FormError(f"blocks [{first}, {last}] are not a range of the material")
    lines = [text_with_joins(blocks[k]) for k in range(first, last + 1)]
    if plain and set(range(first, last + 1)) <= set(plain):
        return [l for l in lines if l.strip()]   # unquoted lines that hang under the instruction (an annex printed after the act): as they stand
    run = sorted(run or [])
    opens_run = not run or first == run[0]
    closes_run = not run or last == run[-1]
    if opens_run:
        if not lines[0][:1] in QUOTE_OPEN:
            raise FormError(f"block {first} does not open with a quotation mark: {lines[0][:40]!r}")
        lines[0] = lines[0][1:]
    if closes_run:
        tail = lines[-1].rstrip()
        stripped = tail.rstrip(".;,:)")
        if stripped and stripped[-1] in QUOTE_CLOSE:
            lines[-1] = stripped[:-1].rstrip()
        elif tail in QUOTE_CLOSE:
            lines = lines[:-1]
        elif closed_by_sequence:
            pass   # the Gazette lost the closer; the parser's finding on the material records it
        else:
            raise FormError(f"block {last} does not close the quotation: {tail[-40:]!r}")
    return [l for l in lines if l.strip()]


def _segment(node: Node, ref, nodes: dict[str, Node] | None = None) -> str:
    """A quoted segment of the instruction (q1, q2, …), or of its parent when the instruction has none („§ 5. … думите „X“ се заменят с „Y“: 1. в чл. 2 …“);
    or, where the Gazette's nested quotation marks cut a segment short, the words themselves as ``{"text": "…"}``, which must stand in the
    instruction's own text symbol for symbol (the material's words, checked, never the act's)."""
    if isinstance(ref, dict) and isinstance(ref.get("text"), str):
        text = ref["text"]
        if not text.strip():
            raise FormError(f"{node.id}: an empty text reference")
        # a punctuation mark the instruction names in words („се поставя запетая“, „запетаята пред тях се заличават“) is the mark itself
        named = {",": "запета", ".": "точка", ";": "точка и запетая", ":": "двоеточие", "–": "тире", "-": "тире"}
        if text.strip() in named:
            if named[text.strip()] in node.text.lower() or (nodes and any(named[text.strip()] in a.text.lower() for a in _ancestors(node, nodes))):
                return text
            raise FormError(f"{node.id}: the instruction names no {text.strip()!r}")
        if text not in node.text and not (nodes and "." in node.id and any(text in a.text for a in _ancestors(node, nodes))):
            raise FormError(f"{node.id}: the text {text[:60]!r} does not stand in the instruction")
        return text   # exactly as it stands in the instruction, marks included
    m = _Q.match(str(ref))
    if not m:
        raise FormError(f"{node.id}: {ref!r} is not a quoted segment reference")
    cur: Node | None = node
    while cur is not None:
        if 1 <= int(m.group(1)) <= len(cur.inline_quotes):
            return cur.inline_quotes[int(m.group(1)) - 1]
        if cur.inline_quotes or nodes is None or "." not in cur.id:
            break
        cur = nodes.get(cur.id.rsplit(".", 1)[0])
    raise FormError(f"{node.id}: {ref!r} is not a quoted segment of the instruction (it has {len(node.inline_quotes)})")


def _ancestors(node: Node, nodes: dict[str, Node]) -> list[Node]:
    out = []
    cur = node.id
    while "." in cur:
        cur = cur.rsplit(".", 1)[0]
        if cur in nodes:
            out.append(nodes[cur])
    return out


def check_form(answer: dict, mat: Material, blocks: list[Block]) -> list[dict]:
    """The operations of an answer against the material: every problem is a FormError; the operations with their texts resolved."""
    if not isinstance(answer, dict) or not isinstance(answer.get("operations"), list):
        raise FormError("the answer is not {material, operations: [...]}")
    nodes = _node_by_id(mat)
    out: list[dict] = []
    seen_ids: set[str] = set()
    for k, op in enumerate(answer["operations"]):
        if not isinstance(op, dict):
            raise FormError(f"operation {k} is not an object")
        if "id" not in op and "instruction" in op:
            op = {**op, "id": op.pop("instruction")}   # the key's other name, read as the form's
        if op.get("kind") not in KINDS and op.get("kind") not in EXTRA_KINDS:
            raise FormError(f"operation {k}: kind {op.get('kind')!r} is not one of {sorted(KINDS)}")
        node = nodes.get(str(op.get("id")))
        if node is None and op.get("kind") == "no_text_change":
            continue   # an id the parser no longer carries (a line now read as quoted text): nothing to change, nothing to check
        if node is None:
            raise FormError(f"operation {k}: id {op.get('id')!r} is not an instruction of the material")
        seen_ids.add(node.id)
        kind = op["kind"]
        extra = set(op) - {"id", "kind", "address", "after", "blocks", "old", "new", "anchor", "where", "to", "everywhere", "note", "punctuation"}
        if extra:
            raise FormError(f"{node.id}: keys outside the form: {sorted(extra)}")
        res = {"id": node.id, "kind": kind, "note": str(op.get("note", ""))}
        if kind in ("no_text_change", "outside_set"):
            if kind == "outside_set" and not res["note"].strip():
                raise FormError(f"{node.id}: outside_set needs a note that says what the instruction does")
            out.append(res)
            continue
        if not isinstance(op.get("address"), str) or not op["address"].strip():
            raise FormError(f"{node.id}: {kind} needs an address")
        res["address"] = op["address"].strip()
        if kind == "replace_provision" and "blocks" not in op and "new" in op and _names_lead(res["address"]):
            # „текстът преди т. 1 се изменя така: „…““ with the words quoted inline: the segment replaces the provision's own words
            res["new"] = _segment(node, op.get("new"), nodes); res["new_ref"] = op.get("new")
            out.append(res)
            continue
        if kind == "insert_provision" and "blocks" not in op and "new" in op and _names_sentence(res["address"]):
            # „създава се изречение второ: „…““ with the sentence quoted inline: the segment is the new sentence
            res["new"] = _segment(node, op.get("new"), nodes); res["new_ref"] = op.get("new"); res["after"] = ""
            out.append(res)
            continue
        if kind in ("replace_provision", "insert_provision", "insert_heading", "replace_annex", "insert_annex") or (kind == "replace_heading" and "blocks" in op):
            b = op.get("blocks")
            if not (isinstance(b, list) and len(b) == 2 and all(isinstance(x, int) for x in b)):
                raise FormError(f"{node.id}: {kind} needs blocks [first, last]")
            allowed = set(node.quoted) | set(node.continuation)
            if allowed and not set(range(b[0], b[1] + 1)) <= allowed:
                raise FormError(f"{node.id}: blocks [{b[0]}, {b[1]}] lie outside the instruction's quoted text {sorted(allowed)}")
            if not allowed:
                res["blocks_outside_parse"] = True   # the parser found no quoted text here: the model's range is recorded as such
            res["lines"] = _quoted_text(blocks, b[0], b[1], node.quoted if allowed else None, node.continuation if allowed else None,
                                        closed_by_sequence=_closed_by_sequence(mat, node))
            res["blocks"] = [b[0], b[1]]
            res["hints"] = [blocks[k].hint for k in range(b[0], b[1] + 1)]
        if kind in ("insert_provision", "insert_heading", "insert_annex"):
            res["after"] = str(op.get("after", "")).strip()
        if kind == "delete_words" and "old" not in op and "anchor" in op:
            # „след думите „…“ се поставя точка и текстът докрая се заличава“: the words after (or before) the anchor go
            if op.get("where") not in ("after", "before"):
                raise FormError(f"{node.id}: delete_words with an anchor needs where: after (the rest of the text goes) or before")
            res["anchor"] = _segment(node, op.get("anchor"), nodes); res["anchor_ref"] = op.get("anchor"); res["where"] = op["where"]
        elif kind in ("replace_words", "delete_words", "corrigendum"):
            res["old"] = _segment(node, op.get("old"), nodes); res["old_ref"] = op.get("old")
        if op.get("punctuation") is not None:
            # „думите „…“ и запетаята пред тях се заличават“: the mark next to the deleted words goes with them;
            # „се поставя запетая и се добавя „…““: the comma comes with the inserted words
            if kind not in ("delete_words", "insert_words") or op["punctuation"] not in ("before", "after", "brackets"):
                raise FormError(f"{node.id}: punctuation is before or after, for delete_words or insert_words only (brackets: the parentheses around the words go, the words stay)")
            res["punctuation"] = op["punctuation"]
        if kind in ("replace_words", "insert_words", "corrigendum") or (kind in ("replace_heading", "replace_sentence") and "blocks" not in op):
            res["new"] = _segment(node, op.get("new"), nodes); res["new_ref"] = op.get("new")
        if kind == "replace_sentence" and "blocks" in op:
            b = op["blocks"]
            if not (isinstance(b, list) and len(b) == 2 and all(isinstance(x, int) for x in b)):
                raise FormError(f"{node.id}: replace_sentence needs blocks [first, last] or new")
            res["lines"] = _quoted_text(blocks, b[0], b[1], node.quoted or None, node.continuation or None); res["blocks"] = [b[0], b[1]]
        if kind == "insert_words":
            where = op.get("where", "after")
            if where not in ("after", "before", "end", "start"):
                raise FormError(f"{node.id}: where {where!r} is not after, before, end or start")
            res["where"] = where
            if where in ("after", "before"):
                res["anchor"] = _segment(node, op.get("anchor"), nodes); res["anchor_ref"] = op.get("anchor")
        if kind in ("replace_words", "delete_words"):
            res["everywhere"] = bool(op.get("everywhere", False))
        if kind == "renumber":
            if not isinstance(op.get("to"), str) or not op["to"].strip():
                raise FormError(f"{node.id}: renumber needs to")
            res["to"] = op["to"].strip()
        out.extend(_expand_range(res))
    leaves = [n.id for n in mat.instructions() if not n.children]
    missing = [i for i in leaves if i not in seen_ids]
    if missing:
        raise FormError(f"no operation for the instruction(s) {', '.join(missing)}; every instruction gets at least one (no_text_change when it changes nothing)")
    return out


_MARKER_ENTRY = re.compile(r"^(?P<words>[^-]+?)\s*-\s*ДВ,\s*бр\.\s*(?P<num>\d+)\s*от\s*(?P<year>\d{4})\s*г\.(?P<extra>.*)$")
_HEAD_RX = (r"^(?:[^*\n]{1,160}?\s+)?\*\*(?:Чл\.\s*\S+\.|Член\s+единствен\.|§\s*\S+\.|Параграф\s+единствен\.)\*\*\s*", r"^\(\d{1,3}[а-я]?\)\s*",
            r"^\d{1,3}(?:[а-я]{1,2})?\.(?:\s+|$|(?=[А-Яа-я(„\"]))", r"^[а-я]{1,3}\)(?:\s+|$)")
_HEADING_MARKER = re.compile(r"\s*\(((?:Загл\. изм|Изм|Нова|Нов|Отм|Ново|Доп|Предишн)[^()]*)\)\s*$", re.I)
_PAIRS = {frozenset({"изм", "доп"}): "Изм. и доп.", frozenset({"нова", "изм"}): "Нова", frozenset({"нов", "изм"}): "Нов"}


def _merge_words(have: str, word: str) -> str:
    """Two markers of one issue on one line become one, in lex.bg's form („Изм. и доп.“); the same word twice stays once."""
    a, b = have.rstrip(".").lower(), word.rstrip(".").lower()
    if a == b or b in a.split(" и "):
        return have
    pair = _PAIRS.get(frozenset(x.strip(".") for x in [a.replace(" и ", " ").split()[0], b]))
    return pair if pair else f"{have.rstrip('.')} и {word[0].lower() + word[1:]}"


def _marker(line: T.Line, word: str, issue: str, extra: str = "") -> None:
    """Add „(Изм. - ДВ, бр. N от YYYY г.)“ after the head, or extend an existing marker with „, изм. - ДВ, …“ (lex.bg's form); two
    operations of one issue on one line give one entry („Изм. и доп.“). A heading's or an annex heading's marker goes at the end
    of the line, as lex.bg writes „… (Загл. изм. - ДВ, …)“."""
    num, year = issue.split("/")
    low = word[0].lower() + word[1:] if line.kind in ("item", "letter") else word
    piece = f"{low} - ДВ, бр. {num} от {year} г." + (f", {extra}" if extra else "")
    if line.kind in T.HEADING_PREFIX or line.kind == "title":
        m = _HEADING_MARKER.search(line.text)
        if m:
            inner = m.group(1)
            if piece.lower() in inner.lower():
                return   # several operations of one issue on one annex or heading: one entry (lex.bg's form)
            line.text = line.text[: m.start()].rstrip() + f" ({inner}, {piece[0].lower() + piece[1:]})"
        else:
            line.text = line.text.rstrip() + f" ({piece})"
        return
    text = line.text
    head_end = 0
    for rx in _HEAD_RX:
        m = re.match(rx, text)
        if m:
            head_end = m.end()
            break
    rest = text[head_end:]
    sep = "" if head_end == 0 or text[head_end - 1].isspace() else " "
    m = T._MARKER.match(rest)
    if m:
        inner = m.group(0).rstrip()
        inner = inner[1:-1] if inner.endswith(")") else inner[1:]
        entries = [e.strip() for e in re.split(r",\s*(?=(?:[Ии]зм|[Дд]оп|[Нн]ов|[Оо]тм|[Пп]опр|[Пп]редишн|[Зз]агл)[^,]*-\s*ДВ)", inner)]
        last = _MARKER_ENTRY.match(entries[-1]) if entries else None
        if last and (last.group("num"), last.group("year")) == (num, year) and not extra and not last.group("extra").strip(" ,") and word.lower().startswith(("изм", "доп")) and last.group("words").lower().startswith(("изм", "доп")):
            merged = _merge_words(last.group('words').strip(), low)
            if line.kind in ("item", "letter"):
                merged = merged[0].lower() + merged[1:]
            entries[-1] = f"{merged} - ДВ, бр. {num} от {year} г."
            new = "(" + ", ".join(entries) + ") "
        elif last and (last.group("num"), last.group("year")) == (num, year) and last.group("words").strip().lower() == low.lower():
            new = "(" + inner + ") "
        else:
            new = f"({inner}, {piece[0].lower() + piece[1:]}) "
        line.text = text[:head_end] + sep + new + rest[m.end():]
    else:
        line.text = text[:head_end] + sep + f"({piece}) " + rest
    line.text = line.text.rstrip()


def _sentences(body: str) -> list[tuple[int, int]]:
    """The spans of the sentences of a provision's words: a full stop followed by a space and a capital, or the end."""
    spans: list[tuple[int, int]] = []
    start = 0
    for m in re.finditer(r"\.\s+(?=[А-ЯA-Z„\"(])", body):
        spans.append((start, m.end()))
        start = m.end()
    if start < len(body):
        spans.append((start, len(body)))
    return spans or [(0, len(body))]


def _scope_text(body: str, sentence, what: str) -> tuple[int, int]:
    if sentence is None:
        return 0, len(body)
    if isinstance(sentence, str) and sentence.startswith("sub:"):
        # „т. 5.15“ inside the item's flattened text: from „5.15.“ to the next „N.M.“ or the end
        sub = sentence[4:]
        m = re.search(rf"(?<![\d.]){re.escape(sub)}\.\s", body)
        if not m:
            raise FormError(f"{what}: the sub-item {sub!r} does not open in the item's text")
        nxt = re.search(r"\s\d+\.\d+\.\s", body[m.end():])
        return m.start(), (m.end() + nxt.start()) if nxt else len(body)
    spans = _sentences(body)
    idx = len(spans) - 1 if sentence == -1 else sentence - 1
    if idx < 0 or idx >= len(spans):
        raise FormError(f"{what}: the provision has {len(spans)} sentence(s), not {sentence}")
    return spans[idx]


def _set_body(line: T.Line, body: str) -> None:
    line.text = (line.head() + body).rstrip()


def _finder(old: str):
    """The places of ``old`` in a text. A number („цифрата „1““) matches a whole number only, never the digit inside „11“ or „13“."""
    if re.fullmatch(r"\d+", old):
        rx = re.compile(rf"(?<!\d){re.escape(old)}(?!\d)")
    else:
        pat = _loose(old)
        # the Gazette names words, not stems: „съюзът „и““ is the word „и“, never the letter inside „или“; a segment that
        # opens or closes with a letter matches at a word boundary there
        letters = "А-Яа-яЁёA-Za-z"
        if old[:1] and re.match(rf"[{letters}]", old[:1]):
            pat = rf"(?<![{letters}])" + pat
        if old[-1:] and re.match(rf"[{letters}]", old[-1:]):
            pat = pat + rf"(?![{letters}])"
        rx = re.compile(pat)
    return lambda text: [(m.start(), m.end()) for m in rx.finditer(text)]


_DASHES, _QUOTES = "-–—", "„“”\"«»"


def _loose(old: str) -> str:
    """The words as a pattern: a dash matches any dash, a quotation mark any mark, and the space before an ellipsis is free
    (the Gazette writes „глава шеста – чл. 242“ where the act has „глава шеста - чл. 242“, „Социално подпомагане“ where the
    act has “Социално подпомагане”, „по…“ where the act has „по …“)."""
    out: list[str] = []
    parts = old.split("…")
    q = "[„“”\"«»]"
    for k, part in enumerate(parts):
        if k:
            out.append(r"\s*…")
        if k < len(parts) - 1:
            part = part.rstrip()
        for ch in part:
            if ch in _DASHES:
                out.append("[-–—]")
            elif ch in _QUOTES:
                out.append(q + "?")       # a mark the instruction writes may be absent in the act
            elif ch == " ":
                out.append(rf"\s+{q}?(?:№\s*)?")   # a mark the act writes („наричан по-нататък „Регламент…““), or a „№“ before a number, may be absent in the instruction
            elif ch in ",;":
                out.append(rf"\s*{re.escape(ch)}?")   # a comma the instruction writes may be missing in the act („детето както и“), and a stray space before it is free
            else:
                out.append(re.escape(ch))
    return "".join(out)


def _row_scope(tree: T.Tree, idx: int) -> list[int]:
    """A table row flattened by the Gazette's HTML: the named cell (which may wrap onto a second row line, „Областна дирекция
    „Земеделие“ –“ then „Варна“) and the number cells printed as the rows after it."""
    out = [idx]
    parent = tree.lines[idx].parent
    rows = tree.lines[parent].children if parent is not None else []
    name_open = tree.lines[idx].text.rstrip().endswith(("–", "-", ","))
    for k in rows:
        if k <= idx:
            continue
        t = tree.lines[k].text.strip()
        if re.fullmatch(r"[\d\s.,–-]+", t):
            out.append(k)
            name_open = False
        elif name_open:
            out.append(k)
            name_open = t.endswith(("–", "-", ","))
        else:
            break
    return out


def _title_words(tree: T.Tree, idx: int, op: dict, what: str, issue: str, log: list[str]) -> None:
    """A words operation on a provision's own title („наименованието на чл. 27“) or on an annex heading's words."""
    line = tree.lines[idx]
    kind = op["kind"]
    if line.kind == "annex_heading":
        words = line.text[3:] if line.text.startswith("## ") else line.text
        m = _HEADING_MARKER.search(words)
        core, marker = (words[: m.start()].rstrip(), words[m.start():]) if m else (words, "")
        prefix = "## " if line.text.startswith("## ") else ""
    elif line.kind == "article" and line.title:
        core, marker, prefix = line.title, "", ""
    elif line.kind in T.HEADING_PREFIX:
        # a chapter's or section's heading words; the number stays
        hashes = len(line.text) - len(line.text.lstrip("#"))
        prefix = line.text[:hashes] + " "
        words = line.text[hashes:].strip()
        m = _HEADING_MARKER.search(words)
        core, marker = (words[: m.start()].rstrip(), words[m.start():]) if m else (words, "")
    else:
        raise FormError(f"{what}: {op['address']!r} names a title, and the provision has none")
    find = _finder(op["old"])
    pos = find(core)
    if not pos:
        pos = [(m.start(), m.end()) for m in re.compile(_loose(op["old"]), re.I).finditer(core)]   # a heading printed in capitals
    if kind == "delete_words" and T._same_n(core.strip(), op["old"]) and line.kind == "article":
        new_core = ""
    else:
        if len(pos) != 1:
            raise FormError(f"{what}: the words {op['old']!r} occur {len(pos)} times in the title {core!r}")
        a, b = pos[0]
        new_core = (core[:a] + (op.get("new", "") if kind != "delete_words" else "") + core[b:]).strip()
        new_core = re.sub(r"  +", " ", new_core)
    if line.kind == "annex_heading":
        line.text = prefix + new_core + marker
        _marker(line, MARKERS[kind], issue)
    elif line.kind in T.HEADING_PREFIX:
        line.text = prefix + new_core + marker
        _marker(line, "Загл. изм.", issue)
    else:
        head_rest = line.text[len(line.title):].lstrip()
        line.text = (new_core + " " + head_rest) if new_core else head_rest
        line.title = new_core or None
        _marker(line, "Загл. изм." if new_core else "Загл. отм.", issue)
    log.append(f"{what}: title words changed")


def _with_punctuation(tree: T.Tree, idx: int, old: str, side: str, what: str, sentence: int | None, lead: bool) -> str:
    """The deleted words together with the comma or semicolon the instruction names before or after them, as they stand in the text."""
    scope = tree.addressable_lines() if idx == T.ACT else ([idx] if lead else tree.subtree(idx))
    find = _finder(old)
    found: list[tuple[str, int]] = []
    for k in scope:
        body = tree.lines[k].body()
        a, b = _scope_text(body, sentence if k == idx else None, what)
        part = body[a:b]
        found.extend((part, p, e) for p, e in find(part))
    if len(found) != 1:
        raise FormError(f"{what}: the words {old!r} occur {len(found)} times at the address; the mark next to them cannot be placed")
    part, p, e = found[0]
    if side == "before":
        j = p - 1
        while j >= 0 and part[j] == " ":
            j -= 1
        if j < 0 or part[j] not in ",;":
            raise FormError(f"{what}: no comma or semicolon stands before the words {old!r}")
        return part[j:e]
    j = e
    while j < len(part) and part[j] == " ":
        j += 1
    if j >= len(part) or part[j] not in ",;":
        raise FormError(f"{what}: no comma or semicolon stands after the words {old!r}")
    return part[p:j + 1]


def _replace_in(tree: T.Tree, idx: int, old: str, new: str, everywhere: bool, what: str, sentence: int | None = None, lead: bool = False) -> tuple[int, list[int]]:
    """Replace old by new in the words of the addressed provision and what hangs under it (its own words only with ``lead``; the whole act
    for ``ACT``); the count replaced and the lines changed."""
    scope = tree.addressable_lines() if idx == T.ACT else ([idx] if lead else tree.subtree(idx))
    if idx != T.ACT and tree.lines[idx].kind == "annex_row":
        scope = _row_scope(tree, idx)
    if idx == T.ACT:
        everywhere = True
    find0 = _finder(old)
    if new.startswith(old) and len(new) > len(old):
        # „министъра на земеделието“ → „министъра на земеделието и храните“: a place that already reads the new words is not changed again
        ext = new[len(old):]
        find = lambda text: [(p, e) for p, e in find0(text) if not text[e:].startswith(ext)]
    else:
        find = find0
    hits: list[tuple[int, int, int]] = []
    for k in scope:
        body = tree.lines[k].body()
        a, b = _scope_text(body, sentence if k == idx else None, what)
        hits.append((k, a, b)) if find(body[a:b]) else None
    count = sum(len(find(tree.lines[k].body()[a:b])) for k, a, b in hits)
    if count == 0:
        raise FormError(f"{what}: the words {old!r} do not occur in {'the act' if idx == T.ACT else tree.lines[idx].text[:50]!r}")
    if count > 1 and not everywhere:
        raise FormError(f"{what}: the words {old!r} occur {count} times at the address; the instruction does not say навсякъде")
    changed: list[int] = []
    for k, a, b in hits:
        changed.append(k)
        l = tree.lines[k]
        body = l.body()
        part = body[a:b]
        # a quoted segment that ends with an abbreviation's dot („до 30 000 лв.“) closed the sentence too; the sentence keeps its full stop
        fix = new + "." if old.endswith(".") and not new.endswith(".") and part.rstrip().endswith(old) else new
        pos = find(part)
        if everywhere:
            replaced = part
            for p, e in reversed(pos):
                replaced = replaced[:p] + new + replaced[e:]
        else:
            replaced = part[:pos[0][0]] + fix + part[pos[0][1]:]
        nb = body[:a] + replaced + body[b:]
        nb = re.sub(r" +([,;.])(?=\s|$)", r"\1", nb)   # a mark that replaced a word („или“ → „,“) closes up to the word before it
        nb = re.sub(r",(?:\s*,)+", ",", nb)             # a quoted segment that ends with the sentence's comma („… (ЗЕЕ),“) meets the comma already there
        if new == "":
            nb = re.sub(r"  +", " ", nb).replace(" ,", ",").replace(" .", ".").replace(" ;", ";").strip()
            nb = re.sub(r",(?:\s*,)+", ",", nb)          # „работи, [X], председателя“ → one comma
            nb = re.sub(r"[,;](?=\s*[.;])", "", nb)       # „защита, [X].“ → „защита.“
            nb = re.sub(r"\s[-–—](?=\s*[,.;])", "", nb)   # „осиновяващият - [X], който“ → „осиновяващият, който“
        _set_body(l, nb)
    return count, changed


_LOOKALIKE = {"a": "а", "e": "е", "o": "о", "c": "с", "p": "р", "x": "х", "y": "у"}


def _cyrillic_marker(text: str) -> str:
    """A letter marker the Gazette typed in Latin („a) …“ for „а) …“): read as the Cyrillic lookalike; the words stay as they are."""
    m = re.match(r"^([aeocpxy])\)(\s)", text)
    return _LOOKALIKE[m.group(1)] + text[1:] if m else text


def _lines_from(texts: list[str], context_kind: str | None, hints: list[str] | None = None) -> list[T.Line]:
    out = [T.line_from_text(_cyrillic_marker(t), context_kind) for t in texts]
    joined: list[T.Line] = []
    for k, l in enumerate(out):
        if joined and l.kind == "text" and joined[-1].kind in ("part_heading", "chapter_heading", "section_heading", "subsection_heading") and T.NUMBER_LINE.match(T.strip_line(joined[-1].text)):
            joined[-1].text = f"{joined[-1].text} {l.text}"
        elif context_kind == "annex_row" and len(joined) == 1 and joined[0].kind == "annex_heading" and _bare_annex_heading(joined[0].text) \
                and l.kind in ("annex_row", "text") and hints and k < len(hints) and hints[k] == "DvCenter" and re.search(r"[А-Яа-я]", l.text):
            # the annex's title line, centred under the heading: the assembler reads the promulgation with the two joined
            joined[0].text = f"{joined[0].text.rstrip()} {l.text.strip()}"
        elif joined and l.kind == "article" and not l.title and joined[-1].kind == "text" and _is_title(joined[-1].text):
            # an article's own title printed on the line before its head (the Family Code's form): the head carries it
            title = T.strip_line(joined[-1].text).strip()
            l.title = title
            l.text = f"{title} {l.text}"
            joined[-1] = l
        else:
            joined.append(l)
    return joined


def _bare_annex_heading(text: str) -> bool:
    """„## Приложение към чл. 6, ал. 2“ or „## Приложение № 3“ with no title words after the identity."""
    t = text[3:] if text.startswith("## ") else text
    m = T._ANNEX_REF.match(t) or T._ANNEX.match(t)
    return bool(m) and not t[m.end():].strip(" .")


def _is_title(text: str) -> bool:
    t = T.strip_line(text).strip()
    return 0 < len(t) <= 800 and not t.endswith((".", ";", ":", ",")) and not t.startswith("(")


def _insert_after(tree: T.Tree, after_idx: int, new_lines: list[T.Line]) -> tuple[int, int]:
    end = max(tree.subtree(after_idx)) + 1
    tree.lines[end:end] = new_lines
    return end, end + len(new_lines) - 1


def _reparse(tree: T.Tree) -> T.Tree:
    return T.parse(tree.to_markdown())


def _span_after_reparse(tree: T.Tree, address: str, first: int, last: int, what: str) -> int:
    """After a re-parse the inserted or replaced lines must hold the address (the inline alinea moves the count by at most the join)."""
    idx = _resolve(tree, address, what)
    if not (first - 1 <= idx <= last + 1):
        raise FormError(f"{what}: the address {address!r} does not name the inserted text (line {idx}, inserted {first}-{last})")
    return idx


def _instruction_text(mat: Material, op_id: str) -> str:
    node = _node_by_id(mat).get(op_id)
    return getattr(node, "text", "") or ""


def _repealed_at(tree: T.Tree, address: str) -> int | None:
    """The line of a repealed provision that still carries the address („(2) (Отм. - ДВ, …)“), or None."""
    try:
        idx = T.resolve(tree, address)
    except T.AddressError:
        return None
    if idx == T.ACT:
        return None
    l = tree.lines[idx]
    marker = l.marker() or ""
    return idx if not l.body().strip() and re.search(r"отм\.", marker, re.I) and l.kind not in T.HEADING_PREFIX else None


def _names_lead(address: str) -> bool:
    try:
        return T.lead_of(address)
    except T.AddressError:
        return False


def _names_sentence(address: str) -> bool:
    try:
        return T.sentence_of(address) is not None
    except T.AddressError:
        return False


_LIST = re.compile(r"^(?P<head>.*?)(?P<list>\d+\s*(?:(?:[–-]|,|\bи\b)\s*\d+\s*)+)$")


def _numbers(text: str) -> list[int]:
    """„14 – 17“ → 14, 15, 16, 17; „2 и 3“ → 2, 3; „2, 3 и 5“ → 2, 3, 5."""
    text = text.strip()
    rng = re.fullmatch(r"(\d+)\s*[–-]\s*(\d+)", text)
    if rng:
        a, b = int(rng.group(1)), int(rng.group(2))
        return list(range(a, b + 1)) if b >= a else []
    return [int(x) for x in re.split(r"\s*(?:,|\bи\b)\s*", text) if x.strip()]


def _expand_range(res: dict) -> list[dict]:
    """„Досегашните т. 14 – 17 стават съответно 15 – 18“, „ал. 2 и 3 стават ал. 3 и 4“: one renumber per number, highest first
    (so none lands on a taken number)."""
    if res["kind"] != "renumber":
        return [res]
    m = _LIST.match(res["address"].strip().rstrip("."))
    n = _LIST.match(str(res.get("to", "")).strip().rstrip("."))
    if not m or not n:
        return [res]
    src, dst = _numbers(m.group("list")), _numbers(n.group("list"))
    if not src or len(src) != len(dst):
        raise FormError(f"{res['id']} renumber: the numbers {m.group('list')!r} and {n.group('list')!r} differ in count")
    head = m.group("head")
    try:
        kind = T.parse_address(head + str(src[0]))[-1][0]
    except T.AddressError as exc:
        raise FormError(f"{res['id']} renumber: {exc}") from None
    word = (n.group("head").strip() or _word(kind)).rstrip()
    pairs = sorted(zip(src, dst), reverse=True)
    return [{**res, "address": f"{head}{a}", "to": f"{word} {b}"} for a, b in pairs]


def _marked(tree: T.Tree, k: int) -> int:
    """The line that carries the marker of a change at line k: an annex row's change is marked on its annex heading."""
    l = tree.lines[k]
    return l.parent if l.kind == "annex_row" and l.parent is not None else k


def _resolve_sibling(tree: T.Tree, after: str, address: str, what: str) -> int:
    """The provision the new text follows: ``after`` as written, or, when it is a bare part („т. 1“) that names several places,
    that part under the address's own parent („чл. 2, ал. 2, т. 1“)."""
    try:
        return T.resolve(tree, after)
    except T.AddressError as exc:
        try:
            parts = [p for p in T.parse_address(address) if p[0] not in ("sentence", "lead", "article_title", "subitem")]
            own = [p for p in T.parse_address(after) if p[0] not in ("sentence", "lead")]
        except T.AddressError:
            raise FormError(f"{what}: {exc}") from None
        if len(own) == 1 and len(parts) > 1:
            parent = ", ".join(f"б. „{n}“" if k == "letter" else f"{_word(k)} {n}" for k, n in parts[:-1])
            return _resolve(tree, f"{parent}, {after}", what)
        raise FormError(f"{what}: {exc}") from None


def _taken(tree: T.Tree, address: str) -> bool:
    """Whether a provision of the act already carries the address."""
    try:
        T.resolve(tree, address)
        return True
    except T.AddressError as exc:
        return "names 0 place" not in str(exc)


def _siblings(a: str, b: str) -> bool:
    """Two addresses of provisions of the same kind under the same parent."""
    try:
        pa = [p for p in T.parse_address(a) if p[0] != "sentence"]
        pb = [p for p in T.parse_address(b) if p[0] != "sentence"]
    except T.AddressError:
        return False
    return len(pa) == len(pb) and pa[:-1] == pb[:-1] and pa[-1][0] == pb[-1][0]


def _renumbered_address(address: str, to: str) -> str:
    """„чл. 25, ал. 3“ moved „ал. 4“ → „чл. 25, ал. 4“: the same path with the last part's number replaced."""
    parts = [p for p in T.parse_address(address) if p[0] not in ("sentence", "lead")]
    new_n = T.parse_address(to)[-1][1]
    parts[-1] = (parts[-1][0], new_n)
    return ", ".join(f"б. „{n}“" if kind == "letter" else f"{_word(kind)} {n}" for kind, n in parts)


def _renumber_taken(tree: T.Tree, ops: list[dict], j: int, done: set[int], issue: str, log: list[str], before: str) -> T.Tree:
    """Apply the renumber at ops[j] early, first moving (recursively) the holder of its own target number."""
    target = _renumbered_address(ops[j]["address"], ops[j]["to"])
    if _taken(tree, target):
        movers = [k for k in range(j + 1, len(ops)) if k not in done and ops[k]["kind"] == "renumber" and ops[k]["address"] == target]
        if movers:
            done.add(movers[0])
            tree = _renumber_taken(tree, ops, movers[0], done, issue, log, ops[j]["id"])
    tree = _renumber(tree, ops[j], issue, log, before=before)
    _follow_moves(tree, ops, [(ops[j]["id"], ops[j]["address"], target)], j + 1, done)
    return tree


def _follow_moves(tree: T.Tree, ops: list[dict], pairs: list[tuple[str, str, str]], start: int, done: set[int]) -> None:
    """„Досегашната ал. 3 става ал. 4 и в нея в т. 4 …“: an instruction's later operation may name the moved provision by its
    former number; it follows the move only where the address as written no longer names a place („стават ал. 3 и 4 и се
    изменят така: (3) … (4) …“ already names the new numbers, and stays)."""
    for op_id, old_addr, new_addr in pairs:
        for k in range(start, len(ops)):
            o = ops[k]
            if k in done or o["id"] != op_id or not o.get("address", "").startswith(old_addr):
                continue
            if _taken(tree, o["address"]):
                continue
            o["address"] = new_addr + o["address"][len(old_addr):]


def _renumber(tree: T.Tree, op: dict, issue: str, log: list[str], before: str | None = None) -> T.Tree:
    what = f"{op['id']} renumber"
    idx = _resolve(tree, op["address"], what)
    line = tree.lines[idx] if idx != T.ACT else None
    if line is None:
        raise FormError(f"{what}: needs a provision")
    try:
        parts = T.parse_address(op["to"])
    except T.AddressError as exc:
        raise FormError(f"{what}: {exc}") from None
    new_n = parts[-1][1]
    if line.kind in ("article", "sign") and parts[-1][0] == "alinea":
        # „Досегашният текст става ал. 1“: the provision's own words become its first alinea, its items under it; the number stays
        body = line.body().strip()
        if any(tree.lines[c].kind == "alinea" for c in line.children):
            raise FormError(f"{what}: {op['address']!r} already has alineas; its text cannot become ал. {new_n}")
        if not body:
            raise FormError(f"{what}: {op['address']!r} has no words of its own to become ал. {new_n}")
        line.text = f"{line.head().rstrip()} ({new_n}) {body}"
        tree = _reparse(tree)
        al = _resolve(tree, f"{op['address']}, ал. {new_n}", what)
        _marker(tree.lines[al], f"Предишен текст на {_word(line.kind)} {line.n}", issue)
        log.append(f"{what}: the text of {op['address']} became ал. {new_n}")
        return tree
    body = line.body()
    head = line.head()
    old_n = line.n
    head2 = head.replace(old_n, new_n, 1) if old_n and old_n in head else head
    if head2 == head:
        raise FormError(f"{what}: the number {old_n!r} was not found in the head {head!r}")
    line.text = head2 + body
    line.n = new_n
    gender = "Предишен" if line.kind in ("article", "sign") else "Предишна"
    _marker(line, f"{gender} {_word(line.kind)} {old_n}", issue)
    log.append(f"{what}: {old_n} -> {new_n}" + (f" (moved before {before})" if before else ""))
    return tree


def apply(answer: dict, mat: Material, blocks: list[Block], markdown: str, issue: str) -> Applied:
    """Apply a material's operations to the body; the form is checked first, and any failure applies nothing."""
    ops = check_form(answer, mat, blocks)
    tree = T.parse(markdown)
    if tree.to_markdown() != markdown:
        raise FormError("the body does not round-trip through the act tree; the apply step cannot hold it")
    log: list[str] = []
    done: set[int] = set()
    for i, op in enumerate(ops):
        if i in done:
            continue
        kind = op["kind"]
        what = f"{op['id']} {kind}"
        if kind == "no_text_change":
            log.append(f"{what}: nothing")
            continue
        if kind == "outside_set":
            raise FormError(f"{what}: outside the closed set of operations: {op['note']}")
        try:
            sentence = T.sentence_of(op["address"]) if "address" in op else None
            sub = T.subitem_of(op["address"]) if "address" in op else None
        except T.AddressError as exc:
            raise FormError(f"{what}: {exc}") from None
        if sub is not None:
            if sentence is not None:
                raise FormError(f"{what}: a sub-item and a sentence cannot both scope an address")
            if kind not in ("replace_words", "delete_words", "insert_words", "corrigendum"):
                raise FormError(f"{what}: a sub-item address fits only an operation on words")
            sentence = f"sub:{sub}"
        if sentence is not None and kind not in ("replace_words", "delete_words", "insert_words", "corrigendum", "replace_sentence", "repeal", "insert_provision", "renumber"):
            raise FormError(f"{what}: a sentence address fits only an operation on words")
        if kind == "insert_provision" and sentence is not None:
            # „създава се изречение второ“: the quoted text joins the provision's words as its new last sentence
            idx = _resolve(tree, op["address"], what)
            line = tree.lines[idx] if idx != T.ACT else None
            if line is None:
                raise FormError(f"{what}: a new sentence needs a provision")
            body = line.body().rstrip()
            spans = _sentences(body)
            have = len(spans)
            if sentence != -1 and not 1 <= sentence <= have + 1:
                raise FormError(f"{what}: the provision has {have} sentence(s); a new one can be number 1 to {have + 1}, the address names {sentence}")
            text = op["new"].strip() if "new" in op else " ".join(l.strip() for l in op["lines"]).strip()
            if not text:
                raise FormError(f"{what}: the quoted text is empty")
            if sentence == -1 or sentence == have + 1:
                _set_body(line, (body + " " + text).strip())
            else:
                # „създава се ново изречение второ“ where a second exists: the new one takes its place, the rest follow it
                at = spans[sentence - 1][0]
                _set_body(line, (body[:at].rstrip() + " " + text + " " + body[at:].lstrip()).strip())
            _marker(line, "Доп.", issue)
            log.append(f"{what}: sentence {have + 1 if sentence in (-1, have + 1) else sentence} added")
            continue
        if kind == "renumber" and sentence is not None:
            log.append(f"{what}: sentences carry no number; nothing to change")
            continue
        if kind == "replace_sentence" and sentence is None:
            raise FormError(f"{what}: replace_sentence needs a sentence in the address (изречение първо, второ, … последно)")
        if kind in ("insert_provision", "insert_heading", "insert_annex"):
            new_lines = _lines_from(op["lines"], "annex_row" if kind == "insert_annex" else None, op.get("hints"))
            if not new_lines:
                raise FormError(f"{what}: the quoted text is empty")
            try:
                parts = [p for p in T.parse_address(op["address"]) if p[0] != "sentence"]
            except T.AddressError as exc:
                raise FormError(f"{what}: {exc}") from None
            want_kind, want_n = parts[-1]
            if kind == "insert_provision" and (new_lines[0].kind != want_kind or not T._same_n(new_lines[0].n, want_n)):
                raise FormError(f"{what}: the new text opens as {new_lines[0].kind} {new_lines[0].n!r}, the address names {want_kind} {want_n!r}")
            if kind == "insert_heading" and new_lines[0].kind not in T.HEADING_PREFIX:
                raise FormError(f"{what}: the new text does not open with a heading")
            if kind == "insert_annex" and new_lines[0].kind != "annex_heading":
                raise FormError(f"{what}: the new text does not open with an annex heading")
            rep = _repealed_at(tree, op["address"]) if kind == "insert_provision" else None
            if rep is not None:
                # „създава се нова ал. 2“ where ал. 2 stands repealed: the repealed head is rewritten, its history kept
                # („(2) (Отм. - ДВ, бр. 66 от 2008 г., нова - ДВ, бр. 21 от 2014 г.) …“, lex.bg's form)
                old_marker = tree.lines[rep].marker()
                new_lines[0].inline = tree.lines[rep].inline
                tree.lines[rep:rep + 1] = new_lines
                tree = _reparse(tree)
                idx = _span_after_reparse(tree, op["address"], rep, rep + len(new_lines) - 1, what)
                if old_marker:
                    head_end = len(tree.lines[idx].head())
                    tree.lines[idx].text = (tree.lines[idx].text[:head_end].rstrip() + f" ({old_marker}) " + tree.lines[idx].text[head_end:]).rstrip()
                _marker(tree.lines[idx], "Нов" if tree.lines[idx].kind in ("article", "sign") else "Нова", issue)
                log.append(f"{what}: {len(new_lines)} line(s) at the repealed {op['address']}")
                continue
            if kind == "insert_provision" and _taken(tree, op["address"]):
                # „създава се нова т. 3“ followed by „досегашните т. 3 и 4 стават т. 4 и 5“: the Gazette writes the insertion first and
                # the move of the provisions that carried the number after it; the engine moves them first, highest number first
                movers = [j for j in range(i + 1, len(ops)) if j not in done and ops[j]["kind"] == "renumber" and _siblings(ops[j]["address"], op["address"])]
                if not movers:
                    raise FormError(f"{what}: the address {op['address']!r} is already carried by a provision, and no renumber of the material moves it")
                movers.sort(key=lambda j: _resolve(tree, ops[j]["address"], f"{ops[j]['id']} renumber"), reverse=True)
                pairs = []
                for j in movers:
                    tree = _renumber(tree, ops[j], issue, log, before=op["id"])
                    done.add(j)
                    pairs.append((ops[j]["id"], ops[j]["address"], _renumbered_address(ops[j]["address"], ops[j]["to"])))
                _follow_moves(tree, ops, pairs, i + 1, done)
            if kind == "insert_annex" and not op["after"]:
                first = len(tree.lines)
                tree.lines.extend(new_lines)
                last = len(tree.lines) - 1
            else:
                if not op["after"]:
                    raise FormError(f"{what}: needs after")
                anchor = _resolve_sibling(tree, op["after"], op["address"], what)
                first, last = _insert_after(tree, anchor, new_lines)
            tree = _reparse(tree)
            idx = _span_after_reparse(tree, op["address"], first, last, what)
            _marker(tree.lines[idx], "Нов" if tree.lines[idx].kind in ("article", "sign") else ("Ново" if tree.lines[idx].kind == "annex_heading" else MARKERS[kind]), issue)
            log.append(f"{what}: {len(new_lines)} line(s) at {op['address']}")
            continue
        idx = _resolve(tree, op["address"], what)
        line = tree.lines[idx] if idx != T.ACT else None
        lead = T.lead_of(op["address"])
        if line is not None and kind == "insert_words" and not line.body().strip() and any(
                tree.lines[c].inline for c in line.children):
            raise FormError(f"{what}: the words of {op['address']!r} are in its alineas; the address names the alinea")
        if kind in ("replace_words", "delete_words") and T.title_part(op["address"]):
            if line is None:
                raise FormError(f"{what}: a title needs a provision")
            _title_words(tree, idx, op, what, issue, log)
        elif kind in ("replace_words", "corrigendum"):
            # „абревиатурата „МЗХ“ се заменя с „МЗХГ““: an abbreviation or a designation is replaced wherever it stands at the address
            everywhere = bool(op.get("everywhere")) or bool(re.search(r"абревиатурата|съкращението|означението", _instruction_text(mat, op["id"]), re.I))
            n, changed = _replace_in(tree, idx, op["old"], op["new"], everywhere, what, sentence, lead)
            for k in ([idx] if line is not None else changed):
                _marker(tree.lines[_marked(tree, k)], MARKERS[kind], issue)
            log.append(f"{what}: {n} replacement(s)")
        elif kind == "delete_words" and "old" in op and line is not None and line.kind == "alinea" and line.n and re.fullmatch(r"\(\s*" + re.escape(line.n) + r"\s*\)", op["old"].strip()):
            parent = tree.lines[line.parent] if line.parent is not None else None
            if parent is None or parent.kind not in ("article", "sign") or any(tree.lines[c].kind == "alinea" and c != idx for c in parent.children):
                raise FormError(f"{what}: the designation {op['old']!r} can go only from an article's single alinea")
            words = line.body()
            parent.text = f"{parent.head().rstrip()} {words}".rstrip()
            del tree.lines[idx]
            tree = _reparse(tree)
            art_addr = op["address"].rsplit(",", 1)[0].strip()
            art = _resolve(tree, art_addr, what)
            _marker(tree.lines[art], "Изм.", issue)
            for k in range(i + 1, len(ops)):   # the material's later operations named the items under the alinea that is no more
                if k not in done and ops[k].get("address", "").startswith(op["address"] + ","):
                    ops[k]["address"] = art_addr + ops[k]["address"][len(op["address"]):]
            log.append(f"{what}: the alinea's designation removed; its words are the article's")
        elif kind == "delete_words" and "anchor" in op:
            if line is None:
                raise FormError(f"{what}: deleting to the end needs a provision")
            body = line.body()
            a, b = _scope_text(body, sentence, what)
            part = body[a:b]
            pos = _finder(op["anchor"])(part)
            if len(pos) != 1:
                raise FormError(f"{what}: the anchor {op['anchor']!r} occurs {len(pos)} times")
            at, end = pos[0]
            close = part.rstrip()[-1] if part.rstrip() and part.rstrip()[-1] in ".;" else "."
            nb = part[:end].rstrip() + close if op["where"] == "after" else part[at:]
            _set_body(line, body[:a] + nb + body[b:])
            _marker(line, MARKERS[kind], issue)
            log.append(f"{what}: the words {'after' if op['where'] == 'after' else 'before'} the anchor deleted")
        elif kind == "delete_words" and op.get("punctuation") == "brackets":
            # „скобите на абревиатурата „СМР“ се заличават“: the parentheses around the words go, the words stay
            if line is None:
                raise FormError(f"{what}: the brackets need a provision")
            body = line.body()
            a, b = _scope_text(body, sentence, what)
            part = body[a:b]
            hits = [m for m in re.finditer(r"\(\s*" + _loose(op["old"]) + r"\s*\)", part)]
            if len(hits) != 1:
                raise FormError(f"{what}: {op['old']!r} in parentheses occurs {len(hits)} times at the address")
            m = hits[0]
            _set_body(line, body[:a] + part[:m.start()] + part[m.start() + 1:m.end() - 1].strip() + part[m.end():] + body[b:])
            _marker(line, MARKERS[kind], issue)
            log.append(f"{what}: the parentheses around {op['old']!r} removed")
        elif kind == "delete_words":
            old = _with_punctuation(tree, idx, op["old"], op["punctuation"], what, sentence, lead) if op.get("punctuation") else op["old"]
            n, changed = _replace_in(tree, idx, old, "", idx == T.ACT or bool(op.get("everywhere")), what, sentence, lead)
            for k in ([idx] if line is not None else changed):
                _marker(tree.lines[_marked(tree, k)], MARKERS[kind], issue)
            log.append(f"{what}: {n} deletion(s)")
        elif kind == "replace_sentence":
            if line is None:
                raise FormError(f"{what}: needs a provision")
            body = line.body()
            a, b = _scope_text(body, sentence, what)
            new_text = " ".join(op["lines"]) if "lines" in op else op["new"]
            new_text = new_text.strip()
            tail = " " if body[b:] and not body[b:].startswith(" ") else ""
            _set_body(line, body[:a] + new_text + tail + body[b:])
            _marker(line, "Изм.", issue)
            log.append(f"{what}: sentence {sentence} replaced")
        elif kind == "insert_words":
            if line is None:
                raise FormError(f"{what}: insert_words needs a provision")
            body = line.body()
            a, b = _scope_text(body, sentence, what)
            part = body[a:b]
            if op["where"] == "end":
                core = part.rstrip()
                close = core[-1] if core and core[-1] in ".;" else ""
                core = core[: -1] if close else core
                new = op["new"].strip()
                if close == "." and new[:1].isupper() and len(new) > 1 and not new[1:2].isupper():
                    # a whole sentence added at the end: the provision's full stop stays before it, the sentence brings its own
                    nb = core + ". " + (new if new.endswith((".", ";", "!", "?", "”", "“")) else new + ".")
                elif op.get("punctuation") == "before":
                    nb = core + ", " + new + close   # „накрая се поставя запетая и се добавя „…““
                else:
                    nb = core + ("" if not core or new.startswith((",", ";", ".")) else " ") + new + close
            elif op["where"] == "start":
                nb = op["new"] + " " + part
            else:
                pos = _finder(op["anchor"])(part)
                if len(pos) != 1:
                    raise FormError(f"{what}: the anchor {op['anchor']!r} occurs {len(pos)} times")
                at, end = pos[0]
                # an anchor that opened a quotation the instruction did not close („наричан по-нататък „Регламент…“) takes the
                # closing mark with it: the words go after the name, not inside its marks
                if len(re.findall(r"[„“”\"«»]", part[at:end])) % 2 == 1 and end < len(part) and part[end] in "“”\"»":
                    end += 1
                new = op["new"]
                if op.get("punctuation") == "before":
                    new = ", " + new
                elif op.get("punctuation") == "after":
                    new = new + ","
                if op["where"] == "after":
                    nb = part[:end] + ("" if new.startswith(",") else " ") + new + part[end:]
                else:
                    nb = part[:at] + new + " " + part[at:]
            _set_body(line, body[:a] + nb + body[b:])
            _marker(line, MARKERS[kind], issue)
            log.append(f"{what}: inserted")
        elif kind == "replace_provision" and lead:
            # „текстът преди т. 1 се изменя така“: the provision's own words change, its items stay
            if line is None:
                raise FormError(f"{what}: the words before the items need a provision")
            if "lines" in op:
                new_lines = _lines_from(op["lines"], None)
                if len(new_lines) != 1:
                    raise FormError(f"{what}: the words before the items are one line, the quoted text has {len(new_lines)}")
                words = new_lines[0].body() if new_lines[0].kind in ("article", "sign", "alinea", "item", "letter") else T.strip_line(new_lines[0].text)
            else:
                words = op["new"].strip()
            _set_body(line, words.strip())
            _marker(line, "Изм.", issue)
            log.append(f"{what}: the words before the items replaced")
        elif kind in ("replace_provision", "replace_annex"):
            if line is None:
                raise FormError(f"{what}: needs a provision")
            new_lines = _lines_from(op["lines"], "annex_row" if kind == "replace_annex" else None, op.get("hints"))
            if not new_lines:
                raise FormError(f"{what}: the quoted text is empty")
            if line.kind in ("article", "sign", "alinea", "item", "letter", "annex_heading") and new_lines[0].kind != line.kind:
                raise FormError(f"{what}: the new text opens as a {new_lines[0].kind}, the address is a {line.kind}")
            renamed = None
            if line.kind == "annex_heading" and not T._same_n(new_lines[0].n, line.n or "") and re.search(r"става приложение", _instruction_text(mat, op["id"]), re.I):
                renamed = line.n   # the Gazette moves the annex to another provision and rewrites it in one instruction
            elif line.kind in ("article", "sign", "alinea", "item", "letter", "annex_heading") and not T._same_n(new_lines[0].n, line.n or ""):
                raise FormError(f"{what}: the new text carries the number {new_lines[0].n!r}, the address {line.n!r}")
            old_marker = line.marker()
            if line.kind in T.HEADING_PREFIX:
                hm0 = _HEADING_MARKER.search(line.text)
                old_marker = hm0.group(1) if hm0 else None   # a heading's marker sits at its end
            span = T.annex_section_span(tree, idx) if line.kind == "annex_row" else tree.subtree(idx)
            first, last = min(span), max(span)
            # lex.bg marks the alineas of an article rewritten whole one by one: „Изм.“ where the number existed, „Нова“ where not
            had_alineas = {tree.lines[c].n for c in line.children if tree.lines[c].kind == "alinea"} if line.kind in ("article", "sign") else None
            if line.inline:
                new_lines[0].inline = True
            if line.kind == "annex_row":
                new_lines = _lines_from(op["lines"], "annex_row", op.get("hints"))
            tree.lines[first:last + 1] = new_lines
            tree = _reparse(tree)
            if renamed is not None:
                idx2 = first
                if old_marker and not _HEADING_MARKER.search(tree.lines[idx2].text):
                    tree.lines[idx2].text = tree.lines[idx2].text.rstrip() + f" ({old_marker})"   # the annex's history first, then the move
                _marker(tree.lines[idx2], f"Предишно приложение {renamed}", issue)
            else:
                idx2 = _span_after_reparse(tree, op["address"], first, first + len(new_lines) - 1, what)
            if tree.lines[idx2].kind == "annex_row":
                _marker(tree.lines[_marked(tree, idx2)], MARKERS[kind], issue)
                log.append(f"{what}: {last - first + 1} row(s) of the annex replaced by {len(new_lines)}")
                continue
            if old_marker and tree.lines[idx2].kind not in T.HEADING_PREFIX:
                head_end = len(tree.lines[idx2].head())
                tree.lines[idx2].text = tree.lines[idx2].text[:head_end].rstrip() + f" ({old_marker}) " + tree.lines[idx2].text[head_end:]
                tree.lines[idx2].text = tree.lines[idx2].text.rstrip()
            elif old_marker and tree.lines[idx2].kind in T.HEADING_PREFIX and not _HEADING_MARKER.search(tree.lines[idx2].text):
                tree.lines[idx2].text = tree.lines[idx2].text.rstrip() + f" ({old_marker})"   # a rewritten annex or heading keeps its history
            new_alineas = [c for c in tree.lines[idx2].children if tree.lines[c].kind == "alinea"] if had_alineas is not None else []
            if new_alineas and had_alineas:
                for c in new_alineas:
                    _marker(tree.lines[c], "Изм." if tree.lines[c].n in had_alineas else "Нова", issue)
            else:
                _marker(tree.lines[idx2], MARKERS[kind], issue)
            log.append(f"{what}: {last - first + 1} line(s) replaced by {len(new_lines)}")
        elif kind == "repeal" and sentence is not None:
            # „изречение второ се заличава“: the sentence goes, the provision stays with an amendment marker
            if line is None:
                raise FormError(f"{what}: needs a provision")
            body = line.body()
            a, b = _scope_text(body, sentence, what)
            head, tail = body[:a].rstrip(), body[b:].lstrip()
            _set_body(line, (head + (" " if head and tail else "") + tail).strip())
            _marker(line, "Изм.", issue)
            log.append(f"{what}: sentence {sentence} deleted")
        elif kind in ("repeal", "repeal_annex"):
            if line is None:
                raise FormError(f"{what}: needs a provision")
            span = tree.subtree(idx)
            first, last = min(span), max(span)
            if line.kind in T.HEADING_PREFIX:
                # a heading keeps its words, and every article, § and sub-heading under it stays as a repealed head with its own
                # marker (lex.bg's form); only their text and the alineas, items and rows go
                kept: list[T.Line] = []
                for k in span:
                    l = tree.lines[k]
                    if l.kind in T.HEADING_PREFIX:
                        kept.append(T.Line(l.kind, l.text, l.n))
                    elif l.kind in ("article", "sign"):
                        kept.append(T.Line(l.kind, l.head().rstrip(), l.n, title=l.title))
                for l in kept:
                    if l.kind != "annex_heading" or True:
                        _marker(l, MARKERS["repeal"], issue)
                tree.lines[first:last + 1] = kept
            else:
                keep = T.Line(line.kind, line.head().rstrip(), line.n, title=line.title, inline=line.inline)
                _marker(keep, MARKERS[kind], issue)
                tree.lines[first:last + 1] = [keep]
            tree = _reparse(tree)
            _span_after_reparse(tree, op["address"], first, first, what)
            log.append(f"{what}: {last - first + 1} line(s) repealed")
        elif kind == "renumber":
            # „досегашната ал. 6 става ал. 7“ followed by „досегашната ал. 7 става ал. 8“: the holder of the target number moves first
            target = _renumbered_address(op["address"], op["to"])
            rep = _repealed_at(tree, target)
            if rep is not None:
                # the target number is held by a repealed head („(6) (Отм. - …)“): the moved provision takes its place
                del tree.lines[rep]
                tree = _reparse(tree)
                log.append(f"{what}: the repealed {target} gave way")
            guard = 0
            while _taken(tree, target) and guard < 20:
                movers = [j for j in range(i + 1, len(ops)) if j not in done and ops[j]["kind"] == "renumber" and ops[j]["address"] == target]
                if not movers:
                    break
                j = movers[0]
                done.add(j)
                tree = _renumber_taken(tree, ops, j, done, issue, log, op["id"])
                guard += 1
            tree = _renumber(tree, op, issue, log)
        elif kind == "replace_heading":
            if line is None:
                raise FormError(f"{what}: needs a heading")
            if "lines" in op:
                new_lines = _lines_from(op["lines"], None)
                if len(new_lines) != 1:
                    raise FormError(f"{what}: a heading is one line, the quoted text has {len(new_lines)}")
                words = T.strip_line(new_lines[0].text)
            else:
                words = op["new"]
            if line.kind == "title":
                line.text = T.render_heading("title", words)
            elif line.kind == "article" and line.title:
                # „Наименованието на чл. 30 „…“ се заменя с „…““: the article's own title, printed before its head
                rest = line.text[len(line.title):].lstrip()
                line.text = f"{words} {rest}"
                line.title = words
                _marker(line, "Загл. изм.", issue)
                log.append(f"{what}: the title replaced")
                continue
            elif line.kind == "article" and idx > 0 and tree.lines[idx - 1].kind in ("section_heading", "subsection_heading") \
                    and tree.lines[idx - 1].children == [] or (line.kind == "article" and idx > 0 and tree.lines[idx - 1].kind == "subsection_heading"):
                # the article's title read as a heading line of its own (the Gazette prints it above the head): its words change
                hl = tree.lines[idx - 1]
                hm = _HEADING_MARKER.search(hl.text)
                prefix = hl.text[: len(hl.text) - len(hl.text.lstrip("#"))]
                hl.text = f"{prefix} {words}".rstrip() if prefix else words
                if hm:
                    hl.text = hl.text + " (" + hm.group(1) + ")"
                _marker(hl, "Загл. изм.", issue)
                log.append(f"{what}: the heading line before the article replaced")
                continue
            elif line.kind in T.HEADING_PREFIX:
                # the number part („Глава двадесет и първа“, „Раздел V“, „Приложение № 3 към чл. 6“) stays; the title words change;
                # the heading's marker history stays and the new marker joins it
                hm = _HEADING_MARKER.search(line.text)
                old_marker = hm.group(1) if hm else None
                current = T.strip_line(line.text[: hm.start()] if hm else line.text).strip()
                if line.kind == "annex_heading":
                    number = current if not words.lower().startswith("приложение") else ""
                else:
                    m = T._HEADING_WORD.match(current)
                    number = m.group(0).rstrip(".") if m else ""
                if words.lower().startswith(number.lower()) and number:
                    text = words
                else:
                    text = (number + " " + words).strip()
                line.text = T.render_heading(line.kind, text) + (f" ({old_marker})" if old_marker else "")
                _marker(line, "Загл. изм.", issue)
            else:
                raise FormError(f"{what}: {op['address']!r} is not a heading")
            log.append(f"{what}: heading replaced")
        tree = _reparse(tree)
    m_id = re.search(r"\d+$", str(answer.get("material", "") or ""))
    return Applied(material=int(m_id.group(0)) if m_id else 0, issue=issue, operations=ops, markdown=tree.to_markdown(), log=log)


def _word(kind: str) -> str:
    return {"alinea": "ал.", "item": "т.", "letter": "б.", "article": "чл.", "sign": "§"}.get(kind, "")


def task_text(mat: Material, blocks: list[Block], tree: T.Tree, slug: str, issue: str, answer_path, findings: list[dict]) -> str:
    """The applier's task: the instructions with their quoted blocks and numbered segments, the current text of the provisions
    the addresses name (where the script can read an address), the closed set and the answer form."""
    lines = [f"# Apply the amending material of ДВ бр. {issue} to {slug}", "",
             "You read the instructions of an amending act and turn each into operations on the act's text, in the form below. "
             "You never retype the act's words: a new text is a reference to the quoted blocks (their indices), an old or new string "
             "is a reference to a quoted segment of the instruction (q1, q2, … in order of appearance), an address is written as the "
             "Gazette writes it („чл. 36, ал. 1, т. 5“, „§ 3“, „глава втора, раздел V“, „Приложение № 3“, „наименованието“). "
             "An instruction that changes no text of this act (entry into force, a transitional rule, an instruction aimed at another act) "
             "is `no_text_change`. An instruction that changes this act's text in a way you cannot express in the closed set is `outside_set` "
             "with a note that says what it does: the script stops the act for the owner.", "",
             "Kinds: " + "; ".join(f"`{k}`: {v}" for k, v in KINDS.items()) + ".", "",
             f"Write exactly one JSON object to `{answer_path}`: {{\"material\": <id>, \"operations\": [...]}}, one or more operations per "
             "instruction id, in the material's order; nothing else, no prose, no code fence. Each operation is an object with these keys and no "
             "others: `id` (the instruction id as written above, e.g. \"§3.1\"), `kind` (one of the kinds), `address` (the provision, in the Gazette's "
             "grammar; not for no_text_change), and by kind: `blocks` ([first, last] block indices of the quoted text, for replace_provision, "
             "insert_provision, insert_heading, replace_annex, insert_annex, or replace_heading with quoted blocks), `after` (the sibling the new text follows, for the "
             "insert kinds), `old` and `new` (segment references like \"q1\", for replace_words, delete_words, corrigendum, insert_words, replace_heading), "
             "`anchor` and `where` (after | before | end | start, for insert_words), `to` (the new number, for renumber), `everywhere` (true when the "
             "instruction says навсякъде, for replace_words), `note` (free text, required for outside_set). Where the Gazette's nested quotation marks "
             "cut a segment short (q1 ends before the inner quote), give `old`, `new` or `anchor` as {\"text\": \"…\"} with the words copied exactly from the "
             "instruction line above, quotation marks included; the script checks they stand there. Example: "
             "{\"id\": \"§1.1\", \"kind\": \"replace_words\", \"address\": \"чл. 36, ал. 1\", \"old\": \"q1\", \"new\": \"q2\"}.", ""]
    if findings:
        lines.append("The parser recorded these findings on the material (where its quoted extents may be wrong, give the block range yourself):")
        lines.extend(f"- block {f['block']}: {f['kind']}: {f['detail']}" for f in findings)
        lines.append("")
    lines.append("## The instructions")
    for n in mat.instructions():
        lines.append(f"### {n.id} (block {n.block}, section {n.section})")
        lines.append(n.text)
        for j, q in enumerate(n.inline_quotes, 1):
            lines.append(f"- q{j}: „{q}“")
        for k in n.quoted:
            lines.append(f"- quoted block {k}: {blocks[k].text}")
        for k in n.continuation:
            lines.append(f"- continuation block {k}: {blocks[k].text}")
        from .material import _head_stripped
        addr = _addresses_in(_head_stripped(n.text))   # the instruction's own § head is not an address of the act
        for a in addr:
            try:
                idx = T.resolve(tree, a)
                lines.append(f"- current text at „{a}“:")
                for k in tree.subtree(idx)[:40]:
                    lines.append(f"    {tree.lines[k].text}")
            except T.AddressError as exc:
                lines.append(f"- „{a}“: {exc}")
        lines.append("")
    return "\n".join(lines)


_ADDR_IN_TEXT = re.compile(r"(?<![\w.])((?:чл\.|член)\s*\d+[а-я]?(?:\d{1,2})?(?:,\s*ал\.\s*\d+[а-я]?)?(?:,\s*т\.\s*\d+[а-я]?)?(?:,\s*б\.\s*[„\"][а-я]{1,2}[“\"])?|§\s*\d+[а-я]?|приложение\s*№\s*\S+)", re.I)


def _addresses_in(text: str) -> list[str]:
    """The addresses an instruction names, for the current text the task shows; the model gives the operation's own address."""
    out: list[str] = []
    for m in _ADDR_IN_TEXT.finditer(text):
        a = re.sub(r"^член\s*", "чл. ", m.group(1).strip(), flags=re.I)
        if a not in out:
            out.append(a)
    return out[:4]
