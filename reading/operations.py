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
from .splitter import Block

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
MARKERS = {"replace_provision": "Изм.", "replace_words": "Изм.", "delete_words": "Изм.", "insert_words": "Доп.", "insert_provision": "Нова",
           "repeal": "Отм.", "renumber": "Предишна", "replace_heading": "Изм.", "insert_heading": "Нова", "replace_annex": "Изм.",
           "insert_annex": "Ново", "repeal_annex": "Отм.", "corrigendum": "Попр."}
QUOTE_OPEN = "„“\"«"
QUOTE_CLOSE = "“”\"»"
_Q = re.compile(r"^q(\d+)$")


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


def _quoted_text(blocks: list[Block], first: int, last: int) -> list[str]:
    """The lines of a quoted run without the quotation marks that enclose it (and the amending act's punctuation after the closer)."""
    if first > last or first < 0 or last >= len(blocks):
        raise FormError(f"blocks [{first}, {last}] are not a range of the material")
    lines = [blocks[k].text for k in range(first, last + 1)]
    if not lines[0][:1] in QUOTE_OPEN:
        raise FormError(f"block {first} does not open with a quotation mark: {lines[0][:40]!r}")
    lines[0] = lines[0][1:]
    tail = lines[-1].rstrip()
    stripped = tail.rstrip(".;,:)")
    if stripped and stripped[-1] in QUOTE_CLOSE:
        lines[-1] = stripped[:-1].rstrip()
    elif tail in QUOTE_CLOSE:
        lines = lines[:-1]
    else:
        raise FormError(f"block {last} does not close the quotation: {tail[-40:]!r}")
    return [l for l in lines if l.strip()]


def _segment(node: Node, ref: str, nodes: dict[str, Node] | None = None) -> str:
    """A quoted segment of the instruction (q1, q2, …), or of its parent when the instruction has none („§ 5. … думите „X“ се заменят с „Y“: 1. в чл. 2 …“)."""
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
        if op.get("kind") not in KINDS:
            raise FormError(f"operation {k}: kind {op.get('kind')!r} is not one of {sorted(KINDS)}")
        node = nodes.get(str(op.get("id")))
        if node is None:
            raise FormError(f"operation {k}: id {op.get('id')!r} is not an instruction of the material")
        seen_ids.add(node.id)
        kind = op["kind"]
        extra = set(op) - {"id", "kind", "address", "after", "blocks", "old", "new", "anchor", "where", "to", "everywhere", "note"}
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
        if kind in ("replace_provision", "insert_provision", "insert_heading", "replace_annex", "insert_annex") or (kind == "replace_heading" and "blocks" in op):
            b = op.get("blocks")
            if not (isinstance(b, list) and len(b) == 2 and all(isinstance(x, int) for x in b)):
                raise FormError(f"{node.id}: {kind} needs blocks [first, last]")
            allowed = set(node.quoted) | set(node.continuation)
            if allowed and not set(range(b[0], b[1] + 1)) <= allowed:
                raise FormError(f"{node.id}: blocks [{b[0]}, {b[1]}] lie outside the instruction's quoted text {sorted(allowed)}")
            if not allowed:
                res["blocks_outside_parse"] = True   # the parser found no quoted text here: the model's range is recorded as such
            res["lines"] = _quoted_text(blocks, b[0], b[1])
            res["blocks"] = [b[0], b[1]]
        if kind in ("insert_provision", "insert_heading", "insert_annex"):
            res["after"] = str(op.get("after", "")).strip()
        if kind in ("replace_words", "delete_words", "corrigendum"):
            res["old"] = _segment(node, op.get("old"), nodes); res["old_ref"] = op.get("old")
        if kind in ("replace_words", "insert_words", "corrigendum") or (kind == "replace_heading" and "blocks" not in op):
            res["new"] = _segment(node, op.get("new"), nodes); res["new_ref"] = op.get("new")
        if kind == "insert_words":
            where = op.get("where", "after")
            if where not in ("after", "before", "end", "start"):
                raise FormError(f"{node.id}: where {where!r} is not after, before, end or start")
            res["where"] = where
            if where in ("after", "before"):
                res["anchor"] = _segment(node, op.get("anchor"), nodes); res["anchor_ref"] = op.get("anchor")
        if kind == "replace_words":
            res["everywhere"] = bool(op.get("everywhere", False))
        if kind == "renumber":
            if not isinstance(op.get("to"), str) or not op["to"].strip():
                raise FormError(f"{node.id}: renumber needs to")
            res["to"] = op["to"].strip()
        out.append(res)
    leaves = [n.id for n in mat.instructions() if not n.children]
    missing = [i for i in leaves if i not in seen_ids]
    if missing:
        raise FormError(f"no operation for the instruction(s) {', '.join(missing)}; every instruction gets at least one (no_text_change when it changes nothing)")
    return out


