# Handover: 2026-07-01 — D-047 bulk re-scrape (remaining ~3,203 non-law acts)

**Author:** ekimir session (Claude Opus 4.8, 1M). **For:** the next clean session.
**One-liner:** The tool is built + hardened, `main` carries all the DRS-priority restores, and the **laws** category (396 acts) is re-scraped on a branch. What remains is the **bulk stage**: the other 4 tree categories (~3,203 acts) through the same gated pipeline, then catalog rebuild + FR-020 verify + merge.

---

## 0. Where we are (one paragraph)

The D-047 parser fix + class-agnostic coverage gate were already committed (prior sessions). This session (a) **hardened the fetcher** with a Cloudflare-clearance layer so the corrective re-bootstrap can reach CF-gated lex.bg (D-047 Task 9), (b) **re-scraped all 396 laws** on branch `refresh/2026-06-29-parser-fix` (0 gate failures), (c) **restored the DRS-priority acts on `main`** (6 priority + 5 DRS-2 + the price/food info ordinances + the НСС decree), (d) fixed a **committer-date bug** that made shared `main` look like it regressed (D-048), and (e) recorded a **new P1 defect** — the corpus omits whole lex.bg act-type categories (D-049 / FR-025). The remaining work is the **bulk stage** (codes + ordinances + regulations + implementing = ~3,203 acts) on the same branch, then the catalog rebuild + FR-020 spot-check + the branch→main merge. After that, **FR-025 is next due.**

## 1. Read path (next session)

1. `.claude/CLAUDE.md` → `docs/sync/ACTIVE.md` → `docs/sync/DEFERRED.md` → `docs/process/delivery-contract.md`.
2. **This handover** (the bulk procedure).
3. `docs/plans/2026-06-29-parser-remediation-plan.md` — Tasks 11 (full re-bootstrap), 12 (rebuild catalog), 13 (FR-020 corrective baseline). The bulk stage IS Task 11 for the remaining categories.
4. `docs/runbook/2026-07-01-cf-cookie-mint.md` — **how to mint / re-mint the `cf_clearance` cookie** (you WILL need this repeatedly).
5. `docs/sync/DECISIONS.md` → **D-047** (the defect), **D-048** (committer-date), **D-049** (category omission).
6. `docs/frs/INDEX.md` → **FR-025** (next-due defect, after this bulk work).

## 2. Current refs (as of 2026-07-01)

| Ref | Commit | Contents |
|---|---|---|
| `origin/main` | `c3f0c49a` | CF-clearance tooling, D-048 fix, ALL DRS restores (6 priority + 5 DRS-2 + price/food info ordinances + НСС decree in `postanovleniya/`), governance (D-048/D-049/FR-025). |
| `origin/refresh/2026-06-29-parser-fix` | `cbd1bbd4` | 396 laws restored (338 `[popravka]` + 18 `[reforma]`, **0 gate-fail**) + merged D-048 fix. **Bulk-ready.** |

`main` and the branch have **diverged** (main = DRS restores + tooling; branch = laws restores). See §6 for the merge.

## 3. THE REMAINING BULK WORK — procedure

Run the other 4 tree categories on the **branch**, same gated pipeline, D-048 dating.

### 3.1 Scope
`--categories code,ords,regs,reg_laws` → corpus dirs `codes` (24) + `ordinances` (2627) + `regulations` (492) + `implementing` (60) = **~3,203 acts**. (`laws` is DONE on the branch — do NOT re-run it.) At ≤1 req/s + parse/gate/commit → **~60–90 min wall-clock + several cookie re-mints** (cf_clearance TTL ≈ 10 min).

