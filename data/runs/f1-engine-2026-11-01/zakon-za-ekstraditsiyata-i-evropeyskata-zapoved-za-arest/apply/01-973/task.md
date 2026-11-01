# Apply the amending material of ДВ бр. 86/2005 to zakon-za-ekstraditsiyata-i-evropeyskata-zapoved-za-arest

You read the instructions of an amending act and turn each into operations on the act's text, in the form below. You never retype the act's words: a new text is a reference to the quoted blocks (their indices), an old or new string is a reference to a quoted segment of the instruction (q1, q2, … in order of appearance), an address is written as the Gazette writes it („чл. 36, ал. 1, т. 5“, „§ 3“, „глава втора, раздел V“, „Приложение № 3“, „наименованието“). An instruction that changes no text of this act (entry into force, a transitional rule, an instruction aimed at another act) is `no_text_change`. An instruction that changes this act's text in a way you cannot express in the closed set is `outside_set` with a note that says what it does: the script stops the act for the owner.

Kinds: `replace_provision`: the addressed provision (article, alinea, item, letter, §) is replaced whole by the quoted text (blocks); `replace_words`: inside the addressed provision the words old are replaced by new; everywhere: true when the instruction says „навсякъде“; `delete_words`: inside the addressed provision the words old are deleted; `insert_words`: inside the addressed provision new is inserted after the words anchor, or at the end (where: end) or the start (where: start); `insert_provision`: a new provision (blocks) is inserted after the sibling named by after, at the address it will carry; `repeal`: the addressed provision is repealed: its number stays with the repeal marker, its text and children go; `renumber`: the addressed provision becomes the number in to (досегашната ал. 2 става ал. 3); `replace_heading`: the addressed heading, or the act's title (address наименованието), takes the words in new (a quoted segment or blocks); `insert_heading`: a new heading (blocks) is inserted after the provision or heading named by after; `replace_annex`: the annex named by address is replaced whole by the quoted blocks; `insert_annex`: a new annex (blocks) is appended after the annex named by after, or at the end of the act; `repeal_annex`: the annex named by address is repealed: its heading stays with the repeal marker, its rows go; `corrigendum`: a corrigendum: inside the addressed provision the words old are replaced by new, marked Попр.; `no_text_change`: the instruction changes no text of this act (entry into force, a transitional rule, an instruction for another act); `outside_set`: the instruction changes this act's text in a way none of the kinds above expresses; the note says what it does, and the script stops the act for the owner.

Write exactly one JSON object to `data/runs/f1-engine-2026-11-01/zakon-za-ekstraditsiyata-i-evropeyskata-zapoved-za-arest/apply/01-973/answer.json`: {"material": <id>, "operations": [...]}, one or more operations per instruction id, in the material's order; nothing else, no prose, no code fence. Each operation is an object with these keys and no others: `id` (the instruction id as written above, e.g. "§3.1"), `kind` (one of the kinds), `address` (the provision, in the Gazette's grammar; not for no_text_change), and by kind: `blocks` ([first, last] block indices of the quoted text, for replace_provision, insert_provision, insert_heading, replace_annex, insert_annex, or replace_heading with quoted blocks), `after` (the sibling the new text follows, for the insert kinds), `old` and `new` (segment references like "q1", for replace_words, delete_words, corrigendum, insert_words, replace_heading), `anchor` and `where` (after | before | end | start, for insert_words), `to` (the new number, for renumber), `everywhere` (true when the instruction says навсякъде, for replace_words), `note` (free text, required for outside_set). Where the Gazette's nested quotation marks cut a segment short (q1 ends before the inner quote), give `old`, `new` or `anchor` as {"text": "…"} with the words copied exactly from the instruction line above, quotation marks included; the script checks they stand there. Example: {"id": "§1.1", "kind": "replace_words", "address": "чл. 36, ал. 1", "old": "q1", "new": "q2"}.

## The instructions
### §10 (block 2409, section transitional_final)
§ 10. В Закона за екстрадицията и Европейската заповед за арест (ДВ, бр. 46 от 2005 г.) се правят следните изменения:

