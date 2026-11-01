# The representative acts for the engine's first verification: a proposal

Who this is for: the owner, who decides the acts on which the Gazette engine (step [F1](#glossary) of the implementation plan of 31 October 2026) is first verified, as decision 5 of that plan's section 7 deferred to the end of step S3.

## The decision asked for

Agree the eleven acts below as the representatives of each kind of act for F1, or strike and replace any of them. [The engine](#glossary) is verified on these acts by rebuilding each one's history from the Gazette and settling every difference from [the witnesses](#glossary) (decision [D-074](#glossary), point 3). Only after that does it run on new issues.

## How they were chosen

Every act comes from the act profiles of step S3, the register that holds one row for each of the corpus's 3,624 acts. Three rules chose them, each with its reason.

1. **The whole history is online as text.** The act was promulgated in 2003 or later and none of its amendments sits in a PDF-only issue, so the engine can read every change as HTML. The pre-2003 and PDF-era acts are a later case: their history is read by vision, which F1 does not build.
2. **Enough amendments to test the engine, few enough to bound the work.** Between 5 and 16 amendment events, except for the two implementing regulations, where the corpus holds only three acts with an online history at all. The coverage map [located](#glossary) some of each act's amendments by title. The rest it could not locate, because they ride inside other acts' transitional provisions. Both cases are the engine's job, so each kind has an act with many unlocated events.
3. **One plain act and one with the layout features that break readers.** For each kind, one act whose page has no annex, table, image or superscript, and one whose page has several of them, so that the engine meets both the simple and the awkward forms. The third наредба adds the one feature the others lack, repeated headings.

## The proposal

| Kind | Act | Promulgated | Amendment events (located by title, unlocated) | Layout |
|---|---|---|---|---|
| закон | Закон за защита на лица, застрашени във връзка с наказателно производство | 2004 | 12 (5, 7) | plain |
| закон | Закон за екстрадицията и европейската заповед за арест | 2005 | 12 (4, 8) | one annex, 202 table rows |
| кодекс | Кодекс на международното частно право | 2005 | 5 (0, 5) | plain |
| кодекс | Семеен кодекс | 2009 | 16 (4, 12) | plain |
| наредба | Наредба № 8121з-310 от 2014 г. за преназначаване на държавните служители | 2014 | 7 (7, 0) | plain |
| наредба | Наредба № 5 от 2006 г. за техническите паспорти на строежите | 2006 | 8 (8, 0) | two annexes, 203 table rows, a superscript |
| наредба | Наредба № 1 от 2015 г. за придобиване на специалност в системата на здравеопазването | 2015 | 10 (10, 0) | two annexes, 283 table rows, five repeated headings |
| правилник | Правилник за устройството, функциите и дейността на Държавно предприятие „Пристанищна инфраструктура“ | 2004 | 8 (8, 0) | plain |
| правилник | Устройствен правилник на областните дирекции „Земеделие“ | 2008 | 12 (12, 0) | one annex, 29 table rows |
| правилник по прилагане | Правилник за прилагане на Закона за защита на лица, застрашени във връзка с наказателно производство | 2005 | 2 (2, 0) | plain |
| правилник по прилагане | Правилник за прилагане на Закона за филмовата индустрия | 2004 | 3 (3, 0) | 34 annex headings, 2,036 table rows, 24 superscripts |

The Закон за обществения транспорт, already committed from its promulgation material with no amendment, is the engine's zero case and needs no place in the table.

## What this does not settle

The acts whose history begins before 2003, among them every code of general law (the Labour Code, the Penal Code, the Commercial Act), are not represented, because their history cannot be rebuilt from online text alone. They are the subject of steps S4 and S5, and the engine reaches them only case by case (decision D-074, point 3). The amendment counts are the coverage map's title pass of 5 September 2026 and will move when the body scan runs.

## How this was checked

The counts come from `docs/data/act-profiles.csv` (the layout columns) and `docs/research/2026-09-05-dv-coverage-map/acts-summary.csv` (the event columns), read by script on 31 October 2026; the selection rules were applied by script over the whole register and the candidates read by the session. No model call was made for this document.

## Glossary

- **F1, S3, S4, S5:** steps of the implementation plan of 31 October 2026 (`docs/plans/2026-10-31-starting-state-implementation-plan.md`): the engine, the act profiles, the sources for the acts before the archive, and the audit by profile.
- **The engine:** the reasoning run that turns a Gazette material into changes to an act.
- **Located, unlocated:** whether the coverage map found the amendment as a Gazette material by its title; an unlocated amendment rides inside another act's transitional and final provisions and is found by reading the bodies.
- **The witnesses:** lex.bg and the Ministry of Justice portal, compared with but never trusted (decision D-061).
- **D-061, D-074:** decisions of `docs/sync/DECISIONS.md`: witnesses are never truth; the starting state is rebuilt forward and the engine is proven on representatives of each kind.
