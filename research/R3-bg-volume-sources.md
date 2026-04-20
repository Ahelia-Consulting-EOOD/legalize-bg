# R3 — BG Legislation Volume, Sources & Feasibility

**Author:** T3 (Volume Analyst)
**Date:** 2026-04-19
**Status:** Complete

## Executive Summary

Bulgarian legislation comprises an estimated **~400 laws (закони)**, **~20 codes (кодекси)**, **~200+ regulations (правилници)**, **~300+ ordinances (наредби)**, and **~100+ implementing rules (правилници по прилагане)** — roughly **1,000-1,200 primary/secondary normative acts** on lex.bg. Including historical/repealed acts, municipal ordinances, and court practice, the full corpus is likely **3,000-5,000 documents**. The total plain text volume is estimated at **150-300 MB**, or **500 MB-1 GB with HTML and metadata**.

A full local mirror is **technically feasible and inexpensive** (under EUR 5/month for storage). The main challenge is acquisition: lex.bg blocks automated access (403/SOAP auth), APIS charges ~EUR 270/year for read-only web access with no bulk export API, and dv.parliament.bg provides raw gazette issues but not consolidated texts. The most promising free source is **dv.parliament.bg** (4,101 issues since 2003, PDF format), supplemented by selective lex.bg scraping via Playwright.

---

## 1. Volume Estimation

### 1.1 lex.bg Tree Analysis

Direct Playwright navigation of lex.bg/laws/tree/ revealed:

| Category | URL Path | Pages | Acts per Page | Est. Total Acts |
|----------|----------|-------|---------------|-----------------|
| Закони (Laws) | /laws/tree/laws | 11 (0-10) | ~35 | **~385** |
| Кодекси (Codes) | /laws/tree/code | 1 | ~15-20 | **~15-20** |
| Наредби (Ordinances) | /laws/tree/ords | multiple | ~35 | **~200-350** |
| Правилници (Regulations) | /laws/tree/regs | multiple | ~35 | **~150-250** |
| Правилници по прилагане | /laws/tree/reg_laws | multiple | ~35 | **~80-150** |
| Конституция | single doc | 1 | 1 | **1** |

**Total estimated acts on lex.bg: ~850-1,150**

The laws tree (most thoroughly counted) has exactly 11 pages (pages 0-10), with the last page ending at letter Х (Kh). Page 0 shows 35 acts. The pagination shows links 1-10 plus ">>" pointing to page 10 as the last page.

Note: lex.bg tree pages return **403 to WebFetch** (simple HTTP), requiring Playwright for JS rendering. The tree is a flat alphabetical list, not a thematic categorization.

### 1.2 Wikisource Cross-Reference

Bulgarian Wikisource maintains a "Списък закони в Република България" with ~280+ laws visible (alphabetical, partially complete through letter И). Extrapolating through the full alphabet suggests **~500-600 total** including historical/repealed laws — consistent with the lex.bg count of ~385 (which may exclude repealed acts).

### 1.3 Volume Calculation

Based on known act sizes (from prior scraping in the project):

| Act Type | Example | Est. Articles | Est. Plain Text Size |
|----------|---------|---------------|---------------------|
| Large law (ЗОП) | ~221 articles | 200-300 | ~300-500 KB |
| Medium law (ЗЕУ) | ~80 articles | 50-100 | ~100-200 KB |
| Small law (ЗНА) | ~50 articles | 20-50 | ~30-80 KB |
| Code (ГПК, НК) | ~400-800 articles | 300-800 | ~500 KB-1 MB |
| Ordinance | ~30-50 articles | 20-50 | ~30-100 KB |

| Metric | Estimate | Method |
|--------|----------|--------|
| Total normative acts (lex.bg) | ~1,000-1,200 | Playwright page count x acts/page |
| Average act length (plain text) | ~150 KB | Weighted average: 20% large, 50% medium, 30% small |
| Total plain text | **~150-200 MB** | 1,100 acts x 150 KB |
| Total with HTML markup | **~300-400 MB** | ~2x plain text |
| Total with full metadata + history | **~500 MB-1 GB** | Including amendment history, cross-refs |
| State Gazette archive (PDF) | **~5-10 GB** | ~4,100 issues x 1-3 MB/issue |

