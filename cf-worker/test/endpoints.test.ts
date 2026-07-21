// Endpoint tests against a fixture-seeded D1 + R2 (see fixtures.ts).
// Covers every error code in api/errors.py's HTTP map that the Worker
// can produce, plus Cache-Control, HEAD, CORS, 404/405, and metrics.
import { createExecutionContext, env, waitOnExecutionContext } from "cloudflare:test";
import { beforeAll, describe, expect, it } from "vitest";

import worker from "../src/index";
import { seedFixtures, KODEKS_BODY_V1, KODEKS_BODY_V3 } from "./fixtures";
import { textHash16 } from "../src/acts";

async function call(
  path: string,
  init: RequestInit = {},
  overrides: Partial<typeof env> = {},
): Promise<Response> {
  const ctx = createExecutionContext();
  const resp = await worker.fetch(
    new Request(`http://worker.local${path}`, init),
    { ...env, ...overrides },
    ctx,
  );
  await waitOnExecutionContext(ctx);
  return resp;
}

async function getJson(path: string): Promise<{ status: number; body: any; resp: Response }> {
  const resp = await call(path);
  return { status: resp.status, body: await resp.json(), resp };
}

beforeAll(async () => {
  await seedFixtures();
});

describe("GET /healthz", () => {
  it("returns ok", async () => {
    const { status, body } = await getJson("/healthz");
    expect(status).toBe(200);
    expect(body).toEqual({ status: "ok" });
  });
});

describe("GET /api/v1/laws", () => {
  it("lists laws ordered by title with totals", async () => {
    const { status, body } = await getJson("/api/v1/laws");
    expect(status).toBe(200);
    expect(body.total).toBe(7);
    expect(body.items.length).toBe(7);
    const first = body.items[0];
    expect(first).toEqual({
      law_id: "neizvesten-akt",
      identificador: "666",
      title: "ЕТИЧЕН КОДЕКС НА ТЕСТЕРИТЕ",
      category: "ordinances",
      status: "vigente",
      first_version: "2026-04-20",
      latest_version: "2026-04-20",
      version_count: 1,
    });
  });
  it("filters by category and estado, paginates", async () => {
    const { body } = await getJson("/api/v1/laws?category=laws&limit=2&offset=1");
    expect(body.total).toBe(4);
    expect(body.items.length).toBe(2);
    const none = await getJson("/api/v1/laws?estado=derogado");
    expect(none.body.total).toBe(0);
  });
  it("clamps limit/offset like queries.list_laws", async () => {
    const { body } = await getJson("/api/v1/laws?limit=0&offset=-5");
    expect(body.items.length).toBe(1); // limit clamped to 1, offset to 0
  });
  it("422s on non-integer limit with pydantic shape", async () => {
    const { status, body } = await getJson("/api/v1/laws?limit=abc");
    expect(status).toBe(422);
    expect(body).toEqual({
      detail: [
        {
          type: "int_parsing",
          loc: ["query", "limit"],
          msg: "Input should be a valid integer, unable to parse string as an integer",
          input: "abc",
        },
      ],
    });
  });
});

