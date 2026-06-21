# Preflight: FR-018 — `get_articles` tool + `get_article` range rejection

Filed 2026-06-21 (batch 2.x-a). Template: `docs/process/IMPLEMENTATION-PREFLIGHT.md` §"Approval Template".

- **protected surface:** 3 (MCP Tool Interface Changes)
- **authoritative source:** `.ahelia/protected-surfaces.yaml` (`mcp_server/server.py (tool signatures)`) + `docs/process/IMPLEMENTATION-PREFLIGHT.md` §"Protected Surface 3" + `docs/plans/2026-05-09-phase1b-mcp-design.md`.
- **hard constraint confirmed:** yes. Existing published tool signatures and response shapes (D-024) must not have breaking changes; new tools may be added freely; additive-only changes to responses; error codes additive-only.
- **what is changing:**
  1. **NEW tool `get_articles(law: str, articles: str, date: str | None = None) -> dict`** returning `{law_id, articles: list[{article, paragraph, text, text_hash}], commit_hash, warnings}`. Adding a new tool is explicitly in Surface 3's *allowed scope* ("adding new tools" — no waiver).
  2. **`get_article` behavior refinement:** when the article spec parses to a **range** (`spec.range_end is not None`), `get_article` now raises `INVALID_ARTICLE_SPEC` (an **existing** taxonomy code already in `get_article`'s contract) with an added `hint` pointing to `get_articles`, instead of silently returning only the first article (the FR-018 bug).
     - Signature unchanged: `get_article(law, article, date) -> GetArticleResponse`.
     - Response shape unchanged for all single-article calls (the success path is untouched).
     - No error code added/removed.
- **violation risk:** the only behavior change is for a **range** input to `get_article`, which previously produced a documented-buggy partial result ("only article=14 is returned in 1b.1" — stated verbatim in the tool docstring). Converting that into an explicit error is not in Surface 3's violation list (no param rename, no return-shape change, no tool removal, no newly-required param, no error-code removal). Downstream skills (ZOP / contracts / rfp-response / legislative-draft) call `get_article` for single articles; none rely on the silent-range behavior (it returned wrong data). Net risk: **low**.
- **allowed scope confirmed:** yes — new tool (additive) + behavior fix within an existing code, no shape/signature change.
- **waiver required:** **no.** No breaking change to a published interface; no error-code removal.
- **tools.json:** regenerated; `TOOLS_JSON_VERSION` 1.1.0 → **1.2.0** (additive: one new tool). Parity test `tests/mcp_server/test_export_tools.py` re-locks it. `.ahelia/protected-surfaces.yaml` `protected_signatures` gains the new `get_articles` line.
- **owner confirmation:** ekimir — via review of the single 2.x-a PR (full-autonomy run; owner reviews before merge).
- **implementation may proceed:** yes (TDD; merge gated on owner PR approval).
