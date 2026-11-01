---
act: naredba-1-ot-22-yanuari-2015-g-za-pridobivane-na-spetsialnost-v-sistemata-na-zdr
title: Наредба № 1 от 22 януари 2015 г. за придобиване на специалност в системата на здравеопазването
route: history
stopped_at: apply
exception: 'material 139711 (бр. 58/2019): the answer is refused: §6 replace_words: the words ''не повече от'' occur 2 times at the address; the instruction does not say навсякъде'
tried:
- run: f1-engine-2026-11-01
  step: chain
  outcome: done
  detail: 9 material(s) change the act after бр. 7/2015; lex.bg names 10 issue(s), 1 unexplained (81/2021), 0 the Gazette adds (none); 0 court decision(s) name the act
  evidence:
  - data/runs/f1-engine-2026-11-01/naredba-1-ot-22-yanuari-2015-g-za-pridobivane-na-spetsialnost-v-sistemata-na-zdr/chain.json
- run: f1-engine-2026-11-01
  step: fetch_material
  outcome: done
  detail: material 91505 of бр. 7/2015 (cached), sha256 3e21d572bf7e
  evidence:
  - data/runs/f1-engine-2026-11-01/naredba-1-ot-22-yanuari-2015-g-za-pridobivane-na-spetsialnost-v-sistemata-na-zdr/material.json
- run: f1-engine-2026-11-01
  step: prepare
  outcome: done
  detail: 971 blocks, 28 sections
  evidence:
  - data/runs/f1-engine-2026-11-01/naredba-1-ot-22-yanuari-2015-g-za-pridobivane-na-spetsialnost-v-sistemata-na-zdr/blocks.json
- run: f1-engine-2026-11-01
  step: label
  outcome: done
  detail: 'round 0 collected: 1 exception(s), 1 source finding(s)'
  evidence:
  - data/runs/f1-engine-2026-11-01/naredba-1-ot-22-yanuari-2015-g-za-pridobivane-na-spetsialnost-v-sistemata-na-zdr/report-round0.json
- run: f1-engine-2026-11-01
  step: ladder
  outcome: done
  detail: no residue after round 1
  evidence:
  - data/runs/f1-engine-2026-11-01/naredba-1-ot-22-yanuari-2015-g-za-pridobivane-na-spetsialnost-v-sistemata-na-zdr/ladder.json
  - data/runs/f1-engine-2026-11-01/naredba-1-ot-22-yanuari-2015-g-za-pridobivane-na-spetsialnost-v-sistemata-na-zdr/report-round1.json
- run: f1-engine-2026-11-01
  step: content_check
  outcome: done
  detail: 'no lost text, no exception; source findings {''malformed_head'': 1}'
  evidence:
  - data/runs/f1-engine-2026-11-01/naredba-1-ot-22-yanuari-2015-g-za-pridobivane-na-spetsialnost-v-sistemata-na-zdr/content-check.json
- run: f1-engine-2026-11-01
  step: apply
  outcome: stop
  detail: 'material 98158 (бр. 83/2015): the answer is refused: §2.2: the text '', обучението за придобиване на специалност „Обща медицина“ и'' does not stand in the instruction'
  evidence:
  - data/runs/f1-engine-2026-11-01/naredba-1-ot-22-yanuari-2015-g-za-pridobivane-na-spetsialnost-v-sistemata-na-zdr/apply/01-98158/answer.json
- run: f1-engine-2026-11-01
  step: apply
  outcome: stop
  detail: 'material 98158 (бр. 83/2015): the answer is refused: §1 insert_words: the anchor ''1'' occurs 6 times'
  evidence:
  - data/runs/f1-engine-2026-11-01/naredba-1-ot-22-yanuari-2015-g-za-pridobivane-na-spetsialnost-v-sistemata-na-zdr/apply/01-98158/answer.json
