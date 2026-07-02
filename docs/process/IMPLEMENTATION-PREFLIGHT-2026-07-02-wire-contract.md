# Preflight: Batch B — MCP wire contract (Tasks 5-8)

Filed 2026-07-02 (pre-UI hardening plan, `docs/plans/2026-07-02-pre-ui-hardening-plan.md`).
Template: `docs/process/IMPLEMENTATION-PREFLIGHT.md` §"Approval Template". Mirrors the
structure of `docs/process/IMPLEMENTATION-PREFLIGHT-2026-06-21-fr018.md`.

This is ONE preflight covering four additive changes to the MCP surface, executed as
Tasks 5-8 of the plan. They are batched here — rather than filed one per task — because
all four touch the same protected surface (3), share one owner sign-off event (the
2026-07-02 review session, D-050), and are individually too small to warrant separate
preflight ceremony. Each task still gets its own TDD cycle and commit.

- **protected surface:** 3 (MCP Tool Interface Changes)
- **authoritative source:** `.ahelia/protected-surfaces.yaml` (`mcp_server/server.py (tool
  signatures)`) + `docs/process/IMPLEMENTATION-PREFLIGHT.md` §"Protected Surface 3" +
  `docs/plans/2026-05-09-phase1b-mcp-design.md` §8 (error taxonomy).
- **hard constraint confirmed:** yes. Existing published tool signatures and response
  shapes (D-024) must not have breaking changes; new tools may be added freely;
  additive-only changes to responses; error codes additive-only (D-026).

## What is changing (as one batch)

