# Source Log: I4 Official consolidation

Investigation I4 — Official Bulgarian consolidation sources. Date: 2026-06-22.
Purpose: rigorously confirm or refute the premise that **no official Bulgarian
consolidated-law source/API exists** (only private commercial compilers do).

## Web Searches Performed

| # | Query | Date | Outcome |
|---|-------|------|---------|
| 1 | консолидирана версия закон официален държавен орган България | 2026-06-22 | negative — only ДВ gazette + private DBs (Lakorda) surfaced; no official consolidated source |
| 2 | официален източник консолидирани нормативни актове действащо законодателство България | 2026-06-22 | negative — points to ДВ (gazette) + MoJ portal + private (Лакорда); no official consolidated DB |
| 3 | Bulgaria official consolidated legislation government portal free access | 2026-06-22 | extract#3 — LoC + N-Lex: ДВ free but editions/corrections only, "no other official legislative database exists" |
| 4 | N-Lex Bulgaria national law portal coverage consolidated | 2026-06-22 | extract#1 — N-Lex links only ДВ; ДВ = editions/corrections, not full law texts |
| 5 | justice.government.bg normdoc нормативни документи база данни консолидирани закони | 2026-06-22 | LEAD — MoJ /home/normdoc/ serves laws with full amendment markers; needs direct verify |
| 6 | data.egov.bg отворени данни закони нормативни актове консолидирани dataset | 2026-06-22 | negative — open-data portal; no consolidated-legislation dataset |
| 7 | parliament.bg народно събрание справка закони действащ текст консолидиран | 2026-06-22 | negative — /bg/laws lists bills/passed acts + EU treaties; no действащ-консолидиран view of national law |
| 8 | justice.government.bg нормативни актове информационна система кой поддържа АПИС Сиела източник | 2026-06-22 | extract#4 — MoJ e-justice portal built "в сътрудничество със Сиела Норма" |
| 9 | Министерство на правосъдието нормативни актове справочник обхват APIS Сиела | 2026-06-22 | extract#4 — Ciela maintains/auto-updates the normative-acts texts behind the MoJ portal |
| 10 | justice.government.bg "Сиела" OR "Апис" нормативни актове портал предоставена база данни | 2026-06-22 | context — confirms paid АПИС/Сиела/Лакорда are the full legal DBs |
| 11 | justice.government.bg "Закон за обществените поръчки" normdoc консолидиран | 2026-06-22 | negative/scope — ЗОП consolidated text surfaced on lex.bg + legislation.apis.bg + ministry PDFs, NOT a MoJ normdoc URL → MoJ normdoc is a curated subset, not the whole corpus |
| 12 | justice.government.bg нормативни актове търсене списък всички закони портал | 2026-06-22 | scope — no top-level "all legislation" browse; normdoc embedded in MoJ institutional portal |
| 13 | EUR-Lex consolidated national law member states only EU acts not national legislation | 2026-06-22 | extract#5 — EUR-Lex consolidates only EU acts; N-Lex is the gateway to national law |
| 14 | (Playwright render) justice.government.bg/home/normdoc/2127837184 (ЗНА) + /521957377 (Constitution) + / (homepage) | 2026-06-22 | extract#6 — MoJ normdoc IS full consolidated text, amended-into-base, current to ДВ бр.30/2026, with per-element "Редакции" + cross-refs |

## Documents Read

| # | File Path | Sections Read | Outcome |
|---|-----------|---------------|---------|
| 1 | docs/sync/HANDOFFS/2026-06-22-freshness-consolidation-resource-roadmap.md | §1, §5 I4 | context |
| 2 | docs/sync/DECISIONS.md | D-002, D-003, D-038, D-039 | context |
| 3 | docs/frs/INDEX.md | FR-024 | context |

## Web Sources Referenced

