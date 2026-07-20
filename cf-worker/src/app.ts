/** Route layer — implements every path in docs/api/openapi-rest.json
 * with FastAPI-identical shapes, statuses, and headers. */

import { Hono, type Context } from "hono";

import openapiSpec from "../../docs/api/openapi-rest.json";
import { fetchActJson, textHash16, type ActArticle, type ActJson } from "./acts";
import { InvalidArticleSpecError, parseArticleSpec } from "./articles";
import { unifiedGitDiff } from "./diff";
import type { Env } from "./env";
import { ToolError, isCatalogError, type JsonValue } from "./errors";
import { metrics } from "./metrics";
import {
  compareSortKeys,
  fullTextSearch,
  lawHistory,
  lawMeta,
  legalArticleSortKey,
  listLaws,
  resolveNameToLawId,
  versionAtDate,
  versionWithWarnings,
  type LawRow,
} from "./queries";
import {
  RequestValidationError,
  missingParam,
  parseBoolParam,
  parseIntParam,
  stringTooShort,
  validateDate,
  type ValidationDetail,
} from "./validation";

const CACHE_300 = "public, max-age=300";
const CACHE_60 = "public, max-age=60";

const SPEC_EXAMPLES = ["чл. 5", "чл. 5, ал. 2", "5.2", "чл. 5-7"];

type AppContext = Context<{ Bindings: Env }>;

function json(body: JsonValue, status = 200, headers: Record<string, string> = {}): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json", ...headers },
  });
}

function errorMessage(e: unknown): string {
  if (e instanceof Error) {
    const causeMsg = e.cause instanceof Error ? `: ${e.cause.message}` : "";
    return `${e.message}${causeMsg}`;
  }
  return String(e);
}

/** Map thrown errors to FastAPI-identical responses (api/errors.py). */
function errorResponse(e: unknown): Response {
  if (e instanceof RequestValidationError) {
    return json({ detail: e.detail as unknown as JsonValue }, 422);
  }
  if (e instanceof InvalidArticleSpecError) {
    return json({ code: "INVALID_ARTICLE_SPEC", detail: e.message, examples: SPEC_EXAMPLES }, 400);
  }
  if (e instanceof ToolError) {
    return json(e.toDict(), e.status);
  }
  const msg = errorMessage(e);
  if (isCatalogError(msg)) {
    return json(
      {
        code: "INDEX_MISSING",
        detail: msg.slice(0, 300),
        hint: "catalog.db is missing tables or corrupt — re-run `python -m index.build`",
      },
      503,
    );
  }
  // Starlette's ServerErrorMiddleware default.
  return new Response("Internal Server Error", {
    status: 500,
    headers: { "content-type": "text/plain; charset=utf-8" },
  });
}

/** Wrap a handler with api/metrics.py-equivalent per-route recording. */
function route(template: string, fn: (c: AppContext) => Promise<Response>) {
  return async (c: AppContext): Promise<Response> => {
    const t0 = performance.now();
    let resp: Response;
    try {
      resp = await fn(c);
    } catch (e) {
      resp = errorResponse(e);
    }
    if (template !== "/api/v1/metrics") {
      metrics.record(template, resp.status < 400, performance.now() - t0);
    }
    return resp;
  };
}

// ── get_law / get_article helpers ───────────────────────────────────────

function metaField(act: ActJson, key: string): JsonValue {
  const v = act.meta[key];
  return v === undefined ? null : v;
}

function buildLawResponse(
  lawId: string,
  metaRow: LawRow,
  act: ActJson,
  commitHash: string,
  warnings: JsonValue[],
): JsonValue {
  // Key order mirrors api/routes/laws.py get_law's literal dict.
  return {
    law_id: lawId,
    identificador: String(metaRow.doc_id),
    titulo: (metaField(act, "titulo") as string | null) || "",
    category: metaRow.category,
    fecha_publicacion: metaField(act, "fecha_publicacion"),
    ultima_actualizacion: metaField(act, "ultima_actualizacion"),
    dv_issue: metaField(act, "dv_issue"),
    dv_year: metaField(act, "dv_year"),
    effective_date: metaField(act, "effective_date"),
    eli: metaField(act, "eli"),
    amendment_history: (metaField(act, "amendment_history") as JsonValue[] | null) || [],
    commit_hash: commitHash,
    body_markdown: act.body_markdown,
    warnings,
  };
}

async function currentActArticleIds(c: AppContext, lawId: string): Promise<string[]> {
  // available_articles mirrors `SELECT DISTINCT article FROM provisions`
  // — provisions are baked from the current text, i.e. the acts/ object.
  const obj = await c.env.ACTS.get(`acts/${lawId}.json`);
  if (!obj) return [];
  const act = (await obj.json()) as ActJson;
  return Object.keys(act.articles).sort((a, b) =>
    compareSortKeys(legalArticleSortKey(a), legalArticleSortKey(b)),
  );
}

