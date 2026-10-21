"""Mechanical checks over a structure map. None of them reads meaning.

``coverage``: every block is placed once or dropped once; a dropped block carries
the ``drop`` label with a reason; a dropped block that opens like a provision, or
that lies between placed blocks, or that lies before or after the act without
being the page's known chrome (``START_CHROME``, the list under ``TAIL_CHROME``),
is an exception; a separator line of dashes or dots is never one.
``reassembly``: each assembled line, markers removed, equals its blocks joined.
``text``: a numbered label's number equals the number written in the block, and a
block that opens like an article, §, alinea, item or letter carries a label that
can open one; a block that opens with an article or § number carries ``article_head``,
``paragraph_sign`` or ``quoted`` and nothing else (``hidden_address``); a ``quoted``
block that opens like a provision starts with a quotation mark or stands inside a
quotation that an earlier quoted block opened with one (a run printed without
marks, as in old acts, goes to the ladder and then to the whole-act read); a §
head not written as "§ N." is a ``malformed_head`` source finding; the page's
known chrome under any label but ``drop`` is ``chrome_placed``.
``numbering``: article numbers do not go backwards; alineas start at (1) after an
article head (or continue the one written in the head) and increase by one;
items likewise per parent; letters follow the Bulgarian lettering order; § numbers
increase and are unique within the act's own provisions, restarting only in a
block "към ЗИД …".
``nesting``: an alinea only after an article head or §; an item only inside an
article, alinea or §; a letter only inside an item, alinea, article or §.
``addresses``: one Чл. N per act; a gap in the article or § numbering, or a first
number other than 1, is a source finding (``article_gap``, ``sign_gap``); the §§
printed after a "КЪМ …" heading are a selection from another act and are not
checked for gaps.
``fragments``: no literal markup fragment in placed text (a source finding).
``confidence``: a block labelled ``unknown`` or with low confidence.
``empty_section``: a heading with nothing under it (a source finding).
Every failure is an exception ``{"block", "kind", "detail"}`` on one block.
"""
from __future__ import annotations

import re

from .assembler import assemble_lines, strip_line
from .splitter import Block

FRAGMENTS = ("sup>", "<sup", "span>", "<span", "div>", "<div", "&nbsp;", "<br", "&lt;", "&amp;", "<p", "</", "<b>", "<i>", "&quot;", "&#")
_LATIN_TO_CYR = str.maketrans("aBbeEkKmMHoOpPcCTxXy", "аВьеЕкКмМНоОрРсСТхХу")
_ARTNUM = re.compile(r"^(\d+)([а-я]?)(\d?)$")
_ART_TEXT = re.compile(r"^Чл\.\s*(\d+[а-я]?\d?)\.")
_EDINSTVEN = re.compile(r"^Член\s+единствен\.")
_SIGN_TEXT = re.compile(r"^(?:§\s*(\d+[а-я]?)\s*\.?|Параграф\s+(единствен)\.)")  # tolerant: "§ 72 ." and "§ 26 В" are heads with a malformed form
_ALINEA_TEXT = re.compile(r"^\((\d+[а-я]?)\)")
_ITEM_TEXT = re.compile(r"^(\d+[а-я]?)\.\s")
_LETTER_TEXT = re.compile(r"^([а-я])\)")
# the first alinea written in an article or § head: right after the number, or after one editorial note in parentheses
_FIRST_ALINEA = re.compile(r"^(?:Чл\.\s*\S+\.|§\s*\S+\.|Член\s+единствен\.|Параграф\s+единствен\.)\s*(?:\((?:[^()]|\([^()]*\))*\)\s*)*\((\d+)\)")
_PROVISION_LIKE = re.compile(r"^(Чл\.\s*\d|Член\s+единствен|§\s*\d|Параграф\s+единствен|\(\d+[а-я]?\)|\d+[а-я]?\.\s|[а-я]\)\s)")
BULGARIAN_LETTERS = "абвгдежзиклмнопрстуфхцчшщюя"  # the lettering order used in acts; й, ъ and ь are skipped
_HEADINGS = {"title", "part_heading", "chapter_heading", "section_heading", "subsection_heading", "provisions_heading", "annex_heading"}
_OPENERS = {"article_head", "paragraph_sign", "alinea", "item", "letter", "quoted", "annex_row", "table_row", "unnumbered_alinea", "unnumbered_item"}
_ADDRESS_LIKE = re.compile(r"^(Чл\.\s*\d|Член\s+единствен|§\s*\d|Параграф\s+единствен)")
_QUOTE_OPEN = re.compile(r"^[\"„“«]")
_SEPARATOR = re.compile(r"^-{3,}$")  # lex.bg's dashed separator line: chrome wherever it stands (dot lines are form fields, act content)
_QUOTE_CLOSE = re.compile(r"[\"“”»][.;,:)]?$")
_SIGN_FORM = re.compile(r"^(?:§\s*\d+[а-я]?\.|Параграф\s+единствен\.)(?:\s|$)")
# the page chrome lex.bg prints before the title and after the act: the only drops allowed outside the act
START_CHROME = re.compile(r"^(ДОБАВИ В МОИТЕ АКТОВЕ|Lex\.bg)")
TAIL_CHROME = "Релевантни актове от Европейското законодателство"


