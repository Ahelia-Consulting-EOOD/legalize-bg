"""Metadata Parser — Legalize MetadataParser interface for lex.bg."""

import re
from datetime import date

from bs4 import BeautifulSoup, Tag

from fetcher.bg.assembler import generate_slug


CATEGORY_TO_RANGO = {
    "laws": "закон",
    "codes": "кодекс",
    "ordinances": "наредба",
    "regulations": "правилник",
    "implementing": "правилник по прилагане",
}

# Bulgarian month names -> month number. Real lex.bg text uses Title-Case
# Cyrillic month names (e.g. "Февруари"), so we match case-insensitively.
BG_MONTHS = {
    "януари": 1,
    "февруари": 2,
    "март": 3,
    "април": 4,
    "май": 5,
    "юни": 6,
    "юли": 7,
    "август": 8,
    "септември": 9,
    "октомври": 10,
    "ноември": 11,
    "декември": 12,
}

_BG_MONTH_ALT = "|".join(BG_MONTHS.keys())

# Regex patterns for parsing Bulgarian dates and DV references.
#
# Two date forms appear in lex.bg HTML:
#   1. Numeric: "15.04.2016 г." (used in .PreHistory for "В сила от ...")
#   2. Bulgarian month name: "16 Февруари 2016г." (used in .HistoryOfDocument
#      for DV references)
DATE_PATTERN = re.compile(
    r"(\d{1,2})\.(\d{1,2})\.(\d{4})\s*г\."
)

# DV reference in .HistoryOfDocument: "ДВ. бр.13 от 16 Февруари 2016г."
# Accept optional period after "ДВ" and after "бр", and accept either
# Bulgarian-month-name form OR numeric form after "от".
DV_REF_PATTERN = re.compile(
    r"(?:ДВ|DV)\.?,?\s*бр\.?\s*(\d+)"
    r"(?:\s*от\s*"
    r"(?:(\d{1,2})\s+(" + _BG_MONTH_ALT + r")\s*(\d{4})\s*г\.?"
    r"|(\d{1,2})\.(\d{1,2})\.(\d{4})\s*г\.?))?",
    re.IGNORECASE,
)

EFFECTIVE_DATE_PATTERN = re.compile(
    r"[Вв]\s*сила\s*от\s*(\d{1,2})\.(\d{1,2})\.(\d{4})\s*г\."
)


