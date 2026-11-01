# Apply the amending material of ДВ бр. 87/2014 to naredba-8121z-310-ot-17-yuli-2014-g-za-prenaznachavane-na-darzhavnite-sluzhiteli

You read the instructions of an amending act and turn each into operations on the act's text, in the form below. You never retype the act's words: a new text is a reference to the quoted blocks (their indices), an old or new string is a reference to a quoted segment of the instruction (q1, q2, … in order of appearance), an address is written as the Gazette writes it („чл. 36, ал. 1, т. 5“, „§ 3“, „глава втора, раздел V“, „Приложение № 3“, „наименованието“). An instruction that changes no text of this act (entry into force, a transitional rule, an instruction aimed at another act) is `no_text_change`. An instruction that changes this act's text in a way you cannot express in the closed set is `outside_set` with a note that says what it does: the script stops the act for the owner.

Kinds: `replace_provision`: the addressed provision (article, alinea, item, letter, §) is replaced whole by the quoted text (blocks); `replace_words`: inside the addressed provision the words old are replaced by new; everywhere: true when the instruction says „навсякъде“; `delete_words`: inside the addressed provision the words old are deleted; `insert_words`: inside the addressed provision new is inserted after the words anchor, or at the end (where: end) or the start (where: start); `insert_provision`: a new provision (blocks) is inserted after the sibling named by after, at the address it will carry; `repeal`: the addressed provision is repealed: its number stays with the repeal marker, its text and children go; `renumber`: the addressed provision becomes the number in to (досегашната ал. 2 става ал. 3); `replace_heading`: the addressed heading, or the act's title (address наименованието), takes the words in new (a quoted segment or blocks); `insert_heading`: a new heading (blocks) is inserted after the provision or heading named by after; `replace_annex`: the annex named by address is replaced whole by the quoted blocks; `insert_annex`: a new annex (blocks) is appended after the annex named by after, or at the end of the act; `repeal_annex`: the annex named by address is repealed: its heading stays with the repeal marker, its rows go; `corrigendum`: a corrigendum: inside the addressed provision the words old are replaced by new, marked Попр.; `no_text_change`: the instruction changes no text of this act (entry into force, a transitional rule, an instruction for another act); `outside_set`: the instruction changes this act's text in a way none of the kinds above expresses; the note says what it does, and the script stops the act for the owner.

Write exactly one JSON object to `data/runs/f1-engine-2026-11-01/naredba-8121z-310-ot-17-yuli-2014-g-za-prenaznachavane-na-darzhavnite-sluzhiteli/apply/01-88705/answer.json`: {"material": <id>, "operations": [...]}, one or more operations per instruction id, in the material's order; nothing else, no prose, no code fence. Each operation is an object with these keys and no others: `id` (the instruction id as written above, e.g. "§3.1"), `kind` (one of the kinds), `address` (the provision, in the Gazette's grammar; not for no_text_change), and by kind: `blocks` ([first, last] block indices of the quoted text, for replace_provision, insert_provision, insert_heading, replace_annex, insert_annex, or replace_heading with quoted blocks), `after` (the sibling the new text follows, for the insert kinds), `old` and `new` (segment references like "q1", for replace_words, delete_words, corrigendum, insert_words, replace_heading), `anchor` and `where` (after | before | end | start, for insert_words), `to` (the new number, for renumber), `everywhere` (true when the instruction says навсякъде, for replace_words), `note` (free text, required for outside_set). Where the Gazette's nested quotation marks cut a segment short (q1 ends before the inner quote), give `old`, `new` or `anchor` as {"text": "…"} with the words copied exactly from the instruction line above, quotation marks included; the script checks they stand there. Example: {"id": "§1.1", "kind": "replace_words", "address": "чл. 36, ал. 1", "old": "q1", "new": "q2"}.

