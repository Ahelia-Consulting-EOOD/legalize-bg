# Preflight: Task 1 — REST API v1 surface registration (FR-028)

Filed 2026-07-02 (FR-028 REST API plan, `docs/plans/2026-07-02-fr028-rest-api-plan.md`).
Template: `docs/process/IMPLEMENTATION-PREFLIGHT.md` §"Approval Template". Mirrors the
structure of `docs/process/IMPLEMENTATION-PREFLIGHT-2026-07-02-wire-contract.md`.

This preflight covers one additive change: registration of a new protected surface
(REST API v1 endpoint contract) and internal relocation of shared query helpers from
the MCP server to a public queries module. No changes to existing surfaces; no breaking
changes to existing tools.

- **new protected surface:** REST API v1 Endpoint Contract (Phase 7.1, legalize-bg-web integration)
- **authoritative source:** `.ahelia/protected-surfaces.yaml` (new entry) + 
  `docs/plans/2026-07-02-fr028-rest-api-plan.md` + `docs/sync/DECISIONS.md` D-052 
  (REST API error mapping).
- **hard constraint confirmed:** yes. The 7 public REST endpoints (GET /api/v1/laws, 
  /laws/{slug}, /laws/{slug}/articles/{art}, /laws/{slug}/history, /laws/{slug}/diff, 
  /search, /stats) and their error taxonomy (D-052) form a binding contract with the 
  legalize-bg-web frontend (Next.js). Renaming/removing an endpoint or changing a 
  response field breaks the frontend; additive changes (new endpoints, new optional 
  fields) are allowed.

## What is changing

**(a) New protected surface "REST API v1 endpoint contract" registered.** The 7 public 
endpoints and their error taxonomy (D-052: application/json error bodies with code, 
message, detail fields) are registered as a new protected surface in 
`.ahelia/protected-surfaces.yaml`. This surface is additive: no existing surface is 
modified. The REST API acts as a peer to the MCP server, both consuming the same 
internal query layer (`mcp_server/queries.py`).

**(b) Internal relocation of shared query helpers.** Four utility functions are moved 
from `mcp_server/server.py` to public names in `mcp_server/queries.py`:
  - `_law_meta` → `law_meta` (a plain SQL `SELECT * FROM laws WHERE law_id = ?` —
    reads the act's metadata row from the SQLite catalog; no Markdown/YAML parsing)
  - `_read_law_markdown` → `read_law_markdown` (loads the raw Markdown text for a
    law at a given commit — a working-tree file read, or `git show` for a
    historical commit; it does not parse the file, that's `split_frontmatter`'s job)
  - `_split_frontmatter` → `split_frontmatter` (parse YAML frontmatter from raw text)
  - `_iso` → `iso_date` (format date/datetime as ISO 8601 string)

These functions are implementation details of the query layer, not part of the MCP tool 
surface. Relocating them to a shared module enables the REST API to reuse the same 
parsing logic as the MCP server, avoiding duplication. The MCP tool signatures, response 
shapes, and error behavior remain unchanged — this is a refactor internal to the server, 
not a Surface-3 event.

**(c) MCP server untouched; SQLite schema untouched.** The MCP server's `server.py` 
continues to import and call the relocated functions (from `queries.py` instead of local 
scope). No tool signature changes, no error-code changes, no behavior changes. All queries 
are read-only SELECTs against the existing SQLite schema.

## Violation risk

None of (a)-(c) modify an existing protected surface or break a published interface. 
(a) adds a new surface (allowed). (b) relocates internal helper functions that are not 
part of any published tool signature or MCP protocol contract (allowed; existing test 
suite guards the MCP tool behavior). (c) guarantees no schema changes. Net risk: **none**.

## Scope confirmation

- **allowed scope confirmed:** yes — (a) is a new surface registration (additive); 
  (b) is an internal refactor (functions are not published tool names or fields); 
  (c) guarantees schema stability.
- **waiver required:** **no.** No breaking change to an existing protected surface; 
  no tool rename; no signature change; no error-code removal.
- **owner confirmation:** ekimir — via the 2026-07-02 review session (D-050, scope 
  decision (1): "REST API in legalize-bg repo per approved Phase-7 design") and the 
  owner's explicit plan approval of `docs/plans/2026-07-02-fr028-rest-api-plan.md` 
  (9-task execution-ready plan for FR-028 REST API).
- **implementation may proceed:** yes (TDD per task; Task 1 establishes the surface 
  registration and dependency setup; subsequent tasks add application code).
