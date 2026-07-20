/** Port of index/fts.py `bg_normalize` — MUST stay in lockstep with the
 * Python original (symmetric normalization is what makes FTS5 queries
 * match the exporter-built index). */

/** (suffix, minStemLen) ordered longest-first — verbatim from
 * index/fts.py `_BG_DEFINITE_SUFFIXES`. */
const BG_DEFINITE_SUFFIXES: ReadonlyArray<readonly [string, number]> = [
  ["ият", 3], // masc adj long-form definite: новият → нов (FR-013)
  ["ът", 4], // masc nom: градът → град
  ["ят", 4], // masc nom variant: дъждът → дъжд
  ["та", 4], // feminine: жената → жена
  ["то", 4], // neuter: детето → дете
  ["те", 4], // plural: новите → нови, обществените → обществени
];

const WS_RE = /\s+/g;

function stripDefiniteArticle(token: string): string {
  for (const [suffix, minStem] of BG_DEFINITE_SUFFIXES) {
    if (token.endsWith(suffix) && token.length - suffix.length >= minStem) {
      return token.slice(0, token.length - suffix.length);
    }
  }
  return token;
}

export function bgNormalize(text: string | null | undefined): string {
  if (!text) return "";
  let t = text.toLowerCase();
  t = t.replace(WS_RE, " ").trim();
  if (!t) return "";
  return t
    .split(" ")
    .map(stripDefiniteArticle)
    .join(" ");
}
