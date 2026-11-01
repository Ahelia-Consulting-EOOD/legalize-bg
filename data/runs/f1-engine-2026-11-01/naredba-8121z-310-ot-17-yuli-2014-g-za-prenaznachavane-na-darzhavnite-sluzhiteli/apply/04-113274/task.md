# Apply the amending material of ДВ бр. 29/2017 to naredba-8121z-310-ot-17-yuli-2014-g-za-prenaznachavane-na-darzhavnite-sluzhiteli

You read the instructions of an amending act and turn each into operations on the act's text, in the form below. You never retype the act's words: a new text is a reference to the quoted blocks (their indices), an old or new string is a reference to a quoted segment of the instruction (q1, q2, … in order of appearance), an address is written as the Gazette writes it („чл. 36, ал. 1, т. 5“, „§ 3“, „глава втора, раздел V“, „Приложение № 3“, „наименованието“). An instruction that changes no text of this act (entry into force, a transitional rule, an instruction aimed at another act) is `no_text_change`. An instruction that changes this act's text in a way you cannot express in the closed set is `outside_set` with a note that says what it does: the script stops the act for the owner.

Kinds: `replace_provision`: the addressed provision (article, alinea, item, letter, §) is replaced whole by the quoted text (blocks); `replace_words`: inside the addressed provision the words old are replaced by new; everywhere: true when the instruction says „навсякъде“; `delete_words`: inside the addressed provision the words old are deleted; `insert_words`: inside the addressed provision new is inserted after the words anchor, or at the end (where: end) or the start (where: start); `insert_provision`: a new provision (blocks) is inserted after the sibling named by after, at the address it will carry; `repeal`: the addressed provision is repealed: its number stays with the repeal marker, its text and children go; `renumber`: the addressed provision becomes the number in to (досегашната ал. 2 става ал. 3); `replace_heading`: the addressed heading, or the act's title (address наименованието), takes the words in new (a quoted segment or blocks); `insert_heading`: a new heading (blocks) is inserted after the provision or heading named by after; `replace_annex`: the annex named by address is replaced whole by the quoted blocks; `insert_annex`: a new annex (blocks) is appended after the annex named by after, or at the end of the act; `repeal_annex`: the annex named by address is repealed: its heading stays with the repeal marker, its rows go; `corrigendum`: a corrigendum: inside the addressed provision the words old are replaced by new, marked Попр.; `no_text_change`: the instruction changes no text of this act (entry into force, a transitional rule, an instruction for another act); `outside_set`: the instruction changes this act's text in a way none of the kinds above expresses; the note says what it does, and the script stops the act for the owner.

Write exactly one JSON object to `data/runs/f1-engine-2026-11-01/naredba-8121z-310-ot-17-yuli-2014-g-za-prenaznachavane-na-darzhavnite-sluzhiteli/apply/04-113274/answer.json`: {"material": <id>, "operations": [...]}, one or more operations per instruction id, in the material's order; nothing else, no prose, no code fence. Each operation is an object with these keys and no others: `id` (the instruction id as written above, e.g. "§3.1"), `kind` (one of the kinds), `address` (the provision, in the Gazette's grammar; not for no_text_change), and by kind: `blocks` ([first, last] block indices of the quoted text, for replace_provision, insert_provision, insert_heading, replace_annex, insert_annex, or replace_heading with quoted blocks), `after` (the sibling the new text follows, for the insert kinds), `old` and `new` (segment references like "q1", for replace_words, delete_words, corrigendum, insert_words, replace_heading), `anchor` and `where` (after | before | end | start, for insert_words), `to` (the new number, for renumber), `everywhere` (true when the instruction says навсякъде, for replace_words), `note` (free text, required for outside_set). Where the Gazette's nested quotation marks cut a segment short (q1 ends before the inner quote), give `old`, `new` or `anchor` as {"text": "…"} with the words copied exactly from the instruction line above, quotation marks included; the script checks they stand there. Example: {"id": "§1.1", "kind": "replace_words", "address": "чл. 36, ал. 1", "old": "q1", "new": "q2"}.

## The instructions
### §1 (block 2, section body)
§ 1. В чл. 1 след думите „ал. 1, т. 1“ се добавя „и ал. 3“, а думите „и по § 86 от преходните и заключителните разпоредби на Закона за изменение и допълнение на Закона за Министерството на вътрешните работи (ДВ, бр. 14 от 2015 г.)“ се заличават.
- q1: „ал. 1, т. 1“
- q2: „и ал. 3“
- q3: „и по § 86 от преходните и заключителните разпоредби на Закона за изменение и допълнение на Закона за Министерството на вътрешните работи (ДВ, бр. 14 от 2015 г.)“
- current text at „чл. 1“:
    **Чл. 1.** (Изм. - ДВ, бр. 29 от 2015 г.) С тази наредба се определят условията и редът за преназначаване, както и редът за временно преназначаване на държавните служители по чл. 142, ал. 1, т. 1 от Закона за Министерството на вътрешните работи (ЗМВР) и по § 86 от преходните и заключителните разпоредби на Закона за изменение и допълнение на Закона за Министерството на вътрешните работи (ДВ, бр. 14 от 2015 г.).