describe("GET /api/v1/laws/{slug}", () => {
  it("serves the current version from acts/ with meta + cache header", async () => {
    const { status, body, resp } = await getJson("/api/v1/laws/zakon-za-testovite-porachki");
    expect(status).toBe(200);
    expect(resp.headers.get("cache-control")).toBe("public, max-age=300");
    expect(Object.keys(body)).toEqual([
      "law_id",
      "identificador",
      "titulo",
      "category",
      "fecha_publicacion",
      "ultima_actualizacion",
      "dv_issue",
      "dv_year",
      "effective_date",
      "eli",
      "amendment_history",
      "commit_hash",
      "body_markdown",
      "warnings",
    ]);
    expect(body.law_id).toBe("zakon-za-testovite-porachki");
    expect(body.identificador).toBe("111");
    expect(body.titulo).toBe("ЗАКОН ЗА ТЕСТОВИТЕ ПОРЪЧКИ");
    expect(body.commit_hash).toBe("aaa1");
    expect(body.body_markdown).toContain("Чл. 14а.");
    expect(body.warnings).toEqual([]);
  });
  it("resolves by identificador and by exact Cyrillic title case-insensitively", async () => {
    const byId = await getJson("/api/v1/laws/111");
    expect(byId.body.law_id).toBe("zakon-za-testovite-porachki");
    const byTitle = await getJson(
      "/api/v1/laws/" + encodeURIComponent("закон за тестовите поръчки"),
    );
    expect(byTitle.body.law_id).toBe("zakon-za-testovite-porachki");
  });
  it("resolves historical versions by date (valid_to inclusive)", async () => {
    const mid = await getJson("/api/v1/laws/testov-kodeks?date=2021-06-15");
    expect(mid.body.commit_hash).toBe("c2");
    const boundary = await getJson("/api/v1/laws/testov-kodeks?date=2023-05-31");
    expect(boundary.body.commit_hash).toBe("c2");
    const next = await getJson("/api/v1/laws/testov-kodeks?date=2023-06-01");
    expect(next.body.commit_hash).toBe("c3");
    expect(next.body.body_markdown).toBe(KODEKS_BODY_V3);
    const v1 = await getJson("/api/v1/laws/testov-kodeks?date=2015-01-01");
    expect(v1.body.commit_hash).toBe("c1");
    expect(v1.body.body_markdown).toBe(KODEKS_BODY_V1);
  });
  it("NO_VERSION_AT_DATE 404 with earliest/latest", async () => {
    const { status, body } = await getJson("/api/v1/laws/testov-kodeks?date=2005-01-01");
    expect(status).toBe(404);
    expect(body).toEqual({
      code: "NO_VERSION_AT_DATE",
      law_id: "testov-kodeks",
      date: "2005-01-01",
      earliest_available: "2010-01-01",
      latest_available: "2023-06-01",
    });
  });
  it("INVALID_DATE 400 on junk, empty, and calendar-invalid dates", async () => {
    for (const d of ["junk", "", "2026-02-30"]) {
      const { status, body } = await getJson(`/api/v1/laws/testov-kodeks?date=${d}`);
      expect(status).toBe(400);
      expect(body.code).toBe("INVALID_DATE");
      expect(body.param).toBe("date");
      expect(body.expected).toBe("YYYY-MM-DD");
    }
  });
  it("LAW_NOT_FOUND 404 with FTS suggestions", async () => {
    const { status, body } = await getJson(
      "/api/v1/laws/" + encodeURIComponent("тестовите поръчки"),
    );
    expect(status).toBe(404);
    expect(body.code).toBe("LAW_NOT_FOUND");
    expect(body.name).toBe("тестовите поръчки");
    expect(body.suggestions.length).toBeGreaterThan(0);
    const s = body.suggestions[0];
    expect(Object.keys(s)).toEqual(["law_id", "title", "relevance"]);
    expect(typeof s.relevance).toBe("number");
  });
  it("AMBIGUOUS_NAME 409 with full candidate list", async () => {
    const { status, body } = await getJson(
      "/api/v1/laws/" + encodeURIComponent("ЗАКОН ЗА ТЕСТОВАТА АМНИСТИЯ"),
    );
    expect(status).toBe(409);
    expect(body.code).toBe("AMBIGUOUS_NAME");
    expect(body.candidates).toEqual([
      {
        law_id: "zakon-za-testovata-amnistiya",
        identificador: "551",
        title: "ЗАКОН ЗА ТЕСТОВАТА АМНИСТИЯ",
        category: "laws",
      },
      {
        law_id: "zakon-za-testovata-amnistiya-2",
        identificador: "552",
        title: "ЗАКОН ЗА ТЕСТОВАТА АМНИСТИЯ",
        category: "laws",
      },
    ]);
  });
  it("carries DATE_UNCERTAIN warnings from law_versions", async () => {
    const { body } = await getJson("/api/v1/laws/neizvesten-akt");
    expect(body.warnings).toEqual([
      {
        code: "DATE_UNCERTAIN",
        law_id: "neizvesten-akt",
        source_date_marker: "unknown",
        note: "publication date not parseable from lex.bg; version validity falls back to bootstrap run date",
      },
    ]);
  });
});

