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

The answer file: `/Users/ekimir/swprj/legalize-bg/.claude/worktrees/unruffled-feynman-cd9070/data/runs/act-profiles-2026-10-31/calls/call-04-answer.yaml`

```yaml
# One YAML document: a mapping from each act's slug (every slug of the task, no other) to its verdict
<slug>:
  verdict: <in_force | repealed | unknown>
  repealed_by: <the material id of the candidate repeal title, only when the verdict is repealed; otherwise null>
  evidence: <the facts and lines you relied on, in one or two sentences>
```

## kodeks-na-targovskoto-koraboplavane-zagl-izm-dv-br-113-ot-2002-g
- title: КОДЕКС НА ТЪРГОВСКОТО КОРАБОПЛАВАНЕ (ЗАГЛ. ИЗМ. - ДВ, БР. 113 ОТ 2002 Г.)
- kind: кодекс; published 1970-07-14; lex.bg records it vigente with 47 amendment rows, the last: ДВ 16/2026 (2026-02-10); ДВ 32/2026 (2026-04-01); ДВ 55/2026 (2026-06-16)
- candidate repeal titles: none share words with this title

## kodeks-na-truda
- title: КОДЕКС НА ТРУДА
- kind: кодекс; published 1986-04-01; lex.bg records it vigente with 135 amendment rows, the last: ДВ 51/2026 (2026-06-05); ДВ 69/2026 (2026-07-31); ДВ 89/2026 (2026-09-29)
- candidate repeal titles:
  - material 342, ДВ 44/2005 (2005-05-27): Правилник за отменяне на Правилника по безопасността на труда при експлоатацията на електрокари и мотокари - Д-05-002 [shared words: труда]
  - material 343, ДВ 44/2005 (2005-05-27): Правилник за отменяне на Правилника по безопасността на труда при експлоатацията, обслужването и ремонта на моторните превозни средства Д-05-003 [shared words: труда]
  - material 2377, ДВ 67/2006 (2006-08-18): Правилник за отменяне на Правилника по безопасността на труда на работниците, поддържащи железния път - В-05-01-02 от 1975 г. [shared words: труда]
  - material 2378, ДВ 67/2006 (2006-08-18): Правилник за отменяне на Правилника по безопасността на труда на работниците от експлоатацията на локомотивното стопанство - В-05-01-01 от 1976 г. [shared words: труда]
  - material 2379, ДВ 67/2006 (2006-08-18): Правилник за отменяне на Правилника по безопасността на труда за работниците и служителите от гаровите и превозните служби - В-05-01-03 от 1976 г. [shared words: труда]
  - material 2380, ДВ 67/2006 (2006-08-18): Правилник за отменяне на Правилника по безопасността на труда в железопътните заводи, депа и работилници - В-05-01-05 от 1976 г. [shared words: труда]
  - material 2381, ДВ 67/2006 (2006-08-18): Правилник за отменяне на Правилника по безопасността на труда във вагонното стопанство - В-05-01-06 от 1988 г. [shared words: труда]
  - material 2382, ДВ 67/2006 (2006-08-18): Правилник за отменяне на Правилника по безопасността на труда при работи по жп контактна мрежа 25 кв, 50 хц - В-05-01-04 от 1989 г. [shared words: труда]
  - material 2850, ДВ 94/2006 (2006-11-21): Правилник за отмяна на Правилника по безопасност на труда при товаро-разтоварните работи (Д-05-001), МТСГ, 1972 г. [shared words: труда]
  - material 14923, ДВ 19/2005 (2005-03-01): Правилник за отменяне на Правилника по безопасността на труда при експлоатация на електрическите уредби и съоръжения Д-01-008 от 1986 г. [shared words: труда]
  - material 18245, ДВ 107/2004 (2004-12-07): Правилник за отмяна на Правилника по безопасността на труда при поддържането и експлоатацията на водоснабдителните и канализационните мрежи и съоръжения - Д-09-001 [shared words: труда]
  - material 18246, ДВ 107/2004 (2004-12-07): Правилник за отмяна на Правилника по безопасността на труда за въздушни компресорни инсталации и уредби - Д-01-014 [shared words: труда]

## nakazatelen-kodeks
- title: НАКАЗАТЕЛЕН КОДЕКС
- kind: кодекс; published 1968-04-02; lex.bg records it vigente with 142 amendment rows, the last: ДВ 27/2026 (2026-03-17); ДВ 32/2026 (2026-04-01); ДВ 55/2026 (2026-06-16)
- candidate repeal titles: none share words with this title

## naredba-0-31-za-rabota-s-radiatsionni-defektoskopi
- title: НАРЕДБА № 0-31 ЗА РАБОТА С РАДИАЦИОННИ ДЕФЕКТОСКОПИ
- kind: наредба; published 1974-07-02; lex.bg records it vigente with 2 amendment rows, the last: ДВ 51/1974 (1974-07-02); ДВ 32/1978 (1978-04-25)
- candidate repeal titles: none share words with this title

