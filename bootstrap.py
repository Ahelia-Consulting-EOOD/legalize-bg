"""Bootstrap Runner — orchestrates Phase 1a full corpus scrape."""

import argparse
import json
import logging
import os
import re
import subprocess
import time
from pathlib import Path

from fetcher.bg.client import LexBgClient, HttpTransport, RateLimitedSession
from fetcher.bg.coverage import make_gate_record, uncovered_legal_text
from fetcher.bg.discovery import CatalogCrawler, CATEGORY_DIRS
from fetcher.bg.text_parser import HtmlToMarkdown
from fetcher.bg.metadata import MetadataParser
from fetcher.bg.assembler import assemble_file, generate_slug
from index.catalog import CatalogIndex

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
log = logging.getLogger(__name__)


class TreeTransport:
    """Thin adapter exposing `get_tree_page(url)` over a RateLimitedSession.

    The discovery module calls `transport.get_tree_page(url)`; we wrap the
    shared session so rate limit, retries, logging, and CF detection apply
    uniformly to tree crawls and document fetches.
    """

    def __init__(self, session: RateLimitedSession | None = None):
        self._session = session or RateLimitedSession()

    def get_tree_page(self, url: str) -> bytes:
        return self._session.get_bytes(url)

    def close(self):
        self._session.close()


