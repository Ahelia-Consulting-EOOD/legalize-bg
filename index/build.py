"""Index builder — populates the SQLite catalog from a git-tracked corpus.

Idempotent: drops & re-creates content rows before insertion (the schema
itself is migrated forward-only via index/migrations.py).

Per design doc §6.1 / §7.1, this is invoked manually by operators after
Phase 1a bootstrap, and automatically by Phase 3 (DV monitor) and Phase 4
(consolidation engine) at the end of their pipelines.

CLI: `python -m index.build [--corpus PATH] [--db PATH]`
"""

from __future__ import annotations

import argparse
import logging
import sqlite3
import subprocess
import sys
from datetime import date
from pathlib import Path

import yaml

from fetcher.bg.discovery import CATEGORY_DIRS
from index.fts import bg_normalize, insert_fts_row
from index.migrations import migrate
from index.provisions import parse as parse_provisions

log = logging.getLogger(__name__)


def _git_head(cwd: Path) -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=cwd, check=True, capture_output=True, text=True,
    ).stdout.strip()


def _iter_corpus_files(corpus_root: Path):
    """Yield (category_dir, path) for every .md file under known
    category directories. Iteration order is deterministic (alphabetical
    within each category) so the laws_fts virtual table receives
    inserts in stable order — useful for diffing builds."""
    seen_dirs = set()
    for cat in CATEGORY_DIRS.values():
        if cat in seen_dirs:
            continue
        seen_dirs.add(cat)
        d = corpus_root / cat
        if not d.is_dir():
            continue
        for f in sorted(d.iterdir()):
            if f.suffix == ".md":
                yield cat, f


def _parse_md(path: Path) -> tuple[dict, str]:
    """Split a Markdown file with YAML frontmatter into (frontmatter, body).

    Frontmatter is delimited by '---' lines; body is everything after the
    closing '---'. Handles the standard Phase-1a assembler output.
    """
    raw = path.read_text(encoding="utf-8")
    if not raw.startswith("---\n"):
        raise ValueError(f"missing frontmatter in {path}")
    # Strip leading '---\n', then split on the closing '\n---\n'.
    after_open = raw[4:]
    parts = after_open.split("\n---\n", 1)
    fm_block = parts[0]
    body = parts[1] if len(parts) > 1 else ""
    return yaml.safe_load(fm_block), body


def _drop_content_rows(conn: sqlite3.Connection) -> None:
    """Idempotency: remove all rows from content tables before
    re-inserting. Schema (managed by migrations.py) stays intact.
    Order matters for FK-style constraints: dependent tables first."""
    for table in ("laws_fts", "provisions", "law_versions", "amendments", "laws"):
        conn.execute(f"DELETE FROM {table}")
    conn.commit()


def build(corpus_root: Path, db_path: str = "catalog.db",
          today_iso: str | None = None) -> int:
    """Build (or rebuild) the SQLite catalog from the corpus at HEAD.

    Returns the number of acts indexed.
    """
    today_iso = today_iso or date.today().isoformat()
    corpus_root = Path(corpus_root)
    conn = sqlite3.connect(db_path)
    try:
        migrate(conn)
        _drop_content_rows(conn)

        head = _git_head(corpus_root)
        log.info("indexing corpus at %s commit=%s", corpus_root, head[:8])

        count = 0
        for cat, path in _iter_corpus_files(corpus_root):
            meta, body = _parse_md(path)
            law_id = path.stem
            # Missing identificador is a data bug (the fetcher always
            # populates it); collapsing to 0 would cause silent dedup.
            raw_id = meta.get("identificador")
            if raw_id in (None, "", 0, "0"):
                raise ValueError(
                    f"{path}: missing or zero identificador; the fetcher "
                    "should always populate this. Refusing to index."
                )
            doc_id = int(raw_id)
            title = meta.get("titulo") or f"<doc_id={doc_id}>"
            # §7.2 detection: when both effective_date and fecha_publicacion
            # are absent, we fall back to today_iso so law_versions.valid_from
            # is non-NULL — but we set date_uncertain=1 so callers see a
            # DATE_UNCERTAIN warning regardless of when the query runs
            # (the prior detection compared valid_from to today() at query
            # time, which silently stopped firing on day 2).
            pub_date = meta.get("effective_date") or meta.get("fecha_publicacion")
            date_uncertain = 1 if pub_date in (None, "") else 0
            effective = pub_date or today_iso
            # Coerce dates to ISO strings (PyYAML may parse them as
            # datetime.date objects).
            if hasattr(effective, "isoformat"):
                effective = effective.isoformat()

            conn.execute(
                """INSERT INTO laws (law_id, doc_id, title, category,
                                     status, current_commit)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (law_id, doc_id, title, cat,
                 meta.get("estado") or "vigente", head),
            )
            conn.execute(
                """INSERT INTO law_versions
                       (law_id, valid_from, commit_hash, date_uncertain)
                   VALUES (?, ?, ?, ?)""",
                (law_id, effective, head, date_uncertain),
            )
            for prov in parse_provisions(body, law_id=law_id):
                conn.execute(
                    """INSERT INTO provisions
                       (law_id, article, paragraph, valid_from, text, text_hash)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (prov.law_id, prov.article, prov.paragraph,
                     effective, prov.text, prov.text_hash),
                )
            insert_fts_row(conn, law_id=law_id, title=title,
                           body=body, category=cat)
            count += 1

        conn.commit()
        log.info("indexed %d acts", count)
        return count
    finally:
        conn.close()


def main() -> int:
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(message)s")
    ap = argparse.ArgumentParser(description="Build SQLite catalog from corpus.")
    ap.add_argument("--corpus", type=Path, default=Path("."))
    ap.add_argument("--db", default="catalog.db")
    args = ap.parse_args()
    n = build(args.corpus, args.db)
    print(f"indexed {n} acts into {args.db}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
