# Witness differences of pravilnik-za-prilagane-na-zakona-za-zashtita-na-litsa-zastrasheni-vav-vrazka-s-n

Settle every difference below: for each, one verdict from the closed set, and a short evidence note naming what you relied on.
The source is the text the act was read from (the Gazette material); the witness is lex.bg or the Ministry of Justice portal. Our body is the source's text as we read it, so a difference can also be our own reading's error.
Verdicts: `source_error`: the source's text is wrong here (a misprint in the Gazette, for example); our body keeps it, the record names it; `witness_error`: the witness's text is wrong here; lex.bg or the portal, not the source; `timing`: the witness carries an amendment, or lacks one, that the source text does not yet or no longer reflect; `same_text_other_form`: the same text in another form: a line the witness adds that is not the act's (an editorial note, a separator), a numbering style, a character the normalisation does not cover; `reading_error`: our body is wrong here: the split, a label or a join of ours lost or moved text; the write stops.
Both sides were normalised before the comparison: whitespace runs become one space; leading and trailing whitespace is removed; quotation marks „ “ ” « » ' are all written as "; the dashes – and — are written as -; the dot that closes a heading number (Глава първа., Раздел I.) is removed, and a heading number line is joined to its title line; inside an amendment marker the entry-into-force clause (", в сила от 22.12.2023 г.") is removed, since the engine of F1 writes the marker without it (1 November 2026); nothing else: a Latin letter for a Cyrillic one, a missing word, a different number, a line joined or split are differences.
Write exactly one JSON object to `/Users/ekimir/swprj/legalize-bg/.claude/worktrees/jolly-wright-479586/data/runs/f1-engine-2026-11-01/pravilnik-za-prilagane-na-zakona-za-zashtita-na-litsa-zastrasheni-vav-vrazka-s-n/witness-answer.json`: its first key `"diff_sha256"` with the value `"978a367e5d226150563ba0ef6e1aa4c75a49a7858395ac1db2f30e1c2a7f8764"` (the hash of the diff you are answering), then one key per witness name, its value an object keyed by the difference number as a string, each value `{"verdict": "<one of the five>", "note": "<short evidence note>"}`. Nothing else: no prose, no code fence.