- run: f1-engine-2026-11-01
  step: apply
  outcome: stop
  detail: 'material 98158 (бр. 83/2015): the answer is refused: §6.1 delete_words: the words ''лекар по дентална медицина, специализант по…'' do not occur in ''(1) Базите за обучение обявяват целогодишно, включ'''
  evidence:
  - data/runs/f1-engine-2026-11-01/naredba-1-ot-22-yanuari-2015-g-za-pridobivane-na-spetsialnost-v-sistemata-na-zdr/apply/01-98158/answer.json
- run: f1-engine-2026-11-01
  step: apply
  outcome: stop
  detail: 'material 98158 (бр. 83/2015): the answer is refused: §8 insert_provision: a sentence address fits only an operation on words'
  evidence:
  - data/runs/f1-engine-2026-11-01/naredba-1-ot-22-yanuari-2015-g-za-pridobivane-na-spetsialnost-v-sistemata-na-zdr/apply/01-98158/answer.json
- run: f1-engine-2026-11-01
  step: label
  outcome: done
  detail: 'round 0 collected: 0 exception(s), 1 source finding(s)'
  evidence:
  - data/runs/f1-engine-2026-11-01/naredba-1-ot-22-yanuari-2015-g-za-pridobivane-na-spetsialnost-v-sistemata-na-zdr/report-round0.json
- run: f1-engine-2026-11-01
  step: ladder
  outcome: done
  detail: no residue after round 0
  evidence:
  - data/runs/f1-engine-2026-11-01/naredba-1-ot-22-yanuari-2015-g-za-pridobivane-na-spetsialnost-v-sistemata-na-zdr/ladder.json
  - data/runs/f1-engine-2026-11-01/naredba-1-ot-22-yanuari-2015-g-za-pridobivane-na-spetsialnost-v-sistemata-na-zdr/report-round0.json
- run: f1-engine-2026-11-01
  step: content_check
  outcome: done
  detail: 'no lost text, no exception; source findings {''malformed_head'': 1}'
  evidence:
  - data/runs/f1-engine-2026-11-01/naredba-1-ot-22-yanuari-2015-g-za-pridobivane-na-spetsialnost-v-sistemata-na-zdr/content-check.json
- run: f1-engine-2026-11-01
  step: apply
  outcome: stop
  detail: 'material 98158 (бр. 83/2015): the answer is refused: §15 replace_provision: ''приложение № 1, раздел II'' names 0 place(s) in the act'
  evidence:
  - data/runs/f1-engine-2026-11-01/naredba-1-ot-22-yanuari-2015-g-za-pridobivane-na-spetsialnost-v-sistemata-na-zdr/apply/01-98158/answer.json
- run: f1-engine-2026-11-01
  step: apply
  outcome: stop
  detail: 'material 139711 (бр. 58/2019): the answer is refused: §6 replace_words: the words ''не повече от'' occur 2 times at the address; the instruction does not say навсякъде'
  evidence:
  - data/runs/f1-engine-2026-11-01/naredba-1-ot-22-yanuari-2015-g-za-pridobivane-na-spetsialnost-v-sistemata-na-zdr/apply/03-139711/answer.json
- run: f1-engine-2026-11-01
  step: apply
  outcome: stop
  detail: 'material 139711 (бр. 58/2019): the answer is refused: §6 replace_words: the words ''не повече от'' occur 2 times at the address; the instruction does not say навсякъде'
  evidence:
  - data/runs/f1-engine-2026-11-01/naredba-1-ot-22-yanuari-2015-g-za-pridobivane-na-spetsialnost-v-sistemata-na-zdr/apply/03-139711/answer.json
- run: f1-engine-2026-11-01
  step: apply
  outcome: stop
  detail: 'material 139711 (бр. 58/2019): the answer is refused: §6 replace_words: the words ''не повече от'' occur 2 times at the address; the instruction does not say навсякъде'
  evidence:
  - data/runs/f1-engine-2026-11-01/naredba-1-ot-22-yanuari-2015-g-za-pridobivane-na-spetsialnost-v-sistemata-na-zdr/apply/03-139711/answer.json
