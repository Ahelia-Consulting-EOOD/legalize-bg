"""The material parser (reading/material.py): the skeleton of a Gazette material, read mechanically."""
from reading import material as M
from reading.splitter import Block, SplitAct


def _act(lines, hints=None):
    hints = hints or {}
    return SplitAct(blocks=[Block(i, t, hints.get(i, "DvJustify")) for i, t in enumerate(lines)], sections=[], source="dv")


LAW = [
    "УКАЗ № 324", "На основание чл. 98, т. 4 от Конституцията на Република България", "ПОСТАНОВЯВАМ:",
    "Да се обнародва в „Държавен вестник“ Законът за изменение и допълнение на Закона за частната охранителна дейност, приет от 52-рото Народно събрание на 7 октомври 2026 г.",
    "Издаден в София на 16 октомври 2026 г.", "Президент на Републиката: Илияна Йотова", "Подпечатан с държавния печат.", "Министър на правосъдието: Николай Найденов",
    "ЗАКОН", "за изменение и допълнение на Закона за частната охранителна дейност", "(обн., ДВ, бр. 10 от 2018 г.; изм., бр. 27 и 92 от 2018 г., бр. 13 и 17 от 2019 г.)",
    "§ 1. В чл. 4 се създава ал. 4:", "„(4) За издаване на удостоверение се събира държавна такса в размер, определен с тарифата по чл. 44, ал. 5.“",
    "§ 2. В чл. 5, ал. 1 т. 5 и 9 се отменят.",
    "§ 3. В чл. 36 се правят следните изменения:", "1. В ал. 1 думите „до 30 000 лв.“ се заменят с „до 1 000 000 евро“.", "2. В ал. 2:",
    "а) точка 2 се изменя така:", "„2. нямат публични задължения;“", "б) точка 3 се отменя.",
    "§ 4. Член 37 се изменя така:", "„Чл. 37. (1) Ценните пратки се транспортират със специализирани автомобили клас „FB2“ по БДС EN 1522.",
    "(2) Пратките над 500 000 евро се транспортират с автомобили клас FB3.“",
    "Преходни и заключителни разпоредби",
    "§ 5. В Закона за движението по пътищата (обн., ДВ, бр. 20 от 1999 г.; изм., бр. 1 от 2000 г.) в чл. 100 се създава ал. 5:",
    "„(5) Текст.“",
    "§ 6. Законът влиза в сила от деня на обнародването му в „Държавен вестник“.",
    "Законът е приет от 52-рото Народно събрание на 7 октомври 2026 г. и е подпечатан с официалния печат на Народното събрание.",
    "Председател на Народното събрание: Михаела Доцова", "5534",
]
LAW_HINTS = {0: "DvCenter", 2: "DvCenter", 5: "DvRight", 6: "DvRight", 7: "DvRight", 8: "DvCenter", 9: "DvCenter", 10: "DvCenter", 23: "DvCenter", 28: "DvRight"}


def test_a_law_parses_into_header_instructions_quoted_text_and_tail():
    m = M.parse(_act(LAW, LAW_HINTS))
    assert m.kind == "law" and m.amending and m.instruction_kind == "amending"
    assert m.target_title == "Закона за частната охранителна дейност"
    assert m.cited_history["promulgation"] == [10, 2018] and m.cited_history["issues"][:3] == [[10, 2018], [27, 2018], [92, 2018]]
    assert m.header == list(range(0, 11)) and m.tail == [27, 28, 29]
    assert [n.id for n in m.nodes] == ["§1", "§2", "§3", "§4", "§5", "§6"]
    assert m.nodes[0].quoted == [12]
    assert [c.id for c in m.nodes[2].children] == ["§3.1", "§3.2"] and [c.id for c in m.nodes[2].children[1].children] == ["§3.2.а", "§3.2.б"]
    assert m.nodes[2].children[1].children[0].quoted == [18]
    assert m.nodes[2].children[0].inline_quotes == ["до 30 000 лв.", "до 1 000 000 евро"]
    assert m.nodes[3].quoted == [21, 22], "a quotation that runs over two blocks, with a nested quote inside"
    assert m.headings == [23] and m.nodes[4].section == "transitional_final" and m.nodes[3].section == "body"
    assert m.nodes[4].target == {"title": "Закона за движението по пътищата", "cite": "обн., ДВ, бр. 20 от 1999 г.; изм., бр. 1 от 2000 г.", "promulgation": [20, 1999],
                                 "issues": [[20, 1999], [1, 2000]], "repeal": False}
    assert sorted(m.roles) == list(range(len(LAW))) and "unplaced" not in m.roles.values()
    assert M.check(m) == [] and m.findings == []


