/** R2 act-JSON access (spec: R2 bucket `legalize-bg-acts`).
 * acts/{law_id}.json for the current version; versions/{law_id}/{valid_from}.json
 * for historical versions. */

import { ToolError, type JsonValue } from "./errors";

export interface ActArticle {
  text: string;
  text_hash?: string;
  /** Paragraph text keyed by alinea number. Spec shape is plain strings;
   * an object form { text, text_hash } is accepted defensively. */
  paragraphs?: Record<string, string | { text: string; text_hash?: string }>;
}

export interface ActJson {
  meta: Record<string, JsonValue>;
  body_markdown: string;
  /** Optional (spec v1.1 proposal): raw file bytes before body_markdown,
   * so preamble_raw + body_markdown == the exact .md file — lets /diff
   * reproduce git's full-file hunks. */
  preamble_raw?: string;
  articles: Record<string, ActArticle>;
}

export function actKey(
  lawId: string,
  commitHash: string,
  validFrom: string,
  currentCommit: string | null,
): string {
  return commitHash === currentCommit
    ? `acts/${lawId}.json`
    : `versions/${lawId}/${validFrom}.json`;
}

const REBUILD_HINT =
  "catalog and corpus have diverged — re-run `python -m index.build` against this corpus";

export async function fetchActJson(
  bucket: R2Bucket,
  lawId: string,
  commitHash: string,
  validFrom: string,
  currentCommit: string | null,
): Promise<ActJson> {
  const key = actKey(lawId, commitHash, validFrom, currentCommit);
  const obj = await bucket.get(key);
  if (!obj) {
    // Mirrors read_law_markdown's INDEX_STALE: the catalog points at a
    // version whose text object is not in the export.
    throw new ToolError("INDEX_STALE", {
      law_id: lawId,
      commit_hash: commitHash,
      detail: `act object missing from R2: ${key}`,
      hint: REBUILD_HINT,
    });
  }
  return (await obj.json()) as ActJson;
}

/** sha256(text)[:16] hex — identical to index/provisions.py `_hash`,
 * used to derive per-paragraph text_hash from the R2 paragraph text. */
export async function textHash16(text: string): Promise<string> {
  const digest = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(text));
  return [...new Uint8Array(digest)]
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("")
    .slice(0, 16);
}
