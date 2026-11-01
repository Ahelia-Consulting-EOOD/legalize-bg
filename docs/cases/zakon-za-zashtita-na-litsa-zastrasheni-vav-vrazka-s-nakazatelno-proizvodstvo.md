---
act: zakon-za-zashtita-na-litsa-zastrasheni-vav-vrazka-s-nakazatelno-proizvodstvo
title: Закон за защита на лица, застрашени във връзка с наказателно производство
route: history
stopped_at: apply
exception: 'material 83184 (бр. 21/2014): the answer is refused: §5.5 replace_provision: ''чл. 14, ал. 7'' names 2 place(s) in the act'
tried:
- run: f1-engine-2026-11-01
  step: chain
  outcome: done
  detail: 12 material(s) change the act after бр. 103/2004; lex.bg names 12 issue(s), 0 unexplained (none), 0 the Gazette adds (none); 0 court decision(s) name the act
  evidence:
  - data/runs/f1-engine-2026-11-01/zakon-za-zashtita-na-litsa-zastrasheni-vav-vrazka-s-nakazatelno-proizvodstvo/chain.json
- run: f1-engine-2026-11-01
  step: fetch_material
  outcome: done
  detail: material 18357 of бр. 103/2004 (cached), sha256 416172435e32
  evidence:
  - data/runs/f1-engine-2026-11-01/zakon-za-zashtita-na-litsa-zastrasheni-vav-vrazka-s-nakazatelno-proizvodstvo/material.json
- run: f1-engine-2026-11-01
  step: prepare
  outcome: done
  detail: 149 blocks, 3 sections
  evidence:
  - data/runs/f1-engine-2026-11-01/zakon-za-zashtita-na-litsa-zastrasheni-vav-vrazka-s-nakazatelno-proizvodstvo/blocks.json
- run: f1-engine-2026-11-01
  step: label
  outcome: done
  detail: 'round 0 collected: 3 exception(s), 0 source finding(s)'
  evidence:
  - data/runs/f1-engine-2026-11-01/zakon-za-zashtita-na-litsa-zastrasheni-vav-vrazka-s-nakazatelno-proizvodstvo/report-round0.json
- run: f1-engine-2026-11-01
  step: ladder
  outcome: done
  detail: no residue after round 1
  evidence:
  - data/runs/f1-engine-2026-11-01/zakon-za-zashtita-na-litsa-zastrasheni-vav-vrazka-s-nakazatelno-proizvodstvo/ladder.json
  - data/runs/f1-engine-2026-11-01/zakon-za-zashtita-na-litsa-zastrasheni-vav-vrazka-s-nakazatelno-proizvodstvo/report-round1.json
- run: f1-engine-2026-11-01
  step: content_check
  outcome: done
  detail: no lost text, no exception; source findings none
  evidence:
  - data/runs/f1-engine-2026-11-01/zakon-za-zashtita-na-litsa-zastrasheni-vav-vrazka-s-nakazatelno-proizvodstvo/content-check.json
- run: f1-engine-2026-11-01
  step: apply
  outcome: stop
  detail: 'material 6481 (бр. 66/2008): the answer is refused: §2.3 insert_provision: ''чл. 6, ал. 5'' names 2 place(s) in the act'
  evidence:
  - data/runs/f1-engine-2026-11-01/zakon-za-zashtita-na-litsa-zastrasheni-vav-vrazka-s-nakazatelno-proizvodstvo/apply/03-6481/answer.json
- run: f1-engine-2026-11-01
  step: apply
  outcome: stop
  detail: 'material 6481 (бр. 66/2008): the answer is refused: §12.1 replace_provision: ''чл. 27, ал. 1, т. 1'' names 0 place(s) in the act'
  evidence:
  - data/runs/f1-engine-2026-11-01/zakon-za-zashtita-na-litsa-zastrasheni-vav-vrazka-s-nakazatelno-proizvodstvo/apply/03-6481/answer.json
