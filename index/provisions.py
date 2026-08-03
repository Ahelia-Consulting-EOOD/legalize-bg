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


_ALINEA_CONTINUATION_RE = re.compile(r"^\s*\(\s*\d{1,3}[а-я]?\s*\)")

# FR-034: after the Task-1 parser fix, article content that lex.bg
# renders as child <div>s — unnumbered алинеи (pre-Указ-883 acts),
# точки ("1."), букви ("а)"), "(Изм. …)"-prefixed алинеи — arrives as
# separate plain paragraphs. While an article is open, everything
# continues it EXCEPT the named closers: '#' structural headers,
# '*' PreHistory italics, standalone '(ОБН' gazette banners, and annex
# starts ('Приложение № …' / 'ПРИЛОЖЕНИЕ'). Without the annex closer
# default-continue swallows appendix forms into the last open article —
# measured: ППЗ-акцизи чл. 102б absorbed 86,503 chars of annexes.
# Default-continue restores pre-FR-034 article-body parity (measured on
# ЗОП: the Cyrillic-only alternative lost 60% of indexed article text).
# High-recall by design (D-055 lesson) — corpus-wide validation via the
# structural gate + fr034_verify rebuild-diff.
_CONTINUATION_CLOSER_RE = re.compile(r"^(?:#|\*|\(ОБН|Приложение\s*№|ПРИЛОЖЕНИЕ)")


def _looks_like_alinea_continuation(para: str) -> bool:
    """A paragraph starting with '(N)' is the continuation of the
    previous article — Phase 1a's text_parser separates alineas with
    \\n\\n when the source HTML has <br> between them (test_text_parser
    `test_preserves_paragraph_structure` enforces this), but inline
    alineas in a single paragraph are also common (most ЗОП articles).
    Both cases must be supported."""
    return bool(_ALINEA_CONTINUATION_RE.match(para))


def _extract_article_blocks(markdown: str) -> list[tuple[str, str]]:
    """Return list of (article_id, body_text).

    Each Article-class HTML element produces one paragraph in the
    markdown when alineas are inline (e.g., "Чл. 1. (1) X. (2) Y."),
    or multiple paragraphs when alineas are separated by \\n\\n (the
    Phase 1a I7 fix path). This extractor merges alinea-continuation
    paragraphs back onto their parent article so `_split_alineas` can
    find all (N) markers regardless of source layout.

    Acceptance rules per paragraph:
      - 0 anchors and looks like alinea continuation: append to current
        article body.
      - 0 anchors and not a continuation: flush pending article and
        discard the paragraph (preamble, narrative, etc.).
      - 1 anchor: flush pending and start a new article.
      - 2+ anchors: cite-list or template (e.g., a декларация template
        citing "Чл. 102а и Чл. 102б"). Flush pending and skip — never
        emit a row for paragraphs with multiple anchors.
      - structural header ('## ПРЕХОДНИ', '#'): flush pending and skip.

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


_SUBPOINT_RE = re.compile(r"^(?:[а-я]\)|\d{1,2}[\.\)])\s")
_ANCHOR_PREFIX_RE = re.compile(r"^(?:\*\*)?Чл\.\s+\d+[а-я]?\.(?:\*\*)?\s*")


def _split_implicit_alineas(body: str) -> list[tuple[str, str]]:
    """Position-derived alineas for marker-less multi-paragraph articles
    (pre-Указ-883 acts: ЗЗД, ЗС, ЗН, ЗЛС…). ВКС cites their алинеи by
    paragraph position („чл. 36, ал. 2 ЗЗД“) even though the source text
    carries no (N) markers. Sub-points (букви а), б)… and точки 1., 2)…)
    merge into the preceding alinea — they subdivide an алинея, they do
    not start one.
    Returns [] for single-paragraph articles (no implicit ал. 1 row —
    mirrors numbered acts, where a marker-less article gets no rows)."""
    paras = [p.strip() for p in _PARAGRAPH_SPLIT_RE.split(body) if p.strip()]
    if len(paras) < 2:
        return []
    merged: list[str] = []
    for p in paras:
        if merged and _SUBPOINT_RE.match(p):
            merged[-1] = merged[-1] + "\n\n" + p
        else:
            merged.append(p)
    if len(merged) < 2:
        return []
    out: list[tuple[str, str]] = []
    for i, text in enumerate(merged, start=1):
        if i == 1:
            text = _ANCHOR_PREFIX_RE.sub("", text, count=1)
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
