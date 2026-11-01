# Apply the amending material of ДВ бр. 98/2011 to naredba-5-ot-28-dekemvri-2006-g-za-tehnicheskite-pasporti-na-stroezhite

You read the instructions of an amending act and turn each into operations on the act's text, in the form below. You never retype the act's words: a new text is a reference to the quoted blocks (their indices), an old or new string is a reference to a quoted segment of the instruction (q1, q2, … in order of appearance), an address is written as the Gazette writes it („чл. 36, ал. 1, т. 5“, „§ 3“, „глава втора, раздел V“, „Приложение № 3“, „наименованието“). An instruction that changes no text of this act (entry into force, a transitional rule, an instruction aimed at another act) is `no_text_change`. An instruction that changes this act's text in a way you cannot express in the closed set is `outside_set` with a note that says what it does: the script stops the act for the owner.

Kinds: `replace_provision`: the addressed provision (article, alinea, item, letter, §) is replaced whole by the quoted text (blocks); `replace_words`: inside the addressed provision the words old are replaced by new; everywhere: true when the instruction says „навсякъде“; `delete_words`: inside the addressed provision the words old are deleted; `insert_words`: inside the addressed provision new is inserted after the words anchor, or at the end (where: end) or the start (where: start); `insert_provision`: a new provision (blocks) is inserted after the sibling named by after, at the address it will carry; `repeal`: the addressed provision is repealed: its number stays with the repeal marker, its text and children go; `renumber`: the addressed provision becomes the number in to (досегашната ал. 2 става ал. 3); `replace_heading`: the addressed heading, or the act's title (address наименованието), takes the words in new (a quoted segment or blocks); `insert_heading`: a new heading (blocks) is inserted after the provision or heading named by after; `replace_annex`: the annex named by address is replaced whole by the quoted blocks; `insert_annex`: a new annex (blocks) is appended after the annex named by after, or at the end of the act; `repeal_annex`: the annex named by address is repealed: its heading stays with the repeal marker, its rows go; `corrigendum`: a corrigendum: inside the addressed provision the words old are replaced by new, marked Попр.; `no_text_change`: the instruction changes no text of this act (entry into force, a transitional rule, an instruction for another act); `outside_set`: the instruction changes this act's text in a way none of the kinds above expresses; the note says what it does, and the script stops the act for the owner.

Write exactly one JSON object to `data/runs/f1-engine-2026-11-01/naredba-5-ot-28-dekemvri-2006-g-za-tehnicheskite-pasporti-na-stroezhite/apply/03-59312/answer.json`: {"material": <id>, "operations": [...]}, one or more operations per instruction id, in the material's order; nothing else, no prose, no code fence. Each operation is an object with these keys and no others: `id` (the instruction id as written above, e.g. "§3.1"), `kind` (one of the kinds), `address` (the provision, in the Gazette's grammar; not for no_text_change), and by kind: `blocks` ([first, last] block indices of the quoted text, for replace_provision, insert_provision, insert_heading, replace_annex, insert_annex, or replace_heading with quoted blocks), `after` (the sibling the new text follows, for the insert kinds), `old` and `new` (segment references like "q1", for replace_words, delete_words, corrigendum, insert_words, replace_heading), `anchor` and `where` (after | before | end | start, for insert_words), `to` (the new number, for renumber), `everywhere` (true when the instruction says навсякъде, for replace_words), `note` (free text, required for outside_set). Where the Gazette's nested quotation marks cut a segment short (q1 ends before the inner quote), give `old`, `new` or `anchor` as {"text": "…"} with the words copied exactly from the instruction line above, quotation marks included; the script checks they stand there. Example: {"id": "§1.1", "kind": "replace_words", "address": "чл. 36, ал. 1", "old": "q1", "new": "q2"}.

