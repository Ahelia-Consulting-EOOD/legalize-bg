---
act: zakon-za-smetnata-palata
title: ЗАКОН ЗА СМЕТНАТА ПАЛАТА
route: history
stopped_at: engine
exception: 'the next step is not defined: engine'
tried: []
run: s2-lexbg-defects-2026-10-31
record: data/runs/route-ledger/zakon-za-smetnata-palata.json
date: '2026-10-31'
---

## Lessons learnt

The detector of FR-042 flagged the act and the investigator confirmed it against the Gazette's promulgation material 91797 (S2 run s2-lexbg-defects-2026-10-31): lex.bg lines 138-144: the additional-provision heading printed three times with title-amendment notes (ДВ бр. 16 and 51 от 2026 г.), then the transitional heading and § 2, with no § 1 and no repeal mark; Gazette lines 172-192 carry § 1 with items 1-13; §§ 2-13 match (lines 144-163 vs 193-212). The Gazette carries: Additional provision § 1 (definitions, items 1-13) under ДОПЪЛНИТЕЛНА РАЗПОРЕДБА. lex.bg's text, which the corpus holds, lacks it (kind: dropped_section).

## Proposal

The act was amended after its promulgation, so its promulgation material is not the whole act and the dropped text can be filled only by rebuilding the act's history through the engine of F1. Leave the act on the list with the route "history" until the engine exists; the corpus keeps lex.bg's text with the defect, and the act counts as distance left.

## The owner's ruling

(not yet given)
