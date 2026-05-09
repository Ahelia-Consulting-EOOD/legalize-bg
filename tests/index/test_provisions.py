import json
import pathlib
import pytest
from index.provisions import parse, Provision

GOLDEN_DIR = pathlib.Path(__file__).parent.parent / "fixtures" / "golden" / "provisions"


def test_extracts_simple_article():
    md = "**Чл. 1.** Този закон определя нещо."
    rows = parse(md, law_id="test")
    article_rows = [r for r in rows if r.paragraph is None]
    assert len(article_rows) == 1
    assert article_rows[0].article == "1"
    assert "този закон" in article_rows[0].text.lower()


def test_extracts_multiple_articles():
    md = """**Чл. 1.** Първи член.

**Чл. 2.** Втори член.

**Чл. 3.** Трети член.
"""
    rows = parse(md, law_id="test")
    article_rows = [r for r in rows if r.paragraph is None]
    assert [r.article for r in article_rows] == ["1", "2", "3"]


def test_extracts_cyrillic_suffix_articles():
    md = """**Чл. 14.** Базов член.

**Чл. 14а.** Допълнителен член.

**Чл. 14б.** Още един.
"""
    rows = parse(md, law_id="test")
    article_rows = [r for r in rows if r.paragraph is None]
    assert [r.article for r in article_rows] == ["14", "14а", "14б"]


def test_stops_at_structural_header():
    md = """**Чл. 5.** Член преди ПЗР.

## ПРЕХОДНИ И ЗАКЛЮЧИТЕЛНИ РАЗПОРЕДБИ

**§ 1.** Параграф от ПЗР — не е член.
"""
    rows = parse(md, law_id="test")
    article_rows = [r for r in rows if r.paragraph is None]
    assert len(article_rows) == 1
    assert "ПРЕХОДНИ" not in article_rows[0].text
    assert "§ 1" not in article_rows[0].text


def test_text_hash_is_stable():
    md = "**Чл. 1.** Текст."
    rows1 = parse(md, law_id="test")
    rows2 = parse(md, law_id="test")
    assert rows1[0].text_hash == rows2[0].text_hash


def test_text_hash_changes_with_content():
    rows1 = parse("**Чл. 1.** Текст А.", law_id="test")
    rows2 = parse("**Чл. 1.** Текст Б.", law_id="test")
    assert rows1[0].text_hash != rows2[0].text_hash


def test_returns_law_id_on_each_row():
    md = "**Чл. 1.** Текст."
    rows = parse(md, law_id="zop")
    for r in rows:
        assert r.law_id == "zop"


def test_skip_paragraph_with_multiple_anchors_cite_list():
    """A paragraph with 2+ capitalized 'Чл. N.' references is a cite list
    or template, not an article. Reviewer found a real instance in the
    ppz-aktsizi declaration template — emitting a row for the first
    cited number duplicates the real article and pollutes search."""
    md = """**Чл. 5.** Истинският член.

Декларация по Чл. 102а и Чл. 102б — образец на формуляр.

**Чл. 7.** Следващият истински член.
"""
    rows = parse(md, law_id="test")
    article_rows = [r for r in rows if r.paragraph is None]
    # 5 and 7 are real articles; the multi-anchor template paragraph
    # (capital Ч cited twice) is rejected.
    assert [r.article for r in article_rows] == ["5", "7"]


def test_skip_sentence_start_capitalized_reference():
    """A paragraph that opens with a capitalized 'Чл. N' but cites
    multiple is editorial/transitional text, not an anchor."""
    md = """Чл. 5 и Чл. 6 уреждат подобни въпроси на дейността.

**Чл. 7.** Истинският член.
"""
    rows = parse(md, law_id="test")
    article_rows = [r for r in rows if r.paragraph is None]
    assert [r.article for r in article_rows] == ["7"]


def test_extracts_alineas_from_article():
    md = """**Чл. 14.** (1) Първа алинея.

(2) Втора алинея.

(3) Трета алинея.
"""
    rows = parse(md, law_id="test")
    alineas = [r for r in rows if r.paragraph is not None]
    assert [r.paragraph for r in alineas] == ["1", "2", "3"]
    assert "Първа" in alineas[0].text
    assert "Втора" in alineas[1].text
    assert "Трета" in alineas[2].text


def test_article_row_text_includes_all_alineas():
    md = """**Чл. 14.** (1) Първа.

(2) Втора.
"""
    rows = parse(md, law_id="test")
    article = next(r for r in rows if r.paragraph is None)
    assert "Първа" in article.text and "Втора" in article.text


def test_article_with_no_alineas_emits_only_article_row():
    md = "**Чл. 1.** Един параграф без алинеи."
    rows = parse(md, law_id="test")
    assert len(rows) == 1
    assert rows[0].paragraph is None


