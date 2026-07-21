/** Hand-crafted fixture corpus conforming to the cf-data-plane spec
 * shapes (D1 tables copied from catalog.db; R2 acts/versions/meta JSON).
 * Cyrillic titles/bodies; one multi-version act; one ambiguous title
 * pair; one date_uncertain act. */

import { env } from "cloudflare:test";

import { bgNormalize } from "../src/normalize";
import { textHash16 } from "../src/acts";

export const SCHEMA_STATEMENTS = [
  `CREATE TABLE IF NOT EXISTS laws (
    law_id TEXT PRIMARY KEY,
    doc_id INTEGER,
    title TEXT NOT NULL,
    category TEXT NOT NULL,
    status TEXT DEFAULT 'vigente',
    current_commit TEXT
  )`,
  `CREATE TABLE IF NOT EXISTS law_versions (
    id INTEGER PRIMARY KEY,
    law_id TEXT REFERENCES laws(law_id),
    valid_from DATE NOT NULL,
    valid_to DATE,
    commit_hash TEXT NOT NULL,
    dv_issue TEXT,
    dv_date DATE,
    amending_act TEXT,
    date_uncertain INTEGER NOT NULL DEFAULT 0
  )`,
  `CREATE TABLE IF NOT EXISTS amendments (
    id INTEGER PRIMARY KEY,
    source_act TEXT NOT NULL,
    target_law TEXT REFERENCES laws(law_id),
    operation TEXT NOT NULL,
    affected_articles TEXT,
    dv_issue TEXT,
    dv_date DATE
  )`,
  `CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
  )`,
  `CREATE VIRTUAL TABLE IF NOT EXISTS laws_fts USING fts5(
    law_id UNINDEXED,
    title,
    body,
    category UNINDEXED,
    tokenize='unicode61 remove_diacritics 2'
  )`,
  `CREATE INDEX IF NOT EXISTS idx_versions_date ON law_versions(law_id, valid_from)`,
  `CREATE INDEX IF NOT EXISTS idx_amendments_target ON amendments(target_law, dv_date)`,
];

interface FixtureLaw {
  lawId: string;
  docId: number;
  title: string;
  category: string;
  status?: string;
  currentCommit: string;
  versions: {
    validFrom: string;
    validTo: string | null;
    commit: string;
    dateUncertain?: number;
  }[];
  amendments?: { operation: string; dvIssue: string; dvDate: string }[];
  body: string;
  articles: Record<string, { text: string; paragraphs?: Record<string, string> }>;
  /** per-version overrides for historical version JSON */
  versionBodies?: Record<string, string>;
  versionArticles?: Record<
    string,
    Record<string, { text: string; paragraphs?: Record<string, string> }>
  >;
  ultimaActualizacion: string;
  fechaPublicacion: string;
}

export const KODEKS_BODY_V1 =
  "# ТЕСТОВ КОДЕКС\n\nЧл. 1. Старият текст на първата разпоредба.\n\nЧл. 2. (1) Първа алинея стара. (2) Втора алинея.\n";
export const KODEKS_BODY_V2 =
  "# ТЕСТОВ КОДЕКС\n\nЧл. 1. Новият текст на първата разпоредба.\n\nЧл. 2. (1) Първа алинея стара. (2) Втора алинея.\n";
export const KODEKS_BODY_V3 =
  "# ТЕСТОВ КОДЕКС\n\nЧл. 1. Новият текст на първата разпоредба.\n\nЧл. 2. (1) Първа алинея стара. (2) Втора алинея.\n\nЧл. 3. Нова разпоредба.\n";

