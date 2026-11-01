---
act: semeen-kodeks
title: Семеен кодекс
route: history
stopped_at: apply
exception: 'material 201987 (бр. 106/2023): the answer is refused: §8.6 replace_provision: ''чл. 84, ал. 6'' names 2 place(s) in the act'
tried:
- run: f1-engine-2026-11-01
  step: chain
  outcome: done
  detail: 16 material(s) change the act after бр. 47/2009; lex.bg names 16 issue(s), 1 unexplained (101/2019), 0 the Gazette adds (none); 0 court decision(s) name the act
  evidence:
  - data/runs/f1-engine-2026-11-01/semeen-kodeks/chain.json
- run: f1-engine-2026-11-01
  step: fetch_material
  outcome: done
  detail: material 22498 of бр. 47/2009 (cached), sha256 a11059eab8cd
  evidence:
  - data/runs/f1-engine-2026-11-01/semeen-kodeks/material.json
- run: f1-engine-2026-11-01
  step: prepare
  outcome: done
  detail: 822 blocks, 29 sections
  evidence:
  - data/runs/f1-engine-2026-11-01/semeen-kodeks/blocks.json
- run: f1-engine-2026-11-01
  step: label
  outcome: done
  detail: 'round 0 collected: 0 exception(s), 0 source finding(s)'
  evidence:
  - data/runs/f1-engine-2026-11-01/semeen-kodeks/report-round0.json
- run: f1-engine-2026-11-01
  step: ladder
  outcome: done
  detail: no residue after round 0
  evidence:
  - data/runs/f1-engine-2026-11-01/semeen-kodeks/ladder.json
  - data/runs/f1-engine-2026-11-01/semeen-kodeks/report-round0.json
- run: f1-engine-2026-11-01
  step: content_check
  outcome: done
  detail: no lost text, no exception; source findings none
  evidence:
  - data/runs/f1-engine-2026-11-01/semeen-kodeks/content-check.json
- run: f1-engine-2026-11-01
  step: apply
  outcome: stop
  detail: 'material 41671 (бр. 100/2010): the answer is refused: §23 insert_provision: the new text opens as text None, the address names article ''127а'''
  evidence:
  - data/runs/f1-engine-2026-11-01/semeen-kodeks/apply/04-41671/answer.json
- run: f1-engine-2026-11-01
  step: label
  outcome: done
  detail: 'round 0 collected: 0 exception(s), 0 source finding(s)'
  evidence:
  - data/runs/f1-engine-2026-11-01/semeen-kodeks/report-round0.json
- run: f1-engine-2026-11-01
  step: ladder
  outcome: done
  detail: no residue after round 0
  evidence:
  - data/runs/f1-engine-2026-11-01/semeen-kodeks/ladder.json
  - data/runs/f1-engine-2026-11-01/semeen-kodeks/report-round0.json
- run: f1-engine-2026-11-01
  step: apply
  outcome: stop
  detail: 'material 41709 (бр. 100/2010): the answer is refused: §2 outside_set: outside the closed set of operations: After the words q1 („изцяло с лично имущество“) a full stop is placed and the rest of the alinea''s text to its end is deleted; the deleted tail is not quoted in the instruction, so no delete_words reference can name it.'
  evidence:
  - data/runs/f1-engine-2026-11-01/semeen-kodeks/apply/05-41709/answer.json
- run: f1-engine-2026-11-01
  step: apply
  outcome: stop
  detail: 'material 41709 (бр. 100/2010): the answer is refused: §4.2 insert_words: the anchor ''Социално подпомагане“'' occurs 0 times'
  evidence:
  - data/runs/f1-engine-2026-11-01/semeen-kodeks/apply/05-41709/answer.json
- run: f1-engine-2026-11-01
  step: apply
  outcome: stop
  detail: 'material 41709 (бр. 100/2010): the answer is refused: §5 delete_words: the words ''и'' occur 13 times at the address; the instruction does not say навсякъде'
  evidence:
  - data/runs/f1-engine-2026-11-01/semeen-kodeks/apply/05-41709/answer.json
- run: f1-engine-2026-11-01
  step: apply
  outcome: interrupted
  detail: ''
  evidence: []
- run: f1-engine-2026-11-01
  step: apply
  outcome: interrupted
  detail: ''
  evidence: []