def _art_key(n: str) -> tuple[int, str, int]:
    if n == "единствен":
        return (1, "", 0)
    m = _ARTNUM.match(n)
    return (int(m.group(1)), m.group(2), int(m.group(3) or 0)) if m else (0, n, 0)


def _num_key(n: str | None) -> tuple[int, str]:
    m = re.match(r"^(\d+)([а-я]?)$", n or "")
    return (int(m.group(1)), m.group(2)) if m else (0, n or "")


def _follows(prev: tuple[int, str] | None, cur: tuple[int, str]) -> bool:
    """(n) follows (n-1); (n-suffix) follows (n) or the previous suffix of n; the first is (1)."""
    if prev is None:
        return cur[0] == 1
    if cur[1]:
        return cur[0] == prev[0] and (prev[1] == "" or ord(cur[1]) > ord(prev[1]))
    return cur[0] == prev[0] + 1


def _same_heading_group(blocks: list[Block], a: int, b: int, la: str, lb: str) -> bool:
    """Two consecutive heading blocks that form one heading (joined by the assembler), or a legal nesting."""
    ta, tb = blocks[a].text, blocks[b].text
    if re.match(r"^(Част|Дял|Глава|Раздел|Подраздел)\s+[\wIVXLC]+\.?$", ta):
        return True
    if re.match(r"^(КЪМ|Към|към)\s", tb):
        return True
    if la == "annex_heading" and lb == "annex_heading" and re.match(r"^Приложение", ta) and not re.match(r"^Приложение", tb):
        return True
    if la == "section_heading" and lb == "subsection_heading":
        return True
    if la in ("part_heading", "chapter_heading", "title"):
        return True
    return False