const FIXTURES: FixtureLaw[] = [
  {
    lawId: "zakon-za-testovite-porachki",
    docId: 111,
    title: "ЗАКОН ЗА ТЕСТОВИТЕ ПОРЪЧКИ",
    category: "laws",
    currentCommit: "aaa1",
    versions: [{ validFrom: "2020-01-01", validTo: null, commit: "aaa1" }],
    amendments: [{ operation: "enacted", dvIssue: "10/2020", dvDate: "2020-01-01" }],
    body:
      "# ЗАКОН ЗА ТЕСТОВИТЕ ПОРЪЧКИ\n\nЧл. 1. Обща разпоредба за тестовете.\n\n" +
      "Чл. 2. (1) Публични тестове са тези. (2) Частни тестове са другите.\n\n" +
      "Чл. 14а. Специална разпоредба.\n",
    articles: {
      "1": { text: "Чл. 1. Обща разпоредба за тестовете." },
      "2": {
        text: "Чл. 2. (1) Публични тестове са тези. (2) Частни тестове са другите.",
        paragraphs: { "1": "Публични тестове са тези.", "2": "Частни тестове са другите." },
      },
      "14а": { text: "Чл. 14а. Специална разпоредба." },
    },
    ultimaActualizacion: "2020-01-01",
    fechaPublicacion: "2020-01-01",
  },
  {
    lawId: "zakon-za-obshtestvenite-porachki",
    docId: 333,
    title: "ЗАКОН ЗА ОБЩЕСТВЕНИТЕ ПОРЪЧКИ",
    category: "laws",
    currentCommit: "bbb1",
    versions: [{ validFrom: "2016-04-15", validTo: null, commit: "bbb1" }],
    amendments: [{ operation: "enacted", dvIssue: "13/2016", dvDate: "2016-02-16" }],
    body: "# ЗАКОН ЗА ОБЩЕСТВЕНИТЕ ПОРЪЧКИ\n\nЧл. 1. Обществените поръчки се възлагат по реда на този закон.\n",
    articles: {
      "1": { text: "Чл. 1. Обществените поръчки се възлагат по реда на този закон." },
    },
    ultimaActualizacion: "2016-04-15",
    fechaPublicacion: "2016-02-16",
  },
  {
    lawId: "naredba-za-testovite-porachki",
    docId: 444,
    title: "НАРЕДБА ЗА ТЕСТОВИТЕ ПОРЪЧКИ",
    category: "ordinances",
    currentCommit: "ccc1",
    versions: [{ validFrom: "2021-03-01", validTo: null, commit: "ccc1" }],
    body: "# НАРЕДБА ЗА ТЕСТОВИТЕ ПОРЪЧКИ\n\nЧл. 1. Редът за тестовите поръчки.\n",
    articles: { "1": { text: "Чл. 1. Редът за тестовите поръчки." } },
    ultimaActualizacion: "2021-03-01",
    fechaPublicacion: "2021-03-01",
  },
  {
    lawId: "testov-kodeks",
    docId: 222,
    title: "ТЕСТОВ КОДЕКС",
    category: "codes",
    currentCommit: "c3",
    versions: [
      { validFrom: "2010-01-01", validTo: "2020-12-31", commit: "c1" },
      { validFrom: "2021-01-01", validTo: "2023-05-31", commit: "c2" },
      { validFrom: "2023-06-01", validTo: null, commit: "c3" },
    ],
    amendments: [
      { operation: "enacted", dvIssue: "1/2010", dvDate: "2010-01-01" },
      { operation: "amendment", dvIssue: "5/2021", dvDate: "2021-01-01" },
      { operation: "amendment", dvIssue: "45/2023", dvDate: "2023-06-01" },
    ],
    body: KODEKS_BODY_V3,
    articles: {
      "1": { text: "Чл. 1. Новият текст на първата разпоредба." },
      "2": {
        text: "Чл. 2. (1) Първа алинея стара. (2) Втора алинея.",
        paragraphs: { "1": "Първа алинея стара.", "2": "Втора алинея." },
      },
      "3": { text: "Чл. 3. Нова разпоредба." },
    },
    versionBodies: { "2010-01-01": KODEKS_BODY_V1, "2021-01-01": KODEKS_BODY_V2 },
    versionArticles: {
      "2010-01-01": {
        "1": { text: "Чл. 1. Старият текст на първата разпоредба." },
        "2": {
          text: "Чл. 2. (1) Първа алинея стара. (2) Втора алинея.",
          paragraphs: { "1": "Първа алинея стара.", "2": "Втора алинея." },
        },
      },
      "2021-01-01": {
        "1": { text: "Чл. 1. Новият текст на първата разпоредба." },
        "2": {
          text: "Чл. 2. (1) Първа алинея стара. (2) Втора алинея.",
          paragraphs: { "1": "Първа алинея стара.", "2": "Втора алинея." },
        },
      },
    },
    ultimaActualizacion: "2023-06-01",
    fechaPublicacion: "2010-01-01",
  },
  {
    lawId: "zakon-za-testovata-amnistiya",
    docId: 551,
    title: "ЗАКОН ЗА ТЕСТОВАТА АМНИСТИЯ",
    category: "laws",
    currentCommit: "ddd1",
    versions: [{ validFrom: "1990-01-01", validTo: null, commit: "ddd1" }],
    body: "# ЗАКОН ЗА ТЕСТОВАТА АМНИСТИЯ\n\nЧл. 1. Амнистира се.\n",
    articles: { "1": { text: "Чл. 1. Амнистира се." } },
    ultimaActualizacion: "1990-01-01",
    fechaPublicacion: "1990-01-01",
  },
  {
    lawId: "zakon-za-testovata-amnistiya-2",
    docId: 552,
    title: "ЗАКОН ЗА ТЕСТОВАТА АМНИСТИЯ",
    category: "laws",
    currentCommit: "ddd2",
    versions: [{ validFrom: "1991-01-01", validTo: null, commit: "ddd2" }],
    body: "# ЗАКОН ЗА ТЕСТОВАТА АМНИСТИЯ\n\nЧл. 1. Пак се амнистира.\n",
    articles: { "1": { text: "Чл. 1. Пак се амнистира." } },
    ultimaActualizacion: "1991-01-01",
    fechaPublicacion: "1991-01-01",
  },
  {
    lawId: "neizvesten-akt",
    docId: 666,
    title: "ЕТИЧЕН КОДЕКС НА ТЕСТЕРИТЕ",
    category: "ordinances",
    currentCommit: "eee1",
    versions: [{ validFrom: "2026-04-20", validTo: null, commit: "eee1", dateUncertain: 1 }],
    body: "# ЕТИЧЕН КОДЕКС НА ТЕСТЕРИТЕ\n\nЧл. 1. Тестерите са етични.\n",
    articles: { "1": { text: "Чл. 1. Тестерите са етични." } },
    ultimaActualizacion: "2026-04-20",
    fechaPublicacion: "2026-04-20",
  },
];

