# Apply the amending material of ДВ бр. 7/2019 to zakon-za-ekstraditsiyata-i-evropeyskata-zapoved-za-arest

You read the instructions of an amending act and turn each into operations on the act's text, in the form below. You never retype the act's words: a new text is a reference to the quoted blocks (their indices), an old or new string is a reference to a quoted segment of the instruction (q1, q2, … in order of appearance), an address is written as the Gazette writes it („чл. 36, ал. 1, т. 5“, „§ 3“, „глава втора, раздел V“, „Приложение № 3“, „наименованието“). An instruction that changes no text of this act (entry into force, a transitional rule, an instruction aimed at another act) is `no_text_change`. An instruction that changes this act's text in a way you cannot express in the closed set is `outside_set` with a note that says what it does: the script stops the act for the owner.

Kinds: `replace_provision`: the addressed provision (article, alinea, item, letter, §) is replaced whole by the quoted text (blocks); `replace_words`: inside the addressed provision the words old are replaced by new; everywhere: true when the instruction says „навсякъде“; `delete_words`: inside the addressed provision the words old are deleted; `insert_words`: inside the addressed provision new is inserted after the words anchor, or at the end (where: end) or the start (where: start); `insert_provision`: a new provision (blocks) is inserted after the sibling named by after, at the address it will carry; `repeal`: the addressed provision is repealed: its number stays with the repeal marker, its text and children go; `renumber`: the addressed provision becomes the number in to (досегашната ал. 2 става ал. 3); `replace_heading`: the addressed heading, or the act's title (address наименованието), takes the words in new (a quoted segment or blocks); `insert_heading`: a new heading (blocks) is inserted after the provision or heading named by after; `replace_annex`: the annex named by address is replaced whole by the quoted blocks; `insert_annex`: a new annex (blocks) is appended after the annex named by after, or at the end of the act; `repeal_annex`: the annex named by address is repealed: its heading stays with the repeal marker, its rows go; `corrigendum`: a corrigendum: inside the addressed provision the words old are replaced by new, marked Попр.; `no_text_change`: the instruction changes no text of this act (entry into force, a transitional rule, an instruction for another act); `outside_set`: the instruction changes this act's text in a way none of the kinds above expresses; the note says what it does, and the script stops the act for the owner.

Write exactly one JSON object to `data/runs/f1-engine-2026-11-01/zakon-za-ekstraditsiyata-i-evropeyskata-zapoved-za-arest/apply/06-134075/answer.json`: {"material": <id>, "operations": [...]}, one or more operations per instruction id, in the material's order; nothing else, no prose, no code fence. Each operation is an object with these keys and no others: `id` (the instruction id as written above, e.g. "§3.1"), `kind` (one of the kinds), `address` (the provision, in the Gazette's grammar; not for no_text_change), and by kind: `blocks` ([first, last] block indices of the quoted text, for replace_provision, insert_provision, insert_heading, replace_annex, insert_annex, or replace_heading with quoted blocks), `after` (the sibling the new text follows, for the insert kinds), `old` and `new` (segment references like "q1", for replace_words, delete_words, corrigendum, insert_words, replace_heading), `anchor` and `where` (after | before | end | start, for insert_words), `to` (the new number, for renumber), `everywhere` (true when the instruction says навсякъде, for replace_words), `note` (free text, required for outside_set). Where the Gazette's nested quotation marks cut a segment short (q1 ends before the inner quote), give `old`, `new` or `anchor` as {"text": "…"} with the words copied exactly from the instruction line above, quotation marks included; the script checks they stand there. Example: {"id": "§1.1", "kind": "replace_words", "address": "чл. 36, ал. 1", "old": "q1", "new": "q2"}.

## The instructions
### §11 (block 103, section transitional_final)
§ 11. В Закона за екстрадицията и Европейската заповед за арест (обн., ДВ, бр. 46 от 2005 г.; изм., бр. 86 от 2005 г., бр. 52 от 2008 г., бр. 49 от 2010 г., бр. 55 от 2011 г. и бр. 53 от 2014 г.) се правят следните изменения и допълнения:

### §11.1 (block 104, section transitional_final)
1. В чл. 43:
- current text at „чл. 43“:
    Задържане под стража **Чл. 43.**
    (1) (Изм. - ДВ, бр. 52 от 2008 г.) В случаите по чл. 42, ал. 1 съдът служебно се произнася по вземане на мярка за неотклонение задържане под стража на исканото лице.
    (2) (Нова - ДВ, бр. 52 от 2008 г.) В случаите по чл. 42, ал. 2 прокурорът внася искането за вземане на тази мярка в съответния окръжен съд.
    (3) (Изм. - ДВ, бр. 86 от 2005 г., предишна ал. 2 - ДВ, бр. 52 от 2008 г., изм. - ДВ, бр. 52 от 2008 г.) Съдът се произнася незабавно по вземането на мярката за неотклонение по реда на чл. 64 от Наказателно-процесуалния кодекс.
    (4) (Предишна ал. 3 - ДВ, бр. 52 от 2008 г.) Съдът назначава на лицето защитник и преводач, ако не владее български език, и го запознава с основанието за задържането му, съдържанието на Европейската заповед за арест, както и с правото му да изрази съгласие за предаване на компетентните органи на издаващата държава членка и последиците от това.
    (5) (Изм. - ДВ, бр. 86 от 2005 г., предишна ал. 4 - ДВ, бр. 52 от 2008 г.) По искане на задържаното лице окръжният съд може да измени мярката задържане под стража в друга мярка, която осигурява участието му в производството по изпълнение на Европейската заповед за арест, по реда на чл. 65 от Наказателно-процесуалния кодекс.

### §11.1.а (block 105, section transitional_final)
а) създава се нова ал. 5:
- quoted block 106: „(5) Съдът уведомява исканото лице за правото му на защитник в издаващата държава членка, който да подпомага защитника в Република България чрез информация и съвети. Ако лицето заяви, че желае да упражни това право, съдът незабавно уведомява за това компетентния орган на издаващата държава членка.“;

### §11.1.б (block 107, section transitional_final)
б) създава се ал. 6:
- quoted block 108: „(6) Правото на лицето по ал. 5 не засяга сроковете по чл. 45, ал. 3 и чл. 48, ал. 3, съгласно които съдът решава дали лицето да бъде предадено.“;

### §11.1.в (block 109, section transitional_final)
в) досегашната ал. 5 става ал. 7.

### §11.2 (block 110, section transitional_final)
2. В чл. 58:
- current text at „чл. 58“:
    Информация, предоставяна от издаващия орган **Чл. 58.** Издаващият орган по чл. 56, ал. 1 предоставя необходимите данни и информация по искане на изпълняващия орган във връзка с производството по изпълнение на Европейска заповед за арест.

### §11.2.а (block 111, section transitional_final)
а) досегашният текст става ал. 1;

### §11.2.б (block 112, section transitional_final)
б) създава се ал. 2:
- quoted block 113: „(2) Когато исканото лице е заявило пред компетентния орган на изпълняващата държава, че желае да упражни правото си на защитник в Република България като издаваща държава, който да подпомага защитника му в изпълняващата държава чрез информация и съвети, и издаващият орган по чл. 56, ал. 1 е бил уведомен за това от компетентния орган на изпълняващата държава, той предоставя на исканото лице необходимата информация, която да го улесни в назначаването на защитник в Република България, и му назначава защитник, ако той не е упълномощил такъв.“
