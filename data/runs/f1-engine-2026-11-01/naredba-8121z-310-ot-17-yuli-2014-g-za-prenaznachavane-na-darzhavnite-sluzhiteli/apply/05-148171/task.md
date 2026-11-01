# Apply the amending material of ДВ бр. 47/2020 to naredba-8121z-310-ot-17-yuli-2014-g-za-prenaznachavane-na-darzhavnite-sluzhiteli

You read the instructions of an amending act and turn each into operations on the act's text, in the form below. You never retype the act's words: a new text is a reference to the quoted blocks (their indices), an old or new string is a reference to a quoted segment of the instruction (q1, q2, … in order of appearance), an address is written as the Gazette writes it („чл. 36, ал. 1, т. 5“, „§ 3“, „глава втора, раздел V“, „Приложение № 3“, „наименованието“). An instruction that changes no text of this act (entry into force, a transitional rule, an instruction aimed at another act) is `no_text_change`. An instruction that changes this act's text in a way you cannot express in the closed set is `outside_set` with a note that says what it does: the script stops the act for the owner.

Kinds: `replace_provision`: the addressed provision (article, alinea, item, letter, §) is replaced whole by the quoted text (blocks); `replace_words`: inside the addressed provision the words old are replaced by new; everywhere: true when the instruction says „навсякъде“; `delete_words`: inside the addressed provision the words old are deleted; `insert_words`: inside the addressed provision new is inserted after the words anchor, or at the end (where: end) or the start (where: start); `insert_provision`: a new provision (blocks) is inserted after the sibling named by after, at the address it will carry; `repeal`: the addressed provision is repealed: its number stays with the repeal marker, its text and children go; `renumber`: the addressed provision becomes the number in to (досегашната ал. 2 става ал. 3); `replace_heading`: the addressed heading, or the act's title (address наименованието), takes the words in new (a quoted segment or blocks); `insert_heading`: a new heading (blocks) is inserted after the provision or heading named by after; `replace_annex`: the annex named by address is replaced whole by the quoted blocks; `insert_annex`: a new annex (blocks) is appended after the annex named by after, or at the end of the act; `repeal_annex`: the annex named by address is repealed: its heading stays with the repeal marker, its rows go; `corrigendum`: a corrigendum: inside the addressed provision the words old are replaced by new, marked Попр.; `no_text_change`: the instruction changes no text of this act (entry into force, a transitional rule, an instruction for another act); `outside_set`: the instruction changes this act's text in a way none of the kinds above expresses; the note says what it does, and the script stops the act for the owner.

Write exactly one JSON object to `data/runs/f1-engine-2026-11-01/naredba-8121z-310-ot-17-yuli-2014-g-za-prenaznachavane-na-darzhavnite-sluzhiteli/apply/05-148171/answer.json`: {"material": <id>, "operations": [...]}, one or more operations per instruction id, in the material's order; nothing else, no prose, no code fence. Each operation is an object with these keys and no others: `id` (the instruction id as written above, e.g. "§3.1"), `kind` (one of the kinds), `address` (the provision, in the Gazette's grammar; not for no_text_change), and by kind: `blocks` ([first, last] block indices of the quoted text, for replace_provision, insert_provision, insert_heading, replace_annex, insert_annex, or replace_heading with quoted blocks), `after` (the sibling the new text follows, for the insert kinds), `old` and `new` (segment references like "q1", for replace_words, delete_words, corrigendum, insert_words, replace_heading), `anchor` and `where` (after | before | end | start, for insert_words), `to` (the new number, for renumber), `everywhere` (true when the instruction says навсякъде, for replace_words), `note` (free text, required for outside_set). Where the Gazette's nested quotation marks cut a segment short (q1 ends before the inner quote), give `old`, `new` or `anchor` as {"text": "…"} with the words copied exactly from the instruction line above, quotation marks included; the script checks they stand there. Example: {"id": "§1.1", "kind": "replace_words", "address": "чл. 36, ал. 1", "old": "q1", "new": "q2"}.

## The instructions
### §1 (block 1, section body)
§ 1. В чл. 2 думите „Закона за Министерството на вътрешните работи (ЗМВР)“ се заменят със „ЗМВР“.
- q1: „Закона за Министерството на вътрешните работи (ЗМВР)“
- q2: „ЗМВР“
- current text at „чл. 2“:
    **Чл. 2.** Професионалното развитие на държавните служители в МВР се основава на основните принципи на управление на държавната служба в МВР, определени в Закона за Министерството на вътрешните работи (ЗМВР).

