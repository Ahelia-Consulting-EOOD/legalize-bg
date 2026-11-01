---
act: pravilnik-za-prilagane-na-zakona-za-zashtita-na-litsa-zastrasheni-vav-vrazka-s-n
title: Правилник за прилагане на Закона за защита на лица, застрашени във връзка с наказателно производство
route: history
stopped_at: write
exception: 'the write path refused the act: pravilnik-za-prilagane-na-zakona-za-zashtita-na-litsa-zastrasheni-vav-vrazka-s-n: the body rebuilt from the chain''s operations differs from the run''s applied.md'
tried:
- run: f1-engine-2026-11-01
  step: chain
  outcome: done
  detail: 2 material(s) change the act after бр. 94/2018; lex.bg names 2 issue(s), 0 unexplained (none), 0 the Gazette adds (none); 0 court decision(s) name the act
  evidence:
  - data/runs/f1-engine-2026-11-01/pravilnik-za-prilagane-na-zakona-za-zashtita-na-litsa-zastrasheni-vav-vrazka-s-n/chain.json
- run: f1-engine-2026-11-01
  step: fetch_material
  outcome: done
  detail: material 131916 of бр. 94/2018 (cached), sha256 cbd101b1b67a
  evidence:
  - data/runs/f1-engine-2026-11-01/pravilnik-za-prilagane-na-zakona-za-zashtita-na-litsa-zastrasheni-vav-vrazka-s-n/material.json
- run: f1-engine-2026-11-01
  step: prepare
  outcome: done
  detail: 277 blocks, 9 sections
  evidence:
  - data/runs/f1-engine-2026-11-01/pravilnik-za-prilagane-na-zakona-za-zashtita-na-litsa-zastrasheni-vav-vrazka-s-n/blocks.json
- run: f1-engine-2026-11-01
  step: label
  outcome: done
  detail: 'round 0 collected: 7 exception(s), 1 source finding(s)'
  evidence:
  - data/runs/f1-engine-2026-11-01/pravilnik-za-prilagane-na-zakona-za-zashtita-na-litsa-zastrasheni-vav-vrazka-s-n/report-round0.json
- run: f1-engine-2026-11-01
  step: ladder
  outcome: done
  detail: no residue after round 1
  evidence:
  - data/runs/f1-engine-2026-11-01/pravilnik-za-prilagane-na-zakona-za-zashtita-na-litsa-zastrasheni-vav-vrazka-s-n/ladder.json
  - data/runs/f1-engine-2026-11-01/pravilnik-za-prilagane-na-zakona-za-zashtita-na-litsa-zastrasheni-vav-vrazka-s-n/report-round1.json
- run: f1-engine-2026-11-01
  step: content_check
  outcome: done
  detail: 'no lost text, no exception; source findings {''malformed_head'': 1}'
  evidence:
  - data/runs/f1-engine-2026-11-01/pravilnik-za-prilagane-na-zakona-za-zashtita-na-litsa-zastrasheni-vav-vrazka-s-n/content-check.json
- run: f1-engine-2026-11-01
  step: apply
  outcome: stop
  detail: 'material 147261 (бр. 31/2020): the answer is refused: §1.1.а insert_provision: ''чл. 29, ал. 2, т. 17'' names 2 place(s) in the act'
  evidence:
  - data/runs/f1-engine-2026-11-01/pravilnik-za-prilagane-na-zakona-za-zashtita-na-litsa-zastrasheni-vav-vrazka-s-n/apply/01-147261/answer.json
- run: f1-engine-2026-11-01
  step: apply
  outcome: stop
  detail: 'material 165363 (бр. 100/2021): the answer is refused: §25.1: punctuation is before or after, for delete_words only'
  evidence:
  - data/runs/f1-engine-2026-11-01/pravilnik-za-prilagane-na-zakona-za-zashtita-na-litsa-zastrasheni-vav-vrazka-s-n/apply/02-165363/answer.json
- run: f1-engine-2026-11-01
  step: apply
  outcome: stop
  detail: 'material 165363 (бр. 100/2021): the answer is refused: §18.3 replace_words: ''чл. 25, ал. 3, т. 4'' names 0 place(s) in the act'
  evidence:
  - data/runs/f1-engine-2026-11-01/pravilnik-za-prilagane-na-zakona-za-zashtita-na-litsa-zastrasheni-vav-vrazka-s-n/apply/02-165363/answer.json
- run: f1-engine-2026-11-01
  step: label
  outcome: done
  detail: 'round 0 collected: 0 exception(s), 1 source finding(s)'
  evidence:
  - data/runs/f1-engine-2026-11-01/pravilnik-za-prilagane-na-zakona-za-zashtita-na-litsa-zastrasheni-vav-vrazka-s-n/report-round0.json
- run: f1-engine-2026-11-01
  step: ladder
  outcome: done
  detail: no residue after round 0
  evidence:
  - data/runs/f1-engine-2026-11-01/pravilnik-za-prilagane-na-zakona-za-zashtita-na-litsa-zastrasheni-vav-vrazka-s-n/ladder.json
  - data/runs/f1-engine-2026-11-01/pravilnik-za-prilagane-na-zakona-za-zashtita-na-litsa-zastrasheni-vav-vrazka-s-n/report-round0.json
