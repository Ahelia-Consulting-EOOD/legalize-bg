"""Deploy-guard: the MCP server must refuse to serve a corpus flagged as
defective (D-047 parser data-loss). Interim safety per the remediation plan
Phase 0 / Task 0. The guard is env-driven and OFF by default; it exists so a
known-incomplete corpus can never be served without an explicit override.
"""

from mcp_server.__main__ import _check_corpus_defective, main


def test_guard_blocks_when_flagged(monkeypatch):
    monkeypatch.setenv("LEGALIZE_CORPUS_DEFECTIVE", "1")
    monkeypatch.delenv("LEGALIZE_ALLOW_DEFECTIVE", raising=False)
    assert _check_corpus_defective() == 2


def test_guard_allows_explicit_override(monkeypatch):
    monkeypatch.setenv("LEGALIZE_CORPUS_DEFECTIVE", "1")
    monkeypatch.setenv("LEGALIZE_ALLOW_DEFECTIVE", "1")
    assert _check_corpus_defective() is None


def test_guard_dormant_when_not_flagged(monkeypatch):
    monkeypatch.delenv("LEGALIZE_CORPUS_DEFECTIVE", raising=False)
    assert _check_corpus_defective() is None


def test_main_refuses_to_start_when_corpus_flagged_defective(monkeypatch):
    """The guard runs before the DB is opened, so a flagged corpus refuses
    to start even with an otherwise-valid (or missing) catalog."""
    monkeypatch.setenv("LEGALIZE_CORPUS_DEFECTIVE", "1")
    monkeypatch.delenv("LEGALIZE_ALLOW_DEFECTIVE", raising=False)
    assert main(["--db", "/nonexistent/catalog.db", "--corpus", "."]) == 2
