# FR-025 discovery spike — finding (2026-07-02)

**Task:** FR-025 plan Task 1 (read-only discovery). **Method:** live lex.bg inspection
via the CF-hardened path (Playwright-minted `cf_clearance` + rate-limited client).

## Headline finding (reshapes FR-025)

**lex.bg does NOT expose ПМС / тарифи / инструкции / решения / укази as browsable
act-type trees.** The plan assumed the bootstrap crawled 5 of N browsable tree
categories and silently dropped the rest; in fact lex.bg's tree browse has **only**
those 5 categories, and the other act-types are not tree-browsable at all.

## Evidence

1. **Tree navigation exposes exactly 5 slugs.** Extracting every `/laws/tree/{slug}`
   link from the navigation yields only: `laws` (Закони), `code` (Кодекси),
   `ords` (Наредби), `regs` (Правилници), `reg_laws` (Правилници по прилагане).
   No `post`/`pms`/`tarifi`/`instr`/`resh`/`ukazi`/etc.

2. **A known active ПМС confirms it.** ldoc 2135501600 (ПОСТАНОВЛЕНИЕ № 46/2005,
   НСС, active) renders with browse links to only those same 5 trees. The act exists
   and is reachable by direct `ldoc`, but nothing on the page (or site nav) places it
   in a browsable act-type index.

3. **Candidate tree slugs return the generic homepage, not a listing.** Probing
   `tree/{slug}/0` via the rate-limited client:
   - baseline `laws/0` → ~51 KB HTML, **36** `ldoc` links (a real listing).
   - `post`, `pms`, `tarifi`, `tarif`, `instr`, `instruktsii`, `resh`, `resheniya`,
     `ukazi`, `ukaz`, `razp`, `reshenia`, `dv`, `postanovleniya` → each ~46 KB HTML,
     **1** `ldoc` link (the homepage fallback). None resolve to an act listing.

4. **Search is keyword-only, not an enumeration.** The site search
   (`https://lex.bg/search`, POST) is full-text with `search_for_acts` /
   `search_for_instr` flags — relevance-ranked keyword search over acts. There is no
   "list all acts of type X" browse. Keyword search cannot exhaustively enumerate an
   act-type set (unknown keyword space, ranked/capped results), so it cannot prove
   completeness — the D-047 discipline we require.

## Implication for FR-025

The corpus omission (ПМС etc. absent) is **real**, but the **cause and the fix both
change**:

- Cause is NOT "we crawled 5 of N browsable trees." It is "lex.bg's browsable index
  covers only 5 act-types; the rest are per-document only."
- Fix therefore CANNOT be "add tree slugs to `CATEGORIES_CONFIG` and crawl them"
  (plan Phase 3/5) — there are no additional trees to crawl.
- Exhaustive coverage of ПМС/тарифи/инструкции/решения/укази requires a source that
  **enumerates by act-type**. The only complete such source for Bulgarian law is the
  **Държавен вестник (ДВ)** — the official gazette, which publishes every act-type.
  That is exactly the acquisition layer **FR-024 / roadmap-Phase-3 (DV monitor)**
  builds. FR-025's sourcing therefore **converges with the ДВ acquisition track**
  (design §6 R4 was the central issue, not a peripheral risk).

## What survives from the plan

- **Task 3 (probe-to-end discovery)** and **Task 4 (corpus-level coverage gate)**
  remain valid *mechanisms* (robustness + a set-level gate), but the gate's manifest
  is not "lex.bg tree slugs" — it must be "act-types that should exist + their source."
- **Tasks 5 & 7 (wire tree slugs + crawl trees)** are invalidated as written.
- The read-only enumerate script (Task 1 Step 2) was made moot by finding #3 (no trees
  to quantify), so it was not written (YAGNI).

## Recommended next step

Owner decision required (escalated 2026-07-02): FR-025 cannot proceed as a lex.bg tree
crawl. Options — (A) merge FR-025 sourcing into the FR-024 / DV-monitor acquisition
layer; (B) lex.bg keyword-search best-effort (cannot prove completeness — contradicts
the coverage principle); (C) on-demand per-act capture only (as done for the НСС
decree) until the ДВ layer exists; (D) pause FR-025 and fold "which act-types + which
source" into the FR-024/DV design.