### §10.1 (block 2410, section transitional_final)
1. В чл. 13:
- current text at „чл. 13“:
    Временно задържане **Чл. 13.**
    (1) В неотложни случаи компетентните органи на молещата държава могат да поискат от Министерството на правосъдието или от Върховната касационна прокуратура временно задържане на исканото лице преди изпращането на молба за екстрадиция.
    (2) В молбата за временно задържане се посочва наличието на акт за задържане, за привличане към наказателна отговорност или присъда и намерението на молещата държава да подаде молба за екстрадиция. Молбата трябва да съдържа и информация за престъплението, за което ще бъде поискана екстрадиция, за времето и мястото на извършването му, както и данни за издирваното лице.
    (3) В случай че молбата за временно задържане е подадена от държава, с която Република България няма сключен договор за екстрадиция, министърът на правосъдието уведомява Върховната касационна прокуратура за наличието на взаимност.
    (4) Молбата за временно задържане може да се изпрати по поща, телеграф, телекс, факс, по дипломатически път, чрез Международната организация на криминалната полиция (Интерпол) или по друг начин, позволяващ писменото доказване на получаването и на нейното съдържание.
    (5) След установяване местонахождението на лицето на територията на Република България и самоличността му Върховната касационна прокуратура го задържа за срок до 72 часа и изпраща молбата за временно задържане заедно с всички документи на окръжния прокурор, в чийто район се намира лицето.
    (6) В срока по ал. 5 окръжният прокурор назначава защитник и преводач на лицето, ако не владее български език, и внася в съответния окръжен съд искане за временното му задържане.
    (7) Окръжният съд разглежда искането по реда на чл. 152а, ал. 5 и 8 от Наказателно-процесуалния кодекс и се произнася с определение, с което взема мярка временно задържане или друга мярка на процесуална принуда, която осигурява участието на лицето в производството по екстрадиция. Мярката временно задържане се взема за срок до 40 дни или за друг срок, установен в международен договор, по който Република България е страна.
    (8) Определението по ал. 7 може да се обжалва и протестира пред съответния апелативен съд в тридневен срок.
    (9) Върховната касационна прокуратура уведомява незабавно министъра на правосъдието и молещата държава за взетата мярка.
    (10) Окръжният съд по искане на задържаното лице в срока по ал. 7 може да измени мярката временно задържане в друга мярка на процесуална принуда, която осигурява участието на лицето в производството по екстрадиция, по реда на чл. 152б от Наказателно-процесуалния кодекс. Определението на окръжния съд може да се обжалва и протестира пред съответния апелативен съд в тридневен срок.
    (11) Прокурорът отменя мярката временно задържане, ако в определения от съда срок на временно задържане Република България не получи молбата за екстрадиция и документите по чл. 9, ал. 3.
    (12) Освобождаването на лицето не е пречка за ново задържане с цел екстрадиция или за извършване на самата екстрадиция, ако молбата за екстрадиция бъде получена след изтичането на срока по ал. 7.

### §10.1.а (block 2411, section transitional_final)
а) в ал. 7 думите “чл. 152а, ал. 5 и 8” се заменят с “чл. 64, ал. 3 и 5”;
- q1: „чл. 152а, ал. 5 и 8“
- q2: „чл. 64, ал. 3 и 5“
- „чл. 152а, ал. 5“: 'чл. 152а, ал. 5' names 0 place(s) in the act
- current text at „чл. 64, ал. 3“:
    (3) Когато вещите по ал. 1 подлежат на изземване или конфискация на територията на Република България, ако са необходими във връзка с висящо наказателно производство в издаващата държава членка, компетентният български съд може да вземе решение временно да бъдат задържани в Република България или временно да бъдат предадени на издаващата държава членка с условие да бъдат върнати.

### §10.1.б (block 2412, section transitional_final)
б) в ал. 10 думите “чл. 152б” се заменят с “чл. 65”.
- q1: „чл. 152б“
- q2: „чл. 65“
- „чл. 152б“: 'чл. 152б' names 0 place(s) in the act
- current text at „чл. 65“:
    Разноски **Чл. 65.**
    (1) Разноските по изпълнение на Европейска заповед за арест, направени на територията на Република България като изпълняваща държава, се поемат от нея.
    (2) Всички останали разноски се поемат от издаващата държава.

