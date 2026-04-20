# Active Work

**Current phase:** Phase 1a (bootstrap scrape) — **COMPLETE and merged into `main`**.
**Current owner:** ekimir
**Started:** 2026-04-20
**Next action:** Kick off Phase 1b (MCP server) — author `docs/plans/2026-XX-XX-phase1b-mcp.md` following the Phase 1a plan precedent. Implementers must read `docs/data/canonical-data-model.md` §7 and `container-view.md` §7 (MCP Server, data-quality constraints subsection) before designing tool behavior.

## Status

Phase 1a shipped: the full Bulgarian national legislation corpus lives on `main` as 3,573 per-act `[bootstrap]` commits, each with `Source-Id` / `Source-Date` / `Norm-Id` trailers and `GIT_AUTHOR_DATE` backdated to the publication date (pre-1970 acts clamped to the 1970-01-01 epoch floor; null-date acts use the bootstrap run date with `Source-Date: unknown` in the body). Per-category counts match PRD targets to within 1 act:

- laws: 395 (target ~394)
- codes: 24 (target ~24)
- ordinances: 2,604 (target ~2,604)
- regulations: 490 (target ~490)
- implementing: 60 (target ~61)

`fetcher/bg/` implements the 4 Legalize interfaces (`LegislativeClient`, `NormDiscovery`, `TextParser`, `MetadataParser`). Transport layer hardened per delivery-contract §Rate Limiting Protocol: global 1 req/sec ceiling, 3× exp backoff on 429/5xx, `CloudflareChallenge` exception on CF markers, per-request INFO logging. SQLite catalog (`catalog.db`, gitignored) is rebuildable from git history and YAML frontmatter. 67 automated tests pass, including real-git-repo integration tests for `_git_commit` backdating.

### Session history (2026-04-20)

1. **Implementation**: parallel subagent dispatch for Tasks 2-5 + 7; sequential Tasks 6, 8, 9. 28 tests on first pass.
2. **Code review** surfaced C1-C3 (transport hardening) + I1-I7. All 10 items fixed with TDD. 55 tests.
3. **Dry run + verification** (`scripts/verify_catalog.py`): 3,677 entries reduced to 3,573 unique after the Конституция/cross-category dedup fix was added to `CatalogCrawler.crawl_all`. `catalog.json` committed as snapshot.
4. **First full bootstrap run**: hit a git date-format bug (bare `YYYY-MM-DD` rejected by `GIT_AUTHOR_DATE`, exit 128); commits silently accumulated staged files. Result: 3,573 files in 121 wrong-dated commits. Tagged the broken state as `bootstrap-phase-1a-broken-backup` for recovery.
5. **Recovery via `scripts/rebuild_bootstrap_commits.py`**: no lex.bg re-fetch. Reset branch to main, replayed one commit per file with the fixed `_format_author_date` (ISO 8601 timestamps, pre-1970 clamped to epoch). 3,573 commits in 2 min 20 s, zero failures.
6. **Spot-check (DoD)**: 10 random acts sampled deterministically; 10/10 titles consistent between SQLite DB, local Markdown, and lex.bg source.
7. **Post-run review (M-1/M-2/M-3)**: M-2 fixed (`--push-every` now requires `--branch` to prevent accidental pushes to `main`); M-1 and M-3 accepted as-is with rationale.
8. **Merge**: `bootstrap/phase-1a` rebased onto `main` and fast-forwarded; linear history preserved, 3,573 backdated per-act commits now on `main`.

### Known corpus caveats (for Phase 1b / Phase 2 implementers)

See `docs/data/canonical-data-model.md` §7 and `container-view.md` §7 MCP Server subsection:
- Slug collisions in ~5-10% of files (generic Наредба/Правилник titles); `law_id` is not derivable from title — always go through SQLite.
- Null `fecha_publicacion` in 121 acts (3.4%); temporal queries must treat these as date-uncertain, not bootstrap-dated.
- 7 acts have empty `titulo` (phantom lex.bg entries); surface by `identificador` in search results.
- `FR-011` tracks the G2 triage backlog for ~128 affected acts.

## Blockers

None.

## Pending

- **Phase 1b plan** — author `docs/plans/2026-XX-XX-phase1b-mcp.md` when starting execution.
- **Phase 1b MCP server** — `get_law()`, `search()`, `get_article()` tools per `container-view.md` §7.
- **Phase 2 temporal index** — FR-001.
- **FR-011 G2 triage** of the ~128 degenerate acts before Phase 5 upstream contribution.
