"""The act-name resolver: a Gazette title in, a corpus act or nothing out.

§5.3 of `docs/plans/2026-09-05-dv-graded-source-design.md`. Every
attribution, every chain-omission row and every candidate grade of the
coverage map rests on this, so the property that matters most is the one
asserted hardest below: the resolver never guesses. Two candidates, or
none, is `None` with `title_ambiguous`, never a best effort.

The titles are real. Twelve come from the contents of брой 74 от 2016
(the fixture `materiali-idObj6121.html`), the rest from the corpus, and
each carries the law_id it must produce or the `None` it must not
improve on.
"""

import collections
import pathlib
import random

import pytest

from fetcher.dv.resolver import (
    CorpusAct,
    NumberedKey,
    Resolver,
    load_corpus_acts,
    normalise_title,
    numbered_key,
    parse_dv_citation,
    strip_amending_prefix,
)

CORPUS_ROOT = pathlib.Path(__file__).resolve().parents[3]


@pytest.fixture(scope="session")
def corpus_acts():
    return load_corpus_acts(CORPUS_ROOT)


@pytest.fixture(scope="session")
def resolver(corpus_acts):
    return Resolver(corpus_acts)


def resolver_without(corpus_acts, title):
    """A resolver that has never seen the act this title names.

    The ordinary case across 42,000 Gazette materials is a title naming
    an act the corpus does not hold: a repealed наредба, a superseded
    устройствен правилник, an act not yet bootstrapped. Asking the full
    corpus for a title it contains only measures the exact index.
    """
    key = normalise_title(title)
    return Resolver(
        [act for act in corpus_acts if normalise_title(act.title) != key]
    )


def resolver_excluding(corpus_acts, *law_ids):
    """A resolver built without the named acts."""
    dropped = set(law_ids)
    return Resolver([act for act in corpus_acts if act.law_id not in dropped])


# --- normalise_title ------------------------------------------------------


def test_the_casefold_is_the_cyrillic_one():
    # SQLite's LOWER() is ASCII-only, which is why FR-019 folds in Python.
    assert normalise_title("ЗАКОН ЗА ТУРИЗМА") == "закон за туризма"
    assert normalise_title("Закон за туризма") == normalise_title("ЗАКОН ЗА ТУРИЗМА")


def test_punctuation_goes_and_hyphens_stay():
    # A hyphen inside a compound act name carries meaning
    # („Данъчно-осигурителен процесуален кодекс“) and the number of a
    # наредба is built out of hyphens („№ РД-02-20-1“).
    assert (
        normalise_title("НАРЕДБА ЗА УСЛОВИЯТА, ПРАВИЛАТА И РЕДА")
        == "наредба за условията правилата и реда"
    )
    assert "данъчно-осигурителен" in normalise_title(
        "ДАНЪЧНО-ОСИГУРИТЕЛЕН ПРОЦЕСУАЛЕН КОДЕКС"
    )


def test_the_title_amendment_note_is_not_part_of_the_title():
    # 282 corpus titles carry it. It records that lex.bg's title differs
    # from the promulgated one, which is exactly what must not enter the
    # matching key.
    assert normalise_title(
        "ЗАКОН ЗА АДМИНИСТРАТИВНОТО РЕГУЛИРАНЕ (ЗАГЛ. ИЗМ. - ДВ, БР. 26 ОТ 2020 Г.)"
    ) == "закон за административното регулиране"


def test_a_regulation_number_in_a_title_survives():
    # „ЗАКОН ЗА ИЗПЪЛНЕНИЕ НА РЕГЛАМЕНТ (ЕС) 2019/125“: not every
    # parenthetical is an editorial note.
    assert "ес" in normalise_title("ЗАКОН ЗА ИЗПЪЛНЕНИЕ НА РЕГЛАМЕНТ (ЕС) 2019/125")


@pytest.mark.parametrize(
    "title, target",
    [
        (
            "Закон за изменение и допълнение на Закона за юридическите лица",
            "закон за юридическите лица",
        ),
        # The adjective keeps its article here: undoing it is not a
        # function, so `title_variants` offers the readings instead.
        ("Закон за изменение на Наказателния кодекс", "наказателния кодекс"),
        ("Закон за допълнение на Търговския закон", "търговския закон"),
        ("Закон за отмяна на Закона за счетоводството", "закон за счетоводството"),
        ("Закон за отменяне на Закона за счетоводството", "закон за счетоводството"),
        ("Поправка в Закона за счетоводството", "закон за счетоводството"),
        (
            "Наредба за изменение и допълнение на Наредба № 2 от 2001 г. за пътищата",
            "наредба № 2 от 2001 г за пътищата",
        ),
        # The act type of the amending act is not the act type of its target.
        (
            "Постановление № 238 от 13 септември 2016 г. за изменение на Наредбата "
            "за цените, приета с Постановление № 97 на Министерския съвет от 2013 г.",
            "наредба за цените",
        ),
    ],
)
def test_the_amending_prefix_and_the_adoption_tail_are_stripped(title, target):
    assert normalise_title(title) == target


def test_a_title_that_amends_nothing_is_left_whole():
    assert normalise_title("ЗАКОН ЗА ОБЩЕСТВЕНИЯ ТРАНСПОРТ") == (
        "закон за обществения транспорт"
    )


def test_strip_amending_prefix_is_available_on_its_own():
    assert strip_amending_prefix(
        "Закон за изменение и допълнение на Кодекса на труда"
    ) == "Кодекса на труда"


@pytest.mark.parametrize(
    "declined, nominative",
    [
        ("Закона за туризма", "закон за туризма"),
        ("Кодекса на труда", "кодекс на труда"),
        ("Наредбата за цените", "наредба за цените"),
        ("Правилника за прилагане", "правилник за прилагане"),
        ("Постановлението за нещо", "постановление за нещо"),
        ("Указа за нещо", "указ за нещо"),
        ("Тарифата за нещо", "тарифа за нещо"),
        ("Инструкцията за нещо", "инструкция за нещо"),
    ],
)
def test_the_definite_act_type_noun_comes_back_to_the_nominative(declined, nominative):
    # This one is a lookup and cannot be wrong, so it is in the key.
    assert normalise_title(declined) == nominative


