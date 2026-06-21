# MISSING acts evaluation — corpus re-scrape 2026-06-21

**For:** owner review (decision required)
**Context:** the `refresh/2026-06` re-scrape found **18 acts in our corpus that no longer appear in lex.bg's browse tree**. Per owner directive they were **kept** (never auto-deleted) with `estado` untouched. This report evaluates *why* each left the tree, by re-fetching its lex.bg page and reading the document status, and recommends an action.

---

## Bottom line

| Finding | Count | Recommended action |
|---|---|---|
| **Confirmed repealed** (`отм. ДВ` marker, all 2026 repeal dates) | **17** | Flip `estado: vigente → derogado`, commit `[otmyana]`. Keeping them `vigente` is now factually wrong — they are no longer in force. |
| **Not a state act** (no ДВ promulgation — private association bylaw) | **1** | **Owner decision** — likely erroneously included; see §3. |

All 17 repeals fall **inside the refresh window** (repeal dates **2026-04-24 → 2026-06-16**), which is exactly why they dropped from lex.bg's "in force" tree. **6 of the 17 were superseded by an act we ADDED this run** (clean old→new pairs — see §2). Nothing here is alarming: no core statute went missing, and every disappearance is explained.

---

## 1. The 17 repealed acts (recommend `estado → derogado`)

The repeal marker is lex.bg's standard `… отм. ДВ. бр. N от <date>` annotation at the end of the document history.

| # | doc_id | Act | Dir | Repealed (ДВ / date) | Superseded by (ADDED this run) |
|---|---|---|---|---|---|
| 1 | 2135506845 | ПРАВИЛНИК за устройството и дейността на Комисията за защита от дискриминация | regulations | 48/2026 · 2026-05-26 | ✅ new КЗД правилник |
| 2 | 2135515370 | НАРЕДБА № 19/2005 — син език (bluetongue) по преживните животни | ordinances | 54/2026 · 2026-06-12 | — |
| 3 | 2135516067 | НАРЕДБА № 31/2005 — мерки за профилактика (ветеринарна) | ordinances | 54/2026 · 2026-06-12 | — |
| 4 | 2135518328 | НАРЕДБА № 26/2006 — защита и хуманно отношение към животните | ordinances | 54/2026 · 2026-06-12 | — |
| 5 | 2135526211 | НАРЕДБА № 22/2005 — намаляване страданията на животните | ordinances | 54/2026 · 2026-06-12 | — |
| 6 | 2135526865 | НАРЕДБА № 47/2006 — гранични инспекционни ветеринарни пунктове | ordinances | 54/2026 · 2026-06-12 | — |
| 7 | 2135533188 | НАРЕДБА № 83/2006 — данни в документите (ветеринарни) | ordinances | 54/2026 · 2026-06-12 | — |
| 8 | 2135535977 | НАРЕДБА № 102/2006 — мерки за профилактика | ordinances | 54/2026 · 2026-06-12 | — |
| 9 | 2135535978 | НАРЕДБА № ДВ-103/2006 — мерки за профилактика | ordinances | 54/2026 · 2026-06-12 | — |
| 10 | 2135536200 | НАРЕДБА — граничен здравен контрол | ordinances | 55/2026 · 2026-06-16 | — |
| 11 | 2135553161 | НАРЕДБА № 21/2007 — мобилни далекосъобщителни мрежи | ordinances | 38/2026 · 2026-04-24 | — |
| 12 | 2135576453 | НАРЕДБА № 26/2007 — прилагане и наблюдение (земеделски помощи) | ordinances | 39/2026 · 2026-04-28 | ✅ НАРЕДБА № 2/2026 |
| 13 | 2135785028 | НАРЕДБА — дейности с оръжия (ГД „Охрана"/ГД „ИН") | ordinances | 42/2026 · 2026-05-08 | ✅ new оръжия наредба |
| 14 | 2135828375 | НАРЕДБА № 35/2012 — проектиране (правила и норми) | ordinances | 38/2026 · 2026-04-24 | — |
| 15 | 2135880580 | НАРЕДБА № 1/2013 — съхраняване на запаси (нефт/нефтопродукти) | ordinances | 45/2026 · 2026-05-15 | ✅ НАРЕДБА № 1/2026 |
| 16 | 2137240577 | НАРЕДБА № Н-1/2024 — подпомагане с парични средства (отбрана) | ordinances | 46/2026 · 2026-05-19 | ✅ НАРЕДБА № Н-2/2026 |
| 17 | 2137247022 | ПРАВИЛНИК за организацията и дейността на Народното събрание (2024 г.) | regulations | 50/2026 · 2026-06-02 | ✅ new ПОДНС |