**(a) Error wire format becomes JSON (Task 5).** `mcp_server.errors.ToolError` currently
subclasses plain `Exception`; FastMCP's `call_tool` only passes `fastmcp.exceptions.
FastMCPError` subclasses through unwrapped (`except FastMCPError: raise`) and otherwise
re-wraps the exception into masked/templated text. Because our `ToolError` isn't a
`FastMCPError`, its structured payload was flattened to Python dict-repr prose
(`"CODE: {'key': 'value'}"`, single-quoted, not valid JSON) before it ever reached a real
MCP client (P0-1, review 2026-07-02). The fix: subclass `fastmcp.exceptions.ToolError`
(which passes through unwrapped) and make `str(e)` be
`json.dumps({"code": ..., **payload}, ensure_ascii=False)`. Same codes, same payload
fields, same `.code`/`.payload`/`.to_dict()` — only the wire *encoding* of the message
text changes, from prose to parseable JSON. Purely additive/behavioral: no code removed,
no payload field removed.

**(b) `INDEX_STALE`/`INDEX_MISSING` become genuinely tool-raised (Task 6).** Today these
two codes exist in `ERROR_CODES` and are documented in `docs/api/error-codes.md`/
`error-codes.json` with `raised_by` listing specific tools, but no tool actually raises
them — there is no runtime staleness/missing-index check wired into any tool's code path.
Task 6 wires a real check (comparing `laws.current_commit` against working-tree HEAD, and
checking `catalog.db` exists with the expected tables) into the tools that read from the
index, and corrects the docs' `raised_by` list to name exactly the tools that now raise
each code (rather than the aspirational list written in Phase 1b.1 before the check
existed). No new code; no signature change; a doc correction plus a genuine behavior
addition.

**(c) New additive error code `INVALID_DATE` (Task 7).** A new code for malformed date
strings passed to any date-taking parameter (distinct from `NO_VERSION_AT_DATE`, which
fires for well-formed dates outside the act's version range, and `INVALID_DATE_RANGE`,
which fires when `from > to`). Purely additive to `ERROR_CODES` — no existing code
changes meaning.

**(d) Real field-level `output_schema` for all tools (Task 8).** Tool responses are
currently typed as Python dataclasses/TypedDicts at the source level (D-024) but
`tools.json`'s exported schema for each tool's output is a loose/untyped placeholder.
Task 8 derives a real JSON Schema per tool from its TypedDict response annotation, so
`tools.json` accurately documents field names and types for non-Python clients. This is
the trigger for the version bump: `mcp_server/export_tools.py:TOOLS_JSON_VERSION`
`1.2.0` → `1.3.0`. Response *shapes* are unchanged — this only makes the already-existing
shape visible in the exported schema. No field removed, no required input added, no tool
renamed. Client-visible side effect: once a tool has a field-level output schema,
`fastmcp.Client`'s `result.data` auto-hydrates into a synthesized typed object (fastmcp's
`Root` model) instead of a plain dict/list-of-dicts; `result.structured_content` remains
the raw wire-format dict/list, unaffected — any Python client relying on `.data` being a
plain `dict`/`list` (as the four in-repo e2e round-trip tests did) needs to switch to
`.structured_content` or accept attribute access on the hydrated object.

## Violation risk

None of (a)-(d) rename a parameter, change a return-type structure by removing/renaming a
field, remove a tool, make a previously optional parameter required, or remove a code
from the taxonomy — the exhaustive violation list in Protected Surface 3. (a) changes
*only* the string encoding of an already-thrown exception's message (the structured data
itself — `code` + payload — is unchanged and was already present in `to_dict()`). (b)
adds behavior under codes that were already documented as part of the taxonomy since
Phase 1b.1; no consumer could have depended on them never firing, since nothing published
promised they wouldn't. (c) is a new code, explicitly allowed. (d) only adds schema
detail; it does not change what a tool accepts or returns. Net risk: **low**.

Downstream consumers (ZOP / contracts / rfp-response / legislative-draft skills, and any
external MCP client) that currently do fragile substring-matching on the old
`"CODE: {...}"` prose format will need to switch to `json.loads(str(e))["code"]` —
called out explicitly here since it's the one behavior change with external visibility.
No such consumer exists in this repo (the only in-repo consumer was the test suite,
updated in Task 5 Step 5); this is a heads-up for any downstream skill maintained
elsewhere.

## Version bump note

Per `docs/api/error-codes.md`'s versioning policy, `error-codes.md`/`error-codes.json`'s
`version` field is kept in lockstep with `TOOLS_JSON_VERSION`
(`tests/mcp_server/test_error_codes_doc.py::test_md_and_json_versions_match` enforces
this three-way equality). `TOOLS_JSON_VERSION` is currently `1.2.0` and is scoped to move
to `1.3.0` only at the end of this batch, in Task 8 (item (d) above — the schema work is
the substantive trigger for the version bump). Tasks 5-7 therefore add documentation and
behavior (new "Wire format" section; corrected `raised_by`; new `INVALID_DATE` code/
section) without bumping the version number, to avoid desyncing the three-way parity
check ahead of Task 8's bump. This is a sequencing detail, not a scope change: by the end
of Batch B the version will read `1.3.0` and will document all of (a)-(d).

## Scope confirmation

- **allowed scope confirmed:** yes — (a) is a behavioral/encoding change with no
  signature/shape impact; (b) is a doc correction + wiring already-documented codes;
  (c) is a new error code (additive); (d) is schema enrichment (additive). None require a
  waiver under Surface 3's "allowed scope" (adding new tools, optional parameters,
  additive response fields, additive error codes).
- **waiver required:** **no.** No breaking change to a published interface; no error-code
  removal; no tool rename; no previously-optional parameter made required.
- **owner confirmation:** ekimir — via the 2026-07-02 comprehensive code-review session
  that verified P0-1 and approved the 18-task pre-UI hardening plan (D-050,
  `docs/research/2026-07-02-pre-ui-code-review.md`,
  `docs/plans/2026-07-02-pre-ui-hardening-plan.md`).
- **implementation may proceed:** yes (TDD per task; each of Tasks 5-8 gets its own
  commit and full-suite gate; this preflight covers all four so they don't each need a
  separate preflight doc).
