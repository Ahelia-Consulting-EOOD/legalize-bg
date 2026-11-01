# The engine's residual error kinds after the F1 run of 1 November 2026

**Filed:** 2026-11-01, F1 run session (worktree `jolly-wright-479586`, PR #55). **Decision:** D-081.

Eight of the eleven representative acts did not reach a commit. Three groups of causes, each with the acts it stopped and where the evidence is.

## 1. Text the engine produced that lex.bg does not have (the write stops on `reading_error`)

The witness comparison settled these against lex.bg (the Ministry of Justice portal answered 500 for every act). Each is an engine defect the next session fixes with a test; the material and the operation are in the act's run folder under `data/runs/f1-engine-2026-11-01/<slug>/apply/`.

- **A space lost between two words after an operation** („паспортна“ for „паспорт на“, „даннии“ for „данни и“, „строежаи“ for „строежа и“): Наредба № 5/2006, differences 9, 22, 95, 108 of `witness-task.md`.
- **A doubled comma after an insertion that brings its own comma** („(ЗЕЕ),,“): Наредба № 5/2006, difference 8.
- **A renumber marker off by one** („предишна т. 4“ where lex.bg has т. 5): Наредба № 5/2006, difference 13.
- **A comma before an added clause** („часа“ against „часа,“ before „ако деянието“, three places): the extradition law, differences 53, 54, 58. Whether the comma is the Gazette's or lex.bg's editorial is not settled; check the material.
- **A „Нова“ marker lost** when the alinea was later replaced („(Изм. - …)“ for „(Нова - ДВ, бр. 100 от 2023 г., изм. - …)“) or created inside a wholesale article replacement (lex.bg marks each new alinea): the extradition law, differences 56 and 97.
- **Words printed twice by one replace** („и храните“ twice in the minister's title, 15 places; „храните и“ lost in § 3): the agricultural directorates' rules (`ustroystven-pravilnik-na-oblastnite-direktsii-zemedelie`), 24 differences, the operation in material 100860 or 107723.

## 2. Instructions the engine refuses because the Gazette's own text leaves the reading open (for the owner)

- **The protected-persons law, бр. 21/2014, § 5:** ал. 6 of чл. 14 becomes ал. 7 and is rewritten while „ал. 7 и 8 се отменят“; two provisions would carry the number 7. The case file: `docs/cases/zakon-za-zashtita-na-litsa-zastrasheni-vav-vrazka-s-nakazatelno-proizvodstvo.md`.
- **Наредба № 1/2015, бр. 58/2019, § 6:** „не повече от“ stands twice in чл. 29, ал. 2 and the instruction does not say „навсякъде“. Case file: `docs/cases/naredba-1-ot-22-yanuari-2015-g-za-pridobivane-na-spetsialnost-v-sistemata-na-zdr.md`.
- **The film-industry regulation, бр. 67/2021, § 34:** „филма“ stands twice in чл. 34, т. 2. Case file: `docs/cases/pravilnik-za-prilagane-na-zakona-za-filmovata-industriya.md`.

## 3. Forms the engine does not yet read (rules to add)

- **A new article's title line** that the parser reads as plain text and the engine does not join to the article when the quoted run opens with it in another position than the one the rule covers: the Family Code, бр. 67/2023, § 20 (чл. 127б).
- **Words inserted into a two-line subheading above an article** („в подзаглавието след думите … се добавя“): the port enterprise rules, бр. 31/2015, § 2.1 (чл. 33).

## What is left to run

The run stopped at 4.77 M of the 5.0 M tokens the owner allowed. Left for the eleven: the Family Code's materials 12 to 16 and its settlement, the port rules' materials 4 to 8 and settlement, the film regulation's 3 materials and settlement, re-settlements of the three fully applied acts after the group 1 fixes, and the owner's readings of group 2. Estimate: about 0.9 M tokens.