### §2 (block 2, section body)
§ 2. В чл. 7 се правят следните изменения и допълнения:
- current text at „чл. 7“:
    **Чл. 7.**
    (1) Ръководител на структура на МВР, в щата на която е заеманата длъжност, предприема действия за предлагане на държавния служител на друга длъжност в следните случаи:
    1. съкращаване на длъжността;
    2. прекратяване на пълномощията на изборната длъжност, когато предишната заемана длъжност не е вакантна;
    3. отказ или отнемане на разрешение за достъп до класифицирана информация;
    4. установяване на несъвместимост в случаите по чл. 153, ал. 3, т. 1 ЗМВР след подадена декларация;
    5. отмяна на заповедта за прекратяване на служебното правоотношение, когато предишната заемана длъжност не е вакантна;
    6. (изм. - ДВ, бр. 29 от 2015 г.) по чл. 164, ал. 3 ЗМВР.
    (2) Когато в същата структура няма друга длъжност, ръководителят изисква информация от другите структури на МВР за наличието на такава вакантна длъжност.
    (3) Вакантни длъжности по ал. 2 от разпределените по щатовете на структурите на МВР са:
    1. длъжности, на които не са назначени стажанти;
    2. длъжности, на които временно не са преназначени служители;
    3. длъжности, за които няма обявен конкурс.
    (4) Предлагането на друга длъжност, съгласието или отказът на служителя да я заеме се удостоверяват писмено със съставянето на протокол с подписите, трите имена и длъжностите на двама служители.
    (5) Ръководителят на приемащата структура преназначава или изготвя предложение до министъра на вътрешните работи за преназначаване на служителя, приел предложената длъжност.
    (6) В случаите по ал. 1, т. 5 на държавния служител се предлага и се преназначава на равностойна длъжност.
    (7) Преназначаването се извършва в тридесетдневен срок от възникване на обстоятелствата по ал. 1, т. 1 – 4 и 6.
    (8) Преназначаването по ал. 1, т. 5 се извършва в тридесетдневен срок от явяване на държавния служител да заеме длъжността, на която е възстановен.

### §2.1 (block 3, section body)
1. В ал. 1:

### §2.1.а (block 4, section body)
а) в т. 5 след думата „вакантна“ се добавя „или е съкратена“;
- q1: „вакантна“
- q2: „или е съкратена“

### §2.1.б (block 5, section body)
б) в т. 6 след думите „ал. 3“ се поставя запетая и се добавя „т. 2“.
- q1: „ал. 3“
- q2: „т. 2“

### §2.2 (block 6, section body)
2. В ал. 6 думите „равностойна длъжност“ се заменят с „длъжност в рамките на съответния вид по чл. 143, ал. 1 ЗМВР“.
- q1: „равностойна длъжност“
- q2: „длъжност в рамките на съответния вид по чл. 143, ал. 1 ЗМВР“
- „чл. 143, ал. 1“: 'чл. 143, ал. 1' names 0 place(s) in the act

### §2.3 (block 7, section body)
3. В ал. 7 се създава изречение второ: „В случаите по ал. 1, т. 6, когато за другата длъжност се изисква професионална квалификация, която служителят не притежава, преназначаването се извършва в тридесетдневен срок от успешното завършване на съответния курс.“
- q1: „В случаите по ал. 1, т. 6, когато за другата длъжност се изисква професионална квалификация, която служителят не притежава, преназначаването се извършва в тридесетдневен срок от успешното завършване на съответния курс.“

### §3 (block 8, section body)
§ 3. Създава се чл. 7а:
- quoted block 9: „Чл. 7а. (1) В случаите по чл. 164, ал. 3, т. 1 ЗМВР заповедта за преназначаване на друга длъжност се издава в тридесетдневен срок от установяване на незадоволителните резултати в служебната дейност. Когато за другата длъжност се изисква професионална квалификация, която служителят не притежава, заповедта се издава в тридесетдневен срок от успешното завършване на съответния курс.
- quoted block 10: (2) Отказът на служителя да заеме длъжността, на която е преназначен, се удостоверява писмено със съставянето на протокол с подписите, трите имена и длъжностите на двама служители.“
- „чл. 7а“: 'чл. 7а' names 0 place(s) in the act

### §4 (block 11, section body)
§ 4. В чл. 11, ал. 1 думите „и 4“ се заличават.
- q1: „и 4“
- current text at „чл. 11, ал. 1“:
    (1) (Доп. - ДВ, бр. 29 от 2017 г.) Преназначаването по този раздел се извършва, ако служителят отговаря на изискванията за заемане на новата длъжност и ако е изтекъл съответният тригодишен срок по чл. 173, ал. 3 и 4 ЗМВР.

### §5 (block 13, section final)
§ 5. Наредбата влиза в сила от деня на обнародването й в „Държавен вестник“.
- q1: „Държавен вестник“