def test_a_decree_amending_several_acts_names_a_target_per_sign_and_an_embedded_act_after_the_signatures():
    lines = ["ПОСТАНОВЛЕНИЕ № 188 ОТ 12 ОКТОМВРИ 2026 Г.", "за приемане на Устройствен правилник на Агенцията", "МИНИСТЕРСКИЯТ СЪВЕТ", "ПОСТАНОВИ:",
             "Чл. 1. Приема Устройствен правилник на Агенцията.", "Заключителни разпоредби",
             "§ 1. В Устройствения правилник на Българския институт по метрология, приет с Постановление № 109 на Министерския съвет от 2006 г. (обн., ДВ, бр. 38 от 2006 г.; изм., бр. 2 от 2007 г.), се правят следните изменения:",
             "1. В чл. 33 се създава ал. 6:", "„(6) Органът по назначаването може да възлага работа от разстояние.“",
             "§ 2. Постановлението влиза в сила от деня на обнародването му в „Държавен вестник“.",
             "Министър-председател: Румен Радев", "Главен секретар на Министерския съвет: Камелия Нейкова",
             "УСТРОЙСТВЕН ПРАВИЛНИК", "на Агенцията", "Глава първа", "ОБЩИ ПОЛОЖЕНИЯ", "Чл. 1. С правилника се определят дейността на Агенцията.", "5555"]
    m = M.parse(_act(lines, {0: "DvCenter", 1: "DvCenter", 2: "DvCenter", 3: "DvCenter", 5: "DvCenter", 10: "DvRight", 11: "DvRight", 12: "DvCenter", 13: "DvCenter", 14: "DvCenter", 15: "DvCenter"}))
    assert m.kind == "decree" and m.instruction_kind == "adopting" and not m.amending
    assert [n.id for n in m.nodes] == ["Чл.1", "§1", "§2"]
    assert m.nodes[1].target["title"].startswith("Устройствения правилник на Българския институт по метрология") and m.nodes[1].target["promulgation"] == [38, 2006]
    assert m.embedded == {"start": 12, "title": "УСТРОЙСТВЕН ПРАВИЛНИК"}
    assert [m.roles[k] for k in range(10, 18)] == ["tail", "tail", "embedded", "embedded", "embedded", "embedded", "embedded", "tail"]
    assert M.check(m) == []


def test_a_ministry_ordinance_with_the_history_on_the_title_line_and_the_old_quotation_marks():
    lines = ["МИНИСТЕРСТВО НА ВЪТРЕШНИТЕ РАБОТИ",
             "Наредба за изменение и допълнение на Наредба № 8121з-310 от 2014 г. за преназначаване на държавните служители (обн., ДВ, бр. 60 от 2014 г.; изм., бр. 87 от 2014 г.)",
             "§ 1. В чл. 3, т. 1 думите “заподозрян” и “уличен” се заличават.",
             "§ 2. Член 3 се изменя така:", "“Чл. 3. Държавният служител се преназначава по предложение на ръководителя.”",
             "Министър: Цветлин Йовчев", "8705"]
    m = M.parse(_act(lines, {0: "DvCenter", 1: "DvCenter", 5: "DvRight"}))
    assert m.kind == "ordinance" and m.amending and m.body_org == "МИНИСТЕРСТВО НА ВЪТРЕШНИТЕ РАБОТИ"
    assert m.target_title.startswith("Наредба № 8121з-310 от 2014 г.") and "(обн" not in m.target_title
    assert m.cited_history["promulgation"] == [60, 2014]
    assert m.nodes[0].inline_quotes == ["заподозрян", "уличен"] and m.nodes[1].quoted == [4]
    assert M.check(m) == []


def test_a_nested_quotation_closed_with_one_mark_ends_the_run_when_the_sequence_resumes():
    lines = ["ЗАКОН", "за изменение на Закона за пробата", "(обн., ДВ, бр. 1 от 2020 г.)",
             "§ 1. В приложение № 7 т. 3 се изменя така:",
             "„3. Ако сте длъжни да осигурите функция, добавете следното: „Можете също да се откажете.“",   # the Gazette closes two quotations with one mark
             "Преходни и заключителни разпоредби",
             "§ 2. Законът влиза в сила от 1 януари 2027 г.",
             "Законът е приет от 52-рото Народно събрание.", "Председател на Народното събрание: Михаела Доцова", "4984"]
    m = M.parse(_act(lines, {0: "DvCenter", 1: "DvCenter", 2: "DvCenter", 5: "DvCenter", 8: "DvRight"}))
    assert [n.id for n in m.nodes] == ["§1", "§2"] and m.nodes[0].quoted == [4] and m.roles[5] == "heading"
    assert m.findings == [] and M.check(m) == []


