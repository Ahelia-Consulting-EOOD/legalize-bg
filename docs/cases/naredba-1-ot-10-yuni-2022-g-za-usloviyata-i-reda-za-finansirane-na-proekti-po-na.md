---
act: naredba-1-ot-10-yuni-2022-g-za-usloviyata-i-reda-za-finansirane-na-proekti-po-na
title: НАРЕДБА № 1 ОТ 10 ЮНИ 2022 Г. ЗА УСЛОВИЯТА И РЕДА ЗА ФИНАНСИРАНЕ НА ПРОЕКТИ ПО НАЦИОНАЛНИ ПРОГРАМИ ЗА МЛАДЕЖТА
route: history
stopped_at: engine
exception: 'the next step is not defined: engine'
tried: []
run: s2-lexbg-defects-2026-10-31
record: data/runs/route-ledger/naredba-1-ot-10-yuni-2022-g-za-usloviyata-i-reda-za-finansirane-na-proekti-po-na.json
date: '2026-10-31'
---

## Lessons learnt

The detector of FR-042 flagged the act and the investigator confirmed it against the Gazette's promulgation material 174253 (S2 run s2-lexbg-defects-2026-10-31): lex.bg block 166 heading Допълнителна разпоредба followed directly by Преходни и Заключителни разпоредби and § 2; Gazette blocks 156-162 carry § 1, т. 1-5; the wording difference in § 2 is an amendment lex.bg marks (ДВ, бр. 10 от 2026 г.), §§ 3-9 match The Gazette carries Допълнителна разпоредба with § 1 (definitions, т. 1-5); lex.bg's text, which the corpus holds, lacks it (kind: dropped_section).

## Proposal

The act was amended after its promulgation, so its promulgation material is not the whole act and the dropped text can be filled only by rebuilding the act's history through the engine of F1. Leave the act on the list with the route "history" until the engine exists; the corpus keeps lex.bg's text with the defect, and the act counts as distance left.

## The owner's ruling

(not yet given)
