# Investigate: are these acts, promulgated before 1989, still in force?

You investigate acts of the legalize-bg corpus that were promulgated before the Gazette's online archive begins
(1989), so no Gazette material of theirs can be read. For each act below you are given the facts the corpus holds
about it and the candidate repeals a script paired with it. The facts: the act's title and kind; its publication
date; lex.bg's history line of the act, which names every publication lex.bg records with its verb („обн.“
promulgated, „изм.“ amended, „доп.“ supplemented, „отм.“ repealed; the line is a witness, not an authority), and
the repeal marker a script read from that line, if any; the last amendment rows of the corpus. The corpus's own
in-force field is the bootstrap's constant „vigente“ for every act and is no evidence, so it is not shown. The
candidates: Gazette materials from 2003 on whose title repeals an act and shares words or the act number with this
act's title, and lines of the general repeal decrees (titles that name no act) whose body lines share words with
this title. Decide from these facts alone, for each act:
- `repealed`, only when a candidate names this very act (the same act, not a same-titled predecessor or a different
  act whose title shares words, and with no later amendment in the history line that contradicts it), with that
  candidate's material id; or when lex.bg's history line carries the repeal marker, with 0;
- `in_force`, only when a fact shows the act alive in the HTML era (an amendment or publication of 2003 or later in
  the history line or the amendment rows) and no candidate names it;
- `unknown` otherwise: when the only evidence is that nothing was found, when the history ends before 2003, or when
  a candidate may name it but the title is ambiguous.
What the pairing cannot see, and you must not guess: repeals published in 1989 to 2002 (the Gazette's PDF era,
not searched) and repeals carried inside another act's transitional and final provisions. Read only this file.
Write exactly one file, the answer file named below, in the form given, with every slug of this task and an
evidence note for each; write nothing else, and reply with one line: the answer file's path.

The answer file: `/Users/ekimir/swprj/legalize-bg/.claude/worktrees/unruffled-feynman-cd9070/data/runs/act-profiles-2026-10-31/calls/call-04-answer.yaml`

```yaml
# One YAML document: a mapping from each act's slug (every slug of the task, no other) to its verdict
<slug>:
  verdict: <in_force | repealed | unknown>
  repealed_by: <the material id of the candidate that repeals it, or 0 for lex.bg's own repeal marker, only when the verdict is repealed; otherwise null>
  evidence: <the facts and lines you relied on, in one or two sentences>
```

## kodeks-na-targovskoto-koraboplavane-zagl-izm-dv-br-113-ot-2002-g
- title: КОДЕКС НА ТЪРГОВСКОТО КОРАБОПЛАВАНЕ (ЗАГЛ. ИЗМ. - ДВ, БР. 113 ОТ 2002 Г.)
- kind: кодекс; published 1970-07-14
- lex.bg's history line: Обн. ДВ. бр. 55 от 14 Юли 1970г. , обн. ДВ. бр.56 от 17 Юли 1970г. , попр. ДВ. бр. 58 от 24 Юли 1970г. , изм. ДВ. бр. 55 от 18 Юли 1975г. , изм. ДВ. б […] 3г. , изм. ДВ. бр. 41 от 10 Май 2024г. , изм. ДВ. бр. 70 от 20 Август 2024г. , изм. ДВ. бр. 63 от 1 Август 2025г. , изм. и доп. ДВ. бр. 13 от 3 Февруари 2026г. , доп. ДВ. бр. 16 от 10 Февруари 2026г. , изм. ДВ. бр. 32 от 1 Април 2026г. , изм. ДВ. бр. 55 от 16 Юни 2026г.
- repeal marker read from it: none
- the corpus's amendment rows: 47, the last: ДВ 16/2026 (2026-02-10); ДВ 32/2026 (2026-04-01); ДВ 55/2026 (2026-06-16)
- candidates: none share words with this title, and lex.bg's history line carries no repeal marker

