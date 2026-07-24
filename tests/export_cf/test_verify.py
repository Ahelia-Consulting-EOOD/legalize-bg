"""--verify self-check: recount rows vs catalog.db, sample acts against
provisions lookups, FTS row count == laws row count, file hashes."""

import json

import pytest

from export_cf.verify import VerifyError, verify_export


def test_verify_passes_on_intact_export(export_run):
    corpus, db, out = export_run
    report = verify_export(db_path=db, out_dir=out, sample_n=25)
    assert report["ok"] is True
    assert report["sampled_acts"] >= 1
    assert report["fts_rows"] == report["laws_rows"]
    assert report["articles_fts_rows"] > report["laws_rows"]
    assert report["sampled_segments"] >= 1


def test_verify_catches_tampered_segment_body(export_run):
    """The spot-hash reimports the fts series and compares sampled
    segment bodies against catalog.db — a corrupted append slice in an
    emitted chunk must surface even though the file's sha256 is
    recomputed from the tampered bytes (i.e. beyond the hash check)."""
    import hashlib
    import json as _json

    corpus, db, out = export_run
    chunk = sorted(out.glob("d1-fts-articles-*.sql"))[-1]
    original = chunk.read_bytes()
    # flip one Cyrillic letter inside a string literal: 'а' → 'б'
    tampered = original.replace("а".encode(), "б".encode(), 1)
    assert tampered != original
    manifest_path = out / "manifest.json"
    manifest_orig = manifest_path.read_text(encoding="utf-8")
    try:
        chunk.write_bytes(tampered)
        # re-point the manifest hash at the tampered bytes so ONLY the
        # semantic spot-hash can catch the corruption
        m = _json.loads(manifest_orig)
        m["files"][chunk.name] = hashlib.sha256(tampered).hexdigest()
        manifest_path.write_text(_json.dumps(m, ensure_ascii=False),
                                 encoding="utf-8")
        with pytest.raises(VerifyError):
            verify_export(db_path=db, out_dir=out, sample_n=25)
    finally:
        chunk.write_bytes(original)
        manifest_path.write_text(manifest_orig, encoding="utf-8")


def test_verify_catches_tampered_act(export_run, tmp_path):
    corpus, db, out = export_run
    victim = out / "r2" / "acts" / "zakon-vremeto.json"
    original = victim.read_text(encoding="utf-8")
    doc = json.loads(original)
    doc["articles"]["1"]["text_hash"] = "0" * 16
    victim.write_text(json.dumps(doc, ensure_ascii=False,
                                 separators=(",", ":")), encoding="utf-8")
    try:
        with pytest.raises(VerifyError):
            verify_export(db_path=db, out_dir=out, sample_n=25)
    finally:
        victim.write_text(original, encoding="utf-8")


def test_verify_catches_missing_d1_chunk(export_run):
    corpus, db, out = export_run
    chunk = next(out.glob("d1-fts-*.sql"))
    moved = chunk.with_suffix(".sql.bak")
    chunk.rename(moved)
    try:
        with pytest.raises(VerifyError):
            verify_export(db_path=db, out_dir=out, sample_n=25)
    finally:
        moved.rename(chunk)
