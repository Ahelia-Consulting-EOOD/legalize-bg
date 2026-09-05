# Follow-up: fetcher hard-stops on Cloudflare - CF-clearing is not integrated into the lex.bg pipeline

- **Status:** Open
- **Discovered:** 2026-07-01, from the drs-bg-government-package НДЕФ-vs-ПУДООС evaluation (external repo `drs-govpkg-pudoos`), needing the НДЕФ наредба primary text.
- **Area:** `fetcher/bg` (`RateLimitedSession` / `LexBgClient`); the refresh / rescrape path.
- **Related:** `docs/plans/2026-06-29-parser-remediation-plan.md`; `docs/research/2026-06-29-parser-data-loss-forensics/` (esp. `rescrape_acts.py`).

## Summary

lex.bg now serves a Cloudflare JS challenge (HTTP 403, "Just a moment...") on `/laws/ldoc/*`.
`RateLimitedSession.get_bytes()` detects this and raises `CloudflareChallenge` **by design** (per the
delivery contract's "stop immediately on Cloudflare challenges"). As a result, any lex.bg re-fetch - a
bootstrap re-run or a targeted rescrape/refresh - hard-stops. A plain browser `User-Agent` does not help;
the challenge is JS-based.

A working workaround exists but is **manual and not integrated**:
`docs/research/2026-06-29-parser-data-loss-forensics/rescrape_acts.py` fetches with a `cf_clearance` cookie
plus a browser UA into a raw `requests.Session`, decodes cp1251, and runs the fixed parser. But the
`cf_clearance` value there is a placeholder ("refresh via Playwright browser ... read context.cookies"), it
expires (session / UA / IP bound), and the extraction is a manual step. Nothing in `fetcher/bg` or the
refresh path clears Cloudflare automatically.

## Reproduction (2026-07-01)

- **Plain fetcher stops.** `LexBgClient(transport=HttpTransport(session=RateLimitedSession(user_agent=CHROME_UA))).fetch_soup(2135484858)`
  raises `CloudflareChallenge: ... (status 403)`, even with a Chrome UA.
- **Correct method works.** Clear the challenge once in a Playwright browser (navigate the act URL, wait for
  "Just a moment" to disappear), read `cf_clearance` via `page.context().cookies('https://lex.bg')`, inject
  it and the matching UA into a `requests.Session`, GET the raw page, `decode("cp1251")`,
  `BeautifulSoup(..., "lxml")`, then the standard `HtmlToMarkdown().convert` + `MetadataParser().parse` +
  `assemble_file`. On the НДЕФ наредба (ordinance `2135484858`, not in the 12-act forensics batch): HTTP
  **200**, coverage gate `uncovered_chars=21` (pass), **20/20 articles**, and the **full ПЗР tail
  recovered**. The old-parser corpus copy
  (`ordinances/naredba-za-ustroystvoto-i-deynostta-na-natsionalniya-doveritelen-ekofond.md`) truncates the
  ПЗР at ПМС № 185/2010; the fixed-parser rescrape captures ПМС № 185/2010, ПМС № 81/2014 (§ 11) and
  ПМС № 1/2016 (§ 12). This confirms the `fix/parser-data-loss` parser is correct on raw HTML; the only
  remaining blocker is Cloudflare clearing.

## Recommendation

Integrate browser-assisted Cloudflare clearing into the fetcher / refresh path. A small Playwright helper:
navigate a lex.bg act URL, wait for the "Just a moment" challenge to clear, read `cf_clearance` (and the
browser UA) from the browser context, and hand both to `RateLimitedSession`; on a caught
`CloudflareChallenge`, refresh the token once before failing. Keep the 1 req/s rate limit and the raw-cp1251
decode. This unblocks the refresh / rescrape track without a manual cookie paste and without touching the
parser.

## Provenance

Surfaced while building `docs/reference/kb-ndef/` (the ПУДООС-vs-НДЕФ suitability evaluation) in
`drs-govpkg-pudoos`. That program's global rule - "lex.bg is never 'blocked'; use the legalize-bg
corpus/tools" - routes such primary-law needs here, which is how this gap was hit from the consumer side.
