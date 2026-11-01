# Apply the amending material of ДВ бр. 6/2023 to naredba-8121z-310-ot-17-yuli-2014-g-za-prenaznachavane-na-darzhavnite-sluzhiteli

You read the instructions of an amending act and turn each into operations on the act's text, in the form below. You never retype the act's words: a new text is a reference to the quoted blocks (their indices), an old or new string is a reference to a quoted segment of the instruction (q1, q2, … in order of appearance), an address is written as the Gazette writes it („чл. 36, ал. 1, т. 5“, „§ 3“, „глава втора, раздел V“, „Приложение № 3“, „наименованието“). An instruction that changes no text of this act (entry into force, a transitional rule, an instruction aimed at another act) is `no_text_change`. An instruction that changes this act's text in a way you cannot express in the closed set is `outside_set` with a note that says what it does: the script stops the act for the owner.

Kinds: `replace_provision`: the addressed provision (article, alinea, item, letter, §) is replaced whole by the quoted text (blocks); `replace_words`: inside the addressed provision the words old are replaced by new; everywhere: true when the instruction says „навсякъде“; `delete_words`: inside the addressed provision the words old are deleted; `insert_words`: inside the addressed provision new is inserted after the words anchor, or at the end (where: end) or the start (where: start); `insert_provision`: a new provision (blocks) is inserted after the sibling named by after, at the address it will carry; `repeal`: the addressed provision is repealed: its number stays with the repeal marker, its text and children go; `renumber`: the addressed provision becomes the number in to (досегашната ал. 2 става ал. 3); `replace_heading`: the addressed heading, or the act's title (address наименованието), takes the words in new (a quoted segment or blocks); `insert_heading`: a new heading (blocks) is inserted after the provision or heading named by after; `replace_annex`: the annex named by address is replaced whole by the quoted blocks; `insert_annex`: a new annex (blocks) is appended after the annex named by after, or at the end of the act; `repeal_annex`: the annex named by address is repealed: its heading stays with the repeal marker, its rows go; `corrigendum`: a corrigendum: inside the addressed provision the words old are replaced by new, marked Попр.; `no_text_change`: the instruction changes no text of this act (entry into force, a transitional rule, an instruction for another act); `outside_set`: the instruction changes this act's text in a way none of the kinds above expresses; the note says what it does, and the script stops the act for the owner.

Write exactly one JSON object to `data/runs/f1-engine-2026-11-01/naredba-8121z-310-ot-17-yuli-2014-g-za-prenaznachavane-na-darzhavnite-sluzhiteli/apply/07-183866/answer.json`: {"material": <id>, "operations": [...]}, one or more operations per instruction id, in the material's order; nothing else, no prose, no code fence. Each operation is an object with these keys and no others: `id` (the instruction id as written above, e.g. "§3.1"), `kind` (one of the kinds), `address` (the provision, in the Gazette's grammar; not for no_text_change), and by kind: `blocks` ([first, last] block indices of the quoted text, for replace_provision, insert_provision, insert_heading, replace_annex, insert_annex, or replace_heading with quoted blocks), `after` (the sibling the new text follows, for the insert kinds), `old` and `new` (segment references like "q1", for replace_words, delete_words, corrigendum, insert_words, replace_heading), `anchor` and `where` (after | before | end | start, for insert_words), `to` (the new number, for renumber), `everywhere` (true when the instruction says навсякъде, for replace_words), `note` (free text, required for outside_set). Where the Gazette's nested quotation marks cut a segment short (q1 ends before the inner quote), give `old`, `new` or `anchor` as {"text": "…"} with the words copied exactly from the instruction line above, quotation marks included; the script checks they stand there. Example: {"id": "§1.1", "kind": "replace_words", "address": "чл. 36, ал. 1", "old": "q1", "new": "q2"}.

## The instructions
### §1 (block 4, section body)
§ 1. В чл. 4а, ал. 5 се създава изречение второ: „Ръководителят на структурата по месторабота на служител, участващ в конкурентен подбор, е длъжен да осигури участието на служителя в подбора.“
- q1: „Ръководителят на структурата по месторабота на служител, участващ в конкурентен подбор, е длъжен да осигури участието на служителя в подбора.“
- current text at „чл. 4а, ал. 5“:
    (5) При кандидатстване за заемане на длъжност в конкурентен подбор не се изисква съгласие на ръководителя на структурата по месторабота на служителя.