**Recommendation:** these are unambiguous repeals. Flip each to `estado: derogado` and record an `[otmyana]` marker commit (the file stays — historical text is the point).

---

## 2. The 6 supersession pairs (old repealed ↔ new added)

These are the textbook "re-photograph" wins — the old version dropped out of the tree the same window a new version was promulgated, and **both are now in the corpus** (old as history, new as current):

| Repealed (now MISSING) | Replacement (ADDED `[nova]`) |
|---|---|
| ПОДНС **2024** (`…narodnoto-sabranie.md`) | ПОДНС new (`…narodnoto-sabranie-2.md`) |
| КЗД правилник (old устройство и дейност) | КЗД правилник new (устройство и **организация на** дейността) |
| НАРЕДБА № 26/2007 (земеделски помощи) | НАРЕДБА № 2/2026 (същата материя) |
| НАРЕДБА — оръжия (ГД Охрана/ИН) | НАРЕДБА — оръжия (нова, `…orazhi-3.md`) |
| НАРЕДБА № 1/2013 (запаси нефт) | НАРЕДБА № 1/2026 (запаси нефт) |
| НАРЕДБА № Н-1/2024 (подпомагане отбрана) | НАРЕДБА № Н-2/2026 (подпомагане отбрана) |

The other 11 repealed acts were repealed without a same-window replacement in the tree (most are 2005–2012 veterinary/health наредби consolidated away by ДВ 54/2026).

---

## 3. The 1 outlier — NOT a state act (decision required)

**`2137255124` — „ПРАВИЛНИК ЗА СОЦИАЛНО ПОДПОМАГАНЕ НА ЧЛЕНОВЕТЕ НА СЪЮЗА НА АРХИТЕКТИТЕ В БЪЛГАРИЯ"** (`implementing/pravilnik-za-sotsialno-podpomagane-na-chlenovete-na-sayuza-na-arhitektite-v-balg.md`)

- **No ДВ promulgation.** Its lex.bg history reads: *"Приет от УС на САБ с Решение … по Протокол от 08.07.2014 г."* — adopted by the **management board of a private professional association** (Съюз на архитектите в България).
- **Source is `bularch.eu`** (the association's own site), not Държавен вестник.
- It carries **no repeal marker** — it simply left the tree, most likely because lex.bg removed it as out-of-scope for the national-legislation tree.

This is an **internal bylaw of a private body, not a национален нормативен акт.** It arguably should never have been in a *national legislation* corpus.

**Decision options for the owner:**
- **(a) Remove as erroneously included** — this is the handover's explicit hard-delete exception ("only ever hard-delete a file if you positively confirm it was published in error"). I have **not** done this; it needs your confirmation.
- **(b) Keep but mark out-of-scope** — flip `estado` to e.g. `derogado`/a non-vigente value and leave a note, treating it as a known data-quality artifact.
- **Follow-up either way:** worth a one-off sweep for other non-ДВ private-body documents that may have slipped into the corpus (grep frontmatter for acts whose `dv_issue` is null AND whose source is a non-ДВ site). I can run that if you want.

---

## 4. How to action this

`refresh.py --flip-missing-estado` flips `vigente → derogado` and writes an `[otmyana]` commit for **every** act gone from the tree. Two caveats before you run it:

1. **It would flip all 18, including the Architects bylaw (#18)** — which is *not* repealed. Decide #3 first; if you choose (a) remove or want #18 handled differently, flip the 17 deliberately rather than the blanket 18.
2. **`[otmyana]` author-date is `today` (2026-06-21), not the real repeal date.** The true repeal dates are known (column above). If you want git history to reflect the actual repeal dates (consistent with the "author-date = legislative date" convention, D-016), that's a small enhancement to `refresh.py` (pass the parsed `отм. ДВ` date as the `[otmyana]` author-date) — I can add it under TDD before the flip. Otherwise the blanket `today` date is acceptable for a marker commit.

**Recommended sequence:** (1) confirm #18's disposition; (2) optionally add the repeal-date enhancement; (3) run the flip for the 17 (or 18); (4) rebuild the index. All on `refresh/2026-06`, still pre-merge.

---

*Generated 2026-06-21. Data: re-fetched all 18 acts' lex.bg pages (1 req/sec). Raw analysis: `/tmp/missing_eval.json` (ephemeral).*
