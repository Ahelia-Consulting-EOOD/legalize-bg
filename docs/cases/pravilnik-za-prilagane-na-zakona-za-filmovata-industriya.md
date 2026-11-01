---
act: pravilnik-za-prilagane-na-zakona-za-filmovata-industriya
title: Правилник за прилагане на Закона за филмовата индустрия
route: history
stopped_at: apply
exception: 'material 160733 (бр. 67/2021): the answer is refused: §34 insert_words: the anchor ''филма'' occurs 2 times'
tried:
- run: f1-engine-2026-11-01
  step: chain
  outcome: done
  detail: 3 material(s) change the act after бр. 102/2018; lex.bg names 3 issue(s), 0 unexplained (none), 0 the Gazette adds (none); 0 court decision(s) name the act
  evidence:
  - data/runs/f1-engine-2026-11-01/pravilnik-za-prilagane-na-zakona-za-filmovata-industriya/chain.json
- run: f1-engine-2026-11-01
  step: fetch_material
  outcome: done
  detail: material 132829 of бр. 102/2018 (cached), sha256 0a99cded559d
  evidence:
  - data/runs/f1-engine-2026-11-01/pravilnik-za-prilagane-na-zakona-za-filmovata-industriya/material.json
- run: f1-engine-2026-11-01
  step: prepare
  outcome: done
  detail: 521 blocks, 14 sections
  evidence:
  - data/runs/f1-engine-2026-11-01/pravilnik-za-prilagane-na-zakona-za-filmovata-industriya/blocks.json
- run: f1-engine-2026-11-01
  step: label
  outcome: done
  detail: 'round 0 collected: 27 exception(s), 17 source finding(s)'
  evidence:
  - data/runs/f1-engine-2026-11-01/pravilnik-za-prilagane-na-zakona-za-filmovata-industriya/report-round0.json
- run: f1-engine-2026-11-01
  step: label
  outcome: done
  detail: 'round 0 collected: 1 exception(s), 17 source finding(s)'
  evidence:
  - data/runs/f1-engine-2026-11-01/pravilnik-za-prilagane-na-zakona-za-filmovata-industriya/report-round0.json
- run: f1-engine-2026-11-01
  step: ladder
  outcome: done
  detail: no residue after round 1
  evidence:
  - data/runs/f1-engine-2026-11-01/pravilnik-za-prilagane-na-zakona-za-filmovata-industriya/ladder.json
  - data/runs/f1-engine-2026-11-01/pravilnik-za-prilagane-na-zakona-za-filmovata-industriya/report-round1.json
- run: f1-engine-2026-11-01
  step: content_check
  outcome: stop
  detail: 'lost text (empty_section), first at block 502: heading with no body before block 503; the act is on the list with the route investigate (D-076)'
  evidence:
  - data/runs/f1-engine-2026-11-01/pravilnik-za-prilagane-na-zakona-za-filmovata-industriya/content-check.json
- run: f1-engine-2026-11-01
  step: ladder
  outcome: done
  detail: no residue after round 1
  evidence:
  - data/runs/f1-engine-2026-11-01/pravilnik-za-prilagane-na-zakona-za-filmovata-industriya/ladder.json
  - data/runs/f1-engine-2026-11-01/pravilnik-za-prilagane-na-zakona-za-filmovata-industriya/report-round1.json
- run: f1-engine-2026-11-01
  step: content_check
  outcome: done
  detail: 'no lost text, no exception; source findings {''malformed_head'': 1, ''annex_in_pdf'': 16}'
  evidence:
  - data/runs/f1-engine-2026-11-01/pravilnik-za-prilagane-na-zakona-za-filmovata-industriya/content-check.json
- run: f1-engine-2026-11-01
  step: apply
  outcome: stop
  detail: 'material 160733 (бр. 67/2021): the answer is refused: §2.1 insert_words: the anchor ''наричан по-нататък Регламент (ЕС) 2017/1084'' occurs 0 times'
  evidence:
  - data/runs/f1-engine-2026-11-01/pravilnik-za-prilagane-na-zakona-za-filmovata-industriya/apply/01-160733/answer.json
