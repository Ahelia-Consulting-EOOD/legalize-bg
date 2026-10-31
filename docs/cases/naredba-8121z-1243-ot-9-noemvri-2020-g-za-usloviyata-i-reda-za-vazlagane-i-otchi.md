---
act: naredba-8121z-1243-ot-9-noemvri-2020-g-za-usloviyata-i-reda-za-vazlagane-i-otchi
title: НАРЕДБА № 8121з-1243 ОТ 9 НОЕМВРИ 2020 Г. ЗА УСЛОВИЯТА И РЕДА ЗА ВЪЗЛАГАНЕ И ОТЧИТАНЕ НА ИЗПЪЛНЕНИЕТО И/ИЛИ УПРАВЛЕНИЕТО НА ПРОЕКТИ ИЛИ ПРОГРАМИ И ЗА ФОРМИРАНЕ И ИЗПЛАЩАНЕ НА ДОПЪЛНИТЕЛНОТО ВЪЗНАГРАЖДЕНИЕ ПО ЧЛ. 178, АЛ. 1, Т. 6 ОТ ЗАКОНА ЗА МИНИСТЕРСТВОТО НА ВЪТРЕШНИТЕ РАБОТИ
route: history
stopped_at: engine
exception: 'the next step is not defined: engine'
tried: []
run: s2-lexbg-defects-2026-10-31
record: data/runs/route-ledger/naredba-8121z-1243-ot-9-noemvri-2020-g-za-usloviyata-i-reda-za-vazlagane-i-otchi.json
date: '2026-10-31'
---

## Lessons learnt

The detector of FR-042 flagged the act and the investigator confirmed it against the Gazette's promulgation material 153560 (S2 run s2-lexbg-defects-2026-10-31): lex.bg block 57 heading Допълнителна разпоредба followed directly by Преходни и Заключителни разпоредби and § 2; Gazette material 153560 carries § 1 under the heading, then §§ 2-4 matching lex.bg. The Gazette carries: Допълнителна разпоредба with § 1 (Дирекция Планиране и управление на бюджета sets the order of planning and reporting). lex.bg's text, which the corpus holds, lacks it (kind: dropped_section).

## Proposal

The act was amended after its promulgation, so its promulgation material is not the whole act and the dropped text can be filled only by rebuilding the act's history through the engine of F1. Leave the act on the list with the route "history" until the engine exists; the corpus keeps lex.bg's text with the defect, and the act counts as distance left.

## The owner's ruling

(not yet given)
