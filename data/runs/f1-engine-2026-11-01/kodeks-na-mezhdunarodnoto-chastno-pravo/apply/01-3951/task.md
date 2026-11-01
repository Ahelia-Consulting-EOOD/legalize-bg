# Apply the amending material of ДВ бр. 59/2007 to kodeks-na-mezhdunarodnoto-chastno-pravo

You read the instructions of an amending act and turn each into operations on the act's text, in the form below. You never retype the act's words: a new text is a reference to the quoted blocks (their indices), an old or new string is a reference to a quoted segment of the instruction (q1, q2, … in order of appearance), an address is written as the Gazette writes it („чл. 36, ал. 1, т. 5“, „§ 3“, „глава втора, раздел V“, „Приложение № 3“, „наименованието“). An instruction that changes no text of this act (entry into force, a transitional rule, an instruction aimed at another act) is `no_text_change`. An instruction that changes this act's text in a way you cannot express in the closed set is `outside_set` with a note that says what it does: the script stops the act for the owner.

Kinds: `replace_provision`: the addressed provision (article, alinea, item, letter, §) is replaced whole by the quoted text (blocks); `replace_words`: inside the addressed provision the words old are replaced by new; everywhere: true when the instruction says „навсякъде“; `delete_words`: inside the addressed provision the words old are deleted; `insert_words`: inside the addressed provision new is inserted after the words anchor, or at the end (where: end) or the start (where: start); `insert_provision`: a new provision (blocks) is inserted after the sibling named by after, at the address it will carry; `repeal`: the addressed provision is repealed: its number stays with the repeal marker, its text and children go; `renumber`: the addressed provision becomes the number in to (досегашната ал. 2 става ал. 3); `replace_heading`: the addressed heading, or the act's title (address наименованието), takes the words in new (a quoted segment or blocks); `insert_heading`: a new heading (blocks) is inserted after the provision or heading named by after; `replace_annex`: the annex named by address is replaced whole by the quoted blocks; `insert_annex`: a new annex (blocks) is appended after the annex named by after, or at the end of the act; `repeal_annex`: the annex named by address is repealed: its heading stays with the repeal marker, its rows go; `corrigendum`: a corrigendum: inside the addressed provision the words old are replaced by new, marked Попр.; `no_text_change`: the instruction changes no text of this act (entry into force, a transitional rule, an instruction for another act); `outside_set`: the instruction changes this act's text in a way none of the kinds above expresses; the note says what it does, and the script stops the act for the owner.

Write exactly one JSON object to `data/runs/f1-engine-2026-11-01/kodeks-na-mezhdunarodnoto-chastno-pravo/apply/01-3951/answer.json`: {"material": <id>, "operations": [...]}, one or more operations per instruction id, in the material's order; nothing else, no prose, no code fence. Each operation is an object with these keys and no others: `id` (the instruction id as written above, e.g. "§3.1"), `kind` (one of the kinds), `address` (the provision, in the Gazette's grammar; not for no_text_change), and by kind: `blocks` ([first, last] block indices of the quoted text, for replace_provision, insert_provision, insert_heading, replace_annex, insert_annex, or replace_heading with quoted blocks), `after` (the sibling the new text follows, for the insert kinds), `old` and `new` (segment references like "q1", for replace_words, delete_words, corrigendum, insert_words, replace_heading), `anchor` and `where` (after | before | end | start, for insert_words), `to` (the new number, for renumber), `everywhere` (true when the instruction says навсякъде, for replace_words), `note` (free text, required for outside_set). Where the Gazette's nested quotation marks cut a segment short (q1 ends before the inner quote), give `old`, `new` or `anchor` as {"text": "…"} with the words copied exactly from the instruction line above, quotation marks included; the script checks they stand there. Example: {"id": "§1.1", "kind": "replace_words", "address": "чл. 36, ал. 1", "old": "q1", "new": "q2"}.

## The instructions
### §7 (block 2620, section transitional_final)
§ 7. В Кодекса на международното частно право (ДВ, бр. 42 от 2005 г.) се правят следните изменения:

### §7.1 (block 2621, section transitional_final)
1. В чл. 12, ал. 1 думите “чл. 83” се заменят с “чл. 109”.
- q1: „чл. 83“
- q2: „чл. 109“
- current text at „чл. 12, ал. 1“:
    (1) Делата по чл. 83 от Гражданския процесуален кодекс относно намиращи се в Република България недвижими вещи, делата за изпълнение или обезпечение върху такива вещи, както и делата за прехвърляне или удостоверяване на вещни права върху тях са изключително подведомствени на българските съдилища и други органи.
- current text at „чл. 83“:
    Произход **Чл. 83.**
    (1) Произходът се урежда от правото на държавата, чието гражданство детето е придобило към момента на раждането.
    (2) Въпреки разпоредбата на ал. 1 може да се приложи, ако това е по-благоприятно за детето:
    1. правото на държавата, на която детето е гражданин или в която има обичайно местопребиваване към момента на установяване на произхода, или
    2. правото, което е приложимо към личните отношения между родителите към момента на раждането.
    (3) Препращането към правото на трета държава се приема, когато това право допуска установяването на произхода на детето.
    (4) Припознаването е действително, ако отговаря на отечественото право на лицето, което го е извършило, или на отечественото право на детето към момента на припознаването, или на правото на държавата, в която е обичайното местопребиваване на детето към момента на припознаването.
    (5) Формата на припознаването се урежда от правото на държавата, в която то е извършено, или от приложимото право съгласно ал. 4.
