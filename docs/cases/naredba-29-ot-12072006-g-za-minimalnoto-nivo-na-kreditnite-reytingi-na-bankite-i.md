---
act: naredba-29-ot-12072006-g-za-minimalnoto-nivo-na-kreditnite-reytingi-na-bankite-i
title: НАРЕДБА № 29 ОТ 12.07.2006 Г. ЗА ИЗИСКВАНИЯТА КЪМ ИНВЕСТИЦИИТЕ НА ФОНДОВЕТЕ ЗА ДОПЪЛНИТЕЛНО ПЕНСИОННО ОСИГУРЯВАНЕ, ПОДФОНДОВЕТЕ В ТЯХ И НА ФОНДОВЕТЕ ЗА ИЗВЪРШВАНЕ НА ПЛАЩАНИЯ ПО ЧЛ. 176, АЛ. 4 ОТ КОДЕКСА ЗА СОЦИАЛНО ОСИГУРЯВАНЕ (ЗАГЛ. ИЗМ. - ДВ, БР. 94 ОТ 2018 Г., В СИЛА ОТ 19.11.2018 Г., ИЗМ. - ДВ, БР. 64 ОТ 2022 Г., В СИЛА ОТ 09.08.2022 Г., ИЗМ. - ДВ, БР. 61 ОТ 2026 Г., В СИЛА ОТ 01.01.2027 Г.)
route: history
stopped_at: engine
exception: 'the next step is not defined: engine'
tried: []
run: s2-lexbg-defects-2026-10-31
record: data/runs/route-ledger/naredba-29-ot-12072006-g-za-minimalnoto-nivo-na-kreditnite-reytingi-na-bankite-i.json
date: '2026-10-31'
---

## Lessons learnt

The detector of FR-042 flagged the act and the investigator confirmed it against the Gazette's amending material 244328 (the promulgation material is 2308) (S2 run s2-lexbg-defects-2026-10-31): lex.bg lines 45-47: the additional-provision heading and its marker Нова - ДВ, бр. 61 от 2026 are followed directly by the final-provisions heading, with no § 1; Gazette line 323-324: § 10 creates that subdivision with new § 1 and gives its text; Gazette line 325: § 11 renumbers old § 1 as § 3, matching lex.bg line 49, so § 1 is the only provision missing. The Gazette carries: Additional provision section with new § 1 (definition of leverage by reference to § 1, item 29 of the additional provisions of the collective investment schemes act), created by § 10 of the amending ordinance in ДВ бр. 61 от 2026. lex.bg's text, which the corpus holds, lacks it (kind: dropped_section). The section enters into force on 2027-01-01; the starting state carries it as the Gazette's consolidated text does, since the Gazette prevails (D-059, D-074): no text is dropped for not yet applying.

## Proposal

The act was amended after its promulgation, so its promulgation material is not the whole act and the dropped text can be filled only by rebuilding the act's history through the engine of F1. Leave the act on the list with the route "history" until the engine exists; the corpus keeps lex.bg's text with the defect, and the act counts as distance left.

## The owner's ruling

(not yet given)