@pytest.mark.parametrize(
    "declined, nominative",
    [
        ("Наказателния кодекс", "наказателен кодекс"),
        ("Административнопроцесуалния кодекс", "административнопроцесуален кодекс"),
        ("Изборния кодекс", "изборен кодекс"),
        ("Семейния кодекс", "семеен кодекс"),
        ("Търговския закон", "търговски закон"),
        ("Гражданския процесуален кодекс", "граждански процесуален кодекс"),
        ("Устройствения правилник на нещо", "устройствен правилник на нещо"),
        (
            "Данъчно-осигурителния процесуален кодекс",
            "данъчно-осигурителен процесуален кодекс",
        ),
    ],
)
def test_the_definite_adjective_is_offered_as_a_reading(declined, nominative):
    # „...ния“ comes from „...ен“ with the fleeting vowel elided and
    # „...ения“ from „...ен“ without it, so the inverse is not a
    # function. Every reading is offered and the corpus index decides.
    from fetcher.dv.resolver import title_variants

    assert nominative in title_variants(normalise_title(declined))


# --- numbered_key ---------------------------------------------------------


@pytest.mark.parametrize(
    "title, key",
    [
        (
            "НАРЕДБА № 3 ОТ 22 АПРИЛ 2026 Г. ЗА УСЛОВИЯТА",
            NumberedKey("наредба", "3", 2026),
        ),
        ("Наредба № 3 от 2026 г.", NumberedKey("наредба", "3", 2026)),
        ("Наредба № 3 от 22.04.2026 г.", NumberedKey("наредба", "3", 2026)),
        # A наредба with no date at all: 1,976 corpus ordinances are
        # numbered and not all of them carry one.
        ("НАРЕДБА № 0-31 ЗА РАБОТА С РАДИАЦИОННИ ДЕФЕКТОСКОПИ",
         NumberedKey("наредба", "0-31", None)),
        ("НАРЕДБА № Н-10 ОТ 20 АВГУСТ 2021 Г. ЗА ПРИДОБИВАНЕ",
         NumberedKey("наредба", "Н-10", 2021)),
        ("НАРЕДБА № РД-02-20-1 ОТ 2015 Г. ЗА НЕЩО",
         NumberedKey("наредба", "РД-02-20-1", 2015)),
        ("НАРЕДБА № 8121з-1006 ОТ 24 АВГУСТ 2015 Г. ЗА РЕДА",
         NumberedKey("наредба", "8121З-1006", 2015)),
        ("НАРЕДБА № 13а-10403 ЗА ПРЕДЕЛНИТЕ РАЗМЕРИ",
         NumberedKey("наредба", "13А-10403", None)),
        ("НАРЕДБА № 16-116 ОТ 8 ФЕВРУАРИ 2008 Г.",
         NumberedKey("наредба", "16-116", 2008)),
        ("Постановление № 235 от 13 септември 2016 г.",
         NumberedKey("постановление", "235", 2016)),
        ("ЗАКОН ЗА ОБЩЕСТВЕНИЯ ТРАНСПОРТ", None),
        ("НАРЕДБА ЗА УСЛОВИЯТА, ПРАВИЛАТА И РЕДА", None),
        ("", None),
    ],
)
def test_numbered_key(title, key):
    assert numbered_key(title) == key


def test_the_number_is_read_from_the_target_not_from_the_amending_act():
    # A ПМС that amends a наредба carries the ПМС number in its own title.
    # Reading that as the наредба's number would attribute the event to
    # whichever наредба happens to carry the decree's number.
    assert numbered_key(
        "Постановление № 238 от 13 септември 2016 г. за изменение на "
        "Наредбата за цените, приета с Постановление № 97 от 2013 г."
    ) is None
    assert numbered_key(
        "Наредба за изменение и допълнение на Наредба № 2 от 2001 г. за пътищата"
    ) == NumberedKey("наредба", "2", 2001)


def test_latin_lookalikes_fold_onto_the_cyrillic_number():
    # The corpus writes the same МВР series both ways: „№ І-3“ with the
    # Cyrillic І and „№ I-107“ with the Latin one; „№ Н-10“ appears with
    # the Cyrillic Н and the Latin H. Folding is the difference between
    # finding the act and recording a Gazette gap that is not there.
    assert numbered_key("Наредба № I-3 от 2015 г.") == numbered_key(
        "Наредба № І-3 от 2015 г."
    )
    assert numbered_key("Наредба № H-10 от 2021 г.") == numbered_key(
        "Наредба № Н-10 от 2021 г."
    )


# --- the promulgation citation --------------------------------------------


@pytest.mark.parametrize(
    "text, citation",
    [
        ("(ДВ, бр. 32 от 2026 г.)", (32, 2026)),
        ("Закона за нещо (ДВ, бр. 153 от 1998 г.)", (153, 1998)),
        ("ДВ, бр. 74 от 2016 г.", (74, 2016)),
        ("нищо тук", None),
    ],
)
def test_parse_dv_citation(text, citation):
    assert parse_dv_citation(text) == citation


# --- the resolutions ------------------------------------------------------