### 1.4 State Gazette Statistics

- **Founded:** July 28, 1879
- **Publication frequency:** Every Tuesday and Friday (working days) + extraordinary issues
- **Total issues digitized:** 4,101 (per dv.parliament.bg search results)
- **Digital archive:** From 2003 (browsable), from 2009 (full-text searchable)
- **Issues per year:** ~100-110 regular + extraordinary
- **Ciela's scanned archive:** 1885-present, 180,000 scanned pages (1920-1989 period alone)

---

## 2. Data Sources

### 2.1 APIS Products

**Company:** АПИС Европа АД (formed from merger of АПИС България ООД in July 2014)

**Key Products:**

| Product | Description | Price (annual) |
|---------|-------------|---------------|
| APIS Pravo (Web) | Bulgarian legislation, consolidated texts, time machine | 525.61 BGN (~EUR 269) |
| APIS Praktika | Court practice database | Bundled/separate |
| APIS Register+ | 1M+ company registrations | Separate pricing |
| Register API | REST API for company data integration | 3 tiers: Start, Basic, Corporate |
| Euro Law | EU legislation | Separate |
| APIS Finance | Tax, accounting | Separate |

**Features of APIS Pravo:**
- Daily updates following State Gazette publication
- Time machine (historical versions at specific dates)
- 104 updates/year
- Cross-referenced hyperlinks between documents
- Export: RTF, HTML, PDF
- Search: Boolean operators, synonyms, advanced filters
- Constitutional Court decisions, Supreme Court practice

**API Access:** Register API exists for company data (REST). **No public API for legislation text.** No bulk download capability documented. Web access only via authenticated session.

**Relationship with lex.bg:** APIS and LEX.BG are **separate companies**:
- LEX.BG ЕАД (EIK 131468681) — owned by Софтуеър Пойнт България ЕООД, registered 2008
- АПИС Европа АД — separate entity, pioneer in legal information systems
- However, legislation.apis.bg offers free access to Bulgarian legislation (unclear relationship)

### 2.2 lex.bg (Free Tier)

**Operator:** ЛЕКС.БГ ЕАД (separate from APIS)

**Freely accessible:**
- Full consolidated texts of all normative acts (laws, codes, ordinances, regulations)
- Constitution
- Last State Gazette issue
- Legal news (news.lex.bg)
- Forum
- Mobile app (Android)

**Not freely accessible / Limited:**
- Справочник (reference/guide) — some features behind paywall/Ciela
- Advanced search — returns limited results (311 bytes for many queries)
- Historical versions — not available in free tier

**Technical limitations:**
- Many document URLs return 403 to simple HTTP requests
- Some documents require SOAP backend authentication
- JS rendering required for tree navigation
- No public API

### 2.3 dv.parliament.bg (State Gazette)

**Operator:** National Assembly of the Republic of Bulgaria

**Structure:**
- Archive from at least 2003 (browsable), some content back to 1989
- Full-text search available from 2009 onwards
- 4,101 total issues indexed
- Two sections: Official (laws, decrees) and Unofficial (admin acts, notifications)

**Formats:**
- Online HTML view of issue contents
- PDF download for individual issues
- Historical first issue (July 28, 1879) available as PDF

**Limitations:**
- No API documented
- No bulk download mechanism
- No XML or structured data export
- Pre-2003 issues require specific filter navigation
- Content is raw gazette (not consolidated) — each issue contains the original text as published, not incorporating subsequent amendments
- JS-heavy interface (prior research confirmed)

**Key insight:** DV provides **original texts as published** (ЗИД format for amendments), not consolidated versions. To build a consolidated view, one must apply all amendments in sequence — a significant technical challenge.

### 2.4 Government Open Data

**opendata.government.bg:**
- Portal exists, prioritized by Council of Ministers
- 119 datasets prioritized for open publication
- **No legislation dataset found** — primarily administrative/statistical data
- Based on EU PSI Directive transposition (Access to Public Information Act, Art. 15d)

**git.egov.bg (GitLab):**
- Government code repository (mirrors to github.com/governmentbg)
- Contains source code of government projects, NOT legislation texts
- EUPL-licensed projects
- Relevant as a hosting model, but no legal content

