---
act: zakon-za-ekstraditsiyata-i-evropeyskata-zapoved-za-arest
title: Закон за екстрадицията и Европейската заповед за арест
route: history
stopped_at: witnesses
exception: 'the settler found our reading wrong (reading_error): lexbg: 205 difference(s), settled reading_error 5, same_text_other_form 196, source_error 2, witness_error 2; moj: absent (the portal answers 500 for https://justice.government.bg/home/normdoc/2135504378 (absent, 2026-11-01T12:45:02+00:00))'
tried:
- run: f1-engine-2026-11-01
  step: chain
  outcome: done
  detail: 12 material(s) change the act after бр. 46/2005; lex.bg names 12 issue(s), 0 unexplained (none), 0 the Gazette adds (none); 0 court decision(s) name the act
  evidence:
  - data/runs/f1-engine-2026-11-01/zakon-za-ekstraditsiyata-i-evropeyskata-zapoved-za-arest/chain.json
- run: f1-engine-2026-11-01
  step: fetch_material
  outcome: done
  detail: material 385 of бр. 46/2005 (cached), sha256 b5f4f8991bc0
  evidence:
  - data/runs/f1-engine-2026-11-01/zakon-za-ekstraditsiyata-i-evropeyskata-zapoved-za-arest/material.json
- run: f1-engine-2026-11-01
  step: prepare
  outcome: done
  detail: 546 blocks, 17 sections
  evidence:
  - data/runs/f1-engine-2026-11-01/zakon-za-ekstraditsiyata-i-evropeyskata-zapoved-za-arest/blocks.json
- run: f1-engine-2026-11-01
  step: label
  outcome: done
  detail: 'round 0 collected: 2 exception(s), 0 source finding(s)'
  evidence:
  - data/runs/f1-engine-2026-11-01/zakon-za-ekstraditsiyata-i-evropeyskata-zapoved-za-arest/report-round0.json
- run: f1-engine-2026-11-01
  step: ladder
  outcome: done
  detail: no residue after round 1
  evidence:
  - data/runs/f1-engine-2026-11-01/zakon-za-ekstraditsiyata-i-evropeyskata-zapoved-za-arest/ladder.json
  - data/runs/f1-engine-2026-11-01/zakon-za-ekstraditsiyata-i-evropeyskata-zapoved-za-arest/report-round1.json
- run: f1-engine-2026-11-01
  step: content_check
  outcome: done
  detail: no lost text, no exception; source findings none
  evidence:
  - data/runs/f1-engine-2026-11-01/zakon-za-ekstraditsiyata-i-evropeyskata-zapoved-za-arest/content-check.json
- run: f1-engine-2026-11-01
  step: ladder
  outcome: done
  detail: no residue after round 1
  evidence:
  - data/runs/f1-engine-2026-11-01/zakon-za-ekstraditsiyata-i-evropeyskata-zapoved-za-arest/ladder.json
  - data/runs/f1-engine-2026-11-01/zakon-za-ekstraditsiyata-i-evropeyskata-zapoved-za-arest/report-round1.json
- run: f1-engine-2026-11-01
  step: content_check
  outcome: done
  detail: no lost text, no exception; source findings none
  evidence:
  - data/runs/f1-engine-2026-11-01/zakon-za-ekstraditsiyata-i-evropeyskata-zapoved-za-arest/content-check.json
- run: f1-engine-2026-11-01
  step: label
  outcome: done
  detail: 'round 0 collected: 1 exception(s), 0 source finding(s)'
  evidence:
  - data/runs/f1-engine-2026-11-01/zakon-za-ekstraditsiyata-i-evropeyskata-zapoved-za-arest/report-round0.json
- run: f1-engine-2026-11-01
  step: ladder
  outcome: done
  detail: no residue after round 1
  evidence:
  - data/runs/f1-engine-2026-11-01/zakon-za-ekstraditsiyata-i-evropeyskata-zapoved-za-arest/ladder.json
  - data/runs/f1-engine-2026-11-01/zakon-za-ekstraditsiyata-i-evropeyskata-zapoved-za-arest/report-round1.json
- run: f1-engine-2026-11-01
  step: content_check
  outcome: done
  detail: no lost text, no exception; source findings none
  evidence:
  - data/runs/f1-engine-2026-11-01/zakon-za-ekstraditsiyata-i-evropeyskata-zapoved-za-arest/content-check.json
