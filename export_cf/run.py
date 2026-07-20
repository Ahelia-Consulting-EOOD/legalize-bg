"""Export orchestrator: one read-only pass over catalog.db + corpus.

`run_export` is the single entry point used by the CLI (`python -m
export_cf`) and the tests. Opens catalog.db strictly read-only
(`mode=ro` URI) — the exporter must never write to it.
"""

from __future__ import annotations

import logging
import sqlite3
from pathlib import Path

from export_cf.acts import export_acts, export_versions
from export_cf.d1 import export_d1
from export_cf.manifest import export_stats, now_iso, write_manifest

log = logging.getLogger(__name__)


def run_export(corpus_root: Path, db_path: str, out_dir: Path) -> dict:
    """Produce the full cf-export tree under `out_dir`; returns the
    manifest dict."""
    corpus_root = Path(corpus_root)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    r2_dir = out_dir / "r2"
    exported_at = now_iso()

    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    try:
        log.info("D1 dump → %s", out_dir)
        d1_counts = export_d1(conn, out_dir)
        log.info("R2 acts/ → %s", r2_dir / "acts")
        acts_n = export_acts(conn, corpus_root, r2_dir)
        log.info("R2 versions/ → %s", r2_dir / "versions")
        versions_n = export_versions(conn, corpus_root, r2_dir)
        log.info("R2 meta/stats.json")
        export_stats(conn, r2_dir, exported_at)
    finally:
        conn.close()

    counts = {**d1_counts, "acts_json": acts_n, "versions_json": versions_n}
    log.info("manifest.json")
    return write_manifest(out_dir, counts, exported_at)
