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
    path; if the corpus invariant changes, both fix together."""
    if not raw.startswith("---\n"):
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

    # ─────────────────── get_law ─────────────────────────────────────

    @mcp.tool()
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

    handle._tools["get_law"] = get_law

    # ─────────────────── search ──────────────────────────────────────

    @mcp.tool()
    def search(query: str, category: str | None = None,
               limit: int = 20) -> list[dict]:
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
            category: Optional filter — one of "laws", "codes",
                "ordinances", "regulations", "implementing".
            limit: Max results (default 20, capped at 50).

        Returns:
            List of {law_id, identificador, title, category, snippet,
            relevance}. `relevance` is positive-where-higher-is-better
            (the negated SQLite bm25 score). Acts with empty titulo
            (§7.3) carry "<doc_id=N>" in the title slot so callers
            never see a blank.
        """
        # Cap limit defensively — FTS5 with very large limits can OOM
        # on a million-row catalog. 50 is plenty for an LLM caller.
        capped = min(max(1, int(limit)), 50)
        return queries.full_text_search(conn, query=query,
                                        category=category, limit=capped)

    handle._tools["search"] = search

    # ─────────────────── get_article ─────────────────────────────────

    @mcp.tool()
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
                    full range support tracked in FR-001 Phase 2).
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
        # article-as-whole row. article_lookup's WHERE clause already
        # filters, so rows is either the alinea (single row) or the
        # article (single row).
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

    handle._tools["get_article"] = get_article

    return handle


def _iso(v: Any) -> str | None:
    """Coerce date-like YAML value to ISO string (PyYAML may yield
    datetime.date for ISO date fields)."""
    if v is None:
        return None
    if hasattr(v, "isoformat"):
        return v.isoformat()
    return str(v)
