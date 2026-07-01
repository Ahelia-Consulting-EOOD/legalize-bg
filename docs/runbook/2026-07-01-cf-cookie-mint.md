# Runbook: minting a Cloudflare `cf_clearance` cookie for the re-scrape (D-047 Task 9)

The corrective re-bootstrap fetches lex.bg through `RateLimitedSession(cookie_path=...)`,
which replays a real-browser-minted `cf_clearance` cookie. Cloudflare clearances are
bound to (IP + User-Agent) and expire (~30 min typical), so a multi-hour full run needs
the cookie **re-minted** a few times. This is the operator loop.

## Cookie file schema

The session reads a JSON file (kept OUT of git — it holds a live token; store under the
session scratchpad, never in the repo):

```json
{
  "user_agent": "Mozilla/5.0 (Macintosh; ...) Chrome/149.0.0.0 Safari/537.36",
  "cf_clearance": "<token>",
  "cookies": { "cf_clearance": "<token>", "lex_session": "...", "PHPSESSID": "..." }
}
```

The `user_agent` MUST be the exact UA of the browser that solved the challenge — a
mismatch invalidates the clearance. `Accept-Encoding` is forced to `gzip, deflate` by the
client (never `br`: `requests` can't decode brotli without the package and silently
corrupts the cp1251 body).

## Mint / re-mint procedure (agent-time, via Playwright MCP)

1. Run this in `browser_run_code_unsafe` (navigates, waits for the CF managed challenge to
   auto-clear in the real browser, returns the full jar + UA):

   ```js
   async (page) => {
     await page.goto('https://lex.bg/laws/ldoc/2135802037', { waitUntil: 'domcontentloaded' });
     let cleared = false;
     for (let i = 0; i < 25; i++) {
       const t = await page.title().catch(() => '');
       if (t && !/just a moment/i.test(t)) { cleared = true; break; }
       await page.waitForTimeout(1000);
     }
     const ua = await page.evaluate(() => navigator.userAgent);
     const cookies = await page.context().cookies('https://lex.bg');
     const jar = {}; for (const c of cookies) jar[c.name] = c.value;
     return JSON.stringify({ cleared, user_agent: ua,
       cf_clearance: jar['cf_clearance'] || null, cookies: jar });
   }
   ```

   (Playwright's VM has no `fs`/`import` — it returns the jar as text; the agent writes the
   file itself. Do not rely on writing from inside the snippet.)

2. `Write` the returned `{user_agent, cf_clearance, cookies}` to the cookie file path.

3. Verify the handoff once with `scratchpad/spike_handoff.py` (expects
   `status 200 · challenged=false · has_Article=true`).

## When to re-mint during a run

`refresh.py` logs, on a CF challenge:

```
CLOUDFLARE challenge at <url> — pausing; awaiting fresh cf_clearance in <cookie file>. Waiting up to 900s.
```

That is the signal: run steps 1–2 above to overwrite the cookie file with a fresh token.
The running session polls the file every 15 s, detects the changed `cf_clearance`, reloads
it, and resumes at <=1 req/s from where it paused. No process restart needed. If no fresh
cookie appears within `--cookie-wait` seconds it halts (D-011); relaunch resumes from
`.refresh-state.json` (loses at most the in-flight act).

## Constraints (non-negotiable)

- <=1 req/s (enforced by `RateLimitedSession`).
- D-011: this is stop-and-wait-for-a-fresh-legitimate-browser-cookie, NOT an automated
  challenge solver. Never add a header-spoofing / cloudscraper bypass here.
- D-039: fetch texts only; build our own structure.