# Real titles. The first block is the contents of брой 74 от 2016 as the
# fixture lists it; the rest are corpus titles and the citations a ЗИД
# would use for them.
CASES = [
    # --- from tests/fixtures/dv/materiali-idObj6121.html ---
    (
        "Закон за изменение и допълнение на Закона за юридическите лица с "
        "нестопанска цел",
        "Народно събрание",
        "zakon-za-yuridicheskite-litsa-s-nestopanska-tsel",
    ),
    (
        "Закон за изменение и допълнение на Административнопроцесуалния кодекс",
        "Народно събрание",
        "administrativnoprotsesualen-kodeks",
    ),
    (
        "Постановление № 235 от 13 септември 2016 г. за приемане на Правилник за "
        "прилагане на Закона за електронната идентификация",
        "Министерски съвет",
        "pravilnik-za-prilagane-na-zakona-za-elektronnata-identifikatsiya",
    ),
    (
        "Постановление № 236 от 13 септември 2016 г. за изменение на Устройствения "
        "правилник на Министерството на финансите, приет с Постановление № 249 на "
        "Министерския съвет от 2009 г.",
        "Министерски съвет",
        "ustroystven-pravilnik-na-ministerstvoto-na-finansite",
    ),
    (
        "Постановление № 237 от 13 септември 2016 г. за допълнение на Постановление "
        "№ 74 на Министерския съвет от 2015 г. за създаване на Национален "
        "икономически съвет",
        "Министерски съвет",
        None,  # the corpus holds no постановления
    ),
    (
        "Постановление № 238 от 13 септември 2016 г. за изменение на Наредбата за "
        "условията, правилата и реда за регулиране и регистриране на цените на "
        "лекарствените продукти, приета с Постановление № 97 на Министерския съвет "
        "от 2013 г.",
        "Министерски съвет",
        "naredba-za-usloviyata-pravilata-i-reda-za-regulirane-i-registrirane-na-tsenite-n",
    ),
    (
        "Постановление № 239 от 13 септември 2016 г. за структурни промени в "
        "системата на здравеопазването",
        "Министерски съвет",
        None,
    ),
    (
        "Договор за изменение и допълнение на Националния рамков договор за "
        "денталните дейности между Националната здравноосигурителна каса и "
        "Българския зъболекарски съюз за 2016 г.",
        "Министерство на здравеопазването",
        None,
    ),
    (
        "Наредба № 1 от 30 август 2016 г. за условията и реда за прием и спортна "
        "подготовка на учениците в спортните училища",
        "Министерство на младежта и спорта",
        # The corpus title was amended in 2019 to „специализирана подготовка“.
        "naredba-1-ot-30-avgust-2016-g-za-usloviyata-i-reda-za-priem-i-spetsializirana-po",
    ),
    (
        "Наредба № 11 от 1 септември 2016 г. за оценяване на резултатите от "
        "обучението на учениците",
        "Министерство на образованието и науката",
        "naredba-11-ot-1-septemvri-2016-g-za-otsenyavane-na-rezultatite-ot-obuchenieto-na",
    ),
    (
        "Наредба за изменение и допълнение на Наредба № 2 от 2001 г. за "
        "сигнализация на пътищата с пътна маркировка",
        "Министерство на регионалното развитие и благоустройството",
        "naredba-2-ot-17-yanuari-2001-g-za-signalizatsiya-na-patishtata-s-patna-markirovk",
    ),
    (
        "Решение № 432 от 29 август 2016 г. за изменение и допълнение на Правилата "
        "за осъществяване на електронни съобщения чрез радиосъоръжения",
        "Комисия за регулиране на съобщенията",
        None,
    ),
    # --- ЗИД citations of corpus acts ---
    (
        "Закон за изменение и допълнение на Кодекса на труда",
        "Народно събрание",
        "kodeks-na-truda",
    ),
    (
        "Закон за изменение и допълнение на Закона за задълженията и договорите",
        "Народно събрание",
        "zakon-za-zadalzheniyata-i-dogovorite",
    ),
    (
        "Закон за изменение на Наказателния кодекс",
        "Народно събрание",
        "nakazatelen-kodeks",
    ),
    (
        "Закон за изменение и допълнение на Семейния кодекс",
        "Народно събрание",
        "semeen-kodeks",
    ),
    (
        "Закон за допълнение на Търговския закон",
        "Народно събрание",
        "targovski-zakon",
    ),
    (
        "Закон за изменение и допълнение на Гражданския процесуален кодекс",
        "Народно събрание",
        "grazhdanski-protsesualen-kodeks",
    ),
    (
        "Закон за изменение и допълнение на Данъчно-осигурителния процесуален кодекс",
        "Народно събрание",
        "danachno-osiguritelen-protsesualen-kodeks",
    ),
    (
        "Закон за изменение и допълнение на Изборния кодекс",
        "Народно събрание",
        "izboren-kodeks",
    ),
    (
        "Закон за изменение и допълнение на Наказателно-процесуалния кодекс",
        "Народно събрание",
        "nakazatelno-protsesualen-kodeks",
    ),
    (
        "Закон за изменение и допълнение на Валутния закон",
        "Народно събрание",
        "valuten-zakon",
    ),
    (
        "Поправка в Закона за обществения транспорт",
        "Народно събрание",
        "zakon-za-obshtestveniya-transport",
    ),
    (
        "ЗАКОН ЗА ОБЩЕСТВЕНИЯ ТРАНСПОРТ",
        "Народно събрание",
        "zakon-za-obshtestveniya-transport",
    ),
    (
        "Закон за изменение и допълнение на Закона за счетоводството",
        "Народно събрание",
        "zakon-za-schetovodstvoto",
    ),
    # A budget law: the year in the title is what tells two of them apart.
    (
        "Закон за държавния бюджет на Република България за 2025 г.",
        "Народно събрание",
        "zakon-za-darzhavniya-byudzhet-na-republika-balgariya-za-2025-g",
    ),
    # --- numbered наредби, including the letter and dash forms ---
    (
        "Наредба № 8121з-1006 от 24 август 2015 г. за реда за осъществяване на "
        "пожарогасителната и спасителната дейност",
        "Министерство на вътрешните работи",
        "naredba-8121z-1006-ot-24-avgust-2015-g-za-reda-za-osashtestvyavane-na-pozharogas",
    ),
    (
        "Наредба № РД-02-21-1 от 23 ноември 2023 г. за сигнализация на пътищата с "
        "пътни знаци",
        "Министерство на регионалното развитие и благоустройството",
        "naredba-rd-02-21-1-ot-23-noemvri-2023-g-za-signalizatsiya-na-patishtata-s-patni-",
    ),
    (
        # Latin I where the corpus writes Cyrillic І.
        "Наредба № I-3 от 13 ноември 2015 г. за специфичните изисквания, условията "
        "и реда за постъпване на държавна служба",
        "Министерство на вътрешните работи",
        "naredba-3-ot-13-noemvri-2015-g-za-spetsifichnite-iziskvaniya-usloviyata-i-reda-z",
    ),
    (
        "Наредба № Н-10 от 23 ноември 2018 г. за условията и реда за уведомяване на "
        "министъра",
        "Министерство на финансите",
        "naredba-n-10-ot-23-noemvri-2018-g-za-usloviyata-i-reda-za-uvedomyavane-na-minist",
    ),
    # --- must not resolve ---
    (
        "Закон за ратифициране на Споразумението за предоставяне на безвъзмездна "
        "финансова помощ между Министерството на външните работи на Република "
        "България и Международната организация на франкофонията",
        "Народно събрание",
        None,
    ),
    (
        # Three corpus acts carry this exact title.
        "Закон за амнистия от 1989 г.",
        "Народно събрание",
        None,
    ),
    (
        # A budget law for a year the corpus does not hold.
        "Закон за държавния бюджет на Република България за 1997 г.",
        "Народно събрание",
        None,
    ),
    ("", "Народно събрание", None),
]


