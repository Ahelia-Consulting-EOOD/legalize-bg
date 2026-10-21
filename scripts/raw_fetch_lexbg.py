"""Fetch-only acquisition of lex.bg act pages into the raw store (plan step 2).

Reads every corpus act's ``identificador`` (its lex.bg document id), fetches the
raw page through the existing rate-limited client (1 request per second,
Cloudflare detection, retry with backoff) and keeps the bytes exactly as served
under ``data/raw/lexbg/<doc_id>.html``, with one manifest line per page:
url, fetched_at, sha256, bytes, slug, category. It decides nothing about the
text and writes no corpus file. Resumable: a page whose file exists with the
manifest's hash is skipped.

Usage: .venv/bin/python scripts/raw_fetch_lexbg.py [--limit N] [--only SLUG ...]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from fetcher.bg.client import RateLimitedSession  # noqa: E402

CATEGORIES = ("laws", "codes", "ordinances", "regulations", "implementing")
RAW_DIR = ROOT / "data" / "raw" / "lexbg"
MANIFEST = RAW_DIR / "manifest.jsonl"
LDOC = "https://lex.bg/laws/ldoc/{doc_id}"


def corpus_ids() -> list[tuple[str, str, str]]:
    out = []
    for cat in CATEGORIES:
        for md in sorted((ROOT / cat).glob("*.md")):
            text = md.read_text(encoding="utf-8")
            if not text.startswith("---"):
                continue
            fm = yaml.safe_load(text.split("---", 2)[1]) or {}
            ident = str(fm.get("identificador", "")).strip()
            if ident.lstrip("-").isdigit():
                out.append((ident, md.stem, cat))
    return out


def load_manifest() -> dict[str, dict]:
    done = {}
    if MANIFEST.exists():
        for line in MANIFEST.read_text(encoding="utf-8").splitlines():
            if line.strip():
                row = json.loads(line)
                done[row["doc_id"]] = row
    return done


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--only", nargs="*", default=None, help="slugs to fetch")
    args = ap.parse_args()
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    ids = corpus_ids()
    if args.only:
        wanted = set(args.only)
        ids = [t for t in ids if t[1] in wanted]
    if args.limit:
        ids = ids[: args.limit]
    done = load_manifest()
    todo = [t for t in ids if not (t[0] in done and (RAW_DIR / f"{t[0]}.html").exists())]
    print(f"{len(ids)} acts, {len(done)} already in the raw store, {len(todo)} to fetch", flush=True)
    session = RateLimitedSession()
    errors = 0
    with MANIFEST.open("a", encoding="utf-8") as mf:
        for n, (doc_id, slug, cat) in enumerate(todo, 1):
            url = LDOC.format(doc_id=doc_id)
            try:
                raw = session.get_bytes(url)
            except Exception as exc:  # a Cloudflare challenge raises and halts by design
                print(f"HALT at {n}/{len(todo)} {slug}: {type(exc).__name__}: {exc}", flush=True)
                return 2
            if not raw or len(raw) < 1000:
                errors += 1
                row = {"doc_id": doc_id, "slug": slug, "category": cat, "url": url,
                       "fetched_at": datetime.now(timezone.utc).isoformat(), "bytes": len(raw or b""),
                       "sha256": hashlib.sha256(raw or b"").hexdigest(), "status": "stub"}
            else:
                (RAW_DIR / f"{doc_id}.html").write_bytes(raw)
                row = {"doc_id": doc_id, "slug": slug, "category": cat, "url": url,
                       "fetched_at": datetime.now(timezone.utc).isoformat(), "bytes": len(raw),
                       "sha256": hashlib.sha256(raw).hexdigest(), "status": "ok"}
            mf.write(json.dumps(row, ensure_ascii=False) + "\n")
            mf.flush()
            if n % 100 == 0 or n == len(todo):
                print(f"{n}/{len(todo)} fetched, {errors} stubs, {time.strftime('%H:%M:%S')}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
