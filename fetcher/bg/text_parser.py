"""HTML-to-Markdown Converter — Legalize TextParser interface for lex.bg."""

import logging
import re

from bs4 import BeautifulSoup, Tag

log = logging.getLogger(__name__)

# CSS class -> (markdown prefix, include in output)
CLASS_MAP = {
    "TitleDocument": ("# ", True),
    "PreHistory": ("*", True),       # italic
    "Part": ("## ", True),
    "Heading": ("### ", True),
    "Section": ("#### ", True),
    "Article": ("", True),           # special handling for bold article number
    "AdditionalEdicts": ("## ", True),       # Допълнителни разпоредби heading
    "FinalEdicts": ("## ", True),            # Заключителни разпоредби (КЪМ …) heading
    "TransitionalFinalEdicts": ("## ", True),
    "FinalEdictsArticle": ("", True),        # § definition / transitional provision bodies
    "HistoryOfDocument": ("", False),  # excluded from body
}

# Known chrome/navigation elements that must never appear in the Markdown body.
# Elements whose class is in neither CLASS_MAP nor CHROME_DENYLIST are kept by
# default (with a warning) so unknown legal classes surface rather than vanish.
CHROME_DENYLIST: frozenset[str] = frozenset({
    "buttons", "boxi", "boxinb", "picHasEditions", "picRefsFromActs",
    "HistoryOfDocument", "HistoryItem", "HistoryReference",
    "NewDocReference", "SameDocReference", "LegalDocReference", "contextads",
})

# Spine classes used to locate the legal-content region (LCA of these elements).
_SPINE: frozenset[str] = frozenset(c for c, (_, inc) in CLASS_MAP.items() if inc)


class HtmlToMarkdown:
    """Converts lex.bg HTML DOM to structured Markdown."""

    def convert(self, soup: BeautifulSoup) -> str:
        """Convert parsed HTML to Markdown body (no frontmatter)."""
        lines: list[str] = []
        region = self._content_region(soup)
        self._walk(region, lines)
        return "\n".join(lines).strip() + "\n"

    def _content_region(self, soup: BeautifulSoup) -> Tag:
        """Return the LCA of all spine elements, scoping the walk to legal content.

        Restricts the keep-by-default pass to the legal-content region so that
        page navigation, header, and footer chrome outside the LCA is never emitted.
        """
        spine_els = [
            e for e in soup.find_all(True)
            if set(e.get("class") or []) & _SPINE
        ]
        if not spine_els:
            return soup  # type: ignore[return-value]
        chains = [set(id(p) for p in el.parents) for el in spine_els]
        common = set.intersection(*chains) if chains else set()
        for p in spine_els[0].parents:
            if id(p) in common:
                return p  # type: ignore[return-value]
        return soup  # type: ignore[return-value]

    def _walk(self, element: Tag, lines: list[str]) -> None:
        """Walk element's direct children and emit content in document order.

        Mapped classes → handled as before (emitted or excluded).
        Chrome denylist → skipped (no descent).
        Unknown class(es) → kept as plain text + WARNING (no descent).
        No class → structural container; descend into its children.

        Never descends into an already-handled element, which prevents
        double-emission of text already covered by a mapped parent's get_text().
        """
        for child in element.children:
            if not isinstance(child, Tag):
                continue

            classes: list[str] = child.get("class") or []
            class_set: set[str] = set(classes)

            # --- Mapped class: emit (or exclude) and do NOT descend ---
            mapped_cls = self._get_mapped_class(child)
            if mapped_cls is not None:
                prefix, include = CLASS_MAP[mapped_cls]
                if include:
                    if mapped_cls == "Article":
                        lines.append(self._format_article(child))
                    elif mapped_cls == "FinalEdictsArticle":
                        lines.append(self._format_edict_article(child))
                    elif mapped_cls == "PreHistory":
                        text = child.get_text(strip=True)
                        if text:
                            lines.append(f"*{text}*")
                    else:
                        # Use get_text(" ") + whitespace collapse to de-glue
                        # heading text from adjacent КЪМ act-name spans.
                        text = re.sub(r"\s+", " ", child.get_text(" ", strip=True)).strip()
                        if text:
                            lines.append(f"{prefix}{text}")
                    lines.append("")
                # Whether included or excluded, don't descend.
                continue

            # --- Chrome denylist: skip entirely ---
            if class_set & CHROME_DENYLIST:
                continue

            # --- Unknown class(es): keep as plain text + warn ---
            if class_set:
                text = re.sub(r"\s+", " ", child.get_text(" ", strip=True)).strip()
                if text:
                    log.warning("unmapped content class kept: %s", classes)
                    lines.append(text)
                    lines.append("")
                continue  # don't descend; text already captured

            # --- No class: structural container, descend ---
            self._walk(child, lines)

    def _get_mapped_class(self, element: Tag) -> str | None:
        """Find the first CSS class that maps to a known role."""
        for cls in element.get("class", []):
            if cls in CLASS_MAP:
                return cls
        return None

    def _block_text(self, element: Tag) -> str:
        """Flatten element text, treating <br> and block tags as paragraph breaks.

        §-provision точки come as <div> children; alineas are separated by <br>.
        Each becomes its own Markdown paragraph (blank-line separated).
        """
        parts: list[str] = []

        def walk(node: Tag) -> None:
            for child in node.children:
                if isinstance(child, Tag):
                    if child.name == "br":
                        parts.append("\n")
                    elif child.name in ("div", "p", "li", "tr"):
                        parts.append("\n")
                        walk(child)
                        parts.append("\n")
                    else:
                        walk(child)
                else:
                    parts.append(str(child))

        walk(element)
        lines = [
            re.sub(r"[ \t ]+", " ", line).strip()
            for line in "".join(parts).split("\n")
        ]
        return "\n\n".join(line for line in lines if line)

    def _format_edict_article(self, element: Tag) -> str:
        """Format a FinalEdictsArticle element with bold § or Чл. number prefix."""
        text = self._block_text(element)
        m = re.match(r"^(§\s*\d+[а-яА-Я]?\.)", text) or re.match(
            r"^(Чл\.\s*\d+[а-яА-Я]?\.)", text
        )
        if m:
            return f"**{m.group(1)}**{text[m.end():]}"
        return text

    def _format_article(self, element: Tag) -> str:
        """Format an article element, bolding the article number."""
        # Extract text, preserving paragraph breaks
        text = self._extract_article_text(element)

        # Bold the article number prefix (e.g., "Чл. 1.")
        if text.startswith("Чл."):
            dot_pos = text.find(".", 4)  # find the dot after article number
            if dot_pos > 0:
                article_num = text[: dot_pos + 1]
                rest = text[dot_pos + 1:]
                return f"**{article_num}**{rest}"

        return text

    def _extract_article_text(self, element: Tag) -> str:
        """Extract article text, treating <br> as a paragraph break.

        Bulgarian legal articles have numbered alineas ((1), (2), ...)
        separated by <br>. In Markdown, a single newline is a soft break
        (rendered as a space) — we need a blank line between alineas so
        each renders as its own paragraph.
        """
        lines: list[str] = []
        buf: list[str] = []

        def flush():
            if buf:
                line = " ".join(s for s in buf if s).strip()
                if line:
                    lines.append(line)
                buf.clear()

        for child in element.children:
            if isinstance(child, Tag):
                if child.name == "br":
                    flush()
                else:
                    buf.append(child.get_text().strip())
            else:
                text = str(child).strip()
                if text:
                    buf.append(text)
        flush()

        return "\n\n".join(lines)
