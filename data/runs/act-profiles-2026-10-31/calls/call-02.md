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

The answer file: `/Users/ekimir/swprj/legalize-bg/.claude/worktrees/unruffled-feynman-cd9070/data/runs/act-profiles-2026-10-31/calls/call-02-answer.yaml`

```yaml
# One YAML document: a mapping from each act's slug (every slug of the task, no other) to its verdict
<slug>:
  verdict: <in_force | repealed | unknown>
  repealed_by: <the material id of the candidate repeal title, only when the verdict is repealed; otherwise null>
  evidence: <the facts and lines you relied on, in one or two sentences>
```

## zakon-za-grazhdanskoto-vazduhoplavane
- title: ЗАКОН ЗА ГРАЖДАНСКОТО ВЪЗДУХОПЛАВАНЕ
- kind: закон; published 1972-12-01; lex.bg records it vigente with 57 amendment rows, the last: ДВ 87/2025 (2025-10-17); ДВ 16/2026 (2026-02-10); ДВ 32/2026 (2026-04-01)
- candidate repeal titles:
  - material 93957, ДВ 31/2015 (2015-04-28): Наредба за отменяне на Наредба № 2320 от 2006 г. за условията и реда за постигане на сигурността в гражданското въздухоплаване [shared words: въздухоплаване, гражданското]
  - material 20967, ДВ 41/2004 (2004-05-18): Постановление № 90 от 3 май 2004 г. за отменяне на Наредбата за гражданското състояние, приета с Постановление № 117 на Министерския съвет от 1975 г. [shared words: гражданското]

## zakon-za-izplashtane-na-zadalzheniyata-ugovoreni-v-zlato
- title: ЗАКОН ЗА ИЗПЛАЩАНЕ НА ЗАДЪЛЖЕНИЯТА, УГОВОРЕНИ В ЗЛАТО
- kind: закон; published 1946-08-14; lex.bg records it vigente with 1 amendment rows, the last: ДВ 184/1946 (1946-08-14)
- candidate repeal titles: none share words with this title

## zakon-za-lihvite-varhu-danatsi-taksi-i-drugi-podobni-darzhavni-vzemaniya
- title: ЗАКОН ЗА ЛИХВИТЕ ВЪРХУ ДАНЪЦИ, ТАКСИ И ДРУГИ ПОДОБНИ ДЪРЖАВНИ ВЗЕМАНИЯ
- kind: закон; published 1957-11-12; lex.bg records it vigente with 7 amendment rows, the last: ДВ 51/1997 (1997-06-27); ДВ 153/1998 (1998-12-23); ДВ 103/1999 (1999-11-30)
- candidate repeal titles: none share words with this title

## zakon-za-litsata-i-semeystvoto
- title: ЗАКОН ЗА ЛИЦАТА И СЕМЕЙСТВОТО
- kind: закон; published 1949-08-09; lex.bg records it vigente with 20 amendment rows, the last: ДВ 67/1999 (1999-07-27); ДВ 81/2000 (2000-10-06); ДВ 120/2002 (2002-12-29)
- candidate repeal titles:
  - material 1419, ДВ 15/2006 (2006-02-17): Постановление № 25 от 6 февруари 2006 г. за отменяне на Наредбата за условията и реда за издаване на разрешителни за риболов и регистрация на лицата, развъждащи и отглеждащи риба и други водни организми, приета с Постановление № 269 на Министерския съвет от 2001 г. [shared words: лицата]
  - material 240221, ДВ 114/2025 (2025-12-24): Наредба за отменяне на Наредба № Н-9 от 2020 г. за условията и реда за вписване в регистъра на лицата, които по занятие предоставят услуги за обмяна между виртуални валути и признати валути без златно покритие, услуги за прехвърляне или обмяна на виртуални активи, услуги по съхраняване на виртуални активи и управление на такива, позволяващо осъществяването на контрол върху активите, и услуги, свързани с публично предлагане на виртуални активи, и на доставчиците на портфейли, които предлагат попечителски услуги [shared words: лицата]

## zakon-za-nasledstvoto
- title: ЗАКОН ЗА НАСЛЕДСТВОТО
- kind: закон; published 1949-01-29; lex.bg records it vigente with 12 amendment rows, the last: ДВ 34/2000 (2000-04-25); ДВ 59/2007 (2007-07-20); ДВ 47/2009 (2009-06-23)
- candidate repeal titles: none share words with this title