async function articleNotFound(
  c: AppContext,
  lawId: string,
  article: string,
  paragraph: string | null,
): Promise<never> {
  throw new ToolError("ARTICLE_NOT_FOUND", {
    law_id: lawId,
    article,
    paragraph,
    available_articles: await currentActArticleIds(c, lawId),
  });
}

function paragraphText(entry: ActArticle, n: string): string | null {
  const p = entry.paragraphs?.[n];
  if (p === undefined) return null;
  return typeof p === "string" ? p : p.text;
}

// ── diff helper (port of queries.diff_law_versions over R2) ────────────

async function diffLawVersions(
  c: AppContext,
  lawId: string,
  date1raw: string,
  date2raw: string,
): Promise<string> {
  const date1 = validateDate(date1raw, "date1");
  const date2 = validateDate(date2raw, "date2");
  if (date1 && date2 && date1 > date2) {
    throw new ToolError("INVALID_DATE_RANGE", { from_date: date1, to_date: date2 });
  }
  const v1 = await versionAtDate(c.env.DB, lawId, date1);
  const v2 = await versionAtDate(c.env.DB, lawId, date2);
  if (v1.commit_hash === v2.commit_hash) {
    return (
      `Хранилището съдържа една консолидирана версия на '${lawId}'; ` +
      `няма записана текстова промяна между ${date1} и ${date2}. / ` +
      `The corpus holds one consolidated version of '${lawId}'; ` +
      `no textual change is recorded between ${date1} and ${date2}.`
    );
  }
  const metaRow = await lawMeta(c.env.DB, lawId);
  if (!metaRow) {
    throw new ToolError("LAW_NOT_FOUND", { name: lawId, suggestions: [] });
  }
  const relPath = `${metaRow.category}/${lawId}.md`;
  const [act1, act2] = await Promise.all([
    fetchActJson(c.env.ACTS, lawId, v1.commit_hash, v1.valid_from, metaRow.current_commit),
    fetchActJson(c.env.ACTS, lawId, v2.commit_hash, v2.valid_from, metaRow.current_commit),
  ]);
  try {
    const raw1 = (act1.preamble_raw ?? "") + act1.body_markdown;
    const raw2 = (act2.preamble_raw ?? "") + act2.body_markdown;
    return unifiedGitDiff(relPath, raw1, raw2);
  } catch (e) {
    throw new ToolError("DIFF_FAILED", {
      law_id: lawId,
      detail: errorMessage(e).slice(0, 300),
    });
  }
}

// ── app ────────────────────────────────────────────────────────────────

