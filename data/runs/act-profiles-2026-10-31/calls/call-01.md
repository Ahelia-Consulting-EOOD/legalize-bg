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

The answer file: `/Users/ekimir/swprj/legalize-bg/.claude/worktrees/unruffled-feynman-cd9070/data/runs/act-profiles-2026-10-31/calls/call-01-answer.yaml`

```yaml
# One YAML document: a mapping from each act's slug (every slug of the task, no other) to its verdict
<slug>:
  verdict: <in_force | repealed | unknown>
  repealed_by: <the material id of the candidate that repeals it, or 0 for lex.bg's own repeal marker, only when the verdict is repealed; otherwise null>
  evidence: <the facts and lines you relied on, in one or two sentences>
```

## zakon-za-administrativnite-narusheniya-i-nakazaniya
- title: ЗАКОН ЗА АДМИНИСТРАТИВНИТЕ НАРУШЕНИЯ И НАКАЗАНИЯ
- kind: закон; published 1969-11-28
- lex.bg's history line: Обн. ДВ. бр. 92 от 28 Ноември 1969г. , изм. ДВ. бр. 54 от 11 Юли 1978г. , изм. ДВ. бр. 28 от 9 Април 1982г. , изм. ДВ. бр. 28 от 8 Април 1983г. , изм. […] . 79 от 17 Септември 2024г. , доп. ДВ. бр. 50 от 20 Юни 2025г. , доп. ДВ. бр. 54 от 4 Юли 2025г. , изм. и доп. ДВ. бр. 61 от 29 Юли 2025г. , изм. и доп. ДВ. бр. 64 от 5 Август 2025г. , изм. и доп. ДВ. бр. 115 от 30 Декември 2025г. , изм. ДВ. бр. 17 от 13 Февруари 2026г.
- repeal marker read from it: none
- the corpus's amendment rows: 74, the last: ДВ 64/2025 (2025-08-05); ДВ 115/2025 (2025-12-30); ДВ 17/2026 (2026-02-13)
- candidates: none share words with this title, and lex.bg's history line carries no repeal marker

## zakon-za-amnistiya-ot-1947-g
- title: ЗАКОН ЗА АМНИСТИЯ ОТ 1947 Г.
- kind: закон; published 1947-06-27
- lex.bg's history line: Обн. ДВ. бр. 146 от 27 Юни 1947г.
- repeal marker read from it: none
- the corpus's amendment rows: 1, the last: ДВ 146/1947 (1947-06-27)
- candidates: none share words with this title, and lex.bg's history line carries no repeal marker

## zakon-za-amnistiya-ot-1950-g
- title: ЗАКОН ЗА АМНИСТИЯ ОТ 1950 Г.
- kind: закон; published 1950-11-11
- lex.bg's history line: Обн. ДВ. бр. 266 от 11 Ноември 1950г.
- repeal marker read from it: none
- the corpus's amendment rows: 1, the last: ДВ 266/1950 (1950-11-11)
- candidates: none share words with this title, and lex.bg's history line carries no repeal marker

## zakon-za-amnistiya-ot-1964-g
- title: ЗАКОН ЗА АМНИСТИЯ ОТ 1964 Г.
- kind: закон; published 1964-09-08
- lex.bg's history line: Обн. ДВ. бр. 71 от 8 Септември 1964г.
- repeal marker read from it: none
- the corpus's amendment rows: 1, the last: ДВ 71/1964 (1964-09-08)
- candidates: none share words with this title, and lex.bg's history line carries no repeal marker

## zakon-za-amnistiya-ot-1974-g
- title: ЗАКОН ЗА АМНИСТИЯ ОТ 1974 Г.
- kind: закон; published 1974-11-08
- lex.bg's history line: Обн. ДВ. бр. 87 от 8 Ноември 1974г.
- repeal marker read from it: none
- the corpus's amendment rows: 1, the last: ДВ 87/1974 (1974-11-08)
- candidates: none share words with this title, and lex.bg's history line carries no repeal marker

