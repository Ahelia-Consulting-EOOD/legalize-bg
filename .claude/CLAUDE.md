# legalize-bg

Bulgarian legislation as code — 3,624 national legislative acts (counted 2026-09-05; live count in `docs/sync/CORPUS-STATUS.json`) as Markdown+YAML in git, with MCP server and REST API for Claude Code and web access.

**Source model (D-059, 2026-09-05):** Държавен вестник is the source of truth wherever its text exists online; lex.bg is a base snapshot and a witness, never truth. Every act carries a provenance grade (A ДВ-complete, B ДВ-audited snapshot, C pre-1989 base). Corpus `.md` files are written only by the pipeline (`refresh.py` and `bootstrap.py` today; the single write gate of PR #23 Part IV will make this structural); never hand-edit, never hand-commit a corpus file.

**DRS topology:** this repo is the S5 surface of the DRS topology (oversight `registry/topology/drs.yaml`). Consumers poll `docs/sync/CORPUS-STATUS.json` and detect per-act freshness by frontmatter `ultima_actualizacion` (D-048), never by git dates. `/sync-drs` run from any DRS repo reads those surfaces read-only.

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
- Rate limit: 1 request/second to lex.bg and to dv.parliament.bg
- lex.bg is Cloudflare-gated on `/laws/ldoc/*`; a challenge is a deliberate halt, cookie minting is interactive (see `docs/followups/`)
- ДВ: `https://dv.parliament.bg/DVWeb/showMaterialDV.jsp?idMat={material}` (UTF-8, server-rendered HTML, no Cloudflare); issue contents at `materiali.faces?idObj={issue}`; `idObj` is sparse, not sequential; HTML materials from about 2005, issue PDFs from 1 January 1989, nothing online before
- Total acts: 3,624 on disk and in `catalog.db` (2026-09-05)

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

- Corpus correctness floor (`docs/process/COVERAGE-FLOOR.md`): no fabricated, lost, ambiguous, contaminated or silently uncertain address; enforced at write time by the single corpus write gate and corpus-wide in CI by `corpus_integrity` (PR #23 Part II). **Not yet built as of 2026-09-05**; until it ships there is NO frontmatter schema validator in this repo, so do not claim one (FR-040)
- Markdown must preserve article/chapter/section structure, including paragraph topology (D-058)
- Consolidation output is compared against the witnesses (lex.bg, Ministry of Justice portal) and every divergence adjudicated; witnesses are never truth (D-061)
- Zero errors is the acceptance standard; percentages are diagnostics (Directive 9)
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
| `docs/process/WAIVERS.md` | Dated owner-signed waivers (Directive 12) |
| `docs/followups/INDEX.md` | Deferred findings register (Directive 13) |
| `docs/frs/INDEX.md` | Future requirements backlog |
| `docs/data/canonical-data-model.md` | Domain entity explanations |
| `docs/data/schema-reference.md` | YAML + SQLite schema |
| `docs/testing/test-strategy.md` | Test layers and acceptance criteria |
| `docs/sync/ACTIVE.md` | Current work state |
| `docs/sync/DECISIONS.md` | Decision log |
| `.ahelia/repo-profile.yaml` | Machine-readable repo profile |