describe("GET /api/v1/laws/{slug}/articles/{art}", () => {
  it("serves whole articles and alineas in all spec formats", async () => {
    const whole = await getJson("/api/v1/laws/zakon-za-testovite-porachki/articles/2");
    expect(whole.status).toBe(200);
    expect(whole.body.article).toBe("2");
    expect(whole.body.paragraph).toBeNull();
    expect(whole.body.text).toBe(
      "Чл. 2. (1) Публични тестове са тези. (2) Частни тестове са другите.",
    );
    expect(whole.body.text_hash).toBe(await textHash16(whole.body.text));
    expect(whole.resp.headers.get("cache-control")).toBe("public, max-age=300");

    for (const spec of ["чл. 2, ал. 2", "2.2", "чл. 2 ал. 2"]) {
      const alinea = await getJson(
        `/api/v1/laws/zakon-za-testovite-porachki/articles/${encodeURIComponent(spec)}`,
      );
      expect(alinea.status).toBe(200);
      expect(alinea.body.paragraph).toBe("2");
      expect(alinea.body.text).toBe("Частни тестове са другите.");
      expect(alinea.body.text_hash).toBe(await textHash16("Частни тестове са другите."));
    }

    const suffixed = await getJson(
      "/api/v1/laws/zakon-za-testovite-porachki/articles/" + encodeURIComponent("чл. 14а"),
    );
    expect(suffixed.status).toBe(200);
    expect(suffixed.body.article).toBe("14а");
  });
  it("rejects ranges with the FastAPI detail text", async () => {
    const { status, body } = await getJson(
      "/api/v1/laws/zakon-za-testovite-porachki/articles/5-7",
    );
    expect(status).toBe(400);
    expect(body).toEqual({
      code: "INVALID_ARTICLE_SPEC",
      spec: "5-7",
      detail:
        "ranges are not served by this endpoint — request single articles (the MCP get_articles tool serves ranges)",
      examples: ["чл. 5", "чл. 5, ал. 2"],
    });
  });
  it("rejects unparseable specs", async () => {
    const { status, body } = await getJson("/api/v1/laws/zakon-za-testovite-porachki/articles/abc");
    expect(status).toBe(400);
    expect(body.code).toBe("INVALID_ARTICLE_SPEC");
    expect(body.detail).toBe("could not parse: 'abc'");
    expect(body.examples).toEqual(["чл. 5", "чл. 5, ал. 2", "5.2", "чл. 5-7"]);
  });
  it("ARTICLE_NOT_FOUND with legally-sorted available_articles", async () => {
    const { status, body } = await getJson("/api/v1/laws/zakon-za-testovite-porachki/articles/999");
    expect(status).toBe(404);
    expect(body).toEqual({
      code: "ARTICLE_NOT_FOUND",
      law_id: "zakon-za-testovite-porachki",
      article: "999",
      paragraph: null,
      available_articles: ["1", "2", "14а"],
    });
  });
  it("ARTICLE_NOT_FOUND for a missing alinea keeps paragraph in the payload", async () => {
    const { status, body } = await getJson(
      "/api/v1/laws/zakon-za-testovite-porachki/articles/" + encodeURIComponent("чл. 2, ал. 9"),
    );
    expect(status).toBe(404);
    expect(body.paragraph).toBe("9");
  });
  it("resolves versioned article text via ?date=", async () => {
    const { body } = await getJson("/api/v1/laws/testov-kodeks/articles/3");
    expect(body.text).toBe("Чл. 3. Нова разпоредба.");
    const old = await getJson("/api/v1/laws/testov-kodeks/articles/3?date=2015-01-01");
    // Article 3 does not exist in v1's articles map.
    expect(old.status).toBe(404);
    expect(old.body.code).toBe("ARTICLE_NOT_FOUND");
  });
  it("INVALID_DATE before article lookup", async () => {
    const { status, body } = await getJson(
      "/api/v1/laws/zakon-za-testovite-porachki/articles/1?date=nope",
    );
    expect(status).toBe(400);
    expect(body.code).toBe("INVALID_DATE");
  });
});

