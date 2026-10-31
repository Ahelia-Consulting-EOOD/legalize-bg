---
act: naredba-8121z-1006-ot-24-avgust-2015-g-za-reda-za-osashtestvyavane-na-pozharogas
title: НАРЕДБА № 8121з-1006 ОТ 24 АВГУСТ 2015 Г. ЗА РЕДА ЗА ОСЪЩЕСТВЯВАНЕ НА ПОЖАРОГАСИТЕЛНАТА И СПАСИТЕЛНАТА ДЕЙНОСТ ОТ ОРГАНИТЕ ЗА ПОЖАРНА БЕЗОПАСНОСТ И ЗАЩИТА НА НАСЕЛЕНИЕТО НА МИНИСТЕРСТВОТО НА ВЪТРЕШНИТЕ РАБОТИ
route: history
stopped_at: engine
exception: 'the next step is not defined: engine'
tried: []
run: s2-lexbg-defects-2026-10-31
record: data/runs/route-ledger/naredba-8121z-1006-ot-24-avgust-2015-g-za-reda-za-osashtestvyavane-na-pozharogas.json
date: '2026-10-31'
---

## Lessons learnt

The detector of FR-042 flagged the act and the investigator confirmed it against the Gazette's promulgation material 97020 (S2 run s2-lexbg-defects-2026-10-31): lex.bg block 272 heading Допълнителна разпоредба followed directly by Заключителни разпоредби and § 2; Gazette blocks 266-276 carry § 1, т. 1-9 under that heading; §§ 2-5 match. The Gazette carries: Допълнителна разпоредба with § 1 (definitions, т. 1-9). lex.bg's text, which the corpus holds, lacks it (kind: dropped_section).

## Proposal

The act was amended after its promulgation, so its promulgation material is not the whole act and the dropped text can be filled only by rebuilding the act's history through the engine of F1. Leave the act on the list with the route "history" until the engine exists; the corpus keeps lex.bg's text with the defect, and the act counts as distance left.

## The owner's ruling

(not yet given)
