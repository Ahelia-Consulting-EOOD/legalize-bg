# Apply the amending material of ДВ бр. 41/2022 to ustroystven-pravilnik-na-oblastnite-direktsii-zemedelie

You read the instructions of an amending act and turn each into operations on the act's text, in the form below. You never retype the act's words: a new text is a reference to the quoted blocks (their indices), an old or new string is a reference to a quoted segment of the instruction (q1, q2, … in order of appearance), an address is written as the Gazette writes it („чл. 36, ал. 1, т. 5“, „§ 3“, „глава втора, раздел V“, „Приложение № 3“, „наименованието“). An instruction that changes no text of this act (entry into force, a transitional rule, an instruction aimed at another act) is `no_text_change`. An instruction that changes this act's text in a way you cannot express in the closed set is `outside_set` with a note that says what it does: the script stops the act for the owner.

Kinds: `replace_provision`: the addressed provision (article, alinea, item, letter, §) is replaced whole by the quoted text (blocks); `replace_words`: inside the addressed provision the words old are replaced by new; everywhere: true when the instruction says „навсякъде“; `delete_words`: inside the addressed provision the words old are deleted; `insert_words`: inside the addressed provision new is inserted after the words anchor, or at the end (where: end) or the start (where: start); `insert_provision`: a new provision (blocks) is inserted after the sibling named by after, at the address it will carry; `repeal`: the addressed provision is repealed: its number stays with the repeal marker, its text and children go; `renumber`: the addressed provision becomes the number in to (досегашната ал. 2 става ал. 3); `replace_heading`: the addressed heading, or the act's title (address наименованието), takes the words in new (a quoted segment or blocks); `insert_heading`: a new heading (blocks) is inserted after the provision or heading named by after; `replace_annex`: the annex named by address is replaced whole by the quoted blocks; `insert_annex`: a new annex (blocks) is appended after the annex named by after, or at the end of the act; `repeal_annex`: the annex named by address is repealed: its heading stays with the repeal marker, its rows go; `corrigendum`: a corrigendum: inside the addressed provision the words old are replaced by new, marked Попр.; `no_text_change`: the instruction changes no text of this act (entry into force, a transitional rule, an instruction for another act); `outside_set`: the instruction changes this act's text in a way none of the kinds above expresses; the note says what it does, and the script stops the act for the owner.

Write exactly one JSON object to `data/runs/f1-engine-2026-11-01/ustroystven-pravilnik-na-oblastnite-direktsii-zemedelie/apply/11-173772/answer.json`: {"material": <id>, "operations": [...]}, one or more operations per instruction id, in the material's order; nothing else, no prose, no code fence. Each operation is an object with these keys and no others: `id` (the instruction id as written above, e.g. "§3.1"), `kind` (one of the kinds), `address` (the provision, in the Gazette's grammar; not for no_text_change), and by kind: `blocks` ([first, last] block indices of the quoted text, for replace_provision, insert_provision, insert_heading, replace_annex, insert_annex, or replace_heading with quoted blocks), `after` (the sibling the new text follows, for the insert kinds), `old` and `new` (segment references like "q1", for replace_words, delete_words, corrigendum, insert_words, replace_heading), `anchor` and `where` (after | before | end | start, for insert_words), `to` (the new number, for renumber), `everywhere` (true when the instruction says навсякъде, for replace_words), `note` (free text, required for outside_set). Where the Gazette's nested quotation marks cut a segment short (q1 ends before the inner quote), give `old`, `new` or `anchor` as {"text": "…"} with the words copied exactly from the instruction line above, quotation marks included; the script checks they stand there. Example: {"id": "§1.1", "kind": "replace_words", "address": "чл. 36, ал. 1", "old": "q1", "new": "q2"}.

## The instructions
### §1 (block 3, section body)
§ 1. В приложението към чл. 6, ал. 2 се правят следните изменения:
- current text at „чл. 6, ал. 2“:
    (2) Числеността на персонала на съответната областна дирекция е посочена в приложението.

### §1.1 (block 4, section body)
1. На ред „Областна дирекция „Земеделие“ – Видин“ числото „62“ се заменя с „59“.
- q1: „Земеделие“
- q2: „62“
- q3: „59“

### §1.2 (block 5, section body)
2. На ред „Областна дирекция „Земеделие“ – Ловеч“ числото „56“ се заменя с „57“.
- q1: „Земеделие“
- q2: „56“
- q3: „57“

### §1.3 (block 6, section body)
3. На ред „Областна дирекция „Земеделие“ – Русе“ числото „53“ се заменя с „52“.
- q1: „Земеделие“
- q2: „53“
- q3: „52“

### §1.4 (block 7, section body)
4. На ред „Областна дирекция „Земеделие“ – Силистра“ числото „54“ се заменя с „57“.
- q1: „Земеделие“
- q2: „54“
- q3: „57“

### §2 (block 8, section body)
§ 2. Навсякъде в правилника думите „министъра на земеделието, храните и горите“, „Министерството на земеделието, храните и горите“ и абревиатурата „МЗХГ“ се заменят съответно с „министъра на земеделието“, „Министерството на земеделието“ и „МЗм“.
- q1: „министъра на земеделието, храните и горите“
- q2: „Министерството на земеделието, храните и горите“
- q3: „МЗХГ“
- q4: „министъра на земеделието“
- q5: „Министерството на земеделието“
- q6: „МЗм“

### §3 (block 10, section final)
§ 3. Правилникът влиза в сила от деня на обнародването му в „Държавен вестник“.
- q1: „Държавен вестник“
