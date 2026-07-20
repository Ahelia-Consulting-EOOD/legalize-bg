/** Port of the D-026/D-052 error taxonomy (mcp_server/errors.py +
 * api/errors.py). Response body is `{"code": ..., **payload}`, status
 * from HTTP_STATUS_BY_CODE — byte-compatible with FastAPI. */

export const HTTP_STATUS_BY_CODE: Readonly<Record<string, number>> = {
  INVALID_DATE: 400,
  INVALID_ARTICLE_SPEC: 400,
  INVALID_DATE_RANGE: 400,
  QUERY_TOO_BROAD: 400,
  LAW_NOT_FOUND: 404,
  ARTICLE_NOT_FOUND: 404,
  NO_VERSION_AT_DATE: 404,
  AMBIGUOUS_NAME: 409,
  DIFF_FAILED: 500,
  INDEX_MISSING: 503,
  INDEX_STALE: 503,
};

export type JsonValue =
  | string
  | number
  | boolean
  | null
  | JsonValue[]
  | { [k: string]: JsonValue };

export class ToolError extends Error {
  readonly code: string;
  readonly payload: Record<string, JsonValue>;

  constructor(code: string, payload: Record<string, JsonValue>) {
    super(JSON.stringify({ code, ...payload }));
    this.code = code;
    this.payload = payload;
  }

  toDict(): Record<string, JsonValue> {
    return { code: this.code, ...this.payload };
  }

  get status(): number {
    return HTTP_STATUS_BY_CODE[this.code] ?? 500;
  }
}

/** Port of mcp_server/queries.py `is_catalog_error` — recognizes a
 * catalog-level SQLite error (schema missing/corrupt) by message. D1
 * wraps SQLite messages (e.g. "D1_ERROR: no such table: laws"), so we
 * match by substring exactly like the Python original. */
const SQLITE_CATALOG_ERRORS = [
  "no such table",
  "no such column",
  "unable to open database",
  "database disk image is malformed",
  "file is not a database",
];

export function isCatalogError(message: string): boolean {
  const msg = message.toLowerCase();
  return SQLITE_CATALOG_ERRORS.some((m) => msg.includes(m));
}

/** Map a caught D1/SQL error to the INDEX_MISSING ToolError the FastAPI
 * layer produces for catalog-level sqlite3.OperationalError. Non-catalog
 * errors are re-thrown (mirrors api/errors.py `_catalog_error`). */
export function mapCatalogError(e: unknown): never {
  const msg = e instanceof Error ? `${e.message}${e.cause instanceof Error ? ": " + e.cause.message : ""}` : String(e);
  if (isCatalogError(msg)) {
    throw new ToolError("INDEX_MISSING", {
      detail: msg.slice(0, 300),
      hint: "catalog.db is missing tables or corrupt — re-run `python -m index.build`",
    });
  }
  throw e;
}