- run: f1-engine-2026-11-01
  step: label
  outcome: done
  detail: 'round 0 collected: 0 exception(s), 0 source finding(s)'
  evidence:
  - data/runs/f1-engine-2026-11-01/zakon-za-zashtita-na-litsa-zastrasheni-vav-vrazka-s-nakazatelno-proizvodstvo/report-round0.json
- run: f1-engine-2026-11-01
  step: ladder
  outcome: done
  detail: no residue after round 0
  evidence:
  - data/runs/f1-engine-2026-11-01/zakon-za-zashtita-na-litsa-zastrasheni-vav-vrazka-s-nakazatelno-proizvodstvo/ladder.json
  - data/runs/f1-engine-2026-11-01/zakon-za-zashtita-na-litsa-zastrasheni-vav-vrazka-s-nakazatelno-proizvodstvo/report-round0.json
- run: f1-engine-2026-11-01
  step: content_check
  outcome: done
  detail: no lost text, no exception; source findings none
  evidence:
  - data/runs/f1-engine-2026-11-01/zakon-za-zashtita-na-litsa-zastrasheni-vav-vrazka-s-nakazatelno-proizvodstvo/content-check.json
- run: f1-engine-2026-11-01
  step: apply
  outcome: interrupted
  detail: ''
  evidence: []
- run: f1-engine-2026-11-01
  step: apply
  outcome: stop
  detail: 'material 83184 (бр. 21/2014): the answer is refused: §1 delete_words: the words ''по глава първа, глава втора, глава шеста – чл. 242, ал. 2, 3 и 4, глава осма – раздел IV, глава единадесета – чл. 330, 333, 354а – 354в, и глава четиринадесета от Наказателния кодекс'' do not occur in ''**Чл. 4.** Застрашените лица могат да получат спец'''
  evidence:
  - data/runs/f1-engine-2026-11-01/zakon-za-zashtita-na-litsa-zastrasheni-vav-vrazka-s-nakazatelno-proizvodstvo/apply/05-83184/answer.json
- run: f1-engine-2026-11-01
  step: apply
  outcome: stop
  detail: 'material 83184 (бр. 21/2014): the answer is refused: §3.2 insert_provision: the address ''чл. 13, ал. 2'' is already carried by a provision, and no renumber of the material moves it'
  evidence:
  - data/runs/f1-engine-2026-11-01/zakon-za-zashtita-na-litsa-zastrasheni-vav-vrazka-s-nakazatelno-proizvodstvo/apply/05-83184/answer.json
- run: f1-engine-2026-11-01
  step: apply
  outcome: stop
  detail: 'material 83184 (бр. 21/2014): the answer is refused: §5.5 replace_provision: ''чл. 14, ал. 7'' names 2 place(s) in the act'
  evidence:
  - data/runs/f1-engine-2026-11-01/zakon-za-zashtita-na-litsa-zastrasheni-vav-vrazka-s-nakazatelno-proizvodstvo/apply/05-83184/answer.json
- run: f1-engine-2026-11-01
  step: apply
  outcome: stop
  detail: 'material 83184 (бр. 21/2014): the answer is refused: §5.5 replace_provision: ''чл. 14, ал. 7'' names 2 place(s) in the act'
  evidence:
  - data/runs/f1-engine-2026-11-01/zakon-za-zashtita-na-litsa-zastrasheni-vav-vrazka-s-nakazatelno-proizvodstvo/apply/05-83184/answer.json
- run: f1-engine-2026-11-01
  step: apply
  outcome: stop
  detail: 'material 83184 (бр. 21/2014): the answer is refused: §5.5 replace_provision: ''чл. 14, ал. 7'' names 2 place(s) in the act'
  evidence:
  - data/runs/f1-engine-2026-11-01/zakon-za-zashtita-na-litsa-zastrasheni-vav-vrazka-s-nakazatelno-proizvodstvo/apply/05-83184/answer.json
