"""Tag-remnant detector: bare closing-tag text nodes left by the converter.

Correctness-floor properties 1 and 4: a remnant carried into an article
heading collides article keys and contaminates the text at the address.
"""

from pathlib import Path

from corpus_integrity.checks.remnants import RemnantCheck
from corpus_integrity.loader import iter_acts


def _corpus(tmp_path: Path, body: str) -> Path:
    d = tmp_path / "laws"
    d.mkdir(exist_ok=True)
    (d / "act.md").write_text(f"---\ntitulo: X\n---\n{body}\n", encoding="utf-8")
    return tmp_path


def test_flags_bare_span_remnant(tmp_path):
    root = _corpus(tmp_path, "**Чл. 3.**/span>. Участващите в производството.")
    v = RemnantCheck().run(iter_acts(root))
    assert len(v) == 1 and "/span>" in v[0].detail


def test_flags_sup_remnant(tmp_path):
    root = _corpus(tmp_path, "**Чл. 14н.**SUP>1. Нова разпоредба.")
    v = RemnantCheck().run(iter_acts(root))
    assert len(v) == 1 and "SUP>" in v[0].detail


def test_clean_act_passes(tmp_path):
    root = _corpus(tmp_path, "**Чл. 1.** Този закон урежда.")
    assert RemnantCheck().run(iter_acts(root)) == []


def test_violation_carries_the_check_name_slug_and_line(tmp_path):
    root = _corpus(tmp_path, "**Чл. 1.** Текст.\n\n**Чл. 2.**/span> Текст.")
    (v,) = RemnantCheck().run(iter_acts(root))
    assert v.check == "tag_remnants"
    assert v.slug == "act"
    # Line numbers are body-relative: the body's first line is line 1.
    assert v.locator == "line 3"


def test_every_marker_on_a_line_is_reported(tmp_path):
    root = _corpus(tmp_path, "**Чл. 1.**/span>SUP>2 Текст.")
    markers = {v.detail for v in RemnantCheck().run(iter_acts(root))}
    assert len(markers) == 2


def test_lowercase_sup_and_bold_remnants_are_flagged(tmp_path):
    root = _corpus(tmp_path, "а) текст/sup> и /B> още текст.")
    assert len(RemnantCheck().run(iter_acts(root))) == 2


def test_matching_is_case_sensitive_for_ordinary_prose(tmp_path):
    """The lowercase word 'sup' inside prose is not a remnant."""
    root = _corpus(tmp_path, "**Чл. 1.** Supervision и supervisor не са остатъци.")
    assert RemnantCheck().run(iter_acts(root)) == []
