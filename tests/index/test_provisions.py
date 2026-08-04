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


# --- FR-034 sweep run 2, anomaly B2: bullets are not PreHistory italics ---

# Shape lifted verbatim (abridged) from
# `naredba-na-velikotarnovskiya-obshtinski-savet-za-upravlenie-stopanisvane-i-polzv-2`
# чл. 6: ал. 5 introduces a bullet list, ал. 6 and ал. 7 follow it. The
# `*` closer used to end the article at the first bullet and strand both.
VELIKO_TARNOVO_MD = """\
**Чл. 6.** (1) Земеделските земи от ОПФ се управляват в интерес на населението.

(5) (Нова - Решение № 1086) Земите могат да се отдават под наем без търг или конкурс:

* когато са заети с трайни насаждения;

* когато не са били използвани две или повече стопански години;

(6) (Нова - Решение № 1086) Общинският съвет определя маломерни имоти.

(7) (Предишна ал. 4) В договорите за наем се предвижда увеличаване на наемната цена.
"""


def test_bullet_paragraph_continues_the_open_article():
    """FR-034 sweep run 2, anomaly B2: a `* …` bullet is source text, not a
    PreHistory italics block. Treating it as a closer stranded every алинея
    that followed it (measured corpus-wide: 9 acts, 40 stranded paragraphs)."""
    rows = parse(VELIKO_TARNOVO_MD, law_id="vt")
    whole = [r for r in rows if r.article == "6" and r.paragraph is None]
    assert len(whole) == 1
    assert "трайни насаждения" in whole[0].text
    alineas = [r for r in rows if r.article == "6" and r.paragraph is not None]
    assert [r.paragraph for r in alineas] == ["1", "5", "6", "7"]
    assert "маломерни имоти" in [r for r in alineas if r.paragraph == "6"][0].text
    assert all(r.implicit is False for r in alineas)


def test_asterisk_footnote_paragraph_continues_the_open_article():
    """Table footnotes marked `*X`, `** X`, `*** X` are source text too —
    the same B2 class (naredba-14/2012 letishta, naredba-rd-02-20-2/2012)."""
    md = ("**Чл. 9.** (1) Стойностите са дадени в таблица 3.\n\n"
          "*Забележка. Конструкции, които могат да бъдат демонтирани.\n\n"
          "** За точна оценка може да се използва динамичен анализ.\n\n"
          "(2) Втора алинея след забележките.\n")
    rows = parse(md, law_id="x")
    whole = [r for r in rows if r.article == "9" and r.paragraph is None]
    assert "Забележка" in whole[0].text and "динамичен анализ" in whole[0].text
    alineas = [r for r in rows if r.article == "9" and r.paragraph is not None]
    assert [r.paragraph for r in alineas] == ["1", "2"]
    assert alineas[1].text.startswith("Втора алинея")


def test_bullets_merge_into_preceding_implicit_alinea():
    """A bullet subdivides an алинея, it does not start one — same rule as
    букви/точки. Without this the newly-admitted bullets would renumber the
    implicit алинеи of marker-less (pre-Указ-883) articles."""
    md = ("**Чл. 41.** Дружеството се прекратява в следните случаи:\n\n"
          "* с постигане целта на дружеството;\n\n"
          "* с изтичането на времето.\n\n"
          "Втора алинея след изброяването.\n")
    rows = parse(md, law_id="zzd")
    alineas = [r for r in rows if r.article == "41" and r.paragraph is not None]
    assert [(r.paragraph, r.implicit) for r in alineas] == [("1", True), ("2", True)]
    assert "с изтичането на времето" in alineas[0].text
    assert alineas[1].text.startswith("Втора алинея")


def test_prehistory_italics_still_closes_the_article():
    """The narrowing must not regress the closer it was written for: a
    whole-line `*…*` italics block (text_parser emits PreHistory as
    `*{text}*`) still ends the open article."""
    md = ("**Чл. 3.** Официалният език в републиката е българският.\n\n"
          "*В сила от 13.07.1991 г.*\n\n"
          "Текст извън члена.\n")
    rows = parse(md, law_id="x")
    whole = [r for r in rows if r.article == "3" and r.paragraph is None]
    assert len(whole) == 1
    assert "В сила от" not in whole[0].text
    assert "Текст извън члена" not in whole[0].text


