# FR-034 corpus sweep — quantification report (runs 1 and 2)

**Date:** 2026-08-03
**Branch:** `fix/fr034-unnumbered-alineas`
**Scope:** full-corpus re-fetch and re-parse of all 3,598 discovered lex.bg acts through the
FR-034 parser, in two runs, plus catalog rebuild and verification.

FR-034 restores paragraph structure that the pre-FR-034 parser flattened: unnumbered алинеи
(and, in older acts, numbered ones) were collapsed onto a single line with the article anchor,
so a whole article read as one undifferentiated block and the index could not address its
алинеи. The remediation is described in
`docs/plans/2026-08-02-fr034-unnumbered-alinea-remediation.md`; the loss analysis is in
`docs/research/2026-07-31-unnumbered-alinea-structure-loss.md`.

---

## 1. Why there were two runs

Run 1 executed the fixed parser across the corpus and produced 617 per-act commits, but it
**silently skipped an entire class of acts**. `refresh.py`'s change classifier normalised the
candidate and committed texts by collapsing *all* whitespace before comparing them. A rewrite
whose only effect was to introduce paragraph breaks therefore compared equal, was classified
`unchanged`, and was never written to disk. ЗЗД, ЗН and ЗС — the canonical acts the whole
remediation was aimed at — fell into exactly that class: they were fetched, re-parsed correctly,
and then thrown away.

This is the third instance of the same blind spot: a check that normalises away the very property
under test. It surfaced as a failed verification (R3: ЗЗД чл. 36 had no алинея rows at all) rather
than as an error, because nothing in the pipeline was wrong except the comparison.

Commit `8c6cfd05` made `normalize_for_compare` structure-aware: horizontal whitespace and soft line
wraps are still cosmetic, but a paragraph boundary (`\n\n`) is preserved and canonicalised, so a
structure-only rewrite now falls through to `popravka`. Run 2 re-fetched the whole corpus on top of
that fix: acts already restructured in run 1 byte-match and classify `unchanged`; the skipped class
lands as `[popravka]` commits.

---

## 2. Run 1 (parser sweep)

| metric | value |
|---|---|
| acts processed | 3,598 |
| commits | **617** — `[popravka]` 496 · `[reforma]` 99 · `[nova]` 22 · `[otmyana]` 0 |
| fetch errors | 0 |
| Cloudflare challenge | none — every request returned `200` at the 1 req/s ceiling |
| gate-fail (writes skipped) | 8 — 7 titulo-precondition content-less stubs + 1 coverage gate (doc_id `2137262832`, `uncovered_chars=1430`), per D-047 precedent |
| `STALE` categories | `{}` — no IMPLEMENTATION-PREFLIGHT trigger |
| structure census | 51 acts with `structure mismatch (report-only)`, **0** `structure check skipped` |
| catalog after rebuild | 3,624 acts |
| implicit алинея rows | 207 laws / 18,488 rows |

Run 1 was interrupted once at 2,448/3,598 by the harness (not a crash) and resumed from its
checkpoint with `tee -a`, preserving the log-derived census.

Its verification gate came back red on six lines: four R1/R2 per-law aggregate drops and two R3
lines showing ЗЗД чл. 36 unfixed. The R3 pair is what exposed the classifier defect above.

---

## 3. Run 2 (classifier-fix sweep)

Base HEAD `8c6cfd05`; final HEAD **`7909845c`**.

| metric | value |
|---|---|
| acts processed | 3,598 |
| dispositions (cumulative checkpoint) | `popravka` **2,923** · `unchanged` 667 · `gate-fail` 8 |
| commits | **2,923** — `[popravka]` 2,923 · `[reforma]` 0 · `[nova]` 0 · `[otmyana]` 0 · untyped 0 |
| fetch errors | **0** |
| Cloudflare challenge | none — zero `cloudflare`/`challenge`/`403` matches in the log |
| gate-fail (writes skipped) | 8 — the same 7 titulo stubs + the same coverage-gate act as run 1 |
| `STALE` categories | `{}` |
| structure census | **51** mismatches (51 distinct doc_ids), **0** skips — identical to run 1 |
| tests | `pytest -m "not perf" -q` → **669 passed**, 8 deselected |
| catalog after rebuild | 3,624 acts · 481,424 provision rows |
| implicit алинея rows | **318 laws / 23,747 rows** (run 1: 207 / 18,488) |

Zero `[reforma]` and zero `[nova]` is the expected shape: run 1 had already absorbed every genuine
upstream content change, so run 2 sees only structure drift, which classifies `popravka` by
construction.

