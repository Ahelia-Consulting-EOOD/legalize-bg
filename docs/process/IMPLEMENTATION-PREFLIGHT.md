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

- authoritative source: design doc "MCP Server Tools" section
- hard constraint: existing MCP tool signatures (`get_law`, `search`, `get_article`, `history`, `diff`, `amendments_in_period`) must not have breaking changes to parameter names, parameter types, or return types once published. New tools may be added freely.
- what counts as violation: renaming a parameter (e.g., `name` to `law_name`), changing return type (e.g., `str` to `dict`), removing a tool, making a previously optional parameter required
- allowed scope: adding new tools, adding new optional parameters to existing tools, enriching return values with additional fields (additive only)
- protected files or directories touched: MCP server module (exact path TBD at implementation)
- waiver required: yes, if making a breaking change to a published tool interface

### Evidence

- governing spec: design doc "MCP Server Tools" section
- related owner directive: Directive 1 (Legalize-compatible pipeline)
- related coverage floor: MCP server must have at minimum `get_law`, `search`, `get_article`
- follow-up: all Claude Code consumer sessions must be tested after any interface change

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
