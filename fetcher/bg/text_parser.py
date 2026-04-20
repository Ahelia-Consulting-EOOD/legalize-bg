"""HTML-to-Markdown Converter — Legalize TextParser interface for lex.bg."""

from bs4 import BeautifulSoup, Tag


# CSS class -> (markdown prefix, include in output)
CLASS_MAP = {
    "TitleDocument": ("# ", True),
    "PreHistory": ("*", True),       # italic
    "Part": ("## ", True),
    "Heading": ("### ", True),
    "Section": ("#### ", True),
    "Article": ("", True),           # special handling for bold article number
    "TransitionalFinalEdicts": ("## ", True),
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
            elif css_class == "PreHistory":
                text = element.get_text(strip=True)
                if text:
                    lines.append(f"*{text}*")
            else:
                text = element.get_text(strip=True)
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
        """Extract article text, converting <br> to newlines."""
        parts = []
        for child in element.children:
            if isinstance(child, Tag):
                if child.name == "br":
                    parts.append("\n")
                else:
                    parts.append(child.get_text())
            else:
                text = str(child)
                if text.strip():
                    parts.append(text.strip())
        return " ".join(parts).replace("  ", " ").strip()
