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

The answer file: `/Users/ekimir/swprj/legalize-bg/.claude/worktrees/unruffled-feynman-cd9070/data/runs/act-profiles-2026-10-31/calls/call-02-answer.yaml`

```yaml
# One YAML document: a mapping from each act's slug (every slug of the task, no other) to its verdict
<slug>:
  verdict: <in_force | repealed | unknown>
  repealed_by: <the material id of the candidate that repeals it, or 0 for lex.bg's own repeal marker, only when the verdict is repealed; otherwise null>
  evidence: <the facts and lines you relied on, in one or two sentences>
```

## zakon-za-grazhdanskoto-vazduhoplavane
- title: ЗАКОН ЗА ГРАЖДАНСКОТО ВЪЗДУХОПЛАВАНЕ
- kind: закон; published 1972-12-01
- lex.bg's history line: Обн. ДВ. бр. 94 от 1 Декември 1972г. , изм. ДВ. бр. 30 от 13 Април 1990г. , изм. ДВ. бр. 16 от 21 Февруари 1997г. , изм. ДВ. бр. 85 от 24 Юли 1998г. , […] 23 Февруари 2021г. , изм. ДВ. бр. 102 от 23 Декември 2022г. , изм. ДВ. бр. 102 от 8 Декември 2023г. , изм. ДВ. бр. 79 от 17 Септември 2024г. , изм. и доп. ДВ. бр. 87 от 17 Октомври 2025г. , изм. и доп. ДВ. бр. 16 от 10 Февруари 2026г. , изм. ДВ. бр. 32 от 1 Април 2026г.
- repeal marker read from it: none
- the corpus's amendment rows: 57, the last: ДВ 87/2025 (2025-10-17); ДВ 16/2026 (2026-02-10); ДВ 32/2026 (2026-04-01)
- candidates:
  - material 93957, ДВ 31/2015 (2015-04-28): Наредба за отменяне на Наредба № 2320 от 2006 г. за условията и реда за постигане на сигурността в гражданското въздухоплаване [shared words: въздухоплаване, гражданското]
  - material 20967, ДВ 41/2004 (2004-05-18): Постановление № 90 от 3 май 2004 г. за отменяне на Наредбата за гражданското състояние, приета с Постановление № 117 на Министерския съвет от 1975 г. [shared words: гражданското]

## zakon-za-izplashtane-na-zadalzheniyata-ugovoreni-v-zlato
- title: ЗАКОН ЗА ИЗПЛАЩАНЕ НА ЗАДЪЛЖЕНИЯТА, УГОВОРЕНИ В ЗЛАТО
- kind: закон; published 1946-08-14
- lex.bg's history line: Обн. ДВ. бр. 184 от 14 Август 1946г.
- repeal marker read from it: none
- the corpus's amendment rows: 1, the last: ДВ 184/1946 (1946-08-14)
- candidates: none share words with this title, and lex.bg's history line carries no repeal marker

## zakon-za-lihvite-varhu-danatsi-taksi-i-drugi-podobni-darzhavni-vzemaniya
- title: ЗАКОН ЗА ЛИХВИТЕ ВЪРХУ ДАНЪЦИ, ТАКСИ И ДРУГИ ПОДОБНИ ДЪРЖАВНИ ВЗЕМАНИЯ
- kind: закон; published 1957-11-12
- lex.bg's history line: Обн. ДВ. бр. 91 от 12 Ноември 1957г. , изм. ДВ. бр. 52 от 2 Юли 1965г. , изм. ДВ. бр. 38 от 19 Май 1989г. , изм. ДВ. бр. 21 от 15 Март 1991г. , изм. ДВ. бр. 51 от 27 Юни 1997г. , изм. ДВ. бр. 153 от 23 Декември 1998г. , изм. ДВ. бр. 103 от 30 Ноември 1999г.
- repeal marker read from it: none
- the corpus's amendment rows: 7, the last: ДВ 51/1997 (1997-06-27); ДВ 153/1998 (1998-12-23); ДВ 103/1999 (1999-11-30)
- candidates: none share words with this title, and lex.bg's history line carries no repeal marker