## naredba-1-za-neprikosnovenite-zapasi-na-morskite-korabi
- title: НАРЕДБА № 1 ЗА НЕПРИКОСНОВЕНИТЕ ЗАПАСИ НА МОРСКИТЕ КОРАБИ
- kind: наредба; published 1981-03-31; lex.bg records it vigente with 1 amendment rows, the last: ДВ 26/1981 (1981-03-31)
- candidate repeal titles:
  - material 208701, ДВ 20/2024 (2024-03-08): Наредба за отменяне на Наредба № 1 за условията, при които министерствата, другите ведомства и организациите могат да експлоатират малък брой автобуси [same act number] [shared words: ]

## naredba-1-za-patuvane-po-zhelezopatniya-i-vodniya-transport-na-opredeleni-katego
- title: НАРЕДБА № 1 ЗА ПЪТУВАНЕ ПО ЖЕЛЕЗОПЪТНИЯ И ВОДНИЯ ТРАНСПОРТ НА ОПРЕДЕЛЕНИ КАТЕГОРИИ ИНВАЛИДИ, АКТИВНИТЕ УЧАСТНИЦИ В МАКЕДОНО-ОДРИНСКОТО ОПЪЛЧЕНИЕ И ЖЕНИТЕ-ДОБРОВОЛКИ, УЧАСТНИЧКИ В ОТЕЧЕСТВЕНАТА ВОЙНА
- kind: наредба; published 1977-06-17; lex.bg records it vigente with 1 amendment rows, the last: ДВ 47/1977 (1977-06-17)
- candidate repeal titles:
  - material 208701, ДВ 20/2024 (2024-03-08): Наредба за отменяне на Наредба № 1 за условията, при които министерствата, другите ведомства и организациите могат да експлоатират малък брой автобуси [same act number] [shared words: ]
  - material 96071, ДВ 57/2015 (2015-07-28): Наредба за отменяне на Наредба № 2 от 2006 г. за условията и реда за предоставяне на средства за компенсиране на намалените приходи от прилагането на цени за пътуване по автомобилния транспорт, предвидени в нормативни актове за определени категории пътници и Наредба № 3 от 2005 г. за условията и реда за предоставяне на средства за субсидиране на превоза на пътниците по нерентабилни автобусни линии във вътрешноградския транспорт и транспорта в планински и други райони [shared words: категории, определени, пътуване, транспорт]

## naredba-1-za-spasitelnata-deynost-v-minite-himicheskite-i-metalurgichnite-zavodi
- title: НАРЕДБА № 1 ЗА СПАСИТЕЛНАТА ДЕЙНОСТ В МИНИТЕ, ХИМИЧЕСКИТЕ И МЕТАЛУРГИЧНИТЕ ЗАВОДИ
- kind: наредба; published 1978-07-18; lex.bg records it vigente with 2 amendment rows, the last: ДВ 56/1978 (1978-07-18); ДВ 57/1978 (1978-07-21)
- candidate repeal titles:
  - material 208701, ДВ 20/2024 (2024-03-08): Наредба за отменяне на Наредба № 1 за условията, при които министерствата, другите ведомства и организациите могат да експлоатират малък брой автобуси [same act number] [shared words: ]

## naredba-1-za-tarsene-izkupuvane-obrabotka-i-realizatsiya-na-mineralni-obraztsi-f
- title: НАРЕДБА № 1 ЗА ТЪРСЕНЕ, ИЗКУПУВАНЕ, ОБРАБОТКА И РЕАЛИЗАЦИЯ НА МИНЕРАЛНИ ОБРАЗЦИ, ФОСИЛИ И ДРУГИ МИНЕРАЛНИ СУРОВИНИ ЗА ЮВЕЛИРНИ, СУВЕНИРНИ И МУЗЕЙНИ НУЖДИ
- kind: наредба; published 1986-01-31; lex.bg records it vigente with 1 amendment rows, the last: ДВ 9/1986 (1986-01-31)
- candidate repeal titles:
  - material 208701, ДВ 20/2024 (2024-03-08): Наредба за отменяне на Наредба № 1 за условията, при които министерствата, другите ведомства и организациите могат да експлоатират малък брой автобуси [same act number] [shared words: ]

## naredba-10-za-sadebnite-i-arbitrazhnite-ekspertizi
- title: НАРЕДБА № 10 ЗА СЪДЕБНИТЕ И АРБИТРАЖНИТЕ ЕКСПЕРТИЗИ
- kind: наредба; published 1983-11-29; lex.bg records it vigente with 1 amendment rows, the last: ДВ 93/1983 (1983-11-29)
- candidate repeal titles: none share words with this title

## naredba-11-ot-2-mart-1987-g-za-staite-za-lichna-higiena-na-zhenite-i-za-pochivka
- title: НАРЕДБА № 11 ОТ 2 МАРТ 1987 Г. ЗА СТАИТЕ ЗА ЛИЧНА ХИГИЕНА НА ЖЕНИТЕ И ЗА ПОЧИВКА НА БРЕМЕННИТЕ ЖЕНИ
- kind: наредба; published 1987-07-24; lex.bg records it vigente with 1 amendment rows, the last: ДВ 57/1987 (1987-07-24)
- candidate repeal titles: none share words with this title
