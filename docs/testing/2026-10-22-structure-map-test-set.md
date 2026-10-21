# Test set for the structure map (plan step 3), 22 October 2026

Who this is for: the owner, who runs these tests with the session on 22 October 2026 after the raw fetch of the night before.

What is tested: the adopted reading architecture (decision D-069). For each act below, the pipeline takes the raw lex.bg page from the raw store, strips it to text, cuts it into blocks, asks Claude Opus 5.5 for the structure map (a label and the block indices per block), assembles the Markdown by copying the blocks under the labels, and runs the checks: the cited blocks re-assemble the source text exactly; article numbers are in sequence; paragraphs sit only inside articles and items only inside paragraphs; one address resolves to one row. A failed check is an exception on the block; two rounds with the neighbouring blocks follow; what survives goes to a whole-act read. The result per act is the map, the assembled Markdown in staging, the exception counts per round, and a diff against the act's current corpus file.

What a pass means: the re-assembly equality holds (no omission, no duplication, no invented block); every exception is either settled by round 1 or 2 or listed for the whole-act read; and the diff against the current corpus file shows only the differences the case predicts. A case that predicts a difference the pipeline does not show, or shows one it does not predict, is a finding.

## Normal cases

| # | Case | Act in the corpus | What the map must get right | Which check or diff shows a miss |
|---|---|---|---|---|
| N1 | A modern law with chapters, sections, articles, paragraphs, items | `laws/zakon-za-obshtestveniya-transport.md` (Закон за обществения транспорт, 2026) | the four levels of headings and the article grammar; the additional provision § 1 (see E8) | numbering sequence; diff against the corpus file |
| N2 | A large code with parts, chapters, sections and many appended transitional blocks | `codes/kodeks-na-truda.md` (Кодекс на труда) | each ПЗР block "към ЗИД" kept apart, § numbering restarting per block | one address one row; diff |
| N3 | The Constitution, chapters without sections | `laws/konstitutsiya-na-republika-balgariya.md` | chapter headings; no false section level | numbering sequence |
| N4 | A ministry ordinance with annexes and tables | `ordinances/naredba-1-ot-1-avgust-2013-g-za-usloviyata-i-reda-za-sahranyavane-na-zapasi-po-z.md` | annex boundary; table rows labelled as annex rows, not provisions | diff; the C7 class |
| N5 | A code with Обща and Особена част | `codes/nakazatelen-kodeks.md` (Наказателен кодекс) | the part level above chapters; article numbers continuing across parts | numbering sequence |
| N6 | A code with дялове | `codes/danachno-osiguritelen-protsesualen-kodeks.md` (ДОПК) | the дял level; superscript article numbers (see E4) | numbering sequence; address uniqueness |
| N7 | A tiny act of one to three articles | `laws/zakon-za-izplashtane-na-zadalzheniyata-ugovoreni-v-zlato.md` | no heading levels invented | diff |
| N8 | A very large page | `laws/targovski-zakon.md` (Търговски закон; raw page 4.5 megabytes) | the splitter and the per-block calls scale; no block over the request limit | the run's size and time report |

## Edge cases the corpus is known to hold

