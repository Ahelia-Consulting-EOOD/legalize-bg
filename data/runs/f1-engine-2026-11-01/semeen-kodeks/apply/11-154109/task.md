# Apply the amending material of ДВ бр. 103/2020 to semeen-kodeks

You read the instructions of an amending act and turn each into operations on the act's text, in the form below. You never retype the act's words: a new text is a reference to the quoted blocks (their indices), an old or new string is a reference to a quoted segment of the instruction (q1, q2, … in order of appearance), an address is written as the Gazette writes it („чл. 36, ал. 1, т. 5“, „§ 3“, „глава втора, раздел V“, „Приложение № 3“, „наименованието“). An instruction that changes no text of this act (entry into force, a transitional rule, an instruction aimed at another act) is `no_text_change`. An instruction that changes this act's text in a way you cannot express in the closed set is `outside_set` with a note that says what it does: the script stops the act for the owner.

Kinds: `replace_provision`: the addressed provision (article, alinea, item, letter, §) is replaced whole by the quoted text (blocks); `replace_words`: inside the addressed provision the words old are replaced by new; everywhere: true when the instruction says „навсякъде“; `delete_words`: inside the addressed provision the words old are deleted; `insert_words`: inside the addressed provision new is inserted after the words anchor, or at the end (where: end) or the start (where: start); `insert_provision`: a new provision (blocks) is inserted after the sibling named by after, at the address it will carry; `repeal`: the addressed provision is repealed: its number stays with the repeal marker, its text and children go; `renumber`: the addressed provision becomes the number in to (досегашната ал. 2 става ал. 3); `replace_heading`: the addressed heading, or the act's title (address наименованието), takes the words in new (a quoted segment or blocks); `insert_heading`: a new heading (blocks) is inserted after the provision or heading named by after; `replace_annex`: the annex named by address is replaced whole by the quoted blocks; `insert_annex`: a new annex (blocks) is appended after the annex named by after, or at the end of the act; `repeal_annex`: the annex named by address is repealed: its heading stays with the repeal marker, its rows go; `corrigendum`: a corrigendum: inside the addressed provision the words old are replaced by new, marked Попр.; `no_text_change`: the instruction changes no text of this act (entry into force, a transitional rule, an instruction for another act); `outside_set`: the instruction changes this act's text in a way none of the kinds above expresses; the note says what it does, and the script stops the act for the owner.

Write exactly one JSON object to `data/runs/f1-engine-2026-11-01/semeen-kodeks/apply/11-154109/answer.json`: {"material": <id>, "operations": [...]}, one or more operations per instruction id, in the material's order; nothing else, no prose, no code fence. Each operation is an object with these keys and no others: `id` (the instruction id as written above, e.g. "§3.1"), `kind` (one of the kinds), `address` (the provision, in the Gazette's grammar; not for no_text_change), and by kind: `blocks` ([first, last] block indices of the quoted text, for replace_provision, insert_provision, insert_heading, replace_annex, insert_annex, or replace_heading with quoted blocks), `after` (the sibling the new text follows, for the insert kinds), `old` and `new` (segment references like "q1", for replace_words, delete_words, corrigendum, insert_words, replace_heading), `anchor` and `where` (after | before | end | start, for insert_words), `to` (the new number, for renumber), `everywhere` (true when the instruction says навсякъде, for replace_words), `note` (free text, required for outside_set). Where the Gazette's nested quotation marks cut a segment short (q1 ends before the inner quote), give `old`, `new` or `anchor` as {"text": "…"} with the words copied exactly from the instruction line above, quotation marks included; the script checks they stand there. Example: {"id": "§1.1", "kind": "replace_words", "address": "чл. 36, ал. 1", "old": "q1", "new": "q2"}.

## The instructions
### §1 (block 10, section body)
§ 1. В чл. 62 се правят следните изменения и допълнения:
- current text at „чл. 62“:
    Оспорване на бащинство **Чл. 62.**
    (1) Съпругът на майката може да оспори, че е баща на детето, като докаже, че то не е могло да бъде заченато от него. Този иск може да бъде предявен до изтичането на една година от узнаване на раждането.
    (2) Майката може да оспори, че съпругът й е баща на детето, като докаже, че то не е могло да бъде заченато от него. Този иск може да бъде предявен до една година от раждането.
    (3) В случая по чл. 61, ал. 2, ако оспорването на бащинството на втория съпруг бъде уважено, за баща на детето се смята първият съпруг. Първият съпруг и майката могат да предявят иск за оспорване на бащинството до една година от узнаването на решението, но не по-късно от три години от влизането му в сила.
    (4) Детето може да оспори бащинството до една година от навършването на пълнолетие.
    (5) Не се допуска оспорване на бащинството, когато детето е родено при условията на асистирана репродукция, ако съпругът на майката е дал информиран писмено съгласие за извършването й.

### §1.1 (block 11, section body)
1. В ал. 1 се създават изречения трето и четвърто: „Ако обстоятелствата, опровергаващи бащинството, са узнати по-късно по независещи от ищеца причини, искът може да бъде предявен до изтичане на една година от узнаване на тези обстоятелства, но не по-късно от навършване на пълнолетие на детето. Съдът решава спора, като взема предвид интереса на детето.“
- q1: „Ако обстоятелствата, опровергаващи бащинството, са узнати по-късно по независещи от ищеца причини, искът може да бъде предявен до изтичане на една година от узнаване на тези обстоятелства, но не по-късно от навършване на пълнолетие на детето. Съдът решава спора, като взема предвид интереса на детето.“

