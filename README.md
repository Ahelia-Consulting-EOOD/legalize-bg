# legalize-bg

Bulgarian legislation corpus as Markdown in git. The pipeline scrapes ~3,574 national
legislative acts from lex.bg (bootstrap) and dv.parliament.bg (ongoing amendments),
converts them to Markdown with YAML frontmatter, and stores each amendment as a git
commit with temporal metadata. An MCP server exposes the corpus to Claude Code sessions
for legal research, legislative drafting, and public procurement analysis.

## What This Repo Produces

- ~3,574 Bulgarian legislative acts (394 laws, 24 codes, 2,604 ordinances, 490 regulations, 61 implementing regs) as Markdown + YAML frontmatter
- SQLite temporal index for date-based queries and amendment tracking
- MCP server with 7 tools: `get_law`, `search`, `get_article`, `get_articles`, `history`, `amendments_in_period`, `diff`
- Git history where each commit represents one legislative amendment event

## Audience

- **Claude Code sessions** -- primary consumer via MCP tools
- **Ahelia Consulting developers** -- pipeline maintenance, corruption research tooling
- **Legalize upstream contributors** -- fetcher/bg/ interfaces for the legalize-dev ecosystem

## Data Sources

| Source | Role |
|--------|------|
| lex.bg | Bootstrap scrape (consolidated texts) and validation oracle |
| dv.parliament.bg | Ongoing amendments (Tue/Fri gazette issues) |
| Municipal websites | Phase 6+ (Sofia first) |

## Legalize Ecosystem

This repo implements `fetcher/bg/` interfaces for the
[legalize-dev](https://github.com/legalize-dev) ecosystem (25 countries, 400K+ norms).
Bulgaria is not yet covered upstream. The Ahelia repo hosts the private layer: MCP
server, SQLite index, consolidation engine, and municipal pipeline.

## Authority Surfaces

| Document | Path |
|----------|------|
| Delivery contract | `docs/process/delivery-contract.md` |
| Owner directives | `docs/process/OWNER-DIRECTIVES.md` |
| Coverage floor | `docs/process/COVERAGE-FLOOR.md` |
| Product requirements | `docs/prd/legalize-bg-prd.md` |
| Architecture | `docs/architecture/` |
| Design document (historical) | `docs/plans/2026-04-19-legalize-bg-design.md` |
| Current work state | `docs/sync/ACTIVE.md` |
| Machine-readable constraints | `.ahelia/constraint-profile.yaml` |
| Protected surfaces | `.ahelia/protected-surfaces.yaml` |

## Project Status

**Phase:** Phase 1b.1 (MCP server) shipping 2026-05-09.

- Phase 1a (bootstrap, 3,573 acts) — **complete** on `main`.
- Phase 1b.1 (MCP server with `get_law` / `search` / `get_article`) —
  **complete**. See [the operator setup
  runbook](docs/runbook/2026-05-09-phase1b1-operator-setup.md) and
  [Phase 1b design](docs/plans/2026-05-09-phase1b-mcp-design.md).
- Phase 1b.2 (structured backend hardening) and 1b.3 (operator polish
  + Bulgarian stemmer) — next.

See the design document for the full 6-phase roadmap and risk register.

## MCP Server

The `mcp_server/` package exposes the corpus to Claude Code, Claude
Desktop, and OpenAI Codex via Model Context Protocol over stdio.

```bash
# One-time index build:
python -m index.build --corpus . --db catalog.db

# Run the server:
python -m mcp_server --db catalog.db --corpus .
```

Or via Docker (`Dockerfile` carries only the app; corpus + `catalog.db`
are mounted at runtime):

```bash
docker build -t legalize-bg-mcp .
docker run --rm -i -v "$PWD:/corpus" legalize-bg-mcp \
    --db /corpus/catalog.db --corpus /corpus
```

See [the operator runbook](docs/runbook/2026-05-09-phase1b1-operator-setup.md)
for host configuration, the Docker index-build step, deploy guards, and
the smoke test.

## REST API

The `api/` package exposes a FastAPI REST surface (FR-028) over the same
shared query layer as the MCP server, for the `legalize-bg-web` Next.js
frontend (sister repo, Phase 7.2) or any other HTTP client: 7 endpoints
(`/api/v1/laws`, `/laws/{slug}`, `/laws/{slug}/articles/{art}`,
`/laws/{slug}/history`, `/laws/{slug}/diff`, `/search`, `/stats`) plus
`/healthz` and `/api/v1/metrics`, with per-request read-only SQLite
connections (no MCP-lock inheritance), CORS, and an OpenAPI contract
locked at `docs/api/openapi-rest.json`.

```bash
# One-time index build (see MCP Server section above), then:
legalize-bg-api --db catalog.db --corpus . --port 8228
```

See [the operator runbook](docs/runbook/2026-05-09-phase1b1-operator-setup.md#rest-api-fr-028)
for the full endpoint table, error mapping (D-052), and CORS setup.

## Organization

Hosted at [Ahelia-Consulting-EOOD](https://github.com/Ahelia-Consulting-EOOD) on GitHub.

## License

Proprietary. Ahelia Consulting EOOD.