def test_quoted_new_signs_continue_a_run_their_numbers_do_not_resume():
    lines = ["ЗАКОН", "за изменение на Закона за пробата", "(обн., ДВ, бр. 1 от 2020 г.)",
             "§ 1. В допълнителните разпоредби се създават § 4а и 4б:",
             "„§ 4а. Заявленията се подават в центровете на Агенция „Автомобилна администрация“.",
             "§ 4б. Лицензите се връчват лично.“",
             "§ 2. Законът влиза в сила от 1 януари 2027 г.",
             "Законът е приет от 52-рото Народно събрание.", "Председател на Народното събрание: Михаела Доцова", "4984"]
    m = M.parse(_act(lines, {0: "DvCenter", 1: "DvCenter", 2: "DvCenter", 8: "DvRight"}))
    assert [n.id for n in m.nodes] == ["§1", "§2"] and m.nodes[0].quoted == [4, 5] and m.findings == []


def test_a_whole_act_and_a_court_decision_are_not_amending_and_a_whole_acts_blocks_carry_the_role_act():
    act = M.parse(_act(["НАРЕДБА № 33 от 6 октомври 2026 г.", "за извършване на услуги", "Глава първа", "ОБЩИ ПОЛОЖЕНИЯ", "Чл. 1. Тази наредба урежда.", "Министър: Иван Иванов", "5001"],
                       {0: "DvCenter", 1: "DvCenter", 2: "DvCenter", 3: "DvCenter", 5: "DvRight"}))
    assert act.kind == "ordinance" and not act.amending and act.nodes == [] and act.instruction_kind == "promulgation" and act.whole_act
    assert [act.roles[k] for k in range(7)] == ["header", "header", "act", "act", "act", "tail", "tail"]
    code = M.parse(_act(["СЕМЕЕН КОДЕКС", "Глава първа", "ОБЩИ ПОЛОЖЕНИЯ", "Чл. 1. Семейният кодекс урежда отношенията.", "Преходни и заключителни разпоредби",
                         "§ 17. В Закона за наследството (обн., ДВ, бр. 22 от 1949 г.; попр., бр. 41 от 1949 г.) чл. 5 се отменя.", "§ 18. Този кодекс влиза в сила от 1 октомври 2009 г.",
                         "Законът е приет от 40-то Народно събрание.", "Председател на Народното събрание: Георги Пирински", "8630"],
                        {0: "DvCenter", 1: "DvCenter", 2: "DvCenter", 4: "DvCenter", 8: "DvRight"}))
    assert code.whole_act and not code.amending and [n.id for n in code.nodes] == ["§17", "§18"] and code.nodes[0].target["title"] == "Закона за наследството"
    assert code.roles[3] == "act" and code.roles[5] == "instruction" and M.check(code) == []
    dec = M.parse(_act(["РЕШЕНИЕ № 15 от 8 октомври 2026 г.", "по конституционно дело № 16 от 2025 г.", "Конституционният съд в състав: председател: Павлина Панова, членове: Атанас Семов",
                        "Производството е по чл. 149, ал. 1, т. 2 от Конституцията.", "РЕШИ:", "Обявява за противоконституционен чл. 19в, ал. 1 от Закона за специалните разузнавателни средства (обн., ДВ, бр. 95 от 1997 г.).",
                        "Конституционни съдии: Атанас Семов", "5546"], {0: "DvCenter", 1: "DvCenter", 4: "DvCenter", 6: "DvRight"}))
    assert dec.kind == "decision" and not dec.amending


def test_parse_cited_history_reads_lists_of_issues():
    h = M.parse_cited_history("(обн., ДВ, бр. 105 от 2005 г.; изм., бр. 30, 33 и 34 от 2006 г., бр. 46 от 2007 г.)")
    assert h["promulgation"] == [105, 2005] and h["issues"] == [[105, 2005], [30, 2006], [33, 2006], [34, 2006], [46, 2007]]
    assert M.parse_cited_history("(ДВ, бр. 79 от 2021 г.)")["promulgation"] == [79, 2021]


def _simple(lines, hints=None):
    return M.parse(_act(lines, hints or {0: "DvCenter", 1: "DvCenter", 2: "DvCenter"}))


