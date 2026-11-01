---
act: naredba-8121z-310-ot-17-yuli-2014-g-za-prenaznachavane-na-darzhavnite-sluzhiteli
title: Наредба № 8121з-310 от 17 юли 2014 г. за преназначаване на държавните служители в Министерството на вътрешните работи
route: history
stopped_at: apply
exception: 'material 148171 (бр. 47/2020): the answer is refused: §2.1.б outside_set: outside the closed set of operations: After the words q1 (ал. 3) in т. 6 a comma is placed and then q2 (т. 2) is added, so the text reads ''по чл. 164, ал. 3, т. 2 ЗМВР''; insert_words cannot carry the comma, which is not a quoted segment and does not stand as a character on the instruction line.'
tried:
- run: f1-engine-2026-11-01
  step: chain
  outcome: done
  detail: 7 material(s) change the act after бр. 60/2014; lex.bg names 7 issue(s), 0 unexplained (none), 0 the Gazette adds (none); 0 court decision(s) name the act
  evidence:
  - data/runs/f1-engine-2026-11-01/naredba-8121z-310-ot-17-yuli-2014-g-za-prenaznachavane-na-darzhavnite-sluzhiteli/chain.json
- run: f1-engine-2026-11-01
  step: fetch_material
  outcome: done
  detail: material 86641 of бр. 60/2014 (cached), sha256 ec1e83a6af5b
  evidence:
  - data/runs/f1-engine-2026-11-01/naredba-8121z-310-ot-17-yuli-2014-g-za-prenaznachavane-na-darzhavnite-sluzhiteli/material.json
- run: f1-engine-2026-11-01
  step: prepare
  outcome: done
  detail: 96 blocks, 2 sections
  evidence:
  - data/runs/f1-engine-2026-11-01/naredba-8121z-310-ot-17-yuli-2014-g-za-prenaznachavane-na-darzhavnite-sluzhiteli/blocks.json
- run: f1-engine-2026-11-01
  step: label
  outcome: done
  detail: 'round 0 collected: 1 exception(s), 2 source finding(s)'
  evidence:
  - data/runs/f1-engine-2026-11-01/naredba-8121z-310-ot-17-yuli-2014-g-za-prenaznachavane-na-darzhavnite-sluzhiteli/report-round0.json
- run: f1-engine-2026-11-01
  step: ladder
  outcome: done
  detail: no residue after round 1
  evidence:
  - data/runs/f1-engine-2026-11-01/naredba-8121z-310-ot-17-yuli-2014-g-za-prenaznachavane-na-darzhavnite-sluzhiteli/ladder.json
  - data/runs/f1-engine-2026-11-01/naredba-8121z-310-ot-17-yuli-2014-g-za-prenaznachavane-na-darzhavnite-sluzhiteli/report-round1.json
- run: f1-engine-2026-11-01
  step: content_check
  outcome: done
  detail: 'no lost text, no exception; source findings {''malformed_head'': 2}'
  evidence:
  - data/runs/f1-engine-2026-11-01/naredba-8121z-310-ot-17-yuli-2014-g-za-prenaznachavane-na-darzhavnite-sluzhiteli/content-check.json
- run: f1-engine-2026-11-01
  step: apply
  outcome: stop
  detail: 'material 88705 (бр. 87/2014): 1 check exception(s) after the operations, first item_order at line 73: 2. opens the list'
  evidence:
  - data/runs/f1-engine-2026-11-01/naredba-8121z-310-ot-17-yuli-2014-g-za-prenaznachavane-na-darzhavnite-sluzhiteli/apply/01-88705/checks.json
- run: f1-engine-2026-11-01
  step: apply
  outcome: stop
  detail: 'material 113274 (бр. 29/2017): the answer is refused: §4.2 delete_words: the words '','' occur 2 times at the address; the instruction does not say навсякъде'
  evidence:
  - data/runs/f1-engine-2026-11-01/naredba-8121z-310-ot-17-yuli-2014-g-za-prenaznachavane-na-darzhavnite-sluzhiteli/apply/04-113274/answer.json
- run: f1-engine-2026-11-01
  step: apply
  outcome: stop
  detail: 'material 148171 (бр. 47/2020): the answer is refused: §2.1.б outside_set: outside the closed set of operations: After the words q1 (ал. 3) in т. 6 a comma is placed and then q2 (т. 2) is added, so the text reads ''по чл. 164, ал. 3, т. 2 ЗМВР''; insert_words cannot carry the comma, which is not a quoted segment and does not stand as a character on the instruction line.'
  evidence:
  - data/runs/f1-engine-2026-11-01/naredba-8121z-310-ot-17-yuli-2014-g-za-prenaznachavane-na-darzhavnite-sluzhiteli/apply/05-148171/answer.json
run: f1-engine-2026-11-01
record: data/runs/route-ledger/naredba-8121z-310-ot-17-yuli-2014-g-za-prenaznachavane-na-darzhavnite-sluzhiteli.json
date: '2026-11-01'
superseded: the act went on in run f1-engine-2026-11-01
resolved: d63ed62d2
---

## Lessons learnt

(not yet written)

## Proposal

(not yet written)

## The owner's ruling

(not yet given)
