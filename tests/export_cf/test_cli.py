"""`python -m export_cf --corpus . --db catalog.db --out ./cf-export/`."""

import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def test_cli_end_to_end_with_verify(export_corpus, tmp_path):
    corpus, db = export_corpus
    out = tmp_path / "cf-export"
    proc = subprocess.run(
        [sys.executable, "-m", "export_cf", "--corpus", str(corpus),
         "--db", db, "--out", str(out), "--verify"],
        cwd=REPO, capture_output=True, text=True,
        env={"PYTHONPATH": str(REPO), "PATH": "/usr/bin:/bin"},
    )
    assert proc.returncode == 0, proc.stderr
    assert (out / "manifest.json").is_file()
    assert (out / "d1-schema.sql").is_file()
    assert (out / "r2" / "meta" / "stats.json").is_file()
    assert "verify: OK" in proc.stdout