def test_a_quoted_numbered_list_is_not_read_as_instructions():
    # the review of 1 November 2026, B1 (material 246111): the quoted new alineas carry their own numbered list
    lines = ["ЗАКОН", "за изменение на Кодекса на труда", "(обн., ДВ, бр. 26 от 1986 г.)",
             "§ 1. В чл. 244 се правят следните изменения и допълнения:",
             "1. Алинея 3 се изменя така:",
             "„(3) Размерът се определя при отчитане на:",
             "1. покупателната способност;",
             "2. общото равнище на работните заплати;",
             "3. темпа на растеж.“",
             "2. Създават се ал. 4, 5 и 6:",
             "„(4) Четвърта.", "(5) Пета.", "(6) Шеста.“",
             "§ 2. Законът влиза в сила от 1 януари 2027 г.",
             "Законът е приет от 52-рото Народно събрание.", "Председател на Народното събрание: Х", "4984"]
    m = _simple(lines, {0: "DvCenter", 1: "DvCenter", 2: "DvCenter", 15: "DvRight"})
    ids = [n.id for n in m.instructions()]
    assert ids == ["§1", "§1.1", "§1.2", "§2"] and m.nodes[0].children[0].quoted == [5, 6, 7, 8] and m.nodes[0].children[1].quoted == [10, 11, 12]
    assert M.check(m) == [] and M.sequence_problems(m) == []
    # a block that itself closes the run never resumes the instructions (246592: „2. оценка …;“.)
    lines2 = ["ЗАКОН", "за изменение на Закона за пробата", "(обн., ДВ, бр. 1 от 2020 г.)",
              "§ 1. В чл. 3 се правят следните изменения:", "1. Точка 1 се изменя така:", "„1. анализ;", "2. оценка.“", "2. Точка 4 се отменя.",
              "Законът е приет.", "Председател на Народното събрание: Х", "1"]
    m2 = _simple(lines2, {0: "DvCenter", 1: "DvCenter", 2: "DvCenter", 9: "DvRight"})
    assert [n.id for n in m2.instructions()] == ["§1", "§1.1", "§1.2"] and m2.nodes[0].children[0].quoted == [5, 6]


def test_duplicate_ids_and_sequence_breaks_are_findings_of_the_check():
    lines = ["ЗАКОН", "за изменение на Закона за пробата", "(обн., ДВ, бр. 1 от 2020 г.)",
             "§ 1. В чл. 3 се правят следните изменения:", "1. Точка 1 се отменя.", "3. Точка 4 се отменя.", "§ 1. Повторен параграф.",
             "Законът е приет.", "Председател на Народното събрание: Х", "1"]
    m = _simple(lines, {0: "DvCenter", 1: "DvCenter", 2: "DvCenter", 8: "DvRight"})
    problems = M.check(m)
    assert any("item 3 after 1 under §1" in p for p in problems) and any("instruction id §1 already" in p for p in problems)


def test_cross_act_citations_in_every_form_the_materials_use():
    cases = {
        "В чл. 30, т. 9 от Устройствения правилник на Министерството на финансите (обн., ДВ, бр. 100 от 2016 г.) думите „а“ се заменят с „б“.": "Устройствения правилник на Министерството на финансите",
        "В § 21 от преходните и заключителните разпоредби на Закона за горите (обн., ДВ, бр. 19 от 2011 г.) думите „а“ се заличават.": "Закона за горите",
        "Законът за предоставяне на финансови услуги от разстояние (обн., ДВ, бр. 105 от 2006 г.) се отменя.": "Законът за предоставяне на финансови услуги от разстояние",
        "Отменя се Наредба № 3 от 2005 г. за реда за водене (ДВ, бр. 45 от 30.04.2005 г.).": "Наредба № 3 от 2005 г. за реда за водене",
        "Навсякъде в Наредбата за пробата (обн., ДВ, бр. 1 от 2020 г.) думите „а“ се заменят с „б“.": "Наредбата за пробата",
        "В Семейния кодекс (обн., ДВ, бр. 47 от 2009 г.) в чл. 5 думите „а“ се заменят с „б“.": "Семейния кодекс",
        "В Закона за защита (ЕС) на данните (обн., ДВ, бр. 1 от 2019 г.) чл. 2 се отменя.": "Закона за защита (ЕС) на данните",
        "В Постановление № 266 на Министерския съвет от 2009 г. за приемане на Устройствен правилник на Министерството на труда (обн., ДВ, бр. 91 от 2009 г.) в приложението числото „650“ се заменя с „600“.":
            "Постановление № 266 на Министерския съвет от 2009 г. за приемане на Устройствен правилник на Министерството на труда",
    }
    for text, title in cases.items():
        t = M._target(text)
        assert t and t["title"] == title, (text, t)
    assert M._target("Законът за предоставяне на финансови услуги от разстояние (обн., ДВ, бр. 105 от 2006 г.) се отменя.")["repeal"]
    assert M._target("Отменя се Наредба № 3 от 2005 г. за реда (ДВ, бр. 45 от 30.04.2005 г.).")["promulgation"] == [45, 2005]
    assert M._target("Постановлението се приема на основание чл. 5 от Закона за пробата (обн., ДВ, бр. 1 от 2019 г.).") is None
    assert M._target("В чл. 62г думите „Наредба № 1 от 2010 г. за правилата (ДВ, бр. 7 от 2010 г.)“ се заменят с „б“.") is None
    assert M._target("В нещо неясно (обн., ДВ, бр. 1 от 2019 г.) се заличава.")["unread_title"]


