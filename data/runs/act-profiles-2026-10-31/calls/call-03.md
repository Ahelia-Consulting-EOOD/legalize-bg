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

The answer file: `/Users/ekimir/swprj/legalize-bg/.claude/worktrees/unruffled-feynman-cd9070/data/runs/act-profiles-2026-10-31/calls/call-03-answer.yaml`

```yaml
# One YAML document: a mapping from each act's slug (every slug of the task, no other) to its verdict
<slug>:
  verdict: <in_force | repealed | unknown>
  repealed_by: <the material id of the candidate that repeals it, or 0 for lex.bg's own repeal marker, only when the verdict is repealed; otherwise null>
  evidence: <the facts and lines you relied on, in one or two sentences>
```

## zakon-za-oproshtavane-na-zadalzheniya-kam-darzhavata
- title: ЗАКОН ЗА ОПРОЩАВАНЕ НА ЗАДЪЛЖЕНИЯ КЪМ ДЪРЖАВАТА
- kind: закон; published 1964-09-15
- lex.bg's history line: Обн. ДВ. бр. 73 от 15 Септември 1964г.
- repeal marker read from it: none
- the corpus's amendment rows: 1, the last: ДВ 73/1964 (1964-09-15)
- candidates: none share words with this title, and lex.bg's history line carries no repeal marker

## zakon-za-otgovornostta-na-darzhavata-i-obshtinite-za-vredi-zagl-izm-dv-br-30-ot-
- title: ЗАКОН ЗА ОТГОВОРНОСТТА НА ДЪРЖАВАТА И ОБЩИНИТЕ ЗА ВРЕДИ (ЗАГЛ. ИЗМ. - ДВ, БР. 30 ОТ 11.04.2006 Г., В СИЛА ОТ 12.07.2006 Г.)
- kind: закон; published 1988-08-05
- lex.bg's history line: Обн. ДВ. бр. 60 от 5 Август 1988г. , изм. ДВ. бр. 59 от 9 Юли 1993г. , изм. ДВ. бр. 12 от 9 Февруари 1996г. , доп. ДВ. бр. 67 от 27 Юли 1999г. , изм.  […]  , доп. ДВ. бр. 48 от 2 Юни 2023г. , изм. ДВ. бр. 84 от 6 Октомври 2023г. , доп. ДВ. бр. 36 от 23 Април 2024г. , изм. и доп. ДВ. бр. 63 от 1 Август 2025г. , изм. ДВ. бр. 16 от 10 Февруари 2026г. , изм. ДВ. бр. 51 от 5 Юни 2026г. , изм. и доп. ДВ. бр. 59 от 30 Юни 2026г.
- repeal marker read from it: none
- the corpus's amendment rows: 21, the last: ДВ 16/2026 (2026-02-10); ДВ 51/2026 (2026-06-05); ДВ 59/2026 (2026-06-30)
- candidates: none share words with this title, and lex.bg's history line carries no repeal marker

## zakon-za-otmenyavane-na-vsichki-zakoni-izdadeni-predi-9091944-g
- title: ЗАКОН ЗА ОТМЕНЯВАНЕ НА ВСИЧКИ ЗАКОНИ, ИЗДАДЕНИ ПРЕДИ 9.09.1944 Г.
- kind: закон; published 1951-11-20
- lex.bg's history line: Обн. ДВ. бр. 93 от 20 Ноември 1951г.
- repeal marker read from it: none
- the corpus's amendment rows: 1, the last: ДВ 93/1951 (1951-11-20)
- candidates: none share words with this title, and lex.bg's history line carries no repeal marker

## zakon-za-sobstvenostta
- title: ЗАКОН ЗА СОБСТВЕНОСТТА
- kind: закон; published 1951-11-16
- lex.bg's history line: Обн. ДВ. бр. 92 от 16 Ноември 1951г. , изм. ДВ. бр. 12 от 11 Февруари 1958г. , изм. ДВ. бр. 90 от 8 Ноември 1960г. , изм. ДВ. бр. 99 от 20 Декември 19 […]  ДВ. бр. 100 от 21 Декември 2010г. , изм. ДВ. бр. 57 от 26 Юли 2011г. , изм. ДВ. бр. 105 от 29 Декември 2011г. , изм. и доп. ДВ. бр. 107 от 24 Декември 2014г. , изм. ДВ. бр. 7 от 19 Януари 2018г. , доп. ДВ. бр. 18 от 28 Февруари 2020г. , изм. ДВ. бр. 18 от 4 Март 2022г.
- repeal marker read from it: none
- the corpus's amendment rows: 37, the last: ДВ 7/2018 (2018-01-19); ДВ 18/2020 (2020-02-28); ДВ 18/2022 (2022-03-04)
- candidates: none share words with this title, and lex.bg's history line carries no repeal marker

