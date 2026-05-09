# legalize-bg Delivery Contract

**Effective:** 2026-04-20
**Scope:** All contributions to ahelia-consulting/legalize-bg
**Authoritative design:** `docs/plans/2026-04-19-legalize-bg-design.md`

---

## Session Model

Claude Code sessions work against this repo with the following startup protocol:

1. Read `.claude/CLAUDE.md` for repo-specific instructions
2. Read `docs/sync/ACTIVE.md` for current work state and next actions
3. Check `.ahelia/constraint-profile.yaml` for machine-readable constraints
4. Check `.ahelia/protected-surfaces.yaml` before modifying any interface or schema
5. Identify current phase (1a through 6c) and work within its scope

Sessions must not skip phases or begin work on a later phase until its prerequisites are met.

---

## Commit Discipline

### Commit Types

All commits to the legislation corpus follow the Legalize SPEC commit format. Five types, mapped to Bulgarian legislative practice:

| Type | Meaning | When Used | Example |
|------|---------|-----------|---------|
| `[bootstrap]` | Initial scrape from lex.bg | Phase 1a only | `[bootstrap] Закон за обществените поръчки` |
| `[reforma]` | Amendment (ЗИД) | Ongoing, from DV | `[reforma] Закон за обществените поръчки` |
| `[nova]` | New law first published | When new act appears in DV | `[nova] Закон за киберсигурността` |
| `[otmyana]` | Full repeal | When act is entirely repealed | `[otmyana] Закон за далекосъобщенията` |
| `[popravka]` | Corrigendum | Correction in subsequent DV issue | `[popravka] Закон за обществените поръчки` |

### Commit Message Format

Every corpus commit must include three metadata fields in the body:

```
[reforma] Закон за обществените поръчки

Source-Id: dv-63-2017
Source-Date: 2017-08-04
Norm-Id: 2136735703
```

- **Source-Id:** Identifier for the source document (DV issue or lex.bg doc)
- **Source-Date:** Publication date of the source (DV issue date)
- **Norm-Id:** lex.bg document ID for the affected law

### Commit Granularity

- **Bootstrap (Phase 1a):** One commit per act. Not one massive commit for all 3,573 acts.
- **Ongoing amendments:** One commit per amendment event.
- **GIT_AUTHOR_DATE + GIT_COMMITTER_DATE:** Must be set to the DV publication date of the amendment, not the session date. This enables `git log --follow` to reconstruct legislative history chronologically.
  - **Format constraint:** git refuses bare `YYYY-MM-DD` with `fatal: invalid date format`. Always emit full ISO 8601 with time and timezone — `YYYY-MM-DDT00:00:00+00:00`. Reference: `bootstrap._format_author_date()`.
  - **Pre-1970 dates:** this git build also rejects negative Unix timestamps. Clamp pre-1970 publication dates to `1970-01-01` for the env var; keep the true date in the `Source-Date:` body line. Reference: D-017, D-018.

### Pipeline Code Commits

Commits to pipeline code (fetcher, consolidation engine, MCP server, tooling) use conventional commit messages. These are not corpus commits and do not require the Legalize format.

---

## Review Requirements

### Data Accuracy (Corpus Commits)

- **Self-review against lex.bg oracle:** After bootstrap or consolidation, compare generated Markdown against current lex.bg text for the same law. Normalize whitespace and quotes before diff.
- **Frontmatter validation:** All 13 YAML fields must be present and correctly populated.
- **Encoding verification:** Output must be valid UTF-8 with no cp1251 artifacts.

### Code Review (Pipeline Commits)

- Pipeline code (fetcher/bg/, consolidation/, monitor/, mcp/) requires code review.
- Changes to protected surfaces (see `.ahelia/protected-surfaces.yaml`) require explicit owner review.

---

## Quality Gates

From Legalize `ADDING_A_COUNTRY.md` -- four hard gates that must pass before upstream contribution:

| Gate | Requirement | Verified By |
|------|------------|-------------|
| **G1** | Fetcher returns valid Blocks for 100% of test norms | Unit tests against sample acts |
| **G2** | Frontmatter validates against SPEC schema for all acts | Schema validation script |
| **G3** | Bootstrap commits pass legalize-pipeline CI | CI run on PR |
| **G4** | Daily update produces zero regressions on existing norms | Diff-based regression test |

No PR to legalize-pipeline will be opened until all four gates pass.

---

## Branch Model

- **`main` branch:** Legislation corpus. Contains Markdown files with YAML frontmatter. Each commit represents a legislative event (bootstrap, amendment, repeal, etc.). History is sacred -- never rebase or force-push.
- **Feature branches:** Pipeline code development. Named descriptively (e.g., `feat/fetcher-discovery`, `feat/mcp-search`). Merged to main via PR after review.
- **No long-lived branches:** Feature branches should be short-lived. Merge or close within a few sessions.

---

## Definition of Done

### Universal phase-promotion gate

Before promoting from any phase X to phase Y, every Open row in `docs/sync/DEFERRED.md` whose Target column is X (or earlier) must be reviewed and resolved (Implemented / Re-affirmed with date / Withdrawn). **Phase promotion is blocked while any such row remains Open.** Re-affirmations require a new `docs/sync/DECISIONS.md` entry stating why the deferral is being kept; Withdrawals require a DECISIONS entry explaining why the work won't happen. This gate applies to every per-phase DoD below; each phase's checklist also surfaces it as its last bullet for local visibility.

### Phase 1a -- Bootstrap Scrape

