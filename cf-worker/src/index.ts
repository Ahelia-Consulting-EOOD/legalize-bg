/** Worker entrypoint: HEAD-as-GET (port of api/head_support.py) and
 * env-configured GET-only CORS (mirrors FastAPI create_app's
 * CORSMiddleware wiring) around the Hono app. */

import { createApp } from "./app";
import type { Env } from "./env";

const app = createApp();

function corsOrigins(env: Env): string[] {
  return (env.CORS_ORIGINS ?? "")
    .split(",")
    .map((s) => s.trim())
    .filter((s) => s.length > 0);
}

function allowedOrigin(origins: string[], origin: string | null): string | null {
  if (!origin || origins.length === 0) return null;
  if (origins.includes("*")) return "*";
  return origins.includes(origin) ? origin : null;
}

function withCors(resp: Response, allow: string | null): Response {
  if (!allow) return resp;
  const headers = new Headers(resp.headers);
  headers.set("access-control-allow-origin", allow);
  if (allow !== "*") headers.append("vary", "Origin");
  return new Response(resp.body, { status: resp.status, headers });
}

export default {
  async fetch(request: Request, env: Env, _ctx: ExecutionContext): Promise<Response> {
    const origins = corsOrigins(env);
    const origin = request.headers.get("origin");

    // CORS preflight (only when CORS is enabled — otherwise OPTIONS falls
    // through to the 405 path like FastAPI without CORSMiddleware).
    if (
      origins.length > 0 &&
      request.method === "OPTIONS" &&
      request.headers.get("access-control-request-method") !== null
    ) {
      const allow = allowedOrigin(origins, origin);
      if (!allow) {
        return new Response("Disallowed CORS origin", {
          status: 400,
          headers: { "content-type": "text/plain; charset=utf-8" },
        });
      }
      const reqHeaders = request.headers.get("access-control-request-headers");
      const headers: Record<string, string> = {
        "access-control-allow-origin": allow,
        "access-control-allow-methods": "GET",
        "access-control-max-age": "600",
      };
      if (reqHeaders) headers["access-control-allow-headers"] = reqHeaders;
      if (allow !== "*") headers["vary"] = "Origin";
      return new Response("OK", { headers: { "content-type": "text/plain; charset=utf-8", ...headers } });
    }

    // HEAD-as-GET: route as GET, drop the body, keep GET-equivalent
    // headers (incl. an explicit content-length).
    if (request.method === "HEAD") {
      const getReq = new Request(request.url, { method: "GET", headers: request.headers });
      const resp = await app.fetch(getReq, env, _ctx);
      const body = await resp.arrayBuffer();
      const headers = new Headers(resp.headers);
      headers.set("content-length", String(body.byteLength));
      return withCors(
        new Response(null, { status: resp.status, headers }),
        allowedOrigin(origins, origin),
      );
    }

    const resp = await app.fetch(request, env, _ctx);
    return withCors(resp, allowedOrigin(origins, origin));
  },
} satisfies ExportedHandler<Env>;
