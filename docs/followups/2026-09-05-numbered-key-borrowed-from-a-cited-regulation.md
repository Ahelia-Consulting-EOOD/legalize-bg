# `numbered_key` reads a cited regulation's number as the act's own

**Date:** 2026-09-05
**Status:** open, a contained defect class in the ДВ resolver, to fix in a `numbered_key` hardening round
**Raised by:** fix round 2 of PR #35 (`feat/dv-coverage-map`), while classifying the silent attributions of the content-word mutation test

## The finding

`fetcher/dv/resolver.py::numbered_key` takes the first „№" in the target title as the act's own number and the year that follows it as the act's own year. For 3 of the 1,987 corpus acts that yield a key, the „№" belongs to an instrument the title cites, not to the act:

| act | key read | subject clause left |
| --- | --- | --- |
| Наредба за реда и начина за ограничаване на производството ... от приложение XVII на Регламент (ЕО) № 1907/2006 (REACH) | (наредба, 1907, 2006) | „2006 reach" |
| Наредба за установяване на мерки по прилагане на Регламент (ЕО) № 1005/2009 относно вещества, които нарушават озоновия слой | (наредба, 1005, 2009) | „вещества които нарушават озоновия слой" |
| Правилник за дейността на щабовете за подобряване на работата в железопътния, водния и автомобилния транспорт ... № 31 | (правилник, 31, None) | the text after that number |

These are unnumbered acts. A key they never had makes them reachable by the numbered route, and reduces the subject clause compared there to residue.

## Exposure, measured

A Gazette title of a different act citing the same regulation number would reach the single-candidate numbered branch of these keys. That branch is bounded since PR #35 fix round 2: the 0.90 floor, the digit guard applied outright, and the `content_mismatch` flag on any content-word difference. Whole-corpus leave-one-out and the year-only variant over 1,932 dated numbered acts are both 0 wrong with the borrowed keys in place, and the corpus supplies no natural instance. The class is contained, not absent: it is 3 acts today and grows with every implementing наредба whose title names an EU regulation before its own subject.

## The action

Restrict the number `numbered_key` reads to the one that directly follows the act-type noun (after `_TITLE_NOTE_RE` has removed a title note), so „НАРЕДБА № 5 ОТ ..." keeps its key and „НАРЕДБА ЗА ... РЕГЛАМЕНТ (ЕО) № 1907/2006" yields none. One test per shape above, red first. Then re-measure and correct every count the resolver tests and docstrings quote that the key feeds: dated numbered acts (1,932), (type, number) keys naming one act (176), numbered наредби stating no year (365).

## Why it is deferred from PR #35

The fix round was scoped to the re-review's I3 and I4 and the class was found while measuring their fix. Changing the key moves the whole-corpus counts the branch's tests assert, which is its own review cycle; the bounds above hold the exposure at zero meanwhile.
