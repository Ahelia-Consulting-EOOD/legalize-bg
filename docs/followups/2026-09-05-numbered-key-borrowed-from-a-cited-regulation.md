# `numbered_key` reads a cited regulation's number as the act's own

**Date:** 2026-09-05
**Status:** open, a contained defect class in the ДВ resolver, to fix in a `numbered_key` hardening round
**Raised by:** fix round 2 of PR #35 (`feat/dv-coverage-map`), while classifying the silent attributions of the content-word mutation test; the count corrected from 3 to 7 in fix round 3, after the re-review swept the corpus with the rule this document proposes

## The finding

`fetcher/dv/resolver.py::numbered_key` takes the first „№“ in the target title as the act's own number and the year that follows it as the act's own year. For 7 of the 1,987 corpus acts that yield a key, that „№“ belongs to an instrument the title cites, not to the act.

The sweep applies the rule proposed below: take the target as `numbered_key` does, `strip_amending_prefix(_TITLE_NOTE_RE.sub("", title))`, and call the key borrowed when any word other than the act-type noun that `act_type_of` reads sits between the start of the target and the first „№“.

| law_id | key read | source of the borrowed number |
| --- | --- | --- |
| `naredba-za-reda-i-nachina-za-ogranichavane-na-proizvodstvoto-upotrebata-ili-pusk` | (наредба, 1907, 2006) | „Регламент (ЕО) № 1907/2006“ (REACH), whose приложение XVII the наредба restricts |
| `naredba-za-ustanovyavane-na-merki-po-prilagane-na-reglament-eo-10052009-otnosno-` | (наредба, 1005, 2009) | „Регламент (ЕО) № 1005/2009“, the regulation the наредба implements |
| `pravilnik-za-deynostta-na-shtabovete-za-podobryavane-na-rabotata-v-zhelezopatniy` | (правилник, 31, None) | „Решение № 31 на Министерския съвет“, the act that created the bodies |
| `zakon-za-vazstanovyavane-sobstvenostta-varhu-konfiskuvanite-s-ukaz-88-na-prezidi` | (закон, 88, None) | „Указ № 88 на Президиума на НС“, whose confiscations the закон reverses |
| `naredba-za-publichniya-registar-na-operatorite-koito-izvarshvat-deynostite-po-pr` | (наредба, 1, None) | „Приложение № 1 към чл. 3, т. 1“ of the закон the наредба implements |
| `pravilnik-za-prilagane-na-ukaz-2242-za-svobodni-zoni-zagl-izm-dv-br-15-ot-1998-g` | (правилник, 2242, None) | „Указ № 2242 за свободни зони“, the decree the правилник applies |
| `pravilnik-za-prilagane-na-ukaz-904-za-borba-s-drebnoto-huliganstvo` | (правилник, 904, None) | „Указ № 904 за борба с дребното хулиганство“, the decree the правилник applies |

These are unnumbered acts. A key they never had makes them reachable by the numbered route, and reduces the subject clause compared there to residue: „2006 reach“ for the first row, „вещества които нарушават озоновия слой“ for the second, „на министерския съвет от 20 февруари 1979 г“ for the third.

Four of the seven were missed when this document was first written, and three of those four are the single most frequent shape of all, „ПРАВИЛНИК ЗА ПРИЛАГАНЕ НА УКАЗ № N“ and its закон analogue: the number of the instrument the act applies, read as the act's own.

## The приложение row is the worst of the seven

`naredba-za-publichniya-registar-na-operatorite-koito-izvarshvat-deynostite-po-pr` is the one to watch. Its number comes from „Приложение № 1“ and no year follows it, so the key is (наредба, 1, None) and `_numbered` keeps the act a candidate for a citation „Наредба № 1 от YYYY г.“ of ANY year; (наредба, 1) is the most crowded number in the corpus, 140 acts, so the borrowed key lands in the largest collision family there is. Its `numbered_date` is borrowed too: the text between the number and the subject clause is „към чл 3 т 1 от закона“, and that string is what `_agrees` is offered as a stated full date. Nothing exploits either today, and both leave-one-out variants, whole-corpus and the year-only one over the 1,932 dated numbered acts, stay 0 wrong with the borrowed keys in place.

## Exposure, measured

A Gazette title of a different act citing the same regulation number would reach the single-candidate numbered branch of these keys. That branch is bounded since PR #35 fix round 2: the 0.90 floor, the digit guard applied outright, and the `content_mismatch` flag on any content-word difference. Whole-corpus leave-one-out and the year-only variant over 1,932 dated numbered acts are both 0 wrong with the borrowed keys in place, and the corpus supplies no natural instance. The class is contained, not absent: it is 7 acts today and grows with every implementing наредба whose title names an EU regulation before its own subject.

## The action

Restrict the number `numbered_key` reads to the one that directly follows the act-type noun (after `_TITLE_NOTE_RE` has removed a title note), so „НАРЕДБА № 5 ОТ ...“ keeps its key and „НАРЕДБА ЗА ... РЕГЛАМЕНТ (ЕО) № 1907/2006“ yields none. One test per source shape in the table above, Регламент, Решение, Указ and Приложение, red first. Then re-measure and correct every count the resolver tests and docstrings quote that the key feeds: dated numbered acts (1,932), (type, number) keys naming one act (176), numbered наредби stating no year (365).

## Why it is deferred from PR #35

The fix round was scoped to the re-review's I3 and I4 and the class was found while measuring their fix. Changing the key moves the whole-corpus counts the branch's tests assert, which is its own review cycle; the bounds above hold the exposure at zero meanwhile.
