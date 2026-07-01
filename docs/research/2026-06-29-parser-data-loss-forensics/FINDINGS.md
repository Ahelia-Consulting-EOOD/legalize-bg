# Forensic findings: corpus-wide structural data loss in the lex.bg parser

**Date:** 2026-06-29
**Trigger:** external FINDING `FINDING-zuo-consolidation-incomplete.md` (a DRS session consuming the corpus) reported ЗУО missing its Допълнителни разпоредби.
**Scope of this log:** all 3,599 bootstrapped acts (5 category dirs) + 7 source HTML captures (закон/кодекс/правилник/наредба). Read-only; no parser or corpus files were modified.
**Artifacts:** `forensics.py` (harness, in session scratchpad), `forensics.json` (machine-readable, this dir).

---

## 1. Verdict

The external finding is **confirmed and materially understated**. The defect is not specific to ЗУО or to definitions. It is a single deterministic parser fault that strips **every §-numbered subdivision** (Допълнителни разпоредби *and* the bodies of Преходни/Заключителни разпоредби) from **100% of the corpus**, across all act types. Article bodies (Чл.) survive; legal definitions and transitional/final provisions do not.

## 2. Root cause (precise)

`fetcher/bg/text_parser.py:7-16,26` — `CLASS_MAP` is a **CSS-class allowlist** and `convert()` does `soup.find_all(class_=list(CLASS_MAP.keys()))`. Any element whose class is not a key is never visited and is silently discarded. The allowlist omits three content-bearing subdivision classes that lex.bg emits:

| lex.bg class | Subdivision it carries | In `CLASS_MAP`? | Verdict |
|---|---|---|---|
| `Article` | Чл. N article bodies | yes | kept |
| `TransitionalFinalEdicts` | "Преходни и Заключителни разпоредби" heading | yes | kept (heading only) |
| `TitleDocument` / `Part` / `Heading` / `Section` | title + Глава/Раздел headings | yes | kept |
| **`AdditionalEdicts`** | **"Допълнителни разпоредби" heading** | **no** | **dropped** |
| **`FinalEdictsArticle`** | **§ bodies — §1 definitions AND all ПЗР §§** | **no** | **dropped** |
| **`FinalEdicts`** | **"Заключителни разпоредби (КЪМ …)" heading** | **no** | **dropped** |
| `Title` (inner `<p>`) | heading text inside the above | no | captured via mapped parent (no loss) |
| `OfInsidetitle` | minor sub-title (2 occurrences total) | no | inspect during fix |
| `HistoryOfDocument` / `HistoryItem` / `HistoryReference` | amendment-history chrome | partial | intentionally excluded (OK) |

The bug is original and unpatched: parser history is two commits (`0ffe7a09` introduced the incomplete map; `f9ccb7db` fixed alinea spacing). `tests/fetcher/bg/test_text_parser.py:58` asserts `TransitionalFinalEdicts` only — there is **no test for the three dropped classes**, so the suite encoded the same blind spot and stayed green.

## 3. Layer 1 — complete dropped-class inventory (source census)

Per-act count of the three dropped subdivision classes (BeautifulSoup census over the source HTML; all windows-1251):

| Act | Type | `AdditionalEdicts` | `FinalEdicts` | `FinalEdictsArticle` | `FinalEdictsArticle` chars dropped |
|---|---|---:|---:|---:|---:|
| ЗУО — Закон за управление на отпадъците | закон | 1 | 5 | 71 | 64,332 |
| ЗЕУ — Закон за електронното управление | закон | 4 | – | 42 | 32,138 |
| ГПК — Граждански процесуален кодекс | кодекс | 1 | – | 121 | 70,591 |
| ЗОП — Закон за обществените поръчки | закон | 1 | – | 84 | 69,552 |
| ППЗ Акцизи | правилник | 2 | – | 56 | 18,325 |
| Правилник съдилища | правилник | 1 | – | 8 | 1,422 |
| Наредба № 4-14 | наредба | 1 | – | 3 | 909 |

Cross-act union of dropped content-bearing classes: `FinalEdictsArticle` 385 elements / 257,269 chars; `FinalEdicts` 31 elements / 3,334 chars; `AdditionalEdicts` 11 elements / 781 chars. **Every act type is affected.**

> Note: `FinalEdicts` (the standalone "Заключителни разпоредби КЪМ …" heading) is the explanation for the original finding's F2 ("2 КЪМ blocks missing": ЗДДФЛ, ЗУЧК). Those amendment blocks were tagged `FinalEdicts`, not `TransitionalFinalEdicts`, so they were dropped. F2 is the **same root cause**, not a separate bug.

## 4. Layer 2 — oracle diff: current parser vs in-memory fixed map (recoverability proof)

The harness ran the REAL parser, then re-ran it with the 3 classes added to `CLASS_MAP` **in memory only** (no file edit), per source:

| Act | current chars | fixed chars | recovered | definitions (cur→fix) | § provisions captured (cur→fix) |
|---|---:|---:|---:|:--:|:--:|
| ЗУО | 306,457 | 371,540 | **+65,083** | F→T | 0→48 |
| ЗЕУ | 105,139 | 137,972 | **+32,833** | F→T | 0→23 |
| ГПК | 456,213 | 527,791 | **+71,578** | F→T | 0→86 |
| ЗОП | 559,209 | 629,573 | **+70,364** | F→T | 0→59 |
| ППЗ Акцизи | 973,384 | 993,453 | **+20,069** | F→F¹ | 0→30 |
| Правилник съдилища | 140,181 | 141,647 | +1,466 | F→T | 0→7 |
| Наредба № 4-14 | 36,459 | 37,430 | +971 | F→T | 0→3 |

¹ ППЗ Акцизи recovers 30 § provisions but the literal phrase "По смисъла" is absent in its ДР (a правилник may define terms differently); content IS recovered, only the heuristic flag is F.

Key facts: the current parser captures **0 §-provisions in every act**; the fix restores the full § range (ЗУО up to §156) and brings back definitions. Recovered chars ≈ dropped chars (no double-counting from nesting), so the fix is clean.

## 5. Layer 3 — corpus-wide structural audit (all 3,599 acts)

> **CORRECTION (full corpus):** the bootstrapped corpus is **3,599 acts across all 5 category dirs** (`laws` 396, `codes` 24, `ordinances` 2627, `regulations` 492, `implementing` 60) — the full national bootstrap already shipped to `main`, and `catalog.db` holds 3,599 laws / 3,851 versions. An earlier pass that scanned only `laws/` (396) undercounted; there is **no "caught before full bootstrap" reprieve.** Numbers below are the true corpus-wide figures.

| Metric | Count (of 3,599) | Share |
|---|---:|---:|
| With base **Допълнителни разпоредби** heading | **7** | **0.19%** |
| With §-definitions phrase ("По смисъла") | 29 | 0.81% (cross-refs in article bodies, not ДР) |
| With any "Преходни и Заключителни разпоредби" heading | 2,145 | 59.6% |
| **With ANY real § provision body** | **5** | **0.14%** |
| With heading-concatenation artifacts | 1,079 | 29.98% |
| By dir (total / has-ДР / has-defs / has-real-§) | laws 396/0/19/1 · codes 24/1/3/0 · ordinances 2627/5/5/2 · regulations 492/1/2/1 · implementing 60/0/0/1 | — |

Interpretation: a heading as frequent as Допълнителни разпоредби appearing in **7 of 3,599** files is impossible naturally — it is a deterministic ~100% drop across every category. The article corpus is largely intact; the §-provision corpus (definitions + transitionals) is ~99.9% destroyed.

## 6. Secondary defect — heading concatenation (separate from the allowlist)

`get_text(strip=True)` flattens a heading div and its sibling КЪМ act-name into one string with no separator, e.g. `## Преходни и Заключителни разпоредбиКЪМ ЗАКОНА ЗА ИЗМЕНЕНИЕ…`, and occasionally merges two headings (`…КОДЕКСПреходни и Заключителни разпоредби`). Present in 77.8% of acts. This is a formatting fault in heading handling, independent of the dropped-class fault, and must be fixed in the same parser pass.

## 7. Downstream contamination

Everything built on these `.md` files inherits the loss: `catalog.db`, FR-018 `get_articles`, FR-019 Cyrillic search, FR-020 time-machine (`law_versions` reconstructed from git log of the corrupted files). The corpus is not legally usable until re-sourced and re-validated.

## 8. Reproduction

```bash
cd /Users/ekimir/swprj/legalize-bg
.venv/bin/python docs/research/2026-06-29-parser-data-loss-forensics/forensics.py
# corpus quick check (all 5 category dirs):
grep -rlF "Допълнителни разпоредби" laws codes ordinances regulations implementing --include='*.md' | wc -l   # → 7 of 3,599
```

## 9. Remediation requirements (feeds the Phase-3 plan; steps 1-5)

R1. Add `AdditionalEdicts`, `FinalEdicts`, `FinalEdictsArticle` to `CLASS_MAP` (FEA needs Article-style `<br>`/alinea handling, not crude get_text). Inspect `OfInsidetitle`.
R2. Fix heading concatenation (insert separator between subdivision label and КЪМ name; prevent double-heading merge).
R3. Harden against the defect *class*: invert the parser to **keep-by-default** (denylist of chrome) so unknown classes surface as visible text, not silent loss; see `COMPLETENESS.md`.
R4. Add TDD tests for all three classes + a **class-agnostic coverage gate** (assert ~0 uncovered legal text per act; the structural oracle that would have caught this) run over 100% of acts.
R5. Re-bootstrap the **full 3,599-act corpus** (all 5 category dirs) with the fixed parser; validate every act against the coverage gate + lex.bg oracle; rebuild `catalog.db`. **Obstacle:** live lex.bg now returns a **Cloudflare 403 challenge** — re-sourcing must solve CF or pull from authoritative primary sources (ДВ/official per D-038/FR-024). Model the re-bootstrap as an FR-020 corrective baseline (D-047/D4).

## 10. Status

Phase 1 (evidence) complete. Next: Phase 2 evaluation, Phase 3 written remediation plan (touches the `fetcher/bg/` protected surface → requires IMPLEMENTATION-PREFLIGHT), then Phase 4 execution after approval.
