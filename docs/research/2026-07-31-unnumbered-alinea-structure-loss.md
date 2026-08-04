# Unnumbered-alinea structure loss (ЗЗД class) — verification, root cause, lineage

**Date:** 2026-07-31 · **Status:** VERIFIED (end-to-end, live-source round-trip)
**Trigger:** external session constatation: „every ЗЗД article returns paragraph: null and any ал. lookup fails“ — claimed corpus parse gap.

## Verdict

The reported behavior is REAL and fully reproduced, but it is **not a ЗЗД-specific parse
accident and not a corpus-integrity failure**. It is the composition of:

1. **Defect A (parser, fidelity loss):** `fetcher/bg/text_parser.py::_extract_article_text`
   treats ONLY `<br>` as an intra-article paragraph break. lex.bg renders old
   (pre-Указ-883/1974) acts with **each unnumbered алинея as its own child `<div>`**
   inside the `Article` element; those div boundaries are silently joined with spaces.
   The corpus Markdown therefore glues multi-alinea articles into one flowed paragraph.
   The gluing is OURS — the lex.bg source preserves the boundaries.
2. **Defect B (data model, scope gap):** `index/provisions.py::_split_alineas` emits
   alinea rows only for explicit `(N)` markers (per D-023). Marker-less (pre-1974)
   acts get zero alinea rows even though their алинеи are legally citable
   (ВКС routinely cites „чл. 36, ал. 2 ЗЗД“). Even with Defect A fixed, Defect B
   independently keeps ал.-lookups failing until implicit position-based numbering
   is added.
3. **Defect C (minor, distinct):** ЗЗД's 1950 ПЗР *quote* articles inserted into the
   old Закон за гражданското съдопроизводство; the extractor adopted the quoted
   anchors as ЗЗД's own articles → bogus `available_articles` entries
   „1001а“–„1001г“. Same family as FR-030 (quoted-anchor false positives), but at
   article level, not alinea level.

**Text content is NOT lost anywhere** — the D-047 coverage gate (text-presence,
character-level) held; what is lost for the affected class is intra-article
*paragraph topology* and alinea addressability.

## Evidence chain

| # | Evidence | Result |
|---|----------|--------|
| 1 | `catalog.db`: ЗЗД provisions | 459 rows, **all** `paragraph IS NULL` |
| 2 | MCP `get_article("…", "чл. 36, ал. 2")` | `ARTICLE_NOT_FOUND` (paragraph="2") — exact reported failure |
| 3 | MCP `get_article("…", "чл. 36")` | one flowed text, both алинеи glued, `paragraph: null` |
| 4 | Live fetch ldoc 2121934337 (pipeline client, 2026-07-31) | чл. 36 = `<div><b>Чл. 36.</b> Едно лице…</div><div>Последиците…</div>` — **source separates алинеи** |
| 5 | Round-trip: fresh HTML → `HtmlToMarkdown().convert()` | byte-identical glued output vs corpus file → corpus faithfully reflects the *current parser*, defect is live, not historical |
| 6 | ЗЗД HTML stats | 453 `Article` divs; **184 with ≥2 child divs** (up to 12) — 184 articles structurally flattened |
| 7 | Sample fetches | ЗН (2121542657): 49/97 articles flattened; ЗЛС (2121624577): 17/166 flattened |
| 8 | `fetcher/bg/coverage.py::uncovered_legal_text` | compares normalized text presence only — structure-blind by design, gate correctly passed |

## Lineage — why every gate and review missed it

- **2026-04-20 `0ffe7a09`** — initial converter: `_extract_article_text` breaks on `<br>` only.
- **2026-04-20 `f9ccb7db`** (Phase 1a I7 fix) — „preserve alinea structure as Markdown
  paragraphs“: fixed the `<br>` layout; test `test_preserves_paragraph_structure`
  pins ONLY a `<br>`-separated fixture. The child-`<div>` layout never had a fixture.
- **2026-05-09 D-023** — provisions populated „one row per `(K)` alinea“: the
  numbered-marker assumption became the data-model contract. No doc anywhere
  mentions the unnumbered pre-1974 class — an undocumented blind spot, not a
  documented limitation.
- **2026-07-01 D-047 remediation** — the SOLE per-act gate is strict source-vs-output
  *text* coverage (heuristics deliberately rejected). Structure loss preserves every
  character → invisible to the gate.
- **2026-07-02 review / P0-2 / FR-030 / D-055** — all alinea work audited the
  *numbered-marker* path (false positives from years/citations). The marker-less
  class was never in any review's hypothesis space.

Systemic cause: every verification surface measures **text presence**; none measures
**paragraph topology**. The defect class sits exactly in the blind spot shared by
all of them.

## Blast radius

- **Zero-alinea acts (lower bound):** 41 acts have no alinea rows at all. Weighted by
  size/importance: ЗЗД (459 арт. rows), Закон за собствеността (125). Rest are minor.
- **Undercount warning:** the zero-alinea query MISSES mixed acts — ЗН has 3
  amendment-era `(N)` markers, so it escapes the query while 49/97 of its articles
  are flattened. The true affected set = „acts where lex.bg uses child-div alinea
  layout“, establishable only by a corpus refetch sweep (~3,600 req @ 1 req/s ≈ 1 h).
- **Concentration:** the class is small in count but is the **civil-law backbone**
  (ЗЗД, ЗС, ЗН, ЗЛС) — maximal practical citation impact (ВКС practice cites their
  алинеи constantly).
- **Modern acts (~3,560) unaffected** on current evidence: they use `<br>`-separated
  numbered алинеи (handled since I7); 305,122 alinea rows exist and work. Definitive
  confirmation of zero div-layout occurrences among them requires the same sweep.

## What this does and does not impugn

- Does NOT impugn: text completeness (D-047 gate held), metadata, numbered-act alinea
  rows, search, time-machine. The corpus remains reliable as *text*.
- DOES impugn: intra-article paragraph structure and ал.-addressability for the
  old-act class; any consumer that equates „no alinea row“ with „single-alinea
  article“; blind trust that text-coverage gates certify *structure*.

## Remediation options (not executed — for owner decision)

1. **Fix Defect A:** `_extract_article_text` must flush on child block boundaries
   (`div`/`p`) as `_block_text` already does — plus a child-div fixture test.
2. **Fix Defect B:** for marker-less multi-paragraph articles, derive implicit
   alinea numbers from paragraph position (ал. 1 = first paragraph, …), flagged
   (e.g. `implicit: true`) to keep provenance honest.
3. **Corpus refetch sweep** (~1 h) to (a) quantify the affected set exactly and
   (b) re-parse affected acts after the fix; per-act commits per convention.
4. **Structure gate:** add a per-act structural check (source block count vs output
   paragraph count per article) to close the topology blind spot permanently.
5. **Defect C:** fold quoted-article-anchor discrimination into the FR-030
   reasoning-based post-processing track.

Frontmatter/FRS/ledger registration deliberately left to the owner's process.
