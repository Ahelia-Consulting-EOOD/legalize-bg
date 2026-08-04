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

1. Task 6c: adjudicate the four known R1/R2 residuals (§4.1). — **DONE, §8.**
2. **New:** rule on the mid-article bullet closer (§4.2) — 9 acts, 40 stranded алинея paragraphs,
   text present in markdown but absent from the index. — **DONE**, fixed in `f0d414c3` (anomaly B2).
3. Consider a per-article baseline, or a per-article delta report, so R1/R2 stop masking offsetting
   changes (§4.3).
4. FR-026: classify annex content, including the ППЗ чл. 102б English remnant and its colliding
   алинея numbering (§5). — **now the dominant open item**, see §10.

---

# 8. Task 6c-b — residual adjudications, implicit-row sampling, structure-mismatch census

**Date:** 2026-08-04 · **HEAD at time of writing:** `f0d414c3` · investigation only, no code change.
`.fr034-baseline.json` untouched (417,566 bytes, mtime 2026-08-03 16:19); `baseline` never run;
`refresh.py` never run; all catalog access read-only.

Headline: **all four verify-red lines are baseline artifacts, none is FR-034 damage** — but the
implicit-row population is **84 % artifacts** in a stratified sample (74.8–93.3 % across three
independent sampling frames, §9.1b), which is far over the 10 %
threshold the plan set, and routes to a fix round before governance (§9.4, §10).

## 8.1 R1 — the two `[reforma]` acts: CONFIRMED lawful amendments

Both are baseline-vs-amendment false positives. `scripts/fr034_verify.py` needs no change; a
post-merge baseline refresh resolves them.

**`naredba-69-ot-15-yuni-2021-…` — commit `6f39175a`, `Source-Date: 2026-07-03`, R1 9 → 6.**
Confirmed lawful amendment, evidence: the sweep commit carries the ДВ бр. 61 от 2026 г. recast — the
title is amended („ЗАГЛ. ИЗМ. - ДВ, БР. 61 ОТ 2026 Г., В СИЛА ОТ 01.01.2027 Г.“), `amendment_history`
gains `dv: 61/2026 / 2026-07-03`, and **чл. 2 is wholly repealed**
(„**Чл. 2.** (Отм - ДВ, бр. 61 от 2026 г., в сила от 01.01.2027 г.)“), taking its four explicit
алинеи with it. A marker census of the parent blob gives exactly the baseline 9:

```
$ git show 6f39175a^:ordinances/naredba-69-ot-15-yuni-2021-…-po-chl-169-al-1-.md \
    | grep -o '([0-9]\+)' | sort | uniq -c
   2 (1)
   2 (2)
   2 (3)
   2 (4)
   1 (5)
```

— чл. 2 ал. 1–4 plus чл. 3 ал. 1–5. The post-sweep catalog holds 6, all under чл. 3;
чл. 3 ал. 4 and ал. 5 survive as „(Отм. …)“ markers.
Side observation, upstream shape not FR-034: lex.bg renders чл. 3 with a **doubled marker** —
„**Чл. 3.** (1) (Изм - ДВ, бр. 61 …) (1) Пожизнените пенсии …“ — so чл. 3 carries two rows with
`paragraph='1'`, one of them the amendment note alone.

**`zakon-za-fiskalen-savet-i-avtomatichni-korektivni-mehanizmi` — commit `455b175f`,
`Source-Date: 2026-07-31`, R1 36 → 34.** Confirmed lawful amendment, evidence: re-parsing the
commit's parent and child blobs with the *current* parser isolates the loss to exactly two rows,
`(чл. 16, ал. 1)` and `(чл. 16, ал. 2)`, with no other provision changed. чл. 16 pre-sweep was
„(Изм. - ДВ, бр. 15 от 2018 г. …) (1) … (2) …“; post-sweep it reads
„(Изм. - ДВ, бр. 15 от 2018 г. …, **изм. - ДВ, бр. 69 от 2026 г., в сила от 31.07.2026 г.**)
Председателят и членовете на Съвета получават месечно възнаграждение, което е не повече от
основното месечно възнаграждение на народен представител.“ — a two-алинея article collapsed into
one unnumbered sentence by ДВ бр. 69/2026, matching the commit trailer and `amendment_history`.

## 8.2 R1/R2 — the two `[popravka]` acts

**`zakon-za-zhelezopatniya-transport` — commit `a661d011`, R1 425 → 424: genuine lex.bg source
change, NOT a parser artifact.** Evidence: a **word-level, whitespace-normalised** diff of the
entire act (40,335 → 40,334 words — line wraps normalised away before comparison, per the
false-refutation trap) yields **exactly one** changed span, at чл. 142:

```
PRE : … в сила от 21.06.2011 г.) (1) (Изм. - ДВ, бр. 11 от 2021 г., отм. - ДВ, бр. 32 от 2026 г. …
POST: … в сила от 21.06.2011 г.,      изм. - ДВ, бр. 11 от 2021 г., отм. - ДВ, бр. 32 от 2026 г. …
```

