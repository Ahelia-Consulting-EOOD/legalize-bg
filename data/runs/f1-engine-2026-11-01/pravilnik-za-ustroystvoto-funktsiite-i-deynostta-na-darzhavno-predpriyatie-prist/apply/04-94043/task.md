# Apply the amending material of ДВ бр. 31/2015 to pravilnik-za-ustroystvoto-funktsiite-i-deynostta-na-darzhavno-predpriyatie-prist

You read the instructions of an amending act and turn each into operations on the act's text, in the form below. You never retype the act's words: a new text is a reference to the quoted blocks (their indices), an old or new string is a reference to a quoted segment of the instruction (q1, q2, … in order of appearance), an address is written as the Gazette writes it („чл. 36, ал. 1, т. 5“, „§ 3“, „глава втора, раздел V“, „Приложение № 3“, „наименованието“). An instruction that changes no text of this act (entry into force, a transitional rule, an instruction aimed at another act) is `no_text_change`. An instruction that changes this act's text in a way you cannot express in the closed set is `outside_set` with a note that says what it does: the script stops the act for the owner.

Kinds: `replace_provision`: the addressed provision (article, alinea, item, letter, §) is replaced whole by the quoted text (blocks); `replace_words`: inside the addressed provision the words old are replaced by new; everywhere: true when the instruction says „навсякъде“; `delete_words`: inside the addressed provision the words old are deleted; `insert_words`: inside the addressed provision new is inserted after the words anchor, or at the end (where: end) or the start (where: start); `insert_provision`: a new provision (blocks) is inserted after the sibling named by after, at the address it will carry; `repeal`: the addressed provision is repealed: its number stays with the repeal marker, its text and children go; `renumber`: the addressed provision becomes the number in to (досегашната ал. 2 става ал. 3); `replace_heading`: the addressed heading, or the act's title (address наименованието), takes the words in new (a quoted segment or blocks); `insert_heading`: a new heading (blocks) is inserted after the provision or heading named by after; `replace_annex`: the annex named by address is replaced whole by the quoted blocks; `insert_annex`: a new annex (blocks) is appended after the annex named by after, or at the end of the act; `repeal_annex`: the annex named by address is repealed: its heading stays with the repeal marker, its rows go; `corrigendum`: a corrigendum: inside the addressed provision the words old are replaced by new, marked Попр.; `no_text_change`: the instruction changes no text of this act (entry into force, a transitional rule, an instruction for another act); `outside_set`: the instruction changes this act's text in a way none of the kinds above expresses; the note says what it does, and the script stops the act for the owner.

Write exactly one JSON object to `data/runs/f1-engine-2026-11-01/pravilnik-za-ustroystvoto-funktsiite-i-deynostta-na-darzhavno-predpriyatie-prist/apply/04-94043/answer.json`: {"material": <id>, "operations": [...]}, one or more operations per instruction id, in the material's order; nothing else, no prose, no code fence. Each operation is an object with these keys and no others: `id` (the instruction id as written above, e.g. "§3.1"), `kind` (one of the kinds), `address` (the provision, in the Gazette's grammar; not for no_text_change), and by kind: `blocks` ([first, last] block indices of the quoted text, for replace_provision, insert_provision, insert_heading, replace_annex, insert_annex, or replace_heading with quoted blocks), `after` (the sibling the new text follows, for the insert kinds), `old` and `new` (segment references like "q1", for replace_words, delete_words, corrigendum, insert_words, replace_heading), `anchor` and `where` (after | before | end | start, for insert_words), `to` (the new number, for renumber), `everywhere` (true when the instruction says навсякъде, for replace_words), `note` (free text, required for outside_set). Where the Gazette's nested quotation marks cut a segment short (q1 ends before the inner quote), give `old`, `new` or `anchor` as {"text": "…"} with the words copied exactly from the instruction line above, quotation marks included; the script checks they stand there. Example: {"id": "§1.1", "kind": "replace_words", "address": "чл. 36, ал. 1", "old": "q1", "new": "q2"}.