def test_alinea_with_cyrillic_letter():
    md = """**Чл. 5.** (1) Първа.

(1а) Допълнителна първа.

(2) Втора.
"""
    rows = parse(md, law_id="test")
    alineas = [r for r in rows if r.paragraph is not None]
    assert [r.paragraph for r in alineas] == ["1", "1а", "2"]


def test_alinea_text_hash_is_alinea_only():
    """Alinea row's text_hash must reflect ONLY that alinea's text, so
    Phase 4 amendment-detection can pinpoint a single-alinea ZID without
    re-hashing the whole article."""
    md = """**Чл. 14.** (1) Първа.

(2) Втора.
"""
    rows = parse(md, law_id="test")
    alineas = [r for r in rows if r.paragraph is not None]
    h_alpha = alineas[0].text_hash
    md2 = """**Чл. 14.** (1) Първа.

(2) ВТОРА (изменена).
"""
    rows2 = parse(md2, law_id="test")
    alineas2 = [r for r in rows2 if r.paragraph is not None]
    assert alineas2[0].text_hash == h_alpha
    assert alineas2[1].text_hash != alineas[1].text_hash


def test_inline_alineas_within_single_paragraph():
    """Real corpus articles often pack all alineas into a single
    paragraph (no \\n\\n between them), e.g.,
    'Предмет и цел Чл. 1. (1) X. (2) Y. (3) Z.' Each (N) marker still
    starts its own alinea row."""
    md = "Предмет и цел Чл. 1. (1) Първа алинея. (2) Втора алинея. (3) Трета алинея."
    rows = parse(md, law_id="test")
    alineas = [r for r in rows if r.paragraph is not None]
    assert [r.paragraph for r in alineas] == ["1", "2", "3"]
    assert "Първа" in alineas[0].text
    assert "Втора" in alineas[1].text
    assert "Трета" in alineas[2].text


@pytest.mark.parametrize("fixture_name,law_id", [
    ("zop", "zop"),
    ("zeu", "zeu"),
    ("gpk", "gpk"),
    ("naredba-04-14", "naredba-04-14"),
    ("pravilnik-sadilishta", "pravilnik-sadilishta"),
    ("ppz-aktsizi", "ppz-aktsizi"),
])
def test_golden_provisions_per_fixture(fixture_name, law_id):
    """Lock the parser against each fixture. Goldens summarize counts
    and the first 10 articles; regenerate via REGENERATE_GOLDENS=1."""
    import os
    from bs4 import BeautifulSoup
    from fetcher.bg.text_parser import HtmlToMarkdown

    fixture = pathlib.Path(__file__).parent.parent / "fixtures" / "html" / f"{fixture_name}.html"
    soup = BeautifulSoup(fixture.read_bytes().decode("cp1251"), "lxml")
    md = HtmlToMarkdown().convert(soup)

    rows = parse(md, law_id=law_id)
    summary = {
        "law_id": law_id,
        "total_rows": len(rows),
        "article_rows": sum(1 for r in rows if r.paragraph is None),
        "alinea_rows": sum(1 for r in rows if r.paragraph is not None),
        "first_articles": sorted(
            {r.article for r in rows if r.paragraph is None},
            key=_article_sort_key,
        )[:10],
    }

    golden_path = GOLDEN_DIR / f"{fixture_name}.json"
    if os.environ.get("REGENERATE_GOLDENS"):
        GOLDEN_DIR.mkdir(parents=True, exist_ok=True)
        golden_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2))
        return

    assert golden_path.exists(), \
        f"missing golden {golden_path} — regenerate with REGENERATE_GOLDENS=1"
    expected = json.loads(golden_path.read_text(encoding="utf-8"))
    assert summary == expected, f"provisions extraction drift for {fixture_name}"


def test_zop_golden_subset():
    """ZOP fixture should produce a known set of articles. Golden anchors
    the parser; alinea-level coverage added in Task 5."""
    from bs4 import BeautifulSoup
    from fetcher.bg.text_parser import HtmlToMarkdown

    fixture = pathlib.Path(__file__).parent.parent / "fixtures" / "html" / "zop.html"
    soup = BeautifulSoup(fixture.read_bytes().decode("cp1251"), "lxml")
    md = HtmlToMarkdown().convert(soup)

    rows = parse(md, law_id="zop")
    articles = sorted({r.article for r in rows if r.paragraph is None}, key=_article_sort_key)
    assert "1" in articles
    assert "100" in articles or any(a.startswith("100") for a in articles)
    assert any(a[-1] in "абвгд" for a in articles), f"expected Cyrillic-suffix articles, got {articles[:20]}..."


def _article_sort_key(article: str):
    import re
    m = re.match(r"^(\d+)([а-я]*)$", article)
    if not m:
        return (0, article)
    return (int(m.group(1)), m.group(2))
