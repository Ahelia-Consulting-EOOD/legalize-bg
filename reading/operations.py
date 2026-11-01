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


def _segment(node: Node, ref: str) -> str:
    m = _Q.match(str(ref))
    if not m or not (1 <= int(m.group(1)) <= len(node.inline_quotes)):
        raise FormError(f"{node.id}: {ref!r} is not a quoted segment of the instruction (it has {len(node.inline_quotes)})")
    return node.inline_quotes[int(m.group(1)) - 1]


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
            if not allowed and kind != "no_text_change":
                allowed = set(range(len(blocks)))   # the model may point outside the parser's extents when the grammar lost the run (a finding is on record)
            res["lines"] = _quoted_text(blocks, b[0], b[1])
            res["blocks"] = [b[0], b[1]]
        if kind in ("insert_provision", "insert_heading", "insert_annex"):
            res["after"] = str(op.get("after", "")).strip()
        if kind in ("replace_words", "delete_words", "corrigendum"):
            res["old"] = _segment(node, op.get("old")); res["old_ref"] = op.get("old")
        if kind in ("replace_words", "insert_words", "corrigendum") or (kind == "replace_heading" and "blocks" not in op):
            res["new"] = _segment(node, op.get("new")); res["new_ref"] = op.get("new")
        if kind == "insert_words":
            where = op.get("where", "after")
            if where not in ("after", "before", "end", "start"):
                raise FormError(f"{node.id}: where {where!r} is not after, before, end or start")
            res["where"] = where
            if where in ("after", "before"):
                res["anchor"] = _segment(node, op.get("anchor")); res["anchor_ref"] = op.get("anchor")
        if kind == "replace_words":
            res["everywhere"] = bool(op.get("everywhere", False))
        if kind == "renumber":
            if not isinstance(op.get("to"), str) or not op["to"].strip():
                raise FormError(f"{node.id}: renumber needs to")
            res["to"] = op["to"].strip()
        out.append(res)
    return out


def _marker(line: T.Line, word: str, issue: str, extra: str = "") -> None:
    """Add „(Изм. - ДВ, бр. N от YYYY г.)“ after the head, or extend an existing marker with „, изм. - ДВ, …“ (lex.bg's form)."""
    num, year = issue.split("/")
    text = line.text
    head_end = 0
    for rx in (r"^(?:[^*\n]{1,160}?\s+)?\*\*(?:Чл\.\s*\S+\.|Член\s+единствен\.|§\s*\S+\.|Параграф\s+единствен\.)\*\*\s*", r"^\(\d{1,3}[а-я]?\)\s*",
               r"^\d{1,3}(?:[а-я]{1,2})?\.\s+", r"^[а-я]{1,3}\)\s+", r"^#{1,5}\s+"):
        m = re.match(rx, text)
        if m:
            head_end = m.end()
            break
    rest = text[head_end:]
    low = word[0].lower() + word[1:] if line.kind in ("item", "letter") else word
    m = T._MARKER.match(rest)
    piece = f"{low} - ДВ, бр. {num} от {year} г." + (f", {extra}" if extra else "")
    sep = "" if head_end == 0 or text[head_end - 1].isspace() else " "
    if m:
        inner = m.group(0).rstrip()
        inner = inner[1:-1] if inner.endswith(")") else inner[1:]
        new = f"({inner}, {piece[0].lower() + piece[1:]}) "
        line.text = text[:head_end] + sep + new + rest[m.end():]
    else:
        line.text = text[:head_end] + sep + f"({piece}) " + rest
    line.text = line.text.rstrip()


