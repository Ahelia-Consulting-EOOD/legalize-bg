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

The answer file: `/Users/ekimir/swprj/legalize-bg/.claude/worktrees/unruffled-feynman-cd9070/data/runs/act-profiles-2026-10-31/calls/call-08-answer.yaml`

```yaml
# One YAML document: a mapping from each act's slug (every slug of the task, no other) to its verdict
<slug>:
  verdict: <in_force | repealed | unknown>
  repealed_by: <the material id of the candidate that repeals it, or 0 for lex.bg's own repeal marker, only when the verdict is repealed; otherwise null>
  evidence: <the facts and lines you relied on, in one or two sentences>
```

## naredba-za-otchitane-sahranyavane-prevozvane-na-yadren-material-i-prilagane-na-g
- title: НАРЕДБА ЗА ОТЧИТАНЕ, СЪХРАНЯВАНЕ, ПРЕВОЗВАНЕ НА ЯДРЕН МАТЕРИАЛ И ПРИЛАГАНЕ НА ГАРАНЦИИТЕ ПО ДОГОВОРА ЗА НЕРАЗПРОСТРАНЕНИЕ НА ЯДРЕНОТО ОРЪЖИЕ (ЗАГЛ. ИЗМ. - ДВ, БР. 33 ОТ 2001 Г.)
- kind: наредба; published 1988-08-26
- lex.bg's history line: Обн. ДВ. бр. 66 от 26 Август 1988г. , изм. ДВ. бр. 83 от 30 Септември 1993г. , изм. ДВ. бр. 33 от 4 Април 2001г.
- repeal marker read from it: none
- the corpus's amendment rows: 3, the last: ДВ 66/1988 (1988-08-26); ДВ 83/1993 (1993-09-30); ДВ 33/2001 (2001-04-04)
- candidates: none share words with this title, and lex.bg's history line carries no repeal marker

## naredba-za-rabotata-na-litsata-nenavarshili-15-godishna-vazrast
- title: НАРЕДБА ЗА РАБОТАТА НА ЛИЦАТА, НЕНАВЪРШИЛИ 15-ГОДИШНА ВЪЗРАСТ
- kind: наредба; published 1987-01-30
- lex.bg's history line: Обн. ДВ. бр. 8 от 30 Януари 1987г. , изм. ДВ. бр. 59 от 9 Юли 1993г. , изм. ДВ. бр. 35 от 10 Април 2001г.
- repeal marker read from it: none
- the corpus's amendment rows: 3, the last: ДВ 8/1987 (1987-01-30); ДВ 59/1993 (1993-07-09); ДВ 35/2001 (2001-04-10)
- candidates: none share words with this title, and lex.bg's history line carries no repeal marker

## naredba-za-rabotnoto-vreme-pochivkite-i-otpuskite
- title: НАРЕДБА ЗА РАБОТНОТО ВРЕМЕ, ПОЧИВКИТЕ И ОТПУСКИТЕ
- kind: наредба; published 1987-01-23
- lex.bg's history line: Обн. ДВ. бр. 6 от 23 Януари 1987г. , изм. ДВ. бр. 31 от 19 Април 1991г. , изм. ДВ. бр. 55 от 12 Юли 1991г. , изм. ДВ. бр. 59 от 23 Юли 1991г. , изм. Д […] . 41 от 23 Май 2017г. , изм. и доп. ДВ. бр. 58 от 13 Юли 2018г. , изм. ДВ. бр. 18 от 28 Февруари 2020г. , доп. ДВ. бр. 56 от 23 Юни 2020г. , изм. и доп. ДВ. бр. 78 от 30 Септември 2022г. , изм. и доп. ДВ. бр. 52 от 18 Юни 2024г. , изм. и доп. ДВ. бр. 52 от 27 Юни 2025г.
- repeal marker read from it: none
- the corpus's amendment rows: 27, the last: ДВ 78/2022 (2022-09-30); ДВ 52/2024 (2024-06-18); ДВ 52/2025 (2025-06-27)
- candidates:
  - material 87379, ДВ 69/2014 (2014-08-19): Инструкция за отменяне на Инструкция № Із-2453 от 2012 г. за реда за разпределяне на работното време на държавните служители в Министерството на вътрешните работи, отчитането му и компенсиране на работата извън установеното работно време [shared words: време, работното]

