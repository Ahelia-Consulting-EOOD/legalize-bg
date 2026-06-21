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


_CONTENT_TABLES = ("laws_fts", "provisions", "law_versions", "amendments", "laws")


def _drop_content_rows(conn: sqlite3.Connection) -> None:
    """Idempotency: remove all rows from content tables before
    re-inserting. Schema (managed by migrations.py) stays intact.
    Order matters for FK-style constraints: dependent tables first."""
    for table in _CONTENT_TABLES:
        conn.execute(f"DELETE FROM {table}")
    conn.commit()


def _delete_act_rows(conn: sqlite3.Connection, law_id: str) -> None:
    """Remove a single act's rows from every content table (FR-014
    incremental rebuild); dependent tables first. `laws_fts` is a regular
    FTS5 table, so a `DELETE ... WHERE law_id = ?` on its UNINDEXED column
    is valid. NOTE: `amendments` keys the act via `target_law`, not
    `law_id` — handled separately."""
    for table in ("laws_fts", "provisions", "law_versions", "laws"):
        conn.execute(f"DELETE FROM {table} WHERE law_id = ?", (law_id,))
    conn.execute("DELETE FROM amendments WHERE target_law = ?", (law_id,))


def _reindex_act(conn: sqlite3.Connection, cat: str, path: Path,
                 head: str, today_iso: str) -> str:
    """Parse one act's Markdown and INSERT its rows into every content
    table at commit `head`. The single source of truth for per-act
    indexing — used by both the full build and the FR-014 incremental
    path. Assumes the act's existing rows (if any) were already removed by
    the caller. Returns the indexed `law_id`.

    Raises ValueError on missing frontmatter / missing-or-zero
    identificador (a data bug the fetcher should never produce)."""
    meta, body = _parse_md(path)
    law_id = path.stem
    # Missing identificador is a data bug (the fetcher always populates it);
    # collapsing to 0 would cause silent dedup.
    raw_id = meta.get("identificador")
    if raw_id in (None, "", 0, "0"):
        raise ValueError(
            f"{path}: missing or zero identificador; the fetcher "
            "should always populate this. Refusing to index."
        )
    doc_id = int(raw_id)
    title = meta.get("titulo") or f"<doc_id={doc_id}>"
    # §7.2 detection: when both effective_date and fecha_publicacion are
    # absent, fall back to today_iso so law_versions.valid_from is non-NULL
    # — but set date_uncertain=1 so callers see a DATE_UNCERTAIN warning
    # regardless of when the query runs.
    pub_date = meta.get("effective_date") or meta.get("fecha_publicacion")
    date_uncertain = 1 if pub_date in (None, "") else 0
    effective = pub_date or today_iso
    if hasattr(effective, "isoformat"):  # PyYAML may parse dates as date objs
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
    # Phase 2 (FR-001): populate `amendments` from amendment_history.
    # Entry 0 is the original promulgation ('enacted'); the rest are
    # 'amendment' (generic — specific ЗИД ops await Phase 4).
    for i, entry in enumerate(meta.get("amendment_history") or []):
        dv_issue = entry.get("dv")
        dv_date = entry.get("date")
        if hasattr(dv_date, "isoformat"):
            dv_date = dv_date.isoformat()
        operation = "enacted" if i == 0 else "amendment"
        conn.execute(
            """INSERT INTO amendments
                   (source_act, target_law, operation,
                    affected_articles, dv_issue, dv_date)
               VALUES (?, ?, ?, NULL, ?, ?)""",
            (f"ДВ {dv_issue}" if dv_issue else "unknown",
             law_id, operation, dv_issue, dv_date),
        )
    for prov in parse_provisions(body, law_id=law_id):
        conn.execute(
            """INSERT INTO provisions
               (law_id, article, paragraph, valid_from, text, text_hash)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (prov.law_id, prov.article, prov.paragraph,
             effective, prov.text, prov.text_hash),
        )
    insert_fts_row(conn, law_id=law_id, title=title, body=body, category=cat)
    return law_id


def _act_count(conn: sqlite3.Connection) -> int:
    return conn.execute("SELECT COUNT(*) FROM laws").fetchone()[0]


def _indexed_commit(conn: sqlite3.Connection) -> str | None:
    """Return the single commit the catalog was last indexed at, or None
    when the catalog is empty OR holds more than one distinct
    `current_commit` (an inconsistent state → force a full rebuild)."""
    try:
        rows = conn.execute(
            "SELECT DISTINCT current_commit FROM laws").fetchall()
    except sqlite3.OperationalError:
        return None  # table missing (pre-migrate) → full build
    if len(rows) == 1 and rows[0][0]:
        return rows[0][0]
    return None


class _CannotIncrement(Exception):
    """Raised when an incremental rebuild can't proceed (e.g. the base
    commit isn't in the repo's history) → caller falls back to full."""


def _path_to_act(corpus_root: Path, rel_path: str,
                 cat_set: set[str]) -> tuple[str, str, Path] | None:
    """Map a git path like `laws/zakon-x.md` to (category, law_id, full
    path) when it is a `.md` directly under a known category dir; else
    None (ignores docs/, nested paths, non-md)."""
    p = Path(rel_path)
    if p.suffix != ".md" or len(p.parts) != 2:
        return None
    cat = p.parts[0]
    if cat not in cat_set:
        return None
    return cat, p.stem, corpus_root / rel_path


def _changed_acts(corpus_root: Path, base: str, head: str):
    """Diff `base..head` (restricted to category dirs) into
    (upserts, deletes): upserts = [(cat, path)] to re-index (Added/
    Modified/renamed-new), deletes = [law_id] removed (Deleted/renamed-old).
    Raises _CannotIncrement if git can't diff the two commits."""
    cat_set = set(CATEGORY_DIRS.values())
    try:
        out = subprocess.run(
            ["git", "diff", "--name-status", base, head, "--", *sorted(cat_set)],
            cwd=corpus_root, check=True, capture_output=True, text=True,
        ).stdout
    except subprocess.CalledProcessError as e:
        raise _CannotIncrement(
            f"git diff {base[:8]}..{head[:8]} failed: "
            f"{(e.stderr or '').strip()[:200]}")
    upserts: list[tuple[str, Path]] = []
    deletes: list[str] = []
    for line in out.splitlines():
        parts = line.split("\t")
        status = parts[0]
        if status.startswith(("R", "C")) and len(parts) >= 3:
            # rename/copy: old path → delete, new path → upsert
            old = _path_to_act(corpus_root, parts[1], cat_set)
            new = _path_to_act(corpus_root, parts[2], cat_set)
            if old and status.startswith("R"):
                deletes.append(old[1])
            if new:
                upserts.append((new[0], new[2]))
            continue
        if len(parts) < 2:
            continue
        info = _path_to_act(corpus_root, parts[1], cat_set)
        if not info:
            continue
        cat, law_id, full = info
        if status.startswith("D"):
            deletes.append(law_id)
        else:  # A, M, T(ypechange)
            upserts.append((cat, full))
    return upserts, deletes