## The instructions
### §1 (block 2, section body)
§ 1. В чл. 23, ал. 1 се създава т. 5:
- quoted block 3: „5. специализирано поделение „Опериране и експлоатация на пристанищни терминали.“
- current text at „чл. 23, ал. 1“:
    (1) Структурата на предприятието включва:
    1. главно управление;
    2. териториални поделения – клонове;
    3. специализирано поделение „Управление на корабния трафик – Черно море“;
    4. специализирано поделение „Управление на корабния трафик – река Дунав“.

### §2 (block 4, section body)
§ 2. В глава четвърта, раздел VIII. Специализирани поделения се правят следните изменения и допълнения:

### §2.1 (block 5, section body)
1. В подзаглавието след думите „Дирекция „Ръководство на корабния трафик – Черно море“ се добавя запетая, а след думите „Дирекция „Ръководство на корабния трафик – река Дунав“ се добавя „и Дирекция „Опериране и експлоатация на пристанищни терминали“.
- q1: „Ръководство на корабния трафик – Черно море“
- q2: „Ръководство на корабния трафик – река Дунав“
- q3: „Опериране и експлоатация на пристанищни терминали“

### §2.2 (block 6, section body)
2. В чл. 33, ал. 1 думата „две“ се заменя с „три“, а думите „и Ръководство на корабния трафик – река Дунав“ се заменят със запетайка и думите „Ръководство на корабния трафик – река Дунав“ и „Опериране и експлоатация на пристанищни терминали“.
- q1: „две“
- q2: „три“
- q3: „и Ръководство на корабния трафик – река Дунав“
- q4: „Ръководство на корабния трафик – река Дунав“
- q5: „Опериране и експлоатация на пристанищни терминали“
- current text at „чл. 33, ал. 1“:
    (1) В предприятието са обособени като специализирани поделения две дирекции: „Ръководство на корабния трафик – Черно море“ и „Ръководство на корабния трафик – река Дунав“.

