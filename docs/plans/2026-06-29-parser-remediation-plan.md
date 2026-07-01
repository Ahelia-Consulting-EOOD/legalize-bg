# Parser Data-Loss Remediation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix the lex.bg body parser so it can never again silently drop legal content, prove completeness per act with a class-agnostic gate, then re-bootstrap the full 3,599-act corpus and rebuild the catalog.

**Architecture:** The parser (`fetcher/bg/text_parser.py`) moves from a drop-by-default CSS allowlist to **format-known-classes + keep-unknown-by-default (chrome denylist)**, and the pipeline gains a **class-agnostic coverage gate** that hard-fails any act whose legal text isn't fully captured. Re-bootstrap re-runs the real fetch→parse→commit pipeline (gated by coverage) and is modelled as an FR-020 corrective baseline. Re-sourcing must first clear a Cloudflare block on lex.bg.

**Tech Stack:** Python 3.12, BeautifulSoup4 (lxml parser), pytest, requests, SQLite, git. `.venv/bin/python`.

## Global Constraints

- **Protected surfaces** (`.ahelia/protected-surfaces.yaml`): `fetcher/bg/` interfaces, YAML frontmatter schema, SQLite schema, MCP tool signatures, commit format. Any change requires an **IMPLEMENTATION-PREFLIGHT** doc per `docs/process/IMPLEMENTATION-PREFLIGHT.md` BEFORE code (Task 1).
- **Decisions of record:** D-047 (this remediation + D1–D4); D-011 (stop on Cloudflare, never retry); D-016 (`GIT_AUTHOR_DATE` = `YYYY-MM-DDT00:00:00+00:00`); D-039 (own structure, public-domain texts only); D-042 (FR-020 multi-version `law_versions` from git log).
- **lex.bg:** windows-1251 (`cp1251`); 1 req/sec; `https://lex.bg/laws/ldoc/{doc_id}`; no Playwright.
- **Completeness is proven by measuring uncovered text, NOT by enumerating classes** (`docs/research/2026-06-29-parser-data-loss-forensics/COMPLETENESS.md`).
- **The strict source-vs-output coverage check is the SOLE acceptance gate, applied to EVERY act** (owner directive 2026-06-29). Structure heuristics — "base Допълнителни разпоредби heading present", "§1 present" — are REJECTED: they give false negatives for acts that define terms in an article (e.g. ЗАДС, definitions in `Чл. 4`, no base ДР) and false positives when amendment blocks mask missing base content. Each act is checked against its OWN source.
- **Evidence base:** `docs/research/2026-06-29-parser-data-loss-forensics/` (`FINDINGS.md`, `EVALUATION.md`, `COMPLETENESS.md`, `forensics.py`, `coverage_ledger.py`).
- **No em-dashes** in any Bulgarian document output (not applicable to code/comments).
- TDD: failing test first; commit per task.

---

## Phase 0 — Interim safety (owner decision D-047/#2: keep serving offline)

> **The MCP server is NOT deployed anywhere yet (owner, 2026-06-29).** So there is no live takedown to perform — the action is a **deploy-guard**: build the refusal so the server *cannot* be deployed against the defective corpus until Phase 4 lifts it. No production checkpoint needed.

### Task 0: Add a deploy-guard so the defective corpus can't be served

**Files:**
- Modify: `mcp_server/__main__.py` (startup guard)
- Create: `docs/runbook/2026-06-29-corpus-offline-notice.md`

**Interfaces:**
- Produces: a startup refusal (env-overridable) so the MCP server does not serve known-incomplete legal text.

- [ ] **Step 1: Write the failing test**

```python
# tests/mcp_server/test_offline_guard.py
import os, pytest
from mcp_server.app_factory import build_app  # adjust to the real factory import

def test_server_refuses_to_start_when_corpus_flagged_defective(monkeypatch):
    monkeypatch.setenv("LEGALIZE_CORPUS_DEFECTIVE", "1")
    monkeypatch.delenv("LEGALIZE_ALLOW_DEFECTIVE", raising=False)
    with pytest.raises(SystemExit):
        build_app(catalog_path="catalog.db")
```

- [ ] **Step 2: Run test to verify it fails** — `Run: .venv/bin/pytest tests/mcp_server/test_offline_guard.py -v` → FAIL.

- [ ] **Step 3: Implement the guard** — in `build_app`, near the top:

