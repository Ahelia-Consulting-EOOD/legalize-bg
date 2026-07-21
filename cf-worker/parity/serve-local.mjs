#!/usr/bin/env node
/**
 * Boot the worker locally (Miniflare) on a REAL `python -m export_cf`
 * export, for the parity gate:
 *
 *   1. npx wrangler deploy --dry-run --outdir dist        (bundle)
 *   2. node parity/serve-local.mjs --export <dir> [--db <ready.sqlite>]
 *        [--full] [--port 8788]
 *   3. node parity/run.mjs --against http://127.0.0.1:8788
 *
 * --export points at the exporter output (d1-schema.sql, d1-data-*.sql,
 * r2/ tree). D1 is seeded either from --db (a ready-imported SQLite of
 * the same dump — fast, recommended) or by executing the SQL chunks.
 * R2 is seeded in-process via the Miniflare API: by default only the
 * keys the golden set touches (plus meta/stats.json); --full loads the
 * whole r2/ tree.
 */

import { cp, mkdir, readFile, readdir, rm, stat } from "node:fs/promises";
import { existsSync } from "node:fs";
import { join } from "node:path";

import { Miniflare } from "miniflare";

import { GOLDEN_REQUESTS } from "./requests.mjs";

const args = process.argv.slice(2);
function argOf(name, fallback = null) {
  const i = args.indexOf(name);
  return i !== -1 && args[i + 1] ? args[i + 1] : fallback;
}
const exportDir = argOf("--export");
const readyDb = argOf("--db");
const full = args.includes("--full");
const port = parseInt(argOf("--port", "8788"), 10);
if (!exportDir) {
  console.error("usage: serve-local.mjs --export <cf-export-dir> [--db <ready.sqlite>] [--full]");
  process.exit(2);
}

const STATE = ".parity-state";
const DIST = "dist/index.js";
if (!existsSync(DIST)) {
  console.error(`bundle missing: run \`npx wrangler deploy --dry-run --outdir dist\` first`);
  process.exit(2);
}

function mfOptions() {
  return {
    modules: true,
    scriptPath: DIST,
    compatibilityDate: "2026-06-01",
    d1Databases: { DB: "legalize-bg" },
    r2Buckets: { ACTS: "legalize-bg-acts" },
    bindings: { CORS_ORIGINS: "" },
    d1Persist: join(STATE, "d1"),
    r2Persist: join(STATE, "r2"),
    port,
  };
}

async function findSqliteFiles(dir) {
  const out = [];
  async function walk(d) {
    for (const e of await readdir(d, { withFileTypes: true })) {
      const p = join(d, e.name);
      if (e.isDirectory()) await walk(p);
      else if (e.name.endsWith(".sqlite")) out.push(p);
    }
  }
  if (existsSync(dir)) await walk(dir);
  return out;
}

// ── D1 seed ────────────────────────────────────────────────────────────

async function seedD1() {
  const marker = join(STATE, "d1-seeded");
  if (existsSync(marker)) {
    console.log("D1 already seeded (rm .parity-state to reseed)");
    return;
  }
  await rm(join(STATE, "d1"), { recursive: true, force: true });
  // Boot once so Miniflare creates the backing SQLite file, then swap it.
  let mf = new Miniflare({ ...mfOptions(), port: undefined });
  const db = await mf.getD1Database("DB");
  await db.prepare("SELECT 1").run();
  await mf.dispose();
  const files = (await findSqliteFiles(join(STATE, "d1"))).filter(
    (f) => !f.endsWith("metadata.sqlite"),
  );
  if (files.length !== 1) {
    console.error(`expected exactly one D1 sqlite file, found ${files.length}`);
    process.exit(1);
  }
  const target = files[0];
  if (readyDb) {
    console.log(`placing ready-imported D1 database: ${readyDb} -> ${target}`);
    await rm(target + "-wal", { force: true });
    await rm(target + "-shm", { force: true });
    await cp(readyDb, target);
  } else {
    console.log("importing d1-schema.sql + chunks via Miniflare (slow path)...");
    mf = new Miniflare({ ...mfOptions(), port: undefined });
    const d1 = await mf.getD1Database("DB");
    const sqlFiles = [
      "d1-schema.sql",
      ...(await readdir(exportDir)).filter((f) => /^d1-data-\d+\.sql$/.test(f)).sort(),
    ];
    for (const f of sqlFiles) {
      console.log(`  ${f}`);
      const sql = await readFile(join(exportDir, f), "utf8");
      await d1.exec(sql);
    }
    await mf.dispose();
  }
  await mkdir(STATE, { recursive: true });
  await (await import("node:fs/promises")).writeFile(marker, new Date().toISOString());
}

// ── R2 seed ────────────────────────────────────────────────────────────

function goldenR2Keys() {
  // acts/ + versions/ keys the golden requests can touch, derived from
  // the slugs referenced in requests.mjs, plus stats.
  const slugs = new Set();
  for (const r of GOLDEN_REQUESTS) {
    const m = /^\/api\/v1\/laws\/([^/?]+)/.exec(r.path);
    if (m) slugs.add(decodeURIComponent(m[1]));
  }
  return { slugs, always: ["meta/stats.json"] };
}

async function seedR2() {
  const mf = new Miniflare({ ...mfOptions(), port: undefined });
  const bucket = await mf.getR2Bucket("ACTS");
  const r2root = join(exportDir, "r2");

  async function putFile(key) {
    const p = join(r2root, key);
    if (!existsSync(p)) return false;
    if (await bucket.head(key)) return true;
    const data = await readFile(p);
    await bucket.put(key, new Uint8Array(data.buffer, data.byteOffset, data.byteLength), {
      httpMetadata: { contentType: "application/json" },
    });
    return true;
  }

  if (full) {
    let n = 0;
    async function walk(dir, prefix) {
      for (const e of await readdir(dir, { withFileTypes: true })) {
        const p = join(dir, e.name);
        const key = prefix ? `${prefix}/${e.name}` : e.name;
        if (e.isDirectory()) await walk(p, key);
        else {
          await putFile(key);
          if (++n % 500 === 0) console.log(`  ${n} objects...`);
        }
      }
    }
    await walk(r2root, "");
    console.log(`R2 seeded (full): ${n} objects`);
  } else {
    const { slugs, always } = goldenR2Keys();
    let n = 0;
    for (const key of always) if (await putFile(key)) n++;
    for (const slug of slugs) {
      if (await putFile(`acts/${slug}.json`)) n++;
      const vdir = join(r2root, "versions", slug);
      if (existsSync(vdir)) {
        for (const f of await readdir(vdir)) {
          if (await putFile(`versions/${slug}/${f}`)) n++;
        }
      }
    }
    console.log(`R2 seeded (golden subset): ${n} objects`);
  }
  await mf.dispose();
}

// ── main ───────────────────────────────────────────────────────────────

await mkdir(STATE, { recursive: true });
await seedD1();
await seedR2();

const mf = new Miniflare(mfOptions());
const url = await mf.ready;
console.log(`worker (real export) listening at ${url}`);
console.log("run: node parity/run.mjs --against " + String(url).replace(/\/$/, ""));
