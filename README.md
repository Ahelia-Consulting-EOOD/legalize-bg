# legalize-bg

Bulgarian legislation corpus as Markdown in git. The pipeline scrapes ~3,574 national
legislative acts from lex.bg (bootstrap) and dv.parliament.bg (ongoing amendments),
converts them to Markdown with YAML frontmatter, and stores each amendment as a git
commit with temporal metadata. An MCP server exposes the corpus to Claude Code sessions
for legal research, legislative drafting, and public procurement analysis.

## What This Repo Produces

- ~3,574 Bulgarian legislative acts (394 laws, 24 codes, 2,604 ordinances, 490 regulations, 61 implementing regs) as Markdown + YAML frontmatter
- SQLite temporal index for date-based queries and amendment tracking
- MCP server with tools: `get_law`, `search`, `get_article`, `history`, `diff`
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
# One-time index build (~45s):
python -m index.build --corpus . --db catalog.db

# Run the server:
python -m mcp_server --db catalog.db --corpus .
```

See [Phase 1b.1 operator setup](docs/runbook/2026-05-09-phase1b1-operator-setup.md)
for host configuration and the smoke test.

## Organization

Hosted at [Ahelia-Consulting-EOOD](https://github.com/Ahelia-Consulting-EOOD) on GitHub.

## License

Proprietary. Ahelia Consulting EOOD.