## naredba-za-trudoustroyavane
- title: НАРЕДБА ЗА ТРУДОУСТРОЯВАНЕ
- kind: наредба; published 1987-01-27
- lex.bg's history line: Обн. ДВ. бр. 7 от 27 Януари 1987г. , доп. ДВ. бр. 52 от 8 Юли 1988г. , доп. ДВ. бр. 47 от 12 Юни 1990г. , изм. ДВ. бр. 111 от 28 Декември 2001г. , изм. ДВ. бр. 78 от 30 Септември 2005г. , изм. ДВ. бр. 17 от 28 Февруари 2014г.
- repeal marker read from it: none
- the corpus's amendment rows: 6, the last: ДВ 111/2001 (2001-12-28); ДВ 78/2005 (2005-09-30); ДВ 17/2014 (2014-02-28)
- candidates: none share words with this title, and lex.bg's history line carries no repeal marker

## pravilnik-18-za-zadachite-organizatsiyata-i-vatreshniya-red-v-stolovete-i-byufet
- title: ПРАВИЛНИК № 18 ЗА ЗАДАЧИТЕ, ОРГАНИЗАЦИЯТА И ВЪТРЕШНИЯ РЕД В СТОЛОВЕТЕ И БЮФЕТИТЕ ПРИ УЧИЛИЩАТА
- kind: правилник; published 1974-10-01
- lex.bg's history line: Обн. ДВ. бр. 76 от 1 Октомври 1974г.
- repeal marker read from it: none
- the corpus's amendment rows: 1, the last: ДВ 76/1974 (1974-10-01)
- candidates:
  - material 134515, ДВ 12/2019 (2019-02-08): Постановление № 19 от 1 февруари 2019 г. за отменяне на Постановление № 216 на Министерския съвет от 1998 г. за създаване на Съвет по сигурността при Министерския съвет и за приемане на правилник за неговите функции, задачи и организация на работа и на Правилника за функциите, задачите и организацията на работа на Съвета по сигурността при Министерския съвет [shared words: задачите, организацията]

## pravilnik-d-01-016-za-bezopasnostta-na-truda-pri-proizvodstvoto-transporta-sahra
- title: ПРАВИЛНИК № Д-01-016 ЗА БЕЗОПАСНОСТТА НА ТРУДА ПРИ ПРОИЗВОДСТВОТО, ТРАНСПОРТА, СЪХРАНЯВАНЕТО И УПОТРЕБАТА НА КИСЛОРОД
- kind: правилник; published 1982-01-01
- lex.bg's history line: none on the page
- repeal marker read from it: none
- the corpus's amendment rows: 0, the last: none
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

## pravilnik-na-edinnata-natsionalna-sistema-ot-kolektsii-za-kulturi
- title: ПРАВИЛНИК НА ЕДИННАТА НАЦИОНАЛНА СИСТЕМА ОТ КОЛЕКЦИИ ЗА КУЛТУРИ
- kind: правилник; published 1975-03-18
- lex.bg's history line: Обн. ДВ. бр. 22 от 18 Март 1975г.
- repeal marker read from it: none
- the corpus's amendment rows: 1, the last: ДВ 22/1975 (1975-03-18)
- candidates: none share words with this title, and lex.bg's history line carries no repeal marker

## pravilnik-za-deynostta-na-protivosvlachishtnite-stantsii-v-narodna-republika-bal
- title: ПРАВИЛНИК ЗА ДЕЙНОСТТА НА ПРОТИВОСВЛАЧИЩНИТЕ СТАНЦИИ В НАРОДНА РЕПУБЛИКА БЪЛГАРИЯ
- kind: правилник; published 1973-02-27
- lex.bg's history line: Обн. ДВ. бр. 17 от 27 Февруари 1973г.
- repeal marker read from it: none
- the corpus's amendment rows: 1, the last: ДВ 17/1973 (1973-02-27)
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