@pytest.mark.parametrize("title, section, expected", CASES)
def test_resolve(resolver, title, section, expected):
    result = resolver.resolve(title, section=section)
    assert result.law_id == expected, (
        f"{title[:70]!r} -> {result.law_id!r} "
        f"({result.method}, {result.score:.3f}, {result.flags}, "
        f"candidates={result.candidates[:4]})"
    )


def test_every_case_that_resolves_names_a_corpus_act(resolver, corpus_acts):
    known = {act.law_id for act in corpus_acts}
    for title, section, expected in CASES:
        if expected is not None:
            assert expected in known


# --- never guessing -------------------------------------------------------


def test_two_candidates_give_nothing_and_say_why(resolver):
    result = resolver.resolve("Закон за амнистия от 1989 г.", section="Народно събрание")
    assert result.law_id is None
    assert "title_ambiguous" in result.flags
    assert len(result.candidates) == 3


def test_the_promulgation_citation_breaks_the_tie(resolver):
    # The three amnesty laws of 1989 differ only by their issue: 37, 91
    # and 99. A ЗИД citing one of them is not ambiguous.
    result = resolver.resolve(
        "Закон за амнистия от 1989 г.",
        section="Народно събрание",
        dv_citation="ДВ, бр. 99 от 1989 г.",
    )
    assert result.law_id == "zakon-za-amnistiya-ot-1989-g-3"
    assert "disambiguated_by_citation" in result.flags


def test_a_citation_that_matches_none_of_the_candidates_resolves_nothing(resolver):
    result = resolver.resolve(
        "Закон за амнистия от 1989 г.",
        section="Народно събрание",
        dv_citation="ДВ, бр. 5 от 1989 г.",
    )
    assert result.law_id is None
    assert "title_ambiguous" in result.flags


def test_an_empty_title_is_flagged_rather_than_matched(resolver):
    # Seven corpus acts have no `titulo` at all and go to unresolved.csv
    # for this reason; an untitled Gazette material is the same problem
    # from the other side.
    result = resolver.resolve("   ", section="Народно събрание")
    assert result.law_id is None
    assert "empty_title" in result.flags


def test_an_act_type_the_corpus_does_not_hold_is_named_as_such(resolver):
    result = resolver.resolve(
        "Постановление № 74 на Министерския съвет от 2015 г. за създаване на "
        "Национален икономически съвет",
        section="Министерски съвет",
    )
    assert result.law_id is None
    assert "act_type_not_in_corpus" in result.flags


def test_no_candidate_is_distinguished_from_too_many(resolver):
    nothing = resolver.resolve(
        "Закон за нещо съвсем измислено и несъществуващо",
        section="Народно събрание",
    )
    assert nothing.law_id is None
    assert "no_candidate" in nothing.flags
    assert nothing.candidates == ()

    many = resolver.resolve("Закон за амнистия от 1989 г.", section="Народно събрание")
    assert "ambiguous_candidates" in many.flags


# --- the section gate -----------------------------------------------------


def test_the_section_gates_the_numbered_key(resolver):
    # A „Наредба № 2 от 2001 г.“ cannot be a material of Народно събрание,
    # which issues закони and кодекси. Without the gate the number would
    # be looked up in the whole corpus.
    citation = "Наредба № 2 от 2001 г. за сигнализация на пътищата с пътна маркировка"
    assert resolver.resolve(citation, section="Народно събрание").law_id is None
    assert (
        resolver.resolve(
            citation, section="Министерство на регионалното развитие"
        ).law_id
        == "naredba-2-ot-17-yanuari-2001-g-za-signalizatsiya-na-patishtata-s-patna-markirovk"
    )


def test_without_a_section_nothing_is_gated(resolver):
    assert (
        resolver.resolve(
            "Наредба № 2 от 2001 г. за сигнализация на пътищата с пътна маркировка"
        ).law_id
        == "naredba-2-ot-17-yanuari-2001-g-za-signalizatsiya-na-patishtata-s-patna-markirovk"
    )


# --- the fuzzy step is bounded -------------------------------------------


def test_the_digit_guard_keeps_the_annual_laws_apart(resolver):
    # „...за 2025 г.“ and „...за 2026 г.“ differ by one character in
    # sixty and score 0.98 against each other. Numbers in a legal title
    # identify the act, so a fuzzy match may not cross them.
    result = resolver.resolve(
        "Закон за държавния бюджет на Република България за 2024 г.",
        section="Народно събрание",
    )
    assert result.law_id is None


