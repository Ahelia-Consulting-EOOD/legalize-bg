# FR-025 Corpus Act-Type Category Coverage — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Bring the omitted lex.bg act-type categories (ПМС confirmed; likely тарифи/инструкции/…) into the corpus, and install a corpus-level coverage gate so no future act-type category can be silently dropped again.

**Architecture:** Fix the *class* not the instance (per D-047): a read-only discovery spike enumerates every act-type tree lex.bg exposes and quantifies the gap → owner scope decision → a committed category manifest becomes the source of truth → discovery is made probe-to-end (no hard-coded page counts) → a corpus-level coverage gate asserts every enumerated category is present-or-waived → the in-scope categories are fetched through the CF-hardened, per-act-coverage-gated pipeline (the D-047 bulk runbook) → catalog rebuild + close-out.

**Tech Stack:** Python 3.12, BeautifulSoup4 (lxml), pytest, requests, SQLite, git, PyYAML. `.venv/bin/python`. Playwright MCP for `cf_clearance` minting.

**Design doc:** `docs/plans/2026-07-02-fr025-category-coverage-design.md` (decisions D1–D5).

## Global Constraints

- **lex.bg:** windows-1251 (`cp1251`); ≤1 req/sec; tree URL `https://lex.bg/laws/tree/{slug}/{page}` (0-based); doc URL `https://lex.bg/laws/ldoc/{doc_id}`.
- **Cloudflare:** live lex.bg is CF-gated. Use the D-047 Task 9 path: real-browser `cf_clearance` minted via Playwright MCP, replayed in `RateLimitedSession(cookie_path=...)`; re-mint on each ~30-min TTL. **D-011:** stop-and-wait for a fresh cookie, NEVER an automated solver. **D-039:** fetch texts only; build our own structure.
- **D-048:** corpus commits set only `GIT_AUTHOR_DATE` (legislative date); committer-date stays real. Never re-introduce `GIT_COMMITTER_DATE` backdating.
- **Coverage gate (D-047):** the strict source-vs-output per-act coverage check is the SOLE per-act acceptance gate; no base-ДР/§1 structure heuristics.
- **Protected surfaces** (`.ahelia/protected-surfaces.yaml`): `fetcher/bg/` interfaces, YAML frontmatter schema (`rango`), SQLite schema, commit-message format. Any change requires IMPLEMENTATION-PREFLIGHT (Task 2) BEFORE code.
- **Single source of truth:** the category list lives ONLY in `fetcher/bg/discovery.py` (`CATEGORIES_CONFIG`, `CATEGORY_DIRS`), imported by `bootstrap.py`/`refresh.py`/`index/build.py`.
- **Slug stability (D-030):** `law_id = path.stem` never changes; ADDED acts mint new slugs, EXISTING reuse on-disk slug; ADDED acts translate the lex.bg tree slug → corpus dir via `CATEGORY_DIRS`.
- No em-dashes in any Bulgarian document output (N/A to code/English docs).
- TDD: failing test first; commit per task.

## File Structure

- `scripts/fr025_enumerate_categories.py` (create) — read-only spike: given a slug list, probe each lex.bg tree to end, count acts, cross-check corpus, emit gap report + manifest.
- `docs/research/2026-07-02-fr025-category-gap.md` (create) — the gap report (human).
- `docs/data/lexbg-categories.yaml` (create) — the category MANIFEST (machine source of truth: every known lex.bg act-type slug + status).
- `fetcher/bg/discovery.py` (modify) — probe-to-end crawl; add in-scope categories to `CATEGORIES_CONFIG`/`CATEGORY_DIRS`.
- `fetcher/bg/coverage_categories.py` (create) — corpus-level coverage gate over the manifest.
- `tests/fetcher/bg/test_discovery_probe.py` (create) — probe-to-end tests.
- `tests/fetcher/bg/test_coverage_categories.py` (create) — corpus-level gate tests.
- `docs/process/IMPLEMENTATION-PREFLIGHT-2026-07-02-fr025.md` (create).
- `docs/process/COVERAGE-FLOOR.md` (modify) — replace fixed-5-categories floor.
- `docs/sync/DECISIONS.md`, `docs/frs/INDEX.md`, `docs/sync/ACTIVE.md` (modify) — governance close-out; register FR-026.

