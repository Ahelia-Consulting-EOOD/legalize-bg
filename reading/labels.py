"""The structure map: one entry per block, returned by the model and validated here.

An entry is ``{"i": <block index>, "label": <one of LABELS>, "n": <number or null>,
"conf": "high" | "low", "note": <optional short reason>}``; the compact form of the call
driver (``l`` for ``label``, ``c`` for ``conf``, ``n`` and ``c`` left out when null or
high) is accepted too. The model never returns text. ``validate_entries`` refuses an entry with an unknown label, a missing or
duplicated index, or a number of the wrong shape, so a malformed answer is an
exception on its blocks rather than a silent gap.
"""
from __future__ import annotations

import re

LABELS: dict[str, str] = {
    "title": "the act's title line",
    "prehistory": "the in-force or publication line that lex.bg prints in italics under the title",
    "preamble": "free text before the first chapter or article that is part of the act (motives, a project number)",
    "part_heading": "Част or Дял heading",
    "chapter_heading": "Глава heading",
    "section_heading": "Раздел heading",
    "subsection_heading": "Подраздел heading",
    "article_title": "an article's own title line printed before its number",
    "article_head": "the line that opens an article: starts with Чл. N. (n = the number with its letter suffix, e.g. 5, 5а, 260и1; 'единствен' for Член единствен)",
    "alinea": "a numbered paragraph line (1), (2) … of the current article (n = the number)",
    "unnumbered_alinea": "a paragraph line of the current article without a number (pre-1974 drafting)",
    "item": "a numbered item line 1., 2. … under the current article or paragraph (n = the number)",
    "unnumbered_item": "a list line without a number under the current article or paragraph (older drafting: lines ending with ';')",
    "letter": "a lettered item line а), б) … or a doubled or tripled sub-letter line аа), бб), ааа) … under a letter (n = the letters as written)",
    "continuation": "a line that continues the previous provision's text (a wrapped or split line)",
    "quoted": "a line that is quoted text inside the current provision and must not become an address, even if it looks like Чл. N. or (1)",
    "provisions_heading": "a heading of Допълнителни, Преходни or Заключителни разпоредби, including the ones 'към ЗИД …'",
    "paragraph_sign": "the line that opens a § provision: starts with § N. (n = the number; 'единствен' for Параграф единствен)",
    "annex_heading": "a heading of a Приложение",
    "annex_row": "a line that belongs to an annex (table rows, forms, lists inside an annex)",
    "table_row": "a table row inside a provision, not an annex",
    "editorial_note": "lex.bg's own note, such as (Изм. - ДВ, бр. … ) printed as a separate line, or 'Загл. изм.'",
    "repeal_note": "a line saying the act or a provision is repealed (отм.)",
    "adoption_formula": "the closing formula of a law: 'Законът е приет от … Народно събрание на … и е подпечатан с официалния печат …'",
    "drop": "site chrome, navigation, advertising or anything that is not the act (note = reason)",
    "unknown": "the model cannot tell (note = why); this is an exception",
}
NUMBERED = {"article_head", "alinea", "item", "letter", "paragraph_sign"}
_NUM = {
    "article_head": re.compile(r"^(\d+[а-я]?\d{0,2}|единствен)$"),  # the superscript may have two digits (ДОПК Чл. 143я¹³)
    "paragraph_sign": re.compile(r"^(\d+[а-я]?|единствен)$"),
    "alinea": re.compile(r"^\d+[а-я]?$"),
    "item": re.compile(r"^\d+[а-я]?$"),
    "letter": re.compile(r"^([а-я])\1{0,2}$"),  # аа), бб) … are sub-letters under a letter (ЗДДС § 1); ааа) … one level deeper (ДОПК § 1а)
}


def validate_entries(entries, expected: list[int], *, target: int | None = None) -> tuple[dict[int, dict], list[dict]]:
    """Return (map by block index, problems). A problem is an exception on a block.

    With ``target`` set (a round above 0) only the target's entry is read; other entries are ignored.
    A problem that cannot be tied to a block of the task carries block -1 and is never re-scheduled.
    """
    out: dict[int, dict] = {}
    problems: list[dict] = []
    seen: set[int] = set()
    if not isinstance(entries, list):
        return out, [{"block": target if target is not None else -1, "kind": "bad_answer", "detail": "the answer is not a JSON array"}]
    for e in entries:
        if not isinstance(e, dict):
            problems.append({"block": -1, "kind": "bad_answer", "detail": "an entry is not an object"})
            continue
        i = e.get("i")
        if isinstance(i, bool) or not isinstance(i, int) or i not in expected:
            problems.append({"block": -1, "kind": "bad_index", "detail": f"index {i!r} not in the task"})
            continue
        if target is not None and i != target:
            continue
        if i in seen:
            problems.append({"block": i, "kind": "duplicate_entry", "detail": "the block was labelled twice"})
            continue
        label = e.get("label", e.get("l"))
        if not isinstance(label, str) or label not in LABELS:
            problems.append({"block": i, "kind": "bad_label", "detail": f"label {label!r}"})
            continue
        n = e.get("n")
        if isinstance(n, int) and not isinstance(n, bool):
            n = str(n)
        if label in NUMBERED:
            if not isinstance(n, str) or not _NUM[label].match(n):
                problems.append({"block": i, "kind": "bad_number", "detail": f"{label} with n={n!r}"})
                continue
        seen.add(i)
        conf = e.get("conf", e.get("c", "high"))
        note = e.get("note")
        out[i] = {"i": i, "label": label, "n": n if label in NUMBERED else None,
                  "conf": conf if conf in ("high", "low") else "low", "note": note if isinstance(note, str) else ""}
    wanted = [target] if target is not None else expected
    for i in wanted:
        if i not in seen:
            problems.append({"block": i, "kind": "missing_entry", "detail": "the block was not labelled"})
    return out, problems
