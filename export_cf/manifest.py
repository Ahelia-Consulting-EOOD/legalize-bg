"""stats.json + manifest.json writers.

Manifest layout:
  counts   — per-table D1 row counts (incl. laws_fts titles and
             articles_fts segments) + acts_json/versions_json file counts
  files    — sha256 per top-level artifact (d1-schema.sql, d1-data-*.sql,
             r2/meta/stats.json)
  classes  — per artifact class (acts, versions): file count + aggregate
             sha256 over sorted "relpath sha256" lines (recomputable from
             the tree alone; keeps manifest.json small at 7k+ objects)
  exported_at — the ONLY timestamp in the export (spec: determinism)
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from mcp_server.queries import corpus_stats

from export_cf.acts import dump_json


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def class_aggregate(out_dir: Path, subdir: str) -> dict:
    """Count + aggregate sha256 for every .json under out_dir/subdir,
    streamed file-by-file in sorted order."""
    files = sorted((Path(out_dir) / subdir).rglob("*.json"))
    h = hashlib.sha256()
    for f in files:
        rel = f.relative_to(out_dir).as_posix()
        h.update(f"{rel} {_sha256_file(f)}\n".encode())
    return {"count": len(files), "sha256": h.hexdigest()}


def export_stats(conn: sqlite3.Connection, r2_dir: Path,
                 exported_at: str) -> dict:
    stats = corpus_stats(conn)
    stats["exported_at"] = exported_at
    dump_json(stats, Path(r2_dir) / "meta" / "stats.json")
    return stats


def write_manifest(out_dir: Path, counts: dict, exported_at: str,
                   max_fts_body_bytes: int = 0,
                   max_statement_bytes: int = 0,
                   fts_guards: dict | None = None) -> dict:
    out_dir = Path(out_dir)
    files = {}
    for f in sorted(out_dir.glob("d1-*.sql")):
        files[f.name] = _sha256_file(f)
    files["r2/meta/stats.json"] = _sha256_file(
        out_dir / "r2" / "meta" / "stats.json")
    manifest = {
        "exported_at": exported_at,
        "counts": counts,
        # v2.0 (replaces the retired fts_truncated key): largest
        # emitted articles_fts body in UTF-8 bytes — must be ≤ 400,000
        # (index SEG_MAX_BYTES contract), which keeps every value far
        # below D1's 2,000,000-byte cap. Nothing is ever truncated.
        "max_fts_body_bytes": max_fts_body_bytes,
        # Largest emitted SQL statement (v1.3: must be ≤ 90,000 — D1
        # rejects statements over ~100 KB with SQLITE_TOOBIG).
        "max_statement_bytes": max_statement_bytes,
        # v1.3.2 idempotency: guarded-statement counts across BOTH fts
        # series (the d1-meta series is NOT idempotent — import into
        # empty tables only).
        "fts_guards": fts_guards or {"inserts": 0, "updates": 0},
        "files": files,
        "classes": {
            "acts": class_aggregate(out_dir, "r2/acts"),
            "versions": class_aggregate(out_dir, "r2/versions"),
        },
    }
    dump_json(manifest, out_dir / "manifest.json")
    return manifest


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