### §2 (block 5, section body)
§ 2. Създава се нов чл. 4б:
- quoted block 6: „Чл. 4б. (1) За преназначаване на длъжности в дирекция „Специални операции и борба с тероризма“ (ДСОБТ) при Главна дирекция „Жандармерия, специални операции и борба с тероризма“ (ГДЖСОБТ) и в звената по чл. 44 от ЗМВР от длъжности с друго направление на дейност органът по преназначаване по чл. 158 или чл. 159, ал. 1 от ЗМВР задължително със заповед обявява конкурентен подбор. Редът за провеждане на конкурентния подбор се определя със заповедта.
- quoted block 7: (2) В заповедта по ал. 1 се определят:
- quoted block 8: 1. вакантните длъжности;
- quoted block 9: 2. условията за участие;
- quoted block 10: 3. необходимите документи за участие, място и срок за подаването им;
- quoted block 11: 4. начин за провеждане, който задължително включва психологично изследване и изследване на физическата годност, които се провеждат по методики, утвърдени от министъра на вътрешните работи;
- quoted block 12: 5. срок за провеждане;
- quoted block 13: 6. състав на комисията за подбор.
- quoted block 14: (3) При провеждането на конкурентен подбор по ал. 1 се прилагат правилата на чл. 4а, ал. 3 – 8.
- quoted block 15: (4) Служителят, успешно завършил курса за професионална специализация, провеждан по реда на наредбата по чл. 170, ал. 5 и чл. 170а, ал. 2 от ЗМВР, се преназначава в ДСОБТ при ГДЖСОБТ и звената по чл. 44 от ЗМВР на длъжността, за която е кандидатствал.“
- current text at „чл. 4б“:
    **Чл. 4б.** (Нов - ДВ, бр. 29 от 2015 г.) Държавният служител може да бъде преназначен на по-висока длъжност в рамките на съответния вид длъжности по чл. 143, ал. 1, т. 6 и 7 ЗМВР, когато е прослужил не по-малко от една година на заеманата длъжност.

### §3 (block 16, section body)
§ 3. Досегашният чл. 4б става чл. 4в.
- current text at „чл. 4б“:
    **Чл. 4б.** (Нов - ДВ, бр. 29 от 2015 г.) Държавният служител може да бъде преназначен на по-висока длъжност в рамките на съответния вид длъжности по чл. 143, ал. 1, т. 6 и 7 ЗМВР, когато е прослужил не по-малко от една година на заеманата длъжност.
- „чл. 4в“: 'чл. 4в' names 0 place(s) in the act

### §4 (block 17, section body)
§ 4. В чл. 7, ал. 3, т. 3 след думата „конкурс“ се добавя „или за които не е започнала процедура по преназначаване на държавен служител“.
- q1: „конкурс“
- q2: „или за които не е започнала процедура по преназначаване на държавен служител“
- current text at „чл. 7, ал. 3, т. 3“:
    3. длъжности, за които няма обявен конкурс.

### §5 (block 18, section body)
§ 5. В чл. 12, ал. 2 след думите „ниво на класифицирана информация за съответната длъжност“ се добавя „и е изтекъл едногодишният срок за изпитване“.
- q1: „ниво на класифицирана информация за съответната длъжност“
- q2: „и е изтекъл едногодишният срок за изпитване“
- current text at „чл. 12, ал. 2“:
    (2) (Доп. - ДВ, бр. 87 от 2014 г., изм. - ДВ, бр. 104 от 2014 г., доп. - ДВ, бр. 29 от 2017 г.) Държавният служител може да бъде временно преназначен на по-висока длъжност, когато отговаря на изискванията за образование, квалификация и достъп до съответното ниво на класифицирана информация за съответната длъжност, а когато е предвидено за съответната длъжност – и на изискването да е хабилитирано лице съгласно Закона за вис­шето образование и Закона за развитието на академичния състав в Република България.

### §6 (block 20, section transitional_final)
§ 6. В тримесечен срок от влизането в сила на наредбата се предоставят за утвърждаване от министъра на вътрешните работи методиките по чл. 4б, ал. 2, т. 4 за:
- „чл. 4б, ал. 2, т. 4“: 'чл. 4б, ал. 2, т. 4' names 0 place(s) in the act

### §6.1 (block 21, section transitional_final)
1. психологично изследване – от Института по психология;

### §6.2 (block 22, section transitional_final)
2. изследване на физическата годност за ДСОБТ при ГДЖСОБТ – от ДСОБТ при ГДЖСОБТ;

### §6.3 (block 23, section transitional_final)
3. изследване на физическата годност за звената по чл. 44 от ЗМВР – от Академията на МВР, съгласувано с ръководителите на звената.
- „чл. 44“: 'чл. 44' names 0 place(s) in the act