чл. 142 had already been **repealed** by ДВ бр. 32 от 2026 г., в сила от 16.04.2026 (present in the
act's `amendment_history`). lex.bg tidied its own rendering of the repealed article: it dropped the
vestigial `(1)` shell and merged the amendment notes into one parenthetical, lowercasing „Изм.“ to
„изм.“. The parser cannot produce that edit — `fetcher/bg/text_parser.py` contains **zero**
occurrences of „Изм/изм/отм/Нов“; it never rewrites amendment notes, never changes case and never
deletes text, and the FR-034 change only *adds* paragraph breaks. `[popravka]` is the correct
classification: an editorial corrigendum at source with no new ДВ issue.

**`naredba-5-ot-10-may-1999-…kadastralni` — commit `5b0ae522`, R2 44 → 43: a phantom article
disappeared; no legal text was lost.** Evidence: parsing both blobs with the current parser gives an
**identical set of 43 distinct article numbers**; the pre-sweep side carries a **duplicate**
whole-article row for чл. 42, the post-sweep side does not. The duplicate is manufactured from
**lex.bg site chrome**: this act's markdown ends with the site's „Новини“ / „Форум“ sidebar, and the
pre-sweep capture's sidebar contained the forum thread title
„Чл. 42 и прилагането на чл. 24 от ЗУТ за Допълващо застрояване - Гараж“, which `_ARTICLE_RE` reads
as an article anchor (it also produced 11 implicit rows). On the sweep date the sidebar listed
different threads, so the phantom vanished and R2 fired. **The baseline, not the sweep, is the
contaminated side.**

That leaves a genuine, separately-routed defect (pre-existing, *not* FR-034): chrome leaks into the
body of this one act. At HEAD, `Посети форума` matches **1** corpus file — this one, from line 12003
to EOF — and `© Lex.bg` matches none. Because news and forum headlines change daily, the act churns
on every refresh and any „Чл. N“ appearing in a thread title manufactures a phantom article.

## 9. Implicit-row sampling — artifact rate 84 %, **over the 10 % bar**

### 9.0 Sampling frame — exact selector

The frame is **law-uniform within a category**, not row-weighted: within each category the distinct
`law_id`s carrying implicit rows are sorted, shuffled once with a fixed seed, and the first *n* are
taken; then **one row is drawn uniformly at random from within that law**. The full selector, which
reproduces the 31 rows exactly (verified by re-running it against the same `catalog.db`):

```python
import sqlite3, random
conn = sqlite3.connect("catalog.db")
rows = conn.execute("""SELECT p.id, p.law_id, l.category, p.article, p.paragraph, p.text
                         FROM provisions p JOIN laws l USING(law_id)
                        WHERE p.implicit = 1 AND p.valid_to IS NULL""").fetchall()
by = {}
for r in rows:
    by.setdefault(r[2], []).append(r)
rnd = random.Random(20260804)                      # fixed seed
quota = {"ordinances": 9, "laws": 7, "regulations": 4, "implementing": 2, "codes": 2}
picked = []
for cat, n in quota.items():
    laws = sorted({r[1] for r in by[cat]})         # law-uniform frame
    rnd.shuffle(laws)
    for lw in laws[:n]:
        picked.append(rnd.choice([r for r in by[cat] if r[1] == lw]))
for lw, n in [("naredba-3-ot-9-yuni-2004-g-za-ustroystvoto-na-elektricheskite-uredbi-i-elektropr", 4),
              ("naredba-1-ot-25-yanuari-2023-g-za-usloviyata-i-reda-za-izvarshvane-na-natsionaln", 3)]:
    picked += rnd.sample([r for r in rows if r[1] == lw], n)
```

Row ids produced (stable across re-runs):
`270844 388491 392112 359493 175877 294109 308504 208012 194972 · 37215 19644 5540 127010 68669
68019 47405 · 412845 412587 450143 460311 · 467470 468319 · 135778 149316` (the 24 random rows),
then `233501 233022 231219 234837 · 160523 160714 160875` (the 7 mandated rows).
**31 rows / 26 laws.**

The mandated rows are 4 from `naredba-3-ot-9-yuni-2004-…` (the act reported in the Task 6c-a
analysis as contributing +451 of the B2 fix's +593 implicit rows — **that split is not re-verifiable
at this HEAD**, since the pre-B2 catalog no longer exists, and is quoted here only as the reason the
act was mandated into the sample) and 3 from `naredba-1-ot-25-yanuari-2023-…` (annex cells under the
false anchor „Чл. 17. т. 5, буква „б“ от Регламент…“).

**Caveat that cuts against this sample, stated for the record:** the `laws` stratum drew **both**
state-budget acts (ЗДБРБ 2025 and ЗДБРБ 2026) among its 7 laws. Under the law-uniform frame with 45
eligible laws that is a ≈2.1 % coincidence, and it makes the `laws` stratum more artifact-heavy than
a typical draw would be. It reproduces deterministically from the seed above; it is not a
row-weighted draw dressed up as law-uniform. The strata re-weighting in §9.1a is the honest way to
read past it — and it moves the number **up**, not down.

### 9.0a Category allocation is neither row- nor law-proportional

| category | eligible laws | implicit rows | row share | sampled | row-proportional would be | law-proportional would be |
|---|---:|---:|---:|---:|---:|---:|
| ordinances | 201 | 12,803 | 52.60 % | 9 | 12.6 | 15.2 |
| laws | 45 | 10,476 | 43.04 % | 7 | 10.3 | 3.4 |
| regulations | 56 | 896 | 3.68 % | 4 | 0.9 | 4.2 |
| implementing | 7 | 97 | 0.40 % | 2 | 0.1 | 0.5 |
| codes | 8 | 68 | 0.28 % | 2 | 0.07 | 0.6 |

The three small categories are over-represented roughly tenfold by row share — and they are the
**least** artifact-dense strata in the sample. Correcting for that raises the rate; see §9.1a.

Standard applied: **genuine** = a self-contained normative paragraph of the article body;
**artifact** = table cell, fragment of a split sentence or enumeration, annex/form/template
material, quoted-ЗИД or false-anchor material, section header, separator or chrome.

| # | act (category) | row | verdict | mechanism |
|---|---|---|---|---|
| S01 | наредба 56/2003 (ord) | чл. 15 ал. 2 = „(Ал. 2 и 3 отм. - ДВ, бр. 94 от 2005 г.)“ | genuine | repeal marker in its own алинея slot |
| S02 | наредба за съществените изисквания… (ord) | чл. 25 ал. 1 | genuine | article lead + точки merged by `_SUBPOINT_RE` |
| S03 | наредба за студентските стажове (ord) | чл. 12 ал. 1 | artifact | annex **template договор** („АДМИНИСТРАЦИЯТА“) under a duplicate чл. 12 anchor |
| S04 | наредба за формата…информация (ord) | чл. 11 ал. 5 = „в ……“ | artifact | annex form absorbed — the closer knows `Приложение №`/`ПРИЛОЖЕНИЕ` but not „**Приложение към чл. 5**“ |
| S05 | наредба 11/2003 (ord) | чл. 10 ал. 4 = „вв) движението на средствата…“ | artifact | `_SUBPOINT_RE` misses **doubled-letter** subpoints (аа/бб/вв) |
| S06 | наредба 8121з-413/2024 (ord) | чл. 6 ал. 5 = „основен език“ | artifact | table cell |
| S07 | наредба Iз-1971/2009 (ord) | чл. 273 ал. 32 = „c“ | artifact | table cell |
| S08 | наредба 2/2021 (ord) | чл. 21а ал. 3 | artifact | `/span>` tag-leak false anchor + absorbed article title |
| S09 | наредба 16/2010 (ord) | чл. 9 ал. 2 = „да посочат страна на произход…“ | artifact | trailing clause of the lead sentence after an enumeration |
| S10 | ЗГМО (law) | чл. 2а ал. 1 | **artifact** (corrected) | чл. 2а has **no** алинеи; ал. 1 and its sibling ал. 2 („при условие че…“) are the two halves of one sentence |
| S11 | ЗДБРБ 2025 (law) | чл. 53 ал. 871 = „998,5“ | artifact | budget table cell |
| S12 | ЗАДС (law) | чл. 4 ал. 2 = „аа) за Германия: Остров Хелиголанд…“ | artifact | doubled-letter subpoint |
| S13 | ЗДБРБ 2026 (law) | чл. 52 ал. 40 = „7 041,6“ | artifact | budget table cell |
| S14 | Закон за офицерските събрания (law) | чл. 3 ал. 2 = „-------------------------“ | artifact | separator rule |
| S15 | ЗОТ (law) | чл. 106 ал. 1 | genuine | sibling ал. 2 = „Допълнителна разпоредба“ — section header, artifact |
| S16 | ЗКПО (law) | чл. 86 ал. 2 = „където:“ | artifact | formula-legend fragment |
| S17 | правилник СОС (СВСУ) (reg) | чл. 16 ал. 4 = „1.3. представлява СВСУ;“ | artifact | `_SUBPOINT_RE` misses **multi-level decimal** subpoints (`1.3.`) |
| S18 | правилник СОС (обществен посредник) (reg) | чл. 29 ал. 3 = „- за нарушаване…“ | artifact | `_SUBPOINT_RE` has no **dash-bullet** alternative |
| S19 | правилник ВГС (reg) | чл. 33 ал. 1 | genuine | sibling ал. 2 = „Допълнителна разпоредба“ — artifact |
| S20 | УП МТСП (reg) | чл. 24 ал. 2 = „изискванията на Закона за счетоводството…“ | artifact | subpoint split mid-sentence |
| S21 | ППЗДвП (impl) | чл. 66 ал. 2 = „Светлоотразяващият елемент…“ | artifact | trailing sentence of an enumeration item (verified in source at line 1488) |
| S22 | ППЗ филмовата индустрия (impl) | чл. 35 ал. 1 | genuine | article lead + точки |
| S23 | ГПК (code) | чл. 22н ал. 1 | artifact | quoted-ЗИД text under a `/span>` tag-leak false anchor |
| S24 | НК (code) | чл. 418 ал. 1 | **artifact** (corrected) | чл. 418 has **no** алинеи; ал. 1 and its sibling ал. 2 („се наказва с лишаване от свобода от пет до петнадесет години.“) are the two halves of one sentence |
| S25–S28 | наредба 3/2004 (ord, **mandated**) | чл. 693 ал. 47 · чл. 583 ал. 40 · чл. 61 ал. 856 · чл. 1194 ал. 102 | artifact ×4 | electrical-installation table cells („стълба плюс 10 m“, „на или“, „10“, „средства под тях“) |
| S29–S31 | наредба 1/2023 (ord, **mandated**) | чл. 17 ал. 2 · ал. 193 · ал. 354 | artifact ×3 | annex cells under the false anchor „Чл. 17. т. 5, буква „б“ от Регламент…“ |

