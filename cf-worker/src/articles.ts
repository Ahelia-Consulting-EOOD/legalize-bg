/** Port of mcp_server/queries.py article-spec parsing. */

export interface ArticleSpec {
  article: string;
  paragraph: string | null;
  rangeEnd: string | null;
}

export class InvalidArticleSpecError extends Error {}

// Python: rf"^\s*(?:чл\.\s*)?(\d+[а-я]?)(?:\s*-\s*(\d+[а-я]?)|(?:[\.,]\s*ал\.\s*|\s+ал\.\s*|\.)(\d+[а-я]?))?\s*$"
// with re.IGNORECASE. JS 'iu' flags give the same Cyrillic case folding.
const FULL_RE =
  /^\s*(?:чл\.\s*)?(\d+[а-я]?)(?:\s*-\s*(\d+[а-я]?)|(?:[.,]\s*ал\.\s*|\s+ал\.\s*|\.)(\d+[а-я]?))?\s*$/iu;

export function parseArticleSpec(spec: string): ArticleSpec {
  if (!spec || !spec.trim()) {
    throw new InvalidArticleSpecError(`empty spec: '${spec}'`);
  }
  const m = FULL_RE.exec(spec);
  if (!m) {
    throw new InvalidArticleSpecError(`could not parse: '${spec}'`);
  }
  return {
    article: m[1] as string,
    paragraph: m[3] ?? null,
    rangeEnd: m[2] ?? null,
  };
}
