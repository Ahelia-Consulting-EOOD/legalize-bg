# Owner Directives

This file is authoritative for repo-specific non-negotiable constraints.
If this file conflicts with a weaker planning doc, this file wins.

## Status

- status: active
- owner: ekimir
- effective date: 2026-04-19
- last amended: 2026-08-11 (directives 9-14, corpus-correctness standard)
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

9. **Zero errors is the acceptance standard for corpus correctness.**
   A single wrong article address is a defect, not a statistic. Percentages, artifact rates and sample-based adjudication are diagnostic tools only; they are never evidence of closure. This corpus is in daily legal use, and a citation to a provision that does not exist is the failure mode this project exists to prevent. The operational definition of a zero-error output is `docs/process/COVERAGE-FLOOR.md` section "Correctness floor".

10. **Detection precedes repair.**
    No fix is written, no sweep is run and no class is called closed before corpus-wide, exhaustive detection exists for that class and has been executed over every act. A census of a subset, however carefully adjudicated, does not authorise a repair.

11. **Correctness is enforced at write time, never at read time.**
    Fixes land in the parser; guarantees land in gates that refuse the write. Query-time filtering, suppression lists and consumer-side exclusion are forbidden as remedies, including as temporary measures.

12. **Gates block or they do not exist.**
    A gate that records a violation and permits the write is not a gate. Report-only mode is permitted solely as a measurement phase, requires a dated waiver naming its expiry condition, and may not be the state in which a class is closed.

13. **Every known defect class is registered before work proceeds.**
    Any defect discovered in any session is recorded as an FR row and a follow-up entry before further work on the surrounding area. Findings held only in a session transcript, a plan appendix or a commit message are treated as unrecorded.

14. **One repair sweep per pipeline generation.**
    All parser fixes for known classes land before the repair sweep is authorised, so that a single sweep repairs the corpus. Sequential per-class sweeps are forbidden; they multiply cost and leave interleaved states no baseline can describe.

## Notes

- Do not bury hard constraints in brainstorming notes or informal PR comments.
- Directives 1-8 derive from HANDOVER.md "Decisions Already Made" and the approved design doc (2026-04-19).
- Directives 9-14 derive from the owner's ruling of 2026-08-11, following the anchor-integrity status review: "1 error, and the corpus is unreliable. Zero errors is the only acceptable standard." They strengthen the oversight baseline, which local repos may do without a waiver.
- Waiver of any directive requires a dated entry in `docs/process/WAIVERS.md` with owner sign-off.