- „§ 86“: '§ 86' names 0 place(s) in the act

### §2 (block 3, section body)
§ 2. Член 3 се изменя така:
- quoted block 4: „Чл. 3. Държавният служител се преназначава на по-висока по вид длъжност по чл. 143, ал. 1 ЗМВР по предложение на ръководителя на съответната структура след класиране от конкурс, проведен при условията и по реда на наредбата по чл. 163, ал. 1 ЗМВР, и след успешно завършване на съответната професионална подготовка.“
- current text at „чл. 3“:
    **Чл. 3.** (Изм. - ДВ, бр. 29 от 2015 г.) Държавният служител се преназначава на по-висока по вид длъжност по чл. 143, ал. 1 ЗМВР по предложение на председателя на конкурсната комисия след класиране от конкурс, проведен при условията и по реда на наредбата по чл. 163, ал. 1 ЗМВР. Предложението се прави чрез ръководителя на съответната структура.

### §3 (block 5, section body)
§ 3. Член 4а се изменя така:
- quoted block 6: „Чл. 4а. (1) За преназначаване на длъжност в рамките на всеки вид длъжност по чл. 143, ал. 1 ЗМВР органът по преназначаване по чл. 158 или чл. 159, ал. 1 ЗМВР може да обяви със заповед провеждането на конкурентен подбор. Редът за провеждане на конкурентния подбор се определя със заповедта.
- quoted block 7: (2) В заповедта по ал. 1 се определят:
- quoted block 8: 1. вакантните длъжности;
- quoted block 9: 2. условията за участие;
- quoted block 10: 3. необходимите документи за участие, място и срок за подаването им;
- quoted block 11: 4. начин за провеждане;
- quoted block 12: 5. срок за провеждане;
- quoted block 13: 6. състав на комисията за подбор.
- quoted block 14: (3) Заповедта по ал. 1 се публикува в интранет страницата на дирекция „Човешки ресурси“ – МВР.
- quoted block 15: (4) Държавните служители могат да кандидатстват за участие в подбора, като подават заявление до ръководителя на структурата, за която е обявен подборът, чрез ръководителя на структурата по месторабота.
- quoted block 16: (5) При кандидатстване за заемане на длъжност в конкурентен подбор не се изисква съгласие на ръководителя на структурата по месторабота на служителя.
- quoted block 17: (6) За резултатите от подбора се изготвя протокол, който се утвърждава от компетентния орган по преназначаване – министъра на вътрешните работи или ръководителя на съответната структура.
- quoted block 18: (7) При избор на държавен служител за заемане на подборната длъжност не се изисква съгласие за преназначаване от ръководителя на структурата по месторабота на служителя.
- quoted block 19: (8) Ръководителят на структурата, за която е обявен подборът, е длъжен да уведоми ръководителя на структурата по месторабота на избрания държавен служител чрез подбор.“
- current text at „чл. 4а“:
    **Чл. 4а.** (Нов - ДВ, бр. 29 от 2015 г.)
    (1) За преназначаване на длъжност в рамките на длъжностите по чл. 143, ал. 1, т. 3 ЗМВР министърът на вътрешните работи може да обяви със заповед провеждането на конкурентен подбор чрез провеждане на конкурс. Редът за провеждане на конкурса се определя със заповедта.
    (2) В заповедта по ал. 1 се определят:
    1. вакантните длъжности;
    2. условията за участие;
    3. необходимите документи за участие, място и срок за подаването им;
    4. начин за провеждане;
    5. срок за провеждане;
    6. състав на конкурсната комисия.

### §4 (block 20, section body)
§ 4. В чл. 5 се правят следните изменения:
- current text at „чл. 5“:
    **Чл. 5.** (Изм. - ДВ, бр. 29 от 2015 г.)
    (1) В случаите по чл. 164, ал. 2 и 3 ЗМВР се изготвя мотивирано предложение от:
    1. главния секретар на МВР – за преназначаване на ръководителите на структури по чл. 37, ал. 1, т. 1 и 4 ЗМВР;
    2. ръководителя на съответната структура – за преназначаване на държавни служители от ръководни длъжности;
    3. прекия ръководител – за преназначаване на държавни служители от изпълнителски и младши изпълнителски длъжности.
    (2) Предложение не се изготвя за ръководителите на структури по чл. 37 ЗМВР извън посочените в ал. 1, т. 1, както и за ръководителите на звена по чл. 33, т. 7 ЗМВР.
    (3) С предложението за преназначаване по чл. 164, ал. 2 ЗМВР държавният служител се запознава срещу подпис и отразява съгласието или несъгласието си.

