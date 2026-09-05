# Audit 2026-09-05: additional provisions dropped by the source (lex.bg)

**Status:** open, evidence complete for two acts, adjudication of the rest folded into the approach C coverage map (FR-042, D-059)
**Author:** Claude session on owner (ekimir) dispatch from the takt-plan programme, 2026-09-05
**Tool:** `scripts/structure_gaps.py` (tests in `tests/test_structure_gaps.py`), run at `origin/main` 5e92aa30
**Related:** `docs/cpd/CPD-2026-09-05-dv-gap-fill-additional-provisions.md`

## Finding

The corpus mirrors lex.bg faithfully, and lex.bg omits the additional provisions of some acts.
Confirmed on Закон за обществения транспорт (ЗОТ, `laws/zakon-za-obshtestveniya-transport.md`,
lex.bg ldoc 2137259781): the live page fetched through `fetcher.bg.client.LexBgClient` on
2026-09-05 renders "Допълнителна разпоредба" with no text and continues with
"Заключителни разпоредби § 2."; the raw HTML holds no hidden "§ 1" (the one match is the prefix of
"§ 10"). The State Gazette record of the promulgated act (ДВ бр. 32 от 1.4.2026 г.,
https://dv.parliament.bg/DVWeb/showMaterialDV.jsp?idMat=242220) carries § 1 with twelve definitions
("Възел за достъп" to "Зарядна станция"). Article by article the Gazette text and the corpus file are
identical for all 106 articles apart from lex.bg's consolidation notes "(В сила от ...)", dash style
(the Gazette uses the en dash, lex.bg the hyphen), and two places where lex.bg prints "и" for the
Gazette's "й" ("административния й център", чл. 29 and чл. 32); the Gazette's own HTML carries a
Latin "E" in "Eдинен превозен документ" (§ 1, т. 4), normalised to Cyrillic on gap fill.

The same lex.bg-side gap was verified live for Закон за прозрачност при представителство на
интереси (ldoc 2137259673: "Допълнителна разпоредба Преходни и Заключителни разпоредби § 2.").

## Method

Two rules over `laws/`, `codes/`, `ordinances/`, `implementing/`, `regulations/`, `postanovleniya/`:

- `additional-empty`: a standalone additional-provisions heading directly followed (blank lines
  apart) by a transitional or final provisions heading.
- `paragraph-start-above-1`: the lowest bold `**§ N.**` in the file is above 1.

The second rule over-approximates: an ordinance adopted by a decree whose §§ belong to the decree,
or an act whose lex.bg rendering numbers its provisions from the amending act, can start above 1
legitimately. Every row below is a candidate to adjudicate against the State Gazette, not a
confirmed defect; the 25 rows where both rules fire are the strongest candidates.

## Results at 5e92aa30

Files flagged: 95; `additional-empty` 25; `paragraph-start-above-1` 95.

| file | additional section empty | lowest § |
| --- | --- | --- |
| `laws/zakon-za-obshtestveniya-transport.md` | yes | lowest § is 2 |
| `laws/zakon-za-obshtite-iziskvaniya-za-bezopasnost-pri-predostavyane-na-atraktsionni-u.md` | yes | lowest § is 2 |
| `laws/zakon-za-prozrachnost-pri-predstavitelstvo-na-interesi.md` | yes | lowest § is 2 |
| `laws/zakon-za-smetnata-palata.md` | no | lowest § is 2 |
| `laws/zakon-za-zadalzheniyata-i-dogovorite.md` | no | lowest § is 2 |
| `codes/kodeks-na-targovskoto-koraboplavane-zagl-izm-dv-br-113-ot-2002-g.md` | no | lowest § is 2 |
| `codes/kodeks-na-truda.md` | no | lowest § is 3 |
| `ordinances/naredba-1-ot-10-yuni-2022-g-za-usloviyata-i-reda-za-finansirane-na-proekti-po-na.md` | yes | lowest § is 2 |
| `ordinances/naredba-10-ot-27-yuni-2023-g-za-usloviyata-i-reda-za-prilagane-na-interventsiite.md` | yes | lowest § is 2 |
| `ordinances/naredba-14-ot-15-april-2004-g-za-meditsinskite-kriterii-i-reda-na-ustanovyavane-.md` | no | lowest § is 6 |
| `ordinances/naredba-16-ot-17-noemvri-2005-g-za-usloviyata-i-reda-za-provezhdane-na-kurs-za-o.md` | no | lowest § is 4 |
| `ordinances/naredba-18-ot-9-avgust-1991-g-za-organizatsiyata-i-deynostta-na-laboratoriite-za.md` | no | lowest § is 2 |
| `ordinances/naredba-2-ot-19-fevruari-1998-g-za-normi-za-dopustimi-emisii-kontsentratsii-v-ot.md` | no | lowest § is 10 |
| `ordinances/naredba-27-ot-13-mart-2014-g-za-statistikata-na-platezhniya-balans-mezhdunarodna.md` | yes | lowest § is 2 |
| `ordinances/naredba-29-ot-12072006-g-za-minimalnoto-nivo-na-kreditnite-reytingi-na-bankite-i.md` | no | lowest § is 2 |
| `ordinances/naredba-3-ot-22-april-2026-g-za-usloviyata-i-reda-za-prilagane-na-interventsiyat.md` | yes | lowest § is 2 |
| `ordinances/naredba-3-ot-27-mart-2026-g-za-meteorologichnoto-osiguryavane-na-vazdushna-navig.md` | yes | lowest § is 2 |
| `ordinances/naredba-3-ot-5-may-2026-g-za-reda-za-vodene-na-registara-po-chl-14-al-4a-ot-zako.md` | yes | lowest § is 2 |
| `ordinances/naredba-33-ot-16-yuli-2026-g-za-individualnite-zayavleniya-za-uchastie-vav-fond-.md` | yes | lowest § is 2 |
| `ordinances/naredba-4-ot-30-yuni-2026-g-za-pokazatelite-za-sapostavyane-na-dohodnostta-na-po.md` | yes | lowest § is 2 |
| `ordinances/naredba-45-ot-17-april-2025-g-otnosno-ustanovyavane-i-reglamentirane-na-pravootn.md` | yes | lowest § is 2 |
| `ordinances/naredba-8-ot-20-yuni-2023-g-za-usloviyata-i-reda-za-prilagane-na-interventsiite-.md` | yes | lowest § is 2 |
| `ordinances/naredba-8121z-1006-ot-24-avgust-2015-g-za-reda-za-osashtestvyavane-na-pozharogas.md` | yes | lowest § is 2 |
| `ordinances/naredba-8121z-1243-ot-9-noemvri-2020-g-za-usloviyata-i-reda-za-vazlagane-i-otchi.md` | yes | lowest § is 2 |
| `ordinances/naredba-9-ot-26-may-2016-g-za-usloviyata-i-reda-za-izdavane-na-razresheniya-za-z.md` | yes | lowest § is 2 |
| `ordinances/naredba-9-ot-26-yuni-2023-g-za-usloviyata-i-reda-za-prilagane-na-interventsiite-.md` | yes | lowest § is 2 |
| `ordinances/naredba-n-10-ot-24-yuni-2026-g-za-usloviyata-i-reda-za-validirane-na-profesional.md` | yes | lowest § is 2 |
| `ordinances/naredba-n-11-ot-24-yuli-2026-g-za-usloviyata-i-reda-za-priemane-na-serzhanti-sta.md` | yes | lowest § is 2 |
| `ordinances/naredba-n-2-ot-15-april-2026-g-za-usloviyata-i-reda-za-podpomagane-s-parichni-sr.md` | yes | lowest § is 2 |
| `ordinances/naredba-n-4-ot-30-mart-2026-g-za-organizatsiyata-na-profilaktikata-i-kontrola-na.md` | yes | lowest § is 2 |
| `ordinances/naredba-za-kriteriite-usloviyata-i-reda-za-opredelyane-na-statut-na-domakinstvo-.md` | yes | lowest § is 2 |
| `ordinances/naredba-za-natsionalniya-geolozhki-fond-zagl-izm-dv-br-43-ot-2011-g.md` | no | lowest § is 12 |
| `ordinances/naredba-za-opredelyane-na-protsedurite-za-administrirane-na-nerednosti-po-fondov.md` | no | lowest § is 24 |
| `ordinances/naredba-za-pravilata-i-normite-za-proektirane-izgrazhdane-i-premahvane-na-fizich.md` | yes | lowest § is 2 |
| `ordinances/naredba-za-reda-i-metodikata-za-opredelyane-na-koefitsienta-po-chl-10-al-4-ot-za.md` | no | lowest § is 24 |
| `ordinances/naredba-za-usloviyata-i-reda-za-izvarshvane-na-nadzor-na-pazara.md` | no | lowest § is 21 |
| `ordinances/naredba-za-usloviyata-i-reda-za-pridobivane-na-profesionalna-kvalifikatsiya-i-za.md` | no | lowest § is 2 |
| `ordinances/naredba-za-usloviyata-i-reda-za-upravlenie-na-sredstvata-ot-fonda-za-bezopasnost.md` | no | lowest § is 8 |
| `ordinances/naredba-za-usloviyata-i-reda-za-vazlagane-na-deynosti-po-chl-7-al-2-ot-zakona-za.md` | no | lowest § is 24 |
| `ordinances/naredba-za-usvoyavane-na-voenni-izdeliya-i-za-sazdavane-i-poddarzhane-na-moshtno.md` | no | lowest § is 11 |
| `implementing/pravilnik-za-prilagane-na-zakona-za-darzhavna-agentsiya-razuznavane.md` | no | lowest § is 5 |
| `implementing/pravilnik-za-prilagane-na-zakona-za-trudovata-migratsiya-i-trudovata-mobilnost.md` | no | lowest § is 9 |
| `regulations/pravilnik-na-stolichen-obshtinski-savet-za-ustroystvoto-organizatsiyata-i-deynos-2.md` | no | lowest § is 2 |
| `regulations/pravilnik-na-velikotarnovskiya-obshtinski-savet-za-organizatsiyata-reda-i-rabota.md` | no | lowest § is 2 |
| `regulations/pravilnik-za-legalizatsiite-zaverkite-i-prevodite-na-dokumenti-i-drugi-knizha-za.md` | no | lowest § is 10 |
| `regulations/pravilnik-za-organizatsiyata-i-deynostta-na-natsionalniya-savet-za-nauka-i-inova.md` | no | lowest § is 91 |
| `regulations/pravilnik-za-organizatsiyata-na-deynostta-na-saveta-za-administrativnata-reforma.md` | no | lowest § is 6 |
| `regulations/pravilnik-za-organizatsiyata-na-deynostta-na-saveta-za-koordinatsiya-v-borbata-s.md` | no | lowest § is 44 |
| `regulations/pravilnik-za-usloviyata-i-reda-za-rabota-na-etichnata-komisiya-po-transplantatsi.md` | no | lowest § is 8 |
| `regulations/pravilnik-za-ustroystvoto-deynostta-i-organizatsiyata-na-rabota-na-tsentara-za-o.md` | no | lowest § is 91 |
| `regulations/pravilnik-za-ustroystvoto-i-deynostta-na-bolnitsa-lozenets.md` | no | lowest § is 12 |
| `regulations/pravilnik-za-ustroystvoto-i-deynostta-na-darzhavnata-komisiya-po-stokovite-borsi.md` | no | lowest § is 24 |
| `regulations/pravilnik-za-ustroystvoto-i-deynostta-na-darzhavno-predpriyatie-kabiyuk-shumen.md` | no | lowest § is 70 |
| `regulations/pravilnik-za-ustroystvoto-i-deynostta-na-mezhduvedomstveniya-savet-po-vaprosite-.md` | no | lowest § is 24 |
| `regulations/pravilnik-za-ustroystvoto-i-deynostta-na-mnogoprofilnite-transportni-bolnitsi-ka.md` | no | lowest § is 77 |
| `regulations/pravilnik-za-ustroystvoto-i-deynostta-na-natsionalniya-savet-za-satrudnichestvo-.md` | no | lowest § is 6 |
| `regulations/pravilnik-za-ustroystvoto-i-deynostta-na-tsentara-za-razvitie-na-choveshkite-res.md` | no | lowest § is 6 |
| `regulations/pravilnik-za-ustroystvoto-i-deynostta-na-voenno-geografskata-sluzhba-2.md` | yes | lowest § is 2 |
| `regulations/pravilnik-za-ustroystvoto-i-organizatsiyata-na-deynostta-na-komisiyata-za-zashti.md` | yes | lowest § is 2 |
| `regulations/ustroystven-pravilnik-na-agentsiyata-po-vpisvaniyata.md` | no | lowest § is 5 |
| `regulations/ustroystven-pravilnik-na-agentsiyata-za-darzhavna-finansova-inspektsiya.md` | no | lowest § is 5 |
| `regulations/ustroystven-pravilnik-na-agentsiyata-za-horata-s-uvrezhdaniya.md` | no | lowest § is 9 |
| `regulations/ustroystven-pravilnik-na-agentsiyata-za-sotsialno-podpomagane.md` | no | lowest § is 9 |
| `regulations/ustroystven-pravilnik-na-balgarskata-agentsiya-po-bezopasnost-na-hranite.md` | no | lowest § is 8 |
| `regulations/ustroystven-pravilnik-na-balgarskata-agentsiya-za-investitsii.md` | no | lowest § is 9 |
| `regulations/ustroystven-pravilnik-na-darzhavna-agentsiya-arhivi.md` | no | lowest § is 6 |
| `regulations/ustroystven-pravilnik-na-darzhavna-agentsiya-darzhaven-rezerv-i-voennovremenni-z.md` | no | lowest § is 9 |
| `regulations/ustroystven-pravilnik-na-darzhavna-agentsiya-tehnicheski-operatsii.md` | no | lowest § is 10 |
| `regulations/ustroystven-pravilnik-na-darzhavnata-agentsiya-za-metrologichen-i-tehnicheski-na.md` | no | lowest § is 21 |
| `regulations/ustroystven-pravilnik-na-darzhavnata-agentsiya-za-zakrila-na-deteto.md` | no | lowest § is 9 |
| `regulations/ustroystven-pravilnik-na-izpalnitelna-agentsiya-avtomobilna-administratsiya.md` | no | lowest § is 10 |
| `regulations/ustroystven-pravilnik-na-izpalnitelna-agentsiya-infrastruktura-na-elektronnoto-u.md` | no | lowest § is 6 |
| `regulations/ustroystven-pravilnik-na-izpalnitelna-agentsiya-sertifikatsionen-odit-na-sredstv.md` | no | lowest § is 6 |
| `regulations/ustroystven-pravilnik-na-izpalnitelna-agentsiya-voenni-klubove-i-voenno-pochivno.md` | no | lowest § is 9 |
| `regulations/ustroystven-pravilnik-na-izpalnitelnata-agentsiya-po-lozata-i-vinoto.md` | no | lowest § is 9 |
| `regulations/ustroystven-pravilnik-na-izpalnitelnata-agentsiya-po-ribarstvo-i-akvakulturi.md` | no | lowest § is 9 |
| `regulations/ustroystven-pravilnik-na-izpalnitelnata-agentsiya-po-selektsiya-i-reproduktsiya-.md` | no | lowest § is 9 |
| `regulations/ustroystven-pravilnik-na-izpalnitelnata-agentsiya-po-sortoizpitvane-aprobatsiya-.md` | no | lowest § is 6 |
| `regulations/ustroystven-pravilnik-na-izpalnitelnata-agentsiya-prouchvane-i-poddarzhane-na-r-.md` | no | lowest § is 77 |
| `regulations/ustroystven-pravilnik-na-ministerstvoto-na-elektronnoto-upravlenie.md` | no | lowest § is 16 |
| `regulations/ustroystven-pravilnik-na-ministerstvoto-na-finansite.md` | no | lowest § is 5 |
| `regulations/ustroystven-pravilnik-na-ministerstvoto-na-ikonomikata-i-industriyata.md` | no | lowest § is 16 |
| `regulations/ustroystven-pravilnik-na-ministerstvoto-na-inovatsiite-i-rastezha.md` | no | lowest § is 9 |
| `regulations/ustroystven-pravilnik-na-ministerstvoto-na-mladezhta-i-sporta.md` | no | lowest § is 6 |
| `regulations/ustroystven-pravilnik-na-ministerstvoto-na-obrazovanieto-i-naukata-zagl-izm-dv-b.md` | no | lowest § is 16 |
| `regulations/ustroystven-pravilnik-na-ministerstvoto-na-okolnata-sreda-i-vodite.md` | no | lowest § is 16 |
| `regulations/ustroystven-pravilnik-na-ministerstvoto-na-otbranata.md` | no | lowest § is 15 |
| `regulations/ustroystven-pravilnik-na-ministerstvoto-na-pravosadieto.md` | no | lowest § is 4 |
| `regulations/ustroystven-pravilnik-na-ministerstvoto-na-regionalnoto-razvitie-i-blagoustroyst.md` | no | lowest § is 11 |
| `regulations/ustroystven-pravilnik-na-ministerstvoto-na-transporta-i-saobshteniyata-zagl-izm-.md` | no | lowest § is 6 |
| `regulations/ustroystven-pravilnik-na-ministerstvoto-na-truda-i-sotsialnata-politika.md` | no | lowest § is 8 |
| `regulations/ustroystven-pravilnik-na-ministerstvoto-na-turizma.md` | no | lowest § is 16 |
| `regulations/ustroystven-pravilnik-na-ministerstvoto-na-zdraveopazvaneto.md` | no | lowest § is 16 |
| `regulations/ustroystven-pravilnik-na-natsionalniya-savet-po-tseni-i-reimbursirane-na-lekarst.md` | no | lowest § is 5 |
| `regulations/ustroystven-pravilnik-na-oblastnite-administratsii.md` | no | lowest § is 3 |

## Disposition

- ЗОТ: NOT hand-filled. The hand-edited `[popravka]` commit proposed in PR #24 was rejected (D-063);
  the act is rebuilt from ДВ бр. 32/2026 as the first grade A pilot of the graded source model (D-059).
- The other 24 acts where both rules fire: adjudicate against the State Gazette one by one as part
  of the coverage map (FR-024 / FR-042); the CPD's gap-fill process is superseded by D-059.
- The 70 acts where only the numbering rule fires: adjudicate; a legitimate case should be
  recorded so the scanner can carry an allow-list.