def test_bold_edict_paragraph_still_closes_the_article():
    """`**§ N.**` provisions are parser-emitted bold (text_parser
    `_format_edict_article`) and must keep closing the preceding article —
    1,667 such paragraphs are reachable with an article open."""
    md = ("**Чл. 11.** Изпълнението се възлага на министъра на финансите.\n\n"
          "**§ 5.** В Закона за митниците се правят следните допълнения:\n\n"
          "(1) Цитиран текст от изменението.\n")
    rows = parse(md, law_id="x")
    whole = [r for r in rows if r.article == "11" and r.paragraph is None]
    assert len(whole) == 1
    assert "§ 5" not in whole[0].text
    assert "Цитиран текст" not in whole[0].text
    assert [r for r in rows if r.article == "11" and r.paragraph is not None] == []


def test_zzd_fixture_unnumbered_alineas_are_implicit_and_correct():
    """FR-034 rule 6 spot-assert against a REAL pre-Указ-883 act.

    ЗЗД carries no `(N)` markers at all, yet ВКС cites its алинеи by
    position („чл. 36, ал. 2 ЗЗД“). This pins the end-to-end behaviour
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


# --- FR-034 Task 6c-d: subpoint, header and sentence-continuation rules ---
# Every shape below is lifted from a real corpus row sampled in
# `docs/research/2026-08-02-fr034-sweep-report.md` §9 (row ids S01–S31).


def test_multi_letter_subpoint_merges_into_preceding_implicit_alinea():
    """§9.1c shape 1 (271 rows): ЗАДС чл. 4 / наредба 11/2003 чл. 10 number
    their букви `аа) бб) вв)` once the single letters run out. `_SUBPOINT_RE`
    knew only the single-letter form, so each one started a new алинея."""
    md = ("**Чл. 4.** По смисъла на този закон:\n\n"
          "я) последната еднобуквена точка;\n\n"
          "аа) за Германия: Остров Хелиголанд;\n\n"
          "бб) за Италия: Ливиньо;\n\n"
          "ввв) за трибуквения вариант;\n\n"
          "Втора алинея след изброяването.\n")
    rows = parse(md, law_id="zads")
    alineas = [r for r in rows if r.article == "4" and r.paragraph is not None]
    assert [(r.paragraph, r.implicit) for r in alineas] == [("1", True), ("2", True)]
    assert "Остров Хелиголанд" in alineas[0].text
    assert "трибуквения вариант" in alineas[0].text
    assert alineas[1].text.startswith("Втора алинея")


def test_multi_level_decimal_subpoint_merges_into_preceding_implicit_alinea():
    """§9.1c shape 2 (304 rows): правилник СОС чл. 16 numbers its subpoints
    `1.1. 1.2. 1.3.`, наредба 3/2004 goes as deep as `2.3.1.2.5.`."""
    md = ("**Чл. 16.** Председателят на СВСУ:\n\n"
          "1.1. свиква заседанията;\n\n"
          "1.3. представлява СВСУ;\n\n"
          "2.3.1.2.5. Ако спирачките са в изправност, се допуска работа.\n\n"
          "Втора алинея след изброяването.\n")
    rows = parse(md, law_id="sos")
    alineas = [r for r in rows if r.article == "16" and r.paragraph is not None]
    assert [(r.paragraph, r.implicit) for r in alineas] == [("1", True), ("2", True)]
    assert "представлява СВСУ" in alineas[0].text
    assert "Ако спирачките" in alineas[0].text
    assert alineas[1].text.startswith("Втора алинея")


def test_dash_bullet_merges_into_preceding_implicit_alinea():
    """§9.1c shape 3 (515 rows): правилник СОС (обществен посредник) чл. 29
    bullets its grounds with `- …`. Includes the en/em-dash variants."""
    md = ("**Чл. 29.** Мандатът се прекратява предсрочно:\n\n"
          "- за нарушаване на този правилник;\n\n"
          "– при трайна невъзможност да изпълнява задълженията си;\n\n"
          "— по негово искане.\n\n"
          "Втора алинея след изброяването.\n")
    rows = parse(md, law_id="sos")
    alineas = [r for r in rows if r.article == "29" and r.paragraph is not None]
    assert [(r.paragraph, r.implicit) for r in alineas] == [("1", True), ("2", True)]
    assert "по негово искане" in alineas[0].text
    assert alineas[1].text.startswith("Втора алинея")


def test_plain_text_section_header_closes_the_article():
    """§9.1c shape 6: „Допълнителна разпоредба“ in the SINGULAR is not
    emitted as a `##` header by text_parser, so the article stayed open and
    swallowed it as an алинея (ЗОТ чл. 106 ал. 2, правилник ВГС чл. 33 ал. 2,
    ЗСП чл. 140 ал. 2/3/5)."""
    md = ("**Чл. 106.** Контролът се осъществява от министъра.\n\n"
          "Допълнителна разпоредба\n\n"
          "§ 1. По смисъла на този закон:\n")
    rows = parse(md, law_id="zot")
    whole = [r for r in rows if r.article == "106" and r.paragraph is None]
    assert len(whole) == 1
    assert "Допълнителна разпоредба" not in whole[0].text
    assert "По смисъла" not in whole[0].text
    assert [r for r in rows if r.article == "106" and r.paragraph is not None] == []


def test_section_header_closer_variants():
    """The plural, the all-caps and the „Преходни наредби:“ form are the other
    51 reachable header paragraphs measured corpus-wide."""
    for header in ("Допълнителни разпоредби", "Заключителна разпоредба",
                   "ЗАКЛЮЧИТЕЛНИ РАЗПОРЕДБИ", "Преходни и Заключителни разпоредби",
                   "Преходни наредби:"):
        md = f"**Чл. 5.** Основен текст.\n\n{header}\n\nСлед заглавието.\n"
        whole = [r for r in parse(md, law_id="x")
                 if r.article == "5" and r.paragraph is None]
        assert header not in whole[0].text, header
        assert "След заглавието" not in whole[0].text, header


def test_section_header_closer_does_not_fire_on_ordinary_prose():
    """Guard: the closer must match a WHOLE header paragraph, not the prefix
    „Допълнителн…“. These three shapes are real corpus rows that a loose
    prefix pattern would wrongly treat as headers (наредба 14/2012 чл. 679,
    наредба 10/2011 чл. 28, правилник за безопасност чл. 182)."""
    for prose in ("Допълнителни огнегасящи вещества",
                  "Допълнителна информация, по преценка на организацията.",
                  "Допълнителни електро-"):
        md = f"**Чл. 7.** Първа алинея.\n\n{prose}\n\nТрета алинея.\n"
        whole = [r for r in parse(md, law_id="x")
                 if r.article == "7" and r.paragraph is None]
        assert prose in whole[0].text, prose


def test_annex_kam_start_closes_the_article():
    """§9.1c shape 4: „Приложение към чл. 5“ carries no `№`, so the annex
    closer did not fire and the form was absorbed as алинеи (S04 —
    наредба за формата…информация чл. 11, наредба Н-1/2025 чл. 16,
    правилник ЦПО чл. 16). 10 such paragraphs are reachable corpus-wide."""
    for header in ("Приложение към чл. 5", "Приложение към чл. 3, ал. 3",
                   "Приложение към споразумение за сътрудничество"):
        md = (f"**Чл. 11.** Отчетът се изготвя по образец.\n\n{header}\n\n"
              "СПРАВКА за състоянието на системите\n\nв ……\n")
        whole = [r for r in parse(md, law_id="x")
                 if r.article == "11" and r.paragraph is None]
        assert header not in whole[0].text, header
        assert "СПРАВКА" not in whole[0].text, header


def test_annex_citation_does_not_close_the_article():
    """Guard: „Приложение II, Регламент (ЕС) 2021/1165“ is a CITATION, not an
    annex start — the closer keys on „към“, not on a bare „Приложение“."""
    md = ("**Чл. 39.** Продуктите се вписват съгласно правилата.\n\n"
          "Приложение II, Регламент (ЕС) 2021/1165\n\n"
          "Втора алинея.\n")
    whole = [r for r in parse(md, law_id="x")
             if r.article == "39" and r.paragraph is None]
    assert "Регламент (ЕС) 2021/1165" in whole[0].text


# Abridged verbatim from `nakazatelen-kodeks` чл. 418 (sample row S24). The
# article carries NO алинеи; the lead ends in a colon, the четири букви are
# merged by `_SUBPOINT_RE`, and the tail „се наказва с…“ used to become a
# manufactured „ал. 2“.
NK_418_MD = """\
**Чл. 418.** (Нов - ДВ, бр. 95 от 1975 г.) Който с целта по предходния член:

а) незаконно лиши от свобода членове на расова група хора;

г) отнема основни права и свободи на организации или лица, понеже те се противопоставят на апартейда,

се наказва с лишаване от свобода от пет до петнадесет години.
"""


def test_sentence_tail_does_not_become_a_separate_implicit_alinea():
    """§9.3 class 5 (S24 НК чл. 418, S10 ЗГМО чл. 2а): one sentence cut into
    two rows. An алинея is a sentence and a Bulgarian sentence opens with a
    capital or a marker — a paragraph opening with a LOWERCASE Cyrillic letter
    is therefore a continuation of the paragraph above it, never a new алинея.
    чл. 418 has no алинеи at all, so it must emit none."""
    rows = parse(NK_418_MD, law_id="nk")
    alineas = [r for r in rows if r.article == "418" and r.paragraph is not None]
    assert alineas == []
    whole = [r for r in rows if r.article == "418" and r.paragraph is None]
    assert "се наказва с лишаване от свобода" in whole[0].text


def test_lowercase_continuation_merges_after_an_unpunctuated_lead():
    """S20 (УП МТСП чл. 24): the source breaks буква „ж)“ mid-clause after the
    word „съгласно“ — no terminal punctuation at all. A rule keyed on the
    PREVIOUS paragraph's punctuation misses this; the lowercase-opening rule
    does not."""
    md = ("**Чл. 24.** Дирекцията подпомага министъра при:\n\n"
          "ж) осигурява съхранението на финансово-счетоводните документи съгласно\n\n"
          "изискванията на Закона за счетоводството и действащите нормативни актове;\n\n"
          "Втора алинея.\n")
    rows = parse(md, law_id="mtsp")
    alineas = [r for r in rows if r.article == "24" and r.paragraph is not None]
    assert [(r.paragraph, r.implicit) for r in alineas] == [("1", True), ("2", True)]
    assert "изискванията на Закона за счетоводството" in alineas[0].text
    assert alineas[1].text.startswith("Втора алинея")


def test_capitalised_paragraph_still_starts_a_new_implicit_alinea():
    """Guard against over-merging: the continuation rule keys on a lowercase
    OPENING only. Real алинеи — capitals, „(Изм. …)“ prefixes, digits, quoted
    text — must keep starting their own row."""
    md = ("**Чл. 30.** Първа алинея.\n\n"
          "Втора алинея с главна буква.\n\n"
          "(Изм. - ДВ, бр. 12 от 1993 г.) Трета алинея.\n\n"
          "„Цитиран текст в кавички.\"\n")
    rows = parse(md, law_id="x")
    alineas = [r for r in rows if r.article == "30" and r.paragraph is not None]
    assert [r.paragraph for r in alineas] == ["1", "2", "3", "4"]


# Verbatim from `zakon-za-zadalzheniyata-i-dogovorite` чл. 265 — the доктринален
# target. The lead ends in a colon and its two enumeration items carry NO
# marker at all, so they were numbered as ал. 2 and ал. 3 and pushed the two
# real алинеи to ал. 4 and ал. 5.
ZZD_265_MD = """\
**Чл. 265.** Ако при извършване на работата изпълнителят се е отклонил от поръчката или ако изпълнената работа има недостатъци, поръчващият може да иска:

поправяне на работата в даден от него подходящ срок без заплащане;

заплащане на разходите, необходими за поправката, или съответно намаление на възнаграждението.

Ако отклонението от поръчката или недостатъците са толкова съществени, че работата е негодна за нейното договорно или обикновено предназначение, поръчващият може да развали договора.

Тия права се погасяват в шест месеца, а при строителни работи - в пет години.
"""


def test_zzd_265_unmarked_enumeration_does_not_shift_the_alinea_numbering():
    """The doctrinal payoff: ЗЗД чл. 265 has three алинеи, and the six-month /
    five-year prescription is ал. 3. The unmarked enumeration items are
    grammatical completions of „поръчващият може да иска: …“, not алинеи."""
    rows = parse(ZZD_265_MD, law_id="zzd")
    alineas = [r for r in rows if r.article == "265" and r.paragraph is not None]
    assert [r.paragraph for r in alineas] == ["1", "2", "3"]
    assert "поправяне на работата" in alineas[0].text
    assert alineas[1].text.startswith("Ако отклонението")
    assert alineas[2].text.startswith("Тия права се погасяват")


def test_amendment_marker_does_not_mask_a_sentence_continuation():
    """НК чл. 410/411/412/417 carry the same split-sentence shape as чл. 418,
    but their tail opens with a `(изм. - ДВ …)` marker, which masked the
    lowercase letter behind it. The continuation rule therefore looks PAST a
    leading parenthetical. Measured: 17 rows corpus-wide, all artifacts
    (4 НК war-crimes articles, the rest formula legends and form labels);
    zero genuine алинеи."""
    md = ("**Чл. 410.** Който в нарушение на правилата за водене на война:\n\n"
          "а) извърши убийство спрямо ранени или болни;\n\n"
          "(изм. - ДВ, бр. 153 от 1998 г.) се наказва с лишаване от свобода "
          "от пет до двадесет години.\n")
    rows = parse(md, law_id="nk")
    assert [r for r in rows if r.article == "410" and r.paragraph is not None] == []


def test_amendment_marker_before_a_capital_still_starts_an_alinea():
    """Guard: the parenthetical is skipped only to read the letter behind it.
    „(Изм. …) Трета алинея.“ opens with a CAPITAL and keeps its own row."""
    md = ("**Чл. 30.** Първа алинея.\n\n"
          "(Изм. - ДВ, бр. 12 от 1993 г.) Втора алинея.\n\n"
          "(Нова - ДВ, бр. 8 от 2001 г.) Трета алинея.\n")
    rows = parse(md, law_id="x")
    alineas = [r for r in rows if r.article == "30" and r.paragraph is not None]
    assert [r.paragraph for r in alineas] == ["1", "2", "3"]


def test_subpoint_re_matches_bukva_shapes_in_isolation():
    """`_SUBPOINT_RE`'s буква branch is currently subsumed by
    `_CONTINUATION_RE` (a bare lowercase Cyrillic opening already merges
    every `а)` / `аа)` / `ввв)` paragraph), so no behavioural test can
    isolate it — deleting the branch leaves all 3,624 corpus files parsing
    identically. It is kept as defence in depth against a later narrowing of
    `_CONTINUATION_RE`, and this test pins it directly so that narrowing
    cannot silently take буква handling with it."""
    from index.provisions import _SUBPOINT_RE
    for shape in ("а) текст", "я) текст", "аа) текст", "бб) текст", "ввв) текст"):
        assert _SUBPOINT_RE.match(shape), shape
    # Not sub-points: a capitalised opening, and a буква with no separator.
    assert not _SUBPOINT_RE.match("А) текст")
    assert not _SUBPOINT_RE.match("абвг) текст")
