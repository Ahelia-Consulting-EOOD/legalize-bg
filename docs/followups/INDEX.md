# legalize-bg follow-ups

Durable records of deferred findings (issues discovered in passing, out of scope for the current change).
One line per follow-up, newest first.

- [`numbered_key` reads a cited regulation's number as the act's own](2026-09-05-numbered-key-borrowed-from-a-cited-regulation.md) - 3 of 1,987 keyed corpus acts carry a key borrowed from a Регламент (ЕО) № their title cites; contained by the floor, the digit guard and `content_mismatch`; fix by binding the number to the act-type noun
- [One act's frontmatter comment is not round-trippable](2026-09-06-frontmatter-comment-is-not-round-trippable.md) - the САБ правилник carries a five-line YAML comment recording why its `estado` is `derogado`; it is the only act of 3,624 that does not round-trip through the write gate's renderer, and the first corpus-wide backfill deletes it silently.
- [The `corpus-integrity` job must become a required status check on `main`](2026-09-06-corpus-integrity-required-check.md) - the CI job exits non-zero on any violation, stale waiver or count drift, but a failing job blocks no merge until it is listed in the branch protection rules; an owner setting, not a code change, and Directive 12 is not satisfied by the job alone.
- [Six unregistered defect classes registered as FR-037 to FR-042](2026-09-05-unregistered-defect-classes.md) - fabricated anchors (C1), ambiguous addresses (C5), un-hashed headings (C6), record truthfulness (C8), cross-reference capture (C9), lex.bg source omissions; measurements carried over from gitignored rescue files, verification status per row.
- [Fetcher hard-stops on Cloudflare; CF-clearing not integrated](2026-07-01-fetcher-cloudflare-clearing.md) - lex.bg now serves a Cloudflare JS challenge; the working `cf_clearance` workaround is a manual forensics script, not wired into `fetcher/bg` or the refresh path. Recommends a browser-assisted CF-clearing helper.