def bootstrap(
    output_dir: Path,
    db_path: str = "catalog.db",
    dry_run: bool = False,
    branch: str | None = None,
    push_every: int = 0,
    remote: str = "origin",
):
    """Run the full bootstrap pipeline.

    Args:
        branch: If set, create + switch to this branch before the loop.
        push_every: If >0, `git push` after every N successful commits
            plus one final push at the end. Requires `branch` or a
            pre-existing upstream on the current branch.
        remote: Remote name to push to (default "origin").

    Raises:
        ValueError: when push_every > 0 without --branch. Without an
            explicit feature branch, an interrupted run would start
            pushing half-bootstrapped commits to the current branch
            (typically main), violating delivery-contract.md's
            "main history is sacred" rule.
    """
    if push_every and not branch:
        raise ValueError(
            "--push-every requires --branch to avoid pushing partial "
            "bootstrap state to the current branch (likely main). "
            "Use --branch bootstrap/phase-1a (or similar) to land commits "
            "on a feature branch first."
        )

    session = RateLimitedSession()
    client = LexBgClient(transport=HttpTransport(session=session))
    tree_transport = TreeTransport(session=session)
    crawler = CatalogCrawler()
    parser = HtmlToMarkdown()
    metadata_parser = MetadataParser()
    db = CatalogIndex(db_path)
    db.initialize()

    for dir_name in CATEGORY_DIRS.values():
        (output_dir / dir_name).mkdir(parents=True, exist_ok=True)

    if branch and not dry_run:
        log.info("creating branch %s", branch)
        _git_checkout_branch(branch, cwd=output_dir)
    push_branch = branch or (_git_current_branch(output_dir) if push_every else None)

    log.info("Crawling lex.bg catalog...")
    catalog = crawler.crawl_all(tree_transport)
    log.info(
        "Found %d acts across %d categories",
        len(catalog), len(CatalogCrawler.CATEGORIES),
    )

    if dry_run:
        log.info("Dry run — stopping after catalog crawl")
        for cat, count in _count_by_cat(catalog).items():
            log.info("  %s: %d", cat, count)
        client.close()
        db.close()
        return catalog

    _threshold_raw = os.environ.get("LEGALIZE_COVERAGE_THRESHOLD", "64")
    try:
        threshold = int(_threshold_raw)
    except (ValueError, TypeError):
        log.warning(
            "Invalid LEGALIZE_COVERAGE_THRESHOLD value %r — falling back to default 64",
            _threshold_raw,
        )
        threshold = 64
    gate_failures: list[dict] = []
    errors = []
    used_slugs: set[str] = set()
    for i, entry in enumerate(catalog, 1):
        doc_id = entry["doc_id"]
        name = entry["name"]
        tree_category = entry["category"]
        corpus_dir = CATEGORY_DIRS.get(tree_category, tree_category)

        try:
            log.info("[%d/%d] %s (doc_id=%d)", i, len(catalog), name, doc_id)

            soup = client.fetch_soup(doc_id)

            body = parser.convert(soup)
            gate = uncovered_legal_text(soup, body)
            meta = metadata_parser.parse(soup, doc_id=doc_id, category=corpus_dir)

            if gate["uncovered_chars"] > threshold:
                slug_hint = generate_slug(meta.get("titulo", "")) or str(doc_id)
                title = meta.get("titulo") or name
                gate_failures.append(make_gate_record(doc_id, slug_hint, title, gate))
                log.warning(
                    "coverage gate FAIL: %s (doc_id=%d) uncovered_chars=%d — skipping write",
                    meta.get("titulo") or name, doc_id, gate["uncovered_chars"],
                )
                continue

            missing_mandatory = [
                k for k in ("fecha_publicacion", "ultima_actualizacion")
                if not meta.get(k)
            ]
            if missing_mandatory:
                log.warning(
                    "mandatory field(s) null for %s (doc_id=%d): %s",
                    meta.get("titulo") or "<no-title>", doc_id, missing_mandatory,
                )

            base_slug = generate_slug(meta["titulo"]) or str(doc_id)
            slug = _unique_slug(base_slug, used_slugs)
            filepath = output_dir / corpus_dir / f"{slug}.md"
            content = assemble_file(meta, body)

            filepath.write_text(content, encoding="utf-8")

            _git_commit(
                filepath=filepath,
                title=meta["titulo"],
                doc_id=doc_id,
                pub_date=meta.get("fecha_publicacion", ""),
                cwd=output_dir,
            )

            commit_hash = _git_head(output_dir)
            db.insert_law(
                law_id=slug,
                doc_id=doc_id,
                title=meta["titulo"],
                category=corpus_dir,
                commit_hash=commit_hash,
                effective_date=meta.get("effective_date") or meta.get("fecha_publicacion", ""),
            )

        except Exception as e:
            log.error("FAILED: %s (doc_id=%d): %s", name, doc_id, e)
            errors.append({"doc_id": doc_id, "name": name, "error": str(e)})
            continue

        if push_every and push_branch and i % push_every == 0:
            log.info("pushing to %s/%s (commits so far: %d)", remote, push_branch, i)
            _git_push(output_dir, branch=push_branch, remote=remote)

    gate_report_path = output_dir / "gate-report.json"
    gate_report_path.write_text(
        json.dumps(gate_failures, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    log.info(
        "coverage gate: %d/%d acts failed",
        len(gate_failures), len(catalog),
    )

    log.info(
        "Bootstrap complete: %d succeeded, %d failed",
        len(catalog) - len(errors) - len(gate_failures), len(errors),
    )
    if errors:
        log.warning("Failed acts:")
        for err in errors:
            log.warning("  %s: %s", err["name"], err["error"])

    if push_branch and (push_every or branch):
        log.info("final push to %s/%s", remote, push_branch)
        _git_push(output_dir, branch=push_branch, remote=remote)

    client.close()
    db.close()
    return catalog


_ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_GIT_EPOCH_FLOOR = "1970-01-01"


def _format_author_date(pub_date: str | None) -> str | None:
    """Convert a YYYY-MM-DD publication date into a git-accepted timestamp.

    Git rejects bare YYYY-MM-DD in GIT_AUTHOR_DATE with
    'fatal: invalid date format' — it needs a full ISO 8601 with time and
    timezone (or RFC 2822, or a Unix timestamp). We emit
    'YYYY-MM-DDT00:00:00+00:00' — midnight UTC on the publication date —
    which git parses as a proper timestamp.

    Pre-1970 dates are clamped to 1970-01-01: this git build (and many
    others) refuses negative Unix timestamps in every input format. Data
    fidelity is preserved via the `Source-Date` line in the commit body,
    which still carries the true publication date. `git log --before`
    queries continue to order pre-1970 acts before all modern ones.

    Returns None for empty / None / malformed input so callers can skip
    setting the env var rather than passing garbage.
    """
    if not pub_date or not isinstance(pub_date, str):
        return None
    if not _ISO_DATE_RE.match(pub_date):
        return None
    # Clamp to epoch floor — lexicographic comparison works for YYYY-MM-DD.
    if pub_date < _GIT_EPOCH_FLOOR:
        pub_date = _GIT_EPOCH_FLOOR
    return f"{pub_date}T00:00:00+00:00"


def _git_commit(filepath: Path, title: str, doc_id: int,
                pub_date: str | None, cwd: Path):
    """Create a [bootstrap] commit for a single act.

    Sets both GIT_AUTHOR_DATE and GIT_COMMITTER_DATE to the publication
    date so `git log --before=DATE` reconstructs legislative history
    chronologically (see delivery-contract §Commit Granularity).
    """
    subprocess.run(
        ["git", "add", str(filepath.relative_to(cwd))],
        cwd=cwd, check=True, capture_output=True,
    )
    source_date_line = pub_date if pub_date else "unknown"
    msg = (
        f"[bootstrap] {title}\n\n"
        f"Source-Id: lexbg-{doc_id}\n"
        f"Source-Date: {source_date_line}\n"
        f"Norm-Id: {doc_id}\n"
    )
    env = os.environ.copy()
    author_date = _format_author_date(pub_date)
    if author_date:
        env["GIT_AUTHOR_DATE"] = author_date
        env["GIT_COMMITTER_DATE"] = author_date
    subprocess.run(
        ["git", "commit", "-m", msg],
        cwd=cwd, check=True, capture_output=True, env=env,
    )


def _git_head(cwd: Path) -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=cwd, check=True, capture_output=True, text=True,
    )
    return result.stdout.strip()


def _git_current_branch(cwd: Path) -> str:
    result = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        cwd=cwd, check=True, capture_output=True, text=True,
    )
    return result.stdout.strip()


