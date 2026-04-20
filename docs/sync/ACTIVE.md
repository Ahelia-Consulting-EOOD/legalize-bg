# Active Work

**Current phase:** Phase 1a (bootstrap scrape)
**Current owner:** ekimir
**Started:** 2026-04-20
**Next action:** Run Task 11 — full bootstrap on `bootstrap/phase-1a` branch with `--push-every 250`.

## Status

Phase 1a pipeline is code-complete and verified:

- `fetcher/bg/` implements the 4 Legalize interfaces: `LegislativeClient` (client), `NormDiscovery` (discovery), `TextParser` (text_parser), `MetadataParser` (metadata).
- `index/catalog.py` provides the SQLite schema and insert/query surface.
- `bootstrap.py` orchestrates the full pipeline: crawl → dedup → fetch → parse → commit → (optional) push → index.
- Transport layer hardened per delivery-contract §Rate Limiting Protocol: global 1 req/sec ceiling, 3× exp backoff on 429/5xx, `CloudflareChallenge` exception on CF markers, per-request INFO logging.
- 6 representative HTML fixtures cover all 5 corpus categories. 59 automated tests pass.

Post–code-review fixes (session 2026-04-20):

- **C1-C3** — Retry/logging/Cloudflare detection centralized in `RateLimitedSession`.
- **I1** — ELI URI now uses `/eli/bg/{rango}/{Y}/{M}/{D}/{ascii-slug}/con`; slug unified with filename via `assembler.generate_slug`.
- **I2** — `_unique_slug` dedups same-run slug collisions with `-N` suffix.
- **I3** — Removed dead `CATEGORY_SLUG_TO_DIR` from metadata.
- **I4** — Missing-metadata edge cases tested; bootstrap WARN-logs null mandatory fields.
- **I5** — 4 additional fixtures + parametrized cross-category smoke test.
- **I6** — Amendment history test asserts non-null parsed dates.
- **I7** — Alinea paragraphs joined with `\n\n` (CommonMark paragraph break).
- Cross-category doc_id dedup in `CatalogCrawler.crawl_all` removes 104 Конституция sidebar duplicates.
- `--branch` and `--push-every` flags added for incremental remote delivery.

Dry run completed 2026-04-20: 104 tree pages in ~2 minutes, no retries, no CF challenges. `catalog.json` snapshot committed. Per-category counts match `COVERAGE-FLOOR.md` targets to within 1 act (3,573 unique acts vs target ~3,574).

## Blockers

None.

## Pending

- Task 11: full bootstrap run (~2 hours, ~3,573 act fetches + commits, periodic pushes every 250 commits).
- Spot-check 10 random acts against lex.bg after Task 11 (Definition of Done, Phase 1a).
- Update this file to Phase 1b once Task 11 verifies.
