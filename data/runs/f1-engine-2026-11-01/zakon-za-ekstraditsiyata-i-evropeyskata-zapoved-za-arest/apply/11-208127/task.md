# Apply the amending material of ДВ бр. 18/2024 to zakon-za-ekstraditsiyata-i-evropeyskata-zapoved-za-arest

You read the instructions of an amending act and turn each into operations on the act's text, in the form below. You never retype the act's words: a new text is a reference to the quoted blocks (their indices), an old or new string is a reference to a quoted segment of the instruction (q1, q2, … in order of appearance), an address is written as the Gazette writes it („чл. 36, ал. 1, т. 5“, „§ 3“, „глава втора, раздел V“, „Приложение № 3“, „наименованието“). An instruction that changes no text of this act (entry into force, a transitional rule, an instruction aimed at another act) is `no_text_change`. An instruction that changes this act's text in a way you cannot express in the closed set is `outside_set` with a note that says what it does: the script stops the act for the owner.

Kinds: `replace_provision`: the addressed provision (article, alinea, item, letter, §) is replaced whole by the quoted text (blocks); `replace_words`: inside the addressed provision the words old are replaced by new; everywhere: true when the instruction says „навсякъде“; `delete_words`: inside the addressed provision the words old are deleted; `insert_words`: inside the addressed provision new is inserted after the words anchor, or at the end (where: end) or the start (where: start); `insert_provision`: a new provision (blocks) is inserted after the sibling named by after, at the address it will carry; `repeal`: the addressed provision is repealed: its number stays with the repeal marker, its text and children go; `renumber`: the addressed provision becomes the number in to (досегашната ал. 2 става ал. 3); `replace_heading`: the addressed heading, or the act's title (address наименованието), takes the words in new (a quoted segment or blocks); `insert_heading`: a new heading (blocks) is inserted after the provision or heading named by after; `replace_annex`: the annex named by address is replaced whole by the quoted blocks; `insert_annex`: a new annex (blocks) is appended after the annex named by after, or at the end of the act; `repeal_annex`: the annex named by address is repealed: its heading stays with the repeal marker, its rows go; `corrigendum`: a corrigendum: inside the addressed provision the words old are replaced by new, marked Попр.; `no_text_change`: the instruction changes no text of this act (entry into force, a transitional rule, an instruction for another act); `outside_set`: the instruction changes this act's text in a way none of the kinds above expresses; the note says what it does, and the script stops the act for the owner.

Write exactly one JSON object to `data/runs/f1-engine-2026-11-01/zakon-za-ekstraditsiyata-i-evropeyskata-zapoved-za-arest/apply/11-208127/answer.json`: {"material": <id>, "operations": [...]}, one or more operations per instruction id, in the material's order; nothing else, no prose, no code fence. Each operation is an object with these keys and no others: `id` (the instruction id as written above, e.g. "§3.1"), `kind` (one of the kinds), `address` (the provision, in the Gazette's grammar; not for no_text_change), and by kind: `blocks` ([first, last] block indices of the quoted text, for replace_provision, insert_provision, insert_heading, replace_annex, insert_annex, or replace_heading with quoted blocks), `after` (the sibling the new text follows, for the insert kinds), `old` and `new` (segment references like "q1", for replace_words, delete_words, corrigendum, insert_words, replace_heading), `anchor` and `where` (after | before | end | start, for insert_words), `to` (the new number, for renumber), `everywhere` (true when the instruction says навсякъде, for replace_words), `note` (free text, required for outside_set). Where the Gazette's nested quotation marks cut a segment short (q1 ends before the inner quote), give `old`, `new` or `anchor` as {"text": "…"} with the words copied exactly from the instruction line above, quotation marks included; the script checks they stand there. Example: {"id": "§1.1", "kind": "replace_words", "address": "чл. 36, ал. 1", "old": "q1", "new": "q2"}.