def _git_checkout_branch(branch: str, cwd: Path) -> None:
    """Create and switch to `branch` (fails if it already exists)."""
    subprocess.run(
        ["git", "checkout", "-b", branch],
        cwd=cwd, check=True, capture_output=True,
    )


def _git_push(
    cwd: Path,
    branch: str,
    remote: str = "origin",
    retries: int = 3,
    sleep=time.sleep,
) -> None:
    """Push `branch` to `remote`. Retries with exponential backoff on failure.

    Intermediate `git push` failures during a long bootstrap are usually
    transient (network blip, GitHub-side timeout). Retry 3x with 2/4/8s
    backoff, then raise so the operator sees the error instead of silently
    proceeding with uncommitted-to-remote state.
    """
    cmd = ["git", "push", "--set-upstream", remote, branch]
    last_exc = None
    for attempt in range(retries + 1):
        try:
            subprocess.run(cmd, cwd=cwd, check=True, capture_output=True)
            return
        except subprocess.CalledProcessError as e:
            last_exc = e
            if attempt < retries:
                backoff = 2.0 * (2 ** attempt)
                log.warning(
                    "git push failed (attempt %d/%d); retrying in %.1fs: %s",
                    attempt + 1, retries, backoff,
                    (e.stderr or b"").decode(errors="replace").strip(),
                )
                sleep(backoff)
    raise last_exc


def _count_by_cat(catalog: list[dict]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for entry in catalog:
        cat = entry["category"]
        counts[cat] = counts.get(cat, 0) + 1
    return counts


def _unique_slug(slug: str, used: set[str]) -> str:
    """Return `slug` if unused, else append a counter (-2, -3, ...) until unique.

    Bulgarian legislation has many similarly-named наредби ("Наредба № 7"
    appears repeatedly across ministries). Without dedup, the second act
    would silently overwrite the first's Markdown file and the SQLite
    insert would fail on the law_id primary key.
    """
    if slug not in used:
        used.add(slug)
        return slug
    n = 2
    while f"{slug}-{n}" in used:
        n += 1
    candidate = f"{slug}-{n}"
    used.add(candidate)
    return candidate


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Bootstrap Bulgarian legislation corpus")
    ap.add_argument("--output", type=Path, default=Path("."), help="Output directory")
    ap.add_argument("--db", default="catalog.db", help="SQLite database path")
    ap.add_argument("--dry-run", action="store_true", help="Only crawl catalog, don't fetch acts")
    ap.add_argument("--branch", default=None,
                    help="Create + switch to this branch before running (e.g. bootstrap/phase-1a)")
    ap.add_argument("--push-every", type=int, default=0,
                    help="Push to remote after every N commits (0 = no intermediate pushes)")
    ap.add_argument("--remote", default="origin", help="Remote to push to")
    args = ap.parse_args()
    bootstrap(
        args.output, args.db, args.dry_run,
        branch=args.branch, push_every=args.push_every, remote=args.remote,
    )
