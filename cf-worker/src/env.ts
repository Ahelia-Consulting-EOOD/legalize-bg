export interface Env {
  DB: D1Database;
  ACTS: R2Bucket;
  /** Comma-separated allowed origins; empty/unset = CORS disabled. */
  CORS_ORIGINS?: string;
}