def test_a_fuzzy_resolution_reports_its_score(resolver):
    result = resolver.resolve(
        "Закон за изменение и допълнение на Семейния кодекс", section="Народно събрание"
    )
    assert result.law_id == "semeen-kodeks"
    # The de-articling makes this an exact hit rather than a guess.
    assert result.method == "exact"
    assert result.score == 1.0


def test_the_corpus_loader_reads_the_chain(corpus_acts):
    by_id = {act.law_id: act for act in corpus_acts}
    kt = by_id["kodeks-na-truda"]
    assert kt.act_type == "кодекс"
    assert kt.dv_year == 1986
    assert kt.dv_issue == "26"
    assert (1986, 26) in kt.chain
    assert len(corpus_acts) == 3624


def test_a_corpus_act_can_be_built_without_the_tree():
    act = CorpusAct.from_frontmatter(
        law_id="x",
        category="laws",
        frontmatter={
            "titulo": "ЗАКОН ЗА НЕЩО",
            "rango": "закон",
            "dv_issue": "32",
            "dv_year": 2026,
            "fecha_publicacion": "2026-04-01",
            "amendment_history": [{"dv": "32/2026", "date": "2026-04-01"}],
        },
    )
    assert act.act_type == "закон"
    assert act.chain == frozenset({(2026, 32)})


def test_a_row_without_a_dv_reference_does_not_break_the_chain():
    act = CorpusAct.from_frontmatter(
        law_id="x",
        category="laws",
        frontmatter={
            "titulo": "ЗАКОН ЗА НЕЩО",
            "rango": "закон",
            "amendment_history": [{"date": "1998-01-01"}, {"dv": "не число/юли"}],
        },
    )
    assert act.chain == frozenset()


# --- the operative verb is the FIRST „за“, not any „за“ -------------------

EU_TITLE = (
    "НАРЕДБА № Н-1 ОТ 25 МАЙ 2022 Г. ЗА УСЛОВИЯТА И РЕДА ЗА ПОДАВАНЕ НА ДАННИ "
    "И ИНФОРМАЦИЯ В ПОРТАЛА НА ЕВРОПЕЙСКИЯ СЪЮЗ (ЕС) ПО ЧЛ. 80, И ЗА ОТМЯНА НА "
    "ДИРЕКТИВА 2001/20/ЕО"
)


def test_a_subject_clause_that_mentions_a_repeal_is_not_a_repeal():
    # This наредба promulgates itself. Deep inside its own subject it says
    # what the EU directive it implements repealed. Reading „ЗА ОТМЯНА НА“
    # there as this material's operative verb turns a promulgation into a
    # repeal of Directive 2001/20/ЕО and files an `estado` dispute against
    # an act nobody repealed.
    from fetcher.dv.resolver import instruction_kind

    assert instruction_kind(EU_TITLE) == "promulgation"


def test_a_subject_clause_that_mentions_a_repeal_keeps_its_whole_title():
    # The same defect from the matching side: the prefix strip took
    # „ДИРЕКТИВА 2001/20/ЕО“ as the act being named and threw the наредба's
    # own name away.
    assert normalise_title(EU_TITLE).startswith("наредба № н-1 от 25 май 2022 г")
    assert strip_amending_prefix(EU_TITLE) == EU_TITLE


@pytest.mark.parametrize(
    "title, kind",
    [
        ("Закон за изменение и допълнение на Кодекса на труда", "amending"),
        ("Закон за изменение на Наказателния кодекс", "amending"),
        ("Закон за допълнение на Търговския закон", "amending"),
        ("Закон за отмяна на Закона за счетоводството", "repeal"),
        ("Закон за отменяне на Закона за счетоводството", "repeal"),
        ("Поправка в Закона за счетоводството", "corrigendum"),
        (
            "Постановление № 235 от 13 септември 2016 г. за приемане на Правилник "
            "за прилагане на Закона за електронната идентификация",
            "adopting",
        ),
        ("ЗАКОН ЗА ОБЩЕСТВЕНИЯ ТРАНСПОРТ", "promulgation"),
        # „ратифициране“ is not an operative verb over a corpus act.
        ("Закон за ратифициране на Споразумението за нещо", "promulgation"),
        # The subject clause opens at the first „за“ and closes the door.
        (
            "Закон за тълкуване на чл. 47 от Закона за чужденците в Република "
            "България",
            "promulgation",
        ),
        (
            "НАРЕДБА ЗА УСЛОВИЯТА И РЕДА ЗА ИЗМЕНЕНИЕ НА ПЛАНОВЕТЕ",
            "promulgation",
        ),
        ("", "promulgation"),
    ],
)
def test_instruction_kind(title, kind):
    from fetcher.dv.resolver import instruction_kind

    assert instruction_kind(title) == kind


# --- a retargeting instruction names an ACT -------------------------------

ADOPTS_A_METHODOLOGY = (
    "НАРЕДБА № 1 ОТ 1 ЮЛИ 2016 Г. ЗА ОДОБРЯВАНЕ НА МЕТОДИКА ЗА ПРИЛАГАНЕ НА "
    "ИЗКЛЮЧЕНИЯТА ПО ЧЛ. 156Б ОТ ЗАКОНА ЗА ВОДИТЕ"
)
REPEALS_UNNAMED_ACTS = (
    "НАРЕДБА № 18 ОТ 6 СЕПТЕМВРИ 1996 Г. ЗА ОТМЯНА НА НОРМАТИВНИ АКТОВЕ"
)
ADOPTS_A_DECLARATION = (
    "ЗАКОН ЗА ПРИЕМАНЕ НА ДЕКЛАРАЦИЯ ПО ЧЛ. 287, АЛ. 1 ОТ КОНВЕНЦИЯТА НА "
    "ОРГАНИЗАЦИЯТА НА ОБЕДИНЕНИТЕ НАЦИИ ПО МОРСКО ПРАВО"
)