### §3 (block 7, section body)
§ 3. В чл. 33 се създава ал. 6:
- quoted block 8: „(6) Дирекция „Опериране и експлоатация на пристанищни терминали“ извършва пристанищните услуги по чл. 116, ал. 2, т. 2 и 3 ЗМПВВППРБ при предсрочно прекратяване на договор с пристанищен оператор до сключването на нов договор по предвидения в закона ред и изпълнява следните функции:
- quoted block 9: 1. отговаря за предоставянето на пристанищните услуги в съответствие с действащата нормативна уредба и установените на терминала технология и организация;
- quoted block 10: 2. изготвя необходимите технологични карти и организира съгласуването и одобряването им по законоустановения ред;
- quoted block 11: 3. отговаря за събирането на цените за извършването на пристанищните услуги;
- quoted block 12: 4. подготвя и организира сключването на договорите с товародателите и другите клиенти на терминала;
- quoted block 13: 5. следи, координира, контролира и отговаря за изпълнението на задълженията по сключените на съответния пристанищен терминал договори с товародатели и другите клиенти на терминала;
- quoted block 14: 6. подготвя необходимите документи и подава съответните заявления за вписване на обстоятелства в регистъра на пристанищата и в регистъра на пристанищните оператори съобразно действаща нормативна уредба.“
- current text at „чл. 33“:
    Дирекция „Ръководство на корабния трафик – река Дунав“ **Чл. 33.**
    (1) В предприятието са обособени като специализирани поделения две дирекции: „Ръководство на корабния трафик – Черно море“ и „Ръководство на корабния трафик – река Дунав“.
    (2) Дирекция „Ръководство на корабния трафик – Черно море“ изпълнява функции по повишаването на безопасността и ефективността на корабоплаването, опазването на човешкия живот на море и защитата на околната среда и прилежащата брегова ивица от възможните вредни въздействия от корабоплаването и информационно обслужване на морския транспорт, като:
    1. обменя информация с други системи, предвидени в националното законодателство или в международен договор, по който Република България е страна;
    2. поддържа необходимите ресурси за осигуряване на денонощна експлоатация и предоставените й системи за обслужване съгласно националното законодателство и пълномощията от Министерския съвет;
    3. поддържа системата и базата данни за информационното обслужване на морските пристанища;
    4. предоставя услуги по информационното обслужване на морските пристанища, събира, разпределя и архивира информацията за издаване на разрешения за свободна практика и за отплаване на корабите;
    5. издава разрешения за отплаване на корабите;
    6. събира приходи от предоставени услуги за достъп до обществена информация, отнасяща се до дейността на дирекцията;
    7. поддържа брегова система за морски радиокомуникации от Морската подвижна служба;
    8. изпълнява международните ангажименти на Република България от Световната морска система за бедствие и безопасност за зона А1, зона А2 и НАВТЕКС;
    9. предоставя далекосъобщителни услуги кораб-бряг и бряг-кораб;
    10. събира, съхранява и предоставя хидрометеорологична информация;
    11. инициира действия за получаване на разрешения, сертификати, лицензии и други документи, необходими за извършване на дейностите;
    12. съвместно със структурите на Министерството на отбраната изпълнява отбранително-мобилизационни мероприятия на територията, на която се разпростират правомощията му.
    (3) Дирекцията има печат – същия като на предприятието, като в долната му част вместо „Главно управление“ се изписва текстът „Ръководство на корабния трафик – Черно море“.
    (4) Дирекция „Управления на корабния трафик – Черно море“ изпълнява функции по:
    1. осъществяване на техническо и визуално наблюдение на плавателни средства във вътрешните морски води и териториалното море на Република България, събиране, обработване и предоставяне на информация, получена чрез системата за докладване и от системите за автоматично опознаване на корабите чрез звената за управление на трафика във Варна и Бургас;
    2. предоставяне на:
    а) информация за навигационната и метеорологичната обстановка в съответните райони, както и за състоянието на бреговите служби и съоръжения, свързани с безопасността на корабоплаването;
    б) информация, препоръки и указания при възникване на аварийни ситуации с кораби, представляващи заплаха за морската безопасност и за безопасността на човешкия живот или околната среда;
    3. организиране на корабния трафик в отговорните райони с цел предотвратяване появата и развитието на опасност от авария, сблъскване, осигуряване заставането, снемането и стоенето на котвените места и кейовете в пристанищата;
    4. осъществяване на предаването и приемането на данни, обменящи се посредством електронна система, която е взаимносвързана с българската част на европейската система SafeSeaNet;
    5. спазване на процедури, инструкции и правила, одобрени от Изпълнителна агенция „Морска администрация“, и споразумения за взаимодействие с други компетентни органи;
    6. осъществяване информационното обслужване на морските пристанища, събиране, разпределяне и архивиране на информацията за издаване на разрешения за свободна практика и за отплаване на корабите;
    7. организиране денонощна операторска служба за информационно обслужване на морските пристанища;
    8. предоставяне на следните услуги:
    а) издаване на разрешения за отплаване на корабите;
    б) предоставяне на информация, свързана с пристигането, престоя и отплаването на корабите от морските пристанища;
    9. спазване на процедури, инструкции и правила, одобрени от Изпълнителна агенция „Морска администрация“, и споразумения за взаимодействие с други компетентни органи;
    10. осигуряване на функционалните изис-квания на СМСББ при осъществяване на:
    а) непрекъснато вахтено обслужване на международните радиоканали за бедствие и на асоциираните към тях радиоканали за зона А1 и зона А2;
    б) радиокомуникации за бедствие, търсене и спасяване в отговорния район за търсене и спасяване на Република България като асоциирана станция на Морския спасително-координационен център (МСКЦ);
    в) радиокомуникации за спешност в случаи на морски инциденти, представляващи опасност за екологията на Черно море и здравето на корабните екипажи;
    г) разпространение на морска информация за безопасност на радиотелефонни канали и системата НАВТЕКС като брегова радиостанция и национален координатор на системата;
    д) други общи радиокомуникации между кораби и брегови наземни телефонни абонати;
    11. осигуряване на радиокомуникации извън изискванията на СМСББ при осъществяване на:
    а) връзки с кораби при поискване от звено „Управление на корабния трафик“;
    б) непрекъснато вахтено обслужване и далекосъобщителни услуги в посока кораб-бряг и бряг-кораб на международно съгласувани работни радиоканали;
    в) прослушване на радиоканали за връзка с малки плаващи съдове, оборудвани извън изискванията на международната конвенция SOLAS;