describe("GET /api/v1/laws/{slug}/history", () => {
  it("returns amendment timeline plus consolidated entry", async () => {
    const { body, resp } = await getJson("/api/v1/laws/testov-kodeks/history");
    expect(resp.headers.get("cache-control")).toBe("public, max-age=300");
    expect(body).toEqual([
      { date: "2010-01-01", dv_issue: "1/2010", operation: "enacted", commit_hash: null },
      { date: "2021-01-01", dv_issue: "5/2021", operation: "amendment", commit_hash: null },
      { date: "2023-06-01", dv_issue: "45/2023", operation: "amendment", commit_hash: null },
      { date: "2023-06-01", dv_issue: null, operation: "consolidated", commit_hash: "c3" },
    ]);
  });
  it("act without amendments gets a single consolidated entry dated valid_from", async () => {
    const { body } = await getJson("/api/v1/laws/naredba-za-testovite-porachki/history");
    expect(body).toEqual([
      { date: "2021-03-01", dv_issue: null, operation: "consolidated", commit_hash: "ccc1" },
    ]);
  });
});

describe("GET /api/v1/laws/{slug}/diff", () => {
  it("returns the bilingual single-version note when both dates resolve to one commit", async () => {
    const { body, resp } = await getJson(
      "/api/v1/laws/zakon-za-testovite-porachki/diff?from=2021-01-01&to=2022-01-01",
    );
    expect(resp.headers.get("cache-control")).toBe("public, max-age=300");
    expect(body).toEqual({
      law_id: "zakon-za-testovite-porachki",
      from_date: "2021-01-01",
      to_date: "2022-01-01",
      diff:
        "Хранилището съдържа една консолидирана версия на 'zakon-za-testovite-porachki'; " +
        "няма записана текстова промяна между 2021-01-01 и 2022-01-01. / " +
        "The corpus holds one consolidated version of 'zakon-za-testovite-porachki'; " +
        "no textual change is recorded between 2021-01-01 and 2022-01-01.",
    });
  });
  it("computes a git-style unified diff over preamble_raw + body_markdown", async () => {
    const { status, body } = await getJson(
      "/api/v1/laws/testov-kodeks/diff?from=2015-01-01&to=2021-06-01",
    );
    expect(status).toBe(200);
    const d: string = body.diff;
    expect(d.startsWith("diff --git a/codes/testov-kodeks.md b/codes/testov-kodeks.md\n")).toBe(
      true,
    );
    expect(d).toContain("--- a/codes/testov-kodeks.md");
    expect(d).toContain("+++ b/codes/testov-kodeks.md");
    expect(d).toContain("-ultima_actualizacion: '2010-01-01'");
    expect(d).toContain("+ultima_actualizacion: '2021-01-01'");
    expect(d).toContain("-Чл. 1. Старият текст на първата разпоредба.");
    expect(d).toContain("+Чл. 1. Новият текст на първата разпоредба.");
    expect(d).toMatch(/@@ -\d+(,\d+)? \+\d+(,\d+)? @@/);
    expect(d.endsWith("\n")).toBe(true);
  });
  it("INVALID_DATE_RANGE on reversed range", async () => {
    const { status, body } = await getJson(
      "/api/v1/laws/testov-kodeks/diff?from=2022-01-01&to=2021-01-01",
    );
    expect(status).toBe(400);
    expect(body).toEqual({
      code: "INVALID_DATE_RANGE",
      from_date: "2022-01-01",
      to_date: "2021-01-01",
    });
  });
  it("INVALID_DATE uses date1/date2 param names like queries.diff_law_versions", async () => {
    const { status, body } = await getJson("/api/v1/laws/testov-kodeks/diff?from=bad&to=2021-01-01");
    expect(status).toBe(400);
    expect(body).toEqual({ code: "INVALID_DATE", param: "date1", value: "bad", expected: "YYYY-MM-DD" });
  });
  it("NO_VERSION_AT_DATE propagates from either endpoint date", async () => {
    const { status, body } = await getJson(
      "/api/v1/laws/testov-kodeks/diff?from=2005-01-01&to=2021-06-01",
    );
    expect(status).toBe(404);
    expect(body.code).toBe("NO_VERSION_AT_DATE");
  });
  it("422 with FastAPI shape when from/to are missing", async () => {
    const { status, body } = await getJson("/api/v1/laws/testov-kodeks/diff?to=2021-01-01");
    expect(status).toBe(422);
    expect(body).toEqual({
      detail: [{ type: "missing", loc: ["query", "from"], msg: "Field required", input: null }],
    });
    const both = await getJson("/api/v1/laws/testov-kodeks/diff");
    expect(both.body.detail.length).toBe(2);
  });
});

