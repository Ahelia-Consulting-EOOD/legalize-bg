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


def test_verify_always_hashes_sliced_segments(export_run):
    """Review 2026-07-24 (FR-032 cf-plane review, Important): a torn
    append-slice leaves row COUNTS intact, so only body hashing can
    catch it — and a uniform stride sample of 25 keys covers ~0.06% of
    a 182K-row corpus. Sliced-class rows (body above the statement
    budget) must therefore ALWAYS be hashed, independent of sample_n.
    This test tampers a byte inside an append-UPDATE statement and runs
    verify with sample_n=1 (stride sample = first key only): detection
    must not depend on the uniform sample getting lucky."""
    import json as _json

    from export_cf.verify import verify_export

    corpus, db, out = export_run
    target = None
    for chunk in sorted(out.glob("d1-fts-articles-*.sql")):
        text = chunk.read_text(encoding="utf-8")
        if "UPDATE articles_fts SET body = body ||" in text:
            target = chunk
            break
    assert target is not None, (
        "fixture must contain a sliced (append-UPDATE) segment — the "
        "conftest corpus seeds a >90KB annex for exactly this")
    original = target.read_bytes()
    idx = original.index("UPDATE articles_fts SET body = body ||"
                         .encode())
    tail = original[idx:]
    tampered = original[:idx] + tail.replace("а".encode(), "б".encode(), 1)
    assert tampered != original
    manifest_path = out / "manifest.json"
    manifest_orig = manifest_path.read_text(encoding="utf-8")
    try:
        target.write_bytes(tampered)
        m = _json.loads(manifest_orig)
        import hashlib
        m["files"][target.name] = hashlib.sha256(tampered).hexdigest()
        manifest_path.write_text(_json.dumps(m), encoding="utf-8")
        import pytest as _pytest

        from export_cf.verify import VerifyError
        with _pytest.raises(VerifyError, match="hash mismatch"):
            verify_export(db_path=db, out_dir=out, sample_n=1)
    finally:
        target.write_bytes(original)
        manifest_path.write_text(manifest_orig, encoding="utf-8")
