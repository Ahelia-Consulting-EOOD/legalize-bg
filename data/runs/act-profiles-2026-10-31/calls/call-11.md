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

The answer file: `/Users/ekimir/swprj/legalize-bg/.claude/worktrees/unruffled-feynman-cd9070/data/runs/act-profiles-2026-10-31/calls/call-11-answer.yaml`

```yaml
# One YAML document: a mapping from each act's slug (every slug of the task, no other) to its verdict
<slug>:
  verdict: <in_force | repealed | unknown>
  repealed_by: <the material id of the candidate that repeals it, or 0 for lex.bg's own repeal marker, only when the verdict is repealed; otherwise null>
  evidence: <the facts and lines you relied on, in one or two sentences>
```

## pravilnik-za-zastroyavane-blagoustroyavane-i-opazvane-na-natsionalniya-arhitektu
- title: ПРАВИЛНИК ЗА ЗАСТРОЯВАНЕ, БЛАГОУСТРОЯВАНЕ И ОПАЗВАНЕ НА НАЦИОНАЛНИЯ АРХИТЕКТУРНО-ИСТОРИЧЕСКИ РЕЗЕРВАТ КОПРИВЩИЦА
- kind: правилник; published 1975-03-18
- lex.bg's history line: Обн. ДВ. бр. 22 от 18 Март 1975г.
- repeal marker read from it: none
- the corpus's amendment rows: 1, the last: ДВ 22/1975 (1975-03-18)
- candidates: none share words with this title, and lex.bg's history line carries no repeal marker

## primeren-pravilnik-za-vatreshniya-red-v-etazhnata-sobstvenost-zagl-izm-dv-br-15-
- title: ПРИМЕРЕН ПРАВИЛНИК ЗА ВЪТРЕШНИЯ РЕД В ЕТАЖНАТА СОБСТВЕНОСТ (ЗАГЛ. ИЗМ. - ДВ, БР. 15 ОТ 2003 Г.)
- kind: правилник; published 1978-09-26
- lex.bg's history line: Обн. ДВ. бр.76 от 26 Септември 1978г. , изм. ДВ. бр. 73 от 14 Септември 1979г. , изм. ДВ. бр. 15 от 14 Февруари 2003г.
- repeal marker read from it: none
- the corpus's amendment rows: 3, the last: ДВ 76/1978 (1978-09-26); ДВ 73/1979 (1979-09-14); ДВ 15/2003 (2003-02-14)
- candidates: none share words with this title, and lex.bg's history line carries no repeal marker

## ukaz-883-ot-24-april-1974-g-za-prilagane-na-zakona-za-normativnite-aktove
- title: УКАЗ № 883 ОТ 24.04.1974 Г. ЗА ПРИЛАГАНЕ НА ЗАКОНА ЗА НОРМАТИВНИТЕ АКТОВЕ
- kind: правилник; published 1974-05-21
- lex.bg's history line: none on the page
- repeal marker read from it: none
- the corpus's amendment rows: 4, the last: ДВ 7/1978 (1978-01-24); ДВ 57/1980 (1980-07-22); ДВ 46/2007 (2007-06-12)
- candidates: none share words with this title, and lex.bg's history line carries no repeal marker

## pravilnik-za-prilagane-na-ukaz-2242-za-svobodni-zoni-zagl-izm-dv-br-15-ot-1998-g
- title: ПРАВИЛНИК ЗА ПРИЛАГАНЕ НА УКАЗ № 2242 ЗА СВОБОДНИ ЗОНИ (ЗАГЛ. ИЗМ. - ДВ, БР. 15 ОТ 1998 Г., В СИЛА ОТ 01.01.1999 Г.)
- kind: правилник по прилагане; published 1987-11-06
- lex.bg's history line: Обн. ДВ. бр.86 от 6 Ноември 1987г. , изм. ДВ. бр.23 от 22 Март 1991г. , изм. ДВ. бр. 72 от 3 Септември 1991г. , изм. ДВ. бр. 15 от 6 Февруари 1998г. , изм. ДВ. бр. 127 от 31 Октомври 1998г. , изм. ДВ. бр. 149 от 17 Декември 1998г. , изм. ДВ. бр. 52 от 27 Юни 2006г. , изм. ДВ. бр. 45 от 16 Юни 2009г. , изм. ДВ. бр. 7 от 21 Януари 2011г. , изм. ДВ. бр. 60 от 22 Юли 2014г.
- repeal marker read from it: none
- the corpus's amendment rows: 10, the last: ДВ 45/2009 (2009-06-16); ДВ 7/2011 (2011-01-21); ДВ 60/2014 (2014-07-22)
- candidates: none share words with this title, and lex.bg's history line carries no repeal marker

## pravilnik-za-prilagane-na-zakona-za-opazvane-na-selskostopanskoto-imushtestvo
- title: ПРАВИЛНИК ЗА ПРИЛАГАНЕ НА ЗАКОНА ЗА ОПАЗВАНЕ НА СЕЛСКОСТОПАНСКОТО ИМУЩЕСТВО
- kind: правилник по прилагане; published 1985-11-22
- lex.bg's history line: Обн. ДВ. бр. 90 от 22 Ноември 1985г.
- repeal marker read from it: none
- the corpus's amendment rows: 1, the last: ДВ 90/1985 (1985-11-22)
- candidates: none share words with this title, and lex.bg's history line carries no repeal marker

