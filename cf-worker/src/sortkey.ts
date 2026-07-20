/** Port of mcp_server/queries.py `_legal_article_sort_key`. */

export type SortKey = readonly [number, string];

const KEY_RE = /^(\d+)([а-я]*)$/u;

export function legalArticleSortKey(article: string): SortKey {
  const m = KEY_RE.exec(article);
  if (!m) return [10 ** 9, article]; // unparseable trails
  return [parseInt(m[1] as string, 10), m[2] as string];
}

export function compareSortKeys(a: SortKey, b: SortKey): number {
  if (a[0] !== b[0]) return a[0] - b[0];
  // Python tuple comparison falls back to string comparison on the
  // suffix; JS '<' on strings compares by UTF-16 code unit, which for
  // Cyrillic matches Python's code-point comparison.
  return a[1] < b[1] ? -1 : a[1] > b[1] ? 1 : 0;
}
