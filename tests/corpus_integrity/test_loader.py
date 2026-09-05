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


def test_a_delimiter_inside_a_block_scalar_does_not_truncate_the_frontmatter(
    tmp_path: Path,
):
    """The split is line-anchored, so only a line that is exactly `---` closes.

    An indented `---` inside a YAML block scalar used to end the frontmatter,
    silently dropping every field after it into the body with no error.
    """
    d = tmp_path / "laws"
    d.mkdir()
    (d / "scalar.md").write_text(
        "---\nnota: |\n  ред\n  ---\n  ред\ntitulo: ТЕСТОВ ЗАКОН\n---\nТЯЛО\n",
        encoding="utf-8",
    )
    (act,) = iter_acts(tmp_path)
    assert act.frontmatter["titulo"] == "ТЕСТОВ ЗАКОН"
    assert act.frontmatter["nota"] == "ред\n---\nред\n"
    assert act.body == "ТЯЛО\n"


def test_a_horizontal_rule_in_the_body_stays_in_the_body(tmp_path: Path):
    d = tmp_path / "laws"
    d.mkdir()
    (d / "rule.md").write_text(
        "---\ntitulo: X\n---\nпреди\n---\nслед\n", encoding="utf-8"
    )
    (act,) = iter_acts(tmp_path)
    assert act.body == "преди\n---\nслед\n"


def test_a_closing_delimiter_at_end_of_file_is_accepted(tmp_path: Path):
    d = tmp_path / "laws"
    d.mkdir()
    (d / "nobody.md").write_text("---\ntitulo: X\n---", encoding="utf-8")
    (act,) = iter_acts(tmp_path)
    assert act.body == ""


def test_a_file_that_is_not_utf8_names_itself_in_the_error(tmp_path: Path):
    """A byte offset with no file name is unusable across 3,624 acts."""
    d = tmp_path / "laws"
    d.mkdir()
    (d / "cp1251.md").write_bytes("---\ntitulo: ЗАКОН\n---\nТЯЛО\n".encode("cp1251"))
    with pytest.raises(ValueError, match=r"cp1251\.md: not valid UTF-8"):
        list(iter_acts(tmp_path))
