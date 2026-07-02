# FR-028 REST API (Phase 7.1) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship the FastAPI REST API (`api/` package) — 7 public endpoints + healthz + metrics over the existing shared query layer — so the `legalize-bg-web` Next.js frontend (Phase 7.2) has a complete, contract-locked backend.

**Architecture:** The REST API is a PEER of the MCP server (approved design `docs/plans/2026-05-11-phase7-legislation-browser-design.md`, D-050): both compose from `mcp_server/queries.py` + `index/fts.py`. Per D-050 the API does NOT inherit the MCP global lock — it opens a read-only SQLite connection PER REQUEST (with the D-051 pragmas) and closes it after the response. Error taxonomy is shared: the same `ToolError` codes map to HTTP statuses (recorded as D-052). Response shapes reuse the existing TypedDicts in `mcp_server/schemas.py` (already parity-locked to the dataclasses by `test_export_tools.py`).

**Tech Stack:** Python 3.12, FastAPI (new `api` extra), Uvicorn, sqlite3 + FTS5, pytest + Starlette TestClient (httpx 0.28.1 already installed via fastmcp).

## Global Constraints

- Interpreter: NO system `python`/`pytest` on PATH. Always `.venv/bin/python -m pytest ...` / `.venv/bin/python -m ...` from repo root `/Users/ekimir/swprj/legalize-bg`.
- Suite gate after EVERY task: `.venv/bin/python -m pytest -q -m "not perf"` must stay green (**478 passed, 7 deselected** at baseline). Do NOT run `tests/perf` (D-051 budgets are locked; perf runs need a quiet machine and are out of scope here).
- Protected surfaces: MCP tool signatures, SQLite schema, frontmatter schema, fetcher interfaces, commit format are NOT modified by this plan. Task 1 writes ONE preflight doc covering the two surface events this plan does have: (a) registration of the NEW "REST API v1 endpoint contract" surface in `.ahelia/protected-surfaces.yaml`; (b) relocation of four PRIVATE helpers from `mcp_server/server.py` to `mcp_server/queries.py` (internal refactor — tool signatures and behavior unchanged, covered by the existing 190-test mcp suite).
- `catalog.db` (1.2 GB, gitignored, 3,601 acts, at HEAD) is read-only for this plan — never rebuild it. Corpus `.md` files are data — never modified.
- Bulgarian text in code/tests: UTF-8 literals, never escaped sequences.
- Pipeline-code commits use conventional messages; each task ends with its own commit (message given per task).
- tools.json stays at 1.3.0 — this plan must NOT touch `mcp_server/export_tools.py`, `tools.json`, or the MCP tool docstrings.
- `git push` requires explicit owner authorization in the execution session. Ask ONCE when reaching Task 8 Step 6 (CI needs a push to run); Task 9's final push is covered by the same authorization.
- ERROR_CODES (12, from `mcp_server/errors.py`): LAW_NOT_FOUND, AMBIGUOUS_NAME, NO_VERSION_AT_DATE, DATE_UNCERTAIN, INVALID_ARTICLE_SPEC, ARTICLE_NOT_FOUND, INDEX_STALE, INDEX_MISSING, QUERY_TOO_BROAD, INVALID_DATE_RANGE, DIFF_FAILED, INVALID_DATE. `str(ToolError)` is compact JSON; `.code` / `.payload` / `.to_dict()` are the API of record.

## The D-052 error→HTTP mapping (ratify in Task 9's DECISIONS row; implement in Task 3)

| HTTP | Codes |
|---|---|
| 400 | INVALID_DATE, INVALID_ARTICLE_SPEC, INVALID_DATE_RANGE, QUERY_TOO_BROAD |
| 404 | LAW_NOT_FOUND, ARTICLE_NOT_FOUND, NO_VERSION_AT_DATE |
| 409 | AMBIGUOUS_NAME (body carries `candidates`) |
| 500 | DIFF_FAILED (+ any unknown code — defensive default) |
| 503 | INDEX_MISSING, INDEX_STALE |

DATE_UNCERTAIN is NOT an error — it rides in successful responses' `warnings` arrays, unchanged. Error body = `ToolError.to_dict()` verbatim: `{"code": "<CODE>", ...payload}` — the SAME shape as the MCP JSON error message (one taxonomy, two transports).

## Interface facts (verified 2026-07-02 — kwargs in plan code use THESE names)

- `queries.resolve_name_to_law_id(conn, name) -> str` — raises `LawNotFound(name, suggestions: list[dict])` / `AmbiguousName(name, candidates: list[dict])`.
- `queries.version_with_warnings(conn, law_id, date) -> tuple[commit: str, warnings: list[dict]]` — raises `NoVersionAtDate(law_id, date, earliest_available, latest_available)`; validates `date` (raises ToolError INVALID_DATE).
- `queries.full_text_search(conn, query, category=None, limit=20, include_body=False) -> list[dict]` (SearchHitDict shape) — raises ToolError QUERY_TOO_BROAD.
- `queries.parse_article_spec(spec) -> ArticleSpec(article, paragraph, range_end)` — raises `InvalidArticleSpec`.
- `queries.article_lookup(conn, law_id, article, paragraph, date) -> list[dict]` — raises `ArticleNotFound(law_id, article, paragraph, available_articles)`.
- `queries.law_history(conn, law_id) -> list[VersionEntry]` (dataclass with `.to_dict()`).
- `queries.diff_law_versions(conn, corpus_root, law_id, date1, date2) -> str` — raises ToolError INVALID_DATE_RANGE/INVALID_DATE/DIFF_FAILED, propagates NoVersionAtDate.
- After Task 2 (relocations): `queries.law_meta(conn, law_id) -> dict` (keys incl. `category`, `doc_id`, `current_commit`), `queries.read_law_markdown(corpus_root, law_id, category, commit_hash, current_commit) -> str` (raises ToolError INDEX_STALE), `queries.split_frontmatter(raw) -> tuple[dict, str]`, `queries.iso_date(v) -> str | None`.
- `laws` table columns: `law_id, doc_id, title, category, status, current_commit`. `law_versions`: `id, law_id, valid_from, valid_to, commit_hash, dv_issue, dv_date, amending_act, date_uncertain`.
- TypedDicts in `mcp_server/schemas.py` (reuse as FastAPI `response_model`): `GetLawResponseDict, SearchHitDict, GetArticleResponseDict, VersionEntryDict` (+ others not needed here).
- MCP tool bodies in `mcp_server/server.py` are the NORMATIVE composition reference (get_law ~line 340, get_article ~line 416). When this plan's endpoint code and server.py disagree on a call sequence, server.py wins — report the discrepancy, don't invent.

## Execution order