## pravilnik-za-prilozhenie-na-ukaza-za-targovskoto-koraboplavane-na-narodna-republ
- title: ПРАВИЛНИК ЗА ПРИЛОЖЕНИЕ НА УКАЗА ЗА ТЪРГОВСКОТО КОРАБОПЛАВАНЕ НА НАРОДНА РЕПУБЛИКА БЪЛГАРИЯ ЗА МЕЖДУНАРОДНИТЕ ПРЕВОЗИ ПО Р. ДУНАВ
- kind: правилник по прилагане; published 1955-09-09
- lex.bg's history line: Обн. ДВ. бр. 73 от 9 Септември 1955г.
- repeal marker read from it: none
- the corpus's amendment rows: 1, the last: ДВ 73/1955 (1955-09-09)
- candidates:
  - material 2755, ДВ 88/2006 (2006-10-31), a line of the general repeal decree „Постановление № 281 от 20 октомври 2006 г. за отменяне на нормативни актове на Министерския съвет“: § 2. Отменя се Постановление № 300 на Министерския съвет от 1996 г. за защитни мерки по вноса на стоки в Република България (обн., ДВ, бр. 109 от 1996 г.; изм., бр. 45 от 1997 г.). [shared words: българия, република]
  - material 2758, ДВ 88/2006 (2006-10-31), a line of the general repeal decree „Постановление № 284 от 23 октомври 2006 г. за отменяне на нормативни актове на Министерския съвет“: 3. Постановление № 79 на Министерския съвет от 1994 г. за освобождаване от митни сборове на имуществата, внасяни в Република България в рамките на безвъзмездната финансова помощ за културата от правителството на Япония (ДВ, бр. 35 от 1994 г.). [shared words: българия, република]
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

## pravilnik-za-prilozhenie-na-ukaza-za-urezhdane-na-tehnicheskata-pravosposobnost-
- title: ПРАВИЛНИК ЗА ПРИЛОЖЕНИЕ НА УКАЗА ЗА УРЕЖДАНЕ НА ТЕХНИЧЕСКАТА ПРАВОСПОСОБНОСТ И ПРАВОТО НА ЧАСТНА ТЕХНИЧЕСКА ПРАКТИКА
- kind: правилник по прилагане; published 1961-08-25
- lex.bg's history line: Обн. ДВ. бр. 68 от 25 Август 1961г.
- repeal marker read from it: none
- the corpus's amendment rows: 1, the last: ДВ 68/1961 (1961-08-25)
- candidates:
  - material 104002, ДВ 33/2003 (2003-04-11): Наредба за отменяне на Наредба № 6 от 1987 г. за техническата правоспособност в проектирането и строителството [shared words: правоспособност, техническата]

## pravilnik-za-prilozhenie-na-zakona-za-opazvane-na-vazduha-vodite-i-pochvata-ot-z
- title: ПРАВИЛНИК ЗА ПРИЛОЖЕНИЕ НА ЗАКОНА ЗА ОПАЗВАНЕ НА ВЪЗДУХА, ВОДИТЕ И ПОЧВАТА ОТ ЗАМЪРСЯВАНЕ
- kind: правилник по прилагане; published 1964-10-09
- lex.bg's history line: Обн. ДВ. бр.80 от 9 Октомври 1964г. , изм. ДВ. бр. 9 от 31 Януари 1978г.
- repeal marker read from it: none
- the corpus's amendment rows: 2, the last: ДВ 80/1964 (1964-10-09); ДВ 9/1978 (1978-01-31)
- candidates: none share words with this title, and lex.bg's history line carries no repeal marker

## pravilnik-za-prilozhenie-na-zakona-za-urezhdane-pravata-na-litsata-koito-sa-zael
- title: ПРАВИЛНИК ЗА ПРИЛОЖЕНИЕ НА ЗАКОНА ЗА УРЕЖДАНЕ ПРАВАТА НА ЛИЦАТА, КОИТО СА ЗАЕЛИ ИЛИ ПОЛУЧИЛИ ДЪРЖАВНИ ДВОРНИ МЕСТА
- kind: правилник по прилагане; published 1957-07-30
- lex.bg's history line: Обн. ДВ. бр. 61 от 30 Юли 1957г.
- repeal marker read from it: none
- the corpus's amendment rows: 1, the last: ДВ 61/1957 (1957-07-30)
- candidates:
  - material 5791, ДВ 60/2008 (2008-07-04), a line of the general repeal decree „Постановление № 149 от 27 юни 2008 г. за отменяне на нормативни актове на Министерския съвет“: 1. В чл. 1 думите “от вещества от приложение № 4 към чл. 3, ал. 2 ЗКНВП, както и от смеси, в които се съдържат вещества от първа и втора категория на приложение № 4 към чл. 3, ал. 2 ЗКНВП” се заличават. [shared words: които, приложение]
  - material 240221, ДВ 114/2025 (2025-12-24): Наредба за отменяне на Наредба № Н-9 от 2020 г. за условията и реда за вписване в регистъра на лицата, които по занятие предоставят услуги за обмяна между виртуални валути и признати валути без златно покритие, услуги за прехвърляне или обмяна на виртуални активи, услуги по съхраняване на виртуални активи и управление на такива, позволяващо осъществяването на контрол върху активите, и услуги, свързани с публично предлагане на виртуални активи, и на доставчиците на портфейли, които предлагат попечителски услуги [shared words: които, лицата]