_MARKER_ENTRY = re.compile(r"^(?P<words>[^-]+?)\s*-\s*ДВ,\s*бр\.\s*(?P<num>\d+)\s*от\s*(?P<year>\d{4})\s*г\.(?P<extra>.*)$")
_HEAD_RX = (r"^(?:[^*\n]{1,160}?\s+)?\*\*(?:Чл\.\s*\S+\.|Член\s+единствен\.|§\s*\S+\.|Параграф\s+единствен\.)\*\*\s*", r"^\(\d{1,3}[а-я]?\)\s*",
            r"^\d{1,3}(?:[а-я]{1,2})?\.\s+", r"^[а-я]{1,3}\)\s+")
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


def _scope_text(body: str, sentence: int | None, what: str) -> tuple[int, int]:
    if sentence is None:
        return 0, len(body)
    spans = _sentences(body)
    idx = len(spans) - 1 if sentence == -1 else sentence - 1
    if idx < 0 or idx >= len(spans):
        raise FormError(f"{what}: the provision has {len(spans)} sentence(s), not {sentence}")
    return spans[idx]


def _set_body(line: T.Line, body: str) -> None:
    line.text = (line.head() + body).rstrip()


def _replace_in(tree: T.Tree, idx: int, old: str, new: str, everywhere: bool, what: str, sentence: int | None = None, lead: bool = False) -> tuple[int, list[int]]:
    """Replace old by new in the words of the addressed provision and what hangs under it (its own words only with ``lead``; the whole act
    for ``ACT``); the count replaced and the lines changed."""
    scope = tree.addressable_lines() if idx == T.ACT else ([idx] if lead else tree.subtree(idx))
    if idx == T.ACT:
        everywhere = True
    hits: list[tuple[int, int, int]] = []
    for k in scope:
        body = tree.lines[k].body()
        a, b = _scope_text(body, sentence if k == idx else None, what)
        hits.append((k, a, b)) if old in body[a:b] else None
    count = sum(tree.lines[k].body()[a:b].count(old) for k, a, b in hits)
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
        replaced = part.replace(old, new) if everywhere else part.replace(old, fix, 1)
        nb = body[:a] + replaced + body[b:]
        if new == "":
            nb = re.sub(r"  +", " ", nb).replace(" ,", ",").replace(" .", ".").replace(" ;", ";").strip()
        _set_body(l, nb)
    return count, changed


def _lines_from(texts: list[str], context_kind: str | None) -> list[T.Line]:
    out = [T.line_from_text(t, context_kind) for t in texts]
    joined: list[T.Line] = []
    for l in out:
        if joined and l.kind == "text" and joined[-1].kind in ("part_heading", "chapter_heading", "section_heading", "subsection_heading") and T.NUMBER_LINE.match(T.strip_line(joined[-1].text)):
            joined[-1].text = f"{joined[-1].text} {l.text}"
        else:
            joined.append(l)
    return joined


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


