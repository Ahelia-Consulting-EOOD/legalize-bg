/** Golden request set for the parity gate (spec: "Parity gate" section).
 * ≥40 requests covering every endpoint, every reachable error code,
 * Cyrillic searches, ?date= edge cases, from/to diff aliases, and the
 * 409 AMBIGUOUS_NAME case. Paths are given unencoded; run.mjs encodes. */

const NAREDBA1 =
  "naredba-1-ot-1-dekemvri-2022-g-za-priemane-na-farmako-terapevtichno-rakovodstvo-";
const NAREDBA1_TITLE =
  "НАРЕДБА № 1 ОТ 1 ДЕКЕМВРИ 2022 Г. ЗА ПРИЕМАНЕ НА ФАРМАКО-ТЕРАПЕВТИЧНО РЪКОВОДСТВО ПО АКУШЕРСТВО И ГИНЕКОЛОГИЯ";
const ZOP = "zakon-za-obshtestvenite-porachki";

export const GOLDEN_REQUESTS = [
  // ── health + stats ──
  { id: "healthz", path: "/healthz" },
  { id: "stats", path: "/api/v1/stats" },

  // ── laws list ──
  { id: "laws-default", path: "/api/v1/laws?limit=2" },
  { id: "laws-category-codes", path: "/api/v1/laws?category=codes&limit=5" },
  { id: "laws-estado-derogado", path: "/api/v1/laws?estado=derogado&limit=3" },
  { id: "laws-combined", path: "/api/v1/laws?category=laws&estado=vigente&limit=2&offset=5" },
  { id: "laws-limit-cap", path: "/api/v1/laws?limit=500&offset=3590" },
  { id: "laws-offset-negative", path: "/api/v1/laws?offset=-5&limit=1" },
  { id: "laws-422-limit", path: "/api/v1/laws?limit=abc" },

  // ── get_law: resolution + versions + dates ──
  { id: "law-small", path: "/api/v1/laws/zakon-za-amnistiya-ot-1989-g" },
  { id: "law-docid", path: "/api/v1/laws/2137229122" },
  { id: "law-title-resolve", path: `/api/v1/laws/${NAREDBA1_TITLE}` },
  { id: "law-version-old", path: `/api/v1/laws/${NAREDBA1}?date=2023-01-01` },
  { id: "law-version-boundary-a", path: `/api/v1/laws/${NAREDBA1}?date=2026-06-04` },
  { id: "law-version-boundary-b", path: `/api/v1/laws/${NAREDBA1}?date=2026-06-05` },
  { id: "law-noversion", path: `/api/v1/laws/${NAREDBA1}?date=1900-01-01` },
  { id: "law-invalid-date", path: `/api/v1/laws/${NAREDBA1}?date=junk` },
  { id: "law-invalid-date-cal", path: `/api/v1/laws/${NAREDBA1}?date=2026-02-30` },
  { id: "law-invalid-date-empty", path: `/api/v1/laws/${NAREDBA1}?date=` },
  { id: "law-notfound", path: "/api/v1/laws/no-such-law-xyz" },
  { id: "law-notfound-suggestions", path: "/api/v1/laws/обществени поръчки" },
  { id: "law-ambiguous-409", path: "/api/v1/laws/ЗАКОН ЗА АМНИСТИЯ ОТ 1989 Г." },
  { id: "law-warnings", path: "/api/v1/laws/etichen-kodeks-na-sadebnite-sluzhiteli" },

  // ── articles ──
  { id: "art-whole", path: `/api/v1/laws/${ZOP}/articles/5` },
  { id: "art-alinea", path: `/api/v1/laws/${ZOP}/articles/чл. 5, ал. 2` },
  { id: "art-dot", path: `/api/v1/laws/${ZOP}/articles/5.2` },
  { id: "art-suffix", path: `/api/v1/laws/${ZOP}/articles/чл. 112а` },
  { id: "art-range-400", path: `/api/v1/laws/${ZOP}/articles/5-7` },
  { id: "art-bad-400", path: `/api/v1/laws/${ZOP}/articles/abc` },
  { id: "art-notfound", path: `/api/v1/laws/${ZOP}/articles/99999` },
  { id: "art-bad-date", path: `/api/v1/laws/${ZOP}/articles/5?date=junk` },
  { id: "art-versioned", path: `/api/v1/laws/${NAREDBA1}/articles/1?date=2023-01-01` },

  // ── history ──
  { id: "history-mitnitsite", path: "/api/v1/laws/zakon-za-mitnitsite/history" },
  { id: "history-small", path: `/api/v1/laws/${NAREDBA1}/history` },
  { id: "history-notfound", path: "/api/v1/laws/nope-nope/history" },

  // ── diff (from/to aliases) ──
  { id: "diff-real", path: `/api/v1/laws/${NAREDBA1}/diff?from=2023-01-01&to=2026-07-01`, normalize: "diff" },
  { id: "diff-note", path: "/api/v1/laws/zakon-za-mitnitsite/diff?from=2026-07-01&to=2026-07-02" },
  { id: "diff-reversed-400", path: `/api/v1/laws/${NAREDBA1}/diff?from=2026-01-01&to=2025-01-01` },
  { id: "diff-noversion", path: `/api/v1/laws/${NAREDBA1}/diff?from=1900-01-01&to=2026-07-01` },
  { id: "diff-baddate", path: `/api/v1/laws/${NAREDBA1}/diff?from=bad&to=2026-07-01` },
  { id: "diff-missing-from-422", path: `/api/v1/laws/${NAREDBA1}/diff?to=2026-01-01` },
  { id: "diff-missing-both-422", path: `/api/v1/laws/${NAREDBA1}/diff` },

  // ── search (Cyrillic, expansion, caps, errors) ──
  { id: "search-zop-abbrev", path: "/api/v1/search?q=ЗОП&limit=3" },
  { id: "search-multiword", path: "/api/v1/search?q=обществени поръчки&limit=5" },
  { id: "search-category", path: "/api/v1/search?q=труд&category=codes&limit=5" },
  { id: "search-definite-form", path: "/api/v1/search?q=поръчките&limit=3" },
  { id: "search-include-body", path: "/api/v1/search?q=ЗОП&limit=3&include_body=true" },
  { id: "search-broad-400", path: "/api/v1/search?q=наредба" },
  { id: "search-broad-definite-400", path: "/api/v1/search?q=Кодексът." },
  { id: "search-long-400", path: `/api/v1/search?q=${"щ".repeat(600)}` },
  { id: "search-422-missing", path: "/api/v1/search" },
  { id: "search-422-empty", path: "/api/v1/search?q=" },
  { id: "search-422-types", path: "/api/v1/search?q=тест&limit=abc&include_body=xx" },
  { id: "search-colon-empty", path: "/api/v1/search?q=foo:bar" },
  { id: "search-quote-empty", path: '/api/v1/search?q="unbalanced' },
  { id: "search-limit-cap", path: "/api/v1/search?q=закон за&limit=100" },

  // ── metrics / openapi / 404 ──
  { id: "metrics", path: "/api/v1/metrics", normalize: "metrics" },
  { id: "openapi", path: "/api/v1/openapi.json", normalize: "openapi" },
  { id: "route-404", path: "/api/v1/nope" },
];
