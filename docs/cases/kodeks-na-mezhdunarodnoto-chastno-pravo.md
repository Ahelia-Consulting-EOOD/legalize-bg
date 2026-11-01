---
act: kodeks-na-mezhdunarodnoto-chastno-pravo
title: Кодекс на международното частно право
route: history
stopped_at: apply
exception: 'material 246208 (бр. 92/2026): the answer is refused: §9.2.б renumber: ''чл. 121, ал. 2 и 3'' names 0 place(s) in the act'
tried:
- run: f1-engine-2026-11-01
  step: chain
  outcome: done
  detail: 6 material(s) change the act after бр. 42/2005; lex.bg names 6 issue(s), 0 unexplained (none), 0 the Gazette adds (none); 0 court decision(s) name the act
  evidence:
  - data/runs/f1-engine-2026-11-01/kodeks-na-mezhdunarodnoto-chastno-pravo/chain.json
- run: f1-engine-2026-11-01
  step: fetch_material
  outcome: done
  detail: material 292 of бр. 42/2005 (cached), sha256 7aaa96adc976
  evidence:
  - data/runs/f1-engine-2026-11-01/kodeks-na-mezhdunarodnoto-chastno-pravo/material.json
- run: f1-engine-2026-11-01
  step: prepare
  outcome: done
  detail: 574 blocks, 20 sections
  evidence:
  - data/runs/f1-engine-2026-11-01/kodeks-na-mezhdunarodnoto-chastno-pravo/blocks.json
- run: f1-engine-2026-11-01
  step: label
  outcome: done
  detail: 'round 0 collected: 0 exception(s), 0 source finding(s)'
  evidence:
  - data/runs/f1-engine-2026-11-01/kodeks-na-mezhdunarodnoto-chastno-pravo/report-round0.json
- run: f1-engine-2026-11-01
  step: ladder
  outcome: done
  detail: no residue after round 0
  evidence:
  - data/runs/f1-engine-2026-11-01/kodeks-na-mezhdunarodnoto-chastno-pravo/ladder.json
  - data/runs/f1-engine-2026-11-01/kodeks-na-mezhdunarodnoto-chastno-pravo/report-round0.json
- run: f1-engine-2026-11-01
  step: content_check
  outcome: done
  detail: no lost text, no exception; source findings none
  evidence:
  - data/runs/f1-engine-2026-11-01/kodeks-na-mezhdunarodnoto-chastno-pravo/content-check.json
- run: f1-engine-2026-11-01
  step: apply
  outcome: stop
  detail: 'material 3951 (бр. 59/2007): the answer is refused: §7.3 outside_set: outside the closed set of operations: The instruction replaces the whole reference (чл. 80, ал. 1, буква plus the quoted letter г and its closing quote mark) with q2, but the Gazette''s nested quotation marks cut segment q1 short before the letter г, so replacing q1 with q2 would leave the letter г and its closing quote mark in the text. No quoted segment covers the full old words; the old string must be the reference including the letter г and its quote marks.'
  evidence:
  - data/runs/f1-engine-2026-11-01/kodeks-na-mezhdunarodnoto-chastno-pravo/apply/01-3951/answer.json
- run: f1-engine-2026-11-01
  step: apply
  outcome: interrupted
  detail: ''
  evidence: []
- run: f1-engine-2026-11-01
  step: label
  outcome: done
  detail: 'round 0 collected: 0 exception(s), 0 source finding(s)'
  evidence:
  - data/runs/f1-engine-2026-11-01/kodeks-na-mezhdunarodnoto-chastno-pravo/report-round0.json
- run: f1-engine-2026-11-01
  step: ladder
  outcome: done
  detail: no residue after round 0
  evidence:
  - data/runs/f1-engine-2026-11-01/kodeks-na-mezhdunarodnoto-chastno-pravo/ladder.json
  - data/runs/f1-engine-2026-11-01/kodeks-na-mezhdunarodnoto-chastno-pravo/report-round0.json
- run: f1-engine-2026-11-01
  step: apply
  outcome: interrupted
  detail: ''
  evidence: []
- run: f1-engine-2026-11-01
  step: apply
  outcome: stop
  detail: 'material 246208 (бр. 92/2026): the answer is refused: §9.2.б renumber: ''чл. 121, ал. 2 и 3'' names 0 place(s) in the act'
  evidence:
  - data/runs/f1-engine-2026-11-01/kodeks-na-mezhdunarodnoto-chastno-pravo/apply/06-246208/answer.json
run: f1-engine-2026-11-01
record: data/runs/route-ledger/kodeks-na-mezhdunarodnoto-chastno-pravo.json
date: '2026-11-01'
superseded: the act went on in run f1-engine-2026-11-01
resolved: 3ff8323b6
---

## Lessons learnt

(not yet written)

## Proposal

(not yet written)

## The owner's ruling

(not yet given)
