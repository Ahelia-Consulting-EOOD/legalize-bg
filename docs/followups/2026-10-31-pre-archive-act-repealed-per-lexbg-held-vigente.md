# A pre-archive act lex.bg marks repealed in 2000 is held in the corpus as in force

Registered 2026-10-31 in the S3 session of the starting state (worktree `unruffled-feynman-cd9070`, branch `claude/s3-act-profiles`, PR #52).

**Finding.** The Наредба № 4 за пощенските съобщения (`ordinances/naredba-4-za-poshtenskite-saobshteniya.md`, promulgated 7 December 1979) carries `estado: vigente` and `ultima_actualizacion: 2000-08-04`. lex.bg's history line of its page ends „отм. ДВ. бр. 64 от 4 Август 2000г.“: lex.bg records the act as repealed on the date the corpus records as its last change. The bootstrap writes `estado: vigente` for every act (`fetcher/bg/metadata.py`), and the refresh path's repeal detection (`refresh.py`, `_REPEAL_RE`) never ran over this act. The S3 pairing's investigator returned the verdict `repealed` with lex.bg's marker as its evidence (`data/runs/act-profiles-2026-10-31/verdicts/naredba-4-za-poshtenskite-saobshteniya.json`).

**Why it matters.** The corpus's `estado` is not a witness of anything for the bootstrapped acts (the S3 review of 31 October 2026 found this; D-077, point 10), and this act shows it wrong. The repeal lies in the Gazette's PDF era (бр. 64/2000), which no title pass can see; only lex.bg's own marker shows it.

**Route to closing.** S2's defect register gains the kind „wrong estado“ only by the owner's word; S4 decides the act's source. Until then the act stays as it is: no corpus file is edited by hand. A script over the raw store for every act whose history line carries „отм.“ against `estado: vigente` would size the class in one pass (the S3 session did not run it: outside S3's scope).
