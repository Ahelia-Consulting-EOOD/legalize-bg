"""Markdown-body → provisions rows extractor.

Walks the Markdown produced by `fetcher.bg.text_parser.HtmlToMarkdown` and
emits article-level rows AND alinea-level rows. Per D-023, both `text` and
`text_hash` columns are populated; `paragraph` is NULL for the
article-as-a-whole row, set to '1', '2', ... for each alinea.

Article anchors look like '**Чл. N.**' or '**Чл. Nа.**' (Cyrillic suffixes).
Alineas are paragraph blocks starting with '(N)' — Phase 1a's text_parser
emits each alinea as its own paragraph.

Phase 1b.1 Task 4: article-level only. Task 5 extends with alinea splitting.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass


# Article anchor: capitalized "Чл. N." or "Чл. Nа.". Capitalized Ч is the
# Bulgarian convention for article-anchor; lowercase "чл." is for inline
# references and is intentionally NOT matched here. The plan's draft
# required bold formatting (`**Чл. N.**`), but the existing text_parser
# only bolds anchors whose Article-class element starts with "Чл." —
# articles that have a title preamble (very common in ЗОП/ГПК/ЗЕУ) are
# emitted as plain "Title preamble Чл. N. ..." inside one paragraph.
# Matching capitalized "Чл. N." regardless of bold catches both forms.
_ARTICLE_RE = re.compile(
    r"(?:\*\*)?Чл\.\s+(\d+[а-я]?)\.?(?:\*\*)?",
)

_PARAGRAPH_SPLIT_RE = re.compile(r"\n\n+")


@dataclass(frozen=True)
class Provision:
    """One provisions-table row.

    Note: no `valid_from` field. The SQLite `provisions` table requires
    valid_from (NOT NULL); the index builder pairs each Provision with
    the law's effective_date at insertion time (see `index.build`). This
    keeps the parse step temporally agnostic — the same Markdown body
    yields the same Provisions whether we're indexing HEAD or a past
    commit; only the writer knows the validity interval.
    """

    law_id: str
    article: str
    paragraph: str | None
    text: str
    text_hash: str
    implicit: bool = False


def _hash(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()[:16]


def _is_structural_header(para: str) -> bool:
    """Markdown structural headers: '#', '## ПРЕХОДНИ…', etc. They never
    introduce articles; skip them in extraction."""
    return para.startswith("#")


# FR-034: after the Task-1 parser fix, article content that lex.bg
# renders as child <div>s — unnumbered алинеи (pre-Указ-883 acts),
# точки ("1."), букви ("а)"), "(Изм. …)"-prefixed алинеи — arrives as
# separate plain paragraphs. While an article is open, everything
# continues it EXCEPT the named closers: '#' structural headers,
# parser-emitted emphasis (see below), standalone '(ОБН' gazette
# banners, and annex starts ('Приложение № …' / 'ПРИЛОЖЕНИЕ'). Without
# the annex closer default-continue swallows appendix forms into the
# last open article — measured: ППЗ-акцизи чл. 102б absorbed 86,503
# chars of annexes. Default-continue restores pre-FR-034 article-body
# parity (measured on ЗОП: the Cyrillic-only alternative lost 60% of
# indexed article text). High-recall by design (D-055 lesson) —
# corpus-wide validation via the structural gate + fr034_verify
# rebuild-diff.
#
# THE EMPHASIS CLOSER (FR-034 sweep run 2, anomaly B2). The rule was
# once a bare '^\*': any leading asterisk closed the article, on the
# assumption that it was a PreHistory italics block. It is not. Only
# TWO leading-asterisk forms are emitted by `fetcher.bg.text_parser`
# itself — `*{text}*` for `.PreHistory` and `**§ N.**` / `**Чл. N.**`
# bold anchors — and both are CLOSED emphasis spans. Every other
# leading asterisk is verbatim source text: bullets ("* когато са
# заети…"), footnote markers ("*Забележка…", "** За точна оценка…",
# "*** - група Б"), and table-cell asterisks. Those are article
# content, and closing on them stranded every алинея that followed —
# measured: 9 acts, 40 stranded алинея paragraphs, the clearest being
# Наредба на Великотърновския общински съвет … чл. 6, whose ал. 6–7
# fell out of the index after ал. 5's bullet list (R1 47 → 45).
# So: close only on a COMPLETE emphasis span at the paragraph start —
# '**…**' bold, or a whole-line '*…*' italic.
# Corpus evidence for the split (3,624 acts, paragraph-level):
#   '**…'  bold-leading        157,510 total · 1,667 reachable with an
#                              article open — the '**§ N.**' ЗИД
#                              provisions the closer must keep closing;
#   '*…*'  wrapped italics       4,961 total · 0 (zero) occurrences
#                              after the first article anchor — genuine
#                              PreHistory only ever sits in the
#                              preamble, so this branch is a safety net,
#                              not a working closer;
#   '* …'  bullets               1,294 total · 42 reachable → B2;
#   '*X…'  footnote markers        468 total · 48 reachable → B2;
#   '*'    bare asterisk cells     687 total ·  8 reachable → B2.
# Effect of the narrowing, measured over the whole corpus: 24 acts
# change, explicit алинея rows 309,906 → 310,003 (+97, zero acts lose
# any), implicit rows 23,747 → 24,340, article text +92,675 chars
# (+0.07%). Rejected alternatives, same measurement: '\*(?!\s)' (only
# '* ' bullets continue) covers 7 of the 9 B2 acts; '\*(?!\**\s)'
# (asterisk RUN + space) also 7 of 9; treating every '**' as a closer
# covers 8 of 9 — only the complete-span rule below covers all nine.
#
# THE PLAIN-TEXT CLOSERS (FR-034 Task 6c-d; sweep report §9.1c/§9.3.4).
# Two closers were keyed too narrowly and let non-article material be
# swallowed as алинеи:
#
#   * SECTION HEADERS. lex.bg emits „Допълнителни разпоредби“ in the
#     PLURAL as a `##` heading, but the SINGULAR „Допълнителна
#     разпоредба“ arrives as an ordinary paragraph, so the article
#     stayed open and absorbed it (measured: 31 implicit rows by the
#     report's loose prefix pattern). The prefix alone over-matches —
#     of those 31 rows only 19 are headers; the rest are table cells
#     („Допълнителни огнегасящи вещества“, „Допълнителни електро-“,
#     „Допълнителна информация, по преценка на организацията“). So the
#     branch below requires the WHOLE paragraph to be
#     „{Допълнителн|Преходн|Заключителн}… [и …] {разпоредб|наредб}…“
#     with an optional trailing colon. Measured corpus-wide over 3,624
#     acts: 140 such paragraphs, 51 of them reachable with an article
#     open, and all 51 are genuine headers — „Допълнителна разпоредба“
#     ×32, „Заключителна разпоредба“ ×13, „Преходни наредби:“ ×2,
#     „Допълнителни разпоредби“, „Преходни и Заключителни разпоредби“,
#     „ДОПЪЛНИТЕЛНИ РАЗПОРЕДБИ“, „ЗАКЛЮЧИТЕЛНИ РАЗПОРЕДБИ“ ×1 each.
#     Zero false positives.
#
#   * ANNEXES WITHOUT A NUMBER. „Приложение № 3“ closed the article but
#     „Приложение към чл. 5“ did not, so the annexed form was indexed as
#     алинеи of the last article (sample row S04). The key is „към“, NOT
#     a bare „Приложение“: that prefix also opens the citation
#     „Приложение II, Регламент (ЕС) 2021/1165“ and the noun form
#     „Приложението по ал. 1 …“. Measured: 931 „Приложение към …“
#     paragraphs corpus-wide, 10 of them reachable with an article open,
#     all 10 genuine annex starts.
_CONTINUATION_CLOSER_RE = re.compile(
    r"^(?:"
    r"#"                        # structural header
    r"|\*\*[^*\n]+\*\*"         # parser-emitted bold: '**§ 5.**', '**Чл. 1.**'
    r"|\*[^*\s][^*\n]*\*\s*$"   # parser-emitted PreHistory italics: '*В сила от …*'
    r"|\(ОБН"                   # gazette banner
    r"|Приложение\s*№|ПРИЛОЖЕНИЕ"  # annex start, numbered / all-caps
    r"|Приложение\s+към\b"      # annex start, „Приложение към чл. 5“ (§9.1c)
    r"|(?:Допълнителн|ДОПЪЛНИТЕЛН|Преходн|ПРЕХОДН|Заключителн|ЗАКЛЮЧИТЕЛН)\S*"
    r"(?:\s+и\s+\S+)?\s+(?:разпоредб|РАЗПОРЕДБ|наредб|НАРЕДБ)\S*\s*:?\s*$"
    r")"
)


def _extract_article_blocks(markdown: str) -> list[tuple[str, str]]:
    """Return list of (article_id, body_text).

    Each Article-class HTML element produces one paragraph in the
    markdown when alineas are inline (e.g., "Чл. 1. (1) X. (2) Y."),
    or multiple paragraphs when alineas are separated by \\n\\n (the
    Phase 1a I7 fix path). This extractor merges alinea-continuation
    paragraphs back onto their parent article so `_split_alineas` can
    find all (N) markers regardless of source layout.

    Acceptance rules per paragraph (FR-034: DEFAULT-CONTINUE — lex.bg
    renders точки, букви and unnumbered алинеи as child <div>s, so an
    article's own text arrives as many plain paragraphs; the previous
    "continue only on (N)" rule discarded all of them and dropped 60% of
    ЗОП's indexed article text):
      - 0 anchors, article open, paragraph is not a closer: append to the
        current article body.
      - 0 anchors and the paragraph IS a closer — '#' structural header,
        a complete parser-emitted emphasis span ('**§ N.**' bold or a
        whole-line '*…*' PreHistory italic), '(ОБН' gazette banner, or an
        annex start ('Приложение № …' / 'ПРИЛОЖЕНИЕ') — flush pending and
        discard. A leading asterisk that is NOT a closed emphasis span is
        source text (bullet, footnote marker) and continues the article —
        FR-034 sweep run 2, anomaly B2. See `_CONTINUATION_CLOSER_RE`.
      - 0 anchors with no article open: discard (preamble, narrative).
      - 1 anchor: flush pending and start a new article.
      - 2+ anchors: cite-list or template (e.g., a декларация template
        citing "Чл. 102а и Чл. 102б"). Flush pending and skip — never
        emit a row for paragraphs with multiple anchors.

    Phase 4 amendment-detection will need a separate
    `body_text_minus_preamble` projection (the article-as-whole text
    here intentionally includes the title preamble + anchor for Phase
    1b.1 search/get_article use). Tracked as FR-012 in
    `docs/frs/INDEX.md`.
    """
    blocks: list[tuple[str, str]] = []
    pending_id: str | None = None
    pending_parts: list[str] = []

    def flush() -> None:
        nonlocal pending_id, pending_parts
        if pending_id is not None:
            blocks.append((pending_id, "\n\n".join(pending_parts)))
            pending_id = None
            pending_parts = []

    for raw_para in _PARAGRAPH_SPLIT_RE.split(markdown):
        para = raw_para.strip()
        if not para or _is_structural_header(para):
            flush()
            continue
        article_ids = _ARTICLE_RE.findall(para)
        n = len(article_ids)
        if n == 1:
            flush()
            pending_id = article_ids[0]
            pending_parts = [para]
        elif n == 0:
            if pending_id is not None and not _CONTINUATION_CLOSER_RE.match(para):
                pending_parts.append(para)
            else:
                flush()
        else:  # n >= 2
            flush()
    flush()
    return blocks


# Alinea boundary inside an article body: "(N)" or "(Nа)" (Cyrillic
# suffix variants). Real corpus articles pack alineas EITHER inline
# inside a single paragraph (e.g., "Чл. 1. (1) X. (2) Y. (3) Z.") OR
# across paragraph breaks (after the post–code-review fix in Phase 1a's
# I7). Both cases share the "(N)" marker, so we split on the marker
# itself, not on \n\n.
#
# The capture group is `\d+[а-я]?` only — parenthetical references like
# "(вж. чл. 2)" or "(в сила от 01.01.2025 г.)" do not match because
# their content is not purely digits. The reviewer's flagged scenario
# (`Чл. 14 (вж. чл. 2) текст…` producing a bogus paragraph='2' row)
# is therefore not a real false-positive against this regex — but the
# scenario lock-test below pins this behavior.
#
# 1-3 digits only: no article has 1,000+ alineas, while parenthesised
# YEARS — "(1969)", "(2003)" — are always 4-digit and were the dominant
# false positive (P0-2, review 2026-07-02: 116 bogus paragraph rows in
# 22 live acts, truncating real alinea text). The digit cap alone fixes
# the whole corruption class with zero collateral loss.
#
# A letter-boundary heuristic (require the marker to follow a
# sentence/anchor punctuation char) was tried and rejected: it cannot
# distinguish a citation "(1969)" following a letter from a real "(4)"
# alinea whose preceding sentence lacks terminal punctuation (common
# after amendment-introduced alineas, e.g. "...управление (4) (Нова -
# ДВ, бр. 94 от 2019 г. ...)"). Review 2026-07-02 confirmed it silently
# dropped real alineas in 3 of 6 fixture acts (zop чл. 196, zeu чл. 5,
# ppz-aktsizi чл. 78) — both cases look identical to the heuristic.
_ALINEA_MARKER_RE = re.compile(r"\(\s*(\d{1,3}[а-я]?)\s*\)")


def _split_alineas(body: str) -> list[tuple[str, str]]:
    """Split an article body into (paragraph_id, text) pairs.
    Returns [] if the article has no '(N)' alinea markers.

    The text for each alinea spans from after the marker to the next
    marker (or end of body), with leading/trailing whitespace stripped.
    """
    matches = list(_ALINEA_MARKER_RE.finditer(body))
    if not matches:
        return []
    out: list[tuple[str, str]] = []
    for i, m in enumerate(matches):
        paragraph_id = m.group(1)
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(body)
        text = body[start:end].strip()
        # Strip leading punctuation/whitespace artifacts left by adjacent
        # markers (e.g., ". " between "(1) Първа." and "(2) Втора.")
        text = re.sub(r"^[\s\.,]+", "", text)
        out.append((paragraph_id, text))
    return out


# Sub-point markers: букви "а)" and точки "1." / "1)" — including the
# Cyrillic-suffixed forms lex.bg uses for inserted точки ("1а.", "4б.",
# "57д."). Missing the suffix variants made a точки list look like a run
# of unnumbered алинеи (measured: all 27 ППЗ-акцизи implicit rows came
# from чл. 85а alone, so "ал. 5" resolved to точка 10а).
# Asterisk bullets ("* когато са заети…") join the same set: they are
# sub-points of the алинея above them, never алинеи of their own. Before
# the FR-034 B2 narrowing of `_CONTINUATION_CLOSER_RE` no asterisk
# paragraph could reach an article body at all, so this alternative is a
# no-op for pre-B2 behaviour; without it the newly-admitted bullets would
# renumber the implicit алинеи of marker-less articles (measured: 19
# corpus rows).
#
# FR-034 Task 6c-d — three further sub-point shapes, each measured over
# the frame `implicit = 1 AND valid_to IS NULL` (24,340 rows) with the
# patterns shipped in sweep report §9.1c:
#   * MULTI-LETTER букви `аа) бб) вв)` — 271 rows by the report's count.
#     lex.bg continues a буква list past „я)“ by doubling (and
#     occasionally tripling) the letter; the old `[а-я]\)` matched only
#     the single-letter form.
#     NOTE for anyone reconciling the prose with the code: the report
#     calls these „doubled-letter“, but the pattern it shipped —
#     and the count of 271 — is the general two-to-three-letter form.
#     Truly doubled (`^([а-я])\1\)\s`) is only 256 rows. The general
#     form is authoritative; `{1,3}` below subsumes both it and the
#     original single letter.
#     ATTRIBUTION, measured (Task 6c-d review): this branch contributes
#     ZERO INCREMENTAL ROWS as the file currently stands, because
#     `_CONTINUATION_RE`'s bare `[а-я]` already matches every буква
#     paragraph — deleting the branch and re-parsing all 3,624 corpus
#     files yields the identical 21,043 implicit rows and 0 acts
#     differing. The 271 rows above are the SHAPE COUNT the report
#     measured, not this branch's marginal effect. It is retained
#     deliberately as defence in depth: if `_CONTINUATION_RE` is ever
#     narrowed (e.g. to the punctuation-gated V3 variant below), буква
#     handling must not vanish with it. `test_subpoint_re_matches_bukva_
#     shapes_in_isolation` pins the branch directly for that reason.
#   * MULTI-LEVEL DECIMAL точки `1.3.`, `2.3.1.2.5.` — 304 rows
#     (правилник СОС чл. 16, наредба 3/2004). The old `\d{1,2}[.)]`
#     stopped at the first dot, so `1.3.` was not a sub-point.
#     LATENT: unlike the old pattern this also matches a date-shaped
#     opener („2026.05.01 г.“). Zero such paragraph openers exist in the
#     corpus today, so it is not a live defect; if dated openers ever
#     appear, bound the first group (`\d{1,2}`) to exclude a year.
#   * DASH BULLETS `- …` (plus the en/em-dash variants) — 515 rows.
#     The report notes a 514↔515 wobble: `^- ` with a literal space
#     gives 514, `^-\s` gives 515 (the extra row is „-\n\n2. Детски
#     заведения“). The shipped `^[-–—]\s` is what is implemented.
# Union of the three = 1,090 rows; with the section headers above, 1,121.
_SUBPOINT_RE = re.compile(
    r"^(?:"
    r"[а-я]{1,3}\)"             # букви: 'а)' … 'я)', 'аа)', 'ввв)'
    r"|\d{1,2}[а-я]?[\.\)]"     # точки: '1.', '4б.', '10)'
    r"|\d+(?:\.\d+)+\.?"        # multi-level decimal: '1.3.', '2.3.1.2.5.'
    r"|[-–—]"                   # dash bullet
    r"|\*+"                     # asterisk bullet / footnote marker (B2)
    r")\s"
)

# FR-034 Task 6c-d — SENTENCE CONTINUATION (sweep report §9.3 class 5, the
# largest artifact class in the random sample: 5 of 24 rows).
#
# An алинея is a sentence, and a Bulgarian sentence opens with a capital
# letter or with a marker. A paragraph that opens with a LOWERCASE Cyrillic
# letter is therefore the continuation of the paragraph above it, never the
# start of a new алинея. The parser was manufacturing алинеи out of the two
# halves of one sentence: НК чл. 418 has no алинеи at all, yet the lead
# („Който с целта по предходния член:“) became ал. 1 and the tail („се
# наказва с лишаване от свобода от пет до петнадесет години.“) became ал. 2;
# same shape at НК чл. 341/356ж/356и and ЗГМО чл. 2а („при условие че…“).
#
# WHY THE BARE-LOWERCASE FORM AND NOT A PUNCTUATION-GATED ONE. Four rules
# were measured by re-running `_split_implicit_alineas` over every
# implicit-eligible article body in `catalog.db` (63,163 bodies):
#   baseline                                        24,340 rows
#   + the three sub-point gaps only                 23,156
#   + lowercase, gated on prev ending „:“           23,074  ← ЗЗД=460
#   + lowercase, gated on prev ending „:“, „,“ „;“  22,843  ← ЗЗД=459
#   + lowercase, ungated (adopted)                  21,149  ← ЗЗД=459
# The „:“-only gate is internally inconsistent — in ЗЗД чл. 265 it merges
# the first enumeration item but not the second, which follows a „;“.
# The „:,;“ gate and the ungated rule agree on every doctrinal act, and the
# tiebreak is COVERAGE of the measured defect set (the same criterion that
# settled the B2 narrowing): the gated rule covers sample rows S10 and S24
# but MISSES S20 (УП МТСП чл. 24, where the source breaks буква „ж)“
# mid-clause after the word „съгласно“ — no terminal punctuation at all).
# Only the ungated rule covers all three. Its extra 1,672 merges were
# audited: they fall in 89 table/form-heavy acts (наредба 3/2004 ×350,
# наредба 10/2011 ×253, наредба 1/2010 ×228 …), 86 % are under 40 chars,
# and all 15 sampled from the highest-risk band (>= 100 chars) are annex,
# form or table material — zero genuine алинеи. Sample row S21 (ППЗДвП
# чл. 66) is NOT covered by any of the four: its trailing sentence opens
# with a capital („Светлоотразяващият елемент…“) and is indistinguishable
# from a real алинея without semantics. Left to FR-026.
#
# Doctrinal effect, measured: ЗС 103 → 103, ЗЛС 44 → 44, ЗЗД 461 → 459.
# The two ЗЗД rows are чл. 265's unmarked enumeration items („поправяне на
# работата…“, „заплащане на разходите…“), which are grammatical completions
# of „поръчващият може да иска: …“, not алинеи. Merging them restores the
# citation-practice numbering: the six-month / five-year prescription is
# чл. 265, ал. 3 ЗЗД, not ал. 5.
#
# The optional leading parenthetical exists because an amendment marker can
# sit in front of the continuation and mask its lowercase opening: НК
# чл. 410/411/412/417 have exactly чл. 418's shape, but their tail reads
# „(изм. - ДВ, бр. 153 от 1998 г.) се наказва с …“. So the test is applied to
# the first letter AFTER any leading `(…)`. Measured: 17 rows corpus-wide
# match — 4 НК war-crimes articles plus formula legends („(Аф-ф)г = …,
# където а = f Sin a“), table cells and form-field labels — and none is a
# genuine алинея. The bound `{0,120}` and the `[^)\n]` class keep the scan
# inside one short parenthetical instead of running across a table cell.
# An алинея that genuinely opens with an amendment marker continues with a
# CAPITAL („(Изм. - ДВ …) Трета алинея.“) and is unaffected.
_CONTINUATION_RE = re.compile(r"^(?:\([^)\n]{0,120}\)\s*)?[а-я]")
# NOT ^-anchored on purpose — rule 1a glues a title preamble in front of
# the anchor, so ал. 1's text begins after the anchor MATCH END wherever
# that falls („Предмет Чл. 1. Този кодекс…“ -> „Този кодекс…“).
_ANCHOR_PREFIX_RE = re.compile(r"(?:\*\*)?Чл\.\s+\d+[а-я]?\.(?:\*\*)?\s*")


def _split_implicit_alineas(body: str) -> list[tuple[str, str]]:
    """Position-derived alineas for marker-less multi-paragraph articles
    (pre-Указ-883 acts: ЗЗД, ЗС, ЗН, ЗЛС…). ВКС cites their алинеи by
    paragraph position („чл. 36, ал. 2 ЗЗД“) even though the source text
    carries no (N) markers. Sub-points (букви а), б)… and точки 1., 2)…)
    merge into the preceding alinea — they subdivide an алинея, they do
    not start one.
    Returns [] for single-paragraph articles (no implicit ал. 1 row —
    mirrors numbered acts, where a marker-less article gets no rows).

    Task 6c-d: a paragraph opening with a lowercase Cyrillic letter is the
    continuation of the sentence above it and merges the same way — see
    `_CONTINUATION_RE`."""
    paras = [p.strip() for p in _PARAGRAPH_SPLIT_RE.split(body) if p.strip()]
    if len(paras) < 2:
        return []
    merged: list[str] = []
    for p in paras:
        if merged and (_SUBPOINT_RE.match(p) or _CONTINUATION_RE.match(p)):
            merged[-1] = merged[-1] + "\n\n" + p
        else:
            merged.append(p)
    if len(merged) < 2:
        return []
    out: list[tuple[str, str]] = []
    for i, text in enumerate(merged, start=1):
        if i == 1:
            # Strip everything up to and including the anchor, located by
            # SEARCH rather than a ^-anchored sub: rule 1a glues a title
            # preamble in front of the anchor, so a ^-anchored strip
            # silently no-ops and ал. 1 keeps „Предмет Чл. 1. …“.
            m = _ANCHOR_PREFIX_RE.search(text)
            if m:
                text = text[m.end():]
        out.append((str(i), text))
    return out


def parse(markdown: str, law_id: str) -> list[Provision]:
    """Emit one article-as-whole row + one row per alinea (D-023).

    Article-as-whole row: paragraph=None, text=full paragraph (preamble
    + anchor + alineas), text_hash over that whole text.

    Alinea rows: paragraph='1'/'2'/'1а'/..., text=just that alinea's
    text, text_hash over only that alinea — so single-alinea amendments
    (Phase 4) can be detected without re-hashing the article.
    """
    rows: list[Provision] = []
    for article_id, body in _extract_article_blocks(markdown):
        rows.append(Provision(
            law_id=law_id,
            article=article_id,
            paragraph=None,
            text=body,
            text_hash=_hash(body),
        ))
        explicit = _split_alineas(body)
        implicit_rows = [] if explicit else _split_implicit_alineas(body)
        for paragraph_id, alinea_text in explicit or implicit_rows:
            rows.append(Provision(
                law_id=law_id,
                article=article_id,
                paragraph=paragraph_id,
                text=alinea_text,
                text_hash=_hash(alinea_text),
                implicit=not explicit,
            ))
    return rows
