# Apply the amending material of ДВ бр. 82/2006 to zakon-za-zashtita-na-litsa-zastrasheni-vav-vrazka-s-nakazatelno-proizvodstvo

You read the instructions of an amending act and turn each into operations on the act's text, in the form below. You never retype the act's words: a new text is a reference to the quoted blocks (their indices), an old or new string is a reference to a quoted segment of the instruction (q1, q2, … in order of appearance), an address is written as the Gazette writes it („чл. 36, ал. 1, т. 5“, „§ 3“, „глава втора, раздел V“, „Приложение № 3“, „наименованието“). An instruction that changes no text of this act (entry into force, a transitional rule, an instruction aimed at another act) is `no_text_change`. An instruction that changes this act's text in a way you cannot express in the closed set is `outside_set` with a note that says what it does: the script stops the act for the owner.

Kinds: `replace_provision`: the addressed provision (article, alinea, item, letter, §) is replaced whole by the quoted text (blocks); `replace_words`: inside the addressed provision the words old are replaced by new; everywhere: true when the instruction says „навсякъде“; `delete_words`: inside the addressed provision the words old are deleted; `insert_words`: inside the addressed provision new is inserted after the words anchor, or at the end (where: end) or the start (where: start); `insert_provision`: a new provision (blocks) is inserted after the sibling named by after, at the address it will carry; `repeal`: the addressed provision is repealed: its number stays with the repeal marker, its text and children go; `renumber`: the addressed provision becomes the number in to (досегашната ал. 2 става ал. 3); `replace_heading`: the addressed heading, or the act's title (address наименованието), takes the words in new (a quoted segment or blocks); `insert_heading`: a new heading (blocks) is inserted after the provision or heading named by after; `replace_annex`: the annex named by address is replaced whole by the quoted blocks; `insert_annex`: a new annex (blocks) is appended after the annex named by after, or at the end of the act; `repeal_annex`: the annex named by address is repealed: its heading stays with the repeal marker, its rows go; `corrigendum`: a corrigendum: inside the addressed provision the words old are replaced by new, marked Попр.; `no_text_change`: the instruction changes no text of this act (entry into force, a transitional rule, an instruction for another act); `outside_set`: the instruction changes this act's text in a way none of the kinds above expresses; the note says what it does, and the script stops the act for the owner.

Write exactly one JSON object to `data/runs/f1-engine-2026-11-01/zakon-za-zashtita-na-litsa-zastrasheni-vav-vrazka-s-nakazatelno-proizvodstvo/apply/01-2662/answer.json`: {"material": <id>, "operations": [...]}, one or more operations per instruction id, in the material's order; nothing else, no prose, no code fence. Each operation is an object with these keys and no others: `id` (the instruction id as written above, e.g. "§3.1"), `kind` (one of the kinds), `address` (the provision, in the Gazette's grammar; not for no_text_change), and by kind: `blocks` ([first, last] block indices of the quoted text, for replace_provision, insert_provision, insert_heading, replace_annex, insert_annex, or replace_heading with quoted blocks), `after` (the sibling the new text follows, for the insert kinds), `old` and `new` (segment references like "q1", for replace_words, delete_words, corrigendum, insert_words, replace_heading), `anchor` and `where` (after | before | end | start, for insert_words), `to` (the new number, for renumber), `everywhere` (true when the instruction says навсякъде, for replace_words), `note` (free text, required for outside_set). Where the Gazette's nested quotation marks cut a segment short (q1 ends before the inner quote), give `old`, `new` or `anchor` as {"text": "…"} with the words copied exactly from the instruction line above, quotation marks included; the script checks they stand there. Example: {"id": "§1.1", "kind": "replace_words", "address": "чл. 36, ал. 1", "old": "q1", "new": "q2"}.

## The instructions
### §11 (block 29, section final)
§ 11. В Закона за защита на лица, застрашени във връзка с наказателно производство (ДВ, бр. 103 от 2004 г.) в чл. 7 се правят следните изменения:
- current text at „чл. 7“:
    **Чл. 7.**
    (1) Физическата охрана на защитено лице е дейност по защита на телесната неприкосновеност от противоправни посегателства и може да бъде денонощна, за определени часове или за определени случаи.
    (2) При осъществяване на дейността по ал. 1 охраняващият екип може да използва лични предпазни средства, както и физическа сила и помощни средства, необходими за изпълнение на мярката при условията и по реда на чл. 79 от Закона за Министерството на вътрешните работи.
    (3) Охраняващият екип може да използва огнестрелно оръжие като крайна мярка при условията на чл. 80, ал. 1, т. 1, 3 - 5 и ал. 2 от Закона за Министерството на вътрешните работи.

### §11.1 (block 30, section final)
1. В ал. 2 думите “чл. 79” се заменят с “чл. 73”.
- q1: „чл. 79“
- q2: „чл. 73“
- „чл. 79“: 'чл. 79' names 0 place(s) in the act
- „чл. 73“: 'чл. 73' names 0 place(s) in the act

### §11.2 (block 31, section final)
2. В ал. 3 думите “чл. 80, ал. 1, т. 1, 3 - 5 и ал. 2” се заменят с “чл. 74, ал. 1, т. 1, 3 и 4 и ал. 2”.
- q1: „чл. 80, ал. 1, т. 1, 3 - 5 и ал. 2“
- q2: „чл. 74, ал. 1, т. 1, 3 и 4 и ал. 2“
- „чл. 80, ал. 1, т. 1“: 'чл. 80, ал. 1, т. 1' names 0 place(s) in the act
- „чл. 74, ал. 1, т. 1“: 'чл. 74, ал. 1, т. 1' names 0 place(s) in the act
