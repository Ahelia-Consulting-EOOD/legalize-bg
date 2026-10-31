---
act: naredba-10-ot-27-yuni-2023-g-za-usloviyata-i-reda-za-prilagane-na-interventsiite
title: НАРЕДБА № 10 ОТ 27 ЮНИ 2023 Г. ЗА УСЛОВИЯТА И РЕДА ЗА ПРИЛАГАНЕ НА ИНТЕРВЕНЦИИТЕ В ОБЛАСТТА НА ОКОЛНАТА СРЕДА И КЛИМАТА И ХУМАННО ОТНОШЕНИЕ КЪМ ЖИВОТНИТЕ, ВКЛЮЧЕНИ В СТРАТЕГИЧЕСКИЯ ПЛАН ЗА РАЗВИТИЕТО НА ЗЕМЕДЕЛИЕТО И СЕЛСКИТЕ РАЙОНИ ЗА ПЕРИОДА 2023-2027 Г.
route: history
stopped_at: engine
exception: 'the next step is not defined: engine'
tried: []
run: s2-lexbg-defects-2026-10-31
record: data/runs/route-ledger/naredba-10-ot-27-yuni-2023-g-za-usloviyata-i-reda-za-prilagane-na-interventsiite.json
date: '2026-10-31'
---

## Lessons learnt

The detector of FR-042 flagged the act and the investigator confirmed it against the Gazette's promulgation material 196800 (S2 run s2-lexbg-defects-2026-10-31): lex.bg block 855 heading Допълнителна разпоредба followed directly by Преходни и Заключителни разпоредби and § 2; Gazette blocks 765-769 carry ДОПЪЛНИТЕЛНА РАЗПОРЕДБА with § 1, т. 1-3; §§ 2-6 match The Gazette carries Допълнителна разпоредба with § 1 (definitions, т. 1-3); lex.bg's text, which the corpus holds, lacks it (kind: dropped_section).

## Proposal

The act was amended after its promulgation, so its promulgation material is not the whole act and the dropped text can be filled only by rebuilding the act's history through the engine of F1. Leave the act on the list with the route "history" until the engine exists; the corpus keeps lex.bg's text with the defect, and the act counts as distance left.

## The owner's ruling

(not yet given)
