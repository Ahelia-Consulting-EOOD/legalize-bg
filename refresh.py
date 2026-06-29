"""Corpus Refresh Runner — wholesale re-scrape of lex.bg as a fresh snapshot.

This is the "re-photograph lex.bg" pass described in
docs/sync/HANDOFFS/2026-06-21-corpus-rescrape-refresh.md. lex.bg already
performs legal consolidation, so re-scraping yields 100%-accurate current
text. For every act on lex.bg today:

  * ADDED    (on lex.bg, not in corpus)  -> write new file, commit [nova]
  * EXISTING (in both)                   -> re-assemble; if changed, overwrite
                                            the SAME slug, commit [reforma]
                                            (amendment_history grew) or
                                            [popravka] (body changed only)
  * MISSING  (in corpus, gone from tree) -> KEEP the file (repealed acts stay);
                                            optionally flip estado, commit
                                            [otmyana]. Reported, never deleted.

It deliberately reuses the Phase-1a fetcher/assembler/commit machinery
(fetcher/bg/*, bootstrap._format_author_date) and does NOT touch any
protected surface (frontmatter schema, fetcher interfaces, commit format,
SQLite schema). The SQLite index is rebuilt afterwards via index.build.
"""

from __future__ import annotations

import json
import logging
import os
import re
import subprocess
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

import yaml

from bootstrap import TreeTransport, _format_author_date, _git_checkout_branch, _unique_slug
from fetcher.bg.assembler import assemble_file, generate_slug
from fetcher.bg.coverage import uncovered_legal_text
from fetcher.bg.client import (
    CloudflareChallenge,
    HttpTransport,
    LexBgClient,
    RateLimitedSession,
)
from fetcher.bg.discovery import (
    CATEGORIES_CONFIG,
    CATEGORY_DIRS,
    ENCODING,
    LEX_BG_TREE,
    CatalogCrawler,
)
from fetcher.bg.metadata import BG_MONTHS, MetadataParser
from fetcher.bg.text_parser import HtmlToMarkdown

log = logging.getLogger(__name__)


# --- corpus catalog (the "before", loaded from disk = source of truth) ------


@dataclass
class CorpusEntry:
    """One act as it currently exists in the committed corpus."""

    doc_id: int
    slug: str            # == path.stem == the MCP handle; NEVER regenerate it
    category: str
    path: Path
    raw_text: str        # full committed file, for the normalized change compare
    frontmatter: dict
    amendment_history: list


def _split_frontmatter(raw: str) -> tuple[dict, str]:
    """Split a Markdown file with YAML frontmatter into (frontmatter, body).

    Mirrors index.build._parse_md so the loader sees exactly what the index
    builder sees.
    """
    if not raw.startswith("---\n"):
        raise ValueError("missing frontmatter")
    parts = raw[4:].split("\n---\n", 1)
    fm = yaml.safe_load(parts[0]) or {}
    body = parts[1] if len(parts) > 1 else ""
    return fm, body


def load_corpus_catalog(corpus_root: Path | str) -> dict[int, CorpusEntry]:
    """Build {doc_id -> CorpusEntry} by scanning the corpus .md files.

    The corpus on disk is the source of truth (catalog.db is gitignored and
    derived), so we read each file's `identificador` frontmatter rather than
    trusting a possibly-stale or absent SQLite catalog. This also guarantees
    we reuse each act's existing slug (path.stem) for EXISTING acts.
    """
    corpus_root = Path(corpus_root)
    catalog: dict[int, CorpusEntry] = {}
    seen_dirs: set[str] = set()
    for cat in CATEGORY_DIRS.values():
        if cat in seen_dirs:
            continue
        seen_dirs.add(cat)
        d = corpus_root / cat
        if not d.is_dir():
            continue
        for f in sorted(d.iterdir()):
            if f.suffix != ".md":
                continue
            raw = f.read_text(encoding="utf-8")
            fm, _ = _split_frontmatter(raw)
            ident = fm.get("identificador")
            if ident in (None, "", 0, "0"):
                raise ValueError(f"{f}: missing identificador")
            doc_id = int(ident)
            catalog[doc_id] = CorpusEntry(
                doc_id=doc_id,
                slug=f.stem,
                category=cat,
                path=f,
                raw_text=raw,
                frontmatter=fm,
                amendment_history=fm.get("amendment_history") or [],
            )
    return catalog


