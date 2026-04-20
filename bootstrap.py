"""Bootstrap Runner — orchestrates Phase 1a full corpus scrape."""

import argparse
import logging
import os
import subprocess
from pathlib import Path

from fetcher.bg.client import LexBgClient, HttpTransport, RateLimitedSession
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


def bootstrap(output_dir: Path, db_path: str = "catalog.db", dry_run: bool = False):
    """Run the full bootstrap pipeline."""
    # Share one rate-limited session across tree and document fetches so the
    # 1 req/sec ceiling applies globally.
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
            meta = metadata_parser.parse(soup, doc_id=doc_id, category=corpus_dir)

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

    log.info(
        "Bootstrap complete: %d succeeded, %d failed",
        len(catalog) - len(errors), len(errors),
    )
    if errors:
        log.warning("Failed acts:")
        for err in errors:
            log.warning("  %s: %s", err["name"], err["error"])

    client.close()
    db.close()
    return catalog


def _git_commit(filepath: Path, title: str, doc_id: int, pub_date: str, cwd: Path):
    """Create a [bootstrap] commit for a single act."""
    subprocess.run(
        ["git", "add", str(filepath.relative_to(cwd))],
        cwd=cwd, check=True, capture_output=True,
    )
    msg = (
        f"[bootstrap] {title}\n\n"
        f"Source-Id: lexbg-{doc_id}\n"
        f"Source-Date: {pub_date}\n"
        f"Norm-Id: {doc_id}\n"
    )
    env = os.environ.copy()
    if pub_date:
        env["GIT_AUTHOR_DATE"] = pub_date
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
    args = ap.parse_args()
    bootstrap(args.output, args.db, args.dry_run)
