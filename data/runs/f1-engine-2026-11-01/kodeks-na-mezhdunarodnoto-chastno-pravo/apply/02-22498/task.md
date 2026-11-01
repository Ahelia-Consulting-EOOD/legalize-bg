# Apply the amending material of ДВ бр. 47/2009 to kodeks-na-mezhdunarodnoto-chastno-pravo

You read the instructions of an amending act and turn each into operations on the act's text, in the form below. You never retype the act's words: a new text is a reference to the quoted blocks (their indices), an old or new string is a reference to a quoted segment of the instruction (q1, q2, … in order of appearance), an address is written as the Gazette writes it („чл. 36, ал. 1, т. 5“, „§ 3“, „глава втора, раздел V“, „Приложение № 3“, „наименованието“). An instruction that changes no text of this act (entry into force, a transitional rule, an instruction aimed at another act) is `no_text_change`. An instruction that changes this act's text in a way you cannot express in the closed set is `outside_set` with a note that says what it does: the script stops the act for the owner.

Kinds: `replace_provision`: the addressed provision (article, alinea, item, letter, §) is replaced whole by the quoted text (blocks); `replace_words`: inside the addressed provision the words old are replaced by new; everywhere: true when the instruction says „навсякъде“; `delete_words`: inside the addressed provision the words old are deleted; `insert_words`: inside the addressed provision new is inserted after the words anchor, or at the end (where: end) or the start (where: start); `insert_provision`: a new provision (blocks) is inserted after the sibling named by after, at the address it will carry; `repeal`: the addressed provision is repealed: its number stays with the repeal marker, its text and children go; `renumber`: the addressed provision becomes the number in to (досегашната ал. 2 става ал. 3); `replace_heading`: the addressed heading, or the act's title (address наименованието), takes the words in new (a quoted segment or blocks); `insert_heading`: a new heading (blocks) is inserted after the provision or heading named by after; `replace_annex`: the annex named by address is replaced whole by the quoted blocks; `insert_annex`: a new annex (blocks) is appended after the annex named by after, or at the end of the act; `repeal_annex`: the annex named by address is repealed: its heading stays with the repeal marker, its rows go; `corrigendum`: a corrigendum: inside the addressed provision the words old are replaced by new, marked Попр.; `no_text_change`: the instruction changes no text of this act (entry into force, a transitional rule, an instruction for another act); `outside_set`: the instruction changes this act's text in a way none of the kinds above expresses; the note says what it does, and the script stops the act for the owner.

Write exactly one JSON object to `data/runs/f1-engine-2026-11-01/kodeks-na-mezhdunarodnoto-chastno-pravo/apply/02-22498/answer.json`: {"material": <id>, "operations": [...]}, one or more operations per instruction id, in the material's order; nothing else, no prose, no code fence. Each operation is an object with these keys and no others: `id` (the instruction id as written above, e.g. "§3.1"), `kind` (one of the kinds), `address` (the provision, in the Gazette's grammar; not for no_text_change), and by kind: `blocks` ([first, last] block indices of the quoted text, for replace_provision, insert_provision, insert_heading, replace_annex, insert_annex, or replace_heading with quoted blocks), `after` (the sibling the new text follows, for the insert kinds), `old` and `new` (segment references like "q1", for replace_words, delete_words, corrigendum, insert_words, replace_heading), `anchor` and `where` (after | before | end | start, for insert_words), `to` (the new number, for renumber), `everywhere` (true when the instruction says навсякъде, for replace_words), `note` (free text, required for outside_set). Where the Gazette's nested quotation marks cut a segment short (q1 ends before the inner quote), give `old`, `new` or `anchor` as {"text": "…"} with the words copied exactly from the instruction line above, quotation marks included; the script checks they stand there. Example: {"id": "§1.1", "kind": "replace_words", "address": "чл. 36, ал. 1", "old": "q1", "new": "q2"}.

## The instructions
### §9 (block 789, section transitional_final)
§ 9. В Кодекса на международното частно право (обн., ДВ., бр. 42 от 2005 г.; изм., бр. 59 от 2007 г.) в чл. 84 се правят следните изменения:
- current text at „чл. 84“:
    Осиновяване **Чл. 84.**
    (1) Условията за осиновяването се уреждат от правото на държавата, чиито граждани са осиновяващият (осиновяващите) и осиновяваният към момента на подаване на молбата за осиновяване.
    (2) Ако те са с различно гражданство, прилага се отечественото право на всяко от лицата.
    (3) Когато осиновяваното лице е български гражданин, иска се съгласието на министъра на правосъдието. Условията и редът за даване на съгласие за осиновяване от чужд гражданин на лице - български гражданин, се определят с наредба на министъра на правосъдието.
    (4) Когато осиновяваното лице е български гражданин, осиновяващият - български или чужд гражданин, който има обичайно местопребиваване в друга държава, трябва да отговаря и на условията за осиновяване по правото на тази държава.
    (5) Действието на осиновяването се урежда от общото отечествено право на осиновителя и осиновения. Ако те са с различно гражданство, прилага се правото на държавата, в която е тяхното общо обичайно местопребиваване.
    (6) Унищожаването на осиновяването се урежда от правото, което е било приложимо към условията за осиновяването съгласно ал. 1, 2 и 4.
    (7) Основанията за прекратяване на осиновяването извън унищожаването по ал. 6 се уреждат от правото, приложимо към действието на осиновяването съгласно ал. 5.
    (8) При прекратяване на осиновяването трябва да се съобразят интересите на ненавършилия пълнолетие осиновен.

### §9.1 (block 790, section transitional_final)
1. В ал. 3:

### §9.1.а (block 791, section transitional_final)
а) изречение първо се изменя така: “Когато осиновяваният е лице с обичайно местопребиваване в Република България, се иска съгласието на министъра на правосъдието, освен ако осиновяващият има обичайно местопребиваване в Република България.”;
- q1: „Когато осиновяваният е лице с обичайно местопребиваване в Република България, се иска съгласието на министъра на правосъдието, освен ако осиновяващият има обичайно местопребиваване в Република България.“

### §9.1.б (block 792, section transitional_final)
б) в изречение второ думите “от чужд гражданин на лице - български гражданин” се заличават.
- q1: „от чужд гражданин на лице - български гражданин“

### §9.2 (block 793, section transitional_final)
2. В ал. 4 думите “български или чужд гражданин” се заличават.
- q1: „български или чужд гражданин“