**Genuine 5 / artifact 26 = 83.9 %.** Excluding the 7 mandated rows the random half alone is
**genuine 5 / artifact 19 = 79.2 %**. Either way the 10 % bar is not merely missed, it is missed by
an order of magnitude.

S10 and S24 were originally scored genuine. That was **inconsistent with the standard stated above**:
in both acts the article carries no алинеи at all, so the parser manufactured *both* rows by cutting
one sentence in two, and the head is as much a fragment as the tail. Correcting them moves the
headline from 77.4 % to 83.9 % and the random half from 70.8 % to 79.2 %. Both corrections move the
number **against** the „acceptable“ direction; the earlier figures were the conservative ones.
The head-of-a-split-sentence class belongs with the trailing-clause segmentation ruling in §11.5.

### 9.1a Strata re-weighting — the number survives it and rises

Because the three small categories are over-sampled ~10× by row share (§9.0a) and are the least
artifact-dense strata, the unweighted random-half figure **understates** the corpus rate. Weighting
each stratum's observed rate by its row share:

| stratum | observed artifact rate (random half) | row weight |
|---|---:|---:|
| ordinances | 7/9 = 77.8 % | 52.60 % |
| laws | 6/7 = 85.7 % | 43.04 % |
| regulations | 3/4 = 75.0 % | 3.68 % |
| implementing | 1/2 = 50.0 % | 0.40 % |
| codes | 2/2 = 100 % | 0.28 % |