### §1.2 (block 12, section body)
2. Алинея 4 се изменя така:
- quoted block 13: „(4) Детето може да оспори бащинството от навършването на четиринадесетгодишна възраст до една година от навършването на пълнолетие.“

### §1.3 (block 14, section body)
3. Създава се нова ал. 5:
- quoted block 15: „(5) Трето лице, което твърди, че е биологичен баща на детето, може да оспори бащинството до изтичане на една година от узнаването на раждането. Този иск задължително се съединява с иск за установяване на произход. Съдът решава спора, като взема предвид интереса на детето.“

### §1.4 (block 16, section body)
4. Досегашната ал. 5 става ал. 6.

### §2 (block 17, section body)
§ 2. В чл. 63 се правят следните изменения и допълнения:
- current text at „чл. 63“:
    Страни по исковете за оспорване на бащинство **Чл. 63.** При оспорване на бащинство като страни се призовават майката, детето и съпругът, а когато бащинството се оспорва от втория съпруг, като страна се призовава и първият съпруг.

### §2.1 (block 18, section body)
1. Досегашният текст става ал. 1.

### §2.2 (block 19, section body)
2. Създава се ал. 2:
- quoted block 20: „(2) Страна по исковете за оспорване на бащинство може да бъде и лицето, което твърди, че е биологичен баща.“

### §3 (block 21, section body)
§ 3. В чл. 66 се правят следните изменения и допълнения:
- current text at „чл. 66“:
    Оспорване на припознаването **Чл. 66.** (Загл. изм. - ДВ, бр. 100 от 2010 г.)
    (1) Родителят или навършилото четиринадесет години дете може да оспори припознаването с писмено заявление до длъжностното лице по гражданското състояние в тримесечен срок от съобщението. Ако припознаването не бъде оспорено, то се вписва в акта за раждане.
    (2) Когато припознаването се оспори, припознаващият може в тримесечен срок от получаване на съобщението да предяви иск за установяване на произход.
    (3) Ако припознаването бъде извършено, преди да е съставен акт за раждане на детето, и родителят заяви по реда на чл. 65, ал. 1, че няма да го оспорва, припозналият се вписва веднага в акта за раждане като родител. Оспорване на припознаването от родителя след съставяне на акта за раждане не се допуска.
    (4) Ако при припознаването детето е малолетно, то може да го оспори по съдебен ред до една година от навършването на пълнолетие или от узнаването на припознаването, ако узнаването е станало по-късно. Ако искът бъде уважен, припознаването се заличава със съответна бележка в акта за раждане.
    (5) (Нова - ДВ, бр. 100 от 2010 г.) Извън случаите по ал. 1 и 4 припознаването може да бъде оспорено по съдебен ред чрез иск, предявен в едногодишен срок от извършването му, от Дирекция „Социално подпомагане“ по настоящия адрес на детето и от прокурора.

### §3.1 (block 22, section body)
1. В ал. 1 се създава ново изречение второ: „Дирекция „Социално подпомагане“ по настоящия адрес на детето може да оспори припознаването чрез възражение по същия ред, ако е в интерес на детето.“, а досегашното изречение второ става изречение трето.
- q1: „Социално подпомагане“

### §3.2 (block 23, section body)
2. Алинея 5 се изменя така:
- quoted block 24: „(5) Извън случаите по ал. 1 и 4 припознаването може да бъде оспорено от всяко лице, което твърди, че е родител на припознатия, чрез иск, предявен в едногодишен срок от узнаването на припознаването. Този иск задължително се съединява с иск за установяване на произход. Съдът решава спора, като взема предвид интереса на детето.“

### §3.3 (block 25, section body)
3. Създава се ал. 6:
- quoted block 26: „(6) Припознаването може да бъде оспорено и от прокурора в защита на обществения интерес чрез иск, предявен в едногодишен срок от узнаването му. Като ответници се призовават припозналият, припознатият и другият родител.“

### §4 (block 28, section transitional)
§ 4. За припознавания, извършени след 1 октомври 2009 г. до влизането в сила на този закон, срокът по чл. 66, ал. 5 тече от влизането в сила на закона.
- current text at „чл. 66, ал. 5“:
    (5) (Нова - ДВ, бр. 100 от 2010 г.) Извън случаите по ал. 1 и 4 припознаването може да бъде оспорено по съдебен ред чрез иск, предявен в едногодишен срок от извършването му, от Дирекция „Социално подпомагане“ по настоящия адрес на детето и от прокурора.

### §5 (block 29, section transitional)
§ 5. За лицата, за които обстоятелствата, обуславящи правото на иск по чл. 62, ал. 1, изрeчение трето и ал. 5, изречение първо, са били налице преди влизането в сила на този закон, сроковете за предявяване на съответните искове текат от влизането в сила на закона.
- current text at „чл. 62, ал. 1“:
    (1) Съпругът на майката може да оспори, че е баща на детето, като докаже, че то не е могло да бъде заченато от него. Този иск може да бъде предявен до изтичането на една година от узнаване на раждането.