## kodeks-na-truda
- title: КОДЕКС НА ТРУДА
- kind: кодекс; published 1986-04-01
- lex.bg's history line: Обн. ДВ. бр. 26 от 1 Април 1986г. , обн. ДВ. бр.27 от 4 Април 1986г. , изм. ДВ. бр. 6 от 22 Януари 1988г. , изм. ДВ. бр. 21 от 13 Март 1990г. , изм. Д […] 7 от 9 Август 2024г. , изм. ДВ. бр. 70 от 20 Август 2024г. , изм. ДВ. бр. 115 от 30 Декември 2025г. , изм. ДВ. бр. 16 от 10 Февруари 2026г. , изм. и доп. ДВ. бр. 51 от 5 Юни 2026г. , изм. и доп. ДВ. бр. 69 от 31 Юли 2026г. , изм. и доп. ДВ. бр. 89 от 29 Септември 2026г.
- repeal marker read from it: none
- the corpus's amendment rows: 135, the last: ДВ 51/2026 (2026-06-05); ДВ 69/2026 (2026-07-31); ДВ 89/2026 (2026-09-29)
- candidates:
  - material 342, ДВ 44/2005 (2005-05-27): Правилник за отменяне на Правилника по безопасността на труда при експлоатацията на електрокари и мотокари - Д-05-002 [shared words: труда]
  - material 343, ДВ 44/2005 (2005-05-27): Правилник за отменяне на Правилника по безопасността на труда при експлоатацията, обслужването и ремонта на моторните превозни средства Д-05-003 [shared words: труда]
  - material 2377, ДВ 67/2006 (2006-08-18): Правилник за отменяне на Правилника по безопасността на труда на работниците, поддържащи железния път - В-05-01-02 от 1975 г. [shared words: труда]
  - material 2378, ДВ 67/2006 (2006-08-18): Правилник за отменяне на Правилника по безопасността на труда на работниците от експлоатацията на локомотивното стопанство - В-05-01-01 от 1976 г. [shared words: труда]
  - material 2379, ДВ 67/2006 (2006-08-18): Правилник за отменяне на Правилника по безопасността на труда за работниците и служителите от гаровите и превозните служби - В-05-01-03 от 1976 г. [shared words: труда]
  - material 2380, ДВ 67/2006 (2006-08-18): Правилник за отменяне на Правилника по безопасността на труда в железопътните заводи, депа и работилници - В-05-01-05 от 1976 г. [shared words: труда]
  - material 2381, ДВ 67/2006 (2006-08-18): Правилник за отменяне на Правилника по безопасността на труда във вагонното стопанство - В-05-01-06 от 1988 г. [shared words: труда]
  - material 2382, ДВ 67/2006 (2006-08-18): Правилник за отменяне на Правилника по безопасността на труда при работи по жп контактна мрежа 25 кв, 50 хц - В-05-01-04 от 1989 г. [shared words: труда]
  - material 2758, ДВ 88/2006 (2006-10-31), a line of the general repeal decree „Постановление № 284 от 23 октомври 2006 г. за отменяне на нормативни актове на Министерския съвет“: 28. Постановление № 228 на Министерския съвет от 1995 г. за освобождаване от митни сборове вноса на безвъзмездно предоставените от Федерална република Германия стоки за професионално-информационните центрове на Националната служба по заетостта при Министерството на труда и социалните грижи във Варна, Видин, Добрич и Пещера (ДВ, бр. 107 от 1995 г.). [shared words: труда]
  - material 2850, ДВ 94/2006 (2006-11-21): Правилник за отмяна на Правилника по безопасност на труда при товаро-разтоварните работи (Д-05-001), МТСГ, 1972 г. [shared words: труда]
  - material 14923, ДВ 19/2005 (2005-03-01): Правилник за отменяне на Правилника по безопасността на труда при експлоатация на електрическите уредби и съоръжения Д-01-008 от 1986 г. [shared words: труда]
  - material 18245, ДВ 107/2004 (2004-12-07): Правилник за отмяна на Правилника по безопасността на труда при поддържането и експлоатацията на водоснабдителните и канализационните мрежи и съоръжения - Д-09-001 [shared words: труда]

