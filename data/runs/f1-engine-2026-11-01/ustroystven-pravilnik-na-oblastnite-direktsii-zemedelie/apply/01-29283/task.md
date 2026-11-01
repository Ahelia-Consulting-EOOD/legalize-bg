# Apply the amending material of ДВ бр. 9/2010 to ustroystven-pravilnik-na-oblastnite-direktsii-zemedelie

You read the instructions of an amending act and turn each into operations on the act's text, in the form below. You never retype the act's words: a new text is a reference to the quoted blocks (their indices), an old or new string is a reference to a quoted segment of the instruction (q1, q2, … in order of appearance), an address is written as the Gazette writes it („чл. 36, ал. 1, т. 5“, „§ 3“, „глава втора, раздел V“, „Приложение № 3“, „наименованието“). An instruction that changes no text of this act (entry into force, a transitional rule, an instruction aimed at another act) is `no_text_change`. An instruction that changes this act's text in a way you cannot express in the closed set is `outside_set` with a note that says what it does: the script stops the act for the owner.

Kinds: `replace_provision`: the addressed provision (article, alinea, item, letter, §) is replaced whole by the quoted text (blocks); `replace_words`: inside the addressed provision the words old are replaced by new; everywhere: true when the instruction says „навсякъде“; `delete_words`: inside the addressed provision the words old are deleted; `insert_words`: inside the addressed provision new is inserted after the words anchor, or at the end (where: end) or the start (where: start); `insert_provision`: a new provision (blocks) is inserted after the sibling named by after, at the address it will carry; `repeal`: the addressed provision is repealed: its number stays with the repeal marker, its text and children go; `renumber`: the addressed provision becomes the number in to (досегашната ал. 2 става ал. 3); `replace_heading`: the addressed heading, or the act's title (address наименованието), takes the words in new (a quoted segment or blocks); `insert_heading`: a new heading (blocks) is inserted after the provision or heading named by after; `replace_annex`: the annex named by address is replaced whole by the quoted blocks; `insert_annex`: a new annex (blocks) is appended after the annex named by after, or at the end of the act; `repeal_annex`: the annex named by address is repealed: its heading stays with the repeal marker, its rows go; `corrigendum`: a corrigendum: inside the addressed provision the words old are replaced by new, marked Попр.; `no_text_change`: the instruction changes no text of this act (entry into force, a transitional rule, an instruction for another act); `outside_set`: the instruction changes this act's text in a way none of the kinds above expresses; the note says what it does, and the script stops the act for the owner.

Write exactly one JSON object to `data/runs/f1-engine-2026-11-01/ustroystven-pravilnik-na-oblastnite-direktsii-zemedelie/apply/01-29283/answer.json`: {"material": <id>, "operations": [...]}, one or more operations per instruction id, in the material's order; nothing else, no prose, no code fence. Each operation is an object with these keys and no others: `id` (the instruction id as written above, e.g. "§3.1"), `kind` (one of the kinds), `address` (the provision, in the Gazette's grammar; not for no_text_change), and by kind: `blocks` ([first, last] block indices of the quoted text, for replace_provision, insert_provision, insert_heading, replace_annex, insert_annex, or replace_heading with quoted blocks), `after` (the sibling the new text follows, for the insert kinds), `old` and `new` (segment references like "q1", for replace_words, delete_words, corrigendum, insert_words, replace_heading), `anchor` and `where` (after | before | end | start, for insert_words), `to` (the new number, for renumber), `everywhere` (true when the instruction says навсякъде, for replace_words), `note` (free text, required for outside_set). Where the Gazette's nested quotation marks cut a segment short (q1 ends before the inner quote), give `old`, `new` or `anchor` as {"text": "…"} with the words copied exactly from the instruction line above, quotation marks included; the script checks they stand there. Example: {"id": "§1.1", "kind": "replace_words", "address": "чл. 36, ал. 1", "old": "q1", "new": "q2"}.

