"""FastMCP server: thin tool definitions over the queries layer.

Tool docstrings are the MCP `tools/list` descriptions seen by Claude
Code, Claude Desktop, and OpenAI Codex. Per D-021, keeping descriptions
in sync with behavior is enforced by FastMCP rendering them automatically
— don't write parallel descriptions elsewhere.

`build_app(conn, corpus_root)` returns an `_AppHandle` carrying:
  - the FastMCP `mcp` instance for production transport (mcp.run())
  - a `_tools` dict for direct sync invocation in tests (call_tool_sync)
  - the bound `_conn` so test fixtures can mutate state (e.g., set the
    date_uncertain flag) and assert on resulting warnings

Per the queries.py docstring: the connection passed in MUST have
`row_factory = sqlite3.Row`. The `__main__` CLI sets this; tests do too
via the conftest fixture.
"""

from __future__ import annotations

import inspect
import logging
import sqlite3
import subprocess
from pathlib import Path
from typing import Any, Callable

import yaml
from fastmcp import FastMCP

from mcp_server import queries
from mcp_server.errors import ToolError
from mcp_server.schemas import GetArticleResponse, GetLawResponse, SearchHit

log = logging.getLogger(__name__)


# ─────────────────────────── helpers ──────────────────────────────────────


def _read_law_markdown(corpus_root: Path, law_id: str, category: str,
                       commit_hash: str, current_commit: str) -> str:
    """Return the full Markdown (frontmatter + body) for the law at the
    given commit.

    Working-tree fast path when commit_hash == current_commit (the
    HEAD-equivalent recorded by `index.build` at index time). Historical
    versions go through `git show`, which Phase 2 will exercise heavily.
    """
    rel_path = f"{category}/{law_id}.md"
    if commit_hash == current_commit:
        path = corpus_root / rel_path
        return path.read_text(encoding="utf-8")
    out = subprocess.run(
        ["git", "show", f"{commit_hash}:{rel_path}"],
        cwd=corpus_root, check=True, capture_output=True, text=True,
    )
    return out.stdout


def _split_frontmatter(raw: str) -> tuple[dict, str]:
    """Split a Markdown file with YAML frontmatter into (frontmatter, body).
    Mirrors `index.build._parse_md` so the read path matches the write
    path; if the corpus invariant changes, both fix together.

    Behavior on missing `---\\n` prefix: returns ({}, raw) and emits a
    WARN log. The build path raises on missing frontmatter; the query
    path doesn't, because the working-tree fast path may legitimately
    encounter a hand-edited file mid-edit. Without the WARN, an operator
    could silently get titulo="" / eli=None responses (audit D-9).
    """
    if not raw.startswith("---\n"):
        log.warning(
            "frontmatter delimiter '---' missing at start of markdown; "
            "returning empty frontmatter dict (working-tree may be dirty "
            "or the file is hand-edited — re-run index.build if so)"
        )
        return {}, raw
    after_open = raw[4:]
    parts = after_open.split("\n---\n", 1)
    fm = yaml.safe_load(parts[0]) or {}
    body = parts[1] if len(parts) > 1 else ""
    return fm, body.lstrip("\n")


def _law_meta(conn: sqlite3.Connection, law_id: str) -> dict:
    row = conn.execute(
        "SELECT * FROM laws WHERE law_id = ?", (law_id,)
    ).fetchone()
    return dict(row) if row else {}


# ─────────────────────────── handle ───────────────────────────────────────


class _AppHandle:
    """Wrapper carrying the FastMCP app + sync test shortcut.

    In production: `handle.mcp.run()` runs the stdio transport.
    In tests: `handle.call_tool_sync("get_law", {...})` invokes the
    registered Python function directly (skipping FastMCP's JSON-RPC
    serialization). End-to-end tests that exercise serialization use
    fastmcp.Client(handle.mcp) — see test_tools_e2e.
    """

    def __init__(self, mcp: FastMCP, conn: sqlite3.Connection,
                 corpus_root: Path):
        self.mcp = mcp
        self._conn = conn
        self._corpus = corpus_root
        self._tools: dict[str, Callable[..., Any]] = {}

    def call_tool_sync(self, name: str, args: dict) -> Any:
        """Run a registered tool synchronously by name (for tests)."""
        return self._tools[name](**args)


# ─────────────────────────── app factory ──────────────────────────────────


