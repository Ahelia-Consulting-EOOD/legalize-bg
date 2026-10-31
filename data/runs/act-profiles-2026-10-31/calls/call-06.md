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

The answer file: `/Users/ekimir/swprj/legalize-bg/.claude/worktrees/unruffled-feynman-cd9070/data/runs/act-profiles-2026-10-31/calls/call-06-answer.yaml`

```yaml
# One YAML document: a mapping from each act's slug (every slug of the task, no other) to its verdict
<slug>:
  verdict: <in_force | repealed | unknown>
  repealed_by: <the material id of the candidate that repeals it, or 0 for lex.bg's own repeal marker, only when the verdict is repealed; otherwise null>
  evidence: <the facts and lines you relied on, in one or two sentences>
```

## naredba-2-po-bezopasnostta-na-truda-pri-proizvodstvoto-i-rabotata-s-hlor
- title: НАРЕДБА № 2 ПО БЕЗОПАСНОСТТА НА ТРУДА ПРИ ПРОИЗВОДСТВОТО И РАБОТАТА С ХЛОР
- kind: наредба; published 1979-01-30
- lex.bg's history line: Обн. ДВ. бр. 9 от 30 Януари 1979г.
- repeal marker read from it: none
- the corpus's amendment rows: 1, the last: ДВ 9/1979 (1979-01-30)
- candidates:
  - material 342, ДВ 44/2005 (2005-05-27): Правилник за отменяне на Правилника по безопасността на труда при експлоатацията на електрокари и мотокари - Д-05-002 [shared words: безопасността, труда]
  - material 343, ДВ 44/2005 (2005-05-27): Правилник за отменяне на Правилника по безопасността на труда при експлоатацията, обслужването и ремонта на моторните превозни средства Д-05-003 [shared words: безопасността, труда]
  - material 2377, ДВ 67/2006 (2006-08-18): Правилник за отменяне на Правилника по безопасността на труда на работниците, поддържащи железния път - В-05-01-02 от 1975 г. [shared words: безопасността, труда]
  - material 2378, ДВ 67/2006 (2006-08-18): Правилник за отменяне на Правилника по безопасността на труда на работниците от експлоатацията на локомотивното стопанство - В-05-01-01 от 1976 г. [shared words: безопасността, труда]
  - material 2379, ДВ 67/2006 (2006-08-18): Правилник за отменяне на Правилника по безопасността на труда за работниците и служителите от гаровите и превозните служби - В-05-01-03 от 1976 г. [shared words: безопасността, труда]
  - material 2380, ДВ 67/2006 (2006-08-18): Правилник за отменяне на Правилника по безопасността на труда в железопътните заводи, депа и работилници - В-05-01-05 от 1976 г. [shared words: безопасността, труда]
  - material 2381, ДВ 67/2006 (2006-08-18): Правилник за отменяне на Правилника по безопасността на труда във вагонното стопанство - В-05-01-06 от 1988 г. [shared words: безопасността, труда]
  - material 2382, ДВ 67/2006 (2006-08-18): Правилник за отменяне на Правилника по безопасността на труда при работи по жп контактна мрежа 25 кв, 50 хц - В-05-01-04 от 1989 г. [shared words: безопасността, труда]
  - material 14923, ДВ 19/2005 (2005-03-01): Правилник за отменяне на Правилника по безопасността на труда при експлоатация на електрическите уредби и съоръжения Д-01-008 от 1986 г. [shared words: безопасността, труда]
  - material 18245, ДВ 107/2004 (2004-12-07): Правилник за отмяна на Правилника по безопасността на труда при поддържането и експлоатацията на водоснабдителните и канализационните мрежи и съоръжения - Д-09-001 [shared words: безопасността, труда]
  - material 18246, ДВ 107/2004 (2004-12-07): Правилник за отмяна на Правилника по безопасността на труда за въздушни компресорни инсталации и уредби - Д-01-014 [shared words: безопасността, труда]
  - material 19591, ДВ 63/2004 (2004-07-20): Правилник за отмяна на Правилника по безопасността на труда при строителните и монтажните работи - Д-02-001 [shared words: безопасността, труда]