## The instructions
### §1 (block 2, section body)
§ 1. Приложението към чл. 6, ал. 2 се изменя, както следва:
- quoted block 3: „Приложение към чл. 6, ал. 2
- quoted block 4: Обща численост на областните дирекции „Земеделие“, в т.ч. и на общинските служби по земеделие към тях – 1742 щатни бройки
- quoted block 5: Областна дирекция „Земеделие“ – Благоевград
- quoted block 6: 77
- quoted block 7: Областна дирекция „Земеделие“ – Бургас
- quoted block 8: 80
- quoted block 9: Областна дирекция „Земеделие“ –
- quoted block 10: Варна
- quoted block 11: 74
- quoted block 12: Областна дирекция „Земеделие“ –
- quoted block 13: Велико Търново
- quoted block 14: 63
- quoted block 15: Областна дирекция „Земеделие“ –
- quoted block 16: Видин
- quoted block 17: 60
- quoted block 18: Областна дирекция „Земеделие“ –
- quoted block 19: Враца
- quoted block 20: 75
- quoted block 21: Областна дирекция „Земеделие“ –
- quoted block 22: Габрово
- quoted block 23: 36
- quoted block 24: Областна дирекция „Земеделие“ –
- quoted block 25: Добрич
- quoted block 26: 70
- quoted block 27: Областна дирекция „Земеделие“ –
- quoted block 28: Кърджали
- quoted block 29: 53
- quoted block 30: Областна дирекция „Земеделие“ –
- quoted block 31: Кюстендил
- quoted block 32: 51
- quoted block 33: Областна дирекция „Земеделие“ –
- quoted block 34: Ловеч
- quoted block 35: 57
- quoted block 36: Областна дирекция „Земеделие“ –
- quoted block 37: Монтана
- quoted block 38: 60
- quoted block 39: Областна дирекция „Земеделие“ –
- quoted block 40: Пазарджик
- quoted block 41: 62
- quoted block 42: Областна дирекция „Земеделие“ –
- quoted block 43: Перник
- quoted block 44: 46
- quoted block 45: Областна дирекция „Земеделие“ –
- quoted block 46: Плевен
- quoted block 47: 70
- quoted block 48: Областна дирекция „Земеделие“ –
- quoted block 49: Пловдив
- quoted block 50: 113
- quoted block 51: Областна дирекция „Земеделие“ –
- quoted block 52: Разград
- quoted block 53: 52
- quoted block 54: Областна дирекция „Земеделие“ –
- quoted block 55: Русе
- quoted block 56: 49
- quoted block 57: Областна дирекция „Земеделие“ –
- quoted block 58: Силистра
- quoted block 59: 50
- quoted block 60: Областна дирекция „Земеделие“ –
- quoted block 61: Сливен
- quoted block 62: 42
- quoted block 63: Областна дирекция „Земеделие“ –
- quoted block 64: Смолян
- quoted block 65: 62
- quoted block 66: Областна дирекция „Земеделие“ – София-град
- quoted block 67: 53
- quoted block 68: Областна дирекция „Земеделие“ –
- quoted block 69: София област
- quoted block 70: 108
- quoted block 71: Областна дирекция „Земеделие“ –
- quoted block 72: Стара Загора
- quoted block 73: 65
- quoted block 74: Областна дирекция „Земеделие“ –
- quoted block 75: Търговище
- quoted block 76: 41
- quoted block 77: Областна дирекция „Земеделие“ –
- quoted block 78: Хасково
- quoted block 79: 68
- quoted block 80: Областна дирекция „Земеделие“ –
- quoted block 81: Шумен
- quoted block 82: 64
- quoted block 83: Областна дирекция „Земеделие“ –
- quoted block 84: Ямбол
- quoted block 85: 41
- current text at „чл. 6, ал. 2“:
    (2) Числеността на персонала на съответната областна дирекция е посочена в приложението.

### §2 (block 87, section final)
§ 2. Правилникът влиза в сила от деня на обнародването му в „Държавен вестник“.
- q1: „Държавен вестник“