- run: f1-engine-2026-11-01
  step: apply
  outcome: stop
  detail: 'material 139711 (бр. 58/2019): the answer is refused: §6 replace_words: the words ''не повече от'' occur 2 times at the address; the instruction does not say навсякъде'
  evidence:
  - data/runs/f1-engine-2026-11-01/naredba-1-ot-22-yanuari-2015-g-za-pridobivane-na-spetsialnost-v-sistemata-na-zdr/apply/03-139711/answer.json
- run: f1-engine-2026-11-01
  step: apply
  outcome: stop
  detail: 'material 139711 (бр. 58/2019): the answer is refused: §6 replace_words: the words ''не повече от'' occur 2 times at the address; the instruction does not say навсякъде'
  evidence:
  - data/runs/f1-engine-2026-11-01/naredba-1-ot-22-yanuari-2015-g-za-pridobivane-na-spetsialnost-v-sistemata-na-zdr/apply/03-139711/answer.json
- run: f1-engine-2026-11-01
  step: apply
  outcome: stop
  detail: 'material 139711 (бр. 58/2019): the answer is refused: §6 replace_words: the words ''не повече от'' occur 2 times at the address; the instruction does not say навсякъде'
  evidence:
  - data/runs/f1-engine-2026-11-01/naredba-1-ot-22-yanuari-2015-g-za-pridobivane-na-spetsialnost-v-sistemata-na-zdr/apply/03-139711/answer.json
- run: f1-engine-2026-11-01
  step: apply
  outcome: stop
  detail: 'material 139711 (бр. 58/2019): the answer is refused: §6 replace_words: the words ''не повече от'' occur 2 times at the address; the instruction does not say навсякъде'
  evidence:
  - data/runs/f1-engine-2026-11-01/naredba-1-ot-22-yanuari-2015-g-za-pridobivane-na-spetsialnost-v-sistemata-na-zdr/apply/03-139711/answer.json
- run: f1-engine-2026-11-01
  step: apply
  outcome: stop
  detail: 'material 139711 (бр. 58/2019): the answer is refused: §6 replace_words: the words ''не повече от'' occur 2 times at the address; the instruction does not say навсякъде'
  evidence:
  - data/runs/f1-engine-2026-11-01/naredba-1-ot-22-yanuari-2015-g-za-pridobivane-na-spetsialnost-v-sistemata-na-zdr/apply/03-139711/answer.json
- run: f1-engine-2026-11-01
  step: apply
  outcome: stop
  detail: 'material 139711 (бр. 58/2019): the answer is refused: §6 replace_words: the words ''не повече от'' occur 2 times at the address; the instruction does not say навсякъде'
  evidence:
  - data/runs/f1-engine-2026-11-01/naredba-1-ot-22-yanuari-2015-g-za-pridobivane-na-spetsialnost-v-sistemata-na-zdr/apply/03-139711/answer.json
- run: f1-engine-2026-11-01
  step: apply
  outcome: stop
  detail: 'material 139711 (бр. 58/2019): the answer is refused: §6 replace_words: the words ''не повече от'' occur 2 times at the address; the instruction does not say навсякъде'
  evidence:
  - data/runs/f1-engine-2026-11-01/naredba-1-ot-22-yanuari-2015-g-za-pridobivane-na-spetsialnost-v-sistemata-na-zdr/apply/03-139711/answer.json
- run: f1-engine-2026-11-01
  step: apply
  outcome: stop
  detail: 'material 139711 (бр. 58/2019): the answer is refused: §6 replace_words: the words ''не повече от'' occur 2 times at the address; the instruction does not say навсякъде'
  evidence:
  - data/runs/f1-engine-2026-11-01/naredba-1-ot-22-yanuari-2015-g-za-pridobivane-na-spetsialnost-v-sistemata-na-zdr/apply/03-139711/answer.json
- run: f1-engine-2026-11-01
  step: apply
  outcome: stop
  detail: 'material 139711 (бр. 58/2019): the answer is refused: §6 replace_words: the words ''не повече от'' occur 2 times at the address; the instruction does not say навсякъде'
  evidence:
  - data/runs/f1-engine-2026-11-01/naredba-1-ot-22-yanuari-2015-g-za-pridobivane-na-spetsialnost-v-sistemata-na-zdr/apply/03-139711/answer.json
