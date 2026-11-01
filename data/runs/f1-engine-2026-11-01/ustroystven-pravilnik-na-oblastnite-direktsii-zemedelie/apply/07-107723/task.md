# Apply the amending material of ДВ бр. 75/2016 to ustroystven-pravilnik-na-oblastnite-direktsii-zemedelie

You read the instructions of an amending act and turn each into operations on the act's text, in the form below. You never retype the act's words: a new text is a reference to the quoted blocks (their indices), an old or new string is a reference to a quoted segment of the instruction (q1, q2, … in order of appearance), an address is written as the Gazette writes it („чл. 36, ал. 1, т. 5“, „§ 3“, „глава втора, раздел V“, „Приложение № 3“, „наименованието“). An instruction that changes no text of this act (entry into force, a transitional rule, an instruction aimed at another act) is `no_text_change`. An instruction that changes this act's text in a way you cannot express in the closed set is `outside_set` with a note that says what it does: the script stops the act for the owner.

Kinds: `replace_provision`: the addressed provision (article, alinea, item, letter, §) is replaced whole by the quoted text (blocks); `replace_words`: inside the addressed provision the words old are replaced by new; everywhere: true when the instruction says „навсякъде“; `delete_words`: inside the addressed provision the words old are deleted; `insert_words`: inside the addressed provision new is inserted after the words anchor, or at the end (where: end) or the start (where: start); `insert_provision`: a new provision (blocks) is inserted after the sibling named by after, at the address it will carry; `repeal`: the addressed provision is repealed: its number stays with the repeal marker, its text and children go; `renumber`: the addressed provision becomes the number in to (досегашната ал. 2 става ал. 3); `replace_heading`: the addressed heading, or the act's title (address наименованието), takes the words in new (a quoted segment or blocks); `insert_heading`: a new heading (blocks) is inserted after the provision or heading named by after; `replace_annex`: the annex named by address is replaced whole by the quoted blocks; `insert_annex`: a new annex (blocks) is appended after the annex named by after, or at the end of the act; `repeal_annex`: the annex named by address is repealed: its heading stays with the repeal marker, its rows go; `corrigendum`: a corrigendum: inside the addressed provision the words old are replaced by new, marked Попр.; `no_text_change`: the instruction changes no text of this act (entry into force, a transitional rule, an instruction for another act); `outside_set`: the instruction changes this act's text in a way none of the kinds above expresses; the note says what it does, and the script stops the act for the owner.

Write exactly one JSON object to `data/runs/f1-engine-2026-11-01/ustroystven-pravilnik-na-oblastnite-direktsii-zemedelie/apply/07-107723/answer.json`: {"material": <id>, "operations": [...]}, one or more operations per instruction id, in the material's order; nothing else, no prose, no code fence. Each operation is an object with these keys and no others: `id` (the instruction id as written above, e.g. "§3.1"), `kind` (one of the kinds), `address` (the provision, in the Gazette's grammar; not for no_text_change), and by kind: `blocks` ([first, last] block indices of the quoted text, for replace_provision, insert_provision, insert_heading, replace_annex, insert_annex, or replace_heading with quoted blocks), `after` (the sibling the new text follows, for the insert kinds), `old` and `new` (segment references like "q1", for replace_words, delete_words, corrigendum, insert_words, replace_heading), `anchor` and `where` (after | before | end | start, for insert_words), `to` (the new number, for renumber), `everywhere` (true when the instruction says навсякъде, for replace_words), `note` (free text, required for outside_set). Where the Gazette's nested quotation marks cut a segment short (q1 ends before the inner quote), give `old`, `new` or `anchor` as {"text": "…"} with the words copied exactly from the instruction line above, quotation marks included; the script checks they stand there. Example: {"id": "§1.1", "kind": "replace_words", "address": "чл. 36, ал. 1", "old": "q1", "new": "q2"}.

## The instructions
### §1 (block 2, section body)
§ 1. Приложението към чл. 6, ал. 2 се изменя така:
- quoted block 3: „Приложение към чл. 6, ал. 2
- quoted block 4: Обща численост на областните дирекции „Земеделие“, в т.ч. и на общинските служби по земеделие към тях – 1762 щатни бройки
- quoted block 5: Областна дирекция „Земеделие“ – Благоевград
- quoted block 6: 84
- quoted block 7: Областна дирекция „Земеделие“ – Бургас
- quoted block 8: 84
- quoted block 9: Областна дирекция „Земеделие“ – Варна
- quoted block 10: 74
- quoted block 11: Областна дирекция „Земеделие“ – В. Търново
- quoted block 12: 63
- quoted block 13: Областна дирекция „Земеделие“ – Видин
- quoted block 14: 62
- quoted block 15: Областна дирекция „Земеделие“ – Враца
- quoted block 16: 63
- quoted block 17: Областна дирекция „Земеделие“ – Габрово
- quoted block 18: 36
- quoted block 19: Областна дирекция „Земеделие“ – Добрич
- quoted block 20: 76
- quoted block 21: Областна дирекция „Земеделие“ – Кърджали
- quoted block 22: 57
- quoted block 23: Областна дирекция „Земеделие“ – Кюстендил
- quoted block 24: 54
- quoted block 25: Областна дирекция „Земеделие“ – Ловеч
- quoted block 26: 55
- quoted block 27: Областна дирекция „Земеделие“ – Монтана
- quoted block 28: 63
- quoted block 29: Областна дирекция „Земеделие“ – Пазарджик
- quoted block 30: 63
- quoted block 31: Областна дирекция „Земеделие“ – Перник
- quoted block 32: 46
- quoted block 33: Областна дирекция „Земеделие“ – Плевен
- quoted block 34: 73
- quoted block 35: Областна дирекция „Земеделие“ – Пловдив
- quoted block 36: 105
- quoted block 37: Областна дирекция „Земеделие“ – Разград
- quoted block 38: 52
- quoted block 39: Областна дирекция „Земеделие“ – Русе
- quoted block 40: 53
- quoted block 41: Областна дирекция „Земеделие“ – Силистра
- quoted block 42: 54
- quoted block 43: Областна дирекция „Земеделие“ – Сливен
- quoted block 44: 48
- quoted block 45: Областна дирекция „Земеделие“ – Смолян
- quoted block 46: 61
- quoted block 47: Областна дирекция „Земеделие“ – София-град
- quoted block 48: 44
- quoted block 49: Областна дирекция „Земеделие“ – София област
- quoted block 50: 101
- quoted block 51: Областна дирекция „Земеделие“ – Стара Загора
- quoted block 52: 66
- quoted block 53: Областна дирекция „Земеделие“ – Търговище
- quoted block 54: 44
- quoted block 55: Областна дирекция „Земеделие“ – Хасково
- quoted block 56: 72
- quoted block 57: Областна дирекция „Земеделие“ – Шумен
- quoted block 58: 64
- quoted block 59: Областна дирекция „Земеделие“ – Ямбол
- quoted block 60: 45“.
- current text at „чл. 6, ал. 2“:
    (2) Числеността на персонала на съответната областна дирекция е посочена в приложението.

### §2 (block 62, section final)
§ 2. Правилникът влиза в сила от деня на обнародването му в „Държавен вестник“.
- q1: „Държавен вестник“