def test_an_annex_after_the_signatures_and_the_decrees_formula():
    law = ["ЗАКОН", "за изменение на Закона за пробата", "(обн., ДВ, бр. 1 от 2020 г.)", "§ 1. Създава се приложение към § 2.",
           "Законът е приет от 52-рото Народно събрание.", "Председател на Народното събрание: Х", "Приложение към § 2", "ред първи", "ред втори", "4984"]
    m = _simple(law, {0: "DvCenter", 1: "DvCenter", 2: "DvCenter", 5: "DvRight", 6: "DvRight"})
    assert [m.roles[k] for k in range(4, 10)] == ["tail", "tail", "annex", "annex", "annex", "tail"] and m.embedded is None
    assert [f["kind"] for f in m.findings] == ["annex_after_signature"]
    whole = ["ЗАКОН", "за пробата", "Глава първа", "Чл. 1. Текст.", "Преходни и заключителни разпоредби", "§ 1. Законът влиза в сила от 1 януари 2027 г.",
             "Законът е приет от 52-рото Народно събрание.", "Председател на Народното събрание: Х", "Приложение № 1 към чл. 1", "ред", "4984"]
    w = _simple(whole, {0: "DvCenter", 1: "DvCenter", 2: "DvCenter", 4: "DvCenter", 7: "DvRight", 8: "DvRight"})
    assert w.whole_act and [w.roles[k] for k in range(6, 11)] == ["tail", "tail", "act", "act", "tail"] and w.findings == []
    decree = ["ПОСТАНОВЛЕНИЕ № 179 ОТ 8 ОКТОМВРИ 2026 Г.", "за допълнение на Постановление № 181 на Министерския съвет от 2009 г.", "МИНИСТЕРСКИЯТ СЪВЕТ", "ПОСТАНОВИ:",
              "§ 1. В чл. 1 се създава ал. 3:", "„(3) Текст.“", "Министър-председател: Румен Радев", "5000"]
    d = _simple(decree, {0: "DvCenter", 1: "DvCenter", 2: "DvCenter", 3: "DvCenter", 6: "DvRight"})
    assert "ПОСТАНОВИ" not in d.own_title and d.target_title == "Постановление № 181 на Министерския съвет от 2009 г."


def test_a_heading_inside_a_quotation_does_not_end_a_whole_acts_provisions():
    code = ["КОДЕКС", "на пробата", "Глава първа", "Чл. 1. Текст.", "Преходни и заключителни разпоредби",
            "§ 1. В Закона за горите (обн., ДВ, бр. 19 от 2011 г.) се създава глава осма:", "„Глава осма", "Допълнителна разпоредба", "§ 1. Нов параграф.“",
            "§ 2. Кодексът влиза в сила от 1 януари 2027 г.", "Законът е приет.", "Председател на Народното събрание: Х", "1"]
    m = _simple(code, {0: "DvCenter", 1: "DvCenter", 2: "DvCenter", 4: "DvCenter", 6: "DvCenter", 7: "DvCenter", 11: "DvRight"})
    assert m.whole_act and [n.id for n in m.nodes] == ["§1", "§2"] and m.nodes[0].quoted == [6, 7, 8] and m.nodes[0].target["title"] == "Закона за горите"


def test_cited_issues_in_the_dated_and_slashed_forms():
    assert M.parse_cited_history("(обн., ДВ, бр. 45 от 30.04.2002 г.; изм., бр. 10 от 2005 г.)")["promulgation"] == [45, 2002]
    assert M.parse_cited_history("(ДВ, бр. 45/2002)")["issues"] == [[45, 2002]]
    assert M.parse_cited_history("(обн., ДВ, бр. 45 от незнайна дата)").get("unread") is True
