"""R2 versions/{law_id}/{date}.json — one per law_versions row, body
taken via git show for historical rows (spec §R2)."""

import json
import sqlite3

import pytest


@pytest.fixture(scope="module")
def versions_dir(export_run):
    _, _, out = export_run
    return out / "r2" / "versions"


def test_one_json_per_version_row(export_run, versions_dir):
    _, db, _ = export_run
    src = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    rows = src.execute(
        "SELECT law_id, valid_from FROM law_versions").fetchall()
    src.close()
    expected = {f"{law_id}/{valid_from}.json" for law_id, valid_from in rows}
    on_disk = {str(p.relative_to(versions_dir))
               for p in versions_dir.rglob("*.json")}
    assert on_disk == expected


def test_historical_version_body_via_git_show(versions_dir):
    old = json.loads((versions_dir / "zakon-vremeto" / "2020-01-01.json")
                     .read_text(encoding="utf-8"))
    new = json.loads((versions_dir / "zakon-vremeto" / "2021-06-15.json")
                     .read_text(encoding="utf-8"))
    assert "СТАРА редакция" in old["body_markdown"]
    assert "НОВА редакция" in new["body_markdown"]
    assert old["articles"]["1"]["paragraphs"]["1"] == "СТАРА редакция."
    # historical row carries its own commit, not HEAD
    assert old["meta"]["commit_hash"] != new["meta"]["commit_hash"]
    # full-file reconstruction holds for git-show bodies too
    assert old["preamble_raw"].startswith("---\n")
    assert old["preamble_raw"].endswith("\n")


def test_latest_version_matches_acts_payload(export_run, versions_dir):
    _, _, out = export_run
    latest = json.loads((versions_dir / "zakon-vremeto" / "2021-06-15.json")
                        .read_text(encoding="utf-8"))
    act = json.loads((out / "r2" / "acts" / "zakon-vremeto.json")
                     .read_text(encoding="utf-8"))
    assert latest == act
