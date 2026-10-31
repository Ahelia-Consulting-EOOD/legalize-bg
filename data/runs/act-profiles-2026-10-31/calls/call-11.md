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

The answer file: `/Users/ekimir/swprj/legalize-bg/.claude/worktrees/unruffled-feynman-cd9070/data/runs/act-profiles-2026-10-31/calls/call-11-answer.yaml`

```yaml
# One YAML document: a mapping from each act's slug (every slug of the task, no other) to its verdict
<slug>:
  verdict: <in_force | repealed | unknown>
  repealed_by: <the material id of the candidate repeal title, only when the verdict is repealed; otherwise null>
  evidence: <the facts and lines you relied on, in one or two sentences>
```

## pravilnik-za-zastroyavane-blagoustroyavane-i-opazvane-na-natsionalniya-arhitektu
- title: ПРАВИЛНИК ЗА ЗАСТРОЯВАНЕ, БЛАГОУСТРОЯВАНЕ И ОПАЗВАНЕ НА НАЦИОНАЛНИЯ АРХИТЕКТУРНО-ИСТОРИЧЕСКИ РЕЗЕРВАТ КОПРИВЩИЦА
- kind: правилник; published 1975-03-18; lex.bg records it vigente with 1 amendment rows, the last: ДВ 22/1975 (1975-03-18)
- candidate repeal titles: none share words with this title

## primeren-pravilnik-za-vatreshniya-red-v-etazhnata-sobstvenost-zagl-izm-dv-br-15-
- title: ПРИМЕРЕН ПРАВИЛНИК ЗА ВЪТРЕШНИЯ РЕД В ЕТАЖНАТА СОБСТВЕНОСТ (ЗАГЛ. ИЗМ. - ДВ, БР. 15 ОТ 2003 Г.)
- kind: правилник; published 1978-09-26; lex.bg records it vigente with 3 amendment rows, the last: ДВ 76/1978 (1978-09-26); ДВ 73/1979 (1979-09-14); ДВ 15/2003 (2003-02-14)
- candidate repeal titles: none share words with this title

## ukaz-883-ot-24-april-1974-g-za-prilagane-na-zakona-za-normativnite-aktove
- title: УКАЗ № 883 ОТ 24.04.1974 Г. ЗА ПРИЛАГАНЕ НА ЗАКОНА ЗА НОРМАТИВНИТЕ АКТОВЕ
- kind: правилник; published 1974-05-21; lex.bg records it vigente with 4 amendment rows, the last: ДВ 7/1978 (1978-01-24); ДВ 57/1980 (1980-07-22); ДВ 46/2007 (2007-06-12)
- candidate repeal titles: none share words with this title

## pravilnik-za-prilagane-na-ukaz-2242-za-svobodni-zoni-zagl-izm-dv-br-15-ot-1998-g
- title: ПРАВИЛНИК ЗА ПРИЛАГАНЕ НА УКАЗ № 2242 ЗА СВОБОДНИ ЗОНИ (ЗАГЛ. ИЗМ. - ДВ, БР. 15 ОТ 1998 Г., В СИЛА ОТ 01.01.1999 Г.)
- kind: правилник по прилагане; published 1987-11-06; lex.bg records it vigente with 10 amendment rows, the last: ДВ 45/2009 (2009-06-16); ДВ 7/2011 (2011-01-21); ДВ 60/2014 (2014-07-22)
- candidate repeal titles: none share words with this title

## pravilnik-za-prilagane-na-zakona-za-opazvane-na-selskostopanskoto-imushtestvo
- title: ПРАВИЛНИК ЗА ПРИЛАГАНЕ НА ЗАКОНА ЗА ОПАЗВАНЕ НА СЕЛСКОСТОПАНСКОТО ИМУЩЕСТВО
- kind: правилник по прилагане; published 1985-11-22; lex.bg records it vigente with 1 amendment rows, the last: ДВ 90/1985 (1985-11-22)
- candidate repeal titles: none share words with this title

