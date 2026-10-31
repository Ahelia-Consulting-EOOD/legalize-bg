---
act: naredba-za-kachestvoto-na-sotsialnite-uslugi
title: НАРЕДБА ЗА КАЧЕСТВОТО НА СОЦИАЛНИТЕ УСЛУГИ
route: history
stopped_at: engine
exception: 'the next step is not defined: engine'
tried: []
run: s2-lexbg-defects-2026-10-31
record: data/runs/route-ledger/naredba-za-kachestvoto-na-sotsialnite-uslugi.json
date: '2026-10-31'
---

## Lessons learnt

The detector of FR-042 flagged the act and the investigator confirmed it against the Gazette's amending material 245068 (the promulgation material is 174310) (S2 run s2-lexbg-defects-2026-10-31): lex.bg lines 45-47: heading Допълнителна разпоредба marked Нова - ДВ, бр. 70 от 2026 г., в сила от 01.01.2028 г., followed directly by the Преходни и Заключителни разпоредби heading and § 1а, with no text under it; amending material lines 297-309: § 14 creates the subdivision after чл. 57 with § 1 and its full text; line 311 renumbers the old § 1 as § 1а, matching lex.bg line 48, so the lowest § 2 flag comes from the missing new § 1. The Gazette carries: Допълнителна разпоредба, new § 1 (definitions, items 1 a-g and 2 a-g), created by § 14 of ПМС № 94 of 27.07.2026 (ДВ, бр. 70 от 2026). lex.bg's text, which the corpus holds, lacks it (kind: dropped_section).

## Proposal

The act was amended after its promulgation, so its promulgation material is not the whole act and the dropped text can be filled only by rebuilding the act's history through the engine of F1. Leave the act on the list with the route "history" until the engine exists; the corpus keeps lex.bg's text with the defect, and the act counts as distance left.

## The owner's ruling

(not yet given)
