# ЗУО re-scrape — completeness verification (interim fix)

**Date:** 2026-06-29 · **File:** `laws/zakon-za-upravlenie-na-otpadatsite.md` · **ldoc:** 2135802037
**Source:** 2026-06-21 lex.bg capture (ЗУО unchanged since dv 81/2024; live lex.bg is Cloudflare-blocked).
**Method:** real pipeline (`LexBgClient.fetch_soup` → `MetadataParser` → `assemble_file`) with the body
parser swapped for `FixedHtmlToMarkdown` (3 dropped classes added + structured §-bodies + de-glued
headings). Harness: `rescrape_zuo.py`. The protected parser module was NOT edited.

## Verdict: COMPLETE ✓

Oracle test (every legal subdivision element in the source must appear in the output, matched
whitespace/markup-insensitively on both its start and end):

| Check | Result |
|---|---|
| Legal subdivision elements in source (Article, FinalEdictsArticle, AdditionalEdicts, FinalEdicts, TransitionalFinalEdicts) | **276** |
| Elements NOT fully covered in output | **0** |
| §1 definitions block (точки 1..51, 13,271 norm-chars) present as one contiguous substring | **yes** |
| Допълнителни разпоредби heading present | yes |
| `## …разпоредби` ДР/ПЗР headings | 25, **0 bare** (all have bodies) |
| Чл. articles preserved | 173 |
| § provisions captured (max №) | 46 distinct (up to §156) |
| Приложения | 8 |
| Heading-concatenation artifacts | 0 (de-glued) |
| Size | 307,783 → **374,203 chars** (+66,420) |

Old broken copy retained at `zuo-OLD-broken.md`; new file at `zuo-NEW-fixed.md` (== corpus file).

## Caveats (do not affect completeness; for the proper parser fix)
- Nested numbered enumerations inside a точка render as top-level paragraphs (cosmetic; all text present).
- This is an INTERIM single-act fix via a sandbox parser. The corpus-wide remediation (D-047) still
  requires the real parser fix (IMPLEMENTATION-PREFLIGHT) + coverage gate + full re-bootstrap.
