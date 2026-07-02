# FR-030 finding — residual 3-digit alinea citation false positives (2026-07-02)

**Surfaced by:** pre-UI hardening plan Task 4's live rebuild + sweep
(`.superpowers/sdd/task-4-report.md`, "3-digit paragraph survivors" section).
**Same corruption class as P0-2** (`index/provisions.py` `_ALINEA_MARKER_RE`,
review 2026-07-02, Task 2): a parenthesised number in running prose gets
parsed as an alinea-boundary marker instead of a real "(N)" clause opener.
P0-2 fixed the 4-digit case (years, e.g. `(1969)`) via a `\d{1,3}` digit cap —
116 bogus rows across 22 acts. That cap has a gap: it also *admits* genuine
3-digit citation-style numbers, which the cap alone cannot distinguish from a
real 3-digit alinea.

## Live sweep evidence (Task 4, post-rebuild, 3601-act catalog)

Bogus `paragraph` values found: `100, 400, 660, 230, 401, 505, 506, 601` (8
distinct values, more than 8 row hits — several recur across multiple
articles in the same act).

| Paragraph | Act | Article(s) | Source context |
|---|---|---|---|
| `(100)` | `naredba-10-ot-1-april-2015-...identifika.md` | 7а | "номер \"100 XXX...\", като първите три цифри на табелата показват кода на страната **(100)**" — country-code gloss |
| `(100)` | `naredba-6-ot-8-oktomvri-2013-...ofitsialna-ide.md` | 8, 10, 11 | "първите три цифри от номера на чипа/кодът на България **(100)**" — chip/country-code gloss (3 hits) |
| `(400)`, `(660)`, `(230)` | `naredba-3-ot-9-yuni-2004-...elektropr.md` | 1195, 1599, 1602, 1619, 1623, 1867, 1868 | dual-voltage citations, e.g. "напрежение 500 **(660)** V", "не по-високо от 220 **(230)** V", "380 **(400)** V" (multiple hits) |
| `(401)`, `(505)`, `(506)`, `(601)` | `naredba-rd-02-20-1-ot-5-oktomvri-2022-...konstruktsii.md` | 62 | BDS EN ISO 5817 weld-defect codes, e.g. "Липса на сплавяване..." **(401)**, "Пръски" **(601)** |
| `(100)` | `naredba-za-taksite-za-izpolzvane-na-letishtata-...aer.md` | 18 | "раздели на сто **(100)** числото на кил..." — divisor gloss |

All 8 were manually vision-eyeballed (per task-4-report.md) and confirmed
false positives — none is a real alinea marker.

## Root cause

The alinea marker regex (`index/provisions.py:_ALINEA_MARKER_RE`,
`r"\(\s*(\d{1,3}[а-я]?)\s*\)"`) cannot distinguish a **citation-in-running-text**
(a country code, voltage pair, standard-defect code, or divisor gloss that
happens to be parenthesised and 1-3 digits) from a **clause-opening marker**
("(N)" at the start of a new alinea). Both are syntactically identical:
digits inside parentheses. There is no cheap syntactic signal — the real
markers and the false positives sit in the same digit range (1-3 digits) and
neither reliably follows sentence-terminal punctuation.

## Rejected approach: letter-boundary filter

Requiring the marker to follow sentence/anchor punctuation was tried and
rejected during the P0-2 fix (see `index/provisions.py` lines 159-166 and
the review 2026-07-02 P0-2 discussion): it cannot distinguish a citation
following a letter from a real alinea whose preceding sentence lacks
terminal punctuation (common after amendment-introduced alineas, e.g.
"...управление (4) (Нова - ДВ, бр. 94 от 2019 г. ...)"). Confirmed to
silently drop real alineas in 3 of 6 fixture acts (zop чл. 196, zeu чл. 5,
ppz-aktsizi чл. 78) when tried live.

## Why this is out of scope for the hardening plan

Fixing this needs a genuinely context-aware boundary check (e.g. distinguish
"(660)" mid-sentence, with no clause structure around it, from a real "(3)"
opening a new normative clause) — a parsing-quality investment, not a
mechanical cap adjustment like P0-2. Deliberately left unfixed here per team
lead's explicit instruction on Task 4; recorded as FR-030 for future pickup.

## Cross-references

- P0-2 / Task 2 (the 4-digit-year fix this gap sits next to):
  `index/provisions.py:_ALINEA_MARKER_RE` and its surrounding comment block.
- D-050 (pre-UI hardening plan).
- Task 4 report: `.superpowers/sdd/task-4-report.md` (git-ignored scratch;
  this note is the durable record of its "3-digit paragraph survivors"
  table).
