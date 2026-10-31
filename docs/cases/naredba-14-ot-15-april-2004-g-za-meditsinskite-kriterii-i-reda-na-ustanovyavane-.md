---
act: naredba-14-ot-15-april-2004-g-za-meditsinskite-kriterii-i-reda-na-ustanovyavane-
title: НАРЕДБА № 14 ОТ 15 АПРИЛ 2004 Г. ЗА МЕДИЦИНСКИТЕ КРИТЕРИИ И РЕДА НА УСТАНОВЯВАНЕ НА СМЪРТ
route: history
stopped_at: engine
exception: 'the next step is not defined: engine'
tried: []
run: s2-lexbg-defects-2026-10-31
record: data/runs/route-ledger/naredba-14-ot-15-april-2004-g-za-meditsinskite-kriterii-i-reda-na-ustanovyavane-.json
date: '2026-10-31'
---

## Lessons learnt

The detector of FR-042 flagged the act and the investigator confirmed it against the Gazette's promulgation material 21032 (S2 run s2-lexbg-defects-2026-10-31): Gazette material 21032 prints the act's own transitional and final provisions § 1 and § 2 after чл. 17 (blocks at file lines 310-312); lex.bg goes from чл. 18 straight to the provisions of the 2013 amending ordinance (§ 4, § 6) and the 2019 amending ordinance (§ 34) (file lines 115-125), with no § 1 or § 2 and no repeal marking, so the act's own section is omitted. The Gazette carries: the act's own Преходни и заключителни разпоредби with § 1 (commissions appointed within three months) and § 2 (legal basis, repeal of Наредба № 4 от 1999 г.). lex.bg's text, which the corpus holds, lacks it (kind: dropped_section).

## Proposal

The act was amended after its promulgation, so its promulgation material is not the whole act and the dropped text can be filled only by rebuilding the act's history through the engine of F1. Leave the act on the list with the route "history" until the engine exists; the corpus keeps lex.bg's text with the defect, and the act counts as distance left.

## The owner's ruling

(not yet given)
