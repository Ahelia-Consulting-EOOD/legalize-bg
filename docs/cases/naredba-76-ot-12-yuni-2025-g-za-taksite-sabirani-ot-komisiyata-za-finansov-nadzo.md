---
act: naredba-76-ot-12-yuni-2025-g-za-taksite-sabirani-ot-komisiyata-za-finansov-nadzo
title: НАРЕДБА № 76 ОТ 12 ЮНИ 2025 Г. ЗА ТАКСИТЕ, СЪБИРАНИ ОТ КОМИСИЯТА ЗА ФИНАНСОВ НАДЗОР
route: history
stopped_at: engine
exception: 'the next step is not defined: engine'
tried: []
run: s2-lexbg-defects-2026-10-31
record: data/runs/route-ledger/naredba-76-ot-12-yuni-2025-g-za-taksite-sabirani-ot-komisiyata-za-finansov-nadzo.json
date: '2026-10-31'
---

## Lessons learnt

The detector of FR-042 flagged the act and the investigator confirmed it against the Gazette's promulgation material 235512 (S2 run s2-lexbg-defects-2026-10-31): lex.bg line 650 prints 'Допълнителна разпоредба' followed directly by the transitional and final heading and § 2 (lines 651-652); the Gazette (material 235512) carries § 1 with points 1-3 under 'ДОПЪЛНИТЕЛНА РАЗПОРЕДБА' (lines 681-685); §§ 2-8 match (lines 652-674 vs 687-709). The Gazette carries: § 1 (definitions, items 1-3) under the additional-provision heading. lex.bg's text, which the corpus holds, lacks it (kind: dropped_section).

## Proposal

The act was amended after its promulgation, so its promulgation material is not the whole act and the dropped text can be filled only by rebuilding the act's history through the engine of F1. Leave the act on the list with the route "history" until the engine exists; the corpus keeps lex.bg's text with the defect, and the act counts as distance left.

## The owner's ruling

(not yet given)