## zakon-za-tvorcheskite-fondove
- title: ЗАКОН ЗА ТВОРЧЕСКИТЕ ФОНДОВЕ
- kind: закон; published 1973-04-03
- lex.bg's history line: Обн. ДВ. бр. 27 от 3 Април 1973г. , изм. и доп. ДВ. бр. 20 от 9 Март 1979г. , изм. ДВ. бр. 153 от 23 Декември 1998г.
- repeal marker read from it: none
- the corpus's amendment rows: 3, the last: ДВ 27/1973 (1973-04-03); ДВ 20/1979 (1979-03-09); ДВ 153/1998 (1998-12-23)
- candidates:
  - material 21286, ДВ 30/2004 (2004-04-13): Наредба за отменяне на Наредба № 3 от 1989 г. за запазване на сградните и благоустройствените фондове в населените места [shared words: фондове]
  - material 21997, ДВ 45/2009 (2009-06-16): Наредба за отменяне на Наредба № 247 от 1995 г. за звената за обработка на архивни фондове и документи на физически и юридически лица, издадена от Главно управление на архивите при Министерския съвет [shared words: фондове]
  - material 27320, ДВ 96/2009 (2009-12-04): Постановление № 277 от 26 ноември 2009 г. за отменяне на Постановление № 197 на Министерския съвет от 2008 г. за материално стимулиране на служителите, изпълняващи функции по усвояване на средства по структурните фондове и предприсъединителните програми на Европейския съюз [shared words: фондове]
  - material 57288, ДВ 80/2011 (2011-10-14): Наредба за отменяне на Наредба № Н-10 от 2005 г. за условията и реда за експлоатация и достъп до информационните фондове на служба „Военна полиция“ [shared words: фондове]
  - material 70892, ДВ 98/2012 (2012-12-11): Наредба за отменяне на Наредба № Із-1215 от 2006 г. за реда за достъп до информационните фондове на Министерството на вътрешните работи [shared words: фондове]
  - material 116401, ДВ 61/2017 (2017-07-28): Инструкция за отменяне на Инструкция № И-4 от 2011 г. за подбора на военнослужещи и граждански лица за работа в служба „Военна информация“ и на Инструкция № 2 от 2011 г. за определяне на реда за създаване, използване и закриване на информационните фондове и за контрола върху тях в служба „Военна информация“ [shared words: фондове]

## zakon-za-urezhdane-pravata-na-kupuvachi-na-nedvizhimi-imoti-s-chastni-dogovori
- title: ЗАКОН ЗА УРЕЖДАНЕ ПРАВАТА НА КУПУВАЧИ НА НЕДВИЖИМИ ИМОТИ С ЧАСТНИ ДОГОВОРИ
- kind: закон; published 1947-07-26
- lex.bg's history line: Обн. ДВ. бр. 171 от 26 Юли 1947г.
- repeal marker read from it: none
- the corpus's amendment rows: 1, the last: ДВ 171/1947 (1947-07-26)
- candidates: none share words with this title, and lex.bg's history line carries no repeal marker

## zakon-za-urezhdane-pravata-na-litsata-koito-sa-zaeli-ili-poluchili-darzhavni-dvo
- title: ЗАКОН ЗА УРЕЖДАНЕ ПРАВАТА НА ЛИЦАТА, КОИТО СА ЗАЕЛИ ИЛИ ПОЛУЧИЛИ ДЪРЖАВНИ ДВОРНИ МЕСТА
- kind: закон; published 1956-11-09
- lex.bg's history line: Обн. ДВ. бр. 90 от 9 Ноември 1956г.
- repeal marker read from it: none
- the corpus's amendment rows: 1, the last: ДВ 90/1956 (1956-11-09)
- candidates:
  - material 240221, ДВ 114/2025 (2025-12-24): Наредба за отменяне на Наредба № Н-9 от 2020 г. за условията и реда за вписване в регистъра на лицата, които по занятие предоставят услуги за обмяна между виртуални валути и признати валути без златно покритие, услуги за прехвърляне или обмяна на виртуални активи, услуги по съхраняване на виртуални активи и управление на такива, позволяващо осъществяването на контрол върху активите, и услуги, свързани с публично предлагане на виртуални активи, и на доставчиците на портфейли, които предлагат попечителски услуги [shared words: които, лицата]