### §10.2 (block 2413, section transitional_final)
2. В чл. 15, ал. 1 думите “чл. 152а, ал. 5 и 8” се заменят с “чл. 64, ал. 3 и 5”.
- q1: „чл. 152а, ал. 5 и 8“
- q2: „чл. 64, ал. 3 и 5“
- current text at „чл. 15, ал. 1“:
    (1) В случаите на чл. 14, ал. 4, т. 4 окръжният съд разглежда незабавно искането за вземане на мярка задържане под стража по реда на чл. 152а, ал. 5 и 8 от Наказателно-процесуалния кодекс.
- „чл. 152а, ал. 5“: 'чл. 152а, ал. 5' names 0 place(s) in the act
- current text at „чл. 64, ал. 3“:
    (3) Когато вещите по ал. 1 подлежат на изземване или конфискация на територията на Република България, ако са необходими във връзка с висящо наказателно производство в издаващата държава членка, компетентният български съд може да вземе решение временно да бъдат задържани в Република България или временно да бъдат предадени на издаващата държава членка с условие да бъдат върнати.

### §10.3 (block 2414, section transitional_final)
3. В чл. 43:
- current text at „чл. 43“:
    Задържане под стража **Чл. 43.**
    (1) В срока по чл. 42, ал. 1 и 2 прокурорът внася искане в съответния окръжен съд за вземане на мярка за неотклонение задържане под стража на исканото лице.
    (2) Съдът разглежда искането незабавно по реда на чл. 152а от Наказателно-процесуалния кодекс.
    (3) Съдът назначава на лицето защитник и преводач, ако не владее български език, и го запознава с основанието за задържането му, съдържанието на Европейската заповед за арест, както и с правото му да изрази съгласие за предаване на компетентните органи на издаващата държава членка и последиците от това.
    (4) По искане на задържаното лице окръжният съд може да измени мярката задържане под стража в друга мярка, която осигурява участието му в производството по изпълнение на Европейската заповед за арест, по реда на чл. 152б от Наказателно-процесуалния кодекс.

### §10.3.а (block 2415, section transitional_final)
а) в ал. 2 думите “чл. 152а” се заменят с “чл. 64”;
- q1: „чл. 152а“
- q2: „чл. 64“
- „чл. 152а“: 'чл. 152а' names 0 place(s) in the act
- current text at „чл. 64“:
    Предаване на вещи **Чл. 64.**
    (1) По искане на издаващия орган или служебно съответният окръжен съд може да разпореди съгласно българското законодателство изземването и предаването на вещи, които:
    1. може да бъдат изискани като доказателства, или
    2. са придобити от исканото лице в резултат на престъплението.
    (2) Вещите по ал. 1 се предават и в случаите, когато Европейската заповед за арест не може да бъде изпълнена поради смърт или укриване на исканото лице.
    (3) Когато вещите по ал. 1 подлежат на изземване или конфискация на територията на Република България, ако са необходими във връзка с висящо наказателно производство в издаващата държава членка, компетентният български съд може да вземе решение временно да бъдат задържани в Република България или временно да бъдат предадени на издаващата държава членка с условие да бъдат върнати.
    (4) Правата, които Република България или трети лица са придобили върху посочените вещи, се запазват. При наличие на такива права вещите се връщат в изпълняващата държава членка на разноски на издаващата държава членка незабавно след приключване на наказателното производство.

### §10.3.б (block 2416, section transitional_final)
б) в ал. 4 думите “чл. 152б” се заменят с “чл. 65”.
- q1: „чл. 152б“
- q2: „чл. 65“
- „чл. 152б“: 'чл. 152б' names 0 place(s) in the act
- current text at „чл. 65“:
    Разноски **Чл. 65.**
    (1) Разноските по изпълнение на Европейска заповед за арест, направени на територията на Република България като изпълняваща държава, се поемат от нея.
    (2) Всички останали разноски се поемат от издаващата държава.
