# Apply the amending material of ДВ бр. 31/2020 to pravilnik-za-prilagane-na-zakona-za-zashtita-na-litsa-zastrasheni-vav-vrazka-s-n

You read the instructions of an amending act and turn each into operations on the act's text, in the form below. You never retype the act's words: a new text is a reference to the quoted blocks (their indices), an old or new string is a reference to a quoted segment of the instruction (q1, q2, … in order of appearance), an address is written as the Gazette writes it („чл. 36, ал. 1, т. 5“, „§ 3“, „глава втора, раздел V“, „Приложение № 3“, „наименованието“). An instruction that changes no text of this act (entry into force, a transitional rule, an instruction aimed at another act) is `no_text_change`. An instruction that changes this act's text in a way you cannot express in the closed set is `outside_set` with a note that says what it does: the script stops the act for the owner.

Kinds: `replace_provision`: the addressed provision (article, alinea, item, letter, §) is replaced whole by the quoted text (blocks); `replace_words`: inside the addressed provision the words old are replaced by new; everywhere: true when the instruction says „навсякъде“; `delete_words`: inside the addressed provision the words old are deleted; `insert_words`: inside the addressed provision new is inserted after the words anchor, or at the end (where: end) or the start (where: start); `insert_provision`: a new provision (blocks) is inserted after the sibling named by after, at the address it will carry; `repeal`: the addressed provision is repealed: its number stays with the repeal marker, its text and children go; `renumber`: the addressed provision becomes the number in to (досегашната ал. 2 става ал. 3); `replace_heading`: the addressed heading, or the act's title (address наименованието), takes the words in new (a quoted segment or blocks); `insert_heading`: a new heading (blocks) is inserted after the provision or heading named by after; `replace_annex`: the annex named by address is replaced whole by the quoted blocks; `insert_annex`: a new annex (blocks) is appended after the annex named by after, or at the end of the act; `repeal_annex`: the annex named by address is repealed: its heading stays with the repeal marker, its rows go; `corrigendum`: a corrigendum: inside the addressed provision the words old are replaced by new, marked Попр.; `no_text_change`: the instruction changes no text of this act (entry into force, a transitional rule, an instruction for another act); `outside_set`: the instruction changes this act's text in a way none of the kinds above expresses; the note says what it does, and the script stops the act for the owner.

Write exactly one JSON object to `data/runs/f1-engine-2026-11-01/pravilnik-za-prilagane-na-zakona-za-zashtita-na-litsa-zastrasheni-vav-vrazka-s-n/apply/01-147261/answer.json`: {"material": <id>, "operations": [...]}, one or more operations per instruction id, in the material's order; nothing else, no prose, no code fence. Each operation is an object with these keys and no others: `id` (the instruction id as written above, e.g. "§3.1"), `kind` (one of the kinds), `address` (the provision, in the Gazette's grammar; not for no_text_change), and by kind: `blocks` ([first, last] block indices of the quoted text, for replace_provision, insert_provision, insert_heading, replace_annex, insert_annex, or replace_heading with quoted blocks), `after` (the sibling the new text follows, for the insert kinds), `old` and `new` (segment references like "q1", for replace_words, delete_words, corrigendum, insert_words, replace_heading), `anchor` and `where` (after | before | end | start, for insert_words), `to` (the new number, for renumber), `everywhere` (true when the instruction says навсякъде, for replace_words), `note` (free text, required for outside_set). Where the Gazette's nested quotation marks cut a segment short (q1 ends before the inner quote), give `old`, `new` or `anchor` as {"text": "…"} with the words copied exactly from the instruction line above, quotation marks included; the script checks they stand there. Example: {"id": "§1.1", "kind": "replace_words", "address": "чл. 36, ал. 1", "old": "q1", "new": "q2"}.