def _replace_in(tree: T.Tree, idx: int, old: str, new: str, everywhere: bool, what: str) -> int:
    """Replace old by new in the words of the addressed provision and what hangs under it; the count replaced."""
    scope = tree.subtree(idx)
    count = sum(tree.lines[k].body().count(old) for k in scope)
    if count == 0:
        raise FormError(f"{what}: the words {old!r} do not occur in {tree.lines[idx].text[:50]!r}")
    if count > 1 and not everywhere:
        raise FormError(f"{what}: the words {old!r} occur {count} times at the address; the instruction does not say навсякъде")
    for k in scope:
        l = tree.lines[k]
        body = l.body()
        if old in body:
            head_len = len(l.text) - len(body) if l.text.endswith(body) else None
            if head_len is None:
                raise FormError(f"{what}: the provision's words could not be separated from its head: {l.text[:50]!r}")
            # a quoted segment that ends with an abbreviation's dot („до 30 000 лв.“) closed the sentence too; the sentence keeps its full stop
            fix = new + "." if old.endswith(".") and not new.endswith(".") and body.rstrip().endswith(old) else new
            l.text = l.text[:head_len] + (body.replace(old, new) if everywhere else body.replace(old, fix, 1))
    return count


def _lines_from(texts: list[str], context_kind: str | None) -> list[T.Line]:
    out: list[T.Line] = []
    for t in texts:
        out.append(T.line_from_text(t, context_kind))
    # a heading number line and its title on two lines are one heading line, as the assembler joins them
    joined: list[T.Line] = []
    for l in out:
        if joined and l.kind == "text" and joined[-1].kind in ("part_heading", "chapter_heading", "section_heading", "subsection_heading") and T.NUMBER_LINE.match(T.strip_line(joined[-1].text)):
            joined[-1].text = f"{joined[-1].text} {l.text}"
        else:
            joined.append(l)
    return joined


def _insert_after(tree: T.Tree, after_idx: int, new_lines: list[T.Line]) -> None:
    end = max(tree.subtree(after_idx)) + 1
    tree.lines[end:end] = new_lines