### 3.1 Why 2,923 commits is not alarming

2,923 is far above the "dozens to low hundreds" that the skipped-class estimate suggested, so the
count was checked rather than assumed. The arithmetic is self-consistent: 3,598 − 667 unchanged
− 8 gate-fail = 2,923, and the 667 unchanged acts are essentially the 617 that run 1 had already
rewritten. In other words, **almost every act not rewritten in run 1 differed only in paragraph
structure**, which is precisely what the structure-blind classifier was hiding.

The content-safety claim was then verified exhaustively rather than by sampling. For **all 2,923
commits** (2,923 files), the pre-commit and post-commit markdown were compared after
whitespace normalisation:

```
commits to check: 2923
files checked: 2923
commits whose text changed beyond whitespace/paragraphing: 0
```

Three randomly chosen commits (seeded sample) illustrate the shape — text identical, blank-line
count up:

| commit | act | normalised text identical | chars | blank lines |
|---|---|---|---|---|
| `f40a1f1b` | Правилник за легализациите, заверките и преводите | yes | 16,118 → 16,137 | 50 → 69 |
| `7e5a2576` | Наредба за специфичните изисквания за хранително банкиране | yes | 16,968 → 17,024 | 39 → 95 |
| `b5af28d7` | Наредба № 83 от 3 декември 2025 г. | yes | 80,455 → 80,763 | 608 → 1,181 |

A representative diff (`88551f55`, Наредба за трудоустрояване), abridged:

```
-**Чл. 1.** (1) … НЕЛК). (2) … ЛКК - до 6 месеца. … (3) … (4) … (5) … (6) …
+**Чл. 1.** (1) … НЕЛК).
+
+(2) … ЛКК - до 6 месеца. …
+
+(3) …
```

Word for word the same text; each алинея simply now occupies its own paragraph.

### 3.2 Canonical acts

| act | slug | implicit rows (run 1 → run 2) | explicit алинеи vs baseline |
|---|---|---|---|
| ЗЗД | `zakon-za-zadalzheniyata-i-dogovorite` | 10 → **461** | 0 → 0 |
| ЗН | `zakon-za-nasledstvoto` | 0 → **0** | 112 → 112 |
| ЗС | `zakon-za-sobstvenostta` | 2 → **103** | 0 → 0 |
| ЗЛС | `zakon-za-litsata-i-semeystvoto` | 44 → **44** | 0 → 0 |

ЗЗД clears the ≈400-row expectation derived from its 184 multi-division articles, and its чл. 36 —
the R3 probe — now carries both алинеи as addressable implicit rows:

```
(None, 0, '**Чл. 36.** Едно лице може да представлява друго по раз')
('1', 1, 'Едно лице може да представлява друго по разпоредба на з')
('2', 1, 'Последиците от правните действия, които представителят ')
```

**ЗН stays at zero implicit rows, and that is correct rather than a miss.** ЗН *was* restructured in
run 2 (commit `f21c2e4f`) — its articles are no longer flattened — but its алинеи carry explicit
`(1)`, `(2)`, `(3)` anchors, so they index as explicit rows, and the old parser had already been
counting those inline anchors (112 before, 112 after). For ЗН the FR-034 gain is document structure,
not new index rows. The research note's "49 of 97 articles flattened" figure measured flattening,
not implicit-алинея yield; the two should not be conflated.

Top 10 acts by implicit rows:

| law_id | implicit rows |
|---|---|
| `zakonza-darzhavniya-byudzhet-na-republika-balgariya-za-2026-g` | 4,668 |
| `zakon-za-darzhavniya-byudzhet-na-republika-balgariya-za-2025-g` | 4,634 |
| `naredba-5-ot-3-septemvri-2018-g-za-prilagane-na-pravilata-na-biologichno-proizvo` | 2,262 |
| `naredba-3-ot-9-yuni-2004-g-za-ustroystvoto-na-elektricheskite-uredbi-i-elektropr` | 1,311 |
| `naredba-iz-1971-ot-29-oktomvri-2009-g-za-stroitelno-tehnicheski-pravila-i-normi-` | 841 |
| `naredba-10-ot-27-septemvri-2011-g-za-usloviyata-i-reda-za-predostavyane-na-bezva` | 789 |
| `naredba-1-ot-27-may-2010-g-za-proektirane-izgrazhdane-i-poddarzhane-na-elektrich` | 500 |
| `zakon-za-zadalzheniyata-i-dogovorite` | 461 |
| `naredba-za-darzhavnite-iziskvaniya-za-pridobivane-na-visshe-obrazovanie-na-obraz-5` | 402 |
| `naredba-rd-02-20-2-ot-21-dekemvri-2015-g-za-tehnicheski-pravila-i-normi-za-proek` | 352 |