def run_all(blocks: list[Block], smap: dict[int, dict]) -> tuple[str, list[dict]]:
    lines, placed, dropped = assemble_lines(blocks, smap)
    md = "\n\n".join(line for line, _ in lines) + "\n"
    ex: list[dict] = []
    idx = {b.i for b in blocks}
    touched = set(placed) | set(dropped)
    for i in sorted(idx - touched):
        ex.append({"block": i, "kind": "not_covered", "detail": "neither placed nor dropped"})
    first_placed, last_placed = (placed[0], placed[-1]) if placed else (-1, -1)
    tail_from = next((i for i in dropped if blocks[i].text == TAIL_CHROME and i > last_placed), None)
    for i in dropped:
        e = smap.get(i, {})
        t = blocks[i].text
        if e.get("label") != "drop":
            ex.append({"block": i, "kind": "dropped_without_label", "detail": "left out without a drop label"})
        elif _PROVISION_LIKE.match(t):
            ex.append({"block": i, "kind": "drop_of_provision", "detail": f"a line that opens like a provision was dropped: {t[:60]!r}"})
        elif _SEPARATOR.match(t):
            continue
        elif first_placed < i < last_placed:
            ex.append({"block": i, "kind": "drop_inside_act", "detail": f"a line between placed blocks was dropped: {t[:60]!r}"})
        elif i < first_placed and not START_CHROME.match(t):
            ex.append({"block": i, "kind": "drop_outside_act", "detail": f"a line before the act is not the page's known chrome: {t[:60]!r}"})
        elif i > last_placed and (tail_from is None or i < tail_from):
            ex.append({"block": i, "kind": "drop_outside_act", "detail": f"a line after the act is not the page's known chrome: {t[:60]!r}"})
        elif not e.get("note"):
            ex.append({"block": i, "kind": "drop_without_reason", "detail": "drop carries no note"})
    for line, idxs in lines:
        if strip_line(line) != " ".join(blocks[i].text for i in idxs):
            ex.append({"block": idxs[0], "kind": "reassembly", "detail": "the assembled line differs from its blocks"})
    if [i for _, idxs in lines for i in idxs] != placed:
        ex.append({"block": placed[0] if placed else 0, "kind": "reassembly", "detail": "the lines do not cover the placed blocks once each, in order"})
    run_open = False  # inside a quotation that a quoted block opened with a quotation mark and no block has closed yet
    for i in placed:
        e = smap.get(i)
        t = blocks[i].text
        if e is None or e["label"] == "unknown":
            run_open = False
            ex.append({"block": i, "kind": "unknown", "detail": (e or {}).get("note", "no label")})
            continue
        if e.get("conf") == "low":
            ex.append({"block": i, "kind": "low_confidence", "detail": e.get("note", "")})
        if e["label"] != "drop" and (START_CHROME.match(t) or t == TAIL_CHROME):
            ex.append({"block": i, "kind": "chrome_placed", "detail": f"the page's chrome carries the label {e['label']}"})
        low = t.lower()
        if any(f in low for f in FRAGMENTS):
            ex.append({"block": i, "kind": "fragment", "detail": "contains a markup fragment"})
        label, n = e["label"], e.get("n")
        tn = t.translate(_LATIN_TO_CYR)
        if label == "article_head":
            m = _ART_TEXT.match(tn)
            if m:
                if m.group(1) != n:
                    ex.append({"block": i, "kind": "label_text_mismatch", "detail": f"article_head n={n!r} but the text says Чл. {m.group(1)}"})
            elif _EDINSTVEN.match(tn):
                if n != "единствен":
                    ex.append({"block": i, "kind": "label_text_mismatch", "detail": "Член единствен needs n 'единствен'"})
            else:
                ex.append({"block": i, "kind": "label_text_mismatch", "detail": "article_head on a line that does not open with Чл. N."})
        elif label == "paragraph_sign":
            m = _SIGN_TEXT.match(tn)
            if not m or (m.group(1) or m.group(2)) != n:
                ex.append({"block": i, "kind": "label_text_mismatch", "detail": f"paragraph_sign n={n!r} on {t[:30]!r}"})
            elif not _SIGN_FORM.match(tn):
                ex.append({"block": i, "kind": "malformed_head", "detail": f"§ head not written as '§ N.': {t[:30]!r}"})
        elif label == "alinea":
            m = _ALINEA_TEXT.match(tn)
            if not m or m.group(1) != n:
                ex.append({"block": i, "kind": "label_text_mismatch", "detail": f"alinea n={n!r} on {t[:30]!r}"})
        elif label == "item":
            m = _ITEM_TEXT.match(tn)
            if not m or m.group(1) != n:
                ex.append({"block": i, "kind": "label_text_mismatch", "detail": f"item n={n!r} on {t[:30]!r}"})
        elif label == "letter":
            m = _LETTER_TEXT.match(tn)
            if not m or m.group(1) != n:
                ex.append({"block": i, "kind": "label_text_mismatch", "detail": f"letter n={n!r} on {t[:30]!r}"})
        elif label == "continuation":
            if _PROVISION_LIKE.match(tn):
                ex.append({"block": i, "kind": "label_text_mismatch", "detail": f"continuation on a line that opens like a provision: {t[:40]!r}"})
        elif label == "quoted":
            # a quoted block that opens like a provision starts with a quotation mark, or stands inside a quotation that an
            # earlier quoted block opened with one and no block since has closed; a run with no mark goes to the ladder
            if _PROVISION_LIKE.match(tn) and not _QUOTE_OPEN.match(t) and not run_open:
                ex.append({"block": i, "kind": "label_text_mismatch", "detail": f"quoted on a line that opens like a provision, outside an open quotation: {t[:40]!r}"})
            if _QUOTE_OPEN.match(t):
                run_open = True
            if _QUOTE_CLOSE.search(t) and not (_QUOTE_OPEN.match(t) and len(t) == 1):
                run_open = False
        elif _ADDRESS_LIKE.match(tn):
            ex.append({"block": i, "kind": "hidden_address", "detail": f"{label} on a line that opens with an address: {t[:40]!r}"})
        elif label not in _OPENERS and label not in _HEADINGS and label not in ("drop", "editorial_note", "repeal_note") and _PROVISION_LIKE.match(tn):
            ex.append({"block": i, "kind": "label_text_mismatch", "detail": f"{label} on a line that opens like a provision: {t[:40]!r}"})
        if label != "quoted":
            run_open = False
    prev_heading: int | None = None
    for i in placed:
        e = smap.get(i)
        if not e:
            continue
        if e["label"] in _HEADINGS:
            if prev_heading is not None and not _same_heading_group(blocks, prev_heading, i, smap[prev_heading]["label"], e["label"]):
                ex.append({"block": prev_heading, "kind": "empty_section", "detail": f"heading with no body before block {i}"})
            prev_heading = i
        else:
            prev_heading = None
    last_art: tuple[int, str, int] | None = None
    seen_art: dict[str, int] = {}
    seen_sign: dict[str, int] = {}
    last_sign: tuple[int, str] | None = None
    in_article = in_sign = False
    last_alinea: tuple[int, str] | None = None
    last_item: tuple[int, str] | None = None
    last_letter = ""
    item_parent_ok = False
    amending = False  # after the first "КЪМ …" provisions heading lex.bg prints a selection of another act's §§: no gap check there
    for i in placed:
        e = smap.get(i)
        if not e or e["label"] == "unknown":
            continue
        label, n = e["label"], e.get("n")
        t = blocks[i].text.translate(_LATIN_TO_CYR)
        if label in _HEADINGS:
            in_article = in_sign = False
            last_alinea = last_item = None
            last_letter = ""
            item_parent_ok = False
            if label == "provisions_heading" and re.search(r"(КЪМ|Към|към)\s", t):
                seen_sign = {}
                last_sign = None
                amending = True
        elif label == "article_head":
            key = _art_key(n)
            if last_art is not None and key < last_art:
                ex.append({"block": i, "kind": "article_order", "detail": f"Чл. {n} after Чл. {last_art[0]}{last_art[1]}{last_art[2] or ''}"})
            if n in seen_art:
                ex.append({"block": i, "kind": "duplicate_address", "detail": f"Чл. {n} already at block {seen_art[n]}"})
            elif last_art is None and key[0] != 1:
                ex.append({"block": i, "kind": "article_gap", "detail": f"the first article is Чл. {n}"})
            elif last_art is not None and key > last_art and not key[1] and not key[2] and key[0] > last_art[0] + 1:
                ex.append({"block": i, "kind": "article_gap", "detail": f"Чл. {n} after Чл. {last_art[0]}{last_art[1]}{last_art[2] or ''}"})
            seen_art[n] = i
            last_art = key
            in_article, in_sign = True, False
            m = _FIRST_ALINEA.search(t)
            last_alinea = (int(m.group(1)), "") if m else None
            last_item = None
            last_letter = ""
            item_parent_ok = True
        elif label == "paragraph_sign":
            key = _num_key(n) if n != "единствен" else (1, "")
            if n in seen_sign:
                ex.append({"block": i, "kind": "duplicate_address", "detail": f"§ {n} already at block {seen_sign[n]} in this provisions block"})
            elif last_sign is not None and key <= last_sign and not key[1] and n != "единствен":
                ex.append({"block": i, "kind": "sign_order", "detail": f"§ {n} after § {last_sign[0]}{last_sign[1]}"})
            elif amending:
                pass
            elif last_sign is None and key[0] != 1:
                ex.append({"block": i, "kind": "sign_gap", "detail": f"the first § of the provisions block is § {n}"})
            elif last_sign is not None and not key[1] and key[0] > last_sign[0] + 1:
                ex.append({"block": i, "kind": "sign_gap", "detail": f"§ {n} after § {last_sign[0]}{last_sign[1]}"})
            seen_sign[n] = i
            last_sign = key
            in_sign, in_article = True, False
            m = _FIRST_ALINEA.search(t)
            last_alinea = (int(m.group(1)), "") if m else None
            last_item = None
            last_letter = ""
            item_parent_ok = True
        elif label == "alinea":
            if not (in_article or in_sign):
                ex.append({"block": i, "kind": "nesting", "detail": "alinea outside an article or §"})
            key = _num_key(n)
            if not _follows(last_alinea, key):
                ex.append({"block": i, "kind": "alinea_order", "detail": f"({n}) after ({last_alinea[0]}{last_alinea[1]})" if last_alinea else f"({n}) opens the article"})
            last_alinea = key
            last_item = None
            last_letter = ""
            item_parent_ok = True
        elif label == "unnumbered_alinea":
            if not (in_article or in_sign):
                ex.append({"block": i, "kind": "nesting", "detail": "paragraph outside an article or §"})
            last_item = None
            last_letter = ""
            item_parent_ok = True
        elif label == "unnumbered_item":
            if not item_parent_ok:
                ex.append({"block": i, "kind": "nesting", "detail": "list line outside an article, alinea or §"})
            last_letter = ""
        elif label == "item":
            if not item_parent_ok:
                ex.append({"block": i, "kind": "nesting", "detail": "item outside an article, alinea or §"})
            key = _num_key(n)
            if not _follows(last_item, key):
                ex.append({"block": i, "kind": "item_order", "detail": f"{n}. after {last_item[0]}{last_item[1]}." if last_item else f"{n}. opens the list"})
            last_item = key
            last_letter = ""
        elif label == "letter":
            if not item_parent_ok:
                ex.append({"block": i, "kind": "nesting", "detail": "letter outside an article, alinea, § or item"})
            if n:
                pos = BULGARIAN_LETTERS.find(n)
                prev = BULGARIAN_LETTERS.find(last_letter) if last_letter else -1
                if pos < 0 and n not in "йъь":
                    ex.append({"block": i, "kind": "letter_order", "detail": f"{n}) is not a lettering letter"})
                elif last_letter and pos >= 0 and pos != prev + 1:
                    ex.append({"block": i, "kind": "letter_order", "detail": f"{n}) after {last_letter})"})
                elif not last_letter and pos > 0:
                    ex.append({"block": i, "kind": "letter_order", "detail": f"{n}) opens the lettering"})
                last_letter = n if pos >= 0 else last_letter
    return md, ex
