# Investigate: are these acts, promulgated before 1989, still in force?

You investigate acts of the legalize-bg corpus that were promulgated before the Gazette's online archive begins
(1989), so no Gazette material of theirs can be read. For each act below you are given the facts the corpus holds
about it (lex.bg's witness: its title, kind, publication date, lex.bg's in-force status, its amendment history as
lex.bg records it) and the candidate repeal titles: Gazette materials from 2003 on whose title repeals an act and
that share words with this act's title. Decide from these facts alone, for each act, whether it is still in force:
`repealed` only when a candidate title names this very act (the same act, not a same-titled predecessor or a
different act whose title shares words), with that candidate's material id; `in_force` when no candidate names it
and lex.bg's record gives no sign of repeal; `unknown` when the facts do not settle it (a candidate may name it but
the title is ambiguous, or lex.bg's record contradicts the titles). A later amendment in lex.bg's history after a
candidate repeal is evidence against that repeal. Read only this file. Write exactly one file, the answer file
named below, in the form given, with every slug of this task and an evidence note for each; write nothing else, and
reply with one line: the answer file's path.

The answer file: `/Users/ekimir/swprj/legalize-bg/.claude/worktrees/unruffled-feynman-cd9070/data/runs/act-profiles-2026-10-31/calls/call-10-answer.yaml`

```yaml
# One YAML document: a mapping from each act's slug (every slug of the task, no other) to its verdict
<slug>:
  verdict: <in_force | repealed | unknown>
  repealed_by: <the material id of the candidate repeal title, only when the verdict is repealed; otherwise null>
  evidence: <the facts and lines you relied on, in one or two sentences>
```

## pravilnik-za-rabotata-na-uveselitelnite-zabavi-i-igri-za-razvlechenie-patuvashti
- title: ПРАВИЛНИК ЗА РАБОТАТА НА УВЕСЕЛИТЕЛНИТЕ ЗАБАВИ И ИГРИ ЗА РАЗВЛЕЧЕНИЕ, ПЪТУВАЩИ ЕСТРАДНО-ЦИРКОВИ ТРУПИ, ИЛЮЗИОНИСТИ И ДР., ОРГАНИЗИРАНИ ОТ ДИРЕКЦИЯТА НА БЪЛГАРСКИТЕ ЦИРКОВЕ
- kind: правилник; published 1969-05-27; lex.bg records it vigente with 3 amendment rows, the last: ДВ 41/1969 (1969-05-27); ДВ 56/1971 (1971-07-16); ДВ 62/1972 (1972-08-08)
- candidate repeal titles: none share words with this title