## zakon-za-normativnite-aktove
- title: ЗАКОН ЗА НОРМАТИВНИТЕ АКТОВЕ
- kind: закон; published 1973-04-03; lex.bg records it vigente with 6 amendment rows, the last: ДВ 46/2007 (2007-06-12); ДВ 34/2016 (2016-05-03); ДВ 30/2026 (2026-03-27)
- candidate repeal titles:
  - material 96071, ДВ 57/2015 (2015-07-28): Наредба за отменяне на Наредба № 2 от 2006 г. за условията и реда за предоставяне на средства за компенсиране на намалените приходи от прилагането на цени за пътуване по автомобилния транспорт, предвидени в нормативни актове за определени категории пътници и Наредба № 3 от 2005 г. за условията и реда за предоставяне на средства за субсидиране на превоза на пътниците по нерентабилни автобусни линии във вътрешноградския транспорт и транспорта в планински и други райони [shared words: актове]

## zakon-za-oblekchenie-rabotata-na-varhovniya-kasatsionen-sad-i-vav-vrazka-s-tova-
- title: ЗАКОН ЗА ОБЛЕКЧЕНИЕ РАБОТАТА НА ВЪРХОВНИЯ КАСАЦИОНЕН СЪД И ВЪВ ВРЪЗКА С ТОВА ЗА ИЗМЕНЕНИЕ НА ЗАКОНИТЕ: 1) ЗА ПЕНСИИТЕ ЗА ИЗСЛУЖЕНО ВРЕМЕ; 2) ЗА ПЕНСИИТЕ И ВЪЗНАГРАЖДЕНИЯТА НА ПОБОРНИЦИТЕ И ОПЪЛЧЕНЦИТЕ; 3) ЗА ПЕНСИИТЕ НА ПОСТРАДАЛИТЕ САНИТАРНИ СЛУЖИТЕЛИ В БОРБА ПРОТИВ ЕПИДЕМИИТЕ: ПЕТНИСТ ТИФ, ХОЛЕРА И ЧУМА; 4) ЗА ПЕНСИИТЕ НА СЛУЖИТЕЛИТЕ ПРИ ДЪРЖАВНИТЕ И ИЗБОРНИТЕ УЧРЕЖДЕНИЯ; 5) ЗА БЛАГОУСТРОЙСТВОТО НА НАСЕЛЕНИТЕ МЕСТА В БЪЛГАРИЯ И 6) ЗА УГЛАВНОТО СЪДОПРОИЗВОДСТВО
- kind: закон; published 1928-10-10; lex.bg records it vigente with 1 amendment rows, the last: ДВ 156/1928 (1928-10-10)
- candidate repeal titles:
  - material 87379, ДВ 69/2014 (2014-08-19): Инструкция за отменяне на Инструкция № Із-2453 от 2012 г. за реда за разпределяне на работното време на държавните служители в Министерството на вътрешните работи, отчитането му и компенсиране на работата извън установеното работно време [shared words: време, държавните, работата, служители]
  - material 3143, ДВ 5/2007 (2007-01-18): Наредба за отменяне на Наредба № 4 от 1999 г. за защита от шум на територията на населените места [shared words: места, населените]
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
- kind: закон; published 1964-09-15; lex.bg records it vigente with 1 amendment rows, the last: ДВ 73/1964 (1964-09-15)
- candidate repeal titles: none share words with this title

## zakon-za-ofitserskite-sabraniya
- title: ЗАКОН ЗА ОФИЦЕРСКИТЕ СЪБРАНИЯ
- kind: закон; published 1948-03-19; lex.bg records it vigente with 1 amendment rows, the last: ДВ 64/1948 (1948-03-19)
- candidate repeal titles: none share words with this title

## zakon-za-opazvane-na-selskostopanskoto-imushtestvo
- title: ЗАКОН ЗА ОПАЗВАНЕ НА СЕЛСКОСТОПАНСКОТО ИМУЩЕСТВО
- kind: закон; published 1974-07-12; lex.bg records it vigente with 20 amendment rows, the last: ДВ 58/2017 (2017-07-18); ДВ 102/2022 (2022-12-23); ДВ 102/2023 (2023-12-08)
- candidate repeal titles: none share words with this title