## The instructions
### §1 (block 4, section body)
§ 1. В чл. 29 се правят следните изменения и допълнения:
- current text at „чл. 29“:
    **Чл. 29.**
    (1) Директорът на Бюрото по защита е пряко подчинен на главния прокурор.
    (2) Директорът на Бюрото по защита:
    1. представлява Бюрото по защита;
    2. осъществява общото и непосредственото ръководство на Бюрото по защита;
    3. ръководи пряко планирането, организирането и контрола на оперативните дейности на Бюрото по защита;
    4. планира, разрешава, отпуска, разходва и отчита бюджетните средства по бюджета на Бюрото по защита;
    5. изготвя становища до главния прокурор относно:
    а) възможността за осигуряване и вида на мерките за предварителна защита;
    б) възможността за включване на застрашеното лице в Програмата за защита, вида на подходящите мерки и първоначалния им срок, както и необходимостта от дейности по чл. 5, ал. 5 от ЗЗЛЗВНП и създаване на нови основни данни по чл. 6, ал. 5 от ЗЗЛЗВНП;
    в) необходимостта от продължаването на мерките по Програмата за защита за всяко защитено лице, както и за изменение на вида на приложената мярка за защита;
    6. изготвя предложения до главния прокурор за:
    а) удължаване на предварителната защита;
    б) прекратяване на предварителната защита;
    в) осигуряване на дейности по чл. 5, ал. 5 от ЗЗЛЗВНП, когато необходимостта е възникнала въз основа на нови обстоятелства;
    г) създаване на нови основни данни по чл. 6, ал. 5 от ЗЗЛЗВНП, когато необходимостта е възникнала въз основа на нови обстоятелства;
    д) прекратяване действието на Програмата за защита;
    7. представя на главния прокурор отчети за изразходваните средства по прилагане на специалната защита – общо и за всеки конкретен случай;
    8. представя на главния прокурор писмените отчети за дейността на Бюрото по защита относно изпълнението на специалната защита;
    9. нарежда изпълнение на мерки за предварителна защита по реда на чл. 6, ал. 4 от ЗЗЛЗВНП;
    10. сключва писмени споразумения със застрашени лица за предоставяне на защита в тридневен срок от датата на съответното разпореждане на главния прокурор или решение на Съвета по защита;
    11. нарежда изпълнение на други мерки от Програмата за защита в случаите по чл. 17а от ЗЗЛЗВНП с изключение на мярката по чл. 6, ал. 2, т. 5 от ЗЗЛЗВНП;
    12. осигурява присъствието в наказателното производство на лица, на които е предоставена специална защита;
    13. осъществява оперативно сътрудничество с компетентните национални органи и с органи на други държави в областта на защитата на застрашени лица във връзка с наказателното производство;
    14. въз основа на международен договор или при условията на взаимност след разпореждане на главния прокурор сключва споразумения с компетентни органи на други държави;
    15. организира осъществяването на лична физическа охрана при условията и по реда на Наказателно-процесуалния кодекс (НПК);
    16. организира изпълнението на разпореждания на главния прокурор за принудително довеждане на лица до орган на съдебната власт и за обезпечаване охраната на действия по разследването;
    17.управлява човешките ресурси съобразно чл. 14д, ал. 2 от ЗЗЛЗВНП и правилата по чл. 28, ал. 2.
    (3) В изпълнение на правомощията си по ал. 2 директорът на Бюрото по защита издава заповеди.
    (4) При изпълнение на функциите си директорът на Бюрото по защита се подпомага от заместник-директор. Заместник-директорът замества директора при ползване на законоустановен отпуск, командироване в страната и в чужбина и при други случаи на негово отсъствие.

### §1.1 (block 5, section body)
1. В ал. 2:

### §1.1.а (block 6, section body)
а) създава се нова т. 17:
- quoted block 7: „17. организира осъществяването на охраната на прокурори и следователи;“

### §1.1.б (block 8, section body)
б) досегашната т. 17 става т. 18.

