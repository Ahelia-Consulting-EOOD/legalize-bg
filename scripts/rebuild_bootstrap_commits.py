"""Rebuild per-act commits on bootstrap/phase-1a from existing Markdown files.

Task 11's first run hit a git date-format bug: bare YYYY-MM-DD in
GIT_AUTHOR_DATE is rejected, which silently bundled 3,573 files into 121
commits. The files on disk are correct — we just need to redo the commits
with the fix in bootstrap._git_commit.

This script does NOT re-fetch lex.bg. It reads YAML frontmatter from each
committed .md file, resets the branch to main, and replays one commit per
file with the correct backdated GIT_AUTHOR_DATE. SQLite catalog is rebuilt
from scratch.

Usage:
    python scripts/rebuild_bootstrap_commits.py \\
        --branch bootstrap/phase-1a \\
        --db catalog.db

Safety:
    - Verifies the current branch matches --branch before resetting.
    - The tag `bootstrap-phase-1a-broken-backup` points at the pre-rebuild
      commit in case recovery is needed (git reset --hard <tag>).
    - Reset is `git reset BASE` (mixed) — keeps working-tree files; they
      show up as untracked and are re-committed one by one.
"""

import argparse
import logging
import subprocess
import sys
from datetime import date
from pathlib import Path

import yaml

from bootstrap import _git_commit, _git_head
from fetcher.bg.discovery import CATEGORY_DIRS
from index.catalog import CatalogIndex

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
log = logging.getLogger(__name__)


def _current_branch(cwd: Path) -> str:
    return subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        cwd=cwd, check=True, capture_output=True, text=True,
    ).stdout.strip()


def _parse_frontmatter(path: Path) -> dict:
    content = path.read_text(encoding="utf-8")
    if not content.startswith("---\n"):
        raise ValueError(f"no frontmatter in {path}")
    # Split on the closing --- delimiter
    parts = content.split("\n---\n", 1)
    if len(parts) != 2:
        raise ValueError(f"malformed frontmatter in {path}")
    yaml_block = parts[0][4:]  # strip leading '---\n'
    return yaml.safe_load(yaml_block)


def rebuild(output_dir: Path, db_path: str, branch: str, base_ref: str):
    current = _current_branch(output_dir)
    if current != branch:
        log.error("current branch is %s; expected %s — checkout %s first",
                  current, branch, branch)
        sys.exit(2)

    # Collect files BEFORE reset so we can iterate in a deterministic order
    files: list[tuple[str, Path]] = []
    for corpus_dir in CATEGORY_DIRS.values():
        d = output_dir / corpus_dir
        if not d.is_dir():
            continue
        for f in sorted(d.iterdir()):
            if f.suffix == ".md":
                files.append((corpus_dir, f))

    log.info("found %d Markdown files in corpus", len(files))
    if len(files) == 0:
        log.error("no files found — nothing to rebuild")
        sys.exit(1)

    # Reset branch ref to base_ref (mixed) — working tree kept, index cleared
    log.info("resetting %s to %s (files become untracked)", branch, base_ref)
    subprocess.run(
        ["git", "reset", base_ref, "--"],
        cwd=output_dir, check=True, capture_output=True,
    )

    # Fresh SQLite catalog
    db_file = Path(db_path)
    if db_file.exists():
        log.info("removing existing %s for fresh rebuild", db_path)
        db_file.unlink()
    db = CatalogIndex(db_path)
    db.initialize()

    errors: list[dict] = []
    today_iso = date.today().isoformat()

    for i, (corpus_dir, f) in enumerate(files, 1):
        try:
            meta = _parse_frontmatter(f)
            title = meta.get("titulo") or ""
            doc_id = int(meta.get("identificador"))
            pub_date = meta.get("fecha_publicacion") or None

            if i == 1 or i % 200 == 0:
                log.info("[%d/%d] %s", i, len(files), f.name)

            _git_commit(filepath=f, title=title, doc_id=doc_id,
                        pub_date=pub_date, cwd=output_dir)

            commit_hash = _git_head(output_dir)
            slug = f.stem
            effective = (
                meta.get("effective_date")
                or meta.get("fecha_publicacion")
                or today_iso  # last-resort fallback for NOT NULL law_versions.valid_from
            )
            db.insert_law(
                law_id=slug, doc_id=doc_id, title=title,
                category=corpus_dir, commit_hash=commit_hash,
                effective_date=effective,
            )
        except Exception as e:
            log.error("FAILED %s: %s", f, e)
            errors.append({"file": str(f), "error": str(e)})

    log.info("rebuild complete: %d committed, %d failed",
             len(files) - len(errors), len(errors))
    if errors:
        log.warning("failures (first 10):")
        for err in errors[:10]:
            log.warning("  %s: %s", err["file"], err["error"])

    db.close()
    return len(errors)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--output", type=Path, default=Path("."))
    ap.add_argument("--db", default="catalog.db")
    ap.add_argument("--branch", default="bootstrap/phase-1a",
                    help="Branch to rebuild (must be current branch)")
    ap.add_argument("--base-ref", default="main",
                    help="Ref to reset to before rebuilding commits")
    args = ap.parse_args()
    failures = rebuild(args.output, args.db, args.branch, args.base_ref)
    sys.exit(1 if failures else 0)