## pravilnik-za-prilozhenie-na-ukaza-za-targovskoto-koraboplavane-na-narodna-republ
- title: ПРАВИЛНИК ЗА ПРИЛОЖЕНИЕ НА УКАЗА ЗА ТЪРГОВСКОТО КОРАБОПЛАВАНЕ НА НАРОДНА РЕПУБЛИКА БЪЛГАРИЯ ЗА МЕЖДУНАРОДНИТЕ ПРЕВОЗИ ПО Р. ДУНАВ
- kind: правилник по прилагане; published 1955-09-09; lex.bg records it vigente with 1 amendment rows, the last: ДВ 73/1955 (1955-09-09)
- candidate repeal titles:
  - material 18034, ДВ 113/2004 (2004-12-28): Наредба за отмяна на Наредба № 12 от 1993 г. за реда и начина за внос на азбест и азбестосъдържащи материали на територията на Република България [shared words: българия, република]
  - material 20903, ДВ 41/2009 (2009-06-02): Наредба за отмяна на Наредба № 26 от 2006 г. за временно упражняване на медицински дейности в Република България за граждани на държава - членка на Европейския съюз, и другите държави от Европейското икономическо пространство [shared words: българия, република]
  - material 21361, ДВ 25/2004 (2004-03-26): Постановление № 60 от 16 март 2004 г. за отменяне на Постановление № 15 на Министерския съвет от 2002 г. за изпълнение от 1 януари 2002 г. на задълженията на Република България, произтичащи от Споразумението за свободна търговия между Република България и Република Естония [shared words: българия, република]
  - material 98929, ДВ 93/2015 (2015-12-01): Инструкция за отменяне на Инструкция № 512 от 2006 г. за провеждане на радиотелефонна комуникация при обслужване на въздушното движение в Република България [shared words: българия, република]
  - material 104005, ДВ 38/2016 (2016-05-20): Постановление № 123 от 17 май 2016 г. за отмяна на Постановление № 260 на Министерския съвет от 2003 г. за определяне възнагражденията на кадровите военнослужещи при участие на Република България в операции по поддържане на мира и в мисии, провеждани под егидата на международни организации [shared words: българия, република]
  - material 111423, ДВ 9/2017 (2017-01-26): Наредба за отменяне на Наредба № 2 от 2002 г. за условията и реда за издаване на разрешения за извършване на дейност на свободна практика от чужденци в Република България [shared words: българия, република]
  - material 127722, ДВ 53/2018 (2018-06-26): Постановление № 105 от 21 юни 2018 г. за отменяне на Наредбата за реда за лицензиране на спортните организации в Република България, приета с Постановление № 237 на Министерския съвет от 2008 г. [shared words: българия, република]
  - material 129046, ДВ 66/2018 (2018-08-10): Наредба за отменяне на Наредба № Н-5 от 2014 г. за подбор на военнослужещи и цивилни служители от Министерството на отбраната, структурите на пряко подчинение на министъра на отбраната и от Българската армия за заемане на длъжности в задграничните представителства на Република България, в щабове или органи на международни организации и на други международни инициативи [shared words: българия, република]
  - material 137725, ДВ 42/2019 (2019-05-28): Наредба за отменяне на Наредба № 6 от 2018 г. за реда за лицензиране на спортните организации в Република България [shared words: българия, република]
  - material 143534, ДВ 97/2019 (2019-12-10): Постановление № 317 от 5 декември 2019 г. за отменяне на Наредбата за реда и начина за определяне в Патентното ведомство на марка като общественоизвестна и марка, ползваща се с известност на територията на Република България, приета с Постановление № 229 на Министерския съвет от 2007 г. [shared words: българия, република]
  - material 154127, ДВ 102/2020 (2020-12-01): Решение за отмяна на Решението за създаване на Временна комисия за разглеждане на проект на Конституцията на Република България, прието от Народното събрание на 2 октомври 2020 г. [shared words: българия, република]
  - material 154713, ДВ 111/2020 (2020-12-31): Инструкция за отмяна на Инструкция № 1 от 2006 г. за издаването на дипломатически и служебни паспорти от Министерството на външните работи на Република България [shared words: българия, република]

## pravilnik-za-prilozhenie-na-ukaza-za-urezhdane-na-tehnicheskata-pravosposobnost-
- title: ПРАВИЛНИК ЗА ПРИЛОЖЕНИЕ НА УКАЗА ЗА УРЕЖДАНЕ НА ТЕХНИЧЕСКАТА ПРАВОСПОСОБНОСТ И ПРАВОТО НА ЧАСТНА ТЕХНИЧЕСКА ПРАКТИКА
- kind: правилник по прилагане; published 1961-08-25; lex.bg records it vigente with 1 amendment rows, the last: ДВ 68/1961 (1961-08-25)
- candidate repeal titles:
  - material 104002, ДВ 33/2003 (2003-04-11): Наредба за отменяне на Наредба № 6 от 1987 г. за техническата правоспособност в проектирането и строителството [shared words: правоспособност, техническата]

## pravilnik-za-prilozhenie-na-zakona-za-opazvane-na-vazduha-vodite-i-pochvata-ot-z
- title: ПРАВИЛНИК ЗА ПРИЛОЖЕНИЕ НА ЗАКОНА ЗА ОПАЗВАНЕ НА ВЪЗДУХА, ВОДИТЕ И ПОЧВАТА ОТ ЗАМЪРСЯВАНЕ
- kind: правилник по прилагане; published 1964-10-09; lex.bg records it vigente with 2 amendment rows, the last: ДВ 80/1964 (1964-10-09); ДВ 9/1978 (1978-01-31)
- candidate repeal titles: none share words with this title

## pravilnik-za-prilozhenie-na-zakona-za-urezhdane-pravata-na-litsata-koito-sa-zael
- title: ПРАВИЛНИК ЗА ПРИЛОЖЕНИЕ НА ЗАКОНА ЗА УРЕЖДАНЕ ПРАВАТА НА ЛИЦАТА, КОИТО СА ЗАЕЛИ ИЛИ ПОЛУЧИЛИ ДЪРЖАВНИ ДВОРНИ МЕСТА
- kind: правилник по прилагане; published 1957-07-30; lex.bg records it vigente with 1 amendment rows, the last: ДВ 61/1957 (1957-07-30)
- candidate repeal titles:
  - material 240221, ДВ 114/2025 (2025-12-24): Наредба за отменяне на Наредба № Н-9 от 2020 г. за условията и реда за вписване в регистъра на лицата, които по занятие предоставят услуги за обмяна между виртуални валути и признати валути без златно покритие, услуги за прехвърляне или обмяна на виртуални активи, услуги по съхраняване на виртуални активи и управление на такива, позволяващо осъществяването на контрол върху активите, и услуги, свързани с публично предлагане на виртуални активи, и на доставчиците на портфейли, които предлагат попечителски услуги [shared words: които, лицата]
