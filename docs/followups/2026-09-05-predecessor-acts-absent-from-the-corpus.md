# Predecessor acts absent from the corpus, revealed by ДВ materials

**Date:** 2026-09-05
**Status:** open, an owner decision on corpus scope; registered as FR-043
**Raised by:** the first coverage-map title pass (PR #43, `scripts/dv_coverage_map.py`), whose review found 712 of 737 „chain omissions“ and all of its `estado` disputes to be materials about same-titled predecessor acts

## The finding

Bulgarian acts are replaced by new acts of the same name, and the corpus holds only the current one. The coverage-map resolver attributes a Gazette material by the act name its title carries, so every material about a repealed predecessor resolves to the successor the corpus does hold: „Закон за изменение и допълнение на Закона за горите“ in бр. 64/2007 resolves to the Закон за горите of 2011; a ЗИД of the Граждански процесуален кодекс in бр. 84/2003 to the code of 2007; a ПМС repealing the правилник of the Висше военноморско училище, published in бр. 92/2018, to the successor правилник promulgated in that same issue.

Measured on 2026-09-05 over the 32,117 enumerated materials: 722 materials name a same-titled act the corpus does not hold, across 207 distinct corpus acts; 719 are published before the successor's promulgation, 2 are repeals published before the successor's last recorded amendment, 1 is a repeal in the successor's own promulgation issue. The instrument writes them to `predecessor-materials.csv` with a `reason` column and keeps them out of `chain-omissions.csv` and `estado-disputes.csv`; the title pass then reports 23 chain omissions and 0 `estado` disputes.

## The action

Two questions for the owner, neither of which the instrument can settle:

1. **Scope.** Whether repealed predecessor acts enter the corpus at all (as `estado: derogado` with their own chains), which is a `rango` and `estado` question the Legalize spec already models, and if so for which categories and from which date. The 722 materials over 207 acts are the measured size of the first batch, and the reading budget for their PDF-era part is not yet estimated.
2. **Resolution.** Until then, the resolver must keep attributing by title, and the `reason` column is the only thing that separates a predecessor's material from a chain omission. A body scan (plan Task A2) will meet the same class inside ПЗР instructions and needs the same rule.

## Verification

The rule is pinned by tests in `tests/scripts/test_dv_coverage_map.py` (one per reason and one for the repeal that stays a dispute). Every predecessor row's issue precedes the act's `fecha_publicacion`, sits in its promulgation issue, or precedes the act's last dated chain event; the review of PR #43 reconciled the 722 against the 737 rows of the pre-fix run.