The two budget acts at the top are heavily tabular; their implicit counts largely reflect table and
annex rows rather than the doctrinal unnumbered-алинея case FR-034 targets.

---

## 4. Verification (`scripts/fr034_verify.py check`)

Verbatim, exit code 1:

```
FR-034 VERIFY FAIL:
 - R2 naredba-5-ot-10-may-1999-g-za-strukturata-na-zapisa-v-tsifrov-vid-na-kadastralni: articles 44 -> 43
 - R1 naredba-69-ot-15-yuni-2021-g-za-tehnicheskite-lihveni-protsenti-po-chl-169-al-1-: explicit alineas 9 -> 6
 - R1 naredba-na-velikotarnovskiya-obshtinski-savet-za-upravlenie-stopanisvane-i-polzv-2: explicit alineas 47 -> 45
 - R1 zakon-za-fiskalen-savet-i-avtomatichni-korektivni-mehanizmi: explicit alineas 36 -> 34
 - R1 zakon-za-zhelezopatniya-transport: explicit alineas 425 -> 424
```

**R3, R4 and R5 are clean.** The two R3 lines that made run 1's gate red — ЗЗД чл. 36 having no
алинея rows and no preserved whole-article structure — are gone. That was the objective of the
classifier fix and it is met.

`.fr034-baseline.json` was not regenerated at any point (417,566 bytes, unchanged); only `check`
was ever run.

### 4.1 The four known residuals — pending Task-6c adjudication

Carried over from run 1 and not re-litigated here:

| act | line | run-1 commit type | note |
|---|---|---|---|
| `naredba-69-ot-15-yuni-2021-…` | R1 9 → 6 | `[reforma]` | title itself amended („ЗАГЛ. ИЗМ. - ДВ, БР. 61 ОТ 2026 Г.“) |
| `zakon-za-fiskalen-savet-…` | R1 36 → 34 | `[reforma]` | upstream text changed |
| `zakon-za-zhelezopatniya-transport` | R1 425 → 424 | `[popravka]` | needs adjudication |
| `naredba-5-ot-10-may-1999-…` | R2 44 → 43 | `[popravka]` | needs adjudication |

The baseline was captured pre-sweep, so a genuine upstream repeal of an алинея during the sweep
necessarily trips R1/R2. The two `[reforma]` rows are therefore plausible gate false positives; the
two `[popravka]` rows are the ones that actually need a ruling.

### 4.2 NEW in run 2 — one additional R1 failure, with a diagnosed mechanism

`naredba-na-velikotarnovskiya-obshtinski-savet-za-upravlenie-stopanisvane-i-polzv-2`
(commit `d4f94a48`, `[popravka]`) drops from 47 to 45 explicit алинеи. Diagnosis only; no fix was
attempted.

The act's markdown text is complete and unchanged — the loss happens at **index** time. Чл. 6 ал. 5
contains an inline bullet list. Before run 2 those bullets sat on the same line as ал. 5; the
structure split moved each onto its own paragraph:

```
(5) (Нова - Решение № 1086 …) Земите от общинския поземлен фонд могат да се отдават … без търг:

* когато са заети с трайни насаждения;

* когато не са били използвани две или повече стопански години;
…
(6) (Нова - Решение № 1086 …) Общинският съвет по предложение на Кмета …
(7) (Предишна ал. 4 …) В договорите за наем се предвижда …
```

The article-continuation rule treats a paragraph starting with `*` as a closer (it was written for
PreHistory italics blocks). The bullets therefore terminate чл. 6, and ал. 6 and ал. 7 fall outside
the article and never reach `provisions`.

Corpus-wide scope of the pattern — an алинея paragraph stranded after a mid-article bullet:

```
acts affected: 9
stranded алинея paragraphs: 40
```