describe("GET /api/v1/search", () => {
  it("finds acts by normalized Cyrillic query with title snippets", async () => {
    const { status, body, resp } = await getJson(
      "/api/v1/search?q=" + encodeURIComponent("тестовите поръчки"),
    );
    expect(status).toBe(200);
    expect(resp.headers.get("cache-control")).toBe("public, max-age=60");
    expect(body.length).toBeGreaterThanOrEqual(2);
    const hit = body[0];
    expect(Object.keys(hit)).toEqual([
      "law_id",
      "identificador",
      "title",
      "category",
      "title_snippet",
      "body_snippet",
      "relevance",
    ]);
    // rang-aware tier sort: the law outranks the ordinance.
    expect(body[0].law_id).toBe("zakon-za-testovite-porachki");
    expect(body.map((h: any) => h.law_id)).toContain("naredba-za-testovite-porachki");
    expect(hit.title_snippet).toContain("<b>");
    expect(hit.body_snippet).toBe("");
    expect(hit.relevance).toBeGreaterThan(0);
  });
  it("expands single-token abbreviations (ЗОП) to the canonical title", async () => {
    const { body } = await getJson("/api/v1/search?q=" + encodeURIComponent("ЗОП"));
    expect(body.length).toBeGreaterThanOrEqual(1);
    expect(body[0].law_id).toBe("zakon-za-obshtestvenite-porachki");
  });
  it("generates body snippets for the top 2 hits when include_body=true", async () => {
    const { body } = await getJson(
      "/api/v1/search?q=" + encodeURIComponent("тестовите поръчки") + "&include_body=true",
    );
    expect(body[0].body_snippet).toContain("<b>");
    for (const h of body.slice(2)) expect(h.body_snippet).toBe("");
  });
  it("filters by category", async () => {
    const { body } = await getJson(
      "/api/v1/search?q=" + encodeURIComponent("тестовите поръчки") + "&category=ordinances",
    );
    expect(body.every((h: any) => h.category === "ordinances")).toBe(true);
    expect(body.length).toBeGreaterThanOrEqual(1);
  });
  it("QUERY_TOO_BROAD on single-word category stop words incl. punctuated variants", async () => {
    for (const q of ["наредба", "НАРЕДБА", "законът—", "кодекс."]) {
      const { status, body } = await getJson("/api/v1/search?q=" + encodeURIComponent(q));
      expect(status).toBe(400);
      expect(body.code).toBe("QUERY_TOO_BROAD");
      expect(body.category_words).toEqual([
        "закон",
        "кодекс",
        "наредба",
        "постановление",
        "правилник",
      ]);
    }
  });
  it("QUERY_TOO_BROAD on >512-char queries with the length hint", async () => {
    const long = "щ".repeat(600);
    const { status, body } = await getJson("/api/v1/search?q=" + encodeURIComponent(long));
    expect(status).toBe(400);
    expect(body.query.length).toBe(200);
    expect(body.hint).toBe("query longer than 512 chars — send a focused query");
  });
  it("suppresses FTS5 user-input syntax errors as empty results", async () => {
    const { status, body } = await getJson("/api/v1/search?q=" + encodeURIComponent('"unbalanced'));
    expect(status).toBe(200);
    expect(body).toEqual([]);
    const colonQ = await getJson("/api/v1/search?q=" + encodeURIComponent("foo:bar"));
    expect(colonQ.status).toBe(200);
    expect(colonQ.body).toEqual([]);
  });
  it("caps limit at 50 without erroring", async () => {
    const { status } = await getJson("/api/v1/search?q=" + encodeURIComponent("тест") + "&limit=100");
    expect(status).toBe(200);
  });
  it("422 shapes: missing q, empty q, bad limit, bad include_body", async () => {
    const missing = await getJson("/api/v1/search");
    expect(missing.status).toBe(422);
    expect(missing.body).toEqual({
      detail: [{ type: "missing", loc: ["query", "q"], msg: "Field required", input: null }],
    });
    const empty = await getJson("/api/v1/search?q=");
    expect(empty.body).toEqual({
      detail: [
        {
          type: "string_too_short",
          loc: ["query", "q"],
          msg: "String should have at least 1 character",
          input: "",
          ctx: { min_length: 1 },
        },
      ],
    });
    const bad = await getJson("/api/v1/search?q=%D1%82%D0%B5%D1%81%D1%82&limit=abc&include_body=xx");
    expect(bad.status).toBe(422);
    expect(bad.body.detail.map((d: any) => d.type)).toEqual(["int_parsing", "bool_parsing"]);
    expect(bad.body.detail[1].msg).toBe("Input should be a valid boolean, unable to interpret input");
  });
  it("INDEX_MISSING 503 when the FTS table is gone", async () => {
    await env.DB.prepare("DROP TABLE laws_fts").run();
    const { status, body } = await getJson("/api/v1/search?q=" + encodeURIComponent("тест"));
    expect(status).toBe(503);
    expect(body.code).toBe("INDEX_MISSING");
    expect(body.hint).toBe(
      "catalog.db is missing tables or corrupt — re-run `python -m index.build`",
    );
  });
});

