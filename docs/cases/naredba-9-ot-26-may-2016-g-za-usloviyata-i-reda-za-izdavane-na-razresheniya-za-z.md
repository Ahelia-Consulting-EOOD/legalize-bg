---
act: naredba-9-ot-26-may-2016-g-za-usloviyata-i-reda-za-izdavane-na-razresheniya-za-z
title: НАРЕДБА № 9 ОТ 26 МАЙ 2016 Г. ЗА УСЛОВИЯТА И РЕДА ЗА ИЗДАВАНЕ НА РАЗРЕШЕНИЯ ЗА ЗАСАЖДАНЕ НА ЛОЗЯ
route: history
stopped_at: engine
exception: 'the next step is not defined: engine'
tried: []
run: s2-lexbg-defects-2026-10-31
record: data/runs/route-ledger/naredba-9-ot-26-may-2016-g-za-usloviyata-i-reda-za-izdavane-na-razresheniya-za-z.json
date: '2026-10-31'
---

## Lessons learnt

The detector of FR-042 flagged the act and the investigator confirmed it against the Gazette's promulgation material 104150 (S2 run s2-lexbg-defects-2026-10-31): lex.bg lines 45-47: heading 'Допълнителна разпоредба' followed directly by the transitional and final heading and § 2; Gazette lines 116-123: § 1 with items 1-5 between the two headings; §§ 2-10 match (lex.bg lines 47-107 vs Gazette lines 124-184); lex.bg §§ 11-12 are marked additions (ДВ бр. 101/2020) The Gazette carries Under the additional-provision heading the Gazette carries § 1 (definitions, items 1 to 5); lex.bg prints the heading with nothing under it and starts at § 2; lex.bg's text, which the corpus holds, lacks it (kind: dropped_section).

## Proposal

The act was amended after its promulgation, so its promulgation material is not the whole act and the dropped text can be filled only by rebuilding the act's history through the engine of F1. Leave the act on the list with the route "history" until the engine exists; the corpus keeps lex.bg's text with the defect, and the act counts as distance left.

## The owner's ruling

(not yet given)