## zakon-za-amnistiya-ot-1981-g
- title: ЗАКОН ЗА АМНИСТИЯ ОТ 1981 Г.
- kind: закон; published 1981-07-10
- lex.bg's history line: Обн. ДВ. бр. 54 от 10 Юли 1981г.
- repeal marker read from it: none
- the corpus's amendment rows: 1, the last: ДВ 54/1981 (1981-07-10)
- candidates: none share words with this title, and lex.bg's history line carries no repeal marker

## zakon-za-amnistiya-ot-1984-g
- title: ЗАКОН ЗА АМНИСТИЯ ОТ 1984 Г.
- kind: закон; published 1984-06-01
- lex.bg's history line: Обн. ДВ. бр. 43 от 1 Юни 1984г.
- repeal marker read from it: none
- the corpus's amendment rows: 1, the last: ДВ 43/1984 (1984-06-01)
- candidates: none share words with this title, and lex.bg's history line carries no repeal marker

## zakon-za-arbitrazha-zagl-izm-dv-br-63-ot-2025-g-v-sila-ot-01082025-g
- title: ЗАКОН ЗА АРБИТРАЖА (ЗАГЛ. ИЗМ. - ДВ, БР. 63 ОТ 2025 Г., В СИЛА ОТ 01.08.2025 Г.)
- kind: закон; published 1988-08-05
- lex.bg's history line: Обн. ДВ. бр. 60 от 5 Август 1988г. , изм. ДВ. бр. 93 от 2 Ноември 1993г. , изм. ДВ. бр. 59 от 26 Май 1998г. , изм. ДВ. бр. 38 от 17 Април 2001г. , изм. ДВ. бр. 46 от 7 Май 2002г. , изм. ДВ. бр. 102 от 1 Ноември 2002г. , изм. ДВ. бр. 59 от 20 Юли 2007г. , изм. и доп. ДВ. бр. 8 от 24 Януари 2017г. , изм. и доп. ДВ. бр. 63 от 1 Август 2025г. , изм. ДВ. бр. 87 от 17 Октомври 2025г.
- repeal marker read from it: none
- the corpus's amendment rows: 10, the last: ДВ 8/2017 (2017-01-24); ДВ 63/2025 (2025-08-01); ДВ 87/2025 (2025-10-17)
- candidates: none share words with this title, and lex.bg's history line carries no repeal marker

## zakon-za-borba-sreshtu-protivoobshtestvenite-proyavi-na-maloletnite-i-nepalnolet
- title: ЗАКОН ЗА БОРБА СРЕЩУ ПРОТИВООБЩЕСТВЕНИТЕ ПРОЯВИ НА МАЛОЛЕТНИТЕ И НЕПЪЛНОЛЕТНИТЕ (ЗАГЛ. ИЗМ. - ИЗВ., БР. 11 ОТ 1961 Г.)
- kind: закон; published 1958-02-14
- lex.bg's history line: Обн. ДВ. бр. 13 от 14 Февруари 1958г. , изм. ДВ. бр. 11 от 7 Февруари 1961г. , изм. ДВ. бр. 35 от 1 Май 1966г. , изм. ДВ. бр. 30 от 15 Април 1969г. ,  […]  2009г. , изм. ДВ. бр. 50 от 2 Юли 2010г. , доп. ДВ. бр. 82 от 26 Октомври 2012г. , изм. ДВ. бр. 15 от 15 Февруари 2013г. , изм. ДВ. бр. 68 от 2 Август 2013г. , изм. ДВ. бр. 59 от 29 Юли 2016г. , изм. ДВ. бр. 24 от 22 Март 2019г. , изм. ДВ. бр. 101 от 27 Декември 2019г.
- repeal marker read from it: none
- the corpus's amendment rows: 28, the last: ДВ 59/2016 (2016-07-29); ДВ 24/2019 (2019-03-22); ДВ 101/2019 (2019-12-27)
- candidates: none share words with this title, and lex.bg's history line carries no repeal marker