**Row-share-weighted rate = 81.0 %** (74.8 % under the pre-correction classification). Every way of
reading the sample lands far above 10 %.

### 9.1b Three independent estimates converge

| method | artifact rate |
|---|---:|
| strata-reweighted, pre-correction classification | 74.8 % |
| random half, standard applied consistently | 79.2 % |
| strata-reweighted, standard applied consistently | 81.0 % |
| full 31-row sample (incl. the 2 mandated concentrations) | 83.9 % |
| **independent row-uniform sample of 15 rows (review round)** | **14/15 = 93.3 %** |

The review round's row-uniform draw — budget cells, electrical table cells, a formula fragment and a
`/span>` remnant, with only `naredba-7-ot-22-fevruari-2008-…` чл. 198 ал. 24 genuine — is the
highest of the five because row-uniform sampling weights the tabular giants at their true mass. The
spread 74.8 %–93.3 % across three independent frames is what makes the >10 % routing unarguable: no
frame, classification standard, or weighting brings the rate within an order of magnitude of the bar.

### 9.1 Judgement-free corroboration

| indicator over all 24,340 current implicit rows | count | share |
|---|---:|---:|
| `LENGTH(text) < 40` | 17,859 | 73.4 % |
| `LENGTH(text) < 15` | 15,415 | 63.3 % |
| text does not end in `.`, `;` or `:` | 18,030 | 74.1 % |
| sits in an article with a **duplicate anchor** (698 such articles) | 4,656 | 19.1 % |
| `LENGTH(text) >= 40` | 6,481 | 26.6 % |

The two state-budget acts alone hold 9,302 rows — 38.2 % of the corpus total — at 99.6 % under 40
chars. Even excluding the top-10 acts by implicit rows, 56.2 % of the remaining 7,656 rows are under
40 chars.

### 9.1c Rows by leading shape — definitions shipped with the counts

An earlier draft of this section quoted three counts derived from loose SQL `GLOB` patterns that
could not be reproduced from the text of the report. They are replaced here by Python `re.match`
counts over an explicitly stated frame, so the fix round can measure its own before/after against
the same definition.

**Frame:** `SELECT text FROM provisions WHERE implicit = 1 AND valid_to IS NULL` — 24,340 rows,
`catalog.db` built at HEAD `f0d414c3`. Each pattern is applied with `re.match` (anchored at the
start of the row text).

| shape | pattern | rows |
|---|---|---:|
| doubled-letter subpoint | `^[а-я]{2,3}\)\s` | **271** |
| multi-level decimal subpoint | `^\d+(?:\.\d+)+\.?\s` | **304** |
| dash bullet | `^[-–—]\s` | **515** |
| annex marker | `^(?:Приложение\|ПРИЛОЖЕНИЕ)` | **4** |
| table marker | `^(?:Таблица\|ТАБЛИЦА\|Табл\.)` | **129** |
| section header | `^(?:Допълнителн\|ДОПЪЛНИТЕЛН\|Преходни\|ПРЕХОДНИ\|Заключителн\|ЗАКЛЮЧИТЕЛН)` | **31** |

The first three are the `_SUBPOINT_RE` gaps; the space requirement is deliberate, because
`_SUBPOINT_RE` itself ends in `\s` and a fix must match that shape. **Union of the three gaps =
1,090 rows; with the 31 section headers = 1,121 rows** (this supersedes the „1,183 rows“ figure in
an earlier draft of §11.1).

Sensitivity — these counts are pattern-brittle, which is why the pattern ships with the number:

| variant | rows |
|---|---:|
| doubled letter, exactly two letters `^[а-я]{2}\)\s` | 267 |
| doubled letter, two or three `^[а-я]{2,3}\)\s` (adopted) | 271 |
| decimal, separator space required `^\d+(?:\.\d+)+\.?\s` (adopted) | 304 |
| decimal, no space required `^\d+(?:\.\d+)+\.?` | 386 |
| dash, ASCII only `^-\s` | 515 |
| table marker without `Табл.` | 127 |
| table marker with `Табл.` (adopted) | 129 |

The three discrepancies raised in review resolve exactly here: 267 vs 271 is „exactly two letters“ vs
„two or three“; 386 vs 304 is „no separator space required“ vs „required“; 127 vs 129 is the
`Табл.` abbreviation. The dash-bullet, annex-marker and section-header counts were already
reproducible and are unchanged.

### 9.2 Where the artifacts cluster — the distinction that changes the ruling

They cluster in **annex and table material** (FR-026 reserved scope). The doctrinal target of
FR-034 is **clean**:

| act | implicit rows | rows < 40 chars |
|---|---:|---:|
| ЗС | 103 | **2.9 %** |
| ЗЗД | 461 | **4.1 %** |
| ЗЛС | 44 | 15.9 % |
| наредба 3/2004 (electrical tables) | 1,753 | 93.2 % |
| ЗДБРБ 2025 / ЗДБРБ 2026 | 4,634 / 4,668 | 99.7 % / 99.6 % |

Spot reads of ЗЗД (чл. 127 ал. 1, чл. 204 ал. 2, чл. 244 ал. 4, чл. 292 ал. 2) and ЗС (чл. 56 ал. 1,
чл. 72 ал. 3) return well-formed, self-contained алинеи. **FR-034's own objective is met.**

