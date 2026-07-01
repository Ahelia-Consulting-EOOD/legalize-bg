# legalize-bg follow-ups

Durable records of deferred findings (issues discovered in passing, out of scope for the current change).
One line per follow-up, newest first.

- [Fetcher hard-stops on Cloudflare; CF-clearing not integrated](2026-07-01-fetcher-cloudflare-clearing.md) - lex.bg now serves a Cloudflare JS challenge; the working `cf_clearance` workaround is a manual forensics script, not wired into `fetcher/bg` or the refresh path. Recommends a browser-assisted CF-clearing helper.
