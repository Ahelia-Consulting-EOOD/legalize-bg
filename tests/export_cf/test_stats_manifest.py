"""meta/stats.json (precomputed /stats payload + exported_at) and
manifest.json (counts + sha256 per artifact class)."""

import hashlib
import json
import sqlite3

import pytest

from mcp_server.queries import corpus_stats


@pytest.fixture(scope="module")
def manifest(export_run):
    _, _, out = export_run
    return json.loads((out / "manifest.json").read_text(encoding="utf-8"))


def test_stats_json(export_run):
    _, db, out = export_run
    stats = json.loads((out / "r2" / "meta" / "stats.json")
                       .read_text(encoding="utf-8"))
    src = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    src.row_factory = sqlite3.Row
    expected = corpus_stats(src)
    src.close()
    exported_at = stats.pop("exported_at")
    assert exported_at  # ISO timestamp present
    assert stats == expected


def test_manifest_counts(export_run, manifest):
    _, db, _ = export_run
    src = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    laws = src.execute("SELECT COUNT(*) FROM laws").fetchone()[0]
    versions = src.execute("SELECT COUNT(*) FROM law_versions").fetchone()[0]
    src.close()
    c = manifest["counts"]
    assert c["laws"] == laws
    assert c["laws_fts"] == laws
    assert c["acts_json"] == laws
    assert c["law_versions"] == versions
    assert c["versions_json"] == versions


def test_manifest_file_hashes(export_run, manifest):
    _, _, out = export_run
    for rel, sha in manifest["files"].items():
        digest = hashlib.sha256((out / rel).read_bytes()).hexdigest()
        assert digest == sha, rel


def test_manifest_class_aggregates(export_run, manifest):
    """Per-class aggregate = sha256 over sorted 'relpath sha256' lines —
    recomputable from the r2/ tree alone."""
    _, _, out = export_run
    for cls, subdir in (("acts", "r2/acts"), ("versions", "r2/versions")):
        files = sorted((out / subdir).rglob("*.json"))
        lines = []
        for f in files:
            rel = f.relative_to(out).as_posix()
            lines.append(f"{rel} {hashlib.sha256(f.read_bytes()).hexdigest()}")
        agg = hashlib.sha256(("\n".join(lines) + "\n").encode()).hexdigest()
        assert manifest["classes"][cls]["count"] == len(files)
        assert manifest["classes"][cls]["sha256"] == agg