**parliament.bg:**
- Has a /bg/laws section
- JS-heavy, difficult to scrape (returned only performance monitoring scripts to WebFetch)
- Lists bills and adopted legislation, but unclear depth

### 2.5 Other Sources

**Ciela Norma (competitor to APIS):**

| Product | Price (annual, excl. VAT) |
|---------|--------------------------|
| Ciela Normi | 284 BGN (~EUR 145) |
| Ciela Normi + Norma magazine | 410 BGN (~EUR 210) |
| Ciela Normi.Net | 324 BGN (~EUR 166) |

- 15 information products
- State Gazette archive: digitized from 1885, 180,000 scanned pages (1920-1989)
- Free DV access at ciela.net/official-gazette (1885-present, but "informational only")
- **Caveat:** Free gazette access "does not include subsequent legislative changes" — no consolidation
- Sofia Bar Association members get free access (renewed Feb 2026)

**legislation.apis.bg:**
- Free access to Bulgarian legislation (discovered in prior research)
- Different structure from lex.bg
- Could not be scraped (returned empty content to WebFetch, likely JS-rendered)
- REST-style URLs observed

**LexAlert.bg:**
- State Gazette archive service
- Only 2025-2026 visible (2,222 publications in 41 issues)
- Informational, directs to dv.parliament.bg for official content

**EPI.bg (European Publishing Institution):**
- Browse State Gazette by issue
- Alternative commercial source

**N-Lex (EU portal):**
- Connects to Bulgarian national database (likely dv.parliament.bg)
- Provides cross-EU search interface
- Server returned 503 during testing

---

## 3. Full Mirror Feasibility

### 3.1 Storage Requirements

| Content | Est. Size | GDrive (15 GB free) | Hetzner VPS | AWS S3 |
|---------|-----------|---------------------|-------------|--------|
| Consolidated acts (plain text) | 150-200 MB | Fits easily | Fits easily | ~$0.005/mo |
| Consolidated acts (HTML + metadata) | 500 MB-1 GB | Fits easily | Fits easily | ~$0.023/mo |
| State Gazette PDFs (2003-present) | 5-10 GB | Fits in free tier | Fits easily | ~$0.23/mo |
| Full DV archive (1879-present, scanned) | 50-100 GB | Needs paid plan | CX22 (40 GB) too small, need upgrade | ~$2.30/mo |
| Full corpus + versions + court practice | 10-20 GB | Fits in free tier | Fits easily | ~$0.46/mo |

**Hosting options:**

| Option | Storage | Monthly Cost (EUR) | Pros | Cons |
|--------|---------|-------------------|------|------|
| Google Drive (free) | 15 GB | 0 | Free, easy sharing | No API, not a server |
| Google Drive (paid) | 100 GB | ~1.99 | Easy sharing | No server capabilities |
| Hetzner CX22 | 40 GB | ~3.79 | Full server, 20 TB transfer | 40 GB may be tight for full archive |
| Hetzner CX32 | 80 GB | ~6.59 | Comfortable for all data | Overkill for just storage |
| AWS S3 Standard | Pay-per-use | ~0.02-2.30 | Scalable, API built-in | Need application layer separately |
| AWS S3 + Lambda | Pay-per-use | ~1-5 | Serverless, scalable | AWS complexity |

**Conclusion:** Storage cost is negligible. Even the full archive with all versions fits comfortably in a EUR 4-7/month VPS.

### 3.2 Crawl Time Estimate

| Source | Acts/Documents | Rate Limit | Est. Crawl Time |
|--------|---------------|------------|-----------------|
| lex.bg (Playwright) | ~1,100 acts | 1 req/3-5 sec (polite) | ~1.5-2 hours |
| dv.parliament.bg PDFs | ~4,100 issues | 1 req/2 sec | ~2-3 hours |
| legislation.apis.bg | ~1,100 acts | Unknown | ~1-2 hours |
| Total initial crawl | | | **~5-7 hours** |

**Incremental updates:** ~2-3 new DV issues per week, ~5-10 modified acts — trivially fast.

### 3.3 Legal Considerations