**Known limitation of this table.** „% rows under 40 chars“ is a proxy for *table cells*, not for
artifacts in general, and it **systematically understates** the artifact rate in doctrinal acts:
four of the five mechanisms in §9.3 — trailing clauses (S09, S21), mid-sentence subpoint splits
(S20), and split-sentence heads and tails (S10, S24) — produce **long** artifacts that the proxy
scores as clean. The low percentages for ЗЗД, ЗС and ЗЛС are therefore evidence that those acts are
free of *table-cell* contamination, and are consistent with — but do not prove — freedom from the
segmentation artifacts. The row-level reads above are the actual evidence for the doctrinal claim;
the table is corroboration only.

### 9.3 …but four mechanisms do contaminate ordinary doctrinal articles

These are not annex material and are cheap to fix in `index/provisions.py`:

1. `_SUBPOINT_RE` misses **doubled-letter** subpoints `аа) бб) вв)` — 271 rows.
2. `_SUBPOINT_RE` misses **multi-level decimal** subpoints `1.3.`, `2.3.1.2.5.` — 304 rows.
3. `_SUBPOINT_RE` has no **dash-bullet** alternative `- …` — 515 rows.
4. Plain-text section headers — „Допълнителна разпоредба“ in the singular is not emitted as a `##`
   header, so it does not close the article and becomes an алинея — 31 rows
   (ЗОТ чл. 106 ал. 2, правилник ВГС чл. 33 ал. 2).

(Counts and their patterns: §9.1c. Union of 1–3 = 1,090 rows; with 4 = 1,121 rows.)

A fifth class — **one sentence cut into two or more rows** — is a segmentation-rule decision, not a
regex gap, and needs an explicit ruling. It is larger than the four regex gaps suggest, because it
covers both halves of each cut, not only the tail: enumeration trailing clauses (S09, S21), the
mid-sentence subpoint split (S20), **and** the split-sentence pairs where the article has no алинеи
at all and both rows are fragments (S10 ЗГМО чл. 2а ал. 1+2, S24 НК чл. 418 ал. 1+2). Five of the 24
random rows — 21 % of the random half on its own — sit in this class.

### 9.4 Ruling

**The artifact rate does not clear the bar and the plan's own condition applies: a fix round before
governance.** The verdict holds under every frame tried — 74.8 % strata-reweighted on the original
classification, 79.2 % on the random half with the standard applied consistently, 81.0 %
strata-reweighted, 83.9 % on the full sample, 93.3 % on an independent row-uniform draw (§9.1b). The
FR-034 doctrinal claim stands; what does not stand is the aggregate figure — `24,340 implicit rows`
must not be quoted as an FR-034 achievement number until annex and table material is classified. The
defensible number today is the doctrinal subset.

## 10. Structure-mismatch census — 51 acts in 4 families

Extracted from `refresh-fr034-run2.log` (`structure mismatch (report-only)`, 51 lines / 51 distinct
doc_ids, identical to run 1) and mapped to acts via `identificador`. The log records only the
*first* mismatching article per act; for each of the 51 the checker's markdown-side attribution
(`fetcher/bg/coverage.structure_mismatches`) was re-implemented against the committed markdown to
record **what stopped attribution**.

| family | acts | classification |
|---|---:|---|
| **A. `SUP>` / `/span>` tag remnant makes „чл. N¹“ a duplicate of „чл. N“** | 21 | **new class** — not FR-034, not FR-030 |
| **B. Duplicate article number from an annex- or ПЗР-embedded act** | 20 | FR-026 (annex-as-separate-document) + FR-030 |
| **C. Capitalized inline citation „Чл. N.“ read as an anchor** | 3 | FR-030 |
| **D. One source `div.Article` spanning several articles or a whole annex** | 7 | FR-026 + check-side over-count |

(C is 3 and D is 7, not 2 and 8: `naredba-4-ot-22-yuli-2016-…` чл. 107 is a citation-false-anchor
case by mechanism — „0Чл. 107. параграф 3, буква „в“ от ДФЕС“ — and is counted in C, where its
prose already placed it.)

**None of the 51 is residual FR-034 scope.** Residual FR-034 in the strict sense: zero.

**Family A — 21 acts.** lex.bg renders superscript article indices („чл. 260и¹“) and the markdown
carries the raw remnant: `**Чл. 14н.**SUP>1.`, `Чл. 260и.SUP>1`, `Чл. 9./span>`. `_ARTICLE_RE` and
`_STRUCT_ARTICLE_RE` read that as a second „чл. 14н“, so **the superscript article is not
addressable under its own number** — its rows collide with the base article's. Corpus-wide at HEAD:
`SUP>` 190 occurrences across 36 acts, `/span>` 577 across 47 acts, `/STRONG>` 1 act — **identical
counts at `main`**, so this is pre-existing and untouched by FR-034. Members include ТЗ чл. 260и,
НК чл. 278б, КСО чл. 123з, ДОПК чл. 143е, ЗКПО чл. 260х, ЗПОО чл. 17а, ЗАПСП чл. 94б,
ЗПФИ чл. 227з, ЗПътищата чл. 36з, ЗКИ чл. 152г, ЗДАНС чл. 42н, ППЗЧРБ чл. 63и,
наредба Н-18 чл. 52а, наредба 16/1999 чл. 14н, ЗМПВВППРБ чл. 117, ЗПППЦК чл. 212а,
ЗЗВВХВС чл. 21б, ЗФуражите чл. 77з, наредба 44/2011 чл. 195г, правилник за ускорени производства
чл. 10, правилник ЦД чл. 46.