- current text at „чл. 109“:
    Увреждане на околната среда **Чл. 109.** Задълженията, произтичащи от увреждане на околната среда, се уреждат от правото на държавата, на чиято територия вредата е настъпила или има опасност да настъпи, освен ако увреденото лице е избрало правото на държавата, в която е извършено вредоносното деяние.

### §7.2 (block 2622, section transitional_final)
2. В чл. 14 думите “чл. 84” се заменят с “чл. 110”.
- q1: „чл. 84“
- q2: „чл. 110“
- current text at „чл. 14“:
    Компетентност по дела при наследяване **Чл. 14.** Българските съдилища и други органи са компетентни по исковете по чл. 84 от Гражданския процесуален кодекс и другите производства, свързани с наследяване, когато наследодателят към момента на неговата смърт е имал обичайно местопребиваване в Република България или е бил български гражданин, както и когато част от имуществото му се намира в Република България.
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
- current text at „чл. 110“:
    Нарушаване на права върху обекти на интелектуална собственост **Чл. 110.** Задълженията, произтичащи от нарушаване на авторски права, на права, сродни на авторското, и на права върху обекти на индустриална собственост, се уреждат от правото на държавата, в която се търси закрилата на правото.

### §7.3 (block 2623, section transitional_final)
3. В чл. 19, ал. 1 думите “чл. 80, ал. 1, буква “г” се заменят с “чл. 104, т. 5”.
- q1: „чл. 80, ал. 1, буква “
- q2: „чл. 104, т. 5“
- current text at „чл. 19, ал. 1“:
    (1) Българските съдилища са изключително компетентни по искове по чл. 80, ал. 1, буква “г” от Гражданския процесуален кодекс, когато юридическото лице е регистрирано в Република България.
- current text at „чл. 80, ал. 1“:
    (1) Изборът на приложимо право по чл. 79, ал. 4 трябва да бъде в писмена форма с дата и подпис на съпрузите.
- „чл. 104, т. 5“: 'чл. 104, т. 5' names 0 place(s) in the act

### §7.4 (block 2624, section transitional_final)
4. В чл. 21, ал. 2 думите “чл. 104” се заменят с “чл. 211”.
- q1: „чл. 104“
- q2: „чл. 211“
- current text at „чл. 21, ал. 2“:
    (2) Когато българските съдилища са международно компетентни по първоначалния иск, те са компетентни и по насрещния иск при условията на чл. 104 от Гражданския процесуален кодекс.
- current text at „чл. 104“:
    Неприложимост на разпоредбите на тази глава **Чл. 104.** Разпоредбите на тази глава не се прилагат към задълженията, произтичащи от менителница, запис на заповед и чек.
- „чл. 211“: 'чл. 211' names 0 place(s) in the act

### §7.5 (block 2625, section transitional_final)
5. В чл. 23, ал. 1, изречение второ думите “най-късно до приключване на първото заседание по делото” се заменят с “в срока за отговор на исковата молба”.
- q1: „най-късно до приключване на първото заседание по делото“
- q2: „в срока за отговор на исковата молба“
- current text at „чл. 23, ал. 1“:
    (1) Когато предмет на делото е имуществено право и спорът не е от изключителната компетентност на българските съдилища, то може да бъде възложено на чуждестранен съд с писмено споразумение между страните. Когато българският съд е сезиран при наличие на такова споразумение, отводът на ответника трябва да бъде заявен най-късно до приключване на първото заседание по делото и преди той да е взел становище по съществото на спора. Изречение първо не се прилага по исковете за издръжка.

### §7.6 (block 2626, section transitional_final)
6. В чл. 24 думите “до приключване на първото заседание по делото” се заменят с “в срока за отговор на исковата молба”.
- q1: „до приключване на първото заседание по делото“
- q2: „в срока за отговор на исковата молба“
- current text at „чл. 24“:
    Мълчаливо учредяване на компетентност на българския съд **Чл. 24.** Когато компетентността на българските съдилища може да бъде уговорена със споразумение по чл. 23, ал. 1, тя се учредява и без такова споразумение, ако ответникът до приключване на първото заседание по делото я приеме изрично или мълчаливо чрез действия по съществото на спора.

### §7.7 (block 2627, section transitional_final)
7. В чл. 30, ал. 2 думите “чл. 133” се заменят с “чл. 164”.
- q1: „чл. 133“
- q2: „чл. 164“
- current text at „чл. 30, ал. 2“:
    (2) Ако правото, приложимо по съществото на делото, разрешава свидетелски показания за обстоятелствата по чл. 133 от Гражданския процесуален кодекс, тези доказателства са допустими, ако фактът се е осъществил на територията на държавата, чието право е приложимо.
- „чл. 133“: 'чл. 133' names 0 place(s) in the act
- „чл. 164“: 'чл. 164' names 0 place(s) in the act