## zakon-za-litsata-i-semeystvoto
- title: ЗАКОН ЗА ЛИЦАТА И СЕМЕЙСТВОТО
- kind: закон; published 1949-08-09
- lex.bg's history line: Обн. ДВ. бр. 182 от 9 Август 1949г. , попр. ДВ. бр. 193 от 22 Август 1949г. , изм. ДВ. бр. 12 от 9 Февруари 1951г. , изм. ДВ. бр. 12 от 8 Февруари 195 […] Май 1979г. , изм. ДВ. бр. 41 от 28 Май 1985г. , изм. ДВ. бр. 46 от 16 Юни 1989г. , изм. ДВ. бр. 20 от 9 Март 1990г. , изм. ДВ. бр. 15 от 18 Февруари 1994г. , изм. ДВ. бр. 67 от 27 Юли 1999г. , изм. ДВ. бр. 81 от 6 Октомври 2000г. , изм. ДВ. бр. 120 от 29 Декември 2002г.
- repeal marker read from it: none
- the corpus's amendment rows: 20, the last: ДВ 67/1999 (1999-07-27); ДВ 81/2000 (2000-10-06); ДВ 120/2002 (2002-12-29)
- candidates:
  - material 1419, ДВ 15/2006 (2006-02-17): Постановление № 25 от 6 февруари 2006 г. за отменяне на Наредбата за условията и реда за издаване на разрешителни за риболов и регистрация на лицата, развъждащи и отглеждащи риба и други водни организми, приета с Постановление № 269 на Министерския съвет от 2001 г. [shared words: лицата]
  - material 240221, ДВ 114/2025 (2025-12-24): Наредба за отменяне на Наредба № Н-9 от 2020 г. за условията и реда за вписване в регистъра на лицата, които по занятие предоставят услуги за обмяна между виртуални валути и признати валути без златно покритие, услуги за прехвърляне или обмяна на виртуални активи, услуги по съхраняване на виртуални активи и управление на такива, позволяващо осъществяването на контрол върху активите, и услуги, свързани с публично предлагане на виртуални активи, и на доставчиците на портфейли, които предлагат попечителски услуги [shared words: лицата]

## zakon-za-nasledstvoto
- title: ЗАКОН ЗА НАСЛЕДСТВОТО
- kind: закон; published 1949-01-29
- lex.bg's history line: Обн. ДВ. бр. 22 от 29 Януари 1949г. , попр. ДВ. бр. 41 от 21 Февруари 1949г. , изм. ДВ. бр. 275 от 22 Ноември 1950г. , изм. ДВ. бр. 41 от 28 Май 1985г […] и 1992г. , изм. ДВ. бр. 21 от 12 Март 1996г. , изм. ДВ. бр. 104 от 6 Декември 1996г. , доп. ДВ. бр. 117 от 10 Декември 1997г. , доп. ДВ. бр. 96 от 5 Ноември 1999г. , изм. ДВ. бр. 34 от 25 Април 2000г. , изм. ДВ. бр. 59 от 20 Юли 2007г. , изм. ДВ. бр. 47 от 23 Юни 2009г.
- repeal marker read from it: none
- the corpus's amendment rows: 12, the last: ДВ 34/2000 (2000-04-25); ДВ 59/2007 (2007-07-20); ДВ 47/2009 (2009-06-23)
- candidates: none share words with this title, and lex.bg's history line carries no repeal marker

