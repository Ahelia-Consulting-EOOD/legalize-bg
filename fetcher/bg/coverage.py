"""Class-agnostic legal-text coverage validator for lex.bg Markdown output.

Answers: "Did any source legal text in the HTML fail to reach the produced Markdown?"

Method (formulation B — match SOURCE text against OUTPUT markdown):
1. Content region is scoped via the same LCA the parser uses (_content_region).
2. Markdown is whitespace/markup-normalised: strip ``**``, unify quotes, collapse whitespace.
3. Every Cyrillic NavigableString in the region that has NO chrome ancestor is checked
   as a substring of the normalised Markdown.  Unmatched text is "uncovered".
4. Counting: when a NavigableString is unmatched, find its nearest enclosing legal
   element (a CLASS_MAP include=True class).  Count that element's full text length
   (de-duplicated: each legal element is counted at most once).  For unmatched nodes
   with no legal ancestor (pure chrome residual), count the node's own char length.
5. Result: {"uncovered_chars": int, "buckets": {class_str: int}}.

This design means that if ANY text node inside a FinalEdictsArticle (or Article, etc.)
is missing from the output, the entire block is reported as uncovered — which correctly
reflects that the parser dropped it as a unit.

DEFAULT_CHROME mirrors CHROME_DENYLIST from text_parser, extended with CLASS_MAP
excluded entries (e.g. HistoryOfDocument).  Pass a custom set to override.
"""

import re
from collections import defaultdict

from bs4 import BeautifulSoup, Comment, NavigableString, Tag

from fetcher.bg.text_parser import CHROME_DENYLIST, CLASS_MAP, HtmlToMarkdown

# ---------------------------------------------------------------------------
# Public constant
# ---------------------------------------------------------------------------

# DEFAULT_CHROME = CHROME_DENYLIST plus any CLASS_MAP entries marked include=False
# (e.g. HistoryOfDocument).  The brief lists these together; keeping them in one
# frozenset means any future excluded CLASS_MAP entry is automatically covered.
DEFAULT_CHROME: frozenset[str] = CHROME_DENYLIST | frozenset(
    c for c, (_, inc) in CLASS_MAP.items() if not inc
)

# Classes that the parser emits as a self-contained block (legal spine classes).
_LEGAL_CLASSES: frozenset[str] = frozenset(c for c, (_, inc) in CLASS_MAP.items() if inc)

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

_CYR = re.compile(r"[А-Яа-я]")


def _normalize(text: str) -> str:
    """Normalize text for whitespace/markup-insensitive substring comparison.

    Steps applied (in order):
    - Strip bold markers (``**``).
    - Unify Bulgarian/typographic quote variants to plain ASCII double-quote.
    - Collapse all whitespace (including newlines) to a single space and strip.
    """
    # Remove bold markers emitted by the Markdown formatter
    text = text.replace("**", "")
    # Unify quote variants: „ " " » «  →  "
    text = re.sub(r'[„""»«]', '"', text)
    # Collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _nearest_class(node: NavigableString) -> str:
    """Return the nearest ancestor's CSS class string, or '<no-class>'."""
    for anc in node.parents:
        cls = anc.get("class") if isinstance(anc, Tag) else None
        if cls:
            return "+".join(cls)
        if isinstance(anc, Tag) and anc.name in ("script", "style"):
            return f"<{anc.name}>"
    return "<no-class>"