| act | stranded | baseline expl. | now | delta |
|---|---|---|---|---|
| `naredba-rd-02-20-2-ot-27-yanuari-2012-…` | 13 | 192 | 225 | +33 |
| `naredba-3-ot-9-yuni-2004-…` | 7 | 2,885 | 2,925 | +40 |
| `naredba-23-ot-27-avgust-2020-…` | 6 | 14 | 15 | +1 |
| `naredba-14-ot-15-oktomvri-2012-…` | 5 | 1,702 | 1,861 | +159 |
| `naredba-rd-02-20-3-ot-21-dekemvri-2015-…` | 3 | 602 | 624 | +22 |
| `naredba-za-reda-za-opredelyane-na-tseni-na-zemedelskite-zemi-…` | 2 | 13 | 15 | +2 |
| `naredba-na-velikotarnovskiya-obshtinski-savet-…-2` | 2 | 47 | **45** | **−2** |
| `pravilnik-po-bezopasnostta-na-truda-pri-vzrivnite-raboti` | 1 | 643 | 648 | +5 |
| `naredba-rd-02-20-3-ot-9-noemvri-2022-…` | 1 | 100 | 115 | +15 |

Only one of the nine trips R1, because in the other eight the FR-034 recoveries elsewhere in the
act outweigh the stranded rows. Which is the concrete form of the next caveat.

### 4.3 Caveat — per-law aggregates mask offsetting per-article changes (Task-5 reviewer, M2)

R1 and R2 compare **per-law totals** against the baseline. A law that loses алинеи in one article
and gains more in another passes the gate with a net-positive delta while still carrying a real
regression. §4.2 is that caveat made concrete: 8 of the 9 acts with stranded алинеи pass R1
outright, and the corpus-wide truth (40 stranded paragraphs) is invisible to the gate. Reading
"R1/R2 clean" as "no per-article loss anywhere" is not warranted; a per-article baseline would be
needed for that claim.

---

## 5. Parked: ППЗ чл. 102б English annex remnant (FR-026 scope)

`pravilnik-za-prilagane-na-zakona-za-aktsizite-i-danachnite-skladove` чл. 102б once absorbed 86,503
chars of appendix material; the annex closer added in Task 1+2 cut that to a **6,429-char**
whole-article row. That remnant is an **English-language translation** of the annex
("Article 102a. (1) The technical devices…") that sits between the article text and the
`Приложение № 28` marker, so no closer fires.

Run 2's structure split changes the remnant's *shape* without changing its size: the article now
also emits **8 English-language алинея rows totalling ~4,320 chars**, whose paragraph numbers
collide with the two genuine Bulgarian алинеи (`1` and `2` each occur three times across the
article's 11 rows). `idx_provisions_lookup` is non-UNIQUE, so this does not break the rebuild, but
`get_article` on this article returns Bulgarian and English rows under the same numbers.

Classification of annex content remains **FR-026 reserved scope**; no action taken here.

---

## 6. Artefacts and state

- Sweep logs: `refresh-fr034.log` (run 1), `refresh-fr034-run2.log` (run 2) — untracked, **not
  gitignored**, must not be committed; they are the sole source of the structure census, which
  `gate-report.json` cannot provide because it records failures only.
- Rebuild logs: `rebuild-fr034.log`, `rebuild-fr034-run2.log` — same handling.
- Checkpoint backups, in `.superpowers/sdd/2026-08-02-fr034-unnumbered-alinea-remediation/`:
  - `refresh-state.pre-fr034.json` — pre-run-1 checkpoint (2026-06-21, D-047 era), 96,475 bytes
  - `refresh-state.run1-fr034.json` — post-run-1 checkpoint, 96,263 bytes
  Each run required clearing `.refresh-state.json` first; leaving it in place makes the sweep a
  silent no-op, since `refresh.py` skips every checkpointed act in all three partitions.
- `catalog.db` is untracked and was rebuilt from HEAD `7909845c`.
- Corpus `.md` files were written exclusively by `refresh.py`; none were hand-edited or amended.

### Operational note

Both runs were killed by the harness at roughly the 60-minute mark and resumed from checkpoint with
`tee -a`. Plain `tee` on resume would truncate the log and destroy the census evidence for the
already-processed acts. Run 2 also hit a single 16-minute socket stall on one tree page, which the
client's retry recovered on the first attempt (`RemoteDisconnected`, then `200`); it was not a
Cloudflare event.

---

## 7. Open items

1. Task 6c: adjudicate the four known R1/R2 residuals (§4.1).
2. **New:** rule on the mid-article bullet closer (§4.2) — 9 acts, 40 stranded алинея paragraphs,
   text present in markdown but absent from the index.
3. Consider a per-article baseline, or a per-article delta report, so R1/R2 stop masking offsetting
   changes (§4.3).
4. FR-026: classify annex content, including the ППЗ чл. 102б English remnant and its colliding
   алинея numbering (§5).