def seed_used_slugs(catalog: dict[int, CorpusEntry]) -> set[str]:
    """Every slug already in use across the whole corpus. New (ADDED) acts are
    deduped against this so a fresh act can never collide with an existing
    handle."""
    return {e.slug for e in catalog.values()}


def mint_slug(title: str, doc_id: int, used_slugs: set[str]) -> str:
    """Mint a NEW, globally-unique slug for an ADDED act. Mutates used_slugs.

    Only ever called for genuinely-new doc_ids. EXISTING acts reuse their
    on-disk slug and must never pass through here (slug-stability rule).
    """
    base = generate_slug(title) or str(doc_id)
    return _unique_slug(base, used_slugs)


# --- catalog crawl with staleness probe -------------------------------------


@dataclass
class CrawlResult:
    catalog: list[dict]                  # [{doc_id, name, category}], deduped
    pages_used: dict[str, int]           # category -> pages actually crawled
    stale_categories: dict[str, int]     # category -> NEW acts found beyond config


def crawl_with_probe(transport, config: dict[str, int] | None = None,
                     max_extra: int = 25) -> CrawlResult:
    """Crawl every lex.bg tree category until a page beyond its configured
    count is dry, so acts on tree pages added since the corpus was scraped are
    not silently missed.

    CATEGORIES_CONFIG page counts are hardcoded and go stale as lex.bg grows.
    The hardcoded counts cannot be trusted to bound the crawl, yet new acts —
    the whole point of a refresh — are exactly what lives on the new pages.
    So we crawl all configured pages (identical first-wins dedup to
    CatalogCrawler.crawl_all), then keep probing each category one page at a
    time until a probe page yields no *new* doc_ids. Staleness is reported by
    NEW acts found beyond the configured range, not by extra pages crawled, so
    a server that clamps an out-of-range page index to the last page (a repeat
    of already-seen acts) does not produce a false stale signal.

    Does NOT modify discovery.CATEGORIES_CONFIG (a protected surface). A
    non-empty `stale_categories` is a signal for the operator to update that
    constant under IMPLEMENTATION-PREFLIGHT.
    """
    config = config or CATEGORIES_CONFIG
    catalog: list[dict] = []
    seen: set[int] = set()
    pages_used: dict[str, int] = {}
    extra_acts: dict[str, int] = {}

    for category, configured in config.items():
        cap = configured + max_extra
        extra_acts[category] = 0
        page_idx = 0
        while page_idx < cap:
            url = f"{LEX_BG_TREE}/{category}/{page_idx}"
            html = transport.get_tree_page(url).decode(ENCODING)
            entries = CatalogCrawler.parse_tree_page(html, category)
            new = [e for e in entries if e["doc_id"] not in seen]
            # Beyond the configured range, an all-seen (dry) page ends the probe.
            if page_idx >= configured and not new:
                break
            for e in new:
                seen.add(e["doc_id"])
                catalog.append(e)
                if page_idx >= configured:
                    extra_acts[category] += 1
            page_idx += 1
        pages_used[category] = page_idx

    stale = {c: n for c, n in extra_acts.items() if n > 0}
    return CrawlResult(catalog=catalog, pages_used=pages_used, stale_categories=stale)


# --- catalog partition ------------------------------------------------------


def partition(lex_ids: set[int], corpus_ids: set[int]):
    """Split doc_ids into (ADDED, EXISTING, MISSING).

    ADDED    = on lex.bg but not in our corpus (new acts to fetch).
    EXISTING = in both (candidates for re-scrape + change detection).
    MISSING  = in our corpus but gone from lex.bg's tree (repealed; kept).
    """
    return (
        lex_ids - corpus_ids,
        lex_ids & corpus_ids,
        corpus_ids - lex_ids,
    )


