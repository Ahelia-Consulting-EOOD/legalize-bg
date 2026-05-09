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


def _hash(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()[:16]


def _is_structural_header(para: str) -> bool:
    """Markdown structural headers: '#', '## ПРЕХОДНИ…', etc. They never
    introduce articles; skip them in extraction."""
    return para.startswith("#")


_ALINEA_CONTINUATION_RE = re.compile(r"^\s*\(\s*\d+[а-я]?\s*\)")


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
            if pending_id is not None and _looks_like_alinea_continuation(para):
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
_ALINEA_MARKER_RE = re.compile(r"\(\s*(\d+[а-я]?)\s*\)")


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
        for paragraph_id, alinea_text in _split_alineas(body):
            rows.append(Provision(
                law_id=law_id,
                article=article_id,
                paragraph=paragraph_id,
                text=alinea_text,
                text_hash=_hash(alinea_text),
            ))
    return rows
