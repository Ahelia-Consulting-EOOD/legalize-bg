"""Reading the Gazette's section string.

Two consumers depend on this: the body sweep, which reads only the
sections that issue corpus acts, and the act-name resolver, which gates
a numbered citation's act type by the section it was published under.
The strings below are the real ones, taken from the contents page of
брой 74 от 2016 (idObj 6121).
"""

import pytest

from fetcher.dv.sections import COUNCIL, MINISTRY, OTHER, PARLIAMENT, section_kind, selected


@pytest.mark.parametrize(
    "section, kind",
    [
        ("Народно събрание", PARLIAMENT),
        ("Министерски съвет", COUNCIL),
        ("Министерство на здравеопазването", MINISTRY),
        ("Министерство на младежта и спорта", MINISTRY),
        (
            "Министерство на регионалното развитие и благоустройството, "
            "Министерство на вътрешните работи, Министерство на транспорта, "
            "информационните технологии и съобщенията",
            MINISTRY,
        ),
        # The material page prints its section path in capitals.
        ("Официален раздел / МИНИСТЕРСТВА И ДРУГИ ВЕДОМСТВА", MINISTRY),
        ("Комисия за регулиране на съобщенията", OTHER),
        ("Централна избирателна комисия", OTHER),
        ("Конституционен съд", OTHER),
        ("Върховен административен съд", OTHER),
        ("Национална здравноосигурителна каса", OTHER),
        ("", OTHER),
        (None, OTHER),
    ],
)
def test_section_kind(section, kind):
    assert section_kind(section) == kind


def test_the_council_is_not_read_as_a_ministry():
    # „Министерски съвет“ issues постановления and the наредби and
    # правилници adopted by decree; a ministry issues наредби and
    # инструкции. Collapsing the two would let a numbered citation
    # resolve to the wrong act type.
    assert section_kind("Министерски съвет") != MINISTRY


def test_extra_sections_widen_and_never_narrow():
    assert selected("Народно събрание", ("Централна избирателна комисия",))
    assert selected("Централна избирателна комисия", ("Централна избирателна комисия",))
    assert not selected("Централна избирателна комисия", ("Конституционен съд",))
    assert selected("Конституционен съд", ("all",))
    assert not selected("Конституционен съд", ())
    assert not selected("Конституционен съд", ("  ",))