## zakon-za-darzhavnite-taksi
- title: ЗАКОН ЗА ДЪРЖАВНИТЕ ТАКСИ
- kind: закон; published 1951-12-28
- lex.bg's history line: Обн. ДВ. бр. 104 от 28 Декември 1951г. , доп. ДВ. бр. 89 от 6 Ноември 1959г. , изм. ДВ. бр. 21 от 11 Март 1960г. , доп. ДВ. бр. 53 от 6 Юли 1973г. , и […] 1г. , изм. ДВ. бр. 68 от 2 Август 2013г. , изм. ДВ. бр. 53 от 27 Юни 2014г. , доп. ДВ. бр. 85 от 24 Октомври 2017г. , изм. ДВ. бр. 17 от 23 Февруари 2018г. , доп. ДВ. бр. 104 от 8 Декември 2020г. , доп. ДВ. бр. 16 от 23 Февруари 2021г. , изм. ДВ. бр. 20 от 9 Март 2021г.
- repeal marker read from it: none
- the corpus's amendment rows: 42, the last: ДВ 104/2020 (2020-12-08); ДВ 16/2021 (2021-02-23); ДВ 20/2021 (2021-03-09)
- candidates:
  - material 2313, ДВ 63/2006 (2006-08-04), a line of the general repeal decree „Постановление № 183 от 25 юли 2006 г. за отменяне на нормативни актове на Министерския съвет“: 3. Тарифата за арбитражните такси по дела, които се разглеждат от Арбитражния съд към Агенцията по обществени поръчки, приета с Постановление № 241 на Министерския съвет от 2004 г. (ДВ, бр. 85 от 2004 г.). [shared words: такси]
  - material 2758, ДВ 88/2006 (2006-10-31), a line of the general repeal decree „Постановление № 284 от 23 октомври 2006 г. за отменяне на нормативни актове на Министерския съвет“: 40. Постановление № 477 на Министерския съвет от 1997 г. за освобождаване от митни сборове и пристанищни такси вноса на дареното от правителството на Република Корея оборудване за изграждане и функциониране на Социален център за инвалиди в София (ДВ, бр. 125 от 1997 г.). [shared words: такси]
  - material 87379, ДВ 69/2014 (2014-08-19): Инструкция за отменяне на Инструкция № Із-2453 от 2012 г. за реда за разпределяне на работното време на държавните служители в Министерството на вътрешните работи, отчитането му и компенсиране на работата извън установеното работно време [shared words: държавните]
  - material 89943, ДВ 99/2014 (2014-12-02): Наредба за отменяне на Наредба № Iз-29 от 2013 г. за предоставяне на информация от специализирана дирекция „Оперативни технически операции“ на Министерството на вътрешните работи на другите структури на Министерството на вътрешните работи, държавните органи и организации [shared words: държавните]
  - material 99467, ДВ 100/2015 (2015-12-18): Инструкция за отменяне на Инструкция № Із-849 от 2007 г. за условията и реда, при които органите на Министерството на вътрешните работи оказват съдействие на частните и държавните съдебни изпълнители при изпълнение на техните правомощия [shared words: държавните]
  - material 217963, ДВ 49/2024 (2024-06-11), a line of the general repeal decree „Постановление № 205 от 7 юни 2024 г. за отменяне на нормативни актове на Министерския съвет“: § 1. Наредбата за реда за използване на държавните дългосрочни облигации, емитирани по Закона за уреждане на необслужваните кредити, договорени до 31 декември 1990 г., за погасяване на задълженията към държавата, възникнали по реда на същия закон, приета с Постановление № 22 на Министерския съвет от 1995 г. (ДВ, бр. 12 от 1995 г.), се отменя. [shared words: държавните]
  - material 244368, ДВ 58/2026 (2026-06-26): Постановление № 75 от 24 юни 2026 г. за отменяне на Тарифата за пристанищните такси, събирани от Държавно предприятие „Пристанищна инфраструктура“, приета с Постановление № 97 на Министерския съвет от 2007 г. [shared words: такси]
