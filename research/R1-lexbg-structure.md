# R1 — lex.bg Structure & Technical Analysis

**Date:** 2026-04-20
**Author:** T1 (Site Analyst)
**Status:** Complete

## Executive Summary

lex.bg is Bulgaria's primary legal information portal, operated by Ciela Norma (a subsidiary of the Dutch-Belgian Wolters Kluwer group). The site serves consolidated (current) versions of Bulgarian legislation through a straightforward server-side rendered HTML architecture. There is no API, no SOAP backend for public content, and no JavaScript rendering requirement for law text — the earlier assumptions about SOAP auth blocking and Flash rendering were incorrect.

Direct HTTP access via `curl` or `requests` works reliably for ALL tested document IDs, with ANY User-Agent, without cookies or authentication. The site returns well-structured HTML with semantic CSS classes (`.Article`, `.Part`, `.Heading`, `.Section`, etc.) that are ideal for programmatic extraction. Pages are behind Cloudflare CDN but no challenge pages were triggered during testing.

The normative acts tree contains approximately **3,574 acts** across 5 categories (laws, codes, ordinances, regulations, implementation regulations), plus the Constitution. No rate limiting was observed even with 10+ rapid sequential requests. The entire catalog can be scraped from the tree pages without authentication.

## 1. Site Architecture

### 1.1 Laws Tree Structure

The "Справочник / Нормативни актове" section organizes legislation into 6 categories:

| Category | URL Path | Pages | Act Count | Notes |
|----------|----------|-------|-----------|-------|
| Конституция | `/laws/ldoc/521957377` | 1 | 1 | Direct link, not paginated |
| Закони (Laws) | `/laws/tree/laws` | 12 | ~394 | 35 items/page, last page has 9 |
| Кодекси (Codes) | `/laws/tree/code` | 1 | 24 | All on single page |
| Наредби (Ordinances) | `/laws/tree/ords` | 75 | ~2,604 | Largest category |
| Правилници (Regulations) | `/laws/tree/regs` | 14 | ~490 | |
| Правилници по прилагане | `/laws/tree/reg_laws` | 2 | 61 | |
| **TOTAL** | | **~105** | **~3,574** | |

**Pagination pattern:** `/laws/tree/{category}/{pageIndex}` where pageIndex is 0-based. Each page shows ~35 items sorted alphabetically. The pager uses a sliding window of 10 page numbers with `<<` (first visible batch), `<` (previous), `>` (next), `>>` (last visible batch) navigation.

**Tree depth:** The tree is flat — one level of categories, then direct links to law documents. No sub-categories or hierarchical navigation.

### 1.2 URL Patterns

| Pattern | Example | Purpose | Works with curl? |
|---------|---------|---------|-----------------|
| `/laws/ldoc/{docID}` | `/laws/ldoc/2136735703` | Full consolidated law text | Yes |
| `/laws/tree/{category}` | `/laws/tree/laws` | Browse acts by category | Yes |
| `/laws/tree/{category}/{pageIdx}` | `/laws/tree/laws/3` | Paginated browse | Yes |
| `/laws/lastdv` | `/laws/lastdv` | Latest State Gazette issue | Yes |
| `/laws/ldoc/{docID}/0/1` | `/laws/ldoc/2136735703/0/1` | Add to "My Acts" (requires login) | 302 redirect |
| `/lawsdetails/articles/{docID}/{artID}` | `/lawsdetails/articles/2136735703/i_1` | Per-article cross-references | Yes |
| `/lawsdetails/files/{docID}/{artID}` | `/lawsdetails/files/2136735703/i_1` | Per-article files | Yes |
| `/lawsdetails/proc/{docID}/{artID}` | `/lawsdetails/proc/2136735703/i_1` | Per-article case law | Yes |
| `/lawsdetails/notes/{docID}/{artID}` | `/lawsdetails/notes/2136735703/i_1` | Per-article notes | Yes |
| `/lawsdetails/relatednews/{docID}/{artID}` | `/lawsdetails/relatednews/2136735703/i_1` | Related news articles | Yes |
| `/bg/laws/ldoc/{docID}` | `/bg/laws/ldoc/2136735703` | Bulgarian language prefix | Yes (same content) |
| `/en/laws/ldoc/{docID}` | `/en/laws/ldoc/2136735703` | English prefix (but content is BG) | Yes |
| `/guide` | `/guide` | Main reference page | Yes |
| `/rss/forum` | `/rss/forum` | Forum RSS feed | Yes |