function preamble(f: FixtureLaw, ultima: string): string {
  return (
    "---\n" +
    `titulo: ${f.title}\n` +
    `identificador: '${f.docId}'\n` +
    "pais: bg\n" +
    `fecha_publicacion: '${f.fechaPublicacion}'\n` +
    `ultima_actualizacion: '${ultima}'\n` +
    "estado: vigente\n" +
    "---\n\n"
  );
}

async function actJson(
  f: FixtureLaw,
  body: string,
  ultima: string,
  articleMap?: Record<string, { text: string; paragraphs?: Record<string, string> }>,
): Promise<string> {
  const articles: Record<string, unknown> = {};
  for (const [id, a] of Object.entries(articleMap ?? f.articles)) {
    articles[id] = {
      text: a.text,
      text_hash: await textHash16(a.text),
      ...(a.paragraphs ? { paragraphs: a.paragraphs } : {}),
    };
  }
  return JSON.stringify({
    meta: {
      titulo: f.title,
      identificador: String(f.docId),
      rango: "закон",
      estado: f.status ?? "vigente",
      fecha_publicacion: f.fechaPublicacion,
      ultima_actualizacion: ultima,
      dv_issue: "13",
      dv_year: 2016,
      effective_date: f.fechaPublicacion,
      eli: `/eli/bg/закон/${f.lawId}/con`,
      amendment_history: (f.amendments ?? []).map((a) => ({
        dv: a.dvIssue,
        date: a.dvDate,
      })),
    },
    preamble_raw: preamble(f, ultima),
    body_markdown: body,
    articles,
  });
}

export async function seedFixtures(): Promise<void> {
  for (const stmt of SCHEMA_STATEMENTS) {
    await env.DB.prepare(stmt).run();
  }
  const inserts: D1PreparedStatement[] = [];
  for (const f of FIXTURES) {
    inserts.push(
      env.DB.prepare(
        "INSERT OR REPLACE INTO laws (law_id, doc_id, title, category, status, current_commit) VALUES (?, ?, ?, ?, ?, ?)",
      ).bind(f.lawId, f.docId, f.title, f.category, f.status ?? "vigente", f.currentCommit),
    );
    for (const v of f.versions) {
      inserts.push(
        env.DB.prepare(
          "INSERT INTO law_versions (law_id, valid_from, valid_to, commit_hash, date_uncertain) VALUES (?, ?, ?, ?, ?)",
        ).bind(f.lawId, v.validFrom, v.validTo, v.commit, v.dateUncertain ?? 0),
      );
    }
    for (const a of f.amendments ?? []) {
      inserts.push(
        env.DB.prepare(
          "INSERT INTO amendments (source_act, target_law, operation, dv_issue, dv_date) VALUES (?, ?, ?, ?, ?)",
        ).bind(f.lawId, f.lawId, a.operation, a.dvIssue, a.dvDate),
      );
    }
    inserts.push(
      env.DB.prepare(
        "INSERT INTO laws_fts (law_id, title, body, category) VALUES (?, ?, ?, ?)",
      ).bind(f.lawId, bgNormalize(f.title), bgNormalize(f.body), f.category),
    );
  }
  await env.DB.batch(inserts);

  for (const f of FIXTURES) {
    await env.ACTS.put(`acts/${f.lawId}.json`, await actJson(f, f.body, f.ultimaActualizacion));
    for (const v of f.versions) {
      const body =
        f.versionBodies?.[v.validFrom] ?? (v.commit === f.currentCommit ? f.body : null);
      if (body === null) continue;
      await env.ACTS.put(
        `versions/${f.lawId}/${v.validFrom}.json`,
        await actJson(f, body, v.validFrom, f.versionArticles?.[v.validFrom]),
      );
    }
  }

  await env.ACTS.put(
    "meta/stats.json",
    JSON.stringify({
      total_acts: FIXTURES.length,
      by_category: { codes: 1, laws: 4, ordinances: 2 },
      by_status: { vigente: FIXTURES.length },
      multi_version_acts: 1,
      latest_version_date: "2026-04-20",
      exported_at: "2026-07-21T00:00:00Z",
    }),
  );
}
