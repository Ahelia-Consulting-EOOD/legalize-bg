"""Chrome detector: site furniture that must never enter the content region.

Correctness-floor properties 1 and 4: a sidebar headline carrying „Чл. N“
manufactures a phantom article, and chrome contaminates the text at an address.
"""

from pathlib import Path

from corpus_integrity.checks.chrome import CHROME_MARKERS, NOT_CHROME, ChromeCheck
from corpus_integrity.loader import iter_acts


def _act(tmp_path: Path, body: str, category: str = "laws") -> Path:
    d = tmp_path / category
    d.mkdir(exist_ok=True)
    (d / "n.md").write_text(f"---\ntitulo: X\n---\n{body}\n", encoding="utf-8")
    return tmp_path


def test_flags_forum_sidebar(tmp_path):
    d = tmp_path / "ordinances"
    d.mkdir()
    (d / "n.md").write_text(
        "---\ntitulo: X\n---\n**Чл. 1.** Текст.\n\nПосети форума\n", encoding="utf-8"
    )
    v = ChromeCheck().run(iter_acts(tmp_path))
    assert len(v) == 1 and "Посети форума" in v[0].detail


def test_flags_the_site_footer_as_the_corpus_emits_it(tmp_path):
    """The footer arrives as „©“ and „Lex.bg |“ on separate lines."""
    root = _act(tmp_path, "**Чл. 1.** Текст.\n\n©\n\nLex.bg |\n")
    (v,) = ChromeCheck().run(iter_acts(root))
    assert v.check == "chrome"
    assert v.slug == "n"
    assert v.locator == "line 5"


def test_clean_act_passes(tmp_path):
    root = _act(tmp_path, "**Чл. 1.** Този закон урежда.")
    assert ChromeCheck().run(iter_acts(root)) == []


def test_words_that_occur_in_legislative_prose_are_not_chrome(tmp_path):
    """„Новини“ and „Форум за“ are ordinary words in enacted text.

    Both sentences below are quoted from the corpus. They are recorded as
    rejected markers so that no later leg silently re-adds them.
    """
    root = _act(
        tmp_path,
        "**Чл. 1.** Новините като информационни факти трябва да бъдат "
        "разграничавани от коментарите към тях.\n"
        '**Чл. 2.** Информационни блокове: "Форум за въпроси и отговори".\n',
    )
    assert ChromeCheck().run(iter_acts(root)) == []
    assert "Новини" in NOT_CHROME and "Форум за" in NOT_CHROME
    assert not (set(CHROME_MARKERS) & set(NOT_CHROME))
