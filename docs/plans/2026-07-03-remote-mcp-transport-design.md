# Design: Remote MCP Transport (FR-031)

**Status:** Planning — not execution-ready. No implementation should start against this
document without an owner scope decision on §7 (Open Questions), per this project's own
protected-surfaces discipline.

**Requirement:** FR-031 (`docs/frs/INDEX.md`). **Interlocks with:** FR-029 (MCP per-call
connection model — a hard prerequisite, not a parallel track, see §4). **Precedent:**
FR-028 / D-050 / D-052 (the REST API already solved the identical peer-transport and
per-request-connection problem for HTTP; this design reuses that pattern rather than
inventing a new one).

---

## 1. Problem Statement

Today, `legalize-bg`'s MCP server is reachable exactly one way: a `stdio` subprocess that
an MCP host (Claude Code, Claude Desktop, OpenAI Codex) launches locally and talks to over
stdin/stdout. That covers "local, within a session" and "global on this machine,
persistent" (both now live — see `docs/runbook/2026-05-09-phase1b1-operator-setup.md`
§MCP host configuration; `legalize-bg` is registered at `--scope user` as of 2026-07-03).

It does **not** cover: a Claude Code session on a different machine, a hosted/shared
deployment multiple people or agents can point at, or any client that isn't spawning a
local subprocess. That's "remote" — and right now it doesn't exist as a capability, not
even in prototype form.

## 2. What Already Exists (verified 2026-07-03, not assumed)

- The installed FastMCP version's `FastMCP.run()` signature accepts a `transport` argument
  beyond the default: confirmed via direct introspection, valid values are
  `stdio | http | sse | streamable-http`.
- `mcp_server/__main__.py::main()` calls `handle.mcp.run()` with **zero arguments** —
  always stdio, no `--transport`/`--host`/`--port` flags exist, nothing else was ever
  wired up. This is a from-scratch feature, not a flip-a-flag change.
- The `Dockerfile` (2.x-c packaging) already runs the stdio server in a container; it does
  not expose a port and its `ENTRYPOINT`/`CMD` assume stdio attachment (`docker run -i`).
- `claude mcp add` (the current Claude Code CLI, not the runbook's older manual-JSON
  instructions) already supports `--transport http` / `--transport sse` as a **client-side**
  registration option — the client tooling is ready; only the server side is missing.

## 3. What "remote" actually requires (not just a transport flag)

Four separable concerns, each real work:

1. **Transport selection.** `streamable-http` is the current MCP spec's replacement for
   the older `sse` transport (SSE is being phased out upstream in the MCP ecosystem as of
   this session's knowledge). Default to `streamable-http`; keep `stdio` as the local/global
   default (unchanged) and treat `http`/`sse`/`streamable-http` as opt-in via a new
   `--transport` flag. Do not remove or change stdio behavior — this is purely additive.
2. **Network exposure & authentication.** This is the actual gap, not the transport
   plumbing. Binding `handle.mcp.run(transport="streamable-http", host="0.0.0.0", port=...)`
   with no further work means an unauthenticated client anywhere can read the entire
   corpus. The corpus itself is public-domain legal text (no confidentiality concern per
   se), but unauthenticated write-free read access to a network port still needs at least:
   - A binding decision (localhost-only behind a reverse proxy that terminates
     TLS/auth, vs. the app binding to a public interface directly — the former matches
     how the REST API's own runbook section already recommends deployment, see
     `docs/runbook/...#rest-api-fr-028`, "recommends reverse-proxy-level rate limiting
     before public exposure").
   - A decision on whether ANY auth is required at all (API key header? none, treated as
     public-read like the REST API?) — this is squarely an owner call, not something to
     default silently.
3. **Concurrency / connection model — the actual hard part, and why this is NOT
   independent of FR-029.** The current MCP server serializes every tool call behind one
   process-wide lock (D-040) — "acceptable for the single-stdio-client reality" per
   FR-029's own text, which explicitly names the trigger for revisiting it: *"Pick this up
   only when a concurrent MCP fronting (multi-session host, MCP-over-HTTP) materializes."*
   That trigger is exactly this design. Standing up `streamable-http` transport WITHOUT
   first (or simultaneously) doing FR-029's per-call connection work means every concurrent
   remote client serializes behind the same global lock that was only ever validated
   against one local stdio client — a slow historical `get_law`/`diff` call would stall
   every other remote client's request server-wide. **This design does not proceed without
   FR-029 landing first or alongside it.** FR-029's own text already specifies the shape of
   the fix (`mode=ro` per-thread/per-call connections) — and the REST API (FR-028/D-052)
   already shipped exactly that pattern for HTTP (`api/deps.py:get_conn`, D-051 pragmas).
   Remote MCP should reuse that same connection strategy, not invent a third one.
4. **Rate limiting / abuse protection.** The REST API's own DEFERRED.md row
   (`D-2026-07-02-01`) already flags that body-only search queries (e.g.
   "административни нарушения") measure 5.4–6.5s and are a real repeat-request DoS lever
   once genuinely network-exposed — the REST API's mitigation was "recommend reverse-proxy
   rate limiting, don't build it into the app." The same reasoning applies here, and the
   same open item applies: this is a reverse-proxy/infra concern, not application code, but
   it's a precondition for actually deploying either transport publicly, not an optional
   afterthought.

## 4. Relationship to FR-029 and FR-028 (read together, not separately)

```
FR-029 (per-call connection model)  ──┐
                                       ├──► FR-031 (this design): remote MCP transport
FR-028 / D-050 / D-052 (REST API)   ──┘     reuses both patterns, invents neither
```

- FR-029 supplies the connection-concurrency fix this design cannot ship without.
- FR-028 already proved the pattern works in production (per-request `mode=ro` + D-051
  pragmas, live-verified against the real 3,602-act catalog) — this design's Phase B
  (below) is substantially "do to `mcp_server/__main__.py` what `api/deps.py` already does,"
  not new design work.
- A live open question this design surfaces but does not resolve (see §7): if the REST API
  already gives remote/network callers structured access to the same data, does a
  network-reachable MCP transport add anything beyond "an MCP client elsewhere gets the
  same 7 tool names instead of REST endpoints"? That's a real use case (e.g., a Claude Code
  session on another machine wanting `get_law`/`history`/`diff` as MCP tools, not HTTP
  calls it has to wrap itself) but it should be named explicitly as the justification, not
  assumed.

## 5. Non-Goals (explicitly out of scope for this design)

- Changing MCP tool signatures or the `tools.json` contract — none of this touches Surface
  (protected surface `mcp_server/server.py (tool signatures)`); transport is orthogonal to
  the tool API.
- Changing the stdio local/global path in any way — additive only, per §3.1.
- Building the reverse-proxy/TLS/rate-limiting infrastructure itself — same posture as the
  REST API's runbook: name the requirement, defer the infra build to deployment time.
- Solving FR-029 inside this document — that's its own FR with its own plan; this design
  only establishes that it's a hard dependency, not a nice-to-have.

## 6. Phasing (tentative — depends on §7 decisions)

**Phase A — FR-029 lands** (prerequisite, not part of this FR's task count). Per-call
`mode=ro` connections replace the D-040 global lock. Existing stdio single-client behavior
must remain byte-identical (regression risk: the lock currently also serializes some
non-DB-bound work — verify exactly what it wraps before removing it, per FR-029's own
text: "the lock wraps entire tool bodies... git subprocesses, 1MB body reads included").

**Phase B — Transport flag, local-only testing.** Add `--transport {stdio,http,sse,
streamable-http}` `--host` `--port` to `mcp_server/__main__.py`; default remains stdio
(zero behavior change for existing local/global users). Test `streamable-http` bound to
`127.0.0.1` only — no network exposure yet. TDD: a test that starts the server on
`streamable-http`, connects an MCP client over HTTP, and runs the same smoke sequence
Task 9 of the FR-028 plan used for REST (`get_law`/`search`/`get_article`/history/diff
against a real fixture corpus).

**Phase C — Auth + exposure decision, network-reachable deployment.** Depends entirely on
§7's owner decisions. Likely mirrors the REST API's `legalize-bg-api --cors-origin` /
reverse-proxy pattern: `legalize-bg-mcp --transport streamable-http --host 0.0.0.0 --port
... ` behind a proxy that terminates TLS and (if the owner decides auth is needed) an API
key or similar.

**Phase D — Docs + runbook.** New "Remote MCP (FR-031)" section in the operator runbook,
parallel to the existing "REST API (FR-028)" section; update `docs/sync/DECISIONS.md` with
the ratified transport/auth choice as a new D-0NN row.

## 7. Open Questions for the Owner (blocking Phase B+ execution)

1. **Is remote MCP actually needed, given the REST API already ships?** Name the concrete
   use case (a specific remote MCP client/session that needs the 7 MCP tools specifically,
   not REST) before committing engineering time — see §4's live question.
2. **Auth strategy** — none (public read, matching the REST API's current posture), a
   shared API key, or something else? This gates all of Phase C.
3. **Hosting target** — same host as the REST API (natural, since both would share
   `catalog.db` and the corpus checkout), or separate? Affects the reverse-proxy design.
4. **Priority relative to FR-029** — FR-029 is currently `Backlog, Low` priority with an
   explicit "on demand" trigger. This design IS that trigger firing. Does the owner want to
   promote FR-029 now, or table this whole design until FR-029 is picked up on its own
   schedule?

No code should be written against Phase B until at least Q1, Q2, and Q4 have owner answers
— Q3 can be deferred to Phase C planning.