```python
import os, sys
if os.environ.get("LEGALIZE_CORPUS_DEFECTIVE") == "1" and os.environ.get("LEGALIZE_ALLOW_DEFECTIVE") != "1":
    sys.stderr.write(
        "REFUSING TO START: corpus flagged defective (D-047 parser data-loss). "
        "Definitions and transitional provisions are missing corpus-wide. "
        "Set LEGALIZE_ALLOW_DEFECTIVE=1 to override for debugging only.\n")
    raise SystemExit(2)
```

- [ ] **Step 4: Run test to verify it passes** — `Run: .venv/bin/pytest tests/mcp_server/test_offline_guard.py -v` → PASS.

- [ ] **Step 5: Set the flag + document** — write `docs/runbook/2026-06-29-corpus-offline-notice.md` (why the guard exists, how to override for local debugging, when it lifts: after Phase 4 re-bootstrap passes the gate). Set `LEGALIZE_CORPUS_DEFECTIVE=1` as the repo/dev default (e.g. in the runbook + any local launch script) since there is no deployment yet.

- [ ] **Step 6: Commit** — `git commit -m "[fix] deploy-guard: refuse to serve defective corpus pending remediation (D-047)"`

---

## Phase 1 — Parser fix (protected surface; TDD)

### Task 1: IMPLEMENTATION-PREFLIGHT for the parser change

**Files:**
- Create: `docs/process/IMPLEMENTATION-PREFLIGHT-2026-06-29-parser.md`

- [ ] **Step 1:** Copy the structure of `docs/process/IMPLEMENTATION-PREFLIGHT-2026-06-21-fr020.md`. Fill in: surface = `fetcher/bg/text_parser.py` (Surface: Legalize fetcher interfaces); change = add 3 subdivision classes, FEA structured handling, heading de-glue, keep-unknown-by-default + chrome denylist; blast radius = whole corpus output (validated by the coverage gate); rollback = revert commit, re-run re-bootstrap; tests = the fixture-based parser tests below + the coverage gate.
- [ ] **Step 2: Commit** — `git commit -m "docs(preflight): parser data-loss remediation (D-047)"`

### Task 2: Restore the three dropped subdivision classes with correct formatting

**Files:**
- Modify: `fetcher/bg/text_parser.py`
- Test: `tests/fetcher/bg/test_text_parser.py`

**Interfaces:**
- Consumes: `HtmlToMarkdown().convert(soup) -> str` (existing).
- Produces: same signature; output now includes `## Допълнителни разпоредби`, `## Заключителни разпоредби …` (FinalEdicts), and the `FinalEdictsArticle` §-bodies with bold `**§ N.**` and точки/alineas as separate paragraphs; subdivision headings de-glued from their КЪМ act-names.

- [ ] **Step 1: Write the failing tests** (use the existing `_load_soup` helper):

```python
def test_additional_provisions_heading_present():
    md = HtmlToMarkdown().convert(_load_soup("zeu.html"))
    assert "## Допълнителни разпоредби" in md

def test_paragraph_definitions_captured():
    md = HtmlToMarkdown().convert(_load_soup("zeu.html"))
    assert "§ 1." in md and "По смисъла" in md

def test_final_edicts_heading_variant_captured():
    # ГПК carries standalone "Заключителни разпоредби КЪМ ..." blocks (class=FinalEdicts)
    md = HtmlToMarkdown().convert(_load_soup("gpk.html"))
    assert "Заключителни разпоредби" in md

def test_transitional_heading_is_not_glued_to_kym():
    md = HtmlToMarkdown().convert(_load_soup("gpk.html"))
    assert "разпоредбиКЪМ" not in md  # de-glued

def test_section_paragraph_bodies_present_for_zuo_like():
    md = HtmlToMarkdown().convert(_load_soup("zop.html"))
    assert md.count("§") > 20  # §-provisions, not just headings
```

- [ ] **Step 2: Run to verify they fail** — `Run: .venv/bin/pytest tests/fetcher/bg/test_text_parser.py -v -k "additional or definitions or final_edicts or glued or paragraph_bodies"` → FAIL.

- [ ] **Step 3: Implement** — extend `CLASS_MAP` and add structured handling:

```python
CLASS_MAP = {
    "TitleDocument": ("# ", True),
    "PreHistory": ("*", True),
    "Part": ("## ", True),
    "Heading": ("### ", True),
    "Section": ("#### ", True),
    "Article": ("", True),
    "AdditionalEdicts": ("## ", True),        # Допълнителни разпоредби heading
    "FinalEdicts": ("## ", True),             # Заключителни разпоредби (КЪМ ...) heading
    "TransitionalFinalEdicts": ("## ", True),
    "FinalEdictsArticle": ("", True),         # § definition / transitional bodies
    "HistoryOfDocument": ("", False),
}
```

Add a `_format_paragraph_article` (handles `<div>`-separated точки and `<br>` alineas, bold `**§ N.**`/`**Чл. N.**`), route `Article` and `FinalEdictsArticle` to it, and render heading classes with `el.get_text(" ", strip=True)` collapsed (de-glue). Reference implementation: `docs/research/2026-06-29-parser-data-loss-forensics/rescrape_zuo.py` (`FixedHtmlToMarkdown._block_text` / `_format_edict_article`) — port it into the module.

- [ ] **Step 4: Run to verify pass** — `Run: .venv/bin/pytest tests/fetcher/bg/test_text_parser.py -v` → PASS (including the pre-existing tests — no regression).

- [ ] **Step 5: Commit** — `git commit -m "[fix] parser: capture ДР/ПЗР subdivisions, de-glue headings (D-047)"`

### Task 3: Keep-unknown-by-default with a chrome denylist

**Files:**
- Modify: `fetcher/bg/text_parser.py`
- Test: `tests/fetcher/bg/test_text_parser.py`

**Interfaces:**
- Produces: any content-region element whose class is neither in `CLASS_MAP` nor in `CHROME_DENYLIST` is still emitted (plain text) AND logged at WARNING, so an unknown legal class surfaces as visible text instead of vanishing.

- [ ] **Step 1: Write the failing test** — synthetic HTML with a novel class:

```python
def test_unknown_content_class_is_kept_not_dropped():
    html = ('<div class="TitleDocument">Z</div>'
            '<div class="SomeBrandNewEdict">КЪМ ЗАКОНА ЗА НЕЩО СИ нова разпоредба</div>')
    md = HtmlToMarkdown().convert(BeautifulSoup(html, "lxml"))
    assert "нова разпоредба" in md  # kept by default, not silently dropped

def test_known_chrome_class_is_excluded():
    html = ('<div class="TitleDocument">Z</div>'
            '<p class="buttons">ДОБАВИ В МОИТЕ АКТОВЕ</p>')
    md = HtmlToMarkdown().convert(BeautifulSoup(html, "lxml"))
    assert "ДОБАВИ В МОИТЕ АКТОВЕ" not in md
```

- [ ] **Step 2: Run to verify they fail** — `Run: .venv/bin/pytest tests/fetcher/bg/test_text_parser.py -v -k "unknown_content or known_chrome"` → FAIL.

- [ ] **Step 3: Implement** — add a denylist and a default-keep branch in `convert`, scoped to the legal-content region (reuse the LCA logic from `coverage_ledger.py`):

```python
import logging
log = logging.getLogger(__name__)
CHROME_DENYLIST = {"buttons", "boxi", "boxinb", "picHasEditions", "picRefsFromActs",
                   "HistoryOfDocument", "HistoryItem", "HistoryReference",
                   "NewDocReference", "SameDocReference", "LegalDocReference", "contextads"}
```

In the content-region walk, for an element whose class is unmapped: if any class is in `CHROME_DENYLIST` → skip; else emit `el.get_text(" ", strip=True)` and `log.warning("unmapped content class kept: %s", el.get("class"))`. (References inside mapped elements stay covered via their parent — do not double-emit nested matches.)

- [ ] **Step 4: Run to verify pass** — `Run: .venv/bin/pytest tests/fetcher/bg/test_text_parser.py -v` → PASS.

- [ ] **Step 5: Commit** — `git commit -m "[fix] parser: keep unknown content by default + chrome denylist (D-047/D3)"`

---

## Phase 2 — Class-agnostic coverage gate (the guarantee; TDD)

### Task 4: Coverage validator module

**Files:**
- Create: `fetcher/bg/coverage.py`
- Test: `tests/fetcher/bg/test_coverage.py`

**Interfaces:**
- Produces: `uncovered_legal_text(soup, markdown, chrome_whitelist=DEFAULT_WHITELIST) -> dict` returning `{"uncovered_chars": int, "buckets": {class: chars}}` — the Cyrillic text in the content region not present in `markdown` and not in a chrome bucket. Productionizes `coverage_ledger.py`.