### §1.2 (block 9, section body)
2. Алинея 4 се изменя така:
- quoted block 10: „(4) При изпълнение на функциите си директорът на Бюрото по защита се подпомага от заместник-директори, чийто брой се определя с длъжностното разписание на служителите в структурите на Бюрото по защита по Закона за Министерството на вътрешните работи. Заместник-директорите заместват директора при ползване на законоустановен отпуск, командироване в страната и в чужбина и при други случаи на негово отсъствие.“

### §1.3 (block 11, section body)
3. Създава се ал. 5:
- quoted block 12: „(5) Директорът определя със заповед ресорните функции на заместник-директорите.“

### §2 (block 13, section body)
§ 2. В чл. 30 се правят следните изменения и допълнения:
- current text at „чл. 30“:
    **Чл. 30.**
    (1) Служителите на Бюрото по защита са:
    1. държавните служители, по отношение на които се прилагат разпоредбите на част трета, глави седма – дванадесета от ЗМВР;
    2. държавните служители, чийто статут се урежда със Закона за държавния служител;
    3. лицата, работещи по трудово правоотношение, чийто статут се урежда при условията и по реда на Кодекса на труда и ЗМВР.
    (2) Служителите изпълняват възложените им задачи и отговарят пред преките си ръководители за изпълнението на работата съобразно длъжностните си характеристики.
    (3) Държавните служители, които изпълняват специфични служебни дейности по смисъла на § 1 от допълнителната разпоредба на ЗЗЛЗВНП, могат:
    1. да използват способи и средства, гарантиращи тяхната лична безопасност и прикритие на самоличността им;
    2. при условията на конспиративност:
    а) да използват сигнално-охранителни и известителни системи, системи за контрол и системи за видеонаблюдение, охранително осветление, комуникационни средства, транспортни средства, съответно оборудвани служебни помещения и др.;
    б) да осъществяват контрол по спазване на поетите задължения по сключените споразумения от защитените лица;
    3. да организират пропускателен режим в обекти, свързани със застрашените/защитените лица.
    (4) Извън изпълнението на специалната защита държавните служители, които изпълняват специфични служебни дейности по смисъла на § 1 от допълнителната разпоредба на ЗЗЛЗВНП, извършват дейности по:
    1. принудително довеждане на лица до орган на съдебната власт;
    2. охрана и обезпечаване на действия по разследването в наказателното производство;
    3. организиране и осъществяване на лична физическа охрана при условията на НПК;
    4. подпомагане на организацията и осъществяването на охраната на застрашени магистрати и членове на техните семейства.
    (5) При осъществяване на функциите си служителите по ал. 3 и 4 имат специфични права и задължения по чл. 14д, ал. 1 от ЗЗЛЗВНП, за чието изпълнение получават съдействие от основни структури на Министерството на вътрешните работи.
    (6) Условията и редът за прилагане на чл. 14д, ал. 2 от ЗЗЛЗВНП се определят с правила, утвърдени от главния прокурор по предложение на директора на Бюрото по защита.
    (7) На служителите на Бюрото по защита, изпълняващи специфични служебни дейности по смисъла на § 1 от допълнителната разпоредба на ЗЗЛЗВНП, при необходимост с разпореждане на директора на Бюрото по защита се осигурява психологична помощ.

### §2.1 (block 14, section body)
1. В ал. 4 т. 4 се изменя така:
- quoted block 15: „4. подпомагане на организацията и осъществяването на охраната на застрашени прокурори и следователи.“

### §2.2 (block 16, section body)
2. В ал. 5 след думите „Министерството на вътрешните работи“ се добавя „и на Главна дирекция „Охрана“ към министъра на правосъдието“.
- q1: „Министерството на вътрешните работи“
- q2: „Охрана“

### §3 (block 18, section final)
§ 3. Постановлението влиза в сила от деня на обнародването му в „Държавен вестник“.
- q1: „Държавен вестник“
