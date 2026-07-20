#!/usr/bin/env node
/**
 * Parity gate (spec: "Parity gate" section, blocks deploy).
 *
 * Modes:
 *   node parity/run.mjs --capture [--base http://127.0.0.1:8787]
 *     Replays the golden request set against the reference FastAPI and
 *     writes parity/golden/{id}.json snapshots.
 *   node parity/run.mjs --against <base-url>
 *     Replays the set against a worker (wrangler dev or deployed) and
 *     byte-compares canonicalized JSON against the goldens. ANY
 *     unsanctioned divergence fails (exit 1). Writes parity-report.json.
 *
 * Sanctioned normalizations (ONLY these, per spec):
 *   - diff responses: the git header lines `diff --git`/`index` and the
 *     function-context text git appends after `@@ ... @@` (hunk ranges
 *     and hunk content ARE compared);
 *   - metrics values (shape compared, numbers/route-key traffic not);
 *   - openapi server URL (`servers` field).
 */

import { mkdir, readFile, writeFile } from "node:fs/promises";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import { GOLDEN_REQUESTS } from "./requests.mjs";

const HERE = dirname(fileURLToPath(import.meta.url));
const GOLDEN_DIR = join(HERE, "golden");

const args = process.argv.slice(2);
const capture = args.includes("--capture");
const baseIdx = args.indexOf(capture ? "--base" : "--against");
const base =
  baseIdx !== -1 && args[baseIdx + 1] ? args[baseIdx + 1] : "http://127.0.0.1:8787";

/** Encode a human-readable path (Cyrillic, spaces, quotes) for HTTP. */
function encodePath(path) {
  const [p, q] = path.split("?", 2);
  const encP = p
    .split("/")
    .map((seg) => encodeURIComponent(seg))
    .join("/");
  if (q === undefined) return encP;
  const encQ = q
    .split("&")
    .map((pair) => {
      const eq = pair.indexOf("=");
      if (eq === -1) return encodeURIComponent(pair);
      return `${encodeURIComponent(pair.slice(0, eq))}=${encodeURIComponent(pair.slice(eq + 1))}`;
    })
    .join("&");
  return `${encP}?${encQ}`;
}

async function fetchSnapshot(req) {
  const url = base.replace(/\/$/, "") + encodePath(req.path);
  const resp = await fetch(url);
  const text = await resp.text();
  let body;
  try {
    body = JSON.parse(text);
  } catch {
    body = { __raw_text__: text };
  }
  return {
    id: req.id,
    path: req.path,
    status: resp.status,
    headers: {
      "content-type": resp.headers.get("content-type"),
      "cache-control": resp.headers.get("cache-control"),
    },
    body,
  };
}

// ── sanctioned normalizations ───────────────────────────────────────────

/** Normalize a unified-diff string: drop `diff --git` + `index` header
 * lines and strip git's function-context suffix after `@@ ... @@`. Hunk
 * ranges and every hunk body line are preserved (and thus compared). */
function normalizeDiffText(text) {
  return text
    .split("\n")
    .filter((l) => !l.startsWith("diff --git ") && !l.startsWith("index "))
    .map((l) => {
      const m = /^(@@ -\d+(?:,\d+)? \+\d+(?:,\d+)? @@)/.exec(l);
      return m ? m[1] : l;
    })
    .join("\n");
}

function normalizeSnapshot(snap, mode) {
  const s = structuredClone(snap);
  if (mode === "diff" && s.body && typeof s.body.diff === "string") {
    s.body.diff = normalizeDiffText(s.body.diff);
  }
  if (mode === "metrics" && s.body && typeof s.body === "object") {
    // Shape-only: every route entry must carry the four numeric fields;
    // traffic-dependent keys/values are a sanctioned divergence.
    const shapeOk = Object.values(s.body).every(
      (m) =>
        m &&
        typeof m.calls === "number" &&
        typeof m.errors === "number" &&
        typeof m.total_ms === "number" &&
        typeof m.avg_ms === "number",
    );
    s.body = { __metrics_shape_ok__: shapeOk };
  }
  if (mode === "openapi" && s.body && typeof s.body === "object") {
    delete s.body.servers;
  }
  return s;
}

/** Canonical JSON: object keys sorted so key-order differences (which
 * JSON semantics ignore) don't produce false diffs. */
function canonical(value) {
  return JSON.stringify(sortKeys(value), null, 1);
}

function sortKeys(v) {
  if (Array.isArray(v)) return v.map(sortKeys);
  if (v && typeof v === "object") {
    return Object.fromEntries(
      Object.keys(v)
        .sort()
        .map((k) => [k, sortKeys(v[k])]),
    );
  }
  return v;
}

function firstDifference(a, b) {
  const la = a.split("\n");
  const lb = b.split("\n");
  for (let i = 0; i < Math.max(la.length, lb.length); i++) {
    if (la[i] !== lb[i]) {
      return { line: i + 1, golden: la[i] ?? "<missing>", actual: lb[i] ?? "<missing>" };
    }
  }
  return null;
}

// ── main ───────────────────────────────────────────────────────────────

if (capture) {
  await mkdir(GOLDEN_DIR, { recursive: true });
  for (const req of GOLDEN_REQUESTS) {
    const snap = await fetchSnapshot(req);
    await writeFile(join(GOLDEN_DIR, `${req.id}.json`), JSON.stringify(snap, null, 1) + "\n");
    console.log(`captured ${req.id} [${snap.status}]`);
  }
  console.log(`\n${GOLDEN_REQUESTS.length} goldens written to ${GOLDEN_DIR} (from ${base})`);
} else {
  const report = { against: base, at: new Date().toISOString(), results: [], failures: 0 };
  for (const req of GOLDEN_REQUESTS) {
    let golden;
    try {
      golden = JSON.parse(await readFile(join(GOLDEN_DIR, `${req.id}.json`), "utf8"));
    } catch {
      report.results.push({ id: req.id, ok: false, reason: "golden snapshot missing" });
      report.failures++;
      continue;
    }
    const actual = await fetchSnapshot(req);
    const g = normalizeSnapshot(golden, req.normalize);
    const a = normalizeSnapshot(actual, req.normalize);
    const problems = [];
    if (g.status !== a.status) problems.push(`status: golden ${g.status} vs actual ${a.status}`);
    for (const h of ["content-type", "cache-control"]) {
      if ((g.headers[h] ?? null) !== (a.headers[h] ?? null)) {
        problems.push(`header ${h}: golden ${g.headers[h]} vs actual ${a.headers[h]}`);
      }
    }
    const gBody = canonical(g.body);
    const aBody = canonical(a.body);
    if (gBody !== aBody) {
      const d = firstDifference(gBody, aBody);
      problems.push(
        `body diverges at canonical line ${d.line}: golden=${JSON.stringify(d.golden)} actual=${JSON.stringify(d.actual)}`,
      );
    }
    const ok = problems.length === 0;
    if (!ok) report.failures++;
    report.results.push({ id: req.id, ok, ...(ok ? {} : { problems }) });
    console.log(`${ok ? "PASS" : "FAIL"} ${req.id}${ok ? "" : "  " + problems.join(" | ")}`);
  }
  await writeFile(join(HERE, "parity-report.json"), JSON.stringify(report, null, 1) + "\n");
  console.log(
    `\n${report.results.length - report.failures}/${report.results.length} passed — report at parity/parity-report.json`,
  );
  process.exit(report.failures > 0 ? 1 : 0);
}
