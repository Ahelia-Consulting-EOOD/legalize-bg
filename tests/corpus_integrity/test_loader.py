"""Loader contract: frontmatter/body split, slug, category and deterministic order."""

from pathlib import Path

import pytest

from corpus_integrity.loader import CATEGORY_DIRS, iter_acts


def test_iter_acts_reads_frontmatter_and_body(tmp_path: Path):
    d = tmp_path / "laws"
    d.mkdir()
    (d / "test-act.md").write_text(
        "---\ntitulo: ТЕСТОВ ЗАКОН\nidentificador: 12345\n---\n\n**Чл. 1.** Текст.\n",
        encoding="utf-8",
    )
    acts = list(iter_acts(tmp_path))
    assert len(acts) == 1
    assert acts[0].slug == "test-act"
    assert acts[0].category == "laws"
    assert acts[0].frontmatter["identificador"] == 12345
    assert acts[0].body.strip() == "**Чл. 1.** Текст."


def test_iter_acts_is_deterministically_ordered(tmp_path: Path):
    d = tmp_path / "laws"
    d.mkdir()
    for name in ("b-act", "a-act", "c-act"):
        (d / f"{name}.md").write_text("---\ntitulo: X\n---\nтекст\n", encoding="utf-8")
    assert [a.slug for a in iter_acts(tmp_path)] == ["a-act", "b-act", "c-act"]


def test_iter_acts_skips_a_missing_category_directory(tmp_path: Path):
    """A corpus checkout need not carry every category directory."""
    d = tmp_path / "codes"
    d.mkdir()
    (d / "only.md").write_text("---\ntitulo: X\n---\nтекст\n", encoding="utf-8")
    assert [(a.category, a.slug) for a in iter_acts(tmp_path)] == [("codes", "only")]


def test_categories_are_ordered_and_cover_every_corpus_directory():
    """Iteration order across categories is fixed, so a run diff is reviewable."""
    assert CATEGORY_DIRS == (
        "laws",
        "codes",
        "ordinances",
        "regulations",
        "implementing",
        "postanovleniya",
    )


def test_act_without_frontmatter_is_an_error(tmp_path: Path):
    d = tmp_path / "laws"
    d.mkdir()
    (d / "raw.md").write_text("**Чл. 1.** Текст.\n", encoding="utf-8")
    with pytest.raises(ValueError, match="missing YAML frontmatter"):
        list(iter_acts(tmp_path))


def test_act_with_unterminated_frontmatter_is_an_error(tmp_path: Path):
    d = tmp_path / "laws"
    d.mkdir()
    (d / "open.md").write_text("---\ntitulo: X\n", encoding="utf-8")
    with pytest.raises(ValueError, match="unterminated YAML frontmatter"):
        list(iter_acts(tmp_path))
