# legalize-bg

Bulgarian legislation as code — ~3,574 national legislative acts as Markdown+YAML in git, with MCP server for Claude Code access.

## Session Startup Protocol

1. Read this file
2. Read `docs/sync/ACTIVE.md` for current work state
3. Read `docs/sync/DEFERRED.md` for items punted from prior phases that may be relevant to current work
4. Read `docs/process/delivery-contract.md` for process rules
5. Read the relevant `docs/prd/` or `docs/plans/` for task context

## Authority Surfaces (in precedence order)

1. Direct user instruction
2. `docs/process/delivery-contract.md`
3. `docs/process/OWNER-DIRECTIVES.md`, `COVERAGE-FLOOR.md`
4. `docs/architecture/`
5. `docs/prd/`
6. `docs/plans/`

## Key Technical Facts

- lex.bg encoding: windows-1251 (decode as `cp1251`, NOT UTF-8)
- lex.bg URL pattern: `https://lex.bg/laws/ldoc/{doc_id}`
- lex.bg tree: `https://lex.bg/laws/tree/{category}/{page_index}` (0-based)
- Categories: `laws` (12 pages), `code` (1), `ords` (75), `regs` (14), `reg_laws` (2)
- Rate limit: 1 request/second to lex.bg
- No Playwright needed — all content is server-rendered HTML
- Total acts: ~3,574

## Commit Conventions

- `[bootstrap]` — initial scrape from lex.bg
- `[reforma]` — ZID (amendment)
- `[nova]` — new law
- `[otmyana]` — full repeal
- `[popravka]` — corrigendum

Commit message must include: `Source-Id`, `Source-Date`, `Norm-Id`

## Legalize SPEC

8 mandatory YAML frontmatter fields: `titulo`, `identificador`, `pais`, `rango`, `fecha_publicacion`, `ultima_actualizacion`, `estado`, `fuente`

## Protected Surfaces

Changes to these require IMPLEMENTATION-PREFLIGHT:
- YAML frontmatter schema
- Legalize `fetcher/bg/` interfaces
- MCP tool signatures
- SQLite schema
- Commit message format

## Quality Gates

- All YAML frontmatter must validate against schema
- Markdown must preserve article/chapter/section structure
- Consolidation output must validate against lex.bg oracle
- Legalize hard gates must pass before upstream PR

## Key File Paths

| Path | Purpose |
|------|---------|
| `docs/prd/legalize-bg-prd.md` | Product requirements |
| `docs/plans/2026-04-19-legalize-bg-design.md` | Design doc (historical) |
| `docs/plans/2026-04-20-doc-dev-plan.md` | Documentation dev plan |
| `docs/architecture/` | System architecture (arc42/C4) |
| `docs/process/delivery-contract.md` | Process contract |
| `docs/process/OWNER-DIRECTIVES.md` | Non-negotiable directives |
| `docs/process/COVERAGE-FLOOR.md` | Completeness requirements |
| `docs/process/IMPLEMENTATION-PREFLIGHT.md` | Preflight checklists |
| `docs/frs/INDEX.md` | Future requirements backlog |
| `docs/data/canonical-data-model.md` | Domain entity explanations |
| `docs/data/schema-reference.md` | YAML + SQLite schema |
| `docs/testing/test-strategy.md` | Test layers and acceptance criteria |
| `docs/sync/ACTIVE.md` | Current work state |
| `docs/sync/DECISIONS.md` | Decision log |
| `.ahelia/repo-profile.yaml` | Machine-readable repo profile |
