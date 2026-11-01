# Apply the amending material of ДВ бр. 92/2026 to kodeks-na-mezhdunarodnoto-chastno-pravo

You read the instructions of an amending act and turn each into operations on the act's text, in the form below. You never retype the act's words: a new text is a reference to the quoted blocks (their indices), an old or new string is a reference to a quoted segment of the instruction (q1, q2, … in order of appearance), an address is written as the Gazette writes it („чл. 36, ал. 1, т. 5“, „§ 3“, „глава втора, раздел V“, „Приложение № 3“, „наименованието“). An instruction that changes no text of this act (entry into force, a transitional rule, an instruction aimed at another act) is `no_text_change`. An instruction that changes this act's text in a way you cannot express in the closed set is `outside_set` with a note that says what it does: the script stops the act for the owner.

Kinds: `replace_provision`: the addressed provision (article, alinea, item, letter, §) is replaced whole by the quoted text (blocks); `replace_words`: inside the addressed provision the words old are replaced by new; everywhere: true when the instruction says „навсякъде“; `delete_words`: inside the addressed provision the words old are deleted; `insert_words`: inside the addressed provision new is inserted after the words anchor, or at the end (where: end) or the start (where: start); `insert_provision`: a new provision (blocks) is inserted after the sibling named by after, at the address it will carry; `repeal`: the addressed provision is repealed: its number stays with the repeal marker, its text and children go; `renumber`: the addressed provision becomes the number in to (досегашната ал. 2 става ал. 3); `replace_heading`: the addressed heading, or the act's title (address наименованието), takes the words in new (a quoted segment or blocks); `insert_heading`: a new heading (blocks) is inserted after the provision or heading named by after; `replace_annex`: the annex named by address is replaced whole by the quoted blocks; `insert_annex`: a new annex (blocks) is appended after the annex named by after, or at the end of the act; `repeal_annex`: the annex named by address is repealed: its heading stays with the repeal marker, its rows go; `corrigendum`: a corrigendum: inside the addressed provision the words old are replaced by new, marked Попр.; `no_text_change`: the instruction changes no text of this act (entry into force, a transitional rule, an instruction for another act); `outside_set`: the instruction changes this act's text in a way none of the kinds above expresses; the note says what it does, and the script stops the act for the owner.

Write exactly one JSON object to `data/runs/f1-engine-2026-11-01/kodeks-na-mezhdunarodnoto-chastno-pravo/apply/06-246208/answer.json`: {"material": <id>, "operations": [...]}, one or more operations per instruction id, in the material's order; nothing else, no prose, no code fence. Each operation is an object with these keys and no others: `id` (the instruction id as written above, e.g. "§3.1"), `kind` (one of the kinds), `address` (the provision, in the Gazette's grammar; not for no_text_change), and by kind: `blocks` ([first, last] block indices of the quoted text, for replace_provision, insert_provision, insert_heading, replace_annex, insert_annex, or replace_heading with quoted blocks), `after` (the sibling the new text follows, for the insert kinds), `old` and `new` (segment references like "q1", for replace_words, delete_words, corrigendum, insert_words, replace_heading), `anchor` and `where` (after | before | end | start, for insert_words), `to` (the new number, for renumber), `everywhere` (true when the instruction says навсякъде, for replace_words), `note` (free text, required for outside_set). Where the Gazette's nested quotation marks cut a segment short (q1 ends before the inner quote), give `old`, `new` or `anchor` as {"text": "…"} with the words copied exactly from the instruction line above, quotation marks included; the script checks they stand there. Example: {"id": "§1.1", "kind": "replace_words", "address": "чл. 36, ал. 1", "old": "q1", "new": "q2"}.

## The instructions
### §9 (block 77, section transitional_final)
§ 9. В Кодекса на международното частно право (обн., ДВ, бр. 42 от 2005 г.; изм., бр. 59 от 2007 г., бр. 47 от 2009 г., бр. 100 от 2010 г., бр. 106 от 2023 г. и бр. 39 от 2024 г.) се правят следните изменения и допълнения:

### §9.1 (block 78, section transitional_final)
1. Създава се чл. 18а:
- quoted block 79: „Компетентност по делата за права от непозволено увреждане поради публичното участие на ответника
- quoted block 80: Чл. 18а. Българските съдилища са компетентни по искове за вреди, предявени от лице с местоживеене в Република България, във връзка с производства по граждански и търговски дела поради публичното му участие, предявени пред съд или правораздавателен орган на държава, която не е членка на Европейския съюз, когато ищецът по тези дела е лице с местоживеене извън Европейския съюз.“
- „чл. 18а“: 'чл. 18а' names 0 place(s) in the act

### §9.2 (block 81, section transitional_final)
2. В чл. 121:
- current text at „чл. 121“:
    Обхват на проверката и защита на длъжника **Чл. 121.**
    (1) Съдът не навлиза в разглеждане на съществото на спора, разрешен от чуждия съд.
    (2) Длъжникът може да направи възражения за погасяване на задължението въз основа на обстоятелства, настъпили след влизането в сила на чуждестранното решение.
    (3) Длъжникът не може да прави възражения за погасяване на задължението въз основа на обстоятелствата по ал. 2, след като решението за допускане на изпълнението е влязло в сила.

### §9.2.а (block 82, section transitional_final)
а) създава се нова ал. 2:
- quoted block 83: „(2) Алинея 1 не се прилага при признаване и допускане до изпълнение на съдебни решения на трети държави по съдебни производства срещу публично участие от страна на физическо или юридическо лице с местоживеене в Република България или друга държава членка, когато съдът счете, че тези производства са очевидно неоснователни или представляват злоупотреба съгласно българското право.“;

### §9.2.б (block 84, section transitional_final)
б) досегашните ал. 2 и 3 стават съответно ал. 3 и 4.
