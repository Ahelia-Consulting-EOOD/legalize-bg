"""The rulings of decision D-072 that change the map before the checks run.

A rule reads the labeller's map and the page's structure and never the meaning of
a line; what a line is, the labeller has already said. Every change a rule makes
is recorded in the act's omissions list, so the body differs from the page only
where the list says so.

Ruling 1, ``superseded_heading``: lex.bg prints an old heading again beside the
current one. In a stretch of headings with no body between them (no article,
§, alinea, item, letter or other provision line, by the labeller's labels), a
heading number line ("Раздел IV.", "Глава тринадесета.") or a provisions heading
that occurs twice is one current heading and one superseded copy. A copy's title
is the line after its number line, unless that line is a number line, a note in
parentheses, or the labeller's ``article_title``. A copy without a title is the
superseded one; of two titled copies the one whose title says „Загл. изм.“ is
current, otherwise the first. The superseded copy, number line and title, is
dropped.

Ruling 5: a run of ``continuation`` lines numbered 1., 2., … right after an item
whose text ends with a colon is that item's numbered list, labelled ``item``.

Ruling 6, ``duplicate_number``: an alinea or item number the page itself prints
twice in a row keeps its label on both lines; the second line's number gets the
suffix ``-2`` and the pair is recorded.

Ruling 8: the „(ОБН. - ДВ, БР. …)“ line, lex.bg's dotted elision line and the
dashed separator before the adoption formula are editorial notes, kept.

Ruling 13, ``remnant_repaired``: lex.bg's superscript markup leaks into an
article head as "Чл. 278б.SUP>1."; when the map's number agrees (278б1), the
head is rewritten with the superscript digit the markup meant ("Чл. 278б¹.") and
the repair is recorded. On a bare article number (Чл. 166.SUP>1.) the number
becomes ``166-1``, ordered after 166 and before 166а. The same leak of a closing
span after an article number, in any block ("Чл. 3./span>. …", "чл. 5./span> до 7"),
is cut out ("Чл. 3. …", "Чл. 5 до 7") and recorded alike.

``JUDGEMENTS`` holds the blocks the session read whole (D-072): the label it gave,
and the opening of the block's text, which must still match.
"""
from __future__ import annotations

import re

from .assembler import NUMBER_LINE
from .splitter import Block

HEADING_LABELS = frozenset({"title", "part_heading", "chapter_heading", "section_heading", "subsection_heading",
                            "provisions_heading", "annex_heading"})
# labels that end a stretch of headings: the act's body has begun
BODY_LABELS = frozenset({"article_title", "article_head", "paragraph_sign", "alinea", "unnumbered_alinea", "item",
                         "unnumbered_item", "letter", "continuation", "quoted", "annex_row", "table_row",
                         "adoption_formula", "preamble", "prehistory", "repeal_note"})
_PROVISIONS = re.compile(r"^(Допълнителн|Преходн|Заключителн)\w*\s")
_TITLE_CHANGED = re.compile(r"загл\.\s*изм\.", re.IGNORECASE)
_SUPERSCRIPT = str.maketrans("0123456789", "⁰¹²³⁴⁵⁶⁷⁸⁹")
_OBN = re.compile(r"^\(ОБН\.\s*-\s*ДВ,\s*БР\.")
_ELISION = re.compile(r"^(?:\.\s*){5,}$")
_SEPARATOR = re.compile(r"^-{3,}$")
_ITEM_HEAD = re.compile(r"^(\d+)\.\s")
_SPAN_REMNANT = re.compile(r"(Чл\.\s*\d+[а-я]{0,2})\./span>")
_REMNANT = re.compile(r"^(Чл\.\s*\d+[а-я]?)\.?(?:SU[PР]>|<sup>)(\d{1,2})(?:</sup>|/sup>)?\.")


