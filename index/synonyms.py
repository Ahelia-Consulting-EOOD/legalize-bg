"""Bulgarian legal-term synonym dictionary.

Maps single-token abbreviations (after bg_normalize lowercasing) to
their canonical multi-word form. Used by mcp_server/queries.py:
full_text_search to rewrite single-token abbreviation queries before
FTS5 sees them, so `search("ЗОП")` → finds "Закон за обществените
поръчки" even though the abbreviation never appears in the act body.

Source: hand-curated from the 20 most-cited Bulgarian legal
abbreviations across `laws/`, `codes/`, and `implementing/`. New
entries should be added with the canonical form pulled from the
authoritative law's `titulo` frontmatter field, so the FTS5 lookup
hits the indexed title text.

Lookup direction is one-way (abbreviation → canonical): the long form
already reaches the act via FTS5 title matching, so we don't need
the reverse direction. Matching is case-insensitive (the lookup key
is bg_normalize-d before consultation).

FR-015 / D-2026-05-09-04 closure (Phase 1b.3).
"""

from __future__ import annotations


# Hand-curated. Keys are bg_normalize-d (lowercase, no diacritics
# stripped — Bulgarian doesn't use them). Values are the canonical
# titulo strings as they appear in the corpus, but lowercased to match
# the indexed laws_fts.title text.
#
# Adding entries: pull the canonical form from the law's frontmatter
# `titulo`, lowercase it, and verify FTS5 returns the expected act for
# both the abbreviation AND the canonical query before committing.
LEGAL_ABBREVIATIONS: dict[str, str] = {
    # Public-procurement / IT / e-government
    "зоп":   "закон за обществените поръчки",
    "ппзоп": "правилник за прилагане на закона за обществените поръчки",
    "зеу":   "закон за електронното управление",
    "завп":  "закон за автомобилните превози",
    # Tax
    "здде":  "закон за данък върху добавената стойност",
    "здднс": "закон за данъците върху доходите на физическите лица",
    "здфл":  "закон за данъците върху доходите на физическите лица",
    "здффл": "закон за данъците върху доходите на физическите лица",
    "зкпо":  "закон за корпоративното подоходно облагане",
    "змдт":  "закон за местните данъци и такси",
    # Civil / commercial
    "зн":    "закон за наследството",
    "зс":    "закон за собствеността",
    "зтр":   "закон за търговския регистър",
    "зт":    "закон за туризма",
    "змоип": "закон за мерките против изпирането на пари",
    # Codes
    "нк":    "наказателен кодекс",
    "нпк":   "наказателно-процесуален кодекс",
    "гпк":   "граждански процесуален кодекс",
    "апк":   "административнопроцесуален кодекс",
    "кт":    "кодекс на труда",
    "ск":    "семеен кодекс",
    "тк":    "търговски кодекс",
}


def expand_if_abbreviation(normalized_query: str) -> str | None:
    """Return the canonical long form if `normalized_query` is a
    single-token abbreviation in `LEGAL_ABBREVIATIONS`, else None.

    The caller (full_text_search) replaces the query with the canonical
    form when this returns a non-None value. Multi-word queries pass
    through unchanged (the user provided context).

    Pre-condition: `normalized_query` has already been bg_normalize-d
    (lowercased, whitespace collapsed).
    """
    if not normalized_query or " " in normalized_query:
        return None
    return LEGAL_ABBREVIATIONS.get(normalized_query)