- [ ] All ~3,574 acts scraped from lex.bg and converted to Markdown
- [ ] YAML frontmatter with all 13 fields populated for every act
- [ ] One `[bootstrap]` commit per act with correct Source-Id, Source-Date, Norm-Id
- [ ] SQLite catalog index built and queryable
- [ ] Spot-check: 10 randomly selected acts match lex.bg text exactly (after normalization)
- [ ] No cp1251 encoding artifacts in any file
- [ ] All Open rows in `docs/sync/DEFERRED.md` with Target ≤ this phase have been resolved per the universal phase-promotion gate above.

### Phase 1b -- MCP Server

- [ ] `get_law()`, `search()`, `get_article()` tools working
- [ ] Claude Code can access Bulgarian legislation via MCP
- [ ] Per-tool p95 latency budgets (soft assertions in 1b.1, hard in 1b.2 per D-027): `search` < 100 ms, `get_law` (current) < 100 ms, `get_law` (historical) < 500 ms, `get_article` < 50 ms.
  - Authoritative source: `docs/plans/2026-05-09-phase1b-mcp-design.md` §9. The "наредба" pathological single-word category query currently exceeds the 100 ms budget at ~290 ms p95 — tracked as FR-016 for Phase 1b.2 hardening.
- [ ] All Open rows in `docs/sync/DEFERRED.md` with Target ≤ this phase have been resolved per the universal phase-promotion gate above.

### Phase 2 -- Temporal Index

- [ ] SQLite law_versions table populated from git history
- [ ] `history()` and `diff()` MCP tools working
- [ ] Date-based law retrieval returns correct historical version
- [ ] All Open rows in `docs/sync/DEFERRED.md` with Target ≤ this phase have been resolved per the universal phase-promotion gate above.

### Phase 3 -- DV Monitor

- [ ] Poller detects new DV issues on Tue/Fri schedule
- [ ] Amendment detector identifies affected laws
- [ ] Alert or log for new amendments requiring processing
- [ ] All Open rows in `docs/sync/DEFERRED.md` with Target ≤ this phase have been resolved per the universal phase-promotion gate above.

### Phase 4 -- Consolidation Engine

- [ ] ZID parser handles substitution, addition, deletion (covers ~80% of amendments)
- [ ] Patcher applies parsed amendments to Markdown
- [ ] Validator compares result against lex.bg oracle
- [ ] Accuracy >= 70% on regex-only; >= 90% with LLM fallback
- [ ] All Open rows in `docs/sync/DEFERRED.md` with Target ≤ this phase have been resolved per the universal phase-promotion gate above.

### Phase 5 -- Legalize Contribution

- [ ] All four quality gates (G1-G4) pass
- [ ] fetcher/bg/ implements all 4 Legalize interfaces
- [ ] PR submitted to legalize-pipeline
- [ ] CI passes on upstream repo
- [ ] All Open rows in `docs/sync/DEFERRED.md` with Target ≤ this phase have been resolved per the universal phase-promotion gate above.

---

## Rate Limiting Protocol

All HTTP access to lex.bg must follow these rules:

1. **Maximum 1 request per second.** Enforce with `time.sleep()` or equivalent.
2. **Set a descriptive User-Agent** identifying the project (not a browser UA string).
3. **Retry with exponential backoff** on 429 or 5xx responses. Max 3 retries.
4. **Stop immediately** if Cloudflare challenges appear. Do not attempt to bypass.
5. **Log all requests** with timestamp, URL, status code, and response time.
6. **Full bootstrap crawl** takes ~2 hours at 1 req/sec for 3,573 acts plus ~104 tree pages. Plan accordingly — do not rush.
7. **Off-peak preferred:** Run large crawls outside Bulgarian business hours when possible.
8. **lex.bg is the validation oracle, not the ongoing source.** After bootstrap, DV (dv.parliament.bg) is the primary source. lex.bg is used only for validation comparisons.

### Reference implementation

All 5 rules are enforced in `fetcher/bg/client.py:RateLimitedSession`:
- Rule 1: `rate_limit_sec` gate before every request; `HttpTransport` (doc pages) and `bootstrap.py:TreeTransport` (tree crawl) share one session so the ceiling is global across the pipeline.
- Rule 2: `USER_AGENT = "legalize-bg/0.1 (https://github.com/Ahelia-Consulting-EOOD/legalize-bg)"`.
- Rule 3: `max_retries=3`, `retry_base_sec=2.0` (2 / 4 / 8 s backoff) on HTTP 429 and 500-599; connection/timeout errors also retry.
- Rule 4: `is_cloudflare_challenge()` matches body markers (`"Just a moment"`, `"challenge-platform"`, `"__cf_chl_"`, `"Attention Required! | Cloudflare"`) on status 403/503 and raises `CloudflareChallenge`, which the bootstrap does NOT catch — the run halts for manual intervention.
- Rule 5: INFO log per successful request with URL, status, and elapsed ms; WARN on retry or transient failure.

## Bootstrap Runner CLI

`python bootstrap.py [flags]` — supported flags:

- `--output PATH` — corpus root (default: `.`).
- `--db PATH` — SQLite catalog path (default: `catalog.db`).
- `--dry-run` — crawl the catalog only; skip per-act fetch and commits. Use to verify counts before a full run; gated by `scripts/verify_catalog.py`.
- `--branch NAME` — create and switch to `NAME` before the loop (recommended: `bootstrap/phase-1a`). Keeps `main` clean until the run is reviewed and merged.
- `--push-every N` — `git push --set-upstream` after every N successful commits plus one final push. 3× retry with 2/4/8s backoff on transient push failures. Requires `--branch` or a pre-existing upstream.
- `--remote NAME` — remote to push to (default: `origin`).

Reference Phase 1a invocation:

```bash
python bootstrap.py --branch bootstrap/phase-1a --push-every 250 --db catalog.db
```