@pytest.mark.parametrize(
    "title", [ADOPTS_A_METHODOLOGY, REPEALS_UNNAMED_ACTS, ADOPTS_A_DECLARATION]
)
def test_an_operative_verb_over_something_that_is_not_an_act_strips_nothing(title):
    # These are the acts' own subjects, not instructions about other acts.
    # Stripping „ЗА ОДОБРЯВАНЕ НА“ throws away the наредба's own name and
    # its number with it, so a citation „Наредба № 1 от 2016 г.“ can never
    # reach it again: 95 numbered corpus acts were in that position.
    from fetcher.dv.resolver import instruction_kind

    assert strip_amending_prefix(title) == title
    assert instruction_kind(title) == "promulgation"


def test_a_numbered_act_keeps_its_number_through_its_own_subject():
    assert numbered_key(ADOPTS_A_METHODOLOGY) == NumberedKey("наредба", "1", 2016)
    assert numbered_key(REPEALS_UNNAMED_ACTS) == NumberedKey("наредба", "18", 1996)


def test_an_instruction_that_does_name_an_act_still_strips():
    # The act type may be the first word, or hide behind one or two
    # adjectives („Устройствения правилник“, „Данъчно-осигурителния
    # процесуален кодекс“), so the whole opening of the name is read.
    for title, target in [
        ("Закон за отмяна на Закона за счетоводството", "закон за счетоводството"),
        (
            "Постановление № 236 от 2016 г. за изменение на Устройствения правилник "
            "на Министерството на финансите",
            "устройствения правилник на министерството на финансите",
        ),
        (
            "Закон за изменение на Данъчно-осигурителния процесуален кодекс",
            "данъчно-осигурителния процесуален кодекс",
        ),
        (
            "Постановление № 235 от 2016 г. за приемане на Правилник за прилагане "
            "на Закона за електронната идентификация",
            "правилник за прилагане на закона за електронната идентификация",
        ),
    ]:
        assert normalise_title(title) == target


def test_every_numbered_corpus_act_has_a_numbered_key(corpus_acts):
    # The numbered key is the only way a citation „Наредба № N от YYYY г.“
    # reaches a наредба, so an act whose title carries a number and whose
    # key is None is unreachable by that route.
    missing = [
        act.law_id
        for act in corpus_acts
        if act.title.startswith(("НАРЕДБА № ", "ПРАВИЛНИК № ", "ИНСТРУКЦИЯ № "))
        and numbered_key(act.title) is None
    ]
    assert missing == []


# --- C1: a content word apart is a different act -------------------------

# Real minimal pairs from the corpus. Each is two acts whose titles share
# a frame and differ in one noun, which is what наредби and правилници
# are built like: 88 % of the corpus is not laws and codes, and that is
# where the fuzzy step meets its hardest cases.
MINIMAL_PAIRS = [
    (
        "ПРАВИЛНИК ЗА УСТРОЙСТВОТО И ДЕЙНОСТТА НА ДЪРЖАВНИТЕ ГОРСКИ СТОПАНСТВА",
        "pravilnik-za-ustroystvoto-i-deynostta-na-darzhavnite-lovni-stopanstva",
    ),
    (
        "ПРАВИЛНИК ЗА ОРГАНИЗАЦИЯТА И ДЕЙНОСТТА НА ВЕЛИКОТО НАРОДНО СЪБРАНИЕ",
        "pravilnik-za-organizatsiyata-i-deynostta-na-narodnoto-sabranie",
    ),
    (
        "ЗАКОН ЗА ВЪЗСТАНОВЯВАНЕ НА СОБСТВЕНОСТТА ВЪРХУ ГОРИТЕ И ЗЕМИТЕ ОТ "
        "РИБНИЯ ФОНД",
        "zakon-za-vazstanovyavane-na-sobstvenostta-varhu-gorite-i-zemite-ot-gorskiya-fond",
    ),
    (
        "ЗАКОН ЗА ЕКСПОРТНИЯ КОНТРОЛ НА ПРОДУКТИ, СВЪРЗАНИ С ЕНЕРГЕТИКАТА",
        "zakon-za-eksportniya-kontrol-na-produkti-svarzani-s-otbranata-i-na-izdeliya-i-teh",
    ),
]


@pytest.mark.parametrize("title, sibling", MINIMAL_PAIRS)
def test_a_title_one_content_word_from_an_act_resolves_to_nothing(
    corpus_acts, title, sibling
):
    resolver = resolver_without(corpus_acts, title)
    # These score 0.91 to 0.95 and share every digit, so neither the floor
    # nor the digit guard sees them. A Gazette material naming an act the
    # corpus does not hold is the ordinary case across 42,000 materials,
    # and attributing it to the sibling one word away files a chain
    # omission, and possibly an `estado` repeal, against a live act.
    result = resolver.resolve(title)
    assert result.law_id is None, f"attributed to {result.law_id} at {result.score:.4f}"
    assert "title_ambiguous" in result.flags


def test_the_refusal_still_names_what_it_considered(corpus_acts):
    resolver = resolver_without(corpus_acts, MINIMAL_PAIRS[0][0])
    result = resolver.resolve(MINIMAL_PAIRS[0][0])
    assert result.law_id is None
    # The candidate is reported so `unresolved.csv` can show the reader
    # the same near miss the resolver saw.
    assert MINIMAL_PAIRS[0][1] in result.candidates


def test_the_fuzzy_step_still_absorbs_a_wording_difference(resolver):
    # What the fuzzy step is for after the guard: the same content words,
    # worded differently. Function words are not content words, so an
    # extra „за“ costs nothing.
    result = resolver.resolve(
        "Закон за задълженията и за договорите", section="Народно събрание"
    )
    assert result.law_id == "zakon-za-zadalzheniyata-i-dogovorite"
    assert result.method == "fuzzy"
    assert result.score >= 0.90


