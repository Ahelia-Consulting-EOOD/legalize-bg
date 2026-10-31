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

The answer file: `/Users/ekimir/swprj/legalize-bg/.claude/worktrees/unruffled-feynman-cd9070/data/runs/act-profiles-2026-10-31/calls/call-03-answer.yaml`

```yaml
# One YAML document: a mapping from each act's slug (every slug of the task, no other) to its verdict
<slug>:
  verdict: <in_force | repealed | unknown>
  repealed_by: <the material id of the candidate repeal title, only when the verdict is repealed; otherwise null>
  evidence: <the facts and lines you relied on, in one or two sentences>
```

## zakon-za-oproshtavane-na-zadalzheniya-kam-darzhavata
- title: ЗАКОН ЗА ОПРОЩАВАНЕ НА ЗАДЪЛЖЕНИЯ КЪМ ДЪРЖАВАТА
- kind: закон; published 1964-09-15; lex.bg records it vigente with 1 amendment rows, the last: ДВ 73/1964 (1964-09-15)
- candidate repeal titles: none share words with this title

## zakon-za-otgovornostta-na-darzhavata-i-obshtinite-za-vredi-zagl-izm-dv-br-30-ot-
- title: ЗАКОН ЗА ОТГОВОРНОСТТА НА ДЪРЖАВАТА И ОБЩИНИТЕ ЗА ВРЕДИ (ЗАГЛ. ИЗМ. - ДВ, БР. 30 ОТ 11.04.2006 Г., В СИЛА ОТ 12.07.2006 Г.)
- kind: закон; published 1988-08-05; lex.bg records it vigente with 21 amendment rows, the last: ДВ 16/2026 (2026-02-10); ДВ 51/2026 (2026-06-05); ДВ 59/2026 (2026-06-30)
- candidate repeal titles: none share words with this title

## zakon-za-otmenyavane-na-vsichki-zakoni-izdadeni-predi-9091944-g
- title: ЗАКОН ЗА ОТМЕНЯВАНЕ НА ВСИЧКИ ЗАКОНИ, ИЗДАДЕНИ ПРЕДИ 9.09.1944 Г.
- kind: закон; published 1951-11-20; lex.bg records it vigente with 1 amendment rows, the last: ДВ 93/1951 (1951-11-20)
- candidate repeal titles: none share words with this title

## zakon-za-sobstvenostta
- title: ЗАКОН ЗА СОБСТВЕНОСТТА
- kind: закон; published 1951-11-16; lex.bg records it vigente with 37 amendment rows, the last: ДВ 7/2018 (2018-01-19); ДВ 18/2020 (2020-02-28); ДВ 18/2022 (2022-03-04)
- candidate repeal titles: none share words with this title

## zakon-za-tvorcheskite-fondove
- title: ЗАКОН ЗА ТВОРЧЕСКИТЕ ФОНДОВЕ
- kind: закон; published 1973-04-03; lex.bg records it vigente with 3 amendment rows, the last: ДВ 27/1973 (1973-04-03); ДВ 20/1979 (1979-03-09); ДВ 153/1998 (1998-12-23)
- candidate repeal titles:
  - material 21286, ДВ 30/2004 (2004-04-13): Наредба за отменяне на Наредба № 3 от 1989 г. за запазване на сградните и благоустройствените фондове в населените места [shared words: фондове]
  - material 21997, ДВ 45/2009 (2009-06-16): Наредба за отменяне на Наредба № 247 от 1995 г. за звената за обработка на архивни фондове и документи на физически и юридически лица, издадена от Главно управление на архивите при Министерския съвет [shared words: фондове]
  - material 27320, ДВ 96/2009 (2009-12-04): Постановление № 277 от 26 ноември 2009 г. за отменяне на Постановление № 197 на Министерския съвет от 2008 г. за материално стимулиране на служителите, изпълняващи функции по усвояване на средства по структурните фондове и предприсъединителните програми на Европейския съюз [shared words: фондове]
  - material 57288, ДВ 80/2011 (2011-10-14): Наредба за отменяне на Наредба № Н-10 от 2005 г. за условията и реда за експлоатация и достъп до информационните фондове на служба „Военна полиция“ [shared words: фондове]
  - material 70892, ДВ 98/2012 (2012-12-11): Наредба за отменяне на Наредба № Із-1215 от 2006 г. за реда за достъп до информационните фондове на Министерството на вътрешните работи [shared words: фондове]
  - material 116401, ДВ 61/2017 (2017-07-28): Инструкция за отменяне на Инструкция № И-4 от 2011 г. за подбора на военнослужещи и граждански лица за работа в служба „Военна информация“ и на Инструкция № 2 от 2011 г. за определяне на реда за създаване, използване и закриване на информационните фондове и за контрола върху тях в служба „Военна информация“ [shared words: фондове]