def _nearest_legal_ancestor(node: NavigableString, region_id: int) -> Tag | None:
    """Return the nearest ancestor with a legal CLASS_MAP include=True class.

    Walks toward the root but stops at the content region boundary.
    Returns None when no legal ancestor exists within the region.
    """
    for anc in node.parents:
        if id(anc) == region_id:
            break
        if not isinstance(anc, Tag):
            continue
        if set(anc.get("class") or []) & _LEGAL_CLASSES:
            return anc
    return None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def uncovered_legal_text(
    soup: BeautifulSoup,
    markdown: str,
    chrome: frozenset[str] = DEFAULT_CHROME,
) -> dict:
    """Return uncovered Cyrillic character counts and per-class buckets.

    Parameters
    ----------
    soup:
        Parsed HTML (BeautifulSoup).
    markdown:
        The Markdown produced by the parser for this act.
    chrome:
        Set of CSS class names to treat as navigation/UI chrome and skip.
        Defaults to ``DEFAULT_CHROME`` (= CHROME_DENYLIST + excluded CLASS_MAP entries).

    Returns
    -------
    dict with keys:

    ``uncovered_chars``
        Total character count of Cyrillic text that was NOT found in *markdown*.
        When the text belongs to a legal block element (Article, FinalEdictsArticle,
        etc.) the entire element's text length is counted (de-duplicated), so that
        "one missing phrase in a 5 000-char block" registers as 5 000 uncovered
        chars — faithfully reflecting a parser drop.
    ``buckets``
        Mapping from nearest-ancestor CSS class → uncovered char count, so callers
        can identify which source elements caused the gap.
    """
    region, _ = HtmlToMarkdown()._content_region(soup)

    # Normalise the Markdown output once; all node checks run against this.
    M = _normalize(markdown)

    uncovered_chars = 0
    buckets: dict[str, int] = defaultdict(int)

    region_id = id(region)
    # Track legal elements already counted to avoid double-counting their chars.
    counted_legal_ids: set[int] = set()

    for tn in region.descendants:
        # Text nodes only
        if not isinstance(tn, NavigableString):
            continue
        if isinstance(tn, Comment):
            continue

        # Skip embedded script / style content
        parent = tn.parent
        if isinstance(parent, Tag) and parent.name in ("script", "style"):
            continue

        # Must contain at least one Cyrillic character
        raw = str(tn)
        if not _CYR.search(raw):
            continue

        # Skip if any ancestor WITHIN the region carries a chrome class.
        # We stop at the region itself so that the region's own classes (e.g.
        # 'boxi'/'boxinb' when it doubles as the LCA) are not counted as chrome.
        has_chrome_ancestor = False
        for anc in tn.parents:
            if id(anc) == region_id:
                break  # reached the region boundary — stop
            if not isinstance(anc, Tag):
                continue
            for cls in anc.get("class") or []:
                if cls in chrome:
                    has_chrome_ancestor = True
                    break
            if has_chrome_ancestor:
                break
        if has_chrome_ancestor:
            continue

        # Normalise the candidate text
        t = _normalize(raw)
        if len(t) < 8:
            # Too short to be meaningful — ignore to avoid false positives
            continue

        # For long strings use just the first 40 chars as the lookup signature
        # (the full string might have trailing punctuation or whitespace that
        # differs between source and output; the prefix is enough to confirm
        # the block was emitted).
        signature = t[:40] if len(t) >= 40 else t

        if signature in M:
            continue  # covered

        # ---- UNCOVERED ----
        # Find the nearest enclosing legal block element.  When found, count the
        # *entire element's text* (not just this node) so that a single missing
        # phrase correctly flags the whole block as dropped.  De-duplicate so
        # multiple unmatched nodes within the same element are only counted once.
        bucket_key = _nearest_class(tn)
        legal_anc = _nearest_legal_ancestor(tn, region_id)

        if legal_anc is not None:
            eid = id(legal_anc)
            if eid not in counted_legal_ids:
                counted_legal_ids.add(eid)
                char_count = len(legal_anc.get_text().strip())
                uncovered_chars += char_count
                buckets[bucket_key] += char_count
            # else: already counted this element — skip
        else:
            # No legal ancestor: count the node's own text (chrome residual etc.)
            char_count = len(raw.strip())
            uncovered_chars += char_count
            buckets[bucket_key] += char_count

    return {"uncovered_chars": uncovered_chars, "buckets": dict(buckets)}