def test_a_typo_inside_a_content_word_is_refused(resolver):
    # The narrowing the guard buys, stated rather than hidden: a
    # one-letter defect inside a content word is indistinguishable from a
    # different act at the token level, so the resolver refuses instead of
    # guessing. The event becomes `unlocated` and `pending`, which blocks
    # a grade and writes nothing false.
    result = resolver.resolve(
        "Закон за изменение и допълнение на Закона за задължениата и договорите",
        section="Народно събрание",
    )
    assert result.law_id is None


# --- C2: the numbered key must not cross a stated year -------------------


def test_a_number_with_a_different_year_is_not_its_sibling(corpus_acts):
    # „НАРЕДБА № РД-07-7 ОТ 5 ОКТОМВРИ 2010 Г.“ is not in the corpus; the
    # 2019 наредба of the same number is. Falling back to „any act with
    # this number“ resolved the one to the other and reported 1.000.
    title = (
        "Наредба № РД-07-7 от 5 октомври 2010 г. за условията и реда за водене "
        "и съхраняване на регистри"
    )
    result = resolver_excluding(
        corpus_acts,
        "naredba-rd-07-7-ot-5-oktomvri-2010-g-za-usloviyata-i-reda-za-vodene-i-sahranyava",
    ).resolve(
        title,
        section="Министерство на труда и социалната политика",
    )
    assert result.law_id is None


def test_a_numbered_tie_reports_its_real_score_and_says_it_was_a_tie(resolver):
    # (наредба, 1, 2016) names six corpus acts. The subject clause after
    # the number and the date is what separates them, and the decision is
    # a comparison, not an exact key, so it may not report 1.000.
    result = resolver.resolve(
        "Наредба № 1 от 30 август 2016 г. за условията и реда за прием и спортна "
        "подготовка на учениците в спортните училища",
        section="Министерство на младежта и спорта",
    )
    assert result.law_id == (
        "naredba-1-ot-30-avgust-2016-g-za-usloviyata-i-reda-za-priem-i-spetsializirana-po"
    )
    assert result.method == "numbered"
    assert "numbered_key_tie" in result.flags
    assert 0.90 <= result.score < 1.0


def test_a_unique_numbered_key_is_not_a_tie(resolver):
    result = resolver.resolve(
        "Наредба № 8121з-1006 от 24 август 2015 г. за реда за осъществяване на "
        "пожарогасителната и спасителната дейност",
        section="Министерство на вътрешните работи",
    )
    assert result.method == "numbered"
    assert result.score == 1.0
    assert "numbered_key_tie" not in result.flags


def test_two_acts_of_one_number_whose_subjects_are_one_word_apart(resolver):
    # The reviewer's group of four: „в областта на ветеринарната биология“
    # is not in the corpus and must not become „ветеринарната медицина“.
    result = resolver.resolve(
        "Наредба № 6 от 11 февруари 2021 г. за реда и условията за придобиване "
        "на специалност в областта на ветеринарната биология",
        section="Министерство на земеделието",
    )
    assert result.law_id is None


# --- I2: the adoption tail is an adoption, not any relative clause -------

TRUNCATED_TITLES = [
    "ЗАКОН ЗА ОТМЕНЯВАНЕ НА ВСИЧКИ ЗАКОНИ, ИЗДАДЕНИ ПРЕДИ 9.09.1944 Г.",
    "ЗАКОН ЗА ОТТЕГЛЯНЕ НА РЕЗЕРВАТА, НАПРАВЕНА ОТ РЕПУБЛИКА БЪЛГАРИЯ ПО ЧЛ. 31 "
    "ОТ КОНВЕНЦИЯТА ЗА СТАТУТА НА ЛИЦАТА БЕЗ ГРАЖДАНСТВО, ПРИЕТА В НЮ ЙОРК НА "
    "28 СЕПТЕМВРИ 1954 Г.",
    "НАРЕДБА № 14 ОТ 22 АПРИЛ 1998 Г. ЗА УСЛОВИЯТА И РЕДА ЗА ПРЕДОСТАВЯНЕ НА "
    "СРЕДСТВА ЗА СЪЗДАВАНЕ, ОБНОВЯВАНЕ И ВЪЗПРОИЗВОДСТВО НА ГЕНОФОНД ОТ РИБИ",
    "НАРЕДБА № 20 ОТ 25 ОКТОМВРИ 2022 Г. ЗА РЕГИСТЪРА НА ИЗДАДЕНИТЕ "
    "УДОСТОВЕРЕНИЯ НА ЧУЖДЕНЦИ, ПРИЕТИ ЗА ОБУЧЕНИЕ В БЪЛГАРСКИ ВИСШИ УЧИЛИЩА",
    "НАРЕДБА № 4 ОТ 4 ФЕВРУАРИ 2025 Г. ЗА УТВЪРЖДАВАНЕ НА МЕЖДУНАРОДНИТЕ "
    "ОДИТОРСКИ СТАНДАРТИ, ИЗДАДЕНИ ОТ МЕЖДУНАРОДНАТА ФЕДЕРАЦИЯ НА СЧЕТОВОДИТЕЛИТЕ",
    "НАРЕДБА № 5 ОТ 4 ФЕВРУАРИ 2025 Г. ЗА УТВЪРЖДАВАНЕ НА РЪКОВОДСТВО ПО "
    "МЕЖДУНАРОДЕН ОДИТ, ИЗДАДЕНО ОТ МЕЖДУНАРОДНАТА ФЕДЕРАЦИЯ НА СЧЕТОВОДИТЕЛИТЕ",
    "НАРЕДБА ЗА ДОПЪЛНИТЕЛНИТЕ МЕРКИ, СВЪРЗАНИ С ПРИЛАГАНЕТО НА РЕГЛАМЕНТИ, "
    "ПРИЕТИ СЪГЛАСНО ЧЛ. 15 ОТ ДИРЕКТИВА 2009/125/ЕО",
    "НАРЕДБА ЗА РЕДА ЗА СЪЗДАВАНЕ, СЪХРАНЯВАНЕ, ОБНОВЯВАНЕ, ПОДДЪРЖАНЕ, "
    "ПРЕДОСТАВЯНЕ И ОТЧИТАНЕ НА ЗАПАСИТЕ ОТ ИНДИВИДУАЛНИ СРЕДСТВА ЗА ЗАЩИТА",
]