# the session's readings of single blocks (D-072, "judgement blocks"): slug -> block -> (label, opening of the text)
JUDGEMENTS: dict[str, dict[int, tuple[str, str]]] = {
    "kodeks-za-zastrahovaneto": {3449: ("section_heading", "Общи положения")},
    "kodeks-na-truda": {1007: ("section_heading", "Права при действието на трудовото правоотношение")},
    "nakazatelen-kodeks": {482: ("section_heading", "Особена разпоредба"), 1048: ("section_heading", "Особена разпоредба"),
                           1148: ("section_heading", "Особена разпоредба"), 1226: ("section_heading", "Особена разпоредба"),
                           2683: ("continuation", "Изпълнението на настоящия кодекс")},
    "kodeks-na-targovskoto-koraboplavane-zagl-izm-dv-br-113-ot-2002-g": {2270: ("continuation", "Изпълнението на закона")},
    "zakon-za-ustroystvo-na-teritoriyata": {2493: ("provisions_heading", "ЗАКОН ЗА ИЗМЕНЕНИЕ И ДОПЪЛНЕНИЕ НА ЗАКОНА ЗА УСТРОЙСТВО")},
    "zakon-za-danatsite-varhu-dohodite-na-fizicheskite-litsa": {843: ("chapter_heading", "ПРИСПАДАНЕ И ВЪЗСТАНОВЯВАНЕ НА ДАНЪК")},
    # § 2 of the final provisions adds a chapter X-а, чл. 1001а to 1001г, to another law, with no quotation marks
    "zakon-za-zadalzheniyata-i-dogovorite": {861: ("quoted", "Чл. 1001а."), 863: ("quoted", "Чл. 1001б."),
                                             865: ("quoted", "Чл. 1001в."), 866: ("quoted", "Чл. 1001г.")},
}


def _key(text: str) -> str | None:
    """The text a repeated heading repeats: a number line, or a provisions heading."""
    t = text.strip()
    if NUMBER_LINE.match(t) or _PROVISIONS.match(t):
        return re.sub(r"\s+", " ", t.rstrip(".")).lower()
    return None


def _stretches(blocks: list[Block], smap: dict[int, dict], skip: frozenset[int] = frozenset()) -> list[list[int]]:
    """Runs of consecutive blocks with no body line between them, each holding at least one heading.

    A „(ОБН. - ДВ …)“ line closes a run: it ends the heading of an amending act's provisions, and the next
    provisions heading belongs to another act even when lex.bg elided every § between them.
    """
    out: list[list[int]] = []
    cur: list[int] = []
    for b in blocks:
        if b.i in skip:
            continue
        label = smap.get(b.i, {}).get("label", "unknown")
        if _OBN.match(b.text.strip()):
            cur.append(b.i)
            if any(smap.get(i, {}).get("label") in HEADING_LABELS or _key(blocks[i].text) for i in cur):
                out.append(cur)
            cur = []
            continue
        if label in BODY_LABELS and not _key(b.text):
            if any(smap.get(i, {}).get("label") in HEADING_LABELS or _key(blocks[i].text) for i in cur):
                out.append(cur)
            cur = []
        else:
            cur.append(b.i)
    if cur:
        out.append(cur)
    return out


def superseded_headings(blocks: list[Block], smap: dict[int, dict], skip: frozenset[int] = frozenset()) -> list[list[int]]:
    """The superseded copies, each as its block indices (number line, then title if it has one)."""
    found: list[list[int]] = []
    for stretch in _stretches(blocks, smap, skip):
        copies: dict[str, list[list[int]]] = {}
        for pos, i in enumerate(stretch):
            k = _key(blocks[i].text)
            if k is None:
                continue
            group = [i]
            if pos + 1 < len(stretch):
                j = stretch[pos + 1]
                tj = blocks[j].text.strip()
                if not _key(tj) and not tj.startswith("(") and smap.get(j, {}).get("label") != "article_title":
                    group.append(j)
            copies.setdefault(k, []).append(group)
        for groups in copies.values():
            if len(groups) < 2:
                continue
            titled = [g for g in groups if len(g) > 1]
            if not titled:
                current = groups[0]
            else:
                changed = [g for g in titled if _TITLE_CHANGED.search(blocks[g[1]].text)]
                current = changed[0] if len(changed) == 1 else titled[0]
            found.extend(g for g in groups if g is not current)
    return sorted(found)


def _ruled(e: dict | None, i: int, label: str, rule: str, n: str | None = None, note: str = "") -> dict:
    return {"i": i, "label": label, "n": n, "conf": "high", "note": note or (e or {}).get("note", ""), "rule": rule}


def numbered_lists(blocks: list[Block], smap: dict[int, dict]) -> list[tuple[int, str]]:
    """Ruling 5: (block, number) of each continuation line that is a numbered list under the item before it."""
    found: list[tuple[int, str]] = []
    k = 0
    while k < len(blocks):
        e = smap.get(blocks[k].i, {})
        if e.get("label") == "item" and blocks[k].text.rstrip().endswith(":"):
            expect, j, run = 1, k + 1, []
            while j < len(blocks) and smap.get(blocks[j].i, {}).get("label") == "continuation":
                m = _ITEM_HEAD.match(blocks[j].text)
                if not m or int(m.group(1)) != expect:
                    break
                run.append((blocks[j].i, m.group(1)))
                expect += 1
                j += 1
            found.extend(run)
            k = j if run else k + 1
        else:
            k += 1
    return found