### §4.1 (block 21, section body)
1. В ал. 1, т. 1 цифрата „4“ се заменя с „3“.
- q1: „4“
- q2: „3“

### §4.2 (block 22, section body)
2. В ал. 2 думите „както и за ръководителите на звена по чл. 33, т. 7 ЗМВР“ и запетаята пред тях се заличават.
- q1: „както и за ръководителите на звена по чл. 33, т. 7 ЗМВР“
- „чл. 33, т. 7“: 'чл. 33, т. 7' names 0 place(s) in the act

### §5 (block 23, section body)
§ 5. В чл. 11, ал. 1 накрая се добавя „и ако е изтекъл съответният тригодишен срок по чл. 173, ал. 3 и 4 ЗМВР“.
- q1: „и ако е изтекъл съответният тригодишен срок по чл. 173, ал. 3 и 4 ЗМВР“
- current text at „чл. 11, ал. 1“:
    (1) Преназначаването по този раздел се извършва, ако служителят отговаря на изискванията за заемане на новата длъжност.
- „чл. 173, ал. 3“: 'чл. 173, ал. 3' names 0 place(s) in the act

### §6 (block 24, section body)
§ 6. В чл. 12, ал. 2 накрая се поставя запетая и се добавя „а когато е предвидено за съответната длъжност – и на изискването да е хабилитирано лице съгласно Закона за вис­шето образование и Закона за развитието на академичния състав в Република България“.
- q1: „а когато е предвидено за съответната длъжност – и на изискването да е хабилитирано лице съгласно Закона за вис­шето образование и Закона за развитието на академичния състав в Република България“
- current text at „чл. 12, ал. 2“:
    (2) (Доп. - ДВ, бр. 87 от 2014 г., изм. - ДВ, бр. 104 от 2014 г.) Държавният служител може да бъде временно преназначен на по-висока длъжност, когато отговаря на изискванията за образование, квалификация и достъп до съответното ниво на класифицирана информация за съответната длъжност.

### §7 (block 25, section body)
§ 7. В чл. 13, ал. 3 думите „както и за ръководителите на звена по чл. 33, т. 7 ЗМВР“ и запетаята пред тях се заличават.
- q1: „както и за ръководителите на звена по чл. 33, т. 7 ЗМВР“
- current text at „чл. 13, ал. 3“:
    (3) (Изм. - ДВ, бр. 29 от 2015 г.) Предложение не се изготвя за ръководителите на структури по чл. 37 ЗМВР извън посочените в чл. 5, ал. 1, т. 1, както и за ръководителите на звена по чл. 33, т. 7 ЗМВР.
- „чл. 33, т. 7“: 'чл. 33, т. 7' names 0 place(s) in the act

### §8 (block 26, section body)
§ 8. В чл. 15 се правят следните изменения и допълнения:
- current text at „чл. 15“:
    **Чл. 15.** Изпълнението на служебните задължения на длъжността, на която държавният служител е временно преназначен, започва с встъпването му в длъжност, което се удостоверява с акт за встъпване в длъжност.

### §8.1 (block 27, section body)
1. Досегашният текст става ал. 1.

### §8.2 (block 28, section body)
2. Създава се ал. 2:
- quoted block 29: „(2) При временно преназначаване в случаите на служебна необходимост изпълнението на служебните задължения на длъжността, на която държавният служител е временно преназначен, започва от деня, следващ датата на запознаването му със заповедта за временно преназначаване. Отказът на държавния служител да се запознае със заповедта се удостоверява в протокол с подписите, трите имена и длъжностите на двама служители.“

### §9 (block 30, section body)
§ 9. В § 1 от допълнителните разпоредби след думите „ал. 1, т.“ се добавя „7 и“.
- q1: „ал. 1, т.“
- q2: „7 и“
- current text at „§ 1“:
    **§ 1.** При преназначаване на длъжности в МВР, посочени в чл. 3, ал. 1, т. 14 от Закона за достъп и разкриване на документите и за обявяване на принадлежност на български граждани към Държавна сигурност и разузнавателните служби на Българската народна армия, се извършва предварителна проверка за установяване на принадлежност към органите по чл. 1 от същия закон.

### §10 (block 32, section final)
§ 10. Наредбата влиза в сила от деня на обнародването й в „Държавен вестник“.
- q1: „Държавен вестник“