describe("GET /api/v1/stats", () => {
  it("serves meta/stats.json without exported_at", async () => {
    const { status, body } = await getJson("/api/v1/stats");
    expect(status).toBe(200);
    expect(body).toEqual({
      total_acts: 7,
      by_category: { codes: 1, laws: 4, ordinances: 2 },
      by_status: { vigente: 7 },
      multi_version_acts: 1,
      latest_version_date: "2026-04-20",
    });
  });
  it("INDEX_MISSING 503 when the stats object is absent", async () => {
    await env.ACTS.delete("meta/stats.json");
    const { status, body } = await getJson("/api/v1/stats");
    expect(status).toBe(503);
    expect(body.code).toBe("INDEX_MISSING");
  });
});

describe("GET /api/v1/metrics and /api/v1/openapi.json", () => {
  it("records per-route metrics with the FastAPI shape", async () => {
    await getJson("/healthz");
    await getJson("/api/v1/stats");
    const { body } = await getJson("/api/v1/metrics");
    expect(body["/healthz"]).toBeDefined();
    expect(body["/api/v1/stats"]).toBeDefined();
    expect(body["/api/v1/metrics"]).toBeUndefined();
    const m = body["/healthz"];
    expect(Object.keys(m)).toEqual(["calls", "errors", "total_ms", "avg_ms"]);
    expect(m.calls).toBeGreaterThanOrEqual(1);
  });
  it("records 4xx as errors on the matched route", async () => {
    await getJson("/api/v1/search?q=" + encodeURIComponent("наредба"));
    const { body } = await getJson("/api/v1/metrics");
    expect(body["/api/v1/search"].errors).toBeGreaterThanOrEqual(1);
  });
  it("serves the checked-in OpenAPI spec verbatim", async () => {
    const { status, body } = await getJson("/api/v1/openapi.json");
    expect(status).toBe(200);
    expect(body.info).toEqual({ title: "legalize-bg REST API", version: "1.0.0" });
    expect(Object.keys(body.paths).length).toBe(9);
  });
});