def duplicate_numbers(blocks: list[Block], smap: dict[int, dict]) -> list[list[int]]:
    """Ruling 6: [first, second] for each alinea or item number printed twice in a row under the same parent."""
    found: list[list[int]] = []
    last: dict[str, tuple[str, int] | None] = {"alinea": None, "item": None}
    for b in blocks:
        e = smap.get(b.i, {})
        label = e.get("label")
        if label in HEADING_LABELS or label in ("article_head", "paragraph_sign"):
            last = {"alinea": None, "item": None}
        elif label in ("alinea", "item"):
            prev = last[label]
            # "1. … :" then "1. …" is a sub-list under the first item, not the number printed again
            if prev and prev[0] == e.get("n") and not (e.get("n") == "1" and blocks[prev[1]].text.rstrip().endswith(":")):
                found.append([prev[1], b.i])
            last[label] = (e.get("n"), b.i)
            if label == "alinea":
                last["item"] = None
    return found


def apply(blocks: list[Block], smap: dict[int, dict], slug: str | None = None) -> tuple[dict[int, dict], list[Block], list[dict]]:
    """Return (map, blocks, omissions) with the rulings applied; the inputs are not changed.

    Every entry a rule changes carries ``rule``; the omissions list records each change to the text or the address.
    """
    out = dict(smap)
    blocks = list(blocks)
    omissions: list[dict] = []
    for i, (label, opening) in JUDGEMENTS.get(slug or "", {}).items():
        if i >= len(blocks) or not blocks[i].text.startswith(opening):
            raise ValueError(f"{slug}: judgement block {i} no longer opens with {opening!r}")
        out[i] = _ruled(out.get(i), i, label, "D-072/judgement", note="read by the session (D-072)")
    for i, n in numbered_lists(blocks, out):
        out[i] = _ruled(out.get(i), i, "item", "D-072/5", n)
    for first, second in duplicate_numbers(blocks, out):
        e = out[second]
        out[second] = _ruled(e, second, e["label"], "D-072/6", f"{e['n']}-2")
        omissions.append({"kind": "duplicate_number", "blocks": [first, second]})
    for k, b in enumerate(blocks):
        t = b.text.strip()
        nxt = next((blocks[j] for j in range(k + 1, len(blocks)) if out.get(blocks[j].i, {}).get("label") != "drop"), None)
        if _OBN.match(t) or _ELISION.match(t) or (
                _SEPARATOR.match(t) and nxt is not None and out.get(nxt.i, {}).get("label") == "adoption_formula"):
            if out.get(b.i, {}).get("label") != "editorial_note" or out[b.i].get("conf") != "high":
                out[b.i] = _ruled(out.get(b.i), b.i, "editorial_note", "D-072/8")
    for group in superseded_headings(blocks, smap):
        for i in group:
            out[i] = {"i": i, "label": "drop", "n": None, "conf": "high", "note": "superseded_heading", "rule": "D-072/1"}
        omissions.append({"kind": "superseded_heading", "blocks": group})
    for b in blocks:
        e = out.get(b.i)
        if _SPAN_REMNANT.search(b.text):
            b = blocks[b.i] = Block(b.i, _SPAN_REMNANT.sub(r"\1", b.text), b.hint)
            omissions.append({"kind": "remnant_repaired", "blocks": [b.i]})
        if e and e["label"] == "article_head":
            m = _REMNANT.match(b.text)
            base = m.group(1).replace(" ", "").removeprefix("Чл.") if m else ""
            if m and e.get("n") in (base + m.group(2), f"{base}-{m.group(2)}"):
                blocks[b.i] = Block(b.i, f"{m.group(1)}{m.group(2).translate(_SUPERSCRIPT)}.{b.text[m.end():]}", b.hint)
                omissions.append({"kind": "remnant_repaired", "blocks": [b.i]})
                if base.isdigit():
                    out[b.i] = _ruled(e, b.i, "article_head", "D-072/13", f"{base}-{m.group(2)}")
    return out, blocks, omissions
