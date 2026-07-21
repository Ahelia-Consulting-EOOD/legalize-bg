/** git-style unified diff over act text using the `diff` npm package.
 *
 * FastAPI runs `git diff <c1> <c2> -- {category}/{law_id}.md` over the
 * FULL file. When the R2 JSON carries `preamble_raw` (frontmatter bytes),
 * we reconstruct the full file and reproduce git's hunks exactly; when it
 * does not, we diff body_markdown only (spec v1 shape) — the parity
 * harness then compares body-level +/- lines only. Sanctioned divergence
 * either way: the `diff --git`/`index` header lines and the function
 * context git appends after `@@ ... @@`. */

import { structuredPatch } from "diff";

export function unifiedGitDiff(relPath: string, oldText: string, newText: string): string {
  const patch = structuredPatch(relPath, relPath, oldText, newText, undefined, undefined, {
    context: 3,
  });
  if (patch.hunks.length === 0) return "";
  const lines: string[] = [
    `diff --git a/${relPath} b/${relPath}`,
    `--- a/${relPath}`,
    `+++ b/${relPath}`,
  ];
  for (const hunk of patch.hunks) {
    const oldRange = hunk.oldLines === 1 ? `${hunk.oldStart}` : `${hunk.oldStart},${hunk.oldLines}`;
    const newRange = hunk.newLines === 1 ? `${hunk.newStart}` : `${hunk.newStart},${hunk.newLines}`;
    lines.push(`@@ -${oldRange} +${newRange} @@`);
    lines.push(...hunk.lines);
  }
  return lines.join("\n") + "\n";
}