## naredba-2-za-opazvane-istoriko-arheologicheskiya-rezervat-v-tsentara-na-gr-sofiy
- title: НАРЕДБА № 2 ЗА ОПАЗВАНЕ ИСТОРИКО-АРХЕОЛОГИЧЕСКИЯ РЕЗЕРВАТ В ЦЕНТЪРА НА ГР. СОФИЯ
- kind: наредба; published 1977-02-08
- lex.bg's history line: Обн. ДВ. бр. 11 от 8 Февруари 1977г. , изм. и доп. ДВ. бр. 85 от 26 Октомври 1979г.
- repeal marker read from it: none
- the corpus's amendment rows: 2, the last: ДВ 11/1977 (1977-02-08); ДВ 85/1979 (1979-10-26)
- candidates: none share words with this title, and lex.bg's history line carries no repeal marker

## naredba-2-za-organizirane-planirane-i-finansirane-razvitieto-na-masovata-fiziche
- title: НАРЕДБА № 2 ЗА ОРГАНИЗИРАНЕ, ПЛАНИРАНЕ И ФИНАНСИРАНЕ РАЗВИТИЕТО НА МАСОВАТА ФИЗИЧЕСКА КУЛТУРА, СПОРТА И ТУРИЗМА
- kind: наредба; published 1983-11-08
- lex.bg's history line: Обн. ДВ. бр. 87 от 8 Ноември 1983г.
- repeal marker read from it: none
- the corpus's amendment rows: 1, the last: ДВ 87/1983 (1983-11-08)
- candidates: none share words with this title, and lex.bg's history line carries no repeal marker

## naredba-2-za-poddarzhaneto-i-kontrola-na-geodezichnite-instrumenti-i-fotogrametr
- title: НАРЕДБА № 2 ЗА ПОДДЪРЖАНЕТО И КОНТРОЛА НА ГЕОДЕЗИЧНИТЕ ИНСТРУМЕНТИ И ФОТОГРАМЕТРИЧНАТА АПАРАТУРА
- kind: наредба; published 1978-12-29
- lex.bg's history line: Обн. ДВ. бр. 102 от 29 Декември 1978г.
- repeal marker read from it: none
- the corpus's amendment rows: 1, the last: ДВ 102/1978 (1978-12-29)
- candidates:
  - material 2758, ДВ 88/2006 (2006-10-31), a line of the general repeal decree „Постановление № 284 от 23 октомври 2006 г. за отменяне на нормативни актове на Министерския съвет“: 34. Постановление № 293 на Министерския съвет от 1994 г. за освобождаване от митни сборове вноса на апаратура, инструменти, машини, материали и медикаменти, получавани като безвъзмездна помощ по линия на Програмата на японските доброволци за сътрудничество с чужбина (ДВ, бр. 103 от 1994 г.). [shared words: апаратура, инструменти]

