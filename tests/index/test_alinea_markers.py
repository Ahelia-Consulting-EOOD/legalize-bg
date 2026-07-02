"""P0-2 (review 2026-07-02): parenthesised years/citation numbers were
parsed as alinea boundaries, truncating real alineas and minting bogus
paragraph rows (116 rows / 22 acts live, e.g. paragraph='1969')."""

from index.provisions import _split_alineas, parse


def test_year_in_parens_is_not_an_alinea_boundary():
    # Naredba № 3/2004 (ship tonnage) pattern — the live corruption case.
    body = ("Чл. 10. (1) При придобиване на кораб в чужбина, за който има "
            "издадено валидно Международно свидетелство за тонажа (1969), "
            "срокът за подаване на заявление за измерване е 3 месеца от "
            "датата на придобиване. (2) Срокът се удължава с 4 седмици.")
    pairs = _split_alineas(body)
    assert [p for p, _ in pairs] == ["1", "2"]
    assert "срокът за подаване" in pairs[0][1]      # not truncated at (1969)
    assert "(1969)" in pairs[0][1]                   # year stays in the text


def test_midtext_citation_number_is_not_a_boundary():
    # ЗРТ чл. 19 pattern: "(2003)" / "(2020)" citations inside running text.
    body = ("Чл. 19. (1) Прилагат се препоръките от Регламента (2003) и "
            "изменението (2020) по отношение на доставчиците. "
            "(2) Друго правило.")
    pairs = _split_alineas(body)
    assert [p for p, _ in pairs] == ["1", "2"]
    assert "(2003)" in pairs[0][1] and "(2020)" in pairs[0][1]


def test_inline_and_suffixed_markers_still_split():
    body = "Чл. 1. (1) Първа. (2) Втора. (2а) Втора-а. (3) Трета."
    assert [p for p, _ in _split_alineas(body)] == ["1", "2", "2а", "3"]


def test_marker_at_start_of_body_and_after_bold_anchor():
    assert [p for p, _ in _split_alineas("(1) Направо алинея. (2) Втора.")] \
        == ["1", "2"]
    assert [p for p, _ in _split_alineas("**Чл. 5.** (1) Първа. (2) Втора.")] \
        == ["1", "2"]


def test_parse_emits_no_bogus_year_paragraph_rows():
    md = ("**Чл. 10.** (1) Свидетелство за тонажа (1969), срокът е 3 "
          "месеца. (2) Удължава се.")
    rows = parse(md, law_id="x")
    paragraphs = [r.paragraph for r in rows if r.paragraph is not None]
    assert paragraphs == ["1", "2"]


def test_alinea_marker_after_letter_still_splits():
    # ЗЕУ чл. 5 pattern (review 2026-07-02): a real, amendment-introduced
    # alinea whose preceding sentence ends without punctuation ("...
    # управление") must still be split out, not absorbed into the prior
    # alinea's text. A letter-boundary heuristic was rejected precisely
    # because it cannot tell this apart from a citation like "(1969)".
    body = ("Чл. 5. (1) Кметът осъществява дейностите по управление "
            "(2) (Нова - ДВ, бр. 94 от 2019 г.) Лицата по чл. 1, ал. 1 "
            "и 2 съгласуват дейностите.")
    pairs = _split_alineas(body)
    assert [p for p, _ in pairs] == ["1", "2"]
