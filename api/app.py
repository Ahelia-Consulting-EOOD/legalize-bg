"""FastAPI application factory (FR-028 / Phase 7.1).

The REST API is a peer of the MCP server over the shared query layer
(design docs/plans/2026-05-11-phase7-legislation-browser-design.md;
D-050). HTTP concerns live here: CORS, per-request connections,
D-052 error mapping, cache headers, metrics."""

from pathlib import Path

from fastapi import FastAPI

from api.errors import install_error_handlers
from api.head_support import install_head_support
from api.metrics import install_metrics

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
    install_metrics(app)

    @app.get("/healthz")
    def healthz() -> dict:
        return {"status": "ok"}

    # Routers are attached by later tasks (laws, search, stats, metrics).
    _include_routers(app)
    # Added last (PR review fix #4) so it's the outermost user
    # middleware — wraps the metrics middleware too, so a HEAD request
    # still gets recorded against the right route.
    install_head_support(app)
    return app


def _include_routers(app: FastAPI) -> None:
    from api.routes import laws_list, stats
    app.include_router(laws_list.router)
    app.include_router(stats.router)
    from api.routes import laws
    app.include_router(laws.router)
    from api.routes import history_diff, search
    app.include_router(history_diff.router)
    app.include_router(search.router)