**lex.bg Terms of Service:**
- Site has cookie consent and terms (lex.bg/termssite/)
- Terms not fully analyzed (would need legal review)
- Technical measures in place (403 blocks, SOAP auth) suggest automated access is discouraged
- No robots.txt information gathered

**dv.parliament.bg:**
- Official state publication — public information by definition
- Law on State Gazette (1995) mandates public access
- Since July 1, 2008: free online access mandated
- **Strongest legal basis for scraping** — government obligation to provide access

**APIS/Ciela products:**
- Commercial databases — redistribution likely prohibited by license
- Using for personal/organizational reference is fine
- Cannot mirror and redistribute

**Legal framework supporting open access:**
- Access to Public Information Act (Art. 15d)
- Electronic Governance Act (Art. 58a, 59)
- EU PSI Directive transposition
- Government code must be published at git.egov.bg (Art. 59, para. 1)

**Recommendation:** Use dv.parliament.bg as the primary **legal** source. Supplement with lex.bg for consolidated text verification, but do not redistribute lex.bg content.

### 3.4 Freshness/Update Strategy

- **State Gazette:** Published every Tuesday and Friday (+ extraordinary)
- **APIS Pravo:** 104 updates/year (matches DV frequency)
- **Proposed update cycle:**
  1. Monitor dv.parliament.bg for new issues (RSS, or poll twice weekly)
  2. Parse new DV for amendments (ЗИД-ове) affecting tracked acts
  3. Apply amendments to local consolidated copies
  4. Verify against lex.bg consolidated text (spot-check)
  5. Full re-crawl monthly for drift detection

---

## 4. Cost Comparison

| Approach | Setup Cost | Monthly Cost | Completeness | Freshness | Consolidation |
|----------|-----------|-------------|-------------|-----------|---------------|
| **APIS Pravo subscription** | 0 | ~EUR 22/mo (269/yr) | High (curated) | Same-day DV | Built-in |
| **Ciela Normi subscription** | 0 | ~EUR 12/mo (145/yr) | High (curated) | Same-day DV | Built-in |
| **Self-hosted mirror (DV-based)** | ~20h dev | EUR 4-7/mo (VPS) | Medium (raw DV) | Twice weekly | Must build |
| **Self-hosted mirror (lex.bg scrape)** | ~40h dev | EUR 4-7/mo (VPS) | High (consolidated) | Weekly re-scrape | Pre-consolidated |
| **Hybrid: subscribe + mirror** | ~10h dev | EUR 16-29/mo | Highest | Real-time | Commercial + local |
| **Google Drive + manual** | ~5h setup | EUR 0-2/mo | Low-medium | Manual | Manual |

---

## 5. Implications for Architecture

Given the volume analysis:

1. **Total data is small** — ~200 MB plain text, ~1 GB with metadata. This is trivially storable and processable. No need for distributed systems, databases, or complex infrastructure.

2. **The hard problem is acquisition, not storage.** lex.bg blocks automated access, APIS/Ciela have no bulk export API, and dv.parliament.bg provides raw (non-consolidated) gazette issues.

3. **Recommended primary approach:** 
   - Use **Playwright-based scraping of lex.bg** for initial corpus (consolidated texts)
   - Use **dv.parliament.bg** for ongoing updates (new DV issues)
   - Build a **consolidation engine** to apply DV amendments to local copies
   - Consider an **APIS Pravo subscription** as a verification/fallback source (EUR 269/year is affordable)

4. **For the user's immediate needs (ZOP-related skills):** A targeted approach scraping only the ~50-100 relevant acts is much simpler than a full mirror and could be done in hours.