---

## Task 1: Discovery & quantification spike (read-only) + owner scope gate

**Files:**
- Create: `scripts/fr025_enumerate_categories.py`
- Create: `docs/research/2026-07-02-fr025-category-gap.md`
- Create: `docs/data/lexbg-categories.yaml`

**Interfaces:**
- Produces: `docs/data/lexbg-categories.yaml` — list of `{slug, name, act_count, in_corpus_count, omitted_count, status}` where `status ∈ {present, candidate}` (candidate = omitted, awaiting scope decision). Consumed by Tasks 3–5 (which slugs to add) and Task 4 (the gate).

- [ ] **Step 1: Enumerate the act-type slugs lex.bg exposes (agent vision, not code).**
  Mint a `cf_clearance` cookie (Playwright MCP; runbook `docs/runbook/2026-07-01-cf-cookie-mint.md`). Navigate the lex.bg legislation navigation (the „Справочник / Нормативни актове" menu and `https://lex.bg/laws/tree/…` roots) and read the category list directly. Record every act-type tree slug and its Bulgarian label. Cross-check against the current 5 (`laws`/`code`/`ords`/`regs`/`reg_laws`). Write the raw slug→label list into the gap report as the enumeration source-of-record.

- [ ] **Step 2: Write the quantifier script.**

```python
# scripts/fr025_enumerate_categories.py
"""FR-025 read-only discovery spike: probe each lex.bg act-type tree to its end,
count acts, cross-check the corpus, emit the gap report + category manifest.
Read-only: no corpus writes, no commits. Honors <=1 req/s + cf_clearance (D-011)."""
import argparse, json, re, sys
from pathlib import Path
import yaml
from fetcher.bg.client import RateLimitedSession, HttpTransport
from fetcher.bg.discovery import LEX_BG_TREE, ENCODING, DOC_ID_PATTERN, CATEGORY_DIRS
from bs4 import BeautifulSoup

def probe_category(transport, slug, max_pages=500):
    """Crawl tree pages 0..N until a page yields NO new doc_ids. Returns the set
    of doc_ids across the category (deduped)."""
    seen = set()
    for page in range(max_pages):
        raw = transport.get_tree_page(f"{LEX_BG_TREE}/{slug}/{page}")
        html = raw.decode(ENCODING)
        ids = {int(m.group(1)) for m in DOC_ID_PATTERN.finditer(html)}
        new = ids - seen
        if not new:
            break            # end-of-category: no new acts on this page
        seen |= new
    return seen

def corpus_doc_ids(root: Path):
    """doc_id -> True for every act already in the corpus (any category dir),
    read from the `identificador` frontmatter field."""
    ids = set()
    for d in set(CATEGORY_DIRS.values()) | {"postanovleniya"}:
        for f in (root / d).glob("*.md") if (root / d).exists() else []:
            m = re.search(r"^identificador:\s*'?(-?\d+)'?", f.read_text(encoding="utf-8"), re.M)
            if m:
                ids.add(int(m.group(1)))
    return ids

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--slugs", required=True, help="comma-separated slug:label pairs, e.g. 'post:Постановления,tarifi:Тарифи'")
    ap.add_argument("--cookie-file", required=True)
    ap.add_argument("--root", default=".")
    ap.add_argument("--out-manifest", default="docs/data/lexbg-categories.yaml")
    ap.add_argument("--out-report", default="docs/research/2026-07-02-fr025-category-gap.md")
    a = ap.parse_args()
    session = RateLimitedSession(cookie_path=a.cookie_file, cookie_wait_sec=900)
    transport = HttpTransport(session=session)
    have = corpus_doc_ids(Path(a.root))
    rows, manifest = [], []
    for pair in a.slugs.split(","):
        slug, _, label = pair.partition(":")
        ids = probe_category(transport, slug)
        in_corpus = len(ids & have)
        omitted = len(ids - have)
        status = "present" if slug in CATEGORY_DIRS else "candidate"
        rows.append((slug, label, len(ids), in_corpus, omitted, status))
        manifest.append({"slug": slug, "name": label, "act_count": len(ids),
                         "in_corpus_count": in_corpus, "omitted_count": omitted,
                         "status": status})
    Path(a.out_manifest).write_text(yaml.safe_dump(manifest, allow_unicode=True, sort_keys=False), encoding="utf-8")
    lines = ["# FR-025 category gap report (2026-07-02)\n",
             "| slug | name | acts | in corpus | omitted | status |",
             "|---|---|---|---|---|---|"]
    for slug, label, n, ic, om, st in rows:
        lines.append(f"| {slug} | {label} | {n} | {ic} | {om} | {st} |")
    Path(a.out_report).write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("wrote", a.out_manifest, "and", a.out_report)

if __name__ == "__main__":
    main()
```

- [ ] **Step 3: Run the spike.**

Run: `.venv/bin/python scripts/fr025_enumerate_categories.py --slugs "<from Step 1>" --cookie-file "$SCRATCH/cf_cookie.json"`
Expected: `docs/data/lexbg-categories.yaml` + `docs/research/2026-07-02-fr025-category-gap.md` written; every enumerated slug has a row; the 5 known slugs show `status=present`.

- [ ] **Step 4: Commit the spike + evidence.**

```bash
git add scripts/fr025_enumerate_categories.py docs/data/lexbg-categories.yaml docs/research/2026-07-02-fr025-category-gap.md
git commit -m "feat(fr025): read-only category discovery spike + gap report + manifest (D-049)"
```

- [ ] **Step 5: OWNER SCOPE GATE (decision, not code).**
  Present the gap-report table to the owner. Owner marks each `candidate` slug as **in-scope** or **waived**. Update `docs/data/lexbg-categories.yaml`: set `status: in_scope` or `status: waived` (+ `waiver_ref`) for each candidate. Record the decision as a DECISIONS addendum to D-049 (done in Task 6). **Do not proceed to Task 3 until this gate is resolved.**

---

## Task 2: IMPLEMENTATION-PREFLIGHT for the protected-surface changes

**Files:**
- Create: `docs/process/IMPLEMENTATION-PREFLIGHT-2026-07-02-fr025.md`

- [ ] **Step 1: Write the preflight.** Copy the structure of `docs/process/IMPLEMENTATION-PREFLIGHT-2026-06-29-parser.md`. Fill in: surfaces = `fetcher/bg/discovery.py` (Legalize fetcher interfaces) + YAML frontmatter (`rango` new values) + commit-format (new `[nova]` acts, no format change); change = probe-to-end crawl + add in-scope categories + new `rango` values + corpus-level coverage gate; blast radius = discovery output + which acts exist in the corpus (validated by the corpus-level gate + per-act coverage gate); rollback = revert commits, corpus dirs are additive; tests = Tasks 3–4 below.

- [ ] **Step 2: Commit.**

```bash
git add docs/process/IMPLEMENTATION-PREFLIGHT-2026-07-02-fr025.md
git commit -m "docs(preflight): FR-025 category coverage (D-049)"
```

---

## Task 3: Probe-to-end discovery (TDD)

**Files:**
- Modify: `fetcher/bg/discovery.py`
- Test: `tests/fetcher/bg/test_discovery_probe.py`

**Interfaces:**
- Consumes: `CatalogCrawler`, `parse_tree_page` (existing).
- Produces: `CatalogCrawler.crawl_category(transport, slug) -> list[dict]` that pages until a page yields no new doc_ids (no reliance on `CATEGORIES_CONFIG` page counts); `crawl_all` uses it so growth and new categories are never truncated.

- [ ] **Step 1: Write the failing test.**

```python
# tests/fetcher/bg/test_discovery_probe.py
from fetcher.bg.discovery import CatalogCrawler

class FakeTransport:
    """Serves 2 pages of a category then empty pages (end-of-category)."""
    def __init__(self, pages): self.pages = pages   # {url: html_bytes}
    def get_tree_page(self, url): return self.pages.get(url, b"<html></html>")

def _page(*doc_ids):
    links = "".join(f'<a href="/laws/ldoc/{i}">act {i}</a>' for i in doc_ids)
    return f"<html>{links}</html>".encode("cp1251")

def test_crawl_category_probes_until_no_new_ids():
    pages = {
        "https://lex.bg/laws/tree/post/0": _page(101, 102),
        "https://lex.bg/laws/tree/post/1": _page(103),
        "https://lex.bg/laws/tree/post/2": _page(),          # empty -> stop
    }
    got = CatalogCrawler().crawl_category(FakeTransport(pages), "post")
    assert sorted(e["doc_id"] for e in got) == [101, 102, 103]

def test_crawl_category_stops_on_all_duplicate_page():
    pages = {
        "https://lex.bg/laws/tree/post/0": _page(101, 102),
        "https://lex.bg/laws/tree/post/1": _page(101, 102),  # no NEW ids -> stop
    }
    got = CatalogCrawler().crawl_category(FakeTransport(pages), "post")
    assert sorted(e["doc_id"] for e in got) == [101, 102]
```

- [ ] **Step 2: Run to verify it fails.**

Run: `.venv/bin/python -m pytest tests/fetcher/bg/test_discovery_probe.py -v`
Expected: FAIL (`crawl_category` not defined).

- [ ] **Step 3: Implement `crawl_category` + route `crawl_all` through it.**

```python
# in fetcher/bg/discovery.py, on CatalogCrawler
def crawl_category(self, transport, slug, max_pages: int = 1000) -> list[dict]:
    """Crawl tree pages 0..N until a page yields no NEW doc_ids (end-of-category).
    Robust to lex.bg growth and to unknown page counts (FR-025/D5)."""
    seen: set[int] = set()
    out: list[dict] = []
    for page_idx in range(max_pages):
        url = f"{LEX_BG_TREE}/{slug}/{page_idx}"
        html = transport.get_tree_page(url).decode(ENCODING)
        new = [e for e in self.parse_tree_page(html, slug) if e["doc_id"] not in seen]
        if not new:
            break
        for e in new:
            seen.add(e["doc_id"])
            out.append(e)
    return out
```

Refactor `crawl_all` to iterate `CATEGORIES_CONFIG` keys and call `crawl_category(transport, slug)` (dropping the fixed `range(num_pages)`), keeping the global dedup `seen` set across categories.

- [ ] **Step 4: Run to verify pass (incl. existing discovery tests).**

Run: `.venv/bin/python -m pytest tests/fetcher/bg/ -v -k "discovery or probe"`
Expected: PASS, no regression.

- [ ] **Step 5: Commit.**

```bash
git add fetcher/bg/discovery.py tests/fetcher/bg/test_discovery_probe.py
git commit -m "feat(discovery): probe-to-end category crawl, no hard-coded page counts (FR-025/D5)"
```

---

## Task 4: Corpus-level coverage gate (TDD) — the durable guarantee

**Files:**
- Create: `fetcher/bg/coverage_categories.py`
- Test: `tests/fetcher/bg/test_coverage_categories.py`

**Interfaces:**
- Consumes: `docs/data/lexbg-categories.yaml` (manifest), `CATEGORY_DIRS`.
- Produces: `uncovered_categories(manifest_path, category_dirs) -> list[str]` returning slugs that are neither present/in_scope-with-a-dir nor waived. Empty list = corpus category coverage complete. Consumed by CI + Task 8 close-out.

- [ ] **Step 1: Write the failing tests.**

```python
# tests/fetcher/bg/test_coverage_categories.py
import textwrap
from fetcher.bg.coverage_categories import uncovered_categories

def _manifest(tmp_path, body):
    p = tmp_path / "lexbg-categories.yaml"
    p.write_text(textwrap.dedent(body), encoding="utf-8")
    return str(p)

def test_all_present_or_waived_is_clean(tmp_path):
    m = _manifest(tmp_path, """
    - {slug: laws, name: Закони, status: present}
    - {slug: post, name: Постановления, status: in_scope}
    - {slug: ukazi, name: Укази, status: waived, waiver_ref: WAIVERS.md#ukazi}
    """)
    dirs = {"laws": "laws", "post": "postanovleniya"}   # in_scope slug has a dir
    assert uncovered_categories(m, dirs) == []

def test_candidate_without_decision_is_flagged(tmp_path):
    m = _manifest(tmp_path, """
    - {slug: laws, name: Закони, status: present}
    - {slug: tarifi, name: Тарифи, status: candidate}
    """)
    assert uncovered_categories(m, {"laws": "laws"}) == ["tarifi"]

def test_in_scope_without_dir_is_flagged(tmp_path):
    m = _manifest(tmp_path, """
    - {slug: post, name: Постановления, status: in_scope}
    """)
    assert uncovered_categories(m, {}) == ["post"]   # in_scope but no corpus dir wired
```

- [ ] **Step 2: Run to verify fail.**

Run: `.venv/bin/python -m pytest tests/fetcher/bg/test_coverage_categories.py -v`
Expected: FAIL (module missing).

- [ ] **Step 3: Implement.**

```python
# fetcher/bg/coverage_categories.py
"""FR-025 corpus-level coverage gate: assert every enumerated lex.bg act-type
category is either represented in the corpus (present/in_scope-with-a-dir) or
explicitly waived. The set-level analogue of the D-047 per-act gate."""
import yaml

def uncovered_categories(manifest_path, category_dirs) -> list[str]:
    manifest = yaml.safe_load(open(manifest_path, encoding="utf-8")) or []
    bad = []
    for entry in manifest:
        slug, status = entry["slug"], entry.get("status")
        if status == "waived":
            continue
        if status in ("present", "in_scope"):
            if slug not in category_dirs:   # claimed in-scope but not wired to a dir
                bad.append(slug)
            continue
        bad.append(slug)                    # candidate/unclassified = not covered
    return bad
```

- [ ] **Step 4: Run to verify pass.**

Run: `.venv/bin/python -m pytest tests/fetcher/bg/test_coverage_categories.py -v`
Expected: PASS.

- [ ] **Step 5: Commit.**

```bash
git add fetcher/bg/coverage_categories.py tests/fetcher/bg/test_coverage_categories.py
git commit -m "feat(coverage): corpus-level category coverage gate (FR-025/D-049)"
```

---

## Task 5: Wire in-scope categories into config + dirs + rango (TDD, parameterized by Task 1 gate)

**Files:**
- Modify: `fetcher/bg/discovery.py` (`CATEGORIES_CONFIG`, `CATEGORY_DIRS`)
- Create: corpus dirs for each in-scope slug (e.g. `postanovleniya/` exists; create others as needed)
- Test: `tests/fetcher/bg/test_discovery_probe.py` (extend)

**Interfaces:**
- Consumes: the in-scope slug list from `docs/data/lexbg-categories.yaml` (Task 1 gate).
- Produces: `CATEGORY_DIRS` mapping each in-scope slug → its corpus dir; `CATEGORIES_CONFIG` containing each in-scope slug (page-count value is now advisory only — Task 3 probes to end — keep a sentinel like `-1` or the last-known count).

> **Parameterized:** for EACH slug the owner marked `in_scope` in Task 1, apply the pattern below. Example uses `post` → `postanovleniya` with `rango: постановление`. Repeat verbatim per in-scope slug with its slug/dir/rango.

- [ ] **Step 1: Write the failing test** (asserts the wiring for each in-scope slug; example shown for `post`).

```python
def test_in_scope_slugs_are_wired():
    from fetcher.bg.discovery import CATEGORIES_CONFIG, CATEGORY_DIRS
    import yaml
    manifest = yaml.safe_load(open("docs/data/lexbg-categories.yaml", encoding="utf-8"))
    for e in manifest:
        if e.get("status") == "in_scope":
            assert e["slug"] in CATEGORIES_CONFIG, f"{e['slug']} missing from CATEGORIES_CONFIG"
            assert e["slug"] in CATEGORY_DIRS, f"{e['slug']} missing from CATEGORY_DIRS"
```

- [ ] **Step 2: Run to verify fail.**

Run: `.venv/bin/python -m pytest tests/fetcher/bg/test_discovery_probe.py::test_in_scope_slugs_are_wired -v`
Expected: FAIL for each unwired in-scope slug.

- [ ] **Step 3: Implement the wiring** (per in-scope slug). Example:

```python
# fetcher/bg/discovery.py
CATEGORIES_CONFIG = {
    "laws": 12, "code": 1, "ords": 75, "regs": 14, "reg_laws": 2,
    "post": -1,          # -1 = probe to end (Task 3); one line per in-scope slug
}
CATEGORY_DIRS = {
    "laws": "laws", "code": "codes", "ords": "ordinances",
    "regs": "regulations", "reg_laws": "implementing",
    "post": "postanovleniya",   # one line per in-scope slug
}
```

Create the corpus dir for each new in-scope slug that lacks one: `mkdir -p <dir> && touch <dir>/.gitkeep`. Map each new `rango` (D3): decide the exact `rango` string per act-type (`постановление`, `тарифа`, `инструкция`, …) — the fetcher's metadata parser sets `rango`; confirm it emits the correct value for the new tree (verify on one fetched act in Task 7).

- [ ] **Step 4: Run to verify pass.**

Run: `.venv/bin/python -m pytest tests/fetcher/bg/test_discovery_probe.py -v`
Expected: PASS.

- [ ] **Step 5: Commit.**

```bash
git add fetcher/bg/discovery.py tests/fetcher/bg/test_discovery_probe.py <new corpus dirs>
git commit -m "feat(discovery): wire FR-025 in-scope act-type categories + dirs (D-049)"
```

---

## Task 6: Governance — COVERAGE-FLOOR rewrite + DECISIONS + FR-026 registration

**Files:**
- Modify: `docs/process/COVERAGE-FLOOR.md`
- Modify: `docs/sync/DECISIONS.md`
- Modify: `docs/frs/INDEX.md`

- [ ] **Step 1: Rewrite the COVERAGE-FLOOR category clause.** Replace the fixed "All 5 lex.bg categories" floor with: "Every act-type category enumerated in `docs/data/lexbg-categories.yaml` is either represented in the corpus (a `CATEGORY_DIRS` entry with acts) or has a dated waiver in `WAIVERS.md`. The `uncovered_categories()` gate (Task 4) enforces this; a new lex.bg category that is neither wired nor waived fails the floor." Keep the per-category count targets as informative, not as the enumeration.

- [ ] **Step 2: DECISIONS addendum to D-049.** Append the Task-1 scope decision (which slugs in_scope vs waived, with counts) and mark D-049 → Addressed once Task 8 completes. Add the corpus-level coverage gate as the standing guarantee.

- [ ] **Step 3: Register FR-026** in `docs/frs/INDEX.md` — annex/приложение-as-separate-document capture (carved out of FR-025 per D2), status Open, with the НСС standards (СС 1–42) as the motivating case.

- [ ] **Step 4: Commit.**

```bash
git add docs/process/COVERAGE-FLOOR.md docs/sync/DECISIONS.md docs/frs/INDEX.md
git commit -m "docs(governance): FR-025 coverage-floor rewrite + D-049 scope + FR-026 (annex) registered"
```

---

## Task 7: Fetch the in-scope categories (CF-hardened, coverage-gated)

**Files:**
- Corpus dirs (new act `.md` files, committed `[nova]` by the pipeline).
- Uses: `refresh.py` (existing), the D-047 bulk runbook.

**Interfaces:**
- Consumes: the in-scope slugs (now in `CATEGORIES_CONFIG`/`CATEGORY_DIRS`), the CF cookie, the per-act coverage gate.

- [ ] **Step 1: Mint a `cf_clearance` cookie** via Playwright MCP (runbook `docs/runbook/2026-07-01-cf-cookie-mint.md`); write to `$SCRATCH/cf_cookie.json`; verify with a one-act fetch.

- [ ] **Step 2: Launch the staged fetch** for the in-scope slugs only, in the background (long-running), same discipline as the D-047 bulk:

Run: `.venv/bin/python refresh.py --categories "<in_scope slugs>" --cookie-file "$SCRATCH/cf_cookie.json" --cookie-wait 900 --state "$SCRATCH/fr025-state.json" > "$SCRATCH/fr025.log" 2>&1` (background)
Expected: new acts committed `[nova]` (author-date = legislative date, D-048); per-act coverage gate active.

- [ ] **Step 3: Babysit the cookie loop + monitor** (Monitor on the log for `CLOUDFLARE challenge`/`Traceback`/`FAILED`; re-mint on each pause; recover any `error`-state acts via the state-clear re-run as in D-047). Consider a `/loop` for pacing.

- [ ] **Step 4: HALT-and-triage every `gate-report.json` entry via vision** (as in D-047: genuine dropped class → fix `text_parser`, re-run; content-less stub → accept). Confirm one fetched act per new category has the correct `rango` (Task 5 D3).

- [ ] **Step 5: Commit** is done per-act by the pipeline; verify `git log` shows the `[nova]` acts and the working tree is clean.

---

## Task 8: Rebuild catalog + verify + close-out

**Files:**
- Modify: `docs/sync/ACTIVE.md`, `docs/sync/DECISIONS.md`, `docs/frs/INDEX.md`, memory.
- Optionally modify: `docs/sync/CORPUS-STATUS.json`.

- [ ] **Step 1: Rebuild + verify.**

Run: `.venv/bin/python -m index.build` then `.venv/bin/python scripts/verify_catalog.py`
Expected: new acts indexed; per-category counts include the new categories.

- [ ] **Step 2: Assert the corpus-level gate is clean.**

Run: `.venv/bin/python -c "from fetcher.bg.coverage_categories import uncovered_categories; from fetcher.bg.discovery import CATEGORY_DIRS; print(uncovered_categories('docs/data/lexbg-categories.yaml', CATEGORY_DIRS))"`
Expected: `[]` (every enumerated category present-or-waived).

- [ ] **Step 3: Full suite.**

Run: `.venv/bin/python -m pytest -q`
Expected: green (the 2 FTS perf-budget tests are load-flaky, non-regression).

- [ ] **Step 4: Close-out docs + memory.** ACTIVE.md → FR-025 done, next focus = FR-026 or the national-functionality track; DECISIONS D-049 → Addressed; FR-025 → Closed; update auto-memory `project_legalize_bg.md` + `MEMORY.md`. Optionally add per-category coverage to `docs/sync/CORPUS-STATUS.json`.

- [ ] **Step 5: Commit.**

```bash
git add docs/sync/ACTIVE.md docs/sync/DECISIONS.md docs/frs/INDEX.md docs/sync/CORPUS-STATUS.json
git commit -m "docs(sync): FR-025 closed — act-type category coverage complete + corpus-level gate (D-049)"
```

---

## Self-Review

- **Spec coverage:** design §5 Phase 1 → Task 1; Phase 2 → Task 2 (+ Task 6 governance); Phase 3 → Tasks 3 & 5; Phase 4 → Task 4; Phase 5 → Task 7; Phase 6 → Task 8. D1 (discover-first) → Task 1 gate; D2 (annex→FR-026) → Task 6 Step 3; D3 (rango) → Task 5 Step 3; D4 (non-article) → no special code (verified Task 7 Step 4); D5 (probe-to-end) → Task 3. COVERAGE-FLOOR rewrite → Task 6 Step 1.
- **Placeholder scan:** the only deliberately-parameterized content is the in-scope slug set (unknowable until Task 1's owner gate); every mechanism task has complete code. No TBD/TODO in code steps.
- **Type consistency:** `crawl_category(transport, slug)` (Task 3) used consistently; `uncovered_categories(manifest_path, category_dirs)` (Task 4) used identically in Task 8 Step 2; manifest schema (`slug`/`name`/`status`/`*_count`/`waiver_ref`) consistent across Tasks 1, 4, 5.
- **Ordering:** preflight (Task 2) precedes protected-surface code (Tasks 3, 5); the owner scope gate (Task 1 Step 5) precedes wiring (Task 5) and fetch (Task 7).
- **Open dependency:** Task 7 overlaps FR-024 (re-source) — sequence after the FR-024 source decision, or explicitly accept lex.bg-as-source for this pass (noted in design §6 R4).