## pravilnik-za-reda-v-koraboplavaneto-po-vatreshnite-vodi-v-narodna-republika-balg
- title: ПРАВИЛНИК ЗА РЕДА В КОРАБОПЛАВАНЕТО ПО ВЪТРЕШНИТЕ ВОДИ В НАРОДНА РЕПУБЛИКА БЪЛГАРИЯ
- kind: правилник; published 1967-05-16; lex.bg records it vigente with 1 amendment rows, the last: ДВ 38/1967 (1967-05-16)
- candidate repeal titles:
  - material 18034, ДВ 113/2004 (2004-12-28): Наредба за отмяна на Наредба № 12 от 1993 г. за реда и начина за внос на азбест и азбестосъдържащи материали на територията на Република България [shared words: българия, реда, република]
  - material 111423, ДВ 9/2017 (2017-01-26): Наредба за отменяне на Наредба № 2 от 2002 г. за условията и реда за издаване на разрешения за извършване на дейност на свободна практика от чужденци в Република България [shared words: българия, реда, република]
  - material 127722, ДВ 53/2018 (2018-06-26): Постановление № 105 от 21 юни 2018 г. за отменяне на Наредбата за реда за лицензиране на спортните организации в Република България, приета с Постановление № 237 на Министерския съвет от 2008 г. [shared words: българия, реда, република]
  - material 137725, ДВ 42/2019 (2019-05-28): Наредба за отменяне на Наредба № 6 от 2018 г. за реда за лицензиране на спортните организации в Република България [shared words: българия, реда, република]
  - material 143534, ДВ 97/2019 (2019-12-10): Постановление № 317 от 5 декември 2019 г. за отменяне на Наредбата за реда и начина за определяне в Патентното ведомство на марка като общественоизвестна и марка, ползваща се с известност на територията на Република България, приета с Постановление № 229 на Министерския съвет от 2007 г. [shared words: българия, реда, република]
  - material 158913, ДВ 51/2021 (2021-06-18): Наредба за отменяне на Наредба № 1 от 2013 г. за реда и начина за идентификация и регистрация на участниците, съхраняването на данни за организираните онлайн залагания на територията на Република България и за подаване на информация за хазартните игри към сървър на Държавната комисия по хазарта и Националната агенция за приходите [shared words: българия, реда, република]
  - material 180849, ДВ 97/2022 (2022-12-06): Наредба за отменяне на Наредба № I-13 от 19 януари 2005 г. за охраната на речния участък от държавната граница и вътрешните водни пътища на Република България [shared words: българия, вътрешните, република]
  - material 190521, ДВ 36/2023 (2023-04-21): Инструкция за отменяне на Инструкция № Iз-1707 от 7 ноември 2007 г. за взаимодействие между Министерството на вътрешните работи и Държавната агенция по горите при опазването на горите, дивеча и рибата в обектите за любителски риболов на територията на Република България [shared words: българия, вътрешните, република]
  - material 8162, ДВ 75/2008 (2008-08-26): Наредба за отменяне на Наредба № Iз-441 от 2008 г. за определяне на категориите служители, осъществяващи правомощията си в униформено облекло, неговия вид и модел, реда за предоставянето му, както и другите принадлежности, свързани с изпълнението на служебните задължения на служителите, върху които са поставени символи и отличителни знаци на структурните звена на Министерството на вътрешните работи [shared words: вътрешните, реда]
  - material 20903, ДВ 41/2009 (2009-06-02): Наредба за отмяна на Наредба № 26 от 2006 г. за временно упражняване на медицински дейности в Република България за граждани на държава - членка на Европейския съюз, и другите държави от Европейското икономическо пространство [shared words: българия, република]
  - material 21361, ДВ 25/2004 (2004-03-26): Постановление № 60 от 16 март 2004 г. за отменяне на Постановление № 15 на Министерския съвет от 2002 г. за изпълнение от 1 януари 2002 г. на задълженията на Република България, произтичащи от Споразумението за свободна търговия между Република България и Република Естония [shared words: българия, република]
  - material 70892, ДВ 98/2012 (2012-12-11): Наредба за отменяне на Наредба № Із-1215 от 2006 г. за реда за достъп до информационните фондове на Министерството на вътрешните работи [shared words: вътрешните, реда]

## pravilnik-za-strukturata-deynostta-i-zadachite-na-okrazhnite-direktsii-bibliotek
- title: ПРАВИЛНИК ЗА СТРУКТУРАТА, ДЕЙНОСТТА И ЗАДАЧИТЕ НА ОКРЪЖНИТЕ ДИРЕКЦИИ "БИБЛИОТЕКИ"
- kind: правилник; published 1979-06-19; lex.bg records it vigente with 1 amendment rows, the last: ДВ 48/1979 (1979-06-19)
- candidate repeal titles: none share words with this title

## pravilnik-za-tehnicheskiya-nadzor-varhu-saorazheniyata-s-povishena-opasnost
- title: ПРАВИЛНИК ЗА ТЕХНИЧЕСКИЯ НАДЗОР ВЪРХУ СЪОРЪЖЕНИЯТА С ПОВИШЕНА ОПАСНОСТ
- kind: правилник; published 1983-09-16; lex.bg records it vigente with 1 amendment rows, the last: ДВ 72/1983 (1983-09-16)
- candidate repeal titles: none share words with this title

## pravilnik-za-tvorcheskiya-fond-pri-ministerstvoto-na-kulturata-zagl-izm-dv-br-10
- title: ПРАВИЛНИК ЗА ТВОРЧЕСКИЯ ФОНД ПРИ МИНИСТЕРСТВОТО НА КУЛТУРАТА (ЗАГЛ. ИЗМ. - ДВ, БР. 101 ОТ 1977 Г, БР. 94 ОТ 1998 Г.)
- kind: правилник; published 1973-06-05; lex.bg records it vigente with 3 amendment rows, the last: ДВ 49/1973 (1973-06-05); ДВ 101/1977 (1977-12-27); ДВ 94/1998 (1998-08-12)
- candidate repeal titles: none share words with this title

