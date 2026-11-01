# The engine's residual error kinds after the F1 run of 1 November 2026

**Filed:** 2026-11-01, F1 run session (worktree `jolly-wright-479586`, PR #55). **Decision:** D-081. **Updated** after the second half of the run (the 0.9 M the owner funded).

Six of the eleven representative acts did not reach a commit. Three groups of causes, each with the acts it stopped and where the evidence is.

## 1. Text the engine produced that lex.bg does not have (the write stops on `reading_error`)

Fixed in the second half of the run, with tests: the run-together words were the Gazette HTML's own (adjacent inline elements with no space; the splitter now records the boundary and the text is spaced), the doubled comma after a quoted segment that ends in the sentence's comma, the comma lost on „накрая се поставя запетая и се добавя“, the alineas of an article rewritten whole (lex.bg marks each: „Изм.“ where the number existed, „Нова“ where not), a replace that extended an already extended place („и храните и храните“), a rewritten annex or heading losing its marker history, one issue marking a heading several times.

Left, all in Наредба № 5/2006 (`data/runs/f1-engine-2026-11-01/naredba-5-ot-28-dekemvri-2006-g-za-tehnicheskite-pasporti-na-stroezhite/witness-task.md`, differences 5 to 10):
- **A heading marker's gender:** „Нова“ on a раздел where lex.bg writes „Нов“ (раздел is masculine; глава feminine; приложение neuter).
- **Two kinds of one issue on one provision across two lines** („Изм.“ on the head, „Доп.“ on an alinea) where lex.bg writes „Изм. и доп.“ on the head.
- **A renumber marker's former number** („предишна т. 4“ against lex.bg's „предишна т. 5“ for бр. 22/2010): which is right needs the material read.
- **Two item-end marks** (`;` against `.`) the task cannot settle without the source.

## 2. Instructions the engine refuses because the Gazette's own text leaves the reading open (for the owner)

- **The protected-persons law, бр. 21/2014, § 5:** ал. 6 of чл. 14 becomes ал. 7 and is rewritten while „ал. 7 и 8 се отменят“; two provisions would carry the number 7. Case file: `docs/cases/zakon-za-zashtita-na-litsa-zastrasheni-vav-vrazka-s-nakazatelno-proizvodstvo.md`.
- **The Family Code, бр. 106/2023, § 8, т. 6:** „досегашната ал. 5 става ал. 6“ while чл. 84 keeps a live ал. 6 that the material neither moves nor repeals (its т. 7 creates ал. 7 and 8). Case file: `docs/cases/semeen-kodeks.md`.
- **Наредба № 1/2015, бр. 58/2019, § 6:** „не повече от“ stands twice in чл. 29, ал. 2 and the instruction does not say „навсякъде“. Case file: `docs/cases/naredba-1-ot-22-yanuari-2015-g-za-pridobivane-na-spetsialnost-v-sistemata-na-zdr.md`.
- **The film-industry regulation, бр. 67/2021, § 34:** „филма“ stands twice in чл. 34, т. 2. Case file: `docs/cases/pravilnik-za-prilagane-na-zakona-za-filmovata-industriya.md`.

## 3. Forms the engine does not yet read (rules to add)

- **Words inserted into a two-line subheading above an article** („в подзаглавието след думите … се добавя запетая“): the port enterprise rules, бр. 31/2015, § 2, т. 1 (the two lines above чл. 33).

## What is left to run

The run spent 5,283,528 tokens of the 5.67 M allowed (166 calls). Left for the eleven: Наредба № 5/2006's four marker fixes and a settlement (about 60,000 tokens), the Family Code's materials 14 to 16 and its settlement after the owner's reading of § 8 (about 200,000), the port rules' materials 4 to 8 and settlement after the subheading rule (about 250,000), the film regulation's three materials after the owner's reading of § 34 (about 150,000), and the owner's readings for the protected-persons law and Наредба № 1/2015. Estimate: about 0.9 M tokens more for the remaining six.
