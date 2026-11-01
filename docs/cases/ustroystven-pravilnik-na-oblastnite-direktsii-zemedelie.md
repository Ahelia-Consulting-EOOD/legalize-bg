---
act: ustroystven-pravilnik-na-oblastnite-direktsii-zemedelie
title: Устройствен правилник на областните дирекции „Земеделие“
route: history
stopped_at: witnesses
exception: 'the settler found our reading wrong (reading_error): lexbg: 73 difference(s), settled reading_error 24, same_text_other_form 46, witness_error 3; moj: absent (the portal answers 500 for https://justice.government.bg/home/normdoc/2135659679 (absent, 2026-11-01T12:49:16+00:00))'
tried:
- run: f1-engine-2026-11-01
  step: chain
  outcome: done
  detail: 12 material(s) change the act after бр. 7/2010; lex.bg names 12 issue(s), 0 unexplained (none), 0 the Gazette adds (none); 0 court decision(s) name the act
  evidence:
  - data/runs/f1-engine-2026-11-01/ustroystven-pravilnik-na-oblastnite-direktsii-zemedelie/chain.json
- run: f1-engine-2026-11-01
  step: fetch_material
  outcome: done
  detail: material 28798 of бр. 7/2010 (cached), sha256 6396c9985418
  evidence:
  - data/runs/f1-engine-2026-11-01/ustroystven-pravilnik-na-oblastnite-direktsii-zemedelie/material.json
- run: f1-engine-2026-11-01
  step: prepare
  outcome: done
  detail: 236 blocks, 7 sections
  evidence:
  - data/runs/f1-engine-2026-11-01/ustroystven-pravilnik-na-oblastnite-direktsii-zemedelie/blocks.json
- run: f1-engine-2026-11-01
  step: label
  outcome: done
  detail: 'round 0 collected: 1 exception(s), 0 source finding(s)'
  evidence:
  - data/runs/f1-engine-2026-11-01/ustroystven-pravilnik-na-oblastnite-direktsii-zemedelie/report-round0.json
- run: f1-engine-2026-11-01
  step: ladder
  outcome: done
  detail: no residue after round 1
  evidence:
  - data/runs/f1-engine-2026-11-01/ustroystven-pravilnik-na-oblastnite-direktsii-zemedelie/ladder.json
  - data/runs/f1-engine-2026-11-01/ustroystven-pravilnik-na-oblastnite-direktsii-zemedelie/report-round1.json
- run: f1-engine-2026-11-01
  step: content_check
  outcome: done
  detail: no lost text, no exception; source findings none
  evidence:
  - data/runs/f1-engine-2026-11-01/ustroystven-pravilnik-na-oblastnite-direktsii-zemedelie/content-check.json
- run: f1-engine-2026-11-01
  step: apply
  outcome: stop
  detail: 'material 29283 (бр. 9/2010): the answer is refused: block 85 does not close the quotation: ''41'''
  evidence:
  - data/runs/f1-engine-2026-11-01/ustroystven-pravilnik-na-oblastnite-direktsii-zemedelie/apply/01-29283/answer.json
- run: f1-engine-2026-11-01
  step: apply
  outcome: stop
  detail: 'material 29283 (бр. 9/2010): the answer is refused: §1 replace_annex: ''Приложението към чл. 6, ал. 2'' names 0 place(s) in the act'
  evidence:
  - data/runs/f1-engine-2026-11-01/ustroystven-pravilnik-na-oblastnite-direktsii-zemedelie/apply/01-29283/answer.json
- run: f1-engine-2026-11-01
  step: label
  outcome: done
  detail: 'round 0 collected: 1 exception(s), 0 source finding(s)'
  evidence:
  - data/runs/f1-engine-2026-11-01/ustroystven-pravilnik-na-oblastnite-direktsii-zemedelie/report-round0.json
- run: f1-engine-2026-11-01
  step: ladder
  outcome: done
  detail: no residue after round 1
  evidence:
  - data/runs/f1-engine-2026-11-01/ustroystven-pravilnik-na-oblastnite-direktsii-zemedelie/ladder.json
  - data/runs/f1-engine-2026-11-01/ustroystven-pravilnik-na-oblastnite-direktsii-zemedelie/report-round1.json
- run: f1-engine-2026-11-01
  step: apply
  outcome: stop
  detail: 'material 35396 (бр. 60/2010): the answer is refused: §1.2 insert_provision: the address ''чл. 3, ал. 3, т. 14'' is already carried by a provision, and no renumber of the material moves it'
  evidence:
  - data/runs/f1-engine-2026-11-01/ustroystven-pravilnik-na-oblastnite-direktsii-zemedelie/apply/02-35396/answer.json
