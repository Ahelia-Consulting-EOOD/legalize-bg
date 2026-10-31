---
act: naredba-27-ot-13-mart-2014-g-za-statistikata-na-platezhniya-balans-mezhdunarodna
title: НАРЕДБА № 27 ОТ 13 МАРТ 2014 Г. ЗА СТАТИСТИКАТА НА ПЛАТЕЖНИЯ БАЛАНС, МЕЖДУНАРОДНАТА ИНВЕСТИЦИОННА ПОЗИЦИЯ И СТАТИСТИКАТА НА ЦЕННИТЕ КНИЖА
route: history
stopped_at: engine
exception: 'the next step is not defined: engine'
tried: []
run: s2-lexbg-defects-2026-10-31
record: data/runs/route-ledger/naredba-27-ot-13-mart-2014-g-za-statistikata-na-platezhniya-balans-mezhdunarodna.json
date: '2026-10-31'
---

## Lessons learnt

The detector of FR-042 flagged the act and the investigator confirmed it against the Gazette's promulgation material 83596 (S2 run s2-lexbg-defects-2026-10-31): lex.bg block 92 heading empty, then Преходни и Заключителни разпоредби and § 2; Gazette material 83596 carries § 1 т. 1-3 under ДОПЪЛНИТЕЛНА РАЗПОРЕДБА; the § 2 difference is an amendment lex.bg marks (ДВ, бр. 108 от 2024 г.); §§ 3-5 match The Gazette carries Допълнителна разпоредба with § 1 (definitions, т. 1-3); lex.bg's text, which the corpus holds, lacks it (kind: dropped_section).

## Proposal

The act was amended after its promulgation, so its promulgation material is not the whole act and the dropped text can be filled only by rebuilding the act's history through the engine of F1. Leave the act on the list with the route "history" until the engine exists; the corpus keeps lex.bg's text with the defect, and the act counts as distance left.

## The owner's ruling

(not yet given)