- run: f1-engine-2026-11-01
  step: apply
  outcome: stop
  detail: 'material 160733 (бр. 67/2021): the answer is refused: §2.1 insert_words: the anchor ''наричан по-нататък Регламент (ЕС) 2017/1084'' occurs 0 times'
  evidence:
  - data/runs/f1-engine-2026-11-01/pravilnik-za-prilagane-na-zakona-za-filmovata-industriya/apply/01-160733/answer.json
- run: f1-engine-2026-11-01
  step: apply
  outcome: stop
  detail: 'material 160733 (бр. 67/2021): the answer is refused: §2.2.б insert_provision: ''т. 1'' names 44 place(s) in the act'
  evidence:
  - data/runs/f1-engine-2026-11-01/pravilnik-za-prilagane-na-zakona-za-filmovata-industriya/apply/01-160733/answer.json
- run: f1-engine-2026-11-01
  step: apply
  outcome: stop
  detail: 'material 160733 (бр. 67/2021): the answer is refused: §8.3 replace_provision: the new text carries the number ''3'', the address ''4'''
  evidence:
  - data/runs/f1-engine-2026-11-01/pravilnik-za-prilagane-na-zakona-za-filmovata-industriya/apply/01-160733/answer.json
- run: f1-engine-2026-11-01
  step: apply
  outcome: stop
  detail: 'material 160733 (бр. 67/2021): the answer is refused: §12 replace_heading: ''раздел II'' names 4 place(s) in the act'
  evidence:
  - data/runs/f1-engine-2026-11-01/pravilnik-za-prilagane-na-zakona-za-filmovata-industriya/apply/01-160733/answer.json
- run: f1-engine-2026-11-01
  step: apply
  outcome: stop
  detail: 'material 160733 (бр. 67/2021): the answer is refused: §17 insert_heading: ''глава втора „а“'' names 0 place(s) in the act'
  evidence:
  - data/runs/f1-engine-2026-11-01/pravilnik-za-prilagane-na-zakona-za-filmovata-industriya/apply/01-160733/answer.json
- run: f1-engine-2026-11-01
  step: apply
  outcome: stop
  detail: 'material 160733 (бр. 67/2021): the answer is refused: §21 delete_words: ''наименованието на глава четвърта'' names a title, and the provision has none'
  evidence:
  - data/runs/f1-engine-2026-11-01/pravilnik-za-prilagane-na-zakona-za-filmovata-industriya/apply/01-160733/answer.json
- run: f1-engine-2026-11-01
  step: apply
  outcome: stop
  detail: 'material 160733 (бр. 67/2021): the answer is refused: §21 delete_words: the words ''на филми'' occur 0 times in the title ''Глава четвърта НАЦИОНАЛНА КОМИСИЯ ПО КАТЕГОРИЗАЦИЯ НА ФИЛМИ'''
  evidence:
  - data/runs/f1-engine-2026-11-01/pravilnik-za-prilagane-na-zakona-za-filmovata-industriya/apply/01-160733/answer.json
- run: f1-engine-2026-11-01
  step: apply
  outcome: stop
  detail: 'material 160733 (бр. 67/2021): the answer is refused: §34 insert_words: the anchor ''филма'' occurs 2 times'
  evidence:
  - data/runs/f1-engine-2026-11-01/pravilnik-za-prilagane-na-zakona-za-filmovata-industriya/apply/01-160733/answer.json
run: f1-engine-2026-11-01
record: data/runs/route-ledger/pravilnik-za-prilagane-na-zakona-za-filmovata-industriya.json
date: '2026-11-01'
---

## Lessons learnt

(not yet written)

## Proposal

(not yet written)

## The owner's ruling

(not yet given)
