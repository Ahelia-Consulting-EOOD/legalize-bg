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


def test_parenthetical_references_dont_create_alinea_rows():
    """Reviewer-flagged scenario: 'Чл. 14 (вж. чл. 2) текст…' should NOT
    produce a bogus paragraph='2' row. The (N) regex requires the
    parens to enclose ONLY digits + optional Cyrillic suffix; references
    like '(вж. чл. 2)' or '(в сила от 01.01.2025 г.)' don't match
    because their content is not purely numeric."""
    md = "**Чл. 14.** (вж. чл. 2) Този член се прилага съответно (в сила от 01.01.2025 г.)."
    rows = parse(md, law_id="test")
    article_rows = [r for r in rows if r.paragraph is None]
    alinea_rows = [r for r in rows if r.paragraph is not None]
    # Article row exists with the full body; no alinea rows generated
    # from parenthetical references.
    assert len(article_rows) == 1 and article_rows[0].article == "14"
    assert alinea_rows == []


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
    # FR-034 rule 6: a REAL pre-Указ-883 act (trimmed live lex.bg fetch of
    # ЗЗД, 2026-07-31, чл. 1–41 incl. чл. 36). Unnumbered алинеи only, so
    # explicit_rows must be 0 and every alinea row implicit — the only
    # fixture that actually exercises the feature this FR exists for.
    ("zzd", "zzd"),
])
def test_golden_provisions_per_fixture(fixture_name, law_id):
    """Lock the parser against each fixture. Goldens summarize counts
    and the first 10 articles; regenerate via REGENERATE_GOLDENS=1.

    FR-034: `explicit_rows` (source-numbered "(N)" alineas) and
    `implicit_rows` (position-derived alineas in pre-Указ-883 acts) are
    pinned SEPARATELY and must never be folded into one `alinea_rows`
    total — a single count lets a loss of explicit rows hide behind a
    gain of implicit ones, which is exactly how silent corpus loss gets
    ratified.

    `explicit_rows` equals the pre-FR-034 values EXACTLY, except these
    verified recoveries of text HEAD had silently dropped:
      - gpk 1,486 -> 1,497: чл. 22а +2, чл. 22з +3, чл. 22и +1 (HEAD
        truncated the article at a top-level <br>; чл. 22и kept only
        73 of 596 chars). The remaining +5 (чл. 16, 37, 54, 61, 165)
        are quoted ЗИД amendment text absorbed onto the DUPLICATE ПЗР
        article rows that HEAD already emitted — not new articles.
      - ppz-aktsizi 824 -> 842: чл. 102а +6 and чл. 102б +10 were
        absent from HEAD entirely (lex.bg emits them as
        "Чл. 102а./span>.", so HEAD's glued paragraph tripped the
        2+-anchor cite-list rule and discarded both real articles);
        чл. 58 +2 (HEAD kept 233 of 2,943 chars).
      - zop stays at 1,156 and zeu at 232 — exact parity.
    """
    import os
    from bs4 import BeautifulSoup
    from fetcher.bg.text_parser import HtmlToMarkdown

    fixture = pathlib.Path(__file__).parent.parent / "fixtures" / "html" / f"{fixture_name}.html"
    soup = BeautifulSoup(fixture.read_bytes().decode("cp1251"), "lxml")
    md = HtmlToMarkdown().convert(soup)

    rows = parse(md, law_id=law_id)

    # Pollution tripwire (FR-034 rule 4): lex.bg nests an AdOcean ad slot
    # and <script>/<style> blocks inside Article elements. Nothing that
    # looks like markup or JavaScript may ever reach a provision row —
    # it would go straight into FTS and into get_article output.
    for r in rows:
        for token in ("ado.", "javascript", "function(", "<"):
            assert token not in r.text, (
                f"{fixture_name}: {token!r} leaked into чл. {r.article} "
                f"(paragraph={r.paragraph}): {r.text[:160]!r}"
            )

    summary = {
        "law_id": law_id,
        "total_rows": len(rows),
        "article_rows": sum(1 for r in rows if r.paragraph is None),
        "explicit_rows": sum(
            1 for r in rows if r.paragraph is not None and not r.implicit
        ),
        "implicit_rows": sum(1 for r in rows if r.implicit),
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


# --- FR-034: unnumbered алинеи (pre-1974 acts) + child-div continuation ---

ZZD_STYLE_MD = """\
**Чл. 36.** Едно лице може да представлява друго по разпоредба на закона или по волята на представлявания.

Последиците от правните действия, които представителят извършва, възникват направо за представлявания.

**Чл. 37.** Еднолинейна разпоредба без втора алинея.

## ПРЕХОДНИ РАЗПОРЕДБИ

(ОБН. - ДВ, БР. 2 ОТ 1950 Г.)
"""


def test_implicit_alineas_for_markerless_multiparagraph_article():
    rows = parse(ZZD_STYLE_MD, law_id="zzd")
    art36 = [r for r in rows if r.article == "36"]
    whole = [r for r in art36 if r.paragraph is None]
    alineas = [r for r in art36 if r.paragraph is not None]
    # article-as-whole keeps BOTH paragraphs (continuation accepted)
    assert len(whole) == 1
    assert "Последиците" in whole[0].text
    assert whole[0].implicit is False
    # two implicit alinea rows, position-numbered
    assert [(r.paragraph, r.implicit) for r in alineas] == [("1", True), ("2", True)]
    assert alineas[0].text.startswith("Едно лице")   # anchor stripped
    assert alineas[1].text.startswith("Последиците")


def test_single_paragraph_article_gets_no_implicit_rows():
    rows = parse(ZZD_STYLE_MD, law_id="zzd")
    art37 = [r for r in rows if r.article == "37"]
    assert len(art37) == 1 and art37[0].paragraph is None


def test_obn_banner_not_swallowed_as_continuation():
    """Both closers must hold: the ## heading closes чл. 37, and a bare
    ^(ОБН banner with no intervening heading also closes an open article."""
    rows = parse(ZZD_STYLE_MD, law_id="zzd")
    art37 = [r for r in rows if r.article == "37"]
    assert "ОБН" not in art37[0].text
    md = ("**Чл. 5.** Първа алинея.\n\n"
          "(ОБН. - ДВ, БР. 2 ОТ 1950 Г.)\n")
    rows2 = parse(md, law_id="x")
    art5 = [r for r in rows2 if r.article == "5"]
    assert "ОБН" not in art5[0].text


def test_digit_tochki_continue_the_open_article():
    """Modern acts: точки arrive as their own paragraphs post-Task-1;
    they must stay in the article body and inside the right alinea."""
    md = ("**Чл. 12.** (1) Изисквания:\n\n"
          "1. първо изискване;\n\n"
          "2. второ изискване.\n\n"
          "(2) Втора алинея.\n")
    rows = parse(md, law_id="x")
    whole = [r for r in rows if r.article == "12" and r.paragraph is None]
    assert "второ изискване" in whole[0].text
    al1 = [r for r in rows if r.article == "12" and r.paragraph == "1"]
    assert "второ изискване" in al1[0].text and al1[0].implicit is False


def test_letter_points_merge_into_preceding_implicit_alinea():
    md = ("**Чл. 363.** Дружеството се прекратява:\n\n"
          "а) с постигане целта на дружеството;\n\n"
          "б) с изтичането на времето.\n\n"
          "Втора алинея след буквите.\n")
    rows = parse(md, law_id="zzd")
    alineas = [r for r in rows if r.article == "363" and r.paragraph is not None]
    assert [r.paragraph for r in alineas] == ["1", "2"]
    assert "б) с изтичането" in alineas[0].text
    assert alineas[1].text.startswith("Втора алинея")


def test_numbered_articles_unchanged_and_not_implicit():
    md = "**Чл. 1.** (1) Първа. (2) Втора.\n"
    rows = parse(md, law_id="x")
    alineas = [r for r in rows if r.paragraph is not None]
    assert [(r.paragraph, r.implicit) for r in alineas] == [("1", False), ("2", False)]


def test_annex_start_closes_the_open_article():
    """FR-034 rule 1: without an annex closer, default-continue swallows
    appendix forms into the last open article (measured: ППЗ-акцизи
    чл. 102б absorbed 86,503 chars of annexes)."""
    md = ("**Чл. 102б.** (1) Подлежащите на контрол лица са длъжни да съдействат.\n\n"
          "Приложение № 28 към чл. 102б\n\n"
          "ОБЯСНИТЕЛНИ БЕЛЕЖКИ по образеца на декларацията.\n")
    rows = parse(md, law_id="ppz")
    whole = [r for r in rows if r.article == "102б" and r.paragraph is None]
    assert len(whole) == 1
    assert "Приложение" not in whole[0].text
    assert "ОБЯСНИТЕЛНИ" not in whole[0].text


def test_uppercase_annex_start_also_closes():
    md = ("**Чл. 7.** Разпоредба.\n\n"
          "ПРИЛОЖЕНИЕ към чл. 7\n\n"
          "Образец на декларация.\n")
    rows = parse(md, law_id="x")
    whole = [r for r in rows if r.article == "7" and r.paragraph is None]
    assert "ПРИЛОЖЕНИЕ" not in whole[0].text and "Образец" not in whole[0].text


def test_zzd_fixture_unnumbered_alineas_are_implicit_and_correct():
    """FR-034 rule 6 spot-assert against a REAL pre-Указ-883 act.

    ЗЗД carries no `(N)` markers at all, yet ВКС cites its алинеи by
    position („чл. 36, ал. 2 ЗЗД"). This pins the end-to-end behaviour
    the whole FR exists for: HTML -> Markdown -> position-derived rows.
    """
    from bs4 import BeautifulSoup
    from fetcher.bg.text_parser import HtmlToMarkdown

    fixture = pathlib.Path(__file__).parent.parent / "fixtures" / "html" / "zzd.html"
    md = HtmlToMarkdown().convert(
        BeautifulSoup(fixture.read_bytes().decode("cp1251"), "lxml")
    )
    rows = parse(md, law_id="zzd")

    # No source-numbered alineas anywhere in a pre-1974 act.
    assert [r for r in rows if r.paragraph is not None and not r.implicit] == []

    art36 = [r for r in rows if r.article == "36"]
    alineas = [r for r in art36 if r.paragraph is not None]
    assert [(r.paragraph, r.implicit) for r in alineas] == [("1", True), ("2", True)]
    # ал. 1 has the anchor stripped; ал. 2 is the second unnumbered алинея.
    assert alineas[0].text.startswith("Едно лице може да представлява")
    assert alineas[1].text.startswith("Последиците")
