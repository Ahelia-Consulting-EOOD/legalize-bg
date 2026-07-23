"""FR-032 full-coverage body segmenter.

Splits an act's Markdown body into ordered segments (article / § / annex /
preamble / other) as OFFSET SPANS over the body. The coverage invariant —
``"".join(body[s.start:s.end]) == body`` — therefore holds by construction:
segments are cut points, never re-assembled strings. This is the design's
answer to the 57%-provisions-coverage trap (design 2026-07-21 §2, D-056).

Segmentation cuts only at PARAGRAPH-INITIAL anchors, so a quoted "Чл. 5."
inside amendment text never splits its paragraph; at worst a quoted anchor
that opens a paragraph mislabels a segment (accepted, labels are advisory —
`get_article` resolves via `provisions`, untouched).

`segment_texts` additionally normalizes each segment and chunks oversized
ones (paragraph-boundary first, hard char-boundary fallback) so no emitted
row exceeds SEG_MAX_BYTES — the rule that structurally retires the D1 2 MB
value cap (spec v2.0). The normalizer must be non-expanding in UTF-8 bytes
(bg_normalize lowercases + collapses whitespace, so it is).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, replace

# Ratified Q4 (D-056) + spike calibration: 400 KB normalized per row.
# Any value ≤ ~1.8 MB is D1-safe; the spike measured a 1.83 MB single
# annex, so chunking (not per-article rows alone) is load-bearing.
SEG_MAX_BYTES = 400_000

# Paragraph-initial anchors. The article form mirrors
# index/provisions.py:_ARTICLE_RE (capitalized "Чл." = anchor; lowercase
# "чл." = inline reference) but is anchored to the paragraph start,
# optionally after bold markers.
_ART_START = re.compile(r"^(?:\*\*)?Чл\.\s+(\d+[а-я]?)\.?")
_PARA_START = re.compile(r"^(?:\*\*)?§\s*(\d+[а-я]?)\.?")
_ANNEX_START = re.compile(r"^(?:\*\*)?Приложение\b\s*(?:№\s*)?(\d*[а-я]?)")
_PARA_SPLIT = re.compile(r"\n\n+")


@dataclass(frozen=True)
class Segment:
    """One body segment. `start`/`end` are character offsets into the
    act body; `label` is a display/citation hint ('чл. 5', '§ 3',
    'приложение 2', '') — advisory metadata, not a lookup key."""

    kind: str   # article | para | annex | preamble | other
    label: str
    start: int
    end: int


def _paragraph_spans(body: str) -> list[tuple[int, int]]:
    """Spans that tile `body` completely; each paragraph carries its
    trailing blank-line separator so no character falls between spans."""
    spans: list[tuple[int, int]] = []
    pos = 0
    for m in _PARA_SPLIT.finditer(body):
        spans.append((pos, m.end()))
        pos = m.end()
    if pos < len(body) or not spans:
        spans.append((pos, len(body)))
    return spans


def _classify(paragraph: str) -> tuple[str, str] | None:
    """(kind, label) when this paragraph STARTS a new segment, else None."""
    t = paragraph.lstrip()
    m = _ART_START.match(t)
    if m:
        return "article", f"чл. {m.group(1)}"
    m = _PARA_START.match(t)
    if m:
        return "para", f"§ {m.group(1)}"
    m = _ANNEX_START.match(t)
    if m:
        return "annex", f"приложение {m.group(1)}".rstrip()
    return None


def segment(body: str) -> list[Segment]:
    """Split `body` into ordered, gap-free segments.

    - Text before the first anchor is one 'preamble' segment.
    - Markdown heading paragraphs ('#...') glue to the FOLLOWING segment.
    - A body with no anchors at all is a single 'other' segment.
    """
    if not body:
        return []
    segs: list[Segment] = []
    cur_kind, cur_label = "preamble", ""
    cur_start = 0
    glue_start: int | None = None  # start of a pending heading run
    any_anchor = False

    for start, end in _paragraph_spans(body):
        text = body[start:end]
        if text.lstrip().startswith("#"):
            if glue_start is None:
                glue_start = start
            continue
        cls = _classify(text)
        if cls is not None:
            cut = glue_start if glue_start is not None else start
            if cut > cur_start:
                segs.append(Segment(cur_kind, cur_label, cur_start, cut))
            cur_kind, cur_label = cls
            cur_start = cut
            any_anchor = True
        glue_start = None

    if not any_anchor:
        cur_kind, cur_label = "other", ""
    if len(body) > cur_start:
        segs.append(Segment(cur_kind, cur_label, cur_start, len(body)))
    return segs


def _hard_split(body: str, seg: Segment, max_bytes: int) -> list[Segment]:
    """Char-boundary split of a paragraph-less oversized span into pieces
    of ≤ max_bytes RAW UTF-8 bytes each (normalizers are non-expanding,
    so the normalized pieces satisfy the bound too)."""
    pieces: list[Segment] = []
    piece_start = seg.start
    acc = 0
    for i in range(seg.start, seg.end):
        n = len(body[i].encode("utf-8"))
        if acc + n > max_bytes and i > piece_start:
            pieces.append(replace(seg, start=piece_start, end=i))
            piece_start, acc = i, 0
        acc += n
    pieces.append(replace(seg, start=piece_start, end=seg.end))
    return pieces


def _chunk(body: str, seg: Segment, normalize, max_bytes: int
           ) -> list[Segment]:
    """Split an oversized segment at paragraph boundaries (greedy fill);
    single paragraphs that still exceed the budget hard-split at char
    boundaries."""
    raw = body[seg.start:seg.end]
    out: list[Segment] = []
    piece_start = 0
    acc_bytes = 0
    for s, e in _paragraph_spans(raw):
        para_bytes = len(normalize(raw[s:e]).encode("utf-8"))
        if acc_bytes and acc_bytes + para_bytes > max_bytes:
            out.append(replace(seg, start=seg.start + piece_start,
                               end=seg.start + s))
            piece_start, acc_bytes = s, 0
        acc_bytes += para_bytes
    out.append(replace(seg, start=seg.start + piece_start, end=seg.end))

    final: list[Segment] = []
    for piece in out:
        if len(normalize(body[piece.start:piece.end]).encode("utf-8")) \
                > max_bytes:
            final.extend(_hard_split(body, piece, max_bytes))
        else:
            final.append(piece)
    return final


def segment_texts(body: str, normalize,
                  max_bytes: int = SEG_MAX_BYTES
                  ) -> list[tuple[Segment, str]]:
    """Segment `body`, normalize each segment with `normalize`, and chunk
    any segment whose normalized text exceeds `max_bytes`. Returns
    ordered (Segment, normalized_text) rows whose spans still tile the
    body exactly."""
    rows: list[tuple[Segment, str]] = []
    for seg in segment(body):
        norm = normalize(body[seg.start:seg.end])
        if len(norm.encode("utf-8")) <= max_bytes:
            rows.append((seg, norm))
            continue
        for piece in _chunk(body, seg, normalize, max_bytes):
            rows.append((piece, normalize(body[piece.start:piece.end])))
    return rows
