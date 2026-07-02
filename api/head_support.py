"""HEAD support for GET routes (PR review fix #4).

Verified against the installed venv (fastapi 0.139.0 / starlette 1.0.0):
FastAPI's `APIRoute.__init__` builds `route.methods` via
`_populate_api_route_state` (`fastapi/routing.py`), which sets
`route.methods = {m.upper() for m in methods}` directly from the
declared `methods=` kwarg — with NO fallback to add `"HEAD"` when
`"GET"` is present. That auto-add only exists on vanilla Starlette's
`Route.__init__` (`starlette/routing.py`), which `APIRoute` does NOT
call (`APIRoute.__init__` never invokes `super().__init__()`). So a
bare `@router.get(...)` — every route in this package — 405s on HEAD.

Declaring `methods=["GET", "HEAD"]` on every route would work, but it
also makes FastAPI's openapi/utils.py (which iterates `route.methods`
with no HEAD special-case in this version) emit a redundant `head:`
operation for every path in the locked contract,
`docs/api/openapi-rest.json` — noise unrelated to fix #3's job of
documenting error responses. Instead, this installs one ASGI-level
middleware: an incoming HEAD request is routed as if it were GET (so
`route.methods == {"GET"}` still matches — no route-declaration changes
needed anywhere), and the outgoing response body bytes are dropped at
send-time, exactly mirroring what Starlette's own `Response.__call__`
does for a route that natively declares HEAD support
(`send_header_only`). Headers — status, Content-Length, Cache-Control,
... — are computed identically to the GET response and left untouched;
only the body bytes are suppressed. This is invisible to
`app.openapi()`: the route's declared `methods` never change, so the
schema is unaffected."""

from fastapi import FastAPI


class _HeadAsGetMiddleware:
    """Pure ASGI middleware — deliberately not `BaseHTTPMiddleware`, so
    it can rewrite `scope["method"]` before routing without buffering
    the whole response."""

    def __init__(self, app):
        self._app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or scope["method"] != "HEAD":
            await self._app(scope, receive, send)
            return

        get_scope = dict(scope, method="GET")

        async def _drop_body(message):
            if message["type"] == "http.response.body" and message.get("body"):
                message = {**message, "body": b""}
            await send(message)

        await self._app(get_scope, receive, _drop_body)


def install_head_support(app: FastAPI) -> None:
    """Let HEAD reach any registered GET route with a bodyless 200 and
    GET-equivalent headers."""
    app.add_middleware(_HeadAsGetMiddleware)
