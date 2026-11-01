---
act: pravilnik-za-ustroystvoto-funktsiite-i-deynostta-na-darzhavno-predpriyatie-prist
title: Правилник за устройството, функциите и дейността на Държавно предприятие „Пристанищна инфраструктура“
route: history
stopped_at: apply
exception: 'material 94043 (бр. 31/2015): the answer is refused: §2.1 insert_words: the words of ''наименованието на чл. 33'' are in its alineas; the address names the alinea'
tried:
- run: f1-engine-2026-11-01
  step: chain
  outcome: done
  detail: 8 material(s) change the act after бр. 36/2011; lex.bg names 8 issue(s), 0 unexplained (none), 0 the Gazette adds (none); 0 court decision(s) name the act
  evidence:
  - data/runs/f1-engine-2026-11-01/pravilnik-za-ustroystvoto-funktsiite-i-deynostta-na-darzhavno-predpriyatie-prist/chain.json
- run: f1-engine-2026-11-01
  step: fetch_material
  outcome: done
  detail: material 49017 of бр. 36/2011 (cached), sha256 3a7fb6d005a2
  evidence:
  - data/runs/f1-engine-2026-11-01/pravilnik-za-ustroystvoto-funktsiite-i-deynostta-na-darzhavno-predpriyatie-prist/material.json
- run: f1-engine-2026-11-01
  step: prepare
  outcome: done
  detail: 556 blocks, 14 sections
  evidence:
  - data/runs/f1-engine-2026-11-01/pravilnik-za-ustroystvoto-funktsiite-i-deynostta-na-darzhavno-predpriyatie-prist/blocks.json
- run: f1-engine-2026-11-01
  step: label
  outcome: done
  detail: 'round 0 collected: 93 exception(s), 0 source finding(s)'
  evidence:
  - data/runs/f1-engine-2026-11-01/pravilnik-za-ustroystvoto-funktsiite-i-deynostta-na-darzhavno-predpriyatie-prist/report-round0.json
- run: f1-engine-2026-11-01
  step: label
  outcome: done
  detail: 'round 0 collected: 93 exception(s), 0 source finding(s)'
  evidence:
  - data/runs/f1-engine-2026-11-01/pravilnik-za-ustroystvoto-funktsiite-i-deynostta-na-darzhavno-predpriyatie-prist/report-round0.json
- run: f1-engine-2026-11-01
  step: ladder
  outcome: done
  detail: no residue after round 2
  evidence:
  - data/runs/f1-engine-2026-11-01/pravilnik-za-ustroystvoto-funktsiite-i-deynostta-na-darzhavno-predpriyatie-prist/ladder.json
  - data/runs/f1-engine-2026-11-01/pravilnik-za-ustroystvoto-funktsiite-i-deynostta-na-darzhavno-predpriyatie-prist/report-round2.json
- run: f1-engine-2026-11-01
  step: content_check
  outcome: done
  detail: no lost text, no exception; source findings none
  evidence:
  - data/runs/f1-engine-2026-11-01/pravilnik-za-ustroystvoto-funktsiite-i-deynostta-na-darzhavno-predpriyatie-prist/content-check.json
- run: f1-engine-2026-11-01
  step: apply
  outcome: stop
  detail: 'material 68862 (бр. 77/2012): the answer is refused: §2 delete_words: the words ''Канцелария'' do not occur in ''# ПРАВИЛНИК за устройството, функциите и дейността'''
  evidence:
  - data/runs/f1-engine-2026-11-01/pravilnik-za-ustroystvoto-funktsiite-i-deynostta-na-darzhavno-predpriyatie-prist/apply/01-68862/answer.json
- run: f1-engine-2026-11-01
  step: apply
  outcome: stop
  detail: 'material 68862 (бр. 77/2012): the answer is refused: §5 delete_words: the address ''чл. 29, т. 5.15'' carries a part the grammar does not read: '',  .15'''
  evidence:
  - data/runs/f1-engine-2026-11-01/pravilnik-za-ustroystvoto-funktsiite-i-deynostta-na-darzhavno-predpriyatie-prist/apply/01-68862/answer.json
