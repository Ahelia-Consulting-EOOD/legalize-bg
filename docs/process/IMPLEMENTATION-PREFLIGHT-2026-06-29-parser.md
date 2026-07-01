# IMPLEMENTATION-PREFLIGHT — parser data-loss remediation (D-047)

Date: 2026-06-29 · Surface: **Protected Surface 1 (`fetcher/bg/` — Legalize `TextParser` interface)**
Plan: `docs/plans/2026-06-29-parser-remediation-plan.md` · Decision: D-047

---

## Preflight: fix `text_parser.py` to stop silently dropping legal subdivisions

- **protected surface:** 1 — `fetcher/bg/text_parser.py` implements the Legalize `TextParser` interface (`HtmlToMarkdown.convert(soup) -> str`).
- **authoritative source:** `legalize-dev/legalize/SPEC.md` (TextParser interface; "Markdown must preserve article/chapter/section structure" quality gate, project CLAUDE.md).
- **hard constraint confirmed:** yes — the public interface (`convert(soup: BeautifulSoup) -> str`, the `TextParser` contract) is UNCHANGED. The change is to the *output completeness*, not the signature. No other `fetcher/bg/` interface (`LegislativeClient`, `NormDiscovery`, `MetadataParser`) is touched.
- **what changes:** (1) add formatting for the 3 dropped subdivision classes `AdditionalEdicts`, `FinalEdicts`, `FinalEdictsArticle`; (2) de-glue subdivision headings from their КЪМ act-names; (3) structured §-body rendering (точки/alinea as paragraphs, bold `**§ N.**`); (4) keep-unknown-content-by-default with a chrome denylist; (5) a new `fetcher/bg/coverage.py` validator (additive module, not an interface change).
- **violation risk:** LOW for the interface (signature stable); the real risk is *output churn* across the whole corpus on re-bootstrap — fully covered by the strict source-vs-output coverage gate (D-047 / plan Phase 2), which is the SOLE per-act acceptance check.
- **allowed scope confirmed:** yes — this is a bug fix that makes the parser SPEC-compliant (it currently violates "preserve article/chapter/section structure" by dropping ДР/ПЗР). It is a contribution-quality improvement to `fetcher/bg/`, not a deviation. MCP server / SQLite / consolidation tooling are NOT touched by the parser change (the deploy-guard in Phase 0 is a separate, non-interface MCP change).
- **waiver required:** no — no SPEC field, commit format, schema, or published interface is broken; the change restores SPEC-required structural fidelity.
- **regression protection:** existing `tests/fetcher/bg/test_text_parser.py` must stay green; new tests for the 3 classes + de-glue + keep-by-default; the `coverage.py` gate asserts ~0 uncovered legal text on all 7 fixtures + the re-fetched acts.
- **rollback:** revert the parser commit; re-run re-bootstrap from the prior corpus state (git).
- **owner confirmation:** ekimir / 2026-06-29 (approved subagent-driven execution)
- **implementation may proceed:** yes

### Evidence
- governing spec: Legalize SPEC.md (TextParser); project CLAUDE.md quality gate "Markdown must preserve article/chapter/section structure".
- related decision: **D-047** (finding + D1–D4 + strict-coverage-gate-every-act directive).
- related coverage floor: all 5 categories / 3,599 acts must parse to structurally-complete Markdown (the defect violates this).
- evidence base: `docs/research/2026-06-29-parser-data-loss-forensics/` (FINDINGS, EVALUATION, COMPLETENESS, ZUO-VERIFICATION).
- follow-up: Phase 4 re-bootstrap re-parses every act through the gate; Phase 5 lifts the deploy-guard.