### 3.2 Exact steps
```bash
cd ~/swprj/legalize-bg
git fetch origin
git checkout refresh/2026-06-29-parser-fix     # branch EXISTS — do NOT pass --branch
git pull --ff-only

# 1) Mint a cookie FIRST (see the runbook §"Mint procedure"): drive the Playwright MCP
#    browser to lex.bg, wait for CF to auto-clear, dump {user_agent, cf_clearance, cookies}
#    and Write it to a cookie file in YOUR session scratchpad, e.g.:
#    $SCRATCH/cf_cookie.json

# 2) Launch the bulk run in the BACKGROUND (it is long):
SCRATCH=<your session scratchpad dir>
.venv/bin/python refresh.py \
  --categories code,ords,regs,reg_laws \
  --cookie-file "$SCRATCH/cf_cookie.json" \
  --cookie-wait 900 \
  --state "$SCRATCH/refresh-bulk-state.json" \
  > "$SCRATCH/refresh-bulk.log" 2>&1   # run_in_background: true
```
- **No `--branch`** (branch exists; `_git_checkout_branch` uses `git checkout -b` and would fail). You must already be *on* the branch.
- **Fresh `--state`** (the laws-run state lived in the prior session's scratchpad; a fresh state is correct — you're processing different categories).
- `--cookie-wait 900`: on a CF challenge the run **pauses** and polls the cookie file for a changed `cf_clearance`; it resumes automatically once you re-mint.

### 3.3 The cookie loop (you must babysit this part)
When the log prints:
```
CLOUDFLARE challenge at <url> — pausing; awaiting fresh cf_clearance in <cookie file>. Waiting up to 900s.
```
→ re-mint via Playwright (runbook §"Mint procedure") and **overwrite the cookie file**. The running process polls every 15 s, reloads, and resumes the exact URL. `.refresh-state.json` means a hard kill loses at most the in-flight act — relaunch (steps above, same `--state`) resumes. Consider a `/loop` (dynamic mode) to poll the log + re-mint + stop when done, as this session did for the laws stage.

### 3.4 Gate discipline (HALT-and-triage)
The class-agnostic coverage gate is the **sole per-act acceptance check** (threshold `LEGALIZE_COVERAGE_THRESHOLD`, default 64). refresh.py **skips writing** any act with `uncovered_chars > threshold` and records it in `gate-report.json` (it does NOT halt the whole run). At the end, **triage every entry in `gate-report.json`**:
- Genuine new dropped class → add it to `CLASS_MAP`/formatting in `fetcher/bg/text_parser.py`, re-run.
- Structural surprise that is actually complete (e.g. ЗАДС defines terms in `Чл. 4`, no base ДР; КРБ has no ДР) → confirm via vision on the raw HTML and accept.
The 396 laws had **0** gate failures; ordinances (2,627, far more varied) will likely surface a handful — **triage via vision, do not auto-accept or auto-skip.**

## 4. After the bulk completes — Tasks 12–13

1. **Rebuild catalog:** `.venv/bin/python -m index.build` (full) then `.venv/bin/python scripts/verify_catalog.py`.
2. **Assert restoration corpus-wide:** `grep -rlF "Допълнителни разпоредби" laws codes ordinances regulations implementing --include='*.md' | wc -l` should now be in the **thousands** (was ~20 at the start of remediation).
3. **FR-020 corrective-baseline check (Task 13):** the corrective commits are `[popravka]`/`[reforma]` author-dated at each act's legislative date; the **same-author-date collapse** in `index/build.py:_all_file_versions` means they overwrite (not duplicate) the latest version row → **no spurious "incomplete→complete" version step** for dated acts. Add/keep an oracle test; **known residual:** the ~121 null-date FR-011 degenerates get a corrective commit dated *today* → one extra version row (accept or handle).
4. Spot-check `get_law(name, date)` / `diff()` return content **with** definitions.

## 5. Key discipline (do not regress)