- run: f1-engine-2026-11-01
  step: prepare
  outcome: done
  detail: 971 blocks, 28 sections
  evidence:
  - data/runs/f1-engine-2026-11-01/naredba-1-ot-22-yanuari-2015-g-za-pridobivane-na-spetsialnost-v-sistemata-na-zdr/blocks.json
- run: f1-engine-2026-11-01
  step: label
  outcome: done
  detail: 'round 0 collected: 0 exception(s), 1 source finding(s)'
  evidence:
  - data/runs/f1-engine-2026-11-01/naredba-1-ot-22-yanuari-2015-g-za-pridobivane-na-spetsialnost-v-sistemata-na-zdr/report-round0.json
- run: f1-engine-2026-11-01
  step: ladder
  outcome: done
  detail: no residue after round 0
  evidence:
  - data/runs/f1-engine-2026-11-01/naredba-1-ot-22-yanuari-2015-g-za-pridobivane-na-spetsialnost-v-sistemata-na-zdr/ladder.json
  - data/runs/f1-engine-2026-11-01/naredba-1-ot-22-yanuari-2015-g-za-pridobivane-na-spetsialnost-v-sistemata-na-zdr/report-round0.json
- run: f1-engine-2026-11-01
  step: content_check
  outcome: done
  detail: 'no lost text, no exception; source findings {''malformed_head'': 1}'
  evidence:
  - data/runs/f1-engine-2026-11-01/naredba-1-ot-22-yanuari-2015-g-za-pridobivane-na-spetsialnost-v-sistemata-na-zdr/content-check.json
- run: f1-engine-2026-11-01
  step: apply
  outcome: stop
  detail: 'material 139711 (бр. 58/2019): the answer is refused: §6 replace_words: the words ''не повече от'' occur 2 times at the address; the instruction does not say навсякъде'
  evidence:
  - data/runs/f1-engine-2026-11-01/naredba-1-ot-22-yanuari-2015-g-za-pridobivane-na-spetsialnost-v-sistemata-na-zdr/apply/03-139711/answer.json
- run: f1-engine-2026-11-01
  step: apply
  outcome: stop
  detail: 'material 139711 (бр. 58/2019): the answer is refused: §6 replace_words: the words ''не повече от'' occur 2 times at the address; the instruction does not say навсякъде'
  evidence:
  - data/runs/f1-engine-2026-11-01/naredba-1-ot-22-yanuari-2015-g-za-pridobivane-na-spetsialnost-v-sistemata-na-zdr/apply/03-139711/answer.json
- run: f1-engine-2026-11-01
  step: apply
  outcome: stop
  detail: 'material 139711 (бр. 58/2019): the answer is refused: §6 replace_words: the words ''не повече от'' occur 2 times at the address; the instruction does not say навсякъде'
  evidence:
  - data/runs/f1-engine-2026-11-01/naredba-1-ot-22-yanuari-2015-g-za-pridobivane-na-spetsialnost-v-sistemata-na-zdr/apply/03-139711/answer.json
- run: f1-engine-2026-11-01
  step: apply
  outcome: stop
  detail: 'material 139711 (бр. 58/2019): the answer is refused: §6 replace_words: the words ''не повече от'' occur 2 times at the address; the instruction does not say навсякъде'
  evidence:
  - data/runs/f1-engine-2026-11-01/naredba-1-ot-22-yanuari-2015-g-za-pridobivane-na-spetsialnost-v-sistemata-na-zdr/apply/03-139711/answer.json
run: f1-engine-2026-11-01
record: data/runs/route-ledger/naredba-1-ot-22-yanuari-2015-g-za-pridobivane-na-spetsialnost-v-sistemata-na-zdr.json
date: '2026-11-01'
---

## Lessons learnt

(not yet written)

## Proposal

(not yet written)

## The owner's ruling

(not yet given)