Tasks 1→9 strictly in order (2 depends on 1's install; 3 depends on 2's relocations; 4–7 depend on 3's app factory; 8 depends on all endpoints; 9 closes out).

---

### Task 1: Preflight + surface registration + `api` extra

**Files:**
- Create: `docs/process/IMPLEMENTATION-PREFLIGHT-2026-07-02-fr028-rest-api.md`
- Modify: `.ahelia/protected-surfaces.yaml` (append new surface)
- Modify: `pyproject.toml` (new optional dependency group `api`; packages include `api*`)

**Interfaces:**
- Produces: installed `fastapi`/`uvicorn` in `.venv`; the registered REST surface; the signed preflight.

- [ ] **Step 1: Write the preflight doc**

Create `docs/process/IMPLEMENTATION-PREFLIGHT-2026-07-02-fr028-rest-api.md` mirroring the section structure of `docs/process/IMPLEMENTATION-PREFLIGHT-2026-07-02-wire-contract.md` (protected surface → authoritative source → hard constraint → what's changing → violation risk → allowed scope → waiver → owner confirmation). Content, as one batch: (a) NEW protected surface "REST API v1 endpoint contract" (the 7 public endpoints + error mapping D-052) registered in `.ahelia/protected-surfaces.yaml` — additive, no existing surface touched; (b) internal relocation of `_law_meta`/`_read_law_markdown`/`_split_frontmatter`/`_iso` from `mcp_server/server.py` to public names in `mcp_server/queries.py` — NOT a Surface-3 event (tool signatures, shapes, and behavior unchanged; existing suite is the guard); (c) MCP server untouched otherwise; SQLite schema untouched (new SQL is read-only SELECTs). Owner sign-off: D-050 scope decision (1) of 2026-07-02 (REST API in this repo per approved Phase-7 design) + the owner's plan-approval of 2026-07-02.

- [ ] **Step 2: Register the surface**

Append to `.ahelia/protected-surfaces.yaml` (after the MCP tool-signatures entry, same style):

```yaml
  # --- REST API v1 Endpoint Contract (FR-028 / Phase 7.1) ---
  # Consumed by legalize-bg-web (Next.js frontend). Renaming/removing an
  # endpoint or changing a response field is a breaking change for the
  # frontend; additions are allowed (additive scope, like Surface 3).
  - path: "api/ (v1 endpoint contract)"
    reason: "REST API consumed by legalize-bg-web; error mapping per D-052"
    edit_mode: owner_review_required
    reference: "docs/plans/2026-07-02-fr028-rest-api-plan.md; docs/sync/DECISIONS.md D-052"
    protected_endpoints:
      - "GET /api/v1/laws"
      - "GET /api/v1/laws/{slug}"
      - "GET /api/v1/laws/{slug}/articles/{art}"
      - "GET /api/v1/laws/{slug}/history"
      - "GET /api/v1/laws/{slug}/diff"
      - "GET /api/v1/search"
      - "GET /api/v1/stats"
```

- [ ] **Step 3: Add the `api` extra and package**

In `pyproject.toml`: under `[project.optional-dependencies]` add:

```toml
api = [
    "fastapi>=0.115",
    "uvicorn>=0.30",
]
```

In `[tool.setuptools.packages.find]` change `include` to `["fetcher*", "index*", "mcp_server*", "api*"]`.

- [ ] **Step 4: Install and verify**

Run: `.venv/bin/pip install -e ".[dev,api]"` then `.venv/bin/python -c "import fastapi, uvicorn; print('api deps OK')"`
Expected: `api deps OK`.

- [ ] **Step 5: Suite gate + commit**

Run: `.venv/bin/python -m pytest -q -m "not perf"` → 478 passed.

```bash
git add docs/process/IMPLEMENTATION-PREFLIGHT-2026-07-02-fr028-rest-api.md .ahelia/protected-surfaces.yaml pyproject.toml
git commit -m "feat(api): FR-028 preflight + REST surface registration + fastapi/uvicorn extra"
```

---

### Task 2: Query-layer completion — relocate composition helpers + `list_laws` + `corpus_stats`

**Files:**
- Modify: `mcp_server/queries.py` (add 4 relocated helpers + 2 new functions)
- Modify: `mcp_server/server.py` (delete the 4 private helpers; import them from queries under the old names)
- Create: `tests/mcp_server/test_queries_listing.py`

**Interfaces:**
- Produces: `queries.law_meta(conn, law_id) -> dict`; `queries.read_law_markdown(corpus_root, law_id, category, commit_hash, current_commit) -> str`; `queries.split_frontmatter(raw) -> tuple[dict, str]`; `queries.iso_date(v) -> str | None`; `queries.list_laws(conn, category=None, estado=None, limit=50, offset=0) -> dict`; `queries.corpus_stats(conn) -> dict`. Tasks 3–7 consume all six.

- [ ] **Step 1: Relocate the four helpers**

Move these functions from `mcp_server/server.py` into `mcp_server/queries.py` VERBATIM (bodies unchanged), renamed public: `_split_frontmatter` (server.py:89) → `split_frontmatter`; `_law_meta` (server.py:114) → `law_meta`; `_read_law_markdown` (server.py:49) → `read_law_markdown`; `_iso` (server.py:784) → `iso_date`. Also move any import each needs (`yaml`, `subprocess` — check what queries.py already imports; add only what's missing). In `mcp_server/server.py`, delete the four bodies and add ONE aliased import so every call site stays untouched:

```python
from mcp_server.queries import (
    iso_date as _iso,
    law_meta as _law_meta,
    read_law_markdown as _read_law_markdown,
    split_frontmatter as _split_frontmatter,
)
```

HARD RULE: zero other edits to server.py. If a helper references another server.py-private name, STOP and report BLOCKED with the reference (do not chain-relocate without instruction).

- [ ] **Step 2: Run the mcp suite to prove the relocation is behavior-neutral**

Run: `.venv/bin/python -m pytest tests/mcp_server -q`
Expected: all pass (~190). Any failure = the relocation changed behavior — fix the relocation, never a test.

- [ ] **Step 3: Write the failing tests for the two new functions**

```python
# tests/mcp_server/test_queries_listing.py
"""FR-028: list_laws + corpus_stats power GET /api/v1/laws and /stats.
They are plain read-only SELECTs over `laws` + `law_versions`."""

import pytest

from mcp_server import queries


def test_list_laws_returns_total_and_items(conn):
    out = queries.list_laws(conn)
    assert set(out.keys()) == {"total", "items"}
    assert out["total"] >= 1
    first = out["items"][0]
    assert set(first.keys()) == {
        "law_id", "identificador", "title", "category", "status",
        "first_version", "latest_version", "version_count",
    }


def test_list_laws_category_filter_and_pagination(conn):
    all_laws = queries.list_laws(conn)
    cat = all_laws["items"][0]["category"]
    filtered = queries.list_laws(conn, category=cat)
    assert filtered["total"] <= all_laws["total"]
    assert all(i["category"] == cat for i in filtered["items"])
    page = queries.list_laws(conn, limit=1, offset=0)
    assert len(page["items"]) == 1
    assert page["total"] == all_laws["total"]  # total ignores pagination


def test_list_laws_caps_limit(conn):
    out = queries.list_laws(conn, limit=100000)
    assert len(out["items"]) <= 200


def test_corpus_stats_shape(conn):
    s = queries.corpus_stats(conn)
    assert set(s.keys()) == {
        "total_acts", "by_category", "by_status",
        "multi_version_acts", "latest_version_date",
    }
    assert s["total_acts"] == sum(s["by_category"].values())
```

(Reuse the existing `conn` fixture from `tests/mcp_server/conftest.py` — it seeds a populated catalog; do NOT build a new fixture.)

- [ ] **Step 4: Run to verify failure**

Run: `.venv/bin/python -m pytest tests/mcp_server/test_queries_listing.py -q`
Expected: FAIL — `AttributeError: module 'mcp_server.queries' has no attribute 'list_laws'`.

- [ ] **Step 5: Implement**

Append to `mcp_server/queries.py`:

```python
_MAX_LIST_LIMIT = 200


def list_laws(conn: sqlite3.Connection, category: str | None = None,
              estado: str | None = None, limit: int = 50,
              offset: int = 0) -> dict:
    """Paginated act listing for the REST API (FR-028).

    Returns {"total": N, "items": [...]}; `total` counts ALL rows
    matching the filters (pagination-independent, so a UI can render
    page controls). Dates come from `law_versions` (min/max valid_from),
    not from frontmatter reads — a list endpoint must not open 3,601
    files.
    """
    limit = max(1, min(int(limit), _MAX_LIST_LIMIT))
    offset = max(0, int(offset))
    where, params = [], []
    if category:
        where.append("l.category = ?")
        params.append(category)
    if estado:
        where.append("l.status = ?")
        params.append(estado)
    where_sql = ("WHERE " + " AND ".join(where)) if where else ""
    total = conn.execute(
        f"SELECT COUNT(*) FROM laws l {where_sql}", params).fetchone()[0]
    rows = conn.execute(
        f"""SELECT l.law_id, l.doc_id, l.title, l.category, l.status,
                   MIN(v.valid_from) AS first_version,
                   MAX(v.valid_from) AS latest_version,
                   COUNT(v.id) AS version_count
            FROM laws l LEFT JOIN law_versions v ON v.law_id = l.law_id
            {where_sql}
            GROUP BY l.law_id ORDER BY l.title
            LIMIT ? OFFSET ?""",
        params + [limit, offset]).fetchall()
    items = [{
        "law_id": r["law_id"], "identificador": str(r["doc_id"]),
        "title": r["title"], "category": r["category"],
        "status": r["status"], "first_version": r["first_version"],
        "latest_version": r["latest_version"],
        "version_count": r["version_count"],
    } for r in rows]
    return {"total": total, "items": items}


def corpus_stats(conn: sqlite3.Connection) -> dict:
    """Corpus stats for GET /api/v1/stats and the frontend sitemap."""
    total = conn.execute("SELECT COUNT(*) FROM laws").fetchone()[0]
    by_cat = dict(conn.execute(
        "SELECT category, COUNT(*) FROM laws GROUP BY category").fetchall())
    by_status = dict(conn.execute(
        "SELECT status, COUNT(*) FROM laws GROUP BY status").fetchall())
    multi = conn.execute(
        "SELECT COUNT(*) FROM (SELECT law_id FROM law_versions "
        "GROUP BY law_id HAVING COUNT(*) > 1)").fetchone()[0]
    latest = conn.execute(
        "SELECT MAX(valid_from) FROM law_versions").fetchone()[0]
    return {"total_acts": total, "by_category": by_cat,
            "by_status": by_status, "multi_version_acts": multi,
            "latest_version_date": latest}
```

- [ ] **Step 6: Run tests + full gate + commit**

Run: `.venv/bin/python -m pytest tests/mcp_server/test_queries_listing.py tests/mcp_server -q` → all pass.
Run: `.venv/bin/python -m pytest -q -m "not perf"` → 482 passed (478 + 4 new).

```bash
git add mcp_server/queries.py mcp_server/server.py tests/mcp_server/test_queries_listing.py
git commit -m "feat(queries): public composition helpers + list_laws/corpus_stats for the REST API (FR-028)"
```

---

### Task 3: API skeleton — errors, per-request connections, app factory, healthz

**Files:**
- Create: `api/__init__.py` (empty), `api/errors.py`, `api/deps.py`, `api/app.py`
- Create: `tests/api/__init__.py` (empty), `tests/api/conftest.py`, `tests/api/test_app_skeleton.py`

**Interfaces:**
- Produces: `api.app.create_app(db_path: str, corpus_root: Path, cors_origins: list[str] | None = None) -> FastAPI` — Tasks 4–8 register routes on / test against it. `api.deps.get_conn` FastAPI dependency yielding a per-request ro connection. `api.errors.HTTP_STATUS_BY_CODE` + `install_error_handlers(app)`.

- [ ] **Step 1: Write the failing tests**

```python
# tests/api/conftest.py
"""Shared API fixture: a REAL 2-commit corpus + built catalog FILE
(per-request `mode=ro` connections require a file DB, not :memory:),
served through the actual FastAPI app via TestClient."""

import os
import subprocess
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from api.app import create_app
from index.build import build


def _commit(corpus, msg, date):
    env = dict(os.environ, GIT_AUTHOR_DATE=f"{date}T00:00:00+00:00",
               GIT_COMMITTER_DATE=f"{date}T00:00:00+00:00")
    subprocess.run(["git", "add", "-A"], cwd=corpus, check=True)
    subprocess.run(
        ["git", "-c", "user.email=t@t", "-c", "user.name=t",
         "commit", "-q", "-m", msg], cwd=corpus, check=True, env=env)


@pytest.fixture(scope="module")
def api_corpus(tmp_path_factory):
    corpus = tmp_path_factory.mktemp("api-corpus")
    law = corpus / "laws" / "zakon-vremeto.md"
    law.parent.mkdir(parents=True)
    fm = ("---\ntitulo: Закон за времето\nidentificador: 777\n"
          "fecha_publicacion: 2020-01-01\n---\n\n")
    law.write_text(fm + "**Чл. 1.** (1) СТАРА редакция. (2) Втора алинея.\n",
                   encoding="utf-8")
    subprocess.run(["git", "init", "-q"], cwd=corpus, check=True)
    _commit(corpus, "[bootstrap] Закон за времето", "2020-01-01")
    law.write_text(fm + "**Чл. 1.** (1) НОВА редакция. (2) Втора алинея.\n",
                   encoding="utf-8")
    _commit(corpus, "[reforma] Закон за времето", "2021-06-15")
    db = str(corpus / "catalog.db")
    build(corpus, db)
    return corpus, db


@pytest.fixture()
def client(api_corpus):
    corpus, db = api_corpus
    app = create_app(db_path=db, corpus_root=Path(corpus))
    with TestClient(app) as c:
        yield c
```

```python
# tests/api/test_app_skeleton.py
"""FR-028 Task 3: app factory, healthz, per-request connections,
D-052 error mapping."""

from mcp_server.errors import ToolError


def test_healthz(client):
    r = client.get("/healthz")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_tool_error_maps_to_http_status_and_json_body(client):
    # No route raises INDEX_MISSING cheaply, so assert on the mapping
    # table + handler via a nonexistent law (LAW_NOT_FOUND → 404),
    # which exercises the full exception→JSON path end to end in Task 5.
    # Here: the mapping table itself is the contract.
    from api.errors import HTTP_STATUS_BY_CODE
    from mcp_server.errors import ERROR_CODES
    mapped = set(HTTP_STATUS_BY_CODE)
    assert mapped == ERROR_CODES - {"DATE_UNCERTAIN"}, (
        "every error code except the DATE_UNCERTAIN warning must map")


def test_unknown_route_is_plain_404(client):
    assert client.get("/api/v1/nope").status_code == 404


def test_cors_headers_present(api_corpus):
    from pathlib import Path
    from fastapi.testclient import TestClient
    from api.app import create_app
    corpus, db = api_corpus
    app = create_app(db_path=db, corpus_root=Path(corpus),
                     cors_origins=["http://localhost:3000"])
    with TestClient(app) as c:
        r = c.get("/healthz", headers={"Origin": "http://localhost:3000"})
        assert r.headers.get("access-control-allow-origin") == "http://localhost:3000"
```

- [ ] **Step 2: Run to verify failure**

Run: `.venv/bin/python -m pytest tests/api -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'api'`.

- [ ] **Step 3: Implement `api/errors.py`**

```python
"""D-052: shared ToolError taxonomy → HTTP statuses. One taxonomy, two
transports — the JSON body is ToolError.to_dict(), byte-compatible with
what an MCP client parses out of str(ToolError)."""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from mcp_server import queries
from mcp_server.errors import ToolError

HTTP_STATUS_BY_CODE = {
    "INVALID_DATE": 400,
    "INVALID_ARTICLE_SPEC": 400,
    "INVALID_DATE_RANGE": 400,
    "QUERY_TOO_BROAD": 400,
    "LAW_NOT_FOUND": 404,
    "ARTICLE_NOT_FOUND": 404,
    "NO_VERSION_AT_DATE": 404,
    "AMBIGUOUS_NAME": 409,
    "DIFF_FAILED": 500,
    "INDEX_MISSING": 503,
    "INDEX_STALE": 503,
}

_SPEC_EXAMPLES = ["чл. 5", "чл. 5, ал. 2", "5.2", "чл. 5-7"]


def _json(code: str, payload: dict) -> JSONResponse:
    return JSONResponse(status_code=HTTP_STATUS_BY_CODE.get(code, 500),
                        content={"code": code, **payload})


def install_error_handlers(app: FastAPI) -> None:
    """Map the query layer's exceptions + ToolError to D-052 responses.
    Endpoints stay thin: they call queries and let exceptions fly."""

    @app.exception_handler(ToolError)
    async def _tool_error(request: Request, exc: ToolError):
        return JSONResponse(
            status_code=HTTP_STATUS_BY_CODE.get(exc.code, 500),
            content=exc.to_dict())

    @app.exception_handler(queries.LawNotFound)
    async def _law_not_found(request: Request, exc: queries.LawNotFound):
        return _json("LAW_NOT_FOUND",
                     {"name": exc.name, "suggestions": exc.suggestions})

    @app.exception_handler(queries.AmbiguousName)
    async def _ambiguous(request: Request, exc: queries.AmbiguousName):
        return _json("AMBIGUOUS_NAME",
                     {"name": exc.name, "candidates": exc.candidates})

    @app.exception_handler(queries.NoVersionAtDate)
    async def _no_version(request: Request, exc: queries.NoVersionAtDate):
        return _json("NO_VERSION_AT_DATE", {
            "law_id": exc.law_id, "date": exc.date,
            "earliest_available": exc.earliest_available,
            "latest_available": exc.latest_available})

    @app.exception_handler(queries.ArticleNotFound)
    async def _article_not_found(request: Request,
                                 exc: queries.ArticleNotFound):
        return _json("ARTICLE_NOT_FOUND", {
            "law_id": exc.law_id, "article": exc.article,
            "paragraph": exc.paragraph,
            "available_articles": exc.available_articles})

    @app.exception_handler(queries.InvalidArticleSpec)
    async def _invalid_spec(request: Request,
                            exc: queries.InvalidArticleSpec):
        return _json("INVALID_ARTICLE_SPEC",
                     {"detail": str(exc), "examples": _SPEC_EXAMPLES})
```

- [ ] **Step 4: Implement `api/deps.py`**

```python
"""Per-request read-only connections (D-050: the REST API does NOT
inherit the MCP global lock). Each request opens its own `mode=ro`
connection with the D-051 pragmas and closes it after the response.
`check_same_thread=False` is REQUIRED: FastAPI may run a sync
dependency and its endpoint on different threadpool threads."""

import sqlite3
from collections.abc import Iterator

from fastapi import Request


def get_conn(request: Request) -> Iterator[sqlite3.Connection]:
    db_path = request.app.state.db_path
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True,
                           check_same_thread=False)
    conn.row_factory = sqlite3.Row
    # D-051 (FR-027): memory-map the 1.2 GB catalog + 64 MB page cache.
    conn.execute("PRAGMA mmap_size = 1073741824")
    conn.execute("PRAGMA cache_size = -65536")
    try:
        yield conn
    finally:
        conn.close()
```

- [ ] **Step 5: Implement `api/app.py`**

```python
"""FastAPI application factory (FR-028 / Phase 7.1).

The REST API is a peer of the MCP server over the shared query layer
(design docs/plans/2026-05-11-phase7-legislation-browser-design.md;
D-050). HTTP concerns live here: CORS, per-request connections,
D-052 error mapping, cache headers, metrics."""

from pathlib import Path

from fastapi import FastAPI

from api.errors import install_error_handlers

API_VERSION = "1.0.0"


def create_app(db_path: str, corpus_root: Path,
               cors_origins: list[str] | None = None) -> FastAPI:
    app = FastAPI(title="legalize-bg REST API", version=API_VERSION,
                  docs_url="/api/v1/docs",
                  openapi_url="/api/v1/openapi.json")
    app.state.db_path = str(db_path)
    app.state.corpus_root = Path(corpus_root)

    if cors_origins:
        from fastapi.middleware.cors import CORSMiddleware
        app.add_middleware(CORSMiddleware, allow_origins=cors_origins,
                           allow_methods=["GET"], allow_headers=["*"])

    install_error_handlers(app)

    @app.get("/healthz")
    def healthz() -> dict:
        return {"status": "ok"}

    # Routers are attached by later tasks (laws, search, stats, metrics).
    _include_routers(app)
    return app


def _include_routers(app: FastAPI) -> None:
    """Import-and-include hook; each routes module is added by its task.
    Keeping the imports here (not module-level) lets create_app stay the
    single composition point."""
    # Task 4: from api.routes import laws_list, stats
    # Task 5: from api.routes import laws
    # Task 6: from api.routes import history_diff, search
    # Task 7: metrics middleware + endpoint
    return None
```

Also create empty `api/__init__.py` and `tests/api/__init__.py`, and `api/routes/__init__.py` (empty — routes modules land in Tasks 4–6).

- [ ] **Step 6: Run tests + gate + commit**

Run: `.venv/bin/python -m pytest tests/api -q` → 4 passed.
Run: `.venv/bin/python -m pytest -q -m "not perf"` → 486 passed.

```bash
git add api/ tests/api/
git commit -m "feat(api): app factory, per-request ro connections, D-052 error handlers, healthz (FR-028)"
```

---

### Task 4: `GET /api/v1/laws` + `GET /api/v1/stats`

**Files:**
- Create: `api/routes/laws_list.py`, `api/routes/stats.py`, `api/schemas.py`
- Modify: `api/app.py` (`_include_routers`)
- Create: `tests/api/test_laws_list.py`

**Interfaces:**
- Consumes: `queries.list_laws`, `queries.corpus_stats` (Task 2), `api.deps.get_conn`.
- Produces: the two endpoints; `api/schemas.py` TypedDicts `LawSummaryDict, LawListResponseDict, StatsResponseDict, DiffResponseDict` (DiffResponseDict used by Task 6).

- [ ] **Step 1: Write the failing tests**

```python
# tests/api/test_laws_list.py
def test_list_laws_returns_seeded_act(client):
    r = client.get("/api/v1/laws")
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 1
    assert body["items"][0]["law_id"] == "zakon-vremeto"
    assert body["items"][0]["title"] == "Закон за времето"


def test_list_laws_filters_and_paginates(client):
    assert client.get("/api/v1/laws",
                      params={"category": "laws"}).json()["total"] == 1
    assert client.get("/api/v1/laws",
                      params={"category": "codes"}).json()["total"] == 0
    page = client.get("/api/v1/laws", params={"limit": 1, "offset": 5}).json()
    assert page["total"] == 1 and page["items"] == []


def test_stats(client):
    r = client.get("/api/v1/stats")
    assert r.status_code == 200
    s = r.json()
    assert s["total_acts"] == 1
    assert s["by_category"] == {"laws": 1}
    assert s["multi_version_acts"] == 1   # the 2-commit fixture act
```

- [ ] **Step 2: Run to verify failure**

Run: `.venv/bin/python -m pytest tests/api/test_laws_list.py -q`
Expected: FAIL — 404 on both routes (routers not registered).

- [ ] **Step 3: Implement**

```python
# api/schemas.py
"""API-only wire shapes (TypedDicts, same convention as
mcp_server/schemas.py — used as FastAPI response_model only)."""

from typing import TypedDict


class LawSummaryDict(TypedDict):
    law_id: str
    identificador: str
    title: str
    category: str
    status: str
    first_version: str | None
    latest_version: str | None
    version_count: int


class LawListResponseDict(TypedDict):
    total: int
    items: list[LawSummaryDict]


class StatsResponseDict(TypedDict):
    total_acts: int
    by_category: dict[str, int]
    by_status: dict[str, int]
    multi_version_acts: int
    latest_version_date: str | None


class DiffResponseDict(TypedDict):
    law_id: str
    from_date: str
    to_date: str
    diff: str
```

```python
# api/routes/laws_list.py
import sqlite3

from fastapi import APIRouter, Depends

from api.deps import get_conn
from api.schemas import LawListResponseDict
from mcp_server import queries

router = APIRouter(prefix="/api/v1")


@router.get("/laws", response_model=LawListResponseDict)
def list_laws(category: str | None = None, estado: str | None = None,
              limit: int = 50, offset: int = 0,
              conn: sqlite3.Connection = Depends(get_conn)):
    return queries.list_laws(conn, category=category, estado=estado,
                             limit=limit, offset=offset)
```

```python
# api/routes/stats.py
import sqlite3

from fastapi import APIRouter, Depends

from api.deps import get_conn
from api.schemas import StatsResponseDict
from mcp_server import queries

router = APIRouter(prefix="/api/v1")


@router.get("/stats", response_model=StatsResponseDict)
def stats(conn: sqlite3.Connection = Depends(get_conn)):
    return queries.corpus_stats(conn)
```

In `api/app.py`, replace `_include_routers`'s body:

```python
def _include_routers(app: FastAPI) -> None:
    from api.routes import laws_list, stats
    app.include_router(laws_list.router)
    app.include_router(stats.router)
```

- [ ] **Step 4: Run tests + gate + commit**

Run: `.venv/bin/python -m pytest tests/api -q` → all pass.
Run: `.venv/bin/python -m pytest -q -m "not perf"` → 489 passed.

```bash
git add api/ tests/api/test_laws_list.py
git commit -m "feat(api): GET /api/v1/laws + /api/v1/stats (FR-028)"
```

---

### Task 5: `GET /api/v1/laws/{slug}` + `GET /api/v1/laws/{slug}/articles/{art}`

**Files:**
- Create: `api/routes/laws.py`
- Modify: `api/app.py` (`_include_routers`)
- Create: `tests/api/test_law_read.py`

**Interfaces:**
- Consumes: `queries.resolve_name_to_law_id`, `version_with_warnings`, `law_meta`, `read_law_markdown`, `split_frontmatter`, `iso_date`, `parse_article_spec`, `article_lookup`; TypedDicts `GetLawResponseDict`, `GetArticleResponseDict` from `mcp_server/schemas.py`.
- Produces: the two read endpoints. Composition mirrors the MCP `get_law`/`get_article` tool bodies in `mcp_server/server.py` (~lines 340 and 416) — server.py is normative on call sequence.

- [ ] **Step 1: Write the failing tests**

```python
# tests/api/test_law_read.py
def test_get_law_current(client):
    r = client.get("/api/v1/laws/zakon-vremeto")
    assert r.status_code == 200
    body = r.json()
    assert body["law_id"] == "zakon-vremeto"
    assert body["titulo"] == "Закон за времето"
    assert "НОВА редакция" in body["body_markdown"]
    assert body["warnings"] == []


def test_get_law_historical_date(client):
    r = client.get("/api/v1/laws/zakon-vremeto", params={"date": "2020-06-01"})
    assert r.status_code == 200
    assert "СТАРА редакция" in r.json()["body_markdown"]


def test_get_law_not_found_is_404_with_taxonomy_body(client):
    r = client.get("/api/v1/laws/nesashtestvuvasht-akt")
    assert r.status_code == 404
    assert r.json()["code"] == "LAW_NOT_FOUND"
    assert "suggestions" in r.json()


def test_get_law_bad_date_is_400(client):
    r = client.get("/api/v1/laws/zakon-vremeto", params={"date": "утре"})
    assert r.status_code == 400
    assert r.json()["code"] == "INVALID_DATE"


def test_get_law_before_first_version_is_404(client):
    r = client.get("/api/v1/laws/zakon-vremeto", params={"date": "1990-01-01"})
    assert r.status_code == 404
    assert r.json()["code"] == "NO_VERSION_AT_DATE"


def test_get_article(client):
    r = client.get("/api/v1/laws/zakon-vremeto/articles/чл. 1, ал. 2")
    assert r.status_code == 200
    body = r.json()
    assert body["article"] == "1" and body["paragraph"] == "2"
    assert "Втора алинея" in body["text"]


def test_get_article_range_rejected(client):
    r = client.get("/api/v1/laws/zakon-vremeto/articles/чл. 1-3")
    assert r.status_code == 400
    assert r.json()["code"] == "INVALID_ARTICLE_SPEC"


def test_get_article_missing_is_404(client):
    r = client.get("/api/v1/laws/zakon-vremeto/articles/чл. 99")
    assert r.status_code == 404
    body = r.json()
    assert body["code"] == "ARTICLE_NOT_FOUND"
    assert body["available_articles"]
```

- [ ] **Step 2: Run to verify failure**

Run: `.venv/bin/python -m pytest tests/api/test_law_read.py -q`
Expected: FAIL — 404 on all (router absent).

- [ ] **Step 3: Implement `api/routes/laws.py`**

```python
"""Law + article read endpoints. Composition mirrors the MCP get_law /
get_article tool bodies (mcp_server/server.py) over per-request
connections; the query layer raises, api/errors.py maps (D-052)."""

import sqlite3

from fastapi import APIRouter, Depends, Request, Response

from api.deps import get_conn
from mcp_server import queries
from mcp_server.errors import ToolError
from mcp_server.schemas import GetArticleResponseDict, GetLawResponseDict

router = APIRouter(prefix="/api/v1")

_CACHE = "public, max-age=300"


@router.get("/laws/{slug}", response_model=GetLawResponseDict)
def get_law(slug: str, request: Request, response: Response,
            date: str | None = None,
            conn: sqlite3.Connection = Depends(get_conn)):
    law_id = queries.resolve_name_to_law_id(conn, slug)
    commit, warnings = queries.version_with_warnings(conn, law_id, date)
    meta_row = queries.law_meta(conn, law_id)
    raw = queries.read_law_markdown(
        request.app.state.corpus_root, law_id, meta_row["category"],
        commit, meta_row["current_commit"])
    fm, body = queries.split_frontmatter(raw)
    response.headers["Cache-Control"] = _CACHE
    return {
        "law_id": law_id,
        "identificador": str(meta_row["doc_id"]),
        "titulo": fm.get("titulo") or "",
        "category": meta_row["category"],
        "fecha_publicacion": queries.iso_date(fm.get("fecha_publicacion")),
        "ultima_actualizacion": queries.iso_date(fm.get("ultima_actualizacion")),
        "dv_issue": fm.get("dv_issue"),
        "dv_year": fm.get("dv_year"),
        "effective_date": queries.iso_date(fm.get("effective_date")),
        "eli": fm.get("eli"),
        "amendment_history": fm.get("amendment_history") or [],
        "commit_hash": commit,
        "body_markdown": body,
        "warnings": warnings,
    }


@router.get("/laws/{slug}/articles/{art}",
            response_model=GetArticleResponseDict)
def get_article(slug: str, art: str, response: Response,
                date: str | None = None,
                conn: sqlite3.Connection = Depends(get_conn)):
    law_id = queries.resolve_name_to_law_id(conn, slug)
    commit, warnings = queries.version_with_warnings(conn, law_id, date)
    spec = queries.parse_article_spec(art)
    if spec.range_end is not None:
        raise ToolError("INVALID_ARTICLE_SPEC", {
            "spec": art,
            "detail": "ranges are not served by this endpoint — request "
                      "single articles (the MCP get_articles tool serves "
                      "ranges)",
            "examples": ["чл. 5", "чл. 5, ал. 2"],
        })
    rows = queries.article_lookup(conn, law_id, spec.article,
                                  spec.paragraph, date)
    row = rows[0]
    response.headers["Cache-Control"] = _CACHE
    return {
        "law_id": law_id,
        "article": row["article"],
        "paragraph": row["paragraph"],
        "text": row["text"],
        "text_hash": row["text_hash"],
        "commit_hash": commit,
        "warnings": warnings,
    }
```

In `api/app.py` `_include_routers`, add:

```python
    from api.routes import laws
    app.include_router(laws.router)
```

NOTE for the implementer: before running, compare this composition against the real `get_law`/`get_article` bodies in `mcp_server/server.py`. If a call there differs (argument, ordering, an extra normalization step), server.py WINS — adjust this file to match and record the difference in your report. The row-dict keys (`article`, `paragraph`, `text`, `text_hash`) must match what `article_lookup` actually returns — check its return construction in queries.py.

- [ ] **Step 4: Run tests + gate + commit**

Run: `.venv/bin/python -m pytest tests/api -q` → all pass.
Run: `.venv/bin/python -m pytest -q -m "not perf"` → 497 passed.

```bash
git add api/ tests/api/test_law_read.py
git commit -m "feat(api): GET /laws/{slug} + /laws/{slug}/articles/{art} with ?date= (FR-028)"
```

---

### Task 6: `GET .../history`, `GET .../diff`, `GET /api/v1/search`

**Files:**
- Create: `api/routes/history_diff.py`, `api/routes/search.py`
- Modify: `api/app.py` (`_include_routers`)
- Create: `tests/api/test_history_diff_search.py`

**Interfaces:**
- Consumes: `queries.law_history`, `queries.diff_law_versions`, `queries.full_text_search`; `VersionEntryDict`, `SearchHitDict` from `mcp_server/schemas.py`; `DiffResponseDict` from `api/schemas.py`.
- Produces: the last three public endpoints.

- [ ] **Step 1: Write the failing tests**

```python
# tests/api/test_history_diff_search.py
def test_history_lists_versions(client):
    r = client.get("/api/v1/laws/zakon-vremeto/history")
    assert r.status_code == 200
    entries = r.json()
    assert isinstance(entries, list) and entries
    assert entries[-1]["operation"] == "consolidated"


def test_diff_between_the_two_versions(client):
    r = client.get("/api/v1/laws/zakon-vremeto/diff",
                   params={"from": "2020-06-01", "to": "2021-12-31"})
    assert r.status_code == 200
    body = r.json()
    assert body["law_id"] == "zakon-vremeto"
    assert "-**Чл. 1.** (1) СТАРА редакция." in body["diff"]
    assert "+**Чл. 1.** (1) НОВА редакция." in body["diff"]


def test_diff_reversed_range_is_400(client):
    r = client.get("/api/v1/laws/zakon-vremeto/diff",
                   params={"from": "2021-12-31", "to": "2020-06-01"})
    assert r.status_code == 400
    assert r.json()["code"] == "INVALID_DATE_RANGE"


def test_diff_missing_params_is_422(client):
    assert client.get("/api/v1/laws/zakon-vremeto/diff").status_code == 422


def test_search_finds_the_act(client):
    r = client.get("/api/v1/search", params={"q": "времето"})
    assert r.status_code == 200
    hits = r.json()
    assert hits and hits[0]["law_id"] == "zakon-vremeto"


def test_search_missing_q_is_422(client):
    assert client.get("/api/v1/search").status_code == 422


def test_search_overlong_query_is_400(client):
    r = client.get("/api/v1/search", params={"q": "закон " * 200})
    assert r.status_code == 400
    assert r.json()["code"] == "QUERY_TOO_BROAD"
```

- [ ] **Step 2: Run to verify failure**

Run: `.venv/bin/python -m pytest tests/api/test_history_diff_search.py -q`
Expected: FAIL — 404s (routers absent).

- [ ] **Step 3: Implement**

```python
# api/routes/history_diff.py
import sqlite3

from fastapi import APIRouter, Depends, Query, Request, Response

from api.deps import get_conn
from api.schemas import DiffResponseDict
from mcp_server import queries
from mcp_server.schemas import VersionEntryDict

router = APIRouter(prefix="/api/v1")


@router.get("/laws/{slug}/history", response_model=list[VersionEntryDict])
def history(slug: str, response: Response,
            conn: sqlite3.Connection = Depends(get_conn)):
    law_id = queries.resolve_name_to_law_id(conn, slug)
    response.headers["Cache-Control"] = "public, max-age=300"
    return [e.to_dict() for e in queries.law_history(conn, law_id)]


@router.get("/laws/{slug}/diff", response_model=DiffResponseDict)
def diff(slug: str, request: Request,
         from_date: str = Query(alias="from"),
         to_date: str = Query(alias="to"),
         conn: sqlite3.Connection = Depends(get_conn)):
    law_id = queries.resolve_name_to_law_id(conn, slug)
    text = queries.diff_law_versions(
        conn, request.app.state.corpus_root, law_id, from_date, to_date)
    return {"law_id": law_id, "from_date": from_date,
            "to_date": to_date, "diff": text}
```

```python
# api/routes/search.py
import sqlite3

from fastapi import APIRouter, Depends, Query, Response

from api.deps import get_conn
from mcp_server import queries
from mcp_server.schemas import SearchHitDict

router = APIRouter(prefix="/api/v1")


@router.get("/search", response_model=list[SearchHitDict])
def search(response: Response, q: str = Query(min_length=1),
           category: str | None = None, limit: int = 20,
           include_body: bool = False,
           conn: sqlite3.Connection = Depends(get_conn)):
    response.headers["Cache-Control"] = "public, max-age=60"
    return queries.full_text_search(conn, q, category=category,
                                    limit=limit, include_body=include_body)
```

In `api/app.py` `_include_routers`, add:

```python
    from api.routes import history_diff, search
    app.include_router(history_diff.router)
    app.include_router(search.router)
```

NOTE: `law_history` returns `VersionEntry` dataclasses — the endpoint converts via `.to_dict()`. If `VersionEntry` has no `to_dict()` (check `mcp_server/schemas.py`), use `dataclasses.asdict(e)` instead and say so in your report.

- [ ] **Step 4: Run tests + gate + commit**

Run: `.venv/bin/python -m pytest tests/api -q` → all pass.
Run: `.venv/bin/python -m pytest -q -m "not perf"` → 505 passed.

```bash
git add api/ tests/api/test_history_diff_search.py
git commit -m "feat(api): history, diff, and search endpoints — REST surface complete (FR-028)"
```

---

### Task 7: Metrics middleware + `GET /api/v1/metrics`

**Files:**
- Create: `api/metrics.py`
- Modify: `api/app.py`
- Create: `tests/api/test_metrics.py`

**Interfaces:**
- Produces: per-route counters (calls, errors, total_ms) collected by an HTTP middleware, exposed at `/api/v1/metrics` (no auth — same trust model as the rest of the read-only API; D-050 assigns /metrics to the API surface).

- [ ] **Step 1: Write the failing test**

```python
# tests/api/test_metrics.py
def test_metrics_counts_requests_and_errors(client):
    client.get("/api/v1/stats")
    client.get("/api/v1/laws/nesashtestvuvasht-akt")   # 404 → error count
    r = client.get("/api/v1/metrics")
    assert r.status_code == 200
    m = r.json()
    stats_m = m["/api/v1/stats"]
    assert stats_m["calls"] >= 1 and stats_m["errors"] == 0
    law_m = m["/api/v1/laws/{slug}"]
    assert law_m["errors"] >= 1
    assert "avg_ms" in stats_m
```

- [ ] **Step 2: Run to verify failure**

Run: `.venv/bin/python -m pytest tests/api/test_metrics.py -q`
Expected: FAIL — 404 on /api/v1/metrics.

- [ ] **Step 3: Implement `api/metrics.py`**

```python
"""Per-route API metrics. Route-template keyed (`/api/v1/laws/{slug}`,
not the concrete URL) so cardinality stays bounded. Thread-safe: the
middleware runs concurrently across requests."""

import threading
import time

from fastapi import FastAPI, Request


class ApiMetrics:
    def __init__(self):
        self._lock = threading.Lock()
        self._data: dict[str, dict] = {}

    def record(self, route: str, ok: bool, ms: float) -> None:
        with self._lock:
            m = self._data.setdefault(
                route, {"calls": 0, "errors": 0, "total_ms": 0.0})
            m["calls"] += 1
            if not ok:
                m["errors"] += 1
            m["total_ms"] += ms

    def snapshot(self) -> dict:
        with self._lock:
            return {route: {**m, "avg_ms": round(m["total_ms"] / m["calls"], 2)}
                    for route, m in self._data.items()}


def install_metrics(app: FastAPI) -> None:
    metrics = ApiMetrics()
    app.state.metrics = metrics

    @app.middleware("http")
    async def _measure(request: Request, call_next):
        t0 = time.perf_counter()
        response = await call_next(request)
        route = getattr(request.scope.get("route"), "path", None)
        if route and route != "/api/v1/metrics":
            metrics.record(route, ok=response.status_code < 400,
                           ms=(time.perf_counter() - t0) * 1000)
        return response

    @app.get("/api/v1/metrics")
    def get_metrics() -> dict:
        return metrics.snapshot()
```

In `api/app.py`, inside `create_app` after `install_error_handlers(app)`:

```python
    from api.metrics import install_metrics
    install_metrics(app)
```

- [ ] **Step 4: Run tests + gate + commit**

Run: `.venv/bin/python -m pytest tests/api -q` → all pass.
Run: `.venv/bin/python -m pytest -q -m "not perf"` → 506 passed.

```bash
git add api/ tests/api/test_metrics.py
git commit -m "feat(api): per-route metrics middleware + /api/v1/metrics (FR-028)"
```

---

### Task 8: CLI entry point, OpenAPI contract export, CI wiring

**Files:**
- Create: `api/__main__.py`, `api/export_openapi.py`
- Modify: `pyproject.toml` (console script), `.github/workflows/ci.yml`
- Create: `docs/api/openapi-rest.json` (generated), `tests/api/test_export_openapi.py`

**Interfaces:**
- Produces: `legalize-bg-api [--db PATH] [--corpus PATH] [--host H] [--port N] [--cors-origin URL ...]` console entry; `python -m api.export_openapi --output|--check docs/api/openapi-rest.json` (same contract-lock pattern as `mcp_server.export_tools`).

- [ ] **Step 1: Write the failing parity test**

```python
# tests/api/test_export_openapi.py
"""Lock docs/api/openapi-rest.json to the live app schema, exactly like
tools.json is locked to the MCP tool schemas."""

import subprocess
import sys
from pathlib import Path

EXPECTED_PATHS = {
    "/healthz", "/api/v1/laws", "/api/v1/laws/{slug}",
    "/api/v1/laws/{slug}/articles/{art}", "/api/v1/laws/{slug}/history",
    "/api/v1/laws/{slug}/diff", "/api/v1/search", "/api/v1/stats",
    "/api/v1/metrics",
}


def test_openapi_export_covers_all_endpoints():
    from api.export_openapi import generate_spec
    spec = generate_spec()
    assert set(spec["paths"].keys()) == EXPECTED_PATHS
    assert spec["info"]["version"] == "1.0.0"


def test_committed_spec_matches_live():
    assert Path("docs/api/openapi-rest.json").exists(), (
        "run: .venv/bin/python -m api.export_openapi "
        "--output docs/api/openapi-rest.json")
    rc = subprocess.run(
        [sys.executable, "-m", "api.export_openapi",
         "--check", "docs/api/openapi-rest.json"]).returncode
    assert rc == 0
```

- [ ] **Step 2: Run to verify failure**

Run: `.venv/bin/python -m pytest tests/api/test_export_openapi.py -q`
Expected: FAIL — `ModuleNotFoundError: api.export_openapi`.

- [ ] **Step 3: Implement**

```python
# api/export_openapi.py
"""Export/verify the REST OpenAPI contract (FR-028) — the REST analogue
of mcp_server.export_tools. The spec is generated from a THROWAWAY app
instance (db need not exist; no request is served)."""

import argparse
import json
import sys
from pathlib import Path

from api.app import create_app


def generate_spec() -> dict:
    app = create_app(db_path="catalog.db", corpus_root=Path("."))
    return app.openapi()


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--output", type=Path)
    g.add_argument("--check", type=Path)
    args = ap.parse_args(argv)
    spec = json.dumps(generate_spec(), ensure_ascii=False, indent=2,
                      sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(spec, encoding="utf-8")
        print(f"wrote {args.output}")
        return 0
    committed = args.check.read_text(encoding="utf-8")
    if committed != spec:
        print("openapi-rest.json is STALE — regenerate with --output",
              file=sys.stderr)
        return 1
    print(f"OK: {args.check} matches live app (version="
          f"{generate_spec()['info']['version']}).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

```python
# api/__main__.py
"""`legalize-bg-api` / `python -m api` — run the REST API with uvicorn."""

import argparse
import sys
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="legalize-bg-api",
        description="legalize-bg REST API (FR-028) — FastAPI over the "
                    "shared query layer; per-request ro connections.")
    ap.add_argument("--db", type=Path, default=Path("catalog.db"))
    ap.add_argument("--corpus", type=Path, default=Path("."))
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8228)
    ap.add_argument("--cors-origin", action="append", default=[],
                    help="allowed origin (repeatable); e.g. "
                         "http://localhost:3000 for the Next.js dev server")
    args = ap.parse_args(argv)
    if not args.db.exists():
        print(f"catalog not found: {args.db} — run `python -m index.build` "
              "first", file=sys.stderr)
        return 2
    import uvicorn
    from api.app import create_app
    app = create_app(db_path=str(args.db), corpus_root=args.corpus,
                     cors_origins=args.cors_origin or None)
    uvicorn.run(app, host=args.host, port=args.port)
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

`pyproject.toml` `[project.scripts]` gains:

```toml
legalize-bg-api = "api.__main__:main"
```

Generate the committed spec: `.venv/bin/python -m api.export_openapi --output docs/api/openapi-rest.json`
Re-install entry point: `.venv/bin/pip install -e ".[dev,api]" -q`

- [ ] **Step 4: Wire CI**

In `.github/workflows/ci.yml`: in the `test` job change the install line to `python -m pip install -e ".[dev,api]"` and add after the export_tools check: `- run: python -m api.export_openapi --check docs/api/openapi-rest.json`. In `install-smoke` change `pip install .` to `pip install ".[api]"` and add `- run: /tmp/smoke/bin/legalize-bg-api --help` after the mcp --help line. Change NOTHING else in the workflow.

- [ ] **Step 5: Run tests + gate**

Run: `.venv/bin/python -m pytest tests/api -q` → all pass (incl. both export tests).
Run: `.venv/bin/python -m pytest -q -m "not perf"` → 508 passed.
Run: `.venv/bin/python -m legalize_bg_api_help_check 2>/dev/null; .venv/bin/legalize-bg-api --help | head -3` → usage text prints.

- [ ] **Step 6: Commit, push (ASK OWNER FIRST — the only push gate in this plan), watch CI**

```bash
git add api/ tests/api/test_export_openapi.py pyproject.toml .github/workflows/ci.yml docs/api/openapi-rest.json
git commit -m "feat(api): legalize-bg-api entry point + OpenAPI contract lock + CI wiring (FR-028)"
# AFTER owner authorization:
git push origin main
gh run watch --exit-status
```

Expected: both CI jobs green. Fix-forward policy for runner-only failures: add skip guards / fix the workflow with an additional `ci:`-prefixed commit — never weaken a test; 3 fix-forward commits max, then BLOCKED.

---

### Task 9: Live smoke + docs + governance close-out

**Files:**
- Modify: `docs/runbook/2026-05-09-phase1b1-operator-setup.md` (REST API section), `README.md` (REST API mention)
- Modify: `docs/frs/INDEX.md` (FR-028 → Done), `docs/sync/DECISIONS.md` (append D-052 row), `docs/sync/ACTIVE.md` (banner + next action)

- [ ] **Step 1: Live smoke against the real catalog** (sequential; record outputs verbatim in the task report)

```bash
.venv/bin/legalize-bg-api --db catalog.db --corpus . --port 8228 &
API_PID=$!; sleep 3
curl -s localhost:8228/healthz
curl -s "localhost:8228/api/v1/stats"
curl -s "localhost:8228/api/v1/laws?category=laws&limit=2"
curl -s "localhost:8228/api/v1/laws/zakon-za-obshtestvenite-porachki" | head -c 400
curl -s "localhost:8228/api/v1/laws/zakon-za-obshtestvenite-porachki/articles/чл.%202"
curl -s "localhost:8228/api/v1/laws/zakon-za-obshtestvenite-porachki/history" | head -c 400
curl -s "localhost:8228/api/v1/laws/zakon-za-obshtestvenite-porachki/diff?from=2020-01-01&to=2025-01-01" | head -c 400
curl -s "localhost:8228/api/v1/search?q=обществени%20поръчки&limit=3"
curl -s -o /dev/null -w "%{http_code}\n" "localhost:8228/api/v1/laws/nesashtestvuvasht"   # expect 404
curl -s "localhost:8228/api/v1/metrics"
kill $API_PID
```

Expected: every call returns valid JSON with the shapes the tests lock; stats shows total_acts=3601; the 404 prints `404`. Any failure = BLOCKED with output.

- [ ] **Step 2: Docs**

Runbook: add a "REST API (FR-028)" section after the MCP sections: start command (`legalize-bg-api --db catalog.db --corpus . --port 8228 --cors-origin https://<frontend-domain>`), the 7+2 endpoint table (`| \`GET /api/v1/...\` | purpose |` — NOTE: use a NON-backticked first column or keep tool-table regex safety in mind: the runbook parity test regex `^\|\s*\`(\w+)\`` matches word-chars only, and `GET` alone would match! Write endpoint rows as `| GET /api/v1/laws | ... |` WITHOUT backticks around GET to keep the parity test's documented set untouched — verify `.venv/bin/python -m pytest tests/mcp_server/test_runbook_parity.py -q` stays green), the D-052 error table, per-request connection note, metrics endpoint. README: add one REST API paragraph + quick-start line under the MCP section.

- [ ] **Step 3: Governance**

- `docs/frs/INDEX.md`: FR-028 → Done, one-line resolution (REST API v1 shipped — 7 endpoints + healthz/metrics, OpenAPI contract-locked, CI-wired; plan `docs/plans/2026-07-02-fr028-rest-api-plan.md`; D-052).
- `docs/sync/DECISIONS.md`: append ONE single-line D-052 row after D-051 (same column structure): REST API v1 shipped per D-050 scope; error→HTTP mapping table (the D-052 table above, inline); per-request ro connections with D-051 pragmas (does NOT inherit the MCP lock — FR-029 unaffected); OpenAPI contract lock `docs/api/openapi-rest.json`; response shapes reuse mcp_server TypedDicts. Status: Active.
- `docs/sync/ACTIVE.md`: banner → FR-028 done; next action → Phase 7.2 (frontend, `legalize-bg-web` repo — per design §7.2; needs its own repo scaffolding per the design's documentation plan).

- [ ] **Step 4: Final gates + commit + push (same owner authorization as Task 8)**

```bash
.venv/bin/python -m pytest -q -m "not perf"                     # all pass
.venv/bin/python -m mcp_server.export_tools --check              # OK 1.3.0 (untouched)
.venv/bin/python -m api.export_openapi --check docs/api/openapi-rest.json  # OK
git add docs/runbook/2026-05-09-phase1b1-operator-setup.md README.md docs/frs/INDEX.md docs/sync/DECISIONS.md docs/sync/ACTIVE.md
git commit -m "docs(sync): FR-028 REST API shipped (D-052) — next: Phase 7.2 frontend"
git push origin main
gh run watch --exit-status
```

Expected: CI green. Done.

---

## Deferred out of this plan (recorded, do NOT implement here)

- **Phase 7.2 frontend** (`legalize-bg-web` repo) — separate repo, separate plan per the design's documentation plan.
- **FR-029 MCP per-call connections** — unaffected; the API's per-request model does not change the MCP lock.
- **Cold body-only search budget** — DEFERRED.md `D-2026-07-02-01` triggers exactly when THIS API gets real traffic missing the web PRD 300ms p95; do not add perf tests here (D-051 budgets locked; measurement needs a quiet machine).
- **Auth/rate-limiting/deployment** (Caddy/nginx, container) — design §Deployment marks them future; the runbook start-command is sufficient for 7.2 development.
- **`/api/v1/laws` amendments feed for the landing page** — needs Phase 3 (ДВ monitor); design says so explicitly.

## Self-review (skill checklist)

- **Spec coverage:** design §REST API endpoints — all 7 mapped (laws→T4, laws/{slug}→T5, articles→T5, history→T6, diff→T6, search→T6, stats→T4) + CORS (T3) + OpenAPI (T8) + tests-on-fixtures (T3 conftest) = §7.1 complete. D-050 obligations: per-request connections (T3), /metrics (T7), no MCP-lock inheritance (T3), additive contract registration (T1).
- **Placeholder scan:** every code step carries complete code; the two "check against reality" notes (T5 composition vs server.py; T6 VersionEntry.to_dict) are verification directives with a stated fallback, not gaps.
- **Type consistency:** `create_app(db_path, corpus_root, cors_origins)` identical in T3 definition and T4–T8 uses; `get_conn` name consistent; `list_laws`/`corpus_stats` signatures match between T2 definition and T4 routes; TypedDict names match `mcp_server/schemas.py` (verified 2026-07-02); exception attrs match queries.py (verified 2026-07-02).
- **Suite arithmetic:** 478 → T2 +4 = 482 → T3 +4 = 486 → T4 +3 = 489 → T5 +8 = 497 → T6 +8 = 505 → T7 +1 = 506 → T8 +2 = 508. (Counts are expectations, not gates — the gate is "green"; report drift, don't force it.)