# --- normalization for change detection -------------------------------------

_WS_RE = re.compile(r"\s+")

# Bulgarian/typographic quote variants -> straight ASCII quotes, matching the
# design's lex.bg-oracle comparison (normalize whitespace + quotes before diff).
_QUOTE_MAP = {
    "„": '"', "“": '"', "”": '"', "«": '"', "»": '"',
    "‘": "'", "’": "'",
}


def normalize_for_compare(text: str) -> str:
    """Collapse whitespace and unify quotes so cosmetic churn doesn't read as
    a real change. Used to compare a freshly-assembled file against the
    committed one."""
    for variant, plain in _QUOTE_MAP.items():
        text = text.replace(variant, plain)
    return _WS_RE.sub(" ", text).strip()


# --- amendment-history helpers ----------------------------------------------


def history_grew(committed: list[dict], candidate: list[dict]) -> bool:
    """True if the freshly-scraped amendment_history contains a DV reference
    the committed frontmatter lacks. This is the primary [reforma] signal:
    a new DV reference is by definition an amendment event."""
    committed_dvs = {e.get("dv") for e in committed}
    return any(e.get("dv") not in committed_dvs for e in candidate)


def latest_amendment_date(history: list[dict]) -> str | None:
    """Return the latest ISO date in an amendment_history array, or None.

    ISO YYYY-MM-DD strings sort lexicographically == chronologically, so
    max() over the dated entries gives the most recent amendment.
    """
    dates = [e["date"] for e in history if e.get("date")]
    return max(dates) if dates else None


# --- typed corpus commit ----------------------------------------------------

COMMIT_TYPES = ("nova", "reforma", "popravka", "otmyana")


def _git_commit_typed(filepath: Path, commit_type: str, title: str,
                      doc_id: int, date: str | None, cwd: Path) -> None:
    """Commit one corpus change with the Legalize commit format.

    Mirrors bootstrap._git_commit but parametrized over commit type. The body
    carries the three mandatory fields (Source-Id / Source-Date / Norm-Id);
    GIT_AUTHOR_DATE and GIT_COMMITTER_DATE are set to the legislative date so
    `git log --before` reconstructs history chronologically. Source-Id stays
    lexbg-{doc_id} because this coarse pass re-pulls from lex.bg rather than a
    specific DV issue.
    """
    if commit_type not in COMMIT_TYPES:
        raise ValueError(f"unknown commit type: {commit_type}")
    subprocess.run(
        ["git", "add", str(filepath.relative_to(cwd))],
        cwd=cwd, check=True, capture_output=True,
    )
    # Resume idempotency: if the file is byte-identical to HEAD nothing is
    # staged; skip the commit so re-processing an already-committed act on
    # resume is a no-op rather than a `git commit` "nothing to commit" error.
    if subprocess.run(["git", "diff", "--cached", "--quiet"],
                      cwd=cwd, capture_output=True).returncode == 0:
        return
    msg = (
        f"[{commit_type}] {title}\n\n"
        f"Source-Id: lexbg-{doc_id}\n"
        f"Source-Date: {date if date else 'unknown'}\n"
        f"Norm-Id: {doc_id}\n"
    )
    env = os.environ.copy()
    author_date = _format_author_date(date)
    if author_date:
        env["GIT_AUTHOR_DATE"] = author_date
        env["GIT_COMMITTER_DATE"] = author_date
    subprocess.run(
        ["git", "commit", "-m", msg],
        cwd=cwd, check=True, capture_output=True, env=env,
    )


# --- resume checkpoint ------------------------------------------------------


def load_state(path: Path | str) -> dict[int, str]:
    """Load {doc_id -> disposition} from a JSON checkpoint, or {} if absent.

    A ~90-min run will be interrupted eventually; the checkpoint lets a
    re-invocation skip already-processed doc_ids and continue idempotently.
    """
    path = Path(path)
    if not path.exists():
        return {}
    raw = json.loads(path.read_text(encoding="utf-8"))
    return {int(k): v for k, v in raw.get("processed", {}).items()}