- run: f1-engine-2026-11-01
  step: apply
  outcome: stop
  detail: 'material 83184 (бр. 21/2014): the answer is refused: §5.5 replace_provision: ''чл. 14, ал. 7'' names 2 place(s) in the act'
  evidence:
  - data/runs/f1-engine-2026-11-01/zakon-za-zashtita-na-litsa-zastrasheni-vav-vrazka-s-nakazatelno-proizvodstvo/apply/05-83184/answer.json
- run: f1-engine-2026-11-01
  step: apply
  outcome: stop
  detail: 'material 83184 (бр. 21/2014): the answer is refused: §5.5 replace_provision: ''чл. 14, ал. 7'' names 2 place(s) in the act'
  evidence:
  - data/runs/f1-engine-2026-11-01/zakon-za-zashtita-na-litsa-zastrasheni-vav-vrazka-s-nakazatelno-proizvodstvo/apply/05-83184/answer.json
- run: f1-engine-2026-11-01
  step: apply
  outcome: stop
  detail: 'material 83184 (бр. 21/2014): the answer is refused: §5.5 replace_provision: ''чл. 14, ал. 7'' names 2 place(s) in the act'
  evidence:
  - data/runs/f1-engine-2026-11-01/zakon-za-zashtita-na-litsa-zastrasheni-vav-vrazka-s-nakazatelno-proizvodstvo/apply/05-83184/answer.json
- run: f1-engine-2026-11-01
  step: apply
  outcome: stop
  detail: 'material 83184 (бр. 21/2014): the answer is refused: §5.5 replace_provision: ''чл. 14, ал. 7'' names 2 place(s) in the act'
  evidence:
  - data/runs/f1-engine-2026-11-01/zakon-za-zashtita-na-litsa-zastrasheni-vav-vrazka-s-nakazatelno-proizvodstvo/apply/05-83184/answer.json
- run: f1-engine-2026-11-01
  step: apply
  outcome: stop
  detail: 'material 83184 (бр. 21/2014): the answer is refused: §5.5 replace_provision: ''чл. 14, ал. 7'' names 2 place(s) in the act'
  evidence:
  - data/runs/f1-engine-2026-11-01/zakon-za-zashtita-na-litsa-zastrasheni-vav-vrazka-s-nakazatelno-proizvodstvo/apply/05-83184/answer.json
- run: f1-engine-2026-11-01
  step: apply
  outcome: stop
  detail: 'material 83184 (бр. 21/2014): the answer is refused: §5.5 replace_provision: ''чл. 14, ал. 7'' names 2 place(s) in the act'
  evidence:
  - data/runs/f1-engine-2026-11-01/zakon-za-zashtita-na-litsa-zastrasheni-vav-vrazka-s-nakazatelno-proizvodstvo/apply/05-83184/answer.json
- run: f1-engine-2026-11-01
  step: apply
  outcome: stop
  detail: 'material 83184 (бр. 21/2014): the answer is refused: §5.5 replace_provision: ''чл. 14, ал. 7'' names 2 place(s) in the act'
  evidence:
  - data/runs/f1-engine-2026-11-01/zakon-za-zashtita-na-litsa-zastrasheni-vav-vrazka-s-nakazatelno-proizvodstvo/apply/05-83184/answer.json
- run: f1-engine-2026-11-01
  step: apply
  outcome: stop
  detail: 'material 83184 (бр. 21/2014): the answer is refused: §5.5 replace_provision: ''чл. 14, ал. 7'' names 2 place(s) in the act'
  evidence:
  - data/runs/f1-engine-2026-11-01/zakon-za-zashtita-na-litsa-zastrasheni-vav-vrazka-s-nakazatelno-proizvodstvo/apply/05-83184/answer.json
run: f1-engine-2026-11-01
record: data/runs/route-ledger/zakon-za-zashtita-na-litsa-zastrasheni-vav-vrazka-s-nakazatelno-proizvodstvo.json
date: '2026-11-01'
---

## Lessons learnt

(not yet written)

## Proposal

(not yet written)

## The owner's ruling

(not yet given)