| # | URL | Title | Date Accessed | Outcome |
|---|-----|-------|---------------|---------|
| 1 | https://n-lex.europa.eu/n-lex/info/info-bg/index | N-Lex — About the national database / Bulgaria (EU official) | 2026-06-22 | extract#1 |
| 2 | https://guides.loc.gov/law-bulgaria/legislative | Library of Congress — Guide to Law Online: Bulgaria (Legislative) | 2026-06-22 | 403 — used via search #3 summary |
| 3 | (search summary) | LoC / European Forum of Official Gazettes via search #3 | 2026-06-22 | extract#3 |
| 4 | https://justice.government.bg/home/normdoc/2127837184 | MoJ — ЗАКОН ЗА НОРМАТИВНИТЕ АКТОВЕ (consolidated) | 2026-06-22 | extract#6 |
| 5 | https://justice.government.bg/home/normdoc/521957377 | MoJ — КОНСТИТУЦИЯ (consolidated) | 2026-06-22 | extract#6 |
| 6 | https://justice.government.bg/ | MoJ — institutional portal homepage | 2026-06-22 | scope (no general legislation browse in nav) |
| 7 | https://www.ciela.net/news/view/236 | Ciela Norma news — MoJ e-justice portal cooperation | 2026-06-22 | extract#4 |
| 8 | https://bg.wikipedia.org/wiki/Правно-информационна_система | Wikipedia (BG) — Legal-information system | 2026-06-22 | extract#7 |
| 9 | http://eur-lex.europa.eu/n-lex/index_en + EUR-Lex consleg help | N-Lex / EUR-Lex scope | 2026-06-22 | extract#5 |

## Extracted Content

| Source ref | Extract (verbatim, <300 words) | Used in section |
|------------|--------------------------------|-----------------|
| extract#1 | (N-Lex EU official, Bulgaria national database page) "State gazette consists mainly of editions and corrections of the official documents, and not of the full texts of actual laws in Bulgaria." … "any search in its database provides mainly information about changes in legislative papers, and not the whole list of acting laws." N-Lex links one primary Bulgarian database: the State Gazette (dv.parliament.bg), the "Bulgarian government official journal." No statement that consolidated versions are available elsewhere. | Q1, Q2, Conclusion |
| extract#3 | (Search #3 summary citing LoC + European Forum of Official Gazettes + N-Lex) "The State Gazette (Darzhaven vestnik) is available free of charge … contains bills promulgated by the National Assembly, decrees … etc." … "the State Gazette consists mainly of editions and corrections of official documents, and not of the full texts of actual laws in Bulgaria." … "apart from the Darzhaven vestnik online, no other official legislative database exists in Bulgaria, though other legal databases may be available through non-government sources." | Q1, Q2, Conclusion |
| extract#4 | (ciela.net/news/view/236) Ministry of Justice created a "портал за електронно правосъдие" in cooperation with "Сиела Норма." "Автоматично ще бъдат актуализирани с последни редакции и всички текстове на нормативни актове" (all normative-act texts auto-updated with their latest editions). "Сиела Норма разработи и новия дизайн на единния портал." Contracted EU-funded project (contract 03.10.2017; value 485,523 BGN; news 02 Dec 2019; launch early 2020). → The consolidated normative-acts texts on the MoJ portal are provided/auto-updated via the private vendor Ciela Norma. | Q1, Q3, Conclusion |
| extract#5 | (EUR-Lex consleg help + N-Lex) "Consolidated versions of EU legal acts combine in one document the initial act with all its subsequent amendments and corrigenda applicable at a specific point in time." Consolidated texts have "no legal effect … intended for use as documentation only." The consolidated-texts section covers EU acts only. "N-Lex provides a single entry point to the national law databases on individual EU countries, which is separate from EUR-Lex's consolidated EU acts section." EUR-Lex also carries national transposition measures for member states that agree to provide them. | Q2, Conclusion |
| extract#6 | (Playwright render of MoJ /home/normdoc/2127837184, ЗНА) Header: "Обн. ДВ. бр.27 от 3 Април 1973г., изм. ДВ. бр.65 от 21 Юли 1995г., доп. … изм. и доп. ДВ. бр.30 от 27 Март 2026г." Body = full article text amended-into-base: "Чл. 1. (Изм. - ДВ, бр. 46 от 2007 г.) Този закон цели да усъвършенствува …"; repealed marked "Чл. 5. (Отм. - ДВ, бр. 46 от 2007 г.)"; new marked "Чл. 1а. (Нов - ДВ, бр. 46 от 2007 г.) …"; renumbered "(Предишна ал. 2 …)". Each element carries UI affordances "Редакции на елемента" (element revisions), "Препратки от документи", "Препратки от практика". → MoJ normdoc is a genuine consolidated, point-in-time-capable legal text, current to 2026. | Q1, Conclusion |
| extract#7 | (Wikipedia BG — Правно-информационна система) Commercial systems named: Сиела, Лакорда, Дакси, Експертис, АПИС, Doxtream — all private "комерсиални продукти"; "за ползването им се налага да се заплати парична сума." On the gazette vs consolidation: "при промяна на текст във вече обнародван нормативен акт … в Държавен вестник се публикуват само отделните части, които се променят," whereas the commercial systems "нанасят промените върху целия текст." | Q1, Q3, Conclusion |
