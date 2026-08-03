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

SHARED-DENYLIST SEAM GUARANTEE
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
The parser (text_parser.HtmlToMarkdown) and this gate share the same
CHROME_DENYLIST.  Both skip the *entire* subtree rooted at any element whose
CSS class is in that denylist.  This design has one invisible boundary: text
under a denylisted ancestor is skipped by BOTH the parser and the gate, so if a
chrome wrapper class were ever applied to an element that directly wraps real
legal text (a spine element such as Article or FinalEdictsArticle), neither pass
would see the gap.  The standing test
``tests/fetcher/bg/test_coverage.py::test_denylist_seam_no_spine_inside_chrome``
asserts this condition does not hold across all 6 act fixtures today.  If a new
act or layout change causes that test to fail, the fix is a targeted denylist
exception (not a blanket class addition) and requires IMPLEMENTATION-PREFLIGHT.
"""

import logging
import re
from collections import defaultdict

from bs4 import BeautifulSoup, Comment, NavigableString, Tag

from fetcher.bg.text_parser import CHROME_DENYLIST, CLASS_MAP, content_region

log = logging.getLogger(__name__)

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

# Article anchor, duplicated from index/provisions.py by design —
# fetcher/bg/ ships upstream without the Ahelia-private index/ package,
# so coverage.py must not import from index/.
_STRUCT_ARTICLE_RE = re.compile(r"(?:\*\*)?Чл\.\s+(\d+[а-я]?)\.")

# Child elements the parser (_block_text) turns into their own Markdown
# paragraph.  <br>-separated alineas inside ONE child are not counted here,
# which makes the source-side count a deliberate LOWER bound (see
# structure_mismatches).
_BLOCK_CHILD_TAGS = ("div", "p")


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


def make_gate_record(
    doc_id: int,
    slug: str,
    title: str,
    gate: dict,
    structure_mismatches: list[dict] | None = None,
) -> dict:
    """Build the canonical gate-failure record written to gate-report.json.

    Extracted to avoid the three-site duplication in bootstrap.py and refresh.py.
    The record shape is stable (protected surface — any change needs IMPLEMENTATION-PREFLIGHT):

        {
            "doc_id": int,
            "slug": str,
            "title": str,
            "uncovered_chars": int,
            "top_buckets": {class: count, ...},  # top 5 by descending count
            "structure_mismatches": [ {article, expected_blocks, got_blocks}, ... ]
        }

    ``structure_mismatches`` is the FR-034 paragraph-topology observation
    (see :func:`structure_mismatches`).  It is REPORT-only data: it never
    participates in the pass/fail decision this cycle, and the key defaults
    to ``[]`` so every existing caller keeps working unchanged.
    """
    return {
        "doc_id": doc_id,
        "slug": slug,
        "title": title,
        "uncovered_chars": gate["uncovered_chars"],
        "top_buckets": dict(
            sorted(gate["buckets"].items(), key=lambda x: -x[1])[:5]
        ),
        "structure_mismatches": list(structure_mismatches or []),
    }


def structure_mismatches(soup: BeautifulSoup, markdown: str) -> list[dict]:
    """Paragraph-topology check (FR-034), REPORT mode.

    Text-presence coverage (:func:`uncovered_legal_text`) is structure-blind:
    a flattened алинея preserves every character, so an article whose source
    paragraphs were glued into one flowed block passes with 0 uncovered chars.
    This check closes that blind spot by comparing TOPOLOGY: every ``Article``
    element whose source contributes N>=2 Markdown paragraphs must map to a
    markdown article block with at least N blank-line-separated paragraphs.

    Source side (expected_blocks)
        Direct child ``<div>``/``<p>`` elements carrying Cyrillic text — the
        blocks ``text_parser._block_text`` turns into separate paragraphs.
        Two deliberate adjustments:

        * **Title glue (parser rule 1a).**  lex.bg renders the article
          заглавие as its own child element before the anchor element, and
          ``_extract_article_text`` re-joins those two into ONE paragraph
          („Предмет Чл. 1. …“).  So when the first block carries no ``Чл. N.``
          anchor and the next block starts with one, the pair counts as a
          single expected block.  Without this, every titled article (ЗОП 261,
          ГПК 715) would be a false positive.
        * **Lower bound by construction.**  ``<br>``-separated alineas inside
          one child element also become separate Markdown paragraphs but are
          NOT counted here, and nested child blocks are counted once at the
          top level.  Both make expected_blocks <= the paragraph count a
          correct parser produces, so the check can only under-report — never
          invent a loss.

    Markdown side (got_blocks)
        Blank-line-separated paragraphs, attributed to the running article by
        the same rule ``index/provisions._extract_article_blocks`` uses (that
        module cannot be imported here — upstream layering): exactly one
        anchor starts an article, zero anchors continue it, a ``#`` header or
        a 2+-anchor paragraph (cite list / template) closes it.  Anchors are
        matched anywhere in the paragraph, not only at its start, because
        rule-1a glue puts the title in front of the anchor.  The first
        occurrence of an article number wins: quoted anchors in ПЗР
        (FR-030 family) must not overwrite the real article's count.

    Returns one dict ``{"article", "expected_blocks", "got_blocks"}`` per
    Article element whose source block count exceeds its markdown paragraph
    count.  REPORT mode: callers record the list next to the coverage data;
    enforcement (hard-fail) is a separate, later decision (D-058) taken only
    after the corpus-wide sweep proves cleanliness.
    """
    region, _ = content_region(soup)

    # --- Markdown side: article number -> paragraph count of its block ---
    md_counts: dict[str, int] = {}
    current: str | None = None
    for para in re.split(r"\n\n+", markdown):
        para = para.strip()
        if not para:
            continue
        if para.startswith("#"):
            current = None
            continue
        anchors = _STRUCT_ARTICLE_RE.findall(para)
        if len(anchors) == 1:
            art = anchors[0]
            if art in md_counts:
                # already seen — a quoted/duplicated anchor; do not attribute
                current = None
                continue
            current = art
            md_counts[art] = 1
        elif not anchors:
            if current is not None:
                md_counts[current] += 1
        else:  # 2+ anchors: cite list or template — attributable to nobody
            current = None

    # --- Source side ---
    out: list[dict] = []
    for el in region.find_all("div", class_="Article"):
        blocks = [
            c for c in el.children
            if isinstance(c, Tag) and c.name in _BLOCK_CHILD_TAGS
            and _CYR.search(c.get_text())
        ]
        expected = len(blocks)
        if expected >= 2:
            first = _normalize(blocks[0].get_text())
            second = _normalize(blocks[1].get_text())
            if not _STRUCT_ARTICLE_RE.search(first) and second.startswith("Чл."):
                expected -= 1  # rule-1a title glue: title + anchor = 1 block
        if expected < 2:
            continue
        m = _STRUCT_ARTICLE_RE.search(el.get_text())
        if not m:
            continue
        art = m.group(1)
        got = md_counts.get(art, 0)
        if got < expected:
            out.append({"article": art,
                        "expected_blocks": expected,
                        "got_blocks": got})
    return out


def safe_structure_mismatches(soup, markdown: str, check=structure_mismatches) -> list[dict]:
    """REPORT-mode wrapper around :func:`structure_mismatches`.

    The paragraph-topology observation is diagnostic data, not a gate: it must
    never abort a 3 600-act run over a layout the topology walk cannot read.
    Any exception is logged and downgraded to an empty list.  ``check`` is
    injectable for the same reason ``refresh``'s ``coverage_gate`` is —
    orchestration tests feed opaque stand-ins instead of real soups.
    """
    try:
        return check(soup, markdown)
    except Exception as e:  # noqa: BLE001 — report-only data, never fatal
        log.warning("structure check skipped (report-mode only): %s", e)
        return []


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
    region, _ = content_region(soup)

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

        # Full-text coverage check at ANY length. The old >200-char rule
        # anchored only the first/last 100 chars, leaving the middle
        # unchecked — a parser bug dropping text from the middle of a
        # long node passed the gate silently (P0-4, review 2026-07-02:
        # the exact D-047 failure class). The head/tail rule existed to
        # tolerate minor trailing-punctuation variance; that tolerance
        # is now explicit and bounded: retry with trailing punctuation
        # stripped, never with the middle unchecked.
        covered = t in M
        if not covered:
            t2 = t.rstrip(" .,;:")
            covered = bool(t2) and t2 in M

        if covered:
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
