"""HTML-to-Markdown Converter — Legalize TextParser interface for lex.bg."""

import re

from bs4 import BeautifulSoup, Tag


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


class HtmlToMarkdown:
    """Converts lex.bg HTML DOM to structured Markdown."""

    def convert(self, soup: BeautifulSoup) -> str:
        """Convert parsed HTML to Markdown body (no frontmatter)."""
        lines: list[str] = []

        for element in soup.find_all(class_=list(CLASS_MAP.keys())):
            if not isinstance(element, Tag):
                continue

            css_class = self._get_mapped_class(element)
            if css_class is None:
                continue

            prefix, include = CLASS_MAP[css_class]
            if not include:
                continue

            if css_class == "Article":
                lines.append(self._format_article(element))
            elif css_class == "FinalEdictsArticle":
                lines.append(self._format_edict_article(element))
            elif css_class == "PreHistory":
                text = element.get_text(strip=True)
                if text:
                    lines.append(f"*{text}*")
            else:
                # Use get_text(" ", strip=True) + whitespace collapse to de-glue
                # heading text from adjacent КЪМ act-name spans.
                text = re.sub(r"\s+", " ", element.get_text(" ", strip=True)).strip()
                if text:
                    lines.append(f"{prefix}{text}")

            lines.append("")  # blank line after each block

        return "\n".join(lines).strip() + "\n"

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
            re.sub(r"[ \t ]+", " ", line).strip()
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