## zakon-za-normativnite-aktove
- title: ЗАКОН ЗА НОРМАТИВНИТЕ АКТОВЕ
- kind: закон; published 1973-04-03
- lex.bg's history line: Обн. ДВ. бр. 27 от 3 Април 1973г. , изм. ДВ. бр. 65 от 21 Юли 1995г. , доп. ДВ. бр. 55 от 17 Юни 2003г. , изм. ДВ. бр. 46 от 12 Юни 2007г. , изм. и доп. ДВ. бр. 34 от 3 Май 2016г. , изм. и доп. ДВ. бр. 30 от 27 Март 2026г.
- repeal marker read from it: none
- the corpus's amendment rows: 6, the last: ДВ 46/2007 (2007-06-12); ДВ 34/2016 (2016-05-03); ДВ 30/2026 (2026-03-27)
- candidates:
  - material 2313, ДВ 63/2006 (2006-08-04), a line of the general repeal decree „Постановление № 183 от 25 юли 2006 г. за отменяне на нормативни актове на Министерския съвет“: за отменяне на нормативни актове на Министерския съвет [shared words: актове]
  - material 2755, ДВ 88/2006 (2006-10-31), a line of the general repeal decree „Постановление № 281 от 20 октомври 2006 г. за отменяне на нормативни актове на Министерския съвет“: за отменяне на нормативни актове на Министерския съвет [shared words: актове]
  - material 2758, ДВ 88/2006 (2006-10-31), a line of the general repeal decree „Постановление № 284 от 23 октомври 2006 г. за отменяне на нормативни актове на Министерския съвет“: за отменяне на нормативни актове на Министерския съвет [shared words: актове]
  - material 5791, ДВ 60/2008 (2008-07-04), a line of the general repeal decree „Постановление № 149 от 27 юни 2008 г. за отменяне на нормативни актове на Министерския съвет“: за отменяне на нормативни актове на Министерския съвет [shared words: актове]
  - material 15239, ДВ 34/2005 (2005-04-19), a line of the general repeal decree „Постановление № 65 от 8 април 2005 г. за отменяне на нормативни актове“: за отменяне на нормативни актове [shared words: актове]
  - material 31908, ДВ 29/2010 (2010-04-16), a line of the general repeal decree „Постановление № 62 от 8 април 2010 г. за отменяне на нормативни актове на Министерския съвет“: за отменяне на нормативни актове на Министерския съвет [shared words: актове]
  - material 31928, ДВ 29/2010 (2010-04-16), a line of the general repeal decree „Постановление № 61 от 8 април 2010 г. за отменяне на нормативни актове на Министерския съвет“: за отменяне на нормативни актове на Министерския съвет [shared words: актове]
  - material 75261, ДВ 38/2013 (2013-04-23), a line of the general repeal decree „Постановление № 91 от 15 април 2013 г. за отменяне на нормативни актове на Министерския съвет“: за отменяне на нормативни актове на Министерския съвет [shared words: актове]
  - material 96071, ДВ 57/2015 (2015-07-28): Наредба за отменяне на Наредба № 2 от 2006 г. за условията и реда за предоставяне на средства за компенсиране на намалените приходи от прилагането на цени за пътуване по автомобилния транспорт, предвидени в нормативни актове за определени категории пътници и Наредба № 3 от 2005 г. за условията и реда за предоставяне на средства за субсидиране на превоза на пътниците по нерентабилни автобусни линии във вътрешноградския транспорт и транспорта в планински и други райони [shared words: актове]
  - material 119269, ДВ 87/2017 (2017-10-31), a line of the general repeal decree „Постановление № 242 от 26 октомври 2017 г. за отменяне на нормативни актове на Министерския съвет“: за отменяне на нормативни актове на Министерския съвет [shared words: актове]
  - material 148685, ДВ 50/2020 (2020-06-02), a line of the general repeal decree „Постановление № 110 от 28 май 2020 г. за отменяне на нормативни актове на Министерския съвет“: за отменяне на нормативни актове на Министерския съвет [shared words: актове]
  - material 173735, ДВ 41/2022 (2022-06-03), a line of the general repeal decree „Постановление № 102 от 30 май 2022 г. за отменяне на нормативни актове на Министерския съвет“: за отменяне на нормативни актове на Министерския съвет [shared words: актове]