def save_state(path: Path | str, processed: dict[int, str]) -> None:
    """Persist the checkpoint atomically (write to a temp file, then rename)."""
    path = Path(path)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(
        json.dumps({"processed": {str(k): v for k, v in processed.items()}},
                   ensure_ascii=False, indent=0),
        encoding="utf-8",
    )
    tmp.replace(path)


def classify_change(committed_raw: str, candidate_raw: str, hist_grew: bool) -> str:
    """Classify an EXISTING act's re-scrape outcome.

    * "reforma"   -> amendment_history gained DV references (a real amendment).
    * "popravka"  -> body changed but history did not (corrigendum).
    * "unchanged" -> normalized files are identical (skip).

    hist_grew is computed by the caller from the committed vs fresh
    amendment_history (see history_grew); a grown history always wins because
    a new DV reference is by definition an amendment event.
    """
    if hist_grew:
        return "reforma"
    if normalize_for_compare(committed_raw) != normalize_for_compare(candidate_raw):
        return "popravka"
    return "unchanged"


_ESTADO_VIGENTE_RE = re.compile(r"(?m)^estado:\s*vigente\s*$")


def _flip_estado_derogado(raw: str) -> str:
    """Flip the frontmatter estado from vigente to derogado (first match)."""
    return _ESTADO_VIGENTE_RE.sub("estado: derogado", raw, count=1)


# lex.bg annotates a repealed act as `… отм. ДВ. бр. N от <day month year>`.
_REPEAL_RE = re.compile(
    r"отм\.\s*ДВ\.?\s*бр\.?\s*\d+\s*от\s*(\d{1,2})\s+([А-Яа-я]+)\s*(\d{4})",
    re.IGNORECASE,
)


def parse_repeal_date(history_text: str) -> str | None:
    """Extract the ISO repeal date from a lex.bg `.HistoryOfDocument` string.

    Returns None when there is no `отм.` repeal marker — i.e. the act left the
    tree for a non-repeal reason (e.g. a private-body bylaw with no ДВ
    promulgation), which must NOT be auto-flipped to derogado.
    """
    m = _REPEAL_RE.search(history_text)
    if not m:
        return None
    month = BG_MONTHS.get(m.group(2).lower())
    if not month:
        return None
    return f"{int(m.group(3)):04d}-{month:02d}-{int(m.group(1)):02d}"


# --- orchestrator -----------------------------------------------------------


@dataclass
class RefreshReport:
    added: list[dict] = field(default_factory=list)        # {doc_id, slug, title}
    reforma: list[dict] = field(default_factory=list)      # {doc_id, slug}
    popravka: list[dict] = field(default_factory=list)     # {doc_id, slug}
    unchanged: list[int] = field(default_factory=list)
    missing_kept: list[dict] = field(default_factory=list)  # {doc_id, slug}
    otmyana: list[dict] = field(default_factory=list)      # {doc_id, slug, repeal_date}
    missing_not_repealed: list[dict] = field(default_factory=list)  # {doc_id, slug}
    errors: list[dict] = field(default_factory=list)       # {doc_id, error}
    gate_failures: list[dict] = field(default_factory=list)  # {doc_id, slug, uncovered_chars, top_buckets}
    stale_categories: dict = field(default_factory=dict)
    pages_used: dict = field(default_factory=dict)

    def summary(self) -> str:
        return (
            f"ADDED={len(self.added)} REFORMA={len(self.reforma)} "
            f"POPRAVKA={len(self.popravka)} UNCHANGED={len(self.unchanged)} "
            f"MISSING(kept)={len(self.missing_kept)} OTMYANA={len(self.otmyana)} "
            f"NO-REPEAL={len(self.missing_not_repealed)} "
            f"ERRORS={len(self.errors)} GATE-FAIL={len(self.gate_failures)} "
            f"STALE={self.stale_categories or '{}'}"
        )