## witness lexbg
17 difference(s); our body 309 lines, the witness 320 lines
### 1 (replace, our line 0, witness line 0)
- ours: `за прилагане на Закона за защита на лица, застрашени във връзка`
- witness: `ЗА ПРИЛАГАНЕ НА ЗАКОНА ЗА ЗАЩИТА НА ЛИЦА, ЗАСТРАШЕНИ ВЪВ ВРЪЗКА С НАКАЗАТЕЛНО ПРОИЗВОДСТВО Приет`
- around: `ПРАВИЛНИК [...] с наказателно производство`
### 2 (replace, our line 0, witness line 1)
- ours: `наказателно производство`
- witness: `ПМС № 242 от 09.11.2018 г.`
- around: `на лица, застрашени във връзка с [...] `
### 3 (structure, our line 0, witness line 0)
- ours: `ПРАВИЛНИК за прилагане на Закона за защита на лица, застрашени във връзка с наказателно производство`
- witness: `ПРАВИЛНИК ЗА ПРИЛАГАНЕ НА ЗАКОНА ЗА ЗАЩИТА НА ЛИЦА, ЗАСТРАШЕНИ ВЪВ ВРЪЗКА С НАКАЗАТЕЛНО ПРОИЗВОДСТВО | Приет с ПМС № 242 от 09.11.2018 г.`
- around: ` [...] 1 line(s) of ours against 2 of the witness, with the differences above inside`
### 4 (replace, our line 49, witness line 50)
- ours: `възможности­те`
- witness: `възможностите`
- around: `жилища се осъществява след проучване на [...] и анализ на средата, в която`
### 5 (witness_line, our line 98, witness line 99)
- ours: ``
- witness: `Раздел II Главен прокурор`
- around: `Раздел II Министър на правосъдието (Загл. изм. - ДВ, бр. 100 от 2021 г.) [...] Чл. 26. (Изм. - ДВ, бр. 100 от 2021 г.) (1) Министърът на правосъдието осъществява общо ръководство и контрол върху дейността на Бюрото по защита.`
### 6 (witness_line, our line 157, witness line 159)
- ours: ``
- witness: `Раздел III Бюро по защита при главния прокурор`
- around: `Раздел III Бюро по защита на застрашени лица (Загл. изм. - ДВ, бр. 100 от 2021 г.) [...] Чл. 28. (1) (Изм. - ДВ, бр. 100 от 2021 г.) Бюрото по защита е юридическо лице със седалище в гр. София. Ръководителят на Бюрото по защита на застрашени лица е второстепенен разпоредител с бюджет по бюджета на Министерството на правосъдието.`
### 7 (replace, our line 238, witness line 241)
- ours: `І`
- witness: `I`
- around: `Раздел [...] Предоставяне на предварителна защита`
### 8 (replace, our line 259, witness line 262)
- ours: `ІІ`
- witness: `II`
- around: `Раздел [...] Включване в Програмата за защита`
### 9 (replace, our line 306, witness line 309)
- ours: `ПРЕХОДНИ И ЗАКЛЮЧИТЕЛНИ РАЗПОРЕДБИ`
- witness: `Преходни и Заключителни разпоредби`
### 10 (witness_line, our line 309, witness line 312)
- ours: ``
- witness: `Заключителни разпоредби`
- around: `§ 2. В тримесечен срок от влизането в сила на този правилник главният прокурор издава правилата по чл. 3, ал. 2. [...] `
### 11 (witness_line, our line 309, witness line 313)
- ours: ``
- witness: `КЪМ ПОСТАНОВЛЕНИЕ № 56 ОТ 31 МАРТ 2020 Г. ЗА ИЗМЕНЕНИЕ И ДОПЪЛНЕНИЕ НА ПРАВИЛНИКА ЗА ПРИЛАГАНЕ НА ЗАКОНА ЗА ЗАЩИТА НА ЛИЦА, ЗАСТРАШЕНИ ВЪВ ВРЪЗКА С НАКАЗАТЕЛНО ПРОИЗВОДСТВО, ПРИЕТ С ПОСТАНОВЛЕНИЕ № 242 НА МИНИСТЕРСКИЯ СЪВЕТ ОТ 2018 Г.`
- around: `§ 2. В тримесечен срок от влизането в сила на този правилник главният прокурор издава правилата по чл. 3, ал. 2. [...] `
### 12 (witness_line, our line 309, witness line 314)
- ours: ``
- witness: `(ОБН. - ДВ, БР. 31 ОТ 2020 Г., В СИЛА ОТ 01.04.2020 Г.)`
- around: `§ 2. В тримесечен срок от влизането в сила на този правилник главният прокурор издава правилата по чл. 3, ал. 2. [...] `
### 13 (witness_line, our line 309, witness line 315)
- ours: ``
- witness: `§ 3. Постановлението влиза в сила от деня на обнародването му в "Държавен вестник".`
- around: `§ 2. В тримесечен срок от влизането в сила на този правилник главният прокурор издава правилата по чл. 3, ал. 2. [...] `
### 14 (witness_line, our line 309, witness line 316)
- ours: ``
- witness: `Заключителни разпоредби`
- around: `§ 2. В тримесечен срок от влизането в сила на този правилник главният прокурор издава правилата по чл. 3, ал. 2. [...] `
### 15 (witness_line, our line 309, witness line 317)
- ours: ``
- witness: `КЪМ ПОСТАНОВЛЕНИЕ № 401 ОТ 25 НОЕМВРИ 2021 Г. ЗА ИЗМЕНЕНИЕ И ДОПЪЛНЕНИЕ НА ПРАВИЛНИКА ЗА ПРИЛАГАНЕ НА ЗАКОНА ЗА ЗАЩИТА НА ЛИЦА, ЗАСТРАШЕНИ ВЪВ ВРЪЗКА С НАКАЗАТЕЛНО ПРОИЗВОДСТВО, ПРИЕТ С ПОСТАНОВЛЕНИЕ № 242 НА МИНИСТЕРСКИЯ СЪВЕТ ОТ 2018 Г.`
- around: `§ 2. В тримесечен срок от влизането в сила на този правилник главният прокурор издава правилата по чл. 3, ал. 2. [...] `
### 16 (witness_line, our line 309, witness line 318)
- ours: ``
- witness: `(ОБН. - ДВ, БР. 100 ОТ 2021 Г., В СИЛА ОТ 30.11.2021 Г.)`
- around: `§ 2. В тримесечен срок от влизането в сила на този правилник главният прокурор издава правилата по чл. 3, ал. 2. [...] `
### 17 (witness_line, our line 309, witness line 319)
- ours: ``
- witness: `§ 46. Постановлението влиза в сила от деня на обнародването му в "Държавен вестник".`
- around: `§ 2. В тримесечен срок от влизането в сила на този правилник главният прокурор издава правилата по чл. 3, ал. 2. [...] `

## witness moj
(absent: the portal answers 500 for https://justice.government.bg/home/normdoc/2137188264 (absent, 2026-11-01T11:42:36+00:00); nothing to settle)