- **D-048:** corpus commits set only `GIT_AUTHOR_DATE` (legislative date, for FR-020's `%ad`); committer-date stays real. Do NOT re-introduce `GIT_COMMITTER_DATE` backdating (it broke shared-main ordering + DRS freshness detection). Guard test: `tests/refresh/test_commit_state.py::test_commit_does_not_backdate_committer_date`.
- **≤1 req/s + D-011:** the CF layer is *stop-and-wait-for-a-fresh-browser-cookie*, NOT an automated bypass. Never add a header-spoofing/cloudscraper solver. **D-039:** texts only.
- **Coverage gate is the sole per-act gate.** No base-ДР/§1 structure heuristics.

## 6. Merge strategy (branch → main)

`main` gained the DRS restores (ordinances/implementing) that the branch lacks; the branch has all laws + (after bulk) all other categories. The bulk run re-restores those same DRS ordinances on the branch, so both sides should be byte-identical for them → a clean merge. When the bulk + catalog verify pass: merge `refresh/2026-06-29-parser-fix` → `main` (or PR), rebuild the catalog once more on `main`, then the corpus is trustworthy again → update `ACTIVE.md` (lift the P0 banner), D-047 → remediated, and memory.

## 7. Coordination with the DRS session

- DRS consumes `origin/main` **by path**. Detect corpus freshness by **CONTENT**, not commit date: `git show origin/main:<path> | grep -c "Допълнителни разпоредби"` (≥1 = D-047-fixed). Commit author-dates are legislative by design (a body fix moves no date).
- The НСС `postanovleniya/` decree is the *adopting ПМС* only; the standards СС 1–42 (a separate приложение) are deferred to FR-025 (owner decision 2026-07-01).

## 8. Next due AFTER the bulk (do not start before the corpus is trustworthy)

**FR-025 / D-049 / Task #9** — corpus omits whole lex.bg act-type categories (ПМС confirmed via НСС; likely тарифи/инструкции/решения) + the приложение-as-separate-doc facet. Enumerate all lex.bg categories → owner scope decision → add dirs/discovery/index/`rango` (protected surfaces → preflight) → corpus-level coverage gate → fetch via the CF-hardened pipeline.

## 9. Ready-to-paste kickoff prompt

```
Continue legalize-bg. Session startup protocol (.claude/CLAUDE.md → docs/sync/ACTIVE.md
→ DEFERRED.md → delivery-contract), then read:
  - docs/sync/HANDOFFS/2026-07-01-bulk-rescrape-handover.md   ← this handover (bulk procedure)
  - docs/runbook/2026-07-01-cf-cookie-mint.md                 ← cookie mint/re-mint
  - docs/plans/2026-06-29-parser-remediation-plan.md          ← Tasks 11–13

TASK: run the D-047 BULK re-scrape — the remaining ~3,203 non-law acts
(--categories code,ords,regs,reg_laws) on branch refresh/2026-06-29-parser-fix, through the
CF-hardened gated pipeline (handover §3). Mint a cf_clearance cookie via the Playwright MCP
first; re-mint on each CF pause (~10-min TTL). HALT-and-triage every gate-report.json entry
via vision. Then rebuild the catalog + verify + FR-020 spot-check (Tasks 12–13), and prepare
the branch→main merge. Do NOT re-run laws (done on the branch). Do NOT re-introduce
GIT_COMMITTER_DATE backdating (D-048). Coverage gate is the sole per-act gate.

FR-025 (corpus category omission) is next due — only AFTER the corpus is trustworthy.
```

## 10. Risks / gotchas

- **R1 — cookie TTL ~10 min.** A 60–90 min bulk needs ~6–9 re-mints. The wait-for-refresh loop handles it, but you must be present to re-mint (or run a `/loop`).
- **R2 — gate failures need vision triage**, not blind skip. Ordinances are the most structurally varied category.
- **R3 — do not pass `--branch`** on the bulk run (branch exists → `checkout -b` fails). Checkout first.
- **R4 — `postanovleniya/` is not in `CATEGORY_DIRS`**, so `index/build` won't index the НСС decree (fine for DRS path-access; indexing is FR-025 scope).
- **R5 — merge divergence** (§6): main has DRS ordinance restores the branch will re-create; expect byte-identical, clean merge, but verify.
- **R6 — `ordinances` count is 2627** (was ~2604 at bootstrap) — a few added since; the staleness probe in `crawl_with_probe` handles new tree pages.
```
