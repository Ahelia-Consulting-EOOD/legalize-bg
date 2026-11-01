---
act: zakon-za-obshtite-iziskvaniya-za-bezopasnost-pri-predostavyane-na-atraktsionni-u
title: ЗАКОН ЗА ОБЩИТЕ ИЗИСКВАНИЯ ЗА БЕЗОПАСНОСТ ПРИ ПРЕДОСТАВЯНЕ НА АТРАКЦИОННИ УСЛУГИ, ПРЕДСТАВЛЯВАЩИ ИЗТОЧНИК НА ПОВИШЕНА ОПАСНОСТ
route: history
stopped_at: engine
exception: 'the next step is not defined: engine'
tried: []
run: s2-lexbg-defects-2026-10-31
record: data/runs/route-ledger/zakon-za-obshtite-iziskvaniya-za-bezopasnost-pri-predostavyane-na-atraktsionni-u.json
date: '2026-10-31'
---

## Lessons learnt

The detector of FR-042 flagged the act and the investigator confirmed it against the Gazette's promulgation material 241045 (S2 run s2-lexbg-defects-2026-10-31): lex.bg lines 341-343: heading 'Допълнителна разпоредба' followed directly by 'Преходни и Заключителни разпоредби' and § 2; Gazette lines 447-458: the same heading, then § 1 with т. 1-8, then the transitional heading and § 2; §§ 2-10 match. The Gazette carries: Допълнителна разпоредба with § 1 (definitions, т. 1-8), which lex.bg omits under its empty heading. lex.bg's text, which the corpus holds, lacks it (kind: dropped_section).

## Proposal

The act was amended after its promulgation, so its promulgation material is not the whole act and the dropped text can be filled only by rebuilding the act's history through the engine of F1. Leave the act on the list with the route "history" until the engine exists; the corpus keeps lex.bg's text with the defect, and the act counts as distance left.

## The owner's ruling

(not yet given)
