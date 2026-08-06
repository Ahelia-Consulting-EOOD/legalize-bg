"""`scripts/fr034_verify.py baseline` must never silently overwrite an
existing baseline file.

`.fr034-baseline.json` is the PRE-SWEEP verification floor: once the
sweep has rewritten the corpus and `catalog.db` has been rebuilt, the
pre-sweep row counts cannot be recomputed from anything still on disk.
The script's only protection used to be prose in its docstring, while
`{"baseline": baseline, "check": check}[sys.argv[1]]()` sits one habit
typo away from destroying it. These tests pin the guard.

The same applies to `.article-baseline.json`, the per-(law_id, article)
floor of D-058 (iv): it is the quantity regression net for the repair
sweep, and it is equally unrecomputable once the sweep has run.

The real baseline files are NEVER touched: `BASELINE`,
`ARTICLE_BASELINE` and `DB` are monkeypatched onto tmp_path for every
test here.
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


# --- D-058 (iv): the per-(law_id, article) baseline -------------------
#
# `check`'s R1/R2 are per-LAW aggregates, so an article that loses rows
# is cancelled by any other article of the same law that gains them. The
# per-article baseline keys the counts on (law_id, article) so a loss
# cannot be offset by a gain elsewhere in the act.


@pytest.fixture
def fr034_articles(fr034, tmp_path, monkeypatch):
    """`fr034`, with ARTICLE_BASELINE also redirected into tmp_path so
    the real `.article-baseline.json` is never touched."""
    monkeypatch.setattr(fr034, "ARTICLE_BASELINE",
                        str(tmp_path / "article-baseline.json"))
    return fr034


def _insert(mod, rows):
    conn = sqlite3.connect(mod.DB)
    conn.executemany("INSERT INTO provisions VALUES (?,?,?,?,?,?,?)", rows)
    conn.commit()
    conn.close()


def test_article_counts_are_keyed_per_article(fr034_articles):
    _insert(fr034_articles, [
        # чл. 2: one whole-article row, one explicit alinea, one implicit
        ("zakon-x", "2", None, "2020-01-01", None, "т", 0),
        ("zakon-x", "2", "1", "2020-01-01", None, "т", 0),
        ("zakon-x", "2", "2", "2020-01-01", None, "т", 1),
        # чл. 3: a superseded row must not be counted
        ("zakon-x", "3", None, "2020-01-01", None, "т", 0),
        ("zakon-x", "3", "1", "2019-01-01", "2020-01-01", "т", 0),
        # a second law must not merge into the first
        ("zakon-y", "2", None, "2020-01-01", None, "т", 0),
    ])
    counts = fr034_articles._article_counts(sqlite3.connect(fr034_articles.DB))
    assert counts["zakon-x"]["1"] == {"explicit_alineas": 0, "articles": 1}
    assert counts["zakon-x"]["2"] == {"explicit_alineas": 1, "articles": 1}
    assert counts["zakon-x"]["3"] == {"explicit_alineas": 0, "articles": 1}
    assert counts["zakon-y"]["2"] == {"explicit_alineas": 0, "articles": 1}
    assert set(counts["zakon-x"]) == {"1", "2", "3"}
    assert set(counts["zakon-y"]) == {"2"}


def test_article_baseline_writes_when_absent(fr034_articles):
    fr034_articles.article_baseline()
    data = json.loads(
        Path(fr034_articles.ARTICLE_BASELINE).read_text(encoding="utf-8"))
    assert data["zakon-x"]["1"]["articles"] == 1


def test_article_baseline_refuses_to_overwrite(fr034_articles):
    Path(fr034_articles.ARTICLE_BASELINE).write_text(
        '{"pre-sweep": "floor"}', encoding="utf-8")
    with pytest.raises(SystemExit) as exc:
        fr034_articles.article_baseline()
    assert exc.value.code != 0
    # untouched
    assert Path(fr034_articles.ARTICLE_BASELINE).read_text(
        encoding="utf-8") == '{"pre-sweep": "floor"}'
    msg = str(exc.value)
    assert "article-baseline.json" in msg and "FR034_FORCE=1" in msg


def test_article_baseline_overwrites_with_force(fr034_articles, monkeypatch):
    Path(fr034_articles.ARTICLE_BASELINE).write_text(
        '{"pre-sweep": "floor"}', encoding="utf-8")
    monkeypatch.setenv("FR034_FORCE", "1")
    fr034_articles.article_baseline()
    data = json.loads(
        Path(fr034_articles.ARTICLE_BASELINE).read_text(encoding="utf-8"))
    assert "zakon-x" in data


def test_article_check_passes_when_unchanged(fr034_articles, capsys):
    fr034_articles.article_baseline()
    fr034_articles.article_check()
    assert "OK" in capsys.readouterr().out


def test_article_check_flags_a_vanished_article_as_A2(fr034_articles, capsys):
    _insert(fr034_articles, [
        ("zakon-x", "2", None, "2020-01-01", None, "т", 0)])
    fr034_articles.article_baseline()
    conn = sqlite3.connect(fr034_articles.DB)
    conn.execute("DELETE FROM provisions WHERE law_id='zakon-x' "
                 "AND article='2'")
    conn.commit()
    conn.close()
    with pytest.raises(SystemExit) as exc:
        fr034_articles.article_check()
    assert exc.value.code != 0
    out = capsys.readouterr().out
    assert "A2 zakon-x чл.2" in out
    # чл. 1 is untouched and must not be reported
    assert "чл.1" not in out


def test_article_check_catches_a_loss_offset_by_a_gain(fr034_articles, capsys):
    """The whole point of D-058 (iv): per-law aggregates net this to
    zero, so `check` sees nothing. Per-article, the loss must surface."""
    _insert(fr034_articles, [
        ("zakon-x", "1", "1", "2020-01-01", None, "т", 0),
        ("zakon-x", "2", None, "2020-01-01", None, "т", 0),
    ])
    fr034_articles.article_baseline()
    conn = sqlite3.connect(fr034_articles.DB)
    # чл. 1 loses its explicit alinea; чл. 2 gains one — per-law totals
    # are unchanged.
    conn.execute("DELETE FROM provisions WHERE law_id='zakon-x' "
                 "AND article='1' AND paragraph='1'")
    conn.execute("INSERT INTO provisions VALUES "
                 "('zakon-x','2','1','2020-01-01',NULL,'т',0)")
    conn.commit()
    conn.close()
    # the per-LAW aggregate really is blind to it: same totals, so R1
    # cannot fire
    per_law = fr034_articles._counts(sqlite3.connect(fr034_articles.DB))
    assert per_law["zakon-x"]["explicit_alineas"] == 1
    with pytest.raises(SystemExit) as exc:
        fr034_articles.article_check()
    assert exc.value.code != 0
    out = capsys.readouterr().out
    assert "A1" in out