def _incremental_build(conn: sqlite3.Connection, corpus_root: Path,
                       base: str, head: str, today_iso: str) -> int:
    """Re-index only the acts changed between the indexed commit `base`
    and `head`; leave unchanged acts' content rows intact and just bump
    their commit pointers to `head` (their files are byte-identical at
    head). Atomic: a single commit at the end, so a parse error mid-way
    rolls back the whole attempt on connection close."""
    if base == head:
        log.info("incremental: index already at HEAD %s; no-op", head[:8])
        return _act_count(conn)

    upserts, deletes = _changed_acts(corpus_root, base, head)
    log.info("incremental: base=%s head=%s upserts=%d deletes=%d",
             base[:8], head[:8], len(upserts), len(deletes))

    for law_id in deletes:
        _delete_act_rows(conn, law_id)
    for cat, path in upserts:
        _delete_act_rows(conn, path.stem)  # remove old rows if Modified
        _reindex_act(conn, cat, path, head, today_iso)

    # Unchanged acts: re-point to head so the staleness check passes and
    # the working-tree fast path stays valid (identical file at head).
    # Changed acts already carry head from _reindex_act. NOTE: the
    # `commit_hash = base` filter assumes one law_versions row per act
    # (current state); revisit when FR-020 lands multi-version rows.
    conn.execute("UPDATE laws SET current_commit = ?", (head,))
    conn.execute(
        "UPDATE law_versions SET commit_hash = ? WHERE commit_hash = ?",
        (head, base))
    conn.commit()
    return _act_count(conn)


def build(corpus_root: Path, db_path: str = "catalog.db",
          today_iso: str | None = None, incremental: bool = False) -> int:
    """Build (or rebuild) the SQLite catalog from the corpus at HEAD.

    `incremental=True` (FR-014) re-indexes only acts changed since the
    catalog's last indexed commit, falling back to a full rebuild when the
    catalog is empty / inconsistent / its base commit isn't in history.
    Default `incremental=False` keeps the full DELETE-then-INSERT rebuild.

    Returns the number of acts indexed (total acts in the catalog).
    """
    today_iso = today_iso or date.today().isoformat()
    corpus_root = Path(corpus_root)
    conn = sqlite3.connect(db_path)
    try:
        migrate(conn)
        head = _git_head(corpus_root)

        if incremental:
            base = _indexed_commit(conn)
            if base:
                try:
                    n = _incremental_build(conn, corpus_root, base, head,
                                           today_iso)
                    log.info("incremental rebuild: catalog now %d acts", n)
                    return n
                except _CannotIncrement as e:
                    log.warning("incremental not possible (%s); "
                                "falling back to full rebuild", e)
            else:
                log.info("no consistent indexed commit; full rebuild")

        _drop_content_rows(conn)
        log.info("indexing corpus at %s commit=%s", corpus_root, head[:8])
        count = 0
        for cat, path in _iter_corpus_files(corpus_root):
            _reindex_act(conn, cat, path, head, today_iso)
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
    ap.add_argument("--incremental", action="store_true",
                    help="Re-index only acts changed since the catalog's last "
                         "indexed commit (FR-014); falls back to a full "
                         "rebuild if the catalog is empty/inconsistent.")
    args = ap.parse_args()
    n = build(args.corpus, args.db, incremental=args.incremental)
    print(f"indexed {n} acts into {args.db}"
          f"{' (incremental)' if args.incremental else ''}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
