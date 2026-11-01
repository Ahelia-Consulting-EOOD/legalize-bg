---
act: naredba-za-usloviyata-i-reda-za-izplashtane-na-kompensatsionni-sumi-na-darzhavni-2
title: НАРЕДБА ЗА УСЛОВИЯТА И РЕДА ЗА ИЗПЛАЩАНЕ НА КОМПЕНСАЦИОННИ СУМИ НА ДЪРЖАВНИТЕ СЛУЖИТЕЛИ ОТ МИНИСТЕРСТВОТО НА ВЪТРЕШНИТЕ РАБОТИ, КОИТО ПОЛЗВАТ ЖИЛИЩЕ ПРИ УСЛОВИЯТА НА СВОБОДНО ДОГОВАРЯНЕ
route: history
stopped_at: engine
exception: 'the next step is not defined: engine'
tried: []
run: s2-lexbg-defects-2026-10-31
record: data/runs/route-ledger/naredba-za-usloviyata-i-reda-za-izplashtane-na-kompensatsionni-sumi-na-darzhavni-2.json
date: '2026-10-31'
---

## Lessons learnt

The detector of FR-042 flagged the act and the investigator confirmed it against the Gazette's promulgation material 87949 (S2 run s2-lexbg-defects-2026-10-31): lex.bg block 36 heading Допълнителна разпоредба followed directly by block 37 Заключителна разпоредба; Gazette material 87949 carries § 1 between the same two headings. The Gazette carries: § 1 under Допълнителна разпоредба (definition of семейство). lex.bg's text, which the corpus holds, lacks it (kind: dropped_section).

## Proposal

The act was amended after its promulgation, so its promulgation material is not the whole act and the dropped text can be filled only by rebuilding the act's history through the engine of F1. Leave the act on the list with the route "history" until the engine exists; the corpus keeps lex.bg's text with the defect, and the act counts as distance left.

## The owner's ruling

(not yet given)
