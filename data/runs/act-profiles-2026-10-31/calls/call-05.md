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

The answer file: `/Users/ekimir/swprj/legalize-bg/.claude/worktrees/unruffled-feynman-cd9070/data/runs/act-profiles-2026-10-31/calls/call-05-answer.yaml`

```yaml
# One YAML document: a mapping from each act's slug (every slug of the task, no other) to its verdict
<slug>:
  verdict: <in_force | repealed | unknown>
  repealed_by: <the material id of the candidate that repeals it, or 0 for lex.bg's own repeal marker, only when the verdict is repealed; otherwise null>
  evidence: <the facts and lines you relied on, in one or two sentences>
```

## naredba-11-za-reda-za-priemane-na-izvarsheni-konservatsionni-i-restavratsionni-r
- title: НАРЕДБА № 11 ЗА РЕДА ЗА ПРИЕМАНЕ НА ИЗВЪРШЕНИ КОНСЕРВАЦИОННИ И РЕСТАВРАЦИОННИ РАБОТИ ПО НЕДВИЖИМИ ПАМЕТНИЦИ НА КУЛТУРАТА
- kind: наредба; published 1983-03-29
- lex.bg's history line: Обн. ДВ. бр. 25 от 29 Март 1983г.
- repeal marker read from it: none
- the corpus's amendment rows: 1, the last: ДВ 25/1983 (1983-03-29)
- candidates:
  - material 8162, ДВ 75/2008 (2008-08-26): Наредба за отменяне на Наредба № Iз-441 от 2008 г. за определяне на категориите служители, осъществяващи правомощията си в униформено облекло, неговия вид и модел, реда за предоставянето му, както и другите принадлежности, свързани с изпълнението на служебните задължения на служителите, върху които са поставени символи и отличителни знаци на структурните звена на Министерството на вътрешните работи [shared words: работи, реда]
  - material 70892, ДВ 98/2012 (2012-12-11): Наредба за отменяне на Наредба № Із-1215 от 2006 г. за реда за достъп до информационните фондове на Министерството на вътрешните работи [shared words: работи, реда]
  - material 87270, ДВ 69/2014 (2014-08-19): Наредба за отменяне на Наредба № I-167 от 2002 г. за условията и реда за взаимодействие между контролните органи на Министерството на вътрешните работи, застрахователните компании и Агенцията за застрахователен надзор при настъпване на застрахователни събития, свързани с моторните превозни средства [shared words: работи, реда]
  - material 87379, ДВ 69/2014 (2014-08-19): Инструкция за отменяне на Инструкция № Із-2453 от 2012 г. за реда за разпределяне на работното време на държавните служители в Министерството на вътрешните работи, отчитането му и компенсиране на работата извън установеното работно време [shared words: работи, реда]
  - material 88746, ДВ 87/2014 (2014-10-21): Инструкция за отменяне на Инструкция № Iз-1863 от 2009 г. за реда за издаване на удостоверителни документи за досъдебни производства в Министерството на вътрешните работи [shared words: работи, реда]
  - material 97483, ДВ 73/2015 (2015-09-25): Наредба за отменяне на Наредба № 8121з-617 от 2014 г. за изискванията към извънщатните сътрудници на Министерството на вътрешните работи, реда за вписването им, техните функции и ред за координация и ръководство на дейността им [shared words: работи, реда]
  - material 99467, ДВ 100/2015 (2015-12-18): Инструкция за отменяне на Инструкция № Із-849 от 2007 г. за условията и реда, при които органите на Министерството на вътрешните работи оказват съдействие на частните и държавните съдебни изпълнители при изпълнение на техните правомощия [shared words: работи, реда]
  - material 109621, ДВ 97/2016 (2016-12-06): Наредба за отменяне на Наредба № 8121з-196 от 2015 г. за реда за осъществяване на превантивен контрол от органите за пожарна безопасност и защита на населението на Министерството на вътрешните работи [shared words: работи, реда]
  - material 147536, ДВ 38/2020 (2020-04-24): Инструкция за отменяне на Инструкция № I-1298 от 2015 г. за вида на информацията и реда за предоставянето й от Министерството на вътрешните работи и Държавна агенция „Национална сигурност“ на Бюрото по защита при главния прокурор за изпълнение на функциите на бюрото [shared words: работи, реда]
  - material 194720, ДВ 45/2023 (2023-05-23): Инструкция за отменяне на Инструкция № Із-547 от 11 март 2013 г. за условията и реда за дейността на дирекция „Специална куриерска служба“ на Министерството на вътрешните работи по осигуряване на военна пощенска свръзка при бедствия, при въвеждане на режим „военно положение“ или „положение на война“ [shared words: работи, реда]