- run: f1-engine-2026-11-01
  step: apply
  outcome: stop
  detail: 'material 68862 (бр. 77/2012): the answer is refused: §6 replace_heading: ''чл. 30'' is not a heading'
  evidence:
  - data/runs/f1-engine-2026-11-01/pravilnik-za-ustroystvoto-funktsiite-i-deynostta-na-darzhavno-predpriyatie-prist/apply/01-68862/answer.json
- run: f1-engine-2026-11-01
  step: apply
  outcome: stop
  detail: 'material 68862 (бр. 77/2012): the answer is refused: §14 replace_heading: ''чл. 36'' is not a heading'
  evidence:
  - data/runs/f1-engine-2026-11-01/pravilnik-za-ustroystvoto-funktsiite-i-deynostta-na-darzhavno-predpriyatie-prist/apply/01-68862/answer.json
- run: f1-engine-2026-11-01
  step: apply
  outcome: stop
  detail: 'material 79704 (бр. 93/2013): the answer is refused: §8: blocks [61, 386] lie outside the instruction''s quoted text [61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 73, 75, 76]'
  evidence:
  - data/runs/f1-engine-2026-11-01/pravilnik-za-ustroystvoto-funktsiite-i-deynostta-na-darzhavno-predpriyatie-prist/apply/02-79704/answer.json
- run: f1-engine-2026-11-01
  step: apply
  outcome: stop
  detail: 'material 79704 (бр. 93/2013): 2 check exception(s) after the operations, first label_text_mismatch at line 322: continuation on a line that opens like a provision: ''a) извършване на анализ на нуждите на пр'''
  evidence:
  - data/runs/f1-engine-2026-11-01/pravilnik-za-ustroystvoto-funktsiite-i-deynostta-na-darzhavno-predpriyatie-prist/apply/02-79704/checks.json
- run: f1-engine-2026-11-01
  step: apply
  outcome: stop
  detail: 'material 82388 (бр. 12/2014): the answer is refused: §7.1.е delete_words: the words ''участие в'' occur 2 times at the address; the instruction does not say навсякъде'
  evidence:
  - data/runs/f1-engine-2026-11-01/pravilnik-za-ustroystvoto-funktsiite-i-deynostta-na-darzhavno-predpriyatie-prist/apply/03-82388/answer.json
- run: f1-engine-2026-11-01
  step: apply
  outcome: stop
  detail: 'material 82388 (бр. 12/2014): the answer is refused: §7.1.е delete_words: the words ''участие в'' occur 2 times at the address; the instruction does not say навсякъде'
  evidence:
  - data/runs/f1-engine-2026-11-01/pravilnik-za-ustroystvoto-funktsiite-i-deynostta-na-darzhavno-predpriyatie-prist/apply/03-82388/answer.json
- run: f1-engine-2026-11-01
  step: apply
  outcome: stop
  detail: 'material 82388 (бр. 12/2014): the answer is refused: §7.1.е delete_words: the words ''участие в'' occur 2 times at the address; the instruction does not say навсякъде'
  evidence:
  - data/runs/f1-engine-2026-11-01/pravilnik-za-ustroystvoto-funktsiite-i-deynostta-na-darzhavno-predpriyatie-prist/apply/03-82388/answer.json
- run: f1-engine-2026-11-01
  step: apply
  outcome: stop
  detail: 'material 94043 (бр. 31/2015): the answer is refused: §2.1 insert_words: the words of ''наименованието на чл. 33'' are in its alineas; the address names the alinea'
  evidence:
  - data/runs/f1-engine-2026-11-01/pravilnik-za-ustroystvoto-funktsiite-i-deynostta-na-darzhavno-predpriyatie-prist/apply/04-94043/answer.json
- run: f1-engine-2026-11-01
  step: apply
  outcome: stop
  detail: 'material 94043 (бр. 31/2015): the answer is refused: §2.1 insert_words: the words of ''наименованието на чл. 33'' are in its alineas; the address names the alinea'
  evidence:
  - data/runs/f1-engine-2026-11-01/pravilnik-za-ustroystvoto-funktsiite-i-deynostta-na-darzhavno-predpriyatie-prist/apply/04-94043/answer.json
run: f1-engine-2026-11-01
record: data/runs/route-ledger/pravilnik-za-ustroystvoto-funktsiite-i-deynostta-na-darzhavno-predpriyatie-prist.json
date: '2026-11-01'
---

## Lessons learnt

(not yet written)

## Proposal

(not yet written)

## The owner's ruling

(not yet given)