## zakon-za-oblekchenie-rabotata-na-varhovniya-kasatsionen-sad-i-vav-vrazka-s-tova-
- title: ЗАКОН ЗА ОБЛЕКЧЕНИЕ РАБОТАТА НА ВЪРХОВНИЯ КАСАЦИОНЕН СЪД И ВЪВ ВРЪЗКА С ТОВА ЗА ИЗМЕНЕНИЕ НА ЗАКОНИТЕ: 1) ЗА ПЕНСИИТЕ ЗА ИЗСЛУЖЕНО ВРЕМЕ; 2) ЗА ПЕНСИИТЕ И ВЪЗНАГРАЖДЕНИЯТА НА ПОБОРНИЦИТЕ И ОПЪЛЧЕНЦИТЕ; 3) ЗА ПЕНСИИТЕ НА ПОСТРАДАЛИТЕ САНИТАРНИ СЛУЖИТЕЛИ В БОРБА ПРОТИВ ЕПИДЕМИИТЕ: ПЕТНИСТ ТИФ, ХОЛЕРА И ЧУМА; 4) ЗА ПЕНСИИТЕ НА СЛУЖИТЕЛИТЕ ПРИ ДЪРЖАВНИТЕ И ИЗБОРНИТЕ УЧРЕЖДЕНИЯ; 5) ЗА БЛАГОУСТРОЙСТВОТО НА НАСЕЛЕНИТЕ МЕСТА В БЪЛГАРИЯ И 6) ЗА УГЛАВНОТО СЪДОПРОИЗВОДСТВО
- kind: закон; published 1928-10-10
- lex.bg's history line: Обн. ДВ. бр. 156 от 10 Октомври 1928г.
- repeal marker read from it: none
- the corpus's amendment rows: 1, the last: ДВ 156/1928 (1928-10-10)
- candidates:
  - material 87379, ДВ 69/2014 (2014-08-19): Инструкция за отменяне на Инструкция № Із-2453 от 2012 г. за реда за разпределяне на работното време на държавните служители в Министерството на вътрешните работи, отчитането му и компенсиране на работата извън установеното работно време [shared words: време, държавните, работата, служители]
  - material 2758, ДВ 88/2006 (2006-10-31), a line of the general repeal decree „Постановление № 284 от 23 октомври 2006 г. за отменяне на нормативни актове на Министерския съвет“: 27. Постановление № 217 на Министерския съвет от 1994 г. за освобождаване от митни сборове вноса на безвъзмездно доставените в Република България стоки във връзка с изграждането на центрове за квалификация и повишаване на квалификацията в рамките на немско-българския проект за намаляване на емиграцията (ДВ, бр. 86 от 1994 г.). [shared words: българия, връзка, във]
  - material 3143, ДВ 5/2007 (2007-01-18): Наредба за отменяне на Наредба № 4 от 1999 г. за защита от шум на територията на населените места [shared words: места, населените]
  - material 5791, ДВ 60/2008 (2008-07-04), a line of the general repeal decree „Постановление № 149 от 27 юни 2008 г. за отменяне на нормативни актове на Министерския съвет“: 3. В чл. 8, ал. 2 и чл. 10, ал. 2 думите “Закона за Върховния административен съд” се заменят с “Административнопроцесуалния кодекс”. [shared words: върховния, съд]
  - material 8162, ДВ 75/2008 (2008-08-26): Наредба за отменяне на Наредба № Iз-441 от 2008 г. за определяне на категориите служители, осъществяващи правомощията си в униформено облекло, неговия вид и модел, реда за предоставянето му, както и другите принадлежности, свързани с изпълнението на служебните задължения на служителите, върху които са поставени символи и отличителни знаци на структурните звена на Министерството на вътрешните работи [shared words: служители, служителите]
  - material 21286, ДВ 30/2004 (2004-04-13): Наредба за отменяне на Наредба № 3 от 1989 г. за запазване на сградните и благоустройствените фондове в населените места [shared words: места, населените]
  - material 104005, ДВ 38/2016 (2016-05-20): Постановление № 123 от 17 май 2016 г. за отмяна на Постановление № 260 на Министерския съвет от 2003 г. за определяне възнагражденията на кадровите военнослужещи при участие на Република България в операции по поддържане на мира и в мисии, провеждани под егидата на международни организации [shared words: българия, възнагражденията]
  - material 129046, ДВ 66/2018 (2018-08-10): Наредба за отменяне на Наредба № Н-5 от 2014 г. за подбор на военнослужещи и цивилни служители от Министерството на отбраната, структурите на пряко подчинение на министъра на отбраната и от Българската армия за заемане на длъжности в задграничните представителства на Република България, в щабове или органи на международни организации и на други международни инициативи [shared words: българия, служители]
  - material 144352, ДВ 1/2020 (2020-01-03): Постановление № 378 от 27 декември 2019 г. за отменяне на Постановление № 112 на Министерския съвет от 2019 г. за одобряване на промени по бюджета на Министерството на здравеопазването за 2019 г. във връзка с увеличаване капитала на търговско дружество [shared words: връзка, във]
  - material 166232, ДВ 104/2021 (2021-12-12): Постановление № 426 от 9 декември 2021 г. за отменяне на Постановление № 6 на Министерския съвет от 2021 г. за одобряване на промени по бюджета на Министерството на финансите за 2021 г. във връзка с увеличаване капитала на търговско дружество [shared words: връзка, във]
  - material 174679, ДВ 53/2022 (2022-07-08): Постановление № 155 от 5 юли 2022 г. за отменяне на Постановление № 33 на Министерския съвет от 2022 г. за одобряване на промени по бюджета на Министерството на земеделието за 2022 г. във връзка с увеличаване капитала на еднолично акционерно дружество с държавно участие в капитала „Врана“ – ЕАД [shared words: връзка, във]
  - material 239806, ДВ 109/2025 (2025-12-16): Наредба за отменяне на Наредба № 24 от 26 април 1999 г. за обмяна на старите банкноти и монети с нови банкноти и монети във връзка с деноминацията на лева [shared words: връзка, във]