- [ ] **Step 1: Write the failing tests**

```python
def test_full_capture_has_zero_uncovered():
    soup = _load_soup("naredba-04-14.html")
    md = HtmlToMarkdown().convert(soup)
    res = uncovered_legal_text(soup, md)
    assert res["uncovered_chars"] <= 30  # only fixed chrome residual (e.g. 'ДОБАВИ...')

def test_detects_a_forced_drop():
    soup = _load_soup("zeu.html")
    md = HtmlToMarkdown().convert(soup)
    # simulate a regression: remove the definitions from the output
    broken = md.replace("По смисъла", "XXXXX")
    res = uncovered_legal_text(soup, broken)
    assert res["uncovered_chars"] > 200
```

- [ ] **Step 2: Run to verify fail** — `Run: .venv/bin/pytest tests/fetcher/bg/test_coverage.py -v` → FAIL.
- [ ] **Step 3: Implement** — port `coverage_ledger.py`'s LCA + per-text-node covered/excluded/uncovered classification into `fetcher/bg/coverage.py`, matching against the markdown with whitespace/markup-insensitive normalization (strip `**`, unify quotes, collapse whitespace — see `ZUO-VERIFICATION.md`).
- [ ] **Step 4: Run to verify pass** — `Run: .venv/bin/pytest tests/fetcher/bg/test_coverage.py -v` → PASS.
- [ ] **Step 5: Commit** — `git commit -m "feat(coverage): class-agnostic legal-text coverage validator (D-047)"`

### Task 5: Wire the gate into the fetch→parse pipeline as a hard fail

**Files:**
- Modify: `bootstrap.py`, `refresh.py` (per-act parse path)
- Test: `tests/test_bootstrap.py`

**Interfaces:**
- Produces: per-act, after `convert`, call `uncovered_legal_text` **against that act's own source soup**; if `uncovered_chars > THRESHOLD` (default 64, env-tunable) → HALT/record a gate failure for that act (do not write a defective file silently); aggregate a gate report. This strict source-vs-output check is the SOLE acceptance gate for every act — no base-ДР/§1 structure heuristic. A gate failure means *uncovered legal text*, which the operator triages into (a) a genuine drop (new unmapped class → add to formatting map) vs (b) a structural surprise that is actually complete; ЗАДС (definitions in `Чл. 4`, no base ДР) is the canonical example of why the heuristic is wrong and the strict check is right.

- [ ] **Step 1: Write the failing test** — feed a fixture through the bootstrap parse path with a stubbed parser that drops the ДР; assert the act is flagged, not written. (Mirror existing `tests/test_bootstrap.py` patterns.)
- [ ] **Step 2: Run to verify fail.**
- [ ] **Step 3: Implement** the gate call + `GateFailure` accumulation + a written `gate-report.json`.
- [ ] **Step 4: Run to verify pass.**
- [ ] **Step 5: Commit** — `git commit -m "feat(pipeline): hard coverage gate on every parsed act (D-047)"`

### Task 6: Regression sweep over all 7 fixtures

- [ ] **Step 1:** Add a parametrized test asserting `uncovered_legal_text(...).uncovered_chars` is within the chrome threshold for every fixture in `tests/fixtures/html/*.html` (closes the original test blind spot).
- [ ] **Step 2: Run** `Run: .venv/bin/pytest tests/fetcher/bg/ -v` → all PASS.
- [ ] **Step 3: Commit** — `git commit -m "test(parser): coverage regression across all act-type fixtures"`

---

## Phase 3 — Cloudflare / re-sourcing spike (owner decision D-047/#1: solve CF + re-fetch lex.bg)

> Investigation, not TDD. Re-bootstrap (Phase 4) is GATED on this producing a working, rate-limited, ToS-respectful fetch path. Honor D-011 (stop on CF) and D-039 (texts only).

### Task 7: Reproduce + characterize the Cloudflare block
- [ ] One rate-limited GET to `https://lex.bg/laws/ldoc/2135802037`; capture status, headers, body markers. Confirm it is the `_CF_MARKERS` path in `fetcher/bg/client.py`.

