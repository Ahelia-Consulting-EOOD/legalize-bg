# legalize-bg follow-ups

Durable records of deferred findings (issues discovered in passing, out of scope for the current change).
One line per follow-up, newest first.

- [Six unregistered defect classes registered as FR-037 to FR-042](2026-09-05-unregistered-defect-classes.md) - fabricated anchors (C1), ambiguous addresses (C5), un-hashed headings (C6), record truthfulness (C8), cross-reference capture (C9), lex.bg source omissions; measurements carried over from gitignored rescue files, verification status per row.
- [Fetcher hard-stops on Cloudflare; CF-clearing not integrated](2026-07-01-fetcher-cloudflare-clearing.md) - lex.bg now serves a Cloudflare JS challenge; the working `cf_clearance` workaround is a manual forensics script, not wired into `fetcher/bg` or the refresh path. Recommends a browser-assisted CF-clearing helper.