- run: f1-engine-2026-11-01
  step: apply
  outcome: stop
  detail: 'material 35396 (бр. 60/2010): the answer is refused: §3.1 replace_words: the annex reference in ''Приложение към чл. 6, ал. 2, наименованието'' is not a provision the grammar reads: ''чл. 6, ал. 2, наименованието'''
  evidence:
  - data/runs/f1-engine-2026-11-01/ustroystven-pravilnik-na-oblastnite-direktsii-zemedelie/apply/02-35396/answer.json
- run: f1-engine-2026-11-01
  step: apply
  outcome: stop
  detail: 'material 35396 (бр. 60/2010): the answer is refused: §3.1 replace_words: the words ''1742'' occur 0 times in the title ''Приложение към чл. 6, ал. 2'''
  evidence:
  - data/runs/f1-engine-2026-11-01/ustroystven-pravilnik-na-oblastnite-direktsii-zemedelie/apply/02-35396/answer.json
- run: f1-engine-2026-11-01
  step: apply
  outcome: stop
  detail: 'material 35396 (бр. 60/2010): the answer is refused: §3.3 replace_words: ''Приложение към чл. 6, ал. 2, ред „Областна дирекция „Земеделие“ – Варна“'' names 0 place(s) in the act'
  evidence:
  - data/runs/f1-engine-2026-11-01/ustroystven-pravilnik-na-oblastnite-direktsii-zemedelie/apply/02-35396/answer.json
- run: f1-engine-2026-11-01
  step: apply
  outcome: stop
  detail: 'material 100860 (бр. 12/2016): 4 check exception(s) after the operations, first label_text_mismatch at line 144: continuation on a line that opens like a provision: ''a) регистрираната техника на територията'''
  evidence:
  - data/runs/f1-engine-2026-11-01/ustroystven-pravilnik-na-oblastnite-direktsii-zemedelie/apply/06-100860/checks.json
- run: f1-engine-2026-11-01
  step: apply
  outcome: stop
  detail: 'material 147660 (бр. 40/2020): the answer is refused: §3.4 replace_words: the words ''МЗХ'' occur 2 times at the address; the instruction does not say навсякъде'
  evidence:
  - data/runs/f1-engine-2026-11-01/ustroystven-pravilnik-na-oblastnite-direktsii-zemedelie/apply/08-147660/answer.json
- run: f1-engine-2026-11-01
  step: apply
  outcome: stop
  detail: 'material 202430 (бр. 3/2024): the answer is refused: §5.3 replace_words: ''Приложение към чл. 6, ал. 2, ред „Областна дирекция „Земеделие“ – Велико Търново“'' names 0 place(s) in the act'
  evidence:
  - data/runs/f1-engine-2026-11-01/ustroystven-pravilnik-na-oblastnite-direktsii-zemedelie/apply/12-202430/answer.json
- run: f1-engine-2026-11-01
  step: apply
  outcome: done
  detail: '12 material(s) applied, operations {''replace_annex'': 4, ''no_text_change'': 38, ''replace_provision'': 15, ''insert_provision'': 13, ''renumber'': 53, ''replace_words'': 92, ''delete_words'': 2, ''repeal'': 16, ''insert_words'': 8}'
  evidence:
  - data/runs/f1-engine-2026-11-01/ustroystven-pravilnik-na-oblastnite-direktsii-zemedelie/apply.json
- run: f1-engine-2026-11-01
  step: witnesses
  outcome: stop
  detail: 'the settler found our reading wrong (reading_error): lexbg: 73 difference(s), settled reading_error 24, same_text_other_form 46, witness_error 3; moj: absent (the portal answers 500 for https://justice.government.bg/home/normdoc/2135659679 (absent, 2026-11-01T12:49:16+00:00))'
  evidence:
  - data/runs/f1-engine-2026-11-01/ustroystven-pravilnik-na-oblastnite-direktsii-zemedelie/witness-diff.json
  - data/runs/f1-engine-2026-11-01/ustroystven-pravilnik-na-oblastnite-direktsii-zemedelie/witness-record.json
run: f1-engine-2026-11-01
record: data/runs/route-ledger/ustroystven-pravilnik-na-oblastnite-direktsii-zemedelie.json
date: '2026-11-01'
---

## Lessons learnt

(not yet written)

## Proposal

(not yet written)

## The owner's ruling

(not yet given)