## nakazatelen-kodeks
- title: НАКАЗАТЕЛЕН КОДЕКС
- kind: кодекс; published 1968-04-02
- lex.bg's history line: Обн. ДВ. бр. 26 от 2 Април 1968г. , попр. ДВ. бр. 29 от 12 Април 1968г. , изм. ДВ. бр. 92 от 28 Ноември 1969г. , изм. ДВ. бр. 26 от 30 Март 1973г. , и […] р. 64 от 5 Август 2025г. , доп. ДВ. бр. 65 от 8 Август 2025г. , доп. ДВ. бр. 87 от 17 Октомври 2025г. , изм. и доп. ДВ. бр. 115 от 30 Декември 2025г. , изм. и доп. ДВ. бр. 27 от 17 Март 2026г. , изм. и доп. ДВ. бр. 32 от 1 Април 2026г. , изм. ДВ. бр. 55 от 16 Юни 2026г.
- repeal marker read from it: none
- the corpus's amendment rows: 142, the last: ДВ 27/2026 (2026-03-17); ДВ 32/2026 (2026-04-01); ДВ 55/2026 (2026-06-16)
- candidates: none share words with this title, and lex.bg's history line carries no repeal marker

## naredba-0-31-za-rabota-s-radiatsionni-defektoskopi
- title: НАРЕДБА № 0-31 ЗА РАБОТА С РАДИАЦИОННИ ДЕФЕКТОСКОПИ
- kind: наредба; published 1974-07-02
- lex.bg's history line: Обн. ДВ. бр. 51 от 2 Юли 1974г. , изм. ДВ. бр. 32 от 25 Април 1978г.
- repeal marker read from it: none
- the corpus's amendment rows: 2, the last: ДВ 51/1974 (1974-07-02); ДВ 32/1978 (1978-04-25)
- candidates: none share words with this title, and lex.bg's history line carries no repeal marker

## naredba-1-za-neprikosnovenite-zapasi-na-morskite-korabi
- title: НАРЕДБА № 1 ЗА НЕПРИКОСНОВЕНИТЕ ЗАПАСИ НА МОРСКИТЕ КОРАБИ
- kind: наредба; published 1981-03-31
- lex.bg's history line: Обн. ДВ. бр. 26 от 31 Март 1981г.
- repeal marker read from it: none
- the corpus's amendment rows: 1, the last: ДВ 26/1981 (1981-03-31)
- candidates:
  - material 208701, ДВ 20/2024 (2024-03-08): Наредба за отменяне на Наредба № 1 за условията, при които министерствата, другите ведомства и организациите могат да експлоатират малък брой автобуси [same act number] [shared words: ]

## naredba-1-za-patuvane-po-zhelezopatniya-i-vodniya-transport-na-opredeleni-katego
- title: НАРЕДБА № 1 ЗА ПЪТУВАНЕ ПО ЖЕЛЕЗОПЪТНИЯ И ВОДНИЯ ТРАНСПОРТ НА ОПРЕДЕЛЕНИ КАТЕГОРИИ ИНВАЛИДИ, АКТИВНИТЕ УЧАСТНИЦИ В МАКЕДОНО-ОДРИНСКОТО ОПЪЛЧЕНИЕ И ЖЕНИТЕ-ДОБРОВОЛКИ, УЧАСТНИЧКИ В ОТЕЧЕСТВЕНАТА ВОЙНА
- kind: наредба; published 1977-06-17
- lex.bg's history line: Обн. ДВ. бр. 47 от 17 Юни 1977г.
- repeal marker read from it: none
- the corpus's amendment rows: 1, the last: ДВ 47/1977 (1977-06-17)
- candidates:
  - material 208701, ДВ 20/2024 (2024-03-08): Наредба за отменяне на Наредба № 1 за условията, при които министерствата, другите ведомства и организациите могат да експлоатират малък брой автобуси [same act number] [shared words: ]
  - material 96071, ДВ 57/2015 (2015-07-28): Наредба за отменяне на Наредба № 2 от 2006 г. за условията и реда за предоставяне на средства за компенсиране на намалените приходи от прилагането на цени за пътуване по автомобилния транспорт, предвидени в нормативни актове за определени категории пътници и Наредба № 3 от 2005 г. за условията и реда за предоставяне на средства за субсидиране на превоза на пътниците по нерентабилни автобусни линии във вътрешноградския транспорт и транспорта в планински и други райони [shared words: категории, определени, пътуване, транспорт]