## The instructions
### §1 (block 1, section body)
§ 1. В чл. 12, ал. 2 се създава изречение второ: „При липса на служител, отговарящ на изискванията за прослужени години на държавна служба в МВР, по изключение може да бъде временно преназначен на по-висока длъжност държавен служител, който има прослужени години на държавна служба в МВР не по-малко от две трети от сроковете по чл. 3, ал. 1, т. 2.“
- q1: „При липса на служител, отговарящ на изискванията за прослужени години на държавна служба в МВР, по изключение може да бъде временно преназначен на по-висока длъжност държавен служител, който има прослужени години на държавна служба в МВР не по-малко от две трети от сроковете по чл. 3, ал. 1, т. 2.“
- current text at „чл. 12, ал. 2“:
    (2) Държавният служител може да бъде временно преназначен на по-висока длъжност, когато отговаря на изискванията за заемане на длъжността.
- current text at „чл. 3, ал. 1, т. 2“:
    2. прослужени години на държавна служба в МВР, както следва:
    а) за висши или старши ръководни длъжности – не по-малко от 7 години, от които не по-малко от една трета на ръководни длъжности;
    б) за ръководни длъжности – не по-малко от 6 години, от които не по-малко от една трета на старши експертни, експертни или изпълнителски длъжности;
    в) за старши експертни длъжности – не по-малко от 5 години, от които не по-малко от една трета на експертни или на изпълнителски длъжности;
    г) за експертни длъжности – не по-малко от 4 години, от които не по-малко от една трета на изпълнителски длъжности;
    д) за изпълнителски длъжности – не по-малко от 3 години на младши изпълнителски длъжности.

### §2 (block 2, section body)
§ 2. В § 3, ал. 1 от преходните и заключителните разпоредби в основния текст думите „извършено за първия отчетен период на 2014 г.“ се заменят с „извършено за последния отчетен период“.
- q1: „извършено за първия отчетен период на 2014 г.“
- q2: „извършено за последния отчетен период“
- current text at „§ 3“:
    **§ 3.**
    (1) До извършването на оценка на професионалната дейност за първия отчетен период по наредбата по чл. 162, ал. 2 ЗМВР при преназначаването по чл. 3 и 4 за оценка на професионалната дейност се счита оценяването на изпълнението на целите, извършено за първия отчетен период на 2014 г. при условията и по реда на Наредба № Iз-2209 от 2012 г. за условията и реда за формиране на допълнително възнаграждение за резултати в служебната дейност (ДВ, бр. 89 от 2012 г., наричана по-нататък „Наредба № Iз-2209 от 2012 г.“), както следва:
    1. изпълнението на:
    а) общата цел – за държавните служители по чл. 26, т. 2, 4, 6 и 7 от Наредба № Iз-2209 от 2012 г.;
    б) общата цел и на подцелите или специфичната цел на съответната структура – за държавните служители по чл. 26, т. 5 от Наредба № Iз-2209 от 2012 г.;
    2. индивидуалната оценка за изпълнение на целите – за държавните служители извън посочените в т. 1.
    (2) За целите на ал. 1, т. 1:
    1. изпълнението над 100 % на общата цел, съответно на общата цел и на подцелите или специфичната цел на съответната структура съгласно Наредба № Iз-2209 от 2012 г., се приравнява на оценка на професионалната дейност „5“ по наредбата по чл. 162, ал. 2 ЗМВР;
    2. изпълнението между 81 % и 100 % на общата цел, съответно на общата цел и на подцелите или специфичната цел на съответната структура съгласно Наредба № Iз-2209 от 2012 г., се приравнява на оценка на професионалната дейност „4“ по наредбата по чл. 162, ал. 2 ЗМВР.
    (3) За целите на ал. 1, т. 2 индивидуалните оценки „5“ и „6“ по Наредба № Iз-2209 от 2012 г. се приравняват съответно на оценки на професионалната дейност „4“ и „5“ по наредбата по чл. 162, ал. 2 ЗМВР.

### §3 (block 4, section transitional)
§ 3. Наредбата влиза в сила от деня на обнародването й в „Държавен вестник“.
- q1: „Държавен вестник“
