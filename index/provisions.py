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


def _extract_article_blocks(markdown: str) -> list[tuple[str, str]]:
    """Return list of (article_id, body_text). Each Article-class HTML
    element produces one paragraph in the markdown body, so paragraph
    boundaries (\\n\\n) are article boundaries. The body is the entire
    paragraph (preserving any title preamble before the anchor and all
    inline alineas after)."""
    blocks: list[tuple[str, str]] = []
    for raw_para in _PARAGRAPH_SPLIT_RE.split(markdown):
        para = raw_para.strip()
        if not para or _is_structural_header(para):
            continue
        m = _ARTICLE_RE.search(para)
        if not m:
            continue
        article_id = m.group(1)
        blocks.append((article_id, para))
    return blocks


def parse(markdown: str, law_id: str) -> list[Provision]:
    """Phase 1b.1 article-level extraction. Alinea rows added in Task 5."""
    rows: list[Provision] = []
    for article_id, body in _extract_article_blocks(markdown):
        rows.append(Provision(
            law_id=law_id,
            article=article_id,
            paragraph=None,
            text=body,
            text_hash=_hash(body),
        ))
    return rows