@pytest.mark.parametrize("title", TRUNCATED_TITLES)
def test_a_relative_clause_is_not_an_adoption_tail(title):
    # An adoption tail names the instrument that adopted the act, always
    # in the instrumental: „, приета С Постановление № 97“. „, издадени ОТ
    # Международната федерация“ names an author, „, приети СЪГЛАСНО чл.
    # 15“ a legal basis, and „, ОБНОВЯВАНЕ“ is not an abbreviation at all.
    # Cutting there threw away most of eight corpus titles, and two of
    # them lost every digit, which voids the digit guard for them.
    normalised = normalise_title(title)
    tail_words = normalise_title(title.split(",")[-1]).split()
    assert tail_words
    assert tail_words[-1] in normalised.split(), normalised


def test_a_real_adoption_tail_is_still_cut():
    assert normalise_title(
        "Постановление № 238 от 2016 г. за изменение на Наредбата за цените, "
        "приета с Постановление № 97 на Министерския съвет от 2013 г."
    ) == "наредба за цените"
    assert normalise_title(
        "Наредбата за нещо, обн. ДВ, бр. 12 от 2001 г."
    ) == "наредба за нещо"


def test_a_slash_inside_a_number_is_part_of_it():
    # „№ РД-07/2“ and „№ РД-07/8“ are two наредби of the Ministry of
    # Labour. Dropping the slash and everything after it folded both onto
    # „РД-07“ and let each resolve to the other.
    assert numbered_key("Наредба № РД-07/2 от 19 март 2008 г. за реда") == NumberedKey(
        "наредба", "РД-07/2", 2008
    )
    assert numbered_key("Наредба № РД-07/8 от 20 декември 2008 г. за нещо") == (
        NumberedKey("наредба", "РД-07/8", 2008)
    )


def test_a_slash_before_a_year_is_not_part_of_the_number():
    # „Наредба № 3/2001“ writes the year after the number rather than
    # inside it, so the slash separates rather than joins.
    assert numbered_key("Наредба № 3/2001 г. за нещо") == NumberedKey(
        "наредба", "3", 2001
    )


def test_a_stated_date_that_contradicts_the_only_candidate_refuses(corpus_acts):
    # „НАРЕДБА № Н-9 ОТ 7 НОЕМВРИ 2018 Г.“ and „НАРЕДБА № Н-9 ОТ 4 АПРИЛ
    # 2018 Г.“ are two acts. With the first held out, the key (наредба,
    # Н-9, 2018) names exactly one act, and returning it reported an
    # exact key at 1.000 for an act the citation does not describe: 230
    # held-out titles resolved this way.
    title = (
        "Наредба № Н-9 от 7 ноември 2018 г. за регистрите, водени от Агенция "
        "Митници"
    )
    result = resolver_excluding(
        corpus_acts, "naredba-n-9-ot-7-noemvri-2018-g-za-registrite-vodeni-ot-agentsiya-mitnitsi"
    ).resolve(title, section="Министерство на финансите")
    assert result.law_id is None
    assert "numbered_date_mismatch" in result.flags
    assert result.candidates


def test_a_corpus_act_that_states_no_date_is_not_contradicted(corpus_acts):
    # 365 numbered наредби state no date at all. Silence cannot
    # contradict a citation that states one.
    result = Resolver(corpus_acts).resolve(
        "Наредба № 0-31 от 12 март 1975 г. за работа с радиационни дефектоскопи"
    )
    assert result.law_id == "naredba-0-31-za-rabota-s-radiatsionni-defektoskopi"


# --- the measurement the bounds are justified by --------------------------


@pytest.mark.slow
def test_leave_one_out_over_the_whole_corpus_attributes_nothing_wrongly(corpus_acts):
    """Hold each title out and ask the rest of the corpus for it.

    This is what a Gazette material naming an act the corpus does not
    hold looks like, and across roughly 42,000 materials it is the
    ordinary case rather than the exception: repealed наредби, superseded
    устройствени правилници, acts not yet bootstrapped. The resolver's
    first rule is that it never guesses, so the count that matters is not
    how many titles it resolves but how many it resolves WRONGLY.

    Two acts may share a normalised title (the corpus holds eight such
    acts, mostly a правилник reissued under the same name), and holding
    one out leaves the other as the only exact match. That is a correct
    exact resolution to an identically titled act, not a guess.
    """
    resolver = Resolver(corpus_acts)
    twins = collections.Counter(
        normalise_title(act.title) for act in corpus_acts if act.title
    )
    wrong = []
    for held in corpus_acts:
        if not held.title:
            continue
        result = resolver.holding_out(held.law_id).resolve(held.title)
        if result.law_id is None:
            continue
        if twins[normalise_title(held.title)] > 1 and result.method == "exact":
            continue
        wrong.append((round(result.score, 4), result.method, held.title[:60],
                      result.law_id))
    assert wrong == []


@pytest.mark.slow
def test_a_reworded_title_still_resolves(corpus_acts):
    # The other side of the guard: what it must not cost. A function word
    # dropped is a wording difference, not a different act, and the fuzzy
    # step exists for exactly that.
    resolver = Resolver(corpus_acts)
    random.seed(11)
    hit = total = 0
    for act in corpus_acts:
        if not act.title:
            continue
        words = normalise_title(act.title).split()
        movable = [i for i, word in enumerate(words) if len(word) <= 2 and i > 0]
        if not movable:
            continue
        index = random.choice(movable)
        total += 1
        if resolver.resolve(" ".join(words[:index] + words[index + 1:])).law_id == (
            act.law_id
        ):
            hit += 1
    assert total > 3500
    assert hit / total > 0.80