## zakon-za-obyavyavane-na-sela-i-selishta-za-gradove-i-selishta-ot-gradski-tip
- title: ЗАКОН ЗА ОБЯВЯВАНЕ НА СЕЛА И СЕЛИЩА ЗА ГРАДОВЕ И СЕЛИЩА ОТ ГРАДСКИ ТИП
- kind: закон; published 1964-09-15
- lex.bg's history line: Обн. ДВ. бр. 73 от 15 Септември 1964г.
- repeal marker read from it: none
- the corpus's amendment rows: 1, the last: ДВ 73/1964 (1964-09-15)
- candidates: none share words with this title, and lex.bg's history line carries no repeal marker

## zakon-za-ofitserskite-sabraniya
- title: ЗАКОН ЗА ОФИЦЕРСКИТЕ СЪБРАНИЯ
- kind: закон; published 1948-03-19
- lex.bg's history line: Обн. ДВ. бр. 64 от 19 Март 1948г.
- repeal marker read from it: none
- the corpus's amendment rows: 1, the last: ДВ 64/1948 (1948-03-19)
- candidates: none share words with this title, and lex.bg's history line carries no repeal marker

## zakon-za-opazvane-na-selskostopanskoto-imushtestvo
- title: ЗАКОН ЗА ОПАЗВАНЕ НА СЕЛСКОСТОПАНСКОТО ИМУЩЕСТВО
- kind: закон; published 1974-07-12
- lex.bg's history line: Обн. ДВ. бр. 54 от 12 Юли 1974г. , изм. ДВ. бр. 22 от 16 Март 1976г. , изм. ДВ. бр. 35 от 4 Май 1979г. , изм. ДВ. бр. 36 от 8 Май 1979г. , изм. ДВ. бр […] 8г. , изм. ДВ. бр. 80 от 9 Октомври 2009г. , изм. ДВ. бр. 88 от 9 Ноември 2010г. , изм. ДВ. бр. 19 от 8 Март 2011г. , изм. ДВ. бр. 77 от 9 Октомври 2012г. , изм. ДВ. бр. 58 от 18 Юли 2017г. , изм. ДВ. бр. 102 от 23 Декември 2022г. , изм. ДВ. бр. 102 от 8 Декември 2023г.
- repeal marker read from it: none
- the corpus's amendment rows: 20, the last: ДВ 58/2017 (2017-07-18); ДВ 102/2022 (2022-12-23); ДВ 102/2023 (2023-12-08)
- candidates: none share words with this title, and lex.bg's history line carries no repeal marker
