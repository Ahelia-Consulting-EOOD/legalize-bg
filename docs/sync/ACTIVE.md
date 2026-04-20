# Active Work

**Current phase:** Phase 1a (bootstrap scrape) — **COMPLETE** on `bootstrap/phase-1a`, pending spot-check and merge to main.
**Current owner:** ekimir
**Started:** 2026-04-20
**Next action:** Spot-check 10 random acts against lex.bg, then decide merge strategy (fast-forward vs squash) for landing `bootstrap/phase-1a` into `main`.

## Status

Phase 1a pipeline is code-complete and the corpus is fully bootstrapped:

- `bootstrap/phase-1a` branch on origin: 3,573 commits, one per act, each with Source-Id / Source-Date / Norm-Id trailers and `GIT_AUTHOR_DATE` backdated to the publication date (pre-1970 acts clamped to 1970-01-01 epoch floor; null-date acts use the bootstrap run date, with `Source-Date: unknown` in the body).
- Per-category counts match PRD targets exactly:
  - laws: 395 (target ~394)
  - codes: 24 (target ~24)
  - ordinances: 2,604 (target ~2,604)
  - regulations: 490 (target ~490)
  - implementing: 60 (target ~61)
- SQLite catalog (`catalog.db`, not tracked): 3,573 `laws` rows + 3,573 `law_versions` rows (one initial version per act, `valid_to = NULL`).
- 66 automated tests pass, including real-git-repo integration tests for `_git_commit` backdating.

### Session history (2026-04-20)

1. **Implementation**: parallel subagent dispatch for Tasks 2-5 + 7; sequential Tasks 6, 8, 9. 28 tests on first pass.
2. **Code review** surfaced C1-C3 (transport hardening) + I1-I7. All 10 items fixed with TDD. 55 tests pass.
3. **Dry run + verification** (`scripts/verify_catalog.py`): 3,677 entries reduced to 3,573 unique after the Конституция/cross-category dedup fix was added to `CatalogCrawler.crawl_all`. `catalog.json` committed as snapshot.
4. **First full bootstrap run**: hit a git date-format bug. Bare `YYYY-MM-DD` is rejected by `GIT_AUTHOR_DATE` (exit 128); commits silently accumulated staged files until a null-date act triggered a successful commit that bundled ~30 files at a time. Result: 3,573 files in 121 wrong-dated commits. Tagged the broken state as `bootstrap-phase-1a-broken-backup` for recovery.
5. **Recovery via `scripts/rebuild_bootstrap_commits.py`**: no lex.bg re-fetch (files on disk were correct). Reset branch to main, replayed one commit per file with the fixed `_format_author_date` (ISO 8601 timestamps, pre-1970 clamped to epoch). 3,573 commits in 2 min 20 s, zero failures. `git push --force-with-lease` replaced the remote branch.

## Blockers

None.

## Pending

- **Spot-check (Definition of Done, Phase 1a)**: 10 randomly sampled acts must match lex.bg text exactly after whitespace/quote normalization.
- **Merge decision**: fast-forward `bootstrap/phase-1a` into `main` (keeps one-commit-per-act history) or squash-merge (one "[bootstrap] initial corpus" commit on main). Squash loses per-act `GIT_AUTHOR_DATE` backdating, so default is fast-forward.
- **Phase 1b (MCP server)**: `get_law()`, `search()`, `get_article()` tools; next phase after this one lands on main.