## naredba-2-za-prodalzhavane-deystvieto-na-edinnite-pravilnitsi-po-bezopasnostta-n
- title: НАРЕДБА № 2 ЗА ПРОДЪЛЖАВАНЕ ДЕЙСТВИЕТО НА ЕДИННИТЕ ПРАВИЛНИЦИ ПО БЕЗОПАСНОСТТА НА ТРУДА
- kind: наредба; published 1987-06-05
- lex.bg's history line: Обн. ДВ. бр. 43 от 5 Юни 1987г. , изм. ДВ. бр. 37 от 16 Май 1989г.
- repeal marker read from it: none
- the corpus's amendment rows: 2, the last: ДВ 43/1987 (1987-06-05); ДВ 37/1989 (1989-05-16)
- candidates:
  - material 342, ДВ 44/2005 (2005-05-27): Правилник за отменяне на Правилника по безопасността на труда при експлоатацията на електрокари и мотокари - Д-05-002 [shared words: безопасността, труда]
  - material 343, ДВ 44/2005 (2005-05-27): Правилник за отменяне на Правилника по безопасността на труда при експлоатацията, обслужването и ремонта на моторните превозни средства Д-05-003 [shared words: безопасността, труда]
  - material 2377, ДВ 67/2006 (2006-08-18): Правилник за отменяне на Правилника по безопасността на труда на работниците, поддържащи железния път - В-05-01-02 от 1975 г. [shared words: безопасността, труда]
  - material 2378, ДВ 67/2006 (2006-08-18): Правилник за отменяне на Правилника по безопасността на труда на работниците от експлоатацията на локомотивното стопанство - В-05-01-01 от 1976 г. [shared words: безопасността, труда]
  - material 2379, ДВ 67/2006 (2006-08-18): Правилник за отменяне на Правилника по безопасността на труда за работниците и служителите от гаровите и превозните служби - В-05-01-03 от 1976 г. [shared words: безопасността, труда]
  - material 2380, ДВ 67/2006 (2006-08-18): Правилник за отменяне на Правилника по безопасността на труда в железопътните заводи, депа и работилници - В-05-01-05 от 1976 г. [shared words: безопасността, труда]
  - material 2381, ДВ 67/2006 (2006-08-18): Правилник за отменяне на Правилника по безопасността на труда във вагонното стопанство - В-05-01-06 от 1988 г. [shared words: безопасността, труда]
  - material 2382, ДВ 67/2006 (2006-08-18): Правилник за отменяне на Правилника по безопасността на труда при работи по жп контактна мрежа 25 кв, 50 хц - В-05-01-04 от 1989 г. [shared words: безопасността, труда]
  - material 14923, ДВ 19/2005 (2005-03-01): Правилник за отменяне на Правилника по безопасността на труда при експлоатация на електрическите уредби и съоръжения Д-01-008 от 1986 г. [shared words: безопасността, труда]
  - material 18245, ДВ 107/2004 (2004-12-07): Правилник за отмяна на Правилника по безопасността на труда при поддържането и експлоатацията на водоснабдителните и канализационните мрежи и съоръжения - Д-09-001 [shared words: безопасността, труда]
  - material 18246, ДВ 107/2004 (2004-12-07): Правилник за отмяна на Правилника по безопасността на труда за въздушни компресорни инсталации и уредби - Д-01-014 [shared words: безопасността, труда]
  - material 19591, ДВ 63/2004 (2004-07-20): Правилник за отмяна на Правилника по безопасността на труда при строителните и монтажните работи - Д-02-001 [shared words: безопасността, труда]

## naredba-3-ot-24-noemvri-1987-g-za-osiguryavane-bezopasnostta-na-atomnite-tsentra
- title: НАРЕДБА № 3 ОТ 24 НОЕМВРИ 1987 Г. ЗА ОСИГУРЯВАНЕ БЕЗОПАСНОСТТА НА АТОМНИТЕ ЦЕНТРАЛИ ПРИ ПРОЕКТИРАНЕ, ИЗГРАЖДАНЕ И ЕКСПЛОАТАЦИЯ
- kind: наредба; published 1988-04-08
- lex.bg's history line: Обн. ДВ. бр. 27 от 8 Април 1988г. , изм. ДВ. бр. 12 от 9 Февруари 2001г.
- repeal marker read from it: none
- the corpus's amendment rows: 2, the last: ДВ 27/1988 (1988-04-08); ДВ 12/2001 (2001-02-09)
- candidates:
  - material 242742, ДВ 38/2026 (2026-04-24): Наредба за отменяне на Наредба № 35 от 2012 г. за правилата и нормите за проектиране, изграждане и въвеждане в експлоатация на кабелни електронни съобщителни мрежи и прилежащата им инфраструктура [shared words: експлоатация, изграждане, проектиране]
  - material 14923, ДВ 19/2005 (2005-03-01): Правилник за отменяне на Правилника по безопасността на труда при експлоатация на електрическите уредби и съоръжения Д-01-008 от 1986 г. [shared words: безопасността, експлоатация]
  - material 15239, ДВ 34/2005 (2005-04-19), a line of the general repeal decree „Постановление № 65 от 8 април 2005 г. за отменяне на нормативни актове“: 3. Наредбата за техническа експлоатация на електрически централи и мрежи, приета с Постановление № 196 на Министерския съвет от 2000 г. (ДВ, бр. 81 от 2000 г.); [shared words: експлоатация, централи]
  - material 110455, ДВ 103/2016 (2016-12-27): Правилник за отменяне на Правилник № 0-33 за проектиране и устройство на медицински рентгенови кабинети и експлоатация на медицински рентгенови уредби с максимално върхово напрежение до 300 KV [shared words: експлоатация, проектиране]

