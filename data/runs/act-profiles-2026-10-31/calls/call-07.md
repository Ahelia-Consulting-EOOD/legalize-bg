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

The answer file: `/Users/ekimir/swprj/legalize-bg/.claude/worktrees/unruffled-feynman-cd9070/data/runs/act-profiles-2026-10-31/calls/call-07-answer.yaml`

```yaml
# One YAML document: a mapping from each act's slug (every slug of the task, no other) to its verdict
<slug>:
  verdict: <in_force | repealed | unknown>
  repealed_by: <the material id of the candidate that repeals it, or 0 for lex.bg's own repeal marker, only when the verdict is repealed; otherwise null>
  evidence: <the facts and lines you relied on, in one or two sentences>
```

## naredba-4-za-poshtenskite-saobshteniya
- title: НАРЕДБА № 4 ЗА ПОЩЕНСКИТЕ СЪОБЩЕНИЯ
- kind: наредба; published 1979-12-07
- lex.bg's history line: Обн. ДВ. бр. 97 от 7 Декември 1979г. , попр. ДВ. бр. 98 от 11 Декември 1979г. , изм. ДВ. бр. 48 от 18 Юни 1991г. , отм. ДВ. бр. 64 от 4 Август 2000г.
- repeal marker read from it: отм. ДВ. бр. 64 от 4 Август 2000г.
- the corpus's amendment rows: 4, the last: ДВ 98/1979 (1979-12-11); ДВ 48/1991 (1991-06-18); ДВ 64/2000 (2000-08-04)
- candidates:
  - 0 (lex.bg's own repeal marker): отм. ДВ. бр. 64 от 4 Август 2000г.
  - material 57295, ДВ 80/2011 (2011-10-14): Инструкция за отменяне на Инструкция № И-10 от 2009 г. за организацията на работата в служба „Военна полиция“ по постъпили съобщения и сигнали [shared words: съобщения]

## naredba-49-za-izkustveno-osvetlenie-na-sgradite
- title: НАРЕДБА № 49 ЗА ИЗКУСТВЕНО ОСВЕТЛЕНИЕ НА СГРАДИТЕ
- kind: наредба; published 1976-01-23
- lex.bg's history line: Обн. ДВ. бр. 7 от 23 Януари 1976г. , изм. ДВ. бр. 64 от 10 Август 1976г.
- repeal marker read from it: none
- the corpus's amendment rows: 2, the last: ДВ 7/1976 (1976-01-23); ДВ 64/1976 (1976-08-10)
- candidates: none share words with this title, and lex.bg's history line carries no repeal marker

## naredba-5-za-bolestite-pri-koito-rabotnitsite-boleduvashti-ot-tyah-imat-osobena-
- title: НАРЕДБА № 5 ЗА БОЛЕСТИТЕ, ПРИ КОИТО РАБОТНИЦИТЕ, БОЛЕДУВАЩИ ОТ ТЯХ, ИМАТ ОСОБЕНА ЗАКРИЛА СЪГЛАСНО ЧЛ. 333, АЛ. 1 ОТ КОДЕКСА НА ТРУДА
- kind: наредба; published 1987-04-28
- lex.bg's history line: Обн. ДВ. бр. 33 от 28 Април 1987г.
- repeal marker read from it: none
- the corpus's amendment rows: 1, the last: ДВ 33/1987 (1987-04-28)
- candidates:
  - material 59709, ДВ 103/2011 (2011-12-23): Наредба за отменяне на Наредба № 5 за набиране и разходване на средствата по фонд „Жилищно строителство“ [same act number] [shared words: ]
  - material 2377, ДВ 67/2006 (2006-08-18): Правилник за отменяне на Правилника по безопасността на труда на работниците, поддържащи железния път - В-05-01-02 от 1975 г. [shared words: работниците, труда]
  - material 2378, ДВ 67/2006 (2006-08-18): Правилник за отменяне на Правилника по безопасността на труда на работниците от експлоатацията на локомотивното стопанство - В-05-01-01 от 1976 г. [shared words: работниците, труда]
  - material 2379, ДВ 67/2006 (2006-08-18): Правилник за отменяне на Правилника по безопасността на труда за работниците и служителите от гаровите и превозните служби - В-05-01-03 от 1976 г. [shared words: работниците, труда]
  - material 28094, ДВ 1/2010 (2010-01-05): Наредба за отменяне на Наредба № 3 от 1996 г. за инструктажа на работниците и служителите по безопасност, хигиена на труда и противопожарна охрана [shared words: работниците, труда]

## naredba-6-za-izpolzuvane-i-predstavyane-na-nedvizhimite-pametnitsi-na-kulturata
- title: НАРЕДБА № 6 ЗА ИЗПОЛЗУВАНЕ И ПРЕДСТАВЯНЕ НА НЕДВИЖИМИТЕ ПАМЕТНИЦИ НА КУЛТУРАТА
- kind: наредба; published 1979-04-13
- lex.bg's history line: Обн. ДВ. бр. 30 от 13 Април 1979г.
- repeal marker read from it: none
- the corpus's amendment rows: 1, the last: ДВ 30/1979 (1979-04-13)
- candidates: none share words with this title, and lex.bg's history line carries no repeal marker

## naredba-6-za-osiguryavane-na-normalna-akustichna-obstanovka-v-zhilishtni-i-obsht
- title: НАРЕДБА № 6 ЗА ОСИГУРЯВАНЕ НА НОРМАЛНА АКУСТИЧНА ОБСТАНОВКА В ЖИЛИЩНИ И ОБЩЕСТВЕНИ СГРАДИ И МЕСТА
- kind: наредба; published 1977-02-25
- lex.bg's history line: Обн. ДВ. бр. 16 от 25 Февруари 1977г.
- repeal marker read from it: none
- the corpus's amendment rows: 1, the last: ДВ 16/1977 (1977-02-25)
- candidates: none share words with this title, and lex.bg's history line carries no repeal marker

## naredba-6-za-ustroystvoto-i-deynostta-na-balgarskiya-koraben-registar
- title: НАРЕДБА № 6 ЗА УСТРОЙСТВОТО И ДЕЙНОСТТА НА БЪЛГАРСКИЯ КОРАБЕН РЕГИСТЪР
- kind: наредба; published 1984-07-17
- lex.bg's history line: Обн. ДВ. бр. 56 от 17 Юли 1984г. , попр. ДВ. бр. 60 от 31 Юли 1984г.
- repeal marker read from it: none
- the corpus's amendment rows: 2, the last: ДВ 56/1984 (1984-07-17); ДВ 60/1984 (1984-07-31)
- candidates:
  - material 49001, ДВ 35/2011 (2011-05-03): Постановление № 110 от 26 април 2011 г. за отменяне на Правилника за устройството и дейността на университет с наименование Академия на Министерството на вътрешните работи, приет с Постановление № 344 на Министерския съвет от 2004 г. [shared words: дейността, устройството]
  - material 132672, ДВ 102/2018 (2018-12-11): Правилник за отменяне на Правилника за организацията и дейността на регионалните съвети за развитие, Правилника за устройството и дейността на дирекциите за техническо съдействие, координация и управление на регионални програми и планове и Правилника за организацията и дейността на областните съвети за развитие [shared words: дейността, устройството]

## naredba-7-za-higiennite-iziskvaniya-za-ustroystvoto-i-eksploatatsiyata-na-gabarn
- title: НАРЕДБА № 7 ЗА ХИГИЕННИТЕ ИЗИСКВАНИЯ ЗА УСТРОЙСТВОТО И ЕКСПЛОАТАЦИЯТА НА ГЪБАРНИЦИ
- kind: наредба; published 1984-04-06
- lex.bg's history line: Обн. ДВ. бр. 28 от 6 Април 1984г.
- repeal marker read from it: none
- the corpus's amendment rows: 1, the last: ДВ 28/1984 (1984-04-06)
- candidates:
  - material 174747, ДВ 56/2022 (2022-07-19): Наредба за отменяне на Наредба № 45 от 1995 г. за хигиенните норми и изисквания за добавките в хранителните продукти [shared words: изисквания, хигиенните]
  - material 178341, ДВ 77/2022 (2022-09-27): Наредба за отменяне на Наредба № 11 от 1995 г. за санитарно-хигиенните изисквания към устройството и работата на селскостопанските аптеки [shared words: изисквания, устройството]

## naredba-8-za-mikroklimata-v-podzemnite-rudnitsi
- title: НАРЕДБА № 8 ЗА МИКРОКЛИМАТА В ПОДЗЕМНИТЕ РУДНИЦИ
- kind: наредба; published 1985-09-24
- lex.bg's history line: Обн. ДВ. бр. 74 от 24 Септември 1985г.
- repeal marker read from it: none
- the corpus's amendment rows: 1, the last: ДВ 74/1985 (1985-09-24)
- candidates: none share words with this title, and lex.bg's history line carries no repeal marker

## naredba-9-za-profesionalnata-kvalifikatsiya-na-stenografite-i-mashinopistsite
- title: НАРЕДБА № 9 ЗА ПРОФЕСИОНАЛНАТА КВАЛИФИКАЦИЯ НА СТЕНОГРАФИТЕ И МАШИНОПИСЦИТЕ
- kind: наредба; published 1985-08-16
- lex.bg's history line: Обн. ДВ. бр. 64 от 16 Август 1985г.
- repeal marker read from it: none
- the corpus's amendment rows: 1, the last: ДВ 64/1985 (1985-08-16)
- candidates: none share words with this title, and lex.bg's history line carries no repeal marker

## naredba-za-komandirovkite-v-stranata
- title: НАРЕДБА ЗА КОМАНДИРОВКИТЕ В СТРАНАТА
- kind: наредба; published 1987-02-10
- lex.bg's history line: Обн. ДВ. бр. 11 от 10 Февруари 1987г. , изм. ДВ. бр. 21 от 15 Март 1991г. , изм. ДВ. бр. 2 от 7 Януари 1994г. , изм. ДВ. бр. 62 от 11 Юли 1995г. , изм. ДВ. бр. 34 от 29 Април 1997г. , изм. ДВ. бр. 40 от 30 Април 1999г. , изм. ДВ. бр. 2 от 8 Януари 2008г. , изм. ДВ. бр. 2 от 7 Януари 2011г. , изм. и доп. ДВ. бр. 27 от 24 Март 2023г. , изм. ДВ. бр. 115 от 30 Декември 2025г.
- repeal marker read from it: none
- the corpus's amendment rows: 10, the last: ДВ 2/2011 (2011-01-07); ДВ 27/2023 (2023-03-24); ДВ 115/2025 (2025-12-30)
- candidates:
  - material 18441, ДВ 97/2004 (2004-11-02): Постановление № 284 от 22 октомври 2004 г. за изменение на Постановление № 226 на Министерския съвет от 1992 г. за отменяне на Наредбата за управление на имуществата на чуждестранни лица в страната и за преодоляване на имуществените последици от нея [shared words: страната]
