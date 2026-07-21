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