## naredba-11-za-ustanovyavane-na-shteti-ot-avarii-pri-targovskoto-moreplavane
- title: НАРЕДБА № 11 ЗА УСТАНОВЯВАНЕ НА ЩЕТИ ОТ АВАРИИ ПРИ ТЪРГОВСКОТО МОРЕПЛАВАНЕ
- kind: наредба; published 1975-08-29
- lex.bg's history line: Обн. ДВ. бр. 67 от 29 Август 1975г.
- repeal marker read from it: none
- the corpus's amendment rows: 1, the last: ДВ 67/1975 (1975-08-29)
- candidates: none share words with this title, and lex.bg's history line carries no repeal marker

## naredba-13a-10403-za-predelnite-razmeri-na-estestvenite-firi-braka-i-lipsite-na-
- title: НАРЕДБА № 13а-10403 ЗА ПРЕДЕЛНИТЕ РАЗМЕРИ НА ЕСТЕСТВЕНИТЕ ФИРИ, БРАКА И ЛИПСИТЕ НА СТОКОВО-МАТЕРИАЛНИ ЦЕННОСТИ ПРИ СЪХРАНЯВАНЕТО И ТРАНСПОРТИРАНЕТО ИМ (ЗАГЛ ДОП. - ДВ, БР. 28 ОТ 1980 Г.)
- kind: наредба; published 1959-07-31
- lex.bg's history line: Обн. ДВ. бр.61 от 31 Юли 1959г. , изм. ДВ. бр.62 от 4 Август 1961г. , изм. ДВ. бр.55 от 10 Юли 1962г. , изм. ДВ. бр.63 от 7 Август 1962г. , изм. ДВ. б […]  17 Януари 1964г. , изм. ДВ. бр.10 от 4 Февруари 1964г. , изм. ДВ. бр.60 от 31 Юли 1964г. , изм. ДВ. бр.23 от 21 Март 1969г. , изм. ДВ. бр.3 от 11 Януари 1972г. , изм. ДВ. бр.14 от 17 Февруари 1976г. , изм. ДВ. бр. 28 от 8 Април 1980г. , изм. ДВ. бр. 41 от 22 Май 2007г.
- repeal marker read from it: none
- the corpus's amendment rows: 15, the last: ДВ 14/1976 (1976-02-17); ДВ 28/1980 (1980-04-08); ДВ 41/2007 (2007-05-22)
- candidates: none share words with this title, and lex.bg's history line carries no repeal marker

## naredba-14-ot-3-avgust-1987-g-za-kurortnite-resursi-kurortnite-mestnosti-i-kuror
- title: НАРЕДБА № 14 ОТ 3 АВГУСТ 1987 Г. ЗА КУРОРТНИТЕ РЕСУРСИ, КУРОРТНИТЕ МЕСТНОСТИ И КУРОРТИТЕ
- kind: наредба; published 1987-10-13
- lex.bg's history line: Обн. ДВ. бр. 79 от 13 Октомври 1987г. , изм. ДВ. бр. 18 от 2 Март 1992г. , изм. ДВ. бр. 12 от 3 Февруари 1995г. , изм. ДВ. бр. 88 от 27 Октомври 2000г. , изм. ДВ. бр. 25 от 8 Март 2002г. , изм. ДВ. бр. 70 от 10 Август 2004г.
- repeal marker read from it: none
- the corpus's amendment rows: 6, the last: ДВ 88/2000 (2000-10-27); ДВ 25/2002 (2002-03-08); ДВ 70/2004 (2004-08-10)
- candidates: none share words with this title, and lex.bg's history line carries no repeal marker

## naredba-1461-za-sadebno-schetovodnite-i-finansovo-ikonomicheskite-ekspertizi
- title: НАРЕДБА № 1461 ЗА СЪДЕБНО-СЧЕТОВОДНИТЕ И ФИНАНСОВО-ИКОНОМИЧЕСКИТЕ ЕКСПЕРТИЗИ
- kind: наредба; published 1975-10-31
- lex.bg's history line: Обн. ДВ. бр. 84 от 31 Октомври 1975г.
- repeal marker read from it: none
- the corpus's amendment rows: 1, the last: ДВ 84/1975 (1975-10-31)
- candidates: none share words with this title, and lex.bg's history line carries no repeal marker

