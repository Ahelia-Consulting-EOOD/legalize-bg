# Implementation Preflight

Complete this checklist before implementing against any protected surface.
Copy the relevant section into your task notes and fill in the answers before proceeding.

---

## Protected Surface 1: Upstream PR to Legalize

### Restatement

- authoritative source: `legalize-dev/legalize-pipeline/ADDING_A_COUNTRY.md` and `legalize-dev/legalize/SPEC.md`
- hard constraint: PR must pass all 4 Legalize hard gates (interfaces implemented, SPEC-compliant frontmatter, commit format correct, CI green)
- what counts as violation: submitting PR with missing SPEC fields, non-standard commit types, broken CI, or fetcher that does not implement all 4 interfaces (`LegislativeClient`, `NormDiscovery`, `TextParser`, `MetadataParser`)
- allowed scope: `fetcher/bg/` module only. MCP server, SQLite index, consolidation engine, and corruption research tooling are Ahelia-private and must NOT be included in the upstream PR
- protected files or directories touched: `fetcher/bg/client.py`, `fetcher/bg/discovery.py`, `fetcher/bg/text_parser.py`, `fetcher/bg/metadata.py`, `config.yaml` (bg section)
- waiver required: no (this is a contribution, not a deviation)

### Evidence

- governing spec: Legalize SPEC.md (8 mandatory YAML fields, commit message format, directory conventions)
- related owner directive: Directive 1 (contribute upstream, not fork)
- related coverage floor: all 5 categories and ~3,574 acts must be fetchable through the interfaces
- follow-up: Phase 5 gate review before PR submission

---

## Protected Surface 2: YAML Frontmatter Schema Changes

### Restatement

- authoritative source: `legalize-dev/legalize/SPEC.md` for mandatory fields; design doc "Markdown File Format" section for Bulgarian extensions
- hard constraint: the 8 mandatory Legalize SPEC fields (`titulo`, `identificador`, `pais`, `rango`, `fecha_publicacion`, `ultima_actualizacion`, `estado`, `fuente`) must never be removed, renamed, or have their semantics changed. Bulgarian extension fields (`dv_issue`, `dv_year`, `effective_date`, `category`, `eli`, `amendment_history`) must remain backward-compatible.
- what counts as violation: removing a mandatory field, renaming a field without migrating all ~3,574 act files, adding a required field without backfilling existing files, changing a field's type (e.g., string to array) without updating all downstream consumers (MCP server, SQLite indexer)
- allowed scope: adding new optional extension fields is allowed without preflight. Any other schema change requires preflight.
- protected files or directories touched: every `.md` file under `laws/`, `codes/`, `ordinances/`, `regulations/`, `implementing/`, `municipal/`
- waiver required: yes, if deviating from Legalize SPEC mandatory fields

### Evidence

- governing spec: Legalize SPEC.md, design doc section "Markdown File Format"
- related owner directive: Directive 4 (Markdown + YAML format)
- related coverage floor: YAML frontmatter on every act with all 8 mandatory fields
- follow-up: migration script must be written and tested before schema change is applied

---

## Protected Surface 3: MCP Tool Interface Changes

### Restatement

- authoritative source: `docs/architecture/container-view.md` §7 + `docs/plans/2026-05-09-phase1b-mcp-design.md`
- hard constraint: existing MCP tool signatures (`get_law -> GetLawResponse`, `search -> list[SearchHit]`, `get_article -> GetArticleResponse`; Phase 2: `history`, `diff`, `amendments_in_period`) must not have breaking changes to parameter names, parameter types, or return-type fields once published. New tools may be added freely. Per D-024, response shapes are typed-dicts/dataclasses, not bare strings — fields may be added but not removed/renamed.
- what counts as violation: renaming a parameter (e.g., `name` to `law_name`), changing the return-type structure (e.g., dropping `body_markdown` from `GetLawResponse`), removing a tool, making a previously optional parameter required, removing a code from the error taxonomy (D-026)
- allowed scope: adding new tools, adding new optional parameters to existing tools, adding new fields to response dataclasses (additive only), adding new error codes to the taxonomy (additive only)
- protected files or directories touched: `mcp_server/server.py`, `mcp_server/queries.py`, `mcp_server/schemas.py`, `mcp_server/errors.py`
- waiver required: yes, if making a breaking change to a published tool interface or removing an error code

### Evidence

- governing spec: `docs/plans/2026-05-09-phase1b-mcp-design.md` §6.5 (FastMCP server) + §8 (error taxonomy)
- related decisions: D-021 (FastMCP), D-024 (typed-dict responses), D-026 (error taxonomy), D-027 (three-milestone phase plan)
- related owner directive: Directive 1 (Legalize-compatible pipeline)
- related coverage floor: MCP server must have at minimum `get_law`, `search`, `get_article` (Phase 1b.1)
- follow-up: Phase 1b.2 publishes `tools.json` schema file as the canonical breaking-change boundary; all three target clients (Claude Code, Claude Desktop, OpenAI Codex) must be smoke-tested after any interface change

---

## Protected Surface 6: Index Builder + FTS Normalizer

### Restatement