**Family B — 20 acts.** The source carries two `div.Article` elements with the same number: the real
article and one inside a Приложение or ПЗР that reproduces another act. The check pairs the annex
element's block count against the real article's paragraph count. Representative:
`pravilnik-za-organizatsiyata-i-deynostta-na-narodnoto-sabranie-2` чл. 1, expected 46 / got 1 — the
real чл. 1 is a single sentence, while the 46 blocks belong to
„Чл. 1./STRONG>. (1) Самостоятелният бюджет на Народното събрание…“ inside „Приложение към
правилника“. Full membership (act · reported article · expected/got):

| act | art | exp/got |
|---|---|---|
| `naredba-na-stolichen-obshtinski-savet-za-pazarite-na-teritoriyata-na-stolichna-o` | 1 | 96/2 |
| `naredba-6-za-izpolzuvane-i-predstavyane-na-nedvizhimite-pametnitsi-na-kulturata` | 1 | 50/2 |
| `zakon-za-mestnite-danatsi-i-taksi` | 1 | 185/13 |
| `pravilnik-na-stolichen-obshtinski-savet-za-organizatsiyata-i-deynostta-na-stolic-2` | 1 | 43/2 |
| `naredba-7-ot-22-fevruari-2008-g-za-utvarzhdavane-na-obraztsite-na-knizha-svarzan` | 44 | 2/1 |
| `naredba-na-stolichen-obshtinski-savet-za-predostavyane-na-sotsialnite-uslugi-asi` | 8 | 5/1 |
| `naredba-na-stolichen-obshtinski-savet-za-tsenite-pri-sdelki-s-nedvizhimi-imoti-n` | 1 | 5/1 |
| `naredba-41-ot-10-dekemvri-2008-g-za-iziskvaniyata-kam-obekti-v-koito-se-otglezhd` | 59 | 6/3 |
| `naredba-na-stolichen-obshtinski-savet-za-sastavyane-izpalnenie-otchitane-i-kontr` | 1 | 60/2 |
| `naredba-14-ot-11-septemvri-2012-g-za-usloviyata-i-reda-za-predostavyane-na-bezva` | 1 | 2/1 |
| `pravilnik-po-bezopasnostta-na-truda-pri-vzrivnite-raboti` | 2 | 5/2 |
| `naredba-na-velikotarnovskiya-obshtinski-savet-za-opredelyaneto-i-administriranet` | 1 | 50/1 |
| `naredba-5-ot-3-septemvri-2018-g-za-prilagane-na-pravilata-na-biologichno-proizvo` | 46 | 45/13 |
| `pravilnik-na-stolichen-obshtinski-savet-za-ustroystvoto-i-deynostta-na-sofiyska-` | 1 | 44/1 |
| `naredba-na-velikotarnovskiya-obshtinski-savet-za-izgrazhdane-poddarzhane-i-opazv` | 1 | 49/5 |
| `pravilnik-za-ustroystvoto-i-deynostta-na-tsentara-za-profesionalno-obuchenie-pri` | 1 | 58/1 |
| `naredba-1-ot-25-yanuari-2023-g-za-usloviyata-i-reda-za-izvarshvane-na-natsionaln` | 17 | 270/8 |
| `naredba-na-stolichen-obshtinski-savet-za-priem-na-detsa-v-obshtinskite-samostoya` | 1 | 2/1 |
| `naredba-za-kriteriite-usloviyata-i-reda-za-opredelyane-na-statut-na-domakinstvo-` | 1 | 27/4 |
| `pravilnik-za-organizatsiyata-i-deynostta-na-narodnoto-sabranie-2` | 1 | 46/1 |

**Family C — 3 acts.** ЗБЛД чл. 59 (56/37): attribution dies at точка 18, whose text carries **two**
capitalized „Чл. N.“ citations, so the paragraph is treated as a cite list and the remaining ~19
paragraphs of чл. 59 are attributed to nobody.
`naredba-na-stolichen-obshtinski-savet-za-imenuvane-i-preimenuvane-na-obshtinski-` чл. 5 (3/0): the
article's own opening paragraph cites „по реда на **Чл. 98.** т.13 от Конституцията“ — two anchors
in one paragraph, so чл. 5 never starts at all.
`naredba-4-ot-22-yuli-2016-g-za-opredelyane-na-reda-za-saglasuvane-na-proektite-n` чл. 107 (14/6):
„0Чл. 107. параграф 3, буква „в“ от ДФЕС“ — an EU-treaty citation inside an annex table read as an
anchor. The same mechanism produces наредба 1/2023 чл. 17's false anchor (counted in B, since that
act's dominant defect is the annex duplicate; it is the row family sampled in §9).

**Family D — 7 acts.** One source `div.Article` carries several articles or an entire annex, so
`expected_blocks` is not a valid lower bound for one article. КТ чл. 131 (3/1): „Чл. 131. (Отм.)“ and
„Чл. 132. (Отм.)“ share one source div and our markdown splits them correctly — a **check-side false
positive**. Наредба 1/2016 чл. 1 (383/8): the act itself has only „Член единствен“, and the reported
„чл. 1“ lives in the annexed МЕТОДИКА. ЗОРВКС чл. 8 (27/3): quoted ЗИД text
(„§ 2. Чл. 330.се изменя така:“). Full membership:

| act | art | exp/got |
|---|---|---|
| `naredba-1-za-spasitelnata-deynost-v-minite-himicheskite-i-metalurgichnite-zavodi` | 121 | 4/2 |
| `kodeks-na-truda` | 131 | 3/1 |
| `pravilnik-na-stolichen-obshtinski-savet-za-ustroystvoto-i-deynostta-na-obshtinsk-2` | 12 | 12/9 |
| `naredba-na-stolichen-obshtinski-savet-za-reda-za-poluchavane-i-upravlenie-na-dar` | 1 | 2/1 |
| `naredba-1-ot-1-yuli-2016-g-za-odobryavane-na-metodika-za-prilagane-na-izklyuchen` | 1 | 383/8 |
| `naredba-na-velikotarnovskiya-obshtinski-savet-za-opredelyaneto-i-administriranet-2` | 23 | 85/9 |
| `zakon-za-oblekchenie-rabotata-na-varhovniya-kasatsionen-sad-i-vav-vrazka-s-tova-` | 8 | 27/3 |

Family A's 21 members are named above; B, C and D are enumerated here, so all 51 lines of the
run-2 census are attributable from this document alone.

## 11. Routing out of Task 6c-b

Fix round, before governance:

1. **Implicit-row artifact rate 84 %** (§9; 74.8–93.3 % across three independent frames, §9.1b).
   Minimum first cut: `_SUBPOINT_RE` gains doubled-letter, multi-level-decimal and dash-bullet
   alternatives (**1,090 rows** by the §9.1c definitions); plain-text section headers close the
   article (31 rows) — 1,121 rows together; the annex closer learns „Приложение към …“. Then
   re-measure the rate against the §9.1c patterns, which are the stated before-state.
2. **FR-026 annex/table classification** — now the dominant artifact mass (top-10 acts hold 16,684
   implicit rows, mostly table cells). Blocks any corpus-level claim about implicit-row counts.
3. **New FR — `SUP>` / `/span>` HTML-tag remnants** (§10, family A): 190 + 577 occurrences,
   superscript articles unaddressable. Pre-existing on `main`.
4. **New FR — lex.bg chrome leak** in `naredba-5-ot-10-may-1999-…kadastralni` (§8.2): one act,
   volatile content, manufactures phantom articles and guarantees refresh churn. Pre-existing on
   `main`.
5. A ruling on **sentences cut across rows** (§9.3, class 5) — segmentation policy, not a regex gap.
   Covers enumeration trailing clauses (S09, S21), mid-sentence subpoint splits (S20) **and
   split-sentence pairs in articles with no алинеи at all**, where head and tail are both fragments
   (S10 ЗГМО чл. 2а, S24 НК чл. 418). 5 of the 24 random rows.

No change is required to `scripts/fr034_verify.py`: all four verify-red lines are baseline
artifacts — two lawful ДВ amendments, one lex.bg editorial corrigendum, one phantom article that
existed in the baseline and not in the sweep.

---

# 12. Post-fix state (Task 6c-d) — the doctrinal/annex split governance should publish

Routing item 1 of §11 was executed on branch `fix/fr034-unnumbered-alineas`, commit `3d325f66`
(`index/provisions.py` + `tests/index/test_provisions.py`; full task record in
`.superpowers/sdd/2026-08-02-fr034-unnumbered-alinea-remediation/task-6c-d-report.md`).
This section supersedes §9.2's „the doctrinal target is clean“ table as the doctrinal claim, and
supersedes the „24,340 implicit rows“ figure everywhere it appears.

## 12.1 What was fixed

`_SUBPOINT_RE` gained the multi-letter буква, multi-level-decimal and dash-bullet alternatives;
`_CONTINUATION_CLOSER_RE` gained a whole-paragraph section-header branch and „Приложение към …“;
and a new `_CONTINUATION_RE` treats a paragraph opening with a lowercase Cyrillic letter (looking
past any leading `(…)` amendment marker) as a sentence continuation rather than a new алинея.

Two of this report's own counts did not survive being read row by row and are corrected here:

* **§9.1c „section header — 31“** selects 31 rows with a loose prefix, but **only 19 are section
  headers**; the other 12 are table cells starting with the same prefix („Допълнителни огнегасящи
  вещества“, „Допълнителни електро-“, „Допълнителна информация, по преценка на организацията“,
  „ДОПЪЛНИТЕЛНИ КРИТЕРИИ“). The shipped closer requires the whole paragraph to be a header.
* **§9.1c „annex marker — 4“** includes one CITATION („Приложение II, Регламент (ЕС) 2021/1165“),
  not an annex start. The shipped closer keys on „към“, not on a bare „Приложение“.

## 12.2 Shape counts, same §9.1c frame and patterns

| shape | before (§9.1c) | after |
|---|---:|---:|
| multi-letter subpoint `^[а-я]{2,3}\)\s` | 271 | **0** |
| multi-level decimal `^\d+(?:\.\d+)+\.?\s` | 304 | **0** |
| dash bullet `^[-–—]\s` | 515 | **7** |
| annex marker `^(?:Приложение\|ПРИЛОЖЕНИЕ)` | 4 | **2** |
| table marker `^(?:Таблица\|ТАБЛИЦА\|Табл\.)` | 129 | **129** |
| section header (loose prefix) | 31 | **12** |
| union of 3 gaps | 1,090 | **7** |
| union with headers | 1,121 | **19** |
| **total implicit rows** | **24,340** | **21,043** |

All 19 residual rows were read and are correct behaviour: the 7 dash rows are article-FIRST table
cells that by construction cannot merge into a predecessor; the 12 header-prefix rows are the
table cells §12.1 identifies as not headers; the 2 annex-prefix rows are the citation above and a
form label. `table marker` is unchanged by design — table markers are FR-026 scope.

Article rows are unchanged (147,771). Explicit alinea rows move 310,003 → 309,999, in exactly two
acts, both repairs: `naredba-14-ot-11-septemvri-2012-…` чл. 4 returns to its pre-FR-034 baseline
of 144 (the annex form „Приложение към споразумение за сътрудничество“ is no longer swallowed),
and `naredba-5-ot-10-may-1999-…kadastralni` чл. 43 no longer absorbs the „Допълнителни
разпоредби“ section. `scripts/fr034_verify.py check` returns exactly the four known adjudicated
residuals of §4.1/§8; R3/R4/R5 clean; no new failure.