def apply(answer: dict, mat: Material, blocks: list[Block], markdown: str, issue: str) -> Applied:
    """Apply a material's operations to the body; the form is checked first, and any failure applies nothing."""
    ops = check_form(answer, mat, blocks)
    tree = T.parse(markdown)
    if tree.to_markdown() != markdown:
        raise FormError("the body does not round-trip through the act tree; the apply step cannot hold it")
    log: list[str] = []
    for op in ops:
        kind = op["kind"]
        what = f"{op['id']} {kind}"
        if kind == "no_text_change":
            log.append(f"{what}: nothing")
            continue
        if kind == "outside_set":
            raise FormError(f"{what}: outside the closed set of operations: {op['note']}")
        try:
            sentence = T.sentence_of(op["address"]) if "address" in op else None
        except T.AddressError as exc:
            raise FormError(f"{what}: {exc}") from None
        if sentence is not None and kind not in ("replace_words", "delete_words", "insert_words", "corrigendum"):
            raise FormError(f"{what}: a sentence address fits only an operation on words")
        if kind in ("insert_provision", "insert_heading", "insert_annex"):
            new_lines = _lines_from(op["lines"], "annex_row" if kind == "insert_annex" else None)
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
            if kind == "insert_annex" and not op["after"]:
                first = len(tree.lines)
                tree.lines.extend(new_lines)
                last = len(tree.lines) - 1
            else:
                if not op["after"]:
                    raise FormError(f"{what}: needs after")
                anchor = _resolve(tree, op["after"], what)
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
        if kind in ("replace_words", "corrigendum"):
            n, changed = _replace_in(tree, idx, op["old"], op["new"], op.get("everywhere", False), what, sentence, lead)
            for k in ([idx] if line is not None else changed):
                _marker(tree.lines[k], MARKERS[kind], issue)
            log.append(f"{what}: {n} replacement(s)")
        elif kind == "delete_words":
            n, changed = _replace_in(tree, idx, op["old"], "", idx == T.ACT, what, sentence, lead)
            for k in ([idx] if line is not None else changed):
                _marker(tree.lines[k], MARKERS[kind], issue)
            log.append(f"{what}: {n} deletion(s)")
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
                nb = core + ("" if not core or op["new"].startswith((",", ";", ".")) else " ") + op["new"] + close
            elif op["where"] == "start":
                nb = op["new"] + " " + part
            else:
                if part.count(op["anchor"]) != 1:
                    raise FormError(f"{what}: the anchor {op['anchor']!r} occurs {part.count(op['anchor'])} times")
                at = part.index(op["anchor"])
                nb = part[:at + len(op["anchor"])] + " " + op["new"] + part[at + len(op["anchor"]):] if op["where"] == "after" else part[:at] + op["new"] + " " + part[at:]
            _set_body(line, body[:a] + nb + body[b:])
            _marker(line, MARKERS[kind], issue)
            log.append(f"{what}: inserted")
        elif kind in ("replace_provision", "replace_annex"):
            if line is None:
                raise FormError(f"{what}: needs a provision")
            new_lines = _lines_from(op["lines"], "annex_row" if kind == "replace_annex" else None)
            if not new_lines:
                raise FormError(f"{what}: the quoted text is empty")
            if line.kind in ("article", "sign", "alinea", "item", "letter", "annex_heading") and new_lines[0].kind != line.kind:
                raise FormError(f"{what}: the new text opens as a {new_lines[0].kind}, the address is a {line.kind}")
            if line.kind in ("article", "sign", "alinea", "item", "letter", "annex_heading") and not T._same_n(new_lines[0].n, line.n or ""):
                raise FormError(f"{what}: the new text carries the number {new_lines[0].n!r}, the address {line.n!r}")
            old_marker = line.marker()
            span = tree.subtree(idx)
            first, last = min(span), max(span)
            if line.inline:
                new_lines[0].inline = True
            tree.lines[first:last + 1] = new_lines
            tree = _reparse(tree)
            idx2 = _span_after_reparse(tree, op["address"], first, first + len(new_lines) - 1, what)
            if old_marker and tree.lines[idx2].kind not in T.HEADING_PREFIX:
                head_end = len(tree.lines[idx2].head())
                tree.lines[idx2].text = tree.lines[idx2].text[:head_end].rstrip() + f" ({old_marker}) " + tree.lines[idx2].text[head_end:]
                tree.lines[idx2].text = tree.lines[idx2].text.rstrip()
            _marker(tree.lines[idx2], MARKERS[kind], issue)
            log.append(f"{what}: {last - first + 1} line(s) replaced by {len(new_lines)}")
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
            if line is None:
                raise FormError(f"{what}: needs a provision")
            try:
                parts = T.parse_address(op["to"])
            except T.AddressError as exc:
                raise FormError(f"{what}: {exc}") from None
            new_n = parts[-1][1]
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
            log.append(f"{what}: {old_n} -> {new_n}")
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
    return Applied(material=int(answer.get("material", 0) or 0), issue=issue, operations=ops, markdown=tree.to_markdown(), log=log)


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
             "instruction id, in the material's order; nothing else, no prose, no code fence.", ""]
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
        addr = _addresses_in(n.text)
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