## The instructions
### §11 (block 353, section final)
§ 11. В Закона за екстрадицията и Европейската заповед за арест (обн., ДВ, бр. 46 от 2005 г.; изм., бр. 86 от 2005 г., бр. 52 от 2008 г., бр. 49 от 2010 г., бр. 55 от 2011 г., бр. 53 от 2014 г., бр. 7 и 45 от 2019 г. и бр. 48, 67 и 100 от 2023 г.) се правят следните изменения:

### §11.1 (block 354, section final)
1. В чл. 13, ал. 7, изречение първо думите „чл. 64, ал. 3 и 5“ се заменят с „чл. 64, ал. 4 и 6“.
- q1: „чл. 64, ал. 3 и 5“
- q2: „чл. 64, ал. 4 и 6“
- current text at „чл. 13, ал. 7“:
    (7) (Изм. - ДВ, бр. 86 от 2005 г.) Окръжният съд разглежда искането по реда на чл. 64, ал. 3 и 5 от Наказателно-процесуалния кодекс и се произнася с определение, с което взема мярка временно задържане или друга мярка на процесуална принуда, която осигурява участието на лицето в производството по екстрадиция. Мярката временно задържане се взема за срок до 40 дни или за друг срок, установен в международен договор, по който Република България е страна.
- current text at „чл. 64, ал. 3“:
    (3) Когато вещите по ал. 1 подлежат на изземване или конфискация на територията на Република България, ако са необходими във връзка с висящо наказателно производство в издаващата държава членка, компетентният български съд може да вземе решение временно да бъдат задържани в Република България или временно да бъдат предадени на издаващата държава членка с условие да бъдат върнати.
- current text at „чл. 64, ал. 4“:
    (4) Правата, които Република България или трети лица са придобили върху посочените вещи, се запазват. При наличие на такива права вещите се връщат в изпълняващата държава членка на разноски на издаващата държава членка незабавно след приключване на наказателното производство.

### §11.2 (block 355, section final)
2. В чл. 15, ал. 1 думите „чл. 64, ал. 3 и 5“ се заменят с „чл. 64, ал. 4 и 6“.
- q1: „чл. 64, ал. 3 и 5“
- q2: „чл. 64, ал. 4 и 6“
- current text at „чл. 15, ал. 1“:
    (1) (Изм. - ДВ, бр. 86 от 2005 г.) В случаите на чл. 14, ал. 4, т. 4 окръжният съд разглежда незабавно искането за вземане на мярка задържане под стража по реда на чл. 64, ал. 3 и 5 от Наказателно-процесуалния кодекс.
- current text at „чл. 64, ал. 3“:
    (3) Когато вещите по ал. 1 подлежат на изземване или конфискация на територията на Република България, ако са необходими във връзка с висящо наказателно производство в издаващата държава членка, компетентният български съд може да вземе решение временно да бъдат задържани в Република България или временно да бъдат предадени на издаващата държава членка с условие да бъдат върнати.
- current text at „чл. 64, ал. 4“:
    (4) Правата, които Република България или трети лица са придобили върху посочените вещи, се запазват. При наличие на такива права вещите се връщат в изпълняващата държава членка на разноски на издаващата държава членка незабавно след приключване на наказателното производство.

### §11.3 (block 356, section final)
3. В чл. 56а, ал. 4 думите „чл. 64, ал. 6 – 8“ се заменят с „чл. 64, ал. 7 – 9“.
- q1: „чл. 64, ал. 6 – 8“
- q2: „чл. 64, ал. 7 – 9“
- current text at „чл. 56а, ал. 4“:
    (4) Определението подлежи на обжалване с частна жалба и протест пред съответния въззивен съд в тридневен срок по реда на чл. 64, ал. 6 – 8 от Наказателно-процесуалния кодекс.
- „чл. 64, ал. 6“: 'чл. 64, ал. 6' names 0 place(s) in the act
- „чл. 64, ал. 7“: 'чл. 64, ал. 7' names 0 place(s) in the act