class MetadataParser:
    """Extracts YAML frontmatter fields from lex.bg HTML DOM."""

    CATEGORY_TO_RANGO = CATEGORY_TO_RANGO

    def parse(self, soup: BeautifulSoup, doc_id: int, category: str) -> dict:
        """Extract all frontmatter fields from parsed HTML.

        Args:
            soup: Parsed HTML DOM
            doc_id: lex.bg document ID
            category: Corpus category directory name (laws, codes, ordinances, ...)

        Returns:
            dict with 13 named fields + amendment_history array
        """
        title = self._extract_title(soup)
        pre_history = self._extract_pre_history(soup)
        amendment_history = self._extract_amendment_history(soup)

        effective_date = self._parse_effective_date(pre_history)
        pub_date = self._extract_publication_date(amendment_history, pre_history)
        last_update = self._extract_last_update(amendment_history, pub_date)
        dv_issue, dv_year = self._extract_first_dv(amendment_history, pre_history)

        rango = CATEGORY_TO_RANGO.get(category, "закон")
        slug = generate_slug(title) if title else str(doc_id)

        return {
            # 8 mandatory Legalize fields
            "titulo": title,
            "identificador": str(doc_id),
            "pais": "bg",
            "rango": rango,
            "fecha_publicacion": pub_date,
            "ultima_actualizacion": last_update,
            "estado": "vigente",
            "fuente": "lex.bg",
            # 5 Bulgarian extensions
            "dv_issue": dv_issue,
            "dv_year": dv_year,
            "effective_date": effective_date,
            "category": category,
            "eli": self._build_eli(rango, pub_date, slug),
            # Amendment history array
            "amendment_history": amendment_history,
        }

    @staticmethod
    def _build_eli(rango: str, pub_date: str | None, slug: str) -> str:
        """Build ELI URI per docs/architecture/data-model.md:134:
        /eli/bg/{rango}/{Y}/{M}/{D}/{slug}/con

        Uses ASCII-transliterated slug for URI interop. Falls back to
        "unknown" segments when publication date is unavailable.
        """
        if pub_date and len(pub_date) >= 10:
            try:
                d = date.fromisoformat(pub_date)
                ymd = f"{d.year}/{d.month}/{d.day}"
            except ValueError:
                ymd = "unknown/unknown/unknown"
        else:
            ymd = "unknown/unknown/unknown"
        return f"/eli/bg/{rango}/{ymd}/{slug}/con"

    def _extract_title(self, soup: BeautifulSoup) -> str:
        el = soup.select_one(".TitleDocument")
        return el.get_text(strip=True) if el else ""

    def _extract_pre_history(self, soup: BeautifulSoup) -> str:
        el = soup.select_one(".PreHistory")
        return el.get_text(strip=True) if el else ""

    def _extract_amendment_history(self, soup: BeautifulSoup) -> list[dict]:
        el = soup.select_one(".HistoryOfDocument")
        if el is None:
            return []

        text = el.get_text()
        entries = []
        for match in DV_REF_PATTERN.finditer(text):
            issue = match.group(1)
            # Group layout:
            #   1: issue number
            #   2,3,4: day, Bulgarian-month-name, year (name form)
            #   5,6,7: day, month, year (numeric form)
            day = month = year = None
            if match.group(2) and match.group(3) and match.group(4):
                day = int(match.group(2))
                month = BG_MONTHS.get(match.group(3).lower())
                year = int(match.group(4))
            elif match.group(5) and match.group(6) and match.group(7):
                day = int(match.group(5))
                month = int(match.group(6))
                year = int(match.group(7))

            if day is not None and month is not None and year is not None:
                try:
                    d = date(year, month, day)
                    entries.append({"dv": f"{issue}/{year}", "date": d.isoformat()})
                except ValueError:
                    entries.append({"dv": f"{issue}/{year}", "date": None})
            else:
                entries.append({"dv": issue, "date": None})

        return entries

    def _parse_effective_date(self, pre_history: str) -> str | None:
        match = EFFECTIVE_DATE_PATTERN.search(pre_history)
        if match:
            day, month, year = int(match.group(1)), int(match.group(2)), int(match.group(3))
            try:
                return date(year, month, day).isoformat()
            except ValueError:
                return None
        return None

    def _extract_publication_date(self, amendments: list[dict], pre_history: str) -> str | None:
        # First DV reference is usually the publication
        if amendments and amendments[0].get("date"):
            return amendments[0]["date"]
        # Fallback: parse from pre_history
        match = DATE_PATTERN.search(pre_history)
        if match:
            day, month, year = int(match.group(1)), int(match.group(2)), int(match.group(3))
            try:
                return date(year, month, day).isoformat()
            except ValueError:
                return None
        return None

    def _extract_last_update(self, amendments: list[dict], pub_date: str | None) -> str | None:
        if amendments:
            # Last amendment with a date
            for entry in reversed(amendments):
                if entry.get("date"):
                    return entry["date"]
        return pub_date

    def _extract_first_dv(self, amendments: list[dict], pre_history: str) -> tuple[str | None, int | None]:
        if amendments:
            dv = amendments[0].get("dv", "")
            if "/" in dv:
                issue, year = dv.split("/", 1)
                return issue, int(year) if year.isdigit() else None
            return dv, None
        # Fallback
        match = DV_REF_PATTERN.search(pre_history)
        if match:
            issue = match.group(1)
            year = None
            if match.group(4):
                year = int(match.group(4))
            elif match.group(7):
                year = int(match.group(7))
            return issue, year
        return None, None