## The instructions
### §единствен (block 2, section body)
Параграф единствен. В § 2, ал. 2 от преходните и заключителните разпоредби се правят следните изменения:
- current text at „§ 2“:
    **§ 2.**
    (1) Техническите паспорти на съществуващи строежи - държавна и общинска собственост, се съставят в срок до 31 декември 2011 г.
    (2) Техническите паспорти на съществуващи строежи, с изключение на строежите по ал. 1, се съставят в следните срокове в зависимост от категорията им:
    1. от първа категория - до 31 декември 2008 г.;
    2. от втора категория - до 31 декември 2010 г.;
    3. от трета категория - до 31 декември 2012 г.;
    4. от четвърта категория - до 31 декември 2014 г.;
    5. от пета категория - до 31 декември 2016 г.
    (3) (Нова - ДВ, бр. 38 от 2008 г.) Сроковете по ал. 2, т. 1 и 2 се отнасят за сградите и съоръженията с основно производствено или технологично предназначение, когато то е определено с нормативен акт. Техническите паспорти на сгради и съоръжения със спомагателно, второстепенно или обслужващо предназначение се съставят в сроковете за съответните категории строежи.
    (4) (Предишна ал. 3 - ДВ, бр. 38 от 2008 г.) За съществуващите строежи по ал. 1 и 2, на които по време на строителството е упражняван строителен надзор (за строежите, започнати след 1 септември 1999 г.) и които са въведени в експлоатация преди влизане в сила на наредбата, техническият паспорт може да се състави, без да се извършва обследване на строежа по глава трета, ако:
    1. лицето, на което е възложено да състави паспорта, удостовери, че строежът съответства на одобрената проектна (екзекутивна) документация и на разрешението за ползване (удостоверението за въвеждане в експлоатация);
    2. техническият паспорт се съставя в срок до две години от влизане в сила на наредбата.
    (5) (Предишна ал. 4 - ДВ, бр. 38 от 2008 г.) Областните управители и общинските съвети одобряват график за изработване на техническите паспорти на строежите по ал. 1 и заявяват необходимите разходи за утвърждаване със Закона за държавния бюджет за съответната година, съответно с общинския бюджет, приет по реда на Закона за общинските бюджети.
    (6) (Предишна ал. 5 - ДВ, бр. 38 от 2008 г.) След изтичане на сроковете по ал. 2 кметът на общината възлага съставянето на технически паспорти на строежите, за които те не са съставени, за сметка на техните собственици, като за извършените разходи общината се снабдява с изпълнителен лист за събиране на вземането съгласно § 2, ал. 1 ЗУТ.
    (7) (Предишна ал. 6 - ДВ, бр. 38 от 2008 г.) Кметовете на общини в сроковете по ал. 2 ежегодно организират разяснителна кампания в населените места на територията на съответните общини за изработване на технически паспорти на строежите. В началото на последната година от определения срок по ал. 2 кметът на общината издава предписание до всеки собственик на строеж, за който не е съставен технически паспорт.

### §единствен.1 (block 3, section body)
1. Думите „с изключение на строежите по ал. 1“ се заменят с „в т.ч. строежите – смесена държавна и частна собственост, или смесена общинска и частна собственост“.
- q1: „с изключение на строежите по ал. 1“
- q2: „в т.ч. строежите – смесена държавна и частна собственост, или смесена общинска и частна собственост“

### §единствен.2 (block 4, section body)
2. В т. 3 думите „31 декември 2012 г.“ се заменят с „31 декември 2014 г.“.
- q1: „31 декември 2012 г.“
- q2: „31 декември 2014 г.“

### §единствен.3 (block 5, section body)
3. В т. 4 думите „31 декември 2014 г.“ се заменят с „31 декември 2016 г.“.
- q1: „31 декември 2014 г.“
- q2: „31 декември 2016 г.“

### §единствен.4 (block 6, section body)
4. В т. 5 думите „31 декември 2016 г.“ се заменят с „31 декември 2018 г.“.
- q1: „31 декември 2016 г.“
- q2: „31 декември 2018 г.“
