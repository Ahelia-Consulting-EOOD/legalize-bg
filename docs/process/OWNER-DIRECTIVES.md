# Owner Directives

This file is authoritative for repo-specific non-negotiable constraints.
If this file conflicts with a weaker planning doc, this file wins.

## Status

- status: active
- owner: ekimir
- effective date: 2026-04-19
- review cadence: per-phase gate (before each phase transition)

## Directives

1. **Option A: Contribute to Legalize upstream, not fork.**
   All pipeline code (fetcher, transformer, committer) must be Legalize-compatible. We implement the 4 standard interfaces (`LegislativeClient`, `NormDiscovery`, `TextParser`, `MetadataParser`) under `fetcher/bg/`. Private-layer code (MCP server, SQLite index, consolidation engine) lives at Ahelia but must not break upstream compatibility.

2. **lex.bg = bootstrap only; DV = ongoing source.**
   Do NOT build ongoing dependency on lex.bg scraping. lex.bg is used once in Phase 1a to populate the initial corpus. After bootstrap, all updates come from dv.parliament.bg (Tue/Fri gazette monitoring) and the consolidation engine. New lex.bg fetches are allowed only for validation (Directive 3) and one-off gap-filling with explicit justification.

3. **lex.bg = validation oracle for consolidation engine.**
   Compare consolidation engine output against lex.bg consolidated text. lex.bg is NOT the source of truth for ongoing updates -- it is the reference answer to validate our own consolidation. Workflow: engine produces consolidated text, fetcher grabs lex.bg version of same law, diff and report. Non-trivial diffs are flagged for human review.

4. **Markdown + YAML format, not Akoma Ntoso.**
   Matches the Legalize ecosystem. All acts stored as Markdown with YAML frontmatter containing the 8 mandatory Legalize SPEC fields (`titulo`, `identificador`, `pais`, `rango`, `fecha_publicacion`, `ultima_actualizacion`, `estado`, `fuente`) plus 5 Bulgarian extensions (`dv_issue`, `dv_year`, `effective_date`, `category`, `eli`). The `amendment_history` array is an optional nested structure, not a named extension field.

5. **Git + SQLite hybrid storage.**
   Git is the versioned store for legislation text (each amendment = one commit with `GIT_AUTHOR_DATE`). SQLite is the derived temporal index for date-range queries, provision-level lookups, and amendment cross-references. SQLite is always rebuildable from git history.

6. **Municipal = Phase 6. Do NOT start municipal work until national pipeline is stable.**
   National pipeline means Phases 1a through 4v are shipping and consolidation accuracy is validated. Sofia Municipality is Phase 6a, top-10 cities are 6b, remaining 265 municipalities are 6c. No municipal fetcher code, no municipal directory structure, no municipal MCP tools until Phase 6 gate is passed.

7. **Host at Ahelia-Consulting-EOOD GitHub org.**
   Private repo `Ahelia-Consulting-EOOD/legalize-bg`. The fetcher/bg/ module is later upstreamed to `legalize-dev/legalize-pipeline` via PR in Phase 5. Private-layer components (MCP server, consolidation engine, corruption research tooling) remain at Ahelia.

8. **cp1251 encoding for all lex.bg fetches.**
   All HTTP responses from lex.bg must be explicitly decoded as `cp1251`. Never assume UTF-8, never rely on auto-detection. Set `resp.encoding = 'cp1251'` immediately after every `requests.get()` call to lex.bg. Output files are UTF-8 (Markdown in git).

## Notes

- Do not bury hard constraints in brainstorming notes or informal PR comments.
- Directives 1-8 derive from HANDOVER.md "Decisions Already Made" and the approved design doc (2026-04-19).
- Waiver of any directive requires a dated entry in `docs/process/WAIVERS.md` with owner sign-off.
