/** Date validation (port of queries._validate_date) + pydantic-v2-shaped
 * 422 helpers matching FastAPI's request-validation error bodies. */

import { ToolError } from "./errors";

const ISO_DATE_RE = /^\d{4}-\d{2}-\d{2}$/;

/** Port of mcp_server/queries.py `_validate_date`: null → null ("today");
 * anything else must be a real YYYY-MM-DD calendar date. */
export function validateDate(value: string | null | undefined, param: string): string | null {
  if (value === null || value === undefined) return null;
  const v = typeof value === "string" ? value.trim() : "";
  if (!ISO_DATE_RE.test(v)) {
    throw new ToolError("INVALID_DATE", {
      param,
      value: String(value).slice(0, 50),
      expected: "YYYY-MM-DD",
    });
  }
  const [y, m, d] = v.split("-").map((x) => parseInt(x, 10)) as [number, number, number];
  const dt = new Date(Date.UTC(y, m - 1, d));
  if (dt.getUTCFullYear() !== y || dt.getUTCMonth() !== m - 1 || dt.getUTCDate() !== d) {
    throw new ToolError("INVALID_DATE", { param, value: v, expected: "YYYY-MM-DD" });
  }
  return v;
}

/** Server-local "today" (matches FastAPI's datetime.date.today(); the
 * worker runs in UTC — documented divergence for requests near local
 * midnight when the reference server runs in a non-UTC timezone). */
export function todayISO(): string {
  return new Date().toISOString().slice(0, 10);
}

// ── pydantic-v2 shaped 422 machinery ────────────────────────────────────

export interface ValidationDetail {
  type: string;
  loc: (string | number)[];
  msg: string;
  input: string | null;
  ctx?: Record<string, number>;
}

export class RequestValidationError extends Error {
  constructor(readonly detail: ValidationDetail[]) {
    super("request validation failed");
  }
}

export function missingParam(name: string): ValidationDetail {
  return { type: "missing", loc: ["query", name], msg: "Field required", input: null };
}

export function stringTooShort(name: string, input: string, minLength: number): ValidationDetail {
  return {
    type: "string_too_short",
    loc: ["query", name],
    msg: `String should have at least ${minLength} character${minLength === 1 ? "" : "s"}`,
    input,
    ctx: { min_length: minLength },
  };
}

const INT_RE = /^[+-]?\d+$/;

/** Parse an optional int query param the way FastAPI/pydantic v2 does;
 * pushes an int_parsing detail on failure. */
export function parseIntParam(
  raw: string | undefined,
  name: string,
  fallback: number,
  errors: ValidationDetail[],
): number {
  if (raw === undefined) return fallback;
  const t = raw.trim();
  if (INT_RE.test(t)) return parseInt(t, 10);
  errors.push({
    type: "int_parsing",
    loc: ["query", name],
    msg: "Input should be a valid integer, unable to parse string as an integer",
    input: raw,
  });
  return fallback;
}

// pydantic v2 lax-bool string values.
const BOOL_TRUE = new Set(["true", "t", "yes", "y", "on", "1"]);
const BOOL_FALSE = new Set(["false", "f", "no", "n", "off", "0"]);

export function parseBoolParam(
  raw: string | undefined,
  name: string,
  fallback: boolean,
  errors: ValidationDetail[],
): boolean {
  if (raw === undefined) return fallback;
  const t = raw.trim().toLowerCase();
  if (BOOL_TRUE.has(t)) return true;
  if (BOOL_FALSE.has(t)) return false;
  errors.push({
    type: "bool_parsing",
    loc: ["query", name],
    msg: "Input should be a valid boolean, unable to interpret input",
    input: raw,
  });
  return fallback;
}