def build_app(conn: sqlite3.Connection, corpus_root: Path,
              name: str = "legalize-bg") -> _AppHandle:
    """Build a FastMCP app with all Phase 1b.1 tools bound to (conn,
    corpus_root). The factory pattern keeps tools pure functions that
    close over the connection rather than reaching for module globals
    — easy to test, easy to swap for a fresh DB in fixtures."""
    mcp = FastMCP(name)
    handle = _AppHandle(mcp, conn, Path(corpus_root))

    def _full_docstring(fn: Callable[..., Any]) -> str:
        """FastMCP only takes the first line of the Python docstring as
        the MCP description. The rest (Args, Returns sections) is what
        actually helps the model decide which tool to call. We use the
        whole cleaned-up docstring as the explicit `description=` kwarg
        so callers see the full contract."""
        return inspect.getdoc(fn) or ""

    # ─────────────────── get_law ─────────────────────────────────────

    def get_law(name: str, date: str | None = None) -> dict:
        """Return the full text and metadata of a Bulgarian normative act.

        Args:
            name: The act's title (e.g. "Закон за обществените поръчки"),
                slug (e.g. "zakon-za-obshtestvenite-porachki"), or
                numeric lex.bg identificador (e.g. "2136735703").
                Identificador is the most stable handle — slugs may carry
                collision suffixes (-2, -3) and titles may be non-unique
                across acts. See §7.1 of canonical-data-model.md.
            date: ISO 8601 date for historical retrieval. If omitted,
                returns the current consolidated version.

        Returns:
            Structured response with metadata fields (titulo, identificador,
            fecha_publicacion, ultima_actualizacion, dv_issue, dv_year,
            effective_date, eli, amendment_history, commit_hash) and
            body_markdown. May include a `warnings` list — DATE_UNCERTAIN
            is set for acts whose publication date was not parseable from
            lex.bg (§7.2).
        """
        try:
            law_id = queries.resolve_name_to_law_id(conn, name)
        except queries.AmbiguousName as e:
            raise ToolError(code="AMBIGUOUS_NAME",
                            payload={"name": e.name,
                                     "candidates": e.candidates})
        except queries.LawNotFound as e:
            raise ToolError(code="LAW_NOT_FOUND",
                            payload={"name": e.name,
                                     "suggestions": e.suggestions})

        try:
            commit, warnings = queries.version_with_warnings(conn, law_id, date)
        except queries.NoVersionAtDate as e:
            raise ToolError(code="NO_VERSION_AT_DATE", payload={
                "law_id": e.law_id,
                "date": e.date,
                "earliest_available": e.earliest_available,
                "latest_available": e.latest_available,
            })

        meta_row = _law_meta(conn, law_id)
        raw = _read_law_markdown(handle._corpus, law_id,
                                 meta_row["category"], commit,
                                 meta_row["current_commit"])
        fm, body = _split_frontmatter(raw)
        resp = GetLawResponse(
            law_id=law_id,
            identificador=str(meta_row["doc_id"]),
            titulo=fm.get("titulo") or "",
            category=meta_row["category"],
            fecha_publicacion=_iso(fm.get("fecha_publicacion")),
            ultima_actualizacion=_iso(fm.get("ultima_actualizacion")),
            dv_issue=fm.get("dv_issue"),
            dv_year=fm.get("dv_year"),
            effective_date=_iso(fm.get("effective_date")),
            eli=fm.get("eli"),
            amendment_history=fm.get("amendment_history") or [],
            commit_hash=commit,
            body_markdown=body,
            warnings=warnings,
        )
        return resp.to_dict()

    mcp.tool(description=_full_docstring(get_law))(get_law)
    handle._tools["get_law"] = get_law

    # ─────────────────── search ──────────────────────────────────────

    def search(query: str, category: str | None = None,
               limit: int = 20,
               include_body: bool = False) -> list[dict]:
        """Full-text search over the Bulgarian legislation corpus.

        Bulgarian morphology is handled via symmetric `bg_normalize`
        pre-processing (definite-article suffix stripping) so queries
        match grammatical variants without requiring exact form. For
        example, "обществените поръчки" (plural definite) and
        "обществени поръчки" (plural indefinite) reduce to the same
        indexed form.

        Args:
            query: Free-form Bulgarian (or mixed Cyrillic/Latin) text.
                Empty / whitespace-only queries return an empty list.
                Single-token Bulgarian abbreviations (`ЗОП`, `НК`,
                `ГПК`, etc. — see index/synonyms.py for the full list)
                are auto-expanded to their canonical long form.
            category: Optional filter — one of "laws", "codes",
                "ordinances", "regulations", "implementing".
            limit: Max results (default 20, capped at 50).
            include_body: When True, the top 2 results carry a
                non-empty `body_snippet` field with a ±60-char window
                around the first matching token in the act's body
                (with `<b>...</b>` highlighting). Adds ~150 ms per
                search call because the largest indexed bodies are
                1+ MB. Default False — preserves the 100 ms p95
                budget. Pass True only when the model needs body
                context to disambiguate similar titles. (FR-017)

        Returns:
            List of {law_id, identificador, title, category,
            title_snippet, body_snippet, relevance}. `relevance` is
            positive-where-higher-is-better (negated SQLite bm25).
            `title_snippet` is always populated (cheap title fragment).
            `body_snippet` is empty unless `include_body=True`, and
            then non-empty for the top 2 hits only.

            Result ordering combines bm25 relevance WITH a rang-aware
            tier sort (FR-015): parent laws (`laws`/`codes` categories)
            float to the top, implementing regs / ordinances follow,
            with bm25 order preserved within each tier. So `relevance`
            is a within-tier signal — don't sort by it globally.

            Acts with empty titulo (§7.3) carry "<doc_id=N>" in the
            title slot.

        Raises:
            QUERY_TOO_BROAD: when the query (after normalization) is a
                single Bulgarian category word ("наредба", "закон",
                "правилник", "кодекс", "постановление"). These would
                match thousands of acts each; the rejection prevents
                a 400 ms+ cold-call latency outside the 100 ms p95
                budget. Multi-word queries containing the same words
                ("наредба за обществени поръчки") are NOT rejected.
        """
        # Cap limit defensively — FTS5 with very large limits can OOM
        # on a million-row catalog. 50 is plenty for an LLM caller.
        capped = min(max(1, int(limit)), 50)
        return queries.full_text_search(conn, query=query,
                                        category=category, limit=capped,
                                        include_body=bool(include_body))

    mcp.tool(description=_full_docstring(search))(search)
    handle._tools["search"] = search

    # ─────────────────── get_article ─────────────────────────────────

    def get_article(law: str, article: str,
                    date: str | None = None) -> dict:
        """Return a specific article (or alinea) of a Bulgarian act.

        Args:
            law: The act's title, slug, or identificador (see get_law).
            article: Article reference. Accepts:
                "чл. 14" / "14" / "Чл. 14" — whole article
                "чл. 14а" / "14а" — Cyrillic-suffix variant
                "чл. 14, ал. 2" / "14.2" / "14, ал. 2" — specific alinea
                "чл. 14-16" — range (only article=14 is returned in 1b.1;
                    full range support tracked in FR-018).
            date: ISO 8601 date for historical retrieval. If omitted,
                returns the current text.

        Returns:
            {law_id, article, paragraph, text, text_hash, commit_hash,
            warnings}. `paragraph` is null for the article-as-whole row
            and a string ("1", "2", "1а"...) for an alinea row.
            `text_hash` is a stable per-row digest — Phase 4 amendment
            detection compares hashes to pinpoint changed alineas.
        """
        try:
            law_id = queries.resolve_name_to_law_id(conn, law)
        except queries.AmbiguousName as e:
            raise ToolError(code="AMBIGUOUS_NAME",
                            payload={"name": e.name,
                                     "candidates": e.candidates})
        except queries.LawNotFound as e:
            raise ToolError(code="LAW_NOT_FOUND",
                            payload={"name": e.name,
                                     "suggestions": e.suggestions})

        try:
            spec = queries.parse_article_spec(article)
        except queries.InvalidArticleSpec:
            raise ToolError(code="INVALID_ARTICLE_SPEC", payload={
                "spec": article,
                "examples": [
                    "чл. 14", "14", "чл. 14а",
                    "чл. 14, ал. 2", "14.2", "чл. 14-16",
                ],
            })

        try:
            commit, warnings = queries.version_with_warnings(
                conn, law_id, date)
        except queries.NoVersionAtDate as e:
            raise ToolError(code="NO_VERSION_AT_DATE", payload={
                "law_id": e.law_id,
                "date": e.date,
                "earliest_available": e.earliest_available,
                "latest_available": e.latest_available,
            })

        try:
            rows = queries.article_lookup(
                conn, law_id, article=spec.article,
                paragraph=spec.paragraph, date=date)
        except queries.ArticleNotFound as e:
            raise ToolError(code="ARTICLE_NOT_FOUND", payload={
                "law_id": e.law_id,
                "article": e.article,
                "paragraph": e.paragraph,
                "available_articles": e.available_articles,
            })

        # When paragraph is requested, return the alinea row; else the
        # article-as-whole row. article_lookup's WHERE clause filters
        # on (law_id, article, paragraph, valid_from <= date,
        # valid_to >= date OR NULL), which guarantees a single row at
        # any given date in 1b.1.
        #
        # Phase-2 caveat (FR-001): when historical versions are
        # backfilled with non-NULL valid_to, this single-row guarantee
        # depends on the temporal predicate staying strict (no overlap
        # between adjacent versions). If FR-001 ever loosens that —
        # e.g., to support range queries — picking rows[0] becomes a
        # silent bug; switch to explicit "highest valid_from" tie-break
        # at that point.
        target = rows[0]
        resp = GetArticleResponse(
            law_id=law_id,
            article=target["article"],
            paragraph=target["paragraph"],
            text=target["text"],
            text_hash=target["text_hash"],
            commit_hash=commit,
            warnings=warnings,
        )
        return resp.to_dict()

    mcp.tool(description=_full_docstring(get_article))(get_article)
    handle._tools["get_article"] = get_article

    # ─────────────────── history (Phase 2) ───────────────────────────

    def history(law: str) -> list[dict]:
        """Return the amendment timeline of a Bulgarian act, oldest→newest.

        Args:
            law: The act's title, slug, or identificador (see get_law).

        Returns:
            A list of version entries, each {date, dv_issue, operation,
            commit_hash}. `operation` is "amendment" for a DV amendment
            event and "consolidated" for the currently-held text. Only
            the consolidated entry carries a non-null `commit_hash`:
            the corpus holds one consolidated text per act, so the text
            of historical amendments is not separately retrievable yet
            (commit_hash is null for those). Use this to answer "when
            was this act amended?" — it lists every DV amendment date.
        """
        try:
            law_id = queries.resolve_name_to_law_id(conn, law)
        except queries.AmbiguousName as e:
            raise ToolError(code="AMBIGUOUS_NAME",
                            payload={"name": e.name, "candidates": e.candidates})
        except queries.LawNotFound as e:
            raise ToolError(code="LAW_NOT_FOUND",
                            payload={"name": e.name, "suggestions": e.suggestions})
        return [v.to_dict() for v in queries.law_history(conn, law_id)]

    mcp.tool(description=_full_docstring(history))(history)
    handle._tools["history"] = history

    # ─────────────────── amendments_in_period (Phase 2) ──────────────

    def amendments_in_period(from_date: str, to_date: str) -> list[dict]:
        """List every dated amendment across the whole corpus in a period.

        Args:
            from_date: ISO 8601 start date (inclusive).
            to_date: ISO 8601 end date (inclusive).

        Returns:
            A list of {law_id, title, date, dv_issue}, oldest first —
            every act amended on a DV date within the period. Useful for
            "what changed in Bulgarian law between X and Y?" research.

        Raises:
            INVALID_DATE_RANGE: when from_date is later than to_date.
        """
        return [a.to_dict()
                for a in queries.amendments_in_period(conn, from_date, to_date)]

    mcp.tool(description=_full_docstring(amendments_in_period))(amendments_in_period)
    handle._tools["amendments_in_period"] = amendments_in_period

    # ─────────────────── diff (Phase 2) ──────────────────────────────

    def diff(law: str, date1: str, date2: str) -> str:
        """Return a git diff of an act's text between two dates.

        Args:
            law: The act's title, slug, or identificador (see get_law).
            date1: ISO 8601 start date.
            date2: ISO 8601 end date.

        Returns:
            The unified `git diff` of the act between the versions in
            force at date1 and date2. When the corpus holds a single
            consolidated version (the current state for most acts), a
            clear bilingual "single consolidated version held" note is
            returned instead of an empty diff. Real diffs appear once
            additional versions are committed (corpus re-scrape / Phase 4).

        Raises:
            INVALID_DATE_RANGE: when date1 is later than date2.
            NO_VERSION_AT_DATE: when a date precedes the act's earliest
                recorded version.
        """
        try:
            law_id = queries.resolve_name_to_law_id(conn, law)
        except queries.AmbiguousName as e:
            raise ToolError(code="AMBIGUOUS_NAME",
                            payload={"name": e.name, "candidates": e.candidates})
        except queries.LawNotFound as e:
            raise ToolError(code="LAW_NOT_FOUND",
                            payload={"name": e.name, "suggestions": e.suggestions})
        try:
            return queries.diff_law_versions(
                conn, handle._corpus, law_id, date1, date2)
        except queries.NoVersionAtDate as e:
            raise ToolError(code="NO_VERSION_AT_DATE", payload={
                "law_id": e.law_id, "date": e.date,
                "earliest_available": e.earliest_available,
                "latest_available": e.latest_available,
            })

    mcp.tool(description=_full_docstring(diff))(diff)
    handle._tools["diff"] = diff

    return handle


def _iso(v: Any) -> str | None:
    """Coerce date-like YAML value to ISO string (PyYAML may yield
    datetime.date for ISO date fields)."""
    if v is None:
        return None
    if hasattr(v, "isoformat"):
        return v.isoformat()
    return str(v)
