# IMPLEMENTATION-PREFLIGHT — CF-clearance fetch path (D-047 Phase 3, Task 9)

Date: 2026-07-01 · Surface: **Protected Surface 1 (`fetcher/bg/` — `RateLimitedSession` / `HttpTransport` contract)**
Plan: `docs/plans/2026-06-29-parser-remediation-plan.md` (Task 9) · Decision: D-047 (CF addendum) · Related: D-011, D-039

---

## Preflight: give `RateLimitedSession` a Cloudflare-clearance layer for the corrective re-bootstrap

- **protected surface:** 1 — `fetcher/bg/client.py`, the `RateLimitedSession` / `HttpTransport` / `LexBgClient` transport contract that `bootstrap.py` and `refresh.py` fetch through.
- **authoritative source:** project CLAUDE.md ("lex.bg encoding cp1251; 1 req/sec; stop on CF"); `docs/process/delivery-contract.md` §Rate Limiting Protocol; D-011 (stop on Cloudflare, never retry-to-defeat).
- **hard constraint confirmed:** yes — existing public signatures are UNCHANGED: `RateLimitedSession.get_bytes(url) -> bytes`, `HttpTransport.get(doc_id) -> bytes`, `LexBgClient.fetch/fetch_soup`. The 1 req/s ceiling, 3-retry/backoff on 429/5xx, and CF-detection markers are all preserved.
- **what changes:** `RateLimitedSession.__init__` gains three OPTIONAL params — `cookie_path` (JSON file of `{user_agent, cf_clearance, cookies}` minted by a real browser via the Playwright MCP), `cookie_wait_sec` (default `0.0` = OFF), `cookie_poll_sec`. When `cookie_path` is set: the session sends the minted UA + cookie jar and `Accept-Encoding: gzip, deflate` (never `br` — `requests` cannot decode brotli without the package, which silently corrupted body decode in the spike). New internal methods `_load_cookies()` and `_await_fresh_cookie()`.
- **behaviour change (bounded, opt-in):** on a Cloudflare challenge, IF `cookie_wait_sec > 0`, the session PAUSES and polls `cookie_path` for a **changed** `cf_clearance` (an out-of-band Playwright re-mint), reloads it, and retries the request; if none arrives within `cookie_wait_sec` it raises `CloudflareChallenge` (unchanged halt). With the defaults (`cookie_path=None`, `cookie_wait_sec=0.0`) behaviour is **byte-identical to today** — CF raises immediately, no retry.
- **D-011 reconciliation:** D-011 forbids *retrying to defeat* Cloudflare (hammering the challenge with an automated solver). This change does the opposite: it **stops scraping** on challenge and **waits for a fresh, legitimately browser-minted cookie** supplied out-of-band, then resumes at ≤1 req/s. No challenge-solver, no header spoofing beyond the real browser's own UA, no sub-second retry. Owner approved the Playwright auto-mint refresh (2026-07-01). This is a compliant refinement of "stop on CF", recorded as a D-047 CF addendum.
- **violation risk:** LOW for the interface (signatures + defaults stable). Residual risk is operational (cookie expiry mid-run) — mitigated by the wait-for-refresh loop + `refresh.py`'s existing per-act `.refresh-state.json` checkpoint (resume loses at most the in-flight act).
- **allowed scope confirmed:** yes — additive, opt-in transport capability that lets the sanctioned corrective re-bootstrap (D-047/D1) actually reach lex.bg, which is currently CF-gated. No frontmatter/schema/commit-format/MCP surface touched.
- **waiver required:** no.
- **regression protection:** existing `tests/fetcher/bg/test_transport.py` must stay green (defaults unchanged); new tests for (1) cookie/UA load, (2) wait-for-refresh reload+retry on CF, (3) CF still raises when wait is disabled. ToS/D-039: texts only, ≤1 req/s.
- **rollback:** revert the client commit; the params are optional so nothing else regresses.
- **owner confirmation:** ekimir / 2026-07-01 (approved Playwright auto-mint cookie source).
- **implementation may proceed:** yes