## naredba-15-ot-21-avgust-1987-g-za-higiennite-iziskvaniya-za-brasnarskite-frizyor
- title: НАРЕДБА № 15 ОТ 21 АВГУСТ 1987 Г. ЗА ХИГИЕННИТЕ ИЗИСКВАНИЯ ЗА БРЪСНАРСКИТЕ, ФРИЗЬОРСКИТЕ И КОЗМЕТИЧНИТЕ САЛОНИ
- kind: наредба; published 1987-10-06
- lex.bg's history line: Обн. ДВ. бр. 77 от 6 Октомври 1987г.
- repeal marker read from it: none
- the corpus's amendment rows: 1, the last: ДВ 77/1987 (1987-10-06)
- candidates:
  - material 174747, ДВ 56/2022 (2022-07-19): Наредба за отменяне на Наредба № 45 от 1995 г. за хигиенните норми и изисквания за добавките в хранителните продукти [shared words: изисквания, хигиенните]

## naredba-16-za-higiennite-i-veterinarno-sanitarnite-iziskvaniya-za-sahranyavane-i
- title: НАРЕДБА № 16 ЗА ХИГИЕННИТЕ И ВЕТЕРИНАРНО-САНИТАРНИТЕ ИЗИСКВАНИЯ ЗА СЪХРАНЯВАНЕ И ИЗПОЛЗУВАНЕ НА ОСОБЕНО БЪРЗОРАЗВАЛЯЩИТЕ СЕ ХРАНИТЕЛНИ ПРОДУКТИ
- kind: наредба; published 1984-10-19
- lex.bg's history line: Обн. ДВ. бр. 83 от 19 Октомври 1984г.
- repeal marker read from it: none
- the corpus's amendment rows: 1, the last: ДВ 83/1984 (1984-10-19)
- candidates:
  - material 31928, ДВ 29/2010 (2010-04-16), a line of the general repeal decree „Постановление № 61 от 8 април 2010 г. за отменяне на нормативни актове на Министерския съвет“: 1. Наредбата за съществените изисквания и оценяване на съответствието на домашни електрически хладилници, замразители, уреди за съхраняване на замразени хранителни продукти и комбинации между тях, приета с Постановление № 193 на Министерския съвет от 2002 г. (обн., ДВ, бр. 84 от 2002 г.; изм. и доп., бр. 24 и 28 от 2006 г., бр. 37 от 2007 г. и бр. 97 от 2008 г.); [shared words: изисквания, продукти, съхраняване, хранителни]
  - material 174747, ДВ 56/2022 (2022-07-19): Наредба за отменяне на Наредба № 45 от 1995 г. за хигиенните норми и изисквания за добавките в хранителните продукти [shared words: изисквания, продукти, хигиенните]

## naredba-16-za-opredelyane-na-uvelichenata-stoynost-i-vpisvane-na-zakonna-ipoteka
- title: НАРЕДБА № 16 ЗА ОПРЕДЕЛЯНЕ НА УВЕЛИЧЕНАТА СТОЙНОСТ И ВПИСВАНЕ НА ЗАКОННА ИПОТЕКА ВЪРХУ НЕДВИЖИМИ ИМОТИ - ПАМЕТНИЦИ НА КУЛТУРАТА
- kind: наредба; published 1978-07-28
- lex.bg's history line: Обн. ДВ. бр. 59 от 28 Юли 1978г.
- repeal marker read from it: none
- the corpus's amendment rows: 1, the last: ДВ 59/1978 (1978-07-28)
- candidates: none share words with this title, and lex.bg's history line carries no repeal marker

## naredba-165-za-otdavane-pod-naem-na-grazhdanski-vazduhoplavatelni-sredstva
- title: НАРЕДБА № 165 ЗА ОТДАВАНЕ ПОД НАЕМ НА ГРАЖДАНСКИ ВЪЗДУХОПЛАВАТЕЛНИ СРЕДСТВА
- kind: наредба; published 1976-01-13
- lex.bg's history line: Обн. ДВ. бр. 4 от 13 Януари 1976г.
- repeal marker read from it: none
- the corpus's amendment rows: 1, the last: ДВ 4/1976 (1976-01-13)
- candidates: none share words with this title, and lex.bg's history line carries no repeal marker

## naredba-18-za-higiennite-iziskvaniya-za-oblekloto-za-detsa-do-14-godishna-vazras
- title: НАРЕДБА № 18 ЗА ХИГИЕННИТЕ ИЗИСКВАНИЯ ЗА ОБЛЕКЛОТО ЗА ДЕЦА ДО 14-ГОДИШНА ВЪЗРАСТ
- kind: наредба; published 1979-08-14
- lex.bg's history line: Обн. ДВ. бр. 64 от 14 Август 1979г.
- repeal marker read from it: none
- the corpus's amendment rows: 1, the last: ДВ 64/1979 (1979-08-14)
- candidates:
  - material 174747, ДВ 56/2022 (2022-07-19): Наредба за отменяне на Наредба № 45 от 1995 г. за хигиенните норми и изисквания за добавките в хранителните продукти [shared words: изисквания, хигиенните]