## pravilnik-za-deynostta-na-shtabovete-za-podobryavane-na-rabotata-v-zhelezopatniy
- title: ПРАВИЛНИК ЗА ДЕЙНОСТТА НА ЩАБОВЕТЕ ЗА ПОДОБРЯВАНЕ НА РАБОТАТА В ЖЕЛЕЗОПЪТНИЯ, ВОДНИЯ И АВТОМОБИЛНИЯ ТРАНСПОРТ, СЪЗДАДЕНИ С РЕШЕНИЕ № 31 НА МИНИСТЕРСКИЯ СЪВЕТ ОТ 20 ФЕВРУАРИ 1979 Г.
- kind: правилник; published 1977-04-26
- lex.bg's history line: Обн. ДВ. бр. 33 от 26 Април 1977г.
- repeal marker read from it: none
- the corpus's amendment rows: 1, the last: ДВ 33/1977 (1977-04-26)
- candidates:
  - material 2130, ДВ 53/2006 (2006-06-30): Постановление № 152 от 21 юни 2006 г. за отменяне на Постановление № 147 на Министерския съвет от 2005 г. за структурни промени в системата на здравеопазването [shared words: министерския, съвет]
  - material 2313, ДВ 63/2006 (2006-08-04), a line of the general repeal decree „Постановление № 183 от 25 юли 2006 г. за отменяне на нормативни актове на Министерския съвет“: за отменяне на нормативни актове на Министерския съвет [shared words: министерския, съвет]
  - material 2755, ДВ 88/2006 (2006-10-31), a line of the general repeal decree „Постановление № 281 от 20 октомври 2006 г. за отменяне на нормативни актове на Министерския съвет“: за отменяне на нормативни актове на Министерския съвет [shared words: министерския, съвет]
  - material 2758, ДВ 88/2006 (2006-10-31), a line of the general repeal decree „Постановление № 284 от 23 октомври 2006 г. за отменяне на нормативни актове на Министерския съвет“: за отменяне на нормативни актове на Министерския съвет [shared words: министерския, съвет]
  - material 5791, ДВ 60/2008 (2008-07-04), a line of the general repeal decree „Постановление № 149 от 27 юни 2008 г. за отменяне на нормативни актове на Министерския съвет“: за отменяне на нормативни актове на Министерския съвет [shared words: министерския, съвет]
  - material 15239, ДВ 34/2005 (2005-04-19), a line of the general repeal decree „Постановление № 65 от 8 април 2005 г. за отменяне на нормативни актове“: Главен секретар на Министерския съвет: Севдалин Мавров [shared words: министерския, съвет]
  - material 19100, ДВ 77/2004 (2004-09-03): Решение № 680 от 24 август 2004 г. за отменяне на Решение № 84 на Министерския съвет от 2004 г. за определяне на спечелилия присъствен конкурс кандидат за предоставяне на концесия върху бъдещ обект - водностопански съоръжения язовир “Раков дол”, изравнителен водоем и гравитачна деривация от него - публична държавна собственост, които ще бъдат изградени със средства на концесионера [shared words: министерския, съвет]
  - material 19785, ДВ 58/2004 (2004-07-06): Постановление № 150 от 2 юли 2004 г. за отменяне на Постановление № 193 на Министерския съвет от 2003 г. за временна забрана на износа на пшеница и брашно [shared words: министерския, съвет]
  - material 20182, ДВ 50/2004 (2004-06-11): Решение № 468 от 31 май 2004 г. за отменяне на Решение № 741 на Министерския съвет от 2003 г. за предоставяне на концесия върху част от минералната вода, обект - изключителна държавна собственост, от находище “Бързия”, с. Бързия, община Берковица, област Монтана, разкрита чрез сондаж № 1 [shared words: министерския, съвет]
  - material 21325, ДВ 27/2004 (2004-04-01): Решение № 213 от 23 март 2004 г. за отменяне на Решение № 414 на Министерския съвет от 2001 г. за предоставяне на концесия върху водоснабдителни и канализационни системи и даване на разрешение за дейностите водоснабдяване и канализация на територията на общините Варна-град, Провадия, Дългопол, Аксаково, Вълчи дол, Аврен, Бяла, Ветрино, Девня, Суворово, Долни чифлик и Белослав в област Варна и на територията на общините Шумен-град, Нови пазар, Върбица, Каолиново, Каспичан, Венец, гара Хитрино, Никола Козлево и Смядово в област Шумен [shared words: министерския, съвет]
  - material 21361, ДВ 25/2004 (2004-03-26): Постановление № 60 от 16 март 2004 г. за отменяне на Постановление № 15 на Министерския съвет от 2002 г. за изпълнение от 1 януари 2002 г. на задълженията на Република България, произтичащи от Споразумението за свободна търговия между Република България и Република Естония [shared words: министерския, съвет]
  - material 21997, ДВ 45/2009 (2009-06-16): Наредба за отменяне на Наредба № 247 от 1995 г. за звената за обработка на архивни фондове и документи на физически и юридически лица, издадена от Главно управление на архивите при Министерския съвет [shared words: министерския, съвет]

## pravilnik-za-deynostta-na-vakuumnata-dezinsektsionna-kamera-v-gr-burgas
- title: ПРАВИЛНИК ЗА ДЕЙНОСТТА НА ВАКУУМНАТА ДЕЗИНСЕКЦИОННА КАМЕРА В ГР. БУРГАС
- kind: правилник; published 1963-01-29
- lex.bg's history line: Обн. ДВ. бр. 8 от 29 Януари 1963г.
- repeal marker read from it: none
- the corpus's amendment rows: 1, the last: ДВ 8/1963 (1963-01-29)
- candidates: none share words with this title, and lex.bg's history line carries no repeal marker