## pravilnik-za-upravlenieto-i-stopanisvaneto-na-svobodnata-bezmitna-zona-ruse
- title: ПРАВИЛНИК ЗА УПРАВЛЕНИЕТО И СТОПАНИСВАНЕТО НА СВОБОДНАТА БЕЗМИТНА ЗОНА - РУСЕ
- kind: правилник; published 1988-11-29; lex.bg records it vigente with 3 amendment rows, the last: ДВ 90/1988 (1988-11-29); ДВ 72/1991 (1991-09-03); ДВ 4/2001 (2001-01-12)
- candidate repeal titles: none share words with this title

## pravilnik-za-ustroystvoto-i-deynostta-na-stopanskata-direktsiya-izgrazhdane-na-s
- title: ПРАВИЛНИК ЗА УСТРОЙСТВОТО И ДЕЙНОСТТА НА СТОПАНСКАТА ДИРЕКЦИЯ "ИЗГРАЖДАНЕ НА СЕЛИЩНИТЕ СИСТЕМИ" ПРИ ОКРЪЖНИТЕ НАРОДНИ СЪВЕТИ И НА ПОДЕЛЕНИЯТА Й
- kind: правилник; published 1980-01-25; lex.bg records it vigente with 1 amendment rows, the last: ДВ 7/1980 (1980-01-25)
- candidate repeal titles:
  - material 132672, ДВ 102/2018 (2018-12-11): Правилник за отменяне на Правилника за организацията и дейността на регионалните съвети за развитие, Правилника за устройството и дейността на дирекциите за техническо съдействие, координация и управление на регионални програми и планове и Правилника за организацията и дейността на областните съвети за развитие [shared words: дейността, съвети, устройството]
  - material 49001, ДВ 35/2011 (2011-05-03): Постановление № 110 от 26 април 2011 г. за отменяне на Правилника за устройството и дейността на университет с наименование Академия на Министерството на вътрешните работи, приет с Постановление № 344 на Министерския съвет от 2004 г. [shared words: дейността, устройството]
  - material 194720, ДВ 45/2023 (2023-05-23): Инструкция за отменяне на Инструкция № Із-547 от 11 март 2013 г. за условията и реда за дейността на дирекция „Специална куриерска служба“ на Министерството на вътрешните работи по осигуряване на военна пощенска свръзка при бедствия, при въвеждане на режим „военно положение“ или „положение на война“ [shared words: дейността, дирекция]

## pravilnik-za-vatreshniya-red-v-turisticheskite-i-alpiyskite-hizhi-zasloni-spalni
- title: ПРАВИЛНИК ЗА ВЪТРЕШНИЯ РЕД В ТУРИСТИЧЕСКИТЕ И АЛПИЙСКИТЕ ХИЖИ, ЗАСЛОНИ, СПАЛНИ И ДОМОВЕ
- kind: правилник; published 1958-04-11; lex.bg records it vigente with 1 amendment rows, the last: ДВ 29/1958 (1958-04-11)
- candidate repeal titles: none share words with this title

## pravilnik-za-vodnospasitelnata-deynost-i-obezopasyavaneto-na-vodnite-ploshti
- title: ПРАВИЛНИК ЗА ВОДНОСПАСИТЕЛНАТА ДЕЙНОСТ И ОБЕЗОПАСЯВАНЕТО НА ВОДНИТЕ ПЛОЩИ
- kind: правилник; published 1983-08-19; lex.bg records it vigente with 2 amendment rows, the last: ДВ 65/1983 (1983-08-19); ДВ 45/1989 (1989-06-13)
- candidate repeal titles:
  - material 226960, ДВ 77/2024 (2024-09-10): Инструкция за отменяне на Инструкция № 1 от 1997 г. за организацията на водноспасителната дейност и обезопасяването на водните площи при провеждане на детски и ученически отдих и туризъм [shared words: водните, водноспасителната, дейност, обезопасяването, площи]

## pravilnik-za-vpisvaniyata
- title: ПРАВИЛНИК ЗА ВПИСВАНИЯТА
- kind: правилник; published 1951-12-18; lex.bg records it vigente with 14 amendment rows, the last: ДВ 92/2014 (2014-11-07); ДВ 2/2021 (2021-01-08); ДВ 112/2025 (2025-12-19)
- candidate repeal titles: none share words with this title
