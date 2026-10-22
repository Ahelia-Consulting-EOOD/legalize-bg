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

## Owner facts

Each entry is an agent's reading of what the owner said, with the date and where. Readings, not quotes; the owner corrects the line.

- **The corpus decides the plan** (owner, 22 October 2026, in the write-path session of the run-design worktree, after reading the reading-path diagram). The acts themselves are the single source of truth for what must be done and planned. Legalize's frameworks for 40 or more countries are one source of information, never the authority. The plan comes from studying this corpus in a structured way: the kinds of act, their formatting conventions and how those changed over time, the Gazette era each act's history falls in, and the acts lex.bg is known to hold wrong.
- **Mechanical checks stay wherever the text has a strict structure** (owner, 21 October 2026, in the legalize-bg planning session). The 20 October rule that pattern checks of free text only list and the model decides covers free prose only. Code, code-like text and the structured skeleton of an act (YAML frontmatter, JSON and CSV tables, commit trailers, the article and paragraph numbering grammar, address uniqueness, heading sequence) keep mechanical checks, and those checks keep blocking. The rule is not absolute: what the judgement needs decides where it sits, meaning for prose, form for structure.
- **Scripts acquire, the reasoning run decides** (owner, 21 October 2026, in the legalize-bg planning session). Scripts fetch, enumerate, diff and write through the gate; what a Gazette material does to which act, how the text reads after it, and how a witness divergence is settled are decided by a reasoning run and recorded as data. The reasoning run is the consolidation engine. The daily update is a declared scheduled loop in the form of the oversight catalogue's loops, not a goal session. The end of this stage is the day lex.bg is no longer needed as a source; municipal sources and court practice come after it.
- **All model runs go through the owner's Claude session plans** (owner, 21 October 2026, in the legalize-bg planning session). Labelling, operations, adjudication, the audit and the backfill run as Claude Code subagents and workflows under the owner's subscription plans, never through an API key. API keys come only when and if the project goes public and is hosted somewhere, which the owner decides. Cost figures in dollars are comparisons between designs, not spend.
- **Model runs use the lean project agent, never a general-purpose subagent** (owner, 22 October 2026, in the structure-map labelling session). Every labelling, operation or adjudication call of a run goes through a project agent defined in `.claude/agents/` with only the tools the call needs (`labeller`: Read and Write), so that the fixed context of a call is the instructions and the task, not the session's tool catalogue; a general-purpose subagent spent about 65,000 tokens of fixed context per call for 3,000 to 8,000 of content. Several tasks go in one call where the content stays well within the model's reliable range. A new agent definition loads at session start, so a run that needs one starts a new session.
- **Costs are reported by token type and cache type, with the time of the calls** (owner, 21 October 2026, in the run-driver design session). Every cost of a model run is given as uncached input, cache writes by cache lifetime, cache reads and output, each at its price, together with the calls' durations, because the price depends on how much of each call the cache serves; a single token count hides this.
- **No measurement runs; estimate from past transcripts, then measure at the start of the real run** (owner, 21 October 2026, in the run-driver design session). Tokens are not spent on measurement alone. A design is estimated from the transcripts of earlier runs, and what the estimate could not settle is measured by the first batch of the real run, before the full run continues.
- **Labeller-type agents are exempt from the first-principles hook** (owner, 21 October 2026, in the run-driver design session, decision D-070). The SubagentStart hook that gives every subagent the first principles skips the project's labeller agents, which read only their task and judge nothing the principles govern; about 1,800 tokens per call are saved. Every other agent keeps the hook.
- **The only success criterion of this stage is an act correctly read, properly parsed and committed in git** (owner, 21 October 2026, in the batch-1 run session of the run-design worktree). A staged text in a run folder, a map, a report or a measurement is not a result; every report is measured by the distance left to a committed act, and that distance is stated first. Batch plans and goal lines carry this criterion, or say in one line why their output stops short of it.
