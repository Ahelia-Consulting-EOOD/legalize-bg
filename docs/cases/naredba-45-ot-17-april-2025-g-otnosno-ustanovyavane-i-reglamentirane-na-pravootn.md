---
act: naredba-45-ot-17-april-2025-g-otnosno-ustanovyavane-i-reglamentirane-na-pravootn
title: НАРЕДБА № 45 ОТ 17 АПРИЛ 2025 Г. ОТНОСНО УСТАНОВЯВАНЕ И РЕГЛАМЕНТИРАНЕ НА ПРАВООТНОШЕНИЯТА НА БЪЛГАРСКАТА НАРОДНА БАНКА С КОНТРАГЕНТИ ПО ПАРИЧНА ПОЛИТИКА
route: history
stopped_at: engine
exception: 'the next step is not defined: engine'
tried: []
run: s2-lexbg-defects-2026-10-31
record: data/runs/route-ledger/naredba-45-ot-17-april-2025-g-otnosno-ustanovyavane-i-reglamentirane-na-pravootn.json
date: '2026-10-31'
---

## Lessons learnt

The detector of FR-042 flagged the act and the investigator confirmed it against the Gazette's promulgation material 234460 (S2 run s2-lexbg-defects-2026-10-31): lex.bg lines 410-412: additional-provision heading followed directly by the transitional and final heading and § 2; Gazette lines 426-472 carry § 1 with items 1-32; §§ 2-4 match (lines 412-419 vs 473-480), and lex.bg's entry-into-force mark on § 3 is not an error The Gazette carries Additional provision § 1 (definitions, items 1-32) under ДОПЪЛНИТЕЛНА РАЗПОРЕДБА; lex.bg's text, which the corpus holds, lacks it (kind: dropped_section).

## Proposal

The act was amended after its promulgation, so its promulgation material is not the whole act and the dropped text can be filled only by rebuilding the act's history through the engine of F1. Leave the act on the list with the route "history" until the engine exists; the corpus keeps lex.bg's text with the defect, and the act counts as distance left.

## The owner's ruling

(not yet given)
