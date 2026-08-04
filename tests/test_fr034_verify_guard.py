"""`scripts/fr034_verify.py baseline` must never silently overwrite an
existing baseline file.

`.fr034-baseline.json` is the PRE-SWEEP verification floor: once the
sweep has rewritten the corpus and `catalog.db` has been rebuilt, the
pre-sweep row counts cannot be recomputed from anything still on disk.
The script's only protection used to be prose in its docstring, while
`{"baseline": baseline, "check": check}[sys.argv[1]]()` sits one habit
typo away from destroying it. These tests pin the guard.

The real `.fr034-baseline.json` is NEVER touched: `BASELINE` (and `DB`)
are monkeypatched onto tmp_path for every test here.
"""

import importlib.util
import json
import sqlite3
from pathlib import Path

import pytest

_SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "fr034_verify.py"


@pytest.fixture
def fr034(tmp_path, monkeypatch):
    """Load scripts/fr034_verify.py with DB and BASELINE redirected into
    tmp_path — the module resolves both as bare relative paths."""
    spec = importlib.util.spec_from_file_location("fr034_verify_under_test",
                                                  _SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    db = tmp_path / "catalog.db"
    conn = sqlite3.connect(db)
    conn.execute("CREATE TABLE provisions (law_id TEXT, article TEXT, "
                 "paragraph TEXT, valid_from TEXT, valid_to TEXT, "
                 "text TEXT, implicit INTEGER NOT NULL DEFAULT 0)")
    conn.execute("INSERT INTO provisions VALUES "
                 "('zakon-x','1',NULL,'2020-01-01',NULL,'т',0)")
    conn.commit()
    conn.close()
    monkeypatch.setattr(mod, "DB", str(db))
    monkeypatch.setattr(mod, "BASELINE", str(tmp_path / "baseline.json"))
    monkeypatch.delenv("FR034_FORCE", raising=False)
    return mod


def test_baseline_writes_when_absent(fr034):
    fr034.baseline()
    data = json.loads(Path(fr034.BASELINE).read_text(encoding="utf-8"))
    assert data["zakon-x"]["articles"] == 1


def test_baseline_refuses_to_overwrite(fr034):
    Path(fr034.BASELINE).write_text('{"pre-sweep": "floor"}',
                                    encoding="utf-8")
    with pytest.raises(SystemExit) as exc:
        fr034.baseline()
    assert exc.value.code != 0
    # untouched
    assert Path(fr034.BASELINE).read_text(encoding="utf-8") == \
        '{"pre-sweep": "floor"}'
    # the message (printed by the interpreter on exit) must name BOTH the
    # file and the override
    msg = str(exc.value)
    assert "baseline.json" in msg and "FR034_FORCE=1" in msg


def test_baseline_overwrites_with_force(fr034, monkeypatch):
    Path(fr034.BASELINE).write_text('{"pre-sweep": "floor"}',
                                    encoding="utf-8")
    monkeypatch.setenv("FR034_FORCE", "1")
    fr034.baseline()
    data = json.loads(Path(fr034.BASELINE).read_text(encoding="utf-8"))
    assert "zakon-x" in data