describe("HEAD, 404/405, CORS", () => {
  it("HEAD returns GET headers with an empty body", async () => {
    const resp = await call("/api/v1/stats", { method: "HEAD" });
    expect(resp.status).toBe(200);
    expect(resp.headers.get("content-type")).toBe("application/json");
    expect(Number(resp.headers.get("content-length"))).toBeGreaterThan(0);
    expect(await resp.text()).toBe("");
  });
  it("HEAD works on error routes too", async () => {
    const resp = await call("/api/v1/laws/no-such-slug-here", { method: "HEAD" });
    expect(resp.status).toBe(404);
    expect(await resp.text()).toBe("");
  });
  it("unknown paths 404 with FastAPI's body", async () => {
    const { status, body } = await getJson("/api/v1/nope");
    expect(status).toBe(404);
    expect(body).toEqual({ detail: "Not Found" });
  });
  it("non-GET on known paths 405s", async () => {
    const resp = await call("/api/v1/search?q=x", { method: "POST" });
    expect(resp.status).toBe(405);
    expect(await resp.json()).toEqual({ detail: "Method Not Allowed" });
    expect(resp.headers.get("allow")).toBe("GET");
  });
  it("CORS disabled by default: no ACAO header", async () => {
    const resp = await call("/healthz", { headers: { origin: "https://a.example" } });
    expect(resp.headers.get("access-control-allow-origin")).toBeNull();
  });
  it("CORS wildcard: ACAO * on GET and preflight for any origin", async () => {
    const cors = { CORS_ORIGINS: "*" };
    const ok = await call("/api/v1/stats", { headers: { origin: "http://localhost:3100" } }, cors);
    expect(ok.headers.get("access-control-allow-origin")).toBe("*");
    const preflight = await call(
      "/api/v1/laws/whatever",
      {
        method: "OPTIONS",
        headers: { origin: "https://legalize.ahelia.com", "access-control-request-method": "GET" },
      },
      cors,
    );
    expect(preflight.status).toBe(200);
    expect(preflight.headers.get("access-control-allow-origin")).toBe("*");
    expect(preflight.headers.get("access-control-allow-methods")).toBe("GET");
  });
  it("CORS enabled via env: allows configured origins on GET and preflight", async () => {
    const cors = { CORS_ORIGINS: "https://a.example, https://b.example" };
    const ok = await call("/healthz", { headers: { origin: "https://a.example" } }, cors);
    expect(ok.headers.get("access-control-allow-origin")).toBe("https://a.example");
    const denied = await call("/healthz", { headers: { origin: "https://evil.example" } }, cors);
    expect(denied.headers.get("access-control-allow-origin")).toBeNull();
    const preflight = await call(
      "/api/v1/search",
      {
        method: "OPTIONS",
        headers: {
          origin: "https://a.example",
          "access-control-request-method": "GET",
        },
      },
      cors,
    );
    expect(preflight.status).toBe(200);
    expect(preflight.headers.get("access-control-allow-methods")).toBe("GET");
    expect(preflight.headers.get("access-control-allow-origin")).toBe("https://a.example");
  });
});