- run: f1-engine-2026-11-01
  step: content_check
  outcome: done
  detail: 'no lost text, no exception; source findings {''malformed_head'': 1}'
  evidence:
  - data/runs/f1-engine-2026-11-01/pravilnik-za-prilagane-na-zakona-za-zashtita-na-litsa-zastrasheni-vav-vrazka-s-n/content-check.json
- run: f1-engine-2026-11-01
  step: apply
  outcome: done
  detail: '2 material(s) applied, operations {''no_text_change'': 27, ''insert_provision'': 18, ''renumber'': 4, ''replace_provision'': 17, ''insert_words'': 4, ''replace_words'': 76, ''delete_words'': 6, ''replace_heading'': 2, ''repeal'': 4}'
  evidence:
  - data/runs/f1-engine-2026-11-01/pravilnik-za-prilagane-na-zakona-za-zashtita-na-litsa-zastrasheni-vav-vrazka-s-n/apply.json
- run: f1-engine-2026-11-01
  step: apply
  outcome: done
  detail: '2 material(s) applied, operations {''no_text_change'': 27, ''insert_provision'': 18, ''renumber'': 4, ''replace_provision'': 17, ''insert_words'': 4, ''replace_words'': 76, ''delete_words'': 6, ''replace_heading'': 2, ''repeal'': 4}'
  evidence:
  - data/runs/f1-engine-2026-11-01/pravilnik-za-prilagane-na-zakona-za-zashtita-na-litsa-zastrasheni-vav-vrazka-s-n/apply.json
- run: f1-engine-2026-11-01
  step: witnesses
  outcome: stop
  detail: 'the settler found our reading wrong (reading_error): lexbg: 19 difference(s), settled reading_error 2, same_text_other_form 15, witness_error 2; moj: absent (the portal answers 500 for https://justice.government.bg/home/normdoc/2137188264 (absent, 2026-11-01T11:42:36+00:00))'
  evidence:
  - data/runs/f1-engine-2026-11-01/pravilnik-za-prilagane-na-zakona-za-zashtita-na-litsa-zastrasheni-vav-vrazka-s-n/witness-diff.json
  - data/runs/f1-engine-2026-11-01/pravilnik-za-prilagane-na-zakona-za-zashtita-na-litsa-zastrasheni-vav-vrazka-s-n/witness-record.json
- run: f1-engine-2026-11-01
  step: apply
  outcome: done
  detail: '2 material(s) applied, operations {''no_text_change'': 27, ''insert_provision'': 18, ''renumber'': 4, ''replace_provision'': 17, ''insert_words'': 4, ''replace_words'': 76, ''delete_words'': 6, ''replace_heading'': 2, ''repeal'': 4}'
  evidence:
  - data/runs/f1-engine-2026-11-01/pravilnik-za-prilagane-na-zakona-za-zashtita-na-litsa-zastrasheni-vav-vrazka-s-n/apply.json
- run: f1-engine-2026-11-01
  step: apply
  outcome: done
  detail: '2 material(s) applied, operations {''no_text_change'': 27, ''insert_provision'': 18, ''renumber'': 4, ''replace_provision'': 17, ''insert_words'': 4, ''replace_words'': 76, ''delete_words'': 6, ''replace_heading'': 2, ''repeal'': 4}'
  evidence:
  - data/runs/f1-engine-2026-11-01/pravilnik-za-prilagane-na-zakona-za-zashtita-na-litsa-zastrasheni-vav-vrazka-s-n/apply.json
- run: f1-engine-2026-11-01
  step: witnesses
  outcome: done
  detail: 'lexbg: 17 difference(s), settled same_text_other_form 15, witness_error 2; moj: absent (the portal answers 500 for https://justice.government.bg/home/normdoc/2137188264 (absent, 2026-11-01T11:42:36+00:00))'
  evidence:
  - data/runs/f1-engine-2026-11-01/pravilnik-za-prilagane-na-zakona-za-zashtita-na-litsa-zastrasheni-vav-vrazka-s-n/witness-diff.json
  - data/runs/f1-engine-2026-11-01/pravilnik-za-prilagane-na-zakona-za-zashtita-na-litsa-zastrasheni-vav-vrazka-s-n/witness-record.json
- run: f1-engine-2026-11-01
  step: write
  outcome: stop
  detail: 'the write path refused the act: pravilnik-za-prilagane-na-zakona-za-zashtita-na-litsa-zastrasheni-vav-vrazka-s-n: the body rebuilt from the chain''s operations differs from the run''s applied.md'
  evidence: []
run: f1-engine-2026-11-01
record: data/runs/route-ledger/pravilnik-za-prilagane-na-zakona-za-zashtita-na-litsa-zastrasheni-vav-vrazka-s-n.json
date: '2026-11-01'
superseded: the act went on in run f1-engine-2026-11-01
resolved: 62d2f4a0d
---

## Lessons learnt

(not yet written)

## Proposal

(not yet written)

## The owner's ruling

(not yet given)
