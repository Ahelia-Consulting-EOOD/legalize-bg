# Runbook: corpus deploy-guard (D-047 parser data-loss)

The MCP server has a startup deploy-guard so a corpus known to be **defective**
(missing definitions / transitional / final provisions) can never be served
unnoticed. This is the Phase 0 interim safety from the D-047 remediation plan
(`docs/plans/2026-06-29-parser-remediation-plan.md`, Task 0).

## What the guard does

At the top of `mcp_server/__main__.py:main()`, before any DB access:

- If `LEGALIZE_CORPUS_DEFECTIVE=1` **and** `LEGALIZE_ALLOW_DEFECTIVE` is not
  `1`, the server logs a refusal and exits with code **2** (does not start).
- The check runs before the `INDEX_MISSING` / `INDEX_STALE` preflight, so the
  refusal wins even when the catalog is present and fresh.

Implementation: `mcp_server/__main__.py::_check_corpus_defective`.
Test: `tests/mcp_server/test_offline_guard.py`.

## Default state

**OFF.** The flag is not set anywhere by default. The guard is a dormant safety
net, not an always-on block. There is no live deployment of the server yet, so
this is latent protection for whenever one is stood up.

## When to SET the flag (`LEGALIZE_CORPUS_DEFECTIVE=1`)

Set it in any environment that serves a corpus you know to be incomplete — for
example, if a future parser or ingest defect is discovered and the corpus is
awaiting a corrective re-bootstrap. This makes "we know the data is wrong"
enforceable rather than tribal knowledge.

## Override for local debugging (`LEGALIZE_ALLOW_DEFECTIVE=1`)

To run the server against a known-defective corpus intentionally (debugging,
reproducing a query, developing a fix), set both:

```bash
LEGALIZE_CORPUS_DEFECTIVE=1 LEGALIZE_ALLOW_DEFECTIVE=1 python -m mcp_server
```

Use the override only for debugging — never in anything a consumer reads.

## Post-remediation status (2026-07-01)

The D-047 corrective re-bootstrap has restored definitions and
transitional/final provisions corpus-wide, so the flag stays **OFF**: the
corpus is trustworthy again. The guard remains in place as reusable protection
for any future corpus-integrity incident.
