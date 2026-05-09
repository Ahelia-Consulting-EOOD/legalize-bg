"""FTS5 helpers and Bulgarian-aware text normalizer.

bg_normalize() is symmetric: called at both index time AND query time so
morphological variants match. Bulgarian definite-article suffixes are
stripped from word endings; lowercasing and whitespace collapse round it
out. No external NLP libs; pure Python.

Per D-022. Symmetry is mandatory — asymmetry silently breaks search.
"""

import re
import sqlite3


# Bulgarian definite-article suffixes — last-character stripping only.
#
# Strip just the trailing definite article: feminine "та", neuter "то",
# masculine "ът"/"ят" (after consonant / after specific vowels), plural
# "те". Critically, NOT stripping the longer "ите"/"ия"/"ето"/"а"
# variants — those would mangle valid base forms or break plural
# symmetry:
#   "ите" stripped: "обществените" → "обществен", but "обществени"
#     (plural indefinite — what users actually type) → "обществени".
#     The two forms diverge → search silently misses indefinite hits.
#     Stripping just "те": both reduce to "обществени". Symmetric.
#   "ето" stripped: "управлението" → "управлени" (mangled).
#   "а" stripped: "държава" → "държав" (feminine base form mangled).
#   "ия" stripped: "решения" → "реше" (plural base form mangled).
#
# All entries are 2 chars, so order doesn't change matching, but we list
# them grouped by gender/number for readability.
_BG_DEFINITE_SUFFIXES: tuple[str, ...] = (
    "ът", "ят",  # masculine
    "та",        # feminine
    "то",        # neuter
    "те",        # plural
)

# Minimum length of the stem AFTER stripping a suffix. 4 chars protects
# against catastrophic over-stripping of short words. Known asymmetry
# this introduces: adjective long-form definite (`новият` 6→`нови` 4)
# does not match indefinite (`нов` 3 chars, below threshold, returned
# unchanged). Acceptable for Phase 1b.1 (rare in legal subject position);
# tracked as FR-013 in `docs/frs/INDEX.md` for the 1b.3 stemmer milestone.
_MIN_STEM_LEN = 4
_WS_RE = re.compile(r"\s+")


def _strip_definite_article(token: str) -> str:
    if len(token) <= _MIN_STEM_LEN:
        return token
    for suffix in _BG_DEFINITE_SUFFIXES:
        if token.endswith(suffix) and len(token) - len(suffix) >= _MIN_STEM_LEN:
            return token[: -len(suffix)]
    return token


def bg_normalize(text: str | None) -> str:
    """Normalize text for symmetric FTS5 indexing/querying.

    - lowercase (Cyrillic + Latin)
    - collapse whitespace to single spaces
    - strip Bulgarian definite-article suffixes from word endings (>4 chars)
    - preserve digits and punctuation context (split on whitespace only)
    """
    if not text:
        return ""
    text = text.lower()
    text = _WS_RE.sub(" ", text).strip()
    if not text:
        return ""
    tokens = text.split(" ")
    return " ".join(_strip_definite_article(t) for t in tokens)


def create_laws_fts_table(conn: sqlite3.Connection) -> None:
    """Idempotent helper — migrations.py already creates this, but build.py
    uses this when working on a non-migrated test db."""
    conn.executescript(
        """
        CREATE VIRTUAL TABLE IF NOT EXISTS laws_fts USING fts5(
            law_id UNINDEXED,
            title,
            body,
            category UNINDEXED,
            tokenize='unicode61 remove_diacritics 2'
        );
        """
    )


def insert_fts_row(conn: sqlite3.Connection, law_id: str, title: str,
                   body: str, category: str) -> None:
    conn.execute(
        "INSERT INTO laws_fts (law_id, title, body, category) VALUES (?, ?, ?, ?)",
        (law_id, bg_normalize(title), bg_normalize(body), category),
    )


def search_fts(conn: sqlite3.Connection, query: str,
               category: str | None = None, limit: int = 20) -> list[sqlite3.Row]:
    """Run an FTS5 MATCH query and return ranked rows joined with laws."""
    normalized = bg_normalize(query)
    if not normalized:
        return []
    sql = """
        SELECT laws_fts.law_id          AS law_id,
               laws.doc_id              AS doc_id,
               laws.title               AS title,
               laws.category            AS category,
               snippet(laws_fts, 2, '<b>', '</b>', '...', 12) AS snippet,
               bm25(laws_fts)           AS score
          FROM laws_fts
          JOIN laws USING(law_id)
         WHERE laws_fts MATCH ?
    """
    params: list = [normalized]
    if category:
        sql += " AND laws.category = ?"
        params.append(category)
    sql += " ORDER BY bm25(laws_fts) LIMIT ?"
    params.append(limit)
    return conn.execute(sql, params).fetchall()