export function createApp(): Hono<{ Bindings: Env }> {
  const app = new Hono<{ Bindings: Env }>();

  app.get(
    "/healthz",
    route("/healthz", async () => json({ status: "ok" })),
  );

  app.get(
    "/api/v1/laws",
    route("/api/v1/laws", async (c) => {
      const q = c.req.query();
      const errors: ValidationDetail[] = [];
      const limit = parseIntParam(q["limit"], "limit", 50, errors);
      const offset = parseIntParam(q["offset"], "offset", 0, errors);
      if (errors.length > 0) throw new RequestValidationError(errors);
      const result = await listLaws(
        c.env.DB,
        q["category"] ?? null,
        q["estado"] ?? null,
        limit,
        offset,
      );
      return json(result as unknown as JsonValue);
    }),
  );

  app.get(
    "/api/v1/laws/:slug",
    route("/api/v1/laws/{slug}", async (c) => {
      const lawId = await resolveNameToLawId(c.env.DB, (c.req.param("slug") ?? ""));
      const { version, warnings } = await versionWithWarnings(
        c.env.DB,
        lawId,
        c.req.query("date") ?? null,
      );
      const metaRow = await lawMeta(c.env.DB, lawId);
      if (!metaRow) throw new ToolError("LAW_NOT_FOUND", { name: lawId, suggestions: [] });
      const act = await fetchActJson(
        c.env.ACTS,
        lawId,
        version.commit_hash,
        version.valid_from,
        metaRow.current_commit,
      );
      return json(
        buildLawResponse(lawId, metaRow, act, version.commit_hash, warnings as unknown as JsonValue[]),
        200,
        { "cache-control": CACHE_300 },
      );
    }),
  );

  app.get(
    "/api/v1/laws/:slug/articles/:art",
    route("/api/v1/laws/{slug}/articles/{art}", async (c) => {
      const art = (c.req.param("art") ?? "");
      const lawId = await resolveNameToLawId(c.env.DB, (c.req.param("slug") ?? ""));
      const spec = parseArticleSpec(art);
      if (spec.rangeEnd !== null) {
        throw new ToolError("INVALID_ARTICLE_SPEC", {
          spec: art,
          detail:
            "ranges are not served by this endpoint — request " +
            "single articles (the MCP get_articles tool serves " +
            "ranges)",
          examples: ["чл. 5", "чл. 5, ал. 2"],
        });
      }
      const date = c.req.query("date") ?? null;
      const { version, warnings } = await versionWithWarnings(c.env.DB, lawId, date);
      const metaRow = await lawMeta(c.env.DB, lawId);
      if (!metaRow) throw new ToolError("LAW_NOT_FOUND", { name: lawId, suggestions: [] });
      const act = await fetchActJson(
        c.env.ACTS,
        lawId,
        version.commit_hash,
        version.valid_from,
        metaRow.current_commit,
      );
      const entry = act.articles[spec.article];
      if (!entry) await articleNotFound(c, lawId, spec.article, spec.paragraph);
      let text: string;
      let textHash: string;
      if (spec.paragraph === null) {
        text = entry!.text;
        textHash = entry!.text_hash ?? (await textHash16(text));
      } else {
        const p = paragraphText(entry!, spec.paragraph);
        if (p === null) await articleNotFound(c, lawId, spec.article, spec.paragraph);
        text = p!;
        const stored = entry!.paragraphs?.[spec.paragraph];
        textHash =
          typeof stored === "object" && stored.text_hash
            ? stored.text_hash
            : await textHash16(text);
      }
      return json(
        {
          law_id: lawId,
          article: spec.article,
          paragraph: spec.paragraph,
          text,
          text_hash: textHash,
          commit_hash: version.commit_hash,
          warnings: warnings as unknown as JsonValue[],
        },
        200,
        { "cache-control": CACHE_300 },
      );
    }),
  );

  app.get(
    "/api/v1/laws/:slug/history",
    route("/api/v1/laws/{slug}/history", async (c) => {
      const lawId = await resolveNameToLawId(c.env.DB, (c.req.param("slug") ?? ""));
      const entries = await lawHistory(c.env.DB, lawId);
      return json(entries as unknown as JsonValue, 200, { "cache-control": CACHE_300 });
    }),
  );

  app.get(
    "/api/v1/laws/:slug/diff",
    route("/api/v1/laws/{slug}/diff", async (c) => {
      const from = c.req.query("from");
      const to = c.req.query("to");
      const errors: ValidationDetail[] = [];
      if (from === undefined) errors.push(missingParam("from"));
      if (to === undefined) errors.push(missingParam("to"));
      if (errors.length > 0) throw new RequestValidationError(errors);
      const lawId = await resolveNameToLawId(c.env.DB, (c.req.param("slug") ?? ""));
      const text = await diffLawVersions(c, lawId, from!, to!);
      return json(
        { law_id: lawId, from_date: from!, to_date: to!, diff: text },
        200,
        { "cache-control": CACHE_300 },
      );
    }),
  );

  app.get(
    "/api/v1/search",
    route("/api/v1/search", async (c) => {
      const q = c.req.query();
      const errors: ValidationDetail[] = [];
      const query = q["q"];
      if (query === undefined) errors.push(missingParam("q"));
      else if (query.length < 1) errors.push(stringTooShort("q", query, 1));
      const limit = parseIntParam(q["limit"], "limit", 20, errors);
      const includeBody = parseBoolParam(q["include_body"], "include_body", false, errors);
      if (errors.length > 0) throw new RequestValidationError(errors);
      const capped = Math.min(Math.max(1, Math.trunc(limit)), 50);
      const hits = await fullTextSearch(
        c.env.DB,
        query!,
        q["category"] ?? null,
        capped,
        includeBody,
      );
      return json(hits as unknown as JsonValue, 200, { "cache-control": CACHE_60 });
    }),
  );

  app.get(
    "/api/v1/stats",
    route("/api/v1/stats", async (c) => {
      const obj = await c.env.ACTS.get("meta/stats.json");
      if (!obj) {
        throw new ToolError("INDEX_MISSING", {
          detail: "stats object missing from R2: meta/stats.json",
          hint: "catalog.db is missing tables or corrupt — re-run `python -m index.build`",
        });
      }
      const stats = (await obj.json()) as Record<string, JsonValue>;
      delete stats["exported_at"];
      return json(stats);
    }),
  );

  app.get(
    "/api/v1/metrics",
    route("/api/v1/metrics", async () => json(metrics.snapshot() as unknown as JsonValue)),
  );

  app.get(
    "/api/v1/openapi.json",
    route("/api/v1/openapi.json", async () => json(openapiSpec as unknown as JsonValue)),
  );

  // FastAPI defaults: 404 {"detail":"Not Found"}; 405 with Allow header
  // when the path exists but the method is not GET.
  const KNOWN_GET_PATHS = [
    /^\/healthz$/,
    /^\/api\/v1\/laws$/,
    /^\/api\/v1\/laws\/[^/]+$/,
    /^\/api\/v1\/laws\/[^/]+\/articles\/[^/]+$/,
    /^\/api\/v1\/laws\/[^/]+\/(history|diff)$/,
    /^\/api\/v1\/(search|stats|metrics|openapi\.json)$/,
  ];

  app.notFound((c) => {
    const path = new URL(c.req.url).pathname;
    const known = KNOWN_GET_PATHS.some((re) => re.test(path));
    if (known && c.req.method !== "GET" && c.req.method !== "HEAD") {
      return json({ detail: "Method Not Allowed" }, 405, { allow: "GET" });
    }
    return json({ detail: "Not Found" }, 404);
  });

  return app;
}