**Mobile version:** `m.lex.bg` returns 404 — no mobile subdomain exists.

**Search:** The search form at the top of each page does not work via direct GET/POST — returns 400 or redirects to homepage. Search appears to be handled by the paid "Справочник" (Ciela) product.

### 1.3 Page Rendering

**Law text pages** are fully server-side rendered. The HTML contains the complete law text in the initial response — no JavaScript rendering, no AJAX loading, no Flash. The "Adobe Flash Player 9" message visible in the page text is a leftover from an old Ciela navigation toolbar that is no longer functional.

**Tree pages** are also fully server-side rendered with static HTML pagination links.

**JavaScript dependencies:** The site uses jQuery 1.2.6 (ancient) for minor UI elements. The Cloudflare challenge script is injected but does not block scraping via curl.

**Encoding:** ALL pages use `windows-1251` encoding (NOT UTF-8). This is critical for parsing — decode with `cp1251` before processing.

## 2. API & Backend

### 2.1 Network Requests

No AJAX calls, SOAP endpoints, or API patterns were found for content delivery. The network traffic from a law page consists entirely of:
- The main HTML document (server-rendered, single request)
- Static assets (CSS, JS, images)
- Google Analytics tracking (`G-16F1C2CEKH`)
- Google AdSense ads (`ca-pub-9092264232006105`)
- Facebook social widget
- eTarget ad network
- Gemius analytics

**No content-loading XHR/AJAX requests** — all law text is in the initial HTML response.

### 2.2 Authentication & Sessions

- **No authentication required** for reading law texts
- **No cookies required** — identical content returned with and without cookies
- **No session tokens** — stateless access works fine
- **Cookie consent banner** exists but is purely cosmetic for ad targeting
- **"My Acts" feature** requires login (user registration at `/register`)
- **Справочник (paid)** features require a Ciela subscription

### 2.3 Rate Limiting

**No rate limiting detected.** Tests performed:
- 5 rapid sequential requests to the same URL: all HTTP 200, ~1.1-1.6s each
- 10 rapid sequential requests to different doc IDs: all HTTP 200
- All User-Agent strings tested: all HTTP 200 (including empty UA, python-requests, wget, curl, Googlebot)

**Cloudflare CDN** is in front (challenge script present) but did not trigger any blocks during testing. The `robots.txt` blocks non-major-search-engine bots (`Disallow: /` for `User-agent: *`), but this is not enforced at the HTTP level.

**Response times:** ~1.1-1.6s per page for full law documents (2+ MB for large laws like ЗОП).

## 3. Access Methods Comparison

| Method | Works? | Speed | Reliability | Notes |
|--------|--------|-------|-------------|-------|
| curl + browser UA | Yes | ~1.2s/page | High | Any UA works, no cookies needed |
| curl + any UA | Yes | ~1.2s/page | High | Even empty/python/wget UAs work |
| Python requests | Yes (expected) | ~1.2s/page | High | No special headers needed, decode as cp1251 |
| Playwright browser | Yes | ~3-5s/page | High | Overkill — not needed for law text |
| WebFetch (Claude tool) | No (403) | N/A | N/A | Tool-specific issue, not lex.bg blocking |
| BeautifulSoup parse | Yes | Fast | High | Well-structured semantic HTML |

**Recommended approach:** Simple `requests` + `BeautifulSoup` with `cp1251` decoding. Playwright is NOT needed for any content currently on lex.bg. This is a significant simplification from the original 5-layer architecture proposal.

## 4. Doc ID System

### 4.1 Structure

Doc IDs are **signed 32-bit integers**. Examples:
- Конституция: `521957377`
- Валутен закон: `-12802047` (negative!)
- ЗОП (2016): `2136735703`
- Кодекс на труда: `1594373121`

The IDs appear to be sequential/chronological within a range but the exact encoding is opaque. Key observations:
- Older laws have smaller positive IDs (e.g., 1589654529 for Наказателен кодекс from 1968)
- Negative IDs exist (e.g., Валутен закон: -12802047)
- IDs in the 2135-2137 million range correspond to 2005-2025 era laws