| # | Case | Act in the corpus | What the map must get right | Which check or diff shows a miss |
|---|---|---|---|---|
| E1 | Unnumbered paragraphs of a pre-1973 act (FR-034) | `laws/zakon-za-zadalzheniyata-i-dogovorite.md` (ЗЗД, 1950) | implicit paragraphs addressable in order, none flattened into the article line | diff against the FR-034 corrected file |
| E2 | A quoted passage inside a provision read as a real article (C1, FR-037) | the same ЗЗД file, the passage that produced "чл. 1001а" | the quoted text labelled as quoted content of its host provision, never as an article | address uniqueness; diff |
| E3 | A bracketed year or number read as a paragraph marker (C2, FR-030) | one of the 22 acts of the July finding; verify tomorrow by grep for a bracketed year at line start in the raw text | the bracket stays inside its sentence | numbering sequence (a paragraph "1969" is out of sequence) |
| E4 | Superscript article numbers with markup remnants (C4, FR-035) | `codes/danachno-osiguritelen-protsesualen-kodeks.md`, `codes/kodeks-za-sotsialno-osiguryavane-zagl-izm-dv-br-67-ot-2003-g.md`, `codes/kodeks-na-targovskoto-koraboplavane-zagl-izm-dv-br-113-ot-2002-g.md` | "чл. 260и¹"-style numbers kept distinct from "чл. 260и"; no `SUP>` fragment in the text | address uniqueness; the literal-fragment check |
| E5 | lex.bg site chrome inside the body (C3, FR-036, waiver W-003) | `ordinances/naredba-5-ot-10-may-1999-g-za-strukturata-na-zapisa-v-tsifrov-vid-na-kadastralni.md` | the two chrome rows labelled as not part of the act and dropped from the assembly | the literal-fragment check; diff |
| E6 | § 1 repeated in every appended transitional block (227 acts) | `laws/zakon-za-danak-varhu-dobavenata-stoynost.md` (ЗДДС) | each § keyed by its block context | one address one row |
| E7 | Annex or table material emitted as provisions (C7) | `ordinances/naredba-04-14-ot-9-oktomvri-2019-g-za-usloviyata-i-reda-za-sertifitsirane-na-bal.md` | annex rows never labelled as articles or paragraphs | numbering sequence; diff |
| E8 | lex.bg omits a promulgated section (FR-042) | `laws/zakon-za-obshtestveniya-transport.md` (the additional provision § 1 is empty on lex.bg) and the second confirmed act of the structure-gaps detector | the map labels the empty heading as a heading with no body; the record lists the omission with its Gazette locator (бр. 32/2026, material 242220) | the re-assembly check passes (nothing to omit on our side); the omission list is the finding |
| E9 | Content-less stub pages (FR-011) | `ordinances/-549676032.md`, `ordinances/2137254802.md`, `ordinances/2136890603.md` (no title in the corpus) | the raw fetch marks the page as a stub and the pipeline refuses it with a reason | the raw manifest status; no staging file |
| E10 | Editorial notes in titles and headings, "Загл. изм. - ДВ, бр. …" and "(Изм. - ДВ, бр. …)" | `codes/kodeks-za-sotsialno-osiguryavane-zagl-izm-dv-br-67-ot-2003-g.md` | the note labelled as an editorial note of the heading, not as text of the provision | diff |
| E11 | A repealed act whose frontmatter carries a comment that the gate's renderer drops (follow-up of 2026-09-06) | the Правилник на Съвета по архитектура и благоустройство named in that follow-up; find by the follow-up's file | the frontmatter comment survives the write or is moved into a field | the frontmatter check; diff |
| E12 | Lettered article numbers and lettered items | `laws/targovski-zakon.md` (чл. 260и¹), `laws/zakon-za-danak-varhu-dobavenata-stoynost.md` (чл. 118а; items "а)", "б)") | letter suffixes kept in the address; lettered items under their paragraph | address uniqueness; numbering sequence |
| E13 | Several additional-provision blocks (a ДР of the act and ДР "към ЗИД") | `laws/zakon-za-danak-varhu-dobavenata-stoynost.md` | each ДР block kept apart with its own § numbering | one address one row |
| E14 | Nested `<div>` structure that the old parser flattened (FR-034 defects A and B) | the acts named in `docs/research/2026-08-02-fr034-sweep-report.md`; pick two tomorrow | child paragraphs kept under their article | diff against the corrected corpus file |
| E15 | A repealed act (estado derogado) | `regulations/pravilnik-za-organizatsiyata-i-deynostta-na-narodnoto-sabranie.md` | the page's repeal note labelled as editorial; the map otherwise as for a live act | diff |
| E16 | Acts whose lex.bg page carries the "Стари редакции" version links and other navigation | any of the above; the splitter must drop navigation before blocks are cut | the literal-fragment check; re-assembly equality over the act text only |

## How the run is recorded

For every act: the raw page's hash from the manifest, the map, the assembled Markdown in `data/runs/structure-map-2026-10-22/<slug>/`, the exception counts per round, the whole-act reads with their verdicts, and the diff against the corpus file. One summary table over all cases closes the run. Nothing is written to the corpus directories.

## What is left out, and where it lives

Gazette materials (amendment operations) are plan step 5 and are not in this set; the catch-up materials are already fetched under `data/runs/catchup-2026-10-21/`. Acts that exist only before the HTML era are grade C and are not reachable by this pipeline from lex.bg alone (decision D-059).