def apply(answer: dict, mat: Material, blocks: list[Block], markdown: str, issue: str) -> Applied:
    """Apply a material's operations to the body; the form is checked first, and any failure applies nothing."""
    ops = check_form(answer, mat, blocks)
    tree = T.parse(markdown)
    log: list[str] = []
    for op in ops:
        kind = op["kind"]
        what = f"{op['id']} {kind}"
        if kind == "no_text_change":
            log.append(f"{what}: nothing")
            continue
        if kind == "outside_set":
            raise FormError(f"{what}: outside the closed set of operations: {op['note']}")
        if kind in ("insert_provision", "insert_heading", "insert_annex"):
            new_lines = _lines_from(op["lines"], "annex_row" if kind == "insert_annex" else None)
            if kind == "insert_annex" and not op["after"]:
                tree.lines.extend(new_lines)
            else:
                anchor = _resolve(tree, op["after"], what) if op["after"] else None
                if anchor is None:
                    raise FormError(f"{what}: needs after")
                _insert_after(tree, anchor, new_lines)
            tree = T.parse(tree.to_markdown())
            idx = _resolve(tree, op["address"], what)
            _marker(tree.lines[idx], MARKERS[kind] if tree.lines[idx].kind not in ("article", "sign") else "Нов", issue)
            log.append(f"{what}: {len(new_lines)} line(s) at {op['address']}")
            continue
        idx = _resolve(tree, op["address"], what)
        line = tree.lines[idx]
        if kind in ("replace_words", "corrigendum"):
            n = _replace_in(tree, idx, op["old"], op["new"], op.get("everywhere", False), what)
            _marker(line, MARKERS[kind], issue)
            log.append(f"{what}: {n} replacement(s)")
        elif kind == "delete_words":
            n = _replace_in(tree, idx, op["old"], "", False, what)
            tree.lines[idx].text = re.sub(r"  +", " ", tree.lines[idx].text).replace(" ,", ",").replace(" .", ".")
            _marker(line, MARKERS[kind], issue)
            log.append(f"{what}: deleted")
        elif kind == "insert_words":
            body = line.body()
            head = line.text[: len(line.text) - len(body)] if line.text.endswith(body) else None
            if head is None:
                raise FormError(f"{what}: the provision's words could not be separated from its head")
            if op["where"] == "end":
                nb = body.rstrip().rstrip(".;") + (" " if not op["new"].startswith((",", ";", ".")) else "") + op["new"] + (body.rstrip()[-1] if body.rstrip()[-1:] in ".;" else "")
            elif op["where"] == "start":
                nb = op["new"] + " " + body
            else:
                if body.count(op["anchor"]) != 1:
                    raise FormError(f"{what}: the anchor {op['anchor']!r} occurs {body.count(op['anchor'])} times")
                a = body.index(op["anchor"])
                nb = body[:a + len(op["anchor"])] + " " + op["new"] + body[a + len(op["anchor"]):] if op["where"] == "after" else body[:a] + op["new"] + " " + body[a:]
            line.text = head + nb
            _marker(line, MARKERS[kind], issue)
            log.append(f"{what}: inserted")
        elif kind in ("replace_provision", "replace_annex"):
            new_lines = _lines_from(op["lines"], "annex_row" if kind == "replace_annex" else None)
            if not new_lines:
                raise FormError(f"{what}: the quoted text is empty")
            if line.kind in ("article", "sign", "alinea", "item", "letter") and new_lines[0].kind != line.kind:
                raise FormError(f"{what}: the new text opens as a {new_lines[0].kind}, the address is a {line.kind}")
            if line.kind in ("article", "sign", "alinea", "item", "letter") and new_lines[0].n != line.n:
                raise FormError(f"{what}: the new text carries the number {new_lines[0].n!r}, the address {line.n!r}")
            old_marker = T._MARKER.match(line.body_with_marker()) if hasattr(line, "body_with_marker") else None
            span = tree.subtree(idx)
            first, last = min(span), max(span)
            tree.lines[first:last + 1] = new_lines
            tree = T.parse(tree.to_markdown())
            idx2 = _resolve(tree, op["address"], what)
            _marker(tree.lines[idx2], MARKERS[kind], issue)
            log.append(f"{what}: {last - first + 1} line(s) replaced by {len(new_lines)}")
        elif kind in ("repeal", "repeal_annex"):
            span = tree.subtree(idx)
            first, last = min(span), max(span)
            head_body = line.body()
            head = line.text[: len(line.text) - len(head_body)] if line.text.endswith(head_body) else line.text
            keep = T.Line(line.kind, head.rstrip(), line.n, title=line.title)
            tree.lines[first:last + 1] = [keep]
            tree = T.parse(tree.to_markdown())
            idx2 = _resolve(tree, op["address"], what)
            _marker(tree.lines[idx2], MARKERS[kind], issue)
            log.append(f"{what}: {last - first + 1} line(s) repealed")
        elif kind == "renumber":
            parts = T.parse_address(op["to"])
            new_n = parts[-1][1]
            body = line.body()
            head = line.text[: len(line.text) - len(body)]
            old_n = line.n
            head2 = head.replace(old_n, new_n, 1) if old_n and old_n in head else head
            if head2 == head:
                raise FormError(f"{what}: the number {old_n!r} was not found in the head {head!r}")
            line.text = head2 + body
            line.n = new_n
            _marker(line, f"Предишна {T.parse_address(op['address'])[-1][0] and _word(line.kind)} {old_n}", issue)
            log.append(f"{what}: {old_n} -> {new_n}")
        elif kind == "replace_heading":
            if "lines" in op:
                new_lines = _lines_from(op["lines"], None)
                if len(new_lines) != 1:
                    raise FormError(f"{what}: a heading is one line, the quoted text has {len(new_lines)}")
                line.text = new_lines[0].text if new_lines[0].kind != "text" else T.render_heading(line.kind, new_lines[0].text) if line.kind in T.HEADING_PREFIX else new_lines[0].text
            else:
                line.text = T.render_heading(line.kind, op["new"]) if line.kind in T.HEADING_PREFIX else op["new"]
            if line.kind != "title":
                _marker(line, "Загл. изм.", issue)
            log.append(f"{what}: heading replaced")
        tree = T.parse(tree.to_markdown())
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
