# Source Log: I3 DV access

Investigation I3 — Държавен вестник (ДВ) access + ЗИД parsing recon. Date: 2026-06-22.
Companion document: `2026-06-22-I3-dv-access.md`.

## Web Searches Performed

| # | Query | Date | Outcome |
|---|-------|------|---------|
| 1 | dv.parliament.bg Държавен вестник брой архив showMaterialDV.jsp idMat | 2026-06-22 | extract#1 (confirms showMaterialDV.jsp?idMat=N, fileUploadShowing.jsp?idFileAtt=N) |
| 2 | Държавен вестник dv.parliament.bg API структура XML данни | 2026-06-22 | extract#2 (materiali.faces?idObj=N; no API/XML docs found) |
| 3 | data.egov.bg Държавен вестник набор от данни dataset | 2026-06-22 | negative (no ДВ dataset surfaced; portal is CKAN) |
| 4 | Държавен вестник закон за изменение и допълнение HistoryOfDocument препратки кой закон изменя | 2026-06-22 | extract#3 (ЗИД idMat=147391; APIS/N-Lex pointers) |
| 5 | N-Lex Bulgaria national law database dv.parliament.bg consolidated legislation access | 2026-06-22 | extract#4 (broeveList.faces; ДВ = corrections not full texts) |
| 6 | dv.parliament.bg broeve.faces брой архив по години PDF "Изтегли броя" | 2026-06-22 | extract#5 (dv130.faces; "Изтегли броя"=download issue) |
| 7 | APIS .HistoryOfDocument препратки законодателство свързани документи изменя отменя | 2026-06-22 | extract#6 (Изменя/Изменен със = APIS-built cross-ref graph) |
| 8 | Държавен вестник график излизане вторник петък извънреден брой dv.parliament.bg PDF формат | 2026-06-22 | extract#7 (Tue/Fri cadence; извънреден any day; PDF + online) |

## Documents Read

| # | File Path | Sections Read | Outcome |
|---|-----------|---------------|---------|
| 1 | docs/sync/HANDOFFS/2026-06-22-freshness-consolidation-resource-roadmap.md | §1, §5 (I3), §3a | context — confirms no API/feed, idMat URLs, PDF download |
| 2 | docs/process/delivery-contract.md | Rate Limiting Protocol, Phase 3 DoD | context — 1 req/sec rules, poller+amendment-detector DoD |
| 3 | docs/frs/INDEX.md | FR-002, FR-003, FR-009, FR-024 | context — DV monitor / ZID parser / re-source backlog |
| 4 | fetcher/bg/client.py | full | reusable RateLimitedSession pattern (lex.bg, cp1251) |

## Web Sources Referenced

| # | URL | Title | Date Accessed | Outcome |
|---|-----|-------|---------------|---------|
| 1 | https://dv.parliament.bg/robots.txt | (404) | 2026-06-22 | negative — no robots.txt (HTTP 404) |
| 2 | https://dv.parliament.bg/DVWeb/broeveList.faces | ДВ issue archive list | 2026-06-22 | extract#8 (413 pages / 4,121 issues; reverse-chron; filters) |
| 3 | https://dv.parliament.bg/DVWeb/showMaterialDV.jsp?idMat=147391 | ЗИД (state-of-emergency law) | 2026-06-22 | extract#9 (HTML text; amended act in TITLE only; no hyperlink) |
| 4 | https://dv.parliament.bg/DVWeb/showMaterialDV.jsp?idMat=17529 | Инструкция Iз-381/2009 | 2026-06-22 | extract#10 (HTML text; prose "(ДВ, бр. N от YYYY)" only) |
| 5 | https://dv.parliament.bg/DVWeb/materiali.faces?idObj=6121 | Issue 46 / 22.6.2026 contents | 2026-06-22 | extract#11 (issue-contents list; per-doc idMat links; sections) |
| 6 | https://n-lex.europa.eu/n-lex/info/info-bg/index | N-Lex Bulgaria national DB | 2026-06-22 | extract#12 (ДВ = official source; search-form only, no API; no free consolidated texts) |
| 7 | https://dv.parliament.bg/DVWeb/index.faces | ДВ home | 2026-06-22 | extract#13 (latest Брой 56/19.6.2026; per-material idMat links) |

## Extracted Content