- authoritative source: `docs/plans/2026-05-09-phase1b-mcp-design.md` §6.1 (index builder), §6.3 (FTS5 + bg_normalize)
- hard constraint: `index/build.py` is idempotent and rebuildable from any git ref. `bg_normalize` is symmetric — same function called at insert AND query time. `provisions` table populated to article AND alinea level from day one (per D-023). FTS5 schema must use `unicode61 remove_diacritics 2` tokenizer.
- what counts as violation: introducing non-determinism into the index build, changing `bg_normalize` at insert time without updating query time (asymmetry breaks search), populating `provisions` with article rows only (regression of D-023), switching to a custom SQLite C tokenizer in 1b.1 without preflight (D-022 explicitly defers this), failing to set `text` column on provisions rows (regression of D-023)
- allowed scope: adding new normalization rules to `bg_normalize` (must be applied symmetrically), adding new columns to `provisions` (with migration via `index/migrations.py` per D-025), adding new FTS5 columns
- protected files or directories touched: `index/build.py`, `index/provisions.py`, `index/fts.py`, `index/migrations.py`, `index/catalog.py`
- waiver required: yes, if changing `bg_normalize` semantics or rolling back D-023 alinea-level rows

### Evidence

- governing spec: design doc §6, §7, §8.2 (§7 data-quality semantics encoded)
- related decisions: D-022 (FTS5 + bg_normalize), D-023 (alinea rows + text column), D-025 (migrations.py from day one)
- related coverage floor: SQLite temporal index covering all acts (Phase 2 dependency)
- follow-up: every change touching `bg_normalize` must run the `bg_search_regression.yaml` suite to detect quality regressions

---

## Protected Surface 7: MCP Server Runtime Dependency (FastMCP)

### Restatement

- authoritative source: `docs/plans/2026-05-09-phase1b-mcp-design.md` §3 (tech stack), D-021
- hard constraint: `fastmcp` is the chosen Python MCP framework. Tool descriptions are docstrings (FastMCP renders them into `tools/list` responses). Dropping a single tool to the low-level `mcp` SDK is acceptable per D-021 if FastMCP cannot express a needed control, but wholesale framework swap requires preflight.
- what counts as violation: replacing FastMCP with a different MCP framework without preflight, hand-writing tool descriptions divergent from docstrings (breaks the description-in-sync-with-behavior property), introducing a transport other than stdio in Phase 1b.1 (SSE/HTTP deferred to 1b.3 per design)
- allowed scope: pinning fastmcp version, dropping individual tools to low-level `mcp` SDK with documentation, adding new transports in Phase 1b.3
- protected files or directories touched: `pyproject.toml` (fastmcp dep), `mcp_server/server.py`
- waiver required: yes, if replacing FastMCP

### Evidence

- governing spec: design doc §3, §6.5
- related decisions: D-021 (FastMCP)
- related coverage floor: MCP server with at minimum `get_law`, `search`, `get_article`
- follow-up: dependency upgrades must run the full L3 integration suite before merge

---

## Protected Surface 4: SQLite Schema Changes

### Restatement

- authoritative source: design doc "SQLite Index Schema" section
- hard constraint: the 4 core tables (`laws`, `law_versions`, `amendments`, `provisions`) and their primary/foreign key relationships must not be altered without preflight. Column additions are allowed. Column removals, renames, or type changes require preflight and a migration script.
- what counts as violation: dropping a column, renaming a column without migration, changing a foreign key relationship, removing an index that temporal queries depend on (`idx_versions_date`, `idx_amendments_target`, `idx_provisions_article`)
- allowed scope: adding new columns (with defaults), adding new indexes, adding new tables, adding new views
- protected files or directories touched: SQLite schema definition file, indexer/rebuild scripts
- waiver required: no for additive changes; yes for destructive changes

### Evidence

- governing spec: design doc "SQLite Index Schema" section
- related owner directive: Directive 5 (Git + SQLite hybrid)
- related coverage floor: SQLite temporal index covering all acts
- follow-up: rebuild script must be tested against full corpus before schema change is deployed

---

## Protected Surface 5: Commit Message Format Changes

### Restatement

- authoritative source: `legalize-dev/legalize/SPEC.md` and design doc "Commit Message Format" section
- hard constraint: commit message format must follow Legalize SPEC. The 5 commit types (`[bootstrap]`, `[reforma]`, `[nova]`, `[otmyana]`, `[popravka]`) and the metadata trailer format (`Source-Id`, `Source-Date`, `Norm-Id`) are fixed. `GIT_AUTHOR_DATE` must be set to the amendment's effective date.
- what counts as violation: using a non-standard commit type prefix, omitting required metadata trailers, setting `GIT_AUTHOR_DATE` to the commit creation date instead of the amendment date, changing the trailer key names
- allowed scope: adding new optional trailers (e.g., `Validation-Status`). Adding new commit types only if Legalize SPEC is updated upstream first.
- protected files or directories touched: committer module, CI/CD pipeline configuration
- waiver required: yes, if deviating from Legalize SPEC commit format

### Evidence

- governing spec: Legalize SPEC.md, design doc "Commit Message Format"
- related owner directive: Directive 1 (Legalize-compatible)
- related coverage floor: every bootstrap and reforma commit must follow the format
- follow-up: CI lint check should validate commit message format on every push

---

## Approval Template

Copy this block when performing preflight for a specific task:

```
## Preflight: [task name]

- protected surface: [1-5 from above]
- authoritative source: [as listed]
- hard constraint confirmed: yes/no
- violation risk: [describe]
- allowed scope confirmed: yes/no
- waiver required: yes/no
- owner confirmation: [ekimir / date]
- implementation may proceed: yes/no
```
