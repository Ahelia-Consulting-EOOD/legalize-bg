---
act: naredba-8-ot-26-noemvri-2007-g-za-usloviyata-i-reda-za-finansirane-na-diagnostik
title: НАРЕДБА № 8 ОТ 26 НОЕМВРИ 2007 Г. ЗА УСЛОВИЯТА И РЕДА ЗА ФИНАНСИРАНЕ НА ДИАГНОСТИКАТА НА ПРОФЕСИОНАЛНИТЕ БОЛЕСТИ ОТ ФОНД "УСЛОВИЯ НА ТРУД"
route: history
stopped_at: engine
exception: 'the next step is not defined: engine'
tried: []
run: s2-lexbg-defects-2026-10-31
record: data/runs/route-ledger/naredba-8-ot-26-noemvri-2007-g-za-usloviyata-i-reda-za-finansirane-na-diagnostik.json
date: '2026-10-31'
---

## Lessons learnt

The detector of FR-042 flagged the act and the investigator confirmed it against the Gazette's promulgation material 4513 (S2 run s2-lexbg-defects-2026-10-31): lex.bg block 109 Допълнителна разпоредба followed directly by block 110 Заключителна разпоредба; Gazette material 4513 carries § 1, т. 1-2 between them; ал. 4 difference is marked amendment ДВ бр. 38/2018. The Gazette carries: § 1 with items 1 and 2 under Допълнителна разпоредба (definition of диагностика на професионалните болести). lex.bg's text, which the corpus holds, lacks it (kind: dropped_section).

## Proposal

The act was amended after its promulgation, so its promulgation material is not the whole act and the dropped text can be filled only by rebuilding the act's history through the engine of F1. Leave the act on the list with the route "history" until the engine exists; the corpus keeps lex.bg's text with the defect, and the act counts as distance left.

## The owner's ruling

(not yet given)