| Source ref | Extract (verbatim, <300 words) | Used in section |
|------------|--------------------------------|-----------------|
| extract#1 | "The URL structure you mentioned (dv.parliament.bg with showMaterialDV.jsp and idMat parameters) is used to access specific materials from the Държавен вестник archive... The `idMat` parameter... appears to be a material ID used to retrieve specific documents." Result also surfaced `fileUploadShowing.jsp?idFileAtt=695143&allowCache=true&openDirectly=false`. | §2 |
| extract#2 | Result surfaced `https://dv.parliament.bg/DVWeb/materiali.faces?idObj=6121`. "the search results do not contain specific technical information about the API structure, XML data format, or programmatic access methods for dv.parliament.bg." | §2, §4 |
| extract#3 | "The search results do not contain a structured machine-readable dataset for ДВ." Portal data.egov.bg "ensures the publication and management of information for reuse in open, machine-readable format" using CKAN; no ДВ dataset identified. | §4 |
| extract#4 | ЗИД example surfaced: `showMaterialDV.jsp?idMat=147391` titled "Закон за изменение и допълнение". APIS legislation.apis.bg docs surfaced for the same family. | §3 |
| extract#5 | "The State Gazette is accessible at https://dv.parliament.bg/DVWeb/broeveList.faces. However... it consists mainly of editions and corrections of official documents rather than full texts of actual laws in Bulgaria." | §1, §3, §4 |
| extract#6 | Result surfaced `https://dv.parliament.bg/DVWeb/dv130.faces`. "'Изтегли броя' means 'Download Issue'... archive containing State Gazette issues... organized by year and issue number." | §1, §2 |
| extract#7 | "APIS offers functionality that allows you to trace the development (history) of 'families' of related acts. The system includes tracking of documents that amend ('Изменя') preceding acts and documents that are amended by ('Изменен със') subsequent amending acts." (web.apis.bg) | §3 |
| extract#8 (live) | broeveList.faces: "Issues are organized primarily by issue number ('Брой') and publication date... 'Брой 56, 19.6.2026 г.' through 'Брой 47, 22.5.2026 г.'... reverse-chronological. 413 pages total across 4,121 found results... 'Брой 52, 8.6.2026 г.' is marked '(извънреден)'... Search by Keyword, Issue number, Type (all, regular, extraordinary), Date range. Links contain jsessionid parameters... .faces resources typical of JavaServer Faces." | §1, §5 |
| extract#9 (live) | showMaterialDV.jsp?idMat=147391: Title "Закон за изменение и допълнение на Закона за мерките и действията по време на извънредното положение, обявено с решение на Народното събрание от 13 март 2020 г." Body = HTML text. "No dedicated 'history of document' section, hyperlinks, or consolidated law references are present." Amended law named in title; inline "(ДВ, бр. 28 от 2020 г.)". Issue: брой 34, 9.4.2020, section Народно събрание. | §2, §3 |
| extract#10 (live) | showMaterialDV.jsp?idMat=17529: Title "Инструкция № Iз-381 от 10 март 2009 г. за реда за обработка на лични данни в Министерството на вътрешните работи". "No hyperlinks to amended legislation exist. The document references laws only through inline prose citations in the format '(ДВ, бр. N от YYYY г.)': '(ДВ, бр. 71 от 2006 г.)'... 'Закона за защита на класифицираната информация'... named in prose without ДВ citation." Body = HTML text. | §2, §3 |
| extract#11 (live) | materiali.faces?idObj=6121: "this is a contents listing for a specific issue showing 18 materials... Issue 46, dated 22.6.2026." Sections: Народно събрание (laws incl. amendments), Министерски съвет (Resolutions 235-239), Ministerial Regulations, Regulatory Commission Decisions, Electoral Commission. "Sample link format: showMaterialDV.jsp;jsessionid=...?idMat=107486". No download-full-issue link in the excerpt. | §1, §2 |
| extract#12 (live) | N-Lex BG: "Bulgarian government official journal is State Gazette (http://dv.parliament.bg/)." Provides "only a search form front-end... no mention of an API. There is no reference to APIS or programmatic access." "State gazette consists mainly of editions and corrections of the official documents, and not of the full texts of actual laws in Bulgaria." Search "provides mainly information about changes in legislative papers, and not the whole list of acting laws." | §3, §4 |
| extract#13 (live) | index.faces: "Issue 56, dated June 19, 2026 ('Брой: 56, от дата 19.6.2026 г.')". "Изтегли броя (download issue) link is present, but the exact URL format is not fully visible... appears incomplete in the source code." Individual materials: "showMaterialDV.jsp;jsessionid=...?idMat=244149". | §1, §2 |
| extract#14 (live) | robots.txt → HTTP 404 Not Found (no robots.txt published at dv.parliament.bg root). | §5 |
| extract#15 | "The State Gazette is issued in regular issues every Tuesday and Friday of the week, when these days are working days." "Special/extraordinary issues... can be issued on both the days mentioned above and on other days of the week, including non-working days. Permission... is given by the Chairman of the National Assembly." "issues in PDF format or view them online." Appendices "published as attachments only on the internet page... has the same legal significance as the publication in the printed edition." (search #8) | §1, §2, §5 |