## naredba-3-za-predelno-dopustimite-kontsentratsii-na-himichni-veshtestva-otdelyan
- title: НАРЕДБА № 3 ЗА ПРЕДЕЛНО ДОПУСТИМИТЕ КОНЦЕНТРАЦИИ НА ХИМИЧНИ ВЕЩЕСТВА, ОТДЕЛЯНИ ОТ ПОЛИМЕРНИ СТРОИТЕЛНИ МАТЕРИАЛИ В ЖИЛИЩНИ И ОБЩЕСТВЕНИ СГРАДИ
- kind: наредба; published 1984-02-28
- lex.bg's history line: Обн. ДВ. бр. 17 от 28 Февруари 1984г.
- repeal marker read from it: none
- the corpus's amendment rows: 1, the last: ДВ 17/1984 (1984-02-28)
- candidates: none share words with this title, and lex.bg's history line carries no repeal marker

## naredba-3-za-zadalzhitelnite-predvaritelni-i-periodichni-meditsinski-pregledi-na
- title: НАРЕДБА № 3 ЗА ЗАДЪЛЖИТЕЛНИТЕ ПРЕДВАРИТЕЛНИ И ПЕРИОДИЧНИ МЕДИЦИНСКИ ПРЕГЛЕДИ НА РАБОТНИЦИТЕ
- kind: наредба; published 1987-02-27
- lex.bg's history line: Обн. ДВ. бр. 16 от 27 Февруари 1987г. , изм. ДВ. бр. 65 от 9 Август 1991г. , изм. ДВ. бр. 102 от 13 Декември 1994г. , изм. ДВ. бр. 78 от 30 Септември 2005г.
- repeal marker read from it: none
- the corpus's amendment rows: 4, the last: ДВ 65/1991 (1991-08-09); ДВ 102/1994 (1994-12-13); ДВ 78/2005 (2005-09-30)
- candidates:
  - material 143219, ДВ 95/2019 (2019-12-03): Наредба за отменяне на Наредба № 8 от 2005 г. за провеждане на задължителните начални, периодични и предсъстезателни медицински прегледи на лица, упражняващи физическо възпитание и спорт [shared words: задължителните, медицински, периодични, прегледи]

## naredba-4-za-bufernite-zoni-okolo-rezervatite
- title: НАРЕДБА № 4 ЗА БУФЕРНИТЕ ЗОНИ ОКОЛО РЕЗЕРВАТИТЕ
- kind: наредба; published 1980-10-03
- lex.bg's history line: Обн. ДВ. бр. 77 от 3 Октомври 1980г.
- repeal marker read from it: none
- the corpus's amendment rows: 1, the last: ДВ 77/1980 (1980-10-03)
- candidates: none share words with this title, and lex.bg's history line carries no repeal marker

## naredba-4-za-higiennite-iziskvaniya-pri-izpolzuvaneto-na-yazoviri-za-piteyno-bit
- title: НАРЕДБА № 4 ЗА ХИГИЕННИТЕ ИЗИСКВАНИЯ ПРИ ИЗПОЛЗУВАНЕТО НА ЯЗОВИРИ ЗА ПИТЕЙНО-БИТОВО ВОДОСНАБДЯВАНЕ
- kind: наредба; published 1984-03-02
- lex.bg's history line: Обн. ДВ. бр. 18 от 2 Март 1984г. , изм. ДВ. бр. 15 от 14 Февруари 2003г.
- repeal marker read from it: none
- the corpus's amendment rows: 2, the last: ДВ 18/1984 (1984-03-02); ДВ 15/2003 (2003-02-14)
- candidates:
  - material 174747, ДВ 56/2022 (2022-07-19): Наредба за отменяне на Наредба № 45 от 1995 г. за хигиенните норми и изисквания за добавките в хранителните продукти [shared words: изисквания, хигиенните]