## zakon-za-urezhdane-pravata-na-kupuvachi-na-nedvizhimi-imoti-s-chastni-dogovori
- title: ЗАКОН ЗА УРЕЖДАНЕ ПРАВАТА НА КУПУВАЧИ НА НЕДВИЖИМИ ИМОТИ С ЧАСТНИ ДОГОВОРИ
- kind: закон; published 1947-07-26; lex.bg records it vigente with 1 amendment rows, the last: ДВ 171/1947 (1947-07-26)
- candidate repeal titles: none share words with this title

## zakon-za-urezhdane-pravata-na-litsata-koito-sa-zaeli-ili-poluchili-darzhavni-dvo
- title: ЗАКОН ЗА УРЕЖДАНЕ ПРАВАТА НА ЛИЦАТА, КОИТО СА ЗАЕЛИ ИЛИ ПОЛУЧИЛИ ДЪРЖАВНИ ДВОРНИ МЕСТА
- kind: закон; published 1956-11-09; lex.bg records it vigente with 1 amendment rows, the last: ДВ 90/1956 (1956-11-09)
- candidate repeal titles:
  - material 240221, ДВ 114/2025 (2025-12-24): Наредба за отменяне на Наредба № Н-9 от 2020 г. за условията и реда за вписване в регистъра на лицата, които по занятие предоставят услуги за обмяна между виртуални валути и признати валути без златно покритие, услуги за прехвърляне или обмяна на виртуални активи, услуги по съхраняване на виртуални активи и управление на такива, позволяващо осъществяването на контрол върху активите, и услуги, свързани с публично предлагане на виртуални активи, и на доставчиците на портфейли, които предлагат попечителски услуги [shared words: които, лицата]

## zakon-za-vanshnata-targoviya
- title: ЗАКОН ЗА ВЪНШНАТА ТЪРГОВИЯ
- kind: закон; published 1969-12-05; lex.bg records it vigente with 4 amendment rows, the last: ДВ 60/1974 (1974-08-02); ДВ 63/1976 (1976-08-06); ДВ 4/1989 (1989-01-13)
- candidate repeal titles:
  - material 21361, ДВ 25/2004 (2004-03-26): Постановление № 60 от 16 март 2004 г. за отменяне на Постановление № 15 на Министерския съвет от 2002 г. за изпълнение от 1 януари 2002 г. на задълженията на Република България, произтичащи от Споразумението за свободна търговия между Република България и Република Естония [shared words: търговия]
  - material 108524, ДВ 85/2016 (2016-10-28): Наредба за отменяне на Наредба № 44 от 2001 г. за търговия с комбинирани фуражи [shared words: търговия]

## zakon-za-zadalzheniyata-i-dogovorite
- title: ЗАКОН ЗА ЗАДЪЛЖЕНИЯТА И ДОГОВОРИТЕ
- kind: закон; published 1950-12-05; lex.bg records it vigente with 27 amendment rows, the last: ДВ 42/2018 (2018-05-22); ДВ 102/2020 (2020-12-01); ДВ 35/2021 (2021-04-27)
- candidate repeal titles:
  - material 21361, ДВ 25/2004 (2004-03-26): Постановление № 60 от 16 март 2004 г. за отменяне на Постановление № 15 на Министерския съвет от 2002 г. за изпълнение от 1 януари 2002 г. на задълженията на Република България, произтичащи от Споразумението за свободна търговия между Република България и Република Естония [shared words: задълженията]
  - material 121425, ДВ 4/2018 (2018-01-09): Наредба за отменяне на Наредба № 23 от 2006 г. за реда за водене на регистър на договорите за влог на зърно от регистрирани зърнохранилища [shared words: договорите]

## zakon-za-zhilishtnostroitelnite-kooperatsii
- title: ЗАКОН ЗА ЖИЛИЩНОСТРОИТЕЛНИТЕ КООПЕРАЦИИ
- kind: закон; published 1978-07-14; lex.bg records it vigente with 10 amendment rows, the last: ДВ 104/1996 (1996-12-06); ДВ 117/1997 (1997-12-10); ДВ 59/1998 (1998-05-26)
- candidate repeal titles: none share words with this title