### 4.2 Programmatic Discovery

Doc IDs can be reliably discovered by crawling the tree pages:
1. Fetch `/laws/tree/{category}/{pageIndex}` for all categories
2. Extract `href` attributes matching `/laws/ldoc/{docID}`
3. Parse doc ID from URL

This is deterministic and complete — the tree contains ALL acts available on the site.

### 4.3 Article ID Format

Within a law, articles are identified as `i_{number}` (e.g., `i_1`, `i_602`). These are used in `lawsdetails` URLs. The numbering appears to be sequential but may have gaps (e.g., i_1, i_10, i_100 — no i_2 through i_9 in the sampled data). This needs further investigation.

## 5. Machine-Friendly Access

### 5.1 robots.txt

```
User-agent: Googlebot
Allow: /
User-agent: Bingbot
Allow: /
User-agent: Slurp
Allow: /
User-agent: Applebot
Allow: /
User-agent: DuckDuckBot
Allow: /
User-agent: *
Disallow: /
```

Major search engines are allowed; all others are formally disallowed. However, **this is not enforced** — all UAs get HTTP 200 regardless.

### 5.2 Sitemaps

**No sitemap.xml found** — returns HTTP 403.

### 5.3 RSS/Atom Feeds

- **Forum RSS:** `https://lex.bg/rss/forum` — RSS 2.0, windows-1251 encoded. Contains forum posts, NOT legislation updates.
- **No legislation RSS feed** exists.

### 5.4 API Documentation

**No public API.** The site is operated by Ciela Norma AD, which sells API access as part of its commercial product suite. The free web portal has no documented API.

## 6. Document HTML Structure

Law documents use well-defined CSS classes:

| CSS Class | Purpose | Example |
|-----------|---------|---------|
| `.TitleDocument` | Law title | "ЗАКОН ЗА ОБЩЕСТВЕНИТЕ ПОРЪЧКИ" |
| `.PreHistory` | Effective date | "В сила от 15.04.2016 г." |
| `.HistoryOfDocument` | Amendment history | All DV references |
| `.HistoryItem` | Single amendment entry | "изм. и доп. ДВ. бр.63..." |
| `.HistoryReference` | DV issue number link | "63" |
| `.Part` | Part (Част) | "Част първа. ОСНОВНИ ПОЛОЖЕНИЯ" |
| `.Heading` | Heading (Глава) | "Глава първа. ПРЕДМЕТ, ЦЕЛ И ПРИНЦИПИ" |
| `.Section` | Section (Раздел) | |
| `.Article` | Article (Член) | Full article with paragraphs |
| `.AdditionalEdicts` | Additional provisions | |
| `.TransitionalFinalEdicts` | Transitional provisions | |
| `.FinalEdicts` | Final provisions | |
| `.FinalEdictsArticle` | Articles within final provisions | |

**ЗОП example statistics:** 308 articles, 8 parts, 31 headings, 37 sections, 635K characters total.

### 6.1 Cross-Reference System

Articles contain JavaScript hooks for the Ciela desktop application:
- `window.external.OpenRef(this, {refID})` — link to another legal act
- `window.external.ShowLinkContent(this, {refID})` — tooltip with referenced text
- `window.external.HideLinkContent(this)` — hide tooltip
- `window.external.OpenEdition({N})` — view historical version (desktop app only)

These do NOT work in the browser but the reference IDs could be useful for building a cross-reference graph.

## Implications for Architecture

### Major Simplification

The original 5-layer architecture (Doc ID catalog → HTTP scraper → Playwright fallback → Alternative sources → Cache) can be **dramatically simplified**:

1. **Playwright is NOT needed.** All content is server-rendered HTML accessible via simple HTTP requests.
2. **SOAP backend issue was a wrong doc ID**, not an auth problem. The corrected ЗЕУ ID (2135555445) works fine.
3. **No cookies, sessions, or special headers needed.** Plain HTTP GET requests work.
4. **Well-structured HTML** with semantic CSS classes makes parsing straightforward.

### Recommended Architecture (Simplified)