## zakon-za-vanshnata-targoviya
- title: ЗАКОН ЗА ВЪНШНАТА ТЪРГОВИЯ
- kind: закон; published 1969-12-05
- lex.bg's history line: Обн. ДВ. бр. 94 от 5 Декември 1969г. , изм. ДВ. бр. 60 от 2 Август 1974г. , изм. ДВ. бр. 63 от 6 Август 1976г. , изм. ДВ. бр. 4 от 13 Януари 1989г.
- repeal marker read from it: none
- the corpus's amendment rows: 4, the last: ДВ 60/1974 (1974-08-02); ДВ 63/1976 (1976-08-06); ДВ 4/1989 (1989-01-13)
- candidates:
  - material 21361, ДВ 25/2004 (2004-03-26): Постановление № 60 от 16 март 2004 г. за отменяне на Постановление № 15 на Министерския съвет от 2002 г. за изпълнение от 1 януари 2002 г. на задълженията на Република България, произтичащи от Споразумението за свободна търговия между Република България и Република Естония [shared words: търговия]
  - material 108524, ДВ 85/2016 (2016-10-28): Наредба за отменяне на Наредба № 44 от 2001 г. за търговия с комбинирани фуражи [shared words: търговия]

## zakon-za-zadalzheniyata-i-dogovorite
- title: ЗАКОН ЗА ЗАДЪЛЖЕНИЯТА И ДОГОВОРИТЕ
- kind: закон; published 1950-12-05
- lex.bg's history line: Попр. ДВ. бр. 2 от 5 Декември 1950г. , обн. ДВ. бр. 275 от 22 Ноември 1950г. , изм. ДВ. бр. 69 от 28 Август 1951г. , изм. ДВ. бр. 92 от 7 Ноември 1952 […] Май 2006г. , изм. ДВ. бр. 59 от 20 Юли 2007г. , изм. ДВ. бр. 92 от 13 Ноември 2007г. , изм. ДВ. бр. 50 от 30 Май 2008г. , изм. ДВ. бр. 96 от 1 Декември 2017г. , доп. ДВ. бр. 42 от 22 Май 2018г. , доп. ДВ. бр. 102 от 1 Декември 2020г. , изм. ДВ. бр. 35 от 27 Април 2021г.
- repeal marker read from it: none
- the corpus's amendment rows: 27, the last: ДВ 42/2018 (2018-05-22); ДВ 102/2020 (2020-12-01); ДВ 35/2021 (2021-04-27)
- candidates:
  - material 2758, ДВ 88/2006 (2006-10-31), a line of the general repeal decree „Постановление № 284 от 23 октомври 2006 г. за отменяне на нормативни актове на Министерския съвет“: 9. Постановление № 416 на Министерския съвет от 1997 г. за освобождаване от митни сборове вноса на стоките, получавани по договорите за предоставяне на безвъзмездна помощ в изпълнение на проектите по Инициативата за развитие на Южните Балкани (обн., ДВ, бр. 106 от 1997 г.; изм., бр. 4 от 2001 г.). [shared words: договорите]
  - material 21361, ДВ 25/2004 (2004-03-26): Постановление № 60 от 16 март 2004 г. за отменяне на Постановление № 15 на Министерския съвет от 2002 г. за изпълнение от 1 януари 2002 г. на задълженията на Република България, произтичащи от Споразумението за свободна търговия между Република България и Република Естония [shared words: задълженията]
  - material 121425, ДВ 4/2018 (2018-01-09): Наредба за отменяне на Наредба № 23 от 2006 г. за реда за водене на регистър на договорите за влог на зърно от регистрирани зърнохранилища [shared words: договорите]
  - material 217963, ДВ 49/2024 (2024-06-11), a line of the general repeal decree „Постановление № 205 от 7 юни 2024 г. за отменяне на нормативни актове на Министерския съвет“: § 1. Наредбата за реда за използване на държавните дългосрочни облигации, емитирани по Закона за уреждане на необслужваните кредити, договорени до 31 декември 1990 г., за погасяване на задълженията към държавата, възникнали по реда на същия закон, приета с Постановление № 22 на Министерския съвет от 1995 г. (ДВ, бр. 12 от 1995 г.), се отменя. [shared words: задълженията]

## zakon-za-zhilishtnostroitelnite-kooperatsii
- title: ЗАКОН ЗА ЖИЛИЩНОСТРОИТЕЛНИТЕ КООПЕРАЦИИ
- kind: закон; published 1978-07-14
- lex.bg's history line: Обн. ДВ. бр. 55 от 14 Юли 1978г. , изм. ДВ. бр. 102 от 29 Декември 1981г. , изм. ДВ. бр. 45 от 8 Юни 1984г. , изм. ДВ. бр. 75 от 30 Септември 1988г. , изм. ДВ. бр. 46 от 16 Юни 1989г. , изм. ДВ. бр. 21 от 13 Март 1990г. , изм. ДВ. бр. 60 от 24 Юли 1992г. , изм. ДВ. бр. 104 от 6 Декември 1996г. , изм. ДВ. бр. 117 от 10 Декември 1997г. , изм. ДВ. бр. 59 от 26 Май 1998г.
- repeal marker read from it: none
- the corpus's amendment rows: 10, the last: ДВ 104/1996 (1996-12-06); ДВ 117/1997 (1997-12-10); ДВ 59/1998 (1998-05-26)
- candidates: none share words with this title, and lex.bg's history line carries no repeal marker
