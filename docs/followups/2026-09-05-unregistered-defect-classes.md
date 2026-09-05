# Follow-up 2026-09-05: defect classes that were unregistered, now FR-037 to FR-042

**Status:** recorded; each class has an FR row in `docs/frs/INDEX.md` (D-063)
**Origin:** authority reconciliation of 2026-09-05. Two gitignored rescue files in
`.superpowers/fr034-preserved/` held measurements for a month without an FR row or a follow-up
entry, which Directive 13 treats as unrecorded. This record gives them a home in the tree.

| FR | Class | Measurement carried over | Verified? |
|---|---|---|---|
| FR-037 | Fabricated article anchors from quoted text (C1) | 90 artifact rows / 8 of 13 doctrinal acts (FR-034 census, every row read); five refutation lenses refuted the leading rule | census verified row by row; rule refutation transcript-only |
| FR-038 | Ambiguous article addresses (C5) | 698 colliding keys / 144 acts (SQL, 2026-08-11); 2,290 / 232 / 4,382 (transcript) | SQL figure reproducible; transcript figure not |
| FR-039 | Un-hashed structural headings (C6) | 12,751 headings / 408 acts | transcript-only, UNVERIFIED |
| FR-040 | Record-layer truthfulness (C8) | 4 declared counts vs 3,624 on disk; declared gates absent | verified 2026-09-05 |
| FR-041 | Cross-reference capture (C9) | 1,662 `SameDocReference` spans discarded at conversion | verified in fixtures |
| FR-042 | lex.bg drops promulgated sections | 95 candidates / 25 empty sections; 2 acts confirmed against ДВ | detector reproducible; 2 confirmations live |

Sources: `.superpowers/fr034-preserved/fr037-transcript-findings-2026-08-06.md`,
`.superpowers/fr034-preserved/anchor-integrity-independent-findings-2026-08-11.md`,
`.superpowers/fr034-preserved/assurance-audit-2026-08-11.md`,
`docs/audits/2026-09-05-source-dropped-additional-provisions.md` (PR #27, open at the time of writing).
