# FR-032 golden-diff review — v1 vs v2 top-5 act orderings

**Date:** 2026-07-24 · **Layer 2 of the ranking-parity strategy** (design §7): every body-tier ordering change explained, owner-reviewed in the implementation PR.
**Method:** v1 = live catalog + v1 code, captured during the spike (2026-07-23, pre-rebuild). v2 = the full production pipeline (`full_text_search`: stop-words, synonym expansion, two-tier search, breadth-corrected pool, rang sort) on the rebuilt v5 catalog, `limit=10`.

## Corrected design claim (title tier)

The design claimed tier-1 ordering "unchanged by construction". That claim was WRONG
in one respect, discovered here: FTS5's bm25 term document-frequency in v1 counted a
term's appearances across the WHOLE row (title + 223M-char body), so v1 title-tier
IDF was body-inflated. The title-only table computes honest title-corpus IDF.
Consequences, visible in every title-served query below: **rank 1 is stable in all
cases** (the locked adversarial tests pass unchanged), while ranks 2–5 reshuffle
among sibling acts. Every observed reshuffle moves a more canonical act up (e.g.
ППЗОП above miscellaneous наредби). Assessment: an improvement, not a regression;
the "by construction" wording in the design §4 Decision 1 is superseded by this note.

## Title-served queries (7 of 10) — rank 1 stable, siblings reshuffle

| Query | v1 top-1 | v2 top-1 | Ranks 2–5 |
|---|---|---|---|
| обществени поръчки | ЗОП | ЗОП (=) | ППЗОП + устройствен правилник АОП move up |
| данък добавена стойност | ЗДДС | ЗДДС (=) | ППЗДДС rises 5→2 |
| лични данни | ЗЗЛД | ЗЗЛД (=) | правилник КЗЛД rises 5→2 |
| движение по пътищата | ЗДвП | ЗДвП (=) | ППЗДвП enters at 2 |
| енергийна ефективност | ЗЕЕ | ЗЕЕ (=) | sibling наредби reorder |
| защита на потребителите | ЗЗП | ЗЗП (=) | правилник НСЗП rises 3→2 |
| trailing sibling reorders in all cases | | | explained by honest title IDF |

## Body-tier queries (3 of 10) — the FR-032 semantics change

| Query | v1 top-5 | v2 top-5 | Explanation |
|---|---|---|---|
| **ЗОП** (synonym-expanded) | ППЗОП, устройствен правилник АОП, наредба-регистър, УП КЗК, наредба-основни-интереси — **ЗОП itself absent** | **ЗОП #1**, then закони whose ПЗР § reference ЗОП (§-labeled matches) | v1 MISSED the law itself (its body was one giant doc, poor bm25); v2's per-segment match finds it and rang-tiers float laws first. Improvement. |
| **трудов договор** | КТ #1, then наредби | ЗВО #1 (§ 4б, a dense трудов-договор provision), ЗЧОД #2 (чл. 74), **КТ #3**, then the same наредби | The breadth correction (D-056 Q1 amendment) + TIER2_ACT_POOL rang rescue keep КТ in the top 3; plain MIN had it at #31. ЗВО § 4б and ЗЧОД чл. 74 are genuinely about трудови договори (higher per-provision precision is the FR-032 point). Acceptable; КТ #1 would need act-level priors beyond scope. |
| **административни нарушения** | ЗАНН #1, then 4 weakly-related acts | **ЗАНН #1**, then законите with административнонаказателни разпоредби (чл.-labeled) | Breadth correction puts ЗАНН decisively first; followers are all acts with real административнонаказателни provisions. Improvement. |
| **касови апарати** | наредба-35 (функционални изисквания) #1 | ЗАвП #1 (чл. 24д — фискални устройства в превозите), ЗДДС § 1, наредба-7, 2 общински наредби, **наредба-18 #6** | Mixed: the two canonical acts (наредба-18 фискални устройства, наредба-35) rank 6 and ~8; two общински наредби at 4–5 are noise (single incidental segments). The rang tier treats all ordinances equally. Known residual small-segment noise; flagged for the owner — acceptable for v2, candidates for a future act-level prior (FR backlog). |

## Cap-recall (the headline criterion) — 3/3

Phrases from the formerly truncated tails, verified absent from the v1 capped
index and found by v2 (spike §4, re-verified on the production index):
КСО ✓, Кодекс за застраховането ✓, наредба за качеството на социалните услуги ✓.

## Segment-attribution samples (Q3 `matched` field)

Body-tier hits now attribute: e.g. "административни нарушения" → Закон за
електронните съобщения (чл. 313), "касови апарати" → ЗАвП (чл. 24д). Title-tier
hits carry `matched: null`.

## Verdict requested from the owner

Approve the v2 orderings as reviewed (one residual noted: касови-апарати-class
small-segment noise among same-rang ordinances). All locked ranking tests pass
unchanged; the D-051 perf budgets all pass (see the re-ratification decision entry).