- run: f1-engine-2026-11-01
  step: apply
  outcome: interrupted
  detail: ''
  evidence: []
- run: f1-engine-2026-11-01
  step: apply
  outcome: stop
  detail: 'material 135546 (бр. 24/2019): the answer is refused: §2.1 replace_words: the words ''приемно семейство, в специализирана институция, посочени от дирекция „Социално подпомагане“ или му се предоставя социална услуга – резидентен тип'' do not occur in ''(7) (Изм. и доп. - ДВ, бр. 100 от 2010 г.) По изкл'''
  evidence:
  - data/runs/f1-engine-2026-11-01/semeen-kodeks/apply/10-135546/answer.json
- run: f1-engine-2026-11-01
  step: apply
  outcome: stop
  detail: 'material 135546 (бр. 24/2019): the answer is refused: §2.4 replace_words: the words ''ръководителят на специализираната институция, в която е настанено детето, както и на институцията, предоставяща социалната услуга – резидентен тип'' do not occur in ''(2) (Изм. - ДВ, бр. 98 от 2010 г., Изм. и доп. - Д'''
  evidence:
  - data/runs/f1-engine-2026-11-01/semeen-kodeks/apply/10-135546/answer.json
- run: f1-engine-2026-11-01
  step: apply
  outcome: stop
  detail: 'material 197941 (бр. 67/2023): the answer is refused: §20 insert_provision: the new text opens as text None, the address names article ''127б'''
  evidence:
  - data/runs/f1-engine-2026-11-01/semeen-kodeks/apply/12-197941/answer.json
- run: f1-engine-2026-11-01
  step: prepare
  outcome: done
  detail: 822 blocks, 29 sections
  evidence:
  - data/runs/f1-engine-2026-11-01/semeen-kodeks/blocks.json
- run: f1-engine-2026-11-01
  step: label
  outcome: done
  detail: 'round 0 collected: 0 exception(s), 0 source finding(s)'
  evidence:
  - data/runs/f1-engine-2026-11-01/semeen-kodeks/report-round0.json
- run: f1-engine-2026-11-01
  step: ladder
  outcome: done
  detail: no residue after round 0
  evidence:
  - data/runs/f1-engine-2026-11-01/semeen-kodeks/ladder.json
  - data/runs/f1-engine-2026-11-01/semeen-kodeks/report-round0.json
- run: f1-engine-2026-11-01
  step: apply
  outcome: stop
  detail: 'material 197941 (бр. 67/2023): the answer is refused: §20 insert_provision: the new text opens as text None, the address names article ''127б'''
  evidence:
  - data/runs/f1-engine-2026-11-01/semeen-kodeks/apply/12-197941/answer.json
- run: f1-engine-2026-11-01
  step: apply
  outcome: stop
  detail: 'material 197941 (бр. 67/2023): the answer is refused: §20 insert_provision: ''чл. 127б'' names 0 place(s) in the act'
  evidence:
  - data/runs/f1-engine-2026-11-01/semeen-kodeks/apply/12-197941/answer.json
- run: f1-engine-2026-11-01
  step: apply
  outcome: stop
  detail: 'material 201987 (бр. 106/2023): the answer is refused: §8.6 replace_provision: ''чл. 84, ал. 6'' names 2 place(s) in the act'
  evidence:
  - data/runs/f1-engine-2026-11-01/semeen-kodeks/apply/13-201987/answer.json
- run: f1-engine-2026-11-01
  step: apply
  outcome: stop
  detail: 'material 201987 (бр. 106/2023): the answer is refused: §8.6 replace_provision: ''чл. 84, ал. 6'' names 2 place(s) in the act'
  evidence:
  - data/runs/f1-engine-2026-11-01/semeen-kodeks/apply/13-201987/answer.json
- run: f1-engine-2026-11-01
  step: apply
  outcome: stop
  detail: 'material 201987 (бр. 106/2023): the answer is refused: §8.6 replace_provision: ''чл. 84, ал. 6'' names 2 place(s) in the act'
  evidence:
  - data/runs/f1-engine-2026-11-01/semeen-kodeks/apply/13-201987/answer.json
run: f1-engine-2026-11-01
record: data/runs/route-ledger/semeen-kodeks.json
date: '2026-11-01'
---

## Lessons learnt

(not yet written)

## Proposal

(not yet written)

## The owner's ruling

(not yet given)