def _fetch_assemble(client, parser, metadata_parser, doc_id, category):
    """Fetch + convert + parse one act into (meta, body, gate).

    gate is the result of uncovered_legal_text(soup, body): a dict with
    ``uncovered_chars`` and ``buckets``.  Callers must check the gate before
    writing any .md file — see refresh() for the threshold logic.
    """
    soup = client.fetch_soup(doc_id)
    body = parser.convert(soup)
    gate = uncovered_legal_text(soup, body)
    meta = metadata_parser.parse(soup, doc_id=doc_id, category=category)
    return meta, body, gate


def refresh(
    output_dir: Path | str,
    *,
    db_path: str = "catalog.db",
    branch: str | None = None,
    state_path: Path | str | None = None,
    dry_run: bool = False,
    flip_missing_estado: bool = False,
    today_iso: str | None = None,
    crawl_config: dict[str, int] | None = None,
    session=None,
    tree_transport=None,
    client=None,
    parser=None,
    metadata_parser=None,
) -> RefreshReport:
    """Re-photograph lex.bg and refresh the corpus as a fresh snapshot.

    See the module docstring and the §4 algorithm in the handoff. Deps are
    injectable for testing; in production they are built from one shared
    RateLimitedSession so the 1 req/sec ceiling spans tree crawl and doc
    fetches uniformly. A CloudflareChallenge is intentionally NOT caught — it
    halts the run for manual intervention (delivery-contract Rate Limiting §4).
    """
    output_dir = Path(output_dir)
    today_iso = today_iso or date.today().isoformat()
    state_path = Path(state_path) if state_path else output_dir / ".refresh-state.json"

    if session is None and (tree_transport is None or client is None):
        session = RateLimitedSession()
    if tree_transport is None:
        tree_transport = TreeTransport(session=session)
    if client is None:
        client = LexBgClient(transport=HttpTransport(session=session))
    parser = parser or HtmlToMarkdown()
    metadata_parser = metadata_parser or MetadataParser()

    if branch and not dry_run:
        log.info("creating branch %s", branch)
        _git_checkout_branch(branch, cwd=output_dir)

    log.info("Crawling lex.bg catalog (with staleness probe)...")
    crawl = crawl_with_probe(tree_transport, config=crawl_config)
    if crawl.stale_categories:
        log.warning(
            "STALE CATEGORIES_CONFIG — new acts found on pages beyond the "
            "hardcoded counts: %s. Update fetcher/bg/discovery.CATEGORIES_CONFIG "
            "under IMPLEMENTATION-PREFLIGHT.", crawl.stale_categories,
        )
    lex_entries = {e["doc_id"]: e for e in crawl.catalog}
    lex_ids = set(lex_entries)

    corpus = load_corpus_catalog(output_dir)
    corpus_ids = set(corpus)
    added_ids, existing_ids, missing_ids = partition(lex_ids, corpus_ids)
    log.info("partition: ADDED=%d EXISTING=%d MISSING=%d",
             len(added_ids), len(existing_ids), len(missing_ids))

    report = RefreshReport(
        stale_categories=crawl.stale_categories, pages_used=crawl.pages_used,
    )

    if dry_run:
        report.added = [
            {"doc_id": d, "title": lex_entries[d]["name"]} for d in sorted(added_ids)
        ]
        report.missing_kept = [
            {"doc_id": d, "slug": corpus[d].slug} for d in sorted(missing_ids)
        ]
        report.unchanged = sorted(existing_ids)  # not classified without a fetch
        log.info("DRY RUN — %s", report.summary())
        return report

    state = load_state(state_path)
    used_slugs = seed_used_slugs(corpus)
    threshold = int(os.environ.get("LEGALIZE_COVERAGE_THRESHOLD", 64))

    # --- ADDED: brand-new acts -> [nova] ---
    for doc_id in sorted(added_ids):
        if doc_id in state:
            continue
        entry = lex_entries[doc_id]
        # Translate the lex.bg tree slug (code/ords/regs/reg_laws) to the
        # corpus directory name (codes/ordinances/regulations/implementing),
        # exactly as bootstrap does. Without this, new acts in 4 of 5
        # categories land in directories index/build.py never scans.
        corpus_dir = CATEGORY_DIRS.get(entry["category"], entry["category"])
        try:
            meta, body, gate = _fetch_assemble(
                client, parser, metadata_parser, doc_id, corpus_dir)
            title = meta.get("titulo") or entry["name"]
            if gate["uncovered_chars"] > threshold:
                slug_hint = generate_slug(title) or str(doc_id)
                record = {
                    "doc_id": doc_id,
                    "slug": slug_hint,
                    "title": title,
                    "uncovered_chars": gate["uncovered_chars"],
                    "top_buckets": dict(
                        sorted(gate["buckets"].items(), key=lambda x: -x[1])[:5]
                    ),
                }
                report.gate_failures.append(record)
                state[doc_id] = "gate-fail"
                save_state(state_path, state)
                log.warning(
                    "coverage gate FAIL [nova] %s (doc_id=%d) uncovered_chars=%d — skipping write",
                    title, doc_id, gate["uncovered_chars"],
                )
                continue
            slug = mint_slug(meta.get("titulo", ""), doc_id, used_slugs)
            filepath = output_dir / corpus_dir / f"{slug}.md"
            filepath.parent.mkdir(parents=True, exist_ok=True)
            filepath.write_text(assemble_file(meta, body), encoding="utf-8")
            _git_commit_typed(filepath, "nova", title, doc_id,
                              meta.get("fecha_publicacion"), output_dir)
            report.added.append({"doc_id": doc_id, "slug": slug, "title": title})
            state[doc_id] = "nova"
            save_state(state_path, state)
            log.info("[nova] %s (doc_id=%d) -> %s", title, doc_id, slug)
        except CloudflareChallenge:
            raise
        except Exception as e:  # noqa: BLE001 — record and continue
            log.error("FAILED nova doc_id=%d: %s", doc_id, e)
            report.errors.append({"doc_id": doc_id, "error": str(e)})
            state[doc_id] = "error"
            save_state(state_path, state)

    # --- EXISTING: re-scrape, compare -> [reforma] / [popravka] / skip ---
    for doc_id in sorted(existing_ids):
        if doc_id in state:
            continue
        ce = corpus[doc_id]
        try:
            meta, body, gate = _fetch_assemble(
                client, parser, metadata_parser, doc_id, ce.category)
            title = meta.get("titulo") or ce.frontmatter.get("titulo") or f"doc {doc_id}"
            if gate["uncovered_chars"] > threshold:
                record = {
                    "doc_id": doc_id,
                    "slug": ce.slug,
                    "title": title,
                    "uncovered_chars": gate["uncovered_chars"],
                    "top_buckets": dict(
                        sorted(gate["buckets"].items(), key=lambda x: -x[1])[:5]
                    ),
                }
                report.gate_failures.append(record)
                state[doc_id] = "gate-fail"
                save_state(state_path, state)
                log.warning(
                    "coverage gate FAIL [existing] %s (doc_id=%d) uncovered_chars=%d — skipping write",
                    title, doc_id, gate["uncovered_chars"],
                )
                continue
            candidate = assemble_file(meta, body)
            fresh_hist = meta.get("amendment_history") or []
            grew = history_grew(ce.amendment_history, fresh_hist)
            disposition = classify_change(ce.raw_text, candidate, grew)
            if disposition == "unchanged":
                report.unchanged.append(doc_id)
                state[doc_id] = "unchanged"
            else:
                # SAME slug — slug stability is the #1 invariant.
                ce.path.write_text(candidate, encoding="utf-8")
                cdate = latest_amendment_date(fresh_hist) or meta.get("fecha_publicacion")
                _git_commit_typed(ce.path, disposition, title, doc_id, cdate, output_dir)
                bucket = report.reforma if disposition == "reforma" else report.popravka
                bucket.append({"doc_id": doc_id, "slug": ce.slug})
                state[doc_id] = disposition
                log.info("[%s] %s (doc_id=%d)", disposition, title, doc_id)
            save_state(state_path, state)
        except CloudflareChallenge:
            raise
        except Exception as e:  # noqa: BLE001
            log.error("FAILED existing doc_id=%d: %s", doc_id, e)
            report.errors.append({"doc_id": doc_id, "error": str(e)})
            state[doc_id] = "error"
            save_state(state_path, state)

    # --- MISSING: keep the file (repealed acts stay). Optionally flip estado. ---
    # With flip_missing_estado, re-fetch each act and flip ONLY those lex.bg
    # confirms repealed (`отм. ДВ`), dating the [otmyana] commit at the real
    # repeal date. Acts that left the tree without a repeal marker (e.g. a
    # non-ДВ private bylaw) are routed to missing_not_repealed for owner review,
    # never auto-flipped.
    for doc_id in sorted(missing_ids):
        ce = corpus[doc_id]
        report.missing_kept.append({"doc_id": doc_id, "slug": ce.slug})
        if not flip_missing_estado or doc_id in state:
            continue
        try:
            soup = client.fetch_soup(doc_id)
            hist_el = soup.select_one(".HistoryOfDocument")
            repeal_date = parse_repeal_date(hist_el.get_text() if hist_el else "")
            if repeal_date is None:
                report.missing_not_repealed.append({"doc_id": doc_id, "slug": ce.slug})
                state[doc_id] = "missing-no-repeal"
                save_state(state_path, state)
                log.warning("MISSING but no repeal marker: %s (doc_id=%d) — review", ce.slug, doc_id)
                continue
            flipped = _flip_estado_derogado(ce.raw_text)
            if flipped != ce.raw_text:
                ce.path.write_text(flipped, encoding="utf-8")
                title = ce.frontmatter.get("titulo") or f"doc {doc_id}"
                _git_commit_typed(ce.path, "otmyana", title, doc_id, repeal_date, output_dir)
                report.otmyana.append({"doc_id": doc_id, "slug": ce.slug, "repeal_date": repeal_date})
                state[doc_id] = "otmyana"
                save_state(state_path, state)
                log.info("[otmyana] %s (doc_id=%d) estado->derogado (repealed %s)",
                         title, doc_id, repeal_date)
        except CloudflareChallenge:
            raise
        except Exception as e:  # noqa: BLE001
            log.error("FAILED otmyana doc_id=%d: %s", doc_id, e)
            report.errors.append({"doc_id": doc_id, "error": str(e)})
            state[doc_id] = "error"
            save_state(state_path, state)

    gate_report_path = output_dir / "gate-report.json"
    gate_report_path.write_text(
        json.dumps(report.gate_failures, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    log.info(
        "coverage gate: %d/%d acts failed",
        len(report.gate_failures),
        len(added_ids) + len(existing_ids),
    )

    if hasattr(client, "close"):
        client.close()
    log.info("REFRESH COMPLETE — %s", report.summary())
    return report


def _build_arg_parser():
    import argparse
    ap = argparse.ArgumentParser(description="Refresh the Bulgarian legislation corpus from lex.bg")
    ap.add_argument("--output", type=Path, default=Path("."), help="Corpus root")
    ap.add_argument("--db", default="catalog.db", help="SQLite catalog path (rebuilt separately)")
    ap.add_argument("--branch", default=None,
                    help="Create + switch to this branch before running (e.g. refresh/2026-06)")
    ap.add_argument("--state", default=None, help="Resume checkpoint path (default <output>/.refresh-state.json)")
    ap.add_argument("--dry-run", action="store_true", help="Crawl + partition only; no fetch/commit")
    ap.add_argument("--flip-missing-estado", action="store_true",
                    help="For acts gone from lex.bg, flip estado vigente->derogado and commit [otmyana]")
    return ap


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    args = _build_arg_parser().parse_args()
    report = refresh(
        args.output,
        db_path=args.db,
        branch=args.branch,
        state_path=args.state,
        dry_run=args.dry_run,
        flip_missing_estado=args.flip_missing_estado,
    )
    print(report.summary())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