5. **Full mirror is feasible** but the development effort for the consolidation engine is significant (see T4's research on this topic).

---

## Open Questions

1. **legislation.apis.bg** — Is this truly free? What's the relationship with APIS commercial products? Could not be scraped (JS-rendered).
2. **lex.bg Terms of Service** — Need full legal review of automated access terms.
3. **APIS/Ciela API roadmap** — Are either planning to offer programmatic API access to legislation?
4. **N-Lex integration** — Could the EU N-Lex gateway provide structured Bulgarian legislation data? (Server was 503 during testing)
5. **Municipal ordinances** — Not counted in volume estimate. Adds potentially hundreds more documents.
6. **Court practice** — APIS Praktika and Ciela Praktika contain Supreme Court/Constitutional Court decisions. Volume not estimated but could be substantial.
7. **Exact count of наредби and правилници** — lex.bg blocked WebFetch for these categories; Playwright browser crashed before counting.

---

## Sources Log

| # | Source | URL | Date Accessed | What Was Found |
|---|--------|-----|--------------|----------------|
| 1 | lex.bg laws tree | https://lex.bg/laws/tree/laws | 2026-04-19 | 11 pages of laws (~385 acts), pagination structure |
| 2 | lex.bg laws tree (last page) | https://lex.bg/laws/tree/laws/10 | 2026-04-19 | ~35 acts ending at letter Х |
| 3 | lex.bg codes tree | https://lex.bg/laws/tree/code | 2026-04-19 | Codes category exists, ~15-20 codes |
| 4 | APIS Pravo product page | https://apis.bg/bg/product/apis-pravo | 2026-04-19 | Features, daily updates, time machine, export formats |
| 5 | APIS products overview | https://apis.bg/en/products | 2026-04-19 | Product portfolio, Register API |
| 6 | APIS pricing page | https://apis.bg/en/prices | 2026-04-19 | 12-month subscriptions, 500 error on fetch |
| 7 | DobiPress APIS Pravo listing | https://dobipress.bg/catalogue/3877 | 2026-04-19 | Price: 525.61 BGN/year (~EUR 269), 104 updates/year |
| 8 | APIS monthly access | https://apis.bg/bg/month-pay-bg | 2026-04-19 | Monthly payment option exists, no prices shown |
| 9 | dv.parliament.bg | https://dv.parliament.bg | 2026-04-19 | Archive from 1989+, full-text search from 2009 |
| 10 | dv.parliament.bg issues list | https://dv.parliament.bg/DVWeb/broeveList.faces | 2026-04-19 | 4,101 total issues, 411 pages |
| 11 | DV Wikipedia (BG) | https://bg.wikipedia.org/wiki/Държавен_вестник | 2026-04-19 | Founded 1879, Tue+Fri schedule, 21K print run |
| 12 | E-Justice Portal (BG) | https://e-justice.europa.eu/.../bg_en | 2026-04-19 | Legal hierarchy, act types, commercial DBs mentioned |
| 13 | NYU Globalex Bulgaria | https://www.nyulawglobal.org/globalex/Bulgaria.html | 2026-04-19 | Legal system overview, DV as official publication |
| 14 | Wikisource BG laws list | https://bg.wikisource.org/wiki/Списък_закони... | 2026-04-19 | ~280+ laws listed (А-И), incomplete |
| 15 | Ciela free gazette | https://www.ciela.net/official-gazette | 2026-04-19 | 1885-present, no consolidation in free tier |
| 16 | Ciela pricing search | Web search | 2026-04-19 | Ciela Normi: 284 BGN/year (~EUR 145) |
| 17 | LEX.BG company info | papagal.bg/eik/131468681 + netlaw.bg | 2026-04-19 | Separate from APIS, owned by Софтуеър Пойнт България |
| 18 | LexAlert archive | https://lexalert.bg/archive/ | 2026-04-19 | 2025-2026 only, 2,222 publications |
| 19 | opendata.government.bg | Web search | 2026-04-19 | 119 datasets prioritized, no legislation dataset |
| 20 | git.egov.bg / governmentbg GitHub | Web search | 2026-04-19 | Code repos (EUPL), not legislation |
| 21 | Hetzner pricing | Web search | 2026-04-19 | CX22: EUR 3.79/mo (40 GB), price increase Apr 2026 |
| 22 | AWS S3 pricing | Web search | 2026-04-19 | Standard: $0.023/GB-month |
| 23 | APIS about page | https://apis.bg/en/about-apis | 2026-04-19 | Pioneer in BG legal info systems |
| 24 | N-Lex Bulgaria | https://n-lex.europa.eu/n-lex/info/info-bg/ | 2026-04-19 | 503 error both attempts |
| 25 | OECD Regulatory Scan BG | OECD PDF (2022) | 2026-04-19 | PDF binary, could not extract text |
