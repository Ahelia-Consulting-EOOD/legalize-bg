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

The answer file: `/Users/ekimir/swprj/legalize-bg/.claude/worktrees/unruffled-feynman-cd9070/data/runs/act-profiles-2026-10-31/calls/call-09-answer.yaml`

```yaml
# One YAML document: a mapping from each act's slug (every slug of the task, no other) to its verdict
<slug>:
  verdict: <in_force | repealed | unknown>
  repealed_by: <the material id of the candidate that repeals it, or 0 for lex.bg's own repeal marker, only when the verdict is repealed; otherwise null>
  evidence: <the facts and lines you relied on, in one or two sentences>
```

## pravilnik-za-finansovata-i-schetovodnata-otchetnost-na-sadebnite-uchrezhdeniya
- title: ПРАВИЛНИК ЗА ФИНАНСОВАТА И СЧЕТОВОДНАТА ОТЧЕТНОСТ НА СЪДЕБНИТЕ УЧРЕЖДЕНИЯ
- kind: правилник; published 1958-11-14
- lex.bg's history line: Обн. ДВ. бр. 91 от 14 Ноември 1958г.
- repeal marker read from it: none
- the corpus's amendment rows: 1, the last: ДВ 91/1958 (1958-11-14)
- candidates: none share words with this title, and lex.bg's history line carries no repeal marker

## pravilnik-za-izpalnenie-na-konventsiyata-za-zashtita-na-kulturnite-tsennosti-v-s
- title: ПРАВИЛНИК ЗА ИЗПЪЛНЕНИЕ НА КОНВЕНЦИЯТА ЗА ЗАЩИТА НА КУЛТУРНИТЕ ЦЕННОСТИ В СЛУЧАЙ НА ВЪОРЪЖЕН КОНФЛИКТ
- kind: правилник; published 1959-03-24
- lex.bg's history line: Обн. ДВ. бр. 24 от 24 Март 1959г.
- repeal marker read from it: none
- the corpus's amendment rows: 1, the last: ДВ 24/1959 (1959-03-24)
- candidates:
  - material 39474, ДВ 89/2010 (2010-11-12): Наредба за отменяне на Наредба № 14 от 2005 г. за дейностите при изпълнение на кадрова военна служба във въоръжените сили, за които поради тяхното естество или условията, при които се осъществяват, полът е съществено и определящо професионално изискване по смисъла на чл. 7, ал. 1, т. 2 от Закона за защита срещу дискриминацията [shared words: защита, изпълнение]
  - material 147536, ДВ 38/2020 (2020-04-24): Инструкция за отменяне на Инструкция № I-1298 от 2015 г. за вида на информацията и реда за предоставянето й от Министерството на вътрешните работи и Държавна агенция „Национална сигурност“ на Бюрото по защита при главния прокурор за изпълнение на функциите на бюрото [shared words: защита, изпълнение]

## pravilnik-za-kategorizirane-i-prekategorizirane-na-rakovoditelite-na-hudozhestve
- title: ПРАВИЛНИК ЗА КАТЕГОРИЗИРАНЕ И ПРЕКАТЕГОРИЗИРАНЕ НА РЪКОВОДИТЕЛИТЕ НА ХУДОЖЕСТВЕНАТА САМОДЕЙНОСТ
- kind: правилник; published 1969-11-19
- lex.bg's history line: Обн. ДВ. бр. 89 от 19 Ноември 1969г.
- repeal marker read from it: none
- the corpus's amendment rows: 1, the last: ДВ 89/1969 (1969-11-19)
- candidates: none share words with this title, and lex.bg's history line carries no repeal marker

## pravilnik-za-legalizatsiite-zaverkite-i-prevodite-na-dokumenti-i-drugi-knizha-za
- title: ПРАВИЛНИК ЗА ЛЕГАЛИЗАЦИИТЕ, ЗАВЕРКИТЕ И ПРЕВОДИТЕ НА ДОКУМЕНТИ И ДРУГИ КНИЖА (ЗАГЛ. ИЗМ. - ДВ, БР. 96 ОТ 1982 Г., В СИЛА ОТ 01.01.1983 Г.)
- kind: правилник; published 1958-09-12
- lex.bg's history line: Обн. ДВ. бр. 73 от 12 Септември 1958г. , доп. ДВ. бр. 10 от 4 Февруари 1964г. , доп. ДВ. бр. 77 от 28 Септември 1976г. , изм. ДВ. бр. 96 от 7 Декември […] , изм. ДВ. бр. 77 от 4 Октомври 1983г. , изм. ДВ. бр. 103 от 25 Декември 1990г. , изм. и доп. ДВ. бр. 95 от 28 Ноември 2017г. , изм. ДВ. бр. 7 от 22 Януари 2019г. , изм. ДВ. бр. 41 от 21 Май 2019г. , доп. ДВ. бр. 39 от 28 Април 2020г. , изм. ДВ. бр. 31 от 7 Април 2023г.
- repeal marker read from it: none
- the corpus's amendment rows: 11, the last: ДВ 41/2019 (2019-05-21); ДВ 39/2020 (2020-04-28); ДВ 31/2023 (2023-04-07)
- candidates: none share words with this title, and lex.bg's history line carries no repeal marker