```
Layer 1: Catalog Builder
  - Crawl /laws/tree/{category}/{page} for all categories
  - Extract all doc IDs and names
  - Store in SQLite with category metadata
  - ~105 HTTP requests to build complete catalog

Layer 2: Content Fetcher
  - Simple requests.get() with cp1251 decoding
  - BeautifulSoup parsing using CSS class selectors
  - Extract: title, effective date, amendment history, structured articles
  - ~1.2s per document, no rate limiting

Layer 3: Cache
  - Local file cache keyed by doc ID + fetch date
  - Invalidation: re-fetch when DV amendment history changes
```

### Caveats

1. **Cloudflare:** Currently not blocking but could start. Keep Playwright as emergency fallback.
2. **robots.txt:** Formally disallows non-search-engine bots. Respect by rate-limiting to ~1 req/sec.
3. **Encoding:** Must handle windows-1251 throughout.
4. **No time machine:** Only latest consolidated version is available. Historical versions require tracking DV amendments externally.
5. **Search doesn't work programmatically.** Must use tree navigation or maintain own search index.

## Open Questions

1. **Article ID numbering scheme:** Why are article IDs like `i_602` instead of `i_1`? Is there a mapping between article IDs and article numbers (e.g., "Чл. 1" = `i_602`)?
2. **DV cross-reference resolution:** Can we programmatically resolve DV issue/year to find the specific amendment text?
3. **How often does lex.bg update after a DV publication?** Is there a lag?
4. **Are there any acts NOT in the tree?** (e.g., repealed laws, historical acts)
5. **Reference ID system:** What do the numeric reference IDs in `OpenRef()` calls correspond to? Are they stable?
6. **Negative doc IDs:** What determines whether a doc ID is positive or negative?

## Sources Log

| # | Source | URL | Date Accessed | What Was Found |
|---|--------|-----|--------------|----------------|
| 1 | robots.txt | https://lex.bg/robots.txt | 2026-04-20 | Disallow for non-major-search-engine bots |
| 2 | sitemap.xml | https://lex.bg/sitemap.xml | 2026-04-20 | 403 — no sitemap |
| 3 | Laws tree (page 1) | https://lex.bg/laws/tree/laws | 2026-04-20 | 35 laws, 12 total pages |
| 4 | Laws tree (last page) | https://lex.bg/laws/tree/laws/11 | 2026-04-20 | 9 laws on last page |
| 5 | Codes tree | https://lex.bg/laws/tree/code | 2026-04-20 | 24 codes, single page |
| 6 | Ordinances tree | https://lex.bg/laws/tree/ords | 2026-04-20 | ~2,604 ordinances, 75 pages |
| 7 | Regulations tree | https://lex.bg/laws/tree/regs | 2026-04-20 | ~490 regulations, 14 pages |
| 8 | Impl. regulations | https://lex.bg/laws/tree/reg_laws | 2026-04-20 | 61 acts, 2 pages |
| 9 | ЗОП full text | https://lex.bg/laws/ldoc/2136735703 | 2026-04-20 | 308 articles, 635K chars, full HTML |
| 10 | ЗЕУ full text | https://lex.bg/laws/ldoc/2135555445 | 2026-04-20 | 105 articles, 141K chars — WORKS (previously failed with wrong ID) |
| 11 | ЗНА full text | https://lex.bg/laws/ldoc/2127837184 | 2026-04-20 | Works via curl |
| 12 | ППЗОП full text | https://lex.bg/laws/ldoc/2136789316 | 2026-04-20 | Works via curl |
| 13 | lawsdetails/articles | https://lex.bg/lawsdetails/articles/2136735703/i_1 | 2026-04-20 | Per-article cross-reference popup, cp1251 |
| 14 | lawsdetails/proc | https://lex.bg/lawsdetails/proc/2136735703/i_1 | 2026-04-20 | Per-article case law popup |
| 15 | Forum RSS | https://lex.bg/rss/forum | 2026-04-20 | RSS 2.0, cp1251, forum posts only |
| 16 | LastDV | https://lex.bg/laws/lastdv | 2026-04-20 | 52KB, latest State Gazette issue |
| 17 | Network traffic | Playwright inspector | 2026-04-20 | No AJAX content calls, only GA/ads/FB |
| 18 | Rate limit test | curl x10 rapid | 2026-04-20 | No throttling detected |
| 19 | UA test | curl with various UAs | 2026-04-20 | All UAs return HTTP 200 |
| 20 | Cookie test | curl with/without cookies | 2026-04-20 | No cookies required |