### Task 8: Evaluate bypass options (decision gate)
- [ ] Compare, with a tiny spike each: (a) realistic browser headers + cookie jar / session warm-up; (b) `cloudscraper`-style challenge solver; (c) a single authenticated browser session exporting cookies for the rate-limited `requests` session; (d) fallback: drive the existing `mcp__plugin_playwright` browser to fetch server-rendered HTML (no Playwright dependency added to the pipeline — used only as a sourcing tool).
- [ ] **Decision gate (owner):** pick the lex.bg-CF path, OR pivot this whole phase to the D-038/FR-024 ДВ + official-consolidation source. Record as a DECISIONS addendum to D-047.

### Task 9: Implement the chosen fetch path behind the existing client interface
- [ ] Keep `HttpTransport.get(doc_id) -> bytes` and the 1 req/sec `RateLimitedSession` contract; add the CF-clearing layer underneath. Add a small live smoke (1 act) gated behind a network marker.

---

## Phase 4 — Full corrective re-bootstrap (gated on Phases 1–3)

### Task 10: Dry-run re-parse from existing fixtures + ЗУО capture
- [ ] Re-parse the 7 fixtures + the ЗУО capture with the fixed parser; run the coverage gate on each; confirm 0 gate failures. (No network.) Commit nothing — this is a go/no-go.

### Task 11: Re-fetch + re-parse the full corpus on a branch
- [ ] Branch `refresh/2026-06-29-parser-fix` (mirror D-014: feature branch, `--push-every 250`, 3× push retry).
- [ ] Run `bootstrap.py` (or `refresh.py`) across all 5 category dirs via `fetcher/bg/discovery.py`, fixed parser + coverage gate active. Any gate failure HALTS and is triaged (do not commit defective acts).
- [ ] Commit discipline: corrective baseline, NOT `[reforma]`. Use a distinct commit tag (e.g. `[popravka-parser]`) and `GIT_AUTHOR_DATE` = each act's existing legislative date (D-016) so FR-020 timelines are not shifted; the baseline boundary is documented for FR-020 (D-047/#4).

### Task 12: Rebuild the catalog + verify
- [ ] `Run: .venv/bin/python -m index.build` (full rebuild) then `.venv/bin/python scripts/verify_catalog.py`.
- [ ] Assert corpus-wide: `grep -rlF "Допълнителни разпоредби" laws codes ordinances regulations implementing --include='*.md' | wc -l` is now in the thousands (was 7), and a sample of acts pass `uncovered_legal_text`.
- [ ] Spot-check FR-020: `get_law(name, date)` / `diff()` on a multi-version act return content WITH definitions.

### Task 13: FR-020 corrective-baseline handling
- [ ] In `index/build.py` version derivation, ensure the corrective-baseline commit does not create a spurious "incomplete→complete" version (squash/ignore the baseline boundary per D-047/#4). Add an oracle test (act with pre-fix + post-fix commits yields the correct version count).

---

## Phase 5 — Lift offline + governance close-out

### Task 14: Lift the offline flag
- [ ] After Task 12 passes, unset `LEGALIZE_CORPUS_DEFECTIVE` in the deployment; smoke the live MCP server (search / get_law / get_article / get_articles / diff / get_law(date)).

### Task 15: Documentation + decisions
- [ ] Update `DECISIONS.md` D-047 → mark remediated (date, commit, gate-report path); add the CF-decision addendum (Task 8).
- [ ] Update `ACTIVE.md`: replace the P0 banner with a "remediated" note; restore the corpus-trustworthy status.
- [ ] Update `docs/sync/MEMORY` pointer and the auto-memory `project_legalize_bg.md` (corpus re-bootstrapped, parser fixed, gate in place).
- [ ] Add `tests/fetcher/bg/test_text_parser.py` note referencing the coverage gate as the standing completeness guarantee.
- [ ] Retire the interim ЗУО note (the act is now part of the clean re-bootstrap).

---

## Self-Review

- **Spec coverage (R1–R5 / D1–D4):** R1 → Task 2; R2 (concat) → Task 2; R3 (keep-by-default) → Task 3; R4 (coverage gate + tests) → Tasks 4–6, 13; R5 (full re-bootstrap) → Tasks 11–12. D1 → Phase 4; D2 → Task 2; D3 → Tasks 3–6; D4 → Task 13. Interim offline (decision #2) → Task 0. CF (decision #1) → Phase 3.
- **Open gates the owner must clear:** Task 0 deployment location; Task 8 CF-vs-ДВ source decision.
- **Risk:** Phase 4 depends entirely on Phase 3 succeeding; if CF cannot be cleared cleanly, escalate to the FR-024 ДВ/official source rather than forcing a fragile bypass.