## 12.3 The split — this, not an aggregate, is the publishable figure

The stratum criterion is `fecha_publicacion` before 1974 (Указ 883): the drafting population
FR-034 exists for, versus everything else.

| stratum | acts | rows | share | artifact rate |
|---|---:|---:|---:|---:|
| **doctrinal** (pre-1974) | 13 | 761 | 3.6 % | **6.8 %** (census, §12.4) |
| **annex/table** (1974+ and undated municipal) | 205 | 20,282 | 96.4 % | **95.0 %** (19/20 sampled) |

Row-share-weighted ≈ 92 %, consistent with §9.1b's row-uniform draw of 93.3 %. **The aggregate
barely moved, and that is the correct outcome**: 96.4 % of the frame is annex and table mass —
the two state-budget acts alone are 9,266 rows — which FR-034 must not and cannot touch. The
3,297 rows removed were the part that contaminated ordinary articles, never the mass.

**`21,043 implicit rows` must not be quoted as an FR-034 achievement number** any more than
24,340 could be. The publishable figure is the doctrinal subset in §12.4, and §11's routing item 2
(FR-026 annex/table classification) still blocks any corpus-level claim.

## 12.4 Doctrinal census — all 761 rows, enumerated

A 20-row sample of the doctrinal stratum scores 15.0 % artifact, but a sample cannot say WHERE
the residue is, and an earlier draft of the task report wrongly generalised its draw into „the
artifacts come from one act“. Every doctrinal row was therefore read. Two classes account for all
of it — **false or quoted anchors** (the article number belongs to another law reproduced in the
act's ПЗР) and **chrome rows** (ЗИД stubs, `/span>` remnants, headings, separator rules,
promulgation formulae):

| act | rows | artifacts | what |
|---|---:|---:|---|
| ЗЗД | 459 | 10 | false-anchor blocks чл. 1001а/1001б/1001г (quoted ГПК + ЗПИ text) |
| ЗС | 103 | 2 | false-anchor duplicate чл. 84 |
| ЗОРВКС | 57 | 23 | false anchors чл. 330/516/517/518/562/677/683 |
| ЗЛС | 44 | 9 | чл. 11 ал. 1; чл. 212а ал. 3/4/5; чл. 284а ал. 3; чл. 918 ал. 3/4/5; чл. 934 ал. 1 |
| ЗБППМН | 7 | 3 | чл. 45/47/155 ал. 1 — `/span>`-chrome ЗИД stubs |
| ЗОС | 4 | 2 | чл. 3 ал. 2 separator; ал. 3 promulgation formula |
| ЗВТ | 5 | 2 | чл. 24 ал. 2 separator; ал. 3 „Издаден в София…“ |
| ЗА-1947 | 11 | 1 | чл. 1 ал. 2 „А. По Военно-наказателния закон - книга II“ |
| ППУ техн. правоспособност · ЗУПКНИ · ЗА-1964 · наредба 13а-10403 · ЗА-1950 | 71 | 0 | — |
| **total** | **761** | **52 = 6.8 %** | **8 of 13 acts contribute** |

A broader reading gives 100 / 761 = 13.1 %: ЗЛС's чл. 915–934 are ЗГС articles inserted by ЗЛС, so
all 44 of its rows could be classed as quoted-anchor material rather than only the 9 chrome rows
(+35); ЗА-1947's ал. 3–11 are unmarked enumeration items under a colon-terminated lead (+9); and
ЗБППМН's 4 quoted-НК provisions (+4). The conservative 52 counts only rows that are chrome or sit
under an anchor the act demonstrably does not own.

**None of these 52 is FR-034 segmentation** — they are the pre-existing false-anchor and
tag-remnant classes of §10 families A/C/D, i.e. routing item 3. What the fix round removed was the
segmentation class; what remains in the doctrinal stratum is anchor-detection work.

**Doctrinal claim, restated for governance:** of 761 implicit rows across 13 pre-Указ-883 acts,
**709 are clean position-derived алинеи and 52 are enumerated pre-existing artifacts in 8 acts**.
Spot reads of ЗЗД, ЗС and ЗЛС continue to return well-formed алинеи, and ЗЗД чл. 265 now numbers
correctly (the six-month / five-year prescription is ал. 3, not ал. 5). FR-034's own objective is
met on its own population.

## 12.5 What the fix round did NOT fix

* **§9.3 class 5, capital-initial half.** Sample row S21 (ППЗДвП чл. 66) is a trailing sentence
  that opens with a capital („Светлоотразяващият елемент…“) and is indistinguishable from a real
  алинея without semantics. No rule of this kind reaches it. → FR-026.
* **A „not a provision“ guard was measured and DECLINED.** Candidate signals (bare number, lone
  punctuation, dotted filler, „< 4 words with no terminal punctuation“) select 14,874 rows —
  **70.7 % of the frame** — with only 2 doctrinal hits, both separator rules already enumerated in
  §12.4. The refusal is not about the separation: it is that deleting is not classifying (routing
  item 2 needs those rows to label), that 14,400 of the 14,874 come from a length heuristic with
  no test of provision-hood, and that a 70.7 % deletion is the D-055 failure shape. The correct
  instrument is a `kind` / `is_annex` column on `provisions`, which makes the split a query.
  Carry this measurement into FR-026 as evidence the population is separable.
* Routing items 2, 3, 4 and the capital-initial part of 5 remain open exactly as written in §11.