## pravilnik-za-mitnishkiya-nadzor-po-reka-dunav
- title: ПРАВИЛНИК ЗА МИТНИШКИЯ НАДЗОР ПО РЕКА ДУНАВ
- kind: правилник; published 1954-03-19
- lex.bg's history line: Обн. ДВ. бр. 23 от 19 Март 1954г.
- repeal marker read from it: none
- the corpus's amendment rows: 1, the last: ДВ 23/1954 (1954-03-19)
- candidates: none share words with this title, and lex.bg's history line carries no repeal marker

## pravilnik-za-ohranata-na-truda-na-uchashtite-se-pri-provezhdane-na-proizvodstven
- title: ПРАВИЛНИК ЗА ОХРАНАТА НА ТРУДА НА УЧАЩИТЕ СЕ ПРИ ПРОВЕЖДАНЕ НА ПРОИЗВОДСТВЕНО ОБУЧЕНИЕ И ПРОИЗВОДСТВЕНА ПРАКТИКА
- kind: правилник; published 1961-02-10
- lex.bg's history line: Обн. ДВ. бр. 12 от 10 Февруари 1961г.
- repeal marker read from it: none
- the corpus's amendment rows: 1, the last: ДВ 12/1961 (1961-02-10)
- candidates: none share words with this title, and lex.bg's history line carries no repeal marker

## pravilnik-za-organizatsiyata-na-kontrolnite-organi-po-radiatsionna-bezopasnost
- title: ПРАВИЛНИК ЗА ОРГАНИЗАЦИЯТА НА КОНТРОЛНИТЕ ОРГАНИ ПО РАДИАЦИОННА БЕЗОПАСНОСТ
- kind: правилник; published 1975-05-13
- lex.bg's history line: Обн. ДВ. бр. 36 от 13 Май 1975г.
- repeal marker read from it: none
- the corpus's amendment rows: 1, the last: ДВ 36/1975 (1975-05-13)
- candidates:
  - material 87270, ДВ 69/2014 (2014-08-19): Наредба за отменяне на Наредба № I-167 от 2002 г. за условията и реда за взаимодействие между контролните органи на Министерството на вътрешните работи, застрахователните компании и Агенцията за застрахователен надзор при настъпване на застрахователни събития, свързани с моторните превозни средства [shared words: контролните, органи]

## pravilnik-za-planirane-na-naselenite-mesta
- title: ПРАВИЛНИК ЗА ПЛАНИРАНЕ НА НАСЕЛЕНИТЕ МЕСТА
- kind: правилник; published 1985-05-01
- lex.bg's history line: none on the page
- repeal marker read from it: none
- the corpus's amendment rows: 0, the last: none
- candidates:
  - material 3143, ДВ 5/2007 (2007-01-18): Наредба за отменяне на Наредба № 4 от 1999 г. за защита от шум на територията на населените места [shared words: места, населените]
  - material 21286, ДВ 30/2004 (2004-04-13): Наредба за отменяне на Наредба № 3 от 1989 г. за запазване на сградните и благоустройствените фондове в населените места [shared words: места, населените]

## pravilnik-za-podgotovka-na-izpalnitelski-kontrolni-i-rakovodni-kadri-po-elektrod
- title: ПРАВИЛНИК ЗА ПОДГОТОВКА НА ИЗПЪЛНИТЕЛСКИ, КОНТРОЛНИ И РЪКОВОДНИ КАДРИ ПО ЕЛЕКТРОДЪГОВО ЗАВАРЯВАНЕ
- kind: правилник; published 1965-07-13
- lex.bg's history line: Обн. ДВ. бр.55 от 13 Юли 1965г. , изм. ДВ. бр. 25 от 27 Март 1979г.
- repeal marker read from it: none
- the corpus's amendment rows: 2, the last: ДВ 55/1965 (1965-07-13); ДВ 25/1979 (1979-03-27)
- candidates: none share words with this title, and lex.bg's history line carries no repeal marker

## pravilnik-za-podgotovka-na-izpalnitelski-kontrolni-i-rakovodni-kadri-po-gazokisl
- title: ПРАВИЛНИК ЗА ПОДГОТОВКА НА ИЗПЪЛНИТЕЛСКИ, КОНТРОЛНИ И РЪКОВОДНИ КАДРИ ПО ГАЗОКИСЛОРОДНО РЯЗАНЕ И ЗАВАРЯВАНЕ
- kind: правилник; published 1970-06-30
- lex.bg's history line: Обн. ДВ. бр.51 от 30 Юни 1970г. , изм. ДВ. бр. 25 от 27 Март 1979г.
- repeal marker read from it: none
- the corpus's amendment rows: 2, the last: ДВ 51/1970 (1970-06-30); ДВ 25/1979 (1979-03-27)
- candidates: none share words with this title, and lex.bg's history line carries no repeal marker