## naredba-1-za-spasitelnata-deynost-v-minite-himicheskite-i-metalurgichnite-zavodi
- title: НАРЕДБА № 1 ЗА СПАСИТЕЛНАТА ДЕЙНОСТ В МИНИТЕ, ХИМИЧЕСКИТЕ И МЕТАЛУРГИЧНИТЕ ЗАВОДИ
- kind: наредба; published 1978-07-18
- lex.bg's history line: Обн. ДВ. бр.56 от 18 Юли 1978г. , обн. ДВ. бр. 57 от 21 Юли 1978г.
- repeal marker read from it: none
- the corpus's amendment rows: 2, the last: ДВ 56/1978 (1978-07-18); ДВ 57/1978 (1978-07-21)
- candidates:
  - material 208701, ДВ 20/2024 (2024-03-08): Наредба за отменяне на Наредба № 1 за условията, при които министерствата, другите ведомства и организациите могат да експлоатират малък брой автобуси [same act number] [shared words: ]

## naredba-1-za-tarsene-izkupuvane-obrabotka-i-realizatsiya-na-mineralni-obraztsi-f
- title: НАРЕДБА № 1 ЗА ТЪРСЕНЕ, ИЗКУПУВАНЕ, ОБРАБОТКА И РЕАЛИЗАЦИЯ НА МИНЕРАЛНИ ОБРАЗЦИ, ФОСИЛИ И ДРУГИ МИНЕРАЛНИ СУРОВИНИ ЗА ЮВЕЛИРНИ, СУВЕНИРНИ И МУЗЕЙНИ НУЖДИ
- kind: наредба; published 1986-01-31
- lex.bg's history line: Обн. ДВ. бр. 9 от 31 Януари 1986г.
- repeal marker read from it: none
- the corpus's amendment rows: 1, the last: ДВ 9/1986 (1986-01-31)
- candidates:
  - material 208701, ДВ 20/2024 (2024-03-08): Наредба за отменяне на Наредба № 1 за условията, при които министерствата, другите ведомства и организациите могат да експлоатират малък брой автобуси [same act number] [shared words: ]

## naredba-10-za-sadebnite-i-arbitrazhnite-ekspertizi
- title: НАРЕДБА № 10 ЗА СЪДЕБНИТЕ И АРБИТРАЖНИТЕ ЕКСПЕРТИЗИ
- kind: наредба; published 1983-11-29
- lex.bg's history line: Обн. ДВ. бр. 93 от 29 Ноември 1983г.
- repeal marker read from it: none
- the corpus's amendment rows: 1, the last: ДВ 93/1983 (1983-11-29)
- candidates: none share words with this title, and lex.bg's history line carries no repeal marker

## naredba-11-ot-2-mart-1987-g-za-staite-za-lichna-higiena-na-zhenite-i-za-pochivka
- title: НАРЕДБА № 11 ОТ 2 МАРТ 1987 Г. ЗА СТАИТЕ ЗА ЛИЧНА ХИГИЕНА НА ЖЕНИТЕ И ЗА ПОЧИВКА НА БРЕМЕННИТЕ ЖЕНИ
- kind: наредба; published 1987-07-24
- lex.bg's history line: Обн. ДВ. бр. 57 от 24 Юли 1987г.
- repeal marker read from it: none
- the corpus's amendment rows: 1, the last: ДВ 57/1987 (1987-07-24)
- candidates: none share words with this title, and lex.bg's history line carries no repeal marker
