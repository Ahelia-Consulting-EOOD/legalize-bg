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