- run: f1-engine-2026-11-01
  step: ladder
  outcome: done
  detail: no residue after round 1
  evidence:
  - data/runs/f1-engine-2026-11-01/zakon-za-ekstraditsiyata-i-evropeyskata-zapoved-za-arest/ladder.json
  - data/runs/f1-engine-2026-11-01/zakon-za-ekstraditsiyata-i-evropeyskata-zapoved-za-arest/report-round1.json
- run: f1-engine-2026-11-01
  step: apply
  outcome: stop
  detail: 'material 34181 (бр. 49/2010): the answer is refused: §3.2: replace_provision needs blocks [first, last]'
  evidence:
  - data/runs/f1-engine-2026-11-01/zakon-za-ekstraditsiyata-i-evropeyskata-zapoved-za-arest/apply/03-34181/answer.json
- run: f1-engine-2026-11-01
  step: apply
  outcome: stop
  detail: 'material 34181 (бр. 49/2010): the answer is refused: §8.1 insert_provision: the provision has 2 sentence(s); the new one would be number 3, the address names 2'
  evidence:
  - data/runs/f1-engine-2026-11-01/zakon-za-ekstraditsiyata-i-evropeyskata-zapoved-za-arest/apply/03-34181/answer.json
- run: f1-engine-2026-11-01
  step: apply
  outcome: stop
  detail: 'material 34181 (бр. 49/2010): the answer is refused: §9.1 insert_provision: the provision has 1 sentence(s); a new one can be number 1 to 2, the address names 3'
  evidence:
  - data/runs/f1-engine-2026-11-01/zakon-za-ekstraditsiyata-i-evropeyskata-zapoved-za-arest/apply/03-34181/answer.json
- run: f1-engine-2026-11-01
  step: apply
  outcome: stop
  detail: 'material 54416 (бр. 55/2011): the answer is refused: §9 replace_provision: the annex reference in ''Приложение към чл. 37, ал. 1, буква (d)'' is not a provision the grammar reads: ''чл. 37, ал. 1, буква (d)'''
  evidence:
  - data/runs/f1-engine-2026-11-01/zakon-za-ekstraditsiyata-i-evropeyskata-zapoved-za-arest/apply/04-54416/answer.json
- run: f1-engine-2026-11-01
  step: apply
  outcome: done
  detail: '12 material(s) applied, operations {''no_text_change'': 30, ''replace_words'': 15, ''insert_words'': 10, ''insert_provision'': 32, ''replace_provision'': 14, ''repeal'': 2, ''renumber'': 10, ''delete_words'': 2, ''replace_sentence'': 2}'
  evidence:
  - data/runs/f1-engine-2026-11-01/zakon-za-ekstraditsiyata-i-evropeyskata-zapoved-za-arest/apply.json
- run: f1-engine-2026-11-01
  step: apply
  outcome: done
  detail: '12 material(s) applied, operations {''no_text_change'': 30, ''replace_words'': 15, ''insert_words'': 10, ''insert_provision'': 32, ''replace_provision'': 14, ''repeal'': 2, ''renumber'': 10, ''delete_words'': 2, ''replace_sentence'': 2}'
  evidence:
  - data/runs/f1-engine-2026-11-01/zakon-za-ekstraditsiyata-i-evropeyskata-zapoved-za-arest/apply.json
- run: f1-engine-2026-11-01
  step: witnesses
  outcome: stop
  detail: 'the settler found our reading wrong (reading_error): lexbg: 205 difference(s), settled reading_error 5, same_text_other_form 196, source_error 2, witness_error 2; moj: absent (the portal answers 500 for https://justice.government.bg/home/normdoc/2135504378 (absent, 2026-11-01T12:45:02+00:00))'
  evidence:
  - data/runs/f1-engine-2026-11-01/zakon-za-ekstraditsiyata-i-evropeyskata-zapoved-za-arest/witness-diff.json
  - data/runs/f1-engine-2026-11-01/zakon-za-ekstraditsiyata-i-evropeyskata-zapoved-za-arest/witness-record.json
run: f1-engine-2026-11-01
record: data/runs/route-ledger/zakon-za-ekstraditsiyata-i-evropeyskata-zapoved-za-arest.json
date: '2026-11-01'
---

## Lessons learnt

(not yet written)

## Proposal

(not yet written)

## The owner's ruling

(not yet given)
